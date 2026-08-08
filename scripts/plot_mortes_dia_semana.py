#!/usr/bin/env python3
"""Em que dia da semana cada doença mata, Brasil 2015-2022.

  dataviz/mortes_dia_semana.png
      Mapa de calor divergente: uma linha por causa, uma coluna por dia da
      semana, cada célula é o desvio percentual em relação à média semanal
      daquela causa. Vermelho = morre mais naquele dia; verde-azulado = menos.
      Ordenado pelo contraste fim de semana contra meio de semana.

POR QUE % DE DESVIO, E NÃO CONTAGEM
Cada linha é normalizada contra a própria média, então a cor compara dias
dentro de uma mesma doença — nunca o tamanho de uma doença contra a outra.
Sem isso o mapa inteiro seria a silhueta do câncer e do infarto.

A taxa por dia usa o número de vezes que aquele dia da semana ocorreu no
período, não uma divisão por sete: 2015-2022 não tem a mesma quantidade de
segundas e de domingos, e ignorar isso injeta um viés de até 0,3%.

O CAMPO DE HORA NÃO ENTRA AQUI, DE PROPÓSITO
A pergunta natural seguinte — a que hora do dia se morre — não é respondível
com este dado. Em 2022, a distribuição de `hora_obito` é chapada da hora 3 à
23 (59 mil a 81 mil óbitos por hora), a hora 0 não existe e as horas 1 e 2 têm
8.849 e 21.496 registros contra as ~60 mil esperadas. Os picos aparentes às
10h e às 20h ocorrem só no minuto :00 (18.805 e 17.619 registros exatos,
contra ~11 mil nas horas vizinhas): são 01:00 e 02:00 lidos como 10:00 e
20:00, perda do zero à esquerda na conversão de HHMM. Um gráfico circadiano
com esse campo mediria o defeito, não a fisiologia. `data_obito` é DATE e não
tem esse problema — por isso o dia da semana se sustenta e a hora não.

OS DOIS FUNDOS DO MAPA TÊM MECANISMOS DIFERENTES
A leitura preguiçosa junta tudo o que cai no fim de semana como "procedimento
agendado". São duas coisas distintas, e o dado separa:

  · Malformações congênitas herdam o calendário das cesáreas. No SINASC,
    2015-2022, nasce-se 23,7% menos no domingo e 13,6% menos no sábado, contra
    +10,4% na segunda — a assinatura do parto marcado. Como quase toda morte
    por malformação é neonatal, a curva de óbito repete a de nascimento com
    ~2 dias de atraso: pico de quarta a sexta (nascimentos de segunda a
    quarta) e fundo no domingo e segunda (nascimentos de sábado e domingo).

  · Doença renal crônica tem segunda (+3,9%) E terça (+4,9%) altas, com
    sábado e domingo baixos. Esse é o desenho do intervalo interdialítico
    longo: quem dialisa segunda-quarta-sexta passa o maior intervalo de
    sexta a segunda, e quem dialisa terça-quinta-sábado, de sábado a terça.
    O excesso cai exatamente nos dois dias seguintes a cada intervalo longo.

RUÍDO
O desvio de cada célula tem erro de amostragem de 100/raiz(N/7). Na mediana
das causas isso dá ±0,8%; no pior caso, gravidez e parto (N=16.188), ±2,1%.
Células abaixo de ~2% em causas pequenas são ruído, e a rampa de cor foi
construída para deixá-las quase neutras.

A rampa satura em ±22%. Afogamento no domingo (+84,9%) e acidentes de
transporte no domingo (+48,4%) estouram a escala — por isso o valor está
escrito em toda célula, e não só a cor.

Fonte: Ministério da Saúde — Sistema de Informações sobre Mortalidade, óbitos
de 2015 a 2022 por causa básica e data do óbito. Agrupamento idêntico ao de
scripts/plot_causas_nao_cancer.py, mais uma linha de referência com todos os
cânceres somados (C00-C97).
"""
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize

DIAS = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]

