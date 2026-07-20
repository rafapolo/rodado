#!/usr/bin/env python3
"""Bolhas: idade média da mãe ao ter filho x fecundidade, por denominação evangélica.

Dados agregados do Censo 2010 (br_ibge_censo_demografico.microdados_pessoa_2010,
via beelink). Eixo x = idade média (v6036) das mulheres com último filho menor de
1 ano (v6660=0, v6633>=1); eixo y = média de filhos nascidos vivos (v6633, zeros
incluídos) das mulheres de 45-49; bolha = população total da denominação
(peso_amostral); religião = v6121, ponderação por peso_amostral em tudo.
Códigos v6121 validados contra os totais publicados do Censo 2010.
"""
import matplotlib.pyplot as plt
import numpy as np

# denom, pop, fecundidade 45-49, idade média mãe, grupo
DATA = [
    ("Assembleia de Deus",     12_314_675, 3.084, 25.97, "pent"),
    ("Outras Pentecostais",     5_513_312, 2.674, 26.44, "pent"),
    ("Batista",                 3_724_183, 2.359, 27.26, "missao"),
    ("Cong. Cristã",            2_288_420, 2.786, 27.20, "pent"),
    ("IURD",                    1_871_148, 2.773, 26.54, "pent"),
    ("Quadrangular",            1_805_142, 2.591, 26.41, "pent"),
    ("Adventista",              1_561_534, 2.754, 26.48, "missao"),
    ("Luterana",                  999_166, 2.125, 28.31, "missao"),
    ("Presbiteriana",             921_482, 2.196, 28.35, "missao"),
    ("Deus é Amor",               843_256, 3.424, 25.36, "pent"),
    ("Maranata",                  354_990, 2.276, 28.48, "pent"),
    ("Metodista",                 340_917, 2.163, 27.90, "missao"),
]

COLORS = {"missao": "#1f77b4", "pent": "#2ca02c", "outras": "#e377c2"}
GROUP_LABEL = {"missao": "Evangélica de Missão", "pent": "Evangélica Pentecostal",
               "outras": "Não determinada / outras"}

# deslocamento dos rótulos (dx, dy) em coordenadas de dados, e alinhamento
LABEL_POS = {
    "Assembleia de Deus":     (0.30, 0.0, "left"),
    "Não determinada":        (-0.12, -0.15, "right"),
    "Outras Pentecostais":    (0.16, -0.02, "left"),
    "Batista":                (0.05, -0.11, "left"),
    "Cong. Cristã":           (-0.06, 0.10, "right"),
    "IURD":                   (0.12, 0.045, "left"),
    "Quadrangular":           (-0.10, -0.10, "right"),
    "Adventista":             (-0.14, 0.01, "right"),
    "Luterana":               (-0.09, 0.0, "right"),
    "Presbiteriana":          (0.09, 0.0, "left"),
    "Deus é Amor":            (0.11, 0.005, "left"),
    "Outras evang. menores":  (0.10, 0.075, "left"),
    "Maranata":               (0.0, 0.06, "center"),
    "Metodista":              (-0.06, -0.08, "right"),
}

def area(pop, max_pop=12_314_675, max_pt2=2600):
    return pop / max_pop * max_pt2

fig, ax = plt.subplots(figsize=(12.5, 8.75), dpi=160)
fig.patch.set_facecolor("#f7f7f5")
ax.set_facecolor("#fcfcfb")

pops = np.array([d[1] for d in DATA], float)
ys = np.array([d[2] for d in DATA])
xs = np.array([d[3] for d in DATA])

# tendência: mínimos quadrados ponderados pela população
w = pops / pops.sum()
b, a = np.polyfit(xs, ys, 1, w=np.sqrt(w))
xt = np.linspace(25.0, 28.9, 50)
ax.plot(xt, a + b * xt, ls="--", color="#999999", lw=1.6, zorder=1)

for name, pop, y, x, grp in DATA:
    ax.scatter(x, y, s=area(pop), color=COLORS[grp], edgecolor="white",
               linewidth=1.5, zorder=3)

for name, pop, y, x, grp in DATA:
    dx, dy, ha = LABEL_POS[name]
    ax.annotate(name, (x + dx, y + dy), ha=ha, va="center",
                fontsize=11.5, color="#333333", zorder=4)

# legenda de cor (canto superior direito)
for i, grp in enumerate(["missao", "pent"]):
    yy = 3.44 - i * 0.095
    ax.scatter(27.62, yy, s=130, color=COLORS[grp], zorder=5)
    ax.text(27.72, yy, GROUP_LABEL[grp], fontsize=12, va="center", color="#333333")

# legenda de tamanho
ax.text(28.2, 3.16, "População total", fontsize=12, color="#333333", ha="center")
for pop, lbl, xx in [(500_000, "500 mil", 27.75), (3_000_000, "3 milhões", 28.16),
                     (12_314_675, "12,3 milhões", 28.68)]:
    ax.scatter(xx, 3.00, s=area(pop), color="#cccccc", edgecolor="#bbbbbb", zorder=2)
    ax.text(xx, 2.85, lbl, fontsize=11, ha="center", color="#333333")

ax.set_xlim(25.0, 29.0)
ax.set_ylim(1.95, 3.60)
ax.set_xlabel("Idade média da mãe — mulheres com filho menor de 1 ano", fontsize=13, labelpad=10)
ax.set_ylabel("Filhos em média — mulheres 45–49 anos (fecundidade completa)", fontsize=13, labelpad=10)
ax.grid(axis="both", color="#e8e8e6", lw=0.8)
for s in ("top", "right", "left", "bottom"):
    ax.spines[s].set_visible(False)
ax.tick_params(colors="#555555", labelsize=11.5, length=0)

fig.suptitle("Filhos mais cedo, mais filhos: idade da mãe x fecundidade entre evangélicos",
             x=0.065, y=0.965, ha="left", fontsize=19, fontweight="bold", color="#111111")
ax.set_title("Denominações evangélicas do Censo 2010 · bolha = população total (todas as idades)",
             loc="left", fontsize=13, color="#555555", pad=14)
fig.text(0.065, 0.015,
         "Fonte: Censo Demográfico 2010 (IBGE), microdados de pessoa — V6633, V6660, V6121 · "
         "IURD = Igreja Universal do Reino de Deus",
         fontsize=10.5, color="#777777")

fig.tight_layout(rect=(0.01, 0.03, 1, 0.93))
out = "dataviz/evangelicos_fecundidade_idade.png"
fig.savefig(out, facecolor=fig.get_facecolor(), bbox_inches="tight")
print("ok:", out)
