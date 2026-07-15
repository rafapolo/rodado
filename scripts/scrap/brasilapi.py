#!/usr/bin/env python3
"""
Fetch BrasilAPI reference/utility endpoints -> Parquet -> beelink.

Small, static/near-static tables: banks, DDD-to-cities, yearly holidays,
current benchmark rates. Each becomes its own table under the same dataset.
Explicitly excludes lookup-shaped endpoints (CEP, CNPJ, ISBN) — those have no
"full table" to mirror and are better served as live mcp_server.py tools
(see tasks/datasets_to_scrap.md's "mcp-live candidates" section).

Usage:
    python3 scripts/scrap/brasilapi.py
"""

import subprocess
import sys
import time
import urllib.request
import json
from pathlib import Path
from urllib.error import HTTPError

BEELINK_HOST = "beelink"
DATASET_PATH = "~/rodado/br_brasilapi"
BEELINK_PATH = f"{DATASET_PATH}/bancos"  # primary/representative table for sync_scraped_datasets.py
BASE = "https://brasilapi.com.br/api"
TEMP_DIR = Path("/private/tmp/claude-501/-Users-polux-Projetos-rodado/50905fb8-827b-445f-bb28-3e8ed468da54/scratchpad/brasilapi")


def get_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (rodado-scraper)"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def fetch_banks():
    return get_json(f"{BASE}/banks/v1")


def fetch_ddd():
    rows = []
    for ddd in range(11, 100):
        try:
            data = get_json(f"{BASE}/ddd/v1/{ddd}")
            for city in data.get("cities", []):
                rows.append({"ddd": ddd, "state": data.get("state"), "city": city})
        except HTTPError:
            pass  # not every 2-digit number is a valid DDD
        time.sleep(0.05)
    return rows


def fetch_feriados():
    rows = []
    for year in range(2020, 2028):
        try:
            data = get_json(f"{BASE}/feriados/v1/{year}")
            for h in data:
                h["year"] = year
                rows.append(h)
        except HTTPError:
            pass
        time.sleep(0.1)
    return rows


def fetch_taxas():
    return get_json(f"{BASE}/taxas/v1")


TABLES = {
    "bancos": fetch_banks,
    "ddd_cidades": fetch_ddd,
    "feriados": fetch_feriados,
    "taxas_referencia": fetch_taxas,
}


def main():
    import pyarrow as pa
    import pyarrow.parquet as pq

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    written = {}
    for table_name, fetch_fn in TABLES.items():
        print(f"Fetching {table_name} ...")
        rows = fetch_fn()
        if not rows:
            print(f"  ⚠ {table_name}: 0 rows, skipping")
            continue
        table = pa.Table.from_pylist(rows)
        parquet_path = TEMP_DIR / f"{table_name}.parquet"
        pq.write_table(table, str(parquet_path), compression="zstd")
        written[table_name] = (parquet_path, table.num_rows)
        print(f"  ✓ {table_name}: {table.num_rows} rows")

    if not written:
        print("No tables written — aborting.")
        return 1

    for table_name, (parquet_path, rows) in written.items():
        remote_dir = f"{DATASET_PATH}/{table_name}"
        subprocess.run(f"ssh {BEELINK_HOST} 'mkdir -p {remote_dir}'", shell=True, check=True)
        result = subprocess.run(f"rsync -av {parquet_path} {BEELINK_HOST}:{remote_dir}/", shell=True)
        if result.returncode != 0:
            print(f"  ✗ rsync failed for {table_name}")
            return 1
        print(f"  ✓ pushed {table_name} ({rows} rows)")

    print(f"\nDone: {len(written)} tables pushed to {BEELINK_HOST}:{DATASET_PATH}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
