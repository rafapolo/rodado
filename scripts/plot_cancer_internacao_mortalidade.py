#!/usr/bin/env python3
"""Câncer no Brasil: internações no SUS contra mortalidade, por sítio do tumor (2022).

Releitura do gráfico clássico "incidência × mortalidade" do Global Cancer
Observatory usando fonte brasileira. O Brasil não tem registro nacional de
incidência de câncer de base populacional — os registros hospitalares e de base
populacional cobrem parte do território e saem com anos de defasagem. O que
existe em cobertura nacional e no mesmo ano são duas contagens completas:
quem morreu e quem foi internado. É esse par que o gráfico cruza.

  eixo X  mortalidade  — óbitos com causa básica C00–C97 (neoplasias malignas),
          Sistema de Informações sobre Mortalidade (SIM), 2022.
  eixo Y  internações  — autorizações de internação hospitalar com diagnóstico
          principal C00–C97, Sistema de Informações Hospitalares (SIH), 2022.
  ambos   por 100 mil habitantes, população do Censo 2022 (IBGE).

A diagonal é a paridade: uma internação para cada morte. Quanto mais alto o
ponto sobe acima dela, mais o SUS interna por aquele câncer em relação ao que
ele mata — leitura indireta de detecção precoce e de sobrevida. Quem encosta
na diagonal é o câncer que interna pouco porque mata rápido.

Cuidados de leitura, que estão no rodapé da figura:
  · taxas brutas, não padronizadas por idade. Como todos os sítios dividem
    pela mesma população no mesmo ano, a comparação entre eles é válida; a
    comparação com séries internacionais padronizadas não é.
  · sítios exclusivos de um sexo (próstata, testículo, mama, colo e corpo do
    útero, ovário) usam como denominador a população daquele sexo.
  · internação conta episódio, não paciente: quem interna três vezes no ano
    aparece três vezes.
  · quimioterapia e radioterapia ambulatoriais são registradas em APAC (SIA),
    não em AIH, e portanto não entram no eixo Y.

Consulta (beelink):
  br_ms_sim.microdados            ano = 2022, causa_basica entre C00 e C97
  br_ms_sih.aihs_reduzidas        ano = 2022, coalesce(cid_principal_subcategoria,
                                  cid_principal_categoria) começando em C
  br_ibge_censo_2022.populacao_idade_sexo   população por sexo (soma nacional)

Totais de controle: 226.762 óbitos por câncer em 2022 (15,0% de todas as
1.507.077 mortes do ano) e 707.675 internações. O agrupamento por sítio cobre
os dois conjuntos menos os códigos de sítio mal definido e secundário
(C76–C80), que ficam de fora por não nomearem um órgão de origem.
"""
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# sítio: (mortalidade/100 mil, internações/100 mil, óbitos, internações, denominador)
DADOS = {
    "Traqueia, brônquios e pulmão":            (13.87, 13.24, 28166, 26892, "ambos"),
    "Mama":                                    (17.58, 75.80, 18383, 79249, "mulheres"),
    "Próstata":                                (15.61, 35.59, 15382, 35065, "homens"),
    "Estômago":                                (6.68, 16.38, 13574, 33267, "ambos"),
    "Cólon":                                   (6.48, 29.42, 13155, 59746, "ambos"),
    "Pâncreas":                                (5.89, 7.95, 11969, 16151, "ambos"),
    "Fígado e vias biliares":                  (4.95, 5.54, 10061, 11258, "ambos"),
    "Cérebro e sistema nervoso":               (4.63, 9.45, 9410, 19201, "ambos"),
    "Esôfago":                                 (3.99, 8.52, 8108, 17298, "ambos"),
    "Reto e ânus":                             (3.92, 18.63, 7960, 37836, "ambos"),
    "Leucemia":                                (3.31, 19.72, 6715, 40052, "ambos"),
    "Colo do útero":                           (6.31, 25.12, 6601, 26261, "mulheres"),
    "Bexiga":                                  (2.40, 10.58, 4877, 21476, "ambos"),
    "Laringe":                                 (2.15, 5.99, 4359, 12161, "ambos"),
    "Linfoma não Hodgkin":                     (2.11, 8.78, 4277, 17831, "ambos"),
    "Rim e vias urinárias":                    (1.99, 5.77, 4032, 11718, "ambos"),
    "Corpo do útero":                          (3.84, 11.31, 4018, 11827, "mulheres"),
    "Ovário":                                  (3.81, 12.97, 3986, 13562, "mulheres"),
    "Vesícula e vias biliares":                (1.88, 3.19, 3828, 6482, "ambos"),
    "Faringe":                                 (1.80, 4.90, 3656, 9959, "ambos"),
    "Lábio e cavidade oral":                   (1.78, 6.47, 3621, 13133, "ambos"),
    "Mieloma múltiplo":                        (1.75, 4.15, 3558, 8435, "ambos"),
    "Pele não melanoma":                       (1.45, 25.37, 2947, 51519, "ambos"),
    "Melanoma de pele":                        (0.92, 3.96, 1868, 8038, "ambos"),
    "Tireoide":                                (0.40, 6.06, 808, 12315, "ambos"),
    "Linfoma de Hodgkin":                      (0.26, 2.57, 532, 5218, "ambos"),
    "Testículo":                               (0.45, 3.75, 446, 3698, "homens"),
}

