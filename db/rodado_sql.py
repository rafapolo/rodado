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
from duckdb import sqltypes

BANCO = os.environ.get("RODADO_DB", "/dados/catalogo.duckdb")
RAIZ = os.environ.get("RODADO_RAIZ", "s3://baseldosdados/")   # onde as views do catálogo leem
# Gambiarra: tabela com cópia no SSD do finland (volume, /dados/local/<dataset>/<tabela>/) é
# lida de lá e não do bucket; catalogo.py troca o caminho ao montar a view.
LOCAL = os.environ.get("RODADO_LOCAL", "/dados/local/")
CA_BUNDLE = os.environ.get("RODADO_CA_BUNDLE", "/etc/ssl/certs/ca-certificates.crt")
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
    # Instância :memory: nova + ATTACH, nunca duckdb.connect(BANCO): o DuckDB reaproveita a
    # instância viva do mesmo caminho, e depois que catalogo.py troca o arquivo isso devolvia
    # a antiga, já travada — todo SET daqui falhava e /catalogo.json dava 500 até reiniciar.
    con = duckdb.connect(":memory:", config=_CONFIG)
    try:
        con.execute(f"ATTACH {_literal(BANCO)} AS catalogo (READ_ONLY)")
        con.execute("USE catalogo")
        con.execute("SET autoinstall_known_extensions=false")
        con.execute("SET autoload_known_extensions=false")
        con.execute("LOAD httpfs")
        con.execute("SET parquet_metadata_cache=true")
        con.execute("SET enable_http_metadata_cache=true")
        con.execute(segredo_s3("rodado_s3"))
        con.create_function("_mascara_cpf", mascara_texto, [sqltypes.VARCHAR], sqltypes.VARCHAR,
                            side_effects=False)
        con.execute("SET allowed_directories=?", [_diretorios_das_views(con)])
        # DuckDB 2.0: o httpfs lê o bundle de CA do disco e o allowed_directories o barra
        con.execute("SET allowed_paths=?", [[CA_BUNDLE]])
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
    con.execute("USE catalogo")   # o USE vale por conexão: cada cursor nasce em memory
    externo, travado = con.execute(
        "SELECT current_setting('enable_external_access'), current_setting('lock_configuration')").fetchall()[0]
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
        arvore = json.loads(con.execute("SELECT json_serialize_sql(?)", [sql]).fetchall()[0][0])
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
    _confere_cpf(con, arvore)


# ---------------------------------------------------------------------------- CPF na saída
# A máscara da saída (mascara_cpf, abaixo) olha tipo e valor: `CAST(cpf AS BIGINT) AS n`,
# `cpf::BLOB`, `split(cpf, '')`, `substr` em dois pedaços ou uma conta devolviam o CPF inteiro
# (conferido em 2026-11-11). Esta regra fecha isso pela árvore do parser: coluna com "cpf" no
# nome pode ser filtrada, juntada, agrupada e ordenada à vontade, mas no que a consulta devolve
# só aparece pura (e a máscara a pega), passada adiante sem mudar (CASE, coalesce, min/max),
# dentro de uma condição (=, IN, IS NULL…) ou contada (count, approx_count_distinct). E não
# pode trocar de nome para um sem "cpf" (alias, CTE com colunas, `* RENAME`, UNION por posição,
# UNPIVOT), senão a transformação viria um nível acima com outro nome. Colunas mistas
# (`cpf_cnpj`) entram também: 8 dígitos de um CPF somados ao miolo que a máscara mostra o
# remontam. O que segue aberto está em tasks/plans/limites_abuso_db.md.

_NOME_CPF = re.compile(r"cpf", re.I)
# o valor sai igual (a máscara da saída o pega)
_PASSA = {"coalesce", "ifnull", "nullif", "min", "max", "any_value", "first", "last", "arbitrary",
          "arg_min", "arg_max", "argmin", "argmax", "min_by", "max_by"}
