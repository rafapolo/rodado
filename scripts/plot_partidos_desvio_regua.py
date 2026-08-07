#!/usr/bin/env python3
"""Mapa de calor: onde cada partido cai em relação à régua do subsídio.

Cada linha é um partido e soma 100%. A cor diz que fatia da bancada daquele
partido caiu em cada faixa de desvio — de encolher patrimônio à esquerda a
multiplicá-lo à direita. A comparação é sempre dentro do partido, nunca entre
partidos: uma célula escura no PSOL e outra no PL significam a mesma coisa
proporcionalmente, e nada sobre o tamanho de uma bancada contra a outra.

  linha    partido do último registro da pessoa, com ao menos 20 parlamentares
           de régua comparável — com bancada menor uma pessoa só vira 5%
           da linha, a cor exagera e a escala de todo mundo se desloca.
  coluna   crescimento patrimonial declarado dividido pelo subsídio bruto
           acumulado no período, em faixas de 0,25.
  traço    a mediana do partido.
  linha    a divisa vertical marca 1×: à direita dela o crescimento supera
  branca   tudo o que o mandato pagou.

Ordem das linhas: da menor mediana para a maior. Quem aparece embaixo tem a
bancada que mais converteu salário em patrimônio declarado.

O que o mapa não diz: que estar à direita seja ilícito. Parlamentar tem renda
fora do subsídio — empresa, aluguel, herança, venda de bem, renda do cônjuge.
O desvio mede o que o salário deixa de explicar, e é onde a checagem começa.

Lê o JSON gerado por scripts/extrai_patrimonio_deputados.py.

Uso:
  python3 scripts/plot_partidos_desvio_regua.py /tmp/patrimonio_dados.json
"""
import json
import statistics
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, Normalize

PISO_REGUA = 200_000
TOTAL, REGUA = 3, 4
MIN_BANCADA = 20

LO, HI, PASSO = -1.0, 2.5, 0.25      # faixas centrais; fora disso, transbordo
SURFACE, FIG_BG = "#fcfcfb", "#f7f7f5"
TXT, TXT2, TXT3 = "#111111", "#555555", "#7b7b76"

RAMPA = LinearSegmentedColormap.from_list("rodado_seq", [
    "#fdfbfa", "#f4dfd9", "#e3aa9c", "#cd6f5c", "#b03d29", "#7d2415"])


def carrega(caminho):
    doc = json.loads(Path(caminho).read_text(encoding="utf-8"))
    partidos = doc["meta"]["partidos"]
    por_partido = {}
    for p in doc["pessoas"]:
        pts = p[5]
        if len(pts) < 2:
            continue
        regua = sum(x[REGUA] or 0 for x in pts)
        if regua < PISO_REGUA:
            continue
        ix = pts[-1][1]
        if ix < 0:
            continue
        mult = (pts[-1][TOTAL] - pts[0][TOTAL]) / regua
        por_partido.setdefault(partidos[ix], []).append(mult)
    return {k: v for k, v in por_partido.items() if len(v) >= MIN_BANCADA}


