#!/usr/bin/env python3
"""Baixo peso e prematuridade por idade da mãe x raça/cor (SINASC 2022).

Gêmeo de plot_peso_prematuridade_idade_mae_2022.py trocando escolaridade por
raca_cor_mae (1 Branca, 2 Preta, 4 Parda, 5 Indígena; Amarela fica de fora por
n insuficiente por idade). Consulta o beelink via SSH em tempo de execução.
Pontos com n < 200 nascimentos são descartados (poda as pontas ruidosas).
"""
import json
import os
import subprocess

import matplotlib.pyplot as plt

SQL = """SET enable_progress_bar=false;
SELECT raca_cor_mae AS raca, idade_mae AS idade, count(*) AS n,
  100.0*count(*) FILTER (WHERE peso < 2500)
      /count(*) FILTER (WHERE peso IS NOT NULL AND peso BETWEEN 200 AND 8000) AS baixo_peso,
  100.0*count(*) FILTER (WHERE semana_gestacao < 37)
      /count(*) FILTER (WHERE semana_gestacao IS NOT NULL) AS prematuro
FROM read_parquet('~/rodado/br_ms_sinasc/microdados/*.parquet')
WHERE ano=2022 AND idade_mae BETWEEN 13 AND 45 AND raca_cor_mae IN ('1','2','4','5')
GROUP BY 1,2 ORDER BY 1,2;
"""

host = os.environ.get("BEELINK_HOST", "beelink")
res = subprocess.run(["ssh", host, "~/bin/duckdb -json"],
                     input=SQL.encode(), capture_output=True, check=True)
rows = json.loads(res.stdout)

series = {}
for r in rows:
    if r["n"] >= 200:
        series.setdefault(r["raca"], []).append((r["idade"], r["baixo_peso"], r["prematuro"]))

ORDER = ["1", "4", "2", "5"]
LABELS = {"1": "Branca", "4": "Parda", "2": "Preta", "5": "Indígena"}
COLORS = {"1": "#1f77b4", "4": "#ff7f0e", "2": "#e377c2", "5": "#2e7d32"}
PANELS = [(1, "Baixo peso ao nascer (menos de 2,5 kg)"),
          (2, "Prematuridade (menos de 37 semanas)")]

fig, axes = plt.subplots(1, 2, figsize=(13.5, 7.2), dpi=160, sharey=True)
fig.patch.set_facecolor("#f7f7f5")

for ax, (idx, titulo) in zip(axes, PANELS):
    ax.set_facecolor("#fcfcfb")
    for raca in ORDER:
        pts = series[raca]
        ax.plot([p[0] for p in pts], [p[idx] for p in pts],
                color=COLORS[raca], lw=2.2, label=LABELS[raca])
    ax.set_title(titulo, loc="left", fontsize=13.5, color="#333333", pad=12)
    ax.set_xlim(12.5, 45.5)
    ax.set_ylim(5, 27)
    ax.set_xticks(range(15, 46, 5))
    ax.set_xlabel("Idade da mãe (anos)", fontsize=12.5, labelpad=8)
    ax.grid(color="#e8e8e6", lw=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left", "bottom"):
        ax.spines[s].set_visible(False)
    ax.tick_params(colors="#555555", labelsize=11.5, length=0)

axes[0].set_ylabel("% dos nascimentos", fontsize=12.5, labelpad=8)
axes[0].legend(loc="upper center", frameon=False, fontsize=11.5, labelcolor="#333333")

fig.suptitle("Idade pesa para todas; raça desloca a curva: baixo peso e prematuridade por raça/cor da mãe",
             x=0.05, y=0.99, ha="left", fontsize=17, fontweight="bold", color="#111111")
fig.text(0.05, 0.925,
         "Nascimentos do SINASC 2022 por idade e raça/cor da mãe · Amarela omitida (n insuficiente "
         "por idade)",
         fontsize=12.5, color="#555555")
fig.text(0.05, 0.015,
         "Fonte: SINASC/DataSUS 2022 (br_ms_sinasc.microdados) — peso, semana_gestacao, idade_mae, "
         "raca_cor_mae · pontos com n < 200 descartados",
         fontsize=10, color="#777777")

fig.tight_layout(rect=(0.01, 0.04, 1, 0.88))
out = "dataviz/peso_prematuridade_idade_raca_2022.png"
fig.savefig(out, facecolor=fig.get_facecolor(), bbox_inches="tight")
print("ok:", out)
