#!/usr/bin/env python3
"""Ressincroniza tabelas do Base dos Dados para o espelho do beelink, com tipo.

    python3 scripts/sync/ressincroniza_bq.py --lista tasks/stale27.txt      # dry-run
    python3 scripts/sync/ressincroniza_bq.py --lista tasks/stale27.txt --apply
    python3 scripts/sync/ressincroniza_bq.py --apply br_bd_diretorios_mundo.pais

Por que existe: em 2026-07-05 dois scripts de sync mandaram o resultado de
`bq query --format=json` para o espelho passando por `pa.Table.from_pylist()`. O JSON
do `bq` não carrega tipo, então 154 colunas de 38 tabelas chegaram como string, e o
`rsync` ainda levou junto o nome do tempfile — 80 `tmp*.parquet` largados ao lado do
export bom, fazendo as views lerem os dois. Ver `tasks/tmp_parquet_38.plan`.

Aqui o JSON não entra no caminho: `QueryJob.to_arrow()` devolve Arrow **já tipado**
direto da API de resultados do BigQuery, e o Parquet sai daí. Sem inferência, sem
round-trip por texto.

Regras que este script respeita, do CLAUDE.md:

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
import urllib.request
from pathlib import Path

BEELINK = os.environ.get("BEELINK_HOST", "beelink")
ROOT = "/home/polo/rodado"
BILLING_PROJECT = "raspa-491716"
BQ_PROJECT = "basedosdados"
LINHAS_POR_SHARD = 500_000


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
    tok = subprocess.run(["gcloud", "auth", "print-access-token"],
                         capture_output=True, text=True, timeout=120).stdout.strip()
    if not tok:
        sys.exit("não consegui um token do gcloud — rode `gcloud auth login`")
    req = urllib.request.Request(
        f"https://cloudbilling.googleapis.com/v1/projects/{BILLING_PROJECT}/billingInfo",
        headers={"Authorization": f"Bearer {tok}"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        info = json.load(resp)
    if info.get("billingEnabled"):
        sys.exit(f"billing ATIVO em {BILLING_PROJECT} — a exceção de BigQuery do "
                 f"CLAUDE.md não vale mais. Abortando.")
    print(f"  sandbox confirmado: billingEnabled=false em {BILLING_PROJECT}")


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


def escreve_shards(tabela, destino, pq):
    """Grava o Arrow em shards `0000000000NN.parquet`, ZSTD, como o resto do espelho."""
    n = tabela.num_rows
    nomes = []
    for i, ini in enumerate(range(0, max(n, 1), LINHAS_POR_SHARD)):
        pedaco = tabela.slice(ini, LINHAS_POR_SHARD)
        nome = f"{i:012d}.parquet"
        pq.write_table(pedaco, str(destino / nome), compression="zstd")
        nomes.append(nome)
        if n == 0:
            break
    return nomes


def ressincroniza(client, bq, pq, alvo, backup_dir, aplicar):
    ds, tb = alvo.split(".", 1)
    remoto = f"{ROOT}/{ds}/{tb}"
    antes = duck(f"SELECT count(*) n FROM read_parquet('{remoto}/*.parquet');")
    n_antes = antes[0]["n"] if antes else 0

    tabela = client.query(f"SELECT * FROM `{BQ_PROJECT}.{ds}.{tb}`").to_arrow()
    n_bq = tabela.num_rows
    tipadas = sum(1 for f in tabela.schema if str(f.type) != "string")
    print(f"  {alvo:52} {n_antes:>10,} -> {n_bq:>10,}  ({n_bq - n_antes:+,})  "
          f"{tipadas}/{len(tabela.schema)} col tipadas")
    if not aplicar:
        return {"tabela": alvo, "antes": n_antes, "depois": n_bq, "aplicado": False}

    with tempfile.TemporaryDirectory() as tmp:
        local = Path(tmp) / tb
        local.mkdir()
        escreve_shards(tabela, local, pq)
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
    sh(f"mkdir -p {backup_dir}/{ds} && "
       f"mv {remoto} {backup_dir}/{ds}/{tb} && "
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
    import pyarrow.parquet as pq

    exige_sandbox()
    client = bq.Client(project=BILLING_PROJECT)

    print(f"\nEstimando ({len(alvos)} tabelas)…")
    total = 0
    for t in alvos:
        ds, tb = t.split(".", 1)
        b = bytes_query(client, bq, ds, tb)
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
        try:
            res.append(ressincroniza(client, bq, pq, t, backup, a.apply))
        except Exception as exc:                                  # noqa: BLE001
            print(f"  {t:52} ERRO {str(exc)[:120]}")
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
