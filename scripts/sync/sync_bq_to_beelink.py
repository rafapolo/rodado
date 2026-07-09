#!/usr/bin/env python3
"""
Sync missing tables from BigQuery → Hetzner S3 → beelink via SSH.
Reports progress to ~/.gcp_sync_progress every iteration.
"""

import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from google.cloud import bigquery
import tempfile

os.environ.setdefault('GOOGLE_CLOUD_PROJECT', os.environ.get('GCP_PROJECT', 'raspa-491716'))

PROGRESS_FILE = Path.home() / ".gcp_sync_progress"
TEMP_DIR = Path(tempfile.gettempdir()) / "bq_to_beelink"
BEELINK_HOST = "beelink"
BEELINK_PATH = "~/baseldosdados-data"
S3_BUCKET = os.environ.get("HETZNER_S3_BUCKET", "baseldosdados")

def write_progress(status, pct, table="", message=""):
    """Write progress to file for polling."""
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "pct": pct,
        "table": table,
        "message": message,
    }
    with open(PROGRESS_FILE, "w") as f:
        json.dump(data, f)
    print(f"[{pct:3d}%] {status:8s} {table:40s} {message}")

def list_bq_tables():
    """Get all tables from basedosdados project."""
    client = bigquery.Client(project=os.environ.get('GCP_PROJECT'))

    tables = {}
    datasets = list(client.list_datasets(project='basedosdados'))
    print(f"Found {len(datasets)} datasets in basedosdados")

    for ds in datasets:
        table_list = list(client.list_tables(f'basedosdados.{ds.dataset_id}'))
        for tbl in table_list:
            full_id = f"{ds.dataset_id}.{tbl.table_id}"
            tables[full_id] = {
                'dataset': ds.dataset_id,
                'table': tbl.table_id,
            }

    return tables

def list_beelink_tables():
    """List tables on beelink."""
    cmd = f"ssh {BEELINK_HOST} 'find {BEELINK_PATH} -maxdepth 2 -mindepth 2 -type d -printf \"%P\\\\n\"' 2>/dev/null"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    tables = set()
    for line in result.stdout.strip().split("\n"):
        if "/" in line:
            ds, tbl = line.split("/", 1)
            tables.add(f"{ds}.{tbl}")
    return tables

def fetch_and_push_table(dataset, table):
    """Fetch table from BigQuery → Parquet → push to beelink."""
    full_name = f"basedosdados.{dataset}.{table}"

    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:
        return False

    # Query
    client = bigquery.Client(project=os.environ.get('GCP_PROJECT'))
    query = f"SELECT * FROM `{full_name}` LIMIT 50000000"

    print(f"  Querying {dataset}.{table}...")
    job = client.query(query)
    rows = list(job.result(timeout=300))

    if not rows:
        print(f"  ✓ {dataset}.{table}: 0 rows")
        return True

    # Convert to Parquet
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    parquet_file = TEMP_DIR / f"{dataset}_{table}.parquet"

    schema = job.schema
    table_arrow = pa.Table.from_pylist(
        [dict(zip([f.name for f in schema], row)) for row in rows]
    )
    pq.write_table(table_arrow, str(parquet_file), compression="snappy")

    # Push to beelink
    remote_dir = f"{BEELINK_HOST}:{BEELINK_PATH}/{dataset}/{table}"
    subprocess.run(
        f"ssh {BEELINK_HOST} 'mkdir -p {BEELINK_PATH}/{dataset}/{table}'",
        shell=True,
        capture_output=True,
    )

    result = subprocess.run(
        f"rsync -av {parquet_file} {remote_dir}/",
        shell=True,
        capture_output=True,
    )

    if result.returncode == 0:
        print(f"  ✓ {dataset}.{table}: {len(rows)} rows")
        parquet_file.unlink()
        return True
    else:
        print(f"  ✗ {dataset}.{table}: rsync failed")
        return False

def main():
    write_progress("scan", 0, "", "Scanning BigQuery...")

    bq_tables = list_bq_tables()
    print(f"✓ Found {len(bq_tables)} tables in BigQuery")

    write_progress("compare", 33, "", f"Found {len(bq_tables)} BQ tables")

    beelink_tables = list_beelink_tables()
    print(f"✓ Found {len(beelink_tables)} tables on beelink")

    missing = sorted([t for t in bq_tables.keys() if t not in beelink_tables])
    print(f"\n➤ Missing: {len(missing)} tables")

    # Filter audit logs
    missing = [t for t in missing if "cloudaudit_googleapis_com" not in t]

    synced = 0
    for idx, full_id in enumerate(missing):
        pct = int(100 * idx / len(missing)) if missing else 100
        dataset, table = full_id.split(".", 1)

        write_progress("fetch", pct, full_id, f"[{idx+1}/{len(missing)}]")

        try:
            if fetch_and_push_table(dataset, table):
                synced += 1
        except Exception as e:
            print(f"  ✗ {full_id}: {e}")

    write_progress("done", 100, "", f"Synced {synced}/{len(missing)}")
    print(f"\n✓ Completed: {synced}/{len(missing)} tables synced")
    return 0

if __name__ == "__main__":
    sys.exit(main())
