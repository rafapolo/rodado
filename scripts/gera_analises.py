#!/usr/bin/env python3
"""Gera uma página própria por análise, em pages/analises/<slug>/index.html.

Por que não basta o /analises/?doc=<slug>: o conteúdo é montado por JS a partir
do .md, e crawler de WhatsApp/Twitter/Slack/Google não roda JS. Com uma URL só,
toda análise compartilhada mostraria o mesmo título e o mesmo cartão. Cada shell
aqui carrega <title>, description e Open Graph próprios no HTML estático — o
viewer continua montando o corpo depois, pro leitor.

O ?doc=<slug> segue funcionando (links assim já circulam); a URL limpa é a
canônica.

Ordem: este script escreve os shells, gera os cartões e chama o gera_seo.py, que
injeta o bloco de SEO/head e refaz o sitemap.
"""

import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ANALISES = RAIZ / "pages" / "analises"
MANIFEST = ANALISES / "results" / "manifest.json"

AVISO = "<!-- gerado por scripts/gera_analises.py — não editar à mão -->"

MODELO = """<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{aviso}
<title>{titulo} — rodado</title>
<meta name="description" content="{dek}">
<!-- a linha do site.css é marca do bloco comum: o gera_seo.py a substitui pelo
     bloco inteiro aqui, e não no fim do <head>, para o analises.css abaixo
     continuar vencendo a cascata -->
<link rel="stylesheet" href="../../assets/site.css">
<link rel="stylesheet" href="../analises.css">
</head>
<body>

<nav class="site-nav">
  <div class="nav-inner">
    <a class="brand" href="/">rodado</a>
    <div class="nav-right">
      <div class="links">
        <a href="/#temas">Temas</a>
        <a href="/analises/">Análises</a>
        <a href="../../mcp.html">MCP</a>
        <a href="https://xn--2dk.xyz/dataviz/">DataViz Hub</a>
      </div>
      <div class="nav-controls">
        <button id="themeToggle" class="theme-toggle" aria-label="Alternar tema claro/escuro" type="button"><i class="fa-solid fa-moon"></i></button>
      </div>
    </div>
  </div>
</nav>

<main>
  <a class="voltar" href="../">&larr; voltar às análises</a>
  <p class="eyebrow" id="eyebrow">Análises</p>
  <p class="meta">rodado em {rodado_em}</p>
  <div id="doc" data-slug="{slug}" data-base="../"><p class="doc-msg">Carregando…</p></div>
</main>

<footer>
  <div class="footer-inner">
    <a href="/">Índice temático</a>
    <span>Dados: fontes públicas oficiais / DuckDB</span>
  </div>
</footer>

<script src="https://cdn.jsdelivr.net/npm/marked@12/marked.min.js"></script>
<script src="../viewer.js"></script>
<script src="../../assets/theme-toggle.js"></script>
</body>
</html>
"""


def escapa(texto: str) -> str:
    return (texto.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def main() -> None:
    # "rodado_em" (DD-MM-AAAA) vem do primeiro commit de results/<slug>.md — não é
    # calculado aqui, precisa ser mantido à mão no manifest a cada análise nova:
    # git log --follow --diff-filter=A --format=%ad --date=format:%d-%m-%Y -- <arquivo> | tail -1
    if not MANIFEST.exists():
        sys.exit(f"manifest não encontrado: {MANIFEST}")
    itens = json.loads(MANIFEST.read_text(encoding="utf-8"))

    slugs = set()
    for item in itens:
        slug = item["slug"]
        slugs.add(slug)
        md = ANALISES / "results" / f"{slug}.md"
        if not md.exists():
            print(f"  ! {slug}: sem results/{slug}.md, pulando")
            continue
        destino = ANALISES / slug
        destino.mkdir(parents=True, exist_ok=True)
        (destino / "index.html").write_text(
            MODELO.format(
                aviso=AVISO,
                titulo=escapa(item["title"]),
                dek=escapa(item["dek"]),
                slug=escapa(slug),
                rodado_em=escapa(item.get("rodado_em", "")),
            ),
            encoding="utf-8",
        )
        print(f"  pages/analises/{slug}/index.html")

    # pastas de análises que sairam do manifest viram 404 silencioso se ficarem
    for sub in ANALISES.iterdir():
        if sub.is_dir() and sub.name not in {"img", "results"} and sub.name not in slugs:
            gerado = (sub / "index.html").exists() and AVISO in (
                sub / "index.html").read_text(encoding="utf-8")
            if gerado:
                print(f"  ! pages/analises/{sub.name}/ não está no manifest "
                      "(gerado antes?) — remova à mão se for o caso")

    print(f"{len(slugs)} análises")
    for script in ("gera_og_image.py", "gera_seo.py"):
        print(f"\n$ {script}")
        subprocess.run([sys.executable, str(RAIZ / "scripts" / script)], check=True)


if __name__ == "__main__":
    main()