# causa: (total de óbitos 2015-2022, [seg, ter, qua, qui, sex, sáb, dom] em % de desvio)
SEMANA = {
    'Afogamento'                          : (39110, [-8.7, -26.1, -27.8, -25.6, -19.4, 22.7, 84.9]),
    'Acidentes de transporte'             : (280165, [-6.0, -22.5, -21.8, -19.0, -6.4, 27.4, 48.4]),
    'Homicídio'                           : (414898, [-6.2, -14.6, -11.8, -10.5, -3.8, 18.5, 28.3]),
    'Suicídio'                            : (104937, [8.1, -4.3, -5.0, -5.1, -5.3, -0.7, 12.4]),
    'Infarto agudo do miocárdio'          : (746384, [2.7, -0.4, -2.3, -1.6, -1.1, 0.9, 1.8]),
    'Diarreia e gastroenterite'           : (36254, [1.2, -0.3, -1.2, -2.5, 0.5, 0.3, 2.0]),
    'Doença hipertensiva'                 : (451760, [3.2, 0.6, -2.0, -2.0, -1.4, -0.2, 1.8]),
    'Epilepsia'                           : (26457, [5.6, 0.2, -2.4, -1.9, -2.3, -1.6, 2.6]),
    'Pneumonite por aspiração'            : (46803, [0.8, -1.0, -0.6, -0.8, -0.4, 0.6, 1.4]),
    'Transtornos por álcool'              : (56612, [7.4, 1.4, -1.8, -3.2, -4.6, -2.6, 3.4]),
    'Infecção do trato urinário'          : (164882, [0.2, 0.8, -1.0, -1.1, 0.1, 0.8, 0.2]),
    'Alzheimer e demências'               : (223153, [0.5, -1.3, -0.3, 0.8, -0.7, -0.3, 1.4]),
    'Asma'                                : (19539, [1.5, 1.7, -3.3, -1.0, 1.4, 0.7, -1.0]),
    'Obesidade'                           : (25947, [2.2, -1.5, -1.1, 0.7, -0.3, -1.6, 1.7]),
    'Doença de Chagas'                    : (34160, [2.3, -1.6, -0.2, -0.6, 0.8, -0.6, -0.1]),
    'AVC isquêmico e não especificado'    : (363149, [0.8, -0.9, -0.4, 0.4, -0.2, 0.4, -0.2]),
    'Pancreatite'                         : (34407, [1.8, 1.2, -0.0, -1.9, -1.3, -0.2, 0.3]),
    'Tuberculose'                         : (38025, [1.9, -0.3, -0.9, -0.9, 1.3, -0.5, -0.6]),
    'Pneumonia e gripe'                   : (630443, [1.1, 0.5, -0.1, -1.1, 0.2, -0.6, -0.0]),
    'Câncer (todos os tipos)'             : (1771057, [-0.9, -0.5, -0.0, 0.4, 1.2, 0.8, -1.0]),
    'DPOC e enfisema'                     : (344685, [1.0, -0.0, 0.4, -0.4, -0.7, 0.1, -0.4]),
    'Afecções perinatais'                 : (184828, [-0.7, -0.9, 1.2, -0.5, 1.4, 0.1, -0.6]),
    'Diabetes'                            : (539953, [2.1, 0.4, 0.3, -0.9, -1.3, -0.7, 0.1]),
    'Insuficiência cardíaca'              : (228691, [0.9, 0.5, 0.4, -1.5, 0.8, -1.0, -0.1]),
    'AIDS'                                : (91579, [-0.5, -0.5, -0.9, 0.4, 2.9, 0.3, -1.7]),
    'COVID-19'                            : (699782, [-1.2, -0.1, 0.3, 1.0, 0.0, -0.4, 0.4]),
    'Úlcera péptica'                      : (31472, [-1.8, 0.6, -0.7, 0.8, 1.6, -1.7, 1.2]),
    'Miocardiopatias'                     : (95758, [3.4, -0.7, -0.5, 0.4, -1.0, -2.7, 0.9]),
    'Parkinson'                           : (34867, [1.0, 0.8, -1.7, 1.9, -1.2, -0.4, -0.4]),
    'Aterosclerose e aneurisma'           : (107919, [0.7, -0.7, 0.4, -0.4, 2.6, -0.6, -1.9]),
    'Hepatites virais'                    : (17793, [-2.7, 0.4, 0.8, 1.2, 0.9, 0.0, -0.6]),
    'Quedas'                              : (123325, [1.7, 0.5, -0.3, -0.5, 1.3, -0.2, -2.5]),
    'Cirrose e doenças do fígado'         : (210983, [1.2, 2.3, 0.1, -1.0, -0.8, -1.0, -0.9]),
    'Septicemia'                          : (170974, [-0.4, 0.4, 0.1, 1.2, 0.5, -0.7, -1.1]),
    'Apendicite, hérnia e obstrução'      : (68847, [0.5, -0.1, 1.2, 0.2, 0.7, -1.2, -1.2]),
    'Sequelas e outras cerebrovasculares' : (264952, [2.3, 0.8, 0.3, 0.2, -0.8, -1.8, -1.1]),
    'Gravidez, parto e puerpério'         : (16188, [1.8, 1.2, 3.9, -3.8, -0.1, -0.9, -2.1]),
    'Insuficiência renal aguda'           : (43693, [1.4, 1.4, 2.0, -0.5, -1.3, -0.3, -2.6]),
    'Outras isquêmicas do coração'        : (168193, [3.6, -1.8, 0.1, 1.2, 2.2, -3.0, -2.3]),
    'Embolia pulmonar e cor pulmonale'    : (67173, [3.0, 0.7, -0.7, 1.2, 1.5, -1.3, -4.5]),
    'Doença renal crônica'                : (84538, [3.9, 4.9, 0.3, -1.0, -0.7, -2.7, -4.7]),
    'Desnutrição'                         : (42156, [2.7, 3.5, 0.5, 0.1, 1.1, -3.6, -4.3]),
    'AVC hemorrágico'                     : (180753, [1.7, 3.5, 2.0, 0.4, 0.6, -3.4, -4.8]),
    'Malformações congênitas'             : (86472, [-3.5, 2.2, 5.0, 4.5, 4.9, -3.8, -9.3]),
}

