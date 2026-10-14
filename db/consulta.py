"""Endpoint HTTP de SQL do db.rodado.xyz (para curl).

    curl -u rodado:SENHA --data-binary 'FROM br_bd_diretorios_brasil.uf' https://db.rodado.xyz/query
    curl -u rodado:SENHA 'https://db.rodado.xyz/query?formato=csv' --data-binary @consulta.sql
    curl -u rodado:SENHA -G https://db.rodado.xyz/query --data-urlencode 'q=SELECT 42'

A senha é cobrada pelo Caddy do mesmo container (finland); este servidor só escuta
em 127.0.0.1 dentro dele.
"""

import base64
import csv
import datetime
import decimal
import hashlib
import io
import json
import os
import re
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import duckdb

import rodado_sql

PAGINA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
# /llm: guia público para agentes; o modelo em llm.md recebe os números e a lista de datasets
GUIA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "llm.md")

# Link curto /q/<id>: o SQL salvo por quem tem senha fica em DIR_Q/<id>.sql, no volume.
# O id é o começo do sha256 do texto (o mesmo SQL dá sempre o mesmo link) e só cresce se
# colidir. /q/<id> é a página do terminal, que busca /q/<id>/sql e executa; o Caddy dá a
# quem abre um link que existe o mesmo acesso de quem tem o token.
DIR_Q = os.environ.get("RODADO_DIR_Q", "/dados/q")
ROTA_Q = re.compile(r"^/q/([A-Za-z0-9_-]{8,16})(/sql)?$")
_catalogo = {"em": 0.0, "json": b""}
_catalogo_trava = threading.Lock()
_guia = {"em": 0.0, "texto": b""}
_guia_trava = threading.Lock()

SQL_GUIA_RESUMO = """
SELECT count(*), count(DISTINCT dataset), coalesce(sum(size_bytes), 0), count(DISTINCT source_name)
FROM _rodado_metadata WHERE source <> 'view_only'
"""
SQL_GUIA_DATASETS = """
SELECT dataset, count(*), coalesce(sum(rows), 0), mode(source_name)
FROM _rodado_metadata WHERE source <> 'view_only'
GROUP BY 1 ORDER BY 1
"""

SQL_CATALOGO = r"""
SELECT v.schema_name AS dataset, v.view_name AS tabela, m.rows AS linhas,
       coalesce(m.description, CASE WHEN v.schema_name = 'main' AND v.view_name LIKE '\_rodado\_%' ESCAPE '\'
         THEN 'catálogo do espelho: _rodado_metadata tem uma linha por tabela (linhas, fonte, data, status, '
           || 'procedência), _rodado_datasets uma por dataset' END) AS descricao,
       m.source_name AS fonte, nullif(m.source_url, '') AS url,
       nullif(m.scrape_date, '') AS atualizado, m.num_files AS arquivos,
       -- a view lê do SSD do finland (cópia em /dados/local, ver catalogo.py) ou do bucket
       contains(v.sql, '{LOCAL}') AS ssd
FROM duckdb_views() v
LEFT JOIN _rodado_metadata m ON m.dataset = v.schema_name AND m."table" = v.view_name
WHERE NOT v.internal AND v.schema_name NOT LIKE '\_%' ESCAPE '\'
ORDER BY v.schema_name <> 'main', 1, 2  -- o catálogo (main._rodado_*) primeiro na árvore
""".replace("{LOCAL}", rodado_sql.LOCAL.replace("'", "''"))

PORTA = int(os.environ.get("RODADO_PORTA_CONSULTA", "18081"))
LIMITE_PADRAO = 10_000
LIMITE_MAXIMO = 1_000_000
N_SIMULTANEAS = int(os.environ.get("RODADO_SIMULTANEAS", "4"))
SIMULTANEAS = threading.BoundedSemaphore(N_SIMULTANEAS)

USO = """\
POST /query com o SQL no corpo (ou GET /query?q=...). Só leitura, um comando por vez.
Parâmetros: formato=json|csv|tsv|parquet (padrão json), limite=N linhas (padrão 10000, máx. 1000000).
Cabeçalhos da resposta: X-Linhas, X-Truncado, X-Segundos.
Exemplo: curl -u usuario:senha --data-binary 'DESCRIBE br_bd_diretorios_brasil.municipio' https://db.rodado.xyz/query
"""


