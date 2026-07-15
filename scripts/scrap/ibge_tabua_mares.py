#!/usr/bin/env python3
"""
Fetch tide predictions (tabua de mares) from IBGE's RMPG (Rede Maregrafica
Permanente para Geodesia) -> Parquet -> beelink.

Source: servicodados.ibge.gov.br/api/v1/rmpg/* -- a genuinely open, unauthenticated
IBGE API (documented at https://servicodados.ibge.gov.br/api/docs/rmpg?versao=1),
distinct from marinha.mil.br/dhn (WAF-blocked) and tabuademares.com (403,
no anonymous access). Discovered as a fresh alternative during a QA pass after
the Navy DHN and tabuademares.com paths were both re-confirmed dead.

RMPG operates 6 tide gauge stations on the Brazilian coast: Belem (PA),
Santana (AP), Fortaleza (CE), Salvador (BA), Arraial do Cabo (RJ), and
Imbituba (SC). The /previsao/{maregrafo} endpoint returns harmonic tide
predictions at 5-minute resolution for an arbitrary date range -- this is
the actual "tabua de mares" product (a nautical tide table), as opposed to
/nivel (raw sensor readings, a different scope -- real-time observed sea
level, left out here).

Date format gotcha: momentoInicial/momentoFinal must be "aaaa-mm-dd-hh-mi"
(dashes throughout, not "T" or colons) -- an ISO8601 datetime returns a 400.

Scope: 2 calendar years (2026 + 2027) x 6 stations, 5-minute resolution,
matching how published tide tables are typically issued a year or two ahead.
Predictions further out (tested 2031) return "Nao existe dados para o
filtro" -- the harmonic model isn't published indefinitely into the future,
so this range is close to the practical ceiling anyway.

Usage:
    python3 scripts/scrap/ibge_tabua_mares.py
"""

import subprocess
import sys
import time
from pathlib import Path

import requests

BEELINK_HOST = "beelink"
BEELINK_PATH = "~/rodado/global_ibge_tabua_mares/previsao"

BASE_URL = "https://servicodados.ibge.gov.br/api/v1/rmpg"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
TEMP_DIR = Path(
    "/private/tmp/claude-501/-Users-polux-Projetos-rodado/c780c9c0-b6b3-44b0-964e-08a3b2f2024c/scratchpad/tabua_mares"
)

YEARS = [2026, 2027]


def fetch_stations(session: requests.Session) -> list[dict]:
    resp = session.get(f"{BASE_URL}/maregrafos", timeout=60)
    resp.raise_for_status()
    return resp.json()


def fetch_previsao_range(
    session: requests.Session, sigla: str, momento_inicial: str, momento_final: str, retries: int = 4
) -> list[dict]:
    last_exc = None
    for attempt in range(retries):
        try:
            resp = session.get(
                f"{BASE_URL}/previsao/{sigla}",
                params={"momentoInicial": momento_inicial, "momentoFinal": momento_final},
                timeout=60,
            )
            if resp.status_code == 400:
                # "Nao existe dados para o filtro" -- range out of published bounds
                print(f"    {sigla} {momento_inicial}: no data ({resp.json().get('message')})")
                return []
            resp.raise_for_status()
            rows = resp.json()
            for row in rows:
                row["siglaMaregrafo"] = sigla
            return rows
        except requests.exceptions.RequestException as exc:
            last_exc = exc
            wait = 2 ** attempt
            print(f"    retry {attempt + 1}/{retries} after error: {exc} (sleeping {wait}s)")
            time.sleep(wait)
    raise last_exc


def fetch_previsao_year(session: requests.Session, sigla: str, year: int) -> list[dict]:
    # Fetch month-by-month: the full-year request (105k rows, ~5.5MB JSON) is
    # prone to transient "Response ended prematurely" chunked-encoding errors
    # against this server; monthly chunks are far more reliable.
    rows = []
    for month in range(1, 13):
        start = f"{year}-{month:02d}-01-00-00"
        if month == 12:
            end = f"{year}-12-31-23-55"
        else:
            import calendar

            last_day = calendar.monthrange(year, month)[1]
            end = f"{year}-{month:02d}-{last_day:02d}-23-55"
        month_rows = fetch_previsao_range(session, sigla, start, end)
        rows.extend(month_rows)
        time.sleep(0.2)
    return rows


def main():
    import pyarrow as pa
    import pyarrow.parquet as pq

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({"User-Agent": UA})

    print("Fetching station list...")
    stations = fetch_stations(session)
    siglas = [s["siglaMaregrafo"] for s in stations]
    print(f"  {len(siglas)} stations: {siglas}")

    all_rows = []
    for sigla in siglas:
        for year in YEARS:
            print(f"Fetching previsao {sigla} {year}...")
            rows = fetch_previsao_year(session, sigla, year)
            print(f"  {len(rows)} predictions")
            all_rows.extend(rows)
            time.sleep(0.3)

    print(f"\nTotal rows: {len(all_rows)}")
    if not all_rows:
        print("No rows fetched -- aborting, not pushing an empty file.")
        return 1

    table = pa.Table.from_pylist(all_rows)
    parquet_path = TEMP_DIR / "previsao.parquet"
    pq.write_table(table, str(parquet_path), compression="zstd")
    print(f"Wrote {parquet_path} ({parquet_path.stat().st_size / 1e6:.1f} MB, {table.num_rows} rows)")

    subprocess.run(f"ssh {BEELINK_HOST} 'mkdir -p {BEELINK_PATH}'", shell=True, check=True)
    result = subprocess.run(
        f"rsync -av {parquet_path} {BEELINK_HOST}:{BEELINK_PATH}/",
        shell=True,
    )
    if result.returncode != 0:
        print("rsync failed", file=sys.stderr)
        return 1

    # Also push the station catalog (small, useful join target for lat/lon/name).
    stations_table = pa.Table.from_pylist(stations)
    stations_path = TEMP_DIR / "estacoes.parquet"
    pq.write_table(stations_table, str(stations_path), compression="zstd")
    stations_beelink_path = "~/rodado/global_ibge_tabua_mares/estacoes"
    subprocess.run(f"ssh {BEELINK_HOST} 'mkdir -p {stations_beelink_path}'", shell=True, check=True)
    result2 = subprocess.run(
        f"rsync -av {stations_path} {BEELINK_HOST}:{stations_beelink_path}/",
        shell=True,
    )
    if result2.returncode != 0:
        print("rsync failed (estacoes)", file=sys.stderr)
        return 1

    print(f"Pushed to {BEELINK_HOST}:{BEELINK_PATH}/{parquet_path.name}")
    print(f"Pushed to {BEELINK_HOST}:{stations_beelink_path}/{stations_path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
