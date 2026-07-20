#!/usr/bin/env python3
"""Baixo peso e prematuridade por idade da mãe x escolaridade (SINASC 2022).

Dois painéis: % de nascidos com <2,5 kg e % com <37 semanas, por idade da mãe
(13-45), uma linha por escolaridade (escolaridade_2010_mae: 0-2 fundamental ou
menos, 3 médio, 4-5 superior). Consulta o beelink via SSH em tempo de execução.
Linhas cortadas onde n é pequeno (médio <15 anos, superior <20 anos).
"""
import json
import os
import subprocess

import matplotlib.pyplot as plt

SQL = """SET enable_progress_bar=false;
SELECT
  CASE WHEN escolaridade_2010_mae IN ('0','1','2') THEN 'fund'
       WHEN escolaridade_2010_mae='3' THEN 'medio'
       ELSE 'sup' END AS esc,
  idade_mae AS idade, count(*) AS n,
  100.0*count(*) FILTER (WHERE peso < 2500)
      /count(*) FILTER (WHERE peso IS NOT NULL AND peso BETWEEN 200 AND 8000) AS baixo_peso,
  100.0*count(*) FILTER (WHERE semana_gestacao < 37)
      /count(*) FILTER (WHERE semana_gestacao IS NOT NULL) AS prematuro
FROM read_parquet('~/rodado/br_ms_sinasc/microdados/*.parquet')
WHERE ano=2022 AND idade_mae BETWEEN 13 AND 45
  AND escolaridade_2010_mae IN ('0','1','2','3','4','5')
GROUP BY 1,2 ORDER BY 1,2;
"""

host = os.environ.get("BEELINK_HOST", "beelink")
res = subprocess.run(["ssh", host, "~/bin/duckdb -json"],
                     input=SQL.encode(), capture_output=True, check=True)
rows = json.loads(res.stdout)

MIN_AGE = {"fund": 13, "medio": 15, "sup": 20}
series = {}
for r in rows:
    if r["idade"] >= MIN_AGE[r["esc"]]:
        series.setdefault(r["esc"], []).append((r["idade"], r["baixo_peso"], r["prematuro"]))

ORDER = ["fund", "medio", "sup"]
LABELS = {"fund": "Fundamental ou menos", "medio": "Ensino Médio",
          "sup": "Superior (incl. incompleto)"}
COLORS = {"fund": "#8ab1d6", "medio": "#3f79b4", "sup": "#134b86"}
PANELS = [(1, "Baixo peso ao nascer (menos de 2,5 kg)"),
          (2, "Prematuridade (menos de 37 semanas)")]

fig, axes = plt.subplots(1, 2, figsize=(13.5, 7.2), dpi=160, sharey=True)
fig.patch.set_facecolor("#f7f7f5")

for ax, (idx, titulo) in zip(axes, PANELS):
    ax.set_facecolor("#fcfcfb")
    for esc in ORDER:
        pts = series[esc]
        ax.plot([p[0] for p in pts], [p[idx] for p in pts],
                color=COLORS[esc], lw=2.2, label=LABELS[esc])
    ax.set_title(titulo, loc="left", fontsize=13.5, color="#333333", pad=12)
    ax.set_xlim(12.5, 45.5)
    ax.set_ylim(6, 22)
    ax.set_xticks(range(15, 46, 5))
    ax.set_xlabel("Idade da mãe (anos)", fontsize=12.5, labelpad=8)
    ax.grid(color="#e8e8e6", lw=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left", "bottom"):
        ax.spines[s].set_visible(False)
    ax.tick_params(colors="#555555", labelsize=11.5, length=0)

axes[0].set_ylabel("% dos nascimentos", fontsize=12.5, labelpad=8)
axes[0].legend(loc="upper center", frameon=False, fontsize=11.5, labelcolor="#333333")

fig.suptitle("O risco é da idade, não do diploma: bebês de mães adolescentes (e de 40+) nascem menores",
             x=0.05, y=0.99, ha="left", fontsize=17.5, fontweight="bold", color="#111111")
fig.text(0.05, 0.925,
         "Nascimentos do SINASC 2022 por idade e escolaridade da mãe · as três linhas quase "
         "coincidem: a curva em U é da idade",
         fontsize=12.5, color="#555555")
fig.text(0.05, 0.015,
         "Fonte: SINASC/DataSUS 2022 (br_ms_sinasc.microdados) — peso, semana_gestacao, idade_mae, "
         "escolaridade_2010_mae · linhas cortadas onde n < ~5 mil/idade",
         fontsize=10, color="#777777")

fig.tight_layout(rect=(0.01, 0.04, 1, 0.88))
out = "dataviz/peso_prematuridade_idade_mae_2022.png"
fig.savefig(out, facecolor=fig.get_facecolor(), bbox_inches="tight")
print("ok:", out)
