#!/usr/bin/env python3
from __future__ import annotations

import logging
import tempfile
from pathlib import Path

import click
import httpx
import pandas as pd

from _utils import download_file, rsync_to_beelink, write_parquet

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

INDEX_URL = "https://data.opensanctions.org/datasets/latest/index.json"
NAMES = {
    "br_tcu_disqualified": "inabilitados",
    "br_tcu_debarred": "inidoneos",
}
DATASET = "br_tcu_sancoes"
TABLE = "sancionados"


def resolve_dataset_urls() -> dict[str, str]:
    client = httpx.Client(follow_redirects=True, timeout=30)
    r = client.get(INDEX_URL, timeout=30)
    r.raise_for_status()
    datasets = r.json().get("datasets", [])
    result: dict[str, str] = {}
    for ds in datasets:
        name = ds.get("name", "")
        if name not in NAMES:
            continue
        resources = ds.get("resources", [])
        csv_url = None
        for res in resources:
            if res.get("name") == "targets.simple.csv":
                csv_url = res.get("url")
                break
        if csv_url:
            result[name] = csv_url
            logger.info("TCU %s -> %s", name, csv_url)
        else:
            logger.warning("TCU %s: targets.simple.csv não encontrado no index.json", name)
    return result


@click.command()
@click.option("--output-dir", default=None)
@click.option("--skip-existing/--no-skip-existing", default=True)
@click.option("--rsync/--no-rsync", default=True)
def main(output_dir: str | None, skip_existing: bool, rsync: bool):
    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
    raw = out / "raw"
    raw.mkdir(parents=True, exist_ok=True)

    parquet_dir = out / DATASET / TABLE
    parquet_path = parquet_dir / "sancionados.parquet"
    if skip_existing and parquet_path.exists():
        logger.info("Pulando TCU (já existe): %s", parquet_path)
        return

    urls = resolve_dataset_urls()
    if not urls:
        logger.error("Nenhuma URL do TCU encontrada no index do OpenSanctions")
        return

    frames: list[pd.DataFrame] = []
    for name, url in urls.items():
        csv_path = raw / f"{name}.csv"
        logger.info("TCU: baixando %s...", NAMES.get(name, name))
        if not download_file(url, csv_path):
            continue
        try:
            df = pd.read_csv(
                csv_path, dtype=str, sep=",", encoding="utf-8",
                keep_default_na=False,
            )
            df["tipo_lista"] = NAMES.get(name, name)
            frames.append(df)
            logger.info("  %s: %d linhas", NAMES.get(name, name), len(df))
        except Exception as e:
            logger.warning("  %s: erro: %s", name, e)

    if not frames:
        logger.error("Nenhum dado do TCU baixado")
        return

    df = pd.concat(frames, ignore_index=True)
    logger.info("TCU: %d linhas total", len(df))

    write_parquet(df, parquet_path)

    if rsync:
        rsync_to_beelink(parquet_dir, f"{DATASET}/{TABLE}")

    logger.info("TCU concluído: %s", parquet_path)


if __name__ == "__main__":
    main()
