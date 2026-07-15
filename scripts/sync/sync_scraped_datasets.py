#!/usr/bin/env python3
"""
Sync missing (or stale) scraped-source datasets to beelink.

Companion to sync_missing_tables.py / sync_drifted_incremental.py, but for the
external-source pipelines under scripts/scrap/ (Portal da Transparencia-adjacent
sanctions lists, jurisprudencia APIs, Querido Diario, TCEs, etc — see
tasks/datasets_to_scrap.md's Status Board for the full catalog and per-source
status). Those BQ-focused scripts diff BigQuery's live table list against
beelink; this script instead diffs scripts/scrap/*.py against what's actually
on beelink, since there's no single upstream catalog to diff against here —
each pipeline is its own self-contained fetch script.

Convention every scripts/scrap/<pipeline>.py must follow for this to find it:
  - a module-level `BEELINK_PATH = "~/rodado/<org>_<dataset>/<tabela>"` constant
    (relative to the beelink home dir, same as the parquet destination the
    script itself rsyncs to).
  - running `python3 scripts/scrap/<pipeline>.py` with no args does a full,
    reasonable-default backfill (own retry/checkpoint/rsync logic included) —
    this driver does not re-implement fetch/convert/rsync itself, it just
    decides *which* pipeline scripts need to run and shells out to them.

Usage:
    python3 scripts/sync/sync_scraped_datasets.py               # backfill missing only
    python3 scripts/sync/sync_scraped_datasets.py --check-only   # report, don't run anything
    python3 scripts/sync/sync_scraped_datasets.py --refresh      # also re-run ones that already have data (periodicals: DOU, gazettes, sanctions lists, etc drift over time)
    python3 scripts/sync/sync_scraped_datasets.py --only querido_diario,tcu  # limit to specific pipelines
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRAP_DIR = REPO_ROOT / "scripts" / "scrap"
BEELINK_HOST = "beelink"
PROGRESS_FILE = Path.home() / ".scrap_sync_progress"

BEELINK_PATH_RE = re.compile(r'^BEELINK_PATH\s*=\s*["\']([^"\']+)["\']', re.MULTILINE)


def write_progress(status, pct, pipeline="", message=""):
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "pct": pct,
        "pipeline": pipeline,
        "message": message,
    }
    with open(PROGRESS_FILE, "w") as f:
        json.dump(data, f)
    print(f"[{pct:3d}%] {status:8s} {pipeline:30s} {message}")


def discover_pipelines():
    """Find every scripts/scrap/*.py that declares BEELINK_PATH."""
    pipelines = []
    if not SCRAP_DIR.exists():
        return pipelines
    for script in sorted(SCRAP_DIR.glob("*.py")):
        if script.name.startswith("_"):
            continue
        src = script.read_text()
        m = BEELINK_PATH_RE.search(src)
        if not m:
            print(f"  ⚠ {script.name}: no BEELINK_PATH constant, skipping (can't tell what it should sync)", file=sys.stderr)
            continue
        beelink_path = m.group(1)
        pipelines.append({"name": script.stem, "script": script, "beelink_path": beelink_path})
    return pipelines


def has_data_on_beelink(beelink_path: str) -> bool:
    """True if beelink_path exists and contains at least one *.parquet file."""
    cmd = (
        f"ssh {BEELINK_HOST} "
        f"\"find {beelink_path} -maxdepth 1 -name '*.parquet' 2>/dev/null | head -1\""
    )
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    return bool(result.stdout.strip())


def check_beelink_reachable() -> bool:
    result = subprocess.run(
        f"ssh {BEELINK_HOST} 'echo ok'", shell=True, capture_output=True, text=True, timeout=15
    )
    return result.returncode == 0 and "ok" in result.stdout


def run_pipeline(pipeline: dict) -> bool:
    """Shell out to the pipeline's own fetch→convert→rsync script."""
    print(f"  → running {pipeline['script'].relative_to(REPO_ROOT)} ...")
    result = subprocess.run(
        [sys.executable, str(pipeline["script"])],
        cwd=REPO_ROOT,
    )
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true", help="report missing/stale pipelines, don't run any")
    parser.add_argument("--refresh", action="store_true", help="also re-run pipelines that already have data on beelink (for periodicals)")
    parser.add_argument("--only", type=str, default=None, help="comma-separated pipeline names (script stem) to limit to")
    args = parser.parse_args()

    if not check_beelink_reachable():
        print("✗ beelink unreachable via SSH — aborting", file=sys.stderr)
        return 1

    write_progress("scan", 0, "", "Discovering scripts/scrap/*.py pipelines...")
    pipelines = discover_pipelines()
    if args.only:
        wanted = set(n.strip() for n in args.only.split(","))
        pipelines = [p for p in pipelines if p["name"] in wanted]
    print(f"✓ Found {len(pipelines)} pipeline(s) with a BEELINK_PATH\n")

    to_run = []
    up_to_date = []
    for idx, p in enumerate(pipelines):
        pct = int(100 * idx / len(pipelines)) if pipelines else 0
        write_progress("check", pct, p["name"], f"checking {p['beelink_path']}")
        present = has_data_on_beelink(p["beelink_path"])
        if present and not args.refresh:
            up_to_date.append(p)
        else:
            to_run.append(p)

    print(f"\n✓ Up to date: {len(up_to_date)}  |  {'Would run' if args.check_only else 'Will run'}: {len(to_run)}\n")
    for p in to_run:
        reason = "missing" if p not in up_to_date and not has_data_on_beelink(p["beelink_path"]) else "refresh"
        print(f"  - {p['name']} ({p['beelink_path']}) [{reason}]")

    if args.check_only or not to_run:
        write_progress("done", 100, "", f"{len(to_run)} pending, {len(up_to_date)} up to date (check-only)")
        return 0

    synced, failed = 0, []
    for idx, p in enumerate(to_run):
        pct = int(100 * idx / len(to_run))
        write_progress("run", pct, p["name"], "fetching + pushing to beelink")
        try:
            if run_pipeline(p):
                synced += 1
                write_progress("done", pct, p["name"], "ok")
            else:
                failed.append(p["name"])
                write_progress("failed", pct, p["name"], "non-zero exit")
        except Exception as e:
            failed.append(p["name"])
            print(f"  ✗ {p['name']}: {e}", file=sys.stderr)

    write_progress("complete", 100, "", f"synced {synced}/{len(to_run)}")
    print(f"\n✓ Synced {synced}/{len(to_run)} pipeline(s)")
    if failed:
        print(f"✗ Failed: {', '.join(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
