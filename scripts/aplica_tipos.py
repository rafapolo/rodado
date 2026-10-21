#!/usr/bin/env python3
"""Reescreve no beelink os parquet das colunas de `docs/context/tipos_aplicar.json`
(saída de `inventaria_tipos.py --seleciona`) com o tipo certo — STRING -> DOUBLE/DATE/
TIMESTAMP/INTEGER/BIGINT — sem perder valor.

Por tabela, nesta ordem, e qualquer falha deixa a tabela como estava:

  1. trava estrita, na tabela inteira: todo valor não vazio casa com o padrão do formato
     escolhido. "Não virar NULL" não basta — TRY_CAST('1.5' AS BIGINT) dá 2 e o
     replace() do formato pt-BR transforma '12.5' em 125, ambos sem NULL nenhum.
     Coluna que não passa fica de fora (registrada), as outras seguem.
  2. cada arquivo é reescrito em ~/tipos_staging (zstd, row_group_size 122880, mesma
     ordem de linhas e de colunas, mesmo nome), fora do glob da tabela
  3. conferência contra o original, por POSITIONAL JOIN: mesmo número de linhas, e
     expr(original) IS NOT DISTINCT FROM novo em toda linha de toda coluna
  4. o original vira hardlink em ~/.backups/tipos-<data>/ (mesmo disco, custo zero) e
     o novo entra por rename atômico — quem está lendo segue com o inode antigo
  5. a view é recriada com o próprio SQL (duckdb_views().sql): ela guarda o tipo antigo

    python3 scripts/aplica_tipos.py --roda [ds.tb,...]  # sobe e dispara (nohup, retomável)
    python3 scripts/aplica_tipos.py --status
"""
import json, os, subprocess, sys

HOST = os.environ.get("BEELINK_HOST", "beelink")
APLICAR = "docs/context/tipos_aplicar.json"

