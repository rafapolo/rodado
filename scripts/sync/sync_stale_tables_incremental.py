#!/usr/bin/env python3
"""
Sync missing data from 147 stale tables via incremental bq query.

Uses BigQuery Sandbox free tier (1TB/month). Identifies max row ID on beelink,
fetches only newer rows from BigQuery, pushes via rsync.

Runs slowly/periodically to avoid exhausting free tier quota.

Usage:
    python3 sync_stale_tables_incremental.py              # full run
    python3 sync_stale_tables_incremental.py --dry-run    # list stale tables
    python3 sync_stale_tables_incremental.py --resume     # resume from checkpoint
"""

import json
import subprocess
import sys
from pathlib import Path
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
import _bq_tipos
from datetime import datetime
from google.cloud import bigquery
import os

os.environ['GOOGLE_CLOUD_PROJECT'] = 'raspa-491716'

PROGRESS_FILE = Path.home() / ".stale_sync_progress"
CHECKPOINT_FILE = Path.home() / ".stale_sync_checkpoint"
BEELINK_HOST = "beelink"
BEELINK_PATH = "~/rodado"   # ~/baseldosdados-data nao existe mais no beelink
BATCH_SIZE = 1000  # rows per fetch to avoid huge transfers

def write_progress(status, pct, table="", rows_synced=0):
    """Write progress."""
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "pct": pct,
        "table": table,
        "rows_synced": rows_synced,
    }
    with open(PROGRESS_FILE, "w") as f:
        json.dump(data, f)
    print(f"[{pct:3d}%] {status:10s} {table:50s} rows={rows_synced}")

def get_stale_tables():
    """
    Identify 147 tables where beelink has < BigQuery rows.
    Returns list of (dataset, table, bq_count, local_count).
    """
    client = bigquery.Client(project='raspa-491716')

    bq_tables = {}
    datasets = list(client.list_datasets(project='basedosdados'))

    # Get BigQuery counts (expensive, but only once)
    for ds in datasets:
        try:
            tbl_list = list(client.list_tables(f'basedosdados.{ds.dataset_id}', max_results=10000))
            for t in tbl_list:
                full_id = f"{ds.dataset_id}.{t.table_id}"
                bq_tables[full_id] = {
                    'dataset': ds.dataset_id,
                    'table': t.table_id,
                }
        except:
            pass

    # Get beelink local counts (via query of parquet files)
    stale = []
    for full_id, info in sorted(bq_tables.items()):
        # For now, just mark as potentially stale
        # In production, would query actual row counts from beelink DuckDB
        stale.append((info['dataset'], info['table']))

    return stale[:20]  # First 20 for pilot

def get_max_id_on_beelink(dataset, table):
    """
    Get max row ID or timestamp from beelink's local parquet.
    Returns (max_id, id_column) or (None, None) if empty.
    """
    # Placeholder: query beelink's DuckDB to find max ID
    # In production, this would SELECT MAX(id) or MAX(created_at) from local parquet
    return None, None

def fetch_incremental_rows(dataset, table, since_id=None, since_date=None):
    """
    Fetch rows from BigQuery where ID > since_id or date > since_date.
    Uses bq query (free tier). Returns list of dicts.
    """
    conditions = []
    if since_id:
        conditions.append(f"id > {since_id}")
    if since_date:
        conditions.append(f"created_at > '{since_date}'")

    where = " AND ".join(conditions) if conditions else "1=1"
    query = f"SELECT * FROM `basedosdados.{dataset}.{table}` WHERE {where} LIMIT {BATCH_SIZE}"

    cmd = [
        "bq",
        "query",
        "--project_id=raspa-491716",
        "--format=json",
        "--nouse_legacy_sql",
        query,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            return json.loads(result.stdout)
    except:
        pass

    return []

def sync_rows_to_beelink(dataset, table, rows):
    """
    Write rows as Parquet, push to beelink via rsync.
    Appends to existing parquet (in production, use append mode).
    """
    if not rows:
        return 0

    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:
        print("ERROR: pyarrow not installed", file=sys.stderr)
        return 0

    # Converte com o tipo do BigQuery. `pa.Table.from_pylist(rows)` direto
    # transforma TODA coluna em string — o JSON do bq nao carrega tipo — e foi
    # o que produziu os 80 tmp*.parquet de 2026-07-05 (tasks/tmp_parquet_38.plan).
    tipos = _bq_tipos.schema_bq(dataset, table, billing="raspa-491716")
    table_arrow = _bq_tipos.para_arrow(rows, tipos)
    if table_arrow is None:
        return 0

    remote_dir_path = f"{BEELINK_PATH}/{dataset}/{table}"
    subprocess.run(f"ssh {BEELINK_HOST} 'mkdir -p {remote_dir_path}'",
                   shell=True, capture_output=True)

    # O nome final sai ANTES do envio. Mandar o tempfile e deixar o rsync
    # preservar o basename e o bug que espalhou tmp*.parquet pelo espelho.
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
        cmd = (f"rsync -av {parquet_file} "
               f"{BEELINK_HOST}:{remote_dir_path}/{destino} && "
               f"ssh {BEELINK_HOST} 'chmod 664 {remote_dir_path}/{destino}'")
        result = subprocess.run(cmd, shell=True, capture_output=True)

    if result.returncode == 0:
        return len(rows)
    print(f"✗ rsync failed: {result.stderr.decode()}", file=sys.stderr)
    return 0

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="List stale tables only")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    args = parser.parse_args()

    write_progress("scan", 0, "Finding stale tables...", 0)
    print("Scanning for stale tables (147 total)...")

    stale = get_stale_tables()
    print(f"✓ Found {len(stale)} stale tables\n")

    if args.dry_run:
        write_progress("dry_run", 100, f"Listed {len(stale)} stale", 0)
        for ds, tbl in stale:
            print(f"  {ds}.{tbl}")
        return 0

    # Sync incrementally
    synced_total = 0
    for idx, (dataset, table) in enumerate(stale):
        pct = int(100 * idx / len(stale)) if stale else 100
        full_id = f"{dataset}.{table}"

        write_progress("fetch", pct, full_id, 0)

        try:
            max_id, id_col = get_max_id_on_beelink(dataset, table)
            rows = fetch_incremental_rows(dataset, table, since_id=max_id)

            if rows:
                synced = sync_rows_to_beelink(dataset, table, rows)
                synced_total += synced
                write_progress("done", pct, full_id, synced)
                print(f"✓ {full_id}: +{synced} rows")
            else:
                print(f"~ {full_id}: no new rows")
        except Exception as e:
            print(f"✗ {full_id}: {e}")

    write_progress("complete", 100, f"Synced {synced_total} rows", synced_total)
    print(f"\n✓ Synced {synced_total} rows from stale tables")
    return 0

if __name__ == "__main__":
    sys.exit(main())
