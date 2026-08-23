#!/usr/bin/env python3
"""
Sync 229 missing tables from BigQuery → beelink.
Progress reported every iteration to ~/.gcp_sync_progress.
"""

import json
import subprocess
from pathlib import Path
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
import _bq_tipos
from datetime import datetime
from google.cloud import bigquery
import os
import sys

os.environ['GOOGLE_CLOUD_PROJECT'] = 'raspa-491716'
PROGRESS_FILE = Path.home() / ".gcp_sync_progress"
BEELINK_HOST = "beelink"
BEELINK_PATH = "~/rodado"   # ~/baseldosdados-data nao existe mais no beelink

def write_progress(status, pct, table="", rows=0):
    """Write progress."""
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "pct": pct,
        "table": table,
        "rows": rows,
    }
    with open(PROGRESS_FILE, "w") as f:
        json.dump(data, f)
    print(f"[{pct:3d}%] {status:8s} {table:45s} rows={rows}")

def get_beelink_tables():
    """List tables on beelink."""
    cmd = f"ssh {BEELINK_HOST} 'find {BEELINK_PATH} -maxdepth 2 -mindepth 2 -type d -printf \"%P\\\\n\"' 2>/dev/null"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    tables = set()
    for line in result.stdout.strip().split("\n"):
        if "/" in line:
            ds, tbl = line.split("/", 1)
            tables.add(f"{ds}.{tbl}")
    return tables

def get_bq_tables():
    """List all tables in BigQuery."""
    client = bigquery.Client(project='raspa-491716')
    tables = []
    datasets = list(client.list_datasets(project='basedosdados'))

    for ds in datasets:
        try:
            tbl_list = list(client.list_tables(f'basedosdados.{ds.dataset_id}', max_results=10000))
            for t in tbl_list:
                tables.append(f"{ds.dataset_id}.{t.table_id}")
        except:
            pass

    return tables

def query_and_show(dataset, table):
    """Query table count via bq CLI."""
    query = f"SELECT COUNT(*) as cnt FROM `basedosdados.{dataset}.{table}` LIMIT 10000000"
    cmd = [
        "bq",
        "query",
        "--project_id=raspa-491716",
        "--format=json",
        "--nouse_legacy_sql",
        "--max_rows=10000000",
        query,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data:
                return int(data[0].get("cnt", 0))
    except:
        pass
    return 0

def sync_to_beelink(dataset, table, row_count):
    """Fetch table data via bq query, convert to Parquet, rsync to beelink."""
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:
        print(f"ERROR: pyarrow not installed for {dataset}.{table}")
        return False

    # Query table data
    full_name = f"basedosdados.{dataset}.{table}"
    query = f"SELECT * FROM `{full_name}` LIMIT 10000000"

    cmd = [
        "bq",
        "query",
        "--project_id=raspa-491716",
        "--format=json",
        "--nouse_legacy_sql",
        "--max_rows=10000000",
        query,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            return False

        rows = json.loads(result.stdout) if result.stdout.strip() else []
        if not rows:
            return True  # Empty table, still successful

        # Converte com o tipo do BigQuery. `pa.Table.from_pylist(rows)` direto
        # transforma TODA coluna em string — o JSON do bq não carrega tipo — e foi
        # o que produziu os 80 tmp*.parquet de 2026-07-05 (tasks/tmp_parquet_38.plan).
        tipos = _bq_tipos.schema_bq(dataset, table, billing="raspa-491716")
        table_arrow = _bq_tipos.para_arrow(rows, tipos)
        if table_arrow is None:
            return True

        remote_dir_path = f"{BEELINK_PATH}/{dataset}/{table}"
        subprocess.run(
            f"ssh {BEELINK_HOST} 'mkdir -p {remote_dir_path}'",
            shell=True,
            capture_output=True,
        )

        # O nome final sai ANTES do envio. Mandar o tempfile e deixar o rsync
        # preservar o basename é o bug que espalhou tmp*.parquet pelo espelho.
        existentes = subprocess.run(
            f"ssh {BEELINK_HOST} 'ls -1 {remote_dir_path} 2>/dev/null'",
            shell=True, capture_output=True, text=True,
        ).stdout.split()
        destino = _bq_tipos.nome_destino(existentes)

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            parquet_file = Path(tmpdir) / destino
            pq.write_table(table_arrow, str(parquet_file), compression="zstd")  # o espelho inteiro e ZSTD
            # o rsync do macOS (openrsync) nao tem --chmod; ajusta no beelink depois
            result = subprocess.run(
                f"rsync -av {parquet_file} "
                f"{BEELINK_HOST}:{remote_dir_path}/{destino} && "
                f"ssh {BEELINK_HOST} 'chmod 664 {remote_dir_path}/{destino}'",
                shell=True,
                capture_output=True,
                timeout=120,
            )
        return result.returncode == 0
    except:
        return False

def main():
    write_progress("scan", 0, "Scanning BigQuery...", 0)
    print("Getting BigQuery tables...")
    bq_tables = get_bq_tables()
    print(f"✓ BigQuery: {len(bq_tables)} tables")

    write_progress("compare", 33, "Comparing with beelink...", 0)
    print("Getting beelink tables...")
    beelink_tables = get_beelink_tables()
    print(f"✓ Beelink: {len(beelink_tables)} tables")

    missing = sorted([t for t in bq_tables if t not in beelink_tables])
    missing = [t for t in missing if "cloudaudit" not in t]
    print(f"✓ Missing: {len(missing)} tables\n")

    # Sync each table
    synced = 0
    for idx, full_id in enumerate(missing):  # All missing tables
        pct = int(100 * idx / len(missing)) if missing else 100
        dataset, table = full_id.split(".", 1)

        write_progress("fetch", pct, full_id, 0)

        try:
            rows = query_and_show(dataset, table)
            if sync_to_beelink(dataset, table, rows):
                synced += 1
                write_progress("done", pct, full_id, rows)
                print(f"✓ {full_id}: {rows} rows")
            else:
                print(f"✗ {full_id}: sync failed")
        except Exception as e:
            print(f"✗ {full_id}: {e}")

    write_progress("complete", 100, f"Synced {synced} of {len(missing)}", synced)
    print(f"\n✓ Synced {synced}/{len(missing)} missing tables")
    return 0

if __name__ == "__main__":
    sys.exit(main())
