#!/usr/bin/env python3
"""
sync_bq_to_local.py

Syncs missing tables from BigQuery (basedosdados project) to Hetzner S3,
then registers them as DuckDB views.

Usage:
    python3 sync_bq_to_local.py              # full sync
    python3 sync_bq_to_local.py --dry-run    # list missing tables only
    python3 sync_bq_to_local.py --resume      # resume from last run

Prerequisites:
    gcloud auth application-default login
    GCP project with billing enabled (free tier: 1 TB/month)

Environment (.env):
    GCP_PROJECT          - GCP project ID for billing
    HETZNER_S3_BUCKET   - S3 bucket name
    HETZNER_S3_ENDPOINT - S3 endpoint URL
    AWS_ACCESS_KEY_ID    - S3 access key
    AWS_SECRET_ACCESS_KEY - S3 secret key
"""

import os
import sys
import json
import argparse
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3
from botocore.config import Config as BotoConfig
from google.cloud import bigquery

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_FILE = f"sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SOURCE_PROJECT = "basedosdados"
MISSING_TABLES_FILE = "tasks/datasets_to_scrap.md"
DONE_FILE = "done_sync.txt"
FAILED_FILE = "failed_sync.txt"
DATA_DIR = "data"
PARQUET_DIR = "parquet"
MAX_RETRIES = 3
BATCH_SIZE = 1  # export one table at a time to manage memory
WORKERS = 4  # parallel uploads

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_env():
    """Load required environment variables."""
    from dotenv import load_dotenv
    load_dotenv()

    required = [
        "GCP_PROJECT",
        "HETZNER_S3_BUCKET",
        "HETZNER_S3_ENDPOINT",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
    ]
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        log.error("Missing env vars: %s", missing)
        sys.exit(1)

    return {v: os.environ[v] for v in required}


