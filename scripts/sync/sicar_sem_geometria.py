#!/usr/bin/env python3
"""Puxa as 5 tabelas do SICAR que faltavam no espelho, SEM a coluna `geometria`.

    python3 scripts/sync/sicar_sem_geometria.py              # dry-run (só estima)
    python3 scripts/sync/sicar_sem_geometria.py --apply      # puxa e grava no beelink
    python3 scripts/sync/sicar_sem_geometria.py --apply app  # só uma tabela

Tabelas: app, area_consolidada, hidrografia, reserva_legal, vegetacao_nativa de
`basedosdados.br_sfb_sicar`. Destino: beelink:~/rodado/br_sfb_sicar/<tabela>/<UF>.parquet
(ZSTD), uma fatia por `sigla_uf` (a coluna de clustering).

Por que sem geometria, e não centroide + área: `ST_CENTROID(geometria)` obriga o
BigQuery a ler a coluna GEOGRAPHY inteira. Medido em 2026-09-25 no dry-run:
projetar só as colunas não-geo custa 6,4 GB para as 5 tabelas; com
`ST_CENTROID`/`ST_AREA` custa 272,6 GB (app sozinha: 3,6 GB contra 162,6 GB).
A localização continua recuperável pelo `id_imovel` -> `area_imovel.geometria`,
que já está no disco. `area` já vem calculada pela fonte (ha).

Regras (AGENTS.md / scripts/sync-with-source.md):
  - Sandbox apenas: confere `billingEnabled=false` pela Cloud Billing API antes de
    qualquer query e aborta se estiver ligado.
  - Só `query` interativa (nada de extract, GCS ou Storage Read API:
    `to_arrow(create_bqstorage_client=False)` pagina pela REST, que é grátis).
  - Cada fatia passa por dry-run, reserva em `bq_quota` e roda com
    `maximum_bytes_billed` como teto duro.
  - Retomável: fatia já presente no beelink é pulada.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bq_quota  # noqa: E402

warnings.filterwarnings("ignore")

BEELINK = os.environ.get("BEELINK_HOST", "beelink")
ROOT = "/home/polo/rodado/br_sfb_sicar"
JOB_PROJECT = "raspa-491716"
SRC = "basedosdados.br_sfb_sicar"
TABELAS = ["area_consolidada", "hidrografia", "reserva_legal", "vegetacao_nativa", "app"]
UFS = ("AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO").split()
TETO_FATIA = 2 * 1024**3  # nenhuma fatia sem geometria deveria passar de 2 GB


def exige_sandbox():
    import google.auth
    import google.auth.transport.requests as gr
    cred, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    cred.refresh(gr.Request())
    req = urllib.request.Request(
        f"https://cloudbilling.googleapis.com/v1/projects/{JOB_PROJECT}/billingInfo",
        headers={"Authorization": f"Bearer {cred.token}"})
    info = json.load(urllib.request.urlopen(req, timeout=60))
    if info.get("billingEnabled") or info.get("billingAccountName"):
        sys.exit(f"billing ATIVO/ligado em {JOB_PROJECT}: {info} — abortando.")
    print(f"sandbox confirmado: {info}")


def ja_no_beelink(tabela):
    r = subprocess.run(["ssh", BEELINK, f"ls {ROOT}/{tabela}/ 2>/dev/null"],
                       capture_output=True, text=True, timeout=120)
    return {l.removesuffix(".parquet") for l in r.stdout.split() if l.endswith(".parquet")}


def colunas(client, tabela):
    t = client.get_table(f"{SRC}.{tabela}")
    return [f.name for f in t.schema if f.field_type != "GEOGRAPHY"]


def fatias():
    for uf in UFS:
        yield uf, f"sigla_uf = '{uf}'"
    yield "_outros", f"sigla_uf IS NULL OR sigla_uf NOT IN ({', '.join(repr(u) for u in UFS)})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tabelas", nargs="*", default=TABELAS)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    from google.cloud import bigquery as bq
    import pyarrow.parquet as pq

    exige_sandbox()
    client = bq.Client(project=JOB_PROJECT)
    total_bytes = 0
    for tabela in a.tabelas:
        cols = ", ".join(colunas(client, tabela))
        feitas = ja_no_beelink(tabela) if a.apply else set()
        linhas_tab = 0
        for nome, where in fatias():
            if nome in feitas:
                print(f"  {tabela}/{nome}: já no beelink, pulando")
                continue
            sql = f"SELECT {cols} FROM `{SRC}.{tabela}` WHERE {where}"
            dry = client.query(sql, job_config=bq.QueryJobConfig(dry_run=True, use_query_cache=False))
            b = dry.total_bytes_processed
            if b > TETO_FATIA:
                sys.exit(f"{tabela}/{nome}: dry-run {b/1e9:.2f} GB acima do teto — geometria vazou?")
            total_bytes += b
            if not a.apply:
                continue
            if not bq_quota.reserve(b):
                sys.exit(f"cota mensal esgotada antes de {tabela}/{nome}: {bq_quota.status()}")
            job = client.query(sql, job_config=bq.QueryJobConfig(
                maximum_bytes_billed=max(int(b * 1.2), 10 * 1024**2), use_query_cache=False))
            t = job.result(timeout=1800).to_arrow(create_bqstorage_client=False)
            print(f"  {tabela}/{nome}: {t.num_rows:,} linhas, job {job.job_id}, "
                  f"processados {job.total_bytes_processed:,} B, faturados {job.total_bytes_billed:,} B",
                  flush=True)
            if t.num_rows == 0:
                continue
            linhas_tab += t.num_rows
            with tempfile.TemporaryDirectory() as tmp:
                arq = Path(tmp) / f"{nome}.parquet"
                pq.write_table(t, arq, compression="zstd", row_group_size=500_000)
                subprocess.run(["ssh", BEELINK, f"mkdir -p {ROOT}/{tabela}"], check=True)
                subprocess.run(["rsync", "-a", str(arq), f"{BEELINK}:{ROOT}/{tabela}/{nome}.parquet"],
                               check=True, timeout=3600)
        print(f"{tabela}: {linhas_tab:,} linhas novas nesta rodada")
    print(f"total dry-run desta rodada: {total_bytes/1e9:.3f} GB | {bq_quota.status()}")


if __name__ == "__main__":
    main()
