#!/usr/bin/env python3
"""schemas.json + dicionario_coverage.json + bridges.yaml + hierarchies.yaml
+ beelink -> docs/context/schema_dict_status.json

    python3 scripts/gera_schema_dict_status.py

Estágios 1+2 de tasks/plan/generate-full-schema-dict.md: toda coluna
STRING/INTEGER que não está em `dicionario_coverage.json` (i.e. sem decode
vivo em `{dataset}.dicionario`) sai desta varredura com uma de cinco
etiquetas — a mesma escala que motivou o plano: `br_ms_sim.circunstancia_obito`
subcontava suicídio (749 contra 789 reais, RJ 2020) sem NENHUM mecanismo
avisando, porque hoje a alternativa a "documentado" não é "menos
documentado", é silêncio total.

Etiquetas (ver o plano pra definição completa):
  dicionario_disponivel    — já coberto por dicionario_coverage.json (fora
                              do escopo deste arquivo, citado só por
                              completude no _meta)
  padrao_externo            — nome bate com um concept/hierarquia já
                              documentado (bridges.yaml `concepts`,
                              `concept_aliases`, ou `hierarchies.yaml`)
  documentado_em_outro_lugar — nome está em bridges.yaml `coded_differently`
                              (mesmo sem enumerar código->label, o
                              comportamento já está escrito), ou aparece
                              literalmente no `provenance_notes` do dataset
  nao_e_codigo               — o valor bruto já É a informação: ou o nome
                              indica um campo autoexplicativo (calendário,
                              medida, contínuo) sem precisar de glossário, ou
                              a cardinalidade medida no beelink é alta demais
                              pra ser um conjunto fechado de códigos
  nao_verificado              — sobrou sem fonte. Candidato real: baixa
                              cardinalidade medida no beelink (<= 100
                              valores distintos), nome não bate com nenhuma
                              fonte já conhecida. Trate como
                              `circunstancia_obito` até prova em contrário.

O critério de "candidato a código" não é um limiar de cardinalidade cru — é
"não dá pra inferir o significado dos VALORES a partir do nome da coluna".
Isso descarta de saída, sem tocar o beelink, qualquer STRING/INTEGER cujo
nome já é a própria explicação (`ano`, `mes`, `latitude`...) ou que já bate
com um concept/hierarquia conhecido — só o que sobra depois desse filtro por
nome paga uma consulta de cardinalidade real.

Limitação conhecida: o match contra `provenance_notes` é best-effort e fraco
— pra dataset espelhado a nota é só um boilerplate ("Espelho do Base dos
Dados..."), não fala de coluna nenhuma; só ajuda pontualmente pra dataset
raspado com nota rica. Não tratar como triagem exaustiva — é o mesmo espírito
de bridges.yaml: "curado, não varrido" (ver o próprio arquivo).

Rerun depois de qualquer sync que mude tabelas, ou depois de estender
bridges.yaml/hierarchies.yaml/dicionario_coverage.json o bastante pra mudar
quem já está coberto.
"""
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO / "docs" / "context" / "basedosdados-schema.json"
DICIONARIO_PATH = REPO / "docs" / "context" / "dicionario_coverage.json"
BRIDGES_PATH = REPO / "docs" / "context" / "bridges.yaml"
HIERARCHIES_PATH = REPO / "docs" / "context" / "hierarchies.yaml"
DST = REPO / "docs" / "context" / "schema_dict_status.json"

BEELINK_HOST = "beelink"
BEELINK_DUCKDB_BIN = "~/bin/duckdb"
BEELINK_DUCKDB_PATH = "~/rodado/basedosdados.duckdb"

CANDIDATE_TYPES = {"STRING", "INTEGER"}
CARDINALITY_THRESHOLD = 100  # distinct values; acima disso não é "código", é dado

