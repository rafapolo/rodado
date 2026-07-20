#!/usr/bin/env python3
"""Matriz de bolhas: idade da mãe (11-18) x idade do pai, SINASC 2022.

Cada bolha é uma célula (idade da mãe, idade do pai) com área proporcional ao
número de nascimentos entre as DNs com idade do pai declarada (~20%).
Referências: diagonal = pai da mesma idade; linha em 18 = pai adulto; faixa
vermelha = mãe <14 (estupro de vulnerável, art. 217-A). Pais de 50+ agrupados.
Consulta o beelink via SSH em tempo de execução.
"""
import json
import os
import subprocess

import matplotlib.pyplot as plt

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

MEDIANAS = {11: 25, 12: 19, 13: 19, 14: 19, 15: 20, 16: 20, 17: 21, 18: 22}
N_MAX = max(r["n"] for r in rows)
S_MAX = 260.0

def size(n):
    return max(S_MAX * n / N_MAX, 5.0)

C_ADULTO, C_MENOR, RED = "#1f77b4", "#a3c0dd", "#b03a3a"

fig, ax = plt.subplots(figsize=(11.5, 10.5), dpi=160)
fig.patch.set_facecolor("#f7f7f5")
ax.set_facecolor("#fcfcfb")

# faixa legal: mãe <14
ax.axvspan(10.55, 13.5, color=RED, alpha=0.06, zorder=0)
ax.text(12.0, 51.8, "mãe <14: estupro de vulnerável (art. 217-A)",
        ha="center", fontsize=10.5, color=RED)

# referências
ax.plot([10.5, 18.5], [10.5, 18.5], ls="--", color="#999999", lw=1.4, zorder=1)
ax.text(11.6, 12.6, "pai da\nmesma idade", fontsize=10, color="#777777",
        ha="right", linespacing=1.2)
ax.axhline(17.5, color="#555555", lw=1.2, zorder=1)
ax.text(18.62, 18.0, "pai adulto (18+)", fontsize=10.5, color="#555555", va="bottom")

for r in rows:
    cor = C_ADULTO if r["idade_pai"] >= 18 else C_MENOR
    ax.scatter(r["idade_mae"], r["idade_pai"], s=size(r["n"]), color=cor,
               alpha=0.85, edgecolor="white", linewidth=0.6, zorder=3)

# mediana da idade do pai por coluna
for mae, med in MEDIANAS.items():
    ax.plot(mae, med, marker="_", color="#111111", markersize=17,
            markeredgewidth=2.2, zorder=4)
ax.text(11.0, 27.2, "— mediana da\n    idade do pai", fontsize=10, color="#111111",
        ha="left", linespacing=1.3)

# legenda de tamanho
for n, yy in [(2000, 45.5), (500, 42.0), (50, 39.2)]:
    ax.scatter(19.6, yy, s=size(n), color="#c9c9c6", edgecolor="#aaaaaa", zorder=2)
    ax.text(19.6, yy - 1.8, f"{n:,}".replace(",", "."), ha="center", fontsize=9.5,
            color="#555555")
ax.text(19.6, 48.2, "nascimentos", ha="center", fontsize=10.5, color="#333333")

ax.set_xlim(10.5, 20.4)
ax.set_ylim(11, 53)
ax.set_xticks(range(11, 19))
ax.set_yticks(list(range(15, 50, 5)) + [50])
ax.set_yticklabels(["15", "20", "25", "30", "35", "40", "45", "50+"], fontsize=11.5)
ax.set_xlabel("Idade da mãe (anos)", fontsize=13, labelpad=10)
ax.set_ylabel("Idade do pai (anos)", fontsize=13, labelpad=10)
ax.grid(color="#ececea", lw=0.7)
ax.set_axisbelow(True)
for s in ("top", "right", "left", "bottom"):
    ax.spines[s].set_visible(False)
ax.tick_params(colors="#555555", labelsize=12, length=0)

fig.suptitle("Cada bolha, um par: idade do pai x idade da mãe adolescente",
             x=0.06, y=0.97, ha="left", fontsize=18.5, fontweight="bold", color="#111111")
fig.text(0.06, 0.932,
         "Nascimentos do SINASC 2022 com idade do pai declarada (~20% das DNs — provável "
         "viés de pai presente) · azul-escuro = pai adulto",
         fontsize=12.5, color="#555555")
fig.text(0.06, 0.012,
         "Fonte: SINASC/DataSUS 2022 (br_ms_sinasc.microdados) — idade_mae, idade_pai · "
         "pais de 50 ou mais agrupados em 50+",
         fontsize=10.5, color="#777777")

fig.tight_layout(rect=(0.02, 0.03, 1, 0.9))
out = "dataviz/matriz_idade_pai_mae_2022.png"
fig.savefig(out, facecolor=fig.get_facecolor(), bbox_inches="tight")
print("ok:", out)
