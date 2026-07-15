#!/usr/bin/env python3
"""
Fetch DATASUS CID-10 (Classificação Internacional de Doenças) reference
tables -> Parquet -> beelink.

Single static zip bundle (~300KB), no auth, no pagination. Ships several
CSVs (categorias, capitulos, grupos, subcategorias, CID-O variants) — each
becomes its own table under the same dataset, matching the multi-table
convention used elsewhere in this repo (e.g. global_icij_offshoreleaks).

Source: http://www2.datasus.gov.br/cid10/V2008/downloads/CID10CSV.zip
CSVs are semicolon-delimited, ISO-8859-1 encoded.

Usage:
    python3 scripts/scrap/datasus_cid10.py
"""

import subprocess
import sys
import zipfile
from pathlib import Path
from urllib.request import urlretrieve, Request, urlopen

BEELINK_HOST = "beelink"
DATASET_PATH = "~/rodado/br_datasus_cid10"
# Multi-table dataset: sync_scraped_datasets.py's existence check needs one concrete
# table path, not the dataset root — "codigos" is the primary/representative table.
BEELINK_PATH = f"{DATASET_PATH}/codigos"
ZIP_URL = "http://www2.datasus.gov.br/cid10/V2008/downloads/CID10CSV.zip"
TEMP_DIR = Path("/private/tmp/claude-501/-Users-polux-Projetos-rodado/50905fb8-827b-445f-bb28-3e8ed468da54/scratchpad/cid10")

# CSV filename (in the zip) -> table name on beelink
TABLE_MAP = {
    "CID-10-CATEGORIAS.CSV": "codigos",
    "CID-10-CAPITULOS.CSV": "capitulos",
    "CID-10-GRUPOS.CSV": "grupos",
    "CID-10-SUBCATEGORIAS.CSV": "subcategorias",
    "CID-O-CATEGORIAS.CSV": "cid_o_categorias",
    "CID-O-GRUPOS.CSV": "cid_o_grupos",
}


def main():
    import pyarrow.csv as pv
    import pyarrow.parquet as pq

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = TEMP_DIR / "CID10CSV.zip"

    print(f"Downloading {ZIP_URL} ...")
    req = Request(ZIP_URL, headers={"User-Agent": "Mozilla/5.0 (rodado-scraper)"})
    with urlopen(req, timeout=60) as resp, open(zip_path, "wb") as f:
        f.write(resp.read())
    print(f"Downloaded {zip_path.stat().st_size / 1e3:.1f} KB")

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
                read_options=pv.ReadOptions(
                    block_size=1 << 24,
                    encoding="iso8859-1",
                ),
                parse_options=pv.ParseOptions(delimiter=";", newlines_in_values=True),
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
