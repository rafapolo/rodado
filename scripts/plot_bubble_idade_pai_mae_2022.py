#!/usr/bin/env python3
"""Bolhas: mediana da idade do pai por idade da mãe adolescente (SINASC 2022).

Uma bolha por idade da mãe (11-18): x = idade da mãe, y = mediana da idade do
pai (entre as DNs que a declaram, ~20%), área = nascimentos totais. A diagonal
"pai da mesma idade" serve de referência: o segmento vertical até cada bolha é
a diferença de idade, anotada. Versão-resumo do ridgeline
(plot_idade_pai_ridgeline_2022.py), com os mesmos números.
"""
import matplotlib.pyplot as plt

# idade_mae: (mediana_pai, nascimentos_totais, pais_declarados)
DATA = {
    11: (25, 72, 10),
    12: (19, 502, 57),
    13: (19, 2989, 456),
    14: (19, 10685, 1919),
    15: (20, 25593, 5096),
    16: (20, 43718, 9283),
    17: (21, 60000, 13702),
    18: (22, 76223, 18080),
}

BLUE, RED = "#1f77b4", "#b03a3a"
N_MAX = max(v[1] for v in DATA.values())

def area(n):
    return max(2600.0 * n / N_MAX, 12)

def fmt(v):
    return f"{v:,}".replace(",", ".")

fig, ax = plt.subplots(figsize=(12.5, 8.75), dpi=160)
fig.patch.set_facecolor("#f7f7f5")
ax.set_facecolor("#fcfcfb")

# faixa legal
ax.axvspan(10.5, 13.5, color=RED, alpha=0.06, zorder=0)
ax.text(12.0, 26.6, "mãe <14: estupro de vulnerável (art. 217-A)",
        ha="center", fontsize=10.5, color=RED)

# diagonal de referência
ax.plot([13.0, 19.0], [13.0, 19.0], ls="--", color="#999999", lw=1.5, zorder=1)
ax.text(14.6, 14.1, "pai da mesma idade", fontsize=10.5, color="#777777",
        rotation=32, rotation_mode="anchor")

# segmentos de diferença + bolhas
for mae, (med, total, decl) in DATA.items():
    ax.plot([mae, mae], [mae, med], color="#c9c9c6", lw=1.6, zorder=2)
    ax.scatter(mae, med, s=area(total), color=BLUE, edgecolor="white",
               linewidth=1.5, zorder=3)
    gap = med - mae
    ymid = (max(mae, 13.6) + med) / 2
    ax.text(mae + 0.13, ymid, f"+{gap}", fontsize=10.5, color="#555555")

ax.annotate("mediana 25 — mas só 10 pais declarados",
            (11, 25), (11.4, 25.6), fontsize=10, color="#555555",
            arrowprops=dict(arrowstyle="-", color="#aaaaaa", lw=1))

# legenda de tamanho
ax.text(15.4, 26.4, "nascimentos (total)", fontsize=11.5, color="#333333", ha="center")
for n, lbl, xx in [(1000, "1 mil", 14.7), (20000, "20 mil", 15.35),
                   (76223, "76 mil", 16.2)]:
    ax.scatter(xx, 25.4, s=area(n), color="#cccccc", edgecolor="#bbbbbb", zorder=2)
    ax.text(xx, 24.6, lbl, fontsize=10, ha="center", color="#555555")

ax.set_xlim(10.5, 19.0)
ax.set_ylim(13.5, 27.2)
ax.set_xticks(range(11, 19))
ax.set_yticks(range(14, 27, 2))
ax.set_xlabel("Idade da mãe (anos)", fontsize=13, labelpad=10)
ax.set_ylabel("Idade mediana do pai (anos)", fontsize=13, labelpad=10)
ax.grid(color="#e8e8e6", lw=0.8)
ax.set_axisbelow(True)
for s in ("top", "right", "left", "bottom"):
    ax.spines[s].set_visible(False)
ax.tick_params(colors="#555555", labelsize=12, length=0)

fig.suptitle("Quanto mais nova a mãe, mais velho o pai (em relação a ela)",
             x=0.065, y=0.965, ha="left", fontsize=18.5, fontweight="bold", color="#111111")
ax.set_title("SINASC 2022 · bolha = nascimentos totais por idade da mãe · mediana do pai "
             "calculada nos ~20% de DNs que a declaram",
             loc="left", fontsize=12.5, color="#555555", pad=14)
fig.text(0.065, 0.015,
         "Fonte: SINASC/DataSUS 2022 (br_ms_sinasc.microdados) — idade_mae, idade_pai · "
         "segmento cinza = diferença entre a mediana do pai e a idade da mãe",
         fontsize=10.5, color="#777777")

fig.tight_layout(rect=(0.01, 0.03, 1, 0.93))
out = "dataviz/bubble_idade_pai_mae_2022.png"
fig.savefig(out, facecolor=fig.get_facecolor(), bbox_inches="tight")
print("ok:", out)
