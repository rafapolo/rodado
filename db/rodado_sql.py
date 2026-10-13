"""Núcleo do db.rodado.xyz: uma conexão DuckDB travada por consulta.

Usado pelo terminal (terminal.py, via ttyd) e pelo endpoint HTTP (consulta.py).
Roda no container do finland e lê os parquet do bucket s3://baseldosdados (Hetzner,
mesma região), por um catálogo de views montado por catalogo.py. Não é o CLI do
DuckDB de propósito: o `-safe` do CLI trava a configuração antes de qualquer `-cmd`,
então não dá para liberar só os prefixos das tabelas; sem ele, `.shell` vira shell.

O processo guarda uma instância `read_only` do catálogo e cada consulta é um cursor
dela: o cache de rodapés de parquet e de metadados HTTP sobrevive entre consultas
(sem ele, cada uma relê pela rede o rodapé de centenas de arquivos). Quando
catalogo.py troca o arquivo, a próxima consulta abre uma instância nova.
"""

import json
import os
import re
import threading

import duckdb

BANCO = os.environ.get("RODADO_DB", "/dados/catalogo.duckdb")
RAIZ = os.environ.get("RODADO_RAIZ", "s3://baseldosdados/")   # onde as views do catálogo leem
# Gambiarra: tabela com cópia no SSD do finland (volume, /dados/local/<dataset>/<tabela>/) é
# lida de lá e não do bucket; catalogo.py troca o caminho ao montar a view.
LOCAL = os.environ.get("RODADO_LOCAL", "/dados/local/")
TEMPO_LIMITE = int(os.environ.get("RODADO_TEMPO_LIMITE", "300"))
TEMP = os.environ.get("RODADO_TEMP", "/tmp/duckdb")

# O finland tem 4 núcleos e 7 GB divididos com gitea, opengist e uqt. As threads passam
# dos núcleos de propósito: ler do S3 é esperar requisição, não CPU (a mesma consulta caiu
# de 23 s para 4 s indo de 4 para 16 threads).
_CONFIG = {
    "memory_limit": os.environ.get("RODADO_MEMORIA", "1500MB"),
    "threads": int(os.environ.get("RODADO_THREADS", "16")),
    "temp_directory": TEMP,
    "max_temp_directory_size": os.environ.get("RODADO_TEMP_MAX", "3GB"),
    # Sob dezenas de requisições simultâneas, o S3 do Hetzner deixa algumas paradas sem
    # responder (um GET de 9 MB que sozinho leva 0,1 s). No padrão (30 s, 3 retries, com
    # keep-alive) a nova tentativa reaproveitava a conexão travada e a consulta morria em
    # ~124 s com "Timeout was reached" — 3 de 4 vezes em br_tse_eleicoes.despesas_candidato,
    # 2026-10-12. Timeout curto + conexão nova a cada requisição: 4 de 4, em 12–38 s.
    "http_timeout": int(os.environ.get("RODADO_HTTP_TIMEOUT", "10")),
    "http_retries": 8,
    "http_retry_backoff": 1.5,
    "http_keep_alive": False,
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
    """Os prefixos que as views leem, um por tabela: é só isso que a consulta pode abrir.

    O bucket espelha ~/rodado do beelink inteiro: tem também scripts, logs, o .duckdb de
    lá e sobras de staging; liberar o prefixo de cada tabela deixa tudo isso fora do
    alcance de read_text/read_blob.
    """
    dirs = set()
    for (sql,) in con.execute("SELECT sql FROM duckdb_views() WHERE NOT internal").fetchall():
        for lit in re.findall(r"'([^']*)'", sql or ""):
            raiz = next((r for r in (RAIZ, LOCAL) if lit.startswith(r)), None)
            if not raiz:
                continue
            partes = []
            for parte in lit[len(raiz):].split("/"):
                if any(ch in parte for ch in "*?[{"):
                    break
                partes.append(parte)
            if partes and "." in partes[-1]:    # arquivo citado pelo nome: libera a pasta dele
                partes.pop()
            partes = [p for p in partes if p]
            # uma view que lesse a raiz do bucket abriria tudo: essa não entra
            if partes:
                dirs.add(raiz + "/".join(partes) + "/")
    return sorted(dirs)


class ConsultaRecusada(Exception):
    pass


_instancia = {"con": None, "arquivo": None}


def _abre() -> duckdb.DuckDBPyConnection:
    """Abre e trava a instância. A ordem importa: extensão e segredo antes de desligar o
    acesso externo, allowed_directories antes disso, e a trava por último, para a própria
    consulta não poder desfazer nada. O temp_directory o DuckDB acrescenta sozinho à lista;
    nenhuma extensão é carregada nem instalada por uma função citada na consulta (st_read
    puxaria o spatial). A chave vai num SECRET, nunca em SET s3_*: current_setting() a
    mostraria, e duckdb_secrets() está na lista de funções recusadas."""
    os.makedirs(TEMP, exist_ok=True)
    con = duckdb.connect(BANCO, read_only=True, config=_CONFIG)
    try:
        con.execute("SET autoinstall_known_extensions=false")
        con.execute("SET autoload_known_extensions=false")
        con.execute("LOAD httpfs")
        con.execute("SET parquet_metadata_cache=true")
        con.execute("SET enable_http_metadata_cache=true")
        con.execute(segredo_s3("rodado_s3"))
        con.execute("SET allowed_directories=?", [_diretorios_das_views(con)])
        con.execute("SET enable_external_access=false")
        con.execute("SET lock_configuration=true")
    except BaseException:
        con.close()
        raise
    return con


def _literal(v: str) -> str:
    return "'" + v.replace("'", "''") + "'"


def segredo_s3(nome: str) -> str:
    """CREATE SECRET do bucket, com a chave do ambiente (S3_KEY/S3_SECRET, do deploy)."""
    return (f"CREATE SECRET {nome} (TYPE s3, KEY_ID {_literal(os.environ['S3_KEY'])}, "
            f"SECRET {_literal(os.environ['S3_SECRET'])}, "
            f"ENDPOINT {_literal(os.environ.get('S3_ENDPOINT', 'hel1.your-objectstorage.com'))}, "
            f"REGION {_literal(os.environ.get('S3_REGIAO', 'hel1'))}, URL_STYLE 'path', "
            f"SCOPE {_literal(RAIZ)})")


def conecta() -> duckdb.DuckDBPyConnection:
    """Um cursor da instância do processo; fechá-lo não fecha a instância.

    Abre outra quando catalogo.py troca o arquivo (rename atômico: o inode muda). A
    instância antiga continua viva enquanto algum cursor dela não fechar.
    """
    with _TRAVA:
        st = os.stat(BANCO)
        arquivo = (st.st_ino, st.st_mtime_ns)
        if _instancia["con"] is None or _instancia["arquivo"] != arquivo:
            _instancia["con"] = _abre()
            _instancia["arquivo"] = arquivo
            global _macros_de_arquivo
            _macros_de_arquivo = None
        base = _instancia["con"]
    con = base.cursor()
    externo, travado = con.execute(
        "SELECT current_setting('enable_external_access'), current_setting('lock_configuration')").fetchone()
    if externo or not travado:
        con.close()
        raise RuntimeError("instância sem trava")
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
