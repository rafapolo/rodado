#!/usr/bin/env python3
"""Histórico compacto do CNPJ a partir dos retratos mensais de `br_me_cnpj`.

    python3 scripts/sync/gera_cnpj_historico.py --tabela socios --prefixo 00 --teste
    python3 scripts/sync/gera_cnpj_historico.py --tabela estabelecimentos
    python3 scripts/sync/gera_cnpj_historico.py --tabela empresas

Por que existe: `br_me_cnpj` guarda o cadastro inteiro da Receita uma vez por mês
(56 retratos, ~256 GB em 2026-10). Guardar só o último perde o que só aparece entre
um retrato e outro: a Receita não publica data de saída de sócio, e
`data_situacao_cadastral` guarda só a última mudança. Estas tabelas guardam esse
histórico em pouco espaço, para que os retratos antigos possam sair.
Plano e conferências em `tasks/cnpj_historico.md`.

- `socios_historico`: uma linha por (cnpj_basico, tipo, documento, nome,
  qualificacao), com primeiro e último retrato em que apareceu, quantos retratos e
  quantos seriam sem buraco (`n_retratos < n_retratos_esperados` = saiu e voltou).
- `estabelecimentos_historico` / `empresas_historico`: SCD tipo 2. Uma linha por
  período em que nenhuma coluna mudou, com `inicio` e `fim` (retratos `aaaamm`).
  Sumir de um retrato também fecha o período.

Retrato = `ano*100+mes`. A coluna `data` não serve: nos meses vindos do
`br_rf_cnpj` ela é o dia 1, nos antigos é o dia real do retrato.

Roda num DuckDB em memória no beelink: lê parquet e grava parquet, sem abrir o
`basedosdados.duckdb` (não disputa lock com ninguém). Sócios vai em 100 pedaços pelo
prefixo de 2 dígitos do CNPJ; estabelecimentos e empresas vão retrato a retrato. Tudo que já
foi gravado é pulado, então rodar de novo retoma.
"""
import argparse
import json
import os
import subprocess
import sys
import time

BEELINK = os.environ.get("BEELINK_HOST", "beelink")
ROOT = "/home/polo/rodado/br_me_cnpj"
TESTE = "/home/polo/scrap_tmp/cnpj_historico_teste"
TRABALHO = "/home/polo/scrap_tmp/cnpj_historico_trabalho"
# A 1.5.4 do ~/bin/duckdb devolveu "Out of buffer" e "ZSTD Decompression failure"
# intermitentes em arquivos íntegros (md5 igual ao do COLD, lido direto do disco),
# em 2026-10-07; a 1.5.5 corrige leitura fora dos limites em parquet. Este script só
# lê e grava parquet, então usa um binário 1.5.6 à parte, sem o ~/.duckdbrc (que
# carrega extensões da 1.5.4) e com as mesmas configurações dele, explícitas.
DUCKDB = "~/bin/duckdb-1.5.6"
PREFIXO = ("SET enable_progress_bar=false; SET memory_limit='16GB'; SET threads=14; "
           "SET temp_directory='/home/polo/duckdb_tmp'; "
           "SET max_temp_directory_size='100GB';\n")

CHAVE = {"socios": "cnpj_basico", "estabelecimentos": "cnpj", "empresas": "cnpj_basico"}
GRAO_SOCIOS = ["cnpj_basico", "tipo", "documento", "nome", "qualificacao"]
FORA = {"ano", "mes", "data"}


def duck(sql, timeout=7200, tentativas=4):
    # "Out of buffer" e "ZSTD Decompression failure" aparecem de vez em quando numa
    # leitura que, repetida, passa (2026-10-07: ~1 em dezenas de consultas pesadas, nas
    # versões 1.5.4 e 1.5.6, em arquivos íntegros — md5 igual ao do COLD lido direto do
    # disco — e com resultado determinístico quando passa). Causa não achada. Repetir
    # com espera é seguro porque o erro é explícito e o resultado final é conferido.
    for t in range(tentativas):
        r = subprocess.run(["ssh", BEELINK, f"{DUCKDB} -init /dev/null -json"],
                           input=PREFIXO + sql + "\n.quit\n",
                           capture_output=True, text=True, timeout=timeout)
        erro = (r.stderr or r.stdout).strip()[-600:]
        if r.returncode == 0 and "Error" not in r.stderr:
            out = r.stdout
            return json.loads(out[out.index("["):]) if "[" in out else []
        transitorio = "Out of buffer" in erro or "ZSTD Decompression failure" in erro
        if not transitorio or t == tentativas - 1:
            raise RuntimeError(erro)
        print(f"    leitura falhou ({erro.splitlines()[-1][:80]}), repetindo "
              f"({t + 1}/{tentativas - 1}): {sql.strip()[:70]!r}", flush=True)
        time.sleep(30)


