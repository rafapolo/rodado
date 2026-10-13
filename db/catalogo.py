#!/usr/bin/env python3
"""Mantém o catálogo do db.rodado.xyz: as views do beelink apontando para o bucket.

Lê s3://baseldosdados/_db/views.json (views e macros, gravado por exporta_views.py no
beelink e levado ao bucket pela sincronização), cria as macros, troca `/home/polo/rodado/` e `~/rodado/` por
`s3://baseldosdados/` e cria cada view num .duckdb novo, que substitui o anterior por
rename atômico. rodado_sql.conecta() percebe a troca e abre uma instância nova.

Criar uma view lê o rodapé de cada parquet que ela cita (79 mil arquivos, ~30 min com
paralelismo), então só remonta quando o views.json muda. Views de outros buckets (as
6 do SIPNI, em s3://healthbr-data) ficam de fora: não tinham segredo aqui nem antes.

    python3 catalogo.py            # laço: confere a cada 15 min
    python3 catalogo.py --uma-vez  # monta (se mudou) e sai
"""
import concurrent.futures
import hashlib
import json
import os
import re
import sys
import time

import duckdb

import rodado_sql

ORIGEM = rodado_sql.RAIZ + "_db/views.json"
BANCO = rodado_sql.BANCO
MARCA = BANCO + ".sha256"
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


def monta(conteudo) -> str:
    views = conteudo["views"] if isinstance(conteudo, dict) else conteudo
    macros = conteudo.get("macros", []) if isinstance(conteudo, dict) else []
    novo = BANCO + ".novo"
    for resto in (novo, novo + ".wal"):
        if os.path.exists(resto):
            os.remove(resto)
    con = _conexao(novo)
    falhas = []
    try:
        validas = []
        for v in views:
            sql = v["sql"] or ""
            if "s3://" in sql:
                falhas.append(f"{v['dataset']}.{v['tabela']}: outro bucket")
                continue
            validas.append((v["dataset"], v["tabela"], para_s3(sql)))
        for d in sorted({d for d, _, _ in validas}):
            con.execute(f'CREATE SCHEMA IF NOT EXISTS "{d}"')
        for m in macros:
            try:
                con.execute(m)
            except duckdb.Error as e:
                falhas.append(f"macro {m[:40]}: {str(e).splitlines()[0]}")

        def cria(item):
            d, t, sql = item
            cur = con.cursor()
            try:
                cur.execute(sql)
                return None
            except duckdb.Error as e:
                return item, str(e).splitlines()[0]
            finally:
                cur.close()

        inicio, feitas = time.monotonic(), 0
        repetir = []
        with concurrent.futures.ThreadPoolExecutor(PARALELO) as ex:
            for r in ex.map(cria, validas):
                feitas += 1
                if r:
                    repetir.append(r)
                if feitas % 100 == 0:
                    log(f"{feitas}/{len(validas)} views em {time.monotonic() - inicio:.0f} s")
        # conflito de escrita no catálogo entre threads: uma segunda tentativa, em série
        for (d, t, sql), _ in repetir:
            r = cria((d, t, sql))
            if r:
                falhas.append(f"{d}.{t}: {r[1]}")
        con.execute("CHECKPOINT")
    finally:
        con.close()
    os.replace(novo, BANCO)
    for f in falhas:
        log(f"fora do catálogo: {f}")
    return f"{len(views) - len(falhas)} views, {len(falhas)} fora"


def copias_locais() -> str:
    """Os parquet completos em /dados/local (sem os .parcial de uma cópia em andamento):
    copiar ou apagar um deles muda a marca e remonta o catálogo na volta seguinte."""
    achados = []
    for raiz, _, arquivos in os.walk(rodado_sql.LOCAL):
        achados += [os.path.join(raiz, a) for a in arquivos if a.endswith(".parquet")]
    return "\n".join(sorted(achados))


def rodada():
    texto, sha_views = baixa_views()
    sha = hashlib.sha256((sha_views + "\n" + copias_locais()).encode()).hexdigest()
    atual = open(MARCA).read().strip() if os.path.exists(MARCA) and os.path.exists(BANCO) else ""
    if sha == atual:
        return False
    log(f"views.json ou cópias no SSD mudaram ({sha[:12]}): montando o catálogo")
    resumo = monta(json.loads(texto))
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
