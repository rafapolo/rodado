#!/usr/bin/env python3
"""Split all tables in docs/context/basedosdados-schema.json into batches ready
for the doc2query prompt (scripts/prompts/doc2query.md, fetched from
origin/ask-web — see tasks/mcp_search_refino.md item 1 for why).

    python3 scripts/doc2query_lotes.py            # batches of 25 -> tasks/doc2query/

Columns are capped at 40 per table: the prompt needs to know what a table is
about, not its full column list (br_inep_censo_escolar.escola has 455).

This is main's own batching step, not a port of ask-web's doc2query_lotes.ts —
that one read web/static/index/meta.json/colunas.json, which don't exist here.
Row counts come from a live `_rodado_metadata` probe on beelink (best-effort;
falls back to null if beelink is unreachable, since row count is prompt
context, not something validation depends on).
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO / "docs" / "context" / "basedosdados-schema.json"
OUT_DIR = REPO / "tasks" / "doc2query"
BATCH_SIZE = 25
MAX_COLS = 40

BEELINK_HOST = "beelink"
BEELINK_DUCKDB_BIN = "~/bin/duckdb"
BEELINK_DUCKDB_PATH = "~/rodado/basedosdados.duckdb"

AMOSTRA = [
    "br_ms_sim.microdados", "br_ms_sinasc.microdados", "br_tse_eleicoes.candidatos",
    "br_bd_diretorios_brasil.municipio", "br_inep_enem.microdados",
    "br_me_caged.microdados_movimentacao", "br_anp_combustiveis.precos",
    "br_pgfn_dividaativa.divida",
]


def probe_row_counts() -> dict:
    sql = 'SET enable_progress_bar=false; SELECT dataset, "table", rows FROM _rodado_metadata;'
    cmd = ["ssh", BEELINK_HOST, f"{BEELINK_DUCKDB_BIN} -json {BEELINK_DUCKDB_PATH}"]
    try:
        out = subprocess.run(cmd, input=sql, capture_output=True, text=True, timeout=60)
    except Exception as exc:                                  # noqa: BLE001
        print(f"  ! row-count probe failed, continuing without: {exc}", file=sys.stderr)
        return {}
    if out.returncode != 0:
        print(f"  ! row-count probe failed, continuing without: {out.stderr.strip()[:200]}", file=sys.stderr)
        return {}
    try:
        rows = json.loads(out.stdout)
    except Exception as exc:                                  # noqa: BLE001
        print(f"  ! row-count probe returned bad JSON, continuing without: {exc}", file=sys.stderr)
        return {}
    return {f"{r['dataset']}.{r['table']}": r["rows"] for r in rows}


def main():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    row_counts = probe_row_counts()

    entries = []
    for dataset, tables in schema.items():
        for table_name, columns in tables.items():
            tid = f"{dataset}.{table_name}"
            entries.append({
                "id": tid,
                "dataset": dataset,
                "tabela": table_name,
                "linhas": row_counts.get(tid),
                "colunas": [c["name"] for c in columns[:MAX_COLS]],
            })
    entries.sort(key=lambda e: e["id"])

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("lote_*.jsonl"):
        old.unlink()

    n = 0
    for i in range(0, len(entries), BATCH_SIZE):
        n += 1
        batch = entries[i:i + BATCH_SIZE]
        path = OUT_DIR / f"lote_{n:02d}.jsonl"
        path.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in batch) + "\n", encoding="utf-8")

    amostra = [e for e in entries if e["id"] in AMOSTRA]
    (OUT_DIR / "lote_00_amostra.jsonl").write_text(
        "\n".join(json.dumps(e, ensure_ascii=False) for e in amostra) + "\n", encoding="utf-8")

    missing_rows = sum(1 for e in entries if e["linhas"] is None)
    print(f"{len(entries)} tabelas -> {n} lotes de {BATCH_SIZE} em {OUT_DIR.relative_to(REPO)}/")
    print(f"lote_00_amostra.jsonl — {len(amostra)} tabelas conhecidas")
    if missing_rows:
        print(f"  ({missing_rows} tabelas sem contagem de linhas — beelink parcial ou tabela fora de _rodado_metadata)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
