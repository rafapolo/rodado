#!/usr/bin/env python3
"""
Fetch Querido Diário gazette metadata → Parquet → push to beelink.

Querido Diário (okfn-brasil/querido-diario, CC BY 4.0) is a search index of
municipal official gazette PDFs scraped from ~3,300 Brazilian city halls.
Its public API lives at https://api.queridodiario.ok.org.br (OpenAPI spec at
/openapi.json — the human-facing /api/docs page on queridodiario.ok.org.br is
just the SPA shell, not the API itself).

API notes discovered by probing (2026-07-10):
  - GET /gazettes returns {"total_gazettes": N, "gazettes": [...]}, one row
    per scraped gazette edition (metadata only — city, date, PDF/TXT URLs,
    edition number — NOT the full document text; "excerpts" are only
    populated when a `querystring` search term is supplied, which we don't
    use here since we want the full index, not a text search).
  - It sits on OpenSearch and enforces the classic max_result_window: any
    query with offset+size > 10000 hits HTTP 500. Unfiltered (no date range)
    requests return total_gazettes=0 — a date range is required to get
    results at all.
  - Real historical data goes back to at least 1990 (scraped opportunistically
    from city archives), and recent weeks run ~1,500-2,200 gazettes/week
    across the whole country. A full historical crawl from 1990 to today
    would need day-level sub-pagination in places and thousands of requests.
    That's out of scope for this pass. Per the task's own guidance ("if the
    total is clearly enormous, fetch a representative recent slice and
    document it"), this script mirrors the last N years (default 3) of the
    metadata index, paginated week-by-week.
  - The upstream API is occasionally flaky under sustained polling (observed:
    a 502 followed by several 404s on the exact same query, which then
    succeeded again moments later on retest). Treat all non-2xx as transient
    and retry with backoff; a bucket that still fails after retries is
    skipped (not fatal) and logged so the gap is visible in the run summary.
  - Full gazette text (the .txt_url per row) is NOT downloaded here — at
    hundreds of thousands of documents that's a separate, much larger job.
    This pass mirrors the metadata/index table only, matching the plan's
    "diarios" table = index of editions, not document bodies.

Resilience: rows are checkpointed to a local JSONL file as each weekly bucket
completes, so a crash or Ctrl-C loses at most one bucket's worth of work, not
the whole run. Re-running the script from scratch re-fetches everything (no
incremental resume logic — the run is fast enough in practice that this
wasn't worth the complexity), but the checkpoint file means a mid-run crash
can still be salvaged manually if needed.

Usage:
    python3 scripts/scrap/querido_diario.py [--years N]
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import requests

API_BASE = "https://api.queridodiario.ok.org.br"
BEELINK_HOST = "beelink"
BEELINK_PATH = "~/rodado/br_ok_queridodiario/diarios"
TEMP_DIR = Path("/private/tmp/claude-501/-Users-polux-Projetos-rodado/50905fb8-827b-445f-bb28-3e8ed468da54/scratchpad/querido_diario")
CHECKPOINT_FILE = TEMP_DIR / "checkpoint.jsonl"

MAX_WINDOW = 10000  # OpenSearch max_result_window enforced by the API
REQUEST_DELAY = 0.3  # be polite between requests


def fetch_window(published_since: str, published_until: str, size: int = MAX_WINDOW, offset: int = 0):
    """Fetch one page from /gazettes. Returns (total_gazettes, gazettes list) or (None, None) on failure."""
    params = {
        "published_since": published_since,
        "published_until": published_until,
        "size": size,
        "offset": offset,
        "sort_by": "ascending_date",
    }
    last_err = None
    for attempt in range(8):
        try:
            resp = requests.get(f"{API_BASE}/gazettes", params=params, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            time.sleep(REQUEST_DELAY)
            return data["total_gazettes"], data["gazettes"]
        except Exception as e:
            last_err = e
            wait = min(2 ** attempt, 60)
            print(f"    retry {attempt+1}/8 after error: {e} (sleeping {wait}s)", file=sys.stderr)
            time.sleep(wait)
    print(f"    giving up on {published_since}..{published_until}: {last_err}", file=sys.stderr)
    return None, None


def fetch_bucket(since: date, until: date):
    """
    Fetch all gazettes in [since, until] (inclusive), recursing into smaller
    sub-ranges if the bucket hits the 10k window cap. Returns (rows, failed_ranges).
    """
    since_s, until_s = since.isoformat(), until.isoformat()
    total, rows = fetch_window(since_s, until_s, size=MAX_WINDOW, offset=0)

    if total is None:
        return [], [(since_s, until_s)]

    if total < MAX_WINDOW or since == until:
        return rows, []

    # Bucket is too big (hit the cap) — split in half and recurse.
    span_days = (until - since).days
    mid = since + timedelta(days=span_days // 2)
    print(f"    bucket {since_s}..{until_s} hit cap ({total}), splitting at {mid}", file=sys.stderr)
    left_rows, left_failed = fetch_bucket(since, mid)
    if mid < until:
        right_rows, right_failed = fetch_bucket(mid + timedelta(days=1), until)
    else:
        right_rows, right_failed = [], []
    return left_rows + right_rows, left_failed + right_failed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", type=int, default=3, help="how many years back from today to mirror")
    args = parser.parse_args()

    today = date.today()
    start = date(today.year - args.years, today.month, today.day)

    print(f"Fetching Querido Diário gazette metadata index: {start} .. {today}")

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    checkpoint_f = open(CHECKPOINT_FILE, "w")

    total_rows = 0
    all_failed = []
    cursor = start
    week = timedelta(days=7)
    week_count = 0

    while cursor <= today:
        bucket_end = min(cursor + week - timedelta(days=1), today)
        rows, failed = fetch_bucket(cursor, bucket_end)
        for r in rows:
            checkpoint_f.write(json.dumps(r) + "\n")
        checkpoint_f.flush()
        total_rows += len(rows)
        all_failed.extend(failed)
        week_count += 1
        if week_count % 20 == 0:
            print(f"  ... {cursor} ({total_rows} rows so far, {len(all_failed)} failed buckets)")
        cursor = bucket_end + timedelta(days=1)

    checkpoint_f.close()
    print(f"Total gazette records fetched: {total_rows}")
    if all_failed:
        print(f"WARNING: {len(all_failed)} date ranges failed after retries and were skipped:")
        for f in all_failed:
            print(f"  - {f[0]}..{f[1]}")

    if total_rows == 0:
        print("No rows fetched — aborting, not writing/pushing an empty file.")
        return 1

    # Reload from checkpoint and dedup (bucket splitting can produce overlaps
    # at boundaries).
    seen = set()
    deduped = []
    with open(CHECKPOINT_FILE) as f:
        for line in f:
            r = json.loads(line)
            key = (r.get("territory_id"), r.get("date"), r.get("url"))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(r)
    print(f"After dedup: {len(deduped)} rows")

    import pyarrow as pa
    import pyarrow.parquet as pq

    columns = [
        "territory_id", "territory_name", "state_code", "date", "edition",
        "is_extra_edition", "url", "txt_url", "scraped_at",
    ]
    table = pa.Table.from_pylist(
        [{c: r.get(c) for c in columns} for r in deduped]
    )

    parquet_file = TEMP_DIR / f"diarios_{start.isoformat()}_{today.isoformat()}.parquet"
    pq.write_table(table, str(parquet_file), compression="zstd")
    print(f"Wrote {parquet_file} ({parquet_file.stat().st_size / 1e6:.1f} MB)")

    subprocess.run(f"ssh {BEELINK_HOST} 'mkdir -p {BEELINK_PATH}'", shell=True, check=True)
    result = subprocess.run(
        f"rsync -av {parquet_file} {BEELINK_HOST}:{BEELINK_PATH}/",
        shell=True,
    )
    if result.returncode != 0:
        print("rsync failed", file=sys.stderr)
        return 1

    print(f"Pushed to {BEELINK_HOST}:{BEELINK_PATH}/{parquet_file.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
