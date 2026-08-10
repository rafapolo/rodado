#!/usr/bin/env python3
"""Build a queryable metadata catalog parquet (`_rodado_metadata/catalog.parquet`)
for all tables on beelink, merging:
  - Table/dataset listing from parquet directories
  - Row counts and file sizes from DuckDB parquet_metadata
  - Provenance info (source URL, status, notes) from tasks/datasets_to_scrap.md
"""

import csv
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BEELINK_HOST = os.environ.get("BEELINK_HOST", "beelink")

# ---------------------------------------------------------------------------
# Parse datasets_to_scrap.md into a lookup dict
# ---------------------------------------------------------------------------

def parse_markdown_table(path: Path) -> dict[str, dict]:
    scraped = {}
    with open(path) as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line.startswith("|") or line.startswith("|---") or "Source" in line:
            continue

        cells = []
        current = ""
        in_backtick = False
        for ch in line:
            if ch == "`":
                in_backtick = not in_backtick
                current += ch
            elif ch == "|" and not in_backtick:
                cells.append(current.strip())
                current = ""
            else:
                current += ch
        if current.strip():
            cells.append(current.strip())

        if len(cells) < 7:
            continue

        beelink_path = cells[2].strip("` ") if len(cells) > 2 else ""
        if not beelink_path or beelink_path == "Beelink path":
            continue

        info = {
            "source_name": cells[1].strip(),
            "source_url": "",
            "source_type": cells[3].strip().split()[0] if len(cells) > 3 else "",
            "status": cells[4].strip() if len(cells) > 4 else "",
            "notes": cells[6].strip()[:500] if len(cells) > 6 else "",
        }
        lu = cells[5].strip() if len(cells) > 5 else ""
        dates = re.findall(r"\d{4}-\d{2}-\d{2}", lu)
        if dates:
            info["scrape_date"] = dates[-1]

        # Store by dataset name (first path segment)
        ds = beelink_path.split("/")[0]
        scraped[ds] = info

    return scraped


# ---------------------------------------------------------------------------
# Deploy and run scan script on beelink
# ---------------------------------------------------------------------------

def get_tables_from_beelink() -> list[dict]:
    """Get all tables from beelink — both from parquet directories on disk
    AND from DuckDB views that don't have local parquet (e.g. S3-backed,
    or DuckDB-internal schemas like main, _local_rais_cnpj, politicos)."""

    # Phase 1: parquet directories on disk (with row counts from parquet_metadata)
    shell_script = """#!/bin/bash
cd ~/rodado
for dsdir in br_* global_* world_* mundo_* eu_* un_* us_*; do
  [ -d "$dsdir" ] || continue
  for tbdir in "$dsdir"/*/; do
    [ -d "$tbdir" ] || continue
    tbl=$(basename "$tbdir")
    # ** e nao * : tabelas particionadas (ex. br_ana_telemetria/series_vazao_diaria,
    # em bacia=XX/) ficavam com rows=0 e num_files=0 no catalogo. O ** tambem casa
    # arquivo direto no diretorio, entao as tabelas planas seguem contando igual.
    result=$(~/bin/duckdb -csv -c "SET enable_progress_bar=false;
WITH pm AS (
  SELECT file_name, row_group_id, row_group_num_rows, total_compressed_size
  FROM parquet_metadata('${tbdir}**/*.parquet')
),
row_groups AS (
  SELECT DISTINCT file_name, row_group_id, row_group_num_rows FROM pm
)
SELECT 'disk' AS src, '${dsdir}' AS d, '${tbl}' AS t,
  (SELECT count(DISTINCT file_name) FROM pm) AS nf,
  coalesce((SELECT sum(row_group_num_rows) FROM row_groups), 0) AS r,
  coalesce((SELECT sum(total_compressed_size) FROM pm), 0) AS b;" 2>/dev/null)
    if [ $? -eq 0 ]; then
      echo "$result"
    else
      echo "disk,${dsdir},${tbl},0,0,0"
    fi
  done
done
"""
    local_script = os.path.join(tempfile.mkdtemp(), "scan_tables.sh")
    with open(local_script, "w") as f:
        f.write(shell_script)
    os.chmod(local_script, 0o755)
    remote_script = f"/tmp/rodado_scan_{os.getpid()}.sh"
    try:
        subprocess.run(
            ["scp", local_script, f"{BEELINK_HOST}:{remote_script}"],
            capture_output=True, timeout=15, check=True,
        )
        proc = subprocess.run(
            ["ssh", BEELINK_HOST, f"bash {remote_script}"],
            capture_output=True, timeout=600,
        )
        subprocess.run(["ssh", BEELINK_HOST, f"rm {remote_script}"], capture_output=True, timeout=10)
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
        print(f"Deploy/run error: {e}", file=sys.stderr)
        return []
    finally:
        shutil.rmtree(os.path.dirname(local_script), ignore_errors=True)

    tables = {}
    if proc.returncode == 0:
        for line in proc.stdout.decode().split("\n"):
            line = line.strip()
            if not line or not "," in line or line.startswith("src,d"):
                continue
            parts = line.split(",")
            if len(parts) < 6:
                continue
            try:
                key = (parts[1].strip(), parts[2].strip())
                if key not in tables:
                    tables[key] = {
                        "dataset": parts[1].strip(),
                        "table": parts[2].strip(),
                        "num_files": int(parts[3]),
                        "rows": int(parts[4]),
                        "size_bytes": int(parts[5]),
                        "source": "disk",
                    }
            except (ValueError, IndexError):
                pass

    # Phase 2: DuckDB schemas/views that don't have disk dirs
    sql = """
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
  AND table_type = 'VIEW'
ORDER BY table_schema, table_name;
"""
    tmp = tempfile.NamedTemporaryFile(mode="wb", suffix=".sql", delete=False)
    tmp.write(b"SET enable_progress_bar=false;\n")
    tmp.write(sql.encode("utf-8"))
    tmp.close()
    remote_tmp = f"/tmp/rodado_cat2_{os.getpid()}.sql"
    try:
        subprocess.run(["scp", tmp.name, f"{BEELINK_HOST}:{remote_tmp}"],
                       capture_output=True, timeout=15, check=True)
        proc2 = subprocess.run(
            ["ssh", BEELINK_HOST, f"~/bin/duckdb ~/rodado/basedosdados.duckdb -csv < {remote_tmp} && rm {remote_tmp}"],
            capture_output=True, timeout=30,
        )
    except subprocess.TimeoutExpired:
        print("DuckDB schema query timed out", file=sys.stderr)
        proc2 = None
    finally:
        os.unlink(tmp.name)

    if proc2 and proc2.returncode == 0:
        for line in proc2.stdout.decode().split("\n"):
            line = line.strip()
            if not line or not "," in line or line.startswith("table_schema"):
                continue
            parts = line.split(",", 1)
            if len(parts) < 2:
                continue
            ds = parts[0].strip()
            tbl = parts[1].strip()
            key = (ds, tbl)
            if key not in tables:
                # Try to estimate row count from parquet if available
                tables[key] = {
                    "dataset": ds,
                    "table": tbl,
                    "num_files": 0,
                    "rows": 0,
                    "size_bytes": 0,
                    "source": "view_only",
                }

    return list(tables.values())


