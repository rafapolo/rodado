#!/usr/bin/env python3
"""Manda ao Telegram as linhas `[limites] AVISO` do log do container rodado-db.

Roda no finland, FORA do container, pelo cron (a cada 5 min). O gatilho em limites.py já dá no
máximo um aviso por chave, tipo e dia; aqui só se evita repetir a mesma linha entre uma rodada e
outra (arquivo de vistos). O token do bot e o chat id ficam em /root/rodado-db/.telegram
(TELEGRAM_BOT=... e TELEGRAM_CHAT_ID=..., chmod 600), nunca no repositório nem no log. Sem esse
arquivo, sai sem consumir nada: quando ele aparecer, os avisos das últimas 26 h seguem para o bot.

  */5 * * * * cd /root/rodado-db && python3 avisos_telegram.py >> avisos_telegram.log 2>&1
"""
import html
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request

DIR = os.environ.get("RODADO_DB_DIR", "/root/rodado-db")
ENV = os.path.join(DIR, ".telegram")
VISTOS = os.path.join(DIR, "avisos_vistos.txt")
JANELA = "26h"


def le_env(caminho):
    dados = {}
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if "=" in linha and not linha.startswith("#"):
                k, v = linha.split("=", 1)
                dados[k.strip()] = v.strip().strip("'\"")
    return dados


def avisos():
    """Linhas de aviso do log, com o carimbo de hora do docker (cada uma é única)."""
    nome = subprocess.run(["docker", "ps", "-qf", "name=rodado-db"], capture_output=True, text=True).stdout.split()
    if not nome:
        return []
    r = subprocess.run(["docker", "logs", "--timestamps", "--since", JANELA, nome[0]],
                       capture_output=True, text=True)
    return [l for l in (r.stdout + r.stderr).splitlines() if "[limites] AVISO" in l]


def envia(token, chat, texto):
    corpo = urllib.parse.urlencode({"chat_id": chat, "text": texto, "parse_mode": "HTML",
                                    "disable_web_page_preview": "true"}).encode()
    with urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage",
                                                        data=corpo), timeout=20) as r:
        return json.load(r).get("ok", False)


def main():
    if not os.path.exists(ENV):
        print(f"sem {ENV}: nada enviado", file=sys.stderr)
        return 0
    env = le_env(ENV)
    token, chat = env.get("TELEGRAM_BOT", ""), env.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat:
        print("TELEGRAM_BOT ou TELEGRAM_CHAT_ID ausente: nada enviado", file=sys.stderr)
        return 0
    try:
        vistos = set(open(VISTOS, encoding="utf-8").read().split("\n"))
    except FileNotFoundError:
        vistos = set()
    for linha in avisos():
        if linha in vistos:
            continue
        texto = linha.split("[limites] AVISO", 1)[1].strip()
        try:
            ok = envia(token, chat, "<b>db.rodado.xyz</b>: " + html.escape(texto))
        except Exception as e:   # a mensagem de erro do urllib não traz o token, mas não arrisca
            print(f"falha ao enviar ({type(e).__name__}); tenta de novo na próxima rodada", file=sys.stderr)
            return 1
        if ok:
            with open(VISTOS, "a", encoding="utf-8") as f:
                f.write(linha + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
