#!/usr/bin/env python3
"""
Fetch CATMAT (materiais) and CATSER (servicos) catalog items from the
ComprasGov open-data API -> Parquet -> beelink.

Source: dadosabertos.compras.gov.br (official ComprasGov/SIASG open-data
platform, Swagger UI at https://dadosabertos.compras.gov.br/swagger-ui/index.html,
OpenAPI spec at https://dadosabertos.compras.gov.br/v3/api-docs). NOT
compras.dados.gov.br (that host 301-redirects here) and NOT the guessed
/materiais/v1/materiais.json path from an earlier pass (404s) — the real
paths are under /modulo-material and /modulo-servico. No auth required.

Endpoints used (item-level, most granular useful table):
  - /modulo-material/4_consultarItemMaterial  (CATMAT items, ~247k rows)
  - /modulo-servico/6_consultarItemServico    (CATSER items, ~3.1k rows)

Pagination: `pagina` (1-based) + `tamanhoPagina` (max 500, confirmed via a
400 error on tamanhoPagina=1000: "Informe um numero de paginacao no
intervalo de 10 a 500"). Response includes totalRegistros/totalPaginas, so
page count is known upfront -> fetched concurrently via a thread pool.

Usage:
    python3 scripts/scrap/comprasgov_catmatcatser.py
"""

import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import Request, urlopen

BEELINK_HOST = "beelink"
DATASET_PATH = "~/rodado/br_comprasgov_catmatcatser"
BEELINK_PATH = f"{DATASET_PATH}/materiais"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
TEMP_DIR = Path("/private/tmp/claude-501/-Users-polux-Projetos-rodado/c780c9c0-b6b3-44b0-964e-08a3b2f2024c/scratchpad/comprasgov_catmatcatser")

BASE = "https://dadosabertos.compras.gov.br"
PAGE_SIZE = 500
WORKERS = 3
MAX_ATTEMPTS = 8

TABLES = {
    "materiais": {
        "endpoint": f"{BASE}/modulo-material/4_consultarItemMaterial",
        "beelink_path": f"{DATASET_PATH}/materiais",
        "extra_params": {"statusItem": "true"},
    },
    "servicos": {
        "endpoint": f"{BASE}/modulo-servico/6_consultarItemServico",
        "beelink_path": f"{DATASET_PATH}/servicos",
        "extra_params": {"statusServico": "true"},
    },
}


def fetch_page(endpoint: str, pagina: int, extra_params: dict) -> dict:
    params = {"pagina": pagina, "tamanhoPagina": PAGE_SIZE, **extra_params}
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{endpoint}?{qs}"
    req = Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    for attempt in range(MAX_ATTEMPTS):
        try:
            with urlopen(req, timeout=60) as resp:
                return json.loads(resp.read())
        except Exception as e:
            is_429 = "429" in str(e)
            wait = (6 * (attempt + 1)) if is_429 else (1 + attempt)
            if attempt == MAX_ATTEMPTS - 1:
                print(f"  pagina {pagina}: giving up ({e})", file=sys.stderr)
                return {"resultado": [], "_failed_pagina": pagina}
            time.sleep(wait)
    return {"resultado": [], "_failed_pagina": pagina}


def fetch_table(name: str, cfg: dict):
    print(f"=== {name} ===")
    first = fetch_page(cfg["endpoint"], 1, cfg["extra_params"])
    total_paginas = first.get("totalPaginas", 1)
    total_registros = first.get("totalRegistros", 0)
    print(f"  totalRegistros={total_registros} totalPaginas={total_paginas}")

    rows = list(first.get("resultado", []))
    failed_paginas = []
    if total_paginas > 1:
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futures = {}
            for p in range(2, total_paginas + 1):
                futures[ex.submit(fetch_page, cfg["endpoint"], p, cfg["extra_params"])] = p
                time.sleep(0.05)  # light pacing to avoid tripping rate limits
            done = 0
            for fut in as_completed(futures):
                page = fut.result()
                if "_failed_pagina" in page:
                    failed_paginas.append(page["_failed_pagina"])
                rows.extend(page.get("resultado", []))
                done += 1
                if done % 50 == 0:
                    print(f"  ... {done}/{total_paginas - 1} pages, {len(rows)} rows so far")

    if failed_paginas:
        print(f"  Retrying {len(failed_paginas)} failed pages serially ...")
        still_failed = []
        for p in failed_paginas:
            time.sleep(2)
            page = fetch_page(cfg["endpoint"], p, cfg["extra_params"])
            if "_failed_pagina" in page:
                still_failed.append(p)
            else:
                rows.extend(page.get("resultado", []))
        if still_failed:
            print(f"  WARNING: {len(still_failed)} pages permanently failed: {still_failed}", file=sys.stderr)

    print(f"  Total rows fetched: {len(rows)} (expected ~{total_registros})")
    return rows


def main():
    import pyarrow as pa
    import pyarrow.parquet as pq

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    ok = True
    for name, cfg in TABLES.items():
        rows = fetch_table(name, cfg)
        if not rows:
            print(f"  No rows fetched for {name} — skipping push.", file=sys.stderr)
            ok = False
            continue

        table = pa.Table.from_pylist(rows)
        parquet_path = TEMP_DIR / f"{name}.parquet"
        pq.write_table(table, str(parquet_path), compression="zstd")
        print(f"  Wrote {parquet_path} ({parquet_path.stat().st_size / 1e6:.1f} MB, {table.num_rows} rows)")

        beelink_path = cfg["beelink_path"]
        for attempt in range(20):
            mkdir_ok = subprocess.run(f"ssh {BEELINK_HOST} 'mkdir -p {beelink_path}'", shell=True).returncode == 0
            if mkdir_ok:
                break
            print(f"  ssh unreachable (attempt {attempt + 1}/20), retrying in 15s ...", file=sys.stderr)
            time.sleep(15)
        else:
            print(f"ssh beelink unreachable after retries — aborting push for {name}.", file=sys.stderr)
            ok = False
            continue
        result = subprocess.run(
            f"rsync -av {parquet_path} {BEELINK_HOST}:{beelink_path}/",
            shell=True,
        )
        if result.returncode != 0:
            print(f"rsync failed for {name}", file=sys.stderr)
            ok = False
            continue
        print(f"  Pushed to {BEELINK_HOST}:{beelink_path}/{parquet_path.name}")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