# o resultado é um número que não carrega o CPF
_CONTA = {"count", "approx_count_distinct", "count_star"}
_BOOL_OPERADORES = {"OPERATOR_IS_NULL", "OPERATOR_IS_NOT_NULL", "COMPARE_IN", "COMPARE_NOT_IN", "OPERATOR_NOT"}
# chaves da árvore em que a coluna não vira valor de saída
_CHAVES_LIVRES = {"partitions", "orders", "filter", "filter_expr", "when_expr", "order_bys"}

_DICA_CPF = ("coluna de CPF só sai pura (mascarada) ou contada: filtre, junte, agrupe e ordene por ela "
             "à vontade (WHERE, JOIN, GROUP BY), conte com count(DISTINCT …), mas não a transforme "
             "(CAST, substr, split, list, to_json…) nem a renomeie para um nome sem \"cpf\". Coluna mista "
             "(cpf_cnpj): para a raiz do CNPJ, CASE WHEN length(regexp_replace(col, '[^0-9]', '', 'g')) = 14 "
             "THEN substr(regexp_replace(col, '[^0-9]', '', 'g'), 1, 8) END")


def _cpf(nome) -> bool:
    return bool(nome) and bool(_NOME_CPF.search(str(nome)))


def _recusa_cpf(motivo: str):
    raise ConsultaRecusada(f"{motivo} — {_DICA_CPF}")


def _ref_cpf(no) -> bool:
    return isinstance(no, dict) and no.get("class") == "COLUMN_REF" and _cpf((no.get("column_names") or [""])[-1])


def _so_cnpj(quando, coluna) -> bool:
    """`length(regexp_replace(<coluna>, '[^0-9]', '', 'g')) = 14`: a condição que só deixa CNPJ.
    `length(<coluna>) = 14` sozinho não serve: CPF formatado (000.000.000-00) também tem 14."""
    if not isinstance(quando, dict) or quando.get("type") != "COMPARE_EQUAL":
        return False
    lados = [quando.get("left"), quando.get("right")]

    def texto(no):
        return (no or {}).get("literal", {}).get("text") if (no or {}).get("class") == "CONSTANT" else None

    def args(no):
        return [a.get("expression") for a in (no or {}).get("arguments") or []] or (no or {}).get("children") or []

    for f, k in (lados, lados[::-1]):
        if texto(k) != "14" or (f or {}).get("function_name", "").lower() not in ("length", "len", "strlen", "char_length"):
            continue
        a = args(f)
        if len(a) != 1 or (a[0] or {}).get("function_name", "").lower() != "regexp_replace":
            continue
        r = args(a[0])
        if len(r) >= 3 and (r[0] or {}).get("class") == "COLUMN_REF" \
                and (r[0].get("column_names") or [""])[-1].lower() == coluna.lower() \
                and texto(r[1]) in ("[^0-9]", "\\D") and texto(r[2]) == "" and (len(r) == 3 or texto(r[3]) == "g"):
            return True
    return False


