#!/usr/bin/env python3
"""Linhas por partição de uma tabela do Base dos Dados, lidas do METADADO do BigQuery.

    python3 scripts/sync/particoes_bq_metadado.py br_ms_sinan.microdados_dengue [dataset.tabela ...]
    python3 scripts/sync/particoes_bq_metadado.py --json saida.json br_ms_sia.psicossocial

Consulta `INFORMATION_SCHEMA.PARTITIONS` do dataset: devolve `partition_id`, `total_rows` e
`last_modified_time` sem varrer a tabela (cada consulta é cobrada como 10 MB). É o caminho
barato para comparar partições com o disco: `count(*) GROUP BY` na tabela custa 8 bytes por
linha (a contagem do plano de 2026-10-09 gastou ~65 GB de cota em RAIS, CNO e MiDES).

Não serve para tabela com row-level security nem para tabela sem partição (devolve uma
linha só, `__UNPARTITIONED__` ou `__NULL__`). Só Sandbox, sem billing: confere antes.
"""
import argparse
import json
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bq_quota  # noqa: E402
from ressincroniza_bq import BILLING_PROJECT, BQ_PROJECT, exige_sandbox  # noqa: E402

CUSTO = 10 * 1024**2  # mínimo cobrado por consulta


def particoes(client, bq, alvo):
    ds, tb = alvo.split(".", 1)
    sql = (f"SELECT partition_id, total_rows, CAST(last_modified_time AS STRING) AS modificado "
           f"FROM `{BQ_PROJECT}.{ds}.INFORMATION_SCHEMA.PARTITIONS` "
           f"WHERE table_name = @tb ORDER BY partition_id")
    if not bq_quota.reserve(CUSTO):
        sys.exit("cota do mês esgotada")
    cfg = bq.QueryJobConfig(query_parameters=[bq.ScalarQueryParameter("tb", "STRING", tb)],
                            maximum_bytes_billed=20 * CUSTO)
    return [dict(r) for r in client.query(sql, job_config=cfg).result()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tabelas", nargs="+", help="dataset.tabela")
    ap.add_argument("--json")
    a = ap.parse_args()
    exige_sandbox()
    warnings.filterwarnings("ignore")
    from google.cloud import bigquery as bq
    client = bq.Client(project=BILLING_PROJECT)
    tudo = {}
    for alvo in a.tabelas:
        ps = particoes(client, bq, alvo)
        tudo[alvo] = ps
        print(f"{alvo}: {len(ps)} partições, {sum(p['total_rows'] for p in ps):,} linhas")
        for p in ps:
            print(f"  {p['partition_id']:>14}  {p['total_rows']:>14,}  {p['modificado'][:10]}")
    if a.json:
        Path(a.json).write_text(json.dumps(tudo, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
