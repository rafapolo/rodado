#!/usr/bin/env python3
"""Generate `docs/context/join_keys.md` from `schemas.json`.

    python3 scripts/gera_schemas.py     # beelink -> schemas.json
    python3 scripts/gera_join_keys.py   # schemas.json -> docs/context/join_keys.md

The previous version of the doc was written by hand (its header credited a
`schema_compiler.py` that does not exist in the repo) and covered 24 columns
whose names already matched across datasets. That misses most of what actually
connects the mirror: the independently-scraped sources name the same key
`UF`, `codIBGE`, `cód_ibge`, `MUNIC`, `CPF_CNPJ`, `nomeMunicipio`…, and the
mirrored datasets carry role-qualified municipality columns
(`id_municipio_residencia`, `_ocorrencia`, `_trabalho`, …) that all resolve to
the same directory. Those are the joins an LLM cannot guess.

Three layers of content:

  1. CURATED   — hand-written sections for the hub keys: what the code is,
                 which table is canonical, and the gotchas.
  2. BRIDGES   — the non-standard columns, each with a tested normalization
                 recipe (see MUNICIPIO_BRIDGES / IDENTITY_BRIDGES). The
                 `verificado` field records what the recipe actually matched
                 when it was run on beelink, so a reader knows the recipe is
                 not aspirational.
  3. AUTO      — every remaining column shared by >= MIN_DATASETS datasets,
                 emitted with the same `### \\`col\\` — N tables` header so
                 `mcp_server.get_join_keys()` can serve it.

`mcp_server.py` parses this file with a regex on that h3 header and slices
until the next one, so every h3 must be a real column name and any prose that
is not part of a column's section must come before the first h3.
"""

import argparse
import json
import re
import subprocess
import sys

import yaml
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "schemas.json"
DST = REPO / "docs" / "context" / "join_keys.md"
BEELINK_HOST = "beelink"
BEELINK_ROOT = "/home/polo/rodado"

# A column has to show up in at least this many datasets to be auto-documented.
# Below that it is only in the file if it was curated or bridged by hand.
MIN_DATASETS = 2

# physical parquet type -> what you see in DuckDB
TYPE_MAP = {
    "BYTE_ARRAY": "VARCHAR",
    "FIXED_LEN_BYTE_ARRAY": "VARCHAR",
    "INT64": "BIGINT",
    "INT32": "INTEGER",
    "INT96": "TIMESTAMP",
    "DOUBLE": "DOUBLE",
    "FLOAT": "FLOAT",
    "BOOLEAN": "BOOLEAN",
}

# ---------------------------------------------------------------------------
# Join knowledge — loaded from docs/context/bridges.yaml
# ---------------------------------------------------------------------------
# All of this used to be inline constants right here: AUTO_DENY, CATEGORIES,
# CURATED and the three bridge lists. It moved into YAML so `mcp_server.py`
# can serve the join expressions as data — before, the only way to reach them
# was to regex-slice the markdown that this script renders, so a tested
# expression like `lpad(CAST(codIBGE AS VARCHAR), 7, '0')` reached the model as
# prose to copy by hand.
#
# The shapes rebuilt below are the ones the renderers already expected; keep
# them in step with the YAML keys.

BRIDGES = REPO / "docs" / "context" / "bridges.yaml"


def load_bridges():
    if not BRIDGES.exists():
        sys.exit(f"{BRIDGES} not found — it is the source of truth for this script.")
    doc = yaml.safe_load(BRIDGES.read_text(encoding="utf-8"))

    categories = [(c["id"], c["title"], c["blurb"]) for c in doc["categories"]]
    auto_deny = set(doc["auto_deny"])

    curated = {}
    for col, e in doc["concepts"].items():
        entry = {"cat": e["category"]}
        if "description" in e:
            entry["desc"] = e["description"]
        if "canonical_table" in e:
            entry["ref"] = e["canonical_table"]
        if "notes" in e:
            entry["notes"] = e["notes"]
        if "example_sql" in e:
            entry["example"] = e["example_sql"]
        curated[col] = entry

    mun = [dict(tabela=b["table"], coluna=b["column"], formato=b["format"],
                recipe=b["expr"], verificado=b["verified"])
           for b in doc["bridges"]["municipio"]]
    uf = [(b["table"], b["column"], b["description"]) for b in doc["bridges"]["uf"]]
    ident = [(b["table"], b["column"], b["description"])
             for b in doc["bridges"]["identity"]]
    return categories, auto_deny, curated, mun, uf, ident


