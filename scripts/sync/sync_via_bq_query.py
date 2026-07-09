#!/usr/bin/env python3
"""
Sync missing tables: bq query → JSON → Parquet → rsync to beelink.
Reports progress every iteration.
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

BQ_PROJECT = "basedosdados"
BEELINK_HOST = "beelink"
BEELINK_PATH = "~/baseldosdados-data"
PROGRESS_FILE = Path.home() / ".gcp_sync_progress"
TEMP_DIR = Path(tempfile.gettempdir()) / "bq_sync_parquet"

def write_progress(status, pct, message="", table=""):
    """Write progress."""
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "pct": pct,
        "message": message,
        "table": table,
    }
    with open(PROGRESS_FILE, "w") as f:
        json.dump(data, f)
    print(f"[{pct:3d}%] {status:8s} {table:40s} {message}")

def list_bq_datasets():
    """List all datasets via bq ls."""
    cmd = ["bq", "ls", "--project_id=" + BQ_PROJECT]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return []

    datasets = []
    for line in result.stdout.strip().split("\n")[2:]:  # Skip header
        if line.strip():
            ds = line.split()[0]
            datasets.append(ds)
    return datasets

def list_bq_tables_in_dataset(dataset):
    """List tables in a dataset."""
    cmd = ["bq", "ls", "--project_id=" + BQ_PROJECT, dataset]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return []

    tables = []
    for line in result.stdout.strip().split("\n")[2:]:  # Skip header
        if line.strip():
            # Format: TABLE_ID | TYPE | LABELS | SCHEMA
            parts = line.split()
            if parts:
                tables.append(parts[0])
    return tables

def get_beelink_tables():
    """List tables on beelink."""
    cmd = f"ssh {BEELINK_HOST} 'find {BEELINK_PATH} -maxdepth 2 -mindepth 2 -type d -printf \"%P\\\\n\"' 2>/dev/null"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    tables = {}
    for line in result.stdout.strip().split("\n"):
        if "/" in line:
            ds, tbl = line.split("/", 1)
            tables[f"{ds}.{tbl}"] = True
    return tables

def fetch_table_via_bq_query(dataset, table):
    """Fetch table using bq query → JSON."""
    full_name = f"{dataset}.{table}"

    cmd = [
        "bq",
        "query",
        "--project_id=" + BQ_PROJECT,
        "--format=json",
        "--nouse_legacy_sql",
        f"SELECT * FROM `{full_name}` LIMIT 10000000",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        return None

    try:
        return json.loads(result.stdout)
    except:
        return None

def json_to_parquet(rows, dataset, table):
    """Convert JSON rows to Parquet."""
    if not rows:
        return None

    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:
        print("ERROR: pyarrow not installed", file=sys.stderr)
        return None

    # Simple schema inference from first row
    table_arrow = pa.Table.from_pylist(rows)

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    out_file = TEMP_DIR / f"{dataset}_{table}.parquet"
    pq.write_table(table_arrow, str(out_file), compression="snappy")

    return out_file

def rsync_to_beelink(local_file, dataset, table):
    """Rsync Parquet to beelink."""
    remote_base = f"{BEELINK_HOST}:{BEELINK_PATH}/{dataset}/{table}"

    # Ensure directory
    subprocess.run(
        f"ssh {BEELINK_HOST} 'mkdir -p {BEELINK_PATH}/{dataset}/{table}'",
        shell=True,
        capture_output=True,
    )

    # Rsync file
    cmd = f"rsync -av --progress {local_file} {remote_base}/"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    return result.returncode == 0

def main():
    write_progress("scan", 0, "Listing BigQuery datasets...")

    datasets = list_bq_datasets()
    print(f"Found {len(datasets)} datasets")

    # Enumerate all tables
    all_bq_tables = {}
    for ds in datasets:
        tables = list_bq_tables_in_dataset(ds)
        for tbl in tables:
            all_bq_tables[f"{ds}.{tbl}"] = True

    print(f"Found {len(all_bq_tables)} tables in BigQuery")

    write_progress("compare", 33, f"Found {len(all_bq_tables)} BQ tables")

    beelink_tables = get_beelink_tables()
    print(f"Found {len(beelink_tables)} tables on beelink")

    missing = sorted([t for t in all_bq_tables.keys() if t not in beelink_tables])

    # Filter audit logs
    missing = [t for t in missing if "cloudaudit_googleapis_com" not in t]

    print(f"\nMissing: {len(missing)} tables")
    for t in missing[:10]:
        print(f"  {t}")
    if len(missing) > 10:
        print(f"  ... {len(missing) - 10} more\n")

    # Fetch and sync each
    synced = 0
    for idx, full_name in enumerate(missing):
        pct = int(100 * idx / len(missing)) if missing else 100
        dataset, table = full_name.split(".", 1)

        write_progress("fetch", pct, f"Querying...", full_name)

        rows = fetch_table_via_bq_query(dataset, table)
        if not rows:
            write_progress("skip", pct, "No rows or error", full_name)
            continue

        write_progress("convert", pct, f"{len(rows)} rows → Parquet", full_name)

        parquet_file = json_to_parquet(rows, dataset, table)
        if not parquet_file:
            write_progress("skip", pct, "Parquet conversion failed", full_name)
            continue

        write_progress("rsync", pct, "Pushing to beelink...", full_name)

        if rsync_to_beelink(parquet_file, dataset, table):
            synced += 1
            write_progress("done", pct, f"✓ {len(rows)} rows", full_name)
            parquet_file.unlink()
        else:
            write_progress("error", pct, "Rsync failed", full_name)

    write_progress("complete", 100, f"Synced {synced}/{len(missing)} tables")
    print(f"\n✓ Synced {synced}/{len(missing)} tables")
    return 0 if synced == len(missing) else 1

if __name__ == "__main__":
    sys.exit(main())
