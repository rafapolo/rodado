#!/usr/bin/env python3
"""Idade das mortes por câncer no Brasil, por sítio do tumor (2022). Duas figuras.

  dataviz/cancer_idade_amplitude_2022.png
      Amplitude etária de cada tipo de câncer: a idade do óbito mais novo e do
      mais velho do ano, com a faixa onde ficam 80% das mortes (10º ao 90º
      percentil), a mediana e a média. Ordenado pela mediana.

  dataviz/cancer_idade_perfil_2022.png
      Mapa de calor: para cada sítio, que fatia das suas mortes cai em cada
      faixa quinquenal de idade. Mostra o formato da distribuição, não só a
      posição — leucemia é bimodal (infância e velhice), testículo é o único
      tumor cujas mortes se concentram antes dos 40.

LIMPEZA OBRIGATÓRIA DO CAMPO DE IDADE
O campo de idade do SIM traz 6.528 óbitos de 2022 (0,44% do total) com valores
impossíveis — de 116 até 220 anos. Não são outliers reais: a distribuição
desses registros tem o formato de uma curva de mortalidade deslocada, o que
denuncia erro sistemático na decodificação do campo (o SIM guarda idade como
unidade + valor, e "anos acima de 100" tem código próprio). Tudo acima de 115
anos é descartado aqui. Sem esse corte, o máximo da próstata sairia 201 anos e
o do lábio, 212 — e um gráfico de amplitude estaria plotando o erro.

Mesmo depois do corte, os extremos são registros isolados e alguns seguem
clinicamente impossíveis (próstata com mínima de 1 ano, pele não melanoma com
1 ano). Por isso as figuras destacam a faixa de 10 a 90% e tratam mínima e
máxima como o traço fino: é o alcance observado, não o alcance típico.

Fonte: Ministério da Saúde — Sistema de Informações sobre Mortalidade, óbitos
de 2022 com causa básica C00–C97, campo de idade em anos completos. Óbitos sem
idade preenchida (2,4%) ficam de fora. Agrupamento por sítio idêntico ao de
scripts/plot_cancer_internacao_mortalidade.py; C76–C80 (sítio mal definido ou
secundário) fora por não nomearem um órgão de origem.
"""
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.lines import Line2D

# sítio: (mortes, média, mediana, mínima, máxima, p10, p90)
STATS = {
    "Testículo":                    (442, 38.3, 33, 4, 97, 22, 68),
    "Linfoma de Hodgkin":           (528, 52.3, 53, 3, 96, 23, 80),
    "Colo do útero":                (6551, 56.0, 55, 16, 113, 36, 78),
    "Leucemia":                     (6646, 58.4, 65, 0, 115, 18, 85),
    "Cérebro e sistema nervoso":    (9333, 59.2, 62, 0, 114, 32, 81),
    "Mama":                         (18239, 62.7, 62, 0, 114, 42, 84),
    "Ovário":                       (3954, 63.0, 64, 14, 104, 44, 82),
    "Faringe":                      (3617, 63.4, 63, 7, 114, 49, 79),
    "Linfoma não Hodgkin":          (4240, 63.7, 67, 1, 112, 37, 84),
    "Lábio e cavidade oral":        (3591, 65.4, 65, 0, 110, 49, 83),
    "Corpo do útero":               (3986, 65.6, 66, 16, 105, 46, 83),
    "Laringe":                      (4323, 66.0, 66, 4, 113, 52, 81),
    "Esôfago":                      (8042, 66.0, 66, 17, 112, 51, 82),
    "Reto e ânus":                  (7902, 66.7, 67, 2, 109, 47, 85),
    "Melanoma de pele":             (1848, 66.9, 69, 6, 110, 45, 87),
    "Estômago":                     (13465, 67.2, 68, 14, 115, 48, 84),
    "Rim e vias urinárias":         (3996, 67.5, 69, 0, 115, 49, 85),
    "Fígado e vias biliares":       (9966, 67.9, 69, 0, 115, 52, 84),
    "Cólon":                        (13031, 68.5, 69, 12, 110, 50, 86),
    "Vesícula e vias biliares":     (3798, 68.8, 69, 23, 107, 51, 85),
    "Tireoide":                     (803, 68.9, 70, 17, 115, 49, 86),
    "Mieloma múltiplo":             (3522, 69.1, 70, 10, 106, 53, 84),
    "Pâncreas":                     (11855, 69.4, 70, 0, 115, 53, 85),
    "Traqueia, brônquios e pulmão": (27881, 69.5, 70, 0, 114, 55, 84),
    "Bexiga":                       (4829, 75.1, 76, 12, 112, 61, 89),
    "Pele não melanoma":            (2921, 77.1, 80, 1, 110, 57, 94),
    "Próstata":                     (15229, 77.3, 78, 1, 115, 64, 90),
}

