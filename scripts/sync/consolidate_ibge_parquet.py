#!/usr/bin/env python3
"""Consolidate per-folder parquet files into single merged tables.
Reads from ~/ibge_ftp_parquet/<folder>/<many>.parquet
Writes to ~/ibge_ftp_consolidated/<folder>.parquet
One file per folder = one queryable SQL table.
"""
import os
import logging
from pathlib import Path
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

PARQUET_DIR = Path.home() / "ibge_ftp_parquet"
CONSOLIDATED = Path.home() / "ibge_ftp_consolidated"
LOG = CONSOLIDATED / "consolidate.log"

CONSOLIDATED.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG, mode="a"),
    ],
)
log = logging.getLogger(__name__)


def consolidate_folder(folder_path, folder_name):
    out_path = CONSOLIDATED / f"{folder_name}.parquet"
    parquet_files = sorted(folder_path.rglob("*.parquet"))
    if not parquet_files:
        return 0, 0

    frames = []
    for pf in parquet_files:
        try:
            df = pd.read_parquet(pf)
            if not df.empty:
                frames.append(df)
        except Exception as e:
            log.warning(f"  skip {pf.name}: {e}")

    if not frames:
        return 0, 0

    # Merge all, filling missing columns with null
    all_columns = set()
    for df in frames:
        all_columns.update(df.columns)
    all_columns = sorted(all_columns)

    merged_frames = []
    for df in frames:
        for col in all_columns:
            if col not in df.columns:
                df[col] = None
        merged_frames.append(df[all_columns])

    merged = pd.concat(merged_frames, ignore_index=True)
    merged = merged.dropna(how="all")

    # Write consolidated parquet
    table = pa.Table.from_pandas(merged, preserve_index=False)
    pq.write_table(table, out_path, compression="zstd")

    return len(parquet_files), len(merged)


def main():
    folders = sorted([
        d for d in PARQUET_DIR.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ])
    log.info(f"Found {len(folders)} folders to consolidate")

    total_files = 0
    total_rows = 0
    total_folders = 0

    for folder in folders:
        folder_name = folder.name
        n_files, n_rows = consolidate_folder(folder, folder_name)
        if n_files > 0:
            total_folders += 1
            total_files += n_files
            total_rows += n_rows
            log.info(f"  {folder_name}: {n_files} files -> {n_rows} rows")
        else:
            log.info(f"  {folder_name}: (empty)")

    log.info(f"=== DONE: {total_folders} folders, {total_files} source files, {total_rows} total rows ===")


if __name__ == "__main__":
    main()
