#!/usr/bin/env python3
"""
Fetch TCU (Tribunal de Contas da Uniao) Acordaos webservice -> Parquet -> beelink.

Source: TCU's official "Webservices TCU" catalog
(https://sites.tcu.gov.br/dados-abertos/webservices-tcu/), service "Consultar
Acordaos": GET https://dados-abertos.apps.tcu.gov.br/api/acordao/recupera-acordaos
?inicio={n}&quantidade={n}. No auth. (The doc's originally guessed
"dadosabertos.apps.tcu.gov.br" host doesn't resolve at all -- the real host is
"dados-abertos.apps.tcu.gov.br", note the hyphen.)

IMPORTANT (re-discovered 2026-07-11): the "F5 TSPD JS bot-challenge" previously
blamed for 0 rows is specific to Python's urllib TLS/HTTP fingerprint -- plain
`curl` sails through with HTTP 200 + clean JSON on the exact same URL, no
challenge at all (verified side by side: urlopen() gets a TSPD challenge HTML
page, `curl` on the identical URL a moment later gets real JSON). This script
now shells out to `curl` instead of urlopen(). (`dataInicio`/`dataFim` query
params are accepted but appear to be silently ignored by the backend --
results at a given `inicio` look identical regardless of date-range params;
ordering is most-recent-first and the only real control is the
`inicio`/`quantidade` offset.)

KNOWN LIMITATION (confirmed via manual probing, not a WAF/bot-mitigation issue):
this is a plain OFFSET-style pagination over what looks like a
search-index-backed store, and response latency grows sharply with `inicio`:
inicio=0 ~5-10s, inicio=10000 ~15s, inicio=60000 ~48s, inicio=100000 ~75s,
inicio=150000 times out even at 90s. This is a genuine backend performance
characteristic of the service, not a block. Full historical coverage (TCU has
issued acordaos for decades) is therefore not practical to pull in one run.
This script pages until either (a) a page comes back empty, (b) a page fails 3
retries in a row (growing timeout), or (c) a wall-clock budget is exceeded --
whichever comes first -- and pushes whatever was collected, deduplicated by
the `key` field (unique per acordao). Re-run periodically / extend
MAX_RUNTIME_SECONDS to backfill deeper over multiple runs.

Usage:
    python3 scripts/scrap/tcu_dadosabertos.py
"""

import subprocess
import sys
import time
from pathlib import Path
import json

BEELINK_HOST = "beelink"
BEELINK_PATH = "~/rodado/br_tcu_dadosabertos/dados"

BASE_URL = "https://dados-abertos.apps.tcu.gov.br/api/acordao/recupera-acordaos"
TEMP_DIR = Path(
    "/private/tmp/claude-501/-Users-polux-Projetos-rodado/c780c9c0-b6b3-44b0-964e-08a3b2f2024c/scratchpad/tcu"
)

PAGE_SIZE = 500
MAX_RUNTIME_SECONDS = 25 * 60  # best-effort budget; API itself is the bottleneck
BASE_TIMEOUT = 40


def fetch_page(inicio: int):
    url = f"{BASE_URL}?inicio={inicio}&quantidade={PAGE_SIZE}"
    last_err = None
    for attempt in range(3):
        timeout = BASE_TIMEOUT * (attempt + 1)
        try:
            result = subprocess.run(
                ["curl", "-s", "-m", str(timeout), url],
                capture_output=True,
                timeout=timeout + 5,
            )
            if result.returncode != 0 or not result.stdout:
                raise RuntimeError(f"curl exit={result.returncode}, stderr={result.stderr[:200]}")
            return json.loads(result.stdout)
        except Exception as e:
            last_err = e
            time.sleep(1 + attempt)
    print(f"  inicio={inicio}: giving up after retries ({last_err})")
    return None  # signals a hard failure (vs [] for a clean empty page)


def main():
    import pyarrow as pa
    import pyarrow.parquet as pq

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    seen_keys = set()
    all_rows = []
    inicio = 0
    start_time = time.monotonic()

    print(f"Fetching TCU acordaos, page size {PAGE_SIZE}, budget {MAX_RUNTIME_SECONDS}s ...")
    while True:
        elapsed = time.monotonic() - start_time
        if elapsed > MAX_RUNTIME_SECONDS:
            print(f"Wall-clock budget ({MAX_RUNTIME_SECONDS}s) exceeded at inicio={inicio} -- stopping.")
            break

        t0 = time.monotonic()
        page = fetch_page(inicio)
        dt = time.monotonic() - t0

        if page is None:
            print(f"Hard failure at inicio={inicio} after retries -- stopping (practical depth limit reached).")
            break
        if not page:
            print(f"Empty page at inicio={inicio} -- reached the end.")
            break

        new = 0
        for row in page:
            k = row.get("key")
            if k in seen_keys:
                continue
            seen_keys.add(k)
            all_rows.append(row)
            new += 1

        print(f"  inicio={inicio}: {len(page)} rows ({new} new, {dt:.1f}s) -- total {len(all_rows)}")
        inicio += PAGE_SIZE

    print(f"\nTotal unique rows fetched: {len(all_rows)}")
    if not all_rows:
        print("No rows fetched -- aborting, not pushing an empty file.")
        return 1

    table = pa.Table.from_pylist(all_rows)
    parquet_path = TEMP_DIR / "dados.parquet"
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