SURFACE, FIG_BG = "#fcfcfb", "#f7f7f5"
TXT, TXT2, TXT3 = "#111111", "#555555", "#7b7b76"
ACENTO, GRID, REF = "#d1453b", "#e6e6e2", "#b6b6ae"

XLIM, YLIM = (0.20, 26.0), (1.9, 105.0)


def vg(v, casas=1):
    return f"{v:.{casas}f}".replace(".", ",")


def area(obitos):
    """área da bolha em pt², proporcional ao número de mortes"""
    return 80 + obitos / 28166 * 1250


fig = plt.figure(figsize=(12.4, 12.2), dpi=200, facecolor=FIG_BG)
ax = fig.add_axes((0.082, 0.115, 0.90, 0.605))
ax.set_facecolor(SURFACE)

ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlim(*XLIM)
ax.set_ylim(*YLIM)
ax.set_xticks([0.25, 0.5, 1, 2, 4, 8, 16])
ax.set_yticks([2, 4, 8, 16, 32, 64])
ax.set_xticklabels([vg(v, 2 if v < 1 else 0) for v in (0.25, 0.5, 1, 2, 4, 8, 16)])
ax.set_yticklabels([f"{v}" for v in (2, 4, 8, 16, 32, 64)])
ax.minorticks_off()
ax.grid(color=GRID, lw=0.8)
ax.set_axisbelow(True)
for sp in ax.spines.values():
    sp.set_visible(False)
ax.tick_params(colors=TXT3, labelsize=12, length=0)

# linhas de razão internações/óbito — em log-log são paralelas
for razao, texto in ((1, "1 internação\npor óbito"), (5, "5 por óbito"),
                     (20, "20 por óbito")):
    xs = [XLIM[0], XLIM[1]]
    ax.plot(xs, [x * razao for x in xs], color=REF, lw=1.1,
            ls=(0, (5, 3.5)), zorder=1)
    x_fim = min(XLIM[1], YLIM[1] / razao) * 0.93
    ax.text(x_fim, x_fim * razao * 1.03, texto, color=TXT3, fontsize=10.5,
            ha="right", va="bottom", linespacing=1.4, zorder=1)

# bolhas — área proporcional ao número de mortes
for sitio, (mort, intern, obitos, _n, _) in sorted(
        DADOS.items(), key=lambda kv: -kv[1][2]):
    ax.scatter(mort, intern, s=area(obitos), color=ACENTO,
               alpha=0.85, edgecolors=SURFACE, linewidths=2, zorder=3)

ax.set_xlabel("mortes por 100 mil habitantes  ·  escala dobrando a cada marca",
              fontsize=12.5, color=TXT2, labelpad=10)
