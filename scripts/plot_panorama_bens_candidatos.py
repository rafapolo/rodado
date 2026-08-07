#!/usr/bin/env python3
"""Panorama do painel de bens: patrimônio declarado × múltiplo do subsídio.

Versão estática da tela de abertura do painel interativo, para abrir a página
da análise. Cada ponto é uma pessoa já eleita deputado federal desde 2010,
posicionada pelo que declara hoje e por quanto o patrimônio dela cresceu em
relação ao subsídio que o cargo pagou no período.

  eixo x   patrimônio total do registro mais recente, escala log — a amplitude
           vai de zero a dezenas de milhões e não cabe em escala linear.
  eixo y   crescimento declarado dividido pelo subsídio bruto acumulado entre
           a primeira e a última declaração. 1× = cresceu exatamente o que o
           cargo pagou.
  cor      espectro do partido do último registro.
  tamanho  número de empresas em que consta como sócio ou titular.

Régua mínima: quem passou poucos meses em mandato federal dentro da janela
entre duas declarações acumula uma régua ínfima, e a divisão devolve múltiplos
sem sentido. Abaixo de ~12 meses de subsídio acumulado a pessoa sai do gráfico
e entra na contagem de "sem régua comparável".

Lê o JSON gerado por scripts/extrai_patrimonio_deputados.py.

Uso:
  python3 scripts/extrai_patrimonio_deputados.py --saida /tmp/patrimonio.json
  python3 scripts/plot_panorama_bens_candidatos.py /tmp/patrimonio.json
"""
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

PISO_REGUA = 200_000        # ~12 meses de subsídio: abaixo disso não mede
TOTAL, REGUA = 3, 4         # posições dentro de cada ponto

SURFACE, FIG_BG = "#fcfcfb", "#f7f7f5"
TXT, TXT2, TXT3 = "#111111", "#555555", "#7b7b76"
GRID = "#e6e6e2"
COR_ESP = {0: "#b2544f", 1: "#8a8f7e", 2: "#5d7f88", -1: "#c8c8c2"}
ROTULO_ESP = {0: "esquerda", 1: "centro", 2: "direita", -1: "sem classificação"}


def carrega(caminho):
    doc = json.loads(Path(caminho).read_text(encoding="utf-8"))
    pontos, sem_regua = [], 0
    for p in doc["pessoas"]:
        nome, esp, empresas, pts = p[0], p[2], p[3], p[5]
        regua = sum(x[REGUA] or 0 for x in pts)
        patrimonio = pts[-1][TOTAL]
        if regua < PISO_REGUA:
            sem_regua += 1
            continue
        pontos.append({
            "nome": nome, "esp": esp, "empresas": empresas,
            "patrimonio": max(patrimonio, 1_000),
            "mult": (pts[-1][TOTAL] - pts[0][TOTAL]) / regua,
        })
    return doc["meta"], pontos, sem_regua


