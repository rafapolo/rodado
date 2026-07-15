#!/usr/bin/env python3
"""
Fetch TCE-ES (Tribunal de Contas do Estado do Espirito Santo) data via the
dados.es.gov.br CKAN portal -> Parquet -> beelink.

CKAN API: https://dados.es.gov.br/api/3/action/
No auth needed. package_show?id=<dataset> gives resource URLs; resources
resolve through a redirect to a presigned S3 URL (urllib follows redirects
by default, no special handling needed).

The TCEES organization publishes 20+ datasets on this portal; mirroring all
of them is out of scope for a first pass. This picks 5 corruption/
accountability-relevant tables (one representative resource per dataset,
except lista_responsaveis which merges 4 same-schema "sanctioned parties"
CSVs into one table with a `categoria` column):

  - julgamento_contas: municipal accounts judgment (parecer previo + camara)
  - obras_publicas: public-works contracts (values, deadlines, overruns) —
    swapped in for the "tcees-contratacoes" dataset's own contratacoes.csv,
    which is 15MB+ and downloads at ~500KB/s from this host (would blow the
    script's time budget); the dedicated "obras-publicas" CKAN dataset has
    the same corruption-relevant contract/value fields at a fraction the size
  - resultados_fiscalizacoes: municipal internal-control audit scores
  - aquisicoes_mensais: monthly TCEES acquisitions/expense reports
  - lista_responsaveis: sanctioned-party lists (inidoneas / proibidos de
    contratar / contas irregulares / inabilitados)

Source files are ';' or ',' delimited CSV in Latin-1 (cp1252-ish) encoding
with mangled accents when read as UTF-8; pandas is used per-resource with
the encoding/delimiter observed for each.

Usage:
    python3 scripts/scrap/tce_es.py
"""

import subprocess
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

BEELINK_HOST = "beelink"
DATASET_PATH = "~/rodado/br_tce_es/dados"
BEELINK_PATH = f"{DATASET_PATH}/julgamento_contas"
TEMP_DIR = Path("/private/tmp/claude-501/-Users-polux-Projetos-rodado/50905fb8-827b-445f-bb28-3e8ed468da54/scratchpad/tce_es")

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

# table_name -> list of (resource_url, delimiter, encoding, extra_columns)
RESOURCES = {
    "julgamento_contas": [
        (
            "https://dados.es.gov.br/dataset/b669d51c-1443-44b9-9011-0d0968dd6270/resource/f4aecbe8-d10b-4e51-afd8-ba5c3f0855c6/download/julgamentodecontas.csv",
            ";", "latin-1", {},
        ),
    ],
    "obras_publicas": [
        (
            "https://dados.es.gov.br/dataset/339b6abf-f521-47ba-b52f-74b25f0f6438/resource/51dde888-1869-449c-abba-b1d1739a30a0/download/obras.csv",
            ";", "utf-8-sig", {},
        ),
    ],
    "resultados_fiscalizacoes": [
        (
            "https://dados.es.gov.br/dataset/a3943f5b-ad00-42b6-9448-fadfe6814885/resource/a96ba397-d49f-4051-ad9f-df7d1baae5d8/download/97-d49f-4051-ad9f-df7d1baae5d8",
            ";", "latin-1", {},
        ),
    ],
    "aquisicoes_mensais": [
        (
            "https://dados.es.gov.br/dataset/962883df-b854-4d69-af40-bbb9ef06bf38/resource/51d19202-af07-4100-bb77-af75e93f3287/download/aquisicoesmensais.csv",
            ";", "utf-8-sig", {},
        ),
    ],
    "lista_responsaveis": [
        (
            "https://dados.es.gov.br/dataset/149e1a1a-db21-4b97-b7e2-fe3d7d75846e/resource/ca979cb0-7ee5-4d91-af6c-804a353b9ef2/download/nempresasinidoneas.csv",
            ";", "latin-1", {"categoria": "empresas_inidoneas"},
        ),
        (
            "https://dados.es.gov.br/dataset/149e1a1a-db21-4b97-b7e2-fe3d7d75846e/resource/2c27a170-e415-4b9d-9679-49a65903979a/download/nproibidoscontratar.csv",
            ";", "latin-1", {"categoria": "proibidos_contratar"},
        ),
        (
            "https://dados.es.gov.br/dataset/149e1a1a-db21-4b97-b7e2-fe3d7d75846e/resource/d2a18709-9c15-46da-bdbd-fbc3ddbc2202/download/ncontasirregulares.csv",
            ";", "latin-1", {"categoria": "contas_irregulares"},
        ),
        (
            "https://dados.es.gov.br/dataset/149e1a1a-db21-4b97-b7e2-fe3d7d75846e/resource/4fe9a28d-02b4-438b-851b-ea33904f2344/download/nresponsaveisinabilitados.csv",
            ";", "latin-1", {"categoria": "responsaveis_inabilitados"},
        ),
    ],
}


def _download(url: str, dest: Path):
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=60) as resp:
        dest.write_bytes(resp.read())


def main():
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    written = {}
    for table_name, resources in RESOURCES.items():
        print(f"Building {table_name} ({len(resources)} resource(s)) ...")
        dfs = []
        for i, (url, delim, encoding, extra_cols) in enumerate(resources):
            csv_path = TEMP_DIR / f"{table_name}_{i}.csv"
            try:
                _download(url, csv_path)
            except Exception as e:
                print(f"  x download failed for {url}: {e}")
                continue
            try:
                df = pd.read_csv(csv_path, sep=delim, encoding=encoding, dtype=str, on_bad_lines="skip")
            except Exception as e:
                print(f"  x parse failed for {csv_path.name}: {e}")
                continue
            for col, val in extra_cols.items():
                df[col] = val
            dfs.append(df)
            print(f"  - resource {i}: {len(df)} rows, {len(df.columns)} cols")
            time.sleep(0.2)

        if not dfs:
            print(f"  x {table_name}: no data, skipping")
            continue

        combined = pd.concat(dfs, ignore_index=True) if len(dfs) > 1 else dfs[0]
        table = pa.Table.from_pandas(combined, preserve_index=False)
        parquet_path = TEMP_DIR / f"{table_name}.parquet"
        pq.write_table(table, str(parquet_path), compression="zstd")
        written[table_name] = (parquet_path, table.num_rows)
        print(f"  v {table_name}: {table.num_rows} total rows -> {parquet_path.name}")

    if not written:
        print("No tables written - aborting, nothing to push.")
        return 1

    for table_name, (parquet_path, rows) in written.items():
        remote_dir = f"{DATASET_PATH}/{table_name}"
        subprocess.run(f"ssh {BEELINK_HOST} 'mkdir -p {remote_dir}'", shell=True, check=True)
        result = subprocess.run(
            f"rsync -av {parquet_path} {BEELINK_HOST}:{remote_dir}/",
            shell=True,
        )
        if result.returncode != 0:
            print(f"  x rsync failed for {table_name}")
            return 1
        print(f"  v pushed {table_name} ({rows} rows) to {BEELINK_HOST}:{remote_dir}/")

    print(f"\nDone: {len(written)} tables pushed to {BEELINK_HOST}:{DATASET_PATH}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