def _confere_expressao(expr, linhas_de_tabela) -> bool:
    """Recusa se a expressão transforma coluna de CPF (ou a linha inteira de uma tabela, ou um
    `COLUMNS(*)`); devolve True se o valor do CPF chega à saída sem mudar."""
    carrega = False
    pilha = [(expr, ())]          # (nó, ancestrais como (nó, chave))
    while pilha:
        no, anc = pilha.pop()
        if isinstance(no, list):
            pilha.extend((x, anc) for x in no)
            continue
        if not isinstance(no, dict):
            continue
        if no.get("class") == "SUBQUERY":        # a consulta de dentro é conferida por conta própria
            continue
        nomes = no.get("column_names") or []
        alvo = (_ref_cpf(no) or (no.get("class") == "COLUMN_REF" and len(nomes) == 1 and nomes[0].lower() in linhas_de_tabela)
                or (no.get("class") == "STAR" and anc))
        if alvo:
            # da saída para dentro: a primeira condição ou contagem neutraliza o que vem abaixo
            # (`length(cpf) = 11` devolve booleano); a primeira transformação antes disso recusa
            passa = True
            coluna = (nomes or [""])[-1]
            for pai, chave in anc:
                if chave == "then_expr" and "cnpj" in coluna.lower() and _so_cnpj(pai.get("when_expr"), coluna):
                    passa = False      # coluna mista dentro de um ramo que só aceita CNPJ
                    break
                classe, tipo = pai.get("class"), pai.get("type")
                funcao = str(pai.get("function_name") or "").lower()
                if chave in _CHAVES_LIVRES or classe in ("COMPARISON", "CONJUNCTION", "BETWEEN") \
                        or (classe == "OPERATOR" and tipo in _BOOL_OPERADORES) \
                        or (classe in ("FUNCTION", "WINDOW", "AGGREGATE") and funcao in _CONTA):
                    passa = False
                    break
                if not classe or classe == "CASE" \
                        or (classe in ("FUNCTION", "AGGREGATE", "WINDOW") and funcao in _PASSA):
                    continue           # entrada de CASE/ORDER sem classe, ou o valor passa igual
                coluna = ".".join(nomes) or "COLUMNS(*)"
                _recusa_cpf(f"{funcao or tipo or classe}() sobre {coluna} devolveria o CPF sem máscara")
            carrega = carrega or passa
            continue
        for chave, valor in no.items():
            if isinstance(valor, (dict, list)):
                pilha.append((valor, anc + ((no, chave),)))
    return carrega


def _nomes_de_saida(no) -> list:
    """[(nome, carrega_cpf)] das colunas que um nó devolve; None no lugar de uma `*`."""
    while no and no.get("type") == "SET_OPERATION_NODE":
        no = (no.get("children") or [no.get("left")])[0]
    saida = []
    for item in (no or {}).get("select_list") or []:
        if item.get("class") == "STAR":
            saida.append(None)
        elif item.get("class") == "COLUMN_REF":
            nome = item.get("alias") or (item.get("column_names") or [""])[-1]
            saida.append((nome, _ref_cpf(item)))
        else:
            saida.append((item.get("alias") or "", None))   # None: decide quem conferiu o item
    return saida


def _confere_renomeia(nomes_novos, antigos, onde):
    for i, novo in enumerate(nomes_novos):
        if i >= len(antigos) or antigos[i] is None:
            if i < len(antigos):
                _recusa_cpf(f"{onde}: renomear colunas de uma `*` não é permitido quando pode haver CPF")
            continue
        nome, carrega = antigos[i]
        if (carrega or _cpf(nome)) and not _cpf(novo):
            _recusa_cpf(f"{onde}: a coluna {nome} viraria {novo}")


def _colunas_da_tabela(con, no):
    try:
        return [(c, _cpf(c)) for (c,) in con.execute(
            "SELECT column_name FROM duckdb_columns() WHERE schema_name = ? AND table_name = ? ORDER BY column_index",
            [no.get("schema_name") or "main", no.get("table_name")]).fetchall()]
    except duckdb.Error:
        return []


