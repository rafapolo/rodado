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
TEMP_DIR = Path(
    "/private/tmp/claude-501/-Users-polux-Projetos-rodado/c780c9c0-b6b3-44b0-964e-08a3b2f2024c/scratchpad/pgfn"
)

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
                mismatch_logged = False
                for row in reader:
                    if len(row) != len(COLUMNS):
                        if not mismatch_logged:
                            print(f"    [DEBUG] {name}: header={header!r} first_bad_row={row!r}")
                            mismatch_logged = True
                        continue
                    record = dict(zip(COLUMNS, row))
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

    parquet_path = TEMP_DIR / "divida.parquet"
    writer = None
    total_rows = 0
    batch = []
    BATCH_SIZE = 200_000

    def flush_batch():
        nonlocal writer, batch, total_rows
        if not batch:
            return
        table = pa.Table.from_pylist(batch)
        if writer is None:
            writer = pq.ParquetWriter(str(parquet_path), table.schema, compression="zstd")
        writer.write_table(table)
        total_rows += len(batch)
        print(f"    ... flushed batch, running total {total_rows} rows")
        batch = []

    for categoria, filename in categories:
        url = f"https://dadosabertos.pgfn.gov.br/{quarter}/{filename}"
        zip_path = TEMP_DIR / filename
        print(f"\n[{categoria}] {url}")
        if not download_zip(session, url, zip_path):
            continue
        count_before = total_rows
        for record in iter_zip_rows(zip_path, categoria, quarter):
            batch.append(record)
            if len(batch) >= BATCH_SIZE:
                flush_batch()
        flush_batch()
        print(f"  [{categoria}] total rows so far: {total_rows} (+{total_rows - count_before})")
        zip_path.unlink(missing_ok=True)  # free disk space before next big download

    flush_batch()
    if writer is not None:
        writer.close()

    print(f"\nTotal rows: {total_rows}")
    if total_rows == 0:
        print("No rows fetched -- aborting, not pushing an empty file.")
        return 1

    print(f"Wrote {parquet_path} ({parquet_path.stat().st_size / 1e6:.1f} MB, {total_rows} rows)")

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
