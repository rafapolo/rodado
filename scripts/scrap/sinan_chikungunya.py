#!/usr/bin/env python3
"""
Fetch SINAN Chikungunya microdata from DataSUS's public FTP -> Parquet -> beelink.

IMPORTANT distinction: Brazil runs two separate chikungunya surveillance systems.
SIVEP-Chikungunya is the case registry for the Amazonia Legal region (where the
disease is endemic and case volume is high). SINAN's CHIK group is where
chikungunya cases occurring OUTSIDE Amazonia Legal are notified -- exactly the
relevant system for a non-endemic municipality like Nova Friburgo/RJ. This
script fetches the SINAN (non-endemic-area) series, not SIVEP-Chikungunya.

`br_ms_sinan` on Base dos Dados only mirrors dengue and influenza/SRAG --
chikungunya was never on Base dos Dados at all. Same pipeline shape as
scripts/scrap/sinan_violencia.py: straight from DataSUS's own FTP instead.

Source: DataSUS's legacy FTP server (plain `ftp://`, not https -- port 443
to this host times out, plain FTP on port 21 works). Group code confirmed by
listing the FTP directories directly (2026-09-01):
  - ftp://ftp.datasus.gov.br/dissemin/publicos/SINAN/DADOS/FINAIS/CHIKBR{YY}.dbc
    (consolidated, 2004-2022)
  - ftp://ftp.datasus.gov.br/dissemin/publicos/SINAN/DADOS/PRELIM/CHIKBR{YY}.dbc
    (preliminary, 2023-2024 -- no 2025/2026 file published yet as of 2026-09-01)

.dbc is DataSUS's own compressed DBF format -- decoded via `pyreaddbc`
(dbc2dbf) then read with `dbfread`. Every field cast to string (dates to
ISO) to avoid cross-year dtype mismatches, same convention as
sinan_violencia.py.

Usage:
    python3 scripts/scrap/sinan_chikungunya.py
"""

import subprocess
import sys
from pathlib import Path

BEELINK_HOST = "beelink"
BEELINK_PATH = "~/rodado/br_ms_sinan_chikungunya/microdados_chikungunya"
FTP_BASE = "ftp://ftp.datasus.gov.br/dissemin/publicos/SINAN/DADOS"
TEMP_DIR = Path(
    "/private/tmp/claude-501/-Users-polux-Projetos-rodado/0c20fa88-739d-4371-b790-94956f16aa3f/scratchpad/sinan_chikungunya"
)

# (year, 2-digit suffix, subdir) -- FINAIS for consolidated years, PRELIM for
# years not yet finalized. Confirmed via a live FTP directory listing on
# 2026-09-01: FINAIS covers 2004-2022, PRELIM covers 2023-2024 only.
YEARS = [(2000 + yy, f"{yy:02d}", "FINAIS") for yy in range(14, 26)] + [
    (2000 + yy, f"{yy:02d}", "PRELIM") for yy in range(26, 27)
]


def fetch_dbc(year: int, suffix: str, subdir: str) -> Path:
    url = f"{FTP_BASE}/{subdir}/CHIKBR{suffix}.dbc"
    dest = TEMP_DIR / f"CHIKBR{suffix}.dbc"
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  [{year}] (cached) {dest}")
        return dest
    print(f"  [{year}] Fetching {url}")
    result = subprocess.run(
        ["curl", "-s", "--max-time", "300", url, "-o", str(dest)],
        capture_output=True,
    )
    if result.returncode != 0 or not dest.exists() or dest.stat().st_size == 0:
        raise RuntimeError(f"download failed for {year}: {result.stderr.decode()[:300]}")
    return dest


def dbc_to_records(dbc_path: Path, year: int) -> list:
    import pyreaddbc
    from dbfread import DBF

    dbf_path = dbc_path.with_suffix(".dbf")
    pyreaddbc.dbc2dbf(str(dbc_path), str(dbf_path))

    table = DBF(str(dbf_path), encoding="latin1", load=False, ignore_missing_memofile=True)
    records = []
    for rec in table:
        row = {}
        for k, v in rec.items():
            if v is None:
                row[k] = None
            elif hasattr(v, "isoformat"):
                row[k] = v.isoformat()
            else:
                row[k] = str(v)
        row["ano_sinan"] = year
        records.append(row)
    dbf_path.unlink(missing_ok=True)
    return records


