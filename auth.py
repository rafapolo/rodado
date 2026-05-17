#!/usr/bin/env python3
"""Minimal cookie-session auth gate for DuckDB shell."""
import decimal, datetime, duckdb, hmac, hashlib, json, os, secrets, threading, time
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import parse_qs

PASSWORD = os.environ.get('BASIC_AUTH_PASSWORD', '').encode()

_con  = None
_lock = threading.Lock()

def _init_db():
    global _con
    endpoint = os.environ.get('HETZNER_S3_ENDPOINT', '').removeprefix('https://').removeprefix('http://')
    _con = duckdb.connect(':memory:')
    _con.execute("INSTALL httpfs; LOAD httpfs;")
    _con.execute(f"""
        SET s3_endpoint='{endpoint}';
        SET s3_access_key_id='{os.environ.get("AWS_ACCESS_KEY_ID", "")}';
        SET s3_secret_access_key='{os.environ.get("AWS_SECRET_ACCESS_KEY", "")}';
        SET s3_region='{os.environ.get("BUCKET_REGION", "")}';
        SET s3_url_style='path';
        SET enable_object_cache=true;
        SET threads=4;
        SET memory_limit='6GB';
        SET preserve_insertion_order=false;
        SET http_keep_alive=true;
        SET http_retries=3;
        SET http_retry_wait_ms=10;
    """)
    _con.execute("ATTACH '/app/data/basedosdados.duckdb' AS basedosdados (READ_ONLY)")
    threading.Thread(target=_warm_cache, daemon=True).start()

def _warm_cache():
    hot_tables = [
        # TSE elections — most queried
        "br_tse_eleicoes.candidatos",
        "br_tse_eleicoes.despesas_candidato",
        "br_tse_eleicoes.resultados_candidato",
        "br_tse_eleicoes.receitas_candidato",
        "br_tse_eleicoes.bens_candidato",
        "br_tse_eleicoes.resultados_candidato_municipio",
        # CNPJ company registry
        "br_me_cnpj.empresas",
        "br_me_cnpj.socios",
        "br_me_cnpj.estabelecimentos",
        "br_me_cnpj.simples",
        # CGU procurement & contracts
        "br_cgu_licitacao_contrato.licitacao_item",
        "br_cgu_licitacao_contrato.contrato_item",
        "br_cgu_licitacao_contrato.licitacao",
        # CGU social benefits
        "br_cgu_beneficios_cidadao.novo_bolsa_familia",
        "br_cgu_beneficios_cidadao.bolsa_familia_pagamento",
        # CGU federal servants
        "br_cgu_servidores_executivo_federal.cadastro_servidores",
        "br_cgu_servidores_executivo_federal.remuneracao",
        # Câmara federal
        "br_camara_dados_abertos.deputado",
        "br_camara_dados_abertos.despesa",
        "br_camara_dados_abertos.votacao_parlamentar",
        # Reference directories
        "br_bd_diretorios_brasil.municipio",
        "br_bd_diretorios_brasil.cnae_2",
        # IBGE
        "br_ibge_censo_2022.municipio",
        "br_ibge_populacao.municipio",
        # Employment
        "br_me_caged.microdados_movimentacao",
        "br_me_rais.microdados_vinculos",
        # Education
        "br_inep_enem.microdados",
    ]
    for t in hot_tables:
        try:
            with _lock:
                _con.execute(f"FROM basedosdados.{t} LIMIT 1")
        except Exception:
            pass

def _json_default(obj):
    if isinstance(obj, decimal.Decimal): return float(obj)
    if isinstance(obj, (datetime.date, datetime.datetime)): return obj.isoformat()
    return str(obj)

def _run_query(sql, json_mode=True):
    with _lock:
        try:
            rel = _con.execute(sql)
            cols = [d[0] for d in rel.description]
            rows = [{cols[i]: row[i] for i in range(len(cols))} for row in rel.fetchall()]
            return json.dumps(rows, default=_json_default).encode()
        except Exception as e:
            return json.dumps({'error': str(e)}).encode()

_SECRET = secrets.token_bytes(32)

def _make_token():
    day = str(int(time.time()) // 86400)
    return hmac.new(_SECRET, day.encode(), hashlib.sha256).hexdigest()

def _valid(token):
    if not token:
        return False
    for delta in (0, 1):
        day = str(int(time.time()) // 86400 - delta)
        expected = hmac.new(_SECRET, day.encode(), hashlib.sha256).hexdigest()
        if hmac.compare_digest(token, expected):
            return True
    return False

LOGIN_HTML = """<!DOCTYPE html>
<html><head><title>DB Shell</title><style>
body{display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;background:#0f1117;font-family:sans-serif}
form{background:#1a1d27;padding:2rem;border-radius:8px;display:flex;flex-direction:column;gap:1rem;min-width:280px}
h2{color:#fff;margin:0}
input{padding:.6rem;border-radius:4px;border:1px solid #333;background:#0f1117;color:#fff;font-size:1rem}
button{padding:.6rem;border-radius:4px;border:none;background:#f4c543;color:#000;font-size:1rem;cursor:pointer;font-weight:600}
</style></head>
<body><form method="POST" action="/login">
  <h2>DB Shell</h2>
  <input type="password" name="password" placeholder="Password" autofocus>
  <button type="submit">Enter</button>
</form></body></html>""".encode()

class H(BaseHTTPRequestHandler):
    def _cookie(self):
        for part in self.headers.get('Cookie', '').split(';'):
            part = part.strip()
            if part.startswith('ddb_auth='):
                return part[9:]
        return ''

    def do_GET(self):
        if self.path == '/auth':
            if _valid(self._cookie()):
                self._resp(200)
            else:
                self.send_response(302)
                self.send_header('Location', '/login')
                self.end_headers()
        elif self.path.startswith('/query'):
            from urllib.parse import urlparse, parse_qs
            pwd = self.headers.get('X-Password', '').encode()
            if not hmac.compare_digest(pwd, PASSWORD):
                self._resp(401, b'Unauthorized\n')
                return
            qs = parse_qs(urlparse(self.path).query)
            sql = qs.get('q', [''])[0]
            if not sql:
                self._resp(400, b'missing ?q=\n')
                return
            self._resp(200, _run_query(sql), 'application/json')
        else:
            self._resp(200, LOGIN_HTML, 'text/html; charset=utf-8')

    def do_POST(self):
        if self.path == '/query':
            pwd = self.headers.get('X-Password', '').encode()
            if not hmac.compare_digest(pwd, PASSWORD):
                self._resp(401, b'Unauthorized\n')
                return
            sql = self.rfile.read(int(self.headers.get('Content-Length', 0))).decode(errors='replace')
            self._resp(200, _run_query(sql), 'application/json')
            return
        body = self.rfile.read(int(self.headers.get('Content-Length', 0))).decode(errors='replace')
        pwd  = parse_qs(body).get('password', [''])[0].encode()
        if hmac.compare_digest(pwd, PASSWORD):
            self.send_response(302)
            self.send_header('Set-Cookie', f'ddb_auth={_make_token()}; Path=/; HttpOnly; SameSite=Strict')
            self.send_header('Location', '/')
            self.end_headers()
        else:
            self._resp(200, LOGIN_HTML, 'text/html; charset=utf-8')

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def _resp(self, code, body=b'', ct='text/plain'):
        self.send_response(code)
        if body:
            self.send_header('Content-Type', ct)
            self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def log_message(self, *_):
        pass

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

_init_db()
ThreadedHTTPServer(('127.0.0.1', 8081), H).serve_forever()
