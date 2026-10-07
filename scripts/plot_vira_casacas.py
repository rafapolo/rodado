#!/usr/bin/env python3
"""Os vira-casacas de 2022 para 2026: as três figuras da análise.

Lê os CSVs de docs/pesquisa/queries/vira_casacas/ (gerados por analise.py e
analise2.py, na mesma pasta) e escreve PNGs em pages/analises/img/vira-casacas-*.png,
no formato das figuras de cancer-mata-interna: matplotlib, 12,4 pol. de largura,
dpi 200, título, subtítulo, leitura e fonte dentro da própria figura.

Paleta: o vermelho de destaque das análises (vira-casaca) e o azul (Lula manteve),
o mesmo par já validado para CVD em plot_dengue_rwd.py.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl

RAIZ = Path(__file__).resolve().parent.parent
Q = RAIZ / "docs" / "pesquisa" / "queries" / "vira_casacas"
OUT = RAIZ / "pages" / "analises" / "img"

SURFACE, FIG_BG = "#fcfcfb", "#f7f7f5"
TXT, TXT2, TXT3 = "#111111", "#555555", "#7b7b76"
RED, BLUE = "#d1453b", "#2a78d6"
RED_L, BLUE_L = "#e8a29c", "#9dc0ec"
GRID, REF = "#e6e6e2", "#b6b6ae"

FONTE_TSE = "TSE · resultados do 1º turno presidencial de 2022 e 2026, por município"


def eixo(ax, grid="y"):
    ax.set_facecolor(SURFACE)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(colors=TXT3, labelsize=11, length=0)
    if grid:
        ax.grid(axis=grid, color=GRID, lw=0.8)
    ax.set_axisbelow(True)


def moldura(fig, titulo, subtitulo, leitura, fonte, topo=0.955):
    fig.text(0.07, topo, titulo, ha="left", va="top", fontsize=23, fontweight="bold", color=TXT)
    fig.text(0.07, topo - 0.043, subtitulo, ha="left", va="top", fontsize=13, color=TXT2)
    fig.text(0.07, topo - 0.080, leitura, ha="left", va="top", fontsize=13, color=TXT, linespacing=1.6)
    fig.text(0.07, 0.015, fonte, ha="left", va="bottom", fontsize=9.5, color=TXT3, linespacing=1.6)


def salva(fig, nome):
    destino = OUT / f"{nome}.png"
    fig.savefig(destino, facecolor=fig.get_facecolor())
    plt.close(fig)
    print("ok:", destino.relative_to(RAIZ))


# --------------------------------------------------------- 1. margens
def margens():
    d = pl.read_csv(Q / "municipios.csv").filter(pl.col("grupo").is_in(["vira", "mantido"]))
    fig = plt.figure(figsize=(12.4, 11.2), dpi=200, facecolor=FIG_BG)
    ax = fig.add_axes((0.09, 0.10, 0.86, 0.66))
    eixo(ax, grid="both")
    for g, cor, rot, z in [("mantido", BLUE, "Lula venceu nas duas (2.661)", 2),
                           ("vira", RED, "Lula em 2022, Flávio em 2026 (703)", 3)]:
        s = d.filter(pl.col("grupo") == g)
        ax.scatter(s["margem22"], s["margem26"], s=10, color=cor, alpha=0.55, lw=0, zorder=z, label=rot)
    ax.axhline(0, color=REF, lw=1.2, zorder=1)
    ax.axvline(10, color=REF, lw=1, ls=(0, (4, 3)), zorder=1)
    ax.text(10.8, -38, "10 p.p.", color=TXT2, fontsize=11, va="bottom")
    ax.text(88, 1.5, "empate em 2026", color=TXT2, fontsize=11, ha="right", va="bottom")
    ax.set_xlim(0, 90); ax.set_ylim(-40, 85)
    ax.set_xlabel("vantagem de Lula sobre Bolsonaro em 2022 (p.p. dos votos válidos)", fontsize=12, color=TXT2)
    ax.set_ylabel("vantagem de Lula sobre Flávio em 2026 (p.p.)", fontsize=12, color=TXT2)
    leg = ax.legend(loc="upper left", frameon=False, fontsize=12, markerscale=2.5, bbox_to_anchor=(0.0, 1.0))
    for t in leg.get_texts():
        t.set_color(TXT)
    moldura(
        fig,
        "Quem virou já estava perto do empate em 2022",
        "Os 3.364 municípios em que Lula venceu o 1º turno de 2022, pela margem de 2022 e pela de 2026",
        "Dois terços dos vira-casacas deram a Lula menos de 10 p.p. de vantagem em 2022 (mediana: 7 p.p.); onde Lula manteve,\n"
        "a mediana era 48 p.p. Em 2026 a virada não foi no fio da navalha: Flávio venceu nesses municípios por 8 p.p. na mediana.\n"
        "Lula perdeu votos em todos eles, em média 8,9 p.p., contra 5,0 p.p. onde manteve a liderança.",
        f"Fonte: {FONTE_TSE}.\nMargem = % de Lula − % do adversário nos votos válidos. Ficam fora 9 empates em 2022 e 7 em 2026 (com uma casa decimal).",
        topo=0.965,
    )
    salva(fig, "vira-casacas-margens")


# --------------------------------------------------------- 2. UF
def por_uf():
    d = (pl.read_csv(Q / "geo_uf.csv").filter(pl.col("lula22") >= 10)
         .sort("taxa"))
    fig = plt.figure(figsize=(12.4, 11.6), dpi=200, facecolor=FIG_BG)
    ax = fig.add_axes((0.09, 0.115, 0.80, 0.66))
    eixo(ax, grid="x")
    y = list(range(d.height))
    ax.barh(y, [t * 100 for t in d["taxa"]], color=RED, height=0.68, edgecolor=SURFACE, lw=2)
    ax.set_yticks(y); ax.set_yticklabels(d["uf"].to_list(), fontsize=11, color=TXT2)
    for i, r in enumerate(d.iter_rows(named=True)):
        ax.text(r["taxa"] * 100 + 1, i, f"{r['vira']} de {r['lula22']}", va="center", fontsize=10.5, color=TXT2)
    ax.set_xlim(0, 100)
    ax.set_xlabel("% dos municípios que Lula venceu em 2022 e Flávio venceu em 2026", fontsize=12, color=TXT2)
    moldura(
        fig,
        "No Sul virou quase tudo; no Nordeste, quase nada",
        "Vira-casacas ÷ municípios em que Lula venceu o 1º turno de 2022, por UF",
        "Santa Catarina (84%), Rio Grande do Sul (76%), Mato Grosso do Sul, Goiás e São Paulo (cerca de 70%)\n"
        "perderam a maior parte dos municípios que Lula tinha. Minas tem o maior número absoluto (175).\n"
        "No Nordeste viraram 15 de 1.779 — Piauí, Pernambuco, Paraíba e Sergipe, nenhum.",
        f"Fonte: {FONTE_TSE}.\nUFs com ao menos 10 municípios vencidos por Lula em 2022 (fora AC e RR, com 4 e 1; em RO e no DF Lula não venceu em nenhum).",
        topo=0.965,
    )
    salva(fig, "vira-casacas-uf")


# --------------------------------------------------------- 3. perfil
ROTULOS = {
    "nbf_share_dom": "famílias no Bolsa Família / domicílios",
    "c22_analfabetismo_15mais": "analfabetismo, 15 anos ou mais",
    "idhm_2010": "IDH municipal (2010)",
    "pib_pc": "PIB per capita",
    "c22_share_branca": "população branca",
    "c22_share_preta": "população preta",
    "pix_ticket_pf": "valor médio do Pix de pessoa física",
    "formalidade": "empregos formais por habitante",
    "credito_ha": "crédito rural por hectare",
    "credito_pc": "crédito rural por habitante",
    "rais_share_publico": "emprego formal no setor público",
    "share_agro": "agropecuária no PIB",
    "rais_sec_C_transformacao": "emprego na indústria de transformação",
    "rais_sec_A_agro": "emprego formal na agropecuária",
    "ideb": "Ideb",
    "log_pop": "população (log)",
}


def perfil():
    t = pl.read_csv(Q / "univariado_robusto.csv").filter(pl.col("indicador").is_in(list(ROTULOS)))
    t = t.sort("rank_biserial")
    fig = plt.figure(figsize=(12.4, 12.0), dpi=200, facecolor=FIG_BG)
    ax = fig.add_axes((0.36, 0.09, 0.58, 0.66))
    eixo(ax, grid="x")
    for i, r in enumerate(t.iter_rows(named=True)):
        fica = bool(r["sobrevive_suporte"])
        cor = RED if fica else REF
        ax.plot([r["rank_biserial"], r["rb_faixa_margem"]], [i, i], color=cor, lw=2, zorder=2)
        ax.scatter([r["rank_biserial"]], [i], s=70, facecolor=SURFACE, edgecolor=cor, lw=2, zorder=3)
        ax.scatter([r["rb_faixa_margem"]], [i], s=70, color=cor, zorder=4, edgecolor=SURFACE, lw=1.5)
    ax.set_yticks(range(t.height))
    ax.set_yticklabels([ROTULOS[x] for x in t["indicador"]], fontsize=11.5, color=TXT)
    for lab, fica in zip(ax.get_yticklabels(), t["sobrevive_suporte"]):
        lab.set_fontweight("bold" if fica else "normal")
    ax.axvline(0, color=REF, lw=1.2, zorder=1)
    ax.set_xlim(-1, 1)
    ax.set_xlabel("← menor nos vira-casacas          diferença (rank-biserial)          maior nos vira-casacas →", fontsize=11.5, color=TXT2)
    ax.scatter([], [], s=70, facecolor=SURFACE, edgecolor=TXT2, lw=2, label="todos os municípios que Lula ganhou em 2022")
    ax.scatter([], [], s=70, color=TXT2, label="só os que Lula ganhou por até 31 p.p. (703 × 649)")
    leg = ax.legend(loc="lower left", bbox_to_anchor=(-0.02, 1.0), ncol=1, frameon=False, fontsize=11)
    for tx in leg.get_texts():
        tx.set_color(TXT)
    moldura(
        fig,
        "Comparados com quem estava igualmente perto, sobra pouco",
        "Vira-casacas × municípios que Lula manteve: todos (vazado) e só os de margem comparável em 2022 (cheio)",
        "Quase tudo encolhe quando a comparação é entre municípios que Lula ganhou por margem parecida. Em vermelho e negrito,\n"
        "o que segue de pé também dentro da mesma UF, com porte, renda, área e margem de 2022 controlados: menos Bolsa Família,\n"
        "mais população branca, crédito rural mais intenso, Pix mais alto e município menor. Emprego público, IDH e PIB per capita não.",
        "Fontes: TSE · eleições 2022 e 2026; IBGE · Censo 2022 e PIB dos municípios; MTE · RAIS 2024; MDS · Bolsa Família;\n"
        "Banco Central · Pix e crédito rural (SICOR); PNUD · IDHM. Rank-biserial vai de −1 a 1; 0 = sem diferença.",
        topo=0.965,
    )
    salva(fig, "vira-casacas-perfil")


if __name__ == "__main__":
    margens()
    por_uf()
    perfil()
