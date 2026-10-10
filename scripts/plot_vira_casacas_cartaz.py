#!/usr/bin/env python3
"""Cartaz-resumo dos vira-casacas: o que os distingue e para onde vai o crédito rural deles.

Lê univariado_robusto.csv e credito_destino.csv de docs/pesquisa/queries/vira_casacas/ e
escreve pages/analises/img/vira-casacas-cartaz.png e -cartaz-escuro.png (retrato, 10,8 × 14,4 pol., dpi 200).
Cores e tipografia são as de plot_vira_casacas.py.
"""
import math
from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl
from matplotlib.patches import Rectangle

from plot_vira_casacas import (BLUE, E_FIG, E_GRID, E_RED, E_SUP, E_TXT, E_TXT2, E_TXT3, FIG_BG,
                               GRID, OUT, Q, RAIZ, RED, RED_L, SURFACE, TXT, TXT2, TXT3)

# o par do tema escuro passa no validador de paleta sobre E_FIG (ΔE 20,9 em protanopia)
TEMAS = {
    "claro": dict(sufixo="", FIG_BG=FIG_BG, SURFACE=SURFACE, TXT=TXT, TXT2=TXT2, TXT3=TXT3, GRID=GRID,
                  RED=RED, BLUE=BLUE, RED_L=RED_L),
    "escuro": dict(sufixo="-escuro", FIG_BG=E_FIG, SURFACE=E_SUP, TXT=E_TXT, TXT2=E_TXT2, TXT3=E_TXT3,
                   GRID=E_GRID, RED=E_RED, BLUE="#4a94e8", RED_L="#8a3d38"),
}

W, H = 108, 144          # a figura em décimos de polegada, y crescendo para baixo
X0 = 7                   # margem esquerda
XB, XB_MAX = 43, 84      # onde as barras começam e até onde a maior vai


def br(v, casas=0):
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(v):
    return f"{br(v * 100)}%"


def reais(v):
    return f"R$ {br(v)}"


def habitantes(v):
    return f"{br(math.exp(v) / 1000)} mil hab."


# indicador, rótulo, explicação, formato — os que resistem à comparação entre municípios parecidos
RESISTEM = [
    ("nbf_share_dom", "Menos Bolsa Família", "famílias no programa, % dos lares", pct),
    ("c22_share_branca", "Mais moradores brancos", "% da população, Censo 2022", pct),
    ("credito_ha", "Agro com mais crédito", "crédito rural por hectare de imóvel rural", reais),
    ("pix_ticket_pf", "Pix de valor mais alto", "valor médio de um Pix de pessoa física", reais),
    ("log_pop", "Municípios menores", "população", habitantes),
]
SOMEM = ("PIB por morador mais alto  ·  agro pesando mais na economia  ·  mais emprego privado que público\n"
         "mais crédito rural por morador (por pouco)  ·  mais homens que mulheres")


def secao(ax, y, titulo, nota):
    ax.plot([X0, W - X0], [y - 3.2, y - 3.2], color=GRID, lw=1.2)
    ax.text(X0, y, titulo, fontsize=17, fontweight="bold", color=TXT, va="top")
    ax.text(X0, y + 3.6, nota, fontsize=11, color=TXT2, va="top")


