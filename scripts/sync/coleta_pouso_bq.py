#!/usr/bin/env python3
"""Baixa do Base dos Dados, no finland, só as partições que faltam, e deixa no pouso do S3.

    python3 coleta_pouso_bq.py <plano.json>

O beelink depende do Mac para ter internet; o finland não. Este script espera a virada da
cota em UTC e traz cada partição do plano para s3://baseldosdados/_pouso/<dataset>/<tabela>/<p>/,
fechando com um ok.json. Do outro lado, scripts/sync/aplica_pouso_bq.py entra no cron do beelink
e aplica o que encontrar quando estiver online. O disco do finland é pequeno e é o mesmo do
db.rodado.xyz e do compacta.py: cada shard sobe e é apagado assim que fica pronto, e a coleta
espera quando sobra pouco, em vez de competir.

O que falta é decidido aqui, depois da contagem exata no BigQuery:
  - partição que o disco não tem entra;
  - partição do disco entra só se cresceu mais de MIN_CRESCIMENTO: reprocessamento de ±2 linhas
    num ano antigo, ou ano que encolheu na fonte, não vale reler a partição inteira;
  - tabela `so_ultimo` (retrato completo por data, CNO e CAFIR) traz só o retrato mais novo.

Retoma sozinho: a partição com ok.json no pouso é pulada. Para ao fim com _pouso/FIM.json.
Precisa de GOOGLE_APPLICATION_CREDENTIALS e de S3_KEY/S3_SECRET no ambiente.
"""
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bq_quota  # noqa: E402
from atualiza_particoes_bq import conforma, literal, tipo_arrow  # noqa: E402
from ressincroniza_bq import BILLING_PROJECT, BQ_PROJECT, escreve_shards, exige_sandbox  # noqa: E402

BUCKET = "s3://baseldosdados/_pouso"
ENDPOINT = "https://hel1.your-objectstorage.com"
MES = os.environ.get("POUSO_MES", "2026-11")
MIN_CRESCIMENTO = 1.01
MIN_LIVRE_GB = 3
ENV = {**os.environ, "AWS_ACCESS_KEY_ID": os.environ["S3_KEY"], "AWS_SECRET_ACCESS_KEY": os.environ["S3_SECRET"],
       "AWS_DEFAULT_REGION": "hel1", "AWS_REQUEST_CHECKSUM_CALCULATION": "when_required",
       "AWS_RESPONSE_CHECKSUM_VALIDATION": "when_required"}


def log(*a):
    print(time.strftime("%F %T"), *a, flush=True)


def aws(*args, check=True):
    return subprocess.run(["aws", *args, "--endpoint-url", ENDPOINT], env=ENV,
                          check=check, capture_output=True, text=True)


def tem_ok(prefixo):
    return aws("s3", "ls", f"{prefixo}/ok.json", check=False).returncode == 0


def espera_disco(tmp):
    while shutil.disk_usage(tmp).free < MIN_LIVRE_GB * 1024**3:
        log("  disco do finland apertado, esperando")
        time.sleep(120)


def sobe(f, destino, tentativas=6):
    for i in range(tentativas):
        r = aws("s3", "cp", str(f), destino, check=False)
        if r.returncode == 0:
            return
        log(f"  envio de {f.name} falhou ({i + 1}/{tentativas}): {r.stderr.strip()[-160:]}")
        time.sleep(15 * 2**i)
    raise RuntimeError(f"não consegui enviar {f.name}")


def sobe_shards(pasta, prefixo, acabou, falhas):
    """Sobe e apaga cada shard pronto; o de número mais alto ainda pode estar sendo escrito.
    Erro aqui não pode morrer na thread: sem shard, o ok.json não pode ser gravado."""
    try:
        sobe_shards_laco(pasta, prefixo, acabou)
    except Exception as exc:  # noqa: BLE001
        falhas.append(str(exc))


def sobe_shards_laco(pasta, prefixo, acabou):
    while True:
        fim = acabou.is_set()   # lido antes de listar: nada escrito depois disto escapa
        shards = sorted(pasta.glob("*.parquet"))
        for f in shards if fim else shards[:-1]:
            sobe(f, f"{prefixo}/{f.name}")
            f.unlink()
        if fim:
            return
        time.sleep(5)


def contagem_exata(client, bq, t):
    """Troca a contagem do metadado pela real, lendo só a coluna de partição."""
    ds, tb = t["tabela"].split(".", 1)
    col, tipo = t["col"], t["tipo"]
    lista = ", ".join(literal(m["p"], tipo) for m in t["mudou"])
    sql = f"SELECT CAST({col} AS STRING) p, count(*) n FROM `{BQ_PROJECT}.{ds}.{tb}` WHERE {col} IN ({lista}) GROUP BY 1"
    seco = client.query(sql, job_config=bq.QueryJobConfig(dry_run=True, use_query_cache=False))
    if not bq_quota.reserve(max(seco.total_bytes_processed or 0, 10 * 1024**2)):
        raise RuntimeError(f"cota: {bq_quota.status()}")
    exato = {r.p: r.n for r in client.query(sql).result()}
    return [{**m, "bq": exato.get(m["p"], 0)} for m in t["mudou"]]


