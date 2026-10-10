#!/usr/bin/env python3
"""Os vira-casacas de 2022 para 2026: as três figuras da análise.

Lê os CSVs de docs/pesquisa/queries/vira_casacas/ (gerados por analise.py e
analise2.py, na mesma pasta) e escreve PNGs em pages/analises/img/vira-casacas-*.png,
no formato das figuras de cancer-mata-interna: matplotlib, 12,4 pol. de largura,
dpi 200, título, subtítulo, leitura e fonte dentro da própria figura.

Paleta: o vermelho de destaque das análises (vira-casaca) e o azul (Lula manteve),
o mesmo par já validado para CVD em plot_dengue_rwd.py.
"""
import math
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.transforms as transforms
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
# Rótulos e números para quem não acompanha eleição: nada de siglas nem de termos de estatística.
ROTULOS = {
    "nbf_share_dom": "Famílias no Bolsa Família (% dos lares)",
    "c22_analfabetismo_15mais": "Analfabetismo (15 anos ou mais)",
    "idhm_2010": "Qualidade de vida (IDH)",
    "pib_pc": "PIB por morador",
    "c22_share_branca": "Moradores brancos",
    "c22_share_preta": "Moradores pretos",
    "pix_ticket_pf": "Valor médio de um Pix",
    "formalidade": "Empregos com carteira a cada 100 moradores",
    "credito_ha": "Crédito rural por hectare",
    "credito_pc": "Crédito rural por morador",
    "rais_share_publico": "Empregos com carteira no setor público",
    "share_agro": "Peso do agro na economia local",
    "rais_sec_C_transformacao": "Empregos com carteira na indústria",
    "rais_sec_A_agro": "Empregos com carteira no agro",
    "ideb": "Nota das escolas (Ideb)",
    "log_pop": "Número de moradores",
}


def _br(v, casas=0):
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _pct(casas):
    return lambda v: f"{_br(v * 100, casas)}%"


def _reais(v):
    return rf"R\$ {_br(v / 1000, 1).removesuffix(',0')} mil" if v >= 1000 else rf"R\$ {_br(v)}"


# como escrever o valor típico (mediana) de cada indicador
MEDIANA = {
    "nbf_share_dom": _pct(0), "rais_share_publico": _pct(0), "share_agro": _pct(0),
    "c22_analfabetismo_15mais": _pct(1), "c22_share_branca": _pct(1), "c22_share_preta": _pct(1),
    "rais_sec_C_transformacao": _pct(1), "rais_sec_A_agro": _pct(1),
    "idhm_2010": lambda v: _br(v, 2), "ideb": lambda v: _br(v, 1), "formalidade": lambda v: _br(v * 100),
    "pib_pc": _reais, "pix_ticket_pf": _reais, "credito_ha": _reais, "credito_pc": _reais,
    "log_pop": lambda v: f"{_br(math.exp(v) / 1000)} mil",
}

# tema escuro, só desta figura: os mesmos papéis de cor das outras, escolhidos para o fundo escuro
E_FIG, E_SUP = "#121211", "#1a1a19"
E_TXT, E_TXT2, E_TXT3 = "#f3f3ef", "#b8b8b1", "#8b8b84"
E_RED, E_CINZA = "#e5645a", "#9c9c95"
E_GRID, E_REF = "#2b2b29", "#5c5c57"


