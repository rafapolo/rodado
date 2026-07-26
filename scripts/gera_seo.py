#!/usr/bin/env python3
"""Injeta metadados de SEO e compartilhamento nas páginas de rodado.xyz.

Para cada página: canonical, Open Graph, Twitter Card, hreflang PT/EN,
ícones, theme-color e JSON-LD. Também gera robots.txt e sitemap.xml.

É idempotente: o bloco inserido é delimitado por sentinelas e reescrito
a cada execução, então rodar de novo não duplica nada.
"""

import html
import re
from datetime import date
from pathlib import Path

BASE = "https://rodado.xyz"
PAGES = Path(__file__).resolve().parent.parent / "pages"

OPEN = "<!-- seo:start (gerado por scripts/gera_seo.py — não editar à mão) -->"
CLOSE = "<!-- seo:end -->"

# Descrições reescritas: sem menção a espelhamento, focadas no que o
# leitor encontra na página.
DESCRICOES = {
    "index.html": (
        "839 tabelas de dados oficiais brasileiros cruzadas em 43 investigações "
        "sobre desigualdade, poder, economia, saúde e violência — o retrato que o "
        "Estado já tem de si mesmo."
    ),
    "en.html": (
        "839 tables of official Brazilian data, cross-referenced into 43 "
        "investigations on inequality, power, economy, health and violence — the "
        "portrait the State already has of itself."
    ),
}

SITE_NAME = "rodado"


def rel_url(path: Path) -> str:
    rel = path.relative_to(PAGES).as_posix()
    return "/" if rel == "index.html" else f"/{rel}"


def contraparte(path: Path) -> Path | None:
    """Devolve a versão no outro idioma, se existir."""
    rel = path.relative_to(PAGES).as_posix()
    mapa = {
        "index.html": "en.html",
        "en.html": "index.html",
        "mcp.html": "mcp-en.html",
        "mcp-en.html": "mcp.html",
    }
    if rel in mapa:
        alvo = PAGES / mapa[rel]
    elif rel.startswith("temas/"):
        alvo = PAGES / rel.replace("temas/", "temas-en/", 1)
    elif rel.startswith("temas-en/"):
        alvo = PAGES / rel.replace("temas-en/", "temas/", 1)
    else:
        return None
    return alvo if alvo.exists() else None


def is_en(path: Path) -> bool:
    rel = path.relative_to(PAGES).as_posix()
    return rel in {"en.html", "mcp-en.html", "technical.html"} or rel.startswith("temas-en/")


def extrai(pattern: str, texto: str) -> str | None:
    m = re.search(pattern, texto, re.I | re.S)
    return m.group(1).strip() if m else None


def bloco(path: Path, titulo: str, descricao: str) -> str:
    en = is_en(path)
    url = BASE + rel_url(path)
    prefixo = "../" if path.parent != PAGES else ""
    imagem = f"{BASE}/assets/{'og-en.png' if en else 'og.png'}"
    locale = "en_US" if en else "pt_BR"
    outra = contraparte(path)

    # Nas páginas de tema o <title> é "Assunto — rodado"; no cartão social
    # o nome do site já aparece à parte, então o sufixo vira ruído.
    social = re.sub(r"\s+—\s+rodado$", "", titulo)
    # a home já traz "rodado" no título; nas páginas internas o alt precisa dele
    alt = social if SITE_NAME in social.lower() else f"{social} — {SITE_NAME}"

    e = html.escape
    linhas = [
        OPEN,
        f'<link rel="canonical" href="{e(url)}">',
    ]

    if outra is not None:
        outra_url = BASE + rel_url(outra)
        aqui, la = ("en", "pt-br") if en else ("pt-br", "en")
        linhas += [
            f'<link rel="alternate" hreflang="{aqui}" href="{e(url)}">',
            f'<link rel="alternate" hreflang="{la}" href="{e(outra_url)}">',
            f'<link rel="alternate" hreflang="x-default" href="{e(BASE + "/")}">',
        ]

    linhas += [
        '<meta property="og:type" content="website">' if path.parent == PAGES
        else '<meta property="og:type" content="article">',
        f'<meta property="og:site_name" content="{SITE_NAME}">',
        f'<meta property="og:locale" content="{locale}">',
        f'<meta property="og:url" content="{e(url)}">',
        f'<meta property="og:title" content="{e(social)}">',
        f'<meta property="og:description" content="{e(descricao)}">',
        f'<meta property="og:image" content="{e(imagem)}">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        f'<meta property="og:image:alt" content="{e(alt)}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{e(social)}">',
        f'<meta name="twitter:description" content="{e(descricao)}">',
        f'<meta name="twitter:image" content="{e(imagem)}">',
        f'<link rel="icon" href="{prefixo}assets/favicon.ico" sizes="any">',
        f'<link rel="icon" type="image/png" sizes="32x32" href="{prefixo}assets/favicon-32.png">',
        f'<link rel="icon" type="image/png" sizes="16x16" href="{prefixo}assets/favicon-16.png">',
        f'<link rel="apple-touch-icon" href="{prefixo}assets/apple-touch-icon.png">',
        f'<link rel="manifest" href="{BASE}/site.webmanifest">',
        '<meta name="theme-color" content="#9c3b2e">',
        '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">',
    ]

    if path.name in ("index.html", "en.html"):
        linhas.append(
            '<script type="application/ld+json">'
            '{"@context":"https://schema.org","@type":"WebSite",'
            f'"name":"{SITE_NAME}","url":"{BASE}/",'
            f'"description":"{e(descricao)}",'
            f'"inLanguage":"{"en" if en else "pt-BR"}"}}'
            "</script>"
        )
    elif path.parent.name in ("temas", "temas-en"):
        linhas.append(
            '<script type="application/ld+json">'
            '{"@context":"https://schema.org","@type":"Article",'
            f'"headline":"{e(social)}","description":"{e(descricao)}",'
            f'"url":"{e(url)}","image":"{e(imagem)}",'
            f'"inLanguage":"{"en" if en else "pt-BR"}",'
            f'"isPartOf":{{"@type":"WebSite","name":"{SITE_NAME}","url":"{BASE}/"}}}}'
            "</script>"
        )

    linhas.append(CLOSE)
    return "\n".join(linhas)


