#!/usr/bin/env python3
"""
Microdados da PNAD COVID19 (IBGE, mai-nov/2020, 7 meses) -> Parquet zstd, um
arquivo por mes, em ~/rodado/br_ibge_pnad_covid/microdados/microdados_2020_MM.parquet.

Roda NO BEELINK (le/grava caminhos locais de la):
    scp scripts/scrap/ibge_pnad_covid_microdados.py beelink:/tmp/ && ssh beelink python3 /tmp/ibge_pnad_covid_microdados.py

Fonte: https://ftp.ibge.gov.br/Trabalho_e_Rendimento/Pesquisa_Nacional_por_Amostra_de_Domicilios_PNAD_COVID19/Microdados/
  - Dados/PNAD_COVID_MM2020.zip (1 CSV por mes: ',' delimitado, ASCII, cabecalho,
    vazio = nao aplicavel, valores em reais inteiros)
  - Documentacao/Dicionario_PNAD_COVID_MM2020_20220621.xls

O questionario cresceu: mai/jun tem 114 colunas, jul-out 145, nov 148 (A006A,
A006B, A007A). Todos os meses saem com o esquema completo de 148 variaveis
(coluna ausente no mes = NULL), para `read_parquet('.../*.parquet')` funcionar
sem union_by_name.

Colunas: o codigo IBGE em minusculas, igual a br_ibge_pnad_covid.dicionario
(a001a, b0011, c007c...). UF vira id_uf; acrescenta ano, mes, sigla_uf e
id_domicilio (upa || v1008, unico por mes).
Tipos:
  - variaveis de categoria -> VARCHAR SEM zero a esquerda ("01" -> "1"), porque
    a `chave` do dicionario do espelho e sem padding ('1', '10', f0022 '0');
    assim `m.c007c = d.chave` casa direto.
  - identificadores (upa, estrato, v1008, posest) -> VARCHAR como no CSV.
  - contagens/idade/horas/datas -> BIGINT; pesos e valores em R$ -> DOUBLE.
"""

import subprocess
import zipfile
from pathlib import Path

import polars as pl

HOME = Path.home()
RAW = HOME / "duckdb_tmp" / "pnad_covid_raw"
OUT = HOME / "rodado" / "br_ibge_pnad_covid" / "microdados"
BASE = (
    "https://ftp.ibge.gov.br/Trabalho_e_Rendimento/"
    "Pesquisa_Nacional_por_Amostra_de_Domicilios_PNAD_COVID19/Microdados/"
)
MESES = ["05", "06", "07", "08", "09", "10", "11"]

UFS = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP",
    "17": "TO", "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB",
    "26": "PE", "27": "AL", "28": "SE", "29": "BA", "31": "MG", "32": "ES",
    "33": "RJ", "35": "SP", "41": "PR", "42": "SC", "43": "RS", "50": "MS",
    "51": "MT", "52": "GO", "53": "DF",
}

# esquema de novembro (o mais completo), na ordem do CSV
COLUNAS = (
    "Ano UF CAPITAL RM_RIDE V1008 V1012 V1013 V1016 Estrato UPA V1022 V1023 V1030 "
    "V1031 V1032 posest A001 A001A A001B1 A001B2 A001B3 A002 A003 A004 A005 A006 "
    "A006A A006B A007 A007A A008 A009 B0011 B0012 B0013 B0014 B0015 B0016 B0017 "
    "B0018 B0019 B00110 B00111 B00112 B00113 B002 B0031 B0032 B0033 B0034 B0035 "
    "B0036 B0037 B0041 B0042 B0043 B0044 B0045 B0046 B005 B006 B007 B008 B009A "
    "B009B B009C B009D B009E B009F B0101 B0102 B0103 B0104 B0105 B0106 B011 C001 "
    "C002 C003 C004 C005 C0051 C0052 C0053 C006 C007 C007A C007B C007C C007D C007E "
    "C007E1 C007E2 C007F C008 C009 C009A C010 C0101 C01011 C01012 C0102 C01021 "
    "C01022 C0103 C0104 C011A C011A1 C011A11 C011A12 C011A2 C011A21 C011A22 C012 "
    "C013 C014 C015 C016 C017A D0011 D0013 D0021 D0023 D0031 D0033 D0041 D0043 "
    "D0051 D0053 D0061 D0063 D0071 D0073 E001 E0021 E0022 E0023 E0024 F001 F0021 "
    "F0022 F002A1 F002A2 F002A3 F002A4 F002A5 F0061 F006"
).split()

