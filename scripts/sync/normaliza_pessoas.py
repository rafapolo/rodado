#!/usr/bin/env python3
"""Tabelas de pagamento com pessoa repetida, normalizadas: a pessoa vai para uma tabela própria
(um trio NIS/CPF/nome por linha, com id inteiro) e o pagamento guarda só o id.

O parquet não enxerga repetição entre arquivos: o mesmo favorecido aparece em todo mês, e
nome/NIS/CPF sem dicionário eram 96% do novo_bolsa_familia (14,84 GiB -> 3,25 normalizado,
ver tasks/plans/normalizar_e_reordenar.md, seção C). Cada tabela de TABELAS vira:

    <papel>             <papel>_id + as colunas da pessoa (favorecido, beneficiario...)
    pagamento           as colunas de antes sem as da pessoa, mais <papel>_id
    <tabela original>   view: pagamento JOIN <papel>..., as mesmas colunas, na mesma ordem

A view com o nome antigo cita as outras views pelo nome, sem caminho de arquivo: o
repara_views_beelink.py só recria view que cita parquet, então a deixa como está. Agregado sem
pessoa vai direto na `pagamento`: o DuckDB não elimina o join mesmo quando a consulta não usa
nome/CPF/NIS (pela view, 3–7x mais lento, medido 2026-10-22).

    python3 scripts/sync/normaliza_pessoas.py converte <dataset.tabela>   # cópia em ~/tipos_staging/normaliza, mede, confere
    python3 scripts/sync/normaliza_pessoas.py aplica <dataset.tabela>     # troca no ~/rodado (precisa do converte antes)
    python3 scripts/sync/normaliza_pessoas.py acrescenta <dataset.tabela> <parquet no beelink>...

`acrescenta` é o caminho de mês novo, chamado pelo scraper (scripts/scrap/portal_transparencia.py)
com o arquivo do mês no formato antigo, já com os tipos ajustados (_tipos.py): grava os trios
novos com id acima do maior, grava pagamento/<mesmo nome do arquivo> (substitui se o mês já
existia), confere com EXCEPT ALL nos dois sentidos e recria as views da pagamento e das pessoas.
Nada é gravado se a conferência falhar ou se os tipos não forem os da tabela atual.

Depois de qualquer modo: scripts/completa_cpf.py sobre a tabela de pessoa (o CPF da fonte vem
mascarado) e a regeneração do catálogo. Roda no beelink, por ssh, como o _tipos.py.
"""
import json
import os
import subprocess
import sys

HOST = os.environ.get("BEELINK_HOST", "beelink")

# tabela -> papéis (nome da tabela de pessoa -> colunas da pessoa) e a ordem de gravação
TABELAS = {
    "br_cgu_novo_bolsa_familia.novo_bolsa_familia": {
        "papeis": {"favorecido": ["nis_favorecido", "cpf_favorecido", "nome_favorecido"]}},
    "br_cgu_pe_de_meia.pe_de_meia": {
        "papeis": {"beneficiario": ["nis_beneficiario", "cpf_beneficiario", "nome_beneficiario"],
                   "responsavel": ["nis_responsavel", "cpf_responsavel", "nome_responsavel"]}},
    "br_cgu_seguro_defeso.seguro_defeso": {
        "papeis": {"favorecido": ["cpf_favorecido", "nis_favorecido", "rgp_favorecido", "nome_favorecido"]}},
    "br_cgu_garantia_safra.garantia_safra": {
        "papeis": {"favorecido": ["nis_favorecido", "nome_favorecido"]}},
}
ORDEM = ["uf", "codigo_municipio_siafi"]  # todas as quatro têm; o id da pessoa vem depois

