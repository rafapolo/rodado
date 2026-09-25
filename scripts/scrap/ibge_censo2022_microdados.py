#!/usr/bin/env python3
"""
Microdados da amostra do Censo Demografico 2022 (IBGE), versao de acesso
publico -> Parquet zstd, um arquivo por UF, em
~/rodado/br_ibge_censo_demografico/microdados_{domicilio,pessoa,familia,mortalidade}_2022/.

Roda NO BEELINK (le/grava caminhos locais de la):
    scp scripts/scrap/ibge_censo2022_microdados.py beelink:/tmp/ && ssh beelink python3 /tmp/ibge_censo2022_microdados.py

Fonte: https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Microdados_e_Areas_de_Ponderacao/
  - Microdados_de_acesso_Publico/csv/<cod>_<UF>.zip (27 zips, publicados 2026-09-14)
    cada zip: Domicilios_<cod>_publico.csv, Pessoas_..., Familia_..., Mortalidade_...
    ';'-delimitado, ASCII, CRLF, decimal com ponto, vazio = nao se aplica.
  - Documentacao/Layout e dicionario/Layout Microdados CD2022 - acesso Publico.xlsx
    (abas DOMI, PESS, FAMI, MORT: VAR, NOME, posicoes, INT, DEC, TIPO C/A/N)

A versao PUBLICA nao tem municipio nem area de ponderacao: o IBGE suprimiu todo
recorte abaixo da UF (Nota metodologica 05/2026). Por isso nao ha id_municipio.

Colunas: o codigo IBGE da variavel em minusculas (p0150, d0350...), exceto as
chaves renomeadas abaixo. Tipo: C (categoria) e A (alfanumerico) -> VARCHAR,
preservando zero a esquerda ("08"); N sem decimal -> BIGINT; N com decimal -> DOUBLE.
A tabela microdados_layout_2022 guarda coluna -> variavel IBGE -> descricao completa.
"""

import json
import subprocess
import sys
import zipfile
from pathlib import Path

import openpyxl
import polars as pl

HOME = Path.home()
WORK = HOME / "censo2022_microdados"
ZIPDIR = WORK / "zip"
OUT = HOME / "rodado" / "br_ibge_censo_demografico"
BASE = "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Microdados_e_Areas_de_Ponderacao/"
CSV_URL = BASE + "Microdados_de_acesso_Publico/csv/"
LAYOUT_URL = (
    BASE + "Documentacao/Layout%20e%20dicion%c3%a1rio/"
    "Layout%20Microdados%20CD2022%20-%20acesso%20P%c3%bablico.xlsx"
)

UFS = [
    ("11", "RO"), ("12", "AC"), ("13", "AM"), ("14", "RR"), ("15", "PA"), ("16", "AP"),
    ("17", "TO"), ("21", "MA"), ("22", "PI"), ("23", "CE"), ("24", "RN"), ("25", "PB"),
    ("26", "PE"), ("27", "AL"), ("28", "SE"), ("29", "BA"), ("31", "MG"), ("32", "ES"),
    ("33", "RJ"), ("35", "SP"), ("41", "PR"), ("42", "SC"), ("43", "RS"), ("50", "MS"),
    ("51", "MT"), ("52", "GO"), ("53", "DF"),
]

# registro: (aba do layout, prefixo do csv, tabela destino, letra das variaveis)
REGISTROS = [
    ("DOMI", "Domicilios", "microdados_domicilio_2022", "D"),
    ("PESS", "Pessoas", "microdados_pessoa_2022", "P"),
    ("FAMI", "Familia", "microdados_familia_2022", "F"),
    ("MORT", "Mortalidade", "microdados_mortalidade_2022", "M"),
]

# chaves com nome legivel (igual ao padrao de microdados_*_2010)
RENOMES = {
    "0010": "id_regiao",
    "0020": "id_uf",
    "0100": "controle",
    "0110": "peso_amostral",
}
RENOMES_REG = {
    "P": {"P0101": "numero_ordem", "P0115": "numero_ordem_familia"},
    "F": {"F0101": "numero_ordem_familia"},
    "M": {"M0101": "numero_ordem_falecido"},
    "D": {},
}
# marcadas N no layout mas sao codigos de categoria
FORCA_TEXTO = {"F0270"}


