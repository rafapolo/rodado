#!/usr/bin/env python3
"""Create a DuckDB database with views for all IBGE FTP parquet files.
Each folder becomes a schema, each parquet becomes a view.
Result: queryable SQL database at ~/ibge_ftp.duckdb

By default points at the v3-normalized tables (~/ibge_ftp_normalized_v3);
pass --source-dir to point at raw/other output instead.
"""
import argparse
import re
from pathlib import Path
import duckdb

PARQUET_DIR = Path.home() / "ibge_ftp_normalized_v3"
DB_PATH = Path.home() / "ibge_ftp.duckdb"

def clean_name(name):
    """Sanitize name for SQL identifier."""
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    if name[0].isdigit():
        name = "t_" + name
    return name.lower()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-dir", default=str(PARQUET_DIR))
    ap.add_argument("--db-path", default=str(DB_PATH))
    args = ap.parse_args()
    source_dir = Path(args.source_dir)
    db_path = Path(args.db_path)

    if db_path.exists():
        db_path.unlink()

    conn = duckdb.connect(str(db_path))

    total_views = 0
    total_schemas = 0

    folders = sorted([
        d for d in source_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ])
    
    for folder in folders:
        folder_name = clean_name(folder.name)
        conn.execute(f'CREATE SCHEMA IF NOT EXISTS "{folder_name}"')
        total_schemas += 1
        
        parquets = sorted(folder.glob("*.parquet"))
        for pq_file in parquets:
            view_name = clean_name(pq_file.stem)
            parquet_path = str(pq_file).replace("'", "''")
            try:
                conn.execute(
                    f'CREATE OR REPLACE VIEW "{folder_name}"."{view_name}" AS '
                    f"SELECT * FROM read_parquet('{parquet_path}')"
                )
                total_views += 1
            except Exception as e:
                print(f"SKIP {folder.name}/{pq_file.name}: {e}")
        
        print(f"  {folder.name}: {len(parquets)} views")
    
    # Create a summary view
    conn.execute("""
        CREATE OR REPLACE VIEW _catalog AS
        SELECT 
            table_schema,
            table_name,
            (SELECT COUNT(*) FROM information_schema.columns c 
             WHERE c.table_schema = t.table_schema AND c.table_name = t.table_name) as columns
        FROM information_schema.tables t
        WHERE table_type = 'VIEW' AND table_schema != 'main'
        ORDER BY table_schema, table_name
    """)
    
    conn.close()
    print(f"\n=== DONE: {total_schemas} schemas, {total_views} views ===")
    print(f"Database: {DB_PATH}")
    print(f"Query: duckdb ~/ibge_ftp.duckdb")


if __name__ == "__main__":
    main()
