import os
import json
import sys
import pyarrow.parquet as pq
import s3fs
import boto3
import duckdb
from dotenv import load_dotenv

# TODO: export bigquery colum description as parquet footer metadata

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
# Phase 3: Enrich table + column descriptions from BD GraphQL API
# ------------------------------------------------------------------ #
print("Phase 3: fetching descriptions from Base dos Dados GraphQL API...")
try:
    from basedosdados.backend import Backend as _BDBackend

    _bd = _BDBackend()
    _GRAPHQL_QUERY = """
        query ($first: Int!, $offset: Int!) {
            allTable(first: $first, offset: $offset) {
                totalCount
                edges {
                    node {
                        slug
                        dataset { slug }
                        descriptionPt
                        columns {
                            edges {
                                node {
                                    name
                                    descriptionPt
                                }
                            }
                        }
                    }
                }
            }
        }
    """
    PAGE_SIZE = 100
    offset = 0
    col_descs: dict = {}   # (dataset.table, col_name) -> description
    tbl_descs: dict = {}   # dataset.table -> description
    total = None

    while True:
        result = _bd._execute_query(
            _GRAPHQL_QUERY, variables={"first": PAGE_SIZE, "offset": offset}
        )
        items = result["allTable"]["items"]
        if total is None:
            total = result["allTable"]["totalCount"]
            print(f"  API reports {total} tables total")
        for tbl_node in items:
            ds_slug  = (tbl_node.get("dataset") or {}).get("slug", "")
            tbl_slug = tbl_node.get("slug", "")
            key = f"{ds_slug}.{tbl_slug}"
            desc_pt = tbl_node.get("descriptionPt") or ""
            if desc_pt:
                tbl_descs[key] = desc_pt
            for col_node in (tbl_node.get("columns") or {}).get("items", []):
                col_name  = col_node.get("name", "")
                col_desc  = col_node.get("descriptionPt") or ""
                if col_name and col_desc:
                    col_descs[(key, col_name)] = col_desc
        offset += PAGE_SIZE
        print(f"  fetched {min(offset, total)}/{total} tables...", end="\r")
        if offset >= total:
            break

    print()  # newline after \r progress

    enriched_tbls = 0
    enriched_cols = 0
    for tbl_key, tbl_info in schemas.items():
        if tbl_key in tbl_descs:
            tbl_info["table_description"] = tbl_descs[tbl_key]
            enriched_tbls += 1
        for col in tbl_info["columns"]:
            lookup = (tbl_key, col["name"])
            if lookup in col_descs and not col.get("description"):
                col["description"] = col_descs[lookup]
                enriched_cols += 1

    print(f"  Enriched {enriched_tbls} table descriptions, {enriched_cols} column descriptions")

except Exception as e:
    print(f"  GraphQL enrichment failed: {e}", file=sys.stderr)

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