def main():
    origem = sys.argv[1] if len(sys.argv) > 1 else "/tmp/patrimonio_dados.json"
    dados = carrega(origem)
    ordem = sorted(dados, key=lambda k: statistics.median(dados[k]))
    print(f"{len(ordem)} partidos com {MIN_BANCADA}+ · "
          f"{sum(len(v) for v in dados.values())} parlamentares")

    bordas = np.arange(LO, HI + PASSO / 2, PASSO)
    n_col = len(bordas) - 1 + 2                      # + transbordo dos dois lados
    matriz = np.zeros((len(ordem), n_col))
    medianas = []
    for i, sigla in enumerate(ordem):
        v = dados[sigla]
        for m in v:
            if m < LO:
                c = 0
            elif m >= HI:
                c = n_col - 1
            else:
                c = 1 + int((m - LO) / PASSO)
            matriz[i, min(c, n_col - 1)] += 1
        matriz[i] = matriz[i] / len(v) * 100
        medianas.append(statistics.median(v))

    vmax = float(np.percentile(matriz[matriz > 0], 97))

    fig = plt.figure(figsize=(12.4, 10.6), dpi=200, facecolor=FIG_BG)
    ax = fig.add_axes((0.148, 0.300, 0.800, 0.395))
    ax.set_facecolor(SURFACE)
    ax.imshow(matriz, aspect="auto", cmap=RAMPA, norm=Normalize(0, vmax),
              interpolation="nearest")

    ax.set_yticks(range(len(ordem)))
    ax.set_yticklabels([f"{s}" for s in ordem], fontsize=12, color=TXT)
    ax.tick_params(colors=TXT3, length=0, labelsize=11.5)
    for sp in ax.spines.values():
        sp.set_visible(False)

    # eixo x: rótulo redondo em -1, 0, 1 e 2
    marcas = {}
    for val in (-1.0, 0.0, 1.0, 2.0):
        marcas[1 + (val - LO) / PASSO - 0.5] = f"{val:.0f}×"
    ax.set_xticks(list(marcas))
    ax.set_xticklabels(list(marcas.values()))

    # a divisa de 1×: onde o crescimento passa a superar o mandato inteiro
    x1 = 1 + (1.0 - LO) / PASSO - 0.5
    ax.axvline(x1, color=TXT, lw=1.6, ls=(0, (4, 3)), zorder=5)
    ax.text(x1 + 0.25, -1.15, "1× — daqui para a direita o crescimento\n"
            "supera tudo o que o mandato pagou",
            fontsize=11, color=TXT, va="bottom", ha="left", linespacing=1.45)

    for xb in (0.5, n_col - 1.5):
        ax.axvline(xb, color="#ffffff", lw=2.4, zorder=4)

    # mediana de cada partido, no mesmo traço branco da figura do câncer
    for i, m in enumerate(medianas):
        x = 0 if m < LO else n_col - 1 if m >= HI else 1 + (m - LO) / PASSO - 0.5
        ax.plot([x, x], [i - 0.34, i + 0.34], color="#ffffff", lw=2.2, zorder=6)

    # N de cada bancada, fora da matriz
    for i, sigla in enumerate(ordem):
        ax.text(n_col - 0.3, i, str(len(dados[sigla])), fontsize=10.5,
                color=TXT3, va="center", ha="left")
    ax.text(n_col - 0.3, -0.95, "n", fontsize=10.5, color=TXT3,
            va="center", ha="left")

    fig.text(0.148, 0.238,
             "crescimento patrimonial declarado, em múltiplos do subsídio do período   ·   "
             "primeira e última coluna = transbordo",
             ha="left", va="top", fontsize=12, color=TXT2)

    fig.text(0.075, 0.968, "Onde cada bancada cai em relação ao salário",
             ha="left", va="top", fontsize=25, fontweight="bold", color=TXT)
    fig.text(0.075, 0.934,
             "Cada linha é um partido e soma 100%: quanto mais escura a célula, "
             "maior a fatia da bancada naquela faixa",
             ha="left", va="top", fontsize=13, color=TXT2)

    maior = ordem[-1]
    menor = ordem[0]
    fig.text(0.075, 0.898,
             f"A ordem vai da menor mediana para a maior — o traço branco marca "
             f"onde ela cai em cada bancada.\nA massa de todas elas fica à "
             f"esquerda da divisa de 1×: o normal, em qualquer partido, é o "
             f"patrimônio\ncrescer menos do que o mandato pagou. O que muda "
             f"entre as legendas é a espessura da cauda\nà direita. "
             f"{maior} tem a maior mediana do conjunto; {menor}, a menor. "
             f"Só entram partidos com pelo\nmenos {MIN_BANCADA} parlamentares "
             f"de régua comparável: com bancada menor, uma pessoa vira 5% da "
             f"linha e a cor exagera.",
             ha="left", va="top", fontsize=13.5, color=TXT, linespacing=1.6)

    cax = fig.add_axes((0.288, 0.183, 0.520, 0.016))
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=Normalize(0, vmax), cmap=RAMPA),
                      cax=cax, orientation="horizontal")
    cb.outline.set_visible(False)
    cb.ax.tick_params(colors=TXT3, labelsize=10.5, length=0)
    cb.set_ticks([0, vmax / 2, vmax])
    cb.set_ticklabels(["0%", f"{vmax/2:.0f}%", f"{vmax:.0f}%"])
    fig.text(0.548, 0.157,
             "fatia da bancada do partido que cai na faixa   ·   cada linha soma 100%",
             ha="center", va="top", fontsize=11, color=TXT2)

    fig.text(0.075, 0.122,
             "Fonte: Tribunal Superior Eleitoral, declarações de bens dos registros de candidatura de 2010 a 2026; Câmara dos Deputados, decretos\n"
             "legislativos que fixaram o subsídio parlamentar. O partido é o do último registro da pessoa, não o da eleição em que foi eleita.\n"
             "O subsídio é bruto, antes de imposto de renda e previdência. Valores nominais, a custo de aquisição, como manda a regra do imposto\n"
             "de renda. Percentuais dentro de cada partido, nunca entre partidos — a cor compara faixas de uma mesma bancada, não o tamanho de\n"
             "uma contra a outra. Estar à direita da divisa não é ilícito: há empresa, aluguel, herança e renda do cônjuge; o desvio mede o que\n"
             "o salário deixa de explicar, que é onde a checagem começa.",
             ha="left", va="top", fontsize=9.1, color=TXT3, linespacing=1.55)

    saida = "pages/analises/img/partidos-desvio-regua.png"
    fig.savefig(saida, facecolor=fig.get_facecolor())
    print("ok:", saida)


if __name__ == "__main__":
    main()
