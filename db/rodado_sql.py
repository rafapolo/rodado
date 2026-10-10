"""Núcleo do db.rodado.xyz: uma conexão DuckDB travada por consulta.

Usado pelo terminal (terminal.py, via ttyd) e pelo endpoint HTTP (consulta.py).
Roda no beelink, onde está o dado. Não é o CLI do DuckDB de propósito: o
`-safe` do CLI trava a configuração antes de qualquer `-cmd`, então não dá para
liberar só `~/rodado`; sem ele, `.shell` vira shell no beelink e
`COPY ... TO '~/rodado/...'` sobrescreve parquet do espelho.

Cada consulta abre e fecha a própria conexão `read_only`: uma aba esquecida não
segura o arquivo nem enxerga views velhas depois de um reparo.
"""

import os
import threading

import duckdb

HOME = os.path.expanduser("~")
BANCO = os.environ.get("RODADO_DB", f"{HOME}/rodado/basedosdados.duckdb")
TEMPO_LIMITE = int(os.environ.get("RODADO_TEMPO_LIMITE", "300"))

# Mais magro que o ~/.duckdbrc (16 GB / 14 threads): várias sessões web
# convivem com o llama-server e com as consultas das outras sessões.
_CONFIG = {
    "memory_limit": os.environ.get("RODADO_MEMORIA", "6GB"),
    "threads": int(os.environ.get("RODADO_THREADS", "4")),
    "temp_directory": f"{HOME}/duckdb_tmp/web",
    "max_temp_directory_size": "30GB",
}

# Só SELECT: DESCRIBE, SHOW, SUMMARIZE, FROM-first e os PRAGMA de leitura o
# parser já entrega como SELECT. EXPLAIN fica de fora porque EXPLAIN ANALYZE
# executa o que estiver dentro (um COPY, por exemplo).
_PERMITIDOS = {duckdb.StatementType.SELECT}


class ConsultaRecusada(Exception):
    pass


def conecta() -> duckdb.DuckDBPyConnection:
    os.makedirs(_CONFIG["temp_directory"], exist_ok=True)
    con = duckdb.connect(BANCO, read_only=True, config=_CONFIG)
    # A ordem importa: allowed_directories antes de desligar o acesso externo,
    # e a trava por último, para a própria consulta não poder desfazer nada.
    con.execute(f"SET allowed_directories=['{HOME}/rodado/', '{HOME}/duckdb_tmp/']")
    con.execute("SET enable_external_access=false")
    con.execute("SET lock_configuration=true")
    return con


def separa(con: duckdb.DuckDBPyConnection, sql: str) -> list:
    """Quebra em comandos e recusa o que não for leitura."""
    try:
        comandos = con.extract_statements(sql)
    except duckdb.Error as e:
        raise ConsultaRecusada(str(e)) from None
    if not comandos:
        raise ConsultaRecusada("consulta vazia")
    for c in comandos:
        if c.type not in _PERMITIDOS:
            tipo = str(c.type).removeprefix("StatementType.")
            raise ConsultaRecusada(f"{tipo} não é permitido: só leitura (SELECT, FROM, WITH, DESCRIBE, SHOW, SUMMARIZE)")
    return comandos


class Cronometro:
    """Interrompe a consulta depois de TEMPO_LIMITE segundos."""

    def __init__(self, con, segundos=TEMPO_LIMITE):
        self.estourou = False
        self._timer = threading.Timer(segundos, self._interrompe, args=(con,))

    def _interrompe(self, con):
        self.estourou = True
        con.interrupt()

    def __enter__(self):
        self._timer.start()
        return self

    def __exit__(self, *_):
        self._timer.cancel()
