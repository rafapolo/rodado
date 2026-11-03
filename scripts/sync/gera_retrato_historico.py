#!/usr/bin/env python3
"""Histórico compacto de uma tabela de retratos (o cadastro inteiro repetido a cada data).

Generaliza a ideia de `gera_cnpj_historico.py` para tabelas sem chave única por linha: a
identidade é a própria linha (hash de todas as colunas menos a data do retrato), e cada
período em que a linha aparece em retratos consecutivos vira uma linha com `inicio` e `fim`
(datas do primeiro e do último retrato do período). Linha repetida dentro do mesmo retrato
(multiconjunto, ex.: `br_rf_cno.areas`) ganha um ordinal `d`, então a reconstrução devolve o
mesmo número de cópias.

Roda NO beelink (a primeira versão foi para `br_rf_cno`, 2026-11-03):

    flock ~/scrap_tmp/pesado.lock python3 gera_retrato_historico.py br_rf_cno microdados \
        --chave id_cno --data data_extracao --exclui 000000000116.parquet,000000000135.parquet

Saída em ~/scrap_tmp/retrato_hist/<ds>/<tb>/ (histórico por faixa de chave e o último
retrato). Nada em ~/rodado é tocado: publicar e apagar os retratos é passo separado, com ok.

Conferência, no fim: para CADA retrato, contagem e soma do hash da linha reconstruída pelo
histórico (`inicio <= data <= fim`) = as mesmas da fonte. Cada faixa também é gravada pela
`copia_dupla` (grava, e recalcula a impressão digital direto da consulta).
"""
import argparse, json, os, subprocess, sys, time

DUCKDB = os.path.expanduser("~/bin/duckdb")
ROOT = os.environ.get("RETRATO_ROOT", os.path.expanduser("~/rodado"))
PREFIXO = ("SET enable_progress_bar=false; SET memory_limit='10GB'; SET threads=6; "
           "SET preserve_insertion_order=false; "
           f"SET temp_directory='{os.path.expanduser('~/duckdb_tmp')}/retrato_hist';\n")


def duck(sql, tentativas=4):
    for t in range(tentativas):
        r = subprocess.run([DUCKDB, "-init", "/dev/null", "-json"], input=PREFIXO + sql + "\n.quit\n",
                           capture_output=True, text=True)
        erro = (r.stderr or "").strip()[-600:]
        if r.returncode == 0 and "Error" not in r.stderr:
            out = r.stdout
            return json.loads(out[out.index("["):]) if "[" in out else []
        transitorio = "Out of buffer" in erro or "ZSTD Decompression failure" in erro
        if not transitorio or t == tentativas - 1:
            raise RuntimeError(erro)
        print(f"    leitura falhou, repetindo ({t + 1}): {erro.splitlines()[-1][:80]}", flush=True)
        time.sleep(30)


def copia_dupla(sql, destino, tentativas=3):
    for t in range(tentativas):
        duck(f"COPY ({sql}) TO '{destino}' (FORMAT parquet, COMPRESSION zstd, ROW_GROUP_SIZE 122880);")
        a = duck(f"SELECT count(*) AS n, sum(hash(t)::HUGEINT)::VARCHAR AS s FROM read_parquet('{destino}') t;")[0]
        b = duck(f"SELECT count(*) AS n, sum(hash(t)::HUGEINT)::VARCHAR AS s FROM ({sql}) t;")[0]
        if a == b:
            return a["n"]
        print(f"    as duas execuções diferem ({a} x {b}), repetindo: {destino}", flush=True)
        os.remove(destino)
    raise RuntimeError(f"duas execuções nunca bateram: {destino}")


