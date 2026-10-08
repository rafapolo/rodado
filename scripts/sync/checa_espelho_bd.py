#!/usr/bin/env python3
"""Compara o espelho do Base dos Dados no beelink com o BigQuery. Só reporta.

    python3 scripts/sync/checa_espelho_bd.py                 # resumo + lista do que está atrás
    python3 scripts/sync/checa_espelho_bd.py --json saida.json
    python3 scripts/sync/checa_espelho_bd.py br_me_          # só datasets com esse prefixo

Irmão de `scripts/checa_frescor_fontes.py` (que cobre as fontes raspadas). Lê do
catálogo (`_rodado_metadata`) as tabelas com `source_name = 'Base dos Dados'` e
pergunta ao BigQuery só o METADADO de cada uma (`get_table`: `num_rows`,
`modified`, `num_bytes`, partição e cluster). Não abre job, não gasta cota e não
grava nada no beelink.

Como ler a saída:
  - `atras`: o BigQuery tem mais linhas. `particao` diz se há coluna para o caminho
    incremental (`sync_drifted_incremental.py`); sem ela, é tabela inteira
    (`ressincroniza_bq.py`), e `gb_bq` é o teto do que a query varre.
  - `encolheu`: o BigQuery tem MENOS linhas que o disco. Não é para sincronizar
    às cegas: ou a fonte refez a tabela, ou o disco tem arquivo sobrando.
  - `mudou`: mesma contagem, mas o BigQuery regravou a tabela depois do nosso
    parquet mais novo. Pode ser correção de valor ou só reprocessamento.
  - `sumiu`: 404 no BigQuery (tabela removida ou renomeada na fonte).
  - `br_me_cnpj` é o `br_rf_cnpj` da fonte desde 2026-08; fica fora daqui, quem
    diz o que falta é `atualiza_cnpj_rf.py` (sem `--apply`).
"""
import argparse
import concurrent.futures as cf
import json
import os
import subprocess
import sys
import warnings

BEELINK = os.environ.get("BEELINK_HOST", "beelink")
JOB_PROJECT = "raspa-491716"
BQ_PROJECT = "basedosdados"
FORA = {"br_me_cnpj"}   # rebatizado na fonte, tem script próprio


def catalogo():
    sql = ("SET enable_progress_bar=false; "
           "SELECT dataset, \"table\" AS tabela, rows, size_bytes, updated_at FROM _rodado_metadata "
           "WHERE source_name = 'Base dos Dados' AND source <> 'view_only' ORDER BY 1, 2;")
    out = subprocess.run(["ssh", BEELINK, "~/bin/duckdb -readonly -json ~/rodado/basedosdados.duckdb"],
                         input=sql, capture_output=True, text=True, timeout=300).stdout
    return json.loads(out[out.index("["):])


def consulta(client, linha):
    from google.api_core import exceptions as gex
    ds, tb = linha["dataset"], linha["tabela"]
    r = {"tabela": f"{ds}.{tb}", "linhas_disco": int(linha["rows"] or 0),
         "gb_disco": round(int(linha["size_bytes"] or 0) / 1e9, 3),
         "regravado": (linha["updated_at"] or "")[:10]}
    try:
        t = client.get_table(f"{BQ_PROJECT}.{ds}.{tb}")
    except gex.NotFound:
        return {**r, "estado": "sumiu"}
    except gex.Forbidden:
        return {**r, "estado": "sem_acesso"}
    except Exception as e:   # rede: reporta, não derruba a varredura
        return {**r, "estado": "erro", "erro": str(e)[:100]}
    if t.table_type != "TABLE":
        return {**r, "estado": "nao_e_tabela", "tipo": t.table_type}
    part = (t.time_partitioning.field if t.time_partitioning else None) or \
           (t.range_partitioning.field if t.range_partitioning else None)
    r.update(linhas_bq=t.num_rows, gb_bq=round((t.num_bytes or 0) / 1e9, 3),
             modificado_bq=t.modified.date().isoformat(), particao=part,
             cluster=list(t.clustering_fields or []))
    dif = t.num_rows - r["linhas_disco"]
    r["dif"] = dif
    if dif > 0:
        r["estado"] = "atras"
    elif dif < 0:
        r["estado"] = "encolheu"
    elif r["regravado"] and r["modificado_bq"] > r["regravado"]:
        r["estado"] = "mudou"
    else:
        r["estado"] = "em_dia"
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prefixos", nargs="*")
    ap.add_argument("--json", help="grava o resultado completo neste arquivo")
    a = ap.parse_args()

    warnings.filterwarnings("ignore")
    from google.cloud import bigquery as bq
    client = bq.Client(project=JOB_PROJECT)

    linhas = [l for l in catalogo() if l["dataset"] not in FORA
              and (not a.prefixos or any(l["dataset"].startswith(p) for p in a.prefixos))]
    with cf.ThreadPoolExecutor(8) as pool:
        res = list(pool.map(lambda l: consulta(client, l), linhas))

    por = {}
    for r in res:
        por.setdefault(r["estado"], []).append(r)
    print(f"{len(res)} tabelas do espelho do Base dos Dados conferidas pelo metadado do BigQuery")
    for estado in ("em_dia", "atras", "encolheu", "mudou", "sumiu", "sem_acesso", "nao_e_tabela", "erro"):
        if estado in por:
            print(f"  {estado:<13} {len(por[estado])}")

    atras = sorted(por.get("atras", []), key=lambda r: -r["dif"])
    if atras:
        print(f"\natrás: {sum(r['dif'] for r in atras):,} linhas a trazer; "
              f"{sum(1 for r in atras if r['particao'] or r['cluster'])} com partição ou cluster".replace(",", "."))
        print(f"{'tabela':<62}{'faltam':>15}{'gb_bq':>9}  partição/cluster  modificado")
        for r in atras:
            chave = r["particao"] or ",".join(r["cluster"]) or "—"
            print(f"{r['tabela']:<62}{r['dif']:>15,}{r['gb_bq']:>9.2f}  {chave:<16}  {r['modificado_bq']}".replace(",", "."))
    for estado, titulo in (("encolheu", "BigQuery com MENOS linhas que o disco"),
                           ("sumiu", "sumiram do BigQuery"), ("erro", "erro na consulta")):
        if por.get(estado):
            print(f"\n{titulo}:")
            for r in por[estado]:
                print(f"  {r['tabela']:<60} {r.get('dif', r.get('erro', ''))}")
    if por.get("mudou"):
        print(f"\nmesma contagem, regravadas no BigQuery depois do nosso parquet: {len(por['mudou'])} "
              f"({sum(r['gb_bq'] for r in por['mudou']):.1f} GB no BigQuery) — lista no --json")
    if a.json:
        with open(a.json, "w") as f:
            json.dump(res, f, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