# mortes por faixa quinquenal de idade: 0-4, 5-9, … 85-89, 90+
GRUPOS = list(range(0, 95, 5))
HIST = {
    "Bexiga": [0, 0, 1, 0, 0, 5, 4, 12, 27, 66, 118, 193, 437, 586, 754, 780, 748, 624, 474],
    "Colo do útero": [0, 0, 0, 2, 36, 162, 358, 548, 720, 702, 644, 706, 638, 563, 531, 381, 280, 164, 116],
    "Corpo do útero": [0, 0, 0, 1, 5, 32, 50, 87, 157, 205, 293, 397, 527, 607, 512, 431, 353, 193, 136],
    "Cérebro e sistema nervoso": [147, 156, 124, 97, 138, 178, 202, 309, 418, 526, 740, 971, 1131, 1144, 1107, 831, 581, 353, 179],
    "Cólon": [0, 0, 2, 7, 26, 56, 98, 191, 372, 490, 744, 1206, 1529, 1849, 1834, 1640, 1351, 980, 656],
    "Estômago": [0, 0, 1, 4, 22, 63, 154, 246, 421, 635, 872, 1240, 1664, 1834, 1973, 1666, 1368, 802, 500],
    "Esôfago": [0, 0, 0, 1, 3, 11, 15, 63, 156, 360, 706, 1097, 1305, 1324, 1067, 826, 575, 353, 180],
    "Faringe": [0, 1, 2, 2, 10, 11, 12, 36, 109, 242, 360, 559, 651, 585, 407, 290, 176, 100, 64],
    "Fígado e vias biliares": [21, 8, 4, 7, 20, 36, 55, 108, 201, 352, 560, 961, 1335, 1628, 1475, 1321, 934, 615, 325],
    "Laringe": [2, 0, 0, 2, 0, 5, 14, 28, 65, 193, 338, 565, 760, 763, 615, 465, 260, 153, 95],
    "Leucemia": [205, 171, 164, 187, 226, 146, 191, 220, 244, 273, 312, 356, 533, 646, 692, 710, 651, 397, 322],
    "Linfoma de Hodgkin": [1, 6, 7, 19, 29, 42, 37, 34, 43, 26, 24, 34, 36, 42, 46, 43, 33, 16, 10],
    "Linfoma não Hodgkin": [10, 23, 28, 36, 81, 86, 101, 115, 170, 189, 232, 365, 441, 510, 529, 530, 395, 269, 130],
    "Lábio e cavidade oral": [1, 0, 0, 1, 4, 12, 16, 42, 111, 177, 325, 528, 557, 521, 412, 308, 275, 174, 127],
    "Mama": [1, 0, 0, 2, 12, 120, 376, 744, 1192, 1533, 1879, 2087, 2084, 2017, 1743, 1506, 1182, 930, 831],
    "Melanoma de pele": [0, 2, 1, 4, 7, 19, 35, 50, 60, 112, 121, 150, 198, 200, 255, 191, 189, 134, 120],
    "Mieloma múltiplo": [0, 0, 1, 1, 4, 7, 8, 23, 63, 112, 182, 333, 442, 572, 575, 477, 378, 217, 127],
    "Ovário": [0, 0, 1, 19, 33, 43, 53, 113, 169, 281, 355, 460, 496, 542, 503, 371, 266, 158, 91],
    "Pele não melanoma": [1, 0, 2, 2, 5, 5, 13, 23, 46, 58, 86, 130, 192, 247, 277, 346, 412, 473, 603],
    "Próstata": [1, 0, 1, 1, 4, 5, 6, 6, 21, 62, 172, 455, 958, 1626, 2385, 2897, 2806, 2119, 1704],
    "Pâncreas": [2, 1, 1, 4, 6, 22, 51, 90, 219, 412, 634, 1075, 1459, 1792, 1850, 1549, 1332, 829, 527],
    "Reto e ânus": [1, 0, 2, 4, 12, 42, 86, 159, 267, 391, 520, 851, 1000, 1056, 1076, 902, 715, 500, 318],
    "Rim e vias urinárias": [26, 25, 6, 4, 12, 18, 25, 48, 95, 147, 236, 343, 490, 597, 566, 507, 405, 275, 171],
    "Testículo": [2, 0, 0, 15, 64, 90, 80, 51, 34, 12, 13, 17, 14, 11, 10, 7, 10, 8, 4],
    "Tireoide": [0, 0, 0, 1, 3, 2, 7, 16, 25, 32, 42, 62, 96, 94, 119, 108, 90, 58, 48],
    "Traqueia, brônquios e pulmão": [6, 2, 6, 13, 28, 47, 79, 169, 363, 631, 1248, 2407, 3894, 4814, 4729, 3852, 2952, 1737, 904],
    "Vesícula e vias biliares": [0, 0, 0, 0, 3, 7, 14, 42, 87, 162, 220, 356, 475, 536, 533, 536, 386, 250, 181],
}