def _milhar(n):
    return f"{int(n):,}".replace(",", ".")


def _gb(n):
    return f"{n / 1e12:.1f} TB".replace(".", ",") if n >= 1e12 else f"{n / 1e9:.0f} GB"


def _linhas(n):
    for limite, nome in ((1e9, "bi"), (1e6, "mi"), (1e3, "mil")):
        if n >= limite:
            return f"{n / limite:.1f} {nome} linhas".replace(".", ",")
    return f"{int(n)} linhas"


def _json_valor(v):
    if isinstance(v, decimal.Decimal):
        return float(v)
    if isinstance(v, (datetime.date, datetime.datetime, datetime.time)):
        return v.isoformat()
    if isinstance(v, datetime.timedelta):
        return str(v)
    if isinstance(v, (bytes, bytearray)):
        return v.hex()
    if isinstance(v, uuid.UUID):
        return str(v)
    return str(v)


class Handler(BaseHTTPRequestHandler):
    server_version = "rodado"

    def log_message(self, fmt, *args):
        # Sem o SQL no log: só método, caminho e status.
        print(f"{self.log_date_time_string()} {fmt % args}", flush=True)

    def _responde(self, status, corpo, tipo="text/plain; charset=utf-8", extra=None):
        dados = corpo.encode("utf-8") if isinstance(corpo, str) else corpo
        self.send_response(status)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(dados)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(dados)

    def _erro(self, status, msg):
        self._responde(status, json.dumps({"erro": msg}, ensure_ascii=False) + "\n",
                       "application/json; charset=utf-8")

    def _json(self, obj, status=200):
        self._responde(status, json.dumps(obj, ensure_ascii=False, default=_json_valor),
                       "application/json; charset=utf-8")

    def _catalogo(self):
        with _catalogo_trava:
            if time.time() - _catalogo["em"] > 600:
                con = rodado_sql.conecta()
                try:
                    rel = con.sql(SQL_CATALOGO)
                    cols = rel.columns
                    dados = [dict(zip(cols, l)) for l in rel.fetchall()]
                finally:
                    con.close()
                _catalogo["json"] = json.dumps(dados, ensure_ascii=False, default=_json_valor).encode()
                _catalogo["em"] = time.time()
            return _catalogo["json"]

    def _guia(self):
        with _guia_trava:
            if time.time() - _guia["em"] > 600:
                con = rodado_sql.conecta()
                try:
                    tab, ds, tamanho, fontes = con.sql(SQL_GUIA_RESUMO).fetchone()
                    datasets = con.sql(SQL_GUIA_DATASETS).fetchall()
                finally:
                    con.close()
                with open(GUIA, encoding="utf-8") as f:
                    modelo = f.read()
                valores = {
                    "resumo": f"{_milhar(tab)} tabelas · {_milhar(ds)} datasets · {_milhar(fontes)} fontes · "
                              f"{_gb(tamanho)}",
                    "gerado": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()),
                    "limite_padrao": _milhar(LIMITE_PADRAO), "limite_maximo": _milhar(LIMITE_MAXIMO),
                    "tempo": rodado_sql.TEMPO_LIMITE, "simultaneas": N_SIMULTANEAS,
                    "datasets": "\n".join(f"- `{d}` · {n} · {_linhas(l)} · {f or '?'}" for d, n, l, f in datasets),
                }
                for chave, valor in valores.items():   # format() quebraria nas chaves do SQL do guia
                    modelo = modelo.replace("{" + chave + "}", str(valor))
                _guia["texto"] = modelo.encode()
                _guia["em"] = time.time()
            return _guia["texto"]

    def _colunas(self, alvo):
        partes = alvo.split(".")
        if len(partes) != 2 or not all(p.isidentifier() for p in partes):
            return self._json({"erro": "use dataset.tabela"}, 400)
        con = rodado_sql.conecta()
        try:
            # duckdb_columns() lê os nomes e tipos guardados no catálogo quando a view foi criada;
            # DESCRIBE religaria a view e releria do S3 o rodapé de cada arquivo (4 mil no CNPJ)
            linhas = con.execute("SELECT column_name, data_type FROM duckdb_columns() "
                                 "WHERE schema_name = ? AND table_name = ? ORDER BY column_index", partes).fetchall()
            if not linhas:
                return self._json({"erro": f"tabela {alvo} não existe"}, 400)
            sql = con.execute("SELECT sql FROM duckdb_views() WHERE schema_name = ? AND view_name = ?",
                              partes).fetchone()
        except duckdb.Error as e:
            return self._json({"erro": str(e)}, 400)
        finally:
            con.close()
        # partição hive de verdade: `/chave=valor/` no caminho dos arquivos da view
        hive = set(re.findall(r"/([A-Za-z_]\w*)=[^/']+/", sql[0] if sql else ""))
        self._json([{"coluna": l[0], "tipo": l[1], "particao": l[0] in hive} for l in linhas])

    def _salva_q(self):
        tamanho = int(self.headers.get("Content-Length") or 0)
        if tamanho > 64_000:
            return self._erro(413, "SQL grande demais para link")
        sql = self.rfile.read(tamanho).decode("utf-8", errors="replace").strip()
        if not sql:
            return self._erro(400, "SQL vazio")
        try:
            con = rodado_sql.conecta()
            try:
                if len(rodado_sql.separa(con, sql)) != 1:
                    return self._erro(400, "um comando por link")
            finally:
                con.close()
        except rodado_sql.ConsultaRecusada as e:
            return self._erro(400, f"recusado: {e}")
        os.makedirs(DIR_Q, exist_ok=True)
        h = base64.urlsafe_b64encode(hashlib.sha256(sql.encode()).digest()).decode()
        for n in range(8, 17):
            caminho = os.path.join(DIR_Q, h[:n] + ".sql")
            try:
                with open(caminho, "x", encoding="utf-8") as f:   # "x": falha se já existe
                    f.write(sql)
                break
            except FileExistsError:
                with open(caminho, encoding="utf-8") as f:
                    if f.read() == sql:
                        break                                     # mesmo SQL, mesmo link
        else:
            return self._erro(500, "colisão de id")
        self._json({"id": h[:n], "url": f"/q/{h[:n]}"})

    def _q(self, ident, parte):
        caminho = os.path.join(DIR_Q, ident + ".sql")
        if not os.path.exists(caminho):
            return self._erro(404, "link não encontrado")
        if not parte:
            with open(PAGINA, "rb") as f:
                return self._responde(200, f.read(), "text/html; charset=utf-8", {"Cache-Control": "no-cache"})
        with open(caminho, encoding="utf-8") as f:
            return self._responde(200, f.read(), extra={"Cache-Control": "no-cache"})

    def do_GET(self):
        url = urlparse(self.path)
        rota = ROTA_Q.match(url.path)
        if rota:
            return self._q(rota.group(1), rota.group(2))
        if url.path == "/health":
            return self._responde(200, "ok\n")
        if url.path == "/ping":  # mede a ida e volta até o servidor Python (o /health o Caddy responde sozinho)
            return self._responde(200, "pong\n", extra={"Cache-Control": "no-store"})
        if url.path == "/":
            with open(PAGINA, "rb") as f:
                return self._responde(200, f.read(), "text/html; charset=utf-8",
                                      {"Cache-Control": "no-cache"})
        if url.path == "/catalogo.json":
            try:
                return self._responde(200, self._catalogo(), "application/json; charset=utf-8")
            except duckdb.Error as e:
                return self._json({"erro": str(e)}, 500)
        if url.path in ("/llm", "/llm.md", "/llms.txt"):
            try:
                return self._responde(200, self._guia(), "text/markdown; charset=utf-8",
                                      {"Cache-Control": "public, max-age=600"})
            except duckdb.Error as e:
                return self._json({"erro": str(e)}, 500)
        if url.path == "/colunas":
            return self._colunas((parse_qs(url.query).get("t") or [""])[0])
        if url.path.rstrip("/") != "/query":
            return self._erro(404, "use /query")
        params = parse_qs(url.query)
        sql = (params.get("q") or [""])[0]
        if not sql.strip():
            return self._responde(200, USO)
        self._executa(sql, params)

    def do_POST(self):
        url = urlparse(self.path)
        if url.path.rstrip("/") == "/q":
            return self._salva_q()
        if url.path.rstrip("/") != "/query":
            return self._erro(404, "use /query")
        params = parse_qs(url.query)
        tamanho = int(self.headers.get("Content-Length") or 0)
        if tamanho > 1_000_000:
            return self._erro(413, "SQL grande demais")
        corpo = self.rfile.read(tamanho).decode("utf-8", errors="replace")
        # curl -d 'q=...' manda formulário; --data-binary manda o SQL cru.
        if corpo.startswith("q=") and "form-urlencoded" in (self.headers.get("Content-Type") or ""):
            corpo = (parse_qs(corpo).get("q") or [""])[0]
        self._executa(corpo, params)

    def _executa(self, sql, params):
        formato = (params.get("formato") or ["json"])[0]
        if formato not in ("json", "csv", "tsv", "parquet"):
            return self._erro(400, "formato deve ser json, csv, tsv ou parquet")
        try:
            limite = min(int((params.get("limite") or [LIMITE_PADRAO])[0]), LIMITE_MAXIMO)
        except ValueError:
            return self._erro(400, "limite deve ser inteiro")

        if not SIMULTANEAS.acquire(timeout=60):
            return self._erro(429, "muitas consultas ao mesmo tempo; tente de novo")
        inicio = time.monotonic()
        try:
            con = rodado_sql.conecta()
            try:
                comandos = rodado_sql.separa(con, sql)
                if len(comandos) != 1:
                    return self._erro(400, "um comando por requisição")
                with rodado_sql.Cronometro(con) as crono:
                    try:
                        rel = con.sql(comandos[0].query)
                        colunas = rel.columns
                        if formato == "parquet":
                            # Gravado pelo servidor (não pela SQL do usuário) dentro do
                            # temp_directory, a única pasta gravável da conexão travada.
                            arq = os.path.join(rodado_sql.TEMP, f"r_{uuid.uuid4().hex}.parquet")
                            try:
                                rel.limit(limite).write_parquet(arq, compression="zstd")
                                with open(arq, "rb") as f:
                                    dados = f.read()
                            finally:
                                if os.path.exists(arq):
                                    os.remove(arq)
                            linhas = None
                        else:
                            linhas = rel.fetchmany(limite + 1)
                    except duckdb.InterruptException:
                        if crono.estourou:
                            return self._erro(504, f"tempo limite de {rodado_sql.TEMPO_LIMITE} s estourado")
                        raise
            finally:
                con.close()
        except rodado_sql.ConsultaRecusada as e:
            return self._erro(400, f"recusado: {e}")
        except duckdb.Error as e:
            return self._erro(400, str(e))
        finally:
            SIMULTANEAS.release()

        if linhas is None:
            return self._responde(200, dados, "application/vnd.apache.parquet",
                                  {"X-Segundos": f"{time.monotonic() - inicio:.3f}"})
        truncado = len(linhas) > limite
        linhas = linhas[:limite]
        extra = {
            "X-Linhas": str(len(linhas)),
            "X-Truncado": "1" if truncado else "0",
            "X-Segundos": f"{time.monotonic() - inicio:.3f}",
        }
        if formato == "json":
            corpo = json.dumps([dict(zip(colunas, l)) for l in linhas],
                               ensure_ascii=False, default=_json_valor) + "\n"
            return self._responde(200, corpo, "application/json; charset=utf-8", extra)
        saida = io.StringIO()
        w = csv.writer(saida, delimiter="\t" if formato == "tsv" else ",", lineterminator="\n")
        w.writerow(colunas)
        w.writerows(linhas)
        tipo = "text/tab-separated-values" if formato == "tsv" else "text/csv"
        self._responde(200, saida.getvalue(), f"{tipo}; charset=utf-8", extra)


if __name__ == "__main__":
    ThreadingHTTPServer.daemon_threads = True
    srv = ThreadingHTTPServer(("127.0.0.1", PORTA), Handler)
    print(f"escutando em 127.0.0.1:{PORTA}", flush=True)
    srv.serve_forever()
