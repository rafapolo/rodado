#!/usr/bin/env python3
"""Convert IBGE FTP raw files to Parquet with metadata.
Reads from ~/ibge_ftp_raw/<folder>/, writes to ~/ibge_ftp_parquet/<folder>/<table>.parquet.
Adds columns: _source_folder, _original_file, _download_date.
Handles: CSV, TXT, DTA, DAT, JSON, XLSX, XLS, ZIP, PDF (tables).
"""
import os
import zipfile
import logging
import tempfile
from pathlib import Path
from datetime import datetime
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

BASE = Path.home() / "ibge_ftp_raw"
OUT = Path.home() / "ibge_ftp_parquet"
LOG_FILE = OUT / "convert.log"
CONVERTIBLE_EXT = {".csv", ".txt", ".dta", ".dat", ".json", ".xlsx", ".xls", ".zip", ".pdf"}
DATA_EXT = {".csv", ".txt", ".dta", ".dat", ".json"}
EXCEL_EXT = {".xlsx", ".xls"}
MAX_ROWS = 10_000_000
MAX_COLS = 500

OUT.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, mode="a"),
    ],
)
log = logging.getLogger(__name__)


def save_parquet(df, path, source_folder, original_file, download_date):
    if df is None or df.empty:
        return 0
    df.insert(0, "_download_date", download_date)
    df.insert(0, "_original_file", original_file)
    df.insert(0, "_source_folder", source_folder)
    df = df.dropna(how="all")
    if df.empty:
        return 0
    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_table(table, path, compression="zstd")
    return len(df)


def read_csv_smart(path):
    for enc in ["utf-8", "latin-1", "iso-8859-1", "cp1252"]:
        for sep in [",", ";", "\t", "|"]:
            try:
                df = pd.read_csv(
                    path, sep=sep, encoding=enc,
                    on_bad_lines="skip", nrows=MAX_ROWS,
                    low_memory=False, dtype=str,
                )
                if len(df.columns) > 1:
                    return df
            except Exception:
                continue
        try:
            df = pd.read_csv(
                path, encoding=enc, on_bad_lines="skip",
                nrows=MAX_ROWS, low_memory=False, dtype=str,
            )
            return df
        except Exception:
            continue
    return None


def read_excel_smart(path):
    engine = "xlrd" if str(path).endswith(".xls") else "openpyxl"
    try:
        xls = pd.ExcelFile(path, engine=engine)
        frames = []
        for sheet in xls.sheet_names:
            try:
                df = pd.read_excel(xls, sheet_name=sheet, nrows=MAX_ROWS, dtype=str)
                if df is not None and len(df) > 0 and len(df.columns) > 0:
                    df["__sheet__"] = sheet
                    frames.append(df)
            except Exception:
                continue
        if frames:
            return pd.concat(frames, ignore_index=True) if len(frames) > 1 else frames[0]
    except Exception:
        pass
    return None


def read_pdf_tables(path):
    if not HAS_PDFPLUMBER:
        return None
    try:
        frames = []
        with pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                for j, table in enumerate(tables):
                    if not table or len(table) < 2:
                        continue
                    header = table[0]
                    if not header or all(c is None for c in header):
                        continue
                    rows = table[1:]
                    try:
                        df = pd.DataFrame(rows, columns=header)
                        df["__page__"] = str(i + 1)
                        df["__table__"] = str(j + 1)
                        frames.append(df)
                    except Exception:
                        continue
        if frames:
            return pd.concat(frames, ignore_index=True)
    except Exception:
        pass
    return None


def process_file(filepath, folder_name):
    out_dir = OUT / folder_name
    out_dir.mkdir(parents=True, exist_ok=True)
    ext = filepath.suffix.lower()
    download_date = datetime.fromtimestamp(filepath.stat().st_mtime).isoformat()
    base_name = filepath.stem
    saved = 0

    if ext in DATA_EXT:
        df = read_csv_smart(filepath)
        if df is not None and not df.empty:
            out_path = out_dir / f"{base_name}.parquet"
            saved = save_parquet(df, out_path, folder_name, filepath.name, download_date)

    elif ext in EXCEL_EXT:
        df = read_excel_smart(filepath)
        if df is not None and not df.empty:
            out_path = out_dir / f"{base_name}.parquet"
            saved = save_parquet(df, out_path, folder_name, filepath.name, download_date)

    elif ext == ".zip":
        try:
            with zipfile.ZipFile(filepath) as zf:
                inner_files = [
                    f for f in zf.namelist()
                    if not f.startswith("__MACOSX") and not f.endswith("/")
                ]
                if not inner_files:
                    return 0
                with tempfile.TemporaryDirectory() as tmp:
                    zf.extractall(tmp)
                    for inner in inner_files:
                        inner_path = Path(tmp) / inner
                        if not inner_path.is_file():
                            continue
                        inner_ext = inner_path.suffix.lower()
                        inner_stem = Path(inner).stem
                        if inner_ext in DATA_EXT:
                            df = read_csv_smart(inner_path)
                            if df is not None and not df.empty:
                                tag = f"{base_name}__{inner_stem}"
                                out_path = out_dir / f"{tag}.parquet"
                                saved += save_parquet(
                                    df, out_path, folder_name,
                                    f"{filepath.name}/{inner}", download_date,
                                )
                        elif inner_ext in EXCEL_EXT:
                            df = read_excel_smart(inner_path)
                            if df is not None and not df.empty:
                                tag = f"{base_name}__{inner_stem}"
                                out_path = out_dir / f"{tag}.parquet"
                                saved += save_parquet(
                                    df, out_path, folder_name,
                                    f"{filepath.name}/{inner}", download_date,
                                )
        except Exception as e:
            log.warning(f"zip error {filepath}: {e}")

    elif ext == ".pdf" and HAS_PDFPLUMBER:
        df = read_pdf_tables(filepath)
        if df is not None and not df.empty:
            out_path = out_dir / f"{base_name}.parquet"
            saved = save_parquet(df, out_path, folder_name, filepath.name, download_date)

    return saved


def main():
    total_files = 0
    total_rows = 0
    total_folders = 0
    errors = []

    folders = sorted(
        [d for d in BASE.iterdir() if d.is_dir() and not d.name.startswith(".")]
    )
    log.info(f"Found {len(folders)} folders in {BASE}")

    for folder in folders:
        folder_name = folder.name
        log.info(f"=== Processing {folder_name} ===")
        folder_rows = 0
        folder_files = 0

        for root, dirs, files in os.walk(folder):
            for fname in files:
                fpath = Path(root) / fname
                ext = fpath.suffix.lower()

                if ext not in CONVERTIBLE_EXT:
                    continue

                try:
                    rows = process_file(fpath, folder_name)
                    if rows > 0:
                        folder_rows += rows
                        folder_files += 1
                        total_rows += rows
                        total_files += 1
                        log.info(f"  {fpath.relative_to(folder)}: {rows} rows")
                except Exception as e:
                    errors.append((str(fpath), str(e)))
                    log.error(f"  FAILED {fpath.relative_to(folder)}: {e}")

        if folder_files > 0:
            total_folders += 1
        log.info(f"  {folder_name}: {folder_files} files, {folder_rows} rows total")

    log.info(f"=== DONE: {total_folders} folders, {total_files} files, {total_rows} rows ===")
    if errors:
        log.warning(f"=== {len(errors)} errors ===")
        for path, err in errors[:20]:
            log.warning(f"  {path}: {err}")


if __name__ == "__main__":
    main()
