#!/usr/bin/env python3
from __future__ import annotations

import logging
import tempfile
from pathlib import Path

import click
import pandas as pd

from _utils import download_file, rsync_to_beelink, write_parquet

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

URL = "https://dadosabertos.bndes.gov.br/dataset/10e21ad1-568e-45e5-a8af-43f2c05ef1a2/resource/6f56b78c-510f-44b6-8274-78a5b7e931f4/download/operacoes-financiamento-operacoes-nao-automaticas.csv"
DATASET = "br_bndes_desembolsos"
TABLE = "operacoes_nao_automaticas"


@click.command()
@click.option("--output-dir", default=None, help="Dir local (opcional, default = temp)")
@click.option("--skip-existing/--no-skip-existing", default=True)
@click.option("--rsync/--no-rsync", default=True)
def main(output_dir: str | None, skip_existing: bool, rsync: bool):
    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
    raw = out / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    csv_path = raw / "operacoes-nao-automaticas.csv"

    parquet_dir = out / DATASET / TABLE
    parquet_path = parquet_dir / "operacoes.parquet"
    if skip_existing and parquet_path.exists():
        logger.info("Pulando BNDES (já existe): %s", parquet_path)
        return

    logger.info("Baixando BNDES...")
    if not download_file(URL, csv_path):
        logger.error("Falha no download BNDES")
        return

    df = pd.read_csv(csv_path, dtype=str, sep=";", encoding="windows-1252", keep_default_na=False)
    logger.info("BNDES: %d linhas, %d colunas", len(df), len(df.columns))

    write_parquet(df, parquet_path)

    if rsync:
        rsync_to_beelink(parquet_dir, f"{DATASET}/{TABLE}")

    logger.info("BNDES concluído: %s", parquet_path)


if __name__ == "__main__":
    main()
