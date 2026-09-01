#!/usr/bin/env python3
"""Grafo societário entre as empresas do levantamento de Nova Friburgo.

Duas empresas ficam ligadas quando dividem um sócio — mesmo documento e mesmo
nome no quadro societário da Receita (o CPF vem mascarado, então documento
sozinho colide entre homônimos; o par documento+nome não).

O desenho mostra só as redes do meio: sai a maior componente e saem as empresas
soltas, que são a maioria (MEI e empresário individual não têm quadro
societário). Cada painel é uma rede; o rótulo da aresta é o sócio que liga.

    python3 scripts/gera_grafo_societario_nf.py            # -> graph.png
    python3 scripts/gera_grafo_societario_nf.py --tudo     # sem tirar a maior
"""

import argparse
import collections
import json
import os
import re
import subprocess
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "pages" / "analises" / "poluentes-do-ar-em-nova-friburgo" / "dados.json"
BEELINK = os.environ.get("BEELINK_HOST", "beelink")

BG, INK, SUAVE, FRACO, RULE, ACC = "#f6f2ea", "#201d18", "#4a443a", "#77705f", "#d9d0bd", "#9c3b2e"
SANS = ["Public Sans", "Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"]
MONO = ["IBM Plex Mono", "Menlo", "DejaVu Sans Mono"]

# ruído de razão social que não ajuda a reconhecer a empresa no rótulo
LIXO = re.compile(
    r"\b(LTDA|ME|EPP|EIRELI|S/?A|SA|INDUSTRIA|INDUSTRIAL|COMERCIO|COMERCIAL|"
    r"SERVICOS|SERVICO|E|DE|DO|DA|DOS|DAS)\b\.?", re.I)


def curto(nome, n=34):
    limpo = re.sub(r"\s+", " ", LIXO.sub(" ", nome)).strip(" .,-")
    # tirar o ruído pode comer a empresa inteira ("C S COMERCIO E SERVICOS" -> "CS")
    if len(limpo) < 5:
        limpo = re.sub(r"\s+", " ", nome).strip()
    return limpo if len(limpo) <= n else limpo[: n - 1].rstrip() + "…"


def coloca(H, semente):
    """Layout fixo para as formas que dominam: par na horizontal, trio em
    triângulo. Spring só quando a rede é maior — assim a grade fica regular e
    o rótulo sempre cai no mesmo lugar."""
    ns = sorted(H.nodes())
    if len(ns) == 2:
        return {ns[0]: (-1.0, 0.0), ns[1]: (1.0, 0.0)}
    if len(ns) == 3:
        return {ns[0]: (-1.0, -0.45), ns[1]: (1.0, -0.45), ns[2]: (0.0, 0.85)}
    return nx.spring_layout(H, seed=semente, k=1.6)


