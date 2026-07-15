#!/usr/bin/env python3
"""
Fetch EU Financial Sanctions Files (FSF) consolidated list -> Parquet -> beelink.

Source: European Commission FSF public CSV export, discovered via the EU Open
Data Portal's dataset API for "consolidated-list-of-persons-groups-and-
entities-subject-to-eu-financial-sanctions"
(https://data.europa.eu/api/hub/search/datasets/consolidated-list-of-persons-groups-and-entities-subject-to-eu-financial-sanctions),
whose distributions list a working direct CSV download_url:

    https://webgate.ec.europa.eu/fsd/fsf/public/files/csvFullSanctionsList_1_1/content?token=dG9rZW4tMjAxNw

The `token` query param is a static, publicly-published token (base64 of the
literal string "token-2017", not a session/rotating credential) baked into
the EU's own open-data catalog metadata — no auth flow needed. This
supersedes the previously-guessed `xmlFullSanctionsList` path (which 403s;
that one apparently does need a session/token flow the CSV export doesn't).

Note on overlap: OpenSanctions' consolidated feed (already on beelink at
global_opensanctions/entities, 1.3M rows) already includes eu_fsf as one of
its ~40 source datasets (~15k entities per opensanctions.org/datasets/eu_fsf).
This pipeline still pulls the EU's own primary-source flat file directly,
since the fetch is cheap and it preserves the EU's original reference
numbers/regulation citations that a consolidated cross-source export may not
retain 1:1.

The CSV is a single wide, denormalized flat file (one row per name/alias +
one row per address/etc. combination sharing the same Entity_LogicalId) with
118 columns, semicolon-delimited, UTF-8 with BOM. Loaded as-is (all string
columns) — no reshaping needed, pyarrow can read the flat structure directly.

Usage:
    python3 scripts/scrap/eu_sanctions.py
"""

import csv
import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen

BEELINK_HOST = "beelink"
BEELINK_PATH = "~/rodado/eu_sanctions/sanctions"
CSV_URL = (
    "https://webgate.ec.europa.eu/fsd/fsf/public/files/csvFullSanctionsList_1_1/"
    "content?token=dG9rZW4tMjAxNw"
)
TEMP_DIR = Path(
    "/private/tmp/claude-501/-Users-polux-Projetos-rodado/"
    "c780c9c0-b6b3-44b0-964e-08a3b2f2024c/scratchpad/eu_sanctions"
)
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)


def fetch_csv() -> bytes:
    req = Request(CSV_URL, headers={"User-Agent": UA})
    with urlopen(req, timeout=120) as resp:
        return resp.read()


def main():
    import pyarrow as pa
    import pyarrow.parquet as pq

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Fetching {CSV_URL} ...")
    raw = fetch_csv()
    print(f"  downloaded {len(raw) / 1e6:.1f} MB")

    csv_path = TEMP_DIR / "eu_fsf_raw.csv"
    csv_path.write_bytes(raw)

    text = raw.decode("utf-8-sig")
    reader = csv.reader(text.splitlines(), delimiter=";")
    header = next(reader)
    # normalize column names (avoid duplicate/empty)
    cols = [h.strip() if h.strip() else f"col_{i}" for i, h in enumerate(header)]

    rows = []
    for rec in reader:
        if not rec or all(v == "" for v in rec):
            continue
        # pad/truncate to header length defensively
        if len(rec) < len(cols):
            rec = rec + [""] * (len(cols) - len(rec))
        elif len(rec) > len(cols):
            rec = rec[: len(cols)]
        rows.append({c: (v if v != "" else None) for c, v in zip(cols, rec)})

    print(f"Total rows parsed: {len(rows)}")
    if not rows:
        print("No rows parsed — aborting, not pushing an empty file.")
        return 1

    table = pa.Table.from_pylist(rows)
    parquet_path = TEMP_DIR / "sanctions.parquet"
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

    print(f"Pushed to {BEELINK_HOST}:{BEELINK_PATH}/{parquet_path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
