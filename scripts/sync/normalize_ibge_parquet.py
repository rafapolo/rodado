#!/usr/bin/env python3
"""Smart normalization v2: group by table type across UFs.

For each folder in ~/ibge_ftp_parquet/:
1. Parse filenames to extract table type (strip UF XX, GR X, BR suffixes)
2. Group files by table type
3. Merge each group into one parquet with _uf, _municipio columns
4. Write to ~/ibge_ftp_normalized/<folder>/<table_type>.parquet
"""
import os
import re
import hashlib
from pathlib import Path
from collections import defaultdict
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import logging

PARQUET_DIR = Path.home() / "ibge_ftp_parquet"
OUT = Path.home() / "ibge_ftp_normalized"
LOG = OUT / "normalize.log"

OUT.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG, mode="w"),
    ],
)
log = logging.getLogger(__name__)

STATE_CODES = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA",
    "16": "AP", "17": "TO", "21": "MA", "22": "PI", "23": "CE",
    "24": "RN", "25": "PB", "26": "PE", "27": "AL", "28": "SE",
    "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
    "41": "PR", "42": "SC", "43": "RS", "50": "MS", "51": "MT",
    "52": "GO", "53": "DF",
}

UF_NAMES = {
    "rondonia": "RO", "acre": "AC", "amazonas": "AM", "roraima": "RR",
    "para": "PA", "amapa": "AP", "tocantins": "TO", "maranhao": "MA",
    "piaui": "PI", "ceara": "CE", "rio_grande_do_norte": "RN",
    "paraiba": "PB", "pernambuco": "PE", "alagoas": "AL", "sergipe": "SE",
    "bahia": "BA", "minas_gerais": "MG", "espirito_santo": "ES",
    "rio_de_janeiro": "RJ", "sao_paulo": "SP", "parana": "PR",
    "santa_catarina": "SC", "rio_grande_do_sul": "RS", "mato_grosso_do_sul": "MS",
    "mato_grosso": "MT", "goias": "GO", "distrito_federal": "DF",
}


def extract_geography(filename):
    """Extract UF and municipio from filename."""
    uf = None
    municipio = None
    name = filename.replace(".parquet", "")

    # Extract UF from "UF XX" pattern
    m = re.search(r"UF (\d{2})", name)
    if m:
        uf = STATE_CODES.get(m.group(1))

    # Extract UF from filename prefix
    if not uf:
        for code, uf_abbr in STATE_CODES.items():
            if name.startswith(code + "_"):
                uf = uf_abbr
                break

    # Extract UF from name
    if not uf:
        for name_part, uf_abbr in UF_NAMES.items():
            if name_part in name.lower():
                uf = uf_abbr
                break

    # Extract municipio code (7 digits)
    m = re.search(r"(\d{7})_", name)
    if m:
        municipio = m.group(1)

    return uf, municipio


def get_table_type(filename):
    """Extract normalized table type from filename.

    Examples:
      "01_cor_raca_produtor_xlsx__TABELA 01925 UF 12.parquet" -> "01_cor_raca_produtor_xlsx__TABELA_01925"
      "ufs__confronto_tab3_10_1.parquet" -> "ufs__confronto_tab3_10_1"
      "Brasil_xls__tab1_1_1.parquet" -> "Brasil_xls__tab1_1_1"
      "01_cor_raca_produtor_xlsx__TABELA 01879 GR 1.parquet" -> "01_cor_raca_produtor_xlsx__TABELA_01879"
    """
    name = filename.replace(".parquet", "")
    parts = name.split("__", 1)
    prefix = parts[0]  # e.g. "01_cor_raca_produtor_xlsx"
    tid = parts[1] if len(parts) == 2 else name

    # Strip UF XX, GR X, BR suffixes
    tid = re.sub(r" UF \d+", "", tid)
    tid = re.sub(r" GR \d+", "", tid)
    tid = re.sub(r" BR$", "", tid)
    tid = re.sub(r", GR e UF$", "", tid)

    # Normalize: replace spaces with underscores, lowercase
    tid = re.sub(r"[^a-zA-Z0-9_]", "_", tid)
    tid = re.sub(r"_+", "_", tid).strip("_").lower()

    if not tid:
        tid = prefix.lower()

    return f"{prefix}__{tid}"


def process_folder(folder_path, folder_name):
    """Group files by table type, merge each group."""
    out_dir = OUT / folder_name
    out_dir.mkdir(parents=True, exist_ok=True)

    parquets = sorted(folder_path.glob("*.parquet"))
    if not parquets:
        return 0, 0

    # Phase 1: group by table type
    groups = defaultdict(list)
    for pq_file in parquets:
        try:
            table_type = get_table_type(pq_file.name)
            uf, municipio = extract_geography(pq_file.name)
            groups[table_type].append((pq_file, uf, municipio))
        except Exception as e:
            log.warning(f"  skip {pq_file.name}: {e}")

    # Phase 2: merge each group
    n_tables = 0
    n_rows = 0
    for table_type, items in groups.items():
        try:
            dfs = []
            for pq_file, uf, municipio in items:
                df = pd.read_parquet(pq_file)
                if df.empty:
                    continue
                df = df.copy()
                df.insert(0, "_municipio", municipio)
                df.insert(0, "_uf", uf)
                dfs.append(df)

            if not dfs:
                continue

            # Merge: union of columns, fill missing with null
            all_cols = set()
            for df in dfs:
                all_cols.update(df.columns)
            all_cols = sorted(all_cols)

            for df in dfs:
                for col in all_cols:
                    if col not in df.columns:
                        df[col] = None

            merged = pd.concat([df[all_cols] for df in dfs], ignore_index=True)
            merged = merged.dropna(how="all")

            if merged.empty:
                continue

            # Write
            out_path = out_dir / f"{table_type}.parquet"
            table = pa.Table.from_pandas(merged, preserve_index=False)
            pq.write_table(table, out_path, compression="zstd")
            n_tables += 1
            n_rows += len(merged)

        except Exception as e:
            log.warning(f"  merge error {table_type}: {e}")

    return n_tables, n_rows


def main():
    folders = sorted([
        d for d in PARQUET_DIR.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ])
    log.info(f"Found {len(folders)} folders to normalize")

    total_tables = 0
    total_rows = 0

    for folder in folders:
        folder_name = folder.name
        n_tables, n_rows = process_folder(folder, folder_name)
        total_tables += n_tables
        total_rows += n_rows
        log.info(f"  {folder_name}: {n_tables} tables, {n_rows} rows")

    log.info(f"=== DONE: {total_tables} tables, {total_rows} total rows ===")


if __name__ == "__main__":
    main()