(CATEGORIES, AUTO_DENY, CURATED,
 MUNICIPIO_BRIDGES, UF_BRIDGES, IDENTITY_BRIDGES) = load_bridges()


# ---------------------------------------------------------------------------
# Auto-discovery
# ---------------------------------------------------------------------------

KEYISH = re.compile(
    r"^(id_|cod|cnpj|cpf|sigla|nome_|chave|nu_|cd_|co_|cnae|cbo|ncm|cid_|cep|"
    r"ano|mes|data|trimestre|semestre|year|month|date|matricula|inscricao|registro)",
    re.I,
)


def load_schema():
    if not SRC.exists():
        sys.exit(f"{SRC} not found — run scripts/gera_schemas.py first.")
    data = json.loads(SRC.read_text(encoding="utf-8"))
    return data["_meta"], data["tables"]


def index_columns(tables):
    """lower(column) -> {tables, datasets, types, spellings}

    Keyed case-insensitively on purpose: DuckDB resolves unquoted identifiers
    that way, so `ano` and `Ano` are the same join key in practice — and
    `mcp_server` indexes this file by lowercased column name, so emitting both
    as separate sections would make one silently shadow the other.
    """
    idx = defaultdict(lambda: {"tables": [], "datasets": set(), "types": Counter(),
                               "spellings": Counter(),
                               "type_tables": defaultdict(list)})
    for tid, meta in tables.items():
        dataset = tid.split(".", 1)[0]
        for col in meta.get("columns", []):
            entry = idx[col["name"].lower()]
            typ = TYPE_MAP.get(col.get("type", ""), col.get("type", "?"))
            entry["tables"].append(tid)
            entry["datasets"].add(dataset)
            entry["types"][typ] += 1
            entry["type_tables"][typ].append(tid)
            entry["spellings"][col["name"]] += 1
    return idx


