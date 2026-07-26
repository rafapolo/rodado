#!/usr/bin/env python3
"""Build a JSON catalog of the v3-normalized IBGE FTP tables.

For every table in ~/ibge_ftp_normalized_v3/<folder>/<table>.parquet, record
its title, IBGE table id, UF/year coverage and row count, so a human (or an
LLM) can find the right table without opening 40k parquet files.

Output: ~/ibge_ftp_catalog.json
"""
import json
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

NORMALIZED_DIR = Path.home() / "ibge_ftp_normalized_v3"
OUT_PATH = Path.home() / "ibge_ftp_catalog.json"


def describe_table(path):
    schema = pq.read_schema(path)
    names = schema.names
    meta = pq.read_metadata(path)
    n_rows = meta.num_rows

    read_cols = [c for c in ("_tabela_id", "_titulo", "_ano", "_uf", "_municipio") if c in names]
    df = pd.read_parquet(path, columns=read_cols) if read_cols else pd.DataFrame()

    def top_value(col):
        if col not in df.columns or df[col].dropna().empty:
            return None
        return df[col].dropna().mode().iloc[0]

    ufs = sorted(df["_uf"].dropna().unique().tolist()) if "_uf" in df.columns else []
    anos = sorted(df["_ano"].dropna().unique().tolist()) if "_ano" in df.columns else []
    n_municipios = int(df["_municipio"].nunique()) if "_municipio" in df.columns else 0

    data_cols = [c for c in names if c not in read_cols and not c.startswith("_")
                 and c not in ("_source_folder", "_original_file", "_download_date")]

    return {
        "tabela_id": top_value("_tabela_id"),
        "titulo": top_value("_titulo"),
        "n_rows": n_rows,
        "n_cols": len(data_cols),
        "ufs": ufs,
        "n_ufs": len(ufs),
        "anos": [str(a) for a in anos],
        "n_municipios": n_municipios,
        "colunas": data_cols[:30],
    }


def main():
    catalog = {}
    folders = sorted(d for d in NORMALIZED_DIR.iterdir() if d.is_dir())
    total = 0
    for folder in folders:
        tables = {}
        for f in sorted(folder.glob("*.parquet")):
            try:
                tables[f.stem] = describe_table(f)
            except Exception as e:
                tables[f.stem] = {"error": str(e)}
            total += 1
        catalog[folder.name] = {"n_tabelas": len(tables), "tabelas": tables}
        print(f"  {folder.name}: {len(tables)} tabelas catalogadas")

    with open(OUT_PATH, "w") as fh:
        json.dump(catalog, fh, ensure_ascii=False, indent=1, default=str)

    print(f"=== DONE: {total} tabelas em {len(folders)} pastas -> {OUT_PATH} ===")


if __name__ == "__main__":
    main()