SURFACE, FIG_BG = "#fcfcfb", "#f7f7f5"
TXT, TXT2, TXT3 = "#111111", "#555555", "#7b7b76"
ACENTO = "#d1453b"

# rampa divergente: dois polos de matiz e um cinza neutro no meio — nunca uma
# terceira cor no centro. Verde-azulado = morre menos naquele dia; vermelho =
# mais. A luminosidade sobe monotonicamente de cada polo até o centro, então a
# leitura funciona também em preto e branco e para daltônicos
RAMPA = LinearSegmentedColormap.from_list("rodado_div", [
    "#00473c", "#0e7565", "#5aa89a", "#a9cfc7", "#dfe9e5",
    "#f2f1ed",
    "#f7ddd7", "#eeb0a5", "#df7c6c", "#c4402e", "#8f1f14"])

VMAX = 22          # a rampa satura aqui; o valor escrito na célula diz a verdade
ORDEM = list(SEMANA)


def vg(v):
    s = f"{v:+.1f}".replace(".", ",")
    return s.replace("+0,0", "0,0").replace("-0,0", "0,0")


def mg(n):
    return f"{n:,}".replace(",", ".")


fig = plt.figure(figsize=(12.4, 17.6), dpi=200, facecolor=FIG_BG)
ax = fig.add_axes((0.315, 0.105, 0.475, 0.715))
ax.set_facecolor(SURFACE)

matriz = [SEMANA[g][1] for g in ORDEM]
im = ax.imshow(matriz, aspect="auto", cmap=RAMPA, norm=Normalize(-VMAX, VMAX),
               interpolation="nearest")

# o valor vai escrito em toda célula: a cor satura em ±22%, o número não
for i, g in enumerate(ORDEM):
    for j, v in enumerate(SEMANA[g][1]):
        ax.text(j, i, vg(v), ha="center", va="center", fontsize=8.2,
                color="#ffffff" if abs(v) > 13 else TXT2,
                fontweight="bold" if abs(v) > 13 else "normal")

