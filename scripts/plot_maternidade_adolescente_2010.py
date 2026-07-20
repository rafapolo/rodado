#!/usr/bin/env python3
"""Dumbbell: maternidade adolescente (15-17) por religião x situação escolar.

Censo 2010 (br_ibge_censo_demografico.microdados_pessoa_2010, via beelink):
% de meninas de 15-17 anos (v6036) com filho (v6633>=1), ponderado por
peso_amostral, por grupo de religião (v6121) e situação escolar (v6400:
'1' = fundamental incompleto/atraso; '2'-'4' = fundamental completo+).
"""
import matplotlib.pyplot as plt

# religiao, % mães em dia na escola, % mães com atraso escolar
DATA = [
    ("Sem religião",       7.10, 17.06),
    ("Católica",           4.09, 11.48),
    ("Evang. Pentecostal", 4.03, 9.88),
    ("Outras religiões",   2.80, 9.58),
    ("Evang. de Missão",   2.67, 7.64),
]

C_EMDIA, C_ATRASO = "#7ba3cd", "#134b86"

fig, ax = plt.subplots(figsize=(12.5, 6.2), dpi=160)
fig.patch.set_facecolor("#f7f7f5")
ax.set_facecolor("#fcfcfb")

ys = range(len(DATA), 0, -1)
for y, (nome, emdia, atraso) in zip(ys, DATA):
    ax.plot([emdia, atraso], [y, y], color="#c9c9c6", lw=2.5, zorder=2)
    ax.scatter(emdia, y, s=170, color=C_EMDIA, edgecolor="white", lw=1.5, zorder=3)
    ax.scatter(atraso, y, s=170, color=C_ATRASO, edgecolor="white", lw=1.5, zorder=3)
    ax.text(emdia - 0.35, y, f"{emdia:.1f}%".replace(".", ","), ha="right", va="center",
            fontsize=11.5, color="#333333")
    ax.text(atraso + 0.35, y, f"{atraso:.1f}%".replace(".", ","), ha="left", va="center",
            fontsize=11.5, color="#333333")
    ax.text(atraso + 2.1, y, f"({atraso/emdia:.1f}×)".replace(".", ","), ha="left",
            va="center", fontsize=10.5, color="#999999")

ax.set_yticks(list(ys))
ax.set_yticklabels([d[0] for d in DATA], fontsize=12.5, color="#333333")
ax.set_xlim(0, 20.5)
ax.set_xticks(range(0, 21, 5))
ax.set_ylim(0.4, len(DATA) + 0.9)
ax.set_xlabel("% de meninas de 15–17 anos que já têm filho", fontsize=13, labelpad=10)
ax.grid(axis="x", color="#e8e8e6", lw=0.8)
ax.set_axisbelow(True)
for s in ("top", "right", "left", "bottom"):
    ax.spines[s].set_visible(False)
ax.tick_params(colors="#555555", labelsize=11.5, length=0)

# legenda
ax.scatter([], [], s=170, color=C_EMDIA, label="Em dia na escola (fundamental completo+)")
ax.scatter([], [], s=170, color=C_ATRASO, label="Com atraso escolar (fundamental incompleto)")
ax.legend(loc="lower right", frameon=False, fontsize=11.5, labelcolor="#333333")

fig.suptitle("Atraso escolar multiplica a maternidade adolescente; religião quase não muda",
             x=0.065, y=0.96, ha="left", fontsize=18, fontweight="bold", color="#111111")
ax.set_title("Meninas de 15–17 anos que já são mães, por religião e situação escolar — Censo 2010",
             loc="left", fontsize=13, color="#555555", pad=14)
fig.text(0.065, 0.02,
         "Fonte: Censo Demográfico 2010 (IBGE), microdados de pessoa — V6036, V6633, V6121, V6400 · "
         "ponderado por peso amostral · entre parênteses, razão atraso/em dia",
         fontsize=10.5, color="#777777")

fig.tight_layout(rect=(0.01, 0.05, 1, 0.92))
out = "dataviz/maternidade_adolescente_religiao_escola_2010.png"
fig.savefig(out, facecolor=fig.get_facecolor(), bbox_inches="tight")
print("ok:", out)
