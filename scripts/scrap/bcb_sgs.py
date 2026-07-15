#!/usr/bin/env python3
"""
Fetch a curated set of high-value BACEN/BCB SGS (Sistema Gerenciador de Séries
Temporais) series -> Parquet -> beelink.

The SGS catalog has thousands of series; mirroring all of them isn't a sane
first pass (per tasks/datasets_to_scrap.md's own note). This pulls a curated
set of well-known macro/finance series full history, one row per
(series_code, date, value) — long/tidy format so more series can be appended
later without a schema change.

API: https://api.bcb.gov.br/dados/serie/bcdata.sgs.<code>/dados?formato=json
No auth, no pagination cap observed for full-history pulls in practice.

Usage:
    python3 scripts/scrap/bcb_sgs.py
"""

import subprocess
import sys
import time
import urllib.request
import json
from pathlib import Path

BEELINK_HOST = "beelink"
BEELINK_PATH = "~/rodado/br_bcb_sgs/series"
TEMP_DIR = Path("/private/tmp/claude-501/-Users-polux-Projetos-rodado/50905fb8-827b-445f-bb28-3e8ed468da54/scratchpad/bcb_sgs")

# code -> human-readable series name (curated high-value subset, not the full SGS catalog)
SERIES = {
    1: "dolar_comercial_venda",
    11: "taxa_selic_diaria",
    12: "cdi_diario",
    433: "ipca_mensal",
    189: "igpm_mensal",
    4390: "meta_selic",
    4391: "selic_anualizada",
    7326: "taxa_juros_credito_pf_livre",
    20714: "taxa_juros_credito_pj_livre",
    24363: "inadimplencia_pf",
    21082: "inadimplencia_pj",
    4380: "pib_mensal_valores_correntes",
    24369: "divida_liquida_setor_publico_pib",
    13521: "reservas_internacionais",
    3695: "saldo_balanca_comercial",
    22701: "investimento_estrangeiro_direto",
    27574: "taxa_desocupacao_pnadc",
    1207: "estoque_credito_total",
}


def _fetch_url(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (rodado-scraper)"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read())
            if not isinstance(data, list):
                raise ValueError(f"unexpected response shape: {str(data)[:200]!r}")
            return data
        except Exception as e:
            print(f"      retry {attempt+1}/4: {e}")
            time.sleep(2 ** attempt)
    return None


def fetch_series(code: str, name: str):
    """Full-history pull; falls back to yearly-chunked date ranges if the API
    rejects an unbounded query (HTTP 406 — observed on high-frequency daily
    series like exchange rate/Selic once history exceeds some point count)."""
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados?formato=json"
    data = _fetch_url(url)
    if data is not None:
        return data

    print(f"    full-history pull failed for {code} ({name}), falling back to yearly chunks")
    from datetime import date
    all_points = []
    for year in range(2000, date.today().year + 1):
        chunk_url = (
            f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados"
            f"?formato=json&dataInicial=01/01/{year}&dataFinal=31/12/{year}"
        )
        chunk = _fetch_url(chunk_url)
        if chunk:
            all_points.extend(chunk)
        time.sleep(0.2)
    if not all_points:
        print(f"    giving up on series {code} ({name})")
    return all_points


def main():
    import pyarrow as pa
    import pyarrow.parquet as pq

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    for code, name in SERIES.items():
        print(f"Fetching series {code} ({name}) ...")
        data = fetch_series(code, name)
        for point in data:
            rows.append({
                "series_code": code,
                "series_name": name,
                "date": point.get("data"),
                "value": point.get("valor"),
            })
        print(f"  -> {len(data)} points")
        time.sleep(0.3)

    print(f"\nTotal rows: {len(rows)}")
    if not rows:
        print("No rows fetched — aborting.")
        return 1

    table = pa.Table.from_pylist(rows)
    parquet_path = TEMP_DIR / "series.parquet"
    pq.write_table(table, str(parquet_path), compression="zstd")
    print(f"Wrote {parquet_path} ({parquet_path.stat().st_size / 1e6:.1f} MB)")

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