REMOTO = r'''
import duckdb, glob, json, os, re, sys, time
H = os.path.expanduser("~")
R = f"{H}/rodado"
DATA = os.environ["DATA"]
BACKUP = f"{H}/.backups/tipos-{DATA}"
STAGING = f"{H}/tipos_staging"
OUT = f"{H}/aplica_tipos.jsonl"
SO = set(filter(None, os.environ.get("SO", "").split(",")))
plano = json.load(open(f"{H}/tipos_aplicar.json"))

NUM_BR = r"[+-]?(\d+|\d{1,3}(\.\d{3})+)(,\d+)?|[+-]?,\d+"
NUM_US = r"[+-]?(\d+|\d{1,3}(,\d{3})+)(\.\d+)?|[+-]?\.\d+|[+-]?\d+(\.\d+)?[eE][+-]?\d+"
ISO_D = r"\d{4}-\d{2}-\d{2}"
# só Z: CAST(... AS TIMESTAMP) descarta o fuso calado ('...-03:00' sai igual a '...Z'), então
# offset diferente de UTC deixa a coluna como texto em vez de deslocar a hora
ISO_DT = r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2}(\.\d+)?)?Z?"
BR_D = r"\d{1,2}/\d{1,2}/\d{4}"
BR_DT = r"\d{1,2}/\d{1,2}/\d{4}[ T]\d{1,2}:\d{2}(:\d{2})?"

def padrao(expr):
    if "replace(replace" in expr: return NUM_BR
    if "replace({x}, ','" in expr: return NUM_US
    if "AS BIGINT" in expr: return r"[+-]?\d+"
    if "'%Y-%m-%d'" in expr: return ISO_D
    if "AS TIMESTAMP" in expr: return f"{ISO_D}|{ISO_DT}"
    if "['%d/%m/%Y" in expr: return f"{BR_D}|{BR_DT}"
    if "'%d/%m/%Y'" in expr: return BR_D
    if "'%Y%m%d'" in expr or "'%d%m%Y'" in expr: return r"\d{8}"
    raise ValueError(expr)

def ident(c): return '"' + c.replace('"', '""') + '"'
def lit(s): return "'" + s.replace("'", "''") + "'"

con = duckdb.connect()
con.execute("SET threads=6; SET memory_limit='8GB'")
con.execute(f"SET temp_directory='{H}/duckdb_tmp'")

feitos = set()
if os.path.exists(OUT):
    for l in open(OUT):
        j = json.loads(l)
        if j.get("fim"): feitos.add(j["tabela"])
f = open(OUT, "a")
def w(o): f.write(json.dumps(o, ensure_ascii=False, default=str) + "\n"); f.flush()

por_tabela = {}
for o in plano: por_tabela.setdefault(o["tabela"], []).append(o)

for tabela, cols in sorted(por_tabela.items()):
    if tabela in feitos or SO and tabela not in SO: continue
    ds, tb = tabela.split(".", 1)
    d = f"{R}/{ds}/{tb}"
    arqs = sorted(glob.glob(f"{d}/**/*.parquet", recursive=True))
    t0 = time.time()
    try:
        full = f"read_parquet({lit(d + '/**/*.parquet')}, union_by_name=true, hive_partitioning=false)"
        tipos_atuais = {r[0]: r[1] for r in con.execute(f"DESCRIBE SELECT * FROM {full}").fetchall()}
        # 1. trava estrita + dígitos significativos na tabela inteira
        ok = []
        for o in cols:
            c = o["coluna"]
            if tipos_atuais.get(c) != "VARCHAR":
                w({"tabela": tabela, "coluna": c, "pulada": f"tipo atual {tipos_atuais.get(c)}"}); continue
            x = f"trim({ident(c)})"
            fora, sig, lz, n = con.execute(
                f"SELECT count_if({x} <> '' AND NOT regexp_full_match({x}, {lit(padrao(o['expr']))})), "
                f"max(length(ltrim(regexp_replace({x}, '[^0-9]', '', 'g'), '0'))) FILTER ({x} <> ''), "
                f"count_if(regexp_full_match({x}, '[+-]?0[0-9].*')), count_if({x} <> '') FROM {full}").fetchone()
            # zero à esquerda em mais de 1% dos valores é código ('014808.2010', protocolo número.ano
            # do IBAMA): o número sai igual, o texto não volta
            if o["tipo"] not in ("DATE", "TIMESTAMP") and n and lz > 0.01 * n:
                w({"tabela": tabela, "coluna": c, "pulada": f"{lz} de {n} valores com zero a esquerda (codigo)"}); continue
            sig = sig or 0
            tipo = o["tipo"]
            if tipo in ("INTEGER", "BIGINT"): tipo = "INTEGER" if sig <= 9 else "BIGINT" if sig <= 18 else None
            if tipo == "DOUBLE" and sig > 15: tipo = None
            if fora or tipo is None:
                w({"tabela": tabela, "coluna": c, "pulada": f"{fora} valores fora do padrao, {sig} digitos"}); continue
            ok.append((c, tipo, o["expr"].format(x=x)))
        if not ok:
            w({"tabela": tabela, "fim": True, "colunas": 0}); continue
        # 2-3. reescreve e confere arquivo a arquivo
        trocas = []
        for a in arqs:
            rel = os.path.relpath(a, R)
            novo = f"{STAGING}/{rel}"
            os.makedirs(os.path.dirname(novo), exist_ok=True)
            presentes = {r[0] for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet({lit(a)})").fetchall()}
            aqui = [(c, t, e) for c, t, e in ok if c in presentes]
            if not aqui: continue
            rep = ", ".join(f"CAST({e} AS {t}) AS {ident(c)}" for c, t, e in aqui)
            con.execute(f"COPY (SELECT * REPLACE ({rep}) FROM read_parquet({lit(a)})) TO {lit(novo)} "
                        "(FORMAT parquet, COMPRESSION zstd, ROW_GROUP_SIZE 122880)")
            n_old = con.execute(f"SELECT count(*) FROM read_parquet({lit(a)})").fetchone()[0]
            n_new = con.execute(f"SELECT count(*) FROM read_parquet({lit(novo)})").fetchone()[0]
            difs = ", ".join(
                f"count_if(CAST({e.replace('trim(' + ident(c) + ')', 'trim(o.' + ident(c) + ')')} AS {t}) IS DISTINCT FROM n.{ident(c)})"
                for c, t, e in aqui)
            perdas = ", ".join(f"count_if(trim(o.{ident(c)}) <> '' AND n.{ident(c)} IS NULL)" for c, _, _ in aqui)
            # uma contagem por coluna, somadas aqui: 1.945 colunas numa soma só (SISDEPEN)
            # estouram o max_expression_depth do DuckDB
            r = con.execute(
                f"SELECT {difs}, {perdas} FROM (SELECT * FROM read_parquet({lit(a)})) o "
                f"POSITIONAL JOIN (SELECT * FROM read_parquet({lit(novo)})) n").fetchone()
            dif, perda = sum(v or 0 for v in r[:len(aqui)]), sum(v or 0 for v in r[len(aqui):])
            tipos_novos = {r[0]: r[1] for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet({lit(novo)})").fetchall()}
            errado = [c for c, t, _ in aqui if tipos_novos.get(c) != t]
            if n_old != n_new or dif or perda or errado:
                raise RuntimeError(f"{rel}: linhas {n_old}->{n_new}, diferencas {dif}, perdas {perda}, tipo {errado}")
            trocas.append((a, novo, rel))
        # 4. backup por hardlink + rename atômico
        for a, novo, rel in trocas:
            b = f"{BACKUP}/{rel}"
            os.makedirs(os.path.dirname(b), exist_ok=True)
            if not os.path.exists(b): os.link(a, b)
            os.replace(novo, a)
        w({"tabela": tabela, "fim": True, "colunas": len(ok), "arquivos": len(trocas),
           "aplicadas": [[c, t] for c, t, _ in ok], "seg": round(time.time() - t0, 1)})
    except Exception as e:
        w({"tabela": tabela, "erro": str(e)[:500]})
print("FIM", file=sys.stderr)
'''


