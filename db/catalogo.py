#!/usr/bin/env python3
"""Mantém o catálogo do db.rodado.xyz: as views do beelink apontando para o bucket.

Lê s3://baseldosdados/_db/views.json (views e macros, gravado por exporta_views.py no
beelink e levado ao bucket pela sincronização), cria as macros, troca `/home/polo/rodado/` e `~/rodado/` por
`s3://baseldosdados/` e cria cada view num .duckdb novo, que substitui o anterior por
rename atômico. rodado_sql.conecta() percebe a troca e abre uma instância nova.

Criar uma view lê o rodapé de cada parquet que ela cita (79 mil arquivos, ~25 min com
paralelismo), então só remonta quando o views.json ou as cópias no SSD mudam, e só as views
cujo SQL mudou: as outras vêm do catálogo anterior (monta). Views de outros buckets (as
6 do SIPNI, em s3://healthbr-data) ficam de fora: não tinham segredo aqui nem antes.

    python3 catalogo.py            # laço: confere a cada 15 min
    python3 catalogo.py --uma-vez  # monta (se mudou) e sai
    python3 catalogo.py --uma-vez --completo  # monta tudo do zero
"""
import concurrent.futures
import fcntl
import hashlib
import json
import os
import re
import shutil
import sys
import time

import duckdb

import rodado_sql

ORIGEM = rodado_sql.RAIZ + "_db/views.json"
BANCO = rodado_sql.BANCO
BANCO_ANON = rodado_sql.BANCO_ANON
MARCA = BANCO + ".sha256"
FONTES = BANCO + ".fontes.json"   # hash do SQL de cada view criada: o que remontar
FONTES_ANON = BANCO_ANON + ".fontes.json"   # o que o catálogo anônimo guarda: ver monta_anonimo
INTERVALO = int(os.environ.get("RODADO_CATALOGO_INTERVALO", "900"))
PARALELO = int(os.environ.get("RODADO_CATALOGO_PARALELO", "8"))
LOCAIS = ("'/home/polo/rodado/", "'~/rodado/")
_NO_BUCKET = re.compile("'" + re.escape(rodado_sql.RAIZ) + "([^']+)'")


def log(msg):
    print(f"{time.strftime('%F %T')} {msg}", flush=True)


def _conexao(arquivo=":memory:"):
    con = duckdb.connect(arquivo, config={"threads": 32, "memory_limit": "1GB"})
    con.execute("LOAD httpfs")
    con.execute(rodado_sql.segredo_s3("catalogo_s3"))  # temporário: não fica gravado no arquivo
    return con


def baixa_views():
    con = _conexao()
    try:
        texto = con.execute("SELECT content FROM read_text(?)", [ORIGEM]).fetchall()[0][0]
    finally:
        con.close()
    return texto, hashlib.sha256(texto.encode()).hexdigest()


def para_s3(sql: str) -> str:
    for local in LOCAIS:
        sql = sql.replace(local, "'" + rodado_sql.RAIZ)
    # parquet com cópia em /dados/local (mesmo caminho relativo do bucket) é lido do SSD
    return _NO_BUCKET.sub(lambda m: "'" + rodado_sql.LOCAL + m[1] + "'"
                          if os.path.isfile(rodado_sql.LOCAL + m[1]) else m[0], sql)


def _sha(sql: str) -> str:
    return hashlib.sha256(sql.encode()).hexdigest()


# ------------------------------------------------------------------ catálogo anônimo
# Quem consulta sem token pessoal lê um segundo arquivo, com o mesmo nome em cada view, onde toda
# coluna de CPF já sai mascarada (`***.456.789-**`, o padrão da CGU) ANTES de qualquer WHERE, JOIN ou
# GROUP BY: filtrar por CPF inteiro nunca casa, e juntar pelo mascarado (como nos dados do governo)
# continua possível. O arquivo é cópia do inteiro em que só as views com coluna de CPF viram
# `SELECT * REPLACE (rodado_cpf(col) AS col) FROM (<corpo original>)`; o resto não relê rodapé nenhum.
# A máscara é SQL nativo, não UDF: roda em centenas de milhões de linhas e existe quando a view é criada.
#
# Regra (a mesma para coluna pura e mista): valor com `*` fica como está (já mascarado: idempotente);
# o que tiver letra fica como está; com `minimo` a 11 dígitos (1 nas colunas de CPF, 10 nas de documento misto, onde
# 6 dígitos são outro código) vira `***.DDD.DDD-**` pelos dígitos 4 a 9 do CPF
# de 11 casas (zeros à esquerda refeitos); mais de 11 dígitos (CNPJ) fica inteiro.
MACRO_CPF = r"""CREATE OR REPLACE MACRO rodado_cpf(s, minimo) AS
  CASE WHEN s IS NULL THEN NULL
       WHEN length(s) = 11 AND regexp_full_match(s, '[0-9]{11}')
            THEN concat('***.', substr(s, 4, 3), '.', substr(s, 7, 3), '-**')
       WHEN contains(s, '*') OR NOT regexp_full_match(s, '[0-9.\-/ ]*[0-9][0-9.\-/ ]*') THEN s
       WHEN length(regexp_replace(s, '[^0-9]', '', 'g')) NOT BETWEEN minimo AND 11 THEN s
       ELSE concat('***.', substr(lpad(regexp_replace(s, '[^0-9]', '', 'g'), 11, '0'), 4, 3), '.',
                   substr(lpad(regexp_replace(s, '[^0-9]', '', 'g'), 11, '0'), 7, 3), '-**') END"""