def get_s3_client(env):
    """Create boto3 S3 client configured for Hetzner."""
    return boto3.client(
        "s3",
        endpoint_url=env["HETZNER_S3_ENDPOINT"],
        aws_access_key_id=env["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=env["AWS_SECRET_ACCESS_KEY"],
        config=BotoConfig(s3={"addressing_style": "path"}),
    )


def get_bq_client():
    """Create BigQuery client using Application Default Credentials."""
    try:
        os.environ["GOOGLE_CLOUD_PROJECT"] = os.environ.get("GCP_PROJECT", "")
        os.environ["GCLOUD_PROJECT"] = os.environ.get("GCP_PROJECT", "")
        client = bigquery.Client(project=os.environ.get("GCP_PROJECT", ""))
        # Test the connection
        list(client.list_datasets(max_results=1))
        return client
    except Exception as e:
        log.error("BigQuery auth failed: %s", e)
        log.error("")
        log.error("Run these commands to authenticate:")
        log.error("  gcloud auth login")
        log.error("  gcloud auth application-default login")
        log.error("  gcloud config set project %s", os.environ.get("GCP_PROJECT", ""))
        log.error("")
        log.error("The free tier (1 TB/month) is sufficient — no credit card needed.")
        sys.exit(1)


def list_bq_tables(bq_client):
    """List all tables in the basedosdados BigQuery project."""
    log.info("Discovering tables in BigQuery project: %s", SOURCE_PROJECT)
    tables = {}

    try:
        datasets = list(bq_client.list_datasets())
        log.info("Found %d datasets", len(datasets))
    except Exception as e:
        log.error("Failed to list datasets: %s", e)
        sys.exit(1)

    for dataset in datasets:
        try:
            tables_list = list(
                bq_client.list_tables(
                    f"{SOURCE_PROJECT}.{dataset.dataset_id}",
                    max_results=10000,
                )
            )
            for t in tables_list:
                tables[f"{dataset.dataset_id}.{t.table_id}"] = {
                    "dataset": dataset.dataset_id,
                    "table": t.table_id,
                    "full_id": f"{SOURCE_PROJECT}.{dataset.dataset_id}.{t.table_id}",
                    "schema": [f.name for f in t.schema] if t.schema else [],
                    "num_bytes": t.num_bytes,
                    "num_rows": t.num_rows,
                }
        except Exception as e:
            log.warning("Failed to list tables in dataset %s: %s", dataset.dataset_id, e)

    log.info("Total BigQuery tables discovered: %d", len(tables))
    return tables


def list_s3_tables(s3_client, bucket):
    """List datasets/tables already exported to S3."""
    log.info("Discovering tables already in S3 bucket: %s", bucket)
    table_files = defaultdict(lambda: defaultdict(list))

    try:
        paginator = s3_client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if not key.endswith(".parquet"):
                    continue
                parts = key.split("/")
                if len(parts) >= 3:
                    dataset, table = parts[0], parts[1]
                    table_files[dataset][table].append(key)
    except Exception as e:
        log.warning("S3 listing error (may be empty bucket): %s", e)

    tables = {}
    for dataset, t_dict in table_files.items():
        for table, files in t_dict.items():
            tables[f"{dataset}.{table}"] = files

    log.info("Total S3 tables discovered: %d", len(tables))
    return tables


def parse_missing_tables_from_md(filepath):
    """Parse the missing tables from tasks/datasets_to_scrap.md.

    Returns a dict mapping 'dataset.table' -> description.
    Falls back to None (use all non-S3 tables) if file not found.
    """
    if not os.path.exists(filepath):
        log.warning("Missing file %s, using all non-S3 tables", filepath)
        return None

    log.info("Parsing missing tables from %s", filepath)
    with open(filepath) as f:
        content = f.read()

    missing = {}
    lines = content.split("\n")
    i = 0

    def next_nonempty(lines, i):
        while i < len(lines) and not lines[i].strip():
            i += 1
        return i

    while i < len(lines):
        line = lines[i].strip()

        # Find the Basedosdados.org section
        if "Basedosdados.org" in line and "Not in basedosdados.duckdb" in line:
            log.info("Found Basedosdados.org section at line %d", i + 1)
            i += 1
            break
        i += 1

    # Now parse table entries
    while i < len(lines):
        line = lines[i].strip()

        # End of section only on top-level ## headers, not ### subsections
        if line.startswith("## "):
            break

        # Skip separators and empty lines
        if not line or line.startswith("---") or "|---" in line:
            i += 1
            continue

        # Find rows with backtick-wrapped dataset names (e.g. | `br_abrinq_oca` | ...)
        if "`" in line and "|" in line:
            # Split by pipe, strip whitespace and backticks
            parts = [p.strip().strip("`").strip() for p in line.split("|")]
            # Filter empty parts
            parts = [p for p in parts if p]

            if len(parts) >= 2:
                dataset_raw = parts[0]
                # Check if it looks like a dataset name (br_*, eu_*, mundo_*, etc.)
                is_dataset = any(
                    dataset_raw.startswith(prefix)
                    for prefix in ("br_", "eu_", "mundo_", "nl_", "world_")
                )

                if is_dataset:
                    # parts[1] contains the missing table names (comma-separated)
                    tables_raw = parts[1]
                    for tbl in tables_raw.split(","):
                        tbl = tbl.strip()
                        # Clean up: remove parenthetical notes, trailing text
                        if "(" in tbl:
                            tbl = tbl.split("(")[0].strip()
                        if tbl and not tbl.startswith("-"):
                            missing[f"{dataset_raw}.{tbl}"] = f"from {filepath}"

        i += 1

    log.info("Parsed %d missing table references from MD", len(missing))
    return missing if missing else None


def compute_missing_tables(bq_tables, s3_tables, md_missing):
    """Compute which tables need to be synced."""
    if md_missing is None:
        log.info("No MD file, computing diff: BQ - S3")
        return [
            (table_id, info)
            for table_id, info in bq_tables.items()
            if table_id not in s3_tables
        ]

    log.info("Computing sync targets: MD missing tables not in S3")
    targets = []
    for key, info in bq_tables.items():
        if key in s3_tables:
            continue
        if key in md_missing:
            targets.append((key, info))
        else:
            # Table not in S3 but not in MD missing list
            # Check if its dataset is partially covered
            dataset = info["dataset"]
            table = info["table"]
            # If any table from this dataset is in MD missing, include it
            dataset_in_md = any(
                k.startswith(f"{dataset}.") and k.split(".", 1)[1] in md_missing
                for k in bq_tables
            )
            if not dataset_in_md:
                targets.append((key, info))

    return targets


def estimate_size_mb(num_bytes):
    """Estimate size in MB."""
    if num_bytes is None:
        return "?"
    return f"{num_bytes / 1_048_576:.1f}"


# ---------------------------------------------------------------------------
# Export logic
# ---------------------------------------------------------------------------

def sync_table(args, table_id, info, dry_run=False):
    """Sync a single table: BQ → parquet → S3 → DuckDB view."""
    bq_client, s3_client, bucket = args
    dataset = info["dataset"]
    table = info["table"]
    full_id = info["full_id"]

    s3_key_prefix = f"{dataset}/{table}"

    if dry_run:
        size_mb = estimate_size_mb(info.get("num_bytes"))
        return True, f"[DRY] {dataset}.{table} (~{size_mb} MB)"

    # Step 1: Query from BigQuery
    log.info("Querying %s from BigQuery", full_id)
    query = f"SELECT * FROM `{full_id}`"

    try:
        query_job = bq_client.query(query, location="US")
        df = query_job.to_dataframe()
    except Exception as e:
        return False, f"BQ query failed for {table_id}: {e}"

    if df.empty:
        return True, f"[SKIP] {table_id} — empty table"

    if df.shape[0] > 10_000_000:
        log.warning("Table %s has %d rows — may be slow/memory-intensive", table_id, df.shape[0])

    # Step 2: Write to parquet in memory, then upload
    import io
    import pyarrow as pa
    import pyarrow.parquet as pq

    buffer = io.BytesIO()
    table_pa = pa.Table.from_pandas(df)

    # Write with zstd compression
    writer = pq.ParquetWriter(
        buffer,
        table_pa.schema,
        compression="zstd",
        use_dictionary=True,
    )
    writer.write_table(table_pa)
    writer.close()
    buffer.seek(0)

    s3_key = f"{s3_key_prefix}/{table}.parquet"
    log.info("Uploading %s → s3://%s/%s (%s, %d rows)",
             table_id, bucket, s3_key,
             f"{buffer.getbuffer().nbytes / 1_048_576:.1f} MB",
             df.shape[0])

    try:
        s3_client.upload_fileobj(
            buffer,
            bucket,
            s3_key,
            ExtraArgs={"ContentType": "application/octet-stream"},
        )
    except Exception as e:
        return False, f"S3 upload failed for {table_id}: {e}"

    log.info("[DONE] %s uploaded to s3://%s/%s", table_id, bucket, s3_key)
    return True, f"[DONE] {table_id}"


def update_duckdb_view(env, table_id, info):
    """Register a new table as a DuckDB view over S3 parquet."""
    import duckdb

    dataset = info["dataset"]
    table = info["table"]
    bucket = env["HETZNER_S3_BUCKET"]
    endpoint = env["HETZNER_S3_ENDPOINT"].removeprefix("https://").removeprefix("http://")
    access_key = env["AWS_ACCESS_KEY_ID"]
    secret_key = env["AWS_SECRET_ACCESS_KEY"]

    # S3 path
    s3_path = f"s3://{bucket}/{dataset}/{table}/{table}.parquet"

    try:
        con = duckdb.connect("basedosdados.duckdb", read_only=False)
        con.execute("INSTALL httpfs; LOAD httpfs;")
        con.execute(f"SET s3_endpoint='{endpoint}';")
        con.execute(f"SET s3_access_key_id='{access_key}';")
        con.execute(f"SET s3_secret_access_key='{secret_key}';")
        con.execute(f"SET s3_url_style='path';")
        con.execute(f"CREATE SCHEMA IF NOT EXISTS {dataset}")
        con.execute(f"""
            CREATE OR REPLACE VIEW {dataset}.{table} AS
            SELECT * FROM read_parquet('{s3_path}', hive_partitioning=true, union_by_name=true)
        """)
        con.close()
        log.info("[DUCKDB] View created: %s.%s", dataset, table)
        return True, None
    except Exception as e:
        log.error("[DUCKDB] Failed to create view %s.%s: %s", dataset, table, e)
        return False, str(e)


def run_sync(targets, args, env, dry_run=False, resume=False):
    """Run the sync for all target tables."""
    s3_client = get_s3_client(env)
    bq_client = get_bq_client()

    # Load done/failed tracking
    done_set = set()
    if resume:
        if os.path.exists(DONE_FILE):
            with open(DONE_FILE) as f:
                done_set = {l.strip() for l in f if l.strip()}
            log.info("Resuming: %d tables already done", len(done_set))

    failed_count = 0
    done_count = 0

    # Filter out already-done tables
    targets = [(tid, info) for tid, info in targets if tid not in done_set]

    if not targets:
        log.info("No tables to sync.")
        return 0, 0

    log.info("Syncing %d tables...", len(targets))

    for i, (table_id, info) in enumerate(targets, 1):
        log.info("--- [%d/%d] Syncing %s ---", i, len(targets), table_id)

        # Sync BQ → S3
        ok, msg = sync_table(
            (bq_client, s3_client, env["HETZNER_S3_BUCKET"]),
            table_id,
            info,
            dry_run=dry_run,
        )
        log.info(msg)

        if dry_run:
            continue

        if not ok:
            with open(FAILED_FILE, "a") as f:
                f.write(f"{table_id}\t{msg}\n")
            failed_count += 1
            continue

        if "empty" in msg.lower():
            continue

        # Update DuckDB view
        ok, err = update_duckdb_view(env, table_id, info)
        if not ok:
            with open(FAILED_FILE, "a") as f:
                f.write(f"{table_id}\tDUCKDB: {err}\n")

        # Mark done
        with open(DONE_FILE, "a") as f:
            f.write(f"{table_id}\n")
        done_count += 1

    return done_count, failed_count


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Sync missing BQ tables to S3")
    parser.add_argument("--dry-run", action="store_true", help="List tables without syncing")
    parser.add_argument("--resume", action="store_true", help="Resume from last run")
    args = parser.parse_args()

    env = load_env()
    dry_run = args.dry_run

    if dry_run:
        log.info("=== DRY RUN MODE ===")

    # Step 1: List BigQuery tables
    bq_client = get_bq_client()
    bq_tables = list_bq_tables(bq_client)

    # Step 2: List S3 tables
    s3_client = get_s3_client(env)
    s3_tables = list_s3_tables(s3_client, env["HETZNER_S3_BUCKET"])

    # Step 3: Parse missing tables from MD
    md_missing = parse_missing_tables_from_md(MISSING_TABLES_FILE)

    # Step 4: Compute targets
    targets = compute_missing_tables(bq_tables, s3_tables, md_missing)

    if not targets:
        log.info("No tables to sync.")
        return

    log.info("")
    log.info("============================================")
    log.info(" Tables to sync: %d", len(targets))
    log.info("============================================")
    for i, (table_id, info) in enumerate(targets, 1):
        size_mb = estimate_size_mb(info.get("num_bytes"))
        md_note = md_missing.get(table_id, "")
        log.info("  [%d] %-50s %6s MB  %s", i, table_id, size_mb, md_note)
    log.info("")

    if dry_run:
        total_bytes = sum(info.get("num_bytes", 0) or 0 for _, info in targets)
        total_gb = total_bytes / 1_073_741_824
        log.info("Total estimated size: %.2f GB (BigQuery compressed bytes)", total_gb)
        log.info("Run without --dry-run to start syncing.")
        return

    # Step 5: Run sync
    log.info("Starting sync...")
    done_count, failed_count = run_sync(targets, None, env, dry_run=False, resume=args.resume)

    log.info("")
    log.info("============================================")
    log.info(" Sync complete!")
    log.info(" Done:    %d tables", done_count)
    log.info(" Failed:  %d tables", failed_count)
    log.info(" Log:     %s", LOG_FILE)
    log.info("============================================")

    if failed_count > 0:
        log.info("Failed tables: see %s", FAILED_FILE)
        sys.exit(1)


if __name__ == "__main__":
    main()
