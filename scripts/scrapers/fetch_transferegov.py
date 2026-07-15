#!/usr/bin/env python3
from __future__ import annotations

import logging
import tempfile
import zipfile
from pathlib import Path

import click
import httpx
import pandas as pd

from _utils import rsync_to_beelink, write_parquet

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://portaldatransparencia.gov.br/download-de-dados"
DATASET = "br_transferegov_emendas"
TABLE = "emendas_parlamentares"
CSV_NAMES = {
    "EmendasParlamentares.csv": "emendas",
    "EmendasParlamentares_PorFavorecido.csv": "favorecidos",
    "EmendasParlamentares_Convenios.csv": "convenios",
}


@click.command()
@click.option("--year", default=2025, type=int)
@click.option("--output-dir", default=None)
@click.option("--skip-existing/--no-skip-existing", default=True)
@click.option("--rsync/--no-rsync", default=True)
def main(year: int, output_dir: str | None, skip_existing: bool, rsync: bool):
    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
    raw = out / "raw"
    raw.mkdir(parents=True, exist_ok=True)

    parquet_dir = out / DATASET / TABLE
    if skip_existing and all((parquet_dir / f"{name}.parquet").exists() for name in CSV_NAMES.values()):
        logger.info("Pulando Transferegov (já existe)")
        return

    url = f"{BASE_URL}/emendas-parlamentares/{year}"
    zip_path = raw / f"emendas_{year}.zip"

    logger.info("Baixando Transferegov %d...", year)
    client = httpx.Client(follow_redirects=True, timeout=600)
    try:
        with client.stream("GET", url) as r:
            r.raise_for_status()
            with open(zip_path, "wb") as f:
                for chunk in r.iter_bytes(65536):
                    f.write(chunk)
        logger.info("Download OK: %s", zip_path.name)
    except Exception as e:
        logger.error("Falha no download: %s", e)
        return
    finally:
        client.close()

    extract_dir = raw / f"emendas_{year}_extracted"
    extract_dir.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extract_dir)
    except zipfile.BadZipFile:
        logger.error("ZIP corrompido")
        return

    parquet_dir.mkdir(parents=True, exist_ok=True)
    for csv_name, table_name in CSV_NAMES.items():
        csv_path = extract_dir / csv_name
        if not csv_path.exists():
            logger.warning("Arquivo não encontrado: %s", csv_name)
            continue
        try:
            df = pd.read_csv(csv_path, dtype=str, sep=";", encoding="latin-1", keep_default_na=False)
            parquet_path = parquet_dir / f"{table_name}.parquet"
            write_parquet(df, parquet_path)
            logger.info("  %s: %d linhas", table_name, len(df))
        except Exception as e:
            logger.warning("  %s: erro: %s", csv_name, e)

    if rsync:
        rsync_to_beelink(parquet_dir, f"{DATASET}/{TABLE}")

    logger.info("Transferegov concluído: ano=%d", year)


if __name__ == "__main__":
    main()
