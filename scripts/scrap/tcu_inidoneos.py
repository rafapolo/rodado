#!/usr/bin/env python3
"""
Fetch TCU (Tribunal de Contas da Uniao) inidoneos/irregulares/inabilitados
lists -> Parquet -> beelink.

Source discovery note: the obvious-looking webservice at
certidoes.apps.tcu.gov.br/api/publico/responsaveis-inidoneos (documented in
various third-party writeups) is guarded by an F5/Shape Security JS
challenge (TSPD cookie + "bobcmn" hashcash payload) on every request,
including OPTIONS -- confirmed blocked across 3 retries, not a path issue.

The REAL open data lives on a plain static-file host instead:
sites.tcu.gov.br/dados-abertos/inidoneos-irregulares/ is a static page (no
WAF) whose own JS (js/script.js) fetches a manifest CSV listing four
pipe-delimited bulk CSV files -- this is the genuine "dados abertos"
distribution channel, not the certidoes API. Manifest:
  https://sites.tcu.gov.br/dados-abertos/inidoneos-irregulares/arquivos/inidoneos-irregulares-arquivos.csv

Four lists (kept as separate tables, different entity/subject shapes):
  - licitantes_inidoneos: barred bidders (companies), CNPJ
  - inabilitados_funcao_publica: individuals barred from public office, CPF
  - resp_contas_julgadas_irregulares: officials with accounts ruled irregular
  - resp_contas_julgadas_irreg_implicacao_eleitoral: same, with electoral-
    eligibility implication flag

No auth required. Files are small (under 7MB each), single GET per file.

Usage:
    python3 scripts/scrap/tcu_inidoneos.py
"""

import csv
import io
import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen

BEELINK_HOST = "beelink"
DATASET_PATH = "~/rodado/br_tcu_inidoneos"
BEELINK_PATH = f"{DATASET_PATH}/empresas"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
TEMP_DIR = Path("/private/tmp/claude-501/-Users-polux-Projetos-rodado/c780c9c0-b6b3-44b0-964e-08a3b2f2024c/scratchpad/tcu_inidoneos")

MANIFEST_URL = "https://sites.tcu.gov.br/dados-abertos/inidoneos-irregulares/arquivos/inidoneos-irregulares-arquivos.csv"
FETCH_TIMEOUT = 60

# manifest "NOME" substring -> target table name
TABLE_MAP = {
    "licitantes inidôneos": "empresas",  # matches BEELINK_PATH's declared tabela
    "inabilitados para função pública": "inabilitados_funcao_publica",
    "contas julgadas irreg. com possível implicação eleitoral": "resp_contas_julgadas_irreg_implicacao_eleitoral",
    "contas julgadas irregulares": "resp_contas_julgadas_irregulares",
}


def http_get(url: str, timeout: int = FETCH_TIMEOUT) -> bytes:
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def parse_manifest() -> list:
    raw = http_get(MANIFEST_URL).decode("utf-8-sig", errors="replace")
    lines = raw.splitlines()
    # First line is a bare date string, second is the pipe-delimited header.
    body = "\n".join(lines[1:])
    reader = csv.DictReader(io.StringIO(body), delimiter="|", quotechar='"')
    entries = []
    for row in reader:
        nome = (row.get("NOME") or "").strip()
        arquivo = (row.get("ARQUIVO") or "").strip()
        if nome and arquivo:
            entries.append((nome, arquivo))
    return entries


def table_name_for(nome: str) -> str:
    nome_lower = nome.lower()
    for key, table in TABLE_MAP.items():
        if key in nome_lower:
            return table
    # Fallback: slugify the name so nothing is silently dropped.
    return nome_lower.replace(" ", "_").replace(".", "")


def fetch_rows(csv_url: str) -> list:
    raw = http_get(csv_url).decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(raw), delimiter="|", quotechar='"')
    rows = [{k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items() if k} for row in reader]
    return rows


def write_and_push(rows: list, table_name: str) -> bool:
    import pyarrow as pa
    import pyarrow.parquet as pq

    if not rows:
        print(f"  No rows for {table_name} — skipping push.", file=sys.stderr)
        return False

    table = pa.Table.from_pylist(rows)
    parquet_path = TEMP_DIR / f"{table_name}.parquet"
    pq.write_table(table, str(parquet_path), compression="zstd")
    print(f"  Wrote {parquet_path} ({parquet_path.stat().st_size / 1e6:.2f} MB, {table.num_rows} rows)")

    beelink_path = f"{DATASET_PATH}/{table_name}"
    subprocess.run(f"ssh {BEELINK_HOST} 'mkdir -p {beelink_path}'", shell=True, check=True)
    result = subprocess.run(
        f"rsync -av {parquet_path} {BEELINK_HOST}:{beelink_path}/",
        shell=True,
    )
    if result.returncode != 0:
        print(f"rsync failed for {table_name}", file=sys.stderr)
        return False
    print(f"  Pushed to {BEELINK_HOST}:{beelink_path}/{parquet_path.name}")
    return True


def main():
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    print("Fetching manifest ...")
    entries = parse_manifest()
    print(f"  {len(entries)} files listed")

    ok = True
    for nome, url in entries:
        table_name = table_name_for(nome)
        print(f"=== {nome} -> {table_name} ===")
        rows = fetch_rows(url)
        print(f"  {len(rows)} rows")
        ok &= write_and_push(rows, table_name)

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
