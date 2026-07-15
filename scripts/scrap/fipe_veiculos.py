#!/usr/bin/env python3
"""
Fetch FIPE (Fundacao Instituto de Pesquisas Economicas) vehicle brand/model
catalog -> Parquet -> beelink.

Source: https://fipe.parallelum.com.br/api/v2 -- the FIPE foundation itself
does not run a public API (its own site, veiculos.fipe.org.br, is an
interactive web app with no clean JSON endpoint); parallelum.com.br is a
long-running (since 2015), widely-used community service that mirrors FIPE's
own data into a clean REST API. No auth required for the base tier: 500
unauthenticated requests per 24h (a free token bumps that to 1,000/day, but
getting one requires signing up -- skipped per this project's "don't
register for credentials" policy, so this script stays anonymous).

Scope note (why this is brands+models, not prices): FIPE's price data is
looked up per (vehicle type, brand, model, model-year), and getting there
requires one API call to list a model's available years, then one more call
per year to get its price. With ~107 car brands, ~102 motorcycle brands and
~29 truck brands, and dozens of models per brand, the combinatorial total
for a genuine full price backfill (all vehicle types x all brands x all
models x all years) is in the tens of thousands of calls -- far beyond the
500/day anonymous budget (would take weeks of staged runs even with the
paid... free token). Since this source was explicitly flagged "low
priority, not corruption-relevant" in the task brief, this script instead
does a genuine full backfill of the CATALOG (every brand and every model,
for cars/motorcycles/trucks) -- that's a bounded ~241 API calls (3 brand
listings + 1 models call per brand), comfortably inside the rate limit, and
still a complete, useful reference table (FIPE codes + names) even without
price history. Price-level data would need a separate, multi-day staged
pipeline and is left out of scope here.

Usage:
    python3 scripts/scrap/fipe_veiculos.py
"""

import subprocess
import sys
import time
from pathlib import Path

import requests

BEELINK_HOST = "beelink"
BEELINK_PATH = "~/rodado/br_fipe_veiculos/precos"

BASE_URL = "https://fipe.parallelum.com.br/api/v2"
VEHICLE_TYPES = ["cars", "motorcycles", "trucks"]
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
TEMP_DIR = Path(
    "/private/tmp/claude-501/-Users-polux-Projetos-rodado/c780c9c0-b6b3-44b0-964e-08a3b2f2024c/scratchpad/fipe"
)


def get_json(session: requests.Session, path: str):
    url = f"{BASE_URL}/{path}"
    for attempt in range(3):
        resp = session.get(url, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 429:
            print(f"    rate limited on {path}, backing off...")
            time.sleep(10)
            continue
        print(f"    unexpected status {resp.status_code} on {path}")
        time.sleep(2)
    return None


def main():
    import pyarrow as pa
    import pyarrow.parquet as pq

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({"User-Agent": UA})

    all_rows = []
    call_count = 0
    for vehicle_type in VEHICLE_TYPES:
        print(f"Fetching {vehicle_type} brands...")
        brands = get_json(session, f"{vehicle_type}/brands")
        call_count += 1
        if not brands:
            print(f"  no brands returned for {vehicle_type}, skipping")
            continue
        print(f"  {len(brands)} brands")

        for brand in brands:
            brand_code = brand["code"]
            brand_name = brand["name"]
            models = get_json(session, f"{vehicle_type}/brands/{brand_code}/models")
            call_count += 1
            if not models:
                continue
            for model in models:
                all_rows.append({
                    "vehicle_type": vehicle_type,
                    "brand_code": brand_code,
                    "brand_name": brand_name,
                    "model_code": model["code"],
                    "model_name": model["name"],
                })
            if call_count % 25 == 0:
                print(f"  ... {call_count} API calls so far, {len(all_rows)} rows collected")
            time.sleep(0.15)  # be polite, stay well under any burst limits

    print(f"\nTotal API calls: {call_count}")
    print(f"Total rows: {len(all_rows)}")
    if not all_rows:
        print("No rows fetched -- aborting, not pushing an empty file.")
        return 1

    table = pa.Table.from_pylist(all_rows)
    parquet_path = TEMP_DIR / "precos.parquet"
    pq.write_table(table, str(parquet_path), compression="zstd")
    print(f"Wrote {parquet_path} ({parquet_path.stat().st_size / 1e6:.1f} MB, {table.num_rows} rows)")

    subprocess.run(f"ssh {BEELINK_HOST} 'mkdir -p {BEELINK_PATH}'", shell=True, check=True)
    result = subprocess.run(
        f"rsync -av {parquet_path} {BEELINK_HOST}:{BEELINK_PATH}/",
        shell=True,
    )
    if result.returncode != 0:
        print("rsync failed", file=sys.stderr)
        return 1

    print(f"Pushed to {BEELINK_HOST}:{BEELINK_PATH}/{parquet_path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