# colunas que carregam CPF: "cpf" no nome (cpf, cpf_cnpj, cgccpf, cnpjcpf, CPFCNPJ…) e as de documento
# misto (CPF ou CNPJ) que não têm "cpf" no nome
_DOCUMENTO_MISTO = {"documento", "documento_credor", "documento_contratado", "documento_emissor",
                    "documento_responsavel", "individual_document"}
VERSAO_MASCARA = _sha(MACRO_CPF + "|cpf|" + ",".join(sorted(_DOCUMENTO_MISTO)))[:16]
_CABECALHO_VIEW = re.compile(r'^\s*CREATE\s+(?:OR\s+REPLACE\s+)?VIEW\s+(?:"[^"]*"|[^\s("]+)(?:\.(?:"[^"]*"|[^\s("]+))*\s+AS\s+',
                             re.I)


def coluna_de_cpf(nome: str) -> bool:
    return "cpf" in nome.lower() or nome.lower() in _DOCUMENTO_MISTO


def _aspas(nome: str) -> str:
    return '"' + nome.replace('"', '""') + '"'


def sql_anonimo(sql: str, colunas: list):
    """O CREATE VIEW anônimo de uma view: None se nenhuma coluna carrega CPF (vale o original), o
    SQL com as colunas de CPF mascaradas, ou False se há coluna de CPF e o SQL não pôde ser
    reescrito (a view fica de fora do catálogo anônimo: nunca passa sem máscara)."""
    sensiveis = [(c, t) for c, t in colunas if coluna_de_cpf(c)]
    if not sensiveis:
        return None
    m = _CABECALHO_VIEW.match(sql or "")
    if not m:
        return False
    corpo = sql[m.end():].strip().rstrip(";").strip()
    trocas = []
    for c, t in sensiveis:
        t, minimo = t.upper(), (10 if c.lower() in _DOCUMENTO_MISTO else 1)
        if t in ("VARCHAR", "JSON"):
            e = f"rodado_cpf({_aspas(c)}, {minimo})"
        elif t in ("VARCHAR[]", "JSON[]"):
            e = f"list_transform({_aspas(c)}, lambda x: rodado_cpf(x, {minimo}))"
        else:
            e = f"rodado_cpf(CAST({_aspas(c)} AS VARCHAR), {minimo})"   # número, struct, blob…: vira texto mascarado
        trocas.append(f"{e} AS {_aspas(c)}")
    return sql[:m.end()] + f"SELECT * REPLACE ({', '.join(trocas)}) FROM ({corpo}) AS _original"


def marca_do_cheio(fontes: dict) -> str:
    return _sha(json.dumps(fontes, sort_keys=True))


def anonimo_em_dia() -> bool:
    """O catálogo anônimo existe e foi montado a partir do inteiro que está no ar."""
    try:
        reg = json.load(open(FONTES_ANON))
        fontes = json.load(open(FONTES))
    except (OSError, ValueError):
        return False
    return os.path.exists(BANCO_ANON) and reg.get("cheio") == marca_do_cheio(fontes) \
        and reg.get("mascara") == VERSAO_MASCARA