ax.set_ylabel("internações no SUS por 100 mil habitantes",
              fontsize=12.5, color=TXT2, labelpad=10)

# legenda de tamanho
leg = [Line2D([], [], marker="o", ls="", markerfacecolor=ACENTO, alpha=0.85,
              markeredgecolor=SURFACE, markeredgewidth=1.5,
              markersize=area(n) ** 0.5 * 0.72,
              label=rot)
       for n, rot in ((28000, "28 mil mortes"), (10000, "10 mil"),
                      (500, "500"))]
ax.legend(handles=leg, loc="lower right", frameon=False, fontsize=11,
          labelcolor=TXT2, handletextpad=1.3, borderpad=1.0,
          labelspacing=1.4, title="tamanho da bolha = mortes no ano",
          title_fontsize=10.5, alignment="left")

# ------------------------------------------------- rótulos sem sobreposição
# tenta oito posições ao redor de cada bolha e fica na primeira que não
# esbarra em rótulo já posto, em outra bolha ou na borda do painel.
fig.canvas.draw()
renderer = fig.canvas.get_renderer()
inv = ax.transData.inverted()

# rótulos longos quebrados em duas linhas, para caberem melhor
QUEBRA = {
    "Traqueia, brônquios e pulmão": "Traqueia, brônquios\ne pulmão",
    "Cérebro e sistema nervoso": "Cérebro e\nsistema nervoso",
    "Fígado e vias biliares": "Fígado e\nvias biliares",
    "Vesícula e vias biliares": "Vesícula e\nvias biliares",
    "Rim e vias urinárias": "Rim e\nvias urinárias",
    "Lábio e cavidade oral": "Lábio e\ncavidade oral",
    "Linfoma não Hodgkin": "Linfoma\nnão Hodgkin",
    "Linfoma de Hodgkin": "Linfoma\nde Hodgkin",
    "Melanoma de pele": "Melanoma\nde pele",
    "Pele não melanoma": "Pele não\nmelanoma",
    "Mieloma múltiplo": "Mieloma\nmúltiplo",
}

DIRECOES = [(1, 0, "left", "center"), (-1, 0, "right", "center"),
            (0, 1, "center", "bottom"), (0, -1, "center", "top"),
            (0.72, 0.72, "left", "bottom"), (0.72, -0.72, "left", "top"),
            (-0.72, 0.72, "right", "bottom"), (-0.72, -0.72, "right", "top")]
AFASTAMENTO = (7, 15, 26, 40, 56)

painel = ax.get_window_extent(renderer)
ocupado = [ax.get_legend().get_window_extent(renderer).expanded(1.02, 1.02)]
# as bolhas também são obstáculos
bolhas = []
for sitio, (mort, intern, obitos, _n, _) in DADOS.items():
    px, py = ax.transData.transform((mort, intern))
    bolhas.append((px, py, area(obitos) ** 0.5 / 2 * fig.dpi / 72))