def sh(cmd, timeout=600):
    r = subprocess.run(["ssh", BEELINK, cmd], capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[:400])
    return r.stdout


def colunas(tb):
    r = duck(f"SELECT column_name c FROM (DESCRIBE SELECT * FROM "
             f"read_parquet('{ROOT}/{tb}/000000000000.parquet'));")
    return [x["c"] for x in r if x["c"] not in FORA]


def retratos(tb):
    """Os retratos presentes, em ordem, com o índice sequencial k (1..n)."""
    r = duck(f"SELECT DISTINCT ano*100+mes AS m FROM read_parquet('{ROOT}/{tb}/*.parquet') "
             f"ORDER BY 1;", timeout=3600)
    return [x["m"] for x in r]


def q(c):
    return '"' + c.replace('"', '""') + '"'


def sql_socios(fonte, filtro, cols, valores_r):
    resto = [c for c in cols if c not in GRAO_SOCIOS]
    grao = ", ".join(q(c) for c in GRAO_SOCIOS)
    ultimos = ",\n  ".join(f"arg_max({q(c)}, k) AS {q(c)}" for c in resto)
    return f"""
WITH r(retrato, k) AS (VALUES {valores_r}),
s AS (
  SELECT r.k, {", ".join("s." + q(c) for c in cols)}
  FROM read_parquet('{fonte}') s JOIN r ON r.retrato = s.ano*100+s.mes
  WHERE {filtro}
),
g AS (
  SELECT {grao}, min(k) AS k1, max(k) AS k2, count(DISTINCT k) AS n_retratos,
  {ultimos}
  FROM s GROUP BY ALL
)
SELECT g.* EXCLUDE (k1, k2),
  r1.retrato AS primeiro_retrato, r2.retrato AS ultimo_retrato,
  k2 - k1 + 1 AS n_retratos_esperados,
  k2 = (SELECT max(k) FROM r) AS no_ultimo_retrato
FROM g JOIN r r1 ON r1.k = g.k1 JOIN r r2 ON r2.k = g.k2
"""


def hash_cols(cols, chave, alias=""):
    return "hash(" + ", ".join(alias + q(c) for c in cols if c != chave) + ")"


