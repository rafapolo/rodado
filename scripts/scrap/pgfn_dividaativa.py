#!/usr/bin/env python3
"""
Fetch PGFN (Procuradoria-Geral da Fazenda Nacional) "Divida Ativa da Uniao"
open-data bulk export -> Parquet -> beelink.

Source: dadosabertos.pgfn.gov.br -- a dedicated static-file host (Apache,
plain HTTP directory of .zip files by quarter), completely outside the main
gov.br WAF that blocks www.gov.br/pgfn's own file downloads. Discovered by
following the "dados-abertos" link from https://www.gov.br/pgfn/pt-br/
assuntos/divida-ativa-da-uniao/transparencia-fiscal-1/dados-abertos (that
HTML page itself loads fine -- only the file host had moved/WAF'd).

Each quarter publishes 3 zips, each containing several semicolon-delimited,
ISO-8859-1 (latin-1) CSVs split by region (numbered 1-6 + "NA"):
  - Dados_abertos_FGTS.zip            (~18MB compressed)
  - Dados_abertos_Previdenciario.zip  (~87MB compressed)
  - Dados_abertos_Nao_Previdenciario.zip (~1.2GB compressed -- the largest
    category by far, general tax debts)

All three share the same 15-column schema: CPF_CNPJ, TIPO_PESSOA,
TIPO_DEVEDOR, NOME_DEVEDOR, UF_DEVEDOR, UNIDADE_RESPONSAVEL,
ENTIDADE_RESPONSAVEL, UNIDADE_INSCRICAO, NUMERO_INSCRICAO,
TIPO_SITUACAO_INSCRICAO, SITUACAO_INSCRICAO, RECEITA_PRINCIPAL,
DATA_INSCRICAO, INDICADOR_AJUIZADO, VALOR_CONSOLIDADO.

This script pulls only the LATEST available quarter (auto-discovered from
the dados-abertos page) by default -- full history goes back to 2020 and
would be tens of GB. Rows are tagged with a `categoria` column
(fgts/previdenciario/nao_previdenciario) and `trimestre` (e.g.
"2026_trimestre_01"). Writes incrementally with a streaming ParquetWriter to
keep peak memory bounded given the Nao_Previdenciario file's size.

Usage:
    python3 scripts/scrap/pgfn_dividaativa.py [--skip-nao-previdenciario]
"""

import argparse
import csv
import io
import re
import subprocess
import sys
import uuid
import zipfile
from pathlib import Path

import requests

BEELINK_HOST = "beelink"
BEELINK_PATH = "~/rodado/br_pgfn_dividaativa/divida"

DADOS_ABERTOS_PAGE = (
    "https://www.gov.br/pgfn/pt-br/assuntos/divida-ativa-da-uniao/"
    "transparencia-fiscal-1/dados-abertos"
)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
TEMP_DIR = Path(f"/tmp/pgfn_dividaativa_{uuid.getnode()}")

QUARTER_RE = re.compile(r"https://dadosabertos\.pgfn\.gov\.br/(\d{4}_trimestre_\d{2})/")
COLUMNS = [
    "CPF_CNPJ", "TIPO_PESSOA", "TIPO_DEVEDOR", "NOME_DEVEDOR", "UF_DEVEDOR",
    "UNIDADE_RESPONSAVEL", "ENTIDADE_RESPONSAVEL", "UNIDADE_INSCRICAO",
    "NUMERO_INSCRICAO", "TIPO_SITUACAO_INSCRICAO", "SITUACAO_INSCRICAO",
    "RECEITA_PRINCIPAL", "DATA_INSCRICAO", "INDICADOR_AJUIZADO", "VALOR_CONSOLIDADO",
]


def find_latest_quarter(session: requests.Session) -> str:
    resp = session.get(DADOS_ABERTOS_PAGE, timeout=30)
    resp.raise_for_status()
    quarters = sorted(set(QUARTER_RE.findall(resp.text)))
    if not quarters:
        raise RuntimeError("No quarter links found on the dados-abertos page")
    return quarters[-1]


