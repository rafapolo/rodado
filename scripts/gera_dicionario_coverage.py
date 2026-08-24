#!/usr/bin/env python3
"""beelink (every {dataset}.dicionario table) -> docs/context/dicionario_coverage.json

    python3 scripts/gera_dicionario_coverage.py

Many datasets across the mirror keep raw source codes as column values
(IBGE census `v0502`, but also `sexo`/`raca_cor` as bare integers in RAIS,
CAGED, SIM, ENEM and 40+ others) instead of decoded Portuguese labels. Each
of those datasets carries its own `dicionario` table (chave->valor per
column per table) but nothing points `describe_table` at it — this script
discovers every dataset with a `dicionario` table and bakes the coverage
(which columns of which table have a decode available) into a small static
file so mcp_server.py doesn't need a live beelink round-trip to answer that.

Originally scoped to just `br_ibge_censo_demografico` (the one place this
was first noticed); generalized 2026-08-24 after a blind MCP test caught a
query silently using RAIS's `sexo` encoding against CAGED (which differs)
and a systematic check found 44 datasets with the same undocumented-decode
shape — see docs/context/bridges.yaml's `coded_differently` section for the
column-level danger this only partially covers (same code, different table,
because the *concept* itself is coded differently by design, not just
locally raw).

Rerun after a sync adds/changes any `{dataset}.dicionario` table.
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

FIND_DATASETS_SQL = """
SET enable_progress_bar=false;
SELECT DISTINCT table_schema
FROM information_schema.tables
WHERE table_name = 'dicionario'
ORDER BY table_schema;
"""

# br_seeg_emissoes.dicionario uses tabela/coluna instead of id_tabela/nome_coluna
# — every other dataset checked (44/45) uses the id_tabela/nome_coluna pair.
COLUMN_ALIASES = {
    "br_seeg_emissoes": ("tabela", "coluna"),
}


def _query(sql: str, timeout: int = 120) -> list:
    cmd = ["ssh", BEELINK_HOST, f"{BEELINK_DUCKDB_BIN} -json {BEELINK_DUCKDB_PATH}"]
    out = subprocess.run(cmd, input=sql, capture_output=True, text=True, timeout=timeout)
    if out.returncode != 0:
        sys.exit(f"beelink query failed: {out.stderr.strip()[:500]}")
    stdout = out.stdout.strip()
    return json.loads(stdout) if stdout else []


def main():
    datasets = [row["table_schema"] for row in _query(FIND_DATASETS_SQL)]
    if not datasets:
        sys.exit("No dataset with a `dicionario` table found — check beelink connectivity.")

    coverage: dict[str, list[str]] = {}
    for ds in datasets:
        id_col, col_col = COLUMN_ALIASES.get(ds, ("id_tabela", "nome_coluna"))
        sql = f"""
        SET enable_progress_bar=false;
        SELECT {id_col} AS id_tabela, list_sort(list(DISTINCT trim({col_col}))) AS colunas
        FROM {ds}.dicionario
        GROUP BY {id_col}
        ORDER BY {id_col};
        """
        try:
            rows = _query(sql)
        except Exception as exc:                                  # noqa: BLE001
            print(f"  skip {ds}: {exc}", file=sys.stderr)
            continue
        for row in rows:
            coverage[f"{ds}.{row['id_tabela']}"] = row["colunas"]

    result = {
        "_meta": {
            "source": "every {dataset}.dicionario table found in the mirror",
            "generated_by": "scripts/gera_dicionario_coverage.py",
            "datasets_scanned": sorted(datasets),
            "note": (
                "chave->valor decode exists per (id_tabela, nome_coluna) in "
                "{dataset}.dicionario — filter it by id_tabela and nome_coluna "
                "to get the code->label mapping for one column. See also "
                "docs/context/bridges.yaml's coded_differently section: some "
                "of these columns (sexo, raca_cor...) use a DIFFERENT code "
                "per dataset for the same concept, not just a raw code that "
                "needs decoding once."
            ),
        },
        "tables": coverage,
    }
    DST.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    total_cols = sum(len(v) for v in coverage.values())
    print(f"{DST.relative_to(REPO)} — {len(datasets)} datasets, {len(coverage)} tabelas, "
          f"{total_cols} colunas decodificáveis")
    return 0


if __name__ == "__main__":
    sys.exit(main())
