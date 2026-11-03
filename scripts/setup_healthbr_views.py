#!/usr/bin/env python3
"""Create DuckDB views for healthbr-data (Cloudflare R2).

healthbr-data (Sidney Bissoli, CC-BY 4.0) mirrors Brazilian health microdata
to Cloudflare R2 as Parquet — ~1.93B rows across 6 datasets.

Creates per-year views for large datasets and direct views for dicionarios.
healthbr-data is a third-party bucket, not project storage — this project owns
no cloud storage of its own. The R2 read config is already in ~/.duckdbrc on
beelink (set by an earlier run).

Usage:
  python3 scripts/setup_healthbr_views.py
"""

import subprocess
import sys
import tempfile

BEELINK_HOST = "beelink"
DB = "~/rodado/basedosdados.duckdb"

# Since 2026-11-03 the dicionarios and the agregados (doses/cobertura 1994-2019) are mirrored
# on beelink's disk (rclone copy of the public bucket); these views read the local copy.
# Only the microdados (and, if ever recreated, covid/sih) stay remote. br_ms_sinasc is NOT
# taken from healthbr: the mirror's own br_ms_sinasc.microdados goes to 2026 (healthbr stops in 2022).
L = "/home/polo/rodado"
views = [
    # (schema, table, path, hive_partitioning)
    ("br_ms_sipni_dicionarios", "vacinas", f"{L}/br_ms_sipni_dicionarios/vacinas/*.parquet", False),
    ("br_ms_sipni_dicionarios", "cobertura_indicadores", f"{L}/br_ms_sipni_dicionarios/cobertura_indicadores/*.parquet", False),
    ("br_ms_sipni_dicionarios", "doses_tipo", f"{L}/br_ms_sipni_dicionarios/doses_tipo/*.parquet", False),
    ("br_ms_sipni_dicionarios", "faixa_etaria", f"{L}/br_ms_sipni_dicionarios/faixa_etaria/*.parquet", False),
    ("br_ms_sipni_doses_historicas", "doses_agregadas", f"{L}/br_ms_sipni_doses_historicas/doses_agregadas/**/*.parquet", True),
    ("br_ms_sipni_cobertura_historica", "cobertura_agregada", f"{L}/br_ms_sipni_cobertura_historica/cobertura_agregada/**/*.parquet", True),
]

# Per-year views for large partitioned datasets
year_views = []
for year in range(2020, 2027):
    year_views.append(("br_ms_sipni_microdados", f"vacinacao_{year}",
                       f"s3://healthbr-data/sipni/microdados/ano={year}/*/*/*.parquet", True))
for year in range(2021, 2027):
    year_views.append(("br_ms_vacinacao_covid19", f"microdados_{year}",
                       f"s3://healthbr-data/sipni/covid/microdados/ano={year}/*/*/*.parquet", True))
for year in range(2020, 2027):
    year_views.append(("br_ms_sih", f"internacoes_{year}",
                       f"s3://healthbr-data/sih/ano={year}/*/*/*.parquet", True))


def run_sql(sql: str, timeout: int = 30) -> bool:
    """Run SQL on beelink via duckdb -c.  The -c flag guarantees clean exit."""
    # Write SQL to file to avoid quoting hell
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as f:
        f.write(sql)
        local = f.name
    remote = f"/tmp/hbv_{subprocess.getoutput('date +%s%N')}.sql"
    try:
        subprocess.run(["scp", local, f"{BEELINK_HOST}:{remote}"],
                       capture_output=True, timeout=15, check=True)
        proc = subprocess.run(
            ["ssh", BEELINK_HOST, f"timeout {timeout} ~/bin/duckdb {DB} -c \"$(cat {remote})\" && rm -f {remote}"],
            capture_output=True, text=True, timeout=timeout + 15)
        if proc.returncode != 0:
            err = proc.stderr.strip()[:300]
            if "lock" in err.lower():
                return "LOCKED"
            print(f"  ERROR ({proc.returncode}): {err}", file=sys.stderr)
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT", file=sys.stderr)
        return False
    finally:
        subprocess.run(["rm", "-f", local], capture_output=True)


def main():
    schemas_created = set()

    for schema, table, path, hive in views:
        if schema not in schemas_created:
            result = run_sql(f'CREATE SCHEMA IF NOT EXISTS "{schema}";', timeout=10)
            if result == "LOCKED":
                print(f"  DB LOCKED — waiting 30 s and retrying...", file=sys.stderr)
                subprocess.run(["ssh", BEELINK_HOST,
                    "sleep 30"],  # never kill: the lock belongs to another session's real work
                    capture_output=True, timeout=45)
                subprocess.run(["sleep", "3"], capture_output=True)
                result = run_sql(f'CREATE SCHEMA IF NOT EXISTS "{schema}";', timeout=10)
            if result is True:
                schemas_created.add(schema)

        hive_clause = ", hive_partitioning=true, union_by_name=true" if hive else ""
        sql = f'CREATE OR REPLACE VIEW "{schema}"."{table}" AS SELECT * FROM read_parquet(\'{path}\'{hive_clause});'
        print(f"  {schema}.{table}...", file=sys.stderr, end=" ")

        result = run_sql(sql, timeout=60)
        if result == "LOCKED":
            print(f"LOCKED — waiting 30 s...", file=sys.stderr)
            subprocess.run(["ssh", BEELINK_HOST,
                "sleep 30"],  # never kill: the lock belongs to another session's real work
                capture_output=True, timeout=45)
            subprocess.run(["sleep", "3"], capture_output=True)
            result = run_sql(sql, timeout=60)

        if result is True:
            print(f"OK", file=sys.stderr)
        elif result is False:
            print(f"FAIL", file=sys.stderr)

    # Also add year views
    for schema, table, path, hive in year_views:
        if schema not in schemas_created:
            run_sql(f'CREATE SCHEMA IF NOT EXISTS "{schema}";', timeout=10)
            schemas_created.add(schema)
        hive_clause = ", hive_partitioning=true, union_by_name=true" if hive else ""
        sql = f'CREATE OR REPLACE VIEW "{schema}"."{table}" AS SELECT * FROM read_parquet(\'{path}\'{hive_clause});'
        print(f"  {schema}.{table}...", file=sys.stderr, end=" ")
        result = run_sql(sql, timeout=60)
        if result == "LOCKED":
            subprocess.run(["ssh", BEELINK_HOST,
                "sleep 30"],  # never kill: the lock belongs to another session's real work
                capture_output=True, timeout=45)
            subprocess.run(["sleep", "3"], capture_output=True)
            result = run_sql(sql, timeout=60)
        if result is True:
            print(f"OK", file=sys.stderr)
        elif result is False:
            print(f"FAIL", file=sys.stderr)

    # Verify
    print("Verifying...", file=sys.stderr)
    r = subprocess.run(["ssh", BEELINK_HOST,
        "~/bin/duckdb ~/rodado/basedosdados.duckdb -c \"SELECT table_schema, table_name "
        "FROM information_schema.tables WHERE table_schema LIKE 'br_ms_sipni%' "
        "OR table_schema = 'br_ms_sinasc' OR table_schema = 'br_ms_sih' "
        "OR table_schema = 'br_ms_vacinacao%' ORDER BY table_schema, table_name;\""],
        capture_output=True, text=True, timeout=30)
    print(r.stdout)
    view_count = r.stdout.count("│ br_ms")
    print(f"Total healthbr views: {view_count}", file=sys.stderr)


if __name__ == "__main__":
    main()
