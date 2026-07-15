#!/usr/bin/env python3
"""
Fetch Senado Federal "Dados Abertos Legislativos" -> Parquet -> beelink.

Source: legis.senado.leg.br's official OpenAPI-documented REST API (spec at
https://legis.senado.leg.br/dadosabertos/v3/api-docs). The doc's originally
guessed "legis.senado.leg.br/dadosabertos/materia/tipos?formato=json" is a
retired path (clean 404) -- the real base is the same host/prefix, just
different concrete paths, found via the live OpenAPI spec rather than guessing.

Two header/param gotchas found while probing:
  - `?formato=json` alone is NOT reliably honored on every endpoint (some still
    return XML); passing `Accept: application/json` is what actually works.
  - `/dadosabertos/materia/pesquisa/lista` (the "obvious" matérias search
    endpoint) is DEPRECATED -- its own response embeds
    "DataDesativacaoCompleta": "2026-02-01" pointing at the replacement service
    "https://legis.senado.leg.br/dadosabertos/processo". This script uses the
    replacement `/dadosabertos/processo` endpoint instead.

Tables written (multi-table pipeline, one parquet file each under BEELINK_PATH's
parent, table name as filename):
  - materias   : /dadosabertos/processo?ano=YYYY, looped over every year with
                 data (empirically 1950 -> current; years with 0 rows are cheap
                 no-ops so the loop just starts from 1826 for safety/completeness).
  - votacoes   : /dadosabertos/votacao?ano=YYYY, same year loop.
  - comissoes  : /dadosabertos/comissao/lista/colegiados (single call, ALL
                 currently-active colegiados on both Senado and Congresso
                 Nacional, including type "CPI" / "Comissao Parlamentar de
                 Inquerito" -- e.g. "CPIPED", "CPIVD" show up here with
                 SiglaTipoColegiado=="CPI". This is why the separate "Senado
                 CPIs" catalog row folds into this same pipeline rather than
                 needing its own script -- there's no separate CPI-only
                 endpoint, CPIs are just one colegiado type among many.
                 NOTE: this listing is "EM ATIVIDADE" (currently active) only,
                 not a full historical archive of every CPI/comissao ever
                 constituted -- a deeper historical crawl would need per-CPI
                 lookups via /dadosabertos/comissao/{codigo}, left out of scope
                 for this pass, same spirit as other partial-scope decisions in
                 this catalog (TCE-PI, TCE-SP, etc).
  - senadores  : /dadosabertos/senador/lista/atual (current senators only,
                 same "current snapshot, not full historical" scoping).

Auth: none.

Usage:
    python3 scripts/scrap/senado_dadosabertos.py
"""

import subprocess
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
import json

BEELINK_HOST = "beelink"
BEELINK_PATH = "~/rodado/br_senado_dadosabertos/materias"
BEELINK_PATH_ROOT = "~/rodado/br_senado_dadosabertos"  # parent for the other tables

BASE = "https://legis.senado.leg.br/dadosabertos"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
TEMP_DIR = Path(
    "/private/tmp/claude-501/-Users-polux-Projetos-rodado/c780c9c0-b6b3-44b0-964e-08a3b2f2024c/scratchpad/senado"
)

FIRST_YEAR = 1826
LAST_YEAR = 2026


def fetch_json(url: str, timeout: int = 45):
    req = Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "application/json",
            "Accept-Language": "pt-BR,pt;q=0.9",
        },
    )
    for attempt in range(3):
        try:
            with urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read())
        except Exception as e:
            if attempt == 2:
                print(f"  {url}: giving up ({e})")
                return None
            time.sleep(1 + attempt)
    return None


def fetch_by_year(path: str, extract):
    """GET {BASE}{path}?ano=YYYY for every year in range, concatenate rows."""
    rows = []
    for year in range(FIRST_YEAR, LAST_YEAR + 1):
        data = fetch_json(f"{BASE}{path}?ano={year}")
        if not data:
            continue
        year_rows = extract(data)
        if year_rows:
            rows.extend(year_rows)
            print(f"  ano={year}: {len(year_rows)} rows (total {len(rows)})")
    return rows


def fetch_materias():
    def extract(data):
        return data if isinstance(data, list) else []

    return fetch_by_year("/processo", extract)


def fetch_votacoes():
    def extract(data):
        return data if isinstance(data, list) else []

    return fetch_by_year("/votacao", extract)


def fetch_comissoes():
    data = fetch_json(f"{BASE}/comissao/lista/colegiados")
    if not data:
        return []
    cols = (
        data.get("ListaColegiados", {})
        .get("Colegiados", {})
        .get("Colegiado", [])
    )
    if isinstance(cols, dict):  # single-element XML->JSON collapse
        cols = [cols]
    return cols


def fetch_senadores():
    data = fetch_json(f"{BASE}/senador/lista/atual")
    if not data:
        return []
    parl = (
        data.get("ListaParlamentarEmExercicio", {})
        .get("Parlamentares", {})
        .get("Parlamentar", [])
    )
    if isinstance(parl, dict):
        parl = [parl]
    # flatten the nested IdentificacaoParlamentar block for a queryable table
    flat = []
    for p in parl:
        row = {}
        ident = p.get("IdentificacaoParlamentar", {})
        for k, v in ident.items():
            if isinstance(v, (dict, list)):
                continue
            row[k] = v
        flat.append(row)
    return flat


def write_and_push(rows, table_name: str):
    import pyarrow as pa
    import pyarrow.parquet as pq

    if not rows:
        print(f"[{table_name}] No rows fetched -- skipping push.")
        return False

    table = pa.Table.from_pylist(rows)
    parquet_path = TEMP_DIR / f"{table_name}.parquet"
    pq.write_table(table, str(parquet_path), compression="zstd")
    print(f"[{table_name}] Wrote {parquet_path} ({parquet_path.stat().st_size / 1e6:.1f} MB, {table.num_rows} rows)")

    remote_dir = f"{BEELINK_PATH_ROOT}/{table_name}"
    mkdir_result = subprocess.run(f"ssh {BEELINK_HOST} 'mkdir -p {remote_dir}'", shell=True)
    if mkdir_result.returncode != 0:
        print(f"[{table_name}] ssh mkdir failed (beelink unreachable?) -- parquet kept locally at {parquet_path}, not pushed.", file=sys.stderr)
        return False
    result = subprocess.run(
        f"rsync -av {parquet_path} {BEELINK_HOST}:{remote_dir}/",
        shell=True,
    )
    if result.returncode != 0:
        print(f"[{table_name}] rsync failed -- parquet kept locally at {parquet_path}", file=sys.stderr)
        return False

    print(f"[{table_name}] Pushed to {BEELINK_HOST}:{remote_dir}/{parquet_path.name}")
    return True


def main():
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    ok = True

    print("=== senadores (current) ===")
    ok = write_and_push(fetch_senadores(), "senadores") and ok

    print("\n=== comissoes (current, incl. CPIs) ===")
    ok = write_and_push(fetch_comissoes(), "comissoes") and ok

    print("\n=== materias / processos (by year) ===")
    ok = write_and_push(fetch_materias(), "materias") and ok

    print("\n=== votacoes (by year) ===")
    ok = write_and_push(fetch_votacoes(), "votacoes") and ok

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
