#!/usr/bin/env python3
"""
Fetch CVM Fundos de Investimento registration/cadastro data -> Parquet -> beelink.

Single bulk CSV download (~18MB), no auth, no pagination. Companion dataset to
the existing br_cvm_administradores_carteira mirror — same portal, same CSV
shape (semicolon-delimited, ISO-8859-1 encoded).

Source: https://dados.cvm.gov.br/dados/FI/CAD/DADOS/cad_fi.csv

Usage:
    python3 scripts/scrap/cvm_fundos.py
"""

import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen

BEELINK_HOST = "beelink"
BEELINK_PATH = "~/rodado/br_cvm_fundos/fundos"
CSV_URL = "https://dados.cvm.gov.br/dados/FI/CAD/DADOS/cad_fi.csv"
TEMP_DIR = Path("/private/tmp/claude-501/-Users-polux-Projetos-rodado/50905fb8-827b-445f-bb28-3e8ed468da54/scratchpad/cvm_fundos")


def main():
    import pyarrow.csv as pv
    import pyarrow.parquet as pq

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = TEMP_DIR / "cad_fi.csv"

    print(f"Downloading {CSV_URL} ...")
    req = Request(CSV_URL, headers={"User-Agent": "Mozilla/5.0 (rodado-scraper)"})
    with urlopen(req, timeout=120) as resp, open(csv_path, "wb") as f:
        f.write(resp.read())
    print(f"Downloaded {csv_path.stat().st_size / 1e6:.1f} MB")

    table = pv.read_csv(
        csv_path,
        read_options=pv.ReadOptions(block_size=1 << 24, encoding="iso8859-1"),
        parse_options=pv.ParseOptions(delimiter=";", newlines_in_values=True),
    )
    print(f"Parsed {table.num_rows} rows, {len(table.column_names)} columns")

    parquet_path = TEMP_DIR / "fundos.parquet"
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
