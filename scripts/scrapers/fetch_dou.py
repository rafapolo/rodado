#!/usr/bin/env python3
from __future__ import annotations

import logging
import tempfile
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree

import click
import httpx
import pandas as pd

from _utils import download_file, rsync_to_beelink, write_parquet

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://dadosabertos-download.cgu.gov.br/inlabs"
# The Inlabs data portal at inlabs.in.gov.br now requires registration.
# The path dadosabertos-download.cgu.gov.br/inlabs returns 403.
# As of Jul/2026, monthly XML ZIPs are available at the Imprensa Nacional
# open data page: https://www.in.gov.br/acesso-a-informacao/dados-abertos/base-de-dados
# but the actual download URL pattern may differ.
SECTIONS = [1, 2, 3]
DATASET = "br_imprensa_nacional_dou"
TABLE = "atos"


def _month_range(start: str, end: str) -> list[str]:
    sy, sm = start.split("-")
    ey, em = end.split("-")
    y, m = int(sy), int(sm)
    ey, em = int(ey), int(em)
    months: list[str] = []
    while (y, m) <= (ey, em):
        months.append(f"{y % 100:02d}{m:02d}")
        m += 1
        if m > 12:
            m = 1
            y += 1
    return months


def _extract_acts_from_xml(xml_path: Path) -> list[dict]:
    try:
        tree = ElementTree.parse(xml_path)
    except ElementTree.ParseError:
        return []
    root = tree.getroot()
    articles = root.findall(".//article") or ([root] if root.tag == "article" else [])
    records: list[dict] = []
    for art in articles:
        ident = art.find(".//identifica")
        texto_el = art.find(".//Texto") or art.find(".//texto")
        title = (ident.find("titulo").text or "").strip() if ident is not None and ident.find("titulo") is not None else ""
        pub_date = (ident.find("data").text or "").strip() if ident is not None and ident.find("data") is not None else ""
        agency = (ident.find("orgao").text or "").strip() if ident is not None and ident.find("orgao") is not None else ""
        section = (ident.find("secao").text or "").strip() if ident is not None and ident.find("secao") is not None else ""
        abstract = ""
        if texto_el is not None:
            abstract = " ".join((p.text or "").strip() for p in texto_el.iter() if p.text and p.text.strip())
        records.append({
            "titulo": title,
            "orgao": agency,
            "ementa": abstract[:2000],
            "secao": section,
            "data_publicacao": pub_date,
            "url": f"https://www.in.gov.br/web/dou/-/{art.get('id', '')}",
        })
    return records


@click.command()
@click.option("--start-month", default="2024-01", help="Início (YYYY-MM)")
@click.option("--end-month", default=lambda: datetime.now().strftime("%Y-%m"), help="Fim (YYYY-MM)")
@click.option("--output-dir", default=None, help="Dir local (opcional, default = temp)")
@click.option("--skip-existing/--no-skip-existing", default=True)
@click.option("--rsync/--no-rsync", default=True, help="Enviar para beelink via rsync")
def main(start_month: str, end_month: str, output_dir: str | None, skip_existing: bool, rsync: bool):
    months = _month_range(start_month, end_month)
    logger.info("DOU: %s a %s (%d meses)", start_month, end_month, len(months))

    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
    raw_dir = out / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    all_records: list[dict] = []
    client = httpx.Client(follow_redirects=True, timeout=120)

    for aamm in months:
        for section in SECTIONS:
            zip_name = f"S0{section}{aamm}.zip"
            url = f"{BASE_URL}/{aamm}/{zip_name}"
            zip_path = raw_dir / zip_name

            if skip_existing and zip_path.exists():
                logger.info("Pulando %s (já baixado)", zip_name)
            else:
                ok = download_file(url, zip_path)
                if not ok:
                    continue

            try:
                with zipfile.ZipFile(zip_path) as zf:
                    for member in zf.namelist():
                        if not member.lower().endswith(".xml"):
                            continue
                        xml_data = zf.read(member)
                        tmp = raw_dir / f"tmp_{member}"
                        tmp.write_bytes(xml_data)
                        records = _extract_acts_from_xml(tmp)
                        all_records.extend(records)
                        tmp.unlink()
                        logger.info("  %s: %d atos", member, len(records))
            except zipfile.BadZipFile:
                logger.warning("ZIP corrompido: %s", zip_name)

    client.close()
    logger.info("Total de atos extraídos: %d", len(all_records))

    if not all_records:
        logger.warning("Nenhum ato encontrado")
        return

    df = pd.DataFrame(all_records)
    parquet_dir = out / DATASET / TABLE
    parquet_path = parquet_dir / f"dou_{start_month}_{end_month}.parquet"
    write_parquet(df, parquet_path)

    if rsync:
        rsync_to_beelink(parquet_dir, f"{DATASET}/{TABLE}")

    logger.info("DOU concluído: %s", parquet_path)


if __name__ == "__main__":
    main()
