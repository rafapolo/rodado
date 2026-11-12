"""CPF mascarado na própria view para quem consulta sem token pessoal (catalogo.monta_anonimo).

    python3 db/testes/cpf_anonimo.py

Sem rede nem bucket: parquet local, um catálogo inteiro e um anônimo montados pelo código de verdade
(`catalogo.monta_anonimo`), o `rodado_sql.conecta` de verdade (instância travada, allowed_directories,
sem monkeypatch) e o `Handler` de verdade num servidor local. Confere o desenho de 2026-11-12:
filtrar ou juntar por CPF inteiro nunca casa no anônimo (nem com os 1.000 candidatos que a máscara
deixa), juntar e contar pelo mascarado funciona, o token pessoal enxerga o CPF inteiro, e o anônimo
não alcança o catálogo inteiro nem os parquet por outro caminho.
"""

import http.client
import json
import os
import subprocess
import sys
import tempfile
import threading
import traceback
from http.server import ThreadingHTTPServer

TMP = tempfile.mkdtemp(prefix="cpf_anonimo_")
RAIZ = os.path.join(TMP, "bucket") + "/"
CHEIO = os.path.join(TMP, "catalogo.duckdb")
ANON = os.path.join(TMP, "catalogo_anon.duckdb")
os.environ.update({
    "RODADO_DB": CHEIO, "RODADO_DB_ANON": ANON, "RODADO_RAIZ": RAIZ, "RODADO_LOCAL": os.path.join(TMP, "local") + "/",
    "RODADO_TEMP": os.path.join(TMP, "duck"), "RODADO_LIMITES_DB": os.path.join(TMP, "l.sqlite"),
    "RODADO_DIR_Q": os.path.join(TMP, "q"), "S3_KEY": "k", "S3_SECRET": "s", "RODADO_CA_BUNDLE": "/etc/hosts",
    "DB_TOKENS": "ana:anaanaanaanaana1234", "DB_TOKEN_LINK": "linklinklinklink4321",
    "RODADO_COTA_DIA": "0", "RODADO_COTA_BYTES_DIA": "0", "RODADO_RESPOSTA_MAX_BYTES": "0", "RODADO_COTA_SENHA_DIA": "0",
    "RODADO_COTA_SENHA_BYTES_DIA": "0", "RODADO_POR_MINUTO": "0", "RODADO_SIMULTANEAS_IP": "0", "RODADO_OFFSET_MAX": "0",
    "RODADO_AMPLO_LIMITE": "0", "RODADO_AVISO_PCT": "0", "RODADO_AVISO_429": "0",
})
os.makedirs(os.environ["RODADO_TEMP"])
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import duckdb  # noqa: E402

import catalogo  # noqa: E402
import consulta  # noqa: E402
import rodado_sql  # noqa: E402

TOKEN_ANA = "anaanaanaanaana1234"
RESULTADOS = []


def teste(f):
    RESULTADOS.append(f)
    return f


def verificadores(d9: str) -> str:
    d = [int(c) for c in d9]
    for n in (9, 10):
        d.append(sum(d[i] * (n + 1 - i) for i in range(n)) * 10 % 11 % 10)
    return "".join(map(str, d))


# três pessoas; os dígitos 4 a 9 são o que a máscara deixa ver
ANA = verificadores("529982247")      # 52998224725
BIA = verificadores("111444777")
CAIO = verificadores("123456789")


def m(c):
    """A máscara esperada: dígitos 4 a 9 do CPF de 11 casas (zeros à esquerda refeitos)."""
    c = c.zfill(11)
    return f"***.{c[3:6]}.{c[6:9]}-**"


MASC = {c: m(c) for c in (ANA, BIA, CAIO)}


