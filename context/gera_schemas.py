import os
import json
import sys
import pyarrow.parquet as pq
import s3fs
import boto3
import duckdb
from dotenv import load_dotenv

load_dotenv()

S3_ENDPOINT  = os.environ["HETZNER_S3_ENDPOINT"]
S3_BUCKET    = os.environ["HETZNER_S3_BUCKET"]
ACCESS_KEY   = os.environ["AWS_ACCESS_KEY_ID"]
SECRET_KEY   = os.environ["AWS_SECRET_ACCESS_KEY"]

s3_host = S3_ENDPOINT.removeprefix("https://").removeprefix("http://")

# --- boto3 client (listing only, zero egress) ---
boto = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
)

# --- s3fs filesystem (footer-only reads via pyarrow) ---
fs = s3fs.S3FileSystem(
    client_kwargs={"endpoint_url": S3_ENDPOINT},
    key=ACCESS_KEY,
    secret=SECRET_KEY,
)

# ------------------------------------------------------------------ #
# Phase 1: File inventory via S3 List API (zero data egress)
# ------------------------------------------------------------------ #
print("Phase 1: listing S3 objects...")
paginator = boto.get_paginator("list_objects_v2")

inventory = {}  # "dataset/table" -> {files: [...], total_size: int}

for page in paginator.paginate(Bucket=S3_BUCKET):
    for obj in page.get("Contents", []):
        key = obj["Key"]
        if not key.endswith(".parquet"):
            continue
        parts = key.split("/")
        if len(parts) < 3:
            continue
        dataset, table = parts[0], parts[1]
        dt = f"{dataset}/{table}"
        if dt not in inventory:
            inventory[dt] = {"files": [], "total_size_bytes": 0}
        inventory[dt]["files"].append(key)
        inventory[dt]["total_size_bytes"] += obj["Size"]

print(f"  Found {len(inventory)} tables across {S3_BUCKET}")

# ------------------------------------------------------------------ #
# Phase 2: Schema reads — footer only (~30 KB per table)
# ------------------------------------------------------------------ #
print("Phase 2: reading parquet footers...")

def fmt_size(b):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if b < 1024 or unit == "TB":
            return f"{b:.1f} {unit}"
        b /= 1024

def extract_col_descriptions(schema):
    """Try to pull per-column descriptions from Arrow metadata."""
    descriptions = {}
    meta = schema.metadata or {}
    # BigQuery exports embed a JSON blob under b'pandas' with column_info
    pandas_meta_raw = meta.get(b"pandas") or meta.get(b"pandas_metadata")
    if pandas_meta_raw:
        try:
            pm = json.loads(pandas_meta_raw)
            for col in pm.get("columns", []):
                name = col.get("name")
                desc = col.get("metadata", {}) or {}
                if isinstance(desc, dict) and "description" in desc:
                    descriptions[name] = desc["description"]
        except Exception:
            pass
    # Also try top-level b'description' or b'schema'
    for key in (b"description", b"schema", b"BigQuery:description"):
        val = meta.get(key)
        if val:
            try:
                descriptions["__table__"] = val.decode("utf-8", errors="replace")
            except Exception:
                pass
    return descriptions

schemas = {}
errors = []

for i, (dt, info) in enumerate(sorted(inventory.items())):
    dataset, table = dt.split("/", 1)
    first_file = info["files"][0]
    s3_path = f"{S3_BUCKET}/{first_file}"
    try:
        schema = pq.read_schema(fs.open(s3_path))
        col_descs = extract_col_descriptions(schema)

        # Build raw metadata dict (decode bytes keys/values)
        raw_meta = {}
        if schema.metadata:
            for k, v in schema.metadata.items():
                try:
                    dk = k.decode("utf-8", errors="replace")
                    dv = v.decode("utf-8", errors="replace")
                    # Try to parse JSON values
                    try:
                        dv = json.loads(dv)
                    except Exception:
                        pass
                    raw_meta[dk] = dv
                except Exception:
                    pass

        columns = []
        for field in schema:
            col = {
                "name": field.name,
                "type": str(field.type),
                "nullable": field.nullable,
            }
            if field.name in col_descs:
                col["description"] = col_descs[field.name]
            # Check field-level metadata
            if field.metadata:
                for k, v in field.metadata.items():
                    try:
                        dk = k.decode("utf-8", errors="replace")
                        dv = v.decode("utf-8", errors="replace")
                        if dk in ("description", "DESCRIPTION", "comment"):
                            col["description"] = dv
                    except Exception:
                        pass
            columns.append(col)

        schemas[f"{dataset}.{table}"] = {
            "path": f"s3://{S3_BUCKET}/{dataset}/{table}/",
            "file_count": len(info["files"]),
            "total_size_bytes": info["total_size_bytes"],
            "total_size_human": fmt_size(info["total_size_bytes"]),
            "columns": columns,
            "metadata": raw_meta,
        }
        print(f"  [{i+1}/{len(inventory)}] ✓ {dataset}.{table} ({len(columns)} cols, {fmt_size(info['total_size_bytes'])})")
    except Exception as e:
        errors.append({"table": f"{dataset}.{table}", "error": str(e)})
        print(f"  [{i+1}/{len(inventory)}] ✗ {dataset}.{table}: {e}", file=sys.stderr)

