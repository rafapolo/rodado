#!/usr/bin/env python3
"""Ressincroniza tabelas do Base dos Dados para o espelho do beelink, com tipo.

    python3 scripts/sync/ressincroniza_bq.py --lista tasks/stale27.txt      # dry-run
    python3 scripts/sync/ressincroniza_bq.py --lista tasks/stale27.txt --apply
    python3 scripts/sync/ressincroniza_bq.py --apply br_bd_diretorios_mundo.pais

Por que existe: em 2026-07-05 dois scripts de sync mandaram o resultado de
`bq query --format=json` para o espelho passando por `pa.Table.from_pylist()`. O JSON
do `bq` não carrega tipo, então 154 colunas de 38 tabelas chegaram como string, e o
`rsync` ainda levou junto o nome do tempfile — 80 `tmp*.parquet` largados ao lado do
export bom, fazendo as views lerem os dois.

Aqui o JSON não entra no caminho: a Storage Read API devolve Arrow **já tipado**
direto da API de resultados do BigQuery, e o Parquet sai daí. Sem inferência, sem
round-trip por texto.

Regras que este script respeita, do AGENTS.md:

  - BigQuery só em Sandbox, sem billing. O script **confere** `billingEnabled` antes de
    qualquer consulta e aborta se estiver ligado — é o que torna o uso pontual seguro.
  - Nada de `bq extract` nem GCS: só a query interativa, que cabe na cota gratuita.
  - Escrita em ZSTD, como o resto do espelho.

O diretório antigo nunca é apagado: vai inteiro para `~/backups/ressync_<data>/`.
"""
import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bq_quota  # noqa: E402

BEELINK = os.environ.get("BEELINK_HOST", "beelink")
ROOT = "/home/polo/rodado"
BILLING_PROJECT = "raspa-491716"
BQ_PROJECT = "basedosdados"
LINHAS_POR_SHARD = 500_000
LINHAS_POR_ROW_GROUP = 122_880  # o padrão do DuckDB


def sh(cmd, timeout=1800, check=False):
    r = subprocess.run(["ssh", BEELINK, cmd], capture_output=True, text=True, timeout=timeout)
    if check and r.returncode != 0:
        sys.exit(f"ssh falhou ({cmd[:60]}…): {r.stderr.strip()[:300]}")
    return r.stdout


def exige_sandbox():
    """Aborta se o projeto de billing tiver billing ativo.

    A exceção que permite BigQuery neste repo vale só enquanto for impossível gerar
    custo. Ligou billing, a exceção acaba — então isto é checagem, não formalidade.
    """
    tok = ""
    if shutil.which("gcloud"):
        tok = subprocess.run(["gcloud", "auth", "print-access-token"],
                             capture_output=True, text=True, timeout=120).stdout.strip()
    if not tok:
        # sem o SDK instalado, o token sai das credenciais ADC
        # (~/.config/gcloud/application_default_credentials.json)
        import google.auth
        import google.auth.transport.requests
        cred, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        cred.refresh(google.auth.transport.requests.Request())
        tok = cred.token
    if not tok:
        sys.exit("não consegui um token — rode `gcloud auth application-default login`")
    req = urllib.request.Request(
        f"https://cloudbilling.googleapis.com/v1/projects/{BILLING_PROJECT}/billingInfo",
        headers={"Authorization": f"Bearer {tok}"})
    for tentativa in range(6):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                info = json.load(resp)
            break
        except urllib.error.HTTPError as exc:
            # a API de billing limita chamadas seguidas (429); sem resposta, não roda
            if exc.code != 429 or tentativa == 5:
                raise
            time.sleep(20 * (tentativa + 1))
    if info.get("billingEnabled"):
        sys.exit(f"billing ATIVO em {BILLING_PROJECT} — a exceção de BigQuery do "
                 f"AGENTS.md não vale mais. Abortando.")
    print(f"  sandbox confirmado: billingEnabled=false em {BILLING_PROJECT}")


# Bytes lógicos do BigQuery por byte de Parquet+zstd no espelho. Medido em 2026-10-07
# em 33 tabelas espelhadas acima de 20M linhas: mediana 8,4, pior caso 2,65
# (`br_cgu_beneficios_cidadao.bpc`). A trava usa o pior caso.
RAZAO_PESSIMISTA = 2.5


def exige_espaco(estimado, reserva_gb):
    """Recusa a tabela se, depois dela, o disco do beelink ficar abaixo da reserva.

    A reserva existe porque `~/duckdb_tmp` (teto de 100 GB) mora no mesmo NVMe.
    Devolve None se cabe, ou a mensagem de recusa.
    """
    out = sh(f"df -B1 --output=avail {ROOT} | tail -1", timeout=60).strip()
    if not out.isdigit():
        return "não consegui ler o espaço livre do beelink"
    livre, precisa = int(out), estimado / RAZAO_PESSIMISTA
    if livre - precisa < reserva_gb * 1e9:
        return (f"sem espaço: livre {livre/1e9:.1f} GB, a tabela pede até "
                f"{precisa/1e9:.1f} GB e a reserva é {reserva_gb:.0f} GB")
    return None


