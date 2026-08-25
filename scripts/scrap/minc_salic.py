#!/usr/bin/env python3
"""
Export SALIC (Ministerio da Cultura -- Lei Rouanet cultural-incentive data) ->
Parquet -> beelink.

Source: not a live scrape by this script -- the actual fetch (legacy MySQL
dump import + live SALIC API sync, both with their own Cloudflare/pagination
gotchas) lives in a separate personal project, ../Mostre, whose consolidated
SQLite already merges:
  - the old dataset (2013-2016, imported from a MySQL dump snapshot)
  - the live SALIC API (api.salic.cultura.gov.br), covering PRONACs
    164380-266608 (~2024-2026) plus 15,449 rows with an unrelated 7-digit
    non-PRONAC edital code mixed into the same numero column (both dump-era
    "Premio Pontos de Valor" 2009 codes and some in the live range -- see
    Mostre's db/mostre.py docstrings for the full story)

This script just reads that already-consolidated storage/development.sqlite3
and pushes each table straight to Parquet+zstd on beelink -- no fetching, no
API calls, no auth.

Tables pushed: projetos, entidades, incentivos, recibos (the SALIC core) plus
areas/segmentos/estados/cidades (small dimension tables projetos/entidades
join against via area_id/segmento_id/estado_id/cidade_id -- included so this
is joinable standalone without also mirroring Mostre's full schema).

Known coverage gap: incentivos/recibos only cover the old 2013-2016 dump --
growing them to the new 2024-2026 projetos requires Mostre's separate,
much slower `sync por_projeto` (per-project captacoes endpoint, resumable,
Cloudflare-limited to ~5-10k projects/session). Not run as of this export.
Re-run this script after that lands to refresh incentivos/recibos.

Usage:
    python3 scripts/scrap/minc_salic.py
"""

import subprocess
import sqlite3
import sys
from pathlib import Path

import polars as pl

MOSTRE_DB = Path("/Users/polux/Projetos/Mostre/storage/development.sqlite3")
BEELINK_HOST = "beelink"
BEELINK_DATASET = "br_minc_salic"
TEMP_DIR = Path("/private/tmp/claude-501/-Users-polux-Projetos-rodado/minc_salic")

TABLES = [
    "projetos",
    "entidades",
    "incentivos",
    "recibos",
    "areas",
    "segmentos",
    "estados",
    "cidades",
]


def main():
    if not MOSTRE_DB.exists():
        print(f"Mostre db not found at {MOSTRE_DB} -- aborting.", file=sys.stderr)
        return 1

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(f"file:{MOSTRE_DB}?mode=ro", uri=True)

    pushed = []
    for table in TABLES:
        try:
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        except sqlite3.OperationalError:
            cols = []
        if not cols:
            print(f"  {table:<12} -- table missing, skipping")
            continue

        rows = conn.execute(f"SELECT * FROM {table}").fetchall()
        df = pl.DataFrame(rows, schema=cols, orient="row")

        out_dir = TEMP_DIR / table
        out_dir.mkdir(parents=True, exist_ok=True)
        parquet_path = out_dir / f"{table}.parquet"
        df.write_parquet(parquet_path, compression="zstd")
        size_mb = parquet_path.stat().st_size / 1e6
        print(f"  {table:<12} {df.height:>8} rows  {size_mb:6.1f} MB  -> {parquet_path}")
        pushed.append((table, df.height))

    conn.close()

    if not pushed:
        print("Nothing to push -- aborting.", file=sys.stderr)
        return 1

    beelink_path = f"~/rodado/{BEELINK_DATASET}"
    subprocess.run(f"ssh {BEELINK_HOST} 'mkdir -p {beelink_path}'", shell=True, check=True)
    for table, _ in pushed:
        result = subprocess.run(
            f"rsync -av {TEMP_DIR / table}/ {BEELINK_HOST}:{beelink_path}/{table}/",
            shell=True,
        )
        if result.returncode != 0:
            print(f"rsync failed for {table}", file=sys.stderr)
            return 1

    print(f"\nPushed {len(pushed)} tables to {BEELINK_HOST}:{beelink_path}/")
    for table, n in pushed:
        print(f"  {table}: {n} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
