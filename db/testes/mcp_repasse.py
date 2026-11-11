"""O MCP de /mcp repassa ao /query quem pediu (IP e token postos pelo Caddy).

    python3 db/testes/mcp_repasse.py

Sobe um /query falso que só anota os cabeçalhos, o mcp_server.py de verdade em HTTP
(MCP_HTTP_BEHIND_AUTH=1, como no container) e chama `run_sql` com os cabeçalhos que o Caddy
poria. Até 2026-11-11 a chamada chegava ao /query sem X-Rodado-Ip e ficava fora de todo limite.
"""

import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

RAIZ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
VISTOS = []


class Falso(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length") or 0))
        VISTOS.append({k.lower(): v for k, v in self.headers.items()})
        corpo = b'[{"x": 1}]'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)


def porta_livre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def chama(porta, cabecalhos):
    corpo = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                        "params": {"name": "run_sql", "arguments": {"sql": "SELECT 1 AS x"}}}).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{porta}/mcp", data=corpo, headers={
        "Content-Type": "application/json", "Accept": "application/json, text/event-stream", **cabecalhos})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def main():
    falso = ThreadingHTTPServer(("127.0.0.1", 0), Falso)
    threading.Thread(target=falso.serve_forever, daemon=True).start()
    porta = porta_livre()
    env = {**os.environ, "MCP_TRANSPORT": "http", "MCP_BACKEND": "http", "MCP_HTTP_BEHIND_AUTH": "1",
           "MCP_HTTP_HOST": "127.0.0.1", "MCP_HTTP_PORT": str(porta),
           "RODADO_URL": f"http://127.0.0.1:{falso.server_address[1]}"}
    for k in ("RODADO_TOKEN", "RODADO_SENHA"):
        env.pop(k, None)
    proc = subprocess.Popen([sys.executable, os.path.join(RAIZ, "mcp", "mcp_server.py")], env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        for _ in range(100):
            try:
                socket.create_connection(("127.0.0.1", porta), timeout=0.2).close()
                break
            except OSError:
                time.sleep(0.2)
        else:
            sys.exit("o MCP não subiu: " + proc.stderr.read().decode()[-2000:])

        VISTOS.clear()
        r = chama(porta, {"X-Rodado-Ip": "203.0.113.7", "X-Rodado-Token": "tokentokentoken123"})
        assert "error" not in json.dumps(r.get("result", {})).lower() or VISTOS, r
        h = VISTOS[-1]
        assert h.get("x-rodado-ip") == "203.0.113.7" and h.get("x-rodado-token") == "tokentokentoken123", h

        VISTOS.clear()   # token pelo cookie (entrada pelo navegador): vira X-Rodado-Token
        chama(porta, {"X-Rodado-Ip": "203.0.113.8", "Cookie": "outro=1; rodado_token=cookiecookiecookie9"})
        h = VISTOS[-1]
        assert h.get("x-rodado-ip") == "203.0.113.8" and h.get("x-rodado-token") == "cookiecookiecookie9", h

        VISTOS.clear()   # uma requisição não herda a identidade da anterior
        chama(porta, {"X-Rodado-Ip": "203.0.113.9"})
        h = VISTOS[-1]
        assert h.get("x-rodado-ip") == "203.0.113.9" and "x-rodado-token" not in h, h
        print("3/3 ok")
    finally:
        proc.terminate()
        proc.wait(timeout=10)
        falso.shutdown()


if __name__ == "__main__":
    main()
