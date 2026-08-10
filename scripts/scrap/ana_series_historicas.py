#!/usr/bin/env python3
"""
ANA historical series (flow + stage) -> Parquet in the beelink data lake.

Companion to `ana_telemetria.py`, which fetches only the station *catalog*
(`br_ana_telemetria/estacoes`) and explicitly left readings out of scope: the
legacy SOAP service has no bulk "all stations' series" operation, so pulling
readings that way means one call per station.

The bulk escape hatch is a one-off publication by ANA itself. After the
Sep/2023 cyberattack they mirrored the whole conventional-station archive to
GitHub (`anagovbr/hidro-dados-estacoes-convencionais`) as a contingency. Two
things to know about it:

  1. ANA *emptied* the repo HEAD in Dec/2025 ("Delete fluviometricas
     directory" and friends), so a zip of refs/heads/main downloads 0 bytes.
     Commit b8b65b0 still carries everything -- that's the 2.3 GB zip already
     sitting extracted on the beelink.
  2. It's a snapshot dated 04/08/2023. Everything after that is the job of
     `ana_series_gap.py`, which goes back to the SOAP service station by
     station.

This script is the CSV -> Parquet pass. It runs ON the beelink, because the
extracted CSVs are already there and pulling 1.4 GB across the network to push
it back would be pointless.

What the archive actually contains (measured, not from the docs -- ANA's own
`Descricao_Arquivos_Dados.csv` claims the date format is MMM/YY, which is
wrong):

  * 7,205 fluviometric station directories, but only 3,954 hold real rows;
    the rest are header-only stubs of ~858 bytes.
  * Coverage 1901 -> 2023. Mean span per station 30.5 years, median 24.
    2,250 stations clear 20 years, 1,714 clear 30, 900 clear 50, 361 clear 70.
  * Files are plain ASCII, LF line endings, ';' separated, '.' decimal,
    exactly 77 fields, and `Data` is always MM/YYYY. The inventory CSV is the
    one exception: UTF-8 with a BOM and CRLF.

Grain note: each CSV row is one station-month that ALSO carries the 31 daily
readings as columns (Vazao01..Vazao31 + a status flag each). So one input file
feeds both a monthly and a daily output table. The daily one is the point --
the status flags 4/5/6 (regua seca / rio cortado / rio seco) are the only
record of a Brazilian river that stopped running, and they exist nowhere in
the monthly aggregates.

Usage (on the beelink):
    python3 ana_series_historicas.py [--apenas vazao|cota|inventario]
"""

import argparse
import sys
from pathlib import Path

import polars as pl

BASE = Path.home() / "ana_zip/extraido/hidro-dados-estacoes-convencionais-b8b65b0"
FLU = BASE / "fluviometricas/csv"
INVENTARIO = BASE / "Inventario_Estacoes_Hidrologicas_04-08-2023.csv"
OUT = Path.home() / "rodado/br_ana_telemetria"

# Stations per read batch. The daily unpivot turns 31 value columns + 31 status
# columns into 31 rows, so a batch briefly costs ~60x its CSV size in memory.
# 200 stations keeps the peak near 1 GB on a 27 GB box.
LOTE = 200

# Header-only stubs. Real files start well above this; the largest stub seen is
# 858 bytes (the header line alone).
MIN_BYTES = 900

# Two variables, same skeleton, three columns of difference.
VARIAVEIS = {
    "vazao": {
        "sufixo": "vazoes",
        "prefixo": "Vazao",     # Vazao01..Vazao31
        "metodo": "MetodoObtencaoVazoes",  # 1=curva de descarga, 2=transferencia, 3=soma, 4=ADCP
        "unidade": "m3/s",
    },
    "cota": {
        "sufixo": "cotas",
        "prefixo": "Cota",      # Cota01..Cota31
        "metodo": "TipoMedicaoCotas",      # 1=escala, 2=linigrafo, 3=datalogger, 4=SMS
        "unidade": "cm",
    },
}

# Status codes on the daily readings, straight from Descricao_Arquivos_Dados.csv.
# 0 is "branco" -- an absent reading, dropped. 4/5/6 are the dry-river codes and
# are deliberately KEPT with a zero value: they are data, not a gap.
STATUS_VAZIO = 0
STATUS_SECO = (4, 5, 6)  # regua seca, rio cortado, rio seco

COLS_MENSAIS = [
    "EstacaoCodigo",
    "NivelConsistencia",
    "Data",
    "Maxima",
    "Minima",
    "Media",
    "DiaMaxima",
    "DiaMinima",
    "MediaAnual",
]


def arquivos(sufixo: str) -> list[Path]:
    """Station files with actual rows, sorted, stubs skipped."""
    achados = sorted(FLU.glob(f"*/*_{sufixo}.csv"))
    return [p for p in achados if p.stat().st_size >= MIN_BYTES]


