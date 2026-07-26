#!/usr/bin/env python3
"""Religião por faixa etária — Censo 2010 vs 2022, população de 15 anos ou mais.

Small multiples: um painel por grupo religioso, mostrando que fatia de cada
faixa etária declara aquela religião. 2022 em degraus preenchidos (a largura do
degrau é a largura real da faixa), 2010 como linha tracejada de referência.

Cada painel tem escala própria, mas TODAS começam em zero — assim a inclinação
visual é comparável entre painéis mesmo com níveis muito diferentes: é a
inclinação relativa que responde "esse grupo é mais jovem?".

Fontes (via beelink):
  2022 — br_ibge_censo2022_religiao.alfabetizacao_idade (SIDRA, soma dos
         municípios), variável "Pessoas de 15 anos ou mais de idade" por
         religião × grupo de idade.
  2010 — read_parquet('~/rodado/br_ibge_censo_demografico/microdados_pessoa_2010/*.parquet'),
         amostra expandida por peso_amostral, v6036 (idade) >= 15, religião
         v6121 reagrupada nos blocos do código IBGE:
           110-119 Católica Apostólica Romana · 200-499 Evangélicas ·
           610-619 Espírita · 620-639 Umbanda e Candomblé · <100 Sem religião.
         Blocos conferidos contra os totais publicados de 2010 (católicas
         123,99 mi, evangélicas 42,28 mi, sem religião 15,33 mi).

O denominador de cada faixa é a população 15+ TOTAL daquela faixa (inclui
"outras religiosidades" e "sem declaração"), por isso os painéis não somam 100%.
"""
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt

# faixas do Censo 2022: (rótulo curto, início, fim exclusivo)
FAIXAS = [("15-19", 15, 20), ("20-24", 20, 25), ("25-29", 25, 30),
          ("30-39", 30, 40), ("40-49", 40, 50), ("50-59", 50, 60),
          ("60-69", 60, 70), ("70-79", 70, 80), ("80+", 80, 90)]
BORDAS = [f[1] for f in FAIXAS] + [FAIXAS[-1][2]]

# população 15+ por faixa, por religião
POP_2010 = {
    "Católica Apostólica Romana": [10814475, 10992309, 10743950, 18606764, 16241547, 12530836, 7988321, 4587668, 2194776],
    "Evangélicas": [3794464, 3624816, 3743696, 6740026, 5342661, 3657203, 2161854, 1137973, 467075],
    "Sem religião": [1651983, 1826988, 1723353, 2606573, 1752855, 1065554, 542937, 244518, 100411],
    "Espírita": [224500, 273035, 339817, 691977, 678349, 566627, 309108, 148259, 64514],
    "Umbanda e Candomblé": [42111, 51451, 59248, 110096, 92082, 67448, 33939, 14949, 4955],
}
POP_2022 = {
    "Católica Apostólica Romana": [7502152, 7912142, 7906384, 16891747, 16663330, 14612383, 11605531, 6703786, 3315801],
    "Evangélicas": [4149251, 4253772, 4312215, 8871882, 8239843, 6248325, 4091272, 2053717, 872861],
    "Sem religião": [1794506, 2210170, 2087459, 3416014, 2476901, 1530845, 915799, 399052, 154198],
    "Espírita": [156514, 180769, 203847, 540201, 646598, 588576, 474707, 225685, 93465],
    "Umbanda e Candomblé": [154816, 205832, 214355, 399818, 341284, 222145, 128081, 49984, 18389],
}
# população total de 15+ por faixa (todas as religiões, inclusive as não plotadas)
TOTAL_2010 = [16999236, 17235420, 17061661, 29631930, 24775964, 18358277, 11362913, 6323234, 2917310]
TOTAL_2022 = [14372213, 15486866, 15453222, 31577371, 29680404, 24219338, 17853297, 9799130, 4599870]

# ordem fixa de slots categóricos (validada: pior par adjacente ΔE normal 27,6)
PAINEIS = [
    ("Católica Apostólica Romana", "Católica Apostólica Romana", "#2a78d6", 82),
    ("Evangélicas", "Evangélicas", "#eb6834", 33),
    ("Sem religião", "Sem religião", "#1baf7a", 16.5),
    ("Espírita", "Espírita", "#e87ba4", 3.6),
    ("Umbanda e Candomblé", "Umbanda e Candomblé", "#4a3aa7", 1.65),
]

SURFACE, FIG_BG = "#fcfcfb", "#f7f7f5"
TXT, TXT2, TXT3, REF = "#111111", "#555555", "#777777", "#9a9a94"


def share(pops, totais):
    return [100 * p / t for p, t in zip(pops, totais)]


