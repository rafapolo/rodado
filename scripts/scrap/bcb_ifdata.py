#!/usr/bin/env python3
"""
BCB IF.data (Olinda OData) -> Parquet -> beelink:~/rodado/br_bcb_ifdata/{relatorio,cadastro}/

`br_bcb_ifdata` already holds `instituicao`, `coluna` and `dicionario` mirrored
from Base dos Dados; the values table (`relatorio`) never came over because it
was above the BigQuery pull ceiling. This pulls it straight from the BCB.

  relatorio  -- every value of every IF.data report, long format:
                one row per (ano_mes, tipo_instituicao, cod_inst, numero_relatorio, grupo, conta)
  cadastro   -- the IF.data registry per quarter, keyed by the SAME cod_inst the
                values use (C0080099, 8-digit CNPJ). The BD `instituicao` table
                recodes those (C0080099 -> 1000080099, CNPJ without leading zeros),
                so it does not join to `relatorio` directly.

API: https://olinda.bcb.gov.br/olinda/servico/IFDATA/versao/v1/odata
  IfDataValores(AnoMes=@AnoMes,TipoInstituicao=@TipoInstituicao,Relatorio=@Relatorio)
      ?@AnoMes=202412&@TipoInstituicao=1&@Relatorio='T'&$format=json
  IfDataCadastro(AnoMes=@AnoMes)?@AnoMes=202412&$format=json
  ListaDeRelatorio()
Relatorio='T' returns all reports in one call. No auth, no pagination needed
(largest single response ~150 MB / ~470k rows, ~60 s).

TipoInstituicao: 1 = conglomerados prudenciais e instituições independentes
(from 2014-03), 2 = conglomerados financeiros e instituições independentes,
3 = instituições individuais, 4 = instituições com operações de câmbio.

Gotchas:
  * saldo is in BRL (not thousands) for money columns, but some columns are
    ratios/indices/counts (Índice de Basileia, quantidade de clientes...).
  * The same `conta` shows up in several reports (e.g. Ativo Total in Resumo
    and in Ativo): never SUM(saldo) without filtering numero_relatorio.
  * Sum across tipo_instituicao double-counts (same institutions, different
    consolidation). Pick one tipo.
  * `conta` codes and column names change between quarters (a new layout from
    2025-09 with the Res. CMN 4.966 COSIF). Filter by conta *within* a quarter.
  * Coverage (measured 2026-09-25): 200003..202606, 106 quarters. tipo 1 from
    2014-03, tipo 4 (only report 15, câmbio) from 2014-12; credit reports 7-14
    from 2014-06, report 16 from 2025-03.
  * The API repeats rows (202509 came back ~3x): exact duplicates are dropped.
  * 6,103 rows (200003-202109, tipo 2) have cod_inst NULL at the source; they are
    kept, and they are the only rows where the natural key repeats.

Usage: python3 scripts/scrap/bcb_ifdata.py [first_anomes] [last_anomes]
"""

import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import polars as pl

BEELINK_HOST = os.environ.get("BEELINK_HOST", "beelink")
BEELINK_BASE = "~/rodado/br_bcb_ifdata"
TEMP_DIR = Path(os.environ.get("RODADO_TMP", "/tmp")) / "bcb_ifdata"
BASE = "https://olinda.bcb.gov.br/olinda/servico/IFDATA/versao/v1/odata"

VAL_SCHEMA = {
    "TipoInstituicao": pl.Int8, "CodInst": pl.Utf8, "AnoMes": pl.Utf8, "NomeRelatorio": pl.Utf8,
    "NumeroRelatorio": pl.Utf8, "Grupo": pl.Utf8, "Conta": pl.Utf8, "NomeColuna": pl.Utf8,
    "DescricaoColuna": pl.Utf8, "Saldo": pl.Float64,
}
CAD_SCHEMA = {
    "CodInst": pl.Utf8, "Data": pl.Utf8, "NomeInstituicao": pl.Utf8, "DataInicioAtividade": pl.Int32,
    "Tcb": pl.Utf8, "Td": pl.Utf8, "Tc": pl.Int32, "SegmentoTb": pl.Utf8, "Atividade": pl.Utf8,
    "Uf": pl.Utf8, "Municipio": pl.Utf8, "Sr": pl.Utf8, "CodConglomeradoFinanceiro": pl.Utf8,
    "CodConglomeradoPrudencial": pl.Utf8, "CnpjInstituicaoLider": pl.Utf8, "Situacao": pl.Utf8,
}


def snake(s: str) -> str:
    out = ""
    for i, c in enumerate(s):
        if c.isupper() and i and not s[i - 1].isupper():
            out += "_"
        out += c.lower()
    return out


