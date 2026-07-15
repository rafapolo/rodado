#!/usr/bin/env python3
"""
Fetch ANVISA's medicamentos registry ("consulta completa" equivalent) ->
Parquet -> beelink.

Source: dados.anvisa.gov.br, a plain Apache/h5ai directory-index host serving
static bulk CSVs. This is a DIFFERENT host from consultas.anvisa.gov.br (the
"consulta completa" REST API), which still 403s under any header combination
this session (generic bot-mitigation WAF). dados.anvisa.gov.br sits outside
that WAF entirely -- confirmed 200 with a plain curl, no special headers, no
Referer needed.

File: DADOS_ABERTOS_MEDICAMENTOS.csv -- semicolon-delimited, ISO-8859-1
(latin-1) encoded, ~43k rows, one row per registered medicamento (product
registration record): tipo, nome, datas, categoria regulatoria, numero de
registro, empresa detentora, situacao, principio ativo. This is the closest
bulk equivalent to the "consulta completa" registry the blocked API exposes.

Usage:
    python3 scripts/scrap/anvisa_registros.py
"""

import subprocess
import sys
from pathlib import Path

BEELINK_HOST = "beelink"
BEELINK_PATH = "~/rodado/br_anvisa_consultas/registros"
URL = "https://dados.anvisa.gov.br/dados/DADOS_ABERTOS_MEDICAMENTOS.csv"
TEMP_DIR = Path(
    "/private/tmp/claude-501/-Users-polux-Projetos-rodado/"
    "c780c9c0-b6b3-44b0-964e-08a3b2f2024c/scratchpad/anvisa"
)
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)


def main():
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = TEMP_DIR / "DADOS_ABERTOS_MEDICAMENTOS.csv"

    print(f"Fetching {URL} ...")
    # Python's certifi bundle is missing an intermediate CA this host serves;
    # curl (using the macOS system keychain) validates fine, so shell out.
    result = subprocess.run(
        ["curl", "-s", "-A", UA, "-o", str(csv_path), "-w", "%{http_code}", URL],
        capture_output=True, text=True,
    )
    if result.stdout.strip() != "200":
        print(f"Fetch failed, HTTP {result.stdout.strip()}: {result.stderr}", file=sys.stderr)
        return 1
    print(f"Downloaded {csv_path.stat().st_size / 1e6:.1f} MB")

    df = pd.read_csv(
        csv_path,
        sep=";",
        encoding="latin-1",
        dtype=str,
        keep_default_na=False,
        na_values=[""],
    )
    print(f"Parsed {len(df)} rows, {len(df.columns)} columns")
    if df.empty:
        print("No rows parsed -- aborting, not pushing an empty file.")
        return 1

    table = pa.Table.from_pandas(df, preserve_index=False)
    parquet_path = TEMP_DIR / "registros.parquet"
    pq.write_table(table, str(parquet_path), compression="zstd")
    print(f"Wrote {parquet_path} ({parquet_path.stat().st_size / 1e6:.1f} MB, {table.num_rows} rows)")

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
