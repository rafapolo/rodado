#!/usr/bin/env python3
"""Build a queryable metadata catalog parquet (`_rodado_metadata/catalog.parquet`)
for all tables on beelink, merging:
  - Table/dataset listing from parquet directories
  - Row counts, file sizes and mtimes from DuckDB parquet_metadata
  - Provenance info (source URL, status, notes) from tasks/datasets_to_scrap.md
  - Base dos Dados attribution for everything that is *not* independently
    scraped — the mirrored portion of the project, whose schema snapshot lives
    in docs/context/schema_ddl.sql

Rows carry a `source` column:
  - `disk`          parquet on beelink; rows measured with parquet_metadata
  - `duckdb_native` no parquet, but the view reads a native table inside
                    basedosdados.duckdb and has rows; counted via DuckDB
  - `view_only`     no parquet and no rows — genuinely orphaned

Counting tables or rows means filtering `source <> 'view_only'`, not
`source = 'disk'`: the latter drops ~93,8M real rows of br_ms_sipni.
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
# Constants
# ---------------------------------------------------------------------------

# Schemas that exist only as DuckDB views and carry no project data: BigQuery
# leftovers, GCP audit logs, and the catalog's own views. Keeping them would
# make the table/dataset counts lie.
JUNK_SCHEMAS = {
    "main",              # _rodado_metadata / _rodado_datasets — self-reference
    "logs",              # cloudaudit_googleapis_com_* — GCP audit leftovers
    "test_dataset",      # upstream Base dos Dados test fixture
    "dataset_new_arch",  # upstream Base dos Dados test fixture
    "information_schema",
    "pg_catalog",
}

# Everything not listed in datasets_to_scrap.md is mirrored from Base dos Dados.
BD_SOURCE_NAME = "Base dos Dados"
BD_SOURCE_TYPE = "mirror"
# Per-dataset BD slugs are not derivable from the dataset id (the site resolves
# them client-side, so a guessed /dataset/<slug> URL cannot be verified). The
# search URL always resolves and lands on the right dataset.
BD_SEARCH_URL = "https://basedosdados.org/search?q={dataset}"

# datasets_to_scrap.md holds several tables that all start with "Source" but
# carry different columns, so match the layout, not the keyword. Only these two
# name real beelink datasets; the `Source | Pipeline | Node Types | Auth | ...`
# ones list mcp-todo pipelines that have no data on disk.
#   value = (dataset column, format, status, date, notes) — None where absent
SCRAP_LAYOUTS = {
    ("Source", "Beelink path", "Format", "Status", "Last updated", "Notes"):
        {"dataset": 2, "source_type": 3, "status": 4, "date": 5, "notes": 6},
    ("Source", "Pipeline", "CDN slug", "Period", "Rows", "Files", "Notes"):
        {"dataset": 2, "source_type": None, "status": None, "date": None, "notes": 7},
}

URL_RE = re.compile(r"https?://[^\s)`|,;]+")
# Most notes name the endpoint as a bare backticked host rather than a full URL
# (`dadosabertos.compras.gov.br`); accept those as a fallback.
HOST_RE = re.compile(
    r"`([a-z0-9][a-z0-9.-]*\.(?:gov\.br|jus\.br|leg\.br|tc\.br|org\.br|com\.br"
    r"|mil\.br|org|com|net|io|eu|br))`"
)


# ---------------------------------------------------------------------------
# Parse docs/context/schema_ddl.sql — the Base dos Dados schema snapshot
# ---------------------------------------------------------------------------

def parse_ddl_tables(path: Path) -> set[tuple[str, str]]:
    """Return {(dataset, table)} declared in the Base dos Dados DDL snapshot.

    Used only to mark which mirrored tables have a confirmed upstream schema —
    the snapshot is partial, so absence from it does not mean a table is not
    from Base dos Dados."""
    if not path.exists():
        return set()
    out = set()
    for m in re.finditer(r"^CREATE TABLE ([a-z0-9_]+)\.([a-z0-9_]+)", path.read_text(), re.M):
        out.add((m.group(1), m.group(2)))
    return out


# ---------------------------------------------------------------------------
# Parse datasets_to_scrap.md into a lookup dict
# ---------------------------------------------------------------------------

def split_row(line: str) -> list[str]:
    """Split a markdown table row on | while respecting `backticked` cells."""
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
    return cells


def parse_markdown_table(path: Path) -> dict[str, dict]:
    scraped = {}
    cols = None

    with open(path) as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line:
            # Some tables are visually split by a blank line — that is still
            # the same table, so do not drop the layout here.
            continue
        if not line.startswith("|"):
            cols = None
            continue
        if line.startswith("|---"):
            continue

        cells = split_row(line)
        # cells[0] is the empty string before the leading pipe
        header = tuple(c for c in cells[1:] if c)
        if header in SCRAP_LAYOUTS:
            cols = SCRAP_LAYOUTS[header]
            continue
        if header[:1] == ("Source",) or header[:1] == ("Dataset",):
            cols = None  # a table layout we do not read
            continue
        if cols is None or len(cells) <= cols["notes"]:
            continue

        beelink_path = cells[cols["dataset"]].strip("` ")
        # `~/...` marks a mirror kept outside ~/rodado, deliberately uncatalogued
        if not beelink_path or beelink_path.startswith("~") or beelink_path == "—":
            continue

        def cell(key, default=""):
            i = cols[key]
            return cells[i].strip() if i is not None and i < len(cells) else default

        notes = cell("notes")
        # datasets_to_scrap.md has no URL column — take the first URL mentioned
        # anywhere in the row, falling back to the first backticked hostname.
        urls = URL_RE.findall(line)
        if urls:
            source_url = urls[0].rstrip(".")
        else:
            host = HOST_RE.search(line)
            source_url = f"https://{host.group(1)}" if host else ""
        info = {
            "source_name": cells[1].strip(),
            "source_url": source_url,
            "source_type": (cell("source_type") or "scraped").split()[0],
            "status": cell("status") or "done",
            "notes": notes[:500],
        }
        dates = re.findall(r"\d{4}-\d{2}-\d{2}", cell("date"))
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
    AND from DuckDB views that don't have local parquet (e.g. stale views
    left over from before the local-parquet migration, or DuckDB-internal
    schemas like main, _local_rais_cnpj, politicos)."""

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
    # data do parquet mais recente: e a unica "quando foi espelhado" que
    # existe para as tabelas do Base dos Dados, que nao tem scrape_date.
    mt=$(find "$tbdir" -name '*.parquet' -printf '%TY-%Tm-%Td\n' 2>/dev/null | sort -r | head -1)
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
      echo "${result},${mt}"
    else
      echo "disk,${dsdir},${tbl},0,0,0,${mt}"
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
                if key[0] in JUNK_SCHEMAS:
                    continue
                if key not in tables:
                    tables[key] = {
                        "dataset": parts[1].strip(),
                        "table": parts[2].strip(),
                        "num_files": int(parts[3]),
                        "rows": int(parts[4]),
                        "size_bytes": int(parts[5]),
                        "mtime": parts[6].strip() if len(parts) > 6 else "",
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
            if ds in JUNK_SCHEMAS:
                continue
            if key not in tables:
                # View with no parquet behind it — the data it pointed at (a
                # dead bucket, a local import) is gone. Kept so the breakage
                # stays visible.
                tables[key] = {
                    "dataset": ds,
                    "table": tbl,
                    "num_files": 0,
                    "rows": 0,
                    "size_bytes": 0,
                    "mtime": "",
                    "source": "view_only",
                }


    # Phase 2b: a view with no parquet is not automatically broken.
    #
    # It used to be recorded as rows=0 / view_orfa on the assumption that its
    # data was gone. That is wrong for the `br_ms_sipni_*` and `politicos`
    # views, which read native tables stored *inside* basedosdados.duckdb —
    # `doses_agregadas` alone holds 93.785.056 rows. Counting via
    # parquet_metadata reports 0 because there is no parquet, not because there
    # is no data. So ask DuckDB instead of assuming.
    no_parquet = [k for k, v in tables.items() if v["source"] == "view_only"]
    if no_parquet:
        counts = _count_via_duckdb(no_parquet)
        for key in no_parquet:
            n = counts.get(key)
            if n is None:
                tables[key]["probe"] = "failed"
            elif n > 0:
                tables[key]["source"] = "duckdb_native"
                tables[key]["rows"] = n
            else:
                tables[key]["probe"] = "empty"

    return list(tables.values())


def _count_via_duckdb(keys):
    """Row counts for tables DuckDB can reach but parquet_metadata cannot.

    Returns {(dataset, table): rows}; a key is absent when its count failed, so
    the caller can tell "no data" from "could not ask" instead of writing a
    confident zero over both.
    """
    if not keys:
        return {}
    union = "\nUNION ALL ".join(
        f"SELECT '{ds}' AS d, '{tbl}' AS t, count(*) AS n FROM \"{ds}\".\"{tbl}\""
        for ds, tbl in keys
    )
    tmp = tempfile.NamedTemporaryFile(mode="wb", suffix=".sql", delete=False)
    tmp.write(b"SET enable_progress_bar=false;\n")
    tmp.write((union + ";\n").encode("utf-8"))
    tmp.close()
    remote = f"/tmp/rodado_cat3_{os.getpid()}.sql"
    out = {}
    try:
        subprocess.run(["scp", tmp.name, f"{BEELINK_HOST}:{remote}"],
                       capture_output=True, timeout=15, check=True)
        proc = subprocess.run(
            ["ssh", BEELINK_HOST,
             f"~/bin/duckdb -readonly ~/rodado/basedosdados.duckdb -csv < {remote}; rm -f {remote}"],
            capture_output=True, timeout=600,
        )
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as exc:
        print(f"  ! row-count probe failed: {exc}", file=sys.stderr)
        return out
    finally:
        os.unlink(tmp.name)
    if proc.returncode != 0:
        print(f"  ! row-count probe failed: {proc.stderr.decode()[:200]}", file=sys.stderr)
        return out
    for line in proc.stdout.decode().split("\n"):
        parts = line.strip().split(",")
        if len(parts) == 3 and parts[2].isdigit():
            out[(parts[0], parts[1])] = int(parts[2])
    return out


# ---------------------------------------------------------------------------
# Merge and write
# ---------------------------------------------------------------------------

def build_catalog():
    # Resolved rows (done/mcp-live/excluded) live in the done/ split file, not
    # the active one (see its 2026-08-24 split header) — merge both, or every
    # dataset moved there falls through to the `info is None` branch below and
    # gets silently misattributed as a Base dos Dados mirror. Caught live
    # 2026-08-25: br_ok_queridodiario (Querido Diário, a project scrape long
    # since marked `done`) was showing source_name='Base dos Dados' in
    # _rodado_metadata for exactly this reason. Active file wins on a key
    # collision (shouldn't happen — a dataset lives in one file at a time).
    scraped_info = parse_markdown_table(REPO_ROOT / "tasks" / "done" / "datasets_to_scrap_done.md")
    scraped_info.update(parse_markdown_table(REPO_ROOT / "tasks" / "datasets_to_scrap.md"))
    ddl_tables = parse_ddl_tables(REPO_ROOT / "docs" / "context" / "schema_ddl.sql")
    beelink_tables = get_tables_from_beelink()

    if not beelink_tables:
        print("ERROR: no tables from beelink", file=sys.stderr)
        sys.exit(1)

    print(f"Got {len(beelink_tables)} tables from beelink", file=sys.stderr)
    print(f"  {len(scraped_info)} scraped datasets in datasets_to_scrap.md + done/datasets_to_scrap_done.md", file=sys.stderr)
    print(f"  {len(ddl_tables)} tables in the Base dos Dados DDL snapshot", file=sys.stderr)
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
        ("source", pa.string()),
        ("updated_at", pa.string()),
    ])

    arrays = {f.name: [] for f in schema}
    n_bd = 0
    for t in beelink_tables:
        ds = t["dataset"]
        info = scraped_info.get(ds)

        if info is None:
            # Not independently scraped => mirrored from Base dos Dados.
            # schema_ddl.sql is a partial snapshot of that mirror, so it can
            # confirm a table but never rule one out.
            n_bd += 1
            confirmed = (ds, t["table"]) in ddl_tables
            info = {
                "source_name": BD_SOURCE_NAME,
                "source_url": BD_SEARCH_URL.format(dataset=ds),
                "source_type": BD_SOURCE_TYPE,
                "status": "mirrored",
                "scrape_date": t.get("mtime", ""),
                "notes": (
                    "Espelho do Base dos Dados; schema confirmado em "
                    "docs/context/schema_ddl.sql."
                    if confirmed else
                    "Espelho do Base dos Dados; fora do recorte de "
                    "docs/context/schema_ddl.sql."
                ),
            }

        status = info.get("status", "mirrored")
        notes = info.get("notes", "")
        if t["source"] == "view_only":
            # Asked DuckDB and it really is empty (or unreachable) — never
            # report it as mirrored data.
            status = "view_orfa"
            notes = ("View DuckDB sem parquet local e sem linhas. " + notes).strip()
        elif t["source"] == "duckdb_native":
            # Real data, just not stored as parquet: the view reads a native
            # table inside basedosdados.duckdb. Counted via DuckDB, not
            # parquet_metadata.
            notes = ("Tabela nativa dentro de basedosdados.duckdb, sem parquet "
                     "em ~/rodado. Consulte pela view, nao por read_parquet. " + notes).strip()

        arrays["dataset"].append(ds)
        arrays["table"].append(t["table"])
        arrays["source_name"].append(info.get("source_name", ""))
        arrays["source_url"].append(info.get("source_url", ""))
        arrays["source_type"].append(info.get("source_type", ""))
        arrays["rows"].append(t["rows"])
        arrays["num_files"].append(t["num_files"])
        arrays["size_bytes"].append(t["size_bytes"])
        arrays["scrape_date"].append(info.get("scrape_date", "") or t.get("mtime", ""))
        arrays["status"].append(status)
        arrays["provenance_notes"].append(notes[:500])
        arrays["source"].append(t["source"])
        arrays["updated_at"].append(today)

    print(f"  {n_bd} tables attributed to {BD_SOURCE_NAME}", file=sys.stderr)

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

    write_all_tables(beelink_tables)
    refresh_views()


