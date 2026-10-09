#!/usr/bin/env python3
"""Traz do Base dos Dados só as partições que mudaram, numa tabela grande do espelho.

    python3 scripts/sync/atualiza_particoes_bq.py --lista grandes.txt            # plano, sem baixar
    python3 scripts/sync/atualiza_particoes_bq.py --lista grandes.txt --apply
    python3 scripts/sync/atualiza_particoes_bq.py br_me_caged.microdados_movimentacao --apply --max-gb 40

Fica entre os dois scripts que já existem: `ressincroniza_bq.py` baixa a tabela
inteira (caro numa tabela de 80 GB em que só o ano corrente andou) e
`sync_drifted_incremental.py` só pega o que passa do máximo local, com `LIMIT`, e
por isso não vê linha nova dentro de partição que já temos.

Aqui a comparação é por partição: conta as linhas de cada valor da coluna de
partição no BigQuery e no disco, e baixa inteira cada partição em que as contagens
diferem (o filtro na coluna de partição faz a consulta varrer só ela). Partição
que não existe no disco entra como arquivo novo. Partição que existe com outra
contagem é trocada: os arquivos antigos vão para `~/backups/particoes_<data>/`,
nunca para o lixo. Isso só é feito quando cada arquivo antigo tem uma partição
só; arquivo que mistura partições é recusado e listado.

O parquet novo sai no tipo de coluna que o disco já tem (a view guarda o schema
da criação). Coluna que só existe de um dos lados, ou valor que não converte,
recusa a tabela.

Nada entra em `~/rodado` antes de a contagem do que foi enviado bater com a do
BigQuery. Arquivo novo tem nome novo, então depois é preciso
`python3 scripts/repara_views_beelink.py --apply`. O COLD só acrescenta: os
arquivos trocados continuam lá e precisam ser podados à mão (ver AGENTS.md).
"""
import argparse
import datetime as dt
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bq_quota  # noqa: E402
from ressincroniza_bq import (BEELINK, BILLING_PROJECT, BQ_PROJECT, ROOT, duck,  # noqa: E402
                              escreve_shards, exige_espaco, exige_sandbox, sh)

ARROW = {"BIGINT": "int64", "INTEGER": "int32", "SMALLINT": "int16", "TINYINT": "int8",
         "DOUBLE": "float64", "FLOAT": "float32", "VARCHAR": "string", "BOOLEAN": "bool_",
         "DATE": "date32", "TIME": "time64[us]", "TIMESTAMP": "timestamp[us]",
         "TIMESTAMP WITH TIME ZONE": "timestamp[us, tz=UTC]", "BLOB": "binary"}


def tipo_arrow(pa, duck_tipo):
    if duck_tipo.startswith("DECIMAL("):
        p, s = duck_tipo[8:-1].split(",")
        return pa.decimal128(int(p), int(s))
    nome = ARROW.get(duck_tipo)
    if nome is None:
        return None
    if "[" in nome:
        return {"time64[us]": pa.time64("us"), "timestamp[us]": pa.timestamp("us"),
                "timestamp[us, tz=UTC]": pa.timestamp("us", tz="UTC")}[nome]
    return getattr(pa, nome)()


def literal(v, tipo):
    return str(v) if tipo in ("INTEGER", "INT64") else f"'{v}'"