def prepara():
    con = duckdb.connect(":memory:")

    def grava(tab, sql, ano=2020):
        pasta = os.path.join(RAIZ, "br_t", tab, f"ano={ano}")
        os.makedirs(pasta, exist_ok=True)
        con.execute(f"COPY ({sql}) TO '{pasta}/p.parquet' (FORMAT parquet)")

    grava("pessoa", f"""SELECT * FROM (VALUES
        ('{ANA}', '{ANA}', 'ANA', '{ANA}', 111, 'a'), ('{BIA}', '{BIA[:3]}.{BIA[3:6]}.{BIA[6:9]}-{BIA[9:]}', 'BIA', '123456', 222, 'b'),
        ('{CAIO}', '12345678000190', 'CAIO', '{MASC[CAIO]}', 333, 'c'), (NULL, NULL, 'DORA', NULL, 444, 'd'),
        ('{ANA[:10]}', '{ANA[1:]}', 'EDU', 'ABC', 555, 'e'))
        t(cpf, cpf_cnpj, nome, documento_credor, valor, ordem)""")
    # CPF numérico, lista de CPFs e um id para o join por chave
    grava("beneficio", f"""SELECT CAST('{ANA}' AS BIGINT) AS cpf_beneficiario, ['{ANA}', '{BIA}'] AS cpf_filhos,
        10.5 AS valor, 1 AS id_pessoa""")
    grava("sem_cpf", "SELECT 1 AS a, 'x' AS nome")
    grava("composta", f"SELECT 7 AS id, '{ANA}' AS cpf_titular")
    cheio = duckdb.connect(CHEIO)
    cheio.execute("CREATE SCHEMA br_t")
    for tab in ("pessoa", "beneficio", "sem_cpf", "composta"):
        cheio.execute(f"CREATE VIEW br_t.{tab} AS SELECT * FROM read_parquet('{RAIZ}br_t/{tab}/*/p.parquet', "
                      "hive_partitioning = CAST('t' AS BOOLEAN), union_by_name = CAST('t' AS BOOLEAN))")
    # view que cita outra (como pe_de_meia): lê o mascarado do irmão, o que a máscara idempotente aguenta
    cheio.execute("CREATE VIEW br_t.junta AS SELECT p.nome, b.valor, b.cpf_beneficiario FROM br_t.pessoa p "
                  "JOIN br_t.beneficio b ON p.ordem = 'a' AND b.id_pessoa = 1")
    # lista de colunas no cabeçalho: não dá para reescrever com segurança, então fica fora do anônimo
    cheio.execute("CREATE VIEW br_t.renomeada(a, cpf) AS SELECT a, nome FROM br_t.sem_cpf")
    cheio.execute("CREATE TABLE _rodado_metadata(dataset VARCHAR, \"table\" VARCHAR, rows BIGINT, size_bytes BIGINT, "
                  "source VARCHAR, source_name VARCHAR, description VARCHAR, source_url VARCHAR, scrape_date VARCHAR, "
                  "num_files INT)")
    cheio.close()
    fontes = {"x": "1"}
    novo, reg = catalogo.monta_anonimo(CHEIO, fontes)
    catalogo.publica_anonimo(novo, reg)
    return reg


REG = prepara()
SERVIDOR = ThreadingHTTPServer(("127.0.0.1", 0), consulta.Handler)
SERVIDOR.daemon_threads = True
threading.Thread(target=SERVIDOR.serve_forever, daemon=True).start()
PORTA = SERVIDOR.server_address[1]


def pede(sql, token=None, cookie=None, fmt="json"):
    cab = {"X-Rodado-Ip": "10.0.0.1"}
    if token:
        cab["X-Rodado-Token"] = token
    if cookie:
        cab["Cookie"] = f"rodado_token={cookie}"
    c = http.client.HTTPConnection("127.0.0.1", PORTA, timeout=120)
    try:
        c.request("POST", f"/query?formato={fmt}&ciente=1", body=sql.encode(), headers=cab)
        r = c.getresponse()
        corpo = r.read().decode()
        return r.status, (json.loads(corpo) if fmt == "json" and corpo.strip() else corpo)
    finally:
        c.close()


def valor(sql, **k):
    st, r = pede(sql, **k)
    assert st == 200, (st, r)
    return list(r[0].values())[0]


def candidatos(c):
    """Os 1.000 CPFs que a máscara `***.DDD.DDD-**` deixa: três primeiros dígitos livres, verificadores válidos."""
    return [verificadores(f"{i:03d}{c[3:9]}") for i in range(1000)]


# ------------------------------------------------------------------ o desenho

@teste
def anonimo_nao_casa_cpf_completo():
    assert valor(f"SELECT count(*) FROM br_t.pessoa WHERE cpf = '{ANA}'") == 0
    assert valor(f"SELECT count(*) FROM br_t.pessoa WHERE nome = 'ANA' AND cpf = '{ANA}'") == 0
    assert valor(f"SELECT count(*) FROM br_t.pessoa WHERE cpf = '{MASC[ANA]}'") == 1     # o mascarado casa
    assert valor(f"SELECT count(*) FROM br_t.pessoa WHERE cpf LIKE '{ANA[:3]}%'") == 0
    assert valor(f"SELECT count(*) FROM br_t.pessoa WHERE cpf_cnpj = '{ANA}'") == 0


