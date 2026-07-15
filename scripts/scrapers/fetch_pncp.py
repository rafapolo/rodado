#!/usr/bin/env python3
from __future__ import annotations

import json
import logging
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

import click
import httpx
import pandas as pd

from _utils import rsync_to_beelink, write_parquet

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

API_BASE = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
MODALIDADES = [1, 3, 5, 6, 8, 9]
DATASET = "br_pncp_contratacoes"
TABLE = "contratos"
MAX_PAGE = 50
DELAY = 1.0


def _fetch_all(client: httpx.Client, start: str, end: str, mod: int) -> list[dict]:
    params = {"dataInicial": start, "dataFinal": end, "codigoModalidadeContratacao": mod, "pagina": 1, "tamanhoPagina": MAX_PAGE}
    r = client.get(API_BASE, params=params)
    if r.status_code == 204:
        return []
    if r.status_code == 429:
        logger.warning("  rate limited, esperando 30s...")
        time.sleep(30)
        r = client.get(API_BASE, params=params)
    r.raise_for_status()
    data = r.json()
    records = data.get("data", [])
    total = int(data.get("totalPaginas", 1) or 1)
    for page in range(2, total + 1):
        params["pagina"] = page
        time.sleep(DELAY)
        r = client.get(API_BASE, params=params)
        if r.status_code == 204:
            break
        if r.status_code == 429:
            logger.warning("  rate limited, esperando 30s...")
            time.sleep(30)
            r = client.get(API_BASE, params=params)
        r.raise_for_status()
        records.extend(r.json().get("data", []))
    return records


@click.command()
@click.option("--start-date", default="2021-01-01")
@click.option("--end-date", default=lambda: datetime.now().strftime("%Y-%m-%d"))
@click.option("--output-dir", default=None)
@click.option("--skip-existing/--no-skip-existing", default=True)
@click.option("--rsync/--no-rsync", default=True)
def main(start_date: str, end_date: str, output_dir: str | None, skip_existing: bool, rsync: bool):
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
    parquet_dir = out / DATASET / TABLE
    parquet_path = parquet_dir / f"contratos_{start_date}_{end_date}.parquet"
    if skip_existing and parquet_path.exists():
        logger.info("Pulando PNCP (já existe): %s", parquet_path)
        return

    all_records: list[dict] = []
    client = httpx.Client(follow_redirects=True, timeout=90, headers={"User-Agent": "rodado-etl/1.0"})
    current = start
    total_mod = len(MODALIDADES)

    try:
        while current < end:
            win_end = min(current + timedelta(days=10), end)
            s = current.strftime("%Y%m%d")
            e = win_end.strftime("%Y%m%d")
            for i, mod in enumerate(MODALIDADES):
                logger.info("PNCP [%s-%s] modalidade %d/%d", s, e, i + 1, total_mod)
                records = _fetch_all(client, s, e, mod)
                all_records.extend(records)
                logger.info("  +%d registros", len(records))
            current = win_end + timedelta(days=1)
    except KeyboardInterrupt:
        logger.info("Interrompido")
    finally:
        client.close()

    logger.info("PNCP: total %d registros", len(all_records))
    if not all_records:
        logger.warning("Nenhum registro encontrado")
        return

    df = pd.DataFrame(all_records)
    write_parquet(df, parquet_path)

    if rsync:
        rsync_to_beelink(parquet_dir, f"{DATASET}/{TABLE}")

    logger.info("PNCP concluído: %s", parquet_path)


if __name__ == "__main__":
    main()
