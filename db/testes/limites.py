"""Testes dos limites contra raspagem (db/limites.py + o que consulta.py faz com eles).

    python3 db/testes/limites.py

Sem catálogo, S3 nem rede: um DuckDB em memória no lugar do catálogo e o `Handler` de verdade
num servidor local. O Caddy (tokens, IP, cabeçalhos) não entra aqui: a conferência dele está em
`db/README.md`, seção "Limites contra raspagem".
"""

import http.client
import io
import json
import os
import sys
import tempfile
import threading
import traceback
from contextlib import redirect_stdout
from http.server import ThreadingHTTPServer

TMP = tempfile.mkdtemp(prefix="limites_teste_")
os.environ.update({
    "RODADO_LIMITES_DB": os.path.join(TMP, "limites.sqlite"), "RODADO_TEMP": os.path.join(TMP, "duck"),
    "RODADO_DIR_Q": os.path.join(TMP, "q"),
    "DB_TOKENS": "ana:anaanaanaanaana1234 bia:biabiabiabiabia5678,polo:pelopelopelopelo9999",
    "DB_TOKEN_LINK": "linklinklinklink4321",
})
os.makedirs(os.environ["RODADO_TEMP"])
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import duckdb  # noqa: E402
from duckdb import sqltypes  # noqa: E402

import consulta  # noqa: E402
import limites  # noqa: E402
import rodado_sql  # noqa: E402

TOKEN_ANA, TOKEN_BIA = "anaanaanaanaana1234", "biabiabiabiabia5678"
RESULTADOS = []


def teste(f):
    RESULTADOS.append(f)
    return f


# ------------------------------------------------------------------ unidades

@teste
def tokens_validos_e_recusados():
    t, rec = limites.carrega_tokens("ana:anaanaanaanaana1234, bia:curto  c:ccccccccccccccccc1 c:dddddddddddddddd2 ana:eeeeeeeeeeeeeeeee3")
    assert t == {"anaanaanaanaana1234": "ana", "ccccccccccccccccc1": "c"}, t
    assert sorted(rec) == ["ana", "bia", "c"], rec   # curto, nome repetido, nome repetido; só o nome, nunca o token


@teste
def regex_do_caddy():
    import re
    r = limites.regex_tokens({"anaanaanaanaana1234": "ana", "bia-bia_bia_bia_56": "bia"})
    assert re.fullmatch(r, "anaanaanaanaana1234") and re.fullmatch(r, "bia-bia_bia_bia_56")
    assert not re.fullmatch(r, "anaanaanaanaana12345") and not re.fullmatch(r, "") and not re.search(r, "xanaanaanaanaana1234")
    sem = limites.regex_tokens({})
    assert not re.search(sem, "") and not re.search(sem, "a") and not re.search(sem, "qualquer")


def _arvore(sql):
    con = duckdb.connect()
    con.execute("CREATE SCHEMA br_t; CREATE TABLE br_t.grande(a INT, b INT); CREATE TABLE br_t.o(a INT)")
    return json.loads(con.execute("SELECT json_serialize_sql(?)", [sql]).fetchall()[0][0])


CFG = limites.Config()


@teste
def offset_alto_e_baixo():
    assert limites.offset_alto(_arvore("SELECT * FROM br_t.grande LIMIT 10 OFFSET 200000"), 100_000) == (200000.0, None)
    assert limites.offset_alto(_arvore("SELECT * FROM br_t.grande LIMIT 10 OFFSET 100000"), 100_000) is None
    assert limites.offset_alto(_arvore("SELECT * FROM br_t.grande ORDER BY a OFFSET 5"), 100_000) is None
    assert limites.offset_alto(_arvore("SELECT * FROM br_t.grande"), 100_000) is None
    assert limites.offset_alto(_arvore("SELECT * FROM br_t.grande OFFSET 200000"), 0) is None   # 0 desliga


