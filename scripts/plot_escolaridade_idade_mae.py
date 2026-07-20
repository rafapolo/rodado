#!/usr/bin/env python3
"""Ridgeline: distribuição da idade da mãe por nível de instrução.

Dados do Censo 2010 (br_ibge_censo_demografico.microdados_pessoa_2010, via
beelink): mulheres com último filho menor de 1 ano (v6660=0, v6633>=1),
idade = v6036, nível de instrução = v6400 (1-4), contagens ponderadas por
peso_amostral, idades 10-55.
"""
import matplotlib.pyplot as plt
import numpy as np

DATA = {
    "1": [(10,1172),(11,1458),(12,1333),(13,2933),(14,10548),(15,24413),(16,40394),(17,46522),(18,51134),(19,51013),(20,51127),(21,51501),(22,51015),(23,48260),(24,46554),(25,44451),(26,41224),(27,41706),(28,39796),(29,37431),(30,35306),(31,31648),(32,29918),(33,26130),(34,24231),(35,22596),(36,19023),(37,18048),(38,14174),(39,12649),(40,11241),(41,7902),(42,6488),(43,4873),(44,3267),(45,2791),(46,1821),(47,1384),(48,856),(49,1057),(50,936),(51,794),(52,701),(53,741),(54,718),(55,883)],
    "2": [(10,90),(11,431),(12,397),(13,443),(14,1756),(15,7876),(16,20280),(17,36650),(18,41277),(19,44167),(20,45066),(21,43677),(22,42198),(23,37572),(24,35055),(25,31236),(26,28011),(27,27201),(28,24026),(29,21492),(30,20020),(31,16223),(32,14334),(33,12312),(34,10353),(35,9464),(36,8226),(37,7423),(38,5959),(39,4563),(40,3726),(41,2329),(42,1917),(43,1124),(44,1011),(45,500),(46,275),(47,252),(48,223),(49,183),(50,100),(51,168),(52,67),(53,80),(54,55),(55,93)],
    "3": [(13,141),(14,141),(15,306),(16,1340),(17,5325),(18,16336),(19,28528),(20,41075),(21,51572),(22,54307),(23,55691),(24,56948),(25,55065),(26,53451),(27,54134),(28,54335),(29,48018),(30,43897),(31,37438),(32,32142),(33,26555),(34,24148),(35,20091),(36,15526),(37,14001),(38,10689),(39,8246),(40,6520),(41,4639),(42,3179),(43,1764),(44,1224),(45,770),(46,543),(47,420),(48,341),(49,153),(50,264),(51,224),(52,134),(53,116),(54,92),(55,79)],
    "4": [(16,9),(17,1),(18,130),(19,223),(20,471),(21,1393),(22,2815),(23,4350),(24,6337),(25,7805),(26,10959),(27,14081),(28,17244),(29,17740),(30,20000),(31,20337),(32,19324),(33,17888),(34,16053),(35,15267),(36,12737),(37,10212),(38,7155),(39,6195),(40,5121),(41,3060),(42,2547),(43,1493),(44,904),(45,456),(46,378),(47,222),(48,145),(49,198),(50,91),(51,93),(52,43),(53,60),(54,22),(55,71)],
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
    ax.text(media + 0.4, 6.6, f"média {media:.1f} anos".replace(".", ","),
            fontsize=12, color="#222222", fontweight="bold")
    ax.text(11.5, 6.6, f"{LABELS[key]}", fontsize=12.5, color="#333333")
    ax.text(11.5, 5.4, f"{fmt_pop(ns.sum())} mães", fontsize=10.5, color="#888888")

    ax.set_xlim(11, 50)
    ax.set_ylim(0, 8.4)
    ax.set_yticks([])
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#dddddb")
    ax.tick_params(colors="#555555", labelsize=11.5, length=0)
    ax.grid(axis="x", color="#e8e8e6", lw=0.8)
    ax.set_axisbelow(True)

axes[-1].set_xlabel("Idade da mãe (anos)", fontsize=13, labelpad=10)
axes[-1].set_xticks(range(15, 51, 5))

fig.suptitle("Quanto mais estudo, mais tarde os filhos: idade da mãe por escolaridade",
             x=0.065, y=0.97, ha="left", fontsize=19, fontweight="bold", color="#111111")
fig.text(0.065, 0.925,
         "Mulheres com filho menor de 1 ano no Censo 2010 · cada curva é a distribuição "
         "da idade (soma 100% por painel)",
         fontsize=13, color="#555555")
fig.text(0.065, 0.012,
         "Fonte: Censo Demográfico 2010 (IBGE), microdados de pessoa — V6036, V6400, V6660",
         fontsize=10.5, color="#777777")

fig.tight_layout(rect=(0.01, 0.03, 1, 0.91))
out = "dataviz/escolaridade_idade_mae.png"
fig.savefig(out, facecolor=fig.get_facecolor(), bbox_inches="tight")
print("ok:", out)
