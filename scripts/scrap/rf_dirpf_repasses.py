"""FDCA/FDI — valores repassados por fundo (destinação de IRPF).

Fonte: gov.br/receitafederal, páginas "fdca-{ano}"/"fdi-{ano}" sob
.../repasse-das-doacoes-feitas-diretamente-no-programa-do-irpf-fdca-e-fdi/.
Cada página lista vários anexos CSV (repasse multiexercício, repasse
corrente, pendentes, fundos aptos/inaptos) com colunas que variam ano a ano
— por isso cada CSV vira seu próprio parquet all-VARCHAR, com 3 colunas de
proveniência (fundo, ano_pagina, arquivo) somadas na frente. Junte tudo com
read_parquet(..., union_by_name=true).

Curiosidade da fonte: HEAD devolve 403 (WAF), GET no mesmo CSV devolve 200 —
mesmo padrão já visto em outras rotas do gov.br (ANP). Nunca testar com -I.
"""
import csv
import io
import re
import sys
import time
import urllib.request
from pathlib import Path

import duckdb

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
BASE = "https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/dados-abertos/receitadata/arrecadacao/repasse-das-doacoes-feitas-diretamente-no-programa-do-irpf-fdca-e-fdi"

FDCA_YEARS = range(2013, 2024)
FDI_YEARS = range(2020, 2024)

SCRATCH = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/rf_dirpf")
RAW = SCRATCH / "raw"
PARQUET = SCRATCH / "parquet"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def list_csvs(fundo: str, ano: int) -> list[str]:
    url = f"{BASE}/{fundo}-{ano}"
    try:
        html = fetch(url).decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  [{fundo}-{ano}] page fetch failed: {e}")
        return []
    hrefs = sorted(set(re.findall(r'href="([^"]+\.csv)"', html)))
    return hrefs


def slug(url: str) -> str:
    return url.rstrip("/").rsplit("/", 1)[-1].removesuffix(".csv")


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    PARQUET.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()

    jobs = [("fdca", y) for y in FDCA_YEARS] + [("fdi", y) for y in FDI_YEARS]
    total_files = 0
    for fundo, ano in jobs:
        csvs = list_csvs(fundo, ano)
        print(f"{fundo}-{ano}: {len(csvs)} csv")
        for url in csvs:
            name = slug(url)
            raw_path = RAW / f"{fundo}_{ano}_{name}.csv"
            if not raw_path.exists():
                try:
                    data = fetch(url)
                except Exception as e:
                    print(f"    FAIL download {url}: {e}")
                    continue
                raw_path.write_bytes(data)
                time.sleep(0.3)
            pq_path = PARQUET / f"{fundo}_{ano}_{name}.parquet"
            if pq_path.exists():
                total_files += 1
                continue
            try:
                raw_bytes = raw_path.read_bytes()
                try:
                    text = raw_bytes.decode("utf-8-sig")
                except UnicodeDecodeError:
                    text = raw_bytes.decode("cp1252")
                # header is on line 2 (line 1 is a title row of just ';'s or a caption)
                lines = text.splitlines()
                header_idx = None
                for i, ln in enumerate(lines[:6]):
                    cells = [c.strip() for c in ln.split(";")]
                    non_empty = [c for c in cells if c]
                    if len(non_empty) >= 3 and any(
                        k in ln for k in ("CNPJ", "Nº", "UF", "Valor", "Município", "Estado")
                    ):
                        header_idx = i
                        break
                if header_idx is None:
                    header_idx = 0
                clean = "\n".join(lines[header_idx:])
                trimmed = raw_path.with_suffix(".trimmed.csv")
                trimmed.write_text(clean, encoding="utf-8")
                con.execute(
                    f"""
                    COPY (
                        SELECT '{fundo}' AS fundo, {ano} AS ano_pagina, '{name}' AS arquivo, *
                        FROM read_csv('{trimmed.as_posix()}', delim=';', header=true,
                                      all_varchar=true, ignore_errors=true, strict_mode=false)
                    ) TO '{pq_path.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
                    """
                )
                trimmed.unlink()
                total_files += 1
            except Exception as e:
                print(f"    FAIL convert {raw_path.name}: {e}")

    print(f"\nTotal parquet files: {total_files}")


if __name__ == "__main__":
    main()