def monta_anonimo(cheio: str, fontes: dict):
    """Monta o catálogo anônimo em BANCO_ANON.novo a partir do arquivo inteiro `cheio` (já pronto).

    Incremental como o inteiro: parte do anônimo atual e só refaz a view cujo SQL, ou a lista de
    colunas de CPF, mudou. Sem anônimo anterior, parte de uma cópia do inteiro e refaz as views com
    CPF. Uma view com CPF que não pôde ser reescrita é apagada do arquivo: o anônimo nunca a serve
    sem máscara. Devolve (caminho do .novo, registro a gravar em FONTES_ANON)."""
    novo = BANCO_ANON + ".novo"
    for resto in (novo, novo + ".wal"):
        if os.path.exists(resto):
            os.remove(resto)
    try:
        reg = json.load(open(FONTES_ANON)) if os.path.exists(BANCO_ANON) else None
    except (OSError, ValueError):
        reg = None
    if reg and reg.get("mascara") == VERSAO_MASCARA:
        anteriores = reg.get("views", {})
        shutil.copyfile(BANCO_ANON, novo)
    else:
        anteriores = None          # cópia do inteiro: as views sem CPF já estão certas, as outras não
        shutil.copyfile(cheio, novo)
    lc = duckdb.connect(cheio, read_only=True)
    try:
        sqls = {f"{s}.{n}": (s, n, q) for s, n, q in lc.execute(
            "SELECT schema_name, view_name, sql FROM duckdb_views() WHERE NOT internal").fetchall()}
        colunas = {}
        for s, t, c, tipo in lc.execute(
                "SELECT schema_name, table_name, column_name, data_type FROM duckdb_columns() "
                "ORDER BY schema_name, table_name, column_index").fetchall():
            colunas.setdefault(f"{s}.{t}", []).append((c, tipo))
    finally:
        lc.close()
    desejado, ausentes = {}, []
    for nome, (s, n, q) in sqls.items():
        r = sql_anonimo(q, colunas.get(nome, []))
        if r is False:
            ausentes.append(nome)
        else:
            desejado[nome] = (s, n, q if r is None else r, VERSAO_MASCARA if r is not None else "")
    if anteriores is None:
        anteriores = {nome: _sha(q) for nome, (s, n, q, v) in desejado.items()
                      if sql_anonimo(sqls[nome][2], colunas.get(nome, [])) is None}
    con = _conexao(novo)
    falhas = []
    try:
        con.execute(MACRO_CPF)
        existentes = {f"{s}.{n}" for s, n in con.execute(
            "SELECT schema_name, view_name FROM duckdb_views() WHERE NOT internal").fetchall()}
        for nome in sorted((existentes - desejado.keys()) | set(ausentes)):
            d, t = nome.split(".", 1)
            con.execute(f"DROP VIEW IF EXISTS {_aspas(d)}.{_aspas(t)}")
            anteriores.pop(nome, None)
        for nome in ausentes:
            falhas.append(f"{nome}: tem coluna de CPF e o SQL não pôde ser reescrito")
        mudaram = [(nome, item) for nome, item in desejado.items()
                   if anteriores.get(nome) != _sha(item[2] + item[3]) or nome not in existentes]
        log(f"anônimo: {len(mudaram)} de {len(desejado)} views para (re)criar")

        def cria(par):
            nome, (d, t, sql, _) = par
            cur = con.cursor()
            try:
                cur.execute(f"DROP VIEW IF EXISTS {_aspas(d)}.{_aspas(t)}")
                cur.execute(sql)
                return None
            except duckdb.Error as e:
                return par, str(e).splitlines()[0]
            finally:
                cur.close()

        repetir = []
        with concurrent.futures.ThreadPoolExecutor(PARALELO) as ex:
            for r in ex.map(cria, mudaram):
                if r:
                    repetir.append(r)
        while repetir:    # conflito de escrita, ou view que cita outra ainda não criada
            antes, repetir = len(repetir), [r for r in (cria(par) for par, _ in repetir) if r]
            if len(repetir) == antes:
                break
        falhou = {nome for (nome, _), _e in repetir}
        for (nome, (d, t, _, _v)), erro in repetir:
            # falhou: a view não pode ficar com o SQL antigo (copiado do inteiro, sem máscara)
            con.execute(f"DROP VIEW IF EXISTS {_aspas(d)}.{_aspas(t)}")
            falhas.append(f"{nome}: {erro}")
        for nome, (_, _, sql, v) in mudaram:
            if nome in falhou:
                anteriores.pop(nome, None)
            else:
                anteriores[nome] = _sha(sql + v)
        con.execute("CHECKPOINT")
        n_views = con.execute("SELECT count(*) FROM duckdb_views() WHERE NOT internal").fetchall()[0][0]
    finally:
        con.close()
    for f in falhas:
        log(f"fora do catálogo anônimo: {f}")
    log(f"catálogo anônimo pronto: {n_views} views, {len(falhas)} fora")
    return novo, {"cheio": marca_do_cheio(fontes), "mascara": VERSAO_MASCARA, "views": anteriores}


