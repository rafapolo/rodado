#!/usr/bin/env python3
"""
ANEEL (dadosabertos.aneel.gov.br, CKAN) — usinas SIGA, tarifas homologadas e
indicadores de continuidade DEC/FEC -> Parquet -> beelink.

Continuação de `br_aneel_dadosabertos.empreendimento_geracao_distribuida`
(2026-09-04). O host só completa TCP a partir de IP brasileiro: o download sai
por `_proxy_br.Pool`. Os recursos vêm da API CKAN (`package_show`), não de URL
fixa, porque o id do recurso muda quando a ANEEL republica.

Tabelas (todas em ~/rodado/br_aneel_dadosabertos/<tabela>/):
  - siga_empreendimentos_geracao   usinas (SIGA), CSV
  - tarifas_homologadas            tarifas por distribuidora/subgrupo/posto, CSV
  - indicadores_continuidade       DEC/FEC apurado por conjunto, 3 parquets (2000–2029)
  - indicadores_continuidade_compensacao   compensação paga por violação, 2 parquets
  - indicadores_continuidade_limite        limites regulatórios DEC/FEC, CSV
  - indicadores_continuidade_atributos     atributos físico-elétricos do conjunto, CSV
  - indicadores_continuidade_dominio       dicionário dos códigos de indicador, CSV

Uso:
    python3 scripts/scrap/aneel_dadosabertos.py [TEMP_DIR]
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _proxy_br import Pool  # noqa: E402

BEELINK_HOST = "beelink"
DATASET_PATH = "~/rodado/br_aneel_dadosabertos"
API = "https://dadosabertos.aneel.gov.br/api/3/action"
TEMP_DIR = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/aneel")

# tabela -> (dataset CKAN, filtro no nome do recurso, formato)
TABELAS = {
    "siga_empreendimentos_geracao": ("siga-sistema-de-informacoes-de-geracao-da-aneel",
                                     lambda n: n == "siga-empreendimentos-geracao.csv", "CSV"),
    "tarifas_homologadas": ("tarifas-distribuidoras-energia-eletrica",
                            lambda n: n.endswith(".csv"), "CSV"),
    "indicadores_continuidade": ("indicadores-coletivos-de-continuidade-dec-e-fec",
                                 lambda n: n.startswith("indicadores-continuidade-coletivos-20"), "PARQUET"),
    "indicadores_continuidade_compensacao": ("indicadores-coletivos-de-continuidade-dec-e-fec",
                                             lambda n: "compensacao" in n, "PARQUET"),
    "indicadores_continuidade_limite": ("indicadores-coletivos-de-continuidade-dec-e-fec",
                                        lambda n: n.endswith("-limite"), "CSV"),
    "indicadores_continuidade_atributos": ("indicadores-coletivos-de-continuidade-dec-e-fec",
                                           lambda n: n.endswith("-atributos"), "CSV"),
    "indicadores_continuidade_dominio": ("indicadores-coletivos-de-continuidade-dec-e-fec",
                                         lambda n: n == "dominio-indicadores-indqual", "CSV"),
}


def csv_para_parquet(src: Path, dst: Path):
    """CSV da ANEEL: `;`, latin-1 na maioria, decimal com vírgula. Tudo vira
    VARCHAR — os tipos saem numa view/consulta, não num palpite do leitor."""
    import duckdb

    raw = src.read_bytes()[:200_000]
    try:
        raw.decode("utf-8")
        enc = "utf-8"
    except UnicodeDecodeError:
        enc = "latin-1"
    con = duckdb.connect()
    con.execute(
        f"COPY (SELECT * FROM read_csv('{src}', delim=';', header=true, all_varchar=true, "
        f"encoding='{enc}', quote='\"', strict_mode=false)) "
        f"TO '{dst}' (FORMAT parquet, COMPRESSION zstd)"
    )
    return con.execute(f"SELECT count(*) FROM '{dst}'").fetchone()[0]


def main():
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    pool = Pool(f"{API}/package_list")
    pacotes = {}
    feitos = {}
    for tabela, (pkg, filtro, fmt) in TABELAS.items():
        if pkg not in pacotes:
            pacotes[pkg] = pool.get(f"{API}/package_show?id={pkg}").json()["result"]["resources"]
        recursos = [r for r in pacotes[pkg] if r["format"].upper() == fmt and filtro(r["name"])]
        if not recursos:
            print(f"  ✗ {tabela}: nenhum recurso {fmt} casou")
            continue
        outdir = TEMP_DIR / "out" / tabela
        outdir.mkdir(parents=True, exist_ok=True)
        linhas = 0
        for r in recursos:
            nome = r["url"].rsplit("/", 1)[-1]
            bruto = TEMP_DIR / "raw" / nome
            bruto.parent.mkdir(exist_ok=True)
            if not bruto.exists():
                print(f"  baixando {nome} ({(r.get('size') or 0) / 1e6:.0f} MB)")
                pool.download(r["url"], bruto)
            stem = Path(nome).stem
            if fmt == "PARQUET":
                dst = outdir / nome
                dst.write_bytes(bruto.read_bytes())
                import duckdb
                n = duckdb.sql(f"SELECT count(*) FROM '{dst}'").fetchone()[0]
            else:
                dst = outdir / f"{stem}.parquet"
                n = csv_para_parquet(bruto, dst)
            linhas += n
            print(f"  ✓ {tabela} <- {nome}: {n:,} linhas")
        feitos[tabela] = linhas

    for tabela in feitos:
        remote = f"{DATASET_PATH}/{tabela}"
        subprocess.run(["ssh", BEELINK_HOST, f"mkdir -p {remote}"], check=True)
        subprocess.run(["rsync", "-a", f"{TEMP_DIR}/out/{tabela}/", f"{BEELINK_HOST}:{remote}/"], check=True)
        print(f"  ✓ push {tabela} ({feitos[tabela]:,} linhas)")
    return 0 if feitos else 1


if __name__ == "__main__":
    sys.exit(main())