@teste
def anonimo_nao_casa_os_mil_candidatos():
    lista = ", ".join(f"'{c}'" for c in candidatos(ANA))
    assert ANA in candidatos(ANA)
    assert valor(f"SELECT count(*) FROM br_t.pessoa WHERE nome = 'ANA' AND cpf IN ({lista})") == 0
    assert valor(f"SELECT count(*) FROM br_t.pessoa WHERE cpf IN ({lista})") == 0
    assert valor(f"SELECT count(*) FROM br_t.pessoa WHERE cpf = ANY([{lista}])") == 0
    # nem em coluna mista, de documento, de número ou dentro de lista
    assert valor(f"SELECT count(*) FROM br_t.pessoa WHERE cpf_cnpj IN ({lista}) OR documento_credor IN ({lista})") == 0
    assert valor(f"SELECT count(*) FROM br_t.beneficio WHERE cpf_beneficiario IN ({lista})") == 0
    assert valor(f"SELECT count(*) FROM br_t.beneficio WHERE list_has_any(cpf_filhos, [{lista}])") == 0


@teste
def anonimo_conta_distintos_e_junta_pelo_mascarado():
    assert valor("SELECT count(DISTINCT cpf) FROM br_t.pessoa") == 4                      # ANA, BIA, CAIO, EDU (10 dígitos)
    assert valor("SELECT count(*) FROM br_t.pessoa p JOIN br_t.beneficio b ON p.cpf = b.cpf_beneficiario") == 1
    assert valor("SELECT count(*) FROM br_t.pessoa p JOIN br_t.beneficio b "
                 "ON p.cpf_cnpj = b.cpf_beneficiario") == 2                              # coluna mista; EDU colide (6 dígitos iguais)
    assert valor("SELECT count(*) FROM br_t.pessoa WHERE cpf IN (SELECT cpf_beneficiario FROM br_t.beneficio)") == 1
    st, r = pede("SELECT nome, cpf, cpf_cnpj, documento_credor FROM br_t.pessoa ORDER BY ordem")
    assert st == 200 and r == [
        {"nome": "ANA", "cpf": MASC[ANA], "cpf_cnpj": MASC[ANA], "documento_credor": MASC[ANA]},
        {"nome": "BIA", "cpf": MASC[BIA], "cpf_cnpj": MASC[BIA], "documento_credor": "123456"},   # 6 dígitos: outro código
        {"nome": "CAIO", "cpf": MASC[CAIO], "cpf_cnpj": "12345678000190", "documento_credor": MASC[CAIO]},  # CNPJ inteiro
        {"nome": "DORA", "cpf": None, "cpf_cnpj": None, "documento_credor": None},
        {"nome": "EDU", "cpf": m(ANA[:10]), "cpf_cnpj": m(ANA[1:]), "documento_credor": "ABC"},   # zeros refeitos
    ], r


@teste
def anonimo_so_ve_asteriscos_no_comeco():
    con = rodado_sql.conecta()
    try:
        assert con.execute("SELECT DISTINCT substr(cpf, 1, 3) FROM br_t.pessoa WHERE cpf IS NOT NULL").fetchall() == [("***",)]
        assert con.execute("SELECT count(*) FROM br_t.pessoa WHERE substr(cpf, 1, 1) <> '*'").fetchall() == [(0,)]
        assert con.execute("SELECT count(*) FROM br_t.pessoa WHERE length(cpf) <> 14").fetchall() == [(0,)]
    finally:
        con.close()
    # o oráculo de dígito a dígito também morre
    assert valor("SELECT count(*) FROM br_t.pessoa WHERE substr(cpf, 1, 1) = '5'") == 0
    assert valor("SELECT count(*) FROM br_t.pessoa WHERE substr(cpf, 1, 3) <> '***'") == 0