def baixa(url: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        return
    subprocess.run(["curl", "-sf", "--retry", "5", "-o", str(dest), url], check=True)


def le_layout(xlsx: Path) -> dict:
    wb = openpyxl.load_workbook(xlsx, read_only=True)
    layout = {}
    for aba, _, _, letra in REGISTROS:
        vars_ = []
        for row in wb[aba].iter_rows(min_row=3, values_only=True):
            if not row or not row[0]:
                continue
            var = str(row[0]).strip()
            nome = " ".join(str(row[1]).split())
            dec = int(row[5] or 0)
            tipo = str(row[6]).strip()
            if var in FORCA_TEXTO or tipo in ("C", "A"):
                dtype = "VARCHAR"
            elif dec > 0:
                dtype = "DOUBLE"
            else:
                dtype = "BIGINT"
            if var[1:] in RENOMES and var[0] == letra:
                col = RENOMES[var[1:]]
            else:
                col = RENOMES_REG[letra].get(var, var.lower())
            if col == "controle":
                dtype = "BIGINT"
            if col == "peso_amostral":
                dtype = "DOUBLE"
            vars_.append({"var": var, "coluna": col, "tipo_ibge": tipo,
                          "decimais": dec, "tipo": dtype, "descricao": nome})
        layout[aba] = vars_
    return layout


PL = {"VARCHAR": pl.Utf8, "BIGINT": pl.Int64, "DOUBLE": pl.Float64}


def converte(zip_path: Path, prefixo: str, cod: str, uf: str, vars_: list, destino: Path) -> int:
    nome = f"{prefixo}_{cod}_publico.csv"
    tmpdir = WORK / "csv"
    tmpdir.mkdir(exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        z.extract(nome, tmpdir)
    csv = tmpdir / nome
    with open(csv, "rb") as fh:
        header = fh.readline().decode("ascii").strip().split(";")
    esperado = [v["var"] for v in vars_]
    if header != esperado:
        faltam = set(esperado) - set(header)
        sobram = set(header) - set(esperado)
        raise SystemExit(f"{nome}: cabecalho difere do layout (faltam {faltam}, sobram {sobram})")
    # streaming: scan_csv -> sink_parquet, sem materializar SP inteiro na RAM
    lf = pl.scan_csv(csv, separator=";", schema={h: pl.Utf8 for h in header})
    exprs = []
    for v in vars_:
        c = pl.col(v["var"]).str.strip_chars()
        c = pl.when(c == "").then(None).otherwise(c)
        exprs.append(c.cast(PL[v["tipo"]], strict=True).alias(v["coluna"]))
    cols = [v["coluna"] for v in vars_]
    lf = lf.select(exprs).with_columns(pl.lit(uf).alias("sigla_uf"))
    lf = lf.select(["id_regiao", "id_uf", "sigla_uf"] + [c for c in cols if c not in ("id_regiao", "id_uf")])
    destino.mkdir(parents=True, exist_ok=True)
    tmp = destino / f".{cod}_{uf}.parquet.tmp"
    lf.sink_parquet(tmp, compression="zstd", compression_level=9, row_group_size=500_000)
    csv.unlink()
    chk = pl.scan_parquet(tmp).select(
        pl.len().alias("n"), (pl.col("id_uf") != cod).sum().alias("bad")
    ).collect()
    if chk["bad"][0]:
        raise SystemExit(f"{nome}: {chk['bad'][0]} linhas com id_uf != {cod}")
    tmp.rename(destino / f"{cod}_{uf}.parquet")
    return chk["n"][0]


def main() -> None:
    ZIPDIR.mkdir(parents=True, exist_ok=True)
    xlsx = WORK / "layout_publico.xlsx"
    baixa(LAYOUT_URL, xlsx)
    layout = le_layout(xlsx)
    (WORK / "layout.json").write_text(json.dumps(layout, ensure_ascii=False, indent=1))

    # tabela de layout (coluna -> variavel IBGE -> descricao com os codigos)
    linhas = []
    for aba, _, tabela, _ in REGISTROS:
        for v in layout[aba]:
            linhas.append({"tabela": tabela, **v})
    lay = pl.DataFrame(linhas)
    dlay = OUT / "microdados_layout_2022"
    dlay.mkdir(parents=True, exist_ok=True)
    lay.write_parquet(dlay / "layout.parquet", compression="zstd")

    contagem = {}
    for cod, uf in UFS:
        zp = ZIPDIR / f"{cod}_{uf}.zip"
        baixa(CSV_URL + zp.name, zp)
        for aba, prefixo, tabela, _ in REGISTROS:
            destino = OUT / tabela
            if (destino / f"{cod}_{uf}.parquet").exists():
                n = pl.scan_parquet(destino / f"{cod}_{uf}.parquet").select(pl.len()).collect().item()
            else:
                n = converte(zp, prefixo, cod, uf, layout[aba], destino)
            contagem.setdefault(tabela, {})[uf] = n
            print(f"{uf} {tabela}: {n:,}", flush=True)
    (WORK / "contagem.json").write_text(json.dumps(contagem, indent=1))
    for t, d in contagem.items():
        print(t, sum(d.values()))


if __name__ == "__main__":
    sys.exit(main())
