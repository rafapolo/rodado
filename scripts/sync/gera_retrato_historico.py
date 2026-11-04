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

Retrato novo (uso normal depois de 2026-11-04): `--anexa`, sem reler o passado nem os retratos
brutos. O retrato novo cai em ~/scrap_tmp/retrato_novo/<ds>/<tb>/ (nunca em <tb>/) e:

    flock ~/scrap_tmp/pesado.lock python3 gera_retrato_historico.py br_rf_cno areas --anexa

  - linha cuja identidade (hash da linha + ordinal da cópia) está vigente (fim = último retrato):
    `fim` passa a D; linha nova ou mudada: período novo, inicio = fim = D; linha que sumiu: fica
    fechada como está. Mesmo resultado de regerar tudo (conferido em 2026-11-04, ver o doc);
  - recusa D <= max(fim), retrato vazio, mais de uma data, id NULL, colunas/tipos diferentes do
    histórico, parquet solto em <tb>/ e encolhimento acima do limite (--aceitar-encolher);
  - confere (contagem + soma do hash) D contra a fonte e TODAS as datas antigas contra o histórico
    de antes; só então troca o histórico e <tb>/000000000000.parquet (os antigos vão para o trabalho).

Conferência, no fim: para CADA retrato, contagem e soma do hash da linha reconstruída pelo
histórico (`inicio <= data <= fim`) = as mesmas da fonte. Cada faixa também é gravada pela
`copia_dupla` (grava, e recalcula a impressão digital direto da consulta).
"""
import argparse, glob, json, os, shutil, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DUCKDB = os.path.expanduser("~/bin/duckdb")
ROOT = os.environ.get("RETRATO_ROOT", os.path.expanduser("~/rodado"))
PREFIXO = ("SET enable_progress_bar=false; SET memory_limit='10GB'; SET threads=6; "
           "SET preserve_insertion_order=false; "
           f"SET temp_directory='{os.path.expanduser('~/duckdb_tmp')}/retrato_hist';\n")


def duck(sql, tentativas=4):
    for t in range(tentativas):
        r = subprocess.run([DUCKDB, "-init", "/dev/null", "-json"], input=PREFIXO + sql.rstrip().rstrip(";") + ";\n.quit\n",
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
    ap.add_argument("--chave", help="coluna para cortar as faixas (não precisa ser única)")
    ap.add_argument("--data", help="coluna da data do retrato")
    ap.add_argument("--anexa", action="store_true",
                    help="acrescenta o retrato novo (de --novo) ao histórico publicado, sem reler o passado")
    ap.add_argument("--novo", help="--anexa: diretório (recursivo) ou glob do retrato novo; "
                                   "padrão ~/scrap_tmp/retrato_novo/<ds>/<tb>")
    ap.add_argument("--aceitar-encolher", action="store_true",
                    help="--anexa: aceita retrato com menos de --limite-encolher das linhas do anterior")
    ap.add_argument("--limite-encolher", type=float, default=0.9)
    ap.add_argument("--sem-publica", action="store_true",
                    help="--anexa: confere e deixa tudo no trabalho, sem trocar nada em ROOT")
    ap.add_argument("--exclui", default="", help="arquivos duplicados byte a byte, a não ler")
    ap.add_argument("--linhas-por-faixa", type=int, default=15_000_000)
    ap.add_argument("--saida",
                    help="trabalho (no --anexa, padrão ~/scrap_tmp/retrato_hist_anexa)")
    a = ap.parse_args()
    a.saida = a.saida or (None if a.anexa else os.path.expanduser("~/scrap_tmp/retrato_hist"))

    if a.anexa:
        import retrato_novo
        cfg = retrato_novo.config(f"{a.ds}.{a.tb}") or {}
        a.chave, a.data = a.chave or cfg.get("chave"), a.data or cfg.get("data")
    if not (a.chave and a.data):
        sys.exit("--chave e --data são obrigatórios (ou a tabela tem de estar em docs/context/retratos_historico.yaml)")
    if a.anexa:
        return anexa(a)

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


# ---------------------------------------------------------------------------------------------
# --anexa
# ---------------------------------------------------------------------------------------------
def q(c):
    return '"' + c.replace('"', '""') + '"'


def acha_novo(spec):
    if os.path.isdir(spec):
        achados = glob.glob(os.path.join(spec, "**", "*.parquet"), recursive=True)
        return sorted(f for f in achados if "/_anexados/" not in f and not os.path.basename(f).startswith("."))
    return sorted(glob.glob(spec))


def tipos(sql):
    return {c["column_name"]: c["column_type"] for c in duck(sql)}


def valida(arquivos):
    for v in (os.path.expanduser("~/scripts/valida_parquet.py"),
              os.path.join(os.path.dirname(os.path.abspath(__file__)), "valida_parquet.py")):
        if os.path.exists(v):
            break
    r = subprocess.run([sys.executable, v, "--stdin", "--sem-anterior"], input="\n".join(arquivos) + "\n",
                       capture_output=True, text=True)
    if r.returncode != 0:
        ruins = [l for l in r.stdout.splitlines() if '"ok": false' in l]
        sys.exit(f"ERRO: valida_parquet reprovou {len(ruins)} arquivo(s): {(ruins[0] if ruins else r.stderr)[:300]}")


def arq_h_cur(hist):
    return [f for f in os.listdir(hist) if f.endswith(".parquet")]


def anexa(a):
    ds, tb, K, D = a.ds, a.tb, a.chave, a.data
    atual, hist = f"{ROOT}/{ds}/{tb}", f"{ROOT}/{ds}/{tb}_historico"
    spec = a.novo or os.path.expanduser(f"~/scrap_tmp/retrato_novo/{ds}/{tb}")
    spec = os.path.expanduser(spec)
    trab_raiz = a.saida or os.path.expanduser("~/scrap_tmp/retrato_hist_anexa")
    os.makedirs(os.path.expanduser("~/duckdb_tmp/retrato_hist"), exist_ok=True)

    # 0. pré-condições
    soltos = sorted(f for f in os.listdir(atual) if f.endswith(".parquet"))
    if soltos != ["000000000000.parquet"]:
        sys.exit(f"ERRO: {atual} deveria ter só 000000000000.parquet (o último retrato); tem {soltos[:6]}. "
                 f"Parquet solto aí dobra o retrato: tire-o dali (para o trabalho) antes de anexar.")
    arq_h = sorted(f"{hist}/{f}" for f in os.listdir(hist) if f.endswith(".parquet"))
    if not arq_h:
        sys.exit(f"ERRO: {hist} sem histórico")
    novos = acha_novo(spec)
    if not novos:
        sys.exit(f"ERRO: retrato vazio: nenhum parquet em {spec}")
    H, F = lista(arq_h), lista(novos)
    th = tipos(f"DESCRIBE SELECT * FROM read_parquet({H});")
    ta = tipos(f"DESCRIBE SELECT * FROM read_parquet('{atual}/000000000000.parquet');")
    tn = tipos(f"DESCRIBE SELECT * FROM read_parquet({F}, union_by_name=true);")
    cols = [c for c in th if c not in ("inicio", "fim")]            # ordem do histórico = ordem do hash
    cols_atual = list(ta)
    if {c: t for c, t in th.items() if c not in ("inicio", "fim")} != {c: t for c, t in ta.items() if c != D}:
        sys.exit("ERRO: histórico e tabela atual com colunas/tipos diferentes")
    if tn != ta:
        dif = {c: (ta.get(c), tn.get(c)) for c in set(ta) | set(tn) if ta.get(c) != tn.get(c)}
        sys.exit(f"ERRO: colunas/tipos do retrato novo diferem da tabela atual (esperado, recebido): {dif}. "
                 f"Schema mudou na fonte: regere o histórico, não anexe.")
    C = ", ".join(q(c) for c in cols)
    fonte = f"read_parquet({F}, union_by_name=true)"
    nulos = duck(f"SELECT count(*) FILTER (WHERE {q(D)} IS NULL) d, count(*) FILTER (WHERE {q(K)} IS NULL) k, "
                 f"count(*) n FROM {fonte};")[0]
    if nulos["n"] == 0:
        sys.exit(f"ERRO: retrato vazio: {len(novos)} arquivo(s) sem linhas")
    if nulos["d"] or nulos["k"]:
        sys.exit(f"ERRO: {nulos['d']} linhas sem {D} e {nulos['k']} sem {K} no retrato novo")
    datas = [r["d"] for r in duck(f"SELECT DISTINCT {q(D)}::VARCHAR d FROM {fonte} ORDER BY 1;")]
    print(f"{ds}.{tb}: retrato(s) novo(s) {datas} em {len(novos)} arquivo(s); {nulos['n']} linhas", flush=True)

    ult = duck(f"SELECT max(fim)::VARCHAR u FROM read_parquet({H});")[0]["u"]
    for d in datas:
        if d <= ult:
            sys.exit(f"ERRO: {D} = {d} <= max(fim) = {ult} do histórico: nada a anexar (ou retrato repetido/mais antigo)")

    # a tabela atual tem de ser o histórico em max(fim)
    def fp_hist(Hs, d):
        return duck(f"SELECT count(*) n, coalesce(sum(hx::HUGEINT), 0)::VARCHAR s FROM (SELECT hash(*COLUMNS(* EXCLUDE (inicio, fim))) hx "
                    f"FROM read_parquet({Hs}) WHERE inicio <= '{d}'::DATE AND fim >= '{d}'::DATE);")[0]

    def fp_fonte(filtro):
        return duck(f"SELECT count(*) n, coalesce(sum(hx::HUGEINT), 0)::VARCHAR s FROM (SELECT hash(*COLUMNS(*)) hx FROM "
                    f"(SELECT {C} FROM {fonte} WHERE {filtro}));")[0]

    fh, fa = fp_hist(H, ult), duck(
        f"SELECT count(*) n, coalesce(sum(hx::HUGEINT), 0)::VARCHAR s FROM (SELECT hash(*COLUMNS(* EXCLUDE ({q(D)}))) hx "
        f"FROM read_parquet('{atual}/000000000000.parquet'));")[0]
    if fh != fa:
        sys.exit(f"ERRO: a tabela atual ({fa}) não é o histórico em {ult} ({fh}): histórico defasado ou tabela mexida")
    n_ult = fh["n"]

    for d in datas:  # um retrato por vez, em ordem
        anexa_um(a, d, ult, n_ult, K, D, cols, cols_atual, C, fonte, H, atual, hist, trab_raiz, novos, fp_hist, fp_fonte)
        ult = d
        arq_h = sorted(f"{hist}/{f}" for f in os.listdir(hist) if f.endswith(".parquet"))
        H = lista(arq_h)
        n_ult = duck(f"SELECT count(*) n FROM read_parquet({H}) WHERE fim = '{ult}'::DATE;")[0]["n"]
    if not a.sem_publica and os.path.isdir(spec):
        dest = f"{spec}/_anexados"
        os.makedirs(dest, exist_ok=True)
        for f in novos:
            rel = os.path.relpath(f, spec)
            os.makedirs(os.path.dirname(f"{dest}/{rel}") or dest, exist_ok=True)
            shutil.move(f, f"{dest}/{rel}")
        print(f"  retrato novo movido para {dest}", flush=True)
    print("OK", flush=True)


def anexa_um(a, d, ult, n_ult, K, D, cols, cols_atual, C, fonte, H, atual, hist, trab_raiz, novos, fp_hist, fp_fonte):
    ds, tb = a.ds, a.tb
    trab = f"{trab_raiz}/{ds}/{tb}/{d}"
    shutil.rmtree(trab, ignore_errors=True)
    os.makedirs(f"{trab}/montagem")
    filtro = f"{q(D)} = '{d}'::DATE"
    src_fp = fp_fonte(filtro)
    print(f"-- {d}: {src_fp['n']} linhas no retrato novo; vigente em {ult}: {n_ult}", flush=True)
    if src_fp["n"] < a.limite_encolher * n_ult and not a.aceitar_encolher:
        sys.exit(f"ERRO: retrato {d} tem {src_fp['n']} linhas, {src_fp['n'] / n_ult:.0%} das {n_ult} de {ult} "
                 f"(limite {a.limite_encolher:.0%}); confira a fonte, ou --aceitar-encolher")

    # datas conferidas: todas as pontas de período do histórico de antes (+ o retrato novo depois)
    antes = f"{trab}/reconstrucao_antes.parquet"
    def reconstrucao(Hs, destino, datas_sql):
        duck(f"COPY (SELECT t.dt::VARCHAR AS dt, count(*) n, sum(hx::HUGEINT)::VARCHAR s FROM "
             f"(SELECT inicio, fim, hash(*COLUMNS(* EXCLUDE (inicio, fim))) hx FROM read_parquet({Hs})) h "
             f"JOIN ({datas_sql}) t(dt) ON t.dt::DATE BETWEEN h.inicio AND h.fim GROUP BY 1 ORDER BY 1) TO '{destino}';")
    dts = f"SELECT DISTINCT x FROM (SELECT inicio x FROM read_parquet({H}) UNION ALL SELECT fim FROM read_parquet({H}))"
    reconstrucao(H, antes, dts)
    n_datas = duck(f"SELECT count(*) n FROM '{antes}';")[0]["n"]

    # faixas: o limite de baixo da faixa i é o min da chave dela; a primeira e a última ficam abertas
    mins = duck(f"SELECT filename f, min({q(K)}) lo, max({q(K)}) hi FROM read_parquet({H}, filename=true) GROUP BY 1 ORDER BY lo;")
    if len(mins) != len(arq_h_cur(hist)):
        sys.exit(f"ERRO: {len(arq_h_cur(hist)) - len(mins)} arquivo(s) de histórico sem linhas em {hist}")
    for x, y in zip(mins, mins[1:]):
        if not x["hi"] < y["lo"]:
            sys.exit(f"ERRO: faixas se sobrepõem: {x['f']} até {x['hi']} x {y['f']} desde {y['lo']}")
    novos_h = lista([m["f"] for m in mins])
    tot = {"estende": 0, "novo": 0, "periodos": 0}
    t0 = time.time()
    for i, m in enumerate(mins):
        lo = m["lo"] if i else None
        hi = mins[i + 1]["lo"] if i + 1 < len(mins) else None
        cond = " AND ".join(c for c in [f"{q(K)} >= '{lo}'" if lo else "",
                                        f"{q(K)} < '{hi}'" if hi else ""] if c) or "true"
        dest = f"{trab}/montagem/{os.path.basename(m['f'])}"
        sql = f"""
