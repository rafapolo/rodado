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
    false_friends = doc["false_friends"]
    auto_deny = set(false_friends)

    aliases = doc.get("concept_aliases", {})

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

    def rica(grupo):
        """Ponte com receita: formato, expressão e o que casou quando foi rodada."""
        return [dict(tabela=b["table"], coluna=b["column"], formato=b["format"],
                     recipe=b["expr"], verificado=b["verified"])
                for b in doc["bridges"].get(grupo, [])]

    def simples(grupo):
        return [(b["table"], b["column"], b["description"])
                for b in doc["bridges"].get(grupo, [])]

    mun = rica("municipio")
    pais = rica("pais")
    uf = simples("uf")
    ident = simples("identity")
    return (categories, auto_deny, curated, mun, uf, ident, pais,
            false_friends, aliases, index_bridged_columns(doc))


# A bridge's `column` field is prose as often as it is an identifier:
# `cnpj_estabelecimento / cnpj_mantenedora`, `ing_nm_municipio + ing_sg_ufmunicipio`,
# `id_municipio_campus (município do campus …)`, `"CPF_CNPJ"`. Split it back into
# the identifiers it names so the auto path can tell "this column already has a
# hand-written recipe" from "nobody has looked at this one".
_BRIDGE_COL_SPLIT = re.compile(r"\s*(?:/|,|\+)\s*")
_BRIDGE_COL_OK = re.compile(r"^[a-z_][a-z0-9_]*$")


def index_bridged_columns(doc):
    """lower(column) -> [{table, format, expr}] for every column bridges.yaml curates.

    Why the auto path has to know: `SG_UF` in `br_ms_sinan_violencia` *looks*
    like a role-qualified `sigla_uf` and is a numeric IBGE code; the three
    `id_municipio_*` columns of `br_ms_sih.aihs_reduzidas` look like the 7-digit
    standard and are 6-digit. Describing either from the shape of its name is
    how you get a join that returns 0 rows without an error. When a bridge
    exists it is the description.
    """
    out = defaultdict(list)
    for group in doc.get("bridges", {}).values():
        for b in group:
            raw = str(b.get("column", ""))
            raw = re.sub(r"\([^)]*\)", " ", raw)          # drop parentheticals
            # `a + b` means the recipe is about the *pair* (SICAF matches on
            # nomeMunicipio AND ufSigla together), so neither half owns it. Note
            # the column as bridged, but let a bridge that names it alone win.
            composite = "+" in raw
            for tok in _BRIDGE_COL_SPLIT.split(raw):
                tok = tok.strip().strip("`\"'").lower()
                if _BRIDGE_COL_OK.match(tok):
                    out[tok].append({"table": b.get("table", ""),
                                     "format": b.get("format") or b.get("description", ""),
                                     "expr": b.get("expr", ""),
                                     "composite": composite})
    return {k: sorted(v, key=lambda e: e["composite"]) for k, v in out.items()}


(CATEGORIES, AUTO_DENY, CURATED,
 MUNICIPIO_BRIDGES, UF_BRIDGES, IDENTITY_BRIDGES, PAIS_BRIDGES,
 FALSE_FRIENDS, CONCEPT_ALIASES, BRIDGED_COLUMNS) = load_bridges()


# ---------------------------------------------------------------------------
# Auto-discovery
# ---------------------------------------------------------------------------

KEYISH = re.compile(
    r"^(id_|cod|cnpj|cpf|sigla|nome_|chave|nu_|cd_|co_|cnae|cbo|ncm|cid_|cep|"
    r"ano|mes|data|trimestre|semestre|year|month|date|matricula|inscricao|registro)",
    re.I,
)