@teste
def offset_escondido():
    sub = "SELECT * FROM (SELECT * FROM br_t.grande ORDER BY a LIMIT 10 OFFSET 500000) x"
    assert limites.offset_alto(_arvore(sub), 100_000) == (500000.0, None)
    cte = "WITH x AS (SELECT * FROM br_t.grande LIMIT 5 OFFSET 999999) SELECT * FROM x"
    assert limites.offset_alto(_arvore(cte), 100_000) == (999999.0, None)
    assert limites.offset_alto(_arvore("SELECT * FROM br_t.grande LIMIT 5 OFFSET 2*3"), 100_000) == (None, "não literal")
    assert limites.offset_alto(_arvore("SELECT * FROM br_t.grande LIMIT 5 OFFSET 1e6"), 100_000) == (1e6, None)


@teste
def selecao_ampla_so_o_que_nao_filtra():
    amp = lambda s: limites.selecao_ampla(_arvore(s))   # noqa: E731
    assert amp("SELECT * FROM br_t.grande") == ("br_t", "grande", None)
    assert amp("FROM br_t.grande") == ("br_t", "grande", None)
    assert amp("SELECT a, b FROM br_t.grande ORDER BY a") == ("br_t", "grande", None)
    assert amp("SELECT * FROM br_t.grande LIMIT 50") == ("br_t", "grande", 50.0)
    assert amp("SELECT * FROM br_t.grande LIMIT 1 PERCENT") == ("br_t", "grande", None)
    for filtrada in ("SELECT * FROM br_t.grande WHERE a = 1", "SELECT a, count(*) FROM br_t.grande GROUP BY 1",
                     "SELECT count(*) FROM br_t.grande", "SELECT DISTINCT a FROM br_t.grande",
                     "SELECT * FROM br_t.grande JOIN br_t.o USING (a)", "SELECT * FROM (SELECT 1) x",
                     "SELECT a, b FROM br_t.grande USING SAMPLE 10", "SELECT max(a) FROM br_t.grande",
                     "SELECT * FROM br_t.grande QUALIFY row_number() OVER () < 5",
                     "SELECT * FROM br_t.grande UNION ALL SELECT * FROM br_t.grande", "DESCRIBE br_t.grande"):
        assert amp(filtrada) is None, filtrada


@teste
def raspagem_usa_o_tamanho_da_tabela():
    linhas = {"grande": 5_000_000, "media": 900_000}
    n = lambda ds, t: linhas.get(t)   # noqa: E731
    r = lambda s, pedido=10_000: limites.raspagem(_arvore(s), n, pedido, CFG)   # noqa: E731
    assert r("SELECT * FROM br_t.grande") and "5.000.000" in r("SELECT * FROM br_t.grande")[0]
    assert r("SELECT * FROM br_t.grande LIMIT 1000") is None
    assert r("SELECT * FROM br_t.grande LIMIT 5000")
    assert r("SELECT * FROM br_t.grande", pedido=1000) is None          # ?limite=1000 vale como LIMIT
    assert r("SELECT * FROM br_t.media") is None                        # abaixo de 1 mi de linhas
    assert r("SELECT * FROM br_t.desconhecida") is None
    assert r("SELECT a, count(*) FROM br_t.grande GROUP BY 1") is None
    assert r("SELECT * FROM br_t.grande LIMIT 10 OFFSET 200000")[0].startswith("OFFSET 200000")


class Relogio:
    def __init__(self, t=1_800_000_000.0):
        self.t = t

    def __call__(self):
        return self.t


@teste
def janela_por_minuto_e_simultaneas():
    rel = Relogio()
    lim = limites.Limites(limites.Config(por_minuto=3, simultaneas_ip=2, arquivo=":memory:"), relogio=rel)
    assert lim.admite("1.1.1.1") is None and lim.admite("1.1.1.1") is None
    espera, motivo = lim.admite("1.1.1.1")      # 3ª: já há 2 em curso
    assert "ao mesmo tempo" in motivo and espera == 5
    lim.libera("1.1.1.1"); lim.libera("1.1.1.1")
    assert lim.admite("1.1.1.1") is None; lim.libera("1.1.1.1")   # a 3ª do minuto
    espera, motivo = lim.admite("1.1.1.1")      # a 4ª, no mesmo instante: 3 por minuto
    assert "por minuto" in motivo and espera == 60
    assert lim.admite("2.2.2.2") is None        # outro IP segue
    rel.t += 30
    assert lim.admite("1.1.1.1")[0] == 30       # Retry-After desce com o tempo
    rel.t += 31
    assert lim.admite("1.1.1.1") is None        # a janela deslizou


