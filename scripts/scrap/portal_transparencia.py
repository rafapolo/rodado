#!/usr/bin/env python3
"""Scrape Portal da Transparencia bulk CSV datasets.

Four datasets confirmed working via direct CDN download (no API key needed):

  1. Garantia-Safra (2013-01+, monthly, 7 cols)
  2. Seguro-Defeso (2013-01+, monthly, 9 cols)
  3. Pe-de-Meia   (2024-03+, monthly, 18 cols)
  4. Viagens      (2011+, yearly, 4 sub-tables)

CDN: dadosabertos-download.cgu.gov.br/PortalDaTransparencia/saida/<slug>/

Each dataset's page lists available periods via JS `arquivos.push()` objects.
The download URL is constructed as: <CDN>/<slug>/<period>_<origin>.zip

Usage:
  python3 scripts/scrap/portal_transparencia.py [--years N] [--dataset garantia-safra]
  --years N: only process last N years (default: all)
  --dataset: only process one dataset, e.g. 'viagens' or 'garantia-safra'
"""

import csv
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
import uuid
from pathlib import Path
from zipfile import ZipFile

import pyarrow as pa
import pyarrow.parquet as pq
import requests

CDN_BASE = "https://dadosabertos-download.cgu.gov.br/PortalDaTransparencia/saida"
BEELINK_HOST = os.environ.get("BEELINK_HOST", "beelink")
TEMP_DIR = Path(f"/tmp/portal_transparencia_{uuid.getnode()}")

DATA_DICT = {
    "garantia-safra": {
        "dataset": "br_cgu_garantia_safra",
        "slug": "garantia-safra",
        "origin": "GarantiaSafra",
        "period": "monthly",
        "tables": {"garantia_safra": "GarantiaSafra"},
    },
    "seguro-defeso": {
        "dataset": "br_cgu_seguro_defeso",
        "slug": "seguro-defeso",
        "origin": "SeguroDefeso",
        "period": "monthly",
        "tables": {"seguro_defeso": "SeguroDefeso"},
    },
    "pe-de-meia": {
        "dataset": "br_cgu_pe_de_meia",
        "slug": "pe-de-meia",
        "origin": "PeDeMeia",
        "period": "monthly",
        "tables": {"pe_de_meia": "PeDeMeia"},
    },
    "viagens": {
        "dataset": "br_cgu_viagens",
        "slug": "viagens",
        "origin": None,  # extracted from page
        "period": "yearly",
        "tables": {
            "viagem": "Viagem",
            "pagamento": "Pagamento",
            "passagem": "Passagem",
            "trecho": "Trecho",
        },
    },
}


def get_page_periods(slug: str) -> list[dict]:
    url = f"https://portaldatransparencia.gov.br/download-de-dados/{slug}"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    html = resp.text
    periods = []
    for match in re.finditer(
        r'arquivos\.push\(\{"ano"\s*:\s*"(\d{4})",\s*"mes"\s*:\s*"(\d*)"[^}]*"origem"\s*:\s*"([^"]+)"',
        html,
    ):
        ano, mes, origem = match.group(1), match.group(2) or None, match.group(3)
        periods.append({"ano": ano, "mes": mes, "origem": origem})
    return periods


def get_viagens_origin(html: str) -> str:
    match = re.search(r'"origem"\s*:\s*"(\d+_Viagens)"', html)
    if match:
        return match.group(1)
    return "20260719_Viagens"


