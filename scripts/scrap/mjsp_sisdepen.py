#!/usr/bin/env python3
"""
Fetch SISDEPEN (ex-INFOPEN) prison establishment survey data -> Parquet -> beelink.

Source: SENAPPEN (Secretaria Nacional de Politicas Penais, MJSP) semiannual
"base de dados" CSV exports -- one row per prison establishment per cycle,
public since 2014.

`br_mjsp_ckan.infopen` (mjsp_ckan.py, dez/2018 snapshot from the old
dados.mj.gov.br CKAN) is both corrupted (CSV read with the wrong encoding,
producing invalid-UTF8 bytes baked into the parquet -- DuckDB/pyarrow refuse
to read it) and orphaned (dados.mj.gov.br is now NXDOMAIN, confirmed
2026-07-26). This is an independent pipeline against the current source:
https://www.gov.br/senappen/pt-br/servicos/sisdepen/bases-de-dados

The CDN 403s any request without a Referer pointing at that index page --
plain bot-check, not a real WAF; setting Referer is enough.

22 cycle files: INFOPEN 2014/2015 (annual, legacy survey format), a 2016 H1
legacy-format file, and SISDEPEN ciclos 1-19 (semiannual, 2016 H2 - 2025 H2,
current survey format). Column headers differ across cycles/eras (survey
questions were added/reworded over a decade) -- 1300-1700+ columns per file.
Cast everything to string and merge with UNION ALL BY NAME, same convention
as sinan_violencia.py's arquivo_origem-tagged concat.

Usage:
    python3 scripts/scrap/mjsp_sisdepen.py
"""

import csv
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

BEELINK_HOST = "beelink"
BEELINK_PATH = "~/rodado/br_mjsp_sisdepen/populacao_carceraria"
INDEX_URL = "https://www.gov.br/senappen/pt-br/servicos/sisdepen/bases-de-dados"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
TEMP_DIR = Path(
    "/private/tmp/claude-501/-Users-polux-Projetos-rodado/8fec5d46-17e3-4bb7-9abd-793d0b6dcd39/scratchpad/sisdepen"
)

BASE = "https://www.gov.br/senappen/pt-br/servicos/sisdepen/bases-de-dados"
CYCLES = [
    ("infopen_2014", f"{BASE}/2014-e-2015/base-de-dados-infopen-2014.csv"),
    ("infopen_2015", f"{BASE}/2014-e-2015/base-de-dados-infopen-2015.csv"),
    ("2016_h1_legacy", f"{BASE}/2016/2016_basefinal_depen_publicacao_revisado_csv.csv"),
    ("ciclo_01_2016_h2", f"{BASE}/2016/1o-ciclo-base-de-dados-2016-2-semestre.csv"),
    ("ciclo_02_2017_h1", f"{BASE}/2017/2o-ciclo-base-de-dados-2017-1-semestre.csv"),
    ("ciclo_03_2017_h2", f"{BASE}/2017/3o-ciclo-base-de-dados-2017-2-semestre.csv"),
    ("ciclo_04_2018_h1", f"{BASE}/2018/4o-ciclo-base-de-dados-2018-1-semestre.csv"),
    ("ciclo_05_2018_h2", f"{BASE}/2018/5o-ciclo-base-de-dados-2018-2-semestre.csv"),
    ("ciclo_06_2019_h1", f"{BASE}/2019/6o-ciclo-base-de-dados-2019-1-semestre.csv"),
    ("ciclo_07_2019_h2", f"{BASE}/2019/7o-ciclo-base-de-dados-2019-2-semestre.csv"),
    ("ciclo_08_2020_h1", f"{BASE}/2020/8o-ciclo-base-de-dados-2020-1-semestre.csv"),
    ("ciclo_09_2020_h2", f"{BASE}/2020/9o-ciclo-base-de-dados-2020-2-semestre.csv"),
    ("ciclo_10_2021_h1", f"{BASE}/2021/10o-ciclo-base-de-dados-2021-1-semestre.csv"),
    ("ciclo_11_2021_h2", f"{BASE}/2021/11o-ciclo-base-de-dados-2021-2-semestre.csv"),
    ("ciclo_12_2022_h1", f"{BASE}/2022/12o-ciclo-base-de-dados-2022-1-semestre.csv"),
    ("ciclo_13_2022_h2", f"{BASE}/2022/13o-ciclo-base-de-dados-2022-2-semestre.csv"),
    ("ciclo_14_2023_h1", f"{BASE}/2023/14o-ciclo-base-de-dados-2023-1-semestre.csv"),
    ("ciclo_15_2023_h2", f"{BASE}/2023/15o-ciclo-base-de-dados-2023-2-semestre.csv"),
    ("ciclo_16_2024_h1", f"{BASE}/2024/16o-ciclo-base-de-dados-2024-1-semestre-retificado.csv"),
    ("ciclo_17_2024_h2", f"{BASE}/2024/17o-ciclo-base-de-dados-2024-2-semestre.csv"),
    ("ciclo_18_2025_h1", f"{BASE}/2025/18o-ciclo-base-de-dados-2025-1-semestre-retificado.csv"),
    ("ciclo_19_2025_h2", f"{BASE}/2025/19o-ciclo-base-de-dados-2025-2-semestre.csv"),
]