def _confere_cpf(con, arvore) -> None:
    """A regra do CPF na saída, em todo SELECT da consulta (subconsulta, CTE, UNION, LATERAL)."""
    # `SELECT t` devolve a linha inteira da tabela t como struct: conta como coluna de CPF quando
    # t é uma view do catálogo com coluna de CPF e o nome não é também coluna dela (CTE e
    # subconsulta ficam de fora: `cnes` pode ser CTE e coluna ao mesmo tempo)
    linhas_de_tabela = set()
    pilha = [arvore]
    while pilha:
        no = pilha.pop()
        if isinstance(no, list):
            pilha.extend(no)
            continue
        if not isinstance(no, dict):
            continue
        if no.get("type") == "BASE_TABLE" and no.get("schema_name"):
            colunas = _colunas_da_tabela(con, no)
            if any(c for _, c in colunas):
                nomes = {n.lower() for n, _ in colunas}
                for k in ("alias", "table_name"):
                    if no.get(k) and str(no[k]).lower() not in nomes:
                        linhas_de_tabela.add(str(no[k]).lower())
        pilha.extend(v for v in no.values() if isinstance(v, (dict, list)))

    pilha = [arvore]
    while pilha:
        no = pilha.pop()
        if isinstance(no, list):
            pilha.extend(no)
            continue
        if not isinstance(no, dict):
            continue
        tipo = no.get("type")
        if tipo == "SELECT_NODE":
            for item in no.get("select_list") or []:
                if item.get("class") == "STAR":
                    for r in item.get("replace_list") or []:
                        carrega = _confere_expressao(r.get("value"), linhas_de_tabela)
                        if carrega and not _cpf(r.get("key")):
                            _recusa_cpf(f"* REPLACE poria CPF em {r.get('key')}")
                    for r in item.get("rename_list") or []:
                        de = r.get("key") or {}
                        de = (de.get("column") or ".".join(de.get("column_names") or [])) if isinstance(de, dict) else str(de)
                        if _cpf(de) and not _cpf(r.get("value")):
                            _recusa_cpf(f"* RENAME: a coluna {de} viraria {r.get('value')}")
                    if item.get("columns") and item.get("expr") is not None:
                        _confere_expressao(item["expr"], linhas_de_tabela)
                    continue
                carrega = _confere_expressao(item, linhas_de_tabela)
                alias = item.get("alias")
                if carrega and alias and not _cpf(alias):
                    _recusa_cpf(f"a coluna de CPF não pode sair com o nome {alias}")
            for cte in ((no.get("cte_map") or {}).get("map") or []):
                aliases = (cte.get("value") or {}).get("aliases") or []
                if aliases:
                    _confere_renomeia(aliases, _nomes_de_saida((cte.get("value") or {}).get("query_node")),
                                      f"WITH {cte.get('key')}(…)")
        elif tipo == "SET_OPERATION_NODE":
            filhos = no.get("children") or [x for x in (no.get("left"), no.get("right")) if x]
            if filhos:
                base = _nomes_de_saida(filhos[0])
                for filho in filhos[1:]:
                    for i, saida in enumerate(_nomes_de_saida(filho)):
                        if saida is None or i >= len(base) or base[i] is None:
                            continue
                        if (saida[1] or _cpf(saida[0])) and not _cpf(base[i][0]):
                            _recusa_cpf(f"UNION poria a coluna {saida[0]} sob o nome {base[i][0]}")
        elif tipo in ("BASE_TABLE", "SUBQUERY") and no.get("column_name_alias"):
            antigos = (_colunas_da_tabela(con, no) if tipo == "BASE_TABLE"
                       else _nomes_de_saida((no.get("subquery") or {}).get("node")))
            _confere_renomeia(no["column_name_alias"], antigos, f"{no.get('alias') or 'tabela'}(…)")
        elif tipo == "PIVOT":
            fora_da_fonte = {k: v for k, v in no.items() if k != "source"}
            sub = [fora_da_fonte]
            while sub:
                x = sub.pop()
                if isinstance(x, list):
                    sub.extend(x)
                elif isinstance(x, dict):
                    if _ref_cpf(x) or x.get("class") == "STAR" or any(_cpf(n) for n in (x.get("unpivot_names") or [])):
                        _recusa_cpf("PIVOT/UNPIVOT sobre coluna de CPF a tiraria do nome")
                    if any(isinstance(n, str) and _cpf(n) for n in (x.get("pivot_names") or []) + (x.get("entries") or [])):
                        _recusa_cpf("PIVOT/UNPIVOT sobre coluna de CPF a tiraria do nome")
                    sub.extend(v for v in x.values() if isinstance(v, (dict, list)))
        pilha.extend(v for v in no.values() if isinstance(v, (dict, list)))


