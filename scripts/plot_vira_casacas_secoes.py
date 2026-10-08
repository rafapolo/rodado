#!/usr/bin/env python3
"""Vira-casacas por seção eleitoral: as duas figuras da seção 6 da análise.

Lê os JSONs por UF do mapa de eleições (xyz/dataviz/eleicoes/secoes/<UF>.json; cada
seção é [secao, v1..v12, l22, b22], candidatos na ordem de locais.json["c"]: 0 = Flávio,
1 = Lula; l22/b22 = % de Lula/Bolsonaro em 2022 x 100, nulo se a seção não é comparável)
e escreve pages/analises/img/vira-casacas-secoes-{recortes,distribuicao}.png.

Regra do mapa: vira-casaca = Lula à frente em 2022 e Flávio à frente em 2026.
Recortes por zona e por local de votação usam a soma dos votos das suas seções comparáveis.
Mesmo estilo de plot_vira_casacas.py (matplotlib, 12,4 pol., dpi 200, título/leitura/fonte na figura).
"""
import json
from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl

RAIZ = Path(__file__).resolve().parent.parent
SECOES = Path.home() / "Projetos" / "xyz" / "dataviz" / "eleicoes" / "secoes"
OUT = RAIZ / "pages" / "analises" / "img"

SURFACE, FIG_BG = "#fcfcfb", "#f7f7f5"
TXT, TXT2, TXT3 = "#111111", "#555555", "#7b7b76"
RED, BLUE = "#d1453b", "#2a78d6"
GRID, REF = "#e6e6e2", "#b6b6ae"
FONTE = "TSE · resultados do 1º turno presidencial de 2022 e 2026, por seção eleitoral (mapa de eleições)"


def br(v, casas=0):
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def carrega():
    meta = json.loads((SECOES / "locais.json").read_text())
    linhas = []
    for uf in meta["ufs"]:
        for loc in json.loads((SECOES / f"{uf}.json").read_text()):
            zona, local, mun = loc[0], loc[1], loc[2]  # arquivo: [zona, local, município, nome, seções]
            for s in loc[4]:
                linhas.append((uf, mun, zona, local, s[1], s[2], s[13], s[14]))
    return pl.DataFrame(linhas, orient="row", schema=["uf", "mun", "zona", "local", "flavio", "lula", "l22", "b22"],
                        infer_schema_length=None)


def prepara():
    d = carrega().with_columns(
        comp=pl.col("l22").is_not_null(),
        vira=(pl.col("l22") > pl.col("b22")) & (pl.col("flavio") > pl.col("lula")),
        inversa=(pl.col("b22") > pl.col("l22")) & (pl.col("lula") > pl.col("flavio")),
    )
    return d


def eixo(ax, grid):
    ax.set_facecolor(SURFACE)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(colors=TXT3, labelsize=11, length=0)
    ax.grid(axis=grid, color=GRID, lw=0.8)
    ax.set_axisbelow(True)


def moldura(fig, titulo, subtitulo, leitura, fonte, topo=0.965):
    fig.text(0.07, topo, titulo, ha="left", va="top", fontsize=23, fontweight="bold", color=TXT)
    fig.text(0.07, topo - 0.05, subtitulo, ha="left", va="top", fontsize=13, color=TXT2)
    fig.text(0.07, topo - 0.095, leitura, ha="left", va="top", fontsize=13, color=TXT, linespacing=1.6)
    fig.text(0.07, 0.015, fonte, ha="left", va="bottom", fontsize=9.5, color=TXT3, linespacing=1.6)


def salva(fig, nome):
    destino = OUT / f"{nome}.png"
    fig.savefig(destino, facecolor=fig.get_facecolor())
    plt.close(fig)
    print("ok:", destino.relative_to(RAIZ))


# Recortes já apurados (os de município, zona e local vêm do mapa de eleições: a unidade
# vira se Lula liderava em 2022 e Flávio lidera em 2026 na soma dos votos da unidade).
RECORTES = [("municípios", 703, 5571), ("zonas eleitorais", 737, 6034),
            ("locais de votação", 6211, 68701), ("seções eleitorais", 37136, 412405)]