def lotes(itens: list, n: int):
    for i in range(0, len(itens), n):
        yield itens[i : i + n]


def le_lote(caminhos: list[Path], prefixo: str, metodo: str) -> pl.DataFrame:
    """Read a batch of station CSVs as all-string columns.

    infer_schema=False matters here. ANA writes flow as '112.196' but also
    '1.0E-2' in a few stations, and empty strings for missing days; letting
    polars guess per batch would produce different dtypes for different
    batches and blow up on concat. Everything is parsed explicitly below.
    """
    dias = [f"{prefixo}{d:02d}" for d in range(1, 32)]
    status = [f"{d}Status" for d in dias]
    # scan_csv, not read_csv: only the lazy reader takes a list of paths.
    return (
        pl.scan_csv(
            caminhos,
            separator=";",
            infer_schema=False,
            encoding="utf8-lossy",
        )
        .select(COLS_MENSAIS + [metodo] + dias + status)
        .collect()
    )


def base_comum(df: pl.DataFrame, metodo: str) -> pl.DataFrame:
    """Parse the identifying columns shared by the monthly and daily outputs."""
    return df.with_columns(
        pl.col("EstacaoCodigo").str.strip_chars().alias("codigo"),
        pl.col("NivelConsistencia").cast(pl.Int8, strict=False).alias("nivel_consistencia"),
        # Always MM/YYYY (verified across the archive); anchored to day 1.
        ("01/" + pl.col("Data")).str.to_date("%d/%m/%Y", strict=False).alias("data"),
        pl.col(metodo).cast(pl.Int8, strict=False).alias("metodo"),
    ).filter(pl.col("data").is_not_null() & pl.col("codigo").is_not_null())


def dedup(df: pl.DataFrame, chaves: list[str]) -> pl.DataFrame:
    """Consisted (2) beats raw (1) for the same key.

    ANA ships both levels for the same month and naively concatenating them
    double-counts every consisted station. `pipeline/processa.py` in
    rios-do-brasil already resolves it this way; same rule here so the two
    pipelines can't disagree about what a station's mean flow is.
    """
    return (
        df.sort("nivel_consistencia", descending=True)
        .unique(subset=chaves, keep="first")
        .sort(chaves)
    )


def mensal(df: pl.DataFrame, unidade: str) -> pl.DataFrame:
    out = df.select(
        "codigo",
        "data",
        "nivel_consistencia",
        "metodo",
        pl.col("Media").cast(pl.Float64, strict=False).alias("media"),
        pl.col("Maxima").cast(pl.Float64, strict=False).alias("maxima"),
        pl.col("Minima").cast(pl.Float64, strict=False).alias("minima"),
        pl.col("DiaMaxima").cast(pl.Int8, strict=False).alias("dia_maxima"),
        pl.col("DiaMinima").cast(pl.Int8, strict=False).alias("dia_minima"),
        pl.col("MediaAnual").cast(pl.Float64, strict=False).alias("media_anual"),
    ).with_columns(pl.lit(unidade).alias("unidade"))
    return dedup(out, ["codigo", "data"])


def diario(df: pl.DataFrame, prefixo: str, unidade: str) -> pl.DataFrame:
    """Unpivot Vazao01..31 / Cota01..31 into one row per station-day.

    Values and status flags are unpivoted separately and rejoined on the day
    number, since polars has no two-column unpivot.
    """
    dias = [f"{prefixo}{d:02d}" for d in range(1, 32)]
    idx = ["codigo", "data", "nivel_consistencia"]
    corte = len(prefixo)

    valores = (
        df.select(idx + dias)
        .unpivot(index=idx, on=dias, variable_name="col", value_name="valor")
        .with_columns(
            pl.col("col").str.slice(corte, 2).cast(pl.Int8).alias("dia"),
            pl.col("valor").cast(pl.Float64, strict=False),
        )
        .drop("col")
    )
    estados = (
        df.select(idx + [f"{d}Status" for d in dias])
        .unpivot(index=idx, on=[f"{d}Status" for d in dias], variable_name="col", value_name="status")
        .with_columns(
            pl.col("col").str.slice(corte, 2).cast(pl.Int8).alias("dia"),
            pl.col("status").cast(pl.Int8, strict=False),
        )
        .drop("col")
    )

    out = valores.join(estados, on=idx + ["dia"], how="left").with_columns(
        # Day 31 of a 30-day month is padding, not a reading. month_end().day()
        # gives the real length and handles leap years for free.
        pl.col("data").dt.month_end().dt.day().alias("ultimo_dia")
    )
    out = out.filter(pl.col("dia") <= pl.col("ultimo_dia")).drop("ultimo_dia")

    out = out.with_columns(
        # A dry river reads as no value with a 4/5/6 flag. Zero is the physical
        # truth and keeps it out of the "missing data" bucket.
        pl.when(pl.col("valor").is_null() & pl.col("status").is_in(STATUS_SECO))
        .then(pl.lit(0.0))
        .otherwise(pl.col("valor"))
        .alias("valor")
    ).filter(
        pl.col("valor").is_not_null()
        & pl.col("status").is_not_null()
        & (pl.col("status") != STATUS_VAZIO)
    )

    out = out.with_columns(
        pl.date(pl.col("data").dt.year(), pl.col("data").dt.month(), pl.col("dia")).alias("data"),
        pl.lit(unidade).alias("unidade"),
    ).drop("dia")

    return dedup(out, ["codigo", "data"])


