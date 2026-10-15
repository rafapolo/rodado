#!/usr/bin/env python3
"""Regrava em zstd as tabelas enriquecidas (CPF completo) e aposenta os *_original.

Para cada par enriquecido/_original:
  1. confere: enriquecido com o CPF remascarado == original (n + soma de hash de todas as linhas)
  2. fonte da regravacao = enriquecido se equivalente; senao, original + join no cpf_lookup
  3. grava zstd em ~/rezstd/stage: um arquivo por UF nas tabelas grandes, ordenado por
     municipio, PESSOA, ano, mes. As repeticoes da mesma pessoa ficam vizinhas e o
     dicionario do parquet volta a funcionar (auxilio_brasil: 3,19 GB snappy -> 0,98 GB;
     ordenado por ano/mes/UF ia a 6,01 GB porque cpf/nis/nome caiam para PLAIN)
  4. cada arquivo e conferido contra o mesmo recorte do original e regravado ate bater:
     a RAM do beelink troca bits na escrita (linha com ano virando NULL, ZSTD ilegivel)
  5. troca: enriquecido antigo e _original vao para ~/rezstd/lixo (nada e apagado aqui)

Retomavel: tabela com linha "ok" versao 2 em ~/rezstd/log.jsonl e pulada; arquivo do stage
que ja bate com o original e reaproveitado.
    python3 rezstd.py enriquecidas      # os 12 pares
    python3 rezstd.py snappy            # recodifica o resto do espelho que nao e zstd
"""
import glob
import json
import os
import shutil
import sys
import time

import duckdb

H = os.path.expanduser("~")
RODADO = f"{H}/rodado"
BASE = f"{H}/rezstd"
STAGE = f"{BASE}/stage"
LIXO = f"{BASE}/lixo"
LOG = f"{BASE}/log.jsonl"
VERSAO = 2

PARES = [  # (dataset, tabela, coluna cpf, coluna nome)
    ("br_cgu_beneficios_cidadao", "auxilio_brasil", "cpf_favorecido", "nome_favorecido"),
    ("br_cgu_beneficios_cidadao", "novo_bolsa_familia", "cpf_favorecido", "nome_favorecido"),
    ("br_cgu_beneficios_cidadao", "bolsa_familia_pagamento", "cpf_favorecido", "nome_favorecido"),
    ("br_cgu_beneficios_cidadao", "bpc", "cpf_favorecido", "nome_favorecido"),
    ("br_cgu_beneficios_cidadao", "auxilio_emergencial", "cpf_beneficiario", "nome_beneficiario"),
    ("br_cgu_servidores_executivo_federal", "cadastro_servidores", "cpf", "nome"),
    ("br_cgu_servidores_executivo_federal", "remuneracao", "cpf", "nome"),
    ("br_cgu_servidores_executivo_federal", "cadastro_aposentados", "cpf", "nome"),
    ("br_cgu_servidores_executivo_federal", "cadastro_pensionistas", "cpf", "nome"),
    ("br_cgu_servidores_executivo_federal", "cadastro_reserva_reforma_militares", "cpf", "nome"),
    ("br_cgu_servidores_executivo_federal", "afastamentos", "cpf", "nome"),
    ("br_cgu_servidores_executivo_federal", "observacoes", "cpf", "nome"),
]
PARTICIONA_ACIMA = 2e9  # bytes
MAX_LINHAS = 60_000_000  # UF acima disso vai em GRUPOS arquivos, por municipio (ou pessoa)
GRUPOS = 16
PESSOA = ["nis_favorecido", "nis_beneficiario", "id_servidor"]
OPTS = "(FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 122880)"


