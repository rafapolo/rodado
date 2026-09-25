#!/usr/bin/env python3
"""
BCB PTAX (Olinda OData) -> Parquet -> beelink:~/rodado/br_bcb_ptax/

Tables:
  moedas              -- the currencies the Olinda PTAX service exposes (10)
  cotacao_dolar_dia   -- PTAX USD/BRL, one row per day (the closing PTAX)
  cotacao_moeda_dia   -- every bulletin (Abertura / Intermediário / Fechamento)
                         of every currency in `moedas`, incl. USD

API: https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata
  Moedas
  CotacaoDolarPeriodo(dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)
  CotacaoMoedaPeriodo(moeda=@moeda,dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)
Dates are 'MM-DD-YYYY'. No auth. Pulled one calendar year per call.

Gotchas:
  * Olinda only knows 10 currencies (AUD CAD CHF DKK EUR GBP JPY NOK SEK USD);
    ARS, CNY etc. return [] -- the ~150-currency boletim lives only in the CSV
    files of www4.bcb.gov.br/Download/fechamento/, not in this API.
  * Values are in the Brazilian currency *of the day* (cruzeiro, cruzado,
    cruzado novo, cruzeiro real...) -- no conversion to BRL before 1994-07-01.
  * History starts 1984-11-29 (EUR 1998-12-31); the USD daily PTAX from 1984-12-03.
  * tipo_boletim: Abertura / Intermediário / Fechamento, plus a 4th type
    "Fechamento Interbancário" (from 1999-10). The PTAX of the day is `Fechamento`.
  * 9 days (mostly 1984-85) carry two USD closing records; cotacao_dolar_dia
    keeps the later one, cotacao_moeda_dia keeps both (8 dates x currency).
  * The run day itself is partial (bulletins published so far).
  * paridade = units of currency per USD (tipo_moeda A) or USD per unit (B).
  * dataHoraCotacao is a string 'YYYY-MM-DD HH:MM:SS.fff' in Brasília time.

Usage: python3 scripts/scrap/bcb_ptax.py
"""

import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import date
from decimal import Decimal
from pathlib import Path

import polars as pl

BEELINK_HOST = os.environ.get("BEELINK_HOST", "beelink")
BEELINK_BASE = "~/rodado/br_bcb_ptax"
TEMP_DIR = Path(os.environ.get("RODADO_TMP", "/tmp")) / "bcb_ptax"
BASE = "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata"
FIRST_YEAR = 1984
TOP = 100000
DEC = pl.Decimal(20, 5)


def get(path: str, params: dict) -> list[dict]:
    qs = "&".join(f"{k}={urllib.parse.quote(str(v), safe=chr(39) + '-')}" for k, v in params.items())
    url = f"{BASE}/{path}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": "rodado-scraper"})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                vals = json.loads(r.read(), parse_float=Decimal)["value"]
            if len(vals) >= TOP:
                raise RuntimeError(f"hit $top={TOP} on {url}")
            return vals
        except RuntimeError:
            raise
        except Exception as e:
            print(f"   retry {attempt + 1}: {e}", flush=True)
            time.sleep(2 ** attempt)
    raise RuntimeError(f"giving up: {url}")


def years():
    return range(FIRST_YEAR, date.today().year + 1)


def period(y):
    return f"'01-01-{y}'", f"'12-31-{y}'"


def parse_ts(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
        pl.col("data_hora_cotacao").str.to_datetime("%Y-%m-%d %H:%M:%S%.f", strict=True)
    ).with_columns(pl.col("data_hora_cotacao").dt.date().alias("data"))


def main():
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    out = {}

    moedas = get("Moedas", {"$format": "json", "$top": TOP})
    out["moedas"] = pl.DataFrame(moedas).rename(
        {"simbolo": "simbolo", "nomeFormatado": "nome_formatado", "tipoMoeda": "tipo_moeda"}
    )
    print("moedas:", out["moedas"].height)

    rows = []
    for y in years():
        a, b = period(y)
        v = get("CotacaoDolarPeriodo(dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)",
                {"@dataInicial": a, "@dataFinalCotacao": b, "$format": "json", "$top": TOP})
        rows += v
        print(f"USD {y}: {len(v)}", flush=True)
        time.sleep(0.3)
    d = pl.DataFrame(rows, schema={"cotacaoCompra": DEC, "cotacaoVenda": DEC, "dataHoraCotacao": pl.Utf8})
    d = d.rename({"cotacaoCompra": "cotacao_compra", "cotacaoVenda": "cotacao_venda",
                  "dataHoraCotacao": "data_hora_cotacao"})
    d = parse_ts(d).unique().sort("data_hora_cotacao")
    n0 = d.height
    # a handful of days (e.g. 1984-12-03) carry 2 records; the later one is the closing PTAX
    d = d.unique(subset="data", keep="last", maintain_order=True)
    print(f"cotacao_dolar_dia: {n0 - d.height} extra same-day records dropped (kept the latest)")
    out["cotacao_dolar_dia"] = d.select("data", "cotacao_compra", "cotacao_venda", "data_hora_cotacao")

    rows = []
    for m in out["moedas"]["simbolo"].to_list():
        for y in years():
            a, b = period(y)
            v = get("CotacaoMoedaPeriodo(moeda=@moeda,dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)",
                    {"@moeda": f"'{m}'", "@dataInicial": a, "@dataFinalCotacao": b, "$format": "json", "$top": TOP})
            for r in v:
                r["moeda"] = m
            rows += v
            if v:
                print(f"{m} {y}: {len(v)}", flush=True)
            time.sleep(0.3)
    sch = {"paridadeCompra": DEC, "paridadeVenda": DEC, "cotacaoCompra": DEC, "cotacaoVenda": DEC,
           "dataHoraCotacao": pl.Utf8, "tipoBoletim": pl.Utf8, "moeda": pl.Utf8}
    d = pl.DataFrame(rows, schema=sch).rename({
        "paridadeCompra": "paridade_compra", "paridadeVenda": "paridade_venda",
        "cotacaoCompra": "cotacao_compra", "cotacaoVenda": "cotacao_venda",
        "dataHoraCotacao": "data_hora_cotacao", "tipoBoletim": "tipo_boletim"})
    n0 = d.height
    d = parse_ts(d).unique().sort("moeda", "data_hora_cotacao")
    print(f"cotacao_moeda_dia: dropped {n0 - d.height} exact duplicate rows")
    out["cotacao_moeda_dia"] = d.select("moeda", "data", "tipo_boletim", "paridade_compra", "paridade_venda",
                                        "cotacao_compra", "cotacao_venda", "data_hora_cotacao")

    for name, df in out.items():
        p = TEMP_DIR / f"{name}.parquet"
        df.write_parquet(p, compression="zstd")
        print(f"{name}: {df.height} rows -> {p}")
        dest = f"{BEELINK_BASE}/{name}"
        subprocess.run(["ssh", BEELINK_HOST, f"mkdir -p {dest}"], check=True)
        subprocess.run(["rsync", "-a", str(p), f"{BEELINK_HOST}:{dest}/{name}.parquet"], check=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