# Nome já explica o valor bruto — calendário, medida contínua, coordenada,
# identificador. Nenhuma consulta ao beelink resolveria melhor que o nome.
NAO_E_CODIGO_RE = re.compile(
    r"^(ano|mes|dia|semana|semestre|trimestre|hora|minuto|segundo|turno"
    r"|idade|populacao|quantidade\w*|numero\w*|total\w*|valor\w*|preco\w*"
    r"|custo\w*|area\w*|distancia\w*|latitude|longitude|nota|pontuacao"
    r"|score|percentual\w*|taxa\w*|indice\w*|peso|altura|cep|ddd|cpf\w*"
    r"|cnpj\w*|uuid|url|email|telefone|id|data\w*|\w*_data|\w*_ano"
    r"|competencia|periodo|geometria|localizacao)$"
)

# indicador_obito, flag_erro_corpo_apac, possui_..., tem_..., is_... — o
# CONCEITO é legível no nome mesmo sem saber se a codificação é S/N ou 0/1.
BOOLEAN_FLAG_RE = re.compile(r"^(indicador|flag|possui|tem|is)_\w+$")


# Padrões públicos e estáveis conhecidos por token exato (coluna dividida em
# "_") mesmo quando o nome exato não bate com concepts/hierarchies — pega
# `cnae_fiscal_principal`, `cbo_2002_profissional`, `id_cid_principal_subcategoria`
# etc. sem precisar enumerar cada variante. CBO e NCM ainda não têm entrada em
# hierarchies.yaml (gap real, registrado aqui em vez de tratado como achado
# novo — não é objeto deste script estender hierarchies.yaml).
KNOWN_TOKEN_PATTERNS = {
    "cnae": "CNAE (classificação de atividade econômica) — hierarchies.yaml cnae",
    "cid": "CID-10 (classificação internacional de doenças) — hierarchies.yaml cid10",
    "cbo": "CBO (Classificação Brasileira de Ocupações), padrão público do MTE — não coberto em hierarchies.yaml ainda, mas é padrão externo estável",
    "ncm": "NCM (Nomenclatura Comum do Mercosul) — não coberto em hierarchies.yaml ainda, mas é padrão externo estável",
    "subcategoria": "nível CID-10 — hierarchies.yaml cid10",
    "categoria": "nível CID-10 — hierarchies.yaml cid10",
    "capitulo": "nível CID-10 — hierarchies.yaml cid10",
    "secao": "nível CNAE — hierarchies.yaml cnae",
    "divisao": "nível CNAE — hierarchies.yaml cnae",
    "subclasse": "nível CNAE — hierarchies.yaml cnae",
}


def _norm(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9_]", "", s.lower().strip())


def _query(sql: str, timeout: int = 120) -> list:
    cmd = ["ssh", BEELINK_HOST, f"{BEELINK_DUCKDB_BIN} -json {BEELINK_DUCKDB_PATH}"]
    out = subprocess.run(cmd, input=sql, capture_output=True, text=True, timeout=timeout)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip()[:500])
    stdout = out.stdout.strip()
    return json.loads(stdout) if stdout else []


def load_known_names() -> tuple[set, dict]:
    """Nomes já cobertos por concepts/concept_aliases/hierarchies -> padrão externo."""
    with open(BRIDGES_PATH, encoding="utf-8") as f:
        bridges = yaml.safe_load(f)
    with open(HIERARCHIES_PATH, encoding="utf-8") as f:
        hierarchies = yaml.safe_load(f).get("hierarchies", {})

    padrao_externo: dict[str, str] = {}  # nome normalizado -> fonte legível
    for name, info in bridges.get("concepts", {}).items():
        padrao_externo[_norm(name)] = f"bridges.yaml concepts.{name} -> {info.get('canonical_table', '?')}"
    for table, aliases in bridges.get("concept_aliases", {}).items():
        for local_name, concept in aliases.items():
            padrao_externo[_norm(local_name)] = f"bridges.yaml concept_aliases.{table} -> concept {concept}"
    for hid, hinfo in hierarchies.items():
        for level in hinfo.get("levels", []):
            padrao_externo[_norm(level)] = f"hierarchies.yaml {hid} -> {hinfo.get('table', '?')}"

    coded_differently = {_norm(k): v.get("reason", "") for k, v in bridges.get("coded_differently", {}).items()}
    return padrao_externo, coded_differently


