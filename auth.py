#!/usr/bin/env python3
"""Minimal cookie-session auth gate for DuckDB shell."""
import hmac, hashlib, json, os, secrets, subprocess, time
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import parse_qs

PASSWORD = os.environ.get('BASIC_AUTH_PASSWORD', '').encode()

_INIT_SQL = None

def _run_query(sql, json_mode=True):
    global _INIT_SQL
    if _INIT_SQL is None:
        with open('/app/ssh_init.sql') as f:
            _INIT_SQL = f.read()
    if json_mode:
        sql = '.mode json\n' + sql
    try:
        r = subprocess.run(
            ['duckdb', '-readonly', '/app/data/basedosdados.duckdb'],
            input=_INIT_SQL + '\n' + sql, capture_output=True, text=True, timeout=120
        )
        if r.stdout.strip().startswith('['):
            return r.stdout.encode()
        err = (r.stderr or r.stdout or 'unknown DuckDB error').strip()
        return json.dumps({'error': err}).encode()
    except subprocess.TimeoutExpired:
        return json.dumps({'error': 'query timed out after 120s'}).encode()
_SECRET  = secrets.token_bytes(32)

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

ThreadedHTTPServer(('127.0.0.1', 8081), H).serve_forever()
