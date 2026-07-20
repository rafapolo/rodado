#!/usr/bin/env python3
"""
Fetch religion results from the Censo Demografico 2022 (IBGE) -> Parquet -> beelink.

Source: SIDRA table 9537 ("Pessoas de 10 anos ou mais de idade, por religiao,
segundo o sexo e os grupos de idade"), part of the "Censo Demografico 2022:
Religioes - Resultados preliminares da amostra" release. Genuinely open,
unauthenticated REST API at apisidra.ibge.gov.br -- no key needed.

This is a gap Base dos Dados does not cover: BD's br_ibge_censo_demografico
dataset only has microdata through 2010 (religion = v6121), and the mirrored
br_ibge_censo_2022 dataset (synced from BD's BigQuery project) has no religion
table at all yet. The 2010 microdata lets you compute anything (TFT, education
crosstabs, denomination-level splits); this 2022 table is coarser (10 broad
religion groups, no denomination-level detail, no individual weights) but is
the freshest available municipio-level religion snapshot for Brazil.

SIDRA quirk: a single /values request is capped at 50,000 returned values.
Municipio level x 10 religion categories = 55,700 -- just over the cap, so
the religion classification is split into two batches of 5 categories each.

Fetches 3 territorial levels for the same variable so municipio-level sums
can be cross-checked against the official published Brasil/UF totals:
  - n6 (municipio): 5570 rows x 10 religions = main table
  - n3 (UF): 27 x 10 = cross-check / convenience aggregate
  - n1 (Brasil): 1 x 10 = cross-check against IBGE's published headline numbers

Sex and age-group breakdowns exist in the same SIDRA table (and richer
religion x education / religion x fecundidade crosstabs exist in tables
10199 and 10087) but are left out of this first pass to keep the request
volume modest -- see tasks/datasets_to_scrap.md for the follow-up note.

Usage:
    python3 scripts/scrap/ibge_censo2022_religiao.py
"""

import subprocess
import sys
import time
from pathlib import Path

import requests

BEELINK_HOST = "beelink"
DATASET = "br_ibge_censo2022_religiao"
TABLE = "populacao_religiao"

BASE_URL = "https://apisidra.ibge.gov.br/values"
TABELA = 9537
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
TEMP_DIR = Path(
    "/private/tmp/claude-501/-Users-polux-Projetos-rodado/b46fb9a0-ca7b-48cf-bdb5-139cca3bae1b/scratchpad/censo2022_religiao"
)

# Religiao (classificacao 133) category ids, split into two batches to stay
# under SIDRA's 50,000-values-per-request cap at municipio level.
RELIGIAO_BATCH_1 = "95278,95263,95277,2826,2827"  # Total, Catolica, Evangelicas, Espirita, Umbanda/Candomble
RELIGIAO_BATCH_2 = "95274,95275,2836,12890,2837"  # Trad. indigenas, Outras, Sem religiao, Nao sabe, Sem declaracao

SEXO_TOTAL = "6794"
IDADE_TOTAL = "95253"

NIVEIS = {
    "municipio": "n6",
    "uf": "n3",
    "brasil": "n1",
}


def fetch_batch(session: requests.Session, nivel_param: str, religiao_batch: str, retries: int = 4) -> list[dict]:
    url = f"{BASE_URL}/t/{TABELA}/{nivel_param}/all/v/140/p/2022/c133/{religiao_batch}/c2/{SEXO_TOTAL}/c58/{IDADE_TOTAL}"
    last_exc = None
    for attempt in range(retries):
        try:
            resp = session.get(url, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict):
                # SIDRA returns a bare error string/object (not a list) on failure
                raise RuntimeError(f"SIDRA error: {data}")
            return data[1:]  # drop the header/description row
        except (requests.exceptions.RequestException, RuntimeError) as exc:
            last_exc = exc
            wait = 2 ** attempt
            print(f"    retry {attempt + 1}/{retries} after error: {exc} (sleeping {wait}s)")
            time.sleep(wait)
    raise last_exc


def fetch_nivel(session: requests.Session, nivel_param: str) -> list[dict]:
    rows = []
    for batch_name, batch in [("batch1", RELIGIAO_BATCH_1), ("batch2", RELIGIAO_BATCH_2)]:
        print(f"  {batch_name}...")
        rows.extend(fetch_batch(session, nivel_param, batch))
        time.sleep(0.3)
    return rows


def to_records(raw_rows: list[dict], nivel: str) -> list[dict]:
    return [
        {
            "nivel": nivel,
            "id_localidade": r["D1C"],
            "localidade": r["D1N"],
            "ano": int(r["D3C"]),
            "religiao": r["D4N"],
            "id_religiao_sidra": r["D4C"],
            "populacao_10_mais": int(r["V"]) if r["V"] not in (None, "-", "..", "...") else None,
        }
        for r in raw_rows
    ]


def main():
    import pyarrow as pa
    import pyarrow.parquet as pq

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({"User-Agent": UA})

    all_records = []
    for nivel, nivel_param in NIVEIS.items():
        print(f"Fetching {nivel} ({nivel_param})...")
        raw_rows = fetch_nivel(session, nivel_param)
        print(f"  {len(raw_rows)} rows")
        all_records.extend(to_records(raw_rows, nivel))

    print(f"\nTotal rows: {len(all_records)}")
    if not all_records:
        print("No rows fetched -- aborting, not pushing an empty file.")
        return 1

    # Sanity check: Brasil-level "Sem religiao" should be ~16.4M (published headline).
    brasil_sem_religiao = next(
        (r["populacao_10_mais"] for r in all_records if r["nivel"] == "brasil" and r["religiao"] == "Sem religião"),
        None,
    )
    print(f"Sanity check -- Brasil, Sem religiao, 2022: {brasil_sem_religiao:,}" if brasil_sem_religiao else "WARNING: Brasil/Sem religiao row not found")
    if brasil_sem_religiao is None or not (15_000_000 < brasil_sem_religiao < 18_000_000):
        print(f"WARNING: Brasil sem-religiao total {brasil_sem_religiao} outside expected ~16.4M range -- check before trusting this run")

    table = pa.Table.from_pylist(all_records)
    parquet_path = TEMP_DIR / "populacao_religiao.parquet"
    pq.write_table(table, str(parquet_path), compression="zstd")
    print(f"Wrote {parquet_path} ({parquet_path.stat().st_size / 1e6:.1f} MB, {table.num_rows} rows)")

    beelink_path = f"~/rodado/{DATASET}/{TABLE}"
    subprocess.run(f"ssh {BEELINK_HOST} 'mkdir -p {beelink_path}'", shell=True, check=True)
    result = subprocess.run(
        f"rsync -av {parquet_path} {BEELINK_HOST}:{beelink_path}/",
        shell=True,
    )
    if result.returncode != 0:
        print("rsync failed", file=sys.stderr)
        return 1

    print(f"Pushed to {BEELINK_HOST}:{beelink_path}/{parquet_path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