# separadores finos entre as células, e a linha que isola o fim de semana
for i in range(len(ORDEM) + 1):
    ax.axhline(i - 0.5, color=FIG_BG, lw=1.2)
for j in range(8):
    ax.axvline(j - 0.5, color=FIG_BG, lw=1.2)
ax.axvline(4.5, color="#9d9d95", lw=1.8)

ax.set_xticks(range(7))
ax.set_xticklabels(DIAS, fontsize=13, color=TXT2, fontweight="bold")
ax.xaxis.set_ticks_position("top")
ax.set_yticks(range(len(ORDEM)))
ax.set_yticklabels(ORDEM, fontsize=10.5, color=TXT2)
ax.tick_params(length=0)
for sp in ax.spines.values():
    sp.set_visible(False)

# coluna de N à direita, fora do mapa: dá o peso de cada linha e deixa ver
# quais estão perto do chão de ruído
ax.text(7.35, -1.05, "óbitos\n2015–2022", fontsize=9.5, color=TXT3,
        ha="left", va="center", linespacing=1.4)
for i, g in enumerate(ORDEM):
    ax.text(7.35, i, mg(SEMANA[g][0]), fontsize=9.5, color=TXT3,
            ha="left", va="center")
ax.set_xlim(-0.5, 6.5)
ax.set_clip_on(False)

cb = fig.colorbar(im, ax=ax, orientation="horizontal", fraction=0.024,
                  pad=0.038, aspect=38)
cb.outline.set_visible(False)
cb.set_ticks([-22, -15, -10, -5, 0, 5, 10, 15, 22])
cb.ax.tick_params(colors=TXT3, labelsize=10, length=0)
cb.ax.xaxis.set_major_formatter(
    lambda v, _: ("≤ −22%" if v <= -22 else "≥ +22%" if v >= 22
                  else f"{v:+.0f}%".replace("+0", "0")))
cb.set_label("desvio em relação à média semanal daquela causa  ·  cada linha é normalizada contra si mesma",
             fontsize=10.5, color=TXT3, labelpad=9)

fig.text(0.082, 0.972, "A semana também mata em ordem",
         ha="left", va="top", fontsize=25, fontweight="bold", color=TXT)
fig.text(0.082, 0.9510,
         "Em que dia da semana cada doença mata mais e menos que a sua própria média — Brasil, 2015 a 2022",
         ha="left", va="top", fontsize=13, color=TXT2)
fig.text(0.082, 0.9290,
         "No topo, o que o fim de semana produz: afogamento mata 85% acima da média no domingo, trânsito 48%,\n"
         "homicídio 28%. No fundo, o inverso, e por dois motivos diferentes: as malformações congênitas seguem o\n"
         "calendário das cesáreas — nasce-se 24% menos no domingo, e a morte neonatal vem dois dias depois —,\n"
         "enquanto a doença renal crônica sobe na segunda e na terça, a marca do intervalo longo sem diálise.\n"
         "E no meio, quase invisível, o achado clássico: o infarto tem segunda-feira, repetida em 8 dos 8 anos.",
         ha="left", va="top", fontsize=13.5, color=TXT, linespacing=1.6)

fig.text(0.082, 0.052,
         "Fonte: Ministério da Saúde — Sistema de Informações sobre Mortalidade, óbitos de 2015 a 2022 por causa básica e data do óbito. A taxa de cada dia usa o número\n"
         "de vezes que aquele dia ocorreu no período, não uma divisão por sete. O erro de amostragem de cada célula é 100/raiz(N/7): ±0,8% na mediana das causas e ±2,1%\n"
         "no pior caso (gravidez, parto e puerpério, N=16.188) — valores abaixo disso em causas pequenas são ruído. A cor satura em ±22%; o número escrito na célula não.\n"
         "A pergunta seguinte, a que hora do dia se morre, não entra aqui: o campo de hora do SIM está corrompido (a hora 0 não existe e 01:00 e 02:00 viram 10:00 e 20:00).",
         ha="left", va="top", fontsize=9.5, color=TXT3, linespacing=1.6)

out = "dataviz/mortes_dia_semana.png"
fig.savefig(out, facecolor=fig.get_facecolor())
print("ok:", out)
