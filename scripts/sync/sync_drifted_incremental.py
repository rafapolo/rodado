#!/usr/bin/env python3
"""
Incrementally sync row-drift on EXISTING beelink tables (BigQuery has more rows than
beelink's local Parquet). Only pulls rows past beelink's local max on a partition/cluster
column — never a full re-pull. Quota-aware: stops for the month via bq_quota and picks up
where it left off next time (no separate state file — local max is always re-derived live
from beelink's actual Parquet files, so re-running is naturally idempotent).

Tables with no usable partition/cluster column are skipped and logged — there is no cheap
incremental path for those; they need a manual, case-by-case decision.

Usage:
    python3 sync_drifted_incremental.py <drifted_tables.txt>   # one dataset/table per line
"""

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
import bq_quota

BQ_PROJECT = "basedosdados"
JOB_PROJECT = "raspa-491716"
BEELINK_HOST = "beelink"
BEELINK_PATH = "~/baseldosdados-data"
PROGRESS_FILE = Path.home() / ".drift_sync_progress"
TEMP_DIR = Path(tempfile.gettempdir()) / "drift_sync"
MAX_ROWS_PER_BATCH = 5_000_000
MAX_DRY_RUN_BYTES = 3 * 1024**3  # 3GB per single incremental pull

TYPE_CASTERS = {
    "INTEGER": lambda x: int(x) if x else None,
    "INT64": lambda x: int(x) if x else None,
    "FLOAT": lambda x: float(x) if x else None,
    "FLOAT64": lambda x: float(x) if x else None,
    "NUMERIC": lambda x: float(x) if x else None,
    "BOOLEAN": lambda x: x.lower() in ("true", "1") if x else None,
    "BOOL": lambda x: x.lower() in ("true", "1") if x else None,
}

QUOTED_TYPES = {"DATE", "DATETIME", "TIMESTAMP", "STRING"}


class QuotaExhausted(Exception):
    pass


def write_progress(status, table="", message=""):
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {"timestamp": datetime.now().isoformat(), "status": status, "table": table, "message": message}
    PROGRESS_FILE.write_text(json.dumps(data))
    print(f"[{status:14s}] {table:55s} {message}")


def get_table_meta(dataset, table):
    """schema + partition/cluster column choice, via bq show (metadata only, free)."""
    cmd = ["bq", "show", "--project_id=" + BQ_PROJECT, "--format=json", f"{dataset}.{table}"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        # bq show failures are sometimes transient (auth token refresh contention when
        # many bq/gcloud processes run concurrently) — retry once before giving up.
        time.sleep(2)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"  [bq show failed x2] {dataset}.{table}: {result.stderr[:200]}", file=sys.stderr)
            return None
    try:
        info = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  [bad json] {dataset}.{table}: {result.stdout[:200]}", file=sys.stderr)
        return None
    schema = info.get("schema", {}).get("fields", [])

    col = None
    if info.get("timePartitioning", {}).get("field"):
        col = info["timePartitioning"]["field"]
    elif info.get("rangePartitioning", {}).get("field"):
        col = info["rangePartitioning"]["field"]
    elif info.get("clustering", {}).get("fields"):
        col = info["clustering"]["fields"][0]

    if not col:
        return {"schema": schema, "column": None}

    col_type = next((f["type"] for f in schema if f["name"] == col), "STRING")
    return {"schema": schema, "column": col, "column_type": col_type}


def get_local_max(dataset, table, column):
    """Current max value of `column` in beelink's actual Parquet files — always live,
    never cached, so re-runs are automatically incremental from wherever the disk is."""
    remote_path = f"{BEELINK_PATH}/{dataset}/{table}/*.parquet"
    sql = f"SELECT max({column}) as m FROM read_parquet('{remote_path}');"
    cmd = f"ssh {BEELINK_HOST} \"~/bin/duckdb -json -c \\\"{sql}\\\"\""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        return None
    try:
        rows = json.loads(result.stdout)
        return rows[0]["m"] if rows else None
    except (json.JSONDecodeError, IndexError, KeyError):
        return None