def vg(v):
    return f"{v:.1f}".replace(".", ",") + "%"


fig, axes = plt.subplots(1, 5, figsize=(17.5, 6.8), dpi=160)
fig.patch.set_facecolor(FIG_BG)
fig.subplots_adjust(left=0.035, right=0.988, top=0.685, bottom=0.155, wspace=0.16)

for ax, (rel, titulo, cor, ymax) in zip(axes, PAINEIS):
    s22 = share(POP_2022[rel], TOTAL_2022)
    s10 = share(POP_2010[rel], TOTAL_2010)
    ax.set_facecolor(SURFACE)

    ax.stairs(s10, BORDAS, color=REF, lw=1.6, ls=(0, (4, 2.5)), baseline=None, zorder=3)
    ax.stairs(s22, BORDAS, color=cor, lw=2.2, baseline=0, fill=True,
              alpha=0.13, zorder=2)
    ax.stairs(s22, BORDAS, color=cor, lw=2.2, baseline=None, zorder=4)

    # valores das pontas, rotulados direto (regra de relevo: aqua e magenta < 3:1)
    # o rótulo vai para o lado livre: acima quando a ponta é o degrau mais alto
    # do par, abaixo quando o degrau vizinho sobe e ocuparia o espaço.
    for x, ha, v, viz in ((16.2, "left", s22[0], s22[1]),
                          (88.8, "right", s22[-1], s22[-2])):
        acima = v >= viz
        ax.annotate(vg(v), (x, v + ymax * (0.035 if acima else -0.045)), color=cor,
                    fontsize=12, fontweight="bold", ha=ha,
                    va="bottom" if acima else "top", zorder=6,
                    path_effects=[pe.withStroke(linewidth=3.2, foreground=SURFACE)])

    ax.set_xlim(15, 90)
    ax.set_ylim(0, ymax)
    ax.set_xticks([20, 40, 60, 80])
    ax.set_xticklabels(["20", "40", "60", "80"])
    ax.grid(axis="y", color="#ececeb", lw=0.8)
    ax.set_axisbelow(True)
    for sp in ("top", "right", "left", "bottom"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(colors=TXT2, labelsize=11, length=0)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:g}%".replace(".", ","))
    ax.set_title(titulo, loc="left", fontsize=13.5, fontweight="bold",
                 color=TXT, pad=10)
    ax.set_xlabel("Idade", fontsize=11, color=TXT3, labelpad=6)

# legenda 2010 / 2022 (identidade também por texto e por traço, não só por cor)
leg = fig.add_axes((0.035, 0.735, 0.30, 0.045))
leg.set_axis_off()
leg.set_xlim(0, 1)
leg.set_ylim(0, 1)
leg.plot([0.0, 0.055], [0.5, 0.5], color="#3d3d3a", lw=2.4, solid_capstyle="round")
leg.text(0.072, 0.5, "Censo 2022", fontsize=12.5, color=TXT2, va="center")
leg.plot([0.30, 0.355], [0.5, 0.5], color=REF, lw=1.6, ls=(0, (4, 2.5)))
leg.text(0.372, 0.5, "Censo 2010", fontsize=12.5, color=TXT2, va="center")

fig.suptitle("O avanço evangélico não é uma onda jovem: ele subiu em todas as idades",
             x=0.035, y=0.955, ha="left", fontsize=21, fontweight="bold", color=TXT)
fig.text(0.035, 0.885,
         "Fatia de cada faixa etária que declara a religião · população de 15 anos ou mais · "
         "quanto mais inclinada a linha, mais o grupo se concentra numa ponta da vida",
         fontsize=12.5, color=TXT2, ha="left")
fig.text(0.035, 0.815,
         "Entre 15 e 19 anos os evangélicos são 28,9% — só 2,5 pontos acima da média de todas as idades (26,4%). "
         "O grupo com cara de juventude é outro: sem religião cai de 12,5% a 3,4%.",
         fontsize=12.5, color=TXT, ha="left")

fig.text(0.035, 0.028,
         "Fonte: IBGE — Censo 2022 (SIDRA, religião × grupo de idade, soma dos municípios) e Censo 2010 "
         "(microdados da amostra, v6121 × v6036, expandidos por peso_amostral).\n"
         "Escalas verticais diferentes por painel, todas começando em zero. Denominador = população de 15+ "
         "da faixa, incluindo outras religiosidades e sem declaração — por isso os painéis não somam 100%.",
         fontsize=10, color=TXT3, ha="left", linespacing=1.5)

out = "dataviz/estrutura_etaria_religiao_2010_2022.png"
fig.savefig(out, facecolor=fig.get_facecolor())
print("ok:", out)
