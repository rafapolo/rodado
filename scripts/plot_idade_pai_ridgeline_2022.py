#!/usr/bin/env python3
"""Ridgeline: distribuição da idade do pai por idade da mãe adolescente (2022).

Um painel por idade da mãe (13 ou menos, 14, 15, 16, 17, 18), cada um com a
distribuição da idade do pai entre as DNs que a declaram (~20%), mediana
tracejada e linha vertical compartilhada em pai = 18 anos, com o % de pais
adultos anotado. Mães de 11-13 agregadas (limiar do art. 217-A).
Consulta o beelink via SSH em tempo de execução.
"""
import json
import os
import subprocess

import matplotlib.pyplot as plt
import numpy as np

SQL = """SET enable_progress_bar=false;
SELECT idade_mae, least(idade_pai, 50) AS idade_pai, count(*) AS n
FROM read_parquet('~/rodado/br_ms_sinasc/microdados/*.parquet')
WHERE ano=2022 AND idade_mae BETWEEN 11 AND 18 AND idade_pai BETWEEN 10 AND 80
GROUP BY 1,2 ORDER BY 1,2;
"""

host = os.environ.get("BEELINK_HOST", "beelink")
res = subprocess.run(["ssh", host, "~/bin/duckdb -json"],
                     input=SQL.encode(), capture_output=True, check=True)
rows = json.loads(res.stdout)

TOTAIS = {13: 3563, 14: 10685, 15: 25593, 16: 43718, 17: 60000, 18: 76223}

counts = {}
for r in rows:
    mae = min(r["idade_mae"], 13) if r["idade_mae"] <= 13 else r["idade_mae"]
    mae = 13 if r["idade_mae"] <= 13 else r["idade_mae"]
    counts.setdefault(mae, {})
    counts[mae][r["idade_pai"]] = counts[mae].get(r["idade_pai"], 0) + r["n"]

PANELS = [13, 14, 15, 16, 17, 18]
LABELS = {13: "Mãe com 13 anos ou menos", 14: "Mãe de 14 anos", 15: "Mãe de 15 anos",
          16: "Mãe de 16 anos", 17: "Mãe de 17 anos", 18: "Mãe de 18 anos"}
COLORS = {13: "#a3c0dd", 14: "#8ab1d6", 15: "#699bc9", 16: "#4a82b8",
          17: "#2f68ac", 18: "#134b86"}
RED = "#b03a3a"

def fmt(v):
    return f"{v:,}".replace(",", ".")

fig, axes = plt.subplots(len(PANELS), 1, figsize=(12.5, 12.2), dpi=160, sharex=True)
fig.patch.set_facecolor("#f7f7f5")

for ax, mae in zip(axes, PANELS):
    ages = np.array(sorted(counts[mae]), float)
    ns = np.array([counts[mae][a] for a in sorted(counts[mae])], float)
    decl = ns.sum()
    pct = ns / decl * 100
    exp = np.repeat(ages, ns.astype(int))
    mediana = float(np.median(exp))
    pct_adulto = 100.0 * ns[ages >= 18].sum() / decl

    ax.set_facecolor("#f7f7f5")
    ax.fill_between(ages, pct, color=COLORS[mae], alpha=0.85, lw=0)
    ax.plot(ages, pct, color=COLORS[mae], lw=2)
    ymax = pct.max() * 1.45
    ax.set_ylim(0, ymax)

    ax.axvline(17.5, color="#555555", lw=1.2, zorder=4)
    ax.axvline(mediana, color="#222222", ls="--", lw=1.3, ymax=0.62, zorder=4)
    ax.text(mediana + 0.5, ymax * 0.84, f"mediana {mediana:.0f}",
            fontsize=11, color="#222222", fontweight="bold")

    ax.text(49.6, ymax * 0.84, LABELS[mae], ha="right", fontsize=13, color="#333333")
    ax.text(49.6, ymax * 0.62, f"{pct_adulto:.0f}% dos pais são adultos",
            ha="right", fontsize=11.5, color="#111111", fontweight="bold")
    ax.text(49.6, ymax * 0.44, f"{fmt(int(decl))} pais declarados "
            f"de {fmt(TOTAIS[mae])} nascimentos", ha="right", fontsize=9.5, color="#888888")
    if mae == 13:
        ax.text(49.6, ymax * 0.26, "mãe <14 = estupro de vulnerável (art. 217-A)",
                ha="right", fontsize=9.5, color=RED)

    ax.set_xlim(12, 50)
    ax.set_yticks([])
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#dddddb")
    ax.tick_params(colors="#555555", labelsize=11.5, length=0)
    ax.grid(axis="x", color="#e8e8e6", lw=0.8)
    ax.set_axisbelow(True)

axes[0].text(17.9, axes[0].get_ylim()[1] * 1.06, "pai adulto (18+) →",
             fontsize=10.5, color="#555555")
axes[-1].set_xlabel("Idade do pai (anos)", fontsize=13, labelpad=10)
axes[-1].set_xticks(range(15, 51, 5))

fig.suptitle("Quem são os pais: a distribuição da idade do pai, mãe a mãe",
             x=0.065, y=0.975, ha="left", fontsize=18.5, fontweight="bold", color="#111111")
fig.text(0.065, 0.94,
         "Nascimentos do SINASC 2022 com idade do pai declarada (~20% das DNs — provável "
         "viés de pai presente) · cada curva soma 100%",
         fontsize=12.5, color="#555555")
fig.text(0.065, 0.011,
         "Fonte: SINASC/DataSUS 2022 (br_ms_sinasc.microdados) — idade_mae, idade_pai · "
         "pais de 50+ agrupados · mães de 11 a 13 agregadas",
         fontsize=10.5, color="#777777")

fig.tight_layout(rect=(0.01, 0.025, 1, 0.925))
out = "dataviz/idade_pai_maes_adolescentes_ridgeline_2022.png"
fig.savefig(out, facecolor=fig.get_facecolor(), bbox_inches="tight")
print("ok:", out)
