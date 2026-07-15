#!/usr/bin/env python3
"""
Fetch ANAC (sistemas.anac.gov.br/dadosabertos) datasets -> Parquet -> beelink.

Open Apache-style directory listing, no auth. Three sub-tables found (tarifas:
not found — no "tarifas" folder anywhere in the crawled tree; ANAC's tariff
data appears to live on a separate portal not exposed under /dadosabertos, so
it's skipped):
  - rab: Registro Aeronautico Brasileiro (aircraft registry), full CSV snapshot
  - voos: Voo Regular Ativo (VRA), most recent month (2026-05)
  - pontualidade: Percentuais de atrasos e cancelamentos, most recent month (2026-05)

Multi-table dataset, same pattern as icij_offshoreleaks.py: BEELINK_PATH
points at one representative table ("rab") for existence checks.

Usage:
    python3 scripts/scrap/anac_dadosabertos.py
"""

import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen

BEELINK_HOST = "beelink"
DATASET_PATH = "~/rodado/br_anac_dadosabertos"
BEELINK_PATH = f"{DATASET_PATH}/rab"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
TEMP_DIR = Path("/private/tmp/claude-501/-Users-polux-Projetos-rodado/50905fb8-827b-445f-bb28-3e8ed468da54/scratchpad/anac")

BASE = "https://sistemas.anac.gov.br/dadosabertos"

# table_name -> (source_url, delimiter)
SOURCES = {
    "rab": (
        f"{BASE}/Aeronaves/RAB/dados_aeronaves.csv",
        ";",
    ),
    "voos": (
        f"{BASE}/Voos%20e%20opera%C3%A7%C3%B5es%20a%C3%A9reas/Voo%20Regular%20Ativo%20%28VRA%29/2026/05%20-%20Maio/VRA_20265.csv",
        ";",
    ),
    "pontualidade": (
        f"{BASE}/Voos%20e%20opera%C3%A7%C3%B5es%20a%C3%A9reas/Percentuais%20de%20atrasos%20e%20cancelamentos/2026/05%20-%20maio/Anexo%20I.csv",
        ";",
    ),
}


def fetch(url: str, dest: Path):
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=90) as resp, open(dest, "wb") as f:
        f.write(resp.read())


def main():
    import pyarrow.csv as pv
    import pyarrow.parquet as pq

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    written = {}

    for table_name, (url, delim) in SOURCES.items():
        print(f"Fetching {table_name}: {url}")
        csv_path = TEMP_DIR / f"{table_name}.csv"
        try:
            fetch(url, csv_path)
        except Exception as e:
            print(f"  ✗ {table_name}: download failed ({e})")
            continue
        print(f"  downloaded {csv_path.stat().st_size / 1e6:.1f} MB")

        try:
            # ANAC CSVs carry a leading "Atualizado em: <date>" metadata line
            # before the real header row — skip it.
            table = pv.read_csv(
                csv_path,
                read_options=pv.ReadOptions(skip_rows=1, block_size=1 << 24, encoding="utf8"),
                parse_options=pv.ParseOptions(delimiter=delim, newlines_in_values=True),
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
