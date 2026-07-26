#!/usr/bin/env python3
"""Rede societária: sócios de igrejas × associações de defesa de direitos sociais.

Semente: pessoas físicas sócias de pelo menos uma empresa ativa com CNAE 9491000
(igrejas) e de pelo menos uma ativa com CNAE 9430800 (associações de defesa de
direitos sociais) — br_me_cnpj.socios via beelink, snapshot 2025-09,
situacao_cadastral='2' (ativa). Expansão em 2 saltos: empresas dessas pessoas
(hop 1), demais sócios dessas empresas — "sócios de sócios" (hop 2), e as
empresas desses novos sócios (hop 3). Dados extraídos em
scripts/data/rede_igrejas_{pessoas,empresas,arestas}.csv.
"""
import colorsys
import csv
import hashlib

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D

DATA_DIR = "scripts/data"
OUT = "dataviz/rede_societaria_igrejas_associacoes.png"

BG = "#0a0a14"
PESSOA_COLOR = "#9a9aa8"
SEED_EDGE_COLOR = "#f5d67a"

GOLDEN = 0.618033988749895


def cnae_color(code, order):
    """Cor determinística por CNAE: matiz espaçado pela razão áurea segundo a
    ordem alfabética dos códigos (boa dispersão visual mesmo com centenas de
    valores), saturação/valor fixos para contraste no fundo escuro."""
    h = (order.get(code, 0) * GOLDEN) % 1.0
    r, g, b = colorsys.hsv_to_rgb(h, 0.62, 0.95)
    return (r, g, b)


def load():
    with open(f"{DATA_DIR}/rede_igrejas_pessoas.csv") as f:
        pessoas = list(csv.DictReader(f))
    with open(f"{DATA_DIR}/rede_igrejas_empresas.csv") as f:
        empresas = list(csv.DictReader(f))
    with open(f"{DATA_DIR}/rede_igrejas_arestas.csv") as f:
        arestas = list(csv.DictReader(f))
    return pessoas, empresas, arestas


def build_graph(pessoas, empresas, arestas):
    G = nx.Graph()
    for p in pessoas:
        pid = f"P:{p['documento']}|{p['nome']}"
        G.add_node(pid, kind="pessoa", is_seed=p["is_seed"] == "true")
    for e in empresas:
        eid = f"E:{e['cnpj_basico']}"
        G.add_node(
            eid,
            kind="empresa",
            cnae=e["cnae_fiscal_principal"],
            cnae_desc=e["descricao_subclasse"],
            is_seed=e["is_seed"] == "true",
        )
    for a in arestas:
        pid = f"P:{a['documento']}|{a['nome']}"
        eid = f"E:{a['cnpj_basico']}"
        if pid in G and eid in G:
            G.add_edge(pid, eid)
    return G


def layout(G):
    try:
        from fa2_modified import ForceAtlas2

        fa2 = ForceAtlas2(
            outboundAttractionDistribution=True,
            edgeWeightInfluence=1.0,
            jitterTolerance=1.0,
            barnesHutOptimize=True,
            barnesHutTheta=1.2,
            scalingRatio=9.0,
            strongGravityMode=False,
            gravity=0.4,
            adjustSizes=True,
            verbose=True,
        )
        return fa2.forceatlas2_networkx_layout(G, pos=None, iterations=1000)
    except ImportError:
        print("fa2_modified indisponível, usando nx.spring_layout (mais lento)")
        return nx.spring_layout(G, k=None, iterations=50, seed=7)


def main():
    pessoas, empresas, arestas = load()
    G = build_graph(pessoas, empresas, arestas)
    print(f"grafo: {G.number_of_nodes()} nós, {G.number_of_edges()} arestas")

    pos = layout(G)

    empresa_nodes = [n for n, d in G.nodes(data=True) if d["kind"] == "empresa"]
    pessoa_nodes = [n for n, d in G.nodes(data=True) if d["kind"] == "pessoa"]

    cnae_counts = {}
    for n in empresa_nodes:
        c = G.nodes[n]["cnae"]
        cnae_counts[c] = cnae_counts.get(c, 0) + 1
    cnae_order = {c: i for i, c in enumerate(sorted(cnae_counts))}

    top_cnaes = sorted(cnae_counts.items(), key=lambda kv: -kv[1])[:15]

    fig, ax = plt.subplots(figsize=(40, 40), dpi=100)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    # edges
    segs = [(pos[u], pos[v]) for u, v in G.edges()]
    ax.add_collection(LineCollection(segs, colors="#ffffff", alpha=0.15, linewidths=0.5, zorder=1))

    # pessoa nodes (menores, cor neutra)
    px = [pos[n][0] for n in pessoa_nodes]
    py = [pos[n][1] for n in pessoa_nodes]
    ax.scatter(px, py, s=4, c=PESSOA_COLOR, alpha=0.55, linewidths=0, zorder=2)

    # empresa nodes (coloridas por CNAE, tamanho pelo grau)
    ex, ey, ec, es, elw, eec = [], [], [], [], [], []
    for n in empresa_nodes:
        d = G.nodes[n]
        x, y = pos[n]
        ex.append(x)
        ey.append(y)
        ec.append(cnae_color(d["cnae"], cnae_order))
        deg = G.degree[n]
        es.append(18 + 9 * np.sqrt(deg))
        if d["is_seed"]:
            elw.append(1.4)
            eec.append(SEED_EDGE_COLOR)
        else:
            elw.append(0)
            eec.append("none")
    ax.scatter(ex, ey, s=es, c=ec, linewidths=elw, edgecolors=eec, alpha=0.9, zorder=3)

    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.margins(0.03)

    cnae_desc = {e["cnae_fiscal_principal"]: e["descricao_subclasse"] for e in empresas}
    legend_handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=cnae_color(c, cnae_order),
               markersize=14, label=f"{cnae_desc.get(c, c)} ({n})")
        for c, n in top_cnaes
    ]
    legend_handles.append(
        Line2D([0], [0], marker="o", color="none", markerfacecolor=PESSOA_COLOR,
               markersize=9, label="Sócio (pessoa física)")
    )
    legend_handles.append(
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#888888",
               markeredgecolor=SEED_EDGE_COLOR, markeredgewidth=2, markersize=14,
               label="Igreja / associação (ponto de partida)")
    )
    leg = ax.legend(
        handles=legend_handles, loc="upper left", frameon=False, fontsize=15,
        labelcolor="#dddddd", title="CNAEs mais frequentes na rede (nº de empresas) + demais categorias",
        title_fontsize=15,
    )
    leg.get_title().set_color("#dddddd")

    fig.text(0.5, 0.965,
              "Rede societária: sócios de igrejas × associações de defesa de direitos sociais",
              ha="center", fontsize=32, fontweight="bold", color="#f2f2f2")
    fig.text(0.5, 0.945,
              f"{len(pessoa_nodes):,} sócios (pessoa física) · {len(empresa_nodes):,} empresas ativas · "
              f"{G.number_of_edges():,} vínculos societários — expansão em 2 saltos a partir da "
              "interseção CNAE 9491000 × 9430800".replace(",", "."),
              ha="center", fontsize=17, color="#a0a0aa")
    fig.text(0.5, 0.012,
              "Fonte: Receita Federal (CNPJ) via Base dos Dados, snapshot 2025-09, apenas empresas com "
              "situação cadastral ativa · cor = CNAE da empresa (código completo) · "
              "pessoa identificada por documento mascarado + nome",
              ha="center", fontsize=13, color="#6a6a76")

    fig.savefig(OUT, facecolor=fig.get_facecolor())
    print("ok:", OUT)


if __name__ == "__main__":
    main()
