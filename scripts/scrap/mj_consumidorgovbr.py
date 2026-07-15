#!/usr/bin/env python3
"""
Fetch Consumidor.gov.br consumer-complaint records (dados.mj.gov.br CKAN,
dataset "reclamacoes-do-consumidor-gov-br") -> Parquet -> beelink.

Source: consumidor.gov.br's own "documentacao-api" page describes an
authenticated API for companies to manage their own complaints (needs a
Silver/Gold registered-company account + OAuth2 token) -- not useful for a
bulk public mirror. The real bulk-download path is the same
`dados.mj.gov.br` CKAN instance already used by mjsp_ckan.py/mjsp_sinesp.py:
package id 0182f1bf-e73d-42b1-ae8c-fa94d9ce9451, discovered via
`https://dados.mj.gov.br/api/3/action/package_show?id=reclamacoes-do-consumidor-gov-br`
(no auth). It publishes 87 CSV resources: annual files for 2014-2017,
semester files for 2018-2019, and one file per month from Jan/2020 onward.

All resources share the same 29-column schema (semicolon-delimited, UTF-8
with BOM, PT-BR headers e.g. "Gestor;Canal de Origem;Regiao;UF;..."). Fetched
with pandas as all-string dtype (dates/codes stay as their original PT-BR
text, matching the mjsp_ckan.py convention) to avoid cross-file dtype
mismatches, then concatenated into one table with an added `arquivo_origem`
column for provenance.

Usage:
    python3 scripts/scrap/mj_consumidorgovbr.py
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

BEELINK_HOST = "beelink"
BEELINK_PATH = "~/rodado/br_mj_consumidorgovbr/reclamacoes"
PACKAGE_API = "https://dados.mj.gov.br/api/3/action/package_show?id=reclamacoes-do-consumidor-gov-br"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
TEMP_DIR = Path(
    "/private/tmp/claude-501/-Users-polux-Projetos-rodado/50905fb8-827b-445f-bb28-3e8ed468da54/scratchpad/consumidor"
)


def fetch_bytes(url: str, timeout=120) -> bytes:
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def list_resources() -> list:
    data = json.loads(fetch_bytes(PACKAGE_API, timeout=30))
    resources = data["result"]["resources"]
    # keep only actual CSV data files (skip the PDF data dictionary etc)
    return [
        r
        for r in resources
        if (r.get("format") or "").upper() == "CSV" and r.get("url")
    ]


def push_frames(frames: list, label: str, existing_path: Path = None) -> bool:
    """Write accumulated per-file DataFrames to their own parquet, then merge
    with whatever's already on beelink (if any) via DuckDB SQL -- not pandas
    concat -- so memory use stays bounded to *this run's new rows* instead of
    growing with the full cumulative dataset on every single run/checkpoint.

    Checkpointing pattern borrowed from comprasgov_sicaf.py: push whatever's
    accumulated so far periodically, so a killed/interrupted run doesn't lose
    everything fetched to that point -- each rerun re-parses cached CSVs
    (fast, local disk) rather than re-downloading (slow, ~240KB/s source).
    """
    import duckdb
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq

    if not frames:
        print(f"No frames to push ({label}) -- skipping.", file=sys.stderr)
        return False

    new_full = pd.concat(frames, ignore_index=True, sort=False)
    new_path = TEMP_DIR / "new_data.parquet"
    pq.write_table(pa.Table.from_pandas(new_full, preserve_index=False), str(new_path), compression="zstd")

    parquet_path = TEMP_DIR / "reclamacoes.parquet"
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

    for attempt in range(20):
        mkdir_ok = subprocess.run(f"ssh {BEELINK_HOST} 'mkdir -p {BEELINK_PATH}'", shell=True).returncode == 0
        if mkdir_ok:
            break
        print(f"  ssh unreachable (attempt {attempt + 1}/20), retrying in 15s ...", file=sys.stderr)
        time.sleep(15)
    else:
        print(f"ssh beelink unreachable after retries -- aborting push ({label}).", file=sys.stderr)
        return False

    result = subprocess.run(
        f"rsync -av {parquet_path} {BEELINK_HOST}:{BEELINK_PATH}/",
        shell=True,
    )
    if result.returncode != 0:
        print(f"rsync failed ({label})", file=sys.stderr)
        return False

    print(f"[{label}] Pushed to {BEELINK_HOST}:{BEELINK_PATH}/{parquet_path.name}")
    # This push's output becomes the "existing" baseline for the next checkpoint
    # in this same run (and for any future rerun) -- copy it into place.
    if str(parquet_path) != str(existing_path):
        import shutil
        shutil.copy(parquet_path, TEMP_DIR / "existing.parquet")
    return True


def load_existing() -> set:
    """Pull whatever's already on beelink and return the set of arquivo_origem
    values already covered, via a cheap DuckDB query -- never materializes the
    full (multi-million-row) existing dataset into Python/pandas memory.
    """
    import duckdb

    local_path = TEMP_DIR / "existing.parquet"
    result = subprocess.run(
        f"rsync -a {BEELINK_HOST}:{BEELINK_PATH}/reclamacoes.parquet {local_path}",
        shell=True, capture_output=True,
    )
    if result.returncode != 0 or not local_path.exists():
        print("No existing beelink data found (or unreachable) -- starting fresh.")
        return set()

    con = duckdb.connect()
    row_count, = con.execute(f"SELECT count(*) FROM read_parquet('{local_path}')").fetchone()
    covered = {row[0] for row in con.execute(f"SELECT DISTINCT arquivo_origem FROM read_parquet('{local_path}')").fetchall()}
    con.close()
    print(f"Existing beelink data: {row_count} rows covering {len(covered)} files -- will skip those.")
    return covered


def main():
    import pandas as pd

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    raw_dir = TEMP_DIR / "raw"
    raw_dir.mkdir(exist_ok=True)

    already_covered = load_existing()
    existing_path = TEMP_DIR / "existing.parquet"
    if not existing_path.exists():
        existing_path = None

    print("Listing resources via CKAN package_show ...")
    all_resources = list_resources()
    resources = [r for r in all_resources if r.get("name", r["id"]) not in already_covered]
    print(f"  {len(all_resources)} CSV resources total, {len(resources)} not yet covered")

    CHECKPOINT_EVERY = 5  # push accumulated progress every N files

    frames = []
    last_pushed_count = 0
    for i, r in enumerate(resources, 1):
        name = r.get("name", r["id"])
        url = r["url"]
        print(f"[{i}/{len(resources)}] Fetching {name}: {url}")
        csv_path = raw_dir / f"{r['id']}.csv"
        if not csv_path.exists():
            try:
                raw = fetch_bytes(url, timeout=400)
            except Exception as e:
                print(f"  ✗ download failed ({e}), skipping")
                continue
            csv_path.write_bytes(raw)
        else:
            print("  (cached, skipping download)")

        # Newer (2020+) files are UTF-8 with BOM; older (2014-2019) files are
        # ISO-8859-1 -- try UTF-8 first, fall back to Latin-1.
        df = None
        for enc in ("utf-8-sig", "latin1"):
            try:
                df = pd.read_csv(
                    csv_path,
                    sep=";",
                    dtype=str,
                    encoding=enc,
                    on_bad_lines="skip",
                    low_memory=False,
                )
                break
            except Exception as e:
                last_err = e
        if df is None:
            print(f"  ✗ parse failed ({last_err}), skipping")
            continue

        df["arquivo_origem"] = name
        frames.append(df)
        print(f"  ✓ {len(df)} rows, {len(df.columns)} cols")

        if len(frames) - last_pushed_count >= CHECKPOINT_EVERY:
            label = f"checkpoint {i}/{len(resources)} files"
            if push_frames(frames, label, existing_path=existing_path):
                # This checkpoint's output is now the on-disk "existing" baseline;
                # drop the just-pushed frames from memory so the next checkpoint
                # only carries new rows, not the whole cumulative dataset.
                frames = []
                last_pushed_count = 0
                existing_path = TEMP_DIR / "existing.parquet"

    if not frames and existing_path is None:
        print("No data fetched -- aborting, nothing to push.")
        return 1
    if not frames:
        print("No new files this run -- already up to date, nothing further to push.")
        return 0

    print(f"\nFinal push: merging {len(frames)} new frames with existing baseline ...")
    ok = push_frames(frames, "final", existing_path=existing_path)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