WITH v AS (SELECT *, hash(*COLUMNS(* EXCLUDE (inicio, fim))) AS __h FROM read_parquet('{m['f']}')),
vv AS (SELECT *, row_number() OVER (PARTITION BY __h, (fim = '{ult}'::DATE) ORDER BY inicio) AS __d FROM v),
n0 AS (SELECT {C}, hash(*COLUMNS(*)) AS __h FROM (SELECT {C} FROM {fonte} WHERE {filtro} AND {cond})),
n AS (SELECT *, row_number() OVER (PARTITION BY __h) AS __d FROM n0)
SELECT inicio, fim, {C} FROM (
  SELECT vv.inicio, CASE WHEN n.__h IS NOT NULL THEN '{d}'::DATE ELSE vv.fim END AS fim, {", ".join("vv." + q(c) for c in cols)}
  FROM vv LEFT JOIN n ON vv.fim = '{ult}'::DATE AND vv.__h = n.__h AND vv.__d = n.__d
  UNION ALL
  SELECT '{d}'::DATE, '{d}'::DATE, {", ".join("n." + q(c) for c in cols)}
  FROM n WHERE NOT EXISTS (SELECT 1 FROM vv WHERE vv.fim = '{ult}'::DATE AND vv.__h = n.__h AND vv.__d = n.__d)
) ORDER BY {q(K)}, inicio"""
        n = copia_dupla(sql, dest)
        r = duck(f"SELECT count(*) FILTER (WHERE inicio = '{d}'::DATE) novos, "
                 f"count(*) FILTER (WHERE fim = '{d}'::DATE AND inicio < '{d}'::DATE) estendidos FROM read_parquet('{dest}');")[0]
        tot["novo"] += r["novos"]; tot["estende"] += r["estendidos"]; tot["periodos"] += n
        print(f"  {os.path.basename(dest)} [{lo}, {hi}): {n} períodos, {r['novos']} novos, {r['estendidos']} estendidos, "
              f"{time.time() - t0:.0f} s", flush=True)
    M = f"{trab}/montagem/*.parquet"

    # conferência 1: D reconstruído = fonte (contagem + soma do hash)
    rd = fp_hist(f"'{M}'", d)
    print(f"  conferência D={d}: histórico {rd} x fonte {src_fp}", flush=True)
    if rd != src_fp:
        sys.exit(f"ERRO: o retrato {d} reconstruído não bate com a fonte; nada publicado, trabalho em {trab}")
    # conferência 2: nenhuma data antiga mudou (contagem + soma do hash em cada ponta de período)
    depois = f"{trab}/reconstrucao_depois.parquet"
    reconstrucao(f"'{M}'", depois, f"SELECT dt FROM '{antes}'")
    dif = duck(f"SELECT count(*) d FROM '{antes}' x FULL JOIN '{depois}' y USING (dt) "
               f"WHERE x.n IS DISTINCT FROM y.n OR x.s IS DISTINCT FROM y.s;")[0]["d"]
    print(f"  conferência do passado: {n_datas} datas, {dif} diferentes", flush=True)
    if dif:
        sys.exit(f"ERRO: {dif} datas antigas mudaram; nada publicado, trabalho em {trab}")
    # conferência 3: períodos antigos intactos fora o fim (o histórico novo, com o fim revertido, é o antigo + novos)
    h_ant = duck(f"SELECT count(*) n, sum(hash(t)::HUGEINT)::VARCHAR s FROM (SELECT inicio, fim, {C} FROM read_parquet({H})) t;")[0]
    h_rev = duck(f"SELECT count(*) n, sum(hash(t)::HUGEINT)::VARCHAR s FROM (SELECT inicio, CASE WHEN fim = '{d}'::DATE THEN '{ult}'::DATE ELSE fim END AS fim, {C} "
                 f"FROM read_parquet('{M}') WHERE inicio < '{d}'::DATE) t;")[0]
    print(f"  histórico antigo {h_ant} x novo sem o que abriu em {d} e com fim revertido {h_rev}", flush=True)
    if h_ant != h_rev:
        sys.exit(f"ERRO: o passado do histórico não é o mesmo; nada publicado, trabalho em {trab}")

    # nova tabela atual: o retrato, na ordem da chave, direto da fonte
    novo_atual = f"{trab}/000000000000.parquet"
    copia_dupla(f"SELECT {', '.join(q(c) for c in cols_atual)} FROM {fonte} WHERE {filtro} ORDER BY {q(K)}", novo_atual)
    fn = duck(f"SELECT count(*) n, sum(hash(*COLUMNS(* EXCLUDE ({q(D)})))::HUGEINT)::VARCHAR s FROM read_parquet('{novo_atual}');")[0]
    if fn != src_fp:
        sys.exit(f"ERRO: tabela atual nova {fn} x fonte {src_fp}")
    valida([novo_atual] + sorted(glob.glob(M)))
    print(f"  {tot['periodos']} períodos ({tot['novo']} abertos em {d}, {tot['estende']} estendidos), validado", flush=True)
    if a.sem_publica:
        print(f"  --sem-publica: tudo conferido, em {trab}", flush=True)
        return

    # publica: o antigo vai para o trabalho (nunca para o lixo); nomes iguais, as views por glob seguem valendo
    ant = f"{trab}/substituido"
    os.makedirs(ant)
    shutil.move(hist, f"{ant}/{tb}_historico")
    shutil.move(f"{trab}/montagem", hist)
    shutil.move(f"{atual}/000000000000.parquet", f"{ant}/000000000000.parquet")
    shutil.copyfile(novo_atual, f"{atual}/000000000000.parquet")
    os.chmod(hist, 0o775)
    for f in glob.glob(f"{hist}/*.parquet") + [f"{atual}/000000000000.parquet"]:
        os.chmod(f, 0o664)
    pos = duck(f"SELECT count(*) n, sum(hash(*COLUMNS(* EXCLUDE ({q(D)})))::HUGEINT)::VARCHAR s FROM read_parquet('{atual}/000000000000.parquet');")[0]
    pos_h = fp_hist(lista(sorted(glob.glob(f"{hist}/*.parquet"))), d)
    if pos != src_fp or pos_h != src_fp:
        sys.exit(f"ERRO depois de publicar: atual {pos}, histórico {pos_h}, fonte {src_fp}; anterior em {ant}")
    print(f"  publicado: {hist} e {atual}/000000000000.parquet = {d} ({pos['n']} linhas); anterior em {ant} (apagar à mão)", flush=True)


if __name__ == "__main__":
    sys.exit(main())