REMOTO = r'''
import duckdb, glob, json, os, sys, time
modo, nome, cfg, ordem, arquivos = json.loads(sys.stdin.read())
H = os.path.expanduser("~")
ds, tb = nome.split(".", 1)
R = f"{H}/rodado/{ds}"
STAGE = f"{H}/tipos_staging/normaliza/{ds}"
BANCO = f"{H}/rodado/basedosdados.duckdb"
BACKUP = f"{H}/.backups/normaliza-{time.strftime('%Y-%m-%d')}/{ds}"
OPT = "FORMAT parquet, COMPRESSION zstd, COMPRESSION_LEVEL 9, ROW_GROUP_SIZE 122880"
papeis = cfg["papeis"]
pessoa = [c for cols in papeis.values() for c in cols]
q = lambda c: '"' + c.replace('"', '""') + '"'
lit = lambda s: "'" + s.replace("'", "''") + "'"
con = duckdb.connect()
con.execute(f"SET memory_limit='12GB'; SET threads=8; SET preserve_insertion_order=false; SET temp_directory='{H}/duckdb_tmp'")

def log(*a): print(time.strftime("%H:%M:%S"), *a, flush=True)
def igual(a, b, cols): return " AND ".join(f"{a}.{q(c)} IS NOT DISTINCT FROM {b}.{q(c)}" for c in cols)
def lista(d): return "[" + ", ".join(lit(f) for f in sorted(glob.glob(f"{d}/*.parquet"))) + "]"

def grava_mes(entrada, raiz, cols):
    """pagamento/<nome do arquivo> a partir de um arquivo no formato antigo, com as pessoas
    já em tabelas temp p_<papel>; confere e só então troca. Devolve (linhas, MiB)."""
    resto = [c for c in cols if c not in pessoa]
    joins = " ".join(f"JOIN p_{p} ON {igual('e', 'p_' + p, pc)}" for p, pc in papeis.items())
    ids = ", ".join(f"p_{p}.{p}_id" for p in papeis)
    saida = f"{raiz}/pagamento/{os.path.basename(entrada)}"
    con.execute(f"CREATE OR REPLACE TEMP VIEW e AS FROM read_parquet({lit(entrada)})")
    ord_ = ", ".join([f"e.{q(c)}" for c in ordem if c in cols] + [f"p_{p}.{p}_id" for p in papeis])
    con.execute(f"COPY (SELECT {', '.join('e.' + q(c) for c in resto)}, {ids} FROM e {joins} ORDER BY {ord_}) "
                f"TO {lit(saida + '.tmp')} ({OPT})")
    view = (f"SELECT {', '.join(q(c) for c in cols)} FROM read_parquet({lit(saida + '.tmp')}) "
            + " ".join(f"JOIN p_{p} USING ({p}_id)" for p in papeis))
    todas = ", ".join(q(c) for c in cols)
    n0, n1 = (con.execute(f"SELECT count(*) FROM ({x})").fetchone()[0] for x in ("FROM e", view))
    d1 = con.execute(f"SELECT count(*) FROM (SELECT {todas} FROM e EXCEPT ALL {view})").fetchone()[0]
    d2 = con.execute(f"SELECT count(*) FROM ({view} EXCEPT ALL SELECT {todas} FROM e)").fetchone()[0]
    if n0 != n1 or d1 or d2:
        os.remove(saida + ".tmp")
        sys.exit(f"{entrada}: NÃO bateu (linhas {n0}->{n1}, diferença {d1}/{d2}); nada gravado")
    os.replace(saida + ".tmp", saida)
    return n0, os.path.getsize(saida) / 2**20

def views_sql(raiz, cols):
    """pagamento e pessoas com lista explícita de arquivos (como o resto do banco); a view
    com o nome antigo pelas outras views, nas colunas e na ordem de antes."""
    s = [f"CREATE OR REPLACE VIEW {ds}.{t} AS SELECT * FROM read_parquet({lista(f'{raiz}/{t}')}, "
         f"hive_partitioning=true, union_by_name=true);" for t in ["pagamento", *papeis]]
    s.append(f"CREATE OR REPLACE VIEW {ds}.{tb} AS SELECT {', '.join(q(c) for c in cols)} FROM {ds}.pagamento "
             + " ".join(f"JOIN {ds}.{p} USING ({p}_id)" for p in papeis) + ";")
    return s

def impressao(fonte):
    hs = ", ".join(f"sum(hash({q(c)}))::HUGEINT" for c in COLS)
    return con.execute(f"SELECT mes_referencia, count(*), sum(valor_parcela), {hs} FROM {fonte} GROUP BY 1 ORDER BY 1").fetchall()

if modo == "converte":
    origem = sorted(glob.glob(f"{R}/{tb}/*.parquet"))
    COLS = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet({lit(origem[0])})").fetchall()]
    if os.path.exists(STAGE):
        sys.exit(f"{STAGE} já existe: apague à mão para refazer")
    for p in ["pagamento", *papeis]:
        os.makedirs(f"{STAGE}/{p}")
    todos = f"read_parquet({lista(f'{R}/{tb}')}, union_by_name=true)"
    t = time.time()
    for p, pc in papeis.items():
        loc = ", ".join(f"arg_min({q(c)}, mes_referencia) AS {q(c)}" for c in ordem)
        con.execute(f"""COPY (SELECT (row_number() OVER (ORDER BY {', '.join(q(c) for c in ordem + pc)}))::INTEGER AS {p}_id,
                {', '.join(q(c) for c in pc)}
            FROM (SELECT {', '.join(q(c) for c in pc)}, {loc} FROM {todos} GROUP BY ALL) ORDER BY 1)
            TO {lit(f'{STAGE}/{p}/inicial.parquet')} ({OPT})""")
        con.execute(f"CREATE OR REPLACE TEMP TABLE p_{p} AS FROM read_parquet({lit(f'{STAGE}/{p}/inicial.parquet')})")
        log(p, con.execute(f"SELECT count(*) FROM p_{p}").fetchone()[0], "pessoas,",
            round(os.path.getsize(f"{STAGE}/{p}/inicial.parquet") / 2**20), "MiB,", round(time.time() - t), "s")
    for a in origem:
        n, mib = grava_mes(a, STAGE, COLS)
        log(os.path.basename(a), n, "linhas conferidas,", round(os.path.getsize(a) / 2**20), "->", round(mib), "MiB")
    tam = lambda d: sum(os.path.getsize(f) for f in glob.glob(f"{d}/*/*.parquet") + glob.glob(f"{d}/*.parquet")) / 2**30
    log(f"TOTAL {nome}: {tam(f'{R}/{tb}'):.3f} GiB -> {tam(STAGE):.3f} GiB ({100 * tam(STAGE) / tam(f'{R}/{tb}'):.1f}%)")

elif modo == "aplica":
    if not os.path.isdir(f"{STAGE}/pagamento"):
        sys.exit(f"sem {STAGE}: rode converte antes")
    origem = f"{R}/{tb}"
    COLS = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet({lit(sorted(glob.glob(origem + '/*.parquet'))[0])})").fetchall()]
    antes = impressao(f"read_parquet({lista(origem)}, union_by_name=true)")
    rw = duckdb.connect(BANCO)  # falha aqui, antes de mexer em arquivo, se alguém segura o banco
    os.makedirs(os.path.dirname(BACKUP), exist_ok=True)
    os.rename(origem, BACKUP)
    for p in ["pagamento", *papeis]:
        os.rename(f"{STAGE}/{p}", f"{R}/{p}")
    os.rmdir(STAGE)
    for s in views_sql(R, COLS):
        rw.execute(s)
    depois = [tuple(r) for r in rw.execute(
        f"SELECT mes_referencia, count(*), sum(valor_parcela), {', '.join(f'sum(hash({q(c)}))::HUGEINT' for c in COLS)} "
        f"FROM {ds}.{tb} GROUP BY 1 ORDER BY 1").fetchall()]
    rw.close()
    ruins = [a[0] for a, d in zip(antes, depois) if a[:2] + a[3:] != d[:2] + d[3:] or abs((a[2] or 0) - (d[2] or 0)) > 0.01]
    log(f"{nome}: {len(antes)} meses antes, {len(depois)} depois, {len(ruins)} diferentes {ruins[:5]}; original em {BACKUP}")
    if ruins or len(antes) != len(depois):
        sys.exit("NÃO BATEU: desfaça movendo o backup de volta e apagando as views novas")

elif modo == "acrescenta":
    ro = duckdb.connect(BANCO, read_only=True)
    tipos = dict((r[0], r[1]) for r in ro.execute(f"DESCRIBE {ds}.{tb}").fetchall())
    ro.close()
    COLS = list(tipos)
    for p, pc in papeis.items():
        con.execute(f"CREATE OR REPLACE TEMP TABLE p_{p} AS FROM read_parquet({lit(R + '/' + p + '/*.parquet')})")
    for a in arquivos:
        a = os.path.expanduser(a)
        aqui = dict((r[0], r[1]) for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet({lit(a)})").fetchall())
        if aqui != tipos:
            sys.exit(f"{a}: colunas/tipos {aqui} != tabela atual {tipos} (rodou o _tipos.py antes?)")
        for p, pc in papeis.items():
            maximo = con.execute(f"SELECT coalesce(max({p}_id), 0) FROM p_{p}").fetchone()[0]
            loc = ", ".join(f"min({q(c)}) AS {q(c)}" for c in ordem)
            con.execute(f"""CREATE OR REPLACE TEMP TABLE novos AS
                SELECT ({maximo} + row_number() OVER (ORDER BY {', '.join(q(c) for c in ordem + pc)}))::INTEGER AS {p}_id, {', '.join(q(c) for c in pc)}
                FROM (SELECT {', '.join('e.' + q(c) for c in pc)}, {loc} FROM read_parquet({lit(a)}) e
                      WHERE NOT EXISTS (SELECT 1 FROM p_{p} WHERE {igual('e', 'p_' + p, pc)}) GROUP BY ALL)""")
            n = con.execute("SELECT count(*) FROM novos").fetchone()[0]
            if n:
                base = os.path.splitext(os.path.basename(a))[0]
                k, destino = 0, f"{R}/{p}/{base}.parquet"
                while os.path.exists(destino):
                    k += 1; destino = f"{R}/{p}/{base}_{k}.parquet"
                con.execute(f"COPY (FROM novos ORDER BY 1) TO {lit(destino + '.tmp')} ({OPT})")
                con.execute(f"INSERT INTO p_{p} FROM novos")
            log(f"{os.path.basename(a)}: {n} {p}(s) novo(s)")
        try:
            linhas, mib = grava_mes(a, R, COLS)
        except SystemExit:
            for f in glob.glob(f"{R}/*/*.tmp"):
                os.remove(f)
            raise
        for f in glob.glob(f"{R}/*/*.parquet.tmp"):
            os.replace(f, f[:-4])
        log(f"{os.path.basename(a)}: {linhas} linhas conferidas, {mib:.0f} MiB")
    try:
        rw = duckdb.connect(BANCO)
        for s in views_sql(R, COLS):
            rw.execute(s)
        rw.close()
        log("views recriadas")
    except duckdb.Error as e:
        log(f"views NÃO recriadas ({str(e).splitlines()[0][:120]}): rode scripts/repara_views_beelink.py --apply")
'''


def roda(modo, nome, arquivos=()):
    if nome not in TABELAS:
        sys.exit(f"{nome} não está em TABELAS: {', '.join(TABELAS)}")
    subprocess.run(["ssh", HOST, "cat > ~/.normaliza_pessoas.py"], input=REMOTO, text=True, check=True)
    r = subprocess.run(["ssh", HOST, "nice python3 ~/.normaliza_pessoas.py"],
                       input=json.dumps([modo, nome, TABELAS[nome], ORDEM, list(arquivos)]), text=True)
    if r.returncode:
        sys.exit(r.returncode)


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ("converte", "aplica", "acrescenta"):
        sys.exit(__doc__)
    roda(sys.argv[1], sys.argv[2], sys.argv[3:])
