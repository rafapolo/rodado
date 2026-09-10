#!/usr/bin/env python3
"""Rebuild the MCP server's schema from a fresh `schemas.json`.

`mcp_server.py` reads `docs/context/rodado-schema.json`, which drifts
away from beelink as new datasets land (it sat at 782 tables while the mirror
had 825, so `describe_table` answered "Unknown table" for anything recent).
Nothing regenerated it — `gera_schemas.py` writes the *other* artifact,
`schemas.json`, in a different shape. This bridges the two.

    python3 scripts/gera_schemas.py      # beelink  -> schemas.json
    python3 scripts/sync_mcp_schema.py   # schemas.json -> the MCP schema

Shapes:
    schemas.json   {"_meta": …, "tables": {"ds.tbl": {"path", "file_count",
                                                      "columns": [{name,type}]}}}
    MCP schema     {"ds": {"tbl": [{"name", "type"}]}}

Types are also translated: `schemas.json` carries a *physical* type — the
parquet physical type (INT64, BYTE_ARRAY) for disk-backed tables, or the
DuckDB logical type (VARCHAR, BIGINT) for `duckdb_native` tables that have no
parquet — the MCP schema wants one *logical* vocabulary (INTEGER, STRING)
regardless of which storage layer a table came from. The previous MCP schema
had been built with an incomplete mapping — 262 columns still held raw
physical names — so this normalizes every column.
"""

import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "schemas.json"
DST = REPO / "docs" / "context" / "rodado-schema.json"

# physical/native type -> logical type used by the MCP schema. Parquet
# physical types (INT64, BYTE_ARRAY, …) and DuckDB logical types (VARCHAR,
# BIGINT, …) share this one map since schemas.json now mixes both, depending
# on whether a table is disk-backed or duckdb_native.
TYPE_MAP = {
    "INT64": "INTEGER",
    "INT32": "INTEGER",
    "INT96": "INTEGER",
    "BYTE_ARRAY": "STRING",
    "FIXED_LEN_BYTE_ARRAY": "STRING",
    "DOUBLE": "FLOAT",
    "FLOAT": "FLOAT",
    "BOOLEAN": "BOOLEAN",
    # DuckDB DESCRIBE output (duckdb_native tables)
    "VARCHAR": "STRING",
    "BIGINT": "INTEGER",
    "UBIGINT": "INTEGER",
    "HUGEINT": "INTEGER",
    "SMALLINT": "INTEGER",
    "TINYINT": "INTEGER",
    "UINTEGER": "INTEGER",
    "REAL": "FLOAT",
    "DATE": "DATE",
    "TIMESTAMP": "TIMESTAMP",
}


def main() -> int:
    if not SRC.exists():
        print(f"{SRC} not found — run scripts/gera_schemas.py first.", file=sys.stderr)
        return 1

    src = json.loads(SRC.read_text(encoding="utf-8"))
    tables = src.get("tables")
    if not tables:
        print("schemas.json has no 'tables' key — aborting.", file=sys.stderr)
        return 1

    old_count = 0
    if DST.exists():
        old = json.loads(DST.read_text(encoding="utf-8"))
        old_count = sum(len(t) for t in old.values())

    out: dict[str, dict] = {}
    unmapped: Counter = Counter()
    skipped_empty: list[str] = []
    for tid, meta in tables.items():
        dataset, _, table = tid.partition(".")
        if not table:
            continue
        # A table whose schema could not be read is useless to every consumer:
        # describe_table returns nothing and search_tables still ranks it, so an
        # LLM gets steered into a dead end. br_mjsp_ckan.infopen used to be the
        # live case here — its parquet footer had raw latin-1 column names
        # (mojibake: "Situa\xe7\xe3o" instead of proper UTF-8 "Situação"), which
        # also poisoned any catalog-wide information_schema.columns/
        # duckdb_columns() query against the whole beelink database, not just
        # this table. Fixed 2026-09-10 by rewriting just the corrupted Thrift
        # fields in the footer (SchemaElement.name, ColumnMetaData
        # .path_in_schema) in place — data pages untouched, original backed up
        # as infopen.parquet.pre-utf8fix-20260910.bak. Some free-text VALUE
        # columns (Endereço, Outras Denominações — the ones read_parquet types
        # as BLOB rather than VARCHAR) still hold latin-1 bytes in the actual
        # cell content, unfixed: that needs decompressing/rewriting data pages,
        # out of scope for a metadata-only patch. br_mjsp_sisdepen remains the
        # documented replacement source; this table stays for provenance.
        # This code path (skip on empty columns) is now dead for infopen but
        # kept generically for whatever table hits it next.
        if not meta.get("columns"):
            skipped_empty.append(tid)
            continue
        cols = []
        for col in meta.get("columns", []):
            phys = col.get("type", "")
            # DECIMAL(18,2) etc — strip params, DuckDB's only parametrized type
            lookup = phys.split("(", 1)[0] if "(" in phys else phys
            logical = TYPE_MAP.get(lookup)
            if logical is None:
                unmapped[phys] += 1
                logical = phys
            cols.append({"name": col["name"], "type": logical})
        out.setdefault(dataset, {})[table] = cols

    n_tables = sum(len(t) for t in out.values())
    n_cols = sum(len(c) for t in out.values() for c in t.values())

    DST.write_text(
        json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    print(f"{DST.relative_to(REPO)}")
    print(f"  datasets : {len(out)}")
    print(f"  tables   : {n_tables}  (was {old_count})")
    print(f"  columns  : {n_cols}")
    print(f"  size     : {DST.stat().st_size / 1e6:.1f} MB")
    if skipped_empty:
        print(f"  skipped  : {len(skipped_empty)} table(s) with an unreadable schema "
              f"— {', '.join(skipped_empty)}")
    if unmapped:
        print(f"  WARNING unmapped physical types kept as-is: {dict(unmapped)}",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
