#!/usr/bin/env python3
"""Summarize mcp_server.py's per-call log (logs/mcp_calls.jsonl).

    python3 scripts/mcp_call_stats.py               # summary table
    python3 scripts/mcp_call_stats.py --outliers     # only tools past the flag threshold

Every `@mcp.tool()` in mcp_server.py is wrapped in `_instrumented`, which
appends one JSON line per call (tool, elapsed_ms, response_bytes) — no
attribution needed (stdio, one client per process), just enough to catch a
tool whose responses are quietly ballooning before it floods a live
session's context. See https://www.runpod.io/blog/designing-mcp-tools
(tips #7/#8) and mcp_server.py's CALL_LOG_PATH.

This script only reads the log; it never touches beelink.
"""
import argparse
import json
import os
import statistics
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CALL_LOG_PATH = Path(os.environ.get("MCP_CALL_LOG", REPO_ROOT / "logs" / "mcp_calls.jsonl"))

# Half of run_sql's own byte budget (RUN_SQL_MAX_CHARS=60000 in mcp_server.py):
# a tool regularly landing above this is worth a look even though nothing
# has broken yet — the same logic as run_sql's own truncation guard, just
# applied across calls instead of within one.
DEFAULT_OUTLIER_BYTES = 30_000


def load_calls(path: Path) -> list[dict]:
    if not path.exists():
        return []
    calls = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                calls.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # a partial last line from a killed process — skip, don't crash the report
    return calls


def summarize(calls: list[dict]) -> dict:
    by_tool = defaultdict(list)
    for c in calls:
        by_tool[c.get("tool", "?")].append(c)

    out = {}
    for tool, rows in by_tool.items():
        sizes = [r.get("response_bytes", 0) for r in rows if r.get("response_bytes", -1) >= 0]
        latencies = [r.get("elapsed_ms", 0) for r in rows]
        out[tool] = {
            "calls": len(rows),
            "bytes_avg": round(statistics.mean(sizes)) if sizes else 0,
            "bytes_max": max(sizes) if sizes else 0,
            "ms_avg": round(statistics.mean(latencies), 1) if latencies else 0,
            "ms_max": round(max(latencies), 1) if latencies else 0,
        }
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--outliers", action="store_true",
                     help="only show tools whose average or max response exceeds the threshold")
    ap.add_argument("--threshold", type=int, default=DEFAULT_OUTLIER_BYTES,
                     help=f"byte threshold for --outliers (default {DEFAULT_OUTLIER_BYTES})")
    args = ap.parse_args()

    calls = load_calls(CALL_LOG_PATH)
    if not calls:
        print(f"No calls logged yet at {CALL_LOG_PATH} — run some MCP tool calls first.")
        return

    stats = summarize(calls)
    rows = sorted(stats.items(), key=lambda kv: kv[1]["bytes_max"], reverse=True)
    if args.outliers:
        rows = [(t, s) for t, s in rows
                if s["bytes_avg"] > args.threshold or s["bytes_max"] > args.threshold]
        if not rows:
            print(f"No tool exceeds {args.threshold} bytes (avg or max) across {len(calls)} logged calls.")
            return

    print(f"{len(calls)} calls logged, {len(stats)} distinct tools "
          f"({CALL_LOG_PATH.relative_to(REPO_ROOT) if CALL_LOG_PATH.is_relative_to(REPO_ROOT) else CALL_LOG_PATH})\n")
    header = f"{'tool':<32} {'calls':>6} {'bytes avg':>10} {'bytes max':>10} {'ms avg':>8} {'ms max':>8}"
    print(header)
    print("-" * len(header))
    for tool, s in rows:
        flag = " ⚠" if s["bytes_max"] > args.threshold else ""
        print(f"{tool:<32} {s['calls']:>6} {s['bytes_avg']:>10} {s['bytes_max']:>10} "
              f"{s['ms_avg']:>8} {s['ms_max']:>8}{flag}")


if __name__ == "__main__":
    main()