def clean_col(name: str, seen: dict) -> str:
    n = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    n = n.strip().lower()
    n = re.sub(r"[^a-z0-9]+", "_", n)
    n = re.sub(r"_+", "_", n).strip("_") or "col"
    n = n[:250]
    if n in seen:
        seen[n] += 1
        n = f"{n}_{seen[n]}"
    else:
        seen[n] = 0
    return n


def fetch_csv(url: str, dest: Path):
    import requests

    if dest.exists() and dest.stat().st_size > 0:
        print(f"  (cached) {dest}")
        return
    resp = requests.get(url, headers={"User-Agent": UA, "Referer": INDEX_URL}, timeout=180)
    resp.raise_for_status()
    dest.write_bytes(resp.content)


def csv_to_table(path: Path, cycle_label: str):
    import pyarrow as pa

    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        delimiter = ";" if sample.count(";") >= sample.count(",") else ","
        reader = csv.DictReader(f, delimiter=delimiter)
        seen: dict = {}
        col_map = {orig: clean_col(orig, seen) for orig in reader.fieldnames}
        cols = list(col_map.values()) + ["ciclo_arquivo"]
        data = {c: [] for c in cols}
        n = 0
        for row in reader:
            for orig, cleaned in col_map.items():
                v = row.get(orig)
                data[cleaned].append(v if v not in (None, "") else None)
            data["ciclo_arquivo"].append(cycle_label)
            n += 1

    if n == 0:
        return None
    schema = pa.schema([(c, pa.string()) for c in cols])
    return pa.table(data, schema=schema)


def push(table, label: str, existing_path: Path):
    import duckdb
    import pyarrow.parquet as pq

    if table is None or table.num_rows == 0:
        print(f"No rows for {label} -- skipping.", file=sys.stderr)
        return False

    new_path = TEMP_DIR / "new_data.parquet"
    pq.write_table(table, str(new_path), compression="zstd")

    merged_path = TEMP_DIR / "populacao_carceraria.parquet"
    con = duckdb.connect()
    if existing_path is not None and existing_path.exists():
        con.execute(f"""
            COPY (
                SELECT * FROM read_parquet('{existing_path}')
                UNION ALL BY NAME
                SELECT * FROM read_parquet('{new_path}')
            ) TO '{merged_path}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """)
    else:
        con.execute(
            f"COPY (SELECT * FROM read_parquet('{new_path}')) TO '{merged_path}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )
    row_count = con.execute(f"SELECT count(*) FROM read_parquet('{merged_path}')").fetchone()[0]
    col_count = len(con.execute(f"SELECT * FROM read_parquet('{merged_path}') LIMIT 0").description)
    con.close()
    print(f"[{label}] Wrote {merged_path} ({merged_path.stat().st_size / 1e6:.1f} MB, {row_count} rows, {col_count} cols)")

    subprocess.run(f"ssh {BEELINK_HOST} 'mkdir -p {BEELINK_PATH}'", shell=True, check=True)
    result = subprocess.run(f"rsync -av {merged_path} {BEELINK_HOST}:{BEELINK_PATH}/", shell=True)
    if result.returncode != 0:
        print(f"rsync failed ({label})", file=sys.stderr)
        return False
    print(f"[{label}] Pushed to {BEELINK_HOST}:{BEELINK_PATH}/{merged_path.name}")

    import shutil

    shutil.copy(merged_path, TEMP_DIR / "existing_baseline.parquet")
    return True


def already_done_cycles() -> tuple:
    import duckdb

    baseline_path = TEMP_DIR / "existing_baseline.parquet"
    result = subprocess.run(
        f"rsync -a {BEELINK_HOST}:{BEELINK_PATH}/populacao_carceraria.parquet {baseline_path}",
        shell=True, capture_output=True,
    )
    if result.returncode != 0 or not baseline_path.exists():
        return set(), None
    con = duckdb.connect()
    cycles = {row[0] for row in con.execute(f"SELECT DISTINCT ciclo_arquivo FROM read_parquet('{baseline_path}')").fetchall()}
    con.close()
    print(f"Existing beelink data covers cycles: {sorted(cycles)}")
    return cycles, baseline_path


def main():
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    done_cycles, existing_path = already_done_cycles()
    pending = [(label, url) for (label, url) in CYCLES if label not in done_cycles]
    print(f"{len(CYCLES)} cycles total, {len(pending)} not yet covered")

    any_pushed = False
    for label, url in pending:
        dest = TEMP_DIR / f"{label}.csv"
        try:
            print(f"[{label}] Fetching {url}")
            fetch_csv(url, dest)
            table = csv_to_table(dest, label)
            if table is None:
                print(f"  [{label}] 0 rows, skipping", file=sys.stderr)
                continue
            print(f"  [{label}] {table.num_rows} rows, {table.num_columns} cols")
        except Exception as e:
            print(f"  [{label}] FAILED: {e}", file=sys.stderr)
            continue

        if push(table, label, existing_path):
            existing_path = TEMP_DIR / "existing_baseline.parquet"
            any_pushed = True

    if not any_pushed and not done_cycles:
        print("No data fetched -- aborting.")
        return 1
    if not any_pushed:
        print("No new cycles this run -- already up to date.")
        return 0

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