def write_all_tables(beelink_tables):
    """Emite docs/context/all_tables.txt — a lista chapada de `dataset.tabela`.

    Era um despejo do `bq ls` da era BigQuery (535 linhas, com
    `logs.cloudaudit_*` e `test_dataset.test_table` dentro) que nenhum script
    lia e ninguem regenerava. Sai daqui porque o catalogo e a unica fonte que
    enxerga as duas metades: o parquet em disco e as tabelas nativas dentro do
    `.duckdb`, que nao tem parquet nenhum e por isso o `gera_schemas.py` nao
    ve."""
    names = sorted(
        f"{t['dataset']}.{t['table']}"
        for t in beelink_tables
        if t["source"] != "view_only"
    )
    out = REPO_ROOT / "docs" / "context" / "all_tables.txt"
    out.write_text("\n".join(names) + "\n", encoding="utf-8")
    print(f"Wrote {len(names)} tables to {out}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Views over the catalog, kept here so they follow the parquet schema
# ---------------------------------------------------------------------------

VIEWS_SQL = """
CREATE OR REPLACE VIEW _rodado_metadata AS
SELECT * FROM read_parquet('~/rodado/_rodado_metadata/catalog.parquet');

CREATE OR REPLACE VIEW _rodado_datasets AS
SELECT
  dataset,
  any_value(source_name)          AS source_name,
  any_value(source_url)           AS source_url,
  any_value(source_type)          AS source_type,
  count(*)                        AS total_tables,
  sum("rows")                     AS total_rows,
  sum(num_files)                  AS total_files,
  sum(size_bytes)                 AS total_size_bytes,
  max(scrape_date)                AS scrape_date,
  string_agg(DISTINCT status, ', ' ORDER BY status) AS status,
  count(*) FILTER (WHERE source = 'view_only') AS orphan_views
FROM read_parquet('~/rodado/_rodado_metadata/catalog.parquet')
GROUP BY dataset;
"""


def refresh_views():
    """Recreate _rodado_metadata / _rodado_datasets on beelink.

    _rodado_datasets groups by dataset alone — grouping by the descriptive
    columns too used to split a dataset into several rows whenever its tables
    disagreed on scrape_date or status."""
    proc = subprocess.run(
        ["ssh", BEELINK_HOST, "~/bin/duckdb ~/rodado/basedosdados.duckdb"],
        input=("SET enable_progress_bar=false;\n" + VIEWS_SQL).encode(),
        capture_output=True, timeout=120,
    )
    if proc.returncode != 0:
        print(f"WARN: could not refresh views: {proc.stderr.decode()[:300]}", file=sys.stderr)
        return
    print("Refreshed views: _rodado_metadata, _rodado_datasets", file=sys.stderr)


if __name__ == "__main__":
    build_catalog()
