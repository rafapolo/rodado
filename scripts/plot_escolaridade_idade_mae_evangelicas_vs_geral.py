#!/usr/bin/env python3
"""Ridgeline comparativo: idade da mãe por instrução — evangélicas vs. todas.

Dados do Censo 2010 (br_ibge_censo_demografico.microdados_pessoa_2010, via
beelink): mulheres com último filho menor de 1 ano (v6660=0, v6633>=1),
idade = v6036, nível de instrução = v6400 (1-4), ponderação por peso_amostral,
idades 10-55. EVANG = recorte v6121 entre 210 e 499 (missão, pentecostal e não
determinada; faixas validadas contra os totais publicados do Censo 2010);
GERAL = todas as mulheres (mesmos dados de plot_escolaridade_idade_mae.py).
"""
import matplotlib.pyplot as plt
import numpy as np

EVANG = {
    "1": [(10,165),(11,219),(12,243),(13,627),(14,2000),(15,4600),(16,7896),(17,9257),(18,10318),(19,10271),(20,10514),(21,11223),(22,10478),(23,10016),(24,10630),(25,10552),(26,9898),(27,10352),(28,9563),(29,9045),(30,8177),(31,7690),(32,7102),(33,6682),(34,6015),(35,5641),(36,4789),(37,4719),(38,3528),(39,2939),(40,2777),(41,1943),(42,1476),(43,1142),(44,702),(45,595),(46,427),(47,306),(48,221),(49,302),(50,218),(51,205),(52,99),(53,175),(54,157),(55,192)],
    "2": [(11,71),(12,100),(13,154),(14,393),(15,1914),(16,4551),(17,8150),(18,9698),(19,10781),(20,11361),(21,10900),(22,10413),(23,9841),(24,9706),(25,8470),(26,7627),(27,8237),(28,6874),(29,6208),(30,5792),(31,4636),(32,4580),(33,3732),(34,2929),(35,2831),(36,2550),(37,2082),(38,1902),(39,1468),(40,1076),(41,624),(42,488),(43,323),(44,233),(45,139),(46,93),(47,60),(48,101),(49,44),(50,55),(51,69),(52,35),(53,24),(54,3)],
    "3": [(13,62),(14,59),(15,85),(16,369),(17,1276),(18,3637),(19,7323),(20,10694),(21,14285),(22,15663),(23,15070),(24,16899),(25,15998),(26,16022),(27,16764),(28,16523),(29,14221),(30,12634),(31,11110),(32,9611),(33,8170),(34,7395),(35,5703),(36,4456),(37,3791),(38,3145),(39,2118),(40,1815),(41,1332),(42,967),(43,350),(44,336),(45,174),(46,145),(47,150),(48,44),(49,48),(50,51),(51,76),(52,18),(53,19),(54,22),(55,31)],
    "4": [(18,22),(19,73),(20,147),(21,366),(22,544),(23,1110),(24,1376),(25,1997),(26,2472),(27,3055),(28,3774),(29,3518),(30,3887),(31,3412),(32,3366),(33,3253),(34,2470),(35,2744),(36,2377),(37,1810),(38,1285),(39,981),(40,979),(41,414),(42,393),(43,265),(44,68),(45,39),(46,168),(47,8),(48,9),(49,17),(50,49),(51,9),(53,10),(55,10)],
}

GERAL = {
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
C_GERAL = "#666660"

def pct_media(data):
    ages = np.array([a for a, _ in data], float)
    ns = np.array([n for _, n in data], float)
    return ages, ns / ns.sum() * 100, (ages * ns).sum() / ns.sum()

def fmt(v):
    return f"{v:.1f}".replace(".", ",")

fig, axes = plt.subplots(4, 1, figsize=(12.5, 9.2), dpi=160, sharex=True)
fig.patch.set_facecolor("#f7f7f5")

for ax, key in zip(axes, "1234"):
    ages_e, pct_e, media_e = pct_media(EVANG[key])
    ages_g, pct_g, media_g = pct_media(GERAL[key])

    ax.set_facecolor("#f7f7f5")
    ax.fill_between(ages_e, pct_e, color=COLORS[key], alpha=0.75, lw=0)
    ax.plot(ages_e, pct_e, color=COLORS[key], lw=2)
    ax.plot(ages_g, pct_g, color=C_GERAL, lw=2, ls=(0, (4, 2)))

    ax.axvline(media_e, color="#222222", ls="-", lw=1.3, ymax=0.78)
    ax.axvline(media_g, color=C_GERAL, ls=(0, (4, 2)), lw=1.4, ymax=0.78)
    ax.text(max(media_e, media_g) + 0.6, 8.2,
            f"média: evangélicas {fmt(media_e)} · todas {fmt(media_g)} anos",
            fontsize=11.5, color="#222222", fontweight="bold")
    ax.text(11.5, 8.2, LABELS[key], fontsize=12.5, color="#333333")

    ax.set_xlim(11, 50)
    ax.set_ylim(0, 9.4)
    ax.set_yticks([])
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#dddddb")
    ax.tick_params(colors="#555555", labelsize=11.5, length=0)
    ax.grid(axis="x", color="#e8e8e6", lw=0.8)
    ax.set_axisbelow(True)

axes[-1].set_xlabel("Idade da mãe (anos)", fontsize=13, labelpad=10)
axes[-1].set_xticks(range(15, 51, 5))

axes[0].fill_between([], [], color="#5b8fc4", alpha=0.75, label="Evangélicas")
axes[0].plot([], [], color=C_GERAL, lw=2, ls=(0, (4, 2)), label="Todas as mulheres")
axes[0].legend(loc="upper right", frameon=False, fontsize=11.5,
               labelcolor="#333333", borderaxespad=0.2)

fig.suptitle("Escolaridade manda, religião quase não mexe: idade da mãe, evangélicas vs. todas",
             x=0.065, y=0.97, ha="left", fontsize=18, fontweight="bold", color="#111111")
fig.text(0.065, 0.925,
         "Mulheres com filho menor de 1 ano no Censo 2010 · cada curva é a distribuição "
         "da idade (soma 100% por painel)",
         fontsize=13, color="#555555")
fig.text(0.065, 0.012,
         "Fonte: Censo Demográfico 2010 (IBGE), microdados de pessoa — V6036, V6400, V6660, V6121",
         fontsize=10.5, color="#777777")

fig.tight_layout(rect=(0.01, 0.03, 1, 0.91))
out = "dataviz/escolaridade_idade_mae_evangelicas_vs_geral.png"
fig.savefig(out, facecolor=fig.get_facecolor(), bbox_inches="tight")
print("ok:", out)