@teste
def cota_sobrevive_a_reinicio_e_zera_no_dia_seguinte():
    arq = os.path.join(TMP, "cota.sqlite")
    rel = Relogio()
    a = limites.Limites(limites.Config(cota_dia=100, arquivo=arq, aviso_pct=0), relogio=rel)
    a.registra("token:ana", 70)
    b = limites.Limites(limites.Config(cota_dia=100, arquivo=arq, aviso_pct=0), relogio=rel)   # "reinício"
    assert b.restante("token:ana") == 30 and b.restante("token:bia") == 100
    assert b.restante("token:ana", isento=True) is None
    rel.t += 86_400
    assert b.restante("token:ana") == 100
    assert limites.Limites(limites.Config(cota_dia=0, arquivo=":memory:")).restante("x") is None


@teste
def aviso_uma_vez_por_chave_e_dia():
    msgs = []
    rel = Relogio()
    lim = limites.Limites(limites.Config(cota_dia=100, aviso_pct=80, aviso_429=2, por_minuto=1, arquivo=":memory:"),
                          avisar=msgs.append, relogio=rel)
    lim.registra("token:ana", 50)
    assert msgs == []
    lim.registra("token:ana", 35); lim.registra("token:ana", 10); lim.registra("token:ana", 5)
    assert len(msgs) == 1 and "token:ana" in msgs[0] and "85" in msgs[0], msgs
    lim.registra("token:bia", 90)
    assert len(msgs) == 2
    lim.admite("9.9.9.9"); lim.libera("9.9.9.9")
    for _ in range(5):
        assert lim.admite("9.9.9.9")      # 1 por minuto: todas as seguintes são recusadas
    assert len([m for m in msgs if "9.9.9.9" in m]) == 1, msgs
    rel.t += 86_400
    lim.registra("token:ana", 90)
    assert len(msgs) == 4 or len([m for m in msgs if "token:ana" in m]) == 2, msgs   # no dia seguinte, avisa de novo


@teste
def meia_noite_de_brasilia():
    # 2027-01-15 12:00 BRT = 15:00 UTC → faltam 12 h
    import datetime
    t = datetime.datetime(2027, 1, 15, 15, 0, tzinfo=datetime.timezone.utc).timestamp()
    assert limites.segundos_ate_meia_noite(t) == 12 * 3600
    assert limites.dia_de(t) == "2027-01-15"


# ------------------------------------------------------------------ o servidor de verdade

def _catalogo():
    """DuckDB em memória que faz as vezes do catálogo: duas tabelas e a _rodado_metadata."""
    base = duckdb.connect(":memory:")
    base.create_function("_mascara_cpf", rodado_sql.mascara_texto, [sqltypes.VARCHAR], sqltypes.VARCHAR,
                         side_effects=False)
    base.execute("""
        CREATE SCHEMA br_t;
        CREATE TABLE br_t.pequena AS SELECT range AS a FROM range(10);
        CREATE TABLE br_t.grande AS SELECT range AS a FROM range(300);
        CREATE TABLE _rodado_metadata(dataset VARCHAR, "table" VARCHAR, rows BIGINT, size_bytes BIGINT, source VARCHAR,
          source_name VARCHAR, description VARCHAR, source_url VARCHAR, scrape_date VARCHAR, num_files INT);
        INSERT INTO _rodado_metadata VALUES ('br_t', 'pequena', 10, 1, 'x', 's', 'd', '', '', 1),
                                            ('br_t', 'grande', 5000000, 1, 'x', 's', 'd', '', '', 1);
    """)
    return base