def cartaz(tema="claro"):
    global FIG_BG, SURFACE, TXT, TXT2, TXT3, GRID, RED, BLUE, RED_L
    t = TEMAS[tema]
    FIG_BG, SURFACE, TXT, TXT2, TXT3 = t["FIG_BG"], t["SURFACE"], t["TXT"], t["TXT2"], t["TXT3"]
    GRID, RED, BLUE, RED_L = t["GRID"], t["RED"], t["BLUE"], t["RED_L"]
    u = {r["indicador"]: r for r in pl.read_csv(Q / "univariado_robusto.csv").iter_rows(named=True)}
    c = pl.read_csv(Q / "credito_destino.csv").filter(pl.col("grupo") == "vira")
    total = c["valor"].sum()
    destinos = c.filter(pl.col("destino") != "Outros").sort("fatia", descending=True)
    outros = c.filter(pl.col("destino") == "Outros")["fatia"][0]

    fig = plt.figure(figsize=(W / 10, H / 10), dpi=200, facecolor=FIG_BG)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, W); ax.set_ylim(H, 0); ax.axis("off")

    ax.text(X0, 5, "ELEIÇÕES 2026  ·  1º TURNO PRESIDENCIAL", fontsize=10.5, color=TXT3, va="top")
    ax.text(X0, 8.3, "O que define um\nmunicípio vira-casaca", fontsize=37, fontweight="bold", color=TXT,
            va="top", linespacing=1.12)
    ax.text(X0, 22,
            "703 municípios deram a vitória a Lula em 2022 e a Flávio Bolsonaro em 2026.\n"
            "Comparados em 155 indicadores com os 2.661 que Lula manteve, poucos traços os separam.",
            fontsize=13, color=TXT2, va="top", linespacing=1.5)

    # ---- 1. o que resiste
    secao(ax, 33, "O que continua diferente entre municípios parecidos",
          "mesmo estado, mesmo porte e mesma vantagem de Lula em 2022  ·  valor do município mediano de cada grupo")
    for x, cor, rot in [(XB, RED, "vira-casacas"), (XB + 19, BLUE, "Lula manteve")]:
        ax.add_patch(Rectangle((x, 41.8), 2.2, 1.5, color=cor, lw=0))
        ax.text(x + 3.1, 42.55, rot, fontsize=11.5, color=TXT, va="center")
    y = 47
    for ind, rot, explica, fmt in RESISTEM:
        a, b = u[ind]["mediana_vira"], u[ind]["mediana_mantido"]
        if ind == "log_pop":
            va_, vb_ = math.exp(a), math.exp(b)
        else:
            va_, vb_ = a, b
        esc = (XB_MAX - XB) / max(va_, vb_)
        ax.text(X0, y + 0.2, rot, fontsize=14.5, fontweight="bold", color=TXT, va="top")
        ax.text(X0, y + 3.3, explica, fontsize=10.5, color=TXT2, va="top")
        for k, (v, bruto, cor) in enumerate([(va_, a, RED), (vb_, b, BLUE)]):
            yb = y + 0.3 + k * 2.75
            ax.add_patch(Rectangle((XB, yb), v * esc, 2.3, color=cor, lw=0))
            ax.text(XB + v * esc + 1.2, yb + 1.15, fmt(bruto), fontsize=12.5, color=TXT, va="center",
                    fontweight="bold" if k == 0 else "normal")
        y += 8.0

    # ---- 2. crédito rural
    secao(ax, 91.5, "Para onde vai o crédito rural dos vira-casacas",
          f"% do valor contratado de 2020 a 2024 nos 703 municípios (R$ {br(total / 1e9)} bilhões)")
    esc = (XB_MAX - XB) / destinos["fatia"][0]
    y = 100.3
    for r in destinos.iter_rows(named=True):
        ax.text(XB - 1.8, y + 1.25, r["destino"], fontsize=12.5, color=TXT, va="center", ha="right")
        ax.add_patch(Rectangle((XB, y), r["fatia"] * esc, 2.5, color=RED, lw=0))
        rotulo = f"{br(r['fatia'] * 100)}%"
        if r["fatia_trator"]:
            ax.add_patch(Rectangle((XB, y), r["fatia_trator"] * esc, 2.5, color=RED_L, lw=0))
            ax.plot([XB + r["fatia_trator"] * esc] * 2, [y, y + 2.5], color=FIG_BG, lw=1.6)
            rotulo += f"   (tratores: {br(r['fatia_trator'] * 100)}%)"
        ax.text(XB + r["fatia"] * esc + 1.2, y + 1.25, rotulo, fontsize=12.5, color=TXT, va="center")
        y += 3.55
    ax.text(XB, y + 0.3, f"Os outros {br(outros * 100)}% se dividem entre dezenas de produtos e benfeitorias.",
            fontsize=10.5, color=TXT2, va="top")

    # ---- 3. o que some
    ax.plot([X0, W - X0], [y + 4.3, y + 4.3], color=GRID, lw=1.2)
    ax.text(X0, y + 6, "Parece diferença, mas some quando se comparam municípios parecidos",
            fontsize=12.5, fontweight="bold", color=TXT, va="top")
    ax.text(X0, y + 9, SOMEM, fontsize=11, color=TXT2, va="top", linespacing=1.55)

    ax.text(X0, H - 3.2,
            "Fontes: TSE (resultados de 2022 e 2026) · CGU (Bolsa Família, julho de 2026) · IBGE (Censo 2022 e população) ·\n"
            "Banco Central (crédito rural 2020–2024 e Pix 2025) · Serviço Florestal Brasileiro (área dos imóveis no CAR).",
            fontsize=9, color=TXT3, va="bottom", linespacing=1.55)

    destino = OUT / f"vira-casacas-cartaz{t['sufixo']}.png"
    fig.savefig(destino, facecolor=fig.get_facecolor())
    plt.close(fig)
    print("ok:", destino.relative_to(RAIZ))


if __name__ == "__main__":
    cartaz("claro")
    cartaz("escuro")