# CPF nunca sai inteiro: a consulta pode filtrar e juntar pelo CPF completo, mas todo
# resultado (terminal, /query em json/csv/tsv/parquet, o MCP que passa por ele, e as
# mensagens de erro, que podem citar um valor) sai no padrão da CGU, ***.456.789-**.
# A máscara olha o valor e não o nome da coluna, para pegar também `cpf AS x`,
# concatenações e o CPF que a Receita põe no nome do MEI. Casa 11 dígitos, com ou sem
# pontuação, soltos (sem dígito colado nem casa decimal: "140.12558008151" e
# "45097157000.0" passam) e só com dígito verificador de CPF válido. Código público de
# 11 dígitos (id_subdistrito do IBGE, por exemplo) só é mascarado quando o verificador
# bate por acaso, ~1 em 100. CNPJ (14 dígitos ou com barra) nunca casa.
# Duas formas só: 11 dígitos seguidos ou 000.000.000-00 completo (pontuação mista como
# "105794.52000" é número decimal, não CPF). Casa decimal fica de fora: ponto e dígito de
# qualquer lado, ou vírgula e 1-2 dígitos depois ("13203808433,50"); vírgula seguida de 3+
# dígitos é lista ("cpf,cpf") e mascara.
_CPF = re.compile(r"(?<![0-9])(?<![0-9]\.)(?:([0-9]{3})(\.)([0-9]{3})(\.)([0-9]{3})(-)([0-9]{2})"
                  r"|([0-9]{3})()([0-9]{3})()([0-9]{3})()([0-9]{2}))"
                  r"(?![0-9])(?!\.[0-9])(?!,[0-9]{1,2}(?![0-9]))")
_INTEIROS = {"TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT", "UTINYINT", "USMALLINT",
             "UINTEGER", "UBIGINT", "UHUGEINT", "DECIMAL"}


def _cpf_valido(d: str) -> bool:
    if len(set(d)) == 1:
        return False
    for n in (9, 10):
        if (sum(int(d[i]) * (n + 1 - i) for i in range(n)) * 10) % 11 % 10 != int(d[n]):
            return False
    return True


def _troca(m) -> str:
    g = m.groups()
    g = g[:7] if g[0] is not None else g[7:]   # formatado ou 11 dígitos seguidos
    if not _cpf_valido(g[0] + g[2] + g[4] + g[6]):
        return m.group(0)
    return f"***{g[1]}{g[2]}{g[3]}{g[4]}{g[5]}**"


def mascara_texto(s):
    """O texto com todo CPF mascarado (também usado nas mensagens de erro)."""
    if not isinstance(s, str) or not any(c.isdigit() for c in s):
        return s
    return _CPF.sub(_troca, s)


def mascara_cpf(rel):
    """A mesma relação com todo CPF mascarado pela função _mascara_cpf (registrada em
    _abre). Coluna de texto passa por ela; lista de texto, item a item; STRUCT/MAP/UNION
    com texto dentro vira texto (o tipo muda, mas o CPF não escapa por dentro de um
    {'x': cpf}); número em coluna com 'cpf' no nome volta a ter 11 dígitos e é mascarado.
    Referência por posição (#n), porque o resultado pode ter dois nomes iguais."""
    if rel is None:
        return rel
    exprs, mudou = [], False
    for i, (nome, tipo) in enumerate(zip(rel.columns, rel.types), 1):
        t, ref, alias = str(tipo).upper(), f"#{i}", '"' + nome.replace('"', '""') + '"'
        if t in ("VARCHAR", "JSON"):
            e = f"_mascara_cpf({ref})"
        elif t in ("VARCHAR[]", "JSON[]"):
            e = f"list_transform({ref}, lambda x: _mascara_cpf(x))"
        elif "VARCHAR" in t or "JSON" in t or t == "BLOB":
            # BLOB: `cpf::BLOB` saía como bytes do CPF inteiro
            e = f"_mascara_cpf(CAST({ref} AS VARCHAR))"
        # só em nome de coluna: `count_star() FILTER (WHERE cpf …)` é contagem, não CPF
        elif "cpf" in nome.lower() and "(" not in nome and t.split("(")[0] in _INTEIROS:
            e = f"_mascara_cpf(lpad(CAST({ref} AS VARCHAR), 11, '0'))"
        else:
            exprs.append(f"{ref} AS {alias}")
            continue
        exprs.append(f"{e} AS {alias}")
        mudou = True
    return rel.project(", ".join(exprs)) if mudou else rel


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