def roda():
    so = sys.argv[2] if len(sys.argv) > 2 else ""
    import datetime
    data = datetime.date.today().isoformat()
    subprocess.run(["scp", "-q", APLICAR, f"{HOST}:tipos_aplicar.json"], check=True)
    subprocess.run(["ssh", HOST, "cat > ~/aplica_tipos_remoto.py"], input=REMOTO, text=True, check=True)
    cmd = f"DATA={data} SO='{so}' nice python3 ~/aplica_tipos_remoto.py >> ~/aplica_tipos.log 2>&1"
    if so:
        subprocess.run(["ssh", HOST, cmd], check=True)
        subprocess.run(["ssh", HOST, "tail -n 50 ~/aplica_tipos.jsonl"])
    else:
        subprocess.run(["ssh", HOST, f"nohup sh -c \"{cmd}\" >/dev/null 2>&1 &"], check=True)
        print("disparado; --status")


def status():
    subprocess.run(["ssh", HOST, "grep -c '\"fim\": true' ~/aplica_tipos.jsonl; grep -c '\"erro\"' ~/aplica_tipos.jsonl; "
                    "grep -c '\"pulada\"' ~/aplica_tipos.jsonl; tail -c 300 ~/aplica_tipos.log"])


MAPA = "docs/context/tipos_colunas.json"


def mapa():
    """O que foi aplicado de fato -> docs/context/tipos_colunas.json, que scripts/scrap/_tipos.py
    lê para a próxima coleta sair no mesmo tipo: {dataset.tabela: {coluna: {tipo, expr, padrao}}}."""
    ns = {}
    exec(REMOTO[REMOTO.index("NUM_BR ="):REMOTO.index("def ident")], ns)
    plano = {(o["tabela"], o["coluna"]): o for o in json.load(open(APLICAR))}
    out = {}
    feitos = subprocess.run(["ssh", HOST, "cat ~/aplica_tipos.jsonl"], capture_output=True, text=True, check=True).stdout
    for l in feitos.splitlines():
        o = json.loads(l)
        for c, t in o.get("aplicadas", []):
            e = plano[(o["tabela"], c)]["expr"]
            out.setdefault(o["tabela"], {})[c] = {"tipo": t, "expr": e, "padrao": ns["padrao"](e)}
    json.dump(dict(sorted(out.items())), open(MAPA, "w"), ensure_ascii=False, indent=1)
    print(f"{sum(map(len, out.values()))} colunas em {len(out)} tabelas -> {MAPA}")


if __name__ == "__main__":
    {"--roda": roda, "--status": status, "--mapa": mapa}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