@teste
def anonimo_tipos_mudam_para_texto_e_lista():
    con = rodado_sql.conecta()
    try:
        assert con.execute("SELECT cpf_beneficiario, cpf_filhos FROM br_t.beneficio").fetchall() == [
            (MASC[ANA], [MASC[ANA], MASC[BIA]])]
        tipos = dict(con.execute("SELECT column_name, data_type FROM duckdb_columns() WHERE table_name = 'beneficio'").fetchall())
        assert tipos["cpf_beneficiario"] == "VARCHAR" and tipos["cpf_filhos"] == "VARCHAR[]", tipos
        # a view que cita outras lê o mascarado do irmão: idempotente, nunca lixo
        assert con.execute("SELECT cpf_beneficiario FROM br_t.junta").fetchall() == [(MASC[ANA],)]
        assert con.execute("SELECT cpf_titular FROM br_t.composta").fetchall() == [(MASC[ANA],)]
        assert con.execute("SELECT a, nome FROM br_t.sem_cpf").fetchall() == [(1, "x")]
    finally:
        con.close()


@teste
def anonimo_fica_sem_a_view_que_nao_da_para_reescrever():
    st, r = pede("SELECT * FROM br_t.renomeada")
    assert st == 400, (st, r)
    assert "renomeada" in json.dumps(r)
    st, r = pede("SELECT view_name FROM duckdb_views() WHERE schema_name = 'br_t' ORDER BY 1")
    assert st == 200 and "renomeada" not in {x["view_name"] for x in r}, r


@teste
def token_pessoal_ve_e_filtra_o_cpf_inteiro():
    lista = ", ".join(f"'{c}'" for c in candidatos(ANA))
    assert valor(f"SELECT count(*) FROM br_t.pessoa WHERE cpf = '{ANA}'", token=TOKEN_ANA) == 1
    assert valor(f"SELECT count(*) FROM br_t.pessoa WHERE nome = 'ANA' AND cpf IN ({lista})", token=TOKEN_ANA) == 1
    assert valor(f"SELECT count(*) FROM br_t.pessoa WHERE cpf = '{ANA}'", cookie=TOKEN_ANA) == 1
    assert valor(f"SELECT count(*) FROM br_t.beneficio WHERE cpf_beneficiario = {ANA}", token=TOKEN_ANA) == 1   # BIGINT
    assert valor("SELECT count(DISTINCT cpf) FROM br_t.pessoa", token=TOKEN_ANA) == 4
    # a máscara de saída segue valendo para todos
    st, r = pede("SELECT cpf FROM br_t.pessoa WHERE nome = 'ANA'", token=TOKEN_ANA)
    assert r == [{"cpf": f"***{ANA[3:9]}**"}], r        # a máscara de saída de sempre (CPF cru: ***982247**)
    assert ANA not in json.dumps(r)


@teste
def senha_token_de_link_e_dono_legado_leem_o_anonimo():
    lista = f"'{ANA}'"
    for kw in ({"token": "linklinklinklink4321"}, {"cookie": "linklinklinklink4321"}, {"token": "tokenqualquerqueexiste1"}):
        assert valor(f"SELECT count(*) FROM br_t.pessoa WHERE cpf IN ({lista})", **kw) == 0, kw


@teste
def anonimo_nao_alcanca_o_catalogo_inteiro_nem_os_parquet():
    con = rodado_sql.conecta()
    try:
        bancos = dict(con.execute("SELECT database_name, path FROM duckdb_databases() WHERE NOT internal").fetchall())
        assert os.path.realpath(bancos["catalogo"]) == os.path.realpath(ANON), bancos
        assert all(not p or os.path.realpath(p) != os.path.realpath(CHEIO) for p in bancos.values()), bancos
        assert con.execute("SELECT current_setting('enable_external_access')").fetchall() == [(False,)]
    finally:
        con.close()
    parquet = os.path.join(RAIZ, "br_t", "pessoa", "ano=2020", "p.parquet")
    recusadas = [
        f"SELECT count(*) FROM read_parquet('{parquet}')",                     # o caminho que duckdb_views() mostra
        f"SELECT * FROM '{parquet}'",
        f"SELECT * FROM read_blob('{CHEIO}')",
        f"SELECT * FROM read_text('{CHEIO}')",
        f"SELECT * FROM parquet_scan('{parquet}')",
        f"SELECT * FROM glob('{RAIZ}*/*')",
        f"SELECT * FROM query('SELECT * FROM read_parquet(''{parquet}'')')",
        f"ATTACH '{CHEIO}' AS cheio",
        f"ATTACH '{CHEIO}' AS cheio (READ_ONLY); SELECT * FROM cheio.br_t.pessoa",
        "SELECT * FROM cheio.br_t.pessoa",
        "SET enable_external_access = true",
        "SET lock_configuration = false",
        "USE memory",
    ]
    for sql in recusadas:
        st, r = pede(sql)
        assert st == 400, (sql, st, r)
        assert ANA not in json.dumps(r), sql
    # o mesmo caminho do parquet e o inteiro também ficam fora para o token pessoal (só as views)
    st, r = pede(f"SELECT count(*) FROM read_parquet('{parquet}')", token=TOKEN_ANA)
    assert st == 400, (st, r)
    # DESCRIBE/SUMMARIZE/SHOW passam pela view mascarada
    st, r = pede("SUMMARIZE br_t.pessoa")
    assert st == 200 and ANA not in json.dumps(r), (st, r)


