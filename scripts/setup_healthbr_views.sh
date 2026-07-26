#!/bin/bash
# Setup healthbr-data views on beelink's DuckDB
# Uses Python (available everywhere) instead of bash associative arrays.

exec python3 - "$@" << 'PYEOF'
import subprocess, os

BEELINK_HOST = os.environ.get("BEELINK_HOST", "beelink")
DB = "~/rodado/basedosdados.duckdb"

# Schema: (schema, table, s3_prefix_glob, hive_partitioning)
views = [
    ("br_ms_sipni_microdados", "microdados_vacinacao", "s3://healthbr-data/sipni/microdados/**/*.parquet", True),
    ("br_ms_sipni_covid", "microdados_covid", "s3://healthbr-data/sipni/covid/microdados/**/*.parquet", True),
    ("br_ms_sipni_doses_historicas", "doses_agregadas", "s3://healthbr-data/sipni/agregados/doses/**/*.parquet", True),
    ("br_ms_sipni_cobertura_historica", "cobertura_agregada", "s3://healthbr-data/sipni/agregados/cobertura/**/*.parquet", True),
    ("br_ms_sinasc", "nascidos_vivos", "s3://healthbr-data/sinasc/**/*.parquet", True),
    ("br_ms_sih", "internacoes", "s3://healthbr-data/sih/**/*.parquet", True),
    ("br_ms_sipni_dicionarios", "dicionario_vacinas", "s3://healthbr-data/sipni/dicionarios/imuno.parquet", False),
    ("br_ms_sipni_dicionarios", "dicionario_cobertura", "s3://healthbr-data/sipni/dicionarios/imunocob.parquet", False),
    ("br_ms_sipni_dicionarios", "dicionario_doses", "s3://healthbr-data/sipni/dicionarios/dose.parquet", False),
    ("br_ms_sipni_dicionarios", "dicionario_faixa_etaria", "s3://healthbr-data/sipni/dicionarios/fxet.parquet", False),
]

# S3 config prefix to inject before every SQL statement (httpfs settings)
S3_PREFIX = """
LOAD httpfs;
SET s3_endpoint = '5c499208eebced4e34bd98ffa204f2fb.r2.cloudflarestorage.com';
SET s3_access_key_id = '28c72d4b3e1140fa468e367ae472b522';
SET s3_secret_access_key = '2937b2106736e2ba64e24e92f2be4e6c312bba3355586e41ce634b14c1482951';
SET s3_region = 'auto';
SET s3_url_style = 'path';
"""

def run_duckdb(sql):
    full_sql = S3_PREFIX + sql
    cmd = ["ssh", BEELINK_HOST, f"~/bin/duckdb {DB} -c \"{full_sql}\""]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        err = result.stderr.replace(full_sql[:80], "...").strip()
        print(f"  Error: {err[:200]}")
    else:
        print(f"  OK")

# Create views
for schema, table, s3_path, hive_partitioning in views:
    print(f"  Creating {schema}.{table}...")
    run_duckdb(f'CREATE SCHEMA IF NOT EXISTS "{schema}";')
    hive = "hive_partitioning=true, union_by_name=true" if hive_partitioning else ""
    hive_clause = f", {hive}" if hive else ""
    sql = f'CREATE OR REPLACE VIEW "{schema}"."{table}" AS SELECT * FROM read_parquet(\'{s3_path}\'{hive_clause});'
    run_duckdb(sql)
    run_duckdb(sql.strip())

# Verify
print("Verifying...")
result = subprocess.run(
    ["ssh", BEELINK_HOST,
     f"~/bin/duckdb {DB} -c \"SELECT table_schema, table_name FROM information_schema.tables "
     f"WHERE table_schema LIKE 'br_ms_sipni%' OR table_schema LIKE 'br_ms_sinasc%' "
     f"OR table_schema LIKE 'br_ms_sih%' ORDER BY table_schema, table_name;\""],
    capture_output=True, text=True, timeout=30)
print(result.stdout)

print("healthbr-data views created successfully.")
PYEOF