BASE = _catalogo()
rodado_sql.conecta = lambda *a, **k: BASE.cursor()
SERVIDOR = ThreadingHTTPServer(("127.0.0.1", 0), consulta.Handler)
SERVIDOR.daemon_threads = True
threading.Thread(target=SERVIDOR.serve_forever, daemon=True).start()
PORTA = SERVIDOR.server_address[1]


def pede(sql, caminho="/query", ip=None, token=None, cookie=None, metodo="POST"):
    cab = {}
    if ip:
        cab["X-Rodado-Ip"] = ip
    if token:
        cab["X-Rodado-Token"] = token
    if cookie:
        cab["Cookie"] = f"rodado_token={cookie}"
    c = http.client.HTTPConnection("127.0.0.1", PORTA, timeout=60)
    try:
        c.request(metodo, caminho, body=sql.encode() if metodo == "POST" else None, headers=cab)
        r = c.getresponse()
        corpo = r.read()
        return r.status, {k.lower(): v for k, v in r.getheaders()}, corpo
    finally:
        c.close()


def novo(**cfg):
    """Config e estado novos, só com os limites que o teste pede ligados."""
    base = dict(cota_dia=0, por_minuto=0, simultaneas_ip=0, offset_max=0, amplo_limite=0, aviso_pct=0, aviso_429=0,
                cota_bytes_dia=0, resposta_max_bytes=0, cota_senha_dia=0, cota_senha_bytes_dia=0, arquivo=":memory:")
    base.update(cfg)
    consulta.CFG = limites.Config(**base)
    consulta.LIMITES = limites.Limites(consulta.CFG, avisar=AVISOS.append)
    return consulta.CFG


AVISOS = []
N60 = "SELECT a FROM br_t.grande WHERE a < 60"


@teste
def sem_ip_nao_escapa_dos_limites():
    # Era a isenção do MCP de dentro do container: /mcp (atrás da mesma senha) virava consulta sem
    # limite nenhum. Agora o MCP repassa IP e token; quem chega sem IP cai num balde próprio, limitado.
    novo(cota_dia=100, por_minuto=2)
    st, cab, _c = pede(N60)
    assert st == 200 and cab["x-cota-restante"] == "40", (st, cab)
    assert pede(N60)[0] == 200
    assert pede(N60)[0] == 429                                     # 2 por minuto, também sem IP


@teste
def por_minuto_por_ip():
    novo(por_minuto=3)
    assert [pede("SELECT 1", ip="10.0.0.1")[0] for _ in range(3)] == [200] * 3
    st, cab, corpo = pede("SELECT 1", ip="10.0.0.1")
    assert st == 429 and int(cab["retry-after"]) >= 1, (st, cab)
    assert "dica" in json.loads(corpo) and "por minuto" in json.loads(corpo)["erro"]
    assert pede("SELECT 1", ip="10.0.0.2")[0] == 200       # outro IP, outra janela
    assert pede("SELECT 1", ip="10.0.0.1", token=TOKEN_ANA)[0] == 429   # o ritmo é por IP, com ou sem token
    assert pede("/", "/llm", ip="10.0.0.1", metodo="GET")[0] == 200     # /llm fora do limite