def fig_recortes(d):
    c = d.filter(pl.col("comp"))
    assert (c["vira"].sum(), c.height) == (RECORTES[3][1], RECORTES[3][2])
    fig = plt.figure(figsize=(12.4, 8.0), dpi=200, facecolor=FIG_BG)
    ax = fig.add_axes((0.20, 0.17, 0.72, 0.52))
    eixo(ax, "x")
    n = len(RECORTES)
    for i, (nome, v, t) in enumerate(RECORTES):
        pct = v / t * 100
        ax.barh(n - 1 - i, pct, height=0.62, color=RED, edgecolor=SURFACE, lw=2)
        ax.text(pct + 0.25, n - 1 - i, f"{br(pct, 1)}%  ({br(v)} de {br(t)})", va="center", fontsize=11.5, color=TXT)
    ax.set_yticks(range(n)); ax.set_yticklabels([r[0] for r in RECORTES][::-1], fontsize=12, color=TXT2)
    ax.set_xlim(0, 20)
    ax.set_xticks([0, 5, 10, 15, 20]); ax.set_xticklabels(["0%", "5%", "10%", "15%", "20%"])
    ax.set_xlabel("% das unidades em que Lula liderava em 2022 e Flávio lidera em 2026", fontsize=12, color=TXT2)
    moldura(
        fig,
        "Quanto menor o recorte, menos vira, mas sempre vira alguém",
        "Vira-casacas ÷ unidades, em quatro recortes do mesmo 1º turno",
        "No agregado municipal viraram 703 dos 5.571 municípios (12,6%). Por seção, 37.136 das 412.405 que dá para\n"
        "comparar com 2022 (9,0%). Essas seções estão em 2.824 municípios, 50,7% do total, quatro vezes o que o mapa\n"
        "municipal mostra, porque num município que não virou ainda há seção que virou. O caminho inverso (Flávio em 2022,\n"
        "Lula em 2026) existe: 2.869 seções, em 327 municípios.",
        f"Fonte: {FONTE}.\nSeção comparável: o TSE renumera e remaneja urnas, e 412.405 das 497.897 seções de 2026 têm correspondente em 2022.",
        topo=0.965,
    )
    salva(fig, "vira-casacas-secoes-recortes")


FAIXAS = [("nenhuma seção virou", lambda f: f == 0),
          ("até 10%", lambda f: (f > 0) & (f <= .10)),
          ("de 10% a 25%", lambda f: (f > .10) & (f <= .25)),
          ("de 25% a 50%", lambda f: (f > .25) & (f <= .50)),
          ("mais da metade", lambda f: f > .50)]


def fig_distribuicao(d):
    m = (d.filter(pl.col("comp")).group_by("uf", "mun")
         .agg(n=pl.len(), v=pl.col("vira").sum()).with_columns(f=pl.col("v") / pl.col("n")))
    total = m.height
    fig = plt.figure(figsize=(12.4, 8.2), dpi=200, facecolor=FIG_BG)
    ax = fig.add_axes((0.20, 0.16, 0.72, 0.52))
    eixo(ax, "x")
    k = len(FAIXAS)
    qtd = [m.filter(fx(pl.col("f"))).height for _, fx in FAIXAS]
    assert sum(qtd) == total
    for i, (q, (nome, _)) in enumerate(zip(qtd, FAIXAS)):
        ax.barh(k - 1 - i, q, height=0.62, color=BLUE if i == 0 else RED, edgecolor=SURFACE, lw=2)
        ax.text(q + 30, k - 1 - i, f"{br(q)}  ({br(q / total * 100, 1)}%)", va="center", fontsize=11.5, color=TXT)
    ax.set_yticks(range(k)); ax.set_yticklabels([f[0] for f in FAIXAS][::-1], fontsize=12, color=TXT2)
    ax.set_xlim(0, 3300)
    ax.set_xticks([0, 1000, 2000, 3000]); ax.set_xticklabels(["0", "1.000", "2.000", "3.000"])
    ax.set_xlabel(f"número de municípios (dos {br(total)} com ao menos uma seção comparável)", fontsize=12, color=TXT2)
    mais0, mais10, mais25, mais50 = (m.filter(pl.col("f") > x).height for x in (0, .10, .25, .50))
    moldura(
        fig,
        "Alguma seção virou em metade dos municípios",
        "Municípios por fatia das suas seções comparáveis que viraram de Lula (2022) para Flávio (2026)",
        f"{br(mais0)} municípios ({br(mais0 / total * 100, 1)}%) têm ao menos uma seção vira-casaca, mas um município tem em média\n"
        f"89 seções, então \"basta uma\" é critério frouxo. Passam de 10% das seções {br(mais10)} ({br(mais10 / total * 100, 1)}%), de 25%\n"
        f"{br(mais25)} ({br(mais25 / total * 100, 1)}%) e de 50% {br(mais50)} ({br(mais50 / total * 100, 1)}%), na maioria municípios pequenos (mediana de 14 seções).",
        f"Fonte: {FONTE}.\nFatia = seções com Lula na frente em 2022 e Flávio na frente em 2026 ÷ seções do município com correspondente em 2022. Azul: nenhuma; vermelho: ao menos uma.",
        topo=0.965,
    )
    salva(fig, "vira-casacas-secoes-distribuicao")


def main():
    d = prepara()
    fig_recortes(d)
    fig_distribuicao(d)


if __name__ == "__main__":
    main()