def planeja(client, bq, alvo):
    """Compara contagem por partição. Devolve o plano ou {'erro': ...}."""
    ds, tb = alvo.split(".", 1)
    t = client.get_table(f"{BQ_PROJECT}.{ds}.{tb}")
    col = (t.range_partitioning.field if t.range_partitioning else
           t.time_partitioning.field if t.time_partitioning else None)
    if not col:
        return {"tabela": alvo, "erro": "sem coluna de partição"}
    tipo = next(f.field_type for f in t.schema if f.name == col)
    remoto = f"{ROOT}/{ds}/{tb}"

    # contagem por partição no BigQuery: lê só a coluna de partição
    sql = f"SELECT CAST({col} AS STRING) p, count(*) n FROM `{BQ_PROJECT}.{ds}.{tb}` GROUP BY 1"
    seco = client.query(sql, job_config=bq.QueryJobConfig(dry_run=True, use_query_cache=False))
    # tabela com row-level security (BD Pro) não devolve estimativa no dry-run, e a
    # consulta só enxerga as linhas liberadas: a conta é feita pelo metadado, e as
    # contagens abaixo são as do que dá para baixar, não as da tabela inteira
    restrita = seco.total_bytes_processed is None
    por_linha = t.num_bytes / max(t.num_rows, 1)
    if not bq_quota.reserve(t.num_rows * 8 if restrita else seco.total_bytes_processed):
        return {"tabela": alvo, "erro": f"cota do mês: {bq_quota.status()}"}
    no_bq = {r.p: r.n for r in client.query(sql).result()}

    local = duck(f"SELECT CAST({col} AS VARCHAR) p, filename f, count(*) n "
                 f"FROM read_parquet('{remoto}/*.parquet', filename=true, union_by_name=true) "
                 f"GROUP BY ALL;", timeout=3600)
    if local is None:
        return {"tabela": alvo, "erro": "não consegui ler o disco"}
    no_disco, arquivos, mistura = {}, {}, {}
    for r in local:
        no_disco[r["p"]] = no_disco.get(r["p"], 0) + r["n"]
        arquivos.setdefault(r["p"], set()).add(r["f"])
        mistura.setdefault(r["f"], set()).add(r["p"])

    mudou, recusadas = [], []
    for p, n in sorted(no_bq.items(), key=lambda kv: str(kv[0])):
        if p is None or no_disco.get(p) == n:
            continue
        antigos = sorted(arquivos.get(p, []))
        if any(len(mistura[f]) > 1 for f in antigos):
            recusadas.append((p, no_disco.get(p, 0), n))
            continue
        mudou.append({"p": p, "disco": no_disco.get(p, 0), "bq": n, "antigos": antigos})
    so_disco = sorted(str(p) for p in no_disco if p not in no_bq)

    custo = 0
    if mudou:
        lista = ", ".join(literal(m["p"], tipo) for m in mudou)
        seco = client.query(f"SELECT * FROM `{BQ_PROJECT}.{ds}.{tb}` WHERE {col} IN ({lista})",
                            job_config=bq.QueryJobConfig(dry_run=True, use_query_cache=False))
        custo = seco.total_bytes_processed
        if custo is None:
            custo = int(sum(m["bq"] for m in mudou) * por_linha)
    return {"tabela": alvo, "col": col, "tipo": tipo, "restrita": restrita, "por_linha": por_linha, "mudou": mudou, "recusadas": recusadas,
            "so_disco": so_disco, "custo": custo,
            "falta": sum(m["bq"] - m["disco"] for m in mudou)}


def conforma(pa, lotes, alvo_schema):
    """Converte cada lote para o schema do disco; estoura se um valor não converte."""
    for lote in lotes:
        yield from (pa.Table.from_batches([lote]).select(alvo_schema.names)
                    .cast(alvo_schema).to_batches())