# ---------------------------------------------------------------------------
# Hub patterns — the MIN_DATASETS bypass
# ---------------------------------------------------------------------------
# KEYISH + MIN_DATASETS is the right bar for the generic case: "this exact name
# repeats across datasets, so it is probably the same thing". It is the wrong
# bar for a *role-qualified spelling of a hub the file already curates*.
# `sigla_uf_residencia`, `id_municipio_gasto`, `cid_morte_categoria`,
# `cnpj_ofertante` each live in exactly one dataset, so MIN_DATASETS=2 hid all
# of them — yet each is a two-letter state code / 7-digit IBGE code / ICD-10
# code / CNPJ, and saying so costs one line. Worse, KEYISH had no bare `uf`
# pattern at all, so `uf_nascimento`, `origem_uf` and `uf_devedor` were
# invisible at *any* dataset count.
#
# A column matching one of these is documented regardless of how many datasets
# carry it. The generic path is untouched.
#
# Two guards keep metric and flag names out, because the cost of a false
# positive here is a plausible-looking join on a column that is not a key:
#
#   HUB_DENY   — the `indicador_`/`taxa_`/`desp_`/`pct_` families.
#                `desp_tot_saude_pc_uf` (br_ieps_saude) is per-capita health
#                spend *at UF grain*, not a UF code; `indicador_uf_paciente`
#                (br_ms_sih) is a same-state flag; `indicador_cnae_2_0`
#                (the directory) is a validity flag.
#   type set   — what survives on name alone. `capital_uf` is a BIGINT boolean
#                on the municipality directory ("is this the state capital"),
#                not a state code, so the sigla family requires VARCHAR.
#
# Deliberately NOT matched: `_pais$` (in Portuguese `pais` without the accent is
# both "country" and "parents" — `orgao_associacao_pais`,
# `responsaveis_comparecem_reuniao_pais`, and sisdepen's `…_pais_de_gales_…`
# columns are all the wrong sense), and `_uf_pais$`
# (`aeroporto_destino_nome_uf_pais` is free text, already a curated bridge).

HUB_DENY = re.compile(
    r"^(indicador|quantidade|taxa|proporcao|percentual|pct|media|peso|valor|"
    r"desp|total|atu|dsu|had|icg)_",
    re.I,
)

# (hub concept this resolves to, name pattern, required types or None for any)
HUB_PATTERNS = [
    ("sigla_uf", r"^sigla_uf(_.+)?$|^siglauf[a-z]*$|^uf$|^uf_.+$|^uf[a-z]+$|.+_uf$",
     {"VARCHAR"}),
    ("id_uf", r"^id_uf(_.+)?$|^(codigo|cod)_uf$", None),
    ("id_municipio", r"^id_municipio(_.+)?$", None),
    ("municipio", r"^(nome_)?municipio(_.+)?$|^(codigo|cod)_(ibge_)?municipio(_.+)?$",
     {"VARCHAR"}),
    ("cnpj", r"^cnpj(_.+)?$|^cnpj_?cpf(_.+)?$|^cpf_?cnpj(_.+)?$|^numero_cnpj(_.+)?$",
     None),
    ("cpf", r"^cpf(_.+)?$", None),
    ("cep", r"^cep(_.+)?$|^(codigo|cod)_cep(_.+)?$", None),
    ("cnae_2_subclasse", r"^cnae(_.+)?$|.+_cnae$|^(codigo|nome)cnae$", None),
    ("cid_principal_categoria", r"^cid_.+$|^id_cid(_.+)?$", None),
    ("cbo_2002", r"^cbo(_.+)?$|^id_cbo(_.+)?$", None),
    ("id_ncm", r"^id_ncm(_.+)?$|^id_sh4(_.+)?$|^(codigo|cod)_ncm$", None),
    ("id_escola", r"^id_escola(_.+)?$", None),
    ("id_estabelecimento_cnes",
     r"^cnes$|^id_cnes$|^(codigo|cod)_cnes$|^id_estabelecimento_cnes(_.+)?$", None),
    ("id_pais", r"^pais_.+$|^id_pais(_.+)?$|^sigla_pais(_.+)?$|^nome_pais(_.+)?$",
     None),
]
HUB_PATTERNS = [(c, re.compile(p, re.I), t) for c, p, t in HUB_PATTERNS]


