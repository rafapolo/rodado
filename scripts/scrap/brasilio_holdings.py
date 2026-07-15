#!/usr/bin/env python3
"""
Fetch Brasil.IO's "holdings" table (part of the socios-brasil dataset,
derived corporate-ownership graph: companies that are partners/shareholders
in other companies) -> Parquet -> beelink.

Source: Brasil.IO does NOT have a documented `brasil.io/api/dataset/` REST
API for this dataset (that guessed path 404s) -- instead it publishes the
whole dataset as bulk gzipped CSV files under a static mirror domain,
confirmed reachable with no auth/API key:
  https://data.brasil.io/dataset/socios-brasil/holdings.csv.gz  (~10MB)
(siblings: empresas.csv.gz ~715MB, socios.csv.gz ~701MB -- not fetched here,
this pipeline targets only the "holdings" table per the catalog entry;
`br_me_cnpj.empresas`/`socios` already covers the raw registry on beelink).

Usage:
    python3 scripts/scrap/brasilio_holdings.py
"""

import gzip
import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen

BEELINK_HOST = "beelink"
BEELINK_PATH = "~/rodado/br_brasilio_holdings/holdings"
URL = "https://data.brasil.io/dataset/socios-brasil/holdings.csv.gz"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
TEMP_DIR = Path(
    "/private/tmp/claude-501/-Users-polux-Projetos-rodado/c780c9c0-b6b3-44b0-964e-08a3b2f2024c/scratchpad/brasilio"
)


def fetch(url: str, dest: Path):
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=180) as resp, open(dest, "wb") as f:
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)


def main():
    import pyarrow.csv as pv
    import pyarrow.parquet as pq

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    gz_path = TEMP_DIR / "holdings.csv.gz"
    csv_path = TEMP_DIR / "holdings.csv"

    print(f"Fetching {URL} ...")
    fetch(URL, gz_path)
    print(f"  downloaded {gz_path.stat().st_size / 1e6:.1f} MB")

    print("Decompressing ...")
    with gzip.open(gz_path, "rb") as fin, open(csv_path, "wb") as fout:
        while True:
            chunk = fin.read(1 << 20)
            if not chunk:
                break
            fout.write(chunk)
    print(f"  decompressed to {csv_path.stat().st_size / 1e6:.1f} MB")

    table = pv.read_csv(
        csv_path,
        read_options=pv.ReadOptions(block_size=1 << 24),
        parse_options=pv.ParseOptions(newlines_in_values=True),
    )
    print(f"Parsed {table.num_rows} rows, {table.num_columns} cols")
    if table.num_rows == 0:
        print("No rows parsed -- aborting, not pushing an empty file.")
        return 1

    parquet_path = TEMP_DIR / "holdings.parquet"
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
