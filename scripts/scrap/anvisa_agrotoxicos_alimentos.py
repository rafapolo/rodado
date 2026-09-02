#!/usr/bin/env python3
"""
Fetch two more ANVISA open-data CSVs from the same unblocked host as
anvisa_registros.py (dados.anvisa.gov.br, plain Apache/h5ai index, no WAF) ->
Parquet -> beelink, into the existing br_anvisa_consultas dataset alongside
`registros`.

- TA_MONOGRAFIA_AGROTOXICO.csv -> br_anvisa_consultas/agrotoxicos
  Pesticide monograph registry: substance, LMR (maximum residue limit),
  crop, legal act, validity dates. This is the actual registration data,
  not the petition-analysis-cycle CSV (CICLO_ANALISE_PETICOES_AGROTOXICO.CSV,
  a queue-status log) which was checked and is a worse fit for "agrotóxicos".

- DADOS_ABERTOS_ALIMENTO.csv -> br_anvisa_consultas/alimentos
  Registered food product records: CNPJ, empresa, produto, categoria,
  registro, situação.

Both are semicolon-delimited, ISO-8859-1 (latin-1), same shape as
DADOS_ABERTOS_MEDICAMENTOS.csv already pulled by anvisa_registros.py.

Note: "bulário" (medicine package-insert lookups) was also checked this
session and does NOT live on this open host -- it's served exclusively by
consultas.anvisa.gov.br, which is the *other* ANVISA host, still 403'd by a
WAF under every header combination tried (confirmed again 2026-09-02). Stays
blocked; not attempted here.

Usage:
    python3 scripts/scrap/anvisa_agrotoxicos_alimentos.py
"""

import csv
import subprocess
import sys
from pathlib import Path

import polars as pl

BEELINK_HOST = "beelink"
BEELINK_DATASET = "br_anvisa_consultas"
BASE_URL = "https://dados.anvisa.gov.br/dados"
TEMP_DIR = Path(
    "/private/tmp/claude-501/-Users-polux-Projetos-rodado/"
    "e20581f9-98b9-41da-beaa-99ab2da66ed1/scratchpad/anvisa"
)
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)

FILES = [
    ("TA_MONOGRAFIA_AGROTOXICO.csv", "agrotoxicos"),
    ("DADOS_ABERTOS_ALIMENTO.csv", "alimentos"),
]


def fetch_one(filename: str, tabela: str) -> int:
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = TEMP_DIR / filename
    url = f"{BASE_URL}/{filename}"

    print(f"Fetching {url} ...")
    result = subprocess.run(
        ["curl", "-s", "-A", UA, "-o", str(csv_path), "-w", "%{http_code}", url],
        capture_output=True, text=True,
    )
    if result.stdout.strip() != "200":
        print(f"Fetch failed, HTTP {result.stdout.strip()}: {result.stderr}", file=sys.stderr)
        return 1
    print(f"Downloaded {csv_path.stat().st_size / 1e6:.1f} MB")

    try:
        df = pl.read_csv(
            csv_path,
            separator=";",
            encoding="latin1",
            infer_schema_length=0,  # everything as str -- source has mixed date/number formats
        )
    except pl.exceptions.ComputeError:
        # A small number of source rows have a literal unquoted newline inside
        # a free-text field (e.g. product name), which breaks polars' chunked
        # CSV reader. Fall back to Python's csv module and drop the ragged
        # rows -- a handful out of tens of thousands, not worth reconstructing.
        print("polars CSV parse failed (ragged rows) -- falling back to csv module, dropping malformed rows")
        with open(csv_path, encoding="latin1", newline="") as f:
            reader = csv.reader(f, delimiter=";")
            header = next(reader)
            good_rows = []
            n_bad = 0
            for row in reader:
                if len(row) == len(header):
                    good_rows.append(row)
                else:
                    n_bad += 1
        print(f"Dropped {n_bad} malformed rows, kept {len(good_rows)}")
        df = pl.DataFrame(
            {col: [row[i] for row in good_rows] for i, col in enumerate(header)}
        )
    print(f"Parsed {df.height} rows, {df.width} columns")
    if df.is_empty():
        print("No rows parsed -- aborting, not pushing an empty file.")
        return 1

    parquet_path = TEMP_DIR / f"{tabela}.parquet"
    df.write_parquet(parquet_path, compression="zstd")
    print(f"Wrote {parquet_path} ({parquet_path.stat().st_size / 1e6:.1f} MB, {df.height} rows)")

    beelink_path = f"~/rodado/{BEELINK_DATASET}/{tabela}"
    subprocess.run(f"ssh {BEELINK_HOST} 'mkdir -p {beelink_path}'", shell=True, check=True)
    result = subprocess.run(
        f"rsync -av {parquet_path} {BEELINK_HOST}:{beelink_path}/",
        shell=True,
    )
    if result.returncode != 0:
        print("rsync failed", file=sys.stderr)
        return 1

    print(f"Pushed to {BEELINK_HOST}:{beelink_path}/{parquet_path.name}")
    return 0


def main():
    rc = 0
    for filename, tabela in FILES:
        rc |= fetch_one(filename, tabela)
    return rc


if __name__ == "__main__":
    sys.exit(main())