def fetch_and_append(dataset, table, column, column_type, local_max):
    full_name = f"{dataset}.{table}"
    val = f"'{local_max}'" if column_type in QUOTED_TYPES else str(local_max)
    where = f"{column} > {val}"
    query = f"SELECT * FROM `{BQ_PROJECT}.{full_name}` WHERE {where} LIMIT {MAX_ROWS_PER_BATCH}"

    dry_cmd = ["bq", "query", "--project_id=" + JOB_PROJECT, "--dry_run", "--format=json", "--nouse_legacy_sql", query]
    try:
        dry = subprocess.run(dry_cmd, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        write_progress("error", full_name, "dry-run timed out")
        return 0
    if dry.returncode != 0:
        write_progress("error", full_name, f"dry-run failed: {dry.stderr[:200]}")
        return 0

    try:
        stats = json.loads(dry.stdout).get("statistics", {})
        bytes_processed = int(stats.get("totalBytesProcessed", 0))
        ref_tables = stats.get("query", {}).get("referencedTables", [])
        is_external = any(t.get("tableType") == "EXTERNAL" for t in ref_tables) if isinstance(ref_tables, list) else False
    except (json.JSONDecodeError, ValueError, AttributeError, TypeError):
        bytes_processed = 0
        is_external = False

    if is_external:
        write_progress("skip_external", full_name, "externally-backed, skipping")
        return 0
    if bytes_processed > MAX_DRY_RUN_BYTES:
        write_progress("skip_big", full_name, f"batch would scan {bytes_processed/1e9:.1f}GB, reduce LIMIT or skip")
        return 0
    if not bq_quota.reserve(bytes_processed):
        write_progress("quota_exhausted", full_name, bq_quota.status())
        raise QuotaExhausted(full_name)

    cmd = ["bq", "query", "--project_id=" + JOB_PROJECT, "--format=json",
           f"--max_rows={MAX_ROWS_PER_BATCH}", "--nouse_legacy_sql", query]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        write_progress("error", full_name, "query timed out")
        return 0
    if result.returncode != 0:
        write_progress("error", full_name, f"query failed: {result.stderr[:200]}")
        return 0

    rows = json.loads(result.stdout)
    return rows


def sync_one(dataset, table, meta):
    full_name = f"{dataset}.{table}"
    column, column_type = meta["column"], meta["column_type"]

    local_max = get_local_max(dataset, table, column)
    if local_max is None:
        write_progress("error", full_name, f"could not read local max({column}) from beelink")
        return "error"

    write_progress("fetching", full_name, f"{column} > {local_max}")
    rows = fetch_and_append(dataset, table, column, column_type, local_max)
    if not rows:
        write_progress("no_new_rows", full_name)
        return "no_new_rows"

    schema_map = {f["name"]: f["type"] for f in meta["schema"]}
    casted = []
    for row in rows:
        casted_row = {}
        for col, v in row.items():
            caster = TYPE_CASTERS.get(schema_map.get(col, "STRING"), lambda x: x)
            try:
                casted_row[col] = caster(v) if v is not None else None
            except (ValueError, TypeError):
                casted_row[col] = v
        casted.append(casted_row)

    import pyarrow as pa
    import pyarrow.parquet as pq

    table_arrow = pa.Table.from_pylist(casted)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    part_name = f"incr_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
    out_path = TEMP_DIR / f"{dataset}_{table}_{part_name}"
    pq.write_table(table_arrow, str(out_path))

    remote_dir = f"{BEELINK_HOST}:{BEELINK_PATH}/{dataset}/{table}"
    rsync_cmd = f"rsync -av {out_path} {remote_dir}/{part_name}"
    result = subprocess.run(rsync_cmd, shell=True, capture_output=True, text=True)
    out_path.unlink()
    if result.returncode != 0:
        write_progress("sync_failed", full_name, result.stderr[:200])
        return "sync_failed"

    write_progress("synced", full_name, f"+{len(rows)} rows")
    return f"+{len(rows)}"


def main():
    if len(sys.argv) < 2:
        print("Usage: sync_drifted_incremental.py <drifted_tables.txt>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        tables = [line.strip().replace("/", ".", 1) for line in f if line.strip()]

    print(f"Drifted tables to check: {len(tables)}")
    print(bq_quota.status())

    results = {}
    for idx, full_name in enumerate(tables):
        dataset, table = full_name.split(".", 1)
        write_progress("checking", full_name, f"[{idx+1}/{len(tables)}]")

        meta = get_table_meta(dataset, table)
        if not meta:
            results[full_name] = "no_schema"
            continue
        if not meta.get("column"):
            write_progress("no_partition_column", full_name, "no timePartitioning/rangePartitioning/clustering — needs manual handling")
            results[full_name] = "no_partition_column"
            continue

        try:
            results[full_name] = sync_one(dataset, table, meta)
        except QuotaExhausted:
            remaining = tables[idx:]
            print(f"\n⏸ Monthly quota exhausted. {len(remaining)} tables deferred to next run.")
            for t in remaining:
                results.setdefault(t, "deferred_quota")
            break
        except Exception as e:
            write_progress("error", full_name, str(e))
            results[full_name] = f"error:{e}"

    print(f"\n{bq_quota.status()}")
    log_path = TEMP_DIR / "drift_results.tsv"
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w") as f:
        for t, r in results.items():
            f.write(f"{t}\t{r}\n")
    print(f"Results: {log_path}")

    no_partition = [t for t, r in results.items() if r == "no_partition_column"]
    if no_partition:
        print(f"\n{len(no_partition)} tables have no usable partition/cluster column — need manual handling:")
        for t in no_partition:
            print(f"  {t}")


if __name__ == "__main__":
    main()
