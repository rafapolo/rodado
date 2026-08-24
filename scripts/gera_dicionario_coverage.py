#!/usr/bin/env python3
"""beelink (br_ibge_censo_demografico.dicionario) -> docs/context/dicionario_coverage.json

    python3 scripts/gera_dicionario_coverage.py

The IBGE census microdata tables (`microdados_pessoa_*`, `microdados_domicilio_*`)
keep raw IBGE codes as column names (`v0502`, `v6033`...) instead of the
Portuguese names/values the rest of the Base dos Dados mirror normalizes to.
The decode table exists (`br_ibge_censo_demografico.dicionario`,
chave->valor per column per table) but nothing points `describe_table` at it —
this script bakes the coverage (which columns of which table have a decode
available) into a small static file so mcp_server.py doesn't need a live
beelink round-trip to answer that.

Rerun after a sync touches `br_ibge_censo_demografico.dicionario` (rare: this
is 1970-2010 census microdata, not a table that grows).
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DST = REPO / "docs" / "context" / "dicionario_coverage.json"

BEELINK_HOST = "beelink"
BEELINK_DUCKDB_BIN = "~/bin/duckdb"
BEELINK_DUCKDB_PATH = "~/rodado/basedosdados.duckdb"
DATASET = "br_ibge_censo_demografico"

SQL = f"""
SET enable_progress_bar=false;
SELECT id_tabela, list_sort(list(DISTINCT trim(nome_coluna))) AS colunas
FROM {DATASET}.dicionario
GROUP BY id_tabela
ORDER BY id_tabela;
"""


def main():
    cmd = ["ssh", BEELINK_HOST, f"{BEELINK_DUCKDB_BIN} -json {BEELINK_DUCKDB_PATH}"]
    try:
        out = subprocess.run(cmd, input=SQL, capture_output=True, text=True, timeout=120)
    except Exception as exc:                                  # noqa: BLE001
        sys.exit(f"beelink query failed: {exc}")
    if out.returncode != 0:
        sys.exit(f"beelink query failed: {out.stderr.strip()[:500]}")

    rows = json.loads(out.stdout)
    if not rows:
        sys.exit(f"{DATASET}.dicionario returned no rows — check the table still exists.")

    coverage = {f"{DATASET}.{row['id_tabela']}": row["colunas"] for row in rows}

    result = {
        "_meta": {
            "source": f"{DATASET}.dicionario",
            "generated_by": "scripts/gera_dicionario_coverage.py",
            "note": (
                "chave->valor decode exists per (id_tabela, nome_coluna) in "
                f"{DATASET}.dicionario — filter it by id_tabela and nome_coluna "
                "to get the code->label mapping for one column."
            ),
        },
        "tables": coverage,
    }
    DST.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    total_cols = sum(len(v) for v in coverage.values())
    print(f"{DST.relative_to(REPO)} — {len(coverage)} tabelas, {total_cols} colunas decodificáveis")
    return 0


if __name__ == "__main__":
    sys.exit(main())
