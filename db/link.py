#!/usr/bin/env python3
"""Link do db.rodado.xyz que abre o terminal e já executa uma consulta.

    db/link.py consulta.sql            # ou o SQL pela entrada padrão
    db/link.py -t consulta.sql         # com ?token= (lido no finland): abre sem senha

O SQL vai em ?z= (deflate cru + base64url), 25–60% mais curto que o ?query= em base64
puro; a página descomprime com DecompressionStream("deflate-raw"). O token dá acesso ao
espelho inteiro, não só a esta consulta: só passe o link com -t a quem pode tê-lo.
"""
import argparse
import base64
import subprocess
import sys
import zlib

BASE = "https://db.rodado.xyz/"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("arquivo", nargs="?", help="arquivo .sql (sem ele, lê da entrada padrão)")
    ap.add_argument("-t", "--token", action="store_true", help="inclui ?token= (ssh finland)")
    a = ap.parse_args()
    sql = (open(a.arquivo, encoding="utf-8").read() if a.arquivo else sys.stdin.read()).strip()
    if not sql:
        sys.exit("SQL vazio")
    c = zlib.compressobj(9, zlib.DEFLATED, -15)           # -15: deflate cru, sem cabeçalho zlib
    z = base64.urlsafe_b64encode(c.compress(sql.encode()) + c.flush()).rstrip(b"=").decode()
    params = f"z={z}"
    if a.token:
        token = subprocess.run(["ssh", "finland", "cat /root/rodado-db/.token"],
                               capture_output=True, text=True, check=True).stdout.strip()
        params = f"token={token}&{params}"
    print(BASE + "?" + params)


if __name__ == "__main__":
    main()