def duck(sql, timeout=1800):
    r = subprocess.run(["ssh", BEELINK, "~/bin/duckdb -json"],
                       input="SET enable_progress_bar=false;\n" + sql + "\n.quit\n",
                       capture_output=True, text=True, timeout=timeout)
    if "[" not in r.stdout:
        return None
    return json.loads(r.stdout[r.stdout.index("["):])


def bytes_query(client, bq, ds, tb):
    cfg = bq.QueryJobConfig(dry_run=True, use_query_cache=False)
    try:
        j = client.query(f"SELECT * FROM `{BQ_PROJECT}.{ds}.{tb}`", job_config=cfg)
        return j.total_bytes_processed
    except Exception as exc:                                      # noqa: BLE001
        return f"erro: {str(exc)[:80]}"


def escreve_shards(lotes, destino, pq):
    """Grava os lotes Arrow em shards `0000000000NN.parquet`, ZSTD, como o resto do espelho.

    Escreve à medida que os lotes chegam, mas junta-os em row groups de
    LINHAS_POR_ROW_GROUP: a Storage Read API entrega lotes de poucas centenas de
    linhas numa tabela larga, e um row group por lote deixou arquivos com 1.200 row
    groups de ~830 linhas, cujos metadados fizeram uma view com `union_by_name`
    passar de 18 GB de memória (2026-10-07). Devolve (linhas, schema); schema None
    se a tabela veio vazia.
    """
    import pyarrow as pa
    n = no_shard = i = 0
    w = schema = None
    buf, no_buf = [], 0

    def descarrega():
        nonlocal buf, no_buf
        if buf:
            w.write_table(pa.Table.from_batches(buf), row_group_size=LINHAS_POR_ROW_GROUP)
        buf, no_buf = [], 0

    for lote in lotes:
        if w is None:
            schema = lote.schema
            w = pq.ParquetWriter(str(destino / f"{i:012d}.parquet"), schema,
                                 compression="zstd")
        buf.append(lote)
        no_buf += lote.num_rows
        n += lote.num_rows
        no_shard += lote.num_rows
        if no_buf >= LINHAS_POR_ROW_GROUP:
            descarrega()
        if no_shard >= LINHAS_POR_SHARD:
            descarrega()
            w.close()
            w, no_shard, i = None, 0, i + 1
    if w is not None:
        descarrega()
        w.close()
    return n, schema