def probe_duplicated_tables():
    """Table dirs on beelink holding a leftover tmp*.parquet from an aborted sync.

    Both the generated DuckDB views and any `*.parquet` glob read the leftover
    alongside the real export, so those tables return every row twice.
    """
    cmd = ["ssh", BEELINK_HOST,
           f"find {BEELINK_ROOT} -maxdepth 3 -name 'tmp*.parquet' -printf '%h\\n'"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except Exception as exc:                                  # noqa: BLE001
        print(f"  ! duplicate probe failed: {exc}", file=sys.stderr)
        return None
    if out.returncode != 0:
        print(f"  ! duplicate probe failed: {out.stderr.strip()[:200]}", file=sys.stderr)
        return None
    prefix = BEELINK_ROOT.rstrip("/") + "/"
    dirs = sorted(
        line[len(prefix):].replace("/", ".", 1)
        for line in out.stdout.split("\n") if line.startswith(prefix)
    )
    return dirs


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def auto_desc(col):
    """One line for an auto-detected key, from the shape of its name.

    Most of the long tail is a hub key wearing a role suffix — saying which hub
    it resolves to is the whole value of listing it.
    """
    if col in ("chave", "id_tabela", "nome_coluna"):
        return ("Part of the `dicionario` composite key "
                "`(id_tabela, nome_coluna, chave) -> valor` that decodes coded "
                "columns inside a dataset — see gotcha 6 at the top of this file.")
    if col.startswith("id_municipio"):
        return ("Role-qualified `id_municipio` — same 7-digit IBGE code, joins "
                "`br_bd_diretorios_brasil.municipio` directly.")
    if col.startswith("sigla_uf"):
        return "Role-qualified `sigla_uf` — same two-letter state code."
    if col.startswith("cpf"):
        return ("A CPF under a role name — see `cpf` for the masking caveats "
                "before joining on it.")
    if col.startswith("cnpj") or col.startswith("cpf_cnpj"):
        return "A CNPJ under a role name — normalize as described under `cnpj`."
    if col.startswith("cnae"):
        return "A CNAE activity code — decode with `br_bd_diretorios_brasil.cnae_2`."
    if col.startswith("cid_"):
        return "An ICD-10 code — decode with `br_bd_diretorios_brasil.cid_10`."
    if col.startswith(("data_", "ano_", "mes_")):
        return "Date/period column. Shared name, but check the type before joining."
    if col.startswith("nome_"):
        return "Name column — usable as a fallback key after `upper(strip_accents(...))`."
    if col.startswith("id_"):
        return "Identifier shared across datasets."
    return "Shared column that looks like a key."


def fmt_types(types, type_tables):
    """`VARCHAR` in 321 tables · `BIGINT` in 1 (br_x.y) — the odd one out named.

    A single table storing the shared key under a different type is exactly the
    join that silently returns nothing, so it is worth naming.
    """
    ranked = types.most_common()
    parts = []
    for typ, n in ranked:
        part = f"`{typ}` in {n} table{'s' if n != 1 else ''}"
        if len(ranked) > 1 and n <= 3:
            part += " (" + ", ".join(f"`{t}`" for t in sorted(type_tables[typ])) + ")"
        parts.append(part)
    text = " · ".join(parts)
    if len(ranked) > 1:
        text += " — **cast explicitly when joining across them**"
    return text


def render_key(col, info, curated, level=3):
    """One `### \\`col\\` — N tables` section."""
    tables, datasets = info["tables"], sorted(info["datasets"])
    max_tables = 24 if curated else 12
    out = [f"{'#' * level} `{col}` — {len(tables)} table{'s' if len(tables) != 1 else ''}", ""]
    if curated:
        out += [curated["desc"], ""]
        ref = curated.get("ref")
        if ref:
            out.append(f"**Reference table:** {ref if ref.startswith('—') else '`' + ref + '`'}")
            out.append("")
    else:
        out += [auto_desc(col.lower()), ""]
    others = [s for s, _ in info["spellings"].most_common()[1:]]
    if others:
        out.append("**Also spelled:** " + ", ".join(f"`{s}`" for s in others)
                   + " — the same key; DuckDB matches unquoted identifiers "
                     "case-insensitively.")
        out.append("")
    out.append(f"**Type:** {fmt_types(info['types'], info['type_tables'])}")
    out.append("")
    out.append(f"**Datasets ({len(datasets)}):** " + ", ".join(f"`{d}`" for d in datasets))
    out.append("")
    shown = tables if len(tables) <= max_tables else tables[:max_tables]
    label = ("**Tables:** " if len(tables) <= max_tables
             else f"**Tables (first {max_tables} of {len(tables)}):** ")
    out.append(label + ", ".join(f"`{t}`" for t in shown))
    out.append("")
    for note in (curated or {}).get("notes", []):
        out.append(f"- {note}")
    if (curated or {}).get("notes"):
        out.append("")
    if (curated or {}).get("example"):
        out += ["```sql", curated["example"], "```", ""]
    return out


def render(meta, tables, idx, duplicated):
    total_tables = len(tables)
    total_datasets = len({t.split(".", 1)[0] for t in tables})
    curated_cols = {c for c in CURATED if c in idx}
    auto_cols = {
        c for c, i in idx.items()
        if c not in curated_cols
        and len(i["datasets"]) >= MIN_DATASETS
        and KEYISH.match(c)
        and c not in AUTO_DENY
        and not re.fullmatch(r"v\d{3}", c)
    }
    # display name = the spelling most tables use
    display = {c: idx[c]["spellings"].most_common(1)[0][0]
               for c in curated_cols | auto_cols}
    documented = curated_cols | auto_cols

    L = [
        "# Join Key Reference",
        "",
        f"How the {total_tables} tables of the mirror connect to each other: the "
        f"columns they share, the columns that mean the same thing under a "
        f"different name, and the conversion each one needs.",
        "",
        f"Generated by `scripts/gera_join_keys.py` from `schemas.json` "
        f"({total_datasets} datasets, {total_tables} tables, "
        f"{date.today().isoformat()}). Do not edit by hand — regenerate.",
        "",
        f"{len(documented)} join columns documented: {len(curated_cols)} curated, "
        f"{len(auto_cols)} auto-detected (shared by {MIN_DATASETS}+ datasets), "
        f"plus {len(MUNICIPIO_BRIDGES)} municipality bridges, {len(UF_BRIDGES)} "
        f"UF bridges and {len(IDENTITY_BRIDGES)} CNPJ/CPF bridges for sources "
        f"that name the key differently.",
        "",
        "## Read this before joining anything",
        "",
    ]

    if duplicated:
        dup_dirs = ", ".join(f"`{d}`" for d in duplicated)
        L += [
            f"**1. {len(duplicated)} tables return every row twice.** An aborted "
            "sync left a `tmp*.parquet` next to the real export, and both the "
            "generated views and any `*.parquet` glob read both files. This hits "
            "almost the whole `br_bd_diretorios_brasil` directory — the tables "
            "this file tells you to join against:",
            "",
            "| table | rows | distinct keys |",
            "|---|---|---|",
            "| `br_bd_diretorios_brasil.municipio` | 11.142 | 5.571 |",
            "| `br_bd_diretorios_brasil.uf` | 54 | 27 |",
            "| `br_bd_diretorios_brasil.escola` | 436.234 | 218.117 |",
            "| `br_bd_diretorios_brasil.cid_10` | 24.954 | 12.477 |",
            "| `br_bd_diretorios_brasil.cbo_2002` | 5.624 | 2.812 |",
            "| `br_bd_diretorios_brasil.cnae_2` | 2.712 | 1.356 |",
            "",
            "It is not only a join problem: fact tables are in the list too "
            "(`br_anatel_banda_larga_fixa.densidade_municipio`, "
            "`br_bndes_operacoes_contratadas.operacoes_nao_automaticas`, most "
            "of `br_camara_dados_abertos`), so a plain `count(*)` or `sum()` on "
            "those is already doubled. The affected names run alphabetically "
            "from `br_abrinq_oca` to `br_camara_dados_abertos`, which is what an "
            "interrupted sync looks like.",
            "",
            "Until the leftovers are removed, join against a deduped subquery "
            "(`SELECT DISTINCT …`) — every example in this file does. "
            "`br_bd_diretorios_brasil.cep` is *not* affected.",
            "",
            f"<details><summary>All {len(duplicated)} affected tables</summary>",
            "",
            dup_dirs,
            "",
            "</details>",
            "",
        ]
    else:
        L += [
            "**1. Check for duplicated tables.** An aborted sync can leave a "
            "`tmp*.parquet` next to the real export, and both the views and any "
            "`*.parquet` glob then read both files, returning every row twice. "
            "This probe did not run for this build "
            "(`find ~/rodado -name 'tmp*.parquet'` on beelink lists them).",
            "",
        ]

    L += [
        "**2. `br_bd_diretorios_brasil.empresa` is empty** (0 rows). It used to "
        "be this file's CNPJ reference. Use `br_me_cnpj.estabelecimentos` "
        "(14-digit `cnpj`, one row per branch) or `br_me_cnpj.empresas` "
        "(8-digit `cnpj_basico`, one row per company).",
        "",
        "**3. Codes are strings.** `id_municipio`, `cnpj`, `cep` and friends are "
        "VARCHAR with meaningful leading zeros. A source that stored them as a "
        "number (or as a float — `2927408.0`) has to be padded back before it "
        "will match. Every bridge below states the exact expression.",
        "",
        "**4. Filter partitions first.** `ano`, `mes` and `sigla_uf` are the "
        "partition columns; a join without them scans the whole table.",
        "",
        "**5. Six datasets have no view** in `basedosdados.duckdb` — "
        "`br_cgu_garantia_safra`, `br_cgu_pe_de_meia`, `br_cgu_seguro_defeso`, "
        "`br_cgu_viagens`, `br_ibama_embargos`, `br_mjsp_sisdepen`. Read them "
        "with `read_parquet('~/rodado/<dataset>/<table>/*.parquet')`. "
        "`br_ms_sipni_*` and `politicos` are the opposite case: native tables "
        "inside the `.duckdb` file with no parquet directory.",
        "",
        "**6. Every dataset with coded columns carries a `dicionario` table** "
        f"({sum(1 for t in tables if t.endswith('.dicionario'))} of them). It "
        "decodes any coded column of that dataset:",
        "",
        "```sql",
        "SELECT c.chave, c.valor, count(*)",
        "FROM br_me_caged.microdados_movimentacao m",
        "JOIN br_me_caged.dicionario c",
        "  ON c.id_tabela = 'microdados_movimentacao'",
        " AND c.nome_coluna = 'tipo_movimentacao'",
        " AND c.chave = CAST(m.tipo_movimentacao AS VARCHAR)",
        "WHERE m.ano = 2023",
        "GROUP BY 1, 2",
        "```",
        "",
    ]

    # ---- sections by category
    by_cat = defaultdict(list)
    for col in curated_cols:
        by_cat[CURATED[col].get("cat", "outros")].append(col)
    for col in auto_cols:
        by_cat["outros"].append(col)

    for cat, title, blurb in CATEGORIES:
        cols = sorted(by_cat.get(cat, []),
                      key=lambda c: (-len(idx[c]["tables"]), c))
        if not cols:
            continue
        L += [f"## {title}", "", blurb, ""]

        # `mcp_server.get_join_keys()` slices from one h3 to the next, so a
        # bridge table has to sit inside the section of the key it belongs to:
        # emitted right after that column, never at the end of the category.
        for col in cols:
            L += render_key(display[col], idx[col], CURATED.get(col))
            if col == "id_municipio":
                L += render_municipio_bridges()
            elif col == "sigla_uf":
                L += render_bridge_table(
                    "Same key, other names — UF",
                    ["table", "column", "format / conversion"],
                    [(f"`{t}`", f"`{c}`", d) for t, c, d in UF_BRIDGES],
                )
            elif col == "cnpj":
                L += render_bridge_table(
                    "Same key, other names — CNPJ / CPF",
                    ["table", "column", "format / conversion"],
                    [(f"`{t}`", f"`{c}`", d) for t, c, d in IDENTITY_BRIDGES],
                )

    return "\n".join(L).rstrip() + "\n"


def render_municipio_bridges():
    rows = [
        (f"`{b['tabela']}`", f"`{b['coluna']}`", b["formato"],
         f"`{b['recipe']}`" if "\n" not in b["recipe"] and not b["recipe"].startswith("unusable")
         else b["recipe"], b["verificado"])
        for b in MUNICIPIO_BRIDGES
    ]
    out = [
        "### Municipality columns under another name",
        "",
        "Independently scraped sources rarely use `id_municipio`. Each "
        "row below is the expression that brings that column back to the "
        "directory (aliased `m`, and deduped — see gotcha 1). *verified* is what "
        "the expression actually matched when it was run on beelink; those are "
        "joined-row counts against the duplicated directory, so roughly twice "
        "the municipality count.",
        "",
        "| table | column | stored as | join expression | verified |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        cells = [c.replace("|", "\\|").replace("\n", "<br>") for c in r]
        out.append("| " + " | ".join(cells) + " |")
    out += [
        "",
        "Role-qualified municipality columns (same 7-digit IBGE code, different "
        "meaning) join to `id_municipio` directly — pick the one that answers "
        "the question:",
        "",
        "| dataset | columns |",
        "|---|---|",
        "| `br_ms_sim.microdados` | `id_municipio_residencia`, `id_municipio_ocorrencia`, `id_municipio_naturalidade`, `id_municipio_svo_iml` |",
        "| `br_ms_sinasc.microdados` | `id_municipio_residencia`, `id_municipio_nascimento`, `id_municipio_mae` |",
        "| `br_ms_sinan.microdados_dengue` | `id_municipio_notificacao`, `id_municipio_residencia`, `id_municipio_infeccao`, `id_municipio_internacao` |",
        "| `br_ms_sih.aihs_reduzidas` | `id_municipio_paciente`, `id_municipio_estabelecimento`, `id_municipio_gestor` |",
        "| `br_ms_sia.psicossocial` | `id_municipio_residencia_paciente` |",
        "| `br_inep_enem.microdados` | `id_municipio_residencia`, `id_municipio_escola`, `id_municipio_prova` |",
        "| `br_mec_sisu.microdados` | `id_municipio_candidato`, `id_municipio_campus` |",
        "| `br_me_rais.microdados_vinculos` | `id_municipio_trabalho` |",
        "| `br_cgu_emendas_parlamentares.microdados` | `id_municipio_gasto` |",
        "| `br_camara_dados_abertos.deputado` | `id_municipio_nascimento` |",
        "| `br_tse_eleicoes.receitas_*` | `id_municipio_tse_doador`, `id_municipio_tse_fornecedor` (TSE numbering) |",
        "| `br_bd_vizinhanca.municipio` | `id_municipio_1`, `id_municipio_2` — the adjacency pair |",
        "",
    ]
    return out


def render_bridge_table(title, headers, rows):
    out = [f"### {title}", "", "| " + " | ".join(headers) + " |",
           "|" + "---|" * len(headers)]
    for r in rows:
        out.append("| " + " | ".join(c.replace("|", "\\|") for c in r) + " |")
    out.append("")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-probe", action="store_true",
                    help="skip the ssh check for duplicated (tmp*.parquet) tables")
    args = ap.parse_args()

    meta, tables = load_schema()
    idx = index_columns(tables)
    duplicated = None if args.no_probe else probe_duplicated_tables()

    DST.write_text(render(meta, tables, idx, duplicated), encoding="utf-8")

    print(f"{DST.relative_to(REPO)}")
    print(f"  source   : schemas.json ({meta.get('total_tables')} tables)")
    print(f"  sections : {sum(1 for line in DST.read_text().split(chr(10)) if line.startswith('### `'))}")
    if duplicated is not None:
        print(f"  duplicated tables on beelink: {len(duplicated)}")
    print(f"  size     : {DST.stat().st_size / 1024:.1f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
