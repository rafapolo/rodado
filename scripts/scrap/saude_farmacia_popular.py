#!/usr/bin/env python3
"""
Fetch Farmacia Popular-participating establishments (CNES estabelecimentos,
filtered to codigo_tipo_unidade=43 = pharmacy-type units, which is how
pharmacies enrolled in the Farmacia Popular program show up in the national
health-facility registry) -> Parquet -> beelink.

API: https://apidadosabertos.saude.gov.br/cnes/estabelecimentos
No auth. Page size is hard-capped at 20 regardless of the `limit` param
requested (confirmed empirically: limit=5000 still returns 20 rows), and total
rows for this filter is ~30-35k, so this fetches ~1500+ pages concurrently via
a thread pool to stay within a reasonable run time.

Usage:
    python3 scripts/scrap/saude_farmacia_popular.py
"""

import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import Request, urlopen
import json

BEELINK_HOST = "beelink"
BEELINK_PATH = "~/rodado/br_saude_farmaciapopular/estabelecimentos"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
TEMP_DIR = Path("/private/tmp/claude-501/-Users-polux-Projetos-rodado/50905fb8-827b-445f-bb28-3e8ed468da54/scratchpad/farmacia_popular")

BASE_URL = "https://apidadosabertos.saude.gov.br/cnes/estabelecimentos"
PAGE_SIZE = 20
MAX_OFFSET = 33000  # safety cap; empirically total is ~31-32k (confirmed empty at 32000)
WORKERS = 15


def fetch_page(offset: int):
    url = f"{BASE_URL}?codigo_tipo_unidade=43&limit={PAGE_SIZE}&offset={offset}"
    req = Request(url, headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            with urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
            return data.get("estabelecimentos", [])
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

    # First, find the true end by probing sequentially in growing steps isn't
    # needed here: we just submit all offsets up to MAX_OFFSET and stop
    # collecting once we've seen enough consecutive empty pages.
    offsets = list(range(0, MAX_OFFSET, PAGE_SIZE))
    rows = []
    empty_streak = 0
    seen_empty_offsets = set()

    print(f"Fetching Farmacia Popular establishments (codigo_tipo_unidade=43) with {WORKERS} workers ...")
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = {ex.submit(fetch_page, off): off for off in offsets}
        done_count = 0
        for fut in as_completed(futures):
            off = futures[fut]
            page = fut.result()
            done_count += 1
            if not page:
                seen_empty_offsets.add(off)
            else:
                rows.extend(page)
            if done_count % 300 == 0:
                print(f"  ... {done_count}/{len(offsets)} pages fetched, {len(rows)} rows so far")

    print(f"\nTotal rows fetched: {len(rows)} (from {len(offsets) - len(seen_empty_offsets)} non-empty pages)")
    if not rows:
        print("No rows fetched — aborting.")
        return 1

    # de-dup in case of overlapping pages from race conditions (shouldn't happen, but cheap to check)
    seen = set()
    dedup_rows = []
    for r in rows:
        key = r.get("codigo_cnes")
        if key in seen:
            continue
        seen.add(key)
        dedup_rows.append(r)
    print(f"After dedup by codigo_cnes: {len(dedup_rows)} rows")

    table = pa.Table.from_pylist(dedup_rows)
    parquet_path = TEMP_DIR / "estabelecimentos.parquet"
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