def publica_anonimo(novo: str, reg: dict):
    os.replace(novo, BANCO_ANON)
    with open(FONTES_ANON + ".novo", "w") as f:
        json.dump(reg, f)
    os.replace(FONTES_ANON + ".novo", FONTES_ANON)


def monta(conteudo):
    """Monta o catálogo novo a partir do atual: só recria a view cujo SQL final (já com o
    caminho do bucket ou do SSD) mudou, cria as novas e apaga as que sumiram. O SQL de
    cada view criada fica em FONTES (hash por dataset.tabela); sem FONTES, ou com
    --completo, monta tudo do zero. Uma view que falha não entra em FONTES e é tentada de
    novo na montagem seguinte."""
    views = conteudo["views"] if isinstance(conteudo, dict) else conteudo
    macros = conteudo.get("macros", []) if isinstance(conteudo, dict) else []
    novo = BANCO + ".novo"
    for resto in (novo, novo + ".wal"):
        if os.path.exists(resto):
            os.remove(resto)
    completo = "--completo" in sys.argv or not (os.path.exists(BANCO) and os.path.exists(FONTES))
    fontes = {} if completo else json.load(open(FONTES))
    if not completo:
        shutil.copyfile(BANCO, novo)
    con = _conexao(novo)
    falhas = []
    try:
        validas = {}
        for v in views:
            sql = v["sql"] or ""
            if "s3://" in sql:
                falhas.append(f"{v['dataset']}.{v['tabela']}: outro bucket")
                continue
            validas[f"{v['dataset']}.{v['tabela']}"] = (v["dataset"], v["tabela"], para_s3(sql))
        existentes = {f"{s}.{n}" for s, n in con.execute(
            "SELECT schema_name, view_name FROM duckdb_views() WHERE NOT internal").fetchall()}
        for nome in sorted(existentes - validas.keys()):
            d, t = nome.split(".", 1)
            con.execute(f'DROP VIEW IF EXISTS "{d}"."{t}"')
            fontes.pop(nome, None)
        for d in sorted({d for d, _, _ in validas.values()}):
            con.execute(f'CREATE SCHEMA IF NOT EXISTS "{d}"')
        for m in macros:
            try:
                con.execute(re.sub(r"^\s*CREATE\s+(MACRO|FUNCTION)\b", r"CREATE OR REPLACE \1", m, flags=re.I))
            except duckdb.Error as e:
                falhas.append(f"macro {m[:40]}: {str(e).splitlines()[0]}")
        mudaram = [(nome, item) for nome, item in validas.items()
                   if fontes.get(nome) != _sha(item[2]) or nome not in existentes]
        log(f"{len(mudaram)} de {len(validas)} views para (re)criar" + (" (montagem completa)" if completo else ""))

        def cria(par):
            nome, (d, t, sql) = par
            cur = con.cursor()
            try:
                cur.execute(f'DROP VIEW IF EXISTS "{d}"."{t}"')
                cur.execute(sql)
                return None
            except duckdb.Error as e:
                return par, str(e).splitlines()[0]
            finally:
                cur.close()

        inicio, feitas = time.monotonic(), 0
        repetir = []
        with concurrent.futures.ThreadPoolExecutor(PARALELO) as ex:
            for r in ex.map(cria, mudaram):
                feitas += 1
                if r:
                    repetir.append(r)
                if feitas % 100 == 0:
                    log(f"{feitas}/{len(mudaram)} views em {time.monotonic() - inicio:.0f} s")
        # conflito de escrita no catálogo entre threads, ou view que cita outra view ainda não
        # criada (br_cgu_novo_bolsa_familia.novo_bolsa_familia = pagamento JOIN favorecido):
        # novas tentativas em série enquanto alguma passar
        while repetir:
            antes, repetir = len(repetir), [r for r in (cria(par) for par, _ in repetir) if r]
            if len(repetir) == antes:
                break
        falhou = set()
        for par, erro in repetir:
            falhou.add(par[0])
            falhas.append(f"{par[0]}: {erro}")
        for nome, (_, _, sql) in mudaram:
            if nome in falhou:
                fontes.pop(nome, None)
            else:
                fontes[nome] = _sha(sql)
        con.execute("CHECKPOINT")
        n_views = con.execute("SELECT count(*) FROM duckdb_views() WHERE NOT internal").fetchall()[0][0]
    finally:
        con.close()
    # o anônimo sai do inteiro recém-montado e os dois entram juntos: se ele falhar, o inteiro
    # também não troca (a falha aparece no log e a volta seguinte tenta de novo)
    anon_novo, reg = monta_anonimo(novo, fontes)
    os.replace(novo, BANCO)
    with open(FONTES + ".novo", "w") as f:
        json.dump(fontes, f)
    os.replace(FONTES + ".novo", FONTES)
    publica_anonimo(anon_novo, reg)
    for f in falhas:
        log(f"fora do catálogo: {f}")
    # timeout do bucket é passageiro: a view volta na próxima montagem (ver rodada)
    passageiras = sum("Timeout was reached" in f for f in falhas)
    return (f"{n_views} views, {len(falhas)} fora, {len(mudaram)} (re)criadas "
            f"em {time.monotonic() - inicio:.0f} s"), passageiras