def load_dicionario_covered() -> set:
    with open(DICIONARIO_PATH, encoding="utf-8") as f:
        tables = json.load(f).get("tables", {})
    return {(tid, _norm(c)) for tid, cols in tables.items() for c in cols}


def load_provenance_notes() -> dict:
    """dataset -> provenance_notes (uma nota por dataset, de _rodado_metadata)."""
    sql = """
    SET enable_progress_bar=false;
    SELECT DISTINCT dataset, provenance_notes FROM _rodado_metadata
    WHERE provenance_notes IS NOT NULL;
    """
    try:
        rows = _query(sql)
    except Exception as exc:  # noqa: BLE001
        print(f"  aviso: não consegui buscar provenance_notes ({exc}) — pulando essa checagem", file=sys.stderr)
        return {}
    notes: dict[str, str] = {}
    for row in rows:
        notes[row["dataset"]] = notes.get(row["dataset"], "") + " " + (row["provenance_notes"] or "")
    return notes


# Acima disso, uma varredura de cardinalidade por coluna vira scan pesado, não
# consulta de metadado — 10,6% das tabelas do espelho passam disto (SIA
# produção ambulatorial: 6,16 bilhões de linhas; CNPJ estabelecimentos: 2,54
# bilhões...). Estágio 1 é "o barato primeiro" por definição do plano; essas
# tabelas ficam nao_verificado com um motivo distinto, pra estágio 3
# (priorizar por uso real) decidir se valem a medição cara.
ROW_COUNT_SAFETY_LIMIT = 50_000_000


def load_row_counts() -> dict:
    sql = """
    SET enable_progress_bar=false;
    SELECT dataset, "table", rows FROM _rodado_metadata WHERE source <> 'view_only';
    """
    try:
        rows = _query(sql)
    except Exception as exc:  # noqa: BLE001
        print(f"  aviso: não consegui buscar rows de _rodado_metadata ({exc}) — sem limite de segurança por tamanho", file=sys.stderr)
        return {}
    return {f"{r['dataset']}.{r['table']}": r["rows"] for r in rows}


