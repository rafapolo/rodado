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
MARCA = BANCO + ".sha256"
FONTES = BANCO + ".fontes.json"   # hash do SQL de cada view criada: o que remontar
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
        texto = con.execute("SELECT content FROM read_text(?)", [ORIGEM]).fetchone()[0]
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
        # conflito de escrita no catálogo entre threads: uma segunda tentativa, em série
        falhou = set()
        for par, _ in repetir:
            r = cria(par)
            if r:
                falhou.add(par[0])
                falhas.append(f"{par[0]}: {r[1]}")
        for nome, (_, _, sql) in mudaram:
            if nome in falhou:
                fontes.pop(nome, None)
            else:
                fontes[nome] = _sha(sql)
        con.execute("CHECKPOINT")
        n_views = con.execute("SELECT count(*) FROM duckdb_views() WHERE NOT internal").fetchone()[0]
    finally:
        con.close()
    os.replace(novo, BANCO)
    with open(FONTES + ".novo", "w") as f:
        json.dump(fontes, f)
    os.replace(FONTES + ".novo", FONTES)
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
