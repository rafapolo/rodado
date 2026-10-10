#!/usr/bin/env python3
"""Regrava a seção "Todos os datasets" de `pages/mcp.html` a partir do catálogo.

    python3 scripts/gera_mcp_datasets.py

Os 43 cards da página destacam ~100 tabelas; o espelho tem 254 datasets. Esta
seção lista todos, um por linha (descrição, tabelas, linhas, fonte), agrupados
pelo tema do atlas, com link para `rodado.xyz/atlas?db=<dataset>`.

Lê `_rodado_metadata/catalog.parquet` (descrição, contagens, fonte) e
`pages/atlas/schema_graph.json` (tema de cada dataset), então roda depois de
`build_metadata_catalog.py` e `gera_schema_graph.py`. Só o trecho entre os
marcadores `<!-- datasets:inicio -->` e `<!-- datasets:fim -->` é gerado; o
resto da página é escrito à mão.
"""
import html
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CATALOGO = RAIZ / "_rodado_metadata" / "catalog.parquet"
GRAFO = RAIZ / "pages" / "atlas" / "schema_graph.json"
PAGINA = RAIZ / "pages" / "mcp.html"
INICIO, FIM = "<!-- datasets:inicio -->", "<!-- datasets:fim -->"


def milhar(n):
    return f"{n:,}".replace(",", ".")


def compacto(n):
    for teto, sufixo in ((1e9, "bi"), (1e6, "mi"), (1e3, "mil")):
        if n >= teto:
            return f"{n / teto:.1f}".replace(".", ",") + f" {sufixo}"
    return str(n)


def main():
    import pyarrow.parquet as pq

    linhas = [r for r in pq.read_table(CATALOGO).to_pylist() if r["source"] != "view_only"]
    grafo = json.loads(GRAFO.read_text())
    tema_de = {d["n"]: d["dom"] for d in grafo["datasets"]}
    rotulo = grafo["domains"]

    ds = defaultdict(lambda: {"desc": "", "tabelas": 0, "linhas": 0, "fontes": Counter()})
    for r in linhas:
        d = ds[r["dataset"]]
        d["desc"] = r["description"] or d["desc"]
        d["tabelas"] += 1
        d["linhas"] += r["rows"] or 0
        d["fontes"][r["source_name"] or ""] += 1

    por_tema = defaultdict(list)
    for nome, d in ds.items():
        por_tema[tema_de.get(nome, "outros")].append((nome, d))

    grupos = []
    for tema in [t for t in rotulo if t in por_tema]:   # ordem do atlas, "outros" por último
        itens = []
        for nome, d in sorted(por_tema[tema]):
            fonte = d["fontes"].most_common(1)[0][0]
            busca = html.escape(f"{nome} {d['desc']} {fonte} {rotulo[tema]}".lower(), quote=True)
            tab = "1 tabela" if d["tabelas"] == 1 else f"{milhar(d['tabelas'])} tabelas"
            itens.append(
                f'            <li class="ds-row" data-search="{busca}">'
                f'<a class="ds-name" href="/atlas/?db={nome}">{nome}</a>'
                f'<span class="ds-desc">{html.escape(d["desc"])}</span>'
                f'<span class="ds-meta">{tab} · {compacto(d["linhas"])} linhas'
                f' · {html.escape(fonte)}</span></li>')
        n_tab = sum(d["tabelas"] for _, d in por_tema[tema])
        grupos.append(
            f'        <details class="ds-group">\n'
            f'          <summary><span class="ds-group-name">{html.escape(rotulo[tema])}</span>'
            f'<span class="ds-group-count">{len(itens)} datasets · {milhar(n_tab)} tabelas</span></summary>\n'
            f'          <ul class="ds-list">\n' + "\n".join(itens) + "\n          </ul>\n"
            f'        </details>')

    proprias = sum(1 for d in ds.values() if d["fontes"].most_common(1)[0][0] != "Base dos Dados")
    bloco = f"""{INICIO}
    <section class="tools-panel datasets-panel" id="datasets">
      <div class="tools-head">
        <span class="card-icon"><i class="fa-solid fa-book"></i></span>
        <h2 class="tools-title">Todos os datasets</h2>
      </div>
      <p class="tools-desc">Os {milhar(len(ds))} datasets que <code>list_datasets()</code> devolve, agrupados por tema: {milhar(len(ds) - proprias)} espelhados do Base dos Dados e {milhar(proprias)} coletados direto na fonte. O nome abre o dataset no <a href="/atlas/">atlas</a>, com as tabelas e as chaves que o ligam aos outros. A busca no topo da página filtra esta lista também.</p>
      <div class="ds-groups">
{chr(10).join(grupos)}
      </div>
      <p class="ds-empty" hidden>Nenhum dataset com esse termo.</p>
    </section>
    {FIM}"""

    pagina = PAGINA.read_text()
    if INICIO not in pagina or FIM not in pagina:
        sys.exit(f"marcadores {INICIO} / {FIM} ausentes em {PAGINA}")
    nova = re.sub(re.escape(INICIO) + r".*?" + re.escape(FIM), lambda _: bloco, pagina, flags=re.S)
    PAGINA.write_text(nova)
    print(f"{PAGINA.relative_to(RAIZ)}: {len(ds)} datasets em {len(grupos)} temas")


if __name__ == "__main__":
    main()
