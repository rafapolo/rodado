#!/usr/bin/env python3
"""
Fetch ICIJ Offshore Leaks full database (CSV bundle) -> Parquet -> beelink.

Single bulk zip download (~73MB), no pagination, no auth. Source ships several
CSVs (entities, officers, intermediaries, addresses, relationships, other) —
each becomes its own table under the same dataset, matching the multi-table
convention used elsewhere in this repo (e.g. br_camara_dados_abertos).

Usage:
    python3 scripts/scrap/icij_offshoreleaks.py
"""

import csv
import subprocess
import sys
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

BEELINK_HOST = "beelink"
DATASET_PATH = "~/rodado/global_icij_offshoreleaks"
# Multi-table dataset: sync_scraped_datasets.py's existence check needs one concrete
# table path, not the dataset root — "entities" is the primary/representative table.
BEELINK_PATH = f"{DATASET_PATH}/entities"
ZIP_URL = "https://offshoreleaks-data.icij.org/offshoreleaks/csv/full-oldb.LATEST.zip"
TEMP_DIR = Path("/private/tmp/claude-501/-Users-polux-Projetos-rodado/50905fb8-827b-445f-bb28-3e8ed468da54/scratchpad/icij")

# CSV filename (in the zip) -> table name on beelink
TABLE_MAP = {
    "nodes-entities.csv": "entities",
    "nodes-officers.csv": "officers",
    "nodes-intermediaries.csv": "intermediaries",
    "nodes-addresses.csv": "addresses",
    "nodes-others.csv": "other",
    "relationships.csv": "relationships",
}


def main():
    import pyarrow as pa
    import pyarrow.parquet as pq
    import pyarrow.csv as pv

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = TEMP_DIR / "full-oldb.zip"

    print(f"Downloading {ZIP_URL} ...")
    urlretrieve(ZIP_URL, zip_path)
    print(f"Downloaded {zip_path.stat().st_size / 1e6:.1f} MB")

    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        print(f"Zip contains {len(names)} files: {names}")
        zf.extractall(TEMP_DIR)

    written = {}
    for csv_name, table_name in TABLE_MAP.items():
        matches = list(TEMP_DIR.rglob(csv_name))
        if not matches:
            print(f"  ⚠ {csv_name} not found in zip, skipping")
            continue
        csv_path = matches[0]
        try:
            table = pv.read_csv(
                csv_path,
                read_options=pv.ReadOptions(block_size=1 << 24),
                parse_options=pv.ParseOptions(newlines_in_values=True),
            )
        except Exception as e:
            print(f"  ✗ {csv_name}: failed to parse ({e})")
            continue
        parquet_path = TEMP_DIR / f"{table_name}.parquet"
        pq.write_table(table, str(parquet_path), compression="zstd")
        written[table_name] = (parquet_path, table.num_rows)
        print(f"  ✓ {table_name}: {table.num_rows} rows -> {parquet_path.name}")

    if not written:
        print("No tables written — aborting, nothing to push.")
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
