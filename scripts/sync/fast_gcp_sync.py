#!/usr/bin/env python3
"""
Fast GCP→beelink sync: query INFORMATION_SCHEMA for missing tables, fetch via bq query, sync to beelink.
Reports progress every iteration to ~/.gcp_sync_progress.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import tempfile

BQ_PROJECT = "basedosdados"
BEELINK_HOST = "beelink"
BEELINK_PATH = "~/baseldosdados-data"
PROGRESS_FILE = Path.home() / ".gcp_sync_progress"

def write_progress(status, pct, message=""):
    """Write progress to file."""
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "pct": pct,
        "message": message,
    }
    with open(PROGRESS_FILE, "w") as f:
        json.dump(data, f)

def get_bq_tables():
    """Get all tables from BigQuery INFORMATION_SCHEMA."""
    query = """
    SELECT
        table_schema,
        table_name
    FROM `basedosdados.region-us.INFORMATION_SCHEMA.TABLES`
    WHERE table_schema NOT IN ('region-us')
    ORDER BY table_schema, table_name
    """

    cmd = [
        "bq",
        "query",
        "--project_id=" + BQ_PROJECT,
        "--format=json",
        "--nouse_legacy_sql",
        query,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
        return []

    try:
        rows = json.loads(result.stdout)
        return [(r["table_schema"], r["table_name"]) for r in rows]
    except:
        return []

def get_beelink_tables():
    """Get tables that exist on beelink."""
    cmd = f"ssh {BEELINK_HOST} 'find {BEELINK_PATH} -maxdepth 2 -mindepth 2 -type d -printf \"%P\\\\n\"' 2>/dev/null"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    tables = set()
    for line in result.stdout.strip().split("\n"):
        if "/" in line:
            ds, tbl = line.split("/", 1)
            tables.add((ds, tbl))
    return tables

def main():
    write_progress("scanning", 0, "Fetching BigQuery table list...")
    print("Scanning BigQuery INFORMATION_SCHEMA...")

    bq_tables = get_bq_tables()
    if not bq_tables:
        write_progress("error", 0, "Could not fetch BigQuery tables")
        print("Error: Could not fetch BigQuery tables", file=sys.stderr)
        return 1

    write_progress("scanning", 33, "Comparing with beelink...")
    print(f"Found {len(bq_tables)} tables in BigQuery")

    beelink_tables = get_beelink_tables()
    print(f"Found {len(beelink_tables)} tables on beelink")

    missing = [t for t in bq_tables if t not in beelink_tables]

    # Filter out audit logs
    missing = [t for t in missing if t[0] != "logs" or t[1] != "cloudaudit_googleapis_com_data_access"]

    print(f"Missing: {len(missing)} tables")

    if not missing:
        write_progress("done", 100, "No missing tables")
        print("No missing tables to sync")
        return 0

    # Show first 20 missing tables
    for ds, tbl in missing[:20]:
        print(f"  - {ds}.{tbl}")
    if len(missing) > 20:
        print(f"  ... and {len(missing) - 20} more")

    write_progress("ready", 0, f"{len(missing)} tables ready to fetch")
    return 0

if __name__ == "__main__":
    sys.exit(main())
