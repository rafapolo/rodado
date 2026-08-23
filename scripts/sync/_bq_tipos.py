#!/usr/bin/env python3
"""Converte o retorno de `bq query --format=json` em Parquet **com tipo**.

Existe por causa dos 80 `tmp*.parquet` de 2026-07-05. Dois scripts de sync faziam

    rows = json.loads(bq_query_output)      # tudo string: o JSON do bq não tem tipo
    table = pa.Table.from_pylist(rows)      # pyarrow infere string em toda coluna
    pq.write_table(table, tempfile...)      # e o rsync levava o nome temporário junto

O resultado foram 154 colunas tipadas viradas string em 38 tabelas — INT64, DOUBLE,
BOOLEAN, DATE, TIMESTAMP, todas BYTE_ARRAY — convivendo no mesmo diretório com o
export bom do BigQuery. As views leem o glob, então `count(*)` saía somado.

Aqui o schema vem do BigQuery (`bq show --schema`) e os valores são convertidos
coluna a coluna antes de virar Arrow. Ver `tasks/tmp_parquet_38.plan`.

**Para código novo, prefira `ressincroniza_bq.py`**, que usa `QueryJob.to_arrow()` da
biblioteca `google-cloud-bigquery`: o Arrow vem tipado direto da API de resultados e o
JSON não entra no caminho, então não há o que reconverter. Este módulo existe para os
dois scripts que já recebem `rows` como JSON do `bq` CLI e seria invasivo reescrever;
ele conserta o tipo depois do estrago, o que é pior que não estragar.
"""
import json
import subprocess

BQ_ARROW = {
    "STRING": "string", "BYTES": "binary", "INTEGER": "int64", "INT64": "int64",
    "FLOAT": "float64", "FLOAT64": "float64", "NUMERIC": "float64",
    "BIGNUMERIC": "float64", "BOOLEAN": "bool", "BOOL": "bool",
    "DATE": "date32", "DATETIME": "timestamp_us", "TIMESTAMP": "timestamp_us_utc",
    "TIME": "time64_us", "GEOGRAPHY": "string", "JSON": "string",
}


def schema_bq(dataset, table, project="basedosdados", billing=None):
    """{coluna: tipo BQ}. Campos REPEATED/RECORD saem como None — ficam string."""
    cmd = ["bq", "show", "--schema", "--format=json"]
    if billing:
        cmd.append(f"--project_id={billing}")
    cmd.append(f"{project}:{dataset}.{table}")
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if out.returncode != 0:
        return {}
    campos = json.loads(out.stdout)
    return {
        c["name"]: (None if c.get("mode") == "REPEATED" or c["type"] == "RECORD"
                    else c["type"])
        for c in campos
    }


def _valor(v, alvo):
    if v is None or v == "":
        return None
    try:
        if alvo == "int64":
            return int(float(v)) if isinstance(v, str) and "." in v else int(v)
        if alvo == "float64":
            return float(v)
        if alvo == "bool":
            return v if isinstance(v, bool) else str(v).lower() in ("true", "1", "t")
        if alvo.startswith("timestamp") and not isinstance(v, str):
            return v
    except (TypeError, ValueError):
        return None
    return v


def para_arrow(rows, tipos):
    """pa.Table tipado. `tipos` é o dict de `schema_bq`; o que faltar vira string."""
    import pyarrow as pa

    if not rows:
        return None
    cols = list(rows[0].keys())
    campos, dados = [], {}
    for c in cols:
        alvo = BQ_ARROW.get((tipos.get(c) or "STRING").upper(), "string")
        dados[c] = [_valor(r.get(c), alvo) for r in rows]
        campos.append(pa.field(c, {
            "string": pa.string(), "binary": pa.binary(), "int64": pa.int64(),
            "float64": pa.float64(), "bool": pa.bool_(), "date32": pa.date32(),
            "timestamp_us": pa.timestamp("us"),
            "timestamp_us_utc": pa.timestamp("us", tz="UTC"),
            "time64_us": pa.time64("us"),
        }[alvo]))
    schema = pa.schema(campos)
    try:
        return pa.Table.from_pydict(dados, schema=schema)
    except (pa.ArrowInvalid, pa.ArrowTypeError):
        # uma coluna não converteu; cai para string nela em vez de perder a tabela
        return pa.Table.from_pydict({c: [None if v is None else str(v) for v in dados[c]]
                                     for c in cols})


def nome_destino(existentes):
    """Próximo `0000000000NN.parquet` livre — nunca deixar o nome do tempfile ir junto."""
    usados = {int(f.split(".")[0]) for f in existentes
              if f.endswith(".parquet") and f.split(".")[0].isdigit()}
    i = 0
    while i in usados:
        i += 1
    return f"{i:012d}.parquet"