def download_zip(session: requests.Session, url: str, dest: Path) -> bool:
    print(f"  Downloading {url} ...")
    resp = session.get(url, timeout=300, stream=True)
    if resp.status_code != 200:
        print(f"  HTTP {resp.status_code} -- skipping")
        return False
    with open(dest, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            f.write(chunk)
    print(f"  {dest.stat().st_size / 1e6:.1f} MB")
    return True


def iter_zip_rows(zip_path: Path, categoria: str, trimestre: str):
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if not name.lower().endswith(".csv"):
                continue
            with zf.open(name) as raw:
                text = io.TextIOWrapper(raw, encoding="latin-1", newline="")
                reader = csv.reader(text, delimiter=";")
                header = next(reader, None)
                if header is None:
                    continue
                mapped_header = [
                    "RECEITA_PRINCIPAL" if h == "TIPO_CREDITO" else h
                    for h in header
                ]
                csv_cols = dict(zip(mapped_header, range(len(mapped_header))))
                for row in reader:
                    if not row:
                        continue
                    if len(row) < len(mapped_header) - 2:
                        continue
                    row = list(row) + [None] * (len(mapped_header) - len(row))
                    record = {}
                    for col in COLUMNS:
                        record[col] = row[csv_cols[col]] if col in csv_cols else None
                    record["categoria"] = categoria
                    record["trimestre"] = trimestre
                    yield record


def main():
    import pyarrow as pa
    import pyarrow.parquet as pq

    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-nao-previdenciario", action="store_true",
                         help="Skip the ~1.2GB Nao_Previdenciario file (fastest, but excludes the largest category)")
    args = parser.parse_args()

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({"User-Agent": UA})

    print("Finding latest available quarter...")
    quarter = find_latest_quarter(session)
    print(f"Latest quarter: {quarter}")

    categories = [
        ("fgts", "Dados_abertos_FGTS.zip"),
        ("previdenciario", "Dados_abertos_Previdenciario.zip"),
    ]
    if not args.skip_nao_previdenciario:
        categories.append(("nao_previdenciario", "Dados_abertos_Nao_Previdenciario.zip"))

    total_rows = 0
    parquet_paths = []

    for categoria, filename in categories:
        url = f"https://dadosabertos.pgfn.gov.br/{quarter}/{filename}"
        zip_path = TEMP_DIR / filename
        print(f"\n[{categoria}] {url}")
        if not download_zip(session, url, zip_path):
            continue

        cat_path = TEMP_DIR / f"{categoria}.parquet"
        writer = None
        batch = []
        cat_rows = 0

        def flush_batch():
            nonlocal writer, batch, cat_rows
            if not batch:
                return
            table = pa.Table.from_pylist(batch)
            null_cols = [f.name for f in table.schema if f.type == pa.null()]
            if null_cols:
                for col in null_cols:
                    idx = table.schema.get_field_index(col)
                    table = table.set_column(idx, col, table.column(col).cast(pa.string()))
            if writer is None:
                writer = pq.ParquetWriter(str(cat_path), table.schema, compression="zstd")
            writer.write_table(table)
            cat_rows += len(batch)
            print(f"    ... flushed batch, running total {cat_rows} rows")
            batch = []

        for record in iter_zip_rows(zip_path, categoria, quarter):
            batch.append(record)
            if len(batch) >= 200_000:
                flush_batch()
        flush_batch()
        if writer is not None:
            writer.close()
        print(f"  [{categoria}] rows: {cat_rows}")
        total_rows += cat_rows
        zip_path.unlink(missing_ok=True)
        if cat_rows == 0:
            cat_path.unlink(missing_ok=True)
            continue

        parquet_paths.append(cat_path)
        # Push each category independently so partial runs don't lose progress
        subprocess.run(f"ssh {BEELINK_HOST} 'mkdir -p {BEELINK_PATH}'", shell=True, check=False)
        result = subprocess.run(
            f"rsync -av {cat_path} {BEELINK_HOST}:{BEELINK_PATH}/",
            shell=True,
        )
        if result.returncode != 0:
            print(f"  rsync failed for {categoria}", file=sys.stderr)
        else:
            print(f"  pushed {categoria} ({cat_rows} rows) to beelink")

    print(f"\nTotal rows: {total_rows}")
    if total_rows == 0:
        print("No rows fetched -- aborting, not pushing an empty file.")
        return 0

    # Merge all category parquets into a single file on beelink via DuckDB
    remote_files = "', '".join(f"{BEELINK_PATH}/{p.name}" for p in parquet_paths)
    merge_sql = f"COPY (SELECT * FROM read_parquet(['{remote_files}'], union_by_name=true)) TO '{BEELINK_PATH}/divida.parquet' (FORMAT PARQUET, COMPRESSION ZSTD);"
    subprocess.run(
        ["ssh", BEELINK_HOST, "~/bin/duckdb", "-c", merge_sql],
        capture_output=True, timeout=120,
    )
    # Remove individual category files
    for p in parquet_paths:
        subprocess.run(["ssh", BEELINK_HOST, "rm", "-f", f"{BEELINK_PATH}/{p.name}"], capture_output=True)

    print(f"Pushed merged to {BEELINK_HOST}:{BEELINK_PATH}/divida.parquet ({total_rows} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