def main():
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        schema: dict = json.load(f)

    padrao_externo_names, coded_differently = load_known_names()
    dicionario_covered = load_dicionario_covered()
    provenance_notes = load_provenance_notes()
    row_counts = load_row_counts()
    print(f"provenance_notes: {len(provenance_notes)} datasets; row_counts: {len(row_counts)} tabelas", file=sys.stderr)

    results: dict[str, dict] = {}
    pending: dict[str, list[str]] = {}  # "dataset.table" -> [colnames precisando de cardinalidade real]

    for dataset, tables in schema.items():
        notes = provenance_notes.get(dataset, "")
        for table_name, cols in tables.items():
            tid = f"{dataset}.{table_name}"
            for col in cols:
                name, ctype = col["name"], col.get("type")
                if ctype not in CANDIDATE_TYPES:
                    continue
                key = f"{tid}.{name}"
                norm_name = _norm(name)
                if (tid, norm_name) in dicionario_covered:
                    continue  # dicionario_disponivel — fora do escopo deste arquivo

                if NAO_E_CODIGO_RE.match(norm_name):
                    results[key] = {
                        "label": "nao_e_codigo",
                        "reason": "nome autoexplicativo (calendário/medida/identificador) — valor bruto já é a informação",
                    }
                    continue
                if BOOLEAN_FLAG_RE.match(norm_name):
                    results[key] = {
                        "label": "nao_e_codigo",
                        "reason": "flag binário — nome já indica o que representa; a codificação exata (S/N, 0/1) pode precisar de conferência pontual, mas não de glossário",
                    }
                    continue
                if norm_name in padrao_externo_names:
                    results[key] = {
                        "label": "padrao_externo",
                        "reason": padrao_externo_names[norm_name],
                    }
                    continue
                if norm_name in coded_differently:
                    results[key] = {
                        "label": "documentado_em_outro_lugar",
                        "reason": f"bridges.yaml coded_differently.{name}: {coded_differently[norm_name]}",
                    }
                    continue
                token_hit = next((KNOWN_TOKEN_PATTERNS[t] for t in norm_name.split("_") if t in KNOWN_TOKEN_PATTERNS), None)
                if token_hit:
                    results[key] = {"label": "padrao_externo", "reason": token_hit}
                    continue
                if notes and name.lower() in notes.lower():
                    results[key] = {
                        "label": "documentado_em_outro_lugar",
                        "reason": "nome da coluna aparece no provenance_notes do dataset (conferir antes de confiar — best-effort)",
                    }
                    continue

                if row_counts.get(tid, 0) > ROW_COUNT_SAFETY_LIMIT:
                    results[key] = {
                        "label": "nao_verificado",
                        "reason": f"tabela grande (~{row_counts[tid]:,} linhas) — cardinalidade adiada nesta "
                                  "rodada por custo de scan; sem fonte conhecida pelo nome. Priorizar "
                                  "manualmente (estágio 3 do plano) antes de medir.".replace(",", "."),
                    }
                    continue

                pending.setdefault(tid, []).append(name)

    n_pending_cols = sum(len(v) for v in pending.values())
    print(f"{len(results)} colunas resolvidas por nome; {n_pending_cols} colunas em {len(pending)} tabelas "
          f"precisam de cardinalidade real no beelink", file=sys.stderr)

    for i, (tid, colnames) in enumerate(pending.items(), 1):
        dataset, table_name = tid.split(".", 1)
        # Recursivo + hive_partitioning: parte do mirror é Hive-particionado em
        # subpastas (ex. br_ana_telemetria.series_cota_diaria/bacia=10/...) e
        # o glob raso `*.parquet` (o que _PARQUET_GLOBS do mcp_server.py usa)
        # não acha nada nesse caso.
        glob = f"~/rodado/{dataset}/{table_name}/**/*.parquet"
        selects = ", ".join(f'approx_count_distinct("{c}") AS "{c}"' for c in colnames)
        sql = f"""
        SET enable_progress_bar=false;
        SELECT {selects} FROM read_parquet('{glob}', union_by_name=true, hive_partitioning=true);
        """
        try:
            rows = _query(sql, timeout=180)
        except Exception as exc:  # noqa: BLE001
            print(f"  [{i}/{len(pending)}] skip {tid}: {exc}", file=sys.stderr)
            for c in colnames:
                results[f"{tid}.{c}"] = {
                    "label": "nao_verificado",
                    "reason": f"consulta de cardinalidade falhou no beelink: {exc}",
                }
            continue
        counts = rows[0] if rows else {}
        for c in colnames:
            n = counts.get(c)
            key = f"{tid}.{c}"
            if n is None:
                results[key] = {"label": "nao_verificado", "reason": "cardinalidade não retornou valor"}
            elif n > CARDINALITY_THRESHOLD:
                results[key] = {
                    "label": "nao_e_codigo",
                    "reason": f"cardinalidade medida ~{n} valores distintos (> {CARDINALITY_THRESHOLD}) — não parece código",
                }
            else:
                results[key] = {
                    "label": "nao_verificado",
                    "reason": f"candidato real: ~{n} valores distintos, nome não bate com fonte conhecida — "
                              "trate como circunstancia_obito até prova em contrário",
                }
        if i % 25 == 0 or i == len(pending):
            print(f"  [{i}/{len(pending)}] tabelas medidas", file=sys.stderr)

    by_label: dict[str, int] = {}
    for r in results.values():
        by_label[r["label"]] = by_label.get(r["label"], 0) + 1

    out = {
        "_meta": {
            "generated_by": "scripts/gera_schema_dict_status.py",
            "plan": "tasks/plan/generate-full-schema-dict.md",
            "scope": "colunas STRING/INTEGER fora de dicionario_coverage.json — FLOAT/BOOLEAN não entram (contínuo/autoexplicativo)",
            "cardinality_threshold": CARDINALITY_THRESHOLD,
            "counts_by_label": by_label,
            "total_columns_labeled": len(results),
            "caveat_provenance_notes": (
                "match contra provenance_notes é best-effort e fraco pra dataset espelhado "
                "(nota é boilerplate); não é triagem exaustiva"
            ),
        },
        "columns": results,
    }
    DST.write_text(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{DST.relative_to(REPO)} — {len(results)} colunas etiquetadas: {by_label}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
