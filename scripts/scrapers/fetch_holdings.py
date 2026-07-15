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

URLS = [
    "https://data.brasil.io/dataset/socios-brasil/holding.csv.gz",
    "https://brasil-io-public.s3.amazonaws.com/dataset/socios-brasil/holding.csv.gz",
]
DATASET = "br_socios_brasil"
TABLE = "holdings"


@click.command()
@click.option("--output-dir", default=None, help="Dir local (opcional, default = temp)")
@click.option("--skip-existing/--no-skip-existing", default=True)
@click.option("--rsync/--no-rsync", default=True)
def main(output_dir: str | None, skip_existing: bool, rsync: bool):
    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
    raw = out / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    gz_path = raw / "holding.csv.gz"

    parquet_dir = out / DATASET / TABLE
    parquet_path = parquet_dir / "holdings.parquet"
    if skip_existing and parquet_path.exists():
        logger.info("Pulando Holdings (já existe): %s", parquet_path)
        return

    ok = False
    for url in URLS:
        logger.info("Tentando: %s", url)
        if download_file(url, gz_path):
            ok = True
            break
    if not ok:
        logger.error("Falha no download Holdings")
        return

    df = pd.read_csv(gz_path, dtype=str, compression="gzip", keep_default_na=False)
    logger.info("Holdings: %d linhas, %d colunas", len(df), len(df.columns))

    write_parquet(df, parquet_path)

    if rsync:
        rsync_to_beelink(parquet_dir, f"{DATASET}/{TABLE}")

    logger.info("Holdings concluído: %s", parquet_path)


if __name__ == "__main__":
    main()
