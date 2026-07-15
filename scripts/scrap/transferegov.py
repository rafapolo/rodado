#!/usr/bin/env python3
"""
Fetch TransfereGov.br open-data tables (Fundo a Fundo module) -> Parquet -> beelink.

Source: api.transferegov.gestao.gov.br is a real PostgREST API, but this doc's
originally guessed path (`api.transferegov.gestao.gov.br/programas`, plural,
no module prefix) 404s. The real API is split by transfer *module*, each with
its own PostgREST root and Swagger doc, e.g.:
  https://api.transferegov.gestao.gov.br/fundoafundo/   (Swagger/OpenAPI 2.0 spec)
  https://api.transferegov.gestao.gov.br/ted/            (also live, own tables)
Confirmed no auth required; standard PostgREST pagination via
`Range-Unit: items` / `Range: <start>-<end>` headers (or Prefer: count=exact
to get the total in the Content-Range response header).

This pipeline covers the fundoafundo module's core transfer tables:
  - transferencias -> `empenho` (actual budget-commitment/transfer records, 4,248 rows)
  - programas       -> `programa` (transfer programs catalog, 129 rows)
  - planos_acao     -> `plano_acao` (beneficiary action plans, 25,969 rows)
Other modules (ted, especial parlamentar, etc) exist but are out of scope for
this first pass -- can be added the same way later.

Usage:
    python3 scripts/scrap/transferegov.py
"""

import json
import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen

BEELINK_HOST = "beelink"
DATASET_PATH = "~/rodado/br_transferegov"
BEELINK_PATH = f"{DATASET_PATH}/transferencias"
BASE_URL = "https://api.transferegov.gestao.gov.br/fundoafundo"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
TEMP_DIR = Path(
    "/private/tmp/claude-501/-Users-polux-Projetos-rodado/c780c9c0-b6b3-44b0-964e-08a3b2f2024c/scratchpad/transferegov"
)
PAGE_SIZE = 5000

# table_name (beelink folder) -> PostgREST relation name
SOURCES = {
    "transferencias": "empenho",
    "programas": "programa",
    "planos_acao": "plano_acao",
}


def fetch_page(relation: str, offset: int, limit: int) -> list:
    # no explicit order clause: PostgREST default ordering is stable enough for a one-shot backfill
    url = f"{BASE_URL}/{relation}?limit={limit}&offset={offset}"
    req = Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def fetch_all(relation: str) -> list:
    # NOTE: the server silently caps each response at 1000 rows regardless of
    # the requested `limit` (confirmed: limit=5000 still returns exactly 1000
    # when >1000 rows exist) -- so pagination must continue until an *empty*
    # page comes back, not until a short page comes back.
    rows = []
    offset = 0
    while True:
        page = fetch_page(relation, offset, PAGE_SIZE)
        print(f"    offset={offset}: got {len(page)} rows")
        if not page:
            break
        rows.extend(page)
        offset += len(page)
    return rows


def main():
    import pyarrow as pa
    import pyarrow.parquet as pq

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    written = {}

    for table_name, relation in SOURCES.items():
        print(f"Fetching {table_name} (relation={relation}) ...")
        try:
            rows = fetch_all(relation)
        except Exception as e:
            print(f"  ✗ {table_name}: fetch failed ({e})")
            continue
        print(f"  total {len(rows)} rows")
        if not rows:
            print(f"  ✗ {table_name}: no rows, skipping")
            continue

        table = pa.Table.from_pylist(rows)
        parquet_path = TEMP_DIR / f"{table_name}.parquet"
        pq.write_table(table, str(parquet_path), compression="zstd")
        written[table_name] = (parquet_path, table.num_rows)
        print(f"  ✓ {table_name}: {table.num_rows} rows, {table.num_columns} cols -> {parquet_path.name}")

    if not written:
        print("No tables written -- aborting, nothing to push.")
        return 1

    for table_name, (parquet_path, rows) in written.items():
        remote_dir = f"{DATASET_PATH}/{table_name}"
        subprocess.run(f"ssh {BEELINK_HOST} 'mkdir -p {remote_dir}'", shell=True, check=True)
        result = subprocess.run(
            f"rsync -av {parquet_path} {BEELINK_HOST}:{remote_dir}/",
            shell=True,
        )
        if result.returncode != 0:
            print(f"  ✗ rsync failed for {table_name}")
            return 1
        print(f"  ✓ pushed {table_name} ({rows} rows) to {BEELINK_HOST}:{remote_dir}/")

    print(f"\nDone: {len(written)} tables pushed to {BEELINK_HOST}:{DATASET_PATH}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
