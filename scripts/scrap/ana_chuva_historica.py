#!/usr/bin/env python3
"""Chuva diária e mensal das estações pluviométricas da ANA -> Parquet.

Terceira e última perna do arquivo histórico da ANA, depois de
`ana_series_historicas.py` (vazão e cota) e `ana_soap_worker.py` (o gap
recente). É a que responde a pergunta que as outras duas não alcançam:
**é seca ou é consumo?** Vazão caindo com chuva estável é uso do solo e
retirada de água; vazão caindo junto com a chuva é clima. Sem a chuva, a
análise de tendência descreve o sintoma e não distingue a causa.

Fonte: `pluviometricas/mdb/<codigo>.zip` no zip histórico já extraído no
beelink — 5.525 arquivos, um banco Access por estação, 1,1 GB comprimidos.

## As três armadilhas deste formato

1. **mdbtools sem root.** O beelink não dá sudo. Instalado em `~/local/root`
   com `apt-get download mdbtools libmdb3t64 libmdbsql3t64` + `dpkg -x`, que
   não precisam de privilégio nenhum. Daí o PATH e o LD_LIBRARY_PATH abaixo.

2. **A data.** `Data` é DateTime no schema, mas o mdb-export imprime
   `07/01/62 00:00:00` por padrão — mês/dia/ano com ano de DOIS dígitos. Ler
   isso como texto faria julho de 1962 virar 7 de janeiro, e o século sairia
   por chute. `-D` não resolve: só vale para data pura. O flag certo para
   coluna com hora é **`-T`**, e com ele sai `1962-07-01`, século resolvido a
   partir do binário. Este é o tipo de erro que não levanta exceção — só
   produz uma série deslocada que parece plausível.

3. **O grão.** Como nas fluviométricas, cada linha é um mês que carrega os 31
   dias como colunas (`Chuva01..31` + status). Uma passada alimenta as duas
   tabelas.

Saída, no padrão das outras:
    ~/rodado/br_ana_telemetria/series_chuva_mensal/bacia=XX/
    ~/rodado/br_ana_telemetria/series_chuva_diaria/bacia=XX/

Uso (no beelink):
    python3 ana_chuva_historica.py [--limite N] [--processos 8]
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import polars as pl

BASE = Path.home() / "ana_zip/extraido/hidro-dados-estacoes-convencionais-b8b65b0"
PLU = BASE / "pluviometricas/mdb"
OUT = Path.home() / "rodado/br_ana_telemetria"

# mdbtools desempacotado no home (ver armadilha 1 no cabeçalho).
LOCAL = Path.home() / "local/root"
MDB_EXPORT = LOCAL / "usr/bin/mdb-export"
ENV = {**os.environ, "LD_LIBRARY_PATH": str(LOCAL / "usr/lib/x86_64-linux-gnu")}

LOTE = 250          # estações por lote de escrita
STATUS_VAZIO = 0    # 0 = branco: ausência de leitura, não zero de chuva

COLS_MENSAIS = [
    "EstacaoCodigo", "NivelConsistencia", "Data", "TipoMedicaoChuvas",
    "Maxima", "Total", "DiaMaxima", "NumDiasDeChuva", "TotalAnual",
]
DIAS = [f"Chuva{d:02d}" for d in range(1, 32)]


def le_mdb(caminho_zip: Path) -> pl.DataFrame | None:
    """Um zip -> a tabela Chuvas como DataFrame de strings.

    Roda em processo separado: mdb-export é um subprocesso por estação e o
    gargalo é ele, não o Python.
    """
    tmp = Path(tempfile.mkdtemp(prefix="chuva_"))
    try:
        with zipfile.ZipFile(caminho_zip) as z:
            nomes = [n for n in z.namelist() if n.lower().endswith(".mdb")]
            if not nomes:
                return None
            z.extract(nomes[0], tmp)
            mdb = tmp / nomes[0]

        saida = subprocess.run(
            [str(MDB_EXPORT), "-T", "%Y-%m-%d", "-D", "%Y-%m-%d", str(mdb), "Chuvas"],
            capture_output=True, env=ENV, timeout=300,
        )
        if saida.returncode != 0 or not saida.stdout:
            return None

        df = pl.read_csv(saida.stdout, infer_schema=False, encoding="utf8-lossy")
        if df.height == 0 or "Data" not in df.columns:
            return None
        faltando = [c for c in COLS_MENSAIS + DIAS if c not in df.columns]
        if faltando:
            return None
        return df.select(
            COLS_MENSAIS + DIAS + [f"{d}Status" for d in DIAS]
        )
    except Exception:
        return None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def base_comum(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
        # zfill(8) e não só strip: o MDB guarda o código como NÚMERO e perde o
        # zero à esquerda — sai `1036005` onde o inventário e as séries de
        # vazão têm `01036005`. Sem isto o join com o inventário devolve zero
        # linhas para as estações afetadas, calado, e o painel de chuva sai
        # vazio sem nenhum erro.
        pl.col("EstacaoCodigo").str.strip_chars().str.zfill(8).alias("codigo"),
        pl.col("NivelConsistencia").cast(pl.Int8, strict=False).alias("nivel_consistencia"),
        pl.col("Data").str.to_date("%Y-%m-%d", strict=False).alias("data"),
        pl.col("TipoMedicaoChuvas").cast(pl.Int8, strict=False).alias("tipo_medicao"),
    ).filter(pl.col("data").is_not_null() & pl.col("codigo").is_not_null())


def dedup(df: pl.DataFrame, chaves: list[str]) -> pl.DataFrame:
    """Consistido (2) vence bruto (1). Mesma regra das outras tabelas."""
    return (df.sort("nivel_consistencia", descending=True)
              .unique(subset=chaves, keep="first")
              .sort(chaves))


def mensal(df: pl.DataFrame) -> pl.DataFrame:
    out = df.select(
        "codigo", "data", "nivel_consistencia", "tipo_medicao",
        pl.col("Total").cast(pl.Float64, strict=False).alias("total"),
        pl.col("Maxima").cast(pl.Float64, strict=False).alias("maxima"),
        pl.col("DiaMaxima").cast(pl.Int8, strict=False).alias("dia_maxima"),
        pl.col("NumDiasDeChuva").cast(pl.Int8, strict=False).alias("dias_com_chuva"),
        pl.col("TotalAnual").cast(pl.Float64, strict=False).alias("total_anual"),
    ).with_columns(pl.lit("mm").alias("unidade"))
    return dedup(out, ["codigo", "data"])


def diario(df: pl.DataFrame) -> pl.DataFrame:
    idx = ["codigo", "data", "nivel_consistencia"]
    valores = (
        df.select(idx + DIAS)
        .unpivot(index=idx, on=DIAS, variable_name="col", value_name="chuva")
        .with_columns(pl.col("col").str.slice(5, 2).cast(pl.Int8).alias("dia"),
                      pl.col("chuva").cast(pl.Float64, strict=False))
        .drop("col")
    )
    estados = (
        df.select(idx + [f"{d}Status" for d in DIAS])
        .unpivot(index=idx, on=[f"{d}Status" for d in DIAS],
                 variable_name="col", value_name="status")
        .with_columns(pl.col("col").str.slice(5, 2).cast(pl.Int8).alias("dia"),
                      pl.col("status").cast(pl.Int8, strict=False))
        .drop("col")
    )
    out = (valores.join(estados, on=idx + ["dia"], how="left")
           .with_columns(pl.col("data").dt.month_end().dt.day().alias("ultimo")))
    out = out.filter(pl.col("dia") <= pl.col("ultimo")).drop("ultimo")

    # Zero de chuva é medição ("não choveu"), diferente de ausência. Só o
    # status distingue os dois, então linha sem status válido cai fora.
    out = out.filter(
        pl.col("chuva").is_not_null()
        & pl.col("status").is_not_null()
        & (pl.col("status") != STATUS_VAZIO)
    ).with_columns(
        pl.date(pl.col("data").dt.year(), pl.col("data").dt.month(), pl.col("dia")).alias("data"),
        pl.lit("mm").alias("unidade"),
    ).drop("dia")
    return dedup(out, ["codigo", "data"])


def grava(df: pl.DataFrame, tabela: str, parte: int) -> int:
    if df.is_empty():
        return 0
    n = 0
    for (bacia,), grupo in df.with_columns(
        pl.col("codigo").str.slice(0, 2).alias("_b")
    ).group_by(["_b"]):
        destino = OUT / tabela / f"bacia={bacia}"
        destino.mkdir(parents=True, exist_ok=True)
        grupo.drop("_b").write_parquet(destino / f"parte-{parte:04d}.parquet",
                                       compression="zstd")
        n += len(grupo)
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limite", type=int)
    ap.add_argument("--processos", type=int, default=8)
    a = ap.parse_args()

    if not MDB_EXPORT.exists():
        print(f"mdb-export não encontrado em {MDB_EXPORT}", file=sys.stderr)
        print("instale sem root: apt-get download mdbtools libmdb3t64 libmdbsql3t64 "
              "&& dpkg -x *.deb ~/local/root", file=sys.stderr)
        return 1
    if not PLU.is_dir():
        print(f"pasta pluviométrica não encontrada: {PLU}", file=sys.stderr)
        return 1

    zips = sorted(PLU.glob("*.zip"))
    if a.limite:
        zips = zips[:a.limite]
    print(f"{len(zips)} estações pluviométricas", flush=True)

    parte, lote, tot_m, tot_d, vazias = 0, [], 0, 0, 0
    with ProcessPoolExecutor(max_workers=a.processos) as pool:
        futs = {pool.submit(le_mdb, z): z for z in zips}
        for i, fut in enumerate(as_completed(futs), 1):
            df = fut.result()
            if df is None or df.height == 0:
                vazias += 1
            else:
                lote.append(df)
            if len(lote) >= LOTE or (i == len(zips) and lote):
                comum = base_comum(pl.concat(lote, how="diagonal_relaxed"))
                tot_m += grava(mensal(comum), "series_chuva_mensal", parte)
                tot_d += grava(diario(comum), "series_chuva_diaria", parte)
                parte += 1
                lote = []
                print(f"  {i}/{len(zips)} estações · {tot_m:,} meses · {tot_d:,} dias "
                      f"· {vazias} sem dados", flush=True)

    print(f"\nchuva: {tot_m:,} linhas mensais, {tot_d:,} linhas diárias, "
          f"{vazias} estações sem dados")
    print(f"escrito em {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