def push(new_records: list, label: str, existing_path: Path = None) -> bool:
    """Write new_records to their own parquet, then merge with whatever's
    already on beelink (if any) via DuckDB SQL -- never loads the full
    cumulative dataset into pandas/Python memory."""
    import duckdb
    import pyarrow as pa
    import pyarrow.parquet as pq

    if not new_records:
        print(f"No records to push ({label}) -- skipping.", file=sys.stderr)
        return False

    new_table = pa.Table.from_pylist(new_records)
    new_path = TEMP_DIR / "new_data.parquet"
    pq.write_table(new_table, str(new_path), compression="zstd")

    parquet_path = TEMP_DIR / "microdados_chikungunya.parquet"
    con = duckdb.connect()
    if existing_path is not None and existing_path.exists():
        con.execute(f"""
            COPY (
                SELECT * FROM read_parquet('{existing_path}')
                UNION ALL BY NAME
                SELECT * FROM read_parquet('{new_path}')
            ) TO '{parquet_path}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """)
    else:
        con.execute(f"COPY (SELECT * FROM read_parquet('{new_path}')) TO '{parquet_path}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    row_count = con.execute(f"SELECT count(*) FROM read_parquet('{parquet_path}')").fetchone()[0]
    con.close()
    print(f"[{label}] Wrote {parquet_path} ({parquet_path.stat().st_size / 1e6:.1f} MB, {row_count} rows)")

    subprocess.run(f"ssh {BEELINK_HOST} 'mkdir -p {BEELINK_PATH}'", shell=True, check=True)
    result = subprocess.run(
        f"rsync -av {parquet_path} {BEELINK_HOST}:{BEELINK_PATH}/",
        shell=True,
    )
    if result.returncode != 0:
        print(f"rsync failed ({label})", file=sys.stderr)
        return False

    print(f"[{label}] Pushed to {BEELINK_HOST}:{BEELINK_PATH}/{parquet_path.name}")
    if str(parquet_path) != str(existing_path):
        import shutil
        shutil.copy(parquet_path, TEMP_DIR / "existing_baseline.parquet")
    return True


def already_done_years() -> tuple:
    """Check beelink for a prior push: return (years_covered_set, local_baseline_path_or_None),
    via a cheap DuckDB query (not loading the full dataset into Python)."""
    import duckdb

    baseline_path = TEMP_DIR / "existing_baseline.parquet"
    result = subprocess.run(
        f"rsync -a {BEELINK_HOST}:{BEELINK_PATH}/microdados_chikungunya.parquet {baseline_path}",
        shell=True, capture_output=True,
    )
    if result.returncode != 0 or not baseline_path.exists():
        return set(), None
    con = duckdb.connect()
    years = {row[0] for row in con.execute(f"SELECT DISTINCT ano_sinan FROM read_parquet('{baseline_path}')").fetchall()}
    con.close()
    print(f"Existing beelink data covers years: {sorted(years)}")
    return years, baseline_path


def main():
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    done_years, existing_path = already_done_years()
    pending = [(y, s, d) for (y, s, d) in YEARS if y not in done_years]
    print(f"{len(YEARS)} years total, {len(pending)} not yet covered")

    all_records = []
    CHECKPOINT_EVERY = 1
    since_checkpoint = 0
    any_pushed = False
    for year, suffix, subdir in pending:
        try:
            dbc_path = fetch_dbc(year, suffix, subdir)
            records = dbc_to_records(dbc_path, year)
            print(f"  [{year}] {len(records)} rows")
            all_records.extend(records)
            since_checkpoint += 1
        except Exception as e:
            print(f"  [{year}] FAILED: {e}", file=sys.stderr)
            continue

        if since_checkpoint >= CHECKPOINT_EVERY:
            if push(all_records, f"checkpoint through {year}", existing_path=existing_path):
                all_records = []
                since_checkpoint = 0
                existing_path = TEMP_DIR / "existing_baseline.parquet"
                any_pushed = True

    if not any_pushed and not all_records and not done_years:
        print("No data fetched -- aborting.")
        return 1
    if not all_records and not any_pushed:
        print("No new years this run -- already up to date.")
        return 0
    if not all_records:
        print("All fetched years already pushed via checkpoint.")
        return 0

    print(f"\nFinal push: {len(all_records)} new rows this run")
    ok = push(all_records, "final", existing_path=existing_path)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
