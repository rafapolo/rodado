#!/usr/bin/env python3
"""
Fetch TCE-SP (Tribunal de Contas do Estado de Sao Paulo) municipal
transparency API data -> Parquet -> beelink.

API: https://transparencia.tce.sp.gov.br/api (undocumented at the /api root
-- a clean 404 with no WAF challenge; real endpoint patterns were recovered
from links embedded in the /apis HTML page). No auth needed.

Endpoints found:
  - /api/json/municipios                       -> full list of SP municipalities
  - /api/json/despesas/{municipio}/{ano}/{mes}  -> per-municipality expenses
  - /api/json/receitas/{municipio}/{ano}/{mes}  -> per-municipality revenue
  - /api/xml/... variants of the above also exist

despesas/receitas are keyed by (municipio slug, ano, mes) - mirroring all
644 municipalities x years x months is a combinatorial pull out of scope for
a first pass (same rationale as bcb_sgs's curated-subset note). This first
pass mirrors the municipios catalog only (small, complete, ~644 rows); a
future pass can iterate municipios x month to backfill despesas/receitas.

Usage:
    python3 scripts/scrap/tce_sp.py
"""

import subprocess
import sys
import urllib.request
import json
from pathlib import Path

BEELINK_HOST = "beelink"
DATASET_PATH = "~/rodado/br_tce_sp/dados"
BEELINK_PATH = f"{DATASET_PATH}/municipios"
TEMP_DIR = Path("/private/tmp/claude-501/-Users-polux-Projetos-rodado/50905fb8-827b-445f-bb28-3e8ed468da54/scratchpad/tce_sp")

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
MUNICIPIOS_URL = "https://transparencia.tce.sp.gov.br/api/json/municipios"


def _fetch_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def main():
    import pyarrow as pa
    import pyarrow.parquet as pq

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Fetching {MUNICIPIOS_URL} ...")
    municipios = _fetch_json(MUNICIPIOS_URL)
    print(f"  -> {len(municipios)} municipios")

    if not municipios:
        print("No rows fetched - aborting.")
        return 1

    table = pa.Table.from_pylist(municipios)
    parquet_path = TEMP_DIR / "municipios.parquet"
    pq.write_table(table, str(parquet_path), compression="zstd")
    print(f"Wrote {parquet_path} ({parquet_path.stat().st_size / 1e3:.1f} KB)")

    subprocess.run(f"ssh {BEELINK_HOST} 'mkdir -p {DATASET_PATH}/municipios'", shell=True, check=True)
    result = subprocess.run(
        f"rsync -av {parquet_path} {BEELINK_HOST}:{DATASET_PATH}/municipios/",
        shell=True,
    )
    if result.returncode != 0:
        print("rsync failed", file=sys.stderr)
        return 1

    print(f"Pushed to {BEELINK_HOST}:{DATASET_PATH}/municipios/{parquet_path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
