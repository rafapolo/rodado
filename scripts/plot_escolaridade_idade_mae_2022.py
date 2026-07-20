#!/usr/bin/env python3
"""Ridgeline 2022: distribuição da idade da mãe por escolaridade (SINASC).

Versão 2022 de plot_escolaridade_idade_mae.py, usando nascimentos reais do
SINASC (br_ms_sinasc.microdados, ano=2022) em vez do Censo: idade_mae x
escolaridade_2010_mae. Consulta o beelink em tempo de execução via SSH
(BEELINK_HOST, default 'beelink'). Níveis 0 e 1 são agregados num painel só.
"""
import json
import os
import subprocess

import matplotlib.pyplot as plt
import numpy as np

SQL = """SET enable_progress_bar=false;
SELECT escolaridade_2010_mae AS esc, idade_mae AS idade, count(*) AS n
FROM read_parquet('~/rodado/br_ms_sinasc/microdados/*.parquet')
WHERE ano=2022 AND idade_mae BETWEEN 5 AND 65  -- exclui só 0 (erro) e 99 (ignorado)
  AND escolaridade_2010_mae IN ('0','1','2','3','4','5')
GROUP BY 1,2 ORDER BY 1,2;
"""

host = os.environ.get("BEELINK_HOST", "beelink")
res = subprocess.run(["ssh", host, "~/bin/duckdb -json"],
                     input=SQL.encode(), capture_output=True, check=True)
rows = json.loads(res.stdout)

# agrega 0+1 num painel só
PANEL_OF = {"0": "01", "1": "01", "2": "2", "3": "3", "4": "4", "5": "5"}
counts = {}
for r in rows:
    key = PANEL_OF[r["esc"]]
    counts.setdefault(key, {})
    counts[key][r["idade"]] = counts[key].get(r["idade"], 0) + r["n"]

PANELS = ["01", "2", "3", "4", "5"]
LABELS = {
    "01": "Sem escolaridade ou Fundamental I (1ª–4ª)",
    "2": "Fundamental II (5ª–8ª)",
    "3": "Ensino Médio",
    "4": "Superior incompleto",
    "5": "Superior completo",
}
COLORS = {"01": "#a3c0dd", "2": "#7ba3cd", "3": "#5586bd", "4": "#2f68ac", "5": "#134b86"}

def fmt_n(v):
    return f"{v/1e6:.2f} mi".replace(".", ",") if v >= 1e6 else f"{v/1e3:.0f} mil"

fig, axes = plt.subplots(5, 1, figsize=(12.5, 10.8), dpi=160, sharex=True)
fig.patch.set_facecolor("#f7f7f5")

for ax, key in zip(axes, PANELS):
    ages = np.array(sorted(counts[key]), float)
    ns = np.array([counts[key][a] for a in sorted(counts[key])], float)
    pct = ns / ns.sum() * 100
    media = (ages * ns).sum() / ns.sum()

    ax.set_facecolor("#f7f7f5")
    ax.fill_between(ages, pct, color=COLORS[key], alpha=0.85, lw=0)
    ax.plot(ages, pct, color=COLORS[key], lw=2)
    ax.axvline(media, color="#333333", ls="--", lw=1.3, ymax=0.80)
    ax.text(media + 0.4, 6.7, f"média {media:.1f} anos".replace(".", ","),
            fontsize=12, color="#222222", fontweight="bold",
            bbox=dict(facecolor="#f7f7f5", edgecolor="none", pad=1.5))
    ax.text(9.5, 6.7, LABELS[key], fontsize=12.5, color="#333333")
    ax.text(9.5, 5.4, f"{fmt_n(ns.sum())} nascimentos", fontsize=10.5, color="#888888")

    ax.set_xlim(9, 55)
    ax.set_ylim(0, 8.4)
    ax.set_yticks([])
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#dddddb")
    ax.tick_params(colors="#555555", labelsize=11.5, length=0)
    ax.grid(axis="x", color="#e8e8e6", lw=0.8)
    ax.set_axisbelow(True)

axes[-1].set_xlabel("Idade da mãe (anos)", fontsize=13, labelpad=10)
axes[-1].set_xticks(range(10, 56, 5))

fig.suptitle("Quanto mais estudo, mais tarde os filhos: idade da mãe por escolaridade (2022)",
             x=0.065, y=0.97, ha="left", fontsize=18.5, fontweight="bold", color="#111111")
fig.text(0.065, 0.932,
         "Nascimentos registrados no SINASC em 2022 · cada curva é a distribuição "
         "da idade da mãe (soma 100% por painel)",
         fontsize=13, color="#555555")
fig.text(0.065, 0.012,
         "Fonte: SINASC/DataSUS 2022 (br_ms_sinasc.microdados) — idade_mae, escolaridade_2010_mae",
         fontsize=10.5, color="#777777")

fig.tight_layout(rect=(0.01, 0.03, 1, 0.92))
out = "dataviz/escolaridade_idade_mae_2022.png"
fig.savefig(out, facecolor=fig.get_facecolor(), bbox_inches="tight")
print("ok:", out)
