#!/usr/bin/env python3
"""Baixa séries mensais de vazão da ANA via SOAP HidroSerieHistorica, com
checkpoint resumível. Roda em qualquer host (beelink/finland/livre) sobre a lista
de códigos; cada linha = 1 estação. Escreve parquets brutos por batch.

Uso:
  python3 ana_soap_worker.py estacoes.csv shard/ 16        # 16 threads
        arquivo: lista CSV com coluna 'codigo'
        saida:  diretório que recebe 'batch_XXX.parquet'
        threads: nº
"""
import argparse
import random
import threading
import time
import xml.etree.ElementTree as ET
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import polars as pl

URL = "http://telemetriaws1.ana.gov.br/ServiceANA.asmx"

# Schema explícito, e não inferido. `pl.DataFrame(lista_de_dicts)` adivinha os
# tipos pelas primeiras 100 linhas: numa estação cujos primeiros meses não
# trazem Maxima/Minima, a coluna era inferida como Null e o primeiro float mais
# adiante estourava
#   ComputeError: could not append value: 3.1254 of type: f64 to the builder
# Pior que o erro: ele sobe do laço principal enquanto o ThreadPoolExecutor
# segue drenando as futures, então o processo continua vivo sem gravar mais
# nenhum lote — uma corrida parou de progredir em 2.500 de 6.203 e parecia
# saudável no `ps`.
ESQUEMA = {
    "codigo": pl.Utf8,
    "mes": pl.Utf8,
    "nivel_consistencia": pl.Int8,
    "vazao_media": pl.Float64,
    "vazao_maxima": pl.Float64,
    "vazao_minima": pl.Float64,
}
BODY = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
 <soap:Body><HidroSerieHistorica xmlns="http://MRCS/">
  <codEstacao>{cod}</codEstacao><dataInicio>01/01/1960</dataInicio>
  <dataFim>31/12/2026</dataFim><tipoDados>3</tipoDados><nivelConsistencia></nivelConsistencia>
 </HidroSerieHistorica></soap:Body></soap:Envelope>"""


# O serviço da ANA devolve **HTTP 429** sob concorrência. Sem backoff, as
# tentativas queimavam em menos de 2 s e a estação era descartada: uma corrida
# com 16 threads passou 6 minutos sem gravar um único lote, porque quase tudo
# voltava 429 e virava "falhou, tenta na próxima execução".
#
# Duas defesas. Backoff exponencial com jitter por tentativa, e um freio
# global: quando alguém leva 429, todas as threads esperam até `_ate`. Sem o
# freio compartilhado as threads se revezam batendo no limite e o 429 nunca
# passa.
_freio = threading.Lock()
_ate = 0.0


def _respira(segundos):
    global _ate
    with _freio:
        _ate = max(_ate, time.time() + segundos)


def _espera_freio():
    while True:
        with _freio:
            falta = _ate - time.time()
        if falta <= 0:
            return
        time.sleep(min(falta, 5))


def soap_estacao(cod, tentativas=6):
    for i in range(tentativas):
        _espera_freio()
        try:
            req = urllib.request.Request(
                URL, data=BODY.format(cod=cod).encode(),
                headers={"Content-Type": "text/xml; charset=utf-8",
                         "SOAPAction": "http://MRCS/HidroSerieHistorica"})
            resp = urllib.request.urlopen(req, timeout=180).read()
            return parse(resp, cod)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                espera = min(60, 2 ** i) + random.uniform(0, 2)
                _respira(espera)
                time.sleep(espera)
                continue
            if i == tentativas - 1:
                return None
            time.sleep(1 + random.uniform(0, 1))
        except Exception:
            if i == tentativas - 1:
                return None
            time.sleep(1 + random.uniform(0, 1))
    return None


def parse(resp, cod):
    root = ET.fromstring(resp)
    meses = {}
    for el in root.iter():
        if el.tag.rsplit("}", 1)[-1] != "SerieHistorica":
            continue
        rec = {c.tag.rsplit("}", 1)[-1]: c.text for c in el}
        data, media = (rec.get("DataHora") or "")[:7], rec.get("Media")
        if not data or media is None:
            continue
        nivel = int(rec.get("NivelConsistencia") or 1)
        if data in meses and meses[data][0] >= nivel:
            continue
        try:
            meses[data] = (nivel, float(media),
                           float(rec["Maxima"]) if rec.get("Maxima") else None,
                           float(rec["Minima"]) if rec.get("Minima") else None)
        except ValueError:
            continue
    return [{"codigo": cod, "mes": m, "nivel_consistencia": v[0], "vazao_media": v[1],
             "vazao_maxima": v[2], "vazao_minima": v[3]} for m, v in sorted(meses.items())]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lista")
    ap.add_argument("saida")
    ap.add_argument("threads", type=int, default=16)
    a = ap.parse_args()

    cods = pl.read_csv(a.lista, infer_schema_length=1000)["codigo"].cast(pl.Utf8).to_list()
    out = Path(a.saida)
    out.mkdir(parents=True, exist_ok=True)
    ja = set()
    for p in out.glob("batch_*.parquet"):
        for c in pl.read_parquet(p)["codigo"].to_list():
            ja.add(c)
    faltam = [c for c in cods if c not in ja]
    print(f"{len(cods)} estações; {len(ja)} já; {len(faltam)} a baixar", flush=True)
    t0 = time.time()
    # Identificador da corrida no nome do lote. Sem ele o contador `done`
    # reinicia do zero a cada execução e a segunda corrida grava
    # batch_000100.parquet por cima da primeira — os códigos daquele lote já
    # estavam no checkpoint, então sumiriam sem nenhum aviso. Com o id, um
    # retomar nunca pisa no que já foi salvo.
    corrida = time.strftime("%Y%m%d%H%M%S")

    batch = []
    done = 0   # conta tentativas concluídas (para nome do batch)
    ok = 0
    with ThreadPoolExecutor(max_workers=a.threads) as pool:
        futs = {pool.submit(soap_estacao, c): c for c in faltam}
        for fut in as_completed(futs):
            c = futs[fut]
            try:
                rows = fut.result()
            except Exception:
                rows = None
            if rows is None:  # falha em todas as tentativas -> re-baixa na próxima execução
                continue
            done += 1
            # Uma estação malformada não pode derrubar a coleta inteira: sem
            # este try, a exceção mata o laço e o processo fica drenando
            # futures sem gravar nada.
            try:
                if rows:
                    batch.append(pl.DataFrame(rows, schema=ESQUEMA))
                    ok += 1
                else:
                    # estação viva mas sem dados: gravar só o código, para não repetir
                    batch.append(pl.DataFrame({"codigo": [c]}, schema={"codigo": pl.Utf8}))
            except Exception as e:
                print(f"  ! estação {c} descartada: {e}", flush=True)
                continue
            # 100 e não 400: sob rate limit da ANA um lote de 400 leva muitos
            # minutos, e é trabalho que se perde se o processo cair.
            if len(batch) >= 100:
                pl.concat(batch, how="diagonal_relaxed").write_parquet(
                    out / f"batch_{corrida}_{done:06d}.parquet", compression="zstd")
                batch = []
                taxa = done / max(1e-9, time.time() - t0)
                falta = (len(faltam) - done) / taxa / 60 if taxa else 0
                print(f"  {done}/{len(faltam)} estações, {ok} com dados, "
                      f"{taxa * 60:.0f}/min, ~{falta:.0f} min restantes", flush=True)
    if batch:
        pl.concat(batch, how="diagonal_relaxed").write_parquet(
            out / f"batch_{corrida}_{done:06d}.parquet", compression="zstd")
    print("fim, ok=", ok)


if __name__ == "__main__":
    main()