#!/usr/bin/env python3
"""Link curto do db.rodado.xyz para uma consulta: https://db.rodado.xyz/q/<id>.

    db/link.py consulta.sql            # ou o SQL pela entrada padrão
    db/link.py -z consulta.sql         # link antigo ?z=, autocontido (pede senha)

O SQL é salvo no servidor (POST /q, autenticado com o token lido no finland). O link abre
o terminal normal e executa a consulta; quem o abre entra sem senha e, a pedido, com o
mesmo acesso de quem tem o token (o espelho inteiro, por 30 dias de cookie).

O ?z= leva o SQL na própria URL (deflate cru + base64url) e não depende de nada salvo,
mas pede a senha.
"""
import argparse
import base64
import json
import subprocess
import sys
import urllib.request
import zlib

BASE = "https://db.rodado.xyz"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("arquivo", nargs="?", help="arquivo .sql (sem ele, lê da entrada padrão)")
    ap.add_argument("-z", action="store_true", help="link ?z= autocontido em vez do link curto")
    a = ap.parse_args()
    sql = (open(a.arquivo, encoding="utf-8").read() if a.arquivo else sys.stdin.read()).strip()
    if not sql:
        sys.exit("SQL vazio")
    if a.z:
        c = zlib.compressobj(9, zlib.DEFLATED, -15)           # -15: deflate cru, sem cabeçalho zlib
        z = base64.urlsafe_b64encode(c.compress(sql.encode()) + c.flush()).rstrip(b"=").decode()
        print(f"{BASE}/?z={z}")
        return
    token = subprocess.run(["ssh", "finland", "cat /root/rodado-db/.token"],
                           capture_output=True, text=True, check=True).stdout.strip()
    req = urllib.request.Request(f"{BASE}/q?token={token}", data=sql.encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            print(BASE + json.load(r)["url"])
    except urllib.error.HTTPError as e:
        sys.exit(json.load(e).get("erro", str(e)))


if __name__ == "__main__":
    main()
