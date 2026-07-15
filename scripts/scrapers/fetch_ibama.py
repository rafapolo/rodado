#!/usr/bin/env python3
from __future__ import annotations

import io
import logging
import tempfile
import zipfile
from pathlib import Path

import click
import httpx
import pandas as pd

from _utils import download_file, rsync_to_beelink, write_parquet

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ZIP_URL = "https://dadosabertos.ibama.gov.br/dados/SIFISC/termo_embargo/termo_embargo/termo_embargo_csv.zip"
CSV_URLS = {
    "termos_embargo": "https://dadosabertos.ibama.gov.br/dados/SIFISC/termo_embargo/termo_embargo/termo_embargo.csv",
    "itens": "https://dadosabertos.ibama.gov.br/dados/SIFISC/termo_embargo/itens/itens.csv",
    "coordenadas": "https://dadosabertos.ibama.gov.br/dados/SIFISC/termo_embargo/coordenadas/coordenadas.csv",
    "historico": "https://dadosabertos.ibama.gov.br/dados/SIFISC/termo_embargo/termo_embargo_historico/termo_embargo_historico.csv",
}
# Server at dadosabertos.ibama.gov.br has been returning 500 for all CSV/CSV.ZIP
# downloads since at least mid-2025. The scraper will attempt the ZIP first with
# a streaming download, then fall back to individual CSV files, and finally report
# failure if nothing works.
DATASET = "br_ibama_areas_embargadas"
TABLE = "termos_embargo"
ZIP_CSV_NAME = "termo_embargo.csv"


@click.command()
@click.option("--output-dir", default=None)
@click.option("--skip-existing/--no-skip-existing", default=True)
@click.option("--rsync/--no-rsync", default=True)
def main(output_dir: str | None, skip_existing: bool, rsync: bool):
    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
    raw = out / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    csv_path = raw / "areas_embargadas.csv"

    parquet_dir = out / DATASET / TABLE
    parquet_path = parquet_dir / "embargoes.parquet"
    if skip_existing and parquet_path.exists():
        logger.info("Pulando IBAMA (já existe): %s", parquet_path)
        return

    df: pd.DataFrame | None = None

    # Strategy 1: try ZIP download (streamed) and extract CSV
    logger.info("Tentando ZIP: %s", ZIP_URL)
    try:
        client = httpx.Client(follow_redirects=True, timeout=300)
        with client.stream("GET", ZIP_URL, timeout=300) as r:
            r.raise_for_status()
            buf = io.BytesIO()
            for chunk in r.iter_bytes(65536):
                buf.write(chunk)
            buf.seek(0)
            with zipfile.ZipFile(buf) as z:
                if ZIP_CSV_NAME in z.namelist():
                    with z.open(ZIP_CSV_NAME) as f:
                        df = pd.read_csv(f, dtype=str, sep=";", encoding="utf-8", keep_default_na=False)
                    logger.info("ZIP OK: %d linhas", len(df))
    except Exception as e:
        logger.warning("Falha ZIP: %s", e)

    # Strategy 2: fall back to individual CSV files
    if df is None:
        logger.info("Tentando CSVs individuais...")
        frames: list[pd.DataFrame] = []
        for name, url in CSV_URLS.items():
            p = raw / f"{name}.csv"
            if download_file(url, p):
                try:
                    fdf = pd.read_csv(p, dtype=str, sep=";", encoding="utf-8", keep_default_na=False)
                    fdf["tabela_origem"] = name
                    frames.append(fdf)
                    logger.info("  %s: %d linhas", name, len(fdf))
                except Exception as e:
                    logger.warning("  %s: erro: %s", name, e)
        if frames:
            df = pd.concat(frames, ignore_index=True)
        else:
            logger.error("Nenhum dado do IBAMA disponível (servidor retornando 500)")
            return

    if df is None or len(df) == 0:
        logger.error("Nenhum dado do IBAMA obtido")
        return

    write_parquet(df, parquet_path)

    if rsync:
        rsync_to_beelink(parquet_dir, f"{DATASET}/{TABLE}")

    logger.info("IBAMA concluído: %s", parquet_path)


if __name__ == "__main__":
    main()