def perfil():
    t = pl.read_csv(Q / "univariado_robusto.csv").filter(pl.col("indicador").is_in(list(ROTULOS)))
    fica = t.filter(pl.col("sobrevive_suporte")).sort("rank_biserial", descending=True)
    some = t.filter(~pl.col("sobrevive_suporte")).sort("rank_biserial", descending=True)

    ALT, LINHA = 13.45, 0.37                      # polegadas: altura da figura e de cada linha
    fig = plt.figure(figsize=(12.4, ALT), dpi=200, facecolor=E_FIG)
    y = lambda pol: 1 - pol / ALT                # polegadas a partir do topo -> fração da figura
    XV1, XV2, X0, LARG = 0.465, 0.59, 0.625, 0.325   # colunas: valor de cada grupo e a barra

    fig.text(0.07, y(0.45), "O que os municípios vira-casacas têm de diferente",
             ha="left", va="top", fontsize=23, fontweight="bold", color=E_TXT)
    fig.text(0.07, y(1.02),
             "Vira-casaca é o município em que Lula foi o mais votado para presidente em 2022 e, em 2026, o mais votado foi Flávio\n"
             "Bolsonaro. São 703. Para descobrir o que eles têm de diferente, cada linha abaixo os compara com os 2.661 municípios\n"
             "em que Lula foi o mais votado nas duas eleições.",
             ha="left", va="top", fontsize=13, color=E_TXT, linespacing=1.6)
    fig.text(0.07, y(2.12),
             "Como ler: os dois números são o valor de um município típico de cada grupo. A barra resume a diferença: para a\n"
             "direita, os vira-casacas têm mais daquilo; para a esquerda, têm menos. Quanto mais comprida a barra, maior a diferença.",
             ha="left", va="top", fontsize=13, color=E_TXT2, linespacing=1.6)

    def bloco(d, topo, cor, titulo, explica, ultimo):
        n = d.height
        ax = fig.add_axes((X0, y(topo + n * LINHA), LARG, n * LINHA / ALT))
        ax.set_facecolor(E_SUP)
        for sp in ax.spines.values():
            sp.set_visible(False)
        na_fig = transforms.blended_transform_factory(fig.transFigure, ax.transData)
        for i, r in enumerate(d.iter_rows(named=True)):
            ax.barh(i, r["rank_biserial"], height=0.5, color=cor, zorder=3)
            f = MEDIANA[r["indicador"]]
            ax.text(0.07, i, ROTULOS[r["indicador"]], va="center", ha="left", fontsize=11.5, color=E_TXT, transform=na_fig)
            ax.text(XV1, i, f(r["mediana_vira"]), va="center", ha="right", fontsize=11.5, color=E_TXT, transform=na_fig)
            ax.text(XV2, i, f(r["mediana_mantido"]), va="center", ha="right", fontsize=11.5, color=E_TXT, transform=na_fig)
            if i:                                    # fio entre as linhas, para o olho ir do nome à barra
                ax.plot([0.07, X0 + LARG], [i - 0.5, i - 0.5], color=E_GRID, lw=0.8, transform=na_fig, clip_on=False, zorder=1)
            if r["indicador"] == "credito_pc":       # o único que fica na beira do corte
                ax.text(-0.05, i, "por pouco não continua", va="center", ha="right", fontsize=9.5, color=E_TXT3)
        ax.axvline(0, color=E_REF, lw=1.2, zorder=2)
        ax.set_xlim(-1, 1); ax.set_ylim(n - 0.5, -0.5)
        ax.set_yticks([])
        ax.set_xticks([-1, 0, 1])
        ax.set_xticklabels(["muito menos", "igual", "muito mais"] if ultimo else [])
        ax.tick_params(colors=E_TXT3, labelsize=10.5, length=0, pad=8)
        for rot, lado in zip(ax.get_xticklabels(), ["left", "center", "right"]):
            rot.set_ha(lado)
        fig.text(0.07, y(topo - (1.20 if not ultimo else 0.92)), titulo, ha="left", va="top", fontsize=13.5, fontweight="bold", color=E_TXT)
        fig.text(0.07, y(topo - (0.90 if not ultimo else 0.62)), explica, ha="left", va="top", fontsize=11, color=E_TXT2, linespacing=1.5)
        return ax

    T1 = 4.35
    bloco(fica, T1, E_RED, f"Diferenças que continuam entre municípios parecidos ({fica.height})",
          "Valem mesmo quando a comparação é só entre municípios do mesmo estado, com tamanho e riqueza semelhantes\n"
          "e onde Lula tinha vencido em 2022 com uma vantagem parecida. São as que dizem algo sobre quem virou.", False)
    T2 = T1 + fica.height * LINHA + 1.30
    bloco(some, T2, E_CINZA, f"Diferenças que somem entre municípios parecidos ({some.height})",
          "Existem no país inteiro, mas não entre vizinhos semelhantes. Refletem sobretudo a região: quase todos os vira-casacas\n"
          "ficam no Sul, no Centro-Oeste e no interior de SP e MG, onde a renda e a escolaridade já são mais altas.", True)

    # cabeçalho das colunas, uma vez só, sobre o primeiro bloco
    cab = y(T1 - 0.08)
    fig.text(XV1, cab, "vira-casacas", ha="right", va="bottom", fontsize=10.5, color=E_TXT2)
    fig.text(XV2, cab, "ficaram com Lula", ha="right", va="bottom", fontsize=10.5, color=E_TXT2)
    fig.text(X0, cab, "← vira-casacas têm menos", ha="left", va="bottom", fontsize=10.5, color=E_TXT2)
    fig.text(X0 + LARG, cab, "têm mais →", ha="right", va="bottom", fontsize=10.5, color=E_TXT2)

    fig.text(0.07, 0.015,
             "Para quem quer o detalhe: os números são medianas. O comprimento da barra é o rank-biserial, de −1 a +1: em +0,5, sorteando um município de cada grupo,\n"
             "o vira-casaca tem o valor maior em 75% das vezes. O teste de “municípios parecidos” é uma regressão com os 703 vira-casacas e os 649 que ficaram com Lula\n"
             "depois de lhe darem até 31 pontos percentuais de vantagem em 2022, com estado, faixas de 2,5 pontos dessa vantagem, população, PIB por morador e área;\n"
             "correção de Benjamini-Hochberg a 5%. Foram testados 155 indicadores e 10 passaram; aqui estão 16 dos 155, entre eles seis dos aprovados.\n"
             "Fontes: TSE · eleições 2022 e 2026; IBGE · Censo 2022 e PIB dos municípios; MTE · RAIS 2024; MDS · Bolsa Família; Banco Central · Pix e crédito rural (SICOR); PNUD · IDHM.",
             ha="left", va="bottom", fontsize=9.5, color=E_TXT3, linespacing=1.6)
    salva(fig, "vira-casacas-perfil")


if __name__ == "__main__":
    margens()
    por_uf()
    perfil()