# ------------------------------------------------------------------ #
# Phase 3: Enrich from br_bd_metadados.bigquery_tables (small table)
# ------------------------------------------------------------------ #
META_TABLE = "br_bd_metadados.bigquery_tables"
meta_dt = "br_bd_metadados/bigquery_tables"

if meta_dt in inventory:
    print(f"Phase 3: enriching from {META_TABLE}...")
    try:
        con = duckdb.connect()
        con.execute("INSTALL httpfs; LOAD httpfs;")
        con.execute(f"""
            SET s3_endpoint='{s3_host}';
            SET s3_access_key_id='{ACCESS_KEY}';
            SET s3_secret_access_key='{SECRET_KEY}';
            SET s3_url_style='path';
        """)
        meta_path = f"s3://{S3_BUCKET}/br_bd_metadados/bigquery_tables/*.parquet"
        # Peek at available columns
        available = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM '{meta_path}' LIMIT 1").fetchall()]
        print(f"  Metadata columns: {available}")

        # Try to find dataset/table description columns
        desc_col = next((c for c in available if "description" in c.lower()), None)
        ds_col   = next((c for c in available if c.lower() in ("dataset_id", "dataset", "schema_name")), None)
        tbl_col  = next((c for c in available if c.lower() in ("table_id", "table_name", "table")), None)

        if desc_col and ds_col and tbl_col:
            rows = con.execute(f"""
                SELECT {ds_col}, {tbl_col}, {desc_col}
                FROM '{meta_path}'
            """).fetchall()
            for ds, tbl, desc in rows:
                key = f"{ds}.{tbl}"
                if key in schemas and desc:
                    schemas[key]["table_description"] = desc
            print(f"  Enriched {len(rows)} table descriptions")
        else:
            print(f"  Could not find expected columns (dataset_id, table_id, description) — skipping enrichment")
        con.close()
    except Exception as e:
        print(f"  Enrichment failed: {e}", file=sys.stderr)
else:
    print("Phase 3: br_bd_metadados.bigquery_tables not in S3 — skipping enrichment")

# ------------------------------------------------------------------ #
# Phase 4a: Write schemas.json
# ------------------------------------------------------------------ #
print("Phase 4: writing outputs...")

output = {
    "_meta": {
        "bucket": S3_BUCKET,
        "total_tables": len(schemas),
        "total_size_bytes": sum(v["total_size_bytes"] for v in schemas.values()),
        "total_size_human": fmt_size(sum(v["total_size_bytes"] for v in schemas.values())),
        "errors": errors,
    },
    "tables": dict(sorted(schemas.items())),
}

with open("schemas.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"  ✓ schemas.json ({len(schemas)} tables)")

# ------------------------------------------------------------------ #
# Phase 4b: Write file_tree.md
# ------------------------------------------------------------------ #
lines = [
    f"# S3 File Tree: {S3_BUCKET}",
    "",
]

# Group by dataset
datasets_map = {}
for dt_key, info in sorted(inventory.items()):
    dataset, table = dt_key.split("/", 1)
    datasets_map.setdefault(dataset, []).append((table, info))

total_files  = sum(len(v["files"]) for v in inventory.values())
total_bytes  = sum(v["total_size_bytes"] for v in inventory.values())

for dataset, tables in sorted(datasets_map.items()):
    ds_bytes = sum(i["total_size_bytes"] for _, i in tables)
    ds_files = sum(len(i["files"]) for _, i in tables)
    lines.append(f"## {dataset}/  ({len(tables)} tables, {fmt_size(ds_bytes)}, {ds_files} files)")
    lines.append("")
    for table, info in sorted(tables):
        schema_entry = schemas.get(f"{dataset}.{table}", {})
        ncols = len(schema_entry.get("columns", []))
        col_str = f", {ncols} cols" if ncols else ""
        table_desc = schema_entry.get("table_description", "")
        desc_str = f" — {table_desc}" if table_desc else ""
        lines.append(f"  - **{table}/**  ({len(info['files'])} files, {fmt_size(info['total_size_bytes'])}{col_str}){desc_str}")
    lines.append("")

lines += [
    "---",
    f"**Total: {len(inventory)} tables · {fmt_size(total_bytes)} · {total_files} parquet files**",
]

with open("file_tree.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print(f"  ✓ file_tree.md ({len(inventory)} tables)")
print()
print("Done!")
print(f"  schemas.json  — full column-level schema dump")
print(f"  file_tree.md  — bucket tree with sizes")
if errors:
    print(f"  {len(errors)} tables failed (see schemas.json _meta.errors)")