@teste
def cota_diaria_por_token_com_corte_e_429():
    novo(cota_dia=100)
    st, cab, corpo = pede(N60, ip="10.0.0.5", token=TOKEN_ANA)
    assert st == 200 and cab["x-cota-restante"] == "40" and cab["x-linhas"] == "60", (st, cab)
    st, cab, corpo = pede(N60, ip="10.0.0.5", token=TOKEN_ANA)   # só 40 de 60 cabem
    assert st == 200 and cab["x-linhas"] == "40" and cab["x-truncado"] == "1" and cab["x-cota-restante"] == "0", cab
    st, cab, corpo = pede("SELECT 1", ip="10.0.0.5", token=TOKEN_ANA)
    assert st == 429 and cab["x-cota-restante"] == "0" and 0 < int(cab["retry-after"]) <= 86_400, (st, cab)
    assert "esgotada" in json.loads(corpo)["erro"] and json.loads(corpo)["dica"]
    # a cota é do token, não do IP: a ana noutro IP continua esgotada; a bia no mesmo IP não
    assert pede("SELECT 1", ip="10.0.0.99", token=TOKEN_ANA)[0] == 429
    st, cab, _c = pede(N60, ip="10.0.0.5", token=TOKEN_BIA)
    assert st == 200 and cab["x-cota-restante"] == "40"
    # sem token a chave é o IP: dois IPs, duas cotas
    assert pede(N60, ip="10.0.0.7")[1]["x-cota-restante"] == "40"
    assert pede(N60, ip="10.0.0.8")[1]["x-cota-restante"] == "40"
    # token que não existe na lista (ou revogado) não ganha nome: cai na cota do IP
    st, cab, _c = pede(N60, ip="10.0.0.7", token="revogadorevogado1234")
    assert st == 200 and cab["x-cota-restante"] == "0", cab   # 40 - 60 cortado em 40 → 0, mesma chave do IP .7


@teste
def cookie_identifica_o_token():
    novo(cota_dia=100)
    pede(N60, ip="10.0.0.20", cookie=TOKEN_BIA)
    assert pede(N60, ip="10.0.0.21", token=TOKEN_BIA)[1]["x-cota-restante"] == "0"   # o mesmo "token:bia"


@teste
def isento_nao_gasta_cota():
    novo(cota_dia=10, isentos=frozenset({"polo"}))
    st, cab, _c = pede(N60, ip="10.0.0.30", token="pelopelopelopelo9999")
    assert st == 200 and cab["x-cota-restante"] == "ilimitada" and cab["x-linhas"] == "60"


@teste
def cota_conta_parquet_pelo_rodape():
    novo(cota_dia=1000)
    st, cab, corpo = pede(N60, "/query?formato=parquet", ip="10.0.0.40")
    assert st == 200 and corpo[:4] == b"PAR1" and cab["x-linhas"] == "60" and cab["x-cota-restante"] == "940", cab


@teste
def parquet_so_com_token_quando_ligado():
    cfg = novo(parquet_so_token=True)
    st, cab, corpo = pede(N60, "/query?formato=parquet", ip="10.0.0.50")
    assert st == 403 and json.loads(corpo)["dica"]
    assert pede(N60, "/query?formato=parquet", ip="10.0.0.50", token=TOKEN_ANA)[0] == 200
    assert pede(N60, "/query?formato=parquet")[0] == 403          # sem IP não é mais exceção
    assert pede(N60, "/query?formato=csv", ip="10.0.0.50")[0] == 200
    cfg.parquet_so_token = False
    assert pede(N60, "/query?formato=parquet", ip="10.0.0.50")[0] == 200   # desligado (padrão): como era


@teste
def offset_e_tabela_grande_recusados_pelo_query():
    novo(offset_max=100_000, amplo_limite=1000)
    st, _h, corpo = pede("SELECT * FROM br_t.grande LIMIT 10 OFFSET 200000")
    assert st == 400 and "OFFSET" in json.loads(corpo)["erro"] and json.loads(corpo)["dica"], corpo
    st, _h, corpo = pede("SELECT * FROM br_t.grande")
    assert st == 400 and "raspagem" in json.loads(corpo)["erro"], corpo
    assert pede("SELECT * FROM br_t.grande", "/query?limite=100")[0] == 200
    assert pede("SELECT * FROM br_t.grande LIMIT 10")[0] == 200
    assert pede("SELECT a % 7 AS g, count(*) FROM br_t.grande GROUP BY 1")[0] == 200
    assert pede("SELECT * FROM br_t.grande WHERE a = 3")[0] == 200
    assert pede("SELECT * FROM br_t.pequena")[0] == 200            # tabela pequena
    assert pede("DESCRIBE br_t.grande")[0] == 200
    assert pede("SELECT * FROM br_t.grande OFFSET 10 LIMIT 5")[0] == 200   # fatia rasa segue valendo
    # sem limite ligado, nada muda
    novo()
    assert pede("SELECT * FROM br_t.grande LIMIT 10 OFFSET 200000")[0] == 200