def clean_col(name: str) -> str:
    name = name.strip()
    name = name.replace("ª", "a").replace("º", "o")
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")
    name = name.replace(" ", "_").replace("-", "_").replace("/", "_")
    name = re.sub(r"[^a-zA-Z0-9_]", "", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_").lower()


def csv_rows_to_parquet(csv_text: str, parquet_path: Path, chunk: int = 50000):
    f = io.StringIO(csv_text)
    reader = csv.DictReader(f, delimiter=";")
    col_map = {clean_col(c): c for c in reader.fieldnames}
    fieldnames = list(col_map.keys())
    schema = pa.schema([(c, pa.string()) for c in fieldnames])

    rows = {c: [] for c in fieldnames}
    for i, csv_row in enumerate(reader):
        for c, orig_c in col_map.items():
            rows[c].append(csv_row.get(orig_c, ""))
        if (i + 1) % chunk == 0:
            _flush(rows, schema, parquet_path)
            rows = {c: [] for c in fieldnames}
    if any(rows.values()):
        _flush(rows, schema, parquet_path)


def _flush(rows, schema, path: Path):
    batch = pa.table(rows, schema=schema)
    if path.exists():
        existing = pq.read_table(path)
        pq.write_table(pa.concat_tables([existing, batch]), path)
    else:
        pq.write_table(batch, path)


def download_and_convert(dataset_info: dict, period: dict) -> dict[str, Path]:
    slug = dataset_info["slug"]
    ano, mes = period["ano"], period.get("mes")

    if dataset_info["period"] == "monthly":
        period_str = f"{ano}{mes}"
        url = f"{CDN_BASE}/{slug}/{period_str}_{dataset_info['origin']}.zip"
    else:  # yearly (viagens)
        origin = period.get("origem", dataset_info.get("origin", ""))
        url = f"{CDN_BASE}/{slug}/{ano}_{origin}.zip"

    print(f"  Downloading {slug} {ano}/{mes or ''}...", file=sys.stderr)
    resp = requests.get(url, timeout=600)
    if resp.status_code == 404:
        print(f"    Not found: {url}", file=sys.stderr)
        return {}
    resp.raise_for_status()

    result = {}
    with ZipFile(io.BytesIO(resp.content)) as zf:
        for table_name, csv_prefix in dataset_info["tables"].items():
            candidates = [n for n in zf.namelist() if csv_prefix in n and n.endswith(".csv")]
            if not candidates:
                continue
            outdir = TEMP_DIR / dataset_info["dataset"] / table_name
            outdir.mkdir(parents=True, exist_ok=True)
            parquet_path = outdir / f"{ano}_{mes or ''}_{table_name}.parquet"

            csv_data = zf.read(candidates[0]).decode("iso-8859-1")
            csv_rows_to_parquet(csv_data, parquet_path)
            print(f"    {table_name}: {parquet_path.stat().st_size / 1024:.0f} KB", file=sys.stderr)
            result[table_name] = parquet_path

    return result


def push_to_beelink(dataset: str, table: str, folder_name: str):
    src = TEMP_DIR / dataset / table
    if not any(src.glob("*.parquet")):
        return
    remote_dir = f"{BEELINK_HOST}:~/rodado/{dataset}/{folder_name}/"
    subprocess.run(["ssh", BEELINK_HOST, f"mkdir -p ~/rodado/{dataset}/{folder_name}"],
                   capture_output=True, timeout=10)
    subprocess.run(["rsync", "-avz", "--remove-source-files", f"{src}/", remote_dir],
                   capture_output=True, timeout=600)
    print(f"  Pushed {dataset}/{folder_name}", file=sys.stderr)


def process_dataset(key: str, max_years: int | None = None):
    info = DATA_DICT[key]
    periods = get_page_periods(info["slug"])

    if info["slug"] == "viagens":
        origin = None
        for p in periods:
            if "origem" in p:
                origin = p["origem"]
                break
        if origin:
            info["origin"] = origin

    if max_years:
        years = sorted(set(int(p["ano"]) for p in periods), reverse=True)
        cutoff = years[:max_years][-1] if len(years) > max_years else None
        periods = [p for p in periods if cutoff is None or int(p["ano"]) >= cutoff]

    print(f"Processing {info['slug']} ({len(periods)} periods)...", file=sys.stderr)

    for i, period in enumerate(periods):
        try:
            tables = download_and_convert(info, period)
            for table_name in tables:
                push_to_beelink(info["dataset"], table_name, table_name.replace(" ", "_"))
        except Exception as e:
            print(f"  Error on {info['slug']} {period['ano']}/{period.get('mes','')}: {e}", file=sys.stderr)

    print(f"Done with {info['slug']}.", file=sys.stderr)


def main():
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", type=int, default=None, help="Last N years only")
    parser.add_argument("--dataset", type=str, default=None, help="One dataset key only")
    args = parser.parse_args()

    datasets = [args.dataset] if args.dataset else list(DATA_DICT)

    for key in datasets:
        if key in DATA_DICT:
            process_dataset(key, max_years=args.years)

    print("All done.", file=sys.stderr)


if __name__ == "__main__":
    main()