SURFACE, FIG_BG = "#fcfcfb", "#f7f7f5"
TXT, TXT2, TXT3 = "#111111", "#555555", "#7b7b76"
ACENTO, FAIXA, EXTREMO, GRID = "#d1453b", "#e79c92", "#c9c9c2", "#e6e6e2"

ORDEM = sorted(STATS, key=lambda s: (STATS[s][2], STATS[s][1]))


def vg(v, casas=1):
    return f"{v:.{casas}f}".replace(".", ",")


# ============================================================ figura 1
# amplitude etária: traço fino = mínima→máxima, barra grossa = 10º ao 90º
# percentil, ponto = mediana, risco = média
fig = plt.figure(figsize=(12.4, 12.6), dpi=200, facecolor=FIG_BG)
ax = fig.add_axes((0.245, 0.135, 0.735, 0.615))
ax.set_facecolor(SURFACE)

for i, sitio in enumerate(ORDEM):
    mortes, media, mediana, mn, mx, p10, p90 = STATS[sitio]
    y = len(ORDEM) - 1 - i
    ax.plot([mn, mx], [y, y], color=EXTREMO, lw=1.6, solid_capstyle="round", zorder=2)
    ax.plot([mn, mn], [y - 0.24, y + 0.24], color=EXTREMO, lw=1.6, zorder=2)
    ax.plot([mx, mx], [y - 0.24, y + 0.24], color=EXTREMO, lw=1.6, zorder=2)
    ax.plot([p10, p90], [y, y], color=FAIXA, lw=8.5, solid_capstyle="round", zorder=3)
    ax.plot([media, media], [y - 0.2, y + 0.2], color="#8f5049", lw=1.8, zorder=4)
    ax.scatter([mediana], [y], s=78, color=ACENTO, edgecolors=SURFACE,
               linewidths=1.6, zorder=5)

