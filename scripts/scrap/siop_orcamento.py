#!/usr/bin/env python3
"""
Fetch SIOP (Sistema Integrado de Planejamento e Orcamento) open-data CSV
exports -> Parquet -> beelink.

Source: `siop.planejamento.gov.br` (the doc's original guess) gives a
Cloudflare JS challenge, and `www1.siop.planejamento.gov.br`'s main app is a
live JSF/JSP interactive tool with no clean API -- BUT that same host also
runs a DokuWiki instance at `/siopdoc/` that hosts the actual open-data CSV
exports as plain wiki attachments, and THAT path has no Cloudflare/WAF in
front of it at all (plain Apache, 200 OK, real CSV content-type). Confirmed
via `www1.siop.planejamento.gov.br/siopdoc/doku.php/acesso_publico:dados_abertos`
(no challenge) and direct fetch.php downloads (200 OK, correct content-length).

Deliberately kept small/low-effort per the catalog's own priority note: this
budget-execution data likely already overlaps `br_me_siconfi` (16 tables,
already on beelink). Covers the latest-year snapshot of the 3 core "ação"
reference tables plus the current year's "alterações orçamentárias" log --
not the full multi-year history (each year is a separate CSV; extending the
YEAR constants below would backfill more years the same way).

CSV format: semicolon-delimited, ISO-8859-1 encoded, quoted fields with
embedded newlines.

Usage:
    python3 scripts/scrap/siop_orcamento.py
"""

import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen

BEELINK_HOST = "beelink"
DATASET_PATH = "~/rodado/br_siop_orcamento"
BEELINK_PATH = f"{DATASET_PATH}/dados"
BASE = "https://www1.siop.planejamento.gov.br/siopdoc/lib/exe/fetch.php"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
TEMP_DIR = Path(
    "/private/tmp/claude-501/-Users-polux-Projetos-rodado/c780c9c0-b6b3-44b0-964e-08a3b2f2024c/scratchpad/siop"
)

# table_name (beelink folder) -> media id (path after fetch.php/)
SOURCES = {
    "dados": "dados_abertos:dados_acao2025.csv",  # representative/primary table (BEELINK_PATH target)
    "localizadores": "dados_abertos:dados_localizador2025.csv",
    "planos_orcamentarios": "dados_abertos:dados_plano_orcamentario2025.csv",
    "alteracoes_orcamentarias": "dados_abertos:alteracoes:alteracoesorcamentarias_2026.csv",
}


def fetch(media_id: str, dest: Path):
    url = f"{BASE}/{media_id}"
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=120) as resp, open(dest, "wb") as f:
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)


def main():
    import pyarrow.csv as pv
    import pyarrow.parquet as pq

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    written = {}

    for table_name, media_id in SOURCES.items():
        print(f"Fetching {table_name}: {media_id}")
        csv_path = TEMP_DIR / f"{table_name}.csv"
        try:
            fetch(media_id, csv_path)
        except Exception as e:
            print(f"  ✗ {table_name}: download failed ({e})")
            continue
        print(f"  downloaded {csv_path.stat().st_size / 1e6:.1f} MB")

        try:
            table = pv.read_csv(
                csv_path,
                read_options=pv.ReadOptions(
                    block_size=1 << 24, encoding="ISO-8859-1"
                ),
                parse_options=pv.ParseOptions(
                    delimiter=";", newlines_in_values=True
                ),
            )
        except Exception as e:
            print(f"  ✗ {table_name}: failed to parse ({e})")
            continue

        parquet_path = TEMP_DIR / f"{table_name}.parquet"
        pq.write_table(table, str(parquet_path), compression="zstd")
        written[table_name] = (parquet_path, table.num_rows)
        print(f"  ✓ {table_name}: {table.num_rows} rows, {table.num_columns} cols -> {parquet_path.name}")

    if not written:
        print("No tables written -- aborting, nothing to push.")
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