@teste
def confere_lista_o_mesmo_problema():
    novo(offset_max=100_000, amplo_limite=1000)
    st, _h, corpo = pede("SELECT * FROM br_t.grande LIMIT 10 OFFSET 200000", "/confere")
    assert st == 200 and any("OFFSET" in p for p in json.loads(corpo)["problemas"]), corpo
    st, _h, corpo = pede("SELECT a FROM br_t.grande WHERE a < 3", "/confere")
    assert st == 200 and json.loads(corpo)["problemas"] == []


@teste
def uso_legitimo_segue_funcionando():
    novo(cota_dia=1000, por_minuto=30, simultaneas_ip=2, offset_max=100_000, amplo_limite=1000)
    st, cab, corpo = pede("SELECT a FROM br_t.pequena ORDER BY a", ip="10.0.1.1")           # senha, sem token
    assert st == 200 and len(json.loads(corpo)["linhas"]) == 10 and cab["x-cota-restante"] == "990"
    st, cab, corpo = pede("SELECT a FROM br_t.pequena", "/query?formato=csv", ip="10.0.1.1")
    assert st == 200 and corpo.startswith(b"a\n") and cab["x-linhas"] == "10"
    st, cab, corpo = pede("SELECT a FROM br_t.pequena", "/query?formato=json", ip="10.0.1.1")   # o MCP via http
    assert st == 200 and len(json.loads(corpo)) == 10
    st, _h, corpo = pede("", f"/query?q={'SELECT+1'}", ip="10.0.1.1", metodo="GET")
    assert st == 200
    for rota in ("/llm", "/contexto", "/contexto?dataset=br_me_cnpj", "/exemplos?busca=desemprego", "/ping",
                 "/tabelas?busca=x"):
        st, _h, _c = pede("", rota, ip="10.0.1.1", metodo="GET")
        assert st == 200, (rota, st)
    st, _h, corpo = pede("SELECT a FROM br_t.pequena", "/confere", ip="10.0.1.1")
    assert st == 200
    st, _h, corpo = pede("", "/llm", metodo="GET")
    assert b"{cota_dia}" not in corpo and b"{por_minuto}" not in corpo and b"{offset_max}" not in corpo
    assert not any(f"{{{k}}}".encode() in corpo for k in ("cota_mb", "resposta_mb", "cota_senha"))
    assert pede("", "/ping", ip="203.0.113.9", metodo="GET")[1]["x-seu-ip"] == "203.0.113.9"


@teste
def log_traz_o_nome_e_nunca_o_token():
    novo(cota_dia=1000)
    saida = io.StringIO()
    with redirect_stdout(saida):
        pede("SELECT a FROM br_t.pequena", ip="10.0.2.2", token=TOKEN_ANA, cookie=TOKEN_BIA)
        pede("SELECT a FROM br_t.pequena", ip="10.0.2.3")
    log = saida.getvalue()
    assert "usuario=ana" in log and "ip=10.0.2.2" in log and "usuario=-" in log, log
    assert TOKEN_ANA not in log and TOKEN_BIA not in log and "SELECT" not in log


@teste
def aviso_de_cota_via_query():
    AVISOS.clear()
    novo(cota_dia=100, aviso_pct=80)
    pede(N60, ip="10.0.3.1", token=TOKEN_ANA)
    assert AVISOS == []
    pede("SELECT a FROM br_t.grande WHERE a < 30", ip="10.0.3.1", token=TOKEN_ANA)
    pede("SELECT a FROM br_t.grande WHERE a < 5", ip="10.0.3.1", token=TOKEN_ANA)
    assert len(AVISOS) == 1 and "token:ana" in AVISOS[0] and TOKEN_ANA not in AVISOS[0], AVISOS