# ---------------------------------------------------------------------------
# Merge and write
# ---------------------------------------------------------------------------

def build_catalog():
    scraped_info = parse_markdown_table(REPO_ROOT / "tasks" / "datasets_to_scrap.md")
    beelink_tables = get_tables_from_beelink()

    if not beelink_tables:
        print("ERROR: no tables from beelink", file=sys.stderr)
        sys.exit(1)

    print(f"Got {len(beelink_tables)} tables from beelink", file=sys.stderr)
    total_rows = sum(t["rows"] for t in beelink_tables)
    print(f"Total rows: {total_rows:,}", file=sys.stderr)

    today = date.today().isoformat()

    import pyarrow as pa
    import pyarrow.parquet as pq

    schema = pa.schema([
        ("dataset", pa.string()),
        ("table", pa.string()),
        ("source_name", pa.string()),
        ("source_url", pa.string()),
        ("source_type", pa.string()),
        ("rows", pa.int64()),
        ("num_files", pa.int64()),
        ("size_bytes", pa.int64()),
        ("scrape_date", pa.string()),
        ("status", pa.string()),
        ("provenance_notes", pa.string()),
        ("updated_at", pa.string()),
    ])

    arrays = {f.name: [] for f in schema}
    for t in beelink_tables:
        ds = t["dataset"]
        info = scraped_info.get(ds, {})
        arrays["dataset"].append(ds)
        arrays["table"].append(t["table"])
        arrays["source_name"].append(info.get("source_name", ""))
        arrays["source_url"].append(info.get("source_url", ""))
        arrays["source_type"].append(info.get("source_type", ""))
        arrays["rows"].append(t["rows"])
        arrays["num_files"].append(t["num_files"])
        arrays["size_bytes"].append(t["size_bytes"])
        arrays["scrape_date"].append(info.get("scrape_date", ""))
        arrays["status"].append(info.get("status", "mirrored"))
        arrays["provenance_notes"].append(info.get("notes", ""))
        arrays["updated_at"].append(today)

    pa_table = pa.table(arrays, schema=schema)

    outdir = REPO_ROOT / "_rodado_metadata"
    outdir.mkdir(exist_ok=True)
    outpath = outdir / "catalog.parquet"
    pq.write_table(pa_table, outpath)
    print(f"Wrote {len(beelink_tables)} rows to {outpath} ({outpath.stat().st_size / 1024:.0f} KB)", file=sys.stderr)

    # Rsync to beelink
    subprocess.run(
        ["ssh", BEELINK_HOST, "mkdir -p ~/rodado/_rodado_metadata"],
        capture_output=True, timeout=10,
    )
    subprocess.run(
        ["rsync", "-avz", str(outpath), f"{BEELINK_HOST}:~/rodado/_rodado_metadata/catalog.parquet"],
        capture_output=True, timeout=120, check=True,
    )
    print(f"Pushed to beelink: ~/rodado/_rodado_metadata/catalog.parquet", file=sys.stderr)


if __name__ == "__main__":
    build_catalog()