ax.set_yticks(range(len(ORDEM)))
ax.set_yticklabels(list(reversed(ORDEM)), fontsize=11, color=TXT2)
ax.set_ylim(-0.8, len(ORDEM) - 0.2)
ax.set_xlim(0, 118)
ax.set_xticks([0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110])
ax.grid(axis="x", color=GRID, lw=0.8)
ax.set_axisbelow(True)
for sp in ax.spines.values():
    sp.set_visible(False)
ax.tick_params(colors=TXT3, labelsize=11.5, length=0)
ax.set_xlabel("idade no momento da morte, em anos", fontsize=12.5, color=TXT2,
              labelpad=10)

# rótulos das medianas nos dois extremos da ordenação
for sitio, dx, ha in (("Testículo", 5, "left"), ("Próstata", -5, "right")):
    y = len(ORDEM) - 1 - ORDEM.index(sitio)
    ax.annotate(f"mediana {STATS[sitio][2]} anos",
                xy=(STATS[sitio][2], y), xytext=(STATS[sitio][2] + dx, y + 0.8),
                fontsize=10.5, color=TXT, fontweight="bold", ha=ha,
                arrowprops=dict(arrowstyle="-", color=TXT3, lw=0.9))

leg = [Line2D([], [], color=EXTREMO, lw=1.6, label="mais novo → mais velho do ano"),
       Line2D([], [], color=FAIXA, lw=8.5, label="onde estão 80% das mortes"),
       Line2D([], [], color=ACENTO, marker="o", ls="", markersize=8.5,
              markeredgecolor=SURFACE, label="mediana"),
       Line2D([], [], color="#8f5049", lw=1.8, label="média")]
ax.legend(handles=leg, loc="lower left", bbox_to_anchor=(-0.005, 1.012), ncol=4,
          frameon=False, fontsize=10.5, labelcolor=TXT2, handletextpad=0.9,
          columnspacing=2.6, borderpad=0.0, handlelength=1.9)

fig.text(0.082, 0.955, "Todo câncer é de idoso — menos três",
         ha="left", va="top", fontsize=25, fontweight="bold", color=TXT)
fig.text(0.082, 0.914,
         "Idade das 226 mil mortes por câncer no Brasil em 2022, por tipo de tumor, ordenada pela mediana",
         ha="left", va="top", fontsize=13, color=TXT2)
fig.text(0.082, 0.878,
         "Do câncer de testículo se morre aos 33 anos; do de próstata, aos 78 — 45 anos de diferença entre as duas pontas\n"
         "da lista. Testículo, linfoma de Hodgkin e colo do útero são os únicos tumores cuja mediana fica antes dos 60.\n"
         "A barra clara mostra que a amplitude é enorme em quase todos: câncer mata em qualquer idade, só que raramente.",
         ha="left", va="top", fontsize=13.5, color=TXT, linespacing=1.6)

fig.text(0.082, 0.058,
         "Fonte: Ministério da Saúde — Sistema de Informações sobre Mortalidade, óbitos de 2022 com causa básica no capítulo das neoplasias malignas.\n"
         "Excluídos os 2,4% de óbitos sem idade preenchida e 6.528 registros (0,44%) com idade impossível, de 116 a 220 anos — erro de codificação do campo, não idade real.\n"
         "Mínima e máxima são registros isolados e alguns seguem clinicamente improváveis; a leitura confiável é a barra dos 80%.",
         ha="left", va="top", fontsize=9.5, color=TXT3, linespacing=1.6)

out1 = "dataviz/cancer_idade_amplitude_2022.png"
fig.savefig(out1, facecolor=fig.get_facecolor())
print("ok:", out1)

# ============================================================ figura 2
# mapa de calor: fatia das mortes de cada sítio em cada faixa quinquenal
RAMPA = LinearSegmentedColormap.from_list("rodado_seq", [
    "#fdf6f4", "#f9dfd9", "#f2bdb2", "#e8968a", "#dc6c5f", "#c9402f", "#96271d"])