def socios(cnpjs_basicos, ano=2025, mes=9):
    lista = ",".join(f"('{b}')" for b in sorted(cnpjs_basicos))
    sql = f"""SET enable_progress_bar=false;
CREATE OR REPLACE TEMP TABLE alvo AS SELECT b AS bas FROM (VALUES {lista}) t(b);
SELECT s.cnpj_basico, s.nome, s.documento
FROM br_me_cnpj.socios s JOIN alvo a ON s.cnpj_basico = a.bas
WHERE s.ano = {ano} AND s.mes = {mes};"""
    saida = subprocess.run(
        ["ssh", BEELINK, "~/bin/duckdb -readonly -json ~/rodado/basedosdados.duckdb"],
        input=sql, capture_output=True, text=True, check=True).stdout
    return json.loads(saida[saida.index("["):])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", default=str(RAIZ / "graph.png"))
    ap.add_argument("--tudo", action="store_true", help="não descarta a maior rede")
    args = ap.parse_args()

    d = json.loads(DADOS.read_text(encoding="utf-8"))
    nome, sit, cat = {}, {}, {}
    curtos = {"1": "marmorarias", "2": "metalurgia (24)", "2b": "produtos de metal (25)",
              "3": "torrefação de café", "4": "produtos químicos", "5": "olaria e cerâmica",
              "6": "gesso", "7": "gorduras", "8": "extração mineral"}
    for r in d["estab"]:
        b = r[3][:8]
        nome.setdefault(b, r[4]); sit.setdefault(b, r[6]); cat.setdefault(b, r[0])

    quadros = collections.defaultdict(set)
    for r in socios(set(nome)):
        quadros[(r["documento"], r["nome"])].add(r["cnpj_basico"])

    G = nx.Graph()
    for (_doc, nm), emps in quadros.items():
        emps = sorted(emps)
        for i in range(len(emps)):
            for j in range(i + 1, len(emps)):
                G.add_edge(emps[i], emps[j], socio=nm)

    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    maior = comps[0] if comps and not args.tudo else None
    redes = [c for c in comps if len(c) > 1 and c is not maior]

    cols = 6
    rows = -(-len(redes) // cols)
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 3.05, rows * 1.95), dpi=175)
    fig.patch.set_facecolor(BG)
    axes = axes.ravel() if hasattr(axes, "ravel") else [axes]

    for ax in axes:
        ax.set_facecolor(BG); ax.axis("off")

    for k, comp in enumerate(redes):
        ax, H = axes[k], G.subgraph(comp)
        pos = coloca(H, 7 + k)
        for a, b in H.edges():
            ax.plot([pos[a][0], pos[b][0]], [pos[a][1], pos[b][1]],
                    color=ACC, lw=1.4, zorder=1, solid_capstyle="round")
        for a, b, dd in H.edges(data=True):
            mx, my = (pos[a][0] + pos[b][0]) / 2, (pos[a][1] + pos[b][1]) / 2
            partes = dd["socio"].split()
            rot = partes[0].title() + (" " + partes[-1].title() if len(partes) > 1 else "")
            ax.text(mx, my, rot, ha="center", va="center", fontsize=4.6, family=MONO,
                    color=FRACO, zorder=3,
                    bbox=dict(boxstyle="round,pad=0.16", fc=BG, ec="none"))
        for n in H.nodes():
            ativo = sit.get(n) == "Ativa"
            ax.scatter(*pos[n], s=52, zorder=4, linewidths=1.4,
                       facecolor=INK if ativo else BG, edgecolor=INK)
            ax.annotate("\n".join(textwrap.wrap(curto(nome.get(n, n)), 20)),
                        pos[n], textcoords="offset points", xytext=(0, -10),
                        ha="center", va="top", fontsize=5.2, family=SANS,
                        color=INK if ativo else SUAVE, zorder=5,
                        bbox=dict(boxstyle="round,pad=0.12", fc=BG, ec="none"))
        ax.margins(0.30, 0.36)
        atvs = sorted({cat.get(n) for n in H.nodes()} - {None})
        rotulo = " · ".join(dict.fromkeys(curtos.get(a, a) for a in atvs))
        if len(rotulo) > 44:
            rotulo = rotulo[:43].rstrip(" ·") + "…"
        ax.set_title(f"{len(comp)} empresas · {rotulo}", loc="left", pad=3,
                     fontsize=5.4, family=MONO, color=FRACO)

    fig.suptitle("Quem é sócio de quem, entre as empresas do levantamento",
                 x=0.012, y=0.982, ha="left", fontsize=15, family=SANS,
                 fontweight="bold", color=INK)
    fig.text(0.012, 0.944,
             f"{sum(len(c) for c in redes)} empresas em {len(redes)} redes de sociedade cruzada, "
             f"em Nova Friburgo/RJ. Duas empresas se ligam quando dividem um sócio — o nome na "
             f"aresta. Ponto cheio, CNPJ ativo; vazado, baixado ou inapto."
             + ("" if maior is None else
                f"  Fora do desenho: a maior rede ({len(maior)} empresas) e as "
                f"{len([c for c in comps if len(c) == 1]) + len(nome) - len(G)} empresas sem sócio em comum."),
             ha="left", va="top", fontsize=7.4, family=SANS, color=SUAVE)
    fig.text(0.012, 0.012,
             f"Fonte: Receita Federal · quadro societário do CNPJ, {d['meta']['ref_label']}. "
             "rodado.xyz/analises/poluentes-do-ar-em-nova-friburgo/",
             ha="left", fontsize=6.2, family=SANS, color=FRACO)

    fig.subplots_adjust(left=0.008, right=0.992, top=0.905, bottom=0.045,
                        wspace=0.02, hspace=0.22)
    fig.savefig(args.saida, facecolor=BG)
    print(f"{args.saida} — {len(redes)} redes, {sum(len(c) for c in redes)} empresas"
          + ("" if maior is None else f" (maior rede de {len(maior)} fora)"))


if __name__ == "__main__":
    main()