def gera_scd2(tb, destino, limite=None):
    """Períodos estáveis por chave, andando retrato a retrato.

    Cada retrato é comparado só com o anterior, pelo hash das colunas: linha nova ou
    de hash diferente abre um período (e vai inteira para `abre_<m>`), linha que
    mudou ou sumiu fecha o anterior (`fecha_<m>`). No fim, cada abertura casa com o
    primeiro fechamento da mesma chave. Ordenar a história inteira de cada CNPJ numa
    janela não coube: 1/100 das chaves levou 9 min e 14 GB (2026-10-07). Cada
    arquivo do espelho tem um mês só, então o filtro por ano/mes lê só aquele mês.
    """
    chave = CHAVE[tb]
    cols = colunas(tb)
    rs = retratos(tb)[:limite]
    fonte = f"{ROOT}/{tb}/*.parquet"
    saida = f"{destino}/{tb}_historico"
    # fora de ~/rodado: o backup para o COLD copia tudo o que está lá, a cada 6h
    trab = f"{TRABALHO}/{'teste_' if destino == TESTE else ''}{tb}"
    sh(f"mkdir -p {trab}")
    print(f"{tb}: {len(rs)} retratos, {rs[0]}..{rs[-1]}; {len(cols)} colunas", flush=True)

    def mes(m, alias=""):
        return f"{alias}ano = {m // 100} AND {alias}mes = {m % 100}"

    def falta(nome):
        return nome not in sh(f"ls {trab}").split()

    def copia(sql, nome):
        duck(f"COPY ({sql}) TO '{trab}/.{nome}' (FORMAT parquet, COMPRESSION zstd);")
        sh(f"mv {trab}/.{nome} {trab}/{nome}")

    lista = ", ".join("e." + q(c) for c in cols)
    nulos_expr = " + ".join(f"({q(c)} IS NULL)::INT" for c in cols if c != chave)
    ant = None
    for m in rs:
        t = time.time()
        if falta(f"h_{m}.parquet"):
            # Uma versão por chave e retrato. O espelho tem linha repetida idêntica
            # (empresas 08464718 em 2022-09) e versões diferentes da mesma chave
            # (empresas 10959550 em 2025-05: a linha real e duas vazias, com
            # razao_social NULL e natureza 0000). Fica a versão com menos colunas
            # vazias; empate decide pelo hash, para ser sempre a mesma.
            copia(f"SELECT {q(chave)}, arg_min(h, {{'n': nulos, 'h': h}}) AS h FROM ("
                  f"SELECT {q(chave)}, {hash_cols(cols, chave)} AS h, {nulos_expr} AS nulos "
                  f"FROM read_parquet('{fonte}') WHERE {mes(m)}) GROUP BY 1", f"h_{m}.parquet")
        if falta(f"abre_{m}.parquet"):
            # a linha inteira da versão escolhida em h_<m>, só se abre período
            sql = (f"SELECT DISTINCT {m} AS inicio, {lista} FROM read_parquet('{fonte}') e "
                   f"JOIN read_parquet('{trab}/h_{m}.parquet') c ON c.{q(chave)} = e.{q(chave)} "
                   f"AND c.h = {hash_cols(cols, chave, 'e.')} ")
            if ant is not None:
                sql += (f"LEFT JOIN read_parquet('{trab}/h_{ant}.parquet') p "
                        f"ON p.{q(chave)} = e.{q(chave)} ")
            sql += f"WHERE {mes(m, 'e.')}"
            if ant is not None:
                sql += " AND (p.h IS NULL OR p.h <> c.h)"
            copia(sql, f"abre_{m}.parquet")
        if ant is not None and falta(f"fecha_{ant}.parquet"):
            copia(f"SELECT p.{q(chave)}, {ant} AS fim FROM read_parquet('{trab}/h_{ant}.parquet') p "
                  f"LEFT JOIN read_parquet('{trab}/h_{m}.parquet') c USING ({q(chave)}) "
                  f"WHERE c.h IS NULL OR c.h <> p.h", f"fecha_{ant}.parquet")
        print(f"  {m}: {time.time()-t:,.0f}s", flush=True)
        ant = m
    ult = rs[-1]
    if falta(f"fecha_{ult}.parquet"):
        copia(f"SELECT {q(chave)}, {ult} AS fim FROM read_parquet('{trab}/h_{ult}.parquet')",
              f"fecha_{ult}.parquet")

    # montagem: cada abertura casa com o primeiro fechamento da chave a partir dela.
    # Grava no trabalho e só vai para ~/rodado conferida: em 2026-10-07 uma montagem
    # reprovada ficou no espelho, legível por read_parquet.
    mont = f"{trab}/montagem"
    sh(f"mkdir -p {mont}")
    feitos = set(sh(f"ls {mont}").split())
    total = no_ultimo = 0
    for d in "0123456789":
        arq = f"p{d}.parquet"
        if arq not in feitos:
            duck(f"""COPY (
SELECT a.inicio, f.fim, a.* EXCLUDE (inicio)
FROM (SELECT * FROM read_parquet('{trab}/abre_*.parquet') WHERE starts_with({q(chave)}, '{d}')) a
ASOF JOIN (SELECT * FROM read_parquet('{trab}/fecha_*.parquet') WHERE starts_with({q(chave)}, '{d}')) f
  ON a.{q(chave)} = f.{q(chave)} AND f.fim >= a.inicio
) TO '{mont}/.{arq}' (FORMAT parquet, COMPRESSION zstd);""")
            sh(f"mv {mont}/.{arq} {mont}/{arq}")
        c = duck(f"SELECT count(*) n, count(*) FILTER (fim = {ult}) u "
                 f"FROM read_parquet('{mont}/{arq}');")[0]
        total += c["n"]
        no_ultimo += c["u"]
        print(f"  montagem {d}: {c['n']:,} períodos", flush=True)
    aberturas = duck(f"SELECT count(*) n FROM read_parquet('{trab}/abre_*.parquet');")[0]["n"]
    orig = duck(f"SELECT count(*) n FROM read_parquet('{trab}/h_{ult}.parquet');")[0]["n"]
    ok = total == aberturas and no_ultimo == orig
    print(f"{tb}_historico: {total:,} períodos (aberturas {aberturas:,}); vigentes em {ult}: "
          f"{no_ultimo:,}, original {orig:,} -> {'OK' if ok else 'NAO BATE'}", flush=True)
    if not ok:
        raise RuntimeError(f"conferência falhou; nada publicado, montagem em {mont}")
    publica(mont, saida)
    print(f"conferido e publicado em {saida}. Intermediários em {trab} (apagar à mão).")


