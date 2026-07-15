#!/usr/bin/env python3
"""
Fetch MJSP (dados.mj.gov.br CKAN) datasets -> Parquet -> beelink.

Two sub-datasets confirmed on this CKAN instance (armas/SINARM: not found —
package_search for "arma", "sinarm", "posse de arma" returns no dedicated
resource, only the unrelated Sinesp crime-stats package, so it's skipped):
  - procon: Cadastro Nacional de Reclamacoes Fundamentadas (Sindec), 2024 CSV
  - infopen: Levantamento Nacional de Informacoes Penitenciarias, dez/2018 CSV

Multi-table dataset, same pattern as icij_offshoreleaks.py: BEELINK_PATH
points at one representative table ("procon") for existence checks.

Usage:
    python3 scripts/scrap/mjsp_ckan.py
"""

import subprocess
import sys
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

BEELINK_HOST = "beelink"
DATASET_PATH = "~/rodado/br_mjsp_ckan"
BEELINK_PATH = f"{DATASET_PATH}/procon"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
TEMP_DIR = Path("/private/tmp/claude-501/-Users-polux-Projetos-rodado/50905fb8-827b-445f-bb28-3e8ed468da54/scratchpad/mjsp")

# table_name -> (source_url, is_zip)
SOURCES = {
    "procon": (
        "https://dados.mj.gov.br/dataset/8ff7032a-d6db-452b-89f1-d860eb6965ff/resource/34a47b5c-5577-421a-bf9b-2dbbfc371d65/download/cnrfdadosabertos2024.zip",
        True,
    ),
    "infopen": (
        "http://dados.mj.gov.br/dataset/f9ebf1f1-8d27-4937-b330-f29b820dca87/resource/7fc972ce-c381-40fd-b46a-387651f9b964/download/copia-de-dadosformulariosjuldez2018.csv",
        False,
    ),
}


def fetch(url: str, dest: Path):
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=60) as resp, open(dest, "wb") as f:
        f.write(resp.read())


def main():
    import pandas as pd
    import pyarrow as pa
    import pyarrow.csv as pv
    import pyarrow.parquet as pq

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    written = {}

    for table_name, (url, is_zip) in SOURCES.items():
        print(f"Fetching {table_name}: {url}")
        raw_path = TEMP_DIR / f"{table_name}_raw"
        try:
            fetch(url, raw_path)
        except Exception as e:
            print(f"  ✗ {table_name}: download failed ({e})")
            continue
        print(f"  downloaded {raw_path.stat().st_size / 1e6:.1f} MB")

        data_path = None
        if is_zip:
            with zipfile.ZipFile(raw_path) as zf:
                names = zf.namelist()
                csv_names = [n for n in names if n.lower().endswith(".csv")]
                xlsx_names = [n for n in names if n.lower().endswith((".xlsx", ".xls"))]
                zf.extractall(TEMP_DIR / table_name)
                if csv_names:
                    data_path = (TEMP_DIR / table_name) / csv_names[0]
                elif xlsx_names:
                    data_path = (TEMP_DIR / table_name) / xlsx_names[0]
                else:
                    print(f"  ✗ {table_name}: no CSV/XLSX found in zip, skipping")
                    continue
        else:
            data_path = raw_path.with_suffix(".csv")
            raw_path.rename(data_path)

        try:
            if data_path.suffix.lower() in (".xlsx", ".xls"):
                df = pd.read_excel(data_path, dtype=str)
                table = pa.Table.from_pandas(df)
            else:
                table = pv.read_csv(
                    data_path,
                    read_options=pv.ReadOptions(block_size=1 << 24),
                    parse_options=pv.ParseOptions(
                        delimiter=";", newlines_in_values=True
                    ),
                )
                if table.num_columns <= 1:
                    # not semicolon-delimited, retry with comma
                    table = pv.read_csv(
                        data_path,
                        read_options=pv.ReadOptions(block_size=1 << 24),
                        parse_options=pv.ParseOptions(newlines_in_values=True),
                    )
        except Exception as e:
            print(f"  ✗ {table_name}: failed to parse ({e})")
            continue

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
