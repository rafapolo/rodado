#!/usr/bin/env python3
"""Injeta metadados de SEO e o <head> comum nas páginas de rodado.xyz.

Dois blocos por página, cada um entre sentinelas:

- seo:*  — canonical, Open Graph, Twitter Card, hreflang PT/EN, ícones,
           theme-color e JSON-LD, derivados do título e da descrição da página;
- head:* — o que toda página carrega igual (fontes, Font Awesome, CSS do site,
           analytics). Edite a lista COMUM aqui e rode o script: muda em todas.

Também gera robots.txt e sitemap.xml.

É idempotente: os blocos são reescritos a cada execução, então rodar de novo
não duplica nada.
"""

import html
import re
from datetime import date
from pathlib import Path

BASE = "https://rodado.xyz"
PAGES = Path(__file__).resolve().parent.parent / "pages"

OPEN = "<!-- seo:start (gerado por scripts/gera_seo.py — não editar à mão) -->"
CLOSE = "<!-- seo:end -->"

HEAD_OPEN = "<!-- head:start (gerado por scripts/gera_seo.py — não editar à mão) -->"
HEAD_CLOSE = "<!-- head:end -->"

# O <head> que toda página compartilha. `{p}` vira "../" nas subpastas.
# Fonte única: mexa aqui, rode o script, vale para as 94 páginas.
COMUM = [
    '<link rel="preconnect" href="https://fonts.googleapis.com">',
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
    '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500'
    '&family=Public+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">',
    '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/'
    '6.5.2/css/all.min.css">',
    '<link rel="stylesheet" href="{p}assets/site.css">',
    '<link rel="stylesheet" href="{p}assets/mcp-theme.css">',
    '<script defer src="https://cloud.umami.is/script.js" '
    'data-website-id="d2597bf7-73e0-4e7e-b353-1202d9f72b7d"></script>',
]

# Marcas das linhas absorvidas pelo bloco comum. Servem para recolher as cópias
# soltas que ainda existam no HTML — o CSS específico de página (mcp-page.css,
# <style> inline) não casa com nenhuma e continua onde está, depois do bloco.
MARCAS_COMUNS = (
    "fonts.googleapis.com",
    "fonts.gstatic.com",
    "font-awesome",
    "assets/site.css",
    "assets/mcp-theme.css",
    "cloud.umami.is",
)

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
    # index.html não aparece na URL: pages/index.html é "/" e
    # pages/analises/<slug>/index.html é "/analises/<slug>/"
    if rel.endswith("index.html"):
        rel = rel[: -len("index.html")]
    return f"/{rel}"


def prefixo_de(path: Path) -> str:
    """Quantos ../ até pages/. As análises estão dois níveis abaixo."""
    return "../" * (len(path.relative_to(PAGES).parts) - 1)


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


def is_analise(path: Path) -> bool:
    """pages/analises/<slug>/index.html — uma análise com página própria."""
    return path.parent.parent.name == "analises" and path.name == "index.html"


def data_da_analise(slug: str) -> str | None:
    for item in analises_manifest():
        if item.get("slug") == slug:
            return item.get("date")
    return None


def analises_manifest() -> list[dict]:
    caminho = PAGES / "analises" / "results" / "manifest.json"
    if not caminho.exists():
        return []
    import json

    return json.loads(caminho.read_text(encoding="utf-8"))


def bloco(path: Path, titulo: str, descricao: str) -> str:
    en = is_en(path)
    url = BASE + rel_url(path)
    prefixo = prefixo_de(path)
    if is_analise(path):
        # cada análise tem seu cartão editorial (scripts/gera_og_image.py); sem
        # isso todas compartilhariam a capa do site no feed
        imagem = f"{BASE}/analises/img/og-{path.parent.name}.png"
    else:
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
        and not is_analise(path) else '<meta property="og:type" content="article">',
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

    # as análises também se chamam index.html, mas são artigos — testar antes
    if path.parent == PAGES and path.name in ("index.html", "en.html"):
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
    elif is_analise(path):
        data = data_da_analise(path.parent.name)
        # o manifest traz só ano-mês; o schema aceita a precisão que houver
        publicado = f',"datePublished":"{e(data)}"' if data else ""
        linhas.append(
            '<script type="application/ld+json">'
            '{"@context":"https://schema.org","@type":"Article",'
            f'"headline":"{e(social)}","description":"{e(descricao)}",'
            f'"url":"{e(url)}","image":"{e(imagem)}"{publicado},'
            '"inLanguage":"pt-BR",'
            f'"author":{{"@type":"Organization","name":"{SITE_NAME}"}},'
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


def bloco_comum(path: Path) -> str:
    prefixo = prefixo_de(path)
    linhas = [linha.replace("{p}", prefixo) for linha in COMUM]
    return "\n".join([HEAD_OPEN, *linhas, HEAD_CLOSE])


def injeta_comum(path: Path) -> bool:
    """Substitui as linhas comuns do <head> pelo bloco gerado."""
    texto = path.read_text(encoding="utf-8")

    m = re.search(r"(?is)(<head[^>]*>)(.*?)(</head>)", texto)
    if m is None:
        print(f"  ! sem <head>, ignorado: {path.name}")
        return False

    # O bloco volta onde já estava (ou, na primeira vez, onde estava a primeira
    # linha comum) para não passar na frente do CSS específico da página e
    # inverter a cascata.
    mantidas: list[str] = []
    pos: int | None = None
    dentro = False
    for linha in m.group(2).split("\n"):
        if HEAD_OPEN in linha:
            dentro = True
        if dentro:
            if pos is None:
                pos = len(mantidas)
            dentro = HEAD_CLOSE not in linha
            continue
        if any(marca in linha for marca in MARCAS_COMUNS):
            if pos is None:
                pos = len(mantidas)
            continue
        mantidas.append(linha)

    if pos is None:  # página nova, ainda sem nenhuma das linhas comuns
        pos = len(mantidas) - 1 if mantidas and not mantidas[-1].strip() else len(mantidas)

    mantidas.insert(pos, bloco_comum(path))
    novo = texto[: m.start(2)] + "\n".join(mantidas) + texto[m.end(2) :]

    if novo != texto:
        path.write_text(novo, encoding="utf-8")
    return True


def alvos() -> list[Path]:
    arquivos = sorted(PAGES.glob("*.html"))
    for sub in ("temas", "temas-en"):
        arquivos += sorted(
            p for p in (PAGES / sub).glob("*.html") if not p.name.startswith("_")
        )
    # as páginas por análise (pages/analises/<slug>/index.html), geradas por
    # scripts/gera_analises.py — o índice analises/index.html fica de fora,
    # o conteúdo dele é montado por JS e não tem metadados próprios
    arquivos += sorted((PAGES / "analises").glob("*/index.html"))
    return arquivos


def alvos_head() -> list[Path]:
    """Todo HTML de pages/ — inclusive os _template.html e o índice de
    analises/, que fica fora do SEO mas também carrega o head comum."""
    return sorted(PAGES.rglob("*.html"))


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
    c = sum(injeta_comum(p) for p in alvos_head())
    gera_sitemap(arquivos)
    gera_robots()
    print(f"{n} páginas com metadados")
    print(f"{c} páginas com head comum")
    print(f"sitemap.xml com {len(arquivos)} URLs")
    print("robots.txt")


if __name__ == "__main__":
    main()
