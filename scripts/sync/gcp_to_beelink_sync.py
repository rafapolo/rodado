#!/usr/bin/env python3
"""
Fetch 247 missing tables from BigQuery → convert to Parquet → sync to beelink.
Uses bq query (Sandbox free) instead of bq extract (needs billing).
Writes progress to ~/.gcp_sync_progress for 2-min loop polling.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

sys.path.insert(0, str(Path(__file__).parent))
import bq_quota
import _bq_tipos

# Config
BQ_PROJECT = "basedosdados"      # public data source — metadata reads only (bq ls/bq show)
JOB_PROJECT = "raspa-491716"     # project that actually runs the query job (Sandbox free tier, no billing)
BEELINK_HOST = "beelink"
BEELINK_PATH = "~/rodado"   # ~/baseldosdados-data nao existe mais no beelink
PROGRESS_FILE = Path.home() / ".gcp_sync_progress"
TEMP_DIR = Path(tempfile.gettempdir()) / "gcp_sync"
MAX_ROWS = 10000000  # Safe default for Sandbox
MAX_ROWS_SAFE = 10000000  # tables above this row count are skipped (too big for a single JSON pull) — matches MAX_ROWS, no point being stricter than the actual fetch cap
MAX_DRY_RUN_BYTES = 3 * 1024**3  # 3GB — views report numRows=0 so we gate on actual scan bytes instead

# A conversao de tipo vive em `_bq_tipos.para_arrow`. O bloco TYPE_CASTERS que estava
# aqui castava INT/FLOAT/BOOL mas deixava DATE/DATETIME/TIMESTAMP como string e ainda
# dependia da inferencia do pyarrow para montar o schema — uma coluna toda nula saia
# como null. Agora o tipo do BigQuery decide o tipo Arrow, coluna a coluna.

class QuotaExhausted(Exception):
    """Raised when the monthly BigQuery Sandbox scan budget would be exceeded."""
    pass

def write_progress(status, pct, message=""):
    """Write progress to file for 2-min loop to read."""
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "pct": pct,
        "message": message,
    }
    with open(PROGRESS_FILE, "w") as f:
        json.dump(data, f)

def list_bq_tables():
    """Get all table names from BigQuery basedosdados project."""
    cmd = [
        "bq",
        "ls",
        "--project_id=" + BQ_PROJECT,
        "-n", "999999",
        "--format=json",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"bq ls failed: {result.stderr}")

    tables = []
    try:
        datasets = json.loads(result.stdout)
    except json.JSONDecodeError:
        datasets = []

    for ds_entry in datasets:
        dataset = ds_entry.get("datasetReference", {}).get("datasetId")
        if not dataset:
            continue
        # List tables in each dataset
        cmd2 = [
            "bq",
            "ls",
            "--project_id=" + BQ_PROJECT,
            "-n", "999999",
            "--format=json",
            dataset,
        ]
        result2 = subprocess.run(cmd2, capture_output=True, text=True)
        if result2.returncode == 0 and result2.stdout.strip():
            try:
                tbl_list = json.loads(result2.stdout)
            except json.JSONDecodeError:
                print(f"⊘ Dataset {dataset}: malformed JSON", file=sys.stderr)
                continue
            for tbl in tbl_list:
                table_name = tbl.get("tableReference", {}).get("tableId")
                tbl_type = tbl.get("type", "TABLE")
                if table_name and tbl_type in ("TABLE", "VIEW"):
                    tables.append(f"{dataset}.{table_name}")

    return sorted(tables)

def list_beelink_tables():
    """Get table dirs that exist on beelink."""
    cmd = f"ssh {BEELINK_HOST} 'find {BEELINK_PATH} -maxdepth 2 -mindepth 2 -type d -printf \"%P\\\\n\"'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        return set()

    tables = set()
    for line in result.stdout.strip().split("\n"):
        if "/" in line:
            ds, tbl = line.split("/", 1)
            tables.add(f"{ds}.{tbl}")
    return tables

def get_table_info(dataset, table):
    """Get BigQuery table schema + row count + type (metadata read, no job)."""
    cmd = [
        "bq",
        "show",
        "--project_id=" + BQ_PROJECT,
        "--format=json",
        f"{dataset}.{table}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None, 0, None

    info = json.loads(result.stdout)
    schema = info.get("schema", {}).get("fields", [])
    num_rows = int(info.get("numRows", 0) or 0)
    tbl_type = info.get("type", "TABLE")
    return schema, num_rows, tbl_type

def fetch_table_parquet(dataset, table, schema):
    """Fetch table from BigQuery via bq query, cast types, save as Parquet."""
    full_name = f"{dataset}.{table}"

    write_progress("fetching", 0, f"Querying {full_name}...")

    # Dry-run first: views report numRows=0 in `bq show`, so this is the only way
    # to know actual scan cost before committing to a real (potentially huge) pull.
    dry_cmd = [
        "bq", "query",
        "--project_id=" + JOB_PROJECT,
        "--dry_run",
        "--format=json",
        "--nouse_legacy_sql",
        f"SELECT * FROM `{BQ_PROJECT}.{full_name}` LIMIT {MAX_ROWS}",
    ]
    try:
        dry_result = subprocess.run(dry_cmd, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        write_progress("error", 0, f"Dry-run timed out: {full_name}")
        return None
    if dry_result.returncode != 0:
        write_progress("error", 0, f"Dry-run failed: {full_name}: {dry_result.stderr[:200]}")
        return None
    try:
        stats = json.loads(dry_result.stdout).get("statistics", {})
        bytes_processed = int(stats.get("totalBytesProcessed", 0))
        # EXTERNAL-backed tables (e.g. Sheets/GCS source, not native BQ storage) report a
        # meaningless LOWER_BOUND estimate — bytes_processed=0 does NOT mean "cheap" here.
        ref_tables = stats.get("query", {}).get("referencedTables", [])
        is_external = any(t.get("tableType") == "EXTERNAL" for t in ref_tables) if isinstance(ref_tables, list) else False
    except (json.JSONDecodeError, ValueError, AttributeError, TypeError):
        bytes_processed = 0
        is_external = False
    if bytes_processed > MAX_DRY_RUN_BYTES:
        write_progress("skip_big", 0, f"{full_name}: dry-run {bytes_processed/1e9:.1f}GB, skipping")
        return None
    if is_external:
        write_progress("skip_external", 0, f"{full_name}: externally-backed table, cost unpredictable, skipping")
        return None

    if not bq_quota.reserve(bytes_processed):
        write_progress("quota_exhausted", 0, f"{full_name}: would need {bytes_processed/1e9:.2f}GB, {bq_quota.status()}")
        raise QuotaExhausted(full_name)

    # Job runs under JOB_PROJECT (Sandbox free tier, no billing account needed);
    # table ref is fully qualified so it still reads from the public basedosdados source.
    # Hard timeout guards against any query that dry-run underestimated.
    cmd = [
        "bq",
        "query",
        "--project_id=" + JOB_PROJECT,
        "--format=json",
        f"--max_rows={MAX_ROWS}",
        "--nouse_legacy_sql",
        f"SELECT * FROM `{BQ_PROJECT}.{full_name}` LIMIT {MAX_ROWS}",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        write_progress("error", 0, f"Query timed out: {full_name}")
        return None
    if result.returncode != 0:
        write_progress("error", 0, f"Query failed: {full_name}: {result.stderr[:200]}")
        return None

    rows = json.loads(result.stdout)
    if not rows:
        write_progress("empty", 0, f"No rows: {full_name}")
        return None

    # → Parquet, com o tipo declarado pelo BigQuery. O schema ja veio do `bq show`
    # em `get_table_info`, entao nao ha chamada extra: REPEATED/RECORD viram None e
    # `para_arrow` os deixa como string, igual ao `schema_bq`.
    try:
        import pyarrow.parquet as pq
    except ImportError:
        write_progress("error", 0, "pyarrow not installed")
        return None

    tipos = {
        f["name"]: (None if f.get("mode") == "REPEATED" or f["type"] == "RECORD"
                    else f["type"])
        for f in schema
    }
    table_arrow = _bq_tipos.para_arrow(rows, tipos)
    if table_arrow is None:
        write_progress("empty", 0, f"No rows: {full_name}")
        return None

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    out_path = TEMP_DIR / f"{dataset}_{table}.parquet"
    pq.write_table(table_arrow, str(out_path), compression="zstd")

    return out_path

def sync_to_beelink(dataset, table, parquet_path):
    """Sync Parquet file to beelink, com o nome de destino resolvido antes do envio.

    O rsync preserva o basename da origem. As views do beelink enumeram os parquet
    um a um (nao usam glob), entao um shard fora da convencao `0000000000NN.parquet`
    entra no diretorio sem que a view o cite — e a consulta responde a menos, calada.
    """
    remote_dir_path = f"{BEELINK_PATH}/{dataset}/{table}"

    # Ensure dir on beelink
    subprocess.run(
        f"ssh {BEELINK_HOST} 'mkdir -p {remote_dir_path}'",
        shell=True,
        capture_output=True,
    )

    existentes = subprocess.run(
        f"ssh {BEELINK_HOST} 'ls {remote_dir_path} 2>/dev/null'",
        shell=True, capture_output=True, text=True,
    ).stdout.split()
    destino = _bq_tipos.nome_destino(existentes)

    cmd = f"rsync -av {parquet_path} {BEELINK_HOST}:{remote_dir_path}/{destino}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode == 0

def main():
    write_progress("init", 0, "Listing tables...")

    if len(sys.argv) > 1:
        # Reuse a precomputed missing-table list (dataset/table per line) instead of
        # re-enumerating all ~180 datasets live.
        with open(sys.argv[1]) as f:
            missing = sorted(
                line.strip().replace("/", ".", 1)
                for line in f
                if line.strip()
            )
    else:
        bq_tables = set(list_bq_tables())
        beelink_tables = list_beelink_tables()
        bq_tables.discard("logs.cloudaudit_googleapis_com_data_access")
        missing = sorted(bq_tables - beelink_tables)

    print(f"Missing (to fetch): {len(missing)}")
    write_progress("starting", 0, f"Starting sync of {len(missing)} tables")

    success = 0
    skipped = []
    for idx, table in enumerate(missing):
        pct = int(100 * idx / len(missing)) if missing else 0
        dataset, tblname = table.split(".", 1)

        write_progress("syncing", pct, f"[{idx+1}/{len(missing)}] {table}")

        try:
            schema, num_rows, tbl_type = get_table_info(dataset, tblname)
            if not schema:
                print(f"⊘ {table}: no schema (missing/inaccessible)")
                skipped.append((table, "no_schema"))
                continue

            if num_rows > MAX_ROWS_SAFE:
                print(f"⊘ {table}: {num_rows} rows, too big for single-shot query, skipping")
                skipped.append((table, f"too_big:{num_rows}"))
                continue

            parquet_path = fetch_table_parquet(dataset, tblname, schema)
            if not parquet_path:
                print(f"⊘ {table}: fetch failed (likely access-denied view)")
                skipped.append((table, "fetch_failed"))
                continue

            if sync_to_beelink(dataset, tblname, parquet_path):
                print(f"✓ {table}")
                success += 1
                parquet_path.unlink()
            else:
                print(f"⊘ {table}: sync failed")
                skipped.append((table, "sync_failed"))
        except QuotaExhausted:
            remaining = missing[idx:]
            print(f"\n⏸ Monthly Sandbox quota exhausted ({bq_quota.status()}).")
            print(f"  Stopping here — {len(remaining)} tables deferred to next month's quota.")
            skipped.extend((t, "deferred_quota") for t in remaining)
            break
        except Exception as e:
            print(f"⊘ {table}: {e}")
            skipped.append((table, str(e)))

    write_progress("done", 100, f"Synced {success}/{len(missing)}")
    print(f"\nDone: {success}/{len(missing)} tables synced, {len(skipped)} skipped")
    if success:
        print("agora rode: python3 scripts/repara_views_beelink.py --apply")
    print(bq_quota.status())
    if skipped:
        skip_log = TEMP_DIR / "skipped.txt"
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with open(skip_log, "w") as f:
            for table, reason in skipped:
                f.write(f"{table}\t{reason}\n")
        print(f"Skipped table list: {skip_log}")

if __name__ == "__main__":
    main()
