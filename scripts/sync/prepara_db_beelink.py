"""Regenera data/basedosdados.duckdb apontando pro beelink (via mount SMB local),
em vez do S3/Hetzner. Beelink tem mais tabelas e está mais atualizado que o bucket."""
import os
import duckdb
from collections import defaultdict

BEELINK_MOUNT = os.path.expanduser("~/mnt/homelab/rodado")
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "basedosdados.duckdb")

table_files = defaultdict(lambda: defaultdict(list))
for dataset in sorted(os.listdir(BEELINK_MOUNT)):
    dataset_path = os.path.join(BEELINK_MOUNT, dataset)
    if not os.path.isdir(dataset_path) or dataset.startswith('.'):
        continue
    for table in sorted(os.listdir(dataset_path)):
        table_path = os.path.join(dataset_path, table)
        if not os.path.isdir(table_path) or table.startswith('.'):
            continue
        parquet_files = [
            os.path.join(table_path, f)
            for f in sorted(os.listdir(table_path))
            if f.endswith('.parquet')
        ]
        if parquet_files:
            table_files[dataset][table] = parquet_files

con = duckdb.connect(DB_PATH)

created, failed = 0, []
for dataset, tables in table_files.items():
    con.execute(f'CREATE SCHEMA IF NOT EXISTS "{dataset}"')
    for table, files in tables.items():
        file_list = ", ".join(f"'{f}'" for f in files)
        try:
            con.execute(f"""
                CREATE OR REPLACE VIEW "{dataset}"."{table}" AS
                SELECT * FROM read_parquet([{file_list}], hive_partitioning=true, union_by_name=true)
            """)
            created += 1
        except Exception as e:
            failed.append((dataset, table, str(e)))

print(f"Views criadas/atualizadas: {created}")
print(f"Datasets: {len(table_files)}")
if failed:
    print(f"Falhas ({len(failed)}):")
    for dataset, table, err in failed[:20]:
        print(f"  {dataset}.{table}: {err}")

con.close()
