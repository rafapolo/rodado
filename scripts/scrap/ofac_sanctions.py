#!/usr/bin/env python3
"""
Fetch OFAC SDN (Specially Designated Nationals) sanctions list -> Parquet -> beelink.

Single bulk CSV download, no pagination, no auth. The file is headerless (classic
OFAC format) — column names below are the well-known standard 12-column SDN schema.

Usage:
    python3 scripts/scrap/ofac_sanctions.py
"""

import subprocess
import sys
from pathlib import Path
from urllib.request import urlretrieve

BEELINK_HOST = "beelink"
BEELINK_PATH = "~/rodado/global_ofac_sanctions/sanctions"
CSV_URL = "https://sanctionslistservice.ofac.treas.gov/api/publicationpreview/exports/sdn.csv"
TEMP_DIR = Path("/private/tmp/claude-501/-Users-polux-Projetos-rodado/50905fb8-827b-445f-bb28-3e8ed468da54/scratchpad/ofac")

COLUMNS = [
    "ent_num", "sdn_name", "sdn_type", "program", "title", "call_sign",
    "vess_type", "tonnage", "grt", "vess_flag", "vess_owner", "remarks",
]


def main():
    import pyarrow.csv as pv
    import pyarrow.parquet as pq

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = TEMP_DIR / "sdn.csv"

    print(f"Downloading {CSV_URL} ...")
    urlretrieve(CSV_URL, csv_path)
    print(f"Downloaded {csv_path.stat().st_size / 1e6:.1f} MB")

    table = pv.read_csv(
        csv_path,
        read_options=pv.ReadOptions(column_names=COLUMNS, block_size=1 << 24),
        parse_options=pv.ParseOptions(
            newlines_in_values=True,
            invalid_row_handler=lambda row: "skip",  # source ends with a stray control-char line
        ),
    )
    print(f"Parsed {table.num_rows} rows")

    if table.num_rows == 0:
        print("No rows fetched — aborting, not pushing an empty file.")
        return 1

    parquet_path = TEMP_DIR / "sanctions.parquet"
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
