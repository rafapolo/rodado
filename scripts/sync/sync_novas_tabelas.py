#!/usr/bin/env python3
"""Puxa tabelas NOVAS (que ainda não existem em beelink:~/rodado/<ds>/<tb>/)
via `QueryJob.to_arrow()`, igual a `ressincroniza_bq.py` -- mas sem a etapa
de mover o diretório antigo pro backup, porque não há diretório antigo.

Por que este script existe, e não `gcp_to_beelink_sync.py`: aquele usa
`bq query --format=json` e o CLI trava ou estoura o timeout de 180s em
tabelas de algumas centenas de milhares de linhas com muitas colunas --
confirmado ao vivo em br_cgu_pessoal_executivo_federal.terceirizados (732K
linhas, dry-run de 0.26GB, nada de acesso negado) e br_bndes/br_me_siconfi
similares. `to_arrow()` lê os resultados tipados direto da API do BigQuery,
sem o round-trip JSON -- o mesmo motivo que fez `ressincroniza_bq.py` nascer
em 2026-07-05 (ver seu próprio docstring).

    python3 scripts/sync/sync_novas_tabelas.py --lista tasks/novas.txt
    python3 scripts/sync/sync_novas_tabelas.py --apply br_x.y br_x.z
"""
import argparse
import json
import os
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
        sys.exit(f"ssh falhou ({cmd[:60]}...): {r.stderr.strip()[:300]}")
    return r.stdout


def exige_sandbox():
    tok = subprocess.run(["gcloud", "auth", "print-access-token"],
                         capture_output=True, text=True, timeout=120).stdout.strip()
    if not tok:
        sys.exit("nao consegui um token do gcloud")
    req = urllib.request.Request(
        f"https://cloudbilling.googleapis.com/v1/projects/{BILLING_PROJECT}/billingInfo",
        headers={"Authorization": f"Bearer {tok}"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        info = json.load(resp)
    if info.get("billingEnabled"):
        sys.exit(f"billing ATIVO em {BILLING_PROJECT} -- abortando.")
    print(f"  sandbox confirmado: billingEnabled=false em {BILLING_PROJECT}")


def escreve_shards(tabela, destino, pq):
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


def puxa(client, pq, alvo, aplicar):
    ds, tb = alvo.split(".", 1)
    remoto = f"{ROOT}/{ds}/{tb}"

    existe = sh(f"[ -d {remoto} ] && ls {remoto}/*.parquet 2>/dev/null | wc -l || echo 0").strip()
    if existe not in ("0", ""):
        return {"tabela": alvo, "erro": f"ja existe no disco ({existe} parquet) -- use ressincroniza_bq.py"}

    tabela = client.query(f"SELECT * FROM `{BQ_PROJECT}.{ds}.{tb}`").to_arrow()
    n_bq = tabela.num_rows
    tipadas = sum(1 for f in tabela.schema if str(f.type) != "string")
    print(f"  {alvo:52} {n_bq:>10,} linhas  {tipadas}/{len(tabela.schema)} col tipadas")
    if not aplicar:
        return {"tabela": alvo, "linhas": n_bq, "aplicado": False}

    with tempfile.TemporaryDirectory() as tmp:
        local = Path(tmp) / tb
        local.mkdir()
        escreve_shards(tabela, local, pq)
        sh(f"mkdir -p {remoto}", check=True)
        r = subprocess.run(
            ["rsync", "-a", f"{local}/", f"{BEELINK}:{remoto}/"],
            capture_output=True, text=True, timeout=3600)
        if r.returncode != 0:
            return {"tabela": alvo, "erro": f"rsync: {r.stderr[:200]}"}

    dep = sh(f"[ -d {remoto} ] && ls {remoto}/*.parquet 2>/dev/null | wc -l || echo 0").strip()
    return {"tabela": alvo, "linhas": n_bq, "aplicado": True, "shards": dep}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tabelas", nargs="*", help="dataset.tabela")
    ap.add_argument("--lista", help="arquivo com um dataset.tabela por linha")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--max-gb", type=float, default=5.0)
    a = ap.parse_args()

    alvos = list(a.tabelas)
    if a.lista:
        alvos += [l.strip() for l in Path(a.lista).read_text().split("\n")
                  if l.strip() and not l.startswith("#")]
    if not alvos:
        sys.exit("nada a fazer: passe tabelas ou --lista")

    import warnings
    warnings.filterwarnings("ignore")
    from google.cloud import bigquery as bq
    import pyarrow.parquet as pq

    exige_sandbox()
    client = bq.Client(project=BILLING_PROJECT)

    print(f"\n{'Puxando' if a.apply else 'Dry-run'} ({len(alvos)} tabelas)...\n")
    res = []
    for t in alvos:
        try:
            res.append(puxa(client, pq, t, a.apply))
        except Exception as exc:                                   # noqa: BLE001
            print(f"  {t:52} ERRO {str(exc)[:150]}")
            res.append({"tabela": t, "erro": str(exc)[:200]})

    erros = [r for r in res if r.get("erro")]
    feitos = [r for r in res if r.get("aplicado")]
    print(f"\n{'-' * 78}")
    if a.apply:
        print(f"{len(feitos)} tabelas novas sincronizadas")
        print("agora rode: python3 scripts/sync/cria_views_novas.py <lista>")
    else:
        print(f"Dry-run. {len(res) - len(erros)} tabelas seriam puxadas.")
    for e in erros:
        print(f"  ERRO {e['tabela']}: {e['erro']}")
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
