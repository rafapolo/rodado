#!/usr/bin/env python3
from __future__ import annotations

import logging
import tempfile
from datetime import datetime
from pathlib import Path

import click
import pandas as pd

from _utils import download_file, rsync_to_beelink, write_parquet

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# 2008-2021: old Senado transparency portal CSV
OLD_URL = "https://www.senado.leg.br/transparencia/LAI/verba/{year}.csv"
# 2022+: new adm-dadosabertos API
NEW_URL = "https://adm.senado.gov.br/adm-dadosabertos/api/v1/senadores/despesas_ceaps/{year}/csv"
API_SPLIT_YEAR = 2022
DATASET = "br_senado_ceaps"
TABLE = "despesas"

OLD_COLUMNS = ["ANO", "MES", "SENADOR", "TIPO_DESPESA", "CNPJ_CPF",
               "FORNECEDOR", "DOCUMENTO", "DATA", "DETALHAMENTO",
               "VALOR_REEMBOLSADO", "COD_DOCUMENTO"]

NEW_COLUMNS = ["ID", "TIPO_DOCUMENTO", "ANO", "MÊS", "COD_SENADOR",
               "NOME_SENADOR", "TIPO_DESPESA", "CPF_CNPJ_FORNECEDOR",
               "NOME_FORNECEDOR", "DOCUMENTO", "DATA", "DETALHAMENTO",
               "VALOR_REEMBOLSADO"]


def normalize_old(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip().upper() for c in df.columns]
    df = df.rename(columns={
        "SENADOR": "NOME_SENADOR",
        "CNPJ_CPF": "CPF_CNPJ_FORNECEDOR",
        "FORNECEDOR": "NOME_FORNECEDOR",
    })
    df["TIPO_DOCUMENTO"] = ""
    df["COD_SENADOR"] = ""
    return df


def normalize_new(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip().upper().replace("Ê", "E") for c in df.columns]
    return df


@click.command()
@click.option("--start-year", default=2008, type=int)
@click.option("--end-year", default=lambda: datetime.now().year, type=int)
@click.option("--output-dir", default=None)
@click.option("--skip-existing/--no-skip-existing", default=True)
@click.option("--rsync/--no-rsync", default=True)
def main(start_year: int, end_year: int, output_dir: str | None, skip_existing: bool, rsync: bool):
    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
    raw = out / "raw"
    raw.mkdir(parents=True, exist_ok=True)

    parquet_dir = out / DATASET / TABLE
    parquet_path = parquet_dir / "despesas.parquet"
    if skip_existing and parquet_path.exists():
        logger.info("Pulando Senado (já existe): %s", parquet_path)
        return

    frames: list[pd.DataFrame] = []
    for year in range(start_year, end_year + 1):
        if year < API_SPLIT_YEAR:
            url = OLD_URL.format(year=year)
            skip = 1
        else:
            url = NEW_URL.format(year=year)
            skip = 0
        csv_path = raw / f"{year}.csv"
        if not download_file(url, csv_path):
            continue
        try:
            kwargs = dict(dtype=str, sep=";", keep_default_na=False)
            if year < API_SPLIT_YEAR:
                kwargs["encoding"] = "latin-1"
                df = pd.read_csv(csv_path, **kwargs, skiprows=skip)
                df = normalize_old(df)
            else:
                kwargs["encoding"] = "utf-8"
                df = pd.read_csv(csv_path, **kwargs)
                df = normalize_new(df)
            frames.append(df)
            logger.info("  %d: %d linhas", year, len(df))
        except Exception as e:
            logger.warning("  %d: erro ao ler: %s", year, e)

    if not frames:
        logger.error("Nenhum dado do Senado baixado")
        return

    df = pd.concat(frames, ignore_index=True, sort=False)
    logger.info("Senado: %d linhas total", len(df))

    write_parquet(df, parquet_path)

    if rsync:
        rsync_to_beelink(parquet_dir, f"{DATASET}/{TABLE}")

    logger.info("Senado concluído: %s", parquet_path)


if __name__ == "__main__":
    main()
