#!/usr/bin/env python3
"""
Fetch STJ (Superior Tribunal de Justica) open-data documentos -> Parquet -> beelink.

Source: STJ's official CKAN open-data portal, dataset
"integras-de-decisoes-terminativas-e-acordaos-do-diario-da-justica"
(https://dadosabertos.web.stj.jus.br/dataset/integras-de-decisoes-terminativas-e-acordaos-do-diario-da-justica).
Discovered via `package_show` on the CKAN API root (the doc's originally guessed
"www.stj.jus.br/sites/STP/sjson/" URL was stale/wrong -- clean 404, not a WAF block).

The dataset publishes one JSON metadata file + one ZIP (full decision texts) per
publication day since 2021-01-04, updated daily. This script pulls only the JSON
metadata resources (format=="JSON", name starting with "metadados") -- one row per
decision/acordao published that day (dataPublicacao, tipoDocumento, processo,
relator, etc). The ZIP full-text bundles are NOT downloaded (would be a much
heavier binary-blob pipeline; metadata is what's structured/queryable and matches
this repo's "documentos" table shape).

Auth: none. IMPORTANT: the CKAN API (api/3/action/*) works with a plain UA, but
the actual resource *download* URLs
(dadosabertos.web.stj.jus.br/dataset/<id>/resource/<rid>/download/<file>) are
behind an F5/BigIP WAF that rejects requests with no Referer header ("Request
Rejected" / "#BDEFK8#" support-ID page) -- adding a Referer pointing back at the
dataset page fixes it. No API key needed either way.

Usage:
    python3 scripts/scrap/stj_dados_abertos.py
"""

import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import Request, urlopen
import json

# NOTE: on this host, Python's urllib (and even a global socket.setdefaulttimeout)
# has been observed to hang/stall indefinitely after roughly 250-300 sequential
# HTTPS requests to this same host, even though a fresh `curl` to the exact same
# URL from the same shell succeeds instantly -- i.e. it's specific to
# long-lived Python-process connection/DNS state, not the remote server or the
# network path itself (never reproduced via curl). Shelling out to `curl` per
# request (own process each time, no shared state to leak) reliably avoids it.

BEELINK_HOST = "beelink"
BEELINK_PATH = "~/rodado/br_stj_dadosabertos/documentos"

CKAN_BASE = "https://dadosabertos.web.stj.jus.br"
DATASET_ID = "integras-de-decisoes-terminativas-e-acordaos-do-diario-da-justica"
REFERER = f"{CKAN_BASE}/dataset/{DATASET_ID}"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
TEMP_DIR = Path(
    "/private/tmp/claude-501/-Users-polux-Projetos-rodado/c780c9c0-b6b3-44b0-964e-08a3b2f2024c/scratchpad/stj"
)
WORKERS = 2


def fetch_json(url: str, headers: dict, timeout: int = 45):
    req = Request(url, headers=headers)
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def list_metadata_resources():
    """package_show -> list of (name, url) for JSON metadata resources only."""
    url = f"{CKAN_BASE}/api/3/action/package_show?id={DATASET_ID}"
    headers = {"User-Agent": UA, "Accept": "application/json"}
    data = None
    for attempt in range(5):
        try:
            data = fetch_json(url, headers=headers, timeout=45)
            break
        except Exception as e:
            wait = 5 * (attempt + 1)
            print(f"  package_show attempt {attempt + 1} failed ({e}), retrying in {wait}s ...")
            time.sleep(wait)
    if data is None:
        raise RuntimeError("package_show failed after retries -- WAF likely rate-limiting")
    resources = data["result"]["resources"]
    return [
        (r["name"], r["url"])
        for r in resources
        if r.get("format", "").upper() == "JSON"
    ]


