#!/usr/bin/env python3
"""Tira o .html dos links internos de todas as páginas em pages/.

O GitHub Pages serve /mcp a partir de mcp.html, então o link limpo funciona e é
o que aparece na barra do navegador e no compartilhamento. Os geradores
(gera_analises, gera_home, gera_card_temas, gera_relatorio_nf...) continuam
escrevendo .html nos modelos; este passo roda no fim do gera_seo.py e
normaliza tudo de uma vez — assim nenhum gerador precisa saber disso.

Regras:
- só href="..." e só links internos (relativos, /raiz ou https://rodado.xyz);
- só quando o alvo existe como arquivo .html em pages/ — link para algo fora do
  deploy fica como está;
- index.html some inteiro: "temas/index.html" → "temas/", "../index.html" → "../";
- #âncora e ?consulta são preservadas.

Prévia local: python -m http.server não resolve /mcp → mcp.html. Para conferir
os links limpos, usar `bun scripts/serve.ts` (porta 8765, `--port N`), que imita o
Pages: /x → x.html, /pasta/ → pasta/index.html.

Uso: python3 scripts/limpa_links_html.py   (idempotente)
"""

import re
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PAGES = RAIZ / "pages"
SITE = "https://rodado.xyz"

HREF = re.compile(r'href="([^"]*?\.html)([#?][^"]*)?"')


def alvo_existe(arquivo: Path, url: str) -> bool:
    caminho = url[len(SITE):] if url.startswith(SITE) else url
    if caminho.startswith("/"):
        destino = PAGES / caminho.lstrip("/")
    else:
        destino = arquivo.parent / caminho
    try:
        return destino.resolve().is_file() and destino.resolve().is_relative_to(PAGES)
    except OSError:
        return False


def limpa(url: str) -> str:
    if url.endswith("index.html"):
        url = url[: -len("index.html")]
        return url or "./"
    return url[: -len(".html")]


def processa(arquivo: Path) -> int:
    texto = arquivo.read_text(encoding="utf-8")
    n = 0

    def troca(m: re.Match) -> str:
        nonlocal n
        url, resto = m.group(1), m.group(2) or ""
        if "://" in url and not url.startswith(SITE):
            return m.group(0)
        if not alvo_existe(arquivo, url):
            return m.group(0)
        n += 1
        return f'href="{limpa(url)}{resto}"'

    novo = HREF.sub(troca, texto)
    if n:
        arquivo.write_text(novo, encoding="utf-8")
    return n


def main() -> None:
    total = arquivos = 0
    # só os versionados: pages/ também recebe checkouts de outros repositórios
    # no deploy, e esses não são deste script
    saida = subprocess.run(["git", "ls-files", "-z", "pages/*.html", "pages/**/*.html"],
                           cwd=RAIZ, capture_output=True, text=True, check=True).stdout
    for rel in sorted(set(filter(None, saida.split("\0")))):
        arquivo = RAIZ / rel
        n = processa(arquivo)
        if n:
            total += n
            arquivos += 1
    print(f"{total} links sem .html em {arquivos} páginas")


if __name__ == "__main__":
    main()
