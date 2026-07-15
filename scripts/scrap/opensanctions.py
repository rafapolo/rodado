#!/usr/bin/env python3
"""
Fetch OpenSanctions consolidated "default" dataset (all sanctions/PEP/crime
lists merged) -> Parquet -> beelink.

Single bulk CSV download (~490MB), no pagination, no auth. This is the
"simple" flattened export (one row per entity, semicolon-joined multi-values)
rather than the full FollowTheMoney JSON graph — much easier to load as a
flat table and matches this repo's Parquet-table convention.

Usage:
    python3 scripts/scrap/opensanctions.py
"""

import subprocess
import sys
from pathlib import Path
from urllib.request import urlretrieve

BEELINK_HOST = "beelink"
BEELINK_PATH = "~/rodado/global_opensanctions/entities"
CSV_URL = "https://data.opensanctions.org/datasets/latest/default/targets.simple.csv"
TEMP_DIR = Path("/private/tmp/claude-501/-Users-polux-Projetos-rodado/50905fb8-827b-445f-bb28-3e8ed468da54/scratchpad/opensanctions")


def main():
    import pyarrow.csv as pv
    import pyarrow.parquet as pq

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = TEMP_DIR / "targets.simple.csv"

    print(f"Downloading {CSV_URL} (~490MB, may take a few minutes) ...")
    urlretrieve(CSV_URL, csv_path)
    print(f"Downloaded {csv_path.stat().st_size / 1e6:.1f} MB")

    table = pv.read_csv(
        csv_path,
        read_options=pv.ReadOptions(block_size=1 << 24),
        parse_options=pv.ParseOptions(newlines_in_values=True),
    )
    print(f"Parsed {table.num_rows} rows")

    if table.num_rows == 0:
        print("No rows fetched — aborting, not pushing an empty file.")
        return 1

    parquet_path = TEMP_DIR / "entities.parquet"
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