def processa(path: Path) -> bool:
    texto = path.read_text(encoding="utf-8")

    # remove bloco anterior — mantém a operação idempotente
    texto = re.sub(
        re.escape(OPEN) + r".*?" + re.escape(CLOSE) + r"\n?",
        "",
        texto,
        flags=re.S,
    )

    titulo = extrai(r"<title>(.*?)</title>", texto)
    if titulo is None:
        print(f"  ! sem <title>, ignorado: {path.name}")
        return False
    titulo = html.unescape(titulo)

    nome = path.relative_to(PAGES).as_posix()
    if nome in DESCRICOES:
        nova = DESCRICOES[nome]
        texto = re.sub(
            r'<meta\s+name="description"\s+content="[^"]*"\s*/?>',
            f'<meta name="description" content="{html.escape(nova)}">',
            texto,
            count=1,
            flags=re.I,
        )
        descricao = nova
    else:
        bruta = extrai(r'<meta\s+name="description"\s+content="([^"]*)"', texto)
        descricao = html.unescape(bruta) if bruta else titulo

    novo_bloco = bloco(path, titulo, descricao)

    # insere logo após a meta description (ou após o <title>)
    m = re.search(r'<meta\s+name="description"[^>]*>', texto, re.I)
    if m is None:
        m = re.search(r"</title>", texto, re.I)
    pos = m.end()
    texto = texto[:pos] + "\n" + novo_bloco + texto[pos:]

    path.write_text(texto, encoding="utf-8")
    return True


def alvos() -> list[Path]:
    arquivos = sorted(PAGES.glob("*.html"))
    for sub in ("temas", "temas-en"):
        arquivos += sorted(
            p for p in (PAGES / sub).glob("*.html") if not p.name.startswith("_")
        )
    return arquivos


def gera_sitemap(arquivos: list[Path]) -> None:
    hoje = date.today().isoformat()
    linhas = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">',
    ]
    for p in arquivos:
        url = BASE + rel_url(p)
        prioridade = "1.0" if p.name == "index.html" else "0.8" if p.parent == PAGES else "0.6"
        linhas.append("  <url>")
        linhas.append(f"    <loc>{html.escape(url)}</loc>")
        outra = contraparte(p)
        if outra is not None:
            aqui, la = ("en", "pt-br") if is_en(p) else ("pt-br", "en")
            linhas.append(
                f'    <xhtml:link rel="alternate" hreflang="{aqui}" href="{html.escape(url)}"/>'
            )
            linhas.append(
                f'    <xhtml:link rel="alternate" hreflang="{la}" '
                f'href="{html.escape(BASE + rel_url(outra))}"/>'
            )
        linhas.append(f"    <lastmod>{hoje}</lastmod>")
        linhas.append(f"    <priority>{prioridade}</priority>")
        linhas.append("  </url>")
    linhas.append("</urlset>")
    (PAGES / "sitemap.xml").write_text("\n".join(linhas) + "\n", encoding="utf-8")


def gera_robots() -> None:
    (PAGES / "robots.txt").write_text(
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        f"Sitemap: {BASE}/sitemap.xml\n",
        encoding="utf-8",
    )


def main() -> None:
    arquivos = alvos()
    n = sum(processa(p) for p in arquivos)
    gera_sitemap(arquivos)
    gera_robots()
    print(f"{n} páginas com metadados")
    print(f"sitemap.xml com {len(arquivos)} URLs")
    print("robots.txt")


if __name__ == "__main__":
    main()