def get(path: str, params: dict) -> list[dict]:
    qs = "&".join(f"{k}={urllib.parse.quote(str(v), safe=chr(39))}" for k, v in params.items())
    url = f"{BASE}/{path}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": "rodado-scraper"})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                return json.loads(r.read())["value"]
        except Exception as e:
            print(f"   retry {attempt + 1}: {e}", flush=True)
            time.sleep(5 * 2 ** attempt)
    raise RuntimeError(f"giving up: {url}")


def quarters(first: int, last: int):
    y, m = divmod(first, 100)
    while y * 100 + m <= last:
        yield y * 100 + m
        m += 3
        if m > 12:
            m, y = 3, y + 1


def push(p: Path, table: str):
    dest = f"{BEELINK_BASE}/{table}"
    subprocess.run(["ssh", BEELINK_HOST, f"mkdir -p {dest}"], check=True)
    subprocess.run(["rsync", "-a", str(p), f"{BEELINK_HOST}:{dest}/{p.name}"], check=True)


def add_period(df: pl.DataFrame, am: int) -> pl.DataFrame:
    return df.with_columns(pl.lit(am, pl.Int32).alias("ano_mes"),
                           pl.lit(am // 100, pl.Int16).alias("ano"),
                           pl.lit(am % 100, pl.Int8).alias("mes"))


def do_quarter(am: int) -> tuple[int, int]:
    rel_p = TEMP_DIR / "relatorio" / f"{am}.parquet"
    cad_p = TEMP_DIR / "cadastro" / f"{am}.parquet"
    n_rel = n_cad = 0
    if not rel_p.exists():
        frames = []
        for tipo in (1, 2, 3, 4):
            v = get("IfDataValores(AnoMes=@AnoMes,TipoInstituicao=@TipoInstituicao,Relatorio=@Relatorio)",
                    {"@AnoMes": am, "@TipoInstituicao": tipo, "@Relatorio": "'T'", "$format": "json"})
            print(f"  {am} tipo {tipo}: {len(v)}", flush=True)
            if v:
                frames.append(pl.DataFrame(v, schema=VAL_SCHEMA))
            del v
            time.sleep(1)
        if not frames:
            return 0, 0
        d = pl.concat(frames)
        assert (d["AnoMes"] == str(am)).all(), f"{am}: AnoMes mismatch"
        n0 = d.height
        d = d.unique(maintain_order=True)
        key = ["TipoInstituicao", "CodInst", "NumeroRelatorio", "Grupo", "Conta"]
        kd = d.height - d.select(key).unique().height
        if n0 != d.height or kd:
            print(f"  {am}: dropped {n0 - d.height} exact dups; {kd} key dups remain", flush=True)
        d = d.drop("AnoMes").rename({c: snake(c) for c in d.columns if c != "AnoMes"})
        d = d.with_columns(pl.col("numero_relatorio").cast(pl.Int8))
        d = add_period(d, am).select(
            "ano_mes", "ano", "mes", "tipo_instituicao", "cod_inst", "numero_relatorio", "nome_relatorio",
            "grupo", "conta", "nome_coluna", "descricao_coluna", "saldo")
        rel_p.parent.mkdir(parents=True, exist_ok=True)
        d.write_parquet(rel_p, compression="zstd")
        n_rel = d.height
        push(rel_p, "relatorio")
    if not cad_p.exists():
        v = get("IfDataCadastro(AnoMes=@AnoMes)", {"@AnoMes": am, "$format": "json"})
        if v:
            c = pl.DataFrame(v, schema=CAD_SCHEMA)
            c = c.drop("Data").rename({k: snake(k) for k in c.columns if k != "Data"})
            c = c.rename({"uf": "sigla_uf"})
            c = add_period(c, am).unique(maintain_order=True)
            c = c.select("ano_mes", "ano", "mes", *[x for x in c.columns if x not in ("ano_mes", "ano", "mes")])
            cad_p.parent.mkdir(parents=True, exist_ok=True)
            c.write_parquet(cad_p, compression="zstd")
            n_cad = c.height
            push(cad_p, "cadastro")
    return n_rel, n_cad


def main():
    today = date.today()
    first = int(sys.argv[1]) if len(sys.argv) > 1 else 200003
    last = int(sys.argv[2]) if len(sys.argv) > 2 else today.year * 100 + today.month
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    for am in quarters(first, last):
        t = time.time()
        n_rel, n_cad = do_quarter(am)
        print(f"{am}: relatorio {n_rel} cadastro {n_cad} ({time.time() - t:.0f}s)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
