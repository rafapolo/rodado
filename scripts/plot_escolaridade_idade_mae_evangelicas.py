#!/usr/bin/env python3
"""Ridgeline: distribuição da idade da mãe por nível de instrução — só evangélicas.

Dados do Censo 2010 (br_ibge_censo_demografico.microdados_pessoa_2010, via
beelink): mulheres evangélicas (v6121 entre 210 e 499 — missão, pentecostal e
não determinada; faixas validadas contra os totais publicados: 7,69/25,37/9,22 mi)
com último filho menor de 1 ano (v6660=0, v6633>=1), idade = v6036, nível de
instrução = v6400 (1-4), contagens ponderadas por peso_amostral, idades 10-55.
"""
import matplotlib.pyplot as plt
import numpy as np

DATA = {
    "1": [(10,165),(11,219),(12,243),(13,627),(14,2000),(15,4600),(16,7896),(17,9257),(18,10318),(19,10271),(20,10514),(21,11223),(22,10478),(23,10016),(24,10630),(25,10552),(26,9898),(27,10352),(28,9563),(29,9045),(30,8177),(31,7690),(32,7102),(33,6682),(34,6015),(35,5641),(36,4789),(37,4719),(38,3528),(39,2939),(40,2777),(41,1943),(42,1476),(43,1142),(44,702),(45,595),(46,427),(47,306),(48,221),(49,302),(50,218),(51,205),(52,99),(53,175),(54,157),(55,192)],
    "2": [(11,71),(12,100),(13,154),(14,393),(15,1914),(16,4551),(17,8150),(18,9698),(19,10781),(20,11361),(21,10900),(22,10413),(23,9841),(24,9706),(25,8470),(26,7627),(27,8237),(28,6874),(29,6208),(30,5792),(31,4636),(32,4580),(33,3732),(34,2929),(35,2831),(36,2550),(37,2082),(38,1902),(39,1468),(40,1076),(41,624),(42,488),(43,323),(44,233),(45,139),(46,93),(47,60),(48,101),(49,44),(50,55),(51,69),(52,35),(53,24),(54,3)],
    "3": [(13,62),(14,59),(15,85),(16,369),(17,1276),(18,3637),(19,7323),(20,10694),(21,14285),(22,15663),(23,15070),(24,16899),(25,15998),(26,16022),(27,16764),(28,16523),(29,14221),(30,12634),(31,11110),(32,9611),(33,8170),(34,7395),(35,5703),(36,4456),(37,3791),(38,3145),(39,2118),(40,1815),(41,1332),(42,967),(43,350),(44,336),(45,174),(46,145),(47,150),(48,44),(49,48),(50,51),(51,76),(52,18),(53,19),(54,22),(55,31)],
    "4": [(18,22),(19,73),(20,147),(21,366),(22,544),(23,1110),(24,1376),(25,1997),(26,2472),(27,3055),(28,3774),(29,3518),(30,3887),(31,3412),(32,3366),(33,3253),(34,2470),(35,2744),(36,2377),(37,1810),(38,1285),(39,981),(40,979),(41,414),(42,393),(43,265),(44,68),(45,39),(46,168),(47,8),(48,9),(49,17),(50,49),(51,9),(53,10),(55,10)],
}

LABELS = {
    "1": "Sem instrução ou fundamental incompleto",
    "2": "Fundamental completo ou médio incompleto",
    "3": "Médio completo ou superior incompleto",
    "4": "Superior completo",
}
COLORS = {"1": "#8ab1d6", "2": "#5b8fc4", "3": "#2f6aad", "4": "#134b86"}

def fmt_pop(v):
    return f"{v/1e6:.1f} mi".replace(".", ",") if v >= 1e6 else f"{v/1e3:.0f} mil"

fig, axes = plt.subplots(4, 1, figsize=(12.5, 9.2), dpi=160, sharex=True)
fig.patch.set_facecolor("#f7f7f5")

for ax, key in zip(axes, "1234"):
    ages = np.array([a for a, _ in DATA[key]], float)
    ns = np.array([n for _, n in DATA[key]], float)
    pct = ns / ns.sum() * 100
    media = (ages * ns).sum() / ns.sum()

    ax.set_facecolor("#f7f7f5")
    ax.fill_between(ages, pct, color=COLORS[key], alpha=0.85, lw=0)
    ax.plot(ages, pct, color=COLORS[key], lw=2)
    ax.axvline(media, color="#333333", ls="--", lw=1.3, ymax=0.82)
    ax.text(media + 0.4, 7.0, f"média {media:.1f} anos".replace(".", ","),
            fontsize=12, color="#222222", fontweight="bold")
    ax.text(11.5, 7.0, f"{LABELS[key]}", fontsize=12.5, color="#333333")
    ax.text(11.5, 5.7, f"{fmt_pop(ns.sum())} mães", fontsize=10.5, color="#888888")

    ax.set_xlim(11, 50)
    ax.set_ylim(0, 8.9)
    ax.set_yticks([])
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#dddddb")
    ax.tick_params(colors="#555555", labelsize=11.5, length=0)
    ax.grid(axis="x", color="#e8e8e6", lw=0.8)
    ax.set_axisbelow(True)

axes[-1].set_xlabel("Idade da mãe (anos)", fontsize=13, labelpad=10)
axes[-1].set_xticks(range(15, 51, 5))

fig.suptitle("Mães evangélicas: quanto mais estudo, mais tarde os filhos",
             x=0.065, y=0.97, ha="left", fontsize=19, fontweight="bold", color="#111111")
fig.text(0.065, 0.925,
         "Mulheres evangélicas com filho menor de 1 ano no Censo 2010 · cada curva é a "
         "distribuição da idade (soma 100% por painel)",
         fontsize=13, color="#555555")
fig.text(0.065, 0.012,
         "Fonte: Censo Demográfico 2010 (IBGE), microdados de pessoa — V6036, V6400, V6660, V6121",
         fontsize=10.5, color="#777777")

fig.tight_layout(rect=(0.01, 0.03, 1, 0.91))
out = "dataviz/escolaridade_idade_mae_evangelicas.png"
fig.savefig(out, facecolor=fig.get_facecolor(), bbox_inches="tight")
print("ok:", out)