# ------------------------------------------------------------------ rodada de 2026-11-11: bypasses

@teste
def chave_ip_agrupa_ipv6_por_64():
    assert limites.chave_ip("2001:db8:1:2::1") == limites.chave_ip("2001:db8:1:2:ffff::9") == "2001:db8:1:2::/64"
    assert limites.chave_ip("2001:db8:1:3::1") != limites.chave_ip("2001:db8:1:2::1")
    assert limites.chave_ip("10.0.0.1") == "10.0.0.1"
    assert limites.chave_ip("::ffff:10.0.0.1") == "10.0.0.1"         # IPv4 mapeado em IPv6
    assert limites.chave_ip("") == "interno" and limites.chave_ip("lixo") == "lixo"


@teste
def mesmo_64_divide_cota_e_ritmo():
    novo(cota_dia=100, por_minuto=3)
    assert pede(N60, ip="2001:db8:5:5::1")[1]["x-cota-restante"] == "40"
    st, cab, _c = pede(N60, ip="2001:db8:5:5::beef")              # outro endereço, mesma /64
    assert st == 200 and cab["x-linhas"] == "40" and cab["x-cota-restante"] == "0", cab
    assert pede("SELECT 1", ip="2001:db8:5:5::cafe")[0] == 429     # 3ª da /64 no minuto... e cota esgotada
    assert pede(N60, ip="2001:db8:5:6::1")[1]["x-cota-restante"] == "40"   # outra /64


@teste
def senha_tem_balde_comum_a_todos_os_ips():
    # trocar de IP (proxy, VPN) multiplicava a cota de quem entra com a senha compartilhada
    novo(cota_dia=1000, cota_senha_dia=100)
    assert pede(N60, ip="10.9.0.1")[1]["x-cota-restante"] == "40"
    st, cab, _c = pede(N60, ip="10.9.0.2")
    assert st == 200 and cab["x-linhas"] == "40" and cab["x-cota-restante"] == "0", cab
    st, cab, corpo = pede(N60, ip="10.9.0.3")
    assert st == 429 and "senha" in json.loads(corpo)["erro"], corpo
    st, cab, _c = pede(N60, ip="10.9.0.3", token=TOKEN_ANA)        # token pessoal tem a cota dele
    assert st == 200 and cab["x-cota-restante"] == "940", cab


EMPACOTADA = "SELECT to_json(list(a))::VARCHAR AS tudo FROM br_t.grande"


@teste
def empacotar_em_uma_linha_gasta_cota_em_bytes():
    # list()/string_agg() numa linha só levavam a tabela inteira gastando 1 linha da cota
    novo(cota_dia=1000, cota_bytes_dia=3000)
    st, cab, corpo = pede(EMPACOTADA, ip="10.8.0.1")
    assert st == 200 and cab["x-linhas"] == "1", cab
    gasto = 3000 - int(cab["x-cota-bytes-restante"])
    assert gasto >= len(corpo) - 200 and gasto > 1000, (gasto, len(corpo))
    pede(EMPACOTADA, ip="10.8.0.1")
    st, cab, corpo = pede(EMPACOTADA, ip="10.8.0.1")
    assert st == 429 and "bytes" in json.loads(corpo)["erro"], (st, corpo)


@teste
def resposta_grande_demais_recusada():
    novo(resposta_max_bytes=500)
    st, cab, corpo = pede(EMPACOTADA, ip="10.8.0.2")
    assert st == 413 and json.loads(corpo)["dica"], (st, corpo)
    st, cab, corpo = pede(EMPACOTADA, "/query?formato=parquet", ip="10.8.0.2")
    assert st == 413, (st, cab)
    assert pede("SELECT a FROM br_t.pequena", ip="10.8.0.2")[0] == 200


