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
coluna a coluna antes de virar Arrow.

**Para código novo, prefira `ressincroniza_bq.py`**, que usa `QueryJob.to_arrow()` da
biblioteca `google-cloud-bigquery`: o Arrow vem tipado direto da API de resultados e o
JSON não entra no caminho, então não há o que reconverter. Este módulo existe para os
dois scripts que já recebem `rows` como JSON do `bq` CLI e seria invasivo reescrever;
ele conserta o tipo depois do estrago, o que é pior que não estragar.
"""
import datetime as dt
import json
import subprocess
import sys

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


def _instante(v, utc):
    """String de data-hora do `bq` -> datetime. TIMESTAMP sai como epoch em segundos
    (`"1577836800.0"`); DATE e DATETIME saem em ISO. Aceita os dois."""
    if isinstance(v, dt.datetime):
        d = v
    else:
        texto = str(v).strip()
        try:
            d = dt.datetime.fromtimestamp(float(texto), dt.timezone.utc)
        except (ValueError, OSError, OverflowError):
            d = dt.datetime.fromisoformat(
                texto.replace("Z", "+00:00").replace(" ", "T", 1))
    if utc:
        return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)
    return d.replace(tzinfo=None) if d.tzinfo else d


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
        if alvo == "date32":
            if isinstance(v, dt.date) and not isinstance(v, dt.datetime):
                return v
            return dt.date.fromisoformat(str(v)[:10])
        if alvo.startswith("timestamp"):
            return _instante(v, utc=alvo.endswith("utc"))
        if alvo == "time64_us":
            return v if isinstance(v, dt.time) else dt.time.fromisoformat(str(v))
    except (TypeError, ValueError, OSError, OverflowError):
        return None
    return v


def para_arrow(rows, tipos):
    """pa.Table tipado. `tipos` é o dict de `schema_bq`; o que faltar vira string.

    Cada coluna é montada e validada **sozinha**: se uma não converter, só ela cai
    para string e as outras seguem tipadas. Montar tudo de uma vez, como antes,
    fazia uma única coluna ruim derrubar a tabela inteira para string — que é
    exatamente o estrago que este módulo existe para evitar.
    """
    import pyarrow as pa

    if not rows:
        return None

    arrow = {
        "string": pa.string(), "binary": pa.binary(), "int64": pa.int64(),
        "float64": pa.float64(), "bool": pa.bool_(), "date32": pa.date32(),
        "timestamp_us": pa.timestamp("us"),
        "timestamp_us_utc": pa.timestamp("us", tz="UTC"),
        "time64_us": pa.time64("us"),
    }

    cols = list(rows[0].keys())
    campos, arrays = [], []
    for c in cols:
        alvo = BQ_ARROW.get((tipos.get(c) or "STRING").upper(), "string")
        tipo = arrow[alvo]
        try:
            arr = pa.array([_valor(r.get(c), alvo) for r in rows], type=tipo)
        except (pa.ArrowInvalid, pa.ArrowTypeError, TypeError, ValueError,
                OverflowError):
            arr = pa.array([None if r.get(c) is None else str(r.get(c)) for r in rows],
                           type=pa.string())
            tipo = pa.string()
        # `_valor` devolve None no que nao converte. Uma coluna que chega cheia e sai
        # toda nula nao levanta erro nenhum — some calada, que e o modo de falha caro
        # aqui. Avisa; nao aborta, porque a coluna pode ser nula na origem mesmo.
        if arr.null_count == len(rows) and any(
            r.get(c) not in (None, "") for r in rows
        ):
            print(f"  ! coluna '{c}' ({tipos.get(c)}) tinha valor e converteu toda "
                  f"para NULL como {tipo}", file=sys.stderr)
        campos.append(pa.field(c, tipo))
        arrays.append(arr)
    return pa.Table.from_arrays(arrays, schema=pa.schema(campos))


def nome_destino(existentes):
    """Próximo `0000000000NN.parquet` livre — nunca deixar o nome do tempfile ir junto."""
    usados = {int(f.split(".")[0]) for f in existentes
              if f.endswith(".parquet") and f.split(".")[0].isdigit()}
    i = 0
    while i in usados:
        i += 1
    return f"{i:012d}.parquet"
