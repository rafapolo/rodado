#!/usr/bin/env python3
"""Build the Rodado Atlas from one source into its two carriers.

    python3 scripts/gera_schema_graph.py   # -> docs/context/schema_graph.json
    python3 scripts/build_atlas.py         # -> pages/atlas/index.html + en.html (+ artifact copy)

`pages/atlas/_page.html` is the single source. It carries a `__GRAPH_JSON__`
placeholder that decides how the graph reaches the browser:

  site      the placeholder is emptied and the graph is copied next to the
            page, which fetches it — a 630 KB blob stays out of every commit
  artifact  the graph is inlined, because a published Artifact runs under a
            CSP that blocks fetching anything, even from its own origin

The source is written artifact-shaped: no doctype, no <html>, no <head>, since
the Artifact runtime supplies those. Served from rodado.xyz nothing supplies
them, so the site build wraps it — without the wrapper the page renders in
quirks mode and, with no charset declared, every accented character in the
interface comes out as mojibake.

Two languages from the same source: index.html (/atlas/, pt-BR) and en.html
(/atlas/en, English). en.html sits beside index.html, not in a subfolder, so
the page's relative fetches (schema_graph.json, ontologia.json, detalhes/)
resolve the same from both. The script's own labels switch on the
`__ATLAS_LANG__` marker (tr(pt, en) pairs in _page.html); the static HTML is
translated here, by exact string, before it ships — crawlers read it, so it
can't wait for JavaScript. A source string that is no longer found stops the
build instead of silently leaving Portuguese behind. Ontology labels come
from docs/context/ontologia.en.yaml via gera_ontologia.ts. Free text from the
data (dataset descriptions, table cards, pitfalls) exists only in pt-BR.
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "pages" / "atlas" / "_page.html"
GRAPH = REPO / "pages" / "atlas" / "schema_graph.json"
SITE = REPO / "pages" / "atlas" / "index.html"
SITE_EN = REPO / "pages" / "atlas" / "en.html"
PLACEHOLDER = "__GRAPH_JSON__"
LANG_PLACEHOLDER = "__ATLAS_LANG__"
# o modo Ontologia busca pages/atlas/ontologia.json (bun scripts/gera_ontologia.ts);
# na cópia de Artifact vai embutido, pelo mesmo motivo do grafo
ONTO = REPO / "pages" / "atlas" / "ontologia.json"
ONTO_PLACEHOLDER = "__ONTO_JSON__"


HREFLANG = """<link rel="alternate" hreflang="pt-br" href="https://rodado.xyz/atlas/">
<link rel="alternate" hreflang="en" href="https://rodado.xyz/atlas/en">
<link rel="alternate" hreflang="x-default" href="https://rodado.xyz/atlas/">
"""

HEAD_PT = """<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Mapa navegável das tabelas do espelho do rodado e das colunas de join que as conectam.">
<link rel="canonical" href="https://rodado.xyz/atlas/">
""" + HREFLANG + """<meta property="og:type" content="website">
<meta property="og:site_name" content="rodado">
<meta property="og:locale" content="pt_BR">
<meta property="og:url" content="https://rodado.xyz/atlas/">
<meta property="og:title" content="Atlas do rodado: as tabelas e as chaves que as ligam">
<meta property="og:description" content="Mapa navegável das tabelas do espelho do rodado e das colunas de join que as conectam.">
<meta property="og:image" content="https://rodado.xyz/assets/og-atlas.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Atlas do rodado">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Atlas do rodado: as tabelas e as chaves que as ligam">
<meta name="twitter:description" content="Mapa navegável das tabelas do espelho do rodado e das colunas de join que as conectam.">
<meta name="twitter:image" content="https://rodado.xyz/assets/og-atlas.png">
"""

HEAD_EN = """<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Navigable map of the tables in the rodado mirror of Brazilian public data and the join columns that connect them.">
<link rel="canonical" href="https://rodado.xyz/atlas/en">
""" + HREFLANG + """<meta property="og:type" content="website">
<meta property="og:site_name" content="rodado">
<meta property="og:locale" content="en_US">
<meta property="og:url" content="https://rodado.xyz/atlas/en">
<meta property="og:title" content="rodado Atlas: the tables and the keys that link them">
<meta property="og:description" content="Navigable map of the tables in the rodado mirror of Brazilian public data and the join columns that connect them.">
<meta property="og:image" content="https://rodado.xyz/assets/og-atlas.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="rodado Atlas">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="rodado Atlas: the tables and the keys that link them">
<meta name="twitter:description" content="Navigable map of the tables in the rodado mirror of Brazilian public data and the join columns that connect them.">
<meta name="twitter:image" content="https://rodado.xyz/assets/og-atlas.png">
"""

HEAD_COMMON = """<link rel="icon" href="/assets/favicon.ico" sizes="any">
<link rel="icon" href="/assets/icon-192.png" type="image/png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<script defer src="https://cloud.umami.is/script.js" data-website-id="d2597bf7-73e0-4e7e-b353-1202d9f72b7d"></script>
"""


NAV_PT = """<nav class="site-nav">
  <div class="nav-inner">
    <a class="brand" href="/">rodado</a>
    <div class="nav-right">
      <div class="links">
        <a href="/analises/">Análises</a>
        <a href="/plataformas/">Plataformas</a>
        <a href="https://xn--2dk.xyz/">DataViz</a>
        <a href="/temas/">Temas</a>
        <a href="/atlas/">Atlas</a>
        <a class="mcp-link" href="/mcp">MCP</a>
      </div>
      <div class="nav-controls">
        <div class="lang-switch">
          <span class="lang-current">PT</span>
          <span class="lang-sep">/</span>
          <a href="/atlas/en" class="lang-link">EN</a>
        </div>
        <button id="themeToggle" class="theme-toggle" aria-label="Alternar tema claro/escuro" type="button"><i class="fa-solid fa-moon"></i></button>"""

NAV_EN = """<nav class="site-nav">
  <div class="nav-inner">
    <a class="brand" href="/en">rodado</a>
    <div class="nav-right">
      <div class="links">
        <a href="/analises/en">Analyses</a>
        <a href="/plataformas/en">Platforms</a>
        <a href="https://xn--2dk.xyz/dataviz/">DataViz</a>
        <a href="/temas-en/">Topics</a>
        <a href="/atlas/en">Atlas</a>
        <a class="mcp-link" href="/mcp-en">MCP</a>
      </div>
      <div class="nav-controls">
        <div class="lang-switch">
          <a href="/atlas/" class="lang-link">PT</a>
          <span class="lang-sep">/</span>
          <span class="lang-current">EN</span>
        </div>
        <button id="themeToggle" class="theme-toggle" aria-label="Toggle light/dark theme" type="button"><i class="fa-solid fa-moon"></i></button>"""

# Static HTML of _page.html → English, by exact string. Every pair must match
# exactly once; edit _page.html and this list together.
STATIC_EN = [
    (NAV_PT, NAV_EN),
    ('<p class="sub">As tabelas não vêm conectadas prontas. O que as liga são colunas que guardam a mesma informação com nomes diferentes — um CNPJ, um município, uma data. Cada etiqueta marca um desses pontos em comum.</p>',
     '<p class="sub">The tables do not come connected. What links them are columns that hold the same information under different names — a CNPJ, a municipality, a date. Each label marks one of those common points. Dataset descriptions, table cards and pitfalls come from the sources and are in Portuguese.</p>'),
    ('<span>tabelas</span>', '<span>tables</span>'),
    ('<span>chaves</span>', '<span>keys</span>'),
    ('<span>ligações</span>', '<span>links</span>'),
    ('placeholder="buscar tabela, dataset ou chave"', 'placeholder="search table, dataset or key"'),
    ('aria-label="Buscar"', 'aria-label="Search"'),
    ('<p class="legend-t">Distribuição</p>', '<p class="legend-t">Layout</p>'),
    ('<p class="legend-t">Grafo 3D</p>', '<p class="legend-t">3D graph</p>'),
    ('aria-pressed="true">mostrar nós</button>', 'aria-pressed="true">show nodes</button>'),
    ('<label for="d3-width">espessura das ligações</label>', '<label for="d3-width">link thickness</label>'),
    ('<label for="d3-expand">expansão do grafo</label>', '<label for="d3-expand">graph spread</label>'),
    ('<p class="list-t" id="list-t">Temas</p>', '<p class="list-t" id="list-t">Themes</p>'),
    ('aria-expanded="false">Painel</button>', 'aria-expanded="false">Panel</button>'),
    ('style="display:none">carregando 3D…</div>', 'style="display:none">loading 3D…</div>'),
    ('aria-label="Ontologia: classes de entidade e relações"', 'aria-label="Ontology: entity classes and relations"'),
    ('<button id="zout" title="Afastar" aria-label="Afastar">', '<button id="zout" title="Zoom out" aria-label="Zoom out">'),
    ('<button id="zin" title="Aproximar" aria-label="Aproximar">', '<button id="zin" title="Zoom in" aria-label="Zoom in">'),
    ('<button id="reset" title="Ver tudo">tudo</button>', '<button id="reset" title="Show everything">all</button>'),
    ('<button id="home" title="Voltar ao ponto de partida">início</button>', '<button id="home" title="Back to the starting point">home</button>'),
    ("""    clique esquerdo + arrastar → girar<br>
    clique direito + arrastar → mover<br>
    rolar → zoom · clique numa esfera → focar""",
     """    left click + drag → rotate<br>
    right click + drag → pan<br>
    scroll → zoom · click a sphere → focus"""),
    ('<button class="close" id="i-close" aria-label="Fechar">', '<button class="close" id="i-close" aria-label="Close">'),
]


def to_english(page: str) -> str:
    for pt, en in STATIC_EN:
        n = page.count(pt)
        if n != 1:
            sys.exit(f"build_atlas: texto do _page.html achado {n}x (esperado 1) — "
                     f"atualize STATIC_EN:\n  {pt[:90]!r}")
        page = page.replace(pt, en)
    return page


def wrap_document(page: str, lang: str = "pt") -> str:
    """Give the standalone page the document the Artifact runtime would."""
    cut = page.index("</style>") + len("</style>")
    head, body = page[:cut], page[cut:]
    meta = (HEAD_EN if lang == "en" else HEAD_PT) + HEAD_COMMON
    return ("<!doctype html>\n<html lang=\"" + ("en" if lang == "en" else "pt-br") + "\">\n<head>\n"
            + meta + head.strip() + "\n</head>\n<body>\n"
            + body.strip() + "\n</body>\n</html>\n")


def build(artifact_out: Path | None = None):
    if not GRAPH.exists():
        sys.exit(f"{GRAPH} missing — run scripts/gera_schema_graph.py first")
    tpl = SRC.read_text()
    if PLACEHOLDER not in tpl:
        sys.exit(f"{SRC} has no {PLACEHOLDER} placeholder")
    graph = GRAPH.read_text()
    if "</script" in graph.lower():
        sys.exit("graph JSON contains a closing script tag")
    if f'"{LANG_PLACEHOLDER}"' not in tpl:
        sys.exit(f"{SRC} has no {LANG_PLACEHOLDER} marker")
    if NAV_PT not in tpl:
        sys.exit(f"{SRC}: o menu não bate com NAV_PT — atualize build_atlas.py")
    lang = lambda page, l: page.replace(f'"{LANG_PLACEHOLDER}"', f'"{l}"')

    site = tpl.replace(PLACEHOLDER, "").replace(ONTO_PLACEHOLDER, "")
    SITE.write_text(wrap_document(lang(site, "pt"), "pt"))
    SITE_EN.write_text(wrap_document(lang(to_english(site), "en"), "en"))
    for out in (SITE, SITE_EN):
        print(f"site     {out.relative_to(REPO)} "
              f"({out.stat().st_size / 1024:.0f} KB + {len(graph) / 1024:.0f} KB de dados)")

    if artifact_out:
        onto = ONTO.read_text().strip() if ONTO.exists() else ""
        artifact_out.write_text(lang(tpl.replace(PLACEHOLDER, graph).replace(ONTO_PLACEHOLDER, onto), "pt"))
        print(f"artifact {artifact_out} ({artifact_out.stat().st_size / 1024:.0f} KB, autocontido)")


if __name__ == "__main__":
    out = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else None
    build(out)
