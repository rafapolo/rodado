#!/usr/bin/env python3
"""Scrape IBAMA embargo enforcement registry.

Source: dadosabertos.ibama.gov.br (CKAN), dataset "fiscalizacao-termo-de-embargo"
8 tables, accessed via CKAN resource URLs.  Previously blocked by SSL proxy
errors (2026-07-13), now unblocked and fully accessible (2026-07-24).

Resources:
  - termo_embargo    — main CSV zip (47MB)
  - itens            — embargoed items with polygon
  - coordenadas      — geographic coordinates of embargoed areas
  - anexo            — attachments/documents
  - decisao          — judicial decisions
  - enquadramento    — legal classification
  - enquadramento_complementar — complementary classification
  - termo_embargo_historico — historical changes
"""

import csv
import io
import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from zipfile import ZipFile

import pyarrow as pa
import pyarrow.parquet as pq
import requests

# CKAN package
PACKAGE_SHOW = "https://dadosabertos.ibama.gov.br/api/3/action/package_show?id=fiscalizacao-termo-de-embargo"
DATASET = "br_ibama_embargos"
TEMP_DIR = Path(f"/tmp/ibama_embargos_{uuid.getnode()}")
BEELINK_HOST = os.environ.get("BEELINK_HOST", "beelink")

# Table name mapping: CKAN resource name -> slug
TABLE_SLUGS = {
    "Termos de embargo": "termo_embargo",
    "Termos de embargo - itens": "itens",
    "Termos de embargo - coordenadas geográficas": "coordenadas",
    "Termos de embargo - anexos": "anexo",
    "Termos de embargo - decisões judiciais": "decisao",
    "Termos de embargo - enquadramento": "enquadramento",
    "Termos de embargo - enquadramento complementar": "enquadramento_complementar",
    "Termos de embargo - histórico": "termo_embargo_historico",
}


def get_resource_urls() -> dict[str, str]:
    resp = requests.get(PACKAGE_SHOW, timeout=15)
    resp.raise_for_status()
    resources = resp.json()["result"]["resources"]
    # Map name -> CSV url
    urls = {}
    for r in resources:
        name = r["name"]
        fmt = r["format"]
        if name in TABLE_SLUGS and fmt == "CSV":
            urls[TABLE_SLUGS[name]] = r["url"]
    return urls


def _clean_col(name: str) -> str:
    return name.replace(" ", "_").replace("(", "").replace(")", "").lower()


def download_and_convert(table_slug: str, url: str) -> Path:
    print(f"  Downloading {table_slug}...", file=sys.stderr)
    resp = requests.get(url, timeout=300)
    resp.raise_for_status()

    content = resp.content
    outdir = TEMP_DIR / table_slug
    outdir.mkdir(parents=True, exist_ok=True)
    parquet_path = outdir / f"{table_slug}.parquet"

    if url.endswith(".zip"):
        with ZipFile(io.BytesIO(content)) as zf:
            csv_names = [n for n in zf.namelist() if n.endswith(".csv")]
            if not csv_names:
                print(f"  No CSV in zip for {table_slug}!", file=sys.stderr)
                return None
            with zf.open(csv_names[0]) as f:
                text = io.TextIOWrapper(f, encoding="iso-8859-1")
                reader = csv.DictReader(text)
                cols = [_clean_col(c) for c in reader.fieldnames]
                _write_parquet(reader, cols, parquet_path)
    else:
        text = io.TextIOWrapper(io.BytesIO(content), encoding="iso-8859-1")
        reader = csv.DictReader(text)
        cols = [_clean_col(c) for c in reader.fieldnames]
        _write_parquet(reader, cols, parquet_path)

    return parquet_path


def _write_parquet(reader, cols, path: Path):
    schema = pa.schema([(c, pa.string()) for c in cols])
    rows = {c: [] for c in cols}
    count = 0
    for csv_row in reader:
        for c in cols:
            rows[c].append(csv_row.get(c, ""))
        count += 1
        if count >= 50000:
            _flush(rows, schema, path)
            rows = {c: [] for c in cols}
            count = 0
    if count > 0:
        _flush(rows, schema, path)


def _flush(rows, schema, path: Path):
    batch = pa.table(rows, schema=schema)
    if path.exists():
        existing = pq.read_table(path)
        pq.write_table(pa.concat_tables([existing, batch]), path)
    else:
        pq.write_table(batch, path)
    print(f"    Flushed {batch.num_rows} rows to {path.name}", file=sys.stderr)


def push_to_beelink(table_slug: str):
    src = TEMP_DIR / table_slug / f"{table_slug}.parquet"
    if not src.exists():
        return
    remote_dir = f"{BEELINK_HOST}:~/rodado/{DATASET}/{table_slug}/"
    subprocess.run(["ssh", BEELINK_HOST, f"mkdir -p ~/rodado/{DATASET}/{table_slug}"],
                   capture_output=True, timeout=10)
    subprocess.run(["rsync", "-avz", str(src), remote_dir],
                   capture_output=True, timeout=120)
    print(f"  Pushed {table_slug}", file=sys.stderr)


def main():
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    print("Fetching resource URLs from CKAN...", file=sys.stderr)
    urls = get_resource_urls()
    print(f"Found {len(urls)} CSV resources", file=sys.stderr)

    for slug, url in urls.items():
        result = download_and_convert(slug, url)
        if result:
            sz = result.stat().st_size
            print(f"  {slug}: {sz / 1024:.0f} KB", file=sys.stderr)
            push_to_beelink(slug)
        print("", file=sys.stderr)

    print("Done.", file=sys.stderr)


if __name__ == "__main__":
    main()