def lista(arqs):
    return "[" + ", ".join(f"'{a}'" for a in arqs) + "]"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ds"); ap.add_argument("tb")
    ap.add_argument("--chave", required=True, help="coluna para cortar as faixas (não precisa ser única)")
    ap.add_argument("--data", required=True, help="coluna da data do retrato")
    ap.add_argument("--exclui", default="", help="arquivos duplicados byte a byte, a não ler")
    ap.add_argument("--linhas-por-faixa", type=int, default=15_000_000)
    ap.add_argument("--saida", default=os.path.expanduser("~/scrap_tmp/retrato_hist"))
    a = ap.parse_args()

    exclui = {x for x in a.exclui.split(",") if x}
    pasta = f"{ROOT}/{a.ds}/{a.tb}"
    arqs = sorted(f"{pasta}/{f}" for f in os.listdir(pasta) if f.endswith(".parquet") and f not in exclui)
    F = lista(arqs)
    out = f"{a.saida}/{a.ds}/{a.tb}"
    os.makedirs(f"{out}/historico", exist_ok=True)
    os.makedirs(os.path.expanduser("~/duckdb_tmp/retrato_hist"), exist_ok=True)
    D, K = a.data, a.chave
    print(f"{a.ds}.{a.tb}: {len(arqs)} arquivos ({len(exclui)} excluídos)", flush=True)

    # 1. retratos (ordinal global) e impressão digital da fonte por retrato
    fonte_fp = f"{out}/fonte_por_retrato.parquet"
    if not os.path.exists(fonte_fp):
        duck(f"COPY (SELECT {D}, count(*) n, sum(h::HUGEINT) s FROM "
             f"(SELECT {D}, hash(*COLUMNS(* EXCLUDE ({D}))) h FROM read_parquet({F})) "
             f"GROUP BY 1 ORDER BY 1) TO '{fonte_fp}';")
    fp = duck(f"SELECT count(*) r, sum(n)::BIGINT n, max({D})::VARCHAR ult FROM '{fonte_fp}';")[0]
    ext = f"{out}/retratos.parquet"
    duck(f"COPY (SELECT {D}, row_number() OVER (ORDER BY {D}) k FROM '{fonte_fp}') TO '{ext}';")
    print(f"  {fp['r']} retratos, {fp['n']} linhas, último {fp['ult']}", flush=True)

    # 2. faixas da chave pelo último retrato
    nf = max(1, -(-fp["n"] // a.linhas_por_faixa))
    qs = [i / nf for i in range(1, nf)]
    lim = duck(f"SELECT quantile_disc({K}, {qs}) q FROM read_parquet({F}) WHERE {D} = '{fp['ult']}';")[0]["q"] if nf > 1 else []
    lim = sorted(set(lim))
    faixas = list(zip([None] + lim, lim + [None]))
    print(f"  {len(faixas)} faixas", flush=True)

    # 3. histórico por faixa
    for i, (lo, hi) in enumerate(faixas):
        dest = f"{out}/historico/faixa_{i:03d}.parquet"
        if os.path.exists(dest):
            continue
        cond = " AND ".join(c for c in [f"{K} >= '{lo}'" if lo else "", f"{K} < '{hi}'" if hi else ""] if c) or "true"
        sql = f"""
WITH src AS (SELECT * FROM read_parquet({F}) WHERE {cond}),
r0 AS (SELECT *, hash(*COLUMNS(* EXCLUDE ({D}))) h FROM src),
r AS (SELECT r0.*, e.k FROM r0 JOIN '{ext}' e USING ({D})),
r2 AS (SELECT *, row_number() OVER (PARTITION BY k, h) d FROM r),
r3 AS (SELECT *, k - row_number() OVER (PARTITION BY h, d ORDER BY k) grp FROM r2)
SELECT * EXCLUDE (h, d, grp) FROM (
  SELECT min({D}) AS inicio, max({D}) AS fim, COLUMNS(lambda c: c NOT IN ('{D}', 'k')) FROM r3 GROUP BY ALL
) ORDER BY {K}, inicio"""
        t0 = time.time()
        n = copia_dupla(sql, dest)
        print(f"  faixa {i:03d} [{lo}, {hi}): {n} períodos, {time.time() - t0:.0f} s", flush=True)

    # 4. conferência por retrato: reconstrução = fonte
    H = f"{out}/historico/faixa_*.parquet"
    rec = f"{out}/reconstrucao_por_retrato.parquet"
    duck(f"COPY (SELECT e.{D}, count(*) n, sum(hx::HUGEINT) s FROM "
         f"(SELECT inicio, fim, hash(*COLUMNS(* EXCLUDE (inicio, fim))) hx FROM read_parquet('{H}')) h "
         f"JOIN '{ext}' e ON e.{D} BETWEEN h.inicio AND h.fim GROUP BY 1 ORDER BY 1) TO '{rec}';")
    dif = duck(f"SELECT count(*) d FROM '{fonte_fp}' f FULL JOIN '{rec}' r USING ({D}) "
               f"WHERE f.n IS DISTINCT FROM r.n OR f.s IS DISTINCT FROM r.s;")[0]["d"]
    tot = duck(f"SELECT count(*) p FROM read_parquet('{H}');")[0]["p"]
    print(f"  conferência: {fp['r']} retratos, {dif} diferentes; {tot} períodos para {fp['n']} linhas", flush=True)
    if dif:
        sys.exit(f"ERRO: {dif} retratos não batem")

    # 5. último retrato, do histórico, conferido contra a fonte
    ult = f"{out}/ultimo_retrato.parquet"
    cols = [c["column_name"] for c in duck(f"DESCRIBE SELECT * FROM read_parquet({lista(arqs[:1])});")]
    sel = ", ".join(f"'{fp['ult']}'::DATE AS {c}" if c == D else c for c in cols)
    copia_dupla(f"SELECT {sel} FROM read_parquet('{H}') WHERE fim = '{fp['ult']}' ORDER BY {K}", ult)
    a1 = duck(f"SELECT count(*) n, sum(hash(t)::HUGEINT)::VARCHAR s FROM read_parquet('{ult}') t;")[0]
    a2 = duck(f"SELECT count(*) n, sum(hash(t)::HUGEINT)::VARCHAR s FROM (SELECT * FROM read_parquet({F}) "
              f"WHERE {D} = '{fp['ult']}') t;")[0]
    print(f"  último retrato: {a1} x fonte {a2}", flush=True)
    if a1 != a2:
        sys.exit("ERRO: último retrato não bate")
    print("OK", flush=True)


if __name__ == "__main__":
    main()
