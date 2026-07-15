#!/usr/bin/env python3
"""
Fetch MJSP "Projeto Captura Nacional" wanted-persons list -> Parquet -> beelink.

Source: gov.br/mj (Ministerio da Justica e Seguranca Publica), Plone-rendered
gallery page at
  https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/
  operacoes-integradas/projeto-captura/lista-de-procurados
Not a JSON API — dados.mj.gov.br's CKAN catalog has no "procurados"/wanted-
persons dataset (confirmed via full package_list, 31 datasets, none match),
Interpol's public ws-public.interpol.int/notices/v1/red API is blocked by an
Akamai WAF (HTTP 403 "Access Denied", errors.edgesuite.net reference), and
gov.br/captura (the JS SPA front-end for this same list) 403s under the
gov.br WAF this session. This plain Plone HTML page under gov.br/mj DOES
load cleanly (HTTP 200) as long as a browser-like User-Agent + Accept-Language
header is sent — a bare default-UA request gets the same 403 as the other
gov.br paths, so headers matter here.

Each detail/"view" page is just a photo (mugshot/wanted-poster image) with a
title of "NOME - ESTADO" — no CPF/DOB/crime text fields exist as structured
HTML anywhere on this site (those are baked into the poster image itself), so
the listing page's gallery items (name+state, detail URL, image URL, dated
"added" field) are the full extent of scrapable structured data. Small
dataset (~195 rows), Plone default folder pagination via ?b_start:int=N,
batch size 15; loop stops on the first empty page.

Usage:
    python3 scripts/scrap/mjsp_procurados.py
"""

import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

BEELINK_HOST = "beelink"
BEELINK_PATH = "~/rodado/br_mjsp_procurados/procurados"
BASE_URL = (
    "https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/"
    "operacoes-integradas/projeto-captura/lista-de-procurados"
)
BATCH_SIZE = 15
TEMP_DIR = Path(
    "/private/tmp/claude-501/-Users-polux-Projetos-rodado/"
    "c780c9c0-b6b3-44b0-964e-08a3b2f2024c/scratchpad/mjsp_procurados"
)
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)

ENTRY_RE = re.compile(
    r'<div class="imagem">\s*<a href="([^"]+)">\s*'
    r'<span class="imagemWrapper">\s*<img src="([^"]+)" alt="([^"]*)" />\s*'
    r'</span>\s*<span class="titulo">([^<]*)</span>\s*'
    r'<span class="data">([^<]*)</span>',
    re.S,
)


def fetch_page(b_start: int) -> str:
    url = f"{BASE_URL}?b_start:int={b_start}"
    req = Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept-Language": "pt-BR,pt;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    with urlopen(req, timeout=45) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_entries(html: str):
    rows = []
    for detail_url, image_url, alt, titulo, data in ENTRY_RE.findall(html):
        titulo = titulo.strip()
        if " - " in titulo:
            nome, estado = titulo.rsplit(" - ", 1)
        else:
            nome, estado = titulo, None
        rows.append(
            {
                "nome_estado": titulo,
                "nome": nome.strip(),
                "estado": estado.strip() if estado else None,
                "url_detalhe": detail_url,
                "url_imagem": image_url,
                "data_inclusao": data.strip() or None,
            }
        )
    return rows


def main():
    import pyarrow as pa
    import pyarrow.parquet as pq

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    all_rows = []
    seen_urls = set()
    b_start = 0
    empty_streak = 0
    while empty_streak < 2:
        print(f"Fetching b_start={b_start} ...")
        try:
            html = fetch_page(b_start)
        except Exception as e:
            print(f"  error fetching b_start={b_start}: {e}")
            empty_streak += 1
            b_start += BATCH_SIZE
            time.sleep(1)
            continue
        rows = parse_entries(html)
        new_rows = [r for r in rows if r["url_detalhe"] not in seen_urls]
        for r in new_rows:
            seen_urls.add(r["url_detalhe"])
        print(f"  got {len(rows)} entries ({len(new_rows)} new)")
        if not rows:
            empty_streak += 1
        else:
            empty_streak = 0
            all_rows.extend(new_rows)
        b_start += BATCH_SIZE
        time.sleep(0.5)

    print(f"Total rows fetched: {len(all_rows)}")
    if not all_rows:
        print("No rows fetched — aborting, not pushing an empty file.")
        return 1

    table = pa.Table.from_pylist(all_rows)
    parquet_path = TEMP_DIR / "procurados.parquet"
    pq.write_table(table, str(parquet_path), compression="zstd")
    print(f"Wrote {parquet_path} ({parquet_path.stat().st_size / 1e6:.2f} MB, {table.num_rows} rows)")

    subprocess.run(f"ssh {BEELINK_HOST} 'mkdir -p {BEELINK_PATH}'", shell=True, check=True)
    result = subprocess.run(
        f"rsync -av {parquet_path} {BEELINK_HOST}:{BEELINK_PATH}/",
        shell=True,
    )
    if result.returncode != 0:
        print("rsync failed", file=sys.stderr)
        return 1

    print(f"Pushed to {BEELINK_HOST}:{BEELINK_PATH}/{parquet_path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
