#!/usr/bin/env python3
"""
Fetch TCE-TO (Tribunal de Contas do Estado do Tocantins) "econtas" API data
-> Parquet -> beelink.

API: https://api.tceto.tc.br/econtas/api (Kong gateway in front of a PHP
backend). No auth needed for public read endpoints. Quirk: the backend
ignores content negotiation unless an explicit `Accept: application/json`
header is sent -- without it, it dumps PHP's print_r() text instead of JSON
(same HTTP 200 + `content-type: application/json` either way).

Endpoints probed:
  - /pautas         -> session agendas (current schedule), works, ~50 items
  - /pessoas?nome=   -> lookup by name, requires a query param (no bulk
                        listing observed) and returned empty/timeout in
                        adhoc testing -- skipped for this first pass
  - /decisoes        -> 501/internal error without further undocumented
                        params -- skipped for this first pass
  - /processo/{num}/{ano} -> per-process detail, needs a process number,
                        not a bulk listing -- skipped for this first pass

First pass mirrors just /pautas (the only endpoint that returns a bulk,
parameter-free listing). Other endpoints need specific query params
(names, process numbers) discovered from the transparency portal UI and are
left for a future pass.

Usage:
    python3 scripts/scrap/tce_to.py
"""

import subprocess
import sys
import urllib.request
import json
from pathlib import Path

BEELINK_HOST = "beelink"
DATASET_PATH = "~/rodado/br_tce_to/dados"
BEELINK_PATH = f"{DATASET_PATH}/pautas"
TEMP_DIR = Path("/private/tmp/claude-501/-Users-polux-Projetos-rodado/50905fb8-827b-445f-bb28-3e8ed468da54/scratchpad/tce_to")

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
PAUTAS_URL = "https://api.tceto.tc.br/econtas/api/pautas"


def _fetch_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def main():
    import pyarrow as pa
    import pyarrow.parquet as pq

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Fetching {PAUTAS_URL} ...")
    data = _fetch_json(PAUTAS_URL)
    pautas = data.get("pautas", []) if isinstance(data, dict) else data
    print(f"  -> {len(pautas)} pautas")

    if not pautas:
        print("No rows fetched - aborting.")
        return 1

    table = pa.Table.from_pylist(pautas)
    parquet_path = TEMP_DIR / "pautas.parquet"
    pq.write_table(table, str(parquet_path), compression="zstd")
    print(f"Wrote {parquet_path} ({parquet_path.stat().st_size / 1e3:.1f} KB)")

    subprocess.run(f"ssh {BEELINK_HOST} 'mkdir -p {DATASET_PATH}/pautas'", shell=True, check=True)
    result = subprocess.run(
        f"rsync -av {parquet_path} {BEELINK_HOST}:{DATASET_PATH}/pautas/",
        shell=True,
    )
    if result.returncode != 0:
        print("rsync failed", file=sys.stderr)
        return 1

    print(f"Pushed to {BEELINK_HOST}:{DATASET_PATH}/pautas/{parquet_path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