def log(**kw):
    kw["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
    print(json.dumps(kw, ensure_ascii=False), flush=True)
    with open(LOG, "a") as f:
        f.write(json.dumps(kw, ensure_ascii=False) + "\n")


def feitos():
    if not os.path.exists(LOG):
        return set()
    out = set()
    for l in open(LOG):
        r = json.loads(l)
        if r.get("status") == "ok" and r.get("versao") == VERSAO:
            out.add(r["tabela"])
    return out


def con(threads=12):
    c = duckdb.connect()
    c.execute(f"""
        SET memory_limit='14GB'; SET threads={threads};
        SET temp_directory='{H}/duckdb_tmp'; SET max_temp_directory_size='100GB';
        SET preserve_insertion_order=false; SET enable_progress_bar=false;
        ATTACH '{RODADO}/basedosdados.duckdb' AS bd (READ_ONLY);
        CREATE MACRO remask(c) AS CASE WHEN c IS NULL OR c LIKE '%*%' THEN c
            ELSE '***.' || substr(c,4,3) || '.' || substr(c,7,3) || '-**' END;
    """)
    return c


def q(nome):
    return '"' + nome.replace('"', '""') + '"'


def fonte_sql(path):
    return f"read_parquet('{path}')" if path.endswith(".parquet") else f"read_parquet('{path}/*.parquet')"


def colunas(c, path):
    return [r[0] for r in c.execute(f"DESCRIBE SELECT * FROM {fonte_sql(path)}").fetchall()]


def hexpr(cols, cpf):
    return ", ".join(f"remask({q(x)})" if x == cpf else q(x) for x in cols)


def assinatura(c, path, cols, cpf=None):
    """n e soma de hash de todas as linhas, na ordem de `cols`; `cpf` sai remascarado."""
    n, s = c.execute(f"SELECT count(*), sum(hash({hexpr(cols, cpf)})::HUGEINT) FROM {fonte_sql(path)}").fetchone()
    return [int(n), str(s)]


def assinatura_segura(c, path, cols, cpf=None):
    try:
        return assinatura(c, path, cols, cpf)
    except duckdb.Error as e:
        return ["ilegivel", str(e)[:150]]


def tamanho(path):
    return sum(os.path.getsize(f) for f in glob.glob(f"{path}/*.parquet"))


def ordem(cols, particionado):
    lugar = ([] if particionado else ["sigla_uf"]) + ["id_municipio"]
    pessoa = [x for x in PESSOA if x in cols][:1]
    tempo = ["ano_competencia", "ano", "mes_competencia", "mes"]
    return [x for x in lugar + pessoa + tempo if x in cols]


def nome_arq(v):
    return "sem_uf" if v is None else str(v)


def grava(c, select, cols, destino, ori, cols_o, cpf, sig_o, grande, cpf_join=False):
    """Grava e confere cada arquivo contra o mesmo recorte do original; regrava ate bater."""
    os.makedirs(destino, exist_ok=True)
    # tabela grande sem sigla_uf (remuneracao) cai inteira em "sem_uf" e e dividida em grupos
    part = (q("sigla_uf") if "sigla_uf" in cols else "NULL::VARCHAR") if grande else None
    by = " ORDER BY " + ", ".join(q(x) for x in ordem(cols, bool(part)))
    if part:
        # soma de hash e aditiva: o esperado da UF e a soma dos seus grupos. O grupo sai do
        # municipio ou, sem ele, da pessoa: cada pessoa continua inteira num arquivo
        chave = next((x for x in ["id_municipio"] + PESSOA if x in cols), None)
        grupo = f"hash({q(chave)}) % {GRUPOS}" if chave else "0"
        por_grupo = {}
        for v, g, n, s in c.execute(
                f"SELECT {part}, {grupo}, count(*), sum(hash({hexpr(cols_o, cpf)})::HUGEINT) "
                f"FROM {fonte_sql(ori)} GROUP BY 1, 2").fetchall():
            por_grupo.setdefault(v, {})[g] = (int(n), int(s))
        alvos = []
        for v in sorted(por_grupo, key=nome_arq):
            fv = f"{part} IS NULL" if v is None else f"{part} = '{v}'"
            grupos = por_grupo[v]
            inteiro = f"{destino}/{nome_arq(v)}.parquet"
            total = [sum(n for n, _ in grupos.values()), str(sum(s for _, s in grupos.values()))]
            # a RAM do beelink troca um bit a cada poucas centenas de milhoes de linhas:
            # UF grande inteira (SP, 157M) nunca passava; em grupos de municipio cada pessoa
            # continua num arquivo so
            if total[0] <= MAX_LINHAS or (os.path.exists(inteiro)
                                          and assinatura_segura(c, inteiro, cols_o, cpf) == total):
                alvos.append((inteiro, fv, total))
                for sobra in glob.glob(f"{destino}/{nome_arq(v)}_*.parquet"):
                    os.remove(sobra)  # a conferencia final soma o diretorio inteiro
                continue
            if os.path.exists(inteiro):
                os.remove(inteiro)
            nomes = {f"{destino}/{nome_arq(v)}_{g}.parquet" for g in grupos}
            for sobra in set(glob.glob(f"{destino}/{nome_arq(v)}_*.parquet")) - nomes:
                os.remove(sobra)  # divisao anterior com outro numero de grupos
            for g, (n, s) in sorted(grupos.items()):
                alvos.append((f"{destino}/{nome_arq(v)}_{g}.parquet", f"{fv} AND {grupo} = {g}", [n, str(s)]))
    else:
        alvos = [(f"{destino}/000000000000.parquet", "true", sig_o)]
    def bate(c, arq, filtro, sig):
        if assinatura_segura(c, arq, cols_o, cpf) != sig:
            return False
        if not cpf_join:
            return True
        # o remascarado so cobre os 6 digitos do meio; o CPF completo vem do join, que e
        # recalculado so como agregacao e comparado
        a = c.execute(f"SELECT count(*), sum(hash({q(cpf)})::HUGEINT) FROM read_parquet('{arq}')").fetchone()
        b = c.execute(f"SELECT count(*), sum(hash({q(cpf)})::HUGEINT) FROM ({select(filtro)})").fetchone()
        if a != b:
            log(evento="cpf_completo_nao_bate", arquivo=arq, arquivo_sig=str(a), join_sig=str(b))
        return a == b

    for arq, filtro, sig in alvos:
        try:
            if os.path.exists(arq) and bate(c, arq, filtro, sig):
                continue
        except duckdb.Error:
            pass
        for tentativa, threads in enumerate((12, 12, 8, 8, 4), 1):
            t0 = time.time()
            try:
                c.close()
                c = con(threads)
                if os.path.exists(arq):
                    os.remove(arq)
                c.execute(f"COPY (SELECT * FROM ({select(filtro)}){by}) TO '{arq}' {OPTS}")
                lido = assinatura_segura(c, arq, cols_o, cpf)
                ok = lido == sig and bate(c, arq, filtro, sig)
            except duckdb.Error as e:
                lido, ok = ["erro", str(e)[:150]], False
            if ok:
                log(evento="arquivo_ok", arquivo=arq, linhas=sig[0], seg=round(time.time() - t0))
                break
            log(evento="arquivo_nao_bate", arquivo=arq, tentativa=tentativa, esperado=sig, lido=lido)
        else:
            raise RuntimeError(f"5 tentativas sem bater: {arq}")
    return c


def move_para_lixo(path, ds):
    alvo = f"{LIXO}/{ds}/{os.path.basename(path)}"
    os.makedirs(os.path.dirname(alvo), exist_ok=True)
    if os.path.exists(alvo):
        alvo += f"_{int(time.time())}"
    shutil.move(path, alvo)
    return alvo


def enriquecidas():
    c = con()
    pular = feitos()
    for ds, t, cpf, nome in PARES:
        chave = f"{ds}.{t}"
        if chave in pular:
            continue
        enr = f"{RODADO}/{ds}/{t}"
        ori = f"{RODADO}/{ds}/{t}_original"
        if not os.path.isdir(ori):
            ori = f"{LIXO}/{ds}/{t}_original"  # ja aposentado pela versao 1
        if not os.path.isdir(ori):
            log(tabela=chave, status="sem_original")
            continue
        t0 = time.time()
        cols_o, cols_e = colunas(c, ori), colunas(c, enr)
        if sorted(cols_o) != sorted(cols_e):
            log(tabela=chave, status="erro", motivo="colunas diferentes", o=cols_o, e=cols_e)
            continue
        sig_o = assinatura(c, ori, cols_o, cpf)
        sig_e = assinatura_segura(c, enr, cols_o, cpf)
        equivalente = sig_o == sig_e
        log(tabela=chave, evento="conferido", original=sig_o, enriquecido=sig_e,
            equivalente=equivalente, seg=round(time.time() - t0))

        # fonte: o enriquecido quando ele e bom (preserva os CPFs exatos), senao refaz pelo join
        if equivalente:
            fonte = "enriquecido"

            def select(filtro):
                return f"SELECT {', '.join(q(x) for x in cols_e)} FROM read_parquet('{enr}/*.parquet') WHERE {filtro}"
        else:
            # join por recorte, com o lookup (224M linhas) reduzido aos nomes do recorte:
            # o join da tabela inteira contra o lookup inteiro espalhou 93 GB de spill
            fonte = "original+join"
            resto = ", ".join(f"t.{q(x)}" for x in cols_e if x != cpf)

            def select(filtro):
                return f"""WITH t AS (SELECT * FROM read_parquet('{ori}/*.parquet') WHERE {filtro}),
                                l AS (SELECT * FROM bd.cpf_lookup
                                      WHERE nome_upper IN (SELECT DISTINCT upper({q(nome)}) FROM t))
                           SELECT CASE WHEN t.{q(cpf)} LIKE '%*%' AND l.cpf_completo IS NOT NULL
                                       THEN l.cpf_completo ELSE t.{q(cpf)} END AS {q(cpf)}, {resto}
                           FROM t LEFT JOIN l
                             ON upper(t.{q(nome)}) = l.nome_upper
                            AND substr(replace(replace(t.{q(cpf)}, '.', ''), '-', ''), 4, 6) = l.cpf_mid6"""
        stage = f"{STAGE}/{ds}/{t}"
        for velho in glob.glob(f"{stage}/*.parquet"):  # stage da versao 1 (um arquivo por ano)
            b = os.path.basename(velho)
            if b[0].isdigit() and b != "000000000000.parquet":
                os.remove(velho)
        t1 = time.time()
        c = grava(c, select, cols_e, stage, ori, cols_o, cpf, sig_o, tamanho(enr) > PARTICIONA_ACIMA,
                  cpf_join=fonte == "original+join")
        sig_s = assinatura(c, stage, cols_o, cpf)
        extra = {}
        if fonte == "enriquecido":
            # re-encode puro: tem que bater inclusive o CPF completo
            extra["exato"] = assinatura(c, stage, cols_e) == assinatura(c, enr, cols_e)
        log(tabela=chave, evento="stage_gravado", fonte=fonte, stage=sig_s,
            bate_original=sig_s == sig_o, gb_antes=round(tamanho(enr) / 1e9, 2),
            gb_depois=round(tamanho(stage) / 1e9, 2), seg=round(time.time() - t1), **extra)
        if sig_s != sig_o or extra.get("exato") is False:
            log(tabela=chave, status="erro", motivo="stage nao bate; nada trocado")
            continue
        lixo = [move_para_lixo(enr, ds)]
        shutil.move(stage, enr)
        if ori.startswith(RODADO):
            lixo.append(move_para_lixo(ori, ds))
        log(tabela=chave, status="ok", versao=VERSAO, acao="trocado", fonte=fonte, lixo=lixo)


def confere_cpf(alvo):
    """CPF completo de uma tabela ja trocada (fonte original+join) contra o join recalculado, por UF."""
    ds, t = alvo.split(".")
    _, _, cpf, nome = next(p for p in PARES if p[0] == ds and p[1] == t)
    c = con(8)
    tab, ori = f"{RODADO}/{ds}/{t}", f"{LIXO}/{ds}/{t}_original"
    resto = ", ".join(f"t.{q(x)}" for x in colunas(c, tab) if x != cpf)
    ufs = [r[0] for r in c.execute(f"SELECT DISTINCT sigla_uf FROM read_parquet('{tab}/*.parquet')").fetchall()]
    ruins = []
    for v in sorted(ufs, key=nome_arq):
        fv = "sigla_uf IS NULL" if v is None else f"sigla_uf = '{v}'"
        join = f"""WITH t AS (SELECT * FROM read_parquet('{ori}/*.parquet') WHERE {fv}),
                        l AS (SELECT * FROM bd.cpf_lookup WHERE nome_upper IN (SELECT DISTINCT upper({q(nome)}) FROM t))
                   SELECT CASE WHEN t.{q(cpf)} LIKE '%*%' AND l.cpf_completo IS NOT NULL
                               THEN l.cpf_completo ELSE t.{q(cpf)} END AS {q(cpf)}
                   FROM t LEFT JOIN l ON upper(t.{q(nome)}) = l.nome_upper
                    AND substr(replace(replace(t.{q(cpf)}, '.', ''), '-', ''), 4, 6) = l.cpf_mid6"""
        for tentativa in range(1, 4):
            try:
                a = c.execute(f"SELECT count(*), sum(hash({q(cpf)})::HUGEINT) FROM read_parquet('{tab}/*.parquet') WHERE {fv}").fetchone()
                b = c.execute(f"SELECT count(*), sum(hash({q(cpf)})::HUGEINT) FROM ({join})").fetchone()
            except duckdb.Error as e:
                a, b = ("erro", str(e)[:100]), None
            if a == b:
                break
            c.close()
            c = con(8)
        log(tabela=alvo, evento="cpf_completo_uf", uf=nome_arq(v), bate=a == b, tentativas=tentativa)
        if a != b:
            ruins.append(nome_arq(v))
    log(tabela=alvo, evento="cpf_completo_fim", ufs_que_nao_batem=ruins)


def snappy():
    """Recodifica arquivo a arquivo, mesmo nome, tudo o que nao e zstd (fora dos pares acima)."""
    c = con()
    pular = feitos()
    pares = {f"{RODADO}/{ds}/{t}/" for ds, t, _, _ in PARES}
    rows = c.execute(f"""SELECT file_name FROM parquet_metadata('{RODADO}/*/*/*.parquet')
                         GROUP BY file_name HAVING bool_or(compression <> 'ZSTD') ORDER BY 1""").fetchall()
    for (f,) in rows:
        if f in pular or "_original/" in f or any(f.startswith(p) for p in pares):
            continue
        cols = colunas(c, f)
        tmp = f"{STAGE}/arquivo.parquet"
        os.makedirs(STAGE, exist_ok=True)
        a = assinatura(c, f, cols)
        for tentativa in range(1, 4):
            try:
                c.execute("SET preserve_insertion_order=true")
                c.execute(f"COPY (SELECT * FROM read_parquet('{f}')) TO '{tmp}' {OPTS}")
                b = assinatura_segura(c, tmp, cols)
            except duckdb.Error as e:
                b = ["erro", str(e)[:150]]
            if a == b:
                break
            log(tabela=f, evento="arquivo_nao_bate", tentativa=tentativa, a=a, b=b)
        else:
            log(tabela=f, status="erro", motivo="recodificado nao bate")
            os.remove(tmp)
            continue
        antes, depois = os.path.getsize(f), os.path.getsize(tmp)
        if depois >= antes:
            log(tabela=f, status="ok", versao=VERSAO, acao="mantido_snappy_menor",
                mb_antes=round(antes / 1e6, 1), mb_zstd=round(depois / 1e6, 1))
            os.remove(tmp)
            continue
        alvo = f"{LIXO}/arquivos{f}"
        os.makedirs(os.path.dirname(alvo), exist_ok=True)
        shutil.move(f, alvo)
        shutil.move(tmp, f)
        log(tabela=f, status="ok", versao=VERSAO, acao="recodificado",
            mb_antes=round(antes / 1e6, 1), mb_depois=round(depois / 1e6, 1))


if __name__ == "__main__":
    os.makedirs(BASE, exist_ok=True)
    if sys.argv[1] == "confere_cpf":
        confere_cpf(sys.argv[2])
    else:
        {"enriquecidas": enriquecidas, "snappy": snappy}[sys.argv[1]]()