def grava(df: pl.DataFrame, tabela: str, parte: int) -> int:
    """Write one part file per basin prefix.

    Partitioning by the leading 2 digits of the station code (ANA's basin) is
    what keeps the daily tables queryable -- undivided they'd be a single
    multi-GB parquet that has to be read whole to answer anything.
    """
    if df.is_empty():
        return 0
    linhas = 0
    for (bacia,), grupo in df.with_columns(
        pl.col("codigo").str.slice(0, 2).alias("_bacia")
    ).group_by(["_bacia"]):
        destino = OUT / tabela / f"bacia={bacia}"
        destino.mkdir(parents=True, exist_ok=True)
        grupo.drop("_bacia").write_parquet(
            destino / f"parte-{parte:04d}.parquet", compression="zstd"
        )
        linhas += len(grupo)
    return linhas


def processa(nome: str, cfg: dict, limite: int | None = None) -> None:
    caminhos = arquivos(cfg["sufixo"])
    if limite:
        caminhos = caminhos[:limite]
    print(f"\n{nome}: {len(caminhos)} estacoes com dados")
    if not caminhos:
        print(f"  nenhum arquivo de {nome} -- nada a fazer")
        return

    total_m = total_d = 0
    for i, lote in enumerate(lotes(caminhos, LOTE)):
        bruto = le_lote(lote, cfg["prefixo"], cfg["metodo"])
        comum = base_comum(bruto, cfg["metodo"])
        total_m += grava(mensal(comum, cfg["unidade"]), f"series_{nome}_mensal", i)
        total_d += grava(diario(comum, cfg["prefixo"], cfg["unidade"]), f"series_{nome}_diaria", i)
        print(
            f"  lote {i + 1}/{-(-len(caminhos) // LOTE)}: "
            f"{total_m:,} meses / {total_d:,} dias",
            flush=True,
        )

    print(f"  {nome}: {total_m:,} linhas mensais, {total_d:,} linhas diarias")


def processa_inventario() -> None:
    """The 04/08/2023 inventory that ships with the archive.

    Kept separate from `estacoes` (the SOAP catalog) rather than merged: this
    one is contemporaneous with the series and its TipoEstacao is text
    ('FLU'/'PLU') where the SOAP one is 1/2, and it carries BaciaNome and
    SubBaciaNome, which the SOAP payload only gives as codes.
    """
    if not INVENTARIO.exists():
        print(f"\ninventario nao encontrado em {INVENTARIO}")
        return
    df = pl.read_csv(INVENTARIO, separator=";", infer_schema=False, encoding="utf8-lossy")
    df = df.rename({c: c.lstrip("﻿") for c in df.columns}).with_columns(
        pl.col("Latitude").cast(pl.Float64, strict=False),
        pl.col("Longitude").cast(pl.Float64, strict=False),
        pl.col("Altitude").cast(pl.Float64, strict=False),
        pl.col("AreaDrenagem").cast(pl.Float64, strict=False),
    )
    destino = OUT / "estacoes_inventario_2023"
    destino.mkdir(parents=True, exist_ok=True)
    df.write_parquet(destino / "inventario.parquet", compression="zstd")
    print(f"\ninventario: {len(df):,} linhas, {len(df.columns)} colunas")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apenas", choices=["vazao", "cota", "inventario"])
    ap.add_argument("--limite", type=int, help="so as N primeiras estacoes (teste)")
    args = ap.parse_args()

    if not FLU.exists():
        print(f"arquivo extraido nao encontrado em {FLU}", file=sys.stderr)
        print("rode este script no beelink -- os CSVs estao la", file=sys.stderr)
        return 1

    if args.apenas in (None, "inventario"):
        processa_inventario()
    for nome, cfg in VARIAVEIS.items():
        if args.apenas in (None, nome):
            processa(nome, cfg, args.limite)

    print(f"\nescrito em {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
