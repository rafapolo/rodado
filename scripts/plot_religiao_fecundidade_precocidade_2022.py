#!/usr/bin/env python3
"""Bolhas 2022: maternidade precoce x filhos por mulher (12+), por grupo de religião.

Versão SEM recorte de idade na fecundidade: y = filhos nascidos vivos totais /
mulheres de 12+ (linha 'Total' da tabela), em vez das mulheres de 45-49.
Medida sensível à estrutura etária de cada grupo (grupos jovens como 'Sem
religião' ficam baixos mesmo com maternidade precoce) — por isso a correlação
com precocidade desaparece (r ponderado 0,08) e não há linha de tendência.
Fontes (via beelink):
read_parquet('~/rodado/br_ibge_censo2022_religiao/mulheres_fecundidade_completa/*.parquet')
e populacao_religiao (id_localidade nível Brasil).
"""
import matplotlib.pyplot as plt

# religiao, pop 10+, filhos por mulher 12+, filhos por mulher 20-24, cor
DATA = [
    ("Católica",             100_216_153, 1.739, 0.437, "#1f77b4"),
    ("Evangélicas",           47_418_024, 1.822, 0.529, "#2ca02c"),
    ("Sem religião",          16_385_342, 1.235, 0.538, "#ff7f0e"),
    ("Outras religiosidades",  7_079_101, 1.502, 0.406, "#e377c2"),
    ("Espírita",               3_257_455, 1.315, 0.202, "#9467bd"),
    ("Umbanda e Candomblé",    1_849_824, 1.276, 0.428, "#00a0a0"),
]

LABEL_POS = {
    "Católica":              (-0.033, 0.0, "right"),
    "Evangélicas":           (0.022, 0.012, "left"),
    "Sem religião":          (0.018, -0.012, "left"),
    "Outras religiosidades": (-0.015, 0.0, "right"),
    "Espírita":              (0.015, 0.025, "left"),
    "Umbanda e Candomblé":   (0.008, -0.045, "left"),
}

def area(pop, max_pop=100_216_153, max_pt2=3400):
    return pop / max_pop * max_pt2

fig, ax = plt.subplots(figsize=(12.5, 8.75), dpi=160)
fig.patch.set_facecolor("#f7f7f5")
ax.set_facecolor("#fcfcfb")

for name, pop, y, x, c in DATA:
    ax.scatter(x, y, s=area(pop), color=c, edgecolor="white", linewidth=1.5, zorder=3)
for name, pop, y, x, c in DATA:
    dx, dy, ha = LABEL_POS[name]
    ax.annotate(name, (x + dx, y + dy), ha=ha, va="center",
                fontsize=12, color="#333333", zorder=4)

# legenda de tamanho (canto superior esquerdo, longe dos pontos)
ax.text(0.245, 1.935, "População (10 anos ou mais)", fontsize=12, color="#333333", ha="center")
for pop, lbl, xx in [(2_000_000, "2 mi", 0.20), (20_000_000, "20 mi", 0.245),
                     (100_216_153, "100,2 mi", 0.31)]:
    ax.scatter(xx, 1.85, s=area(pop), color="#cccccc", edgecolor="#bbbbbb", zorder=2)
    ax.text(xx, 1.775, lbl, fontsize=11, ha="center", color="#333333")

ax.set_xlim(0.15, 0.60)
ax.set_ylim(1.10, 2.00)
ax.set_xlabel("Filhos já tidos por mulher de 20 a 24 anos (maternidade precoce)",
              fontsize=13, labelpad=10)
ax.set_ylabel("Filhos por mulher — todas as mulheres de 12+ (sem recorte de idade)",
              fontsize=13, labelpad=10)
ax.grid(axis="both", color="#e8e8e6", lw=0.8)
for s in ("top", "right", "left", "bottom"):
    ax.spines[s].set_visible(False)
ax.tick_params(colors="#555555", labelsize=11.5, length=0)

fig.suptitle("Sem recorte de idade, a estrutura etária manda: religião e filhos por mulher em 2022",
             x=0.065, y=0.965, ha="left", fontsize=18, fontweight="bold", color="#111111")
ax.set_title("Grupos de religião do Censo 2022 · bolha = população de 10+ · grupos jovens "
             "(Sem religião) ficam baixos mesmo com maternidade precoce",
             loc="left", fontsize=12.5, color="#555555", pad=14)
fig.text(0.065, 0.015,
         "Fonte: Censo Demográfico 2022 (IBGE), tabelas SIDRA de fecundidade por religião — "
         "soma dos municípios · sem tendência: r ponderado = 0,08",
         fontsize=10.5, color="#777777")

fig.tight_layout(rect=(0.01, 0.03, 1, 0.93))
out = "dataviz/religiao_fecundidade_precocidade_2022.png"
fig.savefig(out, facecolor=fig.get_facecolor(), bbox_inches="tight")
print("ok:", out)