def main():
    origem = sys.argv[1] if len(sys.argv) > 1 else "/tmp/patrimonio_dados.json"
    meta, pontos, sem_regua = carrega(origem)
    acima = [p for p in pontos if p["mult"] > 1]
    abaixo = [p for p in pontos if p["mult"] <= 1]
    pct_ab = 100 * len(abaixo) / len(pontos)
    pct_ac = 100 * len(acima) / len(pontos)
    print(f"{len(pontos)} com régua · {sem_regua} sem · "
          f"{len(acima)} acima ({pct_ac:.0f}%) · {len(abaixo)} abaixo ({pct_ab:.0f}%)")

    # mesma moldura fixa do painel: ela não muda com o filtro, e é isso que
    # deixa a linha de 1× sempre na mesma altura
    XLO, XHI, YLO, YHI = 1e3, 10 ** 7.9, -1.5, 8

    fig = plt.figure(figsize=(12.4, 10.4), dpi=200, facecolor=FIG_BG)
    ax = fig.add_axes((0.098, 0.205, 0.880, 0.495))
    ax.set_facecolor(SURFACE)
    ax.set_xscale("log")
    ax.set_xlim(XLO, XHI)
    ax.set_ylim(YLO, YHI)
    ax.grid(color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(colors=TXT3, labelsize=11.5, length=0)
    ax.set_xticks([1e3, 1e4, 1e5, 1e6, 1e7])
    ax.set_xticklabels(["R$ 1 mil", "10 mil", "100 mil", "1 milhão", "10 milhões"])
    ax.set_yticks([-1, 0, 1, 2, 4, 6, 8])
    ax.set_yticklabels(["−1×", "0", "1×", "2×", "4×", "6×", "8×"])

    # território acima da régua
    ax.axhspan(1, YHI, color="#f7ebe7", zorder=0)

    fora = 0
    for p in sorted(pontos, key=lambda p: -p["empresas"]):
        if not (YLO <= p["mult"] <= YHI):
            fora += 1
            continue
        ax.scatter(p["patrimonio"], p["mult"],
                   s=14 + min(p["empresas"], 9) * 11,
                   color=COR_ESP.get(p["esp"], COR_ESP[-1]),
                   alpha=0.62, linewidths=0, zorder=3)

    ax.axhline(1, color=TXT2, lw=1.4, ls=(0, (5, 3.5)), zorder=5)
    ax.text(1.35e3, 1.18, "1× — cresceu exatamente o que o cargo pagou",
            fontsize=12, color=TXT2, va="bottom", ha="left", zorder=6)
    ax.text(10 ** 7.85, 7.55,
            f"{len(acima)} acima da linha — {pct_ac:.0f}%", fontsize=12,
            color="#d1453b", va="top", ha="right", zorder=6)
    ax.text(10 ** 7.85, -1.28,
            f"{len(abaixo)} abaixo — {pct_ab:.0f}% de quem tem régua comparável",
            fontsize=12, color="#5d7f88", va="bottom", ha="right", zorder=6)

    ax.set_xlabel("patrimônio declarado no registro mais recente",
                  fontsize=12.5, color=TXT2, labelpad=11)
    ax.set_ylabel("crescimento declarado,\nem múltiplos do subsídio do período",
                  fontsize=12.5, color=TXT2, labelpad=11, linespacing=1.5)

    fig.text(0.098, 0.972, "Onde o salário deixa de explicar",
             ha="left", va="top", fontsize=25, fontweight="bold", color=TXT)
    fig.text(0.098, 0.940,
             "Cada ponto é uma pessoa já eleita deputado federal desde 2010, "
             "e o quanto ela declara ter contra o que o cargo lhe pagou",
             ha="left", va="top", fontsize=13, color=TXT2)
    fig.text(0.098, 0.906,
             f"Abaixo da linha tracejada está a Câmara como ela normalmente é: "
             f"patrimônio que cresce menos do\nque o subsídio bruto do período — o "
             f"que se espera de quem vive do salário e gasta o que ganha.\n"
             f"São {pct_ab:.0f}% de quem tem régua comparável. Os outros {pct_ac:.0f}%, "
             f"as {len(acima)} pessoas acima da linha,\ndeclararam crescimento maior "
             f"do que tudo o que o mandato pagou. É onde a checagem começa.",
             ha="left", va="top", fontsize=13.5, color=TXT, linespacing=1.6)

    for i, (x, esp) in enumerate(((0.098, 0), (0.248, 1), (0.380, 2), (0.512, -1))):
        fig.patches.append(Rectangle((x, 0.752), 0.015, 0.018,
                                     transform=fig.transFigure,
                                     facecolor=COR_ESP[esp], edgecolor="none"))
        fig.text(x + 0.022, 0.761, ROTULO_ESP[esp], fontsize=11, color=TXT2,
                 va="center", ha="left")
    fig.text(0.700, 0.761, "tamanho do ponto = número de empresas",
             fontsize=11, color=TXT2, va="center", ha="left")

    nota = (f"Fonte: Tribunal Superior Eleitoral, declarações de bens dos registros de candidatura de 2010 a 2026; Câmara dos Deputados, decretos\n"
            f"legislativos que fixaram o subsídio parlamentar; Receita Federal, quadro societário. O subsídio é bruto, antes de imposto de renda e\n"
            f"previdência — declarar menos do que ele é o comportamento da maioria, não anomalia. Os valores são nominais, a custo de aquisição:\n"
            f"imóvel comprado em 1990 segue a preço de 1990. Crescer acima da linha não é ilícito — há empresa, aluguel, herança, venda de bem e\n"
            f"renda do cônjuge; o múltiplo mede só o que o salário deixa de explicar. {sem_regua} pessoas ficam fora por não terem régua comparável:\n"
            f"passaram poucos meses em mandato federal na janela entre duas declarações, e régua curta não mede.")
    if fora:
        nota += f" Outras {fora} passam do teto de 8× e não cabem no eixo."
    fig.text(0.098, 0.140, nota, ha="left", va="top", fontsize=9.4,
             color=TXT3, linespacing=1.6)

    saida = "pages/analises/img/panorama-bens-candidatos.png"
    fig.savefig(saida, facecolor=fig.get_facecolor())
    print("ok:", saida)


if __name__ == "__main__":
    main()