def gera_socios(prefixos, destino):
    tb = "socios"
    chave = CHAVE[tb]
    cols = colunas(tb)
    rs = retratos(tb)
    valores_r = ", ".join(f"({m}, {i})" for i, m in enumerate(rs, 1))
    print(f"{tb}: {len(rs)} retratos, {rs[0]}..{rs[-1]}; {len(cols)} colunas", flush=True)
    fonte = f"{ROOT}/{tb}/*.parquet"
    saida = f"{destino}/{tb}_historico"
    # pedaços no trabalho; o conjunto só vai para ~/rodado com os 100 conferidos
    trab = f"{TRABALHO}/{'teste_' if destino == TESTE else ''}{tb}"
    sh(f"mkdir -p {trab}")
    feitos = set(sh(f"ls {trab}").split())
    for p in prefixos:
        arq = f"p{p}.parquet"
        if arq in feitos:
            print(f"  {p}: já existe, pulando", flush=True)
            continue
        filtro = f"starts_with({q(chave)}, '{p}')"
        corpo = sql_socios(fonte, filtro, cols, valores_r)
        stg = f"{trab}/.{arq}"
        t = time.time()
        # "Out of buffer" apareceu uma vez e sumiu ao repetir (2026-10-07)
        for tentativa in range(3):
            try:
                duck(f"COPY ({corpo}) TO '{stg}' (FORMAT parquet, COMPRESSION zstd);")
                break
            except RuntimeError as exc:
                if tentativa == 2:
                    raise
                print(f"  {p}: falhou, repetindo ({str(exc)[-120:]})", flush=True)
        # conferência: o último retrato reconstruído tem de bater com o original
        ult = rs[-1]
        conf = duck(f"""
SELECT (SELECT count(*) FROM read_parquet('{stg}') WHERE no_ultimo_retrato) AS hist,
       (SELECT count(*) FROM (SELECT DISTINCT {", ".join(q(c) for c in GRAO_SOCIOS)}
          FROM read_parquet('{fonte}') WHERE ano*100+mes = {ult} AND {filtro})) AS orig,
       (SELECT count(*) FROM read_parquet('{stg}')) AS linhas;""")[0]
        if conf["hist"] != conf["orig"]:
            raise RuntimeError(f"{tb} {p}: último retrato não bate: histórico {conf['hist']:,}"
                               f" x original {conf['orig']:,}; staging em {stg}")
        sh(f"mv {stg} {trab}/{arq}")
        tam = sh(f"du -b {trab}/{arq} | cut -f1").strip()
        print(f"  {p}: {conf['linhas']:,} linhas, último retrato {conf['hist']:,} = original, "
              f"{int(tam)/1e6:,.0f} MB, {time.time()-t:,.0f}s", flush=True)
    todos = {f"p{i:02d}.parquet" for i in range(100)}
    if todos <= set(sh(f"ls {trab}").split()):
        sh(f"mkdir -p {trab}/montagem && mv {trab}/p*.parquet {trab}/montagem/")
        publica(f"{trab}/montagem", saida)
        print(f"socios_historico: os 100 pedaços conferidos, publicado em {saida}", flush=True)
    else:
        print(f"socios_historico: pedaços em {trab}; publica quando os 100 estiverem lá",
              flush=True)


def publica(origem, saida):
    """Move o diretório conferido para o destino; recusa sobrescrever."""
    if sh(f"test -e {saida} && echo existe || true").strip():
        raise RuntimeError(f"{saida} já existe; mova-o antes de publicar")
    sh(f"mkdir -p {os.path.dirname(saida)} && mv {origem} {saida} && "
       f"chmod 775 {saida} && chmod 664 {saida}/*.parquet")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tabela", required=True, choices=list(CHAVE))
    ap.add_argument("--prefixo", action="append",
                    help="só para socios: prefixo do cnpj_basico; repetível. Padrão: 00..99")
    ap.add_argument("--retratos", type=int,
                    help="só os N primeiros retratos (para testar com --teste)")
    ap.add_argument("--teste", action="store_true", help=f"grava em {TESTE}, fora do espelho")
    a = ap.parse_args()
    destino = TESTE if a.teste else ROOT
    if a.tabela == "socios":
        # 1 dígito (~140 M linhas por pedaço) estourou os 16 GB do DuckDB no
        # GROUP BY com arg_max (2026-10-07); 2 dígitos dão ~1 min por pedaço
        gera_socios(a.prefixo or [f"{i:02d}" for i in range(100)], destino)
    else:
        gera_scd2(a.tabela, destino, a.retratos)
    return 0


if __name__ == "__main__":
    sys.exit(main())