@teste
def sem_o_arquivo_anonimo_nao_cai_no_inteiro():
    os.rename(ANON, ANON + ".fora")
    try:
        st, r = pede("SELECT 1")
        assert st == 400 and "montado" in json.dumps(r), (st, r)
        # e a instância pessoal segue de pé, só para token pessoal
        assert valor("SELECT count(*) FROM br_t.pessoa", token=TOKEN_ANA) == 5
    finally:
        os.rename(ANON + ".fora", ANON)
    assert valor("SELECT count(*) FROM br_t.pessoa") == 5


@teste
def montagem_incremental_nao_refaz_o_que_nao_mudou():
    novo, reg = catalogo.monta_anonimo(CHEIO, {"x": "1"})
    assert reg["views"] == REG["views"], (reg["views"], REG["views"])
    catalogo.publica_anonimo(novo, reg)
    assert catalogo.anonimo_em_dia() is False       # FONTES do teste não existe: a marca é a do arquivo real
    assert valor(f"SELECT count(*) FROM br_t.pessoa WHERE cpf = '{ANA}'") == 0
    # view nova com CPF entra mascarada; view que sumiu sai
    import gc
    rodado_sql._instancia[True] = {"con": None, "arquivo": None}    # solta o arquivo inteiro para o teste editá-lo
    gc.collect()
    c = duckdb.connect(CHEIO)
    c.execute(f"CREATE VIEW br_t.nova AS SELECT '{ANA}' AS cpf_x, 1 AS n")
    c.execute("DROP VIEW br_t.junta")
    c.close()
    novo, reg = catalogo.monta_anonimo(CHEIO, {"x": "2"})
    catalogo.publica_anonimo(novo, reg)
    assert valor("SELECT cpf_x FROM br_t.nova") == MASC[ANA]
    assert pede("SELECT * FROM br_t.junta")[0] == 400


@teste
def aviso_quando_o_anonimo_cita_cpf_inteiro():
    st, r = pede(f"SELECT count(*) AS n FROM br_t.pessoa WHERE cpf = '{ANA}'", fmt="")
    assert st == 200
    corpo = json.loads(r)
    assert corpo["linhas"] == [{"n": 0}] and any("mascarada" in a for a in corpo["avisos"]), corpo
    st, r = pede(f"SELECT count(*) AS n FROM br_t.pessoa WHERE cpf = '{ANA}'", fmt="", token=TOKEN_ANA)
    assert not any("mascarada" in a for a in json.loads(r)["avisos"])


@teste
def terminal_so_abre_o_catalogo_inteiro_com_o_cabecalho_do_caddy():
    cod = "import terminal; print(terminal.PESSOAL)"
    base = {**os.environ}
    base.pop("TTYD_USER", None)
    saidas = {}
    for user in (None, "anonimo", "pessoal", "PESSOAL", "ana"):
        env = dict(base)
        if user:
            env["TTYD_USER"] = user
        saidas[user] = subprocess.run([sys.executable, "-c", cod], cwd=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."),
                                      env=env, capture_output=True, text=True).stdout.strip().splitlines()[-1:]
    assert saidas == {None: ["False"], "anonimo": ["False"], "pessoal": ["True"], "PESSOAL": ["False"], "ana": ["False"]}, saidas


def main():
    falhas = 0
    for f in RESULTADOS:
        try:
            f()
        except Exception:   # noqa: BLE001
            falhas += 1
            print(f"FALHOU {f.__name__}")
            traceback.print_exc()
    print(f"{len(RESULTADOS) - falhas}/{len(RESULTADOS)} ok")
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