def semeia_fontes(conteudo):
    """Catálogo em dia (a marca bate) montado antes de existir FONTES: cada view que existe
    nele foi criada a partir do SQL atual, então o hash desse SQL é o registro certo."""
    views = conteudo["views"] if isinstance(conteudo, dict) else conteudo
    con = duckdb.connect(BANCO, read_only=True)
    try:
        existentes = {f"{s}.{n}" for s, n in con.execute(
            "SELECT schema_name, view_name FROM duckdb_views() WHERE NOT internal").fetchall()}
    finally:
        con.close()
    fontes = {f"{v['dataset']}.{v['tabela']}": _sha(para_s3(v["sql"] or "")) for v in views
              if f"{v['dataset']}.{v['tabela']}" in existentes and "s3://" not in (v["sql"] or "")}
    with open(FONTES + ".novo", "w") as f:
        json.dump(fontes, f)
    os.replace(FONTES + ".novo", FONTES)
    log(f"registro das views semeado a partir do catálogo atual: {len(fontes)} views")


def copias_locais() -> str:
    """Os parquet completos em /dados/local (sem os .parcial de uma cópia em andamento):
    copiar ou apagar um deles muda a marca e remonta o catálogo na volta seguinte."""
    achados = []
    for raiz, _, arquivos in os.walk(rodado_sql.LOCAL):
        achados += [os.path.join(raiz, a) for a in arquivos if a.endswith(".parquet")]
    return "\n".join(sorted(achados))


def rodada():
    # um só montador por vez: o laço do container e um --uma-vez manual escreveriam o mesmo .novo
    with open(BANCO + ".trava", "w") as trava:
        try:
            fcntl.flock(trava, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            log("outra montagem em andamento: pulo esta volta")
            return False
        return _rodada()


def _rodada():
    texto, sha_views = baixa_views()
    sha = hashlib.sha256((sha_views + "\n" + copias_locais()).encode()).hexdigest()
    atual = open(MARCA).read().strip() if os.path.exists(MARCA) and os.path.exists(BANCO) else ""
    if sha == atual and "--completo" not in sys.argv:
        if not os.path.exists(FONTES):
            semeia_fontes(json.loads(texto))
        if not anonimo_em_dia():     # primeiro deploy com o anônimo, ou regra da máscara mudou
            log("catálogo anônimo ausente ou defasado: montando")
            publica_anonimo(*monta_anonimo(BANCO, json.load(open(FONTES))))
            return True
        return False
    log(f"views.json ou cópias no SSD mudaram ({sha[:12]}): montando o catálogo")
    resumo, passageiras = monta(json.loads(texto))
    if passageiras:
        # sem gravar a marca, a volta seguinte monta de novo: senão a tabela que caiu por
        # timeout ficaria fora até a próxima mudança (br_ms_sia.producao_ambulatorial, 2026-10-13)
        log(f"catálogo pronto: {resumo}; {passageiras} por timeout, monta de novo na próxima volta")
        return True
    with open(MARCA, "w") as f:
        f.write(sha + "\n")
    log(f"catálogo pronto: {resumo}")
    return True


def main():
    os.makedirs(os.path.dirname(BANCO), exist_ok=True)
    while True:
        try:
            rodada()
        except Exception as e:  # rede, bucket, JSON: tenta de novo na próxima volta
            log(f"ERRO: {e}")
            if "--uma-vez" in sys.argv:
                raise
        if "--uma-vez" in sys.argv:
            return
        time.sleep(INTERVALO)


if __name__ == "__main__":
    main()
