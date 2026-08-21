#!/usr/bin/env python3
"""Build the Rodado Atlas from one source into its two carriers.

    python3 scripts/gera_schema_graph.py   # -> docs/context/schema_graph.json
    python3 scripts/build_atlas.py         # -> pages/atlas/ (+ artifact copy)

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
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "pages" / "atlas" / "_page.html"
GRAPH = REPO / "pages" / "atlas" / "schema_graph.json"
SITE = REPO / "pages" / "atlas" / "index.html"
PLACEHOLDER = "__GRAPH_JSON__"


HEAD_EXTRA = """<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Mapa navegável das tabelas do espelho do rodado e das colunas de join que as conectam.">
<link rel="icon" href="/assets/favicon.ico" sizes="any">
<link rel="icon" href="/assets/icon-192.png" type="image/png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
"""


def wrap_document(page: str) -> str:
    """Give the standalone page the document the Artifact runtime would."""
    cut = page.index("</style>") + len("</style>")
    head, body = page[:cut], page[cut:]
    return ("<!doctype html>\n<html lang=\"pt-br\">\n<head>\n"
            + HEAD_EXTRA + head.strip() + "\n</head>\n<body>\n"
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

    SITE.write_text(wrap_document(tpl.replace(PLACEHOLDER, "")))
    print(f"site     {SITE.relative_to(REPO)} "
          f"({SITE.stat().st_size / 1024:.0f} KB + {len(graph) / 1024:.0f} KB de dados)")

    if artifact_out:
        artifact_out.write_text(tpl.replace(PLACEHOLDER, graph))
        print(f"artifact {artifact_out} ({artifact_out.stat().st_size / 1024:.0f} KB, autocontido)")


if __name__ == "__main__":
    out = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else None
    build(out)
