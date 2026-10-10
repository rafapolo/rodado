"""Endpoint HTTP de SQL do db.rodado.xyz (para curl).

    curl -u rodado:SENHA --data-binary 'FROM br_bd_diretorios_brasil.uf' https://db.rodado.xyz/query
    curl -u rodado:SENHA 'https://db.rodado.xyz/query?formato=csv' --data-binary @consulta.sql
    curl -u rodado:SENHA -G https://db.rodado.xyz/query --data-urlencode 'q=SELECT 42'

A senha é cobrada pelo proxy no finland; este servidor só escuta em 127.0.0.1
do beelink e chega lá pelo túnel SSH.
"""

import csv
import datetime
import decimal
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
_catalogo = {"em": 0.0, "json": b""}
_catalogo_trava = threading.Lock()

SQL_CATALOGO = r"""
SELECT v.schema_name AS dataset, v.view_name AS tabela, m.rows AS linhas,
       m.description AS descricao, m.source_name AS fonte, nullif(m.source_url, '') AS url,
       nullif(m.scrape_date, '') AS atualizado, m.num_files AS arquivos
FROM duckdb_views() v
LEFT JOIN _rodado_metadata m ON m.dataset = v.schema_name AND m."table" = v.view_name
WHERE NOT v.internal AND v.schema_name NOT LIKE '\_%' ESCAPE '\'
ORDER BY 1, 2
"""

PORTA = int(os.environ.get("RODADO_PORTA_CONSULTA", "18081"))
LIMITE_PADRAO = 10_000
LIMITE_MAXIMO = 1_000_000
SIMULTANEAS = threading.BoundedSemaphore(int(os.environ.get("RODADO_SIMULTANEAS", "4")))

USO = """\
POST /query com o SQL no corpo (ou GET /query?q=...). Só leitura, um comando por vez.
Parâmetros: formato=json|csv|tsv|parquet (padrão json), limite=N linhas (padrão 10000, máx. 1000000).
Cabeçalhos da resposta: X-Linhas, X-Truncado, X-Segundos.
Exemplo: curl -u usuario:senha --data-binary 'DESCRIBE br_bd_diretorios_brasil.municipio' https://db.rodado.xyz/query
"""


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

    def _colunas(self, alvo):
        partes = alvo.split(".")
        if len(partes) != 2 or not all(p.isidentifier() for p in partes):
            return self._json({"erro": "use dataset.tabela"}, 400)
        con = rodado_sql.conecta()
        try:
            linhas = con.sql(f'DESCRIBE "{partes[0]}"."{partes[1]}"').fetchall()
            sql = con.execute("SELECT sql FROM duckdb_views() WHERE schema_name = ? AND view_name = ?",
                              partes).fetchone()
        except duckdb.Error as e:
            return self._json({"erro": str(e)}, 400)
        finally:
            con.close()
        # partição hive de verdade: `/chave=valor/` no caminho dos arquivos da view
        hive = set(re.findall(r"/([A-Za-z_]\w*)=[^/']+/", sql[0] if sql else ""))
        self._json([{"coluna": l[0], "tipo": l[1], "particao": l[0] in hive} for l in linhas])

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/health":
            return self._responde(200, "ok\n")
        if url.path == "/ping":  # mede a ida e volta até o beelink (o /health o proxy responde sozinho)
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
                            # Gravado pelo servidor (não pela SQL do usuário) dentro de
                            # ~/duckdb_tmp, a única pasta gravável da conexão travada.
                            arq = os.path.join(rodado_sql.HOME, "duckdb_tmp", "web", f"r_{uuid.uuid4().hex}.parquet")
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
