#!/usr/bin/env python3
"""
Fetch SINESP crime-occurrence indicators (dados.mj.gov.br CKAN, dataset
"sistema-nacional-de-estatisticas-de-seguranca-publica") -> Parquet -> beelink.

Two XLSX resources, both tidy long-format (UF/municipio x crime type x year x
month x occurrence count):
  - indicadoressegurancapublicamunic.xlsx  -> table "ocorrencias" (municipio-level, primary)
  - indicadoressegurancapublicauf.xlsx     -> table "ocorrencias_uf" (UF-level aggregate)

No auth, direct XLSX download links from CKAN resource metadata (package_search
on dados.mj.gov.br/api/3/action). mjsp_ckan.py already covers procon/infopen
from the same CKAN instance and explicitly skipped this Sinesp package (it was
looking for arms/SINARM data); this script targets the Sinesp package itself.

Usage:
    python3 scripts/scrap/mjsp_sinesp.py
"""

import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen

BEELINK_HOST = "beelink"
DATASET_PATH = "~/rodado/br_mjsp_sinesp"
BEELINK_PATH = f"{DATASET_PATH}/ocorrencias"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
TEMP_DIR = Path("/private/tmp/claude-501/-Users-polux-Projetos-rodado/50905fb8-827b-445f-bb28-3e8ed468da54/scratchpad/sinesp")

DATASET_ID = "210b9ae2-21fc-4986-89c6-2006eb4db247"
# table_name -> resource download URL
SOURCES = {
    "ocorrencias": (
        f"https://dados.mj.gov.br/dataset/{DATASET_ID}/resource/"
        "03af7ce2-174e-4ebd-b085-384503cfb40f/download/indicadoressegurancapublicamunic.xlsx"
    ),
    "ocorrencias_uf": (
        f"https://dados.mj.gov.br/dataset/{DATASET_ID}/resource/"
        "feeae05e-faba-406c-8a4a-512aec91a9d1/download/indicadoressegurancapublicauf.xlsx"
    ),
}


def fetch(url: str, dest: Path):
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=90) as resp, open(dest, "wb") as f:
        f.write(resp.read())


def main():
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    written = {}

    for table_name, url in SOURCES.items():
        print(f"Fetching {table_name}: {url}")
        xlsx_path = TEMP_DIR / f"{table_name}.xlsx"
        try:
            fetch(url, xlsx_path)
        except Exception as e:
            print(f"  ✗ {table_name}: download failed ({e})")
            continue
        print(f"  downloaded {xlsx_path.stat().st_size / 1e6:.1f} MB")

        try:
            df = pd.read_excel(xlsx_path)
        except Exception as e:
            print(f"  ✗ {table_name}: failed to parse xlsx ({e})")
            continue

        # normalize column names (drop accents/spaces for downstream SQL friendliness)
        df.columns = [
            c.strip()
            .lower()
            .replace(" ", "_")
            .replace("ê", "e")
            .replace("ç", "c")
            .replace("ã", "a")
            .replace("é", "e")
            for c in df.columns
        ]

        table = pa.Table.from_pandas(df, preserve_index=False)
        parquet_path = TEMP_DIR / f"{table_name}.parquet"
        pq.write_table(table, str(parquet_path), compression="zstd")
        written[table_name] = (parquet_path, table.num_rows)
        print(f"  ✓ {table_name}: {table.num_rows} rows, {table.num_columns} cols -> {parquet_path.name}")

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