def hub_concept(col, info):
    """The curated hub a role-qualified column resolves to, or None."""
    if HUB_DENY.match(col):
        return None
    for concept, pat, types in HUB_PATTERNS:
        if not pat.match(col):
            continue
        if types and not (set(info["types"]) & types):
            return None
        return concept
    return None


def select_join_columns(idx):
    """(curated, shared-name, {role column: hub}) — the file's whole column set.

    `gera_schema_graph.py` builds the Atlas from the same three layers, so this
    lives here and is imported there: a pattern added below shows up on
    rodado.xyz/atlas without a second edit.
    """
    curated = {c for c in CURATED if c in idx}

    def eligible(c):
        return (c not in curated and c not in AUTO_DENY
                and not re.fullmatch(r"v\d{3}", c))

    # generic path: same exact name in MIN_DATASETS+ datasets, meaning inferred
    shared = {c for c, i in idx.items()
              if eligible(c) and len(i["datasets"]) >= MIN_DATASETS and KEYISH.match(c)}
    # hub path: a role-qualified spelling of an already-curated concept,
    # documented at any dataset count — see HUB_PATTERNS for why.
    hub = {c: h for c, i in idx.items() if eligible(c) and (h := hub_concept(c, i))}
    return curated, shared, hub


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

def bridged_desc(col):
    """The description of a column bridges.yaml already curates, or None.

    A bridged column keeps its hand-written story instead of one inferred from
    the shape of its name, because the two disagree exactly where it matters:
    `sg_uf` reads as a state sigla and holds a numeric IBGE code,
    `id_municipio_paciente` reads as the 7-digit standard and holds 6 digits.
    """
    entries = BRIDGED_COLUMNS.get(col)
    if not entries:
        return None
    e = entries[0]
    label = "part of a composite bridge" if e["composite"] else "curated bridge"
    txt = f"**{label.capitalize()}** — {e['format']}"
    if not txt.rstrip().endswith((".", "…")):
        txt += "."
    if e["expr"] and "\n" not in e["expr"] and not e["expr"].startswith("unusable"):
        txt += f" Join with `{e['expr']}`."
    others = sorted({x["table"] for x in entries})
    txt += (" Full row (and what it matched when it was run) in the bridge table "
            f"under its hub — seen in {', '.join('`' + t + '`' for t in others)}.")
    return txt