for sitio, (mort, intern, obitos, _n, _) in sorted(
        DADOS.items(), key=lambda kv: -kv[1][2]):
    destaque = obitos >= 15000
    px, py = ax.transData.transform((mort, intern))
    r = area(obitos) ** 0.5 / 2 * fig.dpi / 72
    txt = ax.text(mort, intern, QUEBRA.get(sitio, sitio),
                  fontsize=14 if destaque else 11,
                  color=TXT if destaque else TXT2, linespacing=1.25,
                  fontweight="bold" if destaque else "normal", zorder=4)
    melhor, melhor_custo = None, None
    for passo, (dx, dy, ha, va) in enumerate(DIRECOES):
        for afasta in AFASTAMENTO:
            txt.set_ha(ha)
            txt.set_va(va)
            alvo = (px + dx * (r + afasta), py + dy * (r + afasta))
            txt.set_position(inv.transform(alvo))
            bb = txt.get_window_extent(renderer).expanded(1.06, 1.3)
            custo = 0.0
            for lado in (painel.x0 - bb.x0, bb.x1 - painel.x1,
                         painel.y0 - bb.y0, bb.y1 - painel.y1):
                if lado > 0:                       # sair do painel é proibido
                    custo += 9000 + lado
            for o in ocupado:
                if bb.overlaps(o):
                    custo += 1200
            for bx, by, br in bolhas:
                if (bb.x0 - br < bx < bb.x1 + br) and (bb.y0 - br < by < bb.y1 + br):
                    custo += 600
            custo += {0: 0, 1: 5, 2: 3, 3: 3}.get(passo, 8) + afasta * 0.6
            if melhor_custo is None or custo < melhor_custo:
                melhor, melhor_custo = (ha, va, alvo, afasta), custo
        if melhor_custo is not None and melhor_custo < 10:
            break
    ha, va, alvo, afasta = melhor
    txt.set_ha(ha)
    txt.set_va(va)
    txt.set_position(inv.transform(alvo))
    ocupado.append(txt.get_window_extent(renderer).expanded(1.06, 1.3))
    # linha-guia quando o rótulo fica longe, ou quando alguma outra bolha está
    # mais perto dele do que a própria — sem a guia o rótulo trocaria de dono
    bb = txt.get_window_extent(renderer)
    ax_lab = bb.x0 if ha == "left" else bb.x1 if ha == "right" else (bb.x0 + bb.x1) / 2
    ay_lab = bb.y0 if va == "bottom" else bb.y1 if va == "top" else (bb.y0 + bb.y1) / 2
    dist = max(((ax_lab - px) ** 2 + (ay_lab - py) ** 2) ** 0.5, 1e-6)
    ambigua = any(((ax_lab - bx) ** 2 + (ay_lab - by) ** 2) ** 0.5 - br < dist - r
                  for bx, by, br in bolhas if (bx, by) != (px, py))
    if afasta > 20 or ambigua:
        p0 = inv.transform((px + (ax_lab - px) * r / dist,
                            py + (ay_lab - py) * r / dist))
        p1 = inv.transform((ax_lab - (ax_lab - px) / dist * 4,
                            ay_lab - (ay_lab - py) / dist * 4))
        ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color="#9d9d95", lw=1.0, zorder=2)

fig.text(0.082, 0.955, "O câncer que mais mata no Brasil é o que menos interna",
         ha="left", va="top", fontsize=25, fontweight="bold", color=TXT)
fig.text(0.082, 0.914,
         "Cada bolha é um tipo de câncer em 2022 — quanto ele mata (horizontal) contra quanto interna no SUS (vertical)",
         ha="left", va="top", fontsize=13, color=TXT2)
fig.text(0.082, 0.878,
         "Pulmão é o único sítio abaixo da paridade: 0,95 internação para cada morte. Mama interna 4,3 vezes\n"
         "mais do que mata, tireoide 15 vezes, pele não melanoma 17 vezes. Pâncreas, fígado e vesícula ficam\n"
         "colados na diagonal — internam pouco porque matam rápido. No ano foram 226.762 mortes por câncer\n"
         "e 707.675 internações.",
         ha="left", va="top", fontsize=13.5, color=TXT, linespacing=1.6)

fig.text(0.082, 0.070,
         "Fonte: Ministério da Saúde — Sistema de Informações sobre Mortalidade (óbitos com causa básica C00–C97) e Sistema de Informações Hospitalares\n"
         "(internações com diagnóstico principal C00–C97), ano de 2022. População: IBGE, Censo 2022.\n"
         "Taxas brutas, não padronizadas por idade — comparáveis entre si, não com séries internacionais. Sítios exclusivos de um sexo usam a população daquele sexo.\n"
         "Internação conta episódio, não paciente. Quimioterapia e radioterapia ambulatoriais ficam fora da internação e não entram no eixo vertical.",
         ha="left", va="top", fontsize=9.5, color=TXT3, linespacing=1.6)

out = "dataviz/cancer_internacao_mortalidade_2022.png"
fig.savefig(out, facecolor=fig.get_facecolor())
print("ok:", out)
