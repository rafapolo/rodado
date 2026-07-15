#!/usr/bin/env python3
"""
Fetch SICAF (Sistema de Cadastramento Unificado de Fornecedores) supplier
registry from the ComprasGov open-data API -> Parquet -> beelink.

Source: dadosabertos.compras.gov.br, endpoint /modulo-fornecedor/1_consultarFornecedor
(same host/family as CATMAT/CATSER, see comprasgov_catmatcatser.py for the
domain-discovery notes). No auth required. The `ativo` boolean param is
REQUIRED by the API (confirmed: omitting it is rejected) — there is no single
"all suppliers" call, so this fetches both ativo=true and ativo=false and
concatenates them with a `pesquisado_ativo` column recording which query
found the row.

Pagination: `pagina` + `tamanhoPagina` (max 500). Confirmed totals on
2026-07-10: ativo=true -> 822,339 rows (~1,645 pages); ativo=false ->
133,664 rows (~268 pages). ~956k rows total, fetched concurrently via a
thread pool.

Usage:
    python3 scripts/scrap/comprasgov_sicaf.py
"""

import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import Request, urlopen

BEELINK_HOST = "beelink"
BEELINK_PATH = "~/rodado/br_comprasgov_sicaf/fornecedores"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
TEMP_DIR = Path("/private/tmp/claude-501/-Users-polux-Projetos-rodado/50905fb8-827b-445f-bb28-3e8ed468da54/scratchpad/comprasgov_sicaf")

ENDPOINT = "https://dadosabertos.compras.gov.br/modulo-fornecedor/1_consultarFornecedor"
PAGE_SIZE = 500
WORKERS = 4
MAX_ATTEMPTS = 8


def fetch_page(ativo: str, pagina: int) -> dict:
    url = f"{ENDPOINT}?pagina={pagina}&tamanhoPagina={PAGE_SIZE}&ativo={ativo}"
    req = Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    for attempt in range(MAX_ATTEMPTS):
        try:
            with urlopen(req, timeout=60) as resp:
                return json.loads(resp.read())
        except Exception as e:
            is_429 = "429" in str(e)
            wait = (6 * (attempt + 1)) if is_429 else (1 + attempt)
            if attempt == MAX_ATTEMPTS - 1:
                print(f"  ativo={ativo} pagina={pagina}: giving up ({e})", file=sys.stderr)
                return {"resultado": [], "_failed_pagina": pagina}
            time.sleep(wait)
    return {"resultado": [], "_failed_pagina": pagina}


def fetch_all_for(ativo: str, checkpoint_cb=None, all_rows_prefix=None) -> list:
    print(f"=== ativo={ativo} ===")
    first = fetch_page(ativo, 1)
    total_paginas = first.get("totalPaginas", 1)
    total_registros = first.get("totalRegistros", 0)
    print(f"  totalRegistros={total_registros} totalPaginas={total_paginas}")

    rows = list(first.get("resultado", []))
    for r in rows:
        r["pesquisado_ativo"] = ativo

    failed_paginas = []
    if total_paginas > 1:
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futures = {}
            for p in range(2, total_paginas + 1):
                futures[ex.submit(fetch_page, ativo, p)] = p
                time.sleep(0.05)  # light pacing to avoid tripping rate limits
            done = 0
            for fut in as_completed(futures):
                page = fut.result()
                if "_failed_pagina" in page:
                    failed_paginas.append(page["_failed_pagina"])
                page_rows = page.get("resultado", [])
                for r in page_rows:
                    r["pesquisado_ativo"] = ativo
                rows.extend(page_rows)
                done += 1
                if done % 100 == 0:
                    print(f"  ... {done}/{total_paginas - 1} pages, {len(rows)} rows so far")
                # Checkpoint to beelink periodically so a killed/interrupted
                # process doesn't lose everything fetched so far — this cost
                # an entire ~1-hour run once already (killed at 1600/1644
                # pages with nothing persisted, since the old code only
                # pushed at phase-end). Push whatever's accumulated so far
                # (prior phases' rows + this phase's rows-to-date).
                if done % 200 == 0 and checkpoint_cb is not None:
                    combined = (all_rows_prefix or []) + rows
                    checkpoint_cb(combined, f"checkpoint ativo={ativo} {done}/{total_paginas - 1} pages")

    # Serial retry pass for any pages that failed under concurrent load
    # (typically 429s) — much gentler pacing, one at a time.
    if failed_paginas:
        print(f"  Retrying {len(failed_paginas)} failed pages serially ...")
        still_failed = []
        for p in failed_paginas:
            time.sleep(2)
            page = fetch_page(ativo, p)
            if "_failed_pagina" in page:
                still_failed.append(p)
            else:
                page_rows = page.get("resultado", [])
                for r in page_rows:
                    r["pesquisado_ativo"] = ativo
                rows.extend(page_rows)
        if still_failed:
            print(f"  WARNING: {len(still_failed)} pages permanently failed: {still_failed}", file=sys.stderr)

    print(f"  Subtotal rows: {len(rows)} (expected ~{total_registros})")
    return rows


def push_rows(all_rows: list, label: str) -> bool:
    import pyarrow as pa
    import pyarrow.parquet as pq

    if not all_rows:
        print(f"No rows to push ({label}) — skipping.", file=sys.stderr)
        return False

    table = pa.Table.from_pylist(all_rows)
    parquet_path = TEMP_DIR / "fornecedores.parquet"
    pq.write_table(table, str(parquet_path), compression="zstd")
    print(f"[{label}] Wrote {parquet_path} ({parquet_path.stat().st_size / 1e6:.1f} MB, {table.num_rows} rows)")

    for attempt in range(20):
        mkdir_ok = subprocess.run(f"ssh {BEELINK_HOST} 'mkdir -p {BEELINK_PATH}'", shell=True).returncode == 0
        if mkdir_ok:
            break
        print(f"  ssh unreachable (attempt {attempt + 1}/20), retrying in 15s ...", file=sys.stderr)
        time.sleep(15)
    else:
        print(f"ssh beelink unreachable after retries — aborting push ({label}).", file=sys.stderr)
        return False

    result = subprocess.run(
        f"rsync -av {parquet_path} {BEELINK_HOST}:{BEELINK_PATH}/",
        shell=True,
    )
    if result.returncode != 0:
        print(f"rsync failed ({label})", file=sys.stderr)
        return False

    print(f"[{label}] Pushed to {BEELINK_HOST}:{BEELINK_PATH}/{parquet_path.name}")
    return True


def main():
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # Fetch+push incrementally per `ativo` phase rather than waiting for both
    # to finish: ativo=true alone is ~822k rows (the bulk of the table), so
    # pushing it as soon as it's ready gets real data onto beelink much
    # sooner instead of holding everything hostage to the slower combined
    # runtime. The final push (after ativo=false) overwrites this with the
    # complete ~956k-row file.
    all_rows = []
    ok = True
    for ativo in ("true", "false"):
        prefix = list(all_rows)  # rows from prior phases, for checkpoint pushes
        phase_rows = fetch_all_for(ativo, checkpoint_cb=push_rows, all_rows_prefix=prefix)
        all_rows.extend(phase_rows)
        print(f"Cumulative rows so far: {len(all_rows)}")
        label = f"partial after ativo={ativo}" if ativo == "true" else "final"
        ok = push_rows(all_rows, label)

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