def aplica(client, leitor, bq, pa, pq, plano, backup, reserva_gb):
    alvo = plano["tabela"]
    ds, tb = alvo.split(".", 1)
    remoto = f"{ROOT}/{ds}/{tb}"
    col, tipo = plano["col"], plano["tipo"]

    desc = duck(f"DESCRIBE SELECT * FROM read_parquet('{remoto}/*.parquet', union_by_name=true);")
    campos = []
    for c in desc or []:
        ta = tipo_arrow(pa, c["column_type"])
        if ta is None:
            return {"tabela": alvo, "erro": f"tipo sem conversão: {c['column_name']} {c['column_type']}"}
        campos.append(pa.field(c["column_name"], ta))
    alvo_schema = pa.schema(campos)
    cols_bq = {f.name for f in client.get_table(f"{BQ_PROJECT}.{ds}.{tb}").schema}
    if cols_bq != set(alvo_schema.names):
        return {"tabela": alvo, "erro": "colunas diferem: só no BigQuery "
                f"{sorted(cols_bq - set(alvo_schema.names))}, só no disco "
                f"{sorted(set(alvo_schema.names) - cols_bq)}"}

    feitas = []
    for m in plano["mudou"]:
        where = f"{col} = {literal(m['p'], tipo)}"
        sql = f"SELECT * FROM `{BQ_PROJECT}.{ds}.{tb}` WHERE {where}"
        seco = client.query(sql, job_config=bq.QueryJobConfig(dry_run=True, use_query_cache=False))
        estimado = seco.total_bytes_processed
        if estimado is None:
            estimado = int(m["bq"] * plano["por_linha"])
        falta = exige_espaco(estimado, reserva_gb)
        if falta:
            return {"tabela": alvo, "erro": falta, "feitas": feitas}
        if not bq_quota.reserve(estimado):
            return {"tabela": alvo, "erro": f"cota do mês: {bq_quota.status()}", "feitas": feitas}
        novo = f"{remoto}/.novo_{m['p']}"
        with tempfile.TemporaryDirectory() as tmp:
            local = Path(tmp) / "p"
            local.mkdir()
            lotes = client.query(sql).result().to_arrow_iterable(bqstorage_client=leitor)
            try:
                n, schema = escreve_shards(conforma(pa, lotes, alvo_schema), local, pq)
            except (pa.ArrowInvalid, pa.ArrowNotImplementedError, KeyError) as exc:
                return {"tabela": alvo, "erro": f"{where}: não converte para o schema do disco: "
                        f"{str(exc)[:150]}", "feitas": feitas}
            if n != m["bq"]:
                return {"tabela": alvo, "erro": f"{where}: baixei {n}, o BigQuery dizia {m['bq']}",
                        "feitas": feitas}
            sh(f"rm -rf {novo} && mkdir -p {novo}", check=True)
            r = subprocess.run(["rsync", "-a", f"{local}/", f"{BEELINK}:{novo}/"],
                               capture_output=True, text=True, timeout=7200)
            if r.returncode != 0:
                sh(f"rm -rf {novo}")
                return {"tabela": alvo, "erro": f"rsync: {r.stderr[:200]}", "feitas": feitas}
        conf = duck(f"SELECT count(*) n, count(*) FILTER (WHERE CAST({col} AS VARCHAR) = '{m['p']}') na "
                    f"FROM read_parquet('{novo}/*.parquet');")
        if not conf or conf[0]["n"] != m["bq"] or conf[0]["na"] != m["bq"]:
            return {"tabela": alvo, "erro": f"{where}: conferência no beelink falhou ({conf})",
                    "feitas": feitas}
        # troca: antigos para o backup, novos entram com o próximo nome numérico livre
        dest = f"{backup}/{ds}/{tb}"
        antigos = " ".join(f"'{f}'" for f in m["antigos"])
        mover = f"mkdir -p {dest} && mv {antigos} {dest}/ && " if m["antigos"] else ""
        sh(f"set -e; cd {remoto}; {mover}"
           f"i=0; for f in $(ls .novo_{m['p']}/*.parquet | sort); do "
           f"while [ -e $(printf '%012d.parquet' $i) ]; do i=$((i+1)); done; "
           f"mv $f $(printf '%012d.parquet' $i); chmod 664 $(printf '%012d.parquet' $i); done; "
           f"rmdir .novo_{m['p']}", check=True)
        print(f"    {where}: {m['disco']:,} -> {m['bq']:,}", flush=True)
        feitas.append(m["p"])

    lista = ", ".join(f"'{p}'" for p in feitas)
    dep = duck(f"SELECT CAST({col} AS VARCHAR) p, count(*) n FROM read_parquet('{remoto}/*.parquet', "
               f"union_by_name=true) WHERE CAST({col} AS VARCHAR) IN ({lista}) GROUP BY 1;", timeout=3600)
    obtido = {r["p"]: r["n"] for r in dep or []}
    errado = [m["p"] for m in plano["mudou"] if obtido.get(m["p"]) != m["bq"]]
    if errado:
        return {"tabela": alvo, "erro": f"contagem final diverge nas partições {errado}", "feitas": feitas}
    return {"tabela": alvo, "feitas": feitas, "ganho": plano["falta"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tabelas", nargs="*", help="dataset.tabela")
    ap.add_argument("--lista", help="arquivo com um dataset.tabela por linha")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--max-gb", type=float, default=30.0,
                    help="recusa a tabela cujas partições a trazer passem disto (padrão 30 GB)")
    ap.add_argument("--reserva-gb", type=float, default=100.0)
    ap.add_argument("--json", help="grava o plano neste arquivo")
    ap.add_argument("--plano", help="plano gravado por --json: as tabelas que estão nele não são "
                                    "contadas de novo (a contagem por partição gasta cota)")
    a = ap.parse_args()
    alvos = list(a.tabelas)
    if a.lista:
        alvos += [l.strip() for l in Path(a.lista).read_text().split("\n")
                  if l.strip() and not l.startswith("#")]
    if not alvos:
        sys.exit("nada a fazer: passe tabelas ou --lista")

    import warnings
    warnings.filterwarnings("ignore")
    import pyarrow as pa
    import pyarrow.parquet as pq
    from google.cloud import bigquery as bq
    from google.cloud import bigquery_storage

    exige_sandbox()
    client = bq.Client(project=BILLING_PROJECT)
    leitor = bigquery_storage.BigQueryReadClient()
    backup = f"~/backups/particoes_{dt.datetime.now():%Y%m%d_%H%M}"
    planos, res = [], []
    prontos = {}
    if a.plano:
        prontos = {p["tabela"]: p for p in json.loads(Path(a.plano).read_text()) if not p.get("erro")}
    for alvo in alvos:
        try:
            p = prontos.get(alvo) or planeja(client, bq, alvo)
        except Exception as exc:                                  # noqa: BLE001
            p = {"tabela": alvo, "erro": str(exc)[:200]}
        planos.append(p)
        if p.get("erro"):
            print(f"  {alvo:55} ERRO {p['erro']}", flush=True)
            continue
        parts = ", ".join(f"{m['p']} ({m['disco']:,}->{m['bq']:,})" for m in p["mudou"]) or "nada"
        print(f"  {alvo:55} {p['custo']/1e9:7.1f} GB  {p['falta']:+,}  "
              f"{'[restrita] ' if p.get('restrita') else ''}{parts}", flush=True)
        for q, nd, nb in p["recusadas"]:
            print(f"      recusada {q}: arquivo mistura partições ({nd:,} -> {nb:,})", flush=True)
        if p["so_disco"]:
            print(f"      só no disco: {', '.join(p['so_disco'][:12])}", flush=True)
        if not a.apply or not p["mudou"]:
            continue
        if p["custo"] / 1e9 > a.max_gb:
            print(f"      pulada: {p['custo']/1e9:.1f} GB passa de --max-gb={a.max_gb}", flush=True)
            continue
        try:
            r = aplica(client, leitor, bq, pa, pq, p, backup, a.reserva_gb)
        except Exception as exc:                                  # noqa: BLE001
            r = {"tabela": alvo, "erro": str(exc)[:300]}
        res.append(r)
        print(f"      {'ERRO ' + r['erro'] if r.get('erro') else 'ok, ' + format(r['ganho'], '+,') + ' linhas'}",
              flush=True)
    if a.json:
        Path(a.json).write_text(json.dumps(planos, indent=1, default=list))
    print(f"\ncusto total do plano: {sum(p.get('custo', 0) for p in planos)/1e9:.1f} GB; {bq_quota.status()}")
    if a.apply:
        print(f"antigos em {backup}; agora rode: python3 scripts/repara_views_beelink.py --apply")
    return 1 if any(r.get("erro") for r in res) else 0


if __name__ == "__main__":
    sys.exit(main())
