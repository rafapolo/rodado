#!/usr/bin/env python3
"""Converte o zip 'hidro-dados-estacoes-convencionais' da ANA em parquets unificados
no beelink.

Fonte (zip já extraído):
  ~/ana_zip/extraido/hidro-dados-estacoes-convencionais-b8b65b0/
   - Inventario_Estacoes_Hidrologicas_04-08-2023.csv  (inventário completo)
   - fluviometricas/csv/<codigo>/{codigo}_vazoes.csv   (séries mensais de vazão)
   - fluviometricas/csv/<codigo>/{codigo}_cotas.csv    (séries mensais de cota)

Cada linha dos CSVs = 1 mês; colunas: EstacaoCodigo;NivelConsistencia;Data(MM/YYYY);
MediaDiaria;Maxima;Minima;Media;... + Vazao01..31 (diárias) com seus Status.

Saídas (beelink, padrão do catálogo):
  ~/rodado/br_ana_telemetria/inventario/          inventario.parquet
  ~/rodado/br_ana_telemetria/series_vazao_mensal/  vazao_mensal.parquet
  ~/rodado/br_ana_telemetria/series_cota_mensal/   cota_mensal.parquet

Granularidade das séries: MENSAAL (é o que alimenta a análise de tendência).
"""
import sys
from pathlib import Path

import polars as pl

HOME = Path.home()
RAIZ = HOME / "ana_zip" / "extraido" / "hidro-dados-estacoes-convencionais-b8b65b0"
SAIDA = HOME / "rodado" / "br_ana_telemetria"
INVENTARIO_CSV = RAIZ / "Inventario_Estacoes_Hidrologicas_04-08-2023.csv"
FLUV_CSV = RAIZ / "fluviometricas" / "csv"


def carrega_inventario():
    inv = pl.read_csv(
        INVENTARIO_CSV,
        separator=";",
        encoding="utf8-lossy",
        ignore_errors=True,
    )
    for c in inv.columns:
        key = c.strip().strip("\ufeff").lower().replace(" ", "_")
        if key != c:
            inv = inv.rename({c: key})
    return inv


def le_mensal(caminho, tipo):
    pref = {"vazoes": "Vazao", "cotas": "Cota"}[tipo]
    try:
        df = pl.read_csv(
            caminho,
            separator=";",
            encoding="utf8-lossy",
            ignore_errors=True,
        )
    except Exception:
        return None
    if df.height == 0 or "Data" not in df.columns:
        return None
    base = df.select(
        pl.col("EstacaoCodigo").cast(pl.Utf8).alias("codigo"),
        pl.col("NivelConsistencia").cast(pl.Int8, strict=False).alias("nivel_consistencia"),
        pl.col("Data").str.to_date("%m/%Y", strict=False).alias("mes"),
        pl.col("Maxima").cast(pl.Float64, strict=False).alias("maxima"),
        pl.col("Minima").cast(pl.Float64, strict=False).alias("minima"),
        pl.col("Media").cast(pl.Float64, strict=False).alias("media"),
    )
    return base


def main():
    if not FLUV_CSV.is_dir():
        sys.exit(f"pasta não encontrada: {FLUV_CSV}")

    # --- inventário ---
    inv = carrega_inventario()
    saida_inv = SAIDA / "inventario"
    saida_inv.mkdir(parents=True, exist_ok=True)
    inv.write_parquet(saida_inv / "inventario.parquet", compression="zstd")
    print(f"inventario: {inv.height} estações")

    # --- séries mensais ---
    partes = {"vazoes": [], "cotas": []}
    n = 0
    for d in sorted(FLUV_CSV.iterdir()):
        if not d.is_dir() or not d.name.isdigit():
            continue
        cod = d.name
        for tipo in ("vazoes", "cotas"):
            p = d / f"{cod}_{tipo}.csv"
            if p.is_file():
                df = le_mensal(p, tipo)
                if df is not None:
                    partes[tipo].append(df)
        n += 1
        if n % 1000 == 0:
            print(f"  {n} estações lidas", flush=True)

    for tipo in ("vazoes", "cotas"):
        if not partes[tipo]:
            continue
        todo = pl.concat(partes[tipo])
        todo = (
            todo.sort(["codigo", "mes", "nivel_consistencia"])
            .unique(subset=["codigo", "mes"], keep="first")
            .sort(["codigo", "mes"])
        )
        pasta = SAIDA / f"series_{tipo}_mensal"
        pasta.mkdir(parents=True, exist_ok=True)
        todo.write_parquet(pasta / f"{tipo}_mensal.parquet", compression="zstd")
        print(
            f"{tipo}: {todo.height:,} linhas, {todo['codigo'].n_unique()} estações, "
            f"{str(todo['mes'].min())[:7]}..{str(todo['mes'].max())[:7]}"
        )
    print("OK")


if __name__ == "__main__":
    main()