def o_que_falta(mudou, so_ultimo):
    if so_ultimo:  # a contagem exata pode zerar a data mais nova do metadado: vale a mais nova com linhas
        cheias = [m for m in mudou if m["bq"]]
        return [max(cheias, key=lambda m: m["p"])] if cheias else []
    return [m for m in mudou if m["bq"] and (not m["disco"] or m["bq"] > m["disco"] * MIN_CRESCIMENTO)]


def com_nulas(pa, lotes, alvo):
    """Coluna que a fonte tirou (`nulas` no plano): sai NULL, e a tabela é preenchida depois."""
    for lote in lotes:
        t = pa.Table.from_batches([lote])
        for nome in alvo.names:
            if nome not in t.schema.names:
                t = t.append_column(alvo.field(nome), pa.nulls(len(t), alvo.field(nome).type))
        yield from t.to_batches()


def baixa(client, leitor, bq, pa, pq, t, m, alvo_schema, tmp):
    ds, tb = t["tabela"].split(".", 1)
    prefixo = f"{BUCKET}/{ds}/{tb}/{m['p']}"
    if tem_ok(prefixo):
        log("  já no pouso:", t["tabela"], m["p"])
        return True
    espera_disco(tmp)
    where = f"{t['col']} = {literal(m['p'], t['tipo'])}"
    sql = f"SELECT * FROM `{BQ_PROJECT}.{ds}.{tb}` WHERE {where}"
    seco = client.query(sql, job_config=bq.QueryJobConfig(dry_run=True, use_query_cache=False))
    estimado = seco.total_bytes_processed or int(m["bq"] * t["por_linha"])
    if not bq_quota.reserve(estimado):
        raise RuntimeError(f"cota: {bq_quota.status()}")
    pasta = Path(tmp) / "p"
    shutil.rmtree(pasta, ignore_errors=True)
    pasta.mkdir()
    lotes = client.query(sql).result().to_arrow_iterable(bqstorage_client=leitor)
    acabou = threading.Event()
    falhas = []
    envio = threading.Thread(target=sobe_shards, args=(pasta, prefixo, acabou, falhas))
    envio.start()
    try:
        n, _ = escreve_shards(conforma(pa, com_nulas(pa, lotes, alvo_schema), alvo_schema), pasta, pq)
    finally:
        acabou.set()
        envio.join()
    if falhas:
        raise RuntimeError(f"{where}: {falhas[0]}")
    if n != m["bq"]:
        raise RuntimeError(f"{where}: baixei {n}, o BigQuery dizia {m['bq']}")
    ok = {**m, "tabela": t["tabela"], "col": t["col"], "bytes": estimado, "coletado": dt.datetime.now(dt.UTC).isoformat()}
    (Path(tmp) / "ok.json").write_text(json.dumps(ok))
    sobe(Path(tmp) / "ok.json", f"{prefixo}/ok.json")
    log(f"  {t['tabela']} {m['p']}: {m['disco']:,} -> {m['bq']:,} ({estimado/1e9:.1f} GB lidos)")
    shutil.rmtree(pasta)
    return True


def main():
    plano = json.loads(Path(sys.argv[1]).read_text())
    while dt.datetime.now(dt.UTC).strftime("%Y-%m") < MES:
        time.sleep(60)
    warnings.filterwarnings("ignore")
    import pyarrow as pa
    import pyarrow.parquet as pq
    from google.cloud import bigquery as bq
    from google.cloud import bigquery_storage

    exige_sandbox()
    client = bq.Client(project=BILLING_PROJECT)
    leitor = bigquery_storage.BigQueryReadClient()
    resumo = []
    with tempfile.TemporaryDirectory(dir=Path(sys.argv[1]).parent) as tmp:
        for t in plano:
            try:
                mudou = contagem_exata(client, bq, t) if t.get("aproximado") else t["mudou"]
                partes = o_que_falta(mudou, t.get("so_ultimo"))
                log(t["tabela"], len(partes), "de", len(mudou), "partições")
                tipos = t.get("tipos", {})  # coluna cujo tipo do disco trunca o valor da fonte
                alvo = pa.schema([pa.field(n, tipo_arrow(pa, tipos.get(n, d))) for n, d in t["schema"]])
                for m in partes:
                    baixa(client, leitor, bq, pa, pq, t, m, alvo, tmp)
                resumo.append({"tabela": t["tabela"], "partes": [m["p"] for m in partes]})
            except Exception as exc:  # noqa: BLE001 — uma tabela não derruba as outras
                log("  ERRO", t["tabela"], str(exc)[:300])
                resumo.append({"tabela": t["tabela"], "erro": str(exc)[:300]})
        fim = Path(tmp) / "FIM.json"
        fim.write_text(json.dumps({"fim": dt.datetime.now(dt.UTC).isoformat(), "tabelas": resumo, "cota": bq_quota.status()}))
        aws("s3", "cp", str(fim), f"{BUCKET}/FIM.json")
    log("FIM", bq_quota.status())


if __name__ == "__main__":
    main()