def fetch_day(name_url):
    name, url = name_url
    cmd = [
        "curl", "-s", "--max-time", "30",
        "-A", UA,
        "-H", "Accept: application/json,text/plain,*/*",
        "-H", "Accept-Language: pt-BR,pt;q=0.9,en;q=0.8",
        "-H", f"Referer: {REFERER}",
        url,
    ]
    for attempt in range(4):
        try:
            proc = subprocess.run(cmd, capture_output=True, timeout=40)
            rows = json.loads(proc.stdout)
            if isinstance(rows, list):
                return rows
            return []
        except Exception as e:
            if attempt == 3:
                print(f"  {name}: giving up ({e})")
                return []
            time.sleep(2 * (attempt + 1))
    return []


PROGRESS_FILE_NAME = "progress.json"
CHECKPOINT_FILE_NAME = "documentos.checkpoint.parquet"


def load_progress():
    """Resume support: this host has been observed to kill long-running
    background processes unpredictably (not a script bug -- confirmed the
    process just vanishes mid-run, no exception, no OOM signature we could
    catch). Rather than fight that, the script is resumable: every run reloads
    already-fetched days from a small progress.json + the checkpoint parquet,
    and only fetches what's still missing. Re-running the same command
    repeatedly converges on the full dataset."""
    progress_path = TEMP_DIR / PROGRESS_FILE_NAME
    checkpoint_path = TEMP_DIR / CHECKPOINT_FILE_NAME
    if not progress_path.exists() or not checkpoint_path.exists():
        return set(), []
    import pyarrow.parquet as pq

    done_names = set(json.loads(progress_path.read_text()))
    rows = pq.read_table(str(checkpoint_path)).to_pylist()
    print(f"Resuming: {len(done_names)} days already fetched ({len(rows)} rows) from a previous run.")
    return done_names, rows


def save_checkpoint(all_rows, done_names):
    import pyarrow as pa
    import pyarrow.parquet as pq

    ckpt_table = pa.Table.from_pylist(all_rows)
    pq.write_table(ckpt_table, str(TEMP_DIR / CHECKPOINT_FILE_NAME), compression="zstd")
    (TEMP_DIR / PROGRESS_FILE_NAME).write_text(json.dumps(sorted(done_names)))


def main():
    import pyarrow as pa
    import pyarrow.parquet as pq

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    print("Listing metadata resources via CKAN package_show ...")
    resources = list_metadata_resources()
    print(f"Found {len(resources)} daily JSON metadata files.")
    if not resources:
        print("No resources found -- aborting.")
        return 1

    done_names, all_rows = load_progress()
    remaining = [(n, u) for n, u in resources if n not in done_names]
    print(f"{len(remaining)}/{len(resources)} days still to fetch.")

    print(f"Fetching {len(remaining)} days with {WORKERS} workers ...")
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = {ex.submit(fetch_day, nu): nu for nu in remaining}
        done_count = 0
        for fut in as_completed(futures):
            name, _ = futures[fut]
            rows = fut.result()
            all_rows.extend(rows)
            done_names.add(name)
            done_count += 1
            if done_count % 20 == 0:
                print(f"  ... {done_count}/{len(remaining)} days fetched, {len(all_rows)} rows so far", flush=True)
            if done_count % 20 == 0:
                save_checkpoint(all_rows, done_names)
                print(f"  [checkpoint] {len(all_rows)} rows / {len(done_names)} days saved to disk", flush=True)

    # Final checkpoint save regardless of whether we reached a full multiple of 100
    save_checkpoint(all_rows, done_names)

    print(f"\nTotal unique days fetched so far: {len(done_names)}/{len(resources)}")
    print(f"Total rows fetched: {len(all_rows)}")
    if len(done_names) < len(resources):
        print(
            f"NOTE: {len(resources) - len(done_names)} days still missing -- "
            f"re-run this script again to continue from the checkpoint."
        )
    if not all_rows:
        print("No rows fetched -- aborting, not pushing an empty file.")
        return 1

    table = pa.Table.from_pylist(all_rows)
    parquet_path = TEMP_DIR / "documentos.parquet"
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
