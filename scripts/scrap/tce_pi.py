#!/usr/bin/env python3
"""
Fetch TCE-PI (Tribunal de Contas do Estado do Piaui) "Portal da Cidadania" API
-> Parquet -> beelink.

API: https://sistemas.tce.pi.gov.br/api/portaldacidadania (no auth, no key).
Base URL discovered via the apidoc bundle at
/api/portaldacidadania/docs/assets/main.bundle.js (route table embedded in the
bundled JS, no machine-readable OpenAPI spec exposed).

Pulls a small set of statewide/aggregate endpoints — full per-municipality
per-year drilldowns (despesas/receitas/servidores by idUnidadeGestora) exist
but would require enumerating 224 municipalities x ~15 years each, which is
out of scope for a first pass. This mirrors:
  - prefeituras: municipality registry (id/nome/codIBGE)
  - orgaos: state government units list (id/nome/sigla)
  - despesas_total: statewide expenditure totals by exercicio
  - receitas_total: statewide revenue totals by exercicio
  - licitacoes_estado: upcoming/recent statewide bidding notices (previsto/data)

Usage:
    python3 scripts/scrap/tce_pi.py
"""

import subprocess
import sys
import time
import urllib.request
import json
from pathlib import Path

BEELINK_HOST = "beelink"
DATASET_PATH = "~/rodado/br_tce_pi/dados"
BEELINK_PATH = f"{DATASET_PATH}/despesas_total"
TEMP_DIR = Path("/private/tmp/claude-501/-Users-polux-Projetos-rodado/50905fb8-827b-445f-bb28-3e8ed468da54/scratchpad/tce_pi")

BASE_URL = "https://sistemas.tce.pi.gov.br/api/portaldacidadania"

ENDPOINTS = {
    "prefeituras": "/prefeituras",
    "orgaos": "/orgaos/lista/2024",
    "despesas_total": "/despesas/total",
    "receitas_total": "/receitas/total",
    "licitacoes_estado": "/licitacoes/estado",
}


def _fetch_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (rodado-scraper)"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read())
        except Exception as e:
            print(f"      retry {attempt+1}/4: {e}")
            time.sleep(2 ** attempt)
    return None


def main():
    import pyarrow as pa
    import pyarrow.parquet as pq

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    written = {}
    for table_name, path in ENDPOINTS.items():
        url = BASE_URL + path
        print(f"Fetching {table_name} ({url}) ...")
        data = _fetch_json(url)
        if not data:
            print(f"  ✗ {table_name}: no data, skipping")
            continue
        if not isinstance(data, list):
            print(f"  ✗ {table_name}: unexpected shape ({type(data)}), skipping")
            continue
        try:
            table = pa.Table.from_pylist(data)
        except Exception as e:
            print(f"  ✗ {table_name}: failed to build table ({e})")
            continue
        parquet_path = TEMP_DIR / f"{table_name}.parquet"
        pq.write_table(table, str(parquet_path), compression="zstd")
        written[table_name] = (parquet_path, table.num_rows)
        print(f"  ✓ {table_name}: {table.num_rows} rows -> {parquet_path.name}")
        time.sleep(0.3)

    if not written:
        print("No tables written - aborting, nothing to push.")
        return 1

    for table_name, (parquet_path, rows) in written.items():
        remote_dir = f"{DATASET_PATH}/{table_name}"
        subprocess.run(f"ssh {BEELINK_HOST} 'mkdir -p {remote_dir}'", shell=True, check=True)
        result = subprocess.run(
            f"rsync -av {parquet_path} {BEELINK_HOST}:{remote_dir}/",
            shell=True,
        )
        if result.returncode != 0:
            print(f"  ✗ rsync failed for {table_name}")
            return 1
        print(f"  ✓ pushed {table_name} ({rows} rows) to {BEELINK_HOST}:{remote_dir}/")

    print(f"\nDone: {len(written)} tables pushed to {BEELINK_HOST}:{DATASET_PATH}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
