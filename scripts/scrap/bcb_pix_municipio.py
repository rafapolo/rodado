#!/usr/bin/env python3
"""
Fetch BCB Pix transactions per município (Olinda OData service) -> Parquet -> beelink.

Item 4 of tasks/fontes_novas.md, previously logged as "endpoint quebrado do
lado do BCB" -- it isn't. `TransacoesPixPorMunicipio` is exposed only as an
OData v4 composable FunctionImport, not a plain entity set:

    GET .../TransacoesPixPorMunicipio(DataBase=@DataBase)?@DataBase='YYYYMM'
        &$format=json&$filter=AnoMes eq YYYYMM

A bare entity-set GET (`TransacoesPixPorMunicipio?$top=5`) returns a 400
"URI is malformed" -- that 400 is what earlier sessions read as "broken".
The `DataBase` function parameter is required but does NOT filter the
result (rows for arbitrary months come back regardless of its value) --
real filtering needs `$filter=AnoMes eq <yyyymm>` on the composable
result, which returns exactly ~5,569 rows (one per município) per month.
`$skip` reliably 500s ("Erro desconhecido") at any offset, including 0 --
paginate by month via $filter instead, never by $skip.

Coverage: monthly since 2020-11 (202010 returns empty, 202011 has data).

API: https://olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/versao/v1/odata
No auth.

Usage:
    python3 scripts/scrap/bcb_pix_municipio.py
"""

import subprocess
import sys
import time
import urllib.request
import urllib.parse
import json
from datetime import date
from pathlib import Path

BEELINK_HOST = "beelink"
BEELINK_PATH = "~/rodado/br_bcb_pix_municipio/transacoes"
TEMP_DIR = Path("/private/tmp/claude-501/-Users-polux-Projetos-rodado/7606d457-5f78-4c87-9b85-004cd34feb87/scratchpad/bcb_pix")

BASE = "https://olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/versao/v1/odata/TransacoesPixPorMunicipio(DataBase=@DataBase)"

START = (2020, 11)


def month_range(start, end):
    y, m = start
    ey, em = end
    while (y, m) <= (ey, em):
        yield y * 100 + m
        m += 1
        if m == 13:
            m = 1
            y += 1


def fetch_month(anomes: int):
    params = {
        "@DataBase": f"'{anomes}'",
        "$format": "json",
        "$filter": f"AnoMes eq {anomes}",
        "$top": "10000",
    }
    qs = "&".join(f"{k}={urllib.parse.quote(str(v), safe=chr(39))}" for k, v in params.items())
    url = f"{BASE}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (rodado-scraper)"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read())
            return data.get("value", [])
        except Exception as e:
            print(f"      retry {attempt+1}/5 ({anomes}): {e}")
            time.sleep(2 ** attempt)
    print(f"    giving up on {anomes}")
    return []


def main():
    import pyarrow as pa
    import pyarrow.parquet as pq

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    today = date.today()
    end = (today.year, today.month)

    rows = []
    months_done = 0
    for anomes in month_range(START, end):
        data = fetch_month(anomes)
        print(f"{anomes} -> {len(data)} rows")
        if data:
            rows.extend(data)
            months_done += 1
        time.sleep(0.3)

    print(f"\nTotal rows: {len(rows)} across {months_done} months")
    if not rows:
        print("No rows fetched -- aborting.")
        return 1

    table = pa.Table.from_pylist(rows)
    parquet_path = TEMP_DIR / "transacoes.parquet"
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
