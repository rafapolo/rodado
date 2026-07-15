#!/usr/bin/env python3
"""
Fetch BPS (Boletim de Precos em Saude) purchase records -> Parquet -> beelink.

API: https://apidadosabertos.saude.gov.br/economia-da-saude/bps
No auth. Page size up to 1000 confirmed working (unlike the CNES
estabelecimentos endpoint, which hard-caps at 20). Total rows empirically
between 300k-320k (offset=300000 non-empty, offset=350000 empty), so this
paginates concurrently via a thread pool with limit=1000 pages.

Usage:
    python3 scripts/scrap/saude_bps.py
"""

import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import Request, urlopen
import json

BEELINK_HOST = "beelink"
BEELINK_PATH = "~/rodado/br_saude_bps/dados"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
TEMP_DIR = Path("/private/tmp/claude-501/-Users-polux-Projetos-rodado/50905fb8-827b-445f-bb28-3e8ed468da54/scratchpad/bps")

BASE_URL = "https://apidadosabertos.saude.gov.br/economia-da-saude/bps"
PAGE_SIZE = 1000
MAX_OFFSET = 344000  # safety cap; true total confirmed 342716 (offset=345000 empty)
WORKERS = 12


def fetch_page(offset: int):
    url = f"{BASE_URL}?limit={PAGE_SIZE}&offset={offset}"
    req = Request(url, headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            with urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read())
            return data.get("bps", [])
        except Exception as e:
            if attempt == 2:
                print(f"  offset {offset}: giving up ({e})")
                return []
            time.sleep(1 + attempt)
    return []


def main():
    import pyarrow as pa
    import pyarrow.parquet as pq

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    offsets = list(range(0, MAX_OFFSET, PAGE_SIZE))
    rows = []
    empty_offsets = set()

    print(f"Fetching BPS records with {WORKERS} workers, page size {PAGE_SIZE} ...")
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = {ex.submit(fetch_page, off): off for off in offsets}
        done_count = 0
        for fut in as_completed(futures):
            off = futures[fut]
            page = fut.result()
            done_count += 1
            if not page:
                empty_offsets.add(off)
            else:
                rows.extend(page)
            if done_count % 50 == 0:
                print(f"  ... {done_count}/{len(offsets)} pages fetched, {len(rows)} rows so far")

    print(f"\nTotal rows fetched: {len(rows)} (from {len(offsets) - len(empty_offsets)} non-empty pages)")
    if not rows:
        print("No rows fetched — aborting.")
        return 1

    table = pa.Table.from_pylist(rows)
    parquet_path = TEMP_DIR / "bps.parquet"
    pq.write_table(table, str(parquet_path), compression="zstd")
    print(f"Wrote {parquet_path} ({parquet_path.stat().st_size / 1e6:.1f} MB)")

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
