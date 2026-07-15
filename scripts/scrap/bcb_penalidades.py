#!/usr/bin/env python3
"""
Fetch BCB (Banco Central do Brasil) penalidades aplicadas em Processo
Administrativo Sancionador (PAS) -> Parquet -> beelink.

Source: BCB Olinda OData API, service Gepad_QuadroPenalidades. Discovered via
the dadosabertos.bcb.gov.br CKAN catalog (dataset
"processo-administrativo-sancionador---penalidades-aplicadas"), which lists
the OData endpoint as the machine-readable resource. No auth required, but
"olinda.bcb.gov.br/.../odata/" bare root and "$count" are blocked by a WAF —
the concrete entity path with $top/$skip pagination works fine (confirmed
$top=10000 returns a full page).

Usage:
    python3 scripts/scrap/bcb_penalidades.py
"""

import subprocess
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

BEELINK_HOST = "beelink"
BEELINK_PATH = "~/rodado/br_bcb_penalidades/penalidades"
BASE_URL = (
    "https://olinda.bcb.gov.br/olinda/servico/Gepad_QuadroPenalidades/versao/v1/odata/"
    "QuadroGeralProcessoAdministrativoSancionador"
)
PAGE_SIZE = 10000
TEMP_DIR = Path("/private/tmp/claude-501/-Users-polux-Projetos-rodado/50905fb8-827b-445f-bb28-3e8ed468da54/scratchpad/bcb")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"


def fetch_page(skip: int) -> dict:
    import json

    url = f"{BASE_URL}?$format=json&$top={PAGE_SIZE}&$skip={skip}"
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def main():
    import pyarrow as pa
    import pyarrow.parquet as pq

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    all_rows = []
    skip = 0
    while True:
        print(f"Fetching skip={skip} ...")
        data = fetch_page(skip)
        rows = data.get("value", [])
        print(f"  got {len(rows)} rows")
        all_rows.extend(rows)
        if len(rows) < PAGE_SIZE:
            break
        skip += PAGE_SIZE
        time.sleep(0.5)

    print(f"Total rows fetched: {len(all_rows)}")
    if not all_rows:
        print("No rows fetched — aborting, not pushing an empty file.")
        return 1

    table = pa.Table.from_pylist(all_rows)
    parquet_path = TEMP_DIR / "penalidades.parquet"
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
