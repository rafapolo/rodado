#!/usr/bin/env python3
"""Idade do pai por idade da mãe adolescente (SINASC 2022), em dois painéis.

Painel de cima: escala real — total de nascimentos por idade da mãe (cinza) e
quantos declaram idade do pai (escuro). Painel de baixo: composição 100% da
idade do pai (menor de 18 / 18-24 / 25+) entre os declarados, com a mediana da
idade do pai por barra. Faixa vermelha: mães <14 (estupro de vulnerável,
art. 217-A). Dados de br_ms_sinasc.microdados, ano=2022, idade_pai 10-80.
"""
import matplotlib.pyplot as plt
import numpy as np

# idade_mae: (pai<18, pai 18-24, pai 25+, mediana_pai, nascimentos_totais)
DATA = {
    11: (0, 5, 5, 25, 72),
    12: (18, 27, 12, 19, 502),
    13: (148, 238, 70, 19, 2989),
    14: (498, 1114, 307, 19, 10685),
    15: (943, 3232, 921, 20, 25593),
    16: (1241, 6272, 1770, 20, 43718),
    17: (1154, 9481, 3067, 21, 60000),
    18: (732, 12570, 4778, 22, 76223),
}

BANDS = ["Pai menor de 18", "Pai de 18 a 24", "Pai de 25 ou mais"]
COLORS = ["#a3c0dd", "#5586bd", "#134b86"]
RED = "#b03a3a"

def fmt(v):
    return f"{v:,}".replace(",", ".")

idades = sorted(DATA)
x = np.arange(len(idades))

fig, (ax_n, ax) = plt.subplots(2, 1, figsize=(12.5, 9.6), dpi=160,
                               gridspec_kw={"height_ratios": [1, 2.4], "hspace": 0.16})
fig.patch.set_facecolor("#f7f7f5")

for a in (ax_n, ax):
    a.set_facecolor("#f7f7f5")
# faixa legal (mães 11-13) só no painel da composição
ax.axvspan(-0.5, 2.5, color=RED, alpha=0.06, zorder=0)

# ---- painel de cima: escala real
totais = [DATA[i][4] for i in idades]
decls = [sum(DATA[i][:3]) for i in idades]
ax_n.bar(x, totais, width=0.72, color="#d9d9d5", zorder=2)
ax_n.bar(x, decls, width=0.72, color="#8a8a86", zorder=3)
for i, (t, d) in enumerate(zip(totais, decls)):
    ax_n.text(i, t + 1800, fmt(t), ha="center", fontsize=10, color="#555555")
ax_n.text(len(x) - 0.55, decls[-1] + 4500, "com idade do pai\ndeclarada (~20%)",
          ha="right", va="bottom", fontsize=10, color="#8a8a86", linespacing=1.2)
ax_n.set_title("Quantos nascimentos são (escala real)", loc="left",
               fontsize=12.5, color="#333333", pad=8)
ax_n.set_ylim(0, 88000)
ax_n.set_yticks([])
ax_n.set_xticks(x)
ax_n.set_xticklabels([])
for s in ("top", "right", "left", "bottom"):
    ax_n.spines[s].set_visible(False)
ax_n.tick_params(length=0)

# ---- painel de baixo: composição 100% dos declarados
for i, idade in enumerate(idades):
    menor, meio, mais, mediana, total = DATA[idade]
    decl = menor + meio + mais
    partes = [100.0 * v / decl for v in (menor, meio, mais)]
    base = 0.0
    for pct, cor, txtcor in zip(partes, COLORS, ("#333333", "white", "white")):
        ax.bar(i, pct, bottom=base, width=0.72, color=cor,
               edgecolor="#f7f7f5", linewidth=2, zorder=2)
        if pct >= 8:
            ax.text(i, base + pct / 2, f"{pct:.0f}%", ha="center", va="center",
                    fontsize=10.5, color=txtcor)
        base += pct
    ax.text(i, 102.5, str(DATA[idade][3]), ha="center", va="bottom",
            fontsize=11, color="#333333", fontweight="bold")

ax.text(-0.62, 109.5, "mediana da idade do pai:", ha="left", va="bottom",
        fontsize=10.5, color="#555555")
ax.set_title("Quem são os pais (entre os declarados)", loc="left",
             fontsize=12.5, color="#333333", pad=26)
ax.text(1.0, -7, "mãe <14: estupro de vulnerável (art. 217-A)", ha="center",
        va="top", fontsize=10, color=RED)

ax.set_xticks(x)
ax.set_xticklabels([str(i) for i in idades], fontsize=12.5)
ax.set_xlabel("Idade da mãe (anos)", fontsize=13, labelpad=24)
ax.set_ylim(-2, 114)
ax.set_yticks([0, 50, 100])
ax.set_yticklabels(["0%", "50%", "100%"], fontsize=11)
for s in ("top", "right", "left", "bottom"):
    ax.spines[s].set_visible(False)
ax.tick_params(colors="#555555", length=0)

handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in COLORS]
fig.legend(handles, BANDS, loc="upper right", bbox_to_anchor=(0.97, 0.91),
           ncol=3, frameon=False, fontsize=11.5, labelcolor="#333333",
           columnspacing=1.6, handlelength=1.2)

fig.suptitle("Mães adolescentes, pais adultos: idade do pai por idade da mãe",
             x=0.055, y=0.975, ha="left", fontsize=18.5, fontweight="bold", color="#111111")
fig.text(0.055, 0.935,
         "Nascimentos do SINASC 2022 · a composição cobre só as DNs que declaram a idade "
         "do pai — provável viés de pai presente",
         fontsize=12.5, color="#555555")
fig.text(0.055, 0.012,
         "Fonte: SINASC/DataSUS 2022 (br_ms_sinasc.microdados) — idade_mae, idade_pai",
         fontsize=10.5, color="#777777")

fig.tight_layout(rect=(0.02, 0.03, 1, 0.88))
out = "dataviz/idade_pai_maes_adolescentes_2022.png"
fig.savefig(out, facecolor=fig.get_facecolor(), bbox_inches="tight")
print("ok:", out)