@teste
def parquet_gasta_bytes_descomprimidos():
    novo(cota_bytes_dia=10**9)
    st, cab, corpo = pede("SELECT repeat(a::VARCHAR || 'x', 250) AS s FROM br_t.grande", "/query?formato=parquet", ip="10.8.0.3")
    gasto = 10**9 - int(cab["x-cota-bytes-restante"])
    assert st == 200 and gasto >= 300 * 500 > len(corpo), (gasto, len(corpo))   # zstd não esconde o volume


@teste
def exporta_do_terminal_segue_funcionando_com_os_padroes():
    # o botão #exporta da página: POST /query?formato=csv&limite=1000&ciente=1 com o cookie (ou a
    # senha) — o caminho sancionado de baixar dado, que tem de caber nos limites de produção
    consulta.CFG = limites.Config(arquivo=":memory:")
    consulta.LIMITES = limites.Limites(consulta.CFG, avisar=AVISOS.append)
    for kw in ({"cookie": TOKEN_ANA}, {}):
        st, cab, corpo = pede("SELECT * FROM br_t.grande", "/query?formato=csv&limite=1000&ciente=1", ip="10.7.0.1", **kw)
        assert st == 200 and cab["x-linhas"] == "300" and corpo.startswith(b"a\n"), (kw, st, corpo[:200])
        assert int(cab["x-cota-restante"]) > 0 and int(cab["x-cota-bytes-restante"]) > 0, cab


@teste
def volume_antigo_ganha_a_coluna_de_bytes():
    # o /dados/limites.sqlite de produção tem `cota` sem `bytes`: abrir não pode derrubar o /query
    import sqlite3
    arq = os.path.join(TMP, "antigo.sqlite")
    db = sqlite3.connect(arq)
    db.execute("CREATE TABLE cota (chave TEXT, dia TEXT, linhas INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (chave, dia))")
    db.execute("INSERT INTO cota VALUES ('token:ana', ?, 70)", (limites.dia_de(__import__("time").time()),))
    db.commit(); db.close()
    lim = limites.Limites(limites.Config(cota_dia=100, cota_bytes_dia=1000, aviso_pct=0, arquivo=arq))
    limites.Limites(limites.Config(arquivo=arq))      # a segunda abertura (outro processo) não tenta de novo
    lim.registra("token:ana", 10, bytes_=10)
    assert lim.restante("token:ana") == 20 and lim.restante_bytes("token:ana") == 990


@teste
def token_de_link_tem_cota_propria():
    # o cookie que o link /q grava: nome "link", cota baixa comum a todos os visitantes, fora do
    # balde da senha e longe do token do dono
    assert limites.com_token_de_link({"a" * 16: "link", "b" * 16: "bia"}, "c" * 16) == {"b" * 16: "bia", "c" * 16: "link"}
    assert limites.com_token_de_link({}, "curto") == {} and limites.com_token_de_link({}, "") == {}
    novo(cota_dia=1000, cota_senha_dia=1000, cota_link_dia=100)
    st, cab, _c = pede(N60, ip="10.6.0.1", cookie="linklinklinklink4321")
    assert st == 200 and cab["x-cota-restante"] == "40", cab
    st, cab, _c = pede(N60, ip="10.6.0.2", cookie="linklinklinklink4321")     # outro visitante, mesmo balde
    assert st == 200 and cab["x-linhas"] == "40" and cab["x-cota-restante"] == "0", cab
    assert pede("SELECT 1", ip="10.6.0.3", cookie="linklinklinklink4321")[0] == 429
    assert pede(N60, ip="10.6.0.3")[1]["x-cota-restante"] == "940"            # a senha não foi gasta


if __name__ == "__main__":
    falhas = 0
    for f in RESULTADOS:
        ruido = io.StringIO()     # o servidor de teste loga cada requisição
        try:
            with redirect_stdout(ruido):
                f()
        except Exception:   # noqa: BLE001
            falhas += 1
            print(f"FALHOU: {f.__name__}")
            traceback.print_exc()
    SERVIDOR.shutdown()
    print(f"{len(RESULTADOS) - falhas}/{len(RESULTADOS)} ok")
    sys.exit(1 if falhas else 0)