IDENT = {"upa", "estrato", "v1008", "posest"}
INTEIRO = {
    "ano", "v1012", "v1013", "v1016", "v1030", "a001", "a001b1", "a001b2", "a001b3",
    "a002", "c0051", "c0052", "c0053", "c007e1", "c007e2", "c008", "c009", "f006",
}
DECIMAL = {
    "v1031", "v1032", "c01012", "c01022", "c011a12", "c011a22", "d0013", "d0023",
    "d0033", "d0043", "d0053", "d0063", "d0073", "f0021",
}


def baixa(url: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        return
    tmp = dest.with_suffix(dest.suffix + ".part")
    subprocess.run(["curl", "-sSfL", "--retry", "5", "-o", str(tmp), url], check=True)
    tmp.rename(dest)


def expr(orig: str) -> pl.Expr:
    col = orig.lower()
    c = pl.col(orig)
    if col == "uf":
        return c.alias("id_uf")
    if col in IDENT:
        return c.alias(col)
    if col in INTEIRO:
        return c.cast(pl.Int64, strict=True).alias(col)
    if col in DECIMAL:
        return c.cast(pl.Float64, strict=True).alias(col)
    # categoria: tira zero a esquerda pelo roundtrip inteiro (strict falha alto
    # se aparecer codigo nao numerico)
    return c.cast(pl.Int64, strict=True).cast(pl.Utf8).alias(col)


def converte(mm: str) -> None:
    zpath = RAW / f"PNAD_COVID_{mm}2020.zip"
    baixa(BASE + f"Dados/PNAD_COVID_{mm}2020.zip", zpath)
    baixa(
        BASE + f"Documentacao/Dicionario_PNAD_COVID_{mm}2020_20220621.xls",
        RAW / f"Dicionario_PNAD_COVID_{mm}2020_20220621.xls",
    )
    with zipfile.ZipFile(zpath) as z:
        (nome,) = z.namelist()
        data = z.read(nome)
    df = pl.read_csv(data, infer_schema=False, encoding="utf8")
    extra = set(df.columns) - set(COLUNAS)
    assert not extra, f"{mm}: colunas fora do esquema de nov: {extra}"
    df = df.with_columns(
        [pl.lit(None, pl.Utf8).alias(c) for c in COLUNAS if c not in df.columns]
    ).with_columns(pl.col(pl.Utf8).replace("", None))

    out = df.select([expr(c) for c in COLUNAS])
    assert out["v1013"].unique().to_list() == [int(mm)], f"{mm}: v1013 diverge do arquivo"
    assert out["id_uf"].is_in(list(UFS)).all(), f"{mm}: UF fora da lista"
    out = out.with_columns(
        pl.col("v1013").alias("mes"),
        pl.col("id_uf").replace_strict(UFS).alias("sigla_uf"),
        (pl.col("upa") + pl.col("v1008")).alias("id_domicilio"),
    )
    frente = ["ano", "mes", "sigla_uf", "id_uf", "id_domicilio"]
    out = out.select(frente + [c for c in out.columns if c not in frente])

    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / f"microdados_2020_{mm}.parquet"
    tmp = dest.with_suffix(".parquet.tmp")
    out.write_parquet(tmp, compression="zstd", compression_level=9)
    tmp.rename(dest)
    peso = out["v1032"].sum()
    print(f"2020-{mm}: {out.height:,} linhas, {out.width} colunas, soma v1032 = {peso:,.0f}")


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    for mm in MESES:
        converte(mm)


if __name__ == "__main__":
    main()
