"""Núcleo do db.rodado.xyz: uma conexão DuckDB travada por consulta.

Usado pelo terminal (terminal.py, via ttyd) e pelo endpoint HTTP (consulta.py).
Roda no beelink, onde está o dado. Não é o CLI do DuckDB de propósito: o
`-safe` do CLI trava a configuração antes de qualquer `-cmd`, então não dá para
liberar só `~/rodado`; sem ele, `.shell` vira shell no beelink e
`COPY ... TO '~/rodado/...'` sobrescreve parquet do espelho.

Cada consulta abre e fecha a própria conexão `read_only`: uma aba esquecida não
segura o arquivo nem enxerga views velhas depois de um reparo.
"""

import json
import os
import re
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

_TRAVA = threading.Lock()

# Funções que abrem arquivo, listam diretório ou executam SQL embutido. As views já leem
# os parquet por dentro (o corpo delas não passa por aqui); quem consulta pelo terminal ou
# pelo curl nunca precisa chamar nenhuma destas. json_execute_serialized_sql executa um
# plano serializado, query()/query_table() executam texto: ficam de fora junto.
_FUNCOES_DE_ARQUIVO = {
    "glob", "sniff_csv", "query", "query_table", "json_execute_serialized_sql",
    "duckdb_secrets", "which_secret", "load_aws_credentials", "checkpoint", "force_checkpoint",
    "st_read", "st_read_meta", "st_readosm", "st_readshp", "st_drivers",
    "sqlite_attach", "iceberg_metadata", "iceberg_snapshots",
}
_PREFIXOS_DE_ARQUIVO = ("read_", "parquet_", "postgres_", "mysql_", "sqlite_", "iceberg_", "delta_")
_SUFIXOS_DE_ARQUIVO = ("_scan",)
_macros_de_arquivo = None      # macros do banco que chamam função de arquivo por dentro


def _de_arquivo(nome: str) -> bool:
    nome = nome.lower()
    return (nome in _FUNCOES_DE_ARQUIVO or nome.startswith(_PREFIXOS_DE_ARQUIVO)
            or nome.endswith(_SUFIXOS_DE_ARQUIVO) or nome in (_macros_de_arquivo or ()))


def _carrega_macros(con) -> set:
    """Macros guardadas no banco cujo corpo chama função de arquivo (cnefe_map(path) é um
    read_csv(path) disfarçado): o corpo de uma macro não aparece na árvore da consulta."""
    global _macros_de_arquivo
    if _macros_de_arquivo is None:
        corpos = {nome.lower(): {f.lower() for f in re.findall(r"([A-Za-z_]\w*)\s*\(", corpo)}
                  for nome, corpo in con.execute(
                      "SELECT function_name, coalesce(macro_definition, '') FROM duckdb_functions() "
                      "WHERE NOT internal AND function_type IN ('macro', 'table_macro')").fetchall()}
        # ponto fixo: macro que chama macro de arquivo também é de arquivo
        _macros_de_arquivo = set()
        while True:
            novas = {m for m, fs in corpos.items() if m not in _macros_de_arquivo and any(_de_arquivo(f) for f in fs)}
            if not novas:
                break
            _macros_de_arquivo |= novas
    return _macros_de_arquivo


def _diretorios_das_views(con) -> list:
    """Os diretórios que as views leem, um por tabela: é só isso que a consulta pode abrir.

    `~/rodado` inteiro tem também scripts, logs, o próprio .duckdb e sobras de staging;
    liberar o diretório de cada tabela deixa tudo isso fora do alcance de read_text/read_blob.
    """
    raiz = os.path.join(HOME, "rodado") + os.sep
    dirs = set()
    for (sql,) in con.execute("SELECT sql FROM duckdb_views() WHERE NOT internal").fetchall():
        for lit in re.findall(r"'([^']*)'", sql or ""):
            if not (lit.startswith("~/rodado/") or lit.startswith(raiz)):
                continue
            partes = []
            for parte in os.path.expanduser(lit).split("/"):
                if any(ch in parte for ch in "*?[{"):
                    break
                partes.append(parte)
            caminho = os.path.normpath("/".join(partes) or "/")
            if not os.path.isdir(caminho):      # arquivo citado pelo nome: libera a pasta dele
                caminho = os.path.dirname(caminho)
            caminho = caminho.rstrip("/") + "/"
            # uma view que lesse ~/rodado/*.parquet abriria a raiz inteira: essa não entra
            if caminho.startswith(raiz) and caminho != raiz:
                dirs.add(caminho)
    return sorted(dirs)


class ConsultaRecusada(Exception):
    pass


def conecta() -> duckdb.DuckDBPyConnection:
    os.makedirs(_CONFIG["temp_directory"], exist_ok=True)
    con = duckdb.connect(BANCO, read_only=True, config=_CONFIG)
    # A ordem importa: allowed_directories antes de desligar o acesso externo,
    # e a trava por último, para a própria consulta não poder desfazer nada.
    # Duas conexões vivas no mesmo processo dividem a mesma instância do banco (o terminal abre
    # uma segunda na thread que busca colunas para o autocompletar). Na instância já configurada
    # os SET falham ("configuration has been locked", ou "cannot change allowed_directories when
    # enable_external_access is disabled"); a trava de processo impede que duas configurem ao
    # mesmo tempo, e quem chega depois só confere que a instância está como queremos.
    # O temp_directory o próprio DuckDB acrescenta à lista; nenhuma extensão é carregada
    # nem instalada por conta de uma função citada na consulta (st_read puxaria o spatial).
    with _TRAVA:
        try:
            con.execute("SET autoinstall_known_extensions=false")
            con.execute("SET autoload_known_extensions=false")
            dirs = _diretorios_das_views(con)
            con.execute("SET allowed_directories=?", [dirs])
            con.execute("SET enable_external_access=false")
            con.execute("SET lock_configuration=true")
        except duckdb.Error:
            externo, travado, carrega = con.execute(
                "SELECT current_setting('enable_external_access'), current_setting('lock_configuration'), "
                "current_setting('autoload_known_extensions')").fetchone()
            if externo or not travado or carrega:
                con.close()
                raise
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
        _confere_arvore(con, c.query)
    return comandos


def _confere_arvore(con, sql: str) -> None:
    """Recusa função de arquivo e FROM '<caminho>' em qualquer ponto da consulta.

    Segunda camada além do allowed_directories: lê a árvore do parser (CTE, LATERAL,
    subconsulta, UNION, nome entre aspas), não o texto. Se o DuckDB não serializar a
    consulta, ela não roda.
    """
    _carrega_macros(con)
    try:
        arvore = json.loads(con.execute("SELECT json_serialize_sql(?)", [sql]).fetchone()[0])
    except (duckdb.Error, TypeError, ValueError):
        raise ConsultaRecusada("consulta não pôde ser conferida") from None
    if arvore.get("error"):
        raise ConsultaRecusada(arvore.get("error_message") or "consulta não pôde ser conferida")
    pilha = [arvore]
    while pilha:
        no = pilha.pop()
        if isinstance(no, list):
            pilha.extend(no)
            continue
        if not isinstance(no, dict):
            continue
        nome = str(no.get("function_name") or "").lower()
        if nome and _de_arquivo(nome):
            raise ConsultaRecusada(f"{nome}() não é permitido: acesso direto a arquivo; consulte as views (dataset.tabela)")
        if no.get("type") == "BASE_TABLE" and re.search(r"[/\\.:]", str(no.get("table_name") or "")):
            raise ConsultaRecusada("ler arquivo pelo caminho não é permitido; consulte as views (dataset.tabela)")
        pilha.extend(no.values())


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
