#!/usr/bin/env python3
"""Regrava a seção "Todos os datasets" de `pages/mcp.html` e `pages/mcp-en.html` a partir do catálogo.

    python3 scripts/gera_mcp_datasets.py

Os 43 cards da página destacam ~100 tabelas; o espelho tem 256 datasets. Esta
seção lista todos, um por linha (descrição, tabelas, linhas, fonte), agrupados
pelo tema do atlas, com link para `rodado.xyz/atlas?db=<dataset>`.

Lê `_rodado_metadata/catalog.parquet` (descrição, contagens, fonte) e
`pages/atlas/schema_graph.json` (tema de cada dataset), então roda depois de
`build_metadata_catalog.py` e `gera_schema_graph.py`. Só o trecho entre os
marcadores `<!-- datasets:inicio -->` e `<!-- datasets:fim -->` é gerado; o
resto da página é escrito à mão. Na página em inglês os rótulos e os temas saem em
inglês; a descrição de cada dataset fica como está no catálogo, em português.
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
INICIO, FIM = "<!-- datasets:inicio -->", "<!-- datasets:fim -->"
TEMAS_EN = {"governo": "Government and Public Finance", "economia": "Economy", "educacao": "Education",
            "seguranca": "Security, Crime, Violence and Conflict", "saude": "Health", "meio_ambiente": "Environment",
            "infraestrutura": "Infrastructure and Transport", "politica": "Politics", "populacao": "Population",
            "territorio": "Territorial Organization", "cultura_arte": "Culture and Arts", "outros": "Other"}
IDIOMAS = {
    "pt": {"pagina": RAIZ / "pages" / "mcp.html", "sep": ".", "dec": ",", "sufixos": ("bi", "mi", "mil"),
           "tabela": ("tabela", "tabelas"), "linhas": "linhas", "titulo": "Todos os datasets",
           "desc": "Os {n} datasets que <code>list_datasets()</code> devolve, agrupados por tema: {bd} espelhados do "
                   "Base dos Dados e {pr} coletados direto na fonte. O nome abre o dataset no "
                   "<a href=\"/atlas/\">atlas</a>, com as tabelas e as chaves que o ligam aos outros. "
                   "A busca no topo da página filtra esta lista também.",
           "vazio": "Nenhum dataset com esse termo."},
    "en": {"pagina": RAIZ / "pages" / "mcp-en.html", "sep": ",", "dec": ".", "sufixos": ("bn", "M", "k"),
           "tabela": ("table", "tables"), "linhas": "rows", "titulo": "All datasets",
           "desc": "The {n} datasets returned by <code>list_datasets()</code>, grouped by theme: {bd} mirrored from "
                   "Base dos Dados and {pr} collected straight from the source. The name opens the dataset in the "
                   "<a href=\"/atlas/\">atlas</a>, with its tables and the keys that link it to the others. "
                   "The search box at the top of the page filters this list too. "
                   "Descriptions are in Portuguese, as in the catalog.",
           "vazio": "No dataset matches that term."},
}


def milhar(n, sep="."):
    return f"{n:,}".replace(",", sep)


def compacto(n, L):
    for teto, sufixo in zip((1e9, 1e6, 1e3), L["sufixos"]):
        if n >= teto:
            return f"{n / teto:.1f}".replace(".", L["dec"]) + f" {sufixo}"
    return str(n)


def bloco(ds, por_tema, rotulo, L):
    grupos = []
    for tema in [t for t in rotulo if t in por_tema]:   # ordem do atlas, "outros" por último
        itens = []
        for nome, d in sorted(por_tema[tema]):
            fonte = d["fontes"].most_common(1)[0][0]
            busca = html.escape(f"{nome} {d['desc']} {fonte} {rotulo[tema]}".lower(), quote=True)
            tab = f"{milhar(d['tabelas'], L['sep'])} {L['tabela'][d['tabelas'] != 1]}"
            itens.append(
                f'            <li class="ds-row" data-search="{busca}">'
                f'<a class="ds-name" href="/atlas/?db={nome}">{nome}</a>'
                f'<span class="ds-desc">{html.escape(d["desc"])}</span>'
                f'<span class="ds-meta">{tab} · {compacto(d["linhas"], L)} {L["linhas"]}'
                f' · {html.escape(fonte)}</span></li>')
        n_tab = sum(d["tabelas"] for _, d in por_tema[tema])
        grupos.append(
            f'        <details class="ds-group">\n'
            f'          <summary><span class="ds-group-name">{html.escape(rotulo[tema])}</span>'
            f'<span class="ds-group-count">{len(itens)} datasets · {milhar(n_tab, L["sep"])} {L["tabela"][1]}</span></summary>\n'
            f'          <ul class="ds-list">\n' + "\n".join(itens) + "\n          </ul>\n"
            f'        </details>')
    proprias = sum(1 for d in ds.values() if d["fontes"].most_common(1)[0][0] != "Base dos Dados")
    desc = L["desc"].format(n=milhar(len(ds), L["sep"]), bd=milhar(len(ds) - proprias, L["sep"]), pr=milhar(proprias, L["sep"]))
    return f"""{INICIO}
    <section class="tools-panel datasets-panel" id="datasets">
      <div class="tools-head">
        <span class="card-icon"><i class="fa-solid fa-book"></i></span>
        <h2 class="tools-title">{L["titulo"]}</h2>
      </div>
      <p class="tools-desc">{desc}</p>
      <div class="ds-groups">
{chr(10).join(grupos)}
      </div>
      <p class="ds-empty" hidden>{L["vazio"]}</p>
    </section>
    {FIM}""", len(grupos)


def main():
    import pyarrow.parquet as pq

    linhas = [r for r in pq.read_table(CATALOGO).to_pylist() if r["source"] != "view_only"]
    grafo = json.loads(GRAFO.read_text())
    tema_de = {d["n"]: d["dom"] for d in grafo["datasets"]}

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

    for idioma, L in IDIOMAS.items():
        rotulo = grafo["domains"] if idioma == "pt" else {t: TEMAS_EN.get(t, r) for t, r in grafo["domains"].items()}
        novo, n_grupos = bloco(ds, por_tema, rotulo, L)
        pagina = L["pagina"].read_text()
        if INICIO not in pagina or FIM not in pagina:
            sys.exit(f"marcadores {INICIO} / {FIM} ausentes em {L['pagina']}")
        L["pagina"].write_text(re.sub(re.escape(INICIO) + r".*?" + re.escape(FIM), lambda _: novo, pagina, flags=re.S))
        print(f"{L['pagina'].relative_to(RAIZ)}: {len(ds)} datasets em {n_grupos} temas")


if __name__ == "__main__":
    main()