fig2 = plt.figure(figsize=(12.4, 10.6), dpi=200, facecolor=FIG_BG)
ax2 = fig2.add_axes((0.245, 0.255, 0.70, 0.505))
ax2.set_facecolor(SURFACE)

matriz = []
for sitio in ORDEM:                       # mesma ordem da figura 1: mais novo no topo
    tot = sum(HIST[sitio])
    matriz.append([100 * n / tot for n in HIST[sitio]])

vmax = max(max(linha) for linha in matriz)
im = ax2.imshow(matriz, aspect="auto", cmap=RAMPA, norm=Normalize(0, vmax),
                interpolation="nearest")

# risco branco na idade mediana — ancora as duas figuras
for i, sitio in enumerate(ORDEM):
    x = min(STATS[sitio][2] / 5, 18.5) - 0.5
    ax2.plot([x, x], [i - 0.45, i + 0.45], color="#ffffff", lw=2.4,
             solid_capstyle="butt", zorder=3)

ax2.set_yticks(range(len(ORDEM)))
ax2.set_yticklabels(ORDEM, fontsize=11, color=TXT2)
ax2.set_xticks(range(0, 19, 2))
ax2.set_xticklabels([f"{g}" for g in GRUPOS[::2]], fontsize=11.5, color=TXT3)
ax2.tick_params(length=0)
for sp in ax2.spines.values():
    sp.set_visible(False)
ax2.set_xlabel("faixa etária no momento da morte  ·  última coluna = 90 anos ou mais",
               fontsize=12.5, color=TXT2, labelpad=10)

cb = fig2.colorbar(im, ax=ax2, orientation="horizontal", fraction=0.035,
                   pad=0.095, aspect=42)
cb.outline.set_visible(False)
cb.ax.tick_params(colors=TXT3, labelsize=10.5, length=0)
cb.set_label("fatia das mortes daquele câncer que cai na faixa  ·  cada linha soma 100%",
             fontsize=10.5, color=TXT3, labelpad=9)
cb.ax.xaxis.set_major_formatter(lambda v, _: f"{v:g}%".replace(".", ","))

fig2.text(0.082, 0.955, "O mapa etário do câncer, tumor por tumor",
          ha="left", va="top", fontsize=25, fontweight="bold", color=TXT)
fig2.text(0.082, 0.914,
          "Cada linha é um tumor e soma 100%: quanto mais escura a célula, mais mortes daquele câncer naquela idade",
          ha="left", va="top", fontsize=13, color=TXT2)
fig2.text(0.082, 0.878,
          "A mancha desce da esquerda para a direita porque a lista segue a ordem da figura anterior, da menor mediana\n"
          "para a maior — o traço branco marca onde ela cai. Leucemia é o tumor que mais mata jovem: 14,3% das suas\n"
          "mortes vêm antes dos 25 anos, contra 0,2% no de pulmão e 0,1% no de mama. Testículo é o oposto de tudo, com\n"
          "o pico entre 25 e 29 anos e quase nada depois dos 45.",
          ha="left", va="top", fontsize=13.5, color=TXT, linespacing=1.6)

fig2.text(0.082, 0.115,
          "Fonte: Ministério da Saúde — Sistema de Informações sobre Mortalidade, óbitos de 2022 com causa básica no capítulo das neoplasias malignas.\n"
          "Mesma limpeza da figura de amplitude: fora os óbitos sem idade e os 0,44% com idade impossível. Percentuais dentro de cada tumor, não entre tumores —\n"
          "a cor compara idades de um mesmo câncer, nunca o tamanho de um câncer contra o outro.",
          ha="left", va="top", fontsize=9.5, color=TXT3, linespacing=1.6)

out2 = "dataviz/cancer_idade_perfil_2022.png"
fig2.savefig(out2, facecolor=fig2.get_facecolor())
print("ok:", out2)