def auto_desc(col, info=None):
    """One line for an auto-detected key, from the shape of its name.

    Most of the long tail is a hub key wearing a role suffix — saying which hub
    it resolves to is the whole value of listing it.
    """
    bridged = bridged_desc(col)
    if bridged:
        return bridged
    if col in ("chave", "id_tabela", "nome_coluna"):
        return ("Part of the `dicionario` composite key "
                "`(id_tabela, nome_coluna, chave) -> valor` that decodes coded "
                "columns inside a dataset — see gotcha 6 at the top of this file.")
    # `id_municipio_6_*` is the 6-digit variant, not the 7-digit standard: the
    # naive join against `id_municipio` returns 0 rows and no error.
    if col.startswith("id_municipio_6"):
        return ("Role-qualified `id_municipio_6` — the **6-digit** IBGE code, not "
                "the 7-digit standard. Join `br_bd_diretorios_brasil.municipio` on "
                "`id_municipio_6`; against `id_municipio` it silently matches nothing.")
    if col.startswith("id_municipio_tse"):
        return ("Role-qualified municipality code in **TSE numbering**, not IBGE — "
                "cross through `br_bd_diretorios_brasil.municipio.id_municipio_tse`.")
    if col.startswith("id_municipio_rf"):
        return ("Role-qualified municipality code in **Receita Federal numbering** "
                "(4 digits) — cross through "
                "`br_bd_diretorios_brasil.municipio.id_municipio_rf`.")
    if col.startswith("id_municipio"):
        return ("Role-qualified `id_municipio` — same 7-digit IBGE code, joins "
                "`br_bd_diretorios_brasil.municipio` directly.")
    if col.startswith("nome_municipio") or col.startswith("municipio"):
        return ("Municipality by name, not by code — usable as a fallback key after "
                "`upper(strip_accents(...))`, and only together with a UF column: "
                "names repeat across states.")
    if col.startswith(("codigo_municipio", "cod_municipio", "codigo_ibge_municipio")):
        return ("Municipality IBGE code under another name — check the digit count "
                "and pad (`lpad(CAST(x AS VARCHAR), 7, '0')`) before joining "
                "`br_bd_diretorios_brasil.municipio`.")
    if col == "nome_uf" or col.startswith("nome_uf"):
        return ("State by **full name**, not the two-letter sigla — join "
                "`br_bd_diretorios_brasil.uf.nome`, never `sigla_uf`.")
    if col.startswith("id_uf") or col in ("codigo_uf", "cod_uf"):
        return ("Role-qualified `id_uf` — the numeric IBGE state code (11–53), not "
                "the sigla. Joins `br_bd_diretorios_brasil.uf.id_uf`.")
    if (col.startswith(("sigla_uf", "siglauf", "uf_", "uf"))
            or col.endswith("_uf")):
        return ("Role-qualified `sigla_uf` — same two-letter state code, joins "
                "`br_bd_diretorios_brasil.uf` (whose own column is spelled `sigla`).")
    if col.startswith("cpf"):
        return ("A CPF under a role name — see `cpf` for the masking caveats "
                "before joining on it.")
    if col.startswith(("cnpj", "cpf_cnpj", "numero_cnpj", "cnpjcpf", "cpfcnpj")):
        return "A CNPJ under a role name — normalize as described under `cnpj`."
    if col.startswith("cep") or col.startswith("codigo_cep"):
        return ("A CEP under a role name — 8 digits with meaningful leading zeros; "
                "decode with `br_bd_diretorios_brasil.cep`.")
    if col.startswith(("cnae", "codigocnae", "nomecnae")) or col.endswith("_cnae"):
        return "A CNAE activity code — decode with `br_bd_diretorios_brasil.cnae_2`."
    if col.startswith(("cid_", "id_cid")):
        return "An ICD-10 code — decode with `br_bd_diretorios_brasil.cid_10`."
    if col.startswith(("cbo", "id_cbo")):
        return ("A CBO-2002 occupation code — decode with "
                "`br_bd_diretorios_brasil.cbo_2002`.")
    if col.startswith(("id_ncm", "codigo_ncm", "id_sh4")):
        return ("An NCM/SH4 product code — decode with "
                "`br_bd_diretorios_mundo.ncm` / `.sh4`.")
    if col.startswith("id_escola"):
        return ("A school INEP code under a role name — decode with "
                "`br_bd_diretorios_brasil.escola`.")
    if col.startswith(("cnes", "id_cnes", "codigo_cnes", "id_estabelecimento_cnes")):
        return ("A CNES health-facility code under a role name — decode with "
                "`br_ms_cnes.estabelecimento`.")
    if col.startswith(("pais_", "id_pais", "sigla_pais", "nome_pais")):
        return ("A country under a role name — `br_bd_diretorios_mundo.pais` is the "
                "hub, and it renamed its columns in 2026-08 (see `sigla_pais_iso3`).")
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
        desc = auto_desc(col.lower(), info)
        # A code hub stored as a number has lost its leading zeros; every one of
        # these is a join that returns fewer rows than it should, quietly.
        if (not set(info["types"]) & {"VARCHAR"}
                and re.match(r"^(id_municipio|codigo_municipio|cod_municipio|"
                             r"codigo_ibge_municipio|cnpj|cpf|cep|cnae|codigocnae|"
                             r"cid_|cbo|codigo_cnes|id_estabelecimento_cnes)",
                             col.lower())):
            desc += (" Stored here as a **number**: `lpad(CAST(x AS VARCHAR), n, '0')` "
                     "before joining, or the leading zeros never come back.")
        out += [desc, ""]
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
    curated_cols, shared_cols, hub_cols = select_join_columns(idx)
    auto_cols = shared_cols | set(hub_cols)
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
        f"{len(shared_cols - set(hub_cols))} auto-detected by shared name "
        f"({MIN_DATASETS}+ datasets), {len(hub_cols)} auto-detected as a "
        f"role-qualified spelling of a curated hub (`sigla_uf_residencia`, "
        f"`id_municipio_gasto`, `cid_morte_categoria`… — documented at any dataset "
        f"count, because the hub they resolve to already is), "
        f"plus {len(MUNICIPIO_BRIDGES)} municipality bridges, {len(UF_BRIDGES)} "
        f"UF bridges, {len(PAIS_BRIDGES)} country "
        f"{'bridge' if len(PAIS_BRIDGES) == 1 else 'bridges'} and "
        f"{len(IDENTITY_BRIDGES)} CNPJ/CPF bridges for sources "
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
    elif duplicated is None:
        L += [
            "**1. Check for duplicated tables.** An aborted sync can leave a "
            "`tmp*.parquet` next to the real export, and both the views and any "
            "`*.parquet` glob then read both files, returning every row twice. "
            "This probe did not run for this build "
            "(`find ~/rodado -name 'tmp*.parquet'` on beelink lists them).",
            "",
        ]
    else:
        L += [
            "**1. No duplicated tables.** The probe ran for this build and found "
            "no `tmp*.parquet` left over on beelink, so no table returns every "
            "row twice and the examples below join directly. The 80 leftovers "
            "from the aborted 2026-07-05 sync were triaged and removed on "
            "2026-08-23.",
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

    L += render_false_friends()

    # ---- sections by category
    by_cat = defaultdict(list)
    for col in curated_cols:
        by_cat[CURATED[col].get("cat", "outros")].append(col)
    for col in auto_cols:
        # A role-qualified column belongs beside its hub, not in a 200-row
        # "outros" bucket: `sigla_uf_residencia` is geography, `cnpj_ofertante`
        # is identity. The generic shared-name path has no hub, so it stays.
        hub = hub_cols.get(col)
        by_cat[CURATED.get(hub, {}).get("cat", "outros") if hub else "outros"].append(col)

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
                L += render_municipio_bridges(tables)
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
            elif col == "sigla_pais_iso3":
                L += render_pais_bridges()

    return "\n".join(L).rstrip() + "\n"


def rich_bridge_rows(bridges):
    """As linhas da tabela de pontes-com-receita, escapadas para markdown."""
    return [
        (f"`{b['tabela']}`", f"`{b['coluna']}`", b["formato"],
         f"`{b['recipe']}`" if "\n" not in b["recipe"] and not b["recipe"].startswith("unusable")
         else b["recipe"], b["verificado"])
        for b in bridges
    ]


def rich_bridge_table(rows):
    out = ["| table | column | stored as | join expression | verified |",
           "|---|---|---|---|---|"]
    for r in rows:
        cells = [c.replace("|", "\\|").replace("\n", "<br>") for c in r]
        out.append("| " + " | ".join(cells) + " |")
    return out


def render_pais_bridges():
    """A ponte de país existe porque o hub renomeou a coluna, não porque o
    formato do dado difere — é o único caso desses no arquivo."""
    if not PAIS_BRIDGES:
        return []
    return [
        "### Country columns under another name",
        "",
        "`br_bd_diretorios_mundo.pais` is the country hub, and in 2026-08-23 Base dos "
        "Dados renamed its columns — `sigla_pais_iso3` became `sigla_iso3`, `nome` "
        "became `nome_pt`, `id_pais_m49` became `id_m49`. The mirror followed the "
        "source. What consumes the key did *not* get renamed, so the two ends now "
        "spell the same concept differently and the naive equality raises "
        "`column not found`. Join with the expression below (hub aliased `p`).",
        "",
        *rich_bridge_table(rich_bridge_rows(PAIS_BRIDGES)),
        "",
    ]


_ROLE_MUN = re.compile(r"^id_municipio_(?!6$|tse$|rf$|bcb$)", re.I)


def role_municipio_rows(tables):
    """The role-qualified `id_municipio_*` columns, per table, read off the schema.

    This used to be a hand-written markdown table. It drifted: it was missing
    `br_bcb_sicor`, `br_ms_cnes.profissional`,
    `br_ms_sih.servicos_profissionais` and the whole
    `br_ms_sinan.microdados_influenza_srag` row, and it claimed
    `br_ms_sih.aihs_reduzidas` joins `id_municipio` directly while the bridge
    table three lines above said its codes are 6-digit. Generating it from
    `schemas.json` is the only way that stops happening.
    """
    per_table = defaultdict(list)
    for tid, meta in tables.items():
        for col in meta.get("columns", []):
            if _ROLE_MUN.match(col["name"]):
                per_table[tid].append(col["name"])
    rows = []
    for tid in sorted(per_table):
        cols = []
        for c in per_table[tid]:
            low = c.lower()
            # The name is not enough: br_ms_sih spells its 6-digit codes
            # `id_municipio_paciente`, with nothing in the name to say so. The
            # bridge's own expression is what settles it.
            bridged = BRIDGED_COLUMNS.get(low, [])
            expr = " ".join(e["expr"] for e in bridged)
            if low.startswith("id_municipio_6") or "id_municipio_6" in expr:
                cols.append(f"`{c}` (6-digit)")
            elif low.startswith("id_municipio_tse") or "id_municipio_tse" in expr:
                cols.append(f"`{c}` (TSE numbering)")
            elif low.startswith("id_municipio_rf") or "id_municipio_rf" in expr:
                cols.append(f"`{c}` (Receita Federal numbering)")
            else:
                cols.append(f"`{c}`")
        rows.append((f"`{tid}`", ", ".join(cols)))
    return rows


def render_municipio_bridges(tables):
    rows = rich_bridge_rows(MUNICIPIO_BRIDGES)
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
        *rich_bridge_table(rows),
    ]
    role_rows = role_municipio_rows(tables)
    out += [
        "",
        "Role-qualified municipality columns — the 7-digit IBGE code under a "
        "table-specific role name, joining `id_municipio` directly unless marked "
        "otherwise. Each also has its own section below (they are auto-detected "
        "as `id_municipio` role variants, so this table cannot go stale). Pick "
        "the role that answers the question — `id_municipio_ocorrencia` and "
        "`id_municipio_residencia` give different answers to the same mortality "
        "question:",
        "",
        "| table | columns |",
        "|---|---|",
    ]
    out += [f"| {t} | {c} |" for t, c in role_rows]
    out += [
        "",
        "`(6-digit)` above does **not** join `id_municipio`: use "
        "`m.id_municipio_6`, or the 7-digit join returns 0 rows with no error. "
        "`(TSE numbering)` is not IBGE at all — cross through "
        "`m.id_municipio_tse`.",
        "",
    ]
    return out


def render_false_friends():
    """Columns that look like keys and are not — with the reason, not just a drop."""
    out = [
        "## Columns that look like keys and are not",
        "",
        "These appear in two or more datasets under the same name and mean something "
        "different in each, so they are deliberately kept out of the sections below. "
        "Joining on one of them produces a large, plausible, wrong result.",
        "",
        "| column | why it is not a join key | where |",
        "|---|---|---|",
    ]
    for col, e in FALSE_FRIENDS.items():
        out.append(f"| `{col}` | {e['reason']} | {e['seen_in']} |")
    out.append("")
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