def ressincroniza(client, leitor, bq, pq, alvo, backup_dir, aplicar, estimado=0, reserva_gb=100.0):
    ds, tb = alvo.split(".", 1)
    remoto = f"{ROOT}/{ds}/{tb}"
    antes = duck(f"SELECT count(*) n FROM read_parquet('{remoto}/*.parquet');")
    n_antes = antes[0]["n"] if antes else 0

    if not aplicar:
        # sem --apply, só o metadado: nenhuma query, nenhuma cota
        n_bq = client.get_table(f"{BQ_PROJECT}.{ds}.{tb}").num_rows
        print(f"  {alvo:52} {n_antes:>10,} -> {n_bq:>10,}  ({n_bq - n_antes:+,})")
        return {"tabela": alvo, "antes": n_antes, "depois": n_bq, "aplicado": False}

    falta = exige_espaco(estimado, reserva_gb)
    if falta:
        return {"tabela": alvo, "erro": falta}
    if not bq_quota.reserve(estimado):
        return {"tabela": alvo, "erro": f"cota do mês: {bq_quota.status()}"}

    with tempfile.TemporaryDirectory() as tmp:
        local = Path(tmp) / tb
        local.mkdir()
        # Storage Read API, em streaming: pela REST vêm ~4 mil linhas/s (medido em
        # 2026-10-07), e uma tabela grande não cabe em memória de uma vez
        lotes = (client.query(f"SELECT * FROM `{BQ_PROJECT}.{ds}.{tb}`").result()
                 .to_arrow_iterable(bqstorage_client=leitor))
        n_bq, schema = escreve_shards(lotes, local, pq)
        if schema is None:
            # tabela vazia: um shard vazio, com o schema que o BigQuery devolve
            vazio = (client.query(f"SELECT * FROM `{BQ_PROJECT}.{ds}.{tb}` LIMIT 0")
                     .result().to_arrow())
            pq.write_table(vazio, str(local / f"{0:012d}.parquet"), compression="zstd")
            schema = vazio.schema
        tipadas = sum(1 for f in schema if str(f.type) != "string")
        print(f"  {alvo:52} {n_antes:>10,} -> {n_bq:>10,}  ({n_bq - n_antes:+,})  "
              f"{tipadas}/{len(schema)} col tipadas", flush=True)
        sh(f"rm -rf {remoto}.novo && mkdir -p {remoto}.novo", check=True)
        # sem --chmod: o rsync do macOS (openrsync, "2.6.9 compatible") não tem a
        # flag. O modo vai para 664 no beelink, depois da troca.
        r = subprocess.run(
            ["rsync", "-a", f"{local}/", f"{BEELINK}:{remoto}.novo/"],
            capture_output=True, text=True, timeout=3600)
        if r.returncode != 0:
            sh(f"rm -rf {remoto}.novo")
            return {"tabela": alvo, "erro": f"rsync: {r.stderr[:200]}"}

    # troca: o antigo vai inteiro para o backup, nunca para o lixo
    # tabela nova não tem o que guardar
    sh(f"if [ -d {remoto} ]; then mkdir -p {backup_dir}/{ds} && "
       f"mv {remoto} {backup_dir}/{ds}/{tb}; fi && "
       f"mv {remoto}.novo {remoto} && "
       f"chmod 775 {remoto} && chmod 664 {remoto}/*.parquet", check=True)

    dep = duck(f"SELECT count(*) n FROM read_parquet('{remoto}/*.parquet');")
    n_dep = dep[0]["n"] if dep else -1
    if n_dep != n_bq:
        return {"tabela": alvo, "erro": f"conferência falhou: disco {n_dep} x BQ {n_bq}"}
    return {"tabela": alvo, "antes": n_antes, "depois": n_dep, "aplicado": True}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tabelas", nargs="*", help="dataset.tabela")
    ap.add_argument("--lista", help="arquivo com um dataset.tabela por linha")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--max-gb", type=float, default=20.0,
                    help="recusa tabela cuja query passe disto (padrão 20 GB)")
    ap.add_argument("--reserva-gb", type=float, default=100.0,
                    help="espaço que tem de sobrar no beelink depois de cada tabela "
                         "(padrão 100 GB)")
    a = ap.parse_args()

    alvos = list(a.tabelas)
    if a.lista:
        alvos += [l.strip() for l in Path(a.lista).read_text().split("\n")
                  if l.strip() and not l.startswith("#")]
    if not alvos:
        sys.exit("nada a fazer: passe tabelas ou --lista")
    if not shutil.which("rsync"):
        sys.exit("rsync não encontrado")

    import warnings
    warnings.filterwarnings("ignore")
    from google.cloud import bigquery as bq
    from google.cloud import bigquery_storage
    import pyarrow.parquet as pq

    exige_sandbox()
    client = bq.Client(project=BILLING_PROJECT)
    leitor = bigquery_storage.BigQueryReadClient()

    print(f"\nEstimando ({len(alvos)} tabelas)…")
    total = 0
    estimados = {}
    for t in alvos:
        ds, tb = t.split(".", 1)
        b = bytes_query(client, bq, ds, tb)
        estimados[t] = b if isinstance(b, int) else 0
        if isinstance(b, str):
            print(f"  {t:52} {b}")
        elif b is None:
            print(f"  {t:52}    sem estimativa (view ou tabela lógica)")
        else:
            total += b
            if b / 1e9 > a.max_gb:
                sys.exit(f"{t} processaria {b/1e9:.1f} GB, acima de --max-gb={a.max_gb}")
    print(f"  {'TOTAL estimado':52} {total/1e9:.3f} GB "
          f"({total/1e12*100:.2f}% da cota mensal de 1 TB)")

    backup = f"~/backups/ressync_{dt.datetime.now():%Y%m%d_%H%M}"
    print(f"\n{'Ressincronizando' if a.apply else 'Dry-run'}"
          f"{'; antigo vai para ' + backup if a.apply else ''}…\n")

    res = []
    for t in alvos:
        # o stream da Storage API cai às vezes no meio ("503 Stream removed",
        # 2026-10-07); até a troca nada mudou no espelho, então repetir é seguro
        for tentativa in range(3):
            try:
                res.append(ressincroniza(client, leitor, bq, pq, t, backup, a.apply,
                                         estimados[t], a.reserva_gb))
                break
            except Exception as exc:                              # noqa: BLE001
                print(f"  {t:52} ERRO (tentativa {tentativa + 1}/3) {str(exc)[:120]}",
                      flush=True)
                if tentativa == 2:
                    res.append({"tabela": t, "erro": str(exc)[:200]})

    erros = [r for r in res if r.get("erro")]
    feitos = [r for r in res if r.get("aplicado")]
    ganho = sum(r["depois"] - r["antes"] for r in feitos)
    print(f"\n{'-' * 78}")
    if a.apply:
        print(f"{len(feitos)} tabelas ressincronizadas, {ganho:+,} linhas no total")
        print(f"antigo preservado em {backup} (apagar só depois de conferir)")
        print("agora rode: python3 scripts/repara_views_beelink.py --apply")
    else:
        print(f"Dry-run. {len(res) - len(erros)} tabelas seriam ressincronizadas.")
    for e in erros:
        print(f"  ERRO {e['tabela']}: {e['erro']}")
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
