#!/usr/bin/env python3
"""As doenças que não são câncer: quanto matam, quanto internam e em que idade (2022).

Continuação de scripts/plot_cancer_internacao_mortalidade.py e
scripts/plot_cancer_idade.py, aplicando o mesmo par de leituras às causas de
morte fora do capítulo das neoplasias. Câncer responde por 15,4% dos óbitos do
país; as outras 1.275.091 mortes de 2022 nunca passaram por esse recorte.

  dataviz/nao_cancer_quantidades_2022.png
      A escala. Barras ordenadas pelo número de mortes, com o total de câncer
      como régua no topo. Mostra que nenhuma causa isolada chega perto do
      câncer somado, mas que infarto, pneumonia e diabetes sozinhos superam
      qualquer tumor individual.

  dataviz/nao_cancer_internacao_mortalidade_2022.png
      O mesmo cruzamento mata × interna do gráfico do câncer. Lá havia um único
      ponto abaixo da paridade (pulmão). Aqui há seis, e eles formam um grupo
      coerente: Chagas, Parkinson, Alzheimer, pneumonite por aspiração,
      sequelas de AVC e doença hipertensiva — doenças crônicas e
      neurodegenerativas para as quais o hospital não tem oferta.

  dataviz/nao_cancer_idade_perfil_2022.png
      Mapa de calor da idade do óbito, uma linha por causa, ordenado pela
      mediana. Vai de 0 (afecções perinatais) a 86 anos (Alzheimer) — uma
      amplitude que o câncer, concentrado entre 33 e 78, não tem.

AGRUPAMENTO
As causas seguem blocos da CID-10 próximos aos da lista de causas evitáveis do
Ministério da Saúde. Duas juntam códigos de capítulos diferentes:
  · COVID-19 — em 2022 o SIM não usa U07: grava tudo em B34.2, no capítulo das
    infecciosas. Sem esse remendo a COVID desapareceria diluída.
  · Alzheimer e demências — G30–G31 (cap. VI) somado a F00–F03 (cap. V). Os
    dois códigos descrevem a mesma doença e a escolha entre eles é do
    codificador; separados, cada metade some do ranking.
Os 43 grupos cobrem 77,4% das mortes não-câncer. O resto fica em códigos
residuais dos capítulos e nas 91.888 mortes mal definidas (cap. XVIII), que não
nomeiam doença nenhuma e por isso não entram.

CAUSA EXTERNA: POR QUE ELA ENTRA AGREGADA NO GRÁFICO DE INTERNAÇÃO
O SIM registra a causa externa (capítulo XX, V01–Y98: homicídio, trânsito,
queda). O SIH registra a lesão que ela produziu (capítulo XIX, S00–T98: fratura,
ferimento). O campo do SIH que guardaria a causa externa
(cid_causa_categoria) está 100% vazio em 2022. Dá para cruzar os dois totais,
mas não dá para saber quantas das internações por lesão vieram de agressão e
quantas de acidente — por isso o gráfico de internação traz uma bolha única,
"causas externas (lesões)", enquanto o mapa etário, que só usa o SIM, separa
homicídio, trânsito, suicídio, queda e afogamento.

Gravidez, parto e puerpério fica fora do gráfico de internação: as 2.234.475
internações do capítulo XV são quase todas partos normais, não tratamento de
doença, e a razão de 1.524 internações por morte não é comparável com nada.
A causa continua nas outras duas figuras.

LIMPEZA DO CAMPO DE IDADE
Mesmo corte de scripts/plot_cancer_idade.py, mais um: além dos 36.846 óbitos
sem idade (2,4%) e dos 6.528 com idade impossível de 116 a 220 anos (0,44%),
descartam-se 1.006 registros com idade negativa (0,07%, até -1,82) — outro
sintoma do mesmo erro de decodificação do campo, que o recorte do câncer não
tinha alcançado porque nenhum deles caía em C00–C97.

As afecções perinatais têm 60% dos óbitos sem idade preenchida: o SIM guarda a
idade em unidade + valor, e a conversão para anos completos perde grande parte
das mortes contadas em horas e dias. A linha do mapa de calor é normalizada
dentro de si mesma, então continua correta ao dizer "morrem no primeiro ano";
o que ela não sustenta é comparação de volume com as outras linhas.

Fonte: Ministério da Saúde — Sistema de Informações sobre Mortalidade (óbitos de
2022 por causa básica) e Sistema de Informações Hospitalares (internações de
2022 por diagnóstico principal). População: IBGE, Censo 2022 (203.080.756).
"""
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

POP = 203_080_756
MORTES_CANCER = 231_986
MORTES_PULMAO = 28_166   # o tumor que mais mata, régua do gráfico de quantidades
MORTES_TOTAL = 1_507_077

# grupo: (mortes, internações, mortes/100 mil, internações/100 mil, família)
DADOS = {
    'Infarto agudo do miocárdio'          : (92815, 162983, 45.7, 80.26, 'circ'),
    'Pneumonia e gripe'                   : (88101, 677393, 43.38, 333.56, 'resp'),
    'Diabetes'                            : (70034, 137350, 34.49, 67.63, 'meta'),
    'COVID-19'                            : (63788, 164865, 31.41, 81.18, 'inf'),
    'Doença hipertensiva'                 : (61902, 59749, 30.48, 29.42, 'circ'),
    'DPOC e enfisema'                     : (47104, 105852, 23.19, 52.12, 'resp'),
    'AVC isquêmico e não especificado'    : (46276, 208836, 22.79, 102.83, 'circ'),
    'Afecções perinatais'                 : (41914, 331617, 20.64, 163.29, 'mat'),
    'Homicídio'                           : (38874, 0, 19.14, 0.0, 'ext'),
    'Alzheimer e demências'               : (35704, 17105, 17.58, 8.42, 'neuro'),
    'Insuficiência cardíaca'              : (32513, 201810, 16.01, 99.37, 'circ'),
    'Sequelas e outras cerebrovasculares' : (32091, 21382, 15.8, 10.53, 'circ'),
    'Acidentes de transporte'             : (30815, 0, 15.17, 0.0, 'ext'),
    'Septicemia'                          : (28203, 154178, 13.89, 75.92, 'inf'),
    'Infecção do trato urinário'          : (26689, 211593, 13.14, 104.19, 'meta'),
    'Cirrose e doenças do fígado'         : (26675, 61453, 13.14, 30.26, 'meta'),
    'AVC hemorrágico'                     : (23450, 33101, 11.55, 16.3, 'circ'),
    'Outras isquêmicas do coração'        : (21175, 134814, 10.43, 66.38, 'circ'),
    'Quedas'                              : (14949, 0, 7.36, 0.0, 'ext'),
    'Aterosclerose e aneurisma'           : (14791, 105825, 7.28, 52.11, 'circ'),
    'Suicídio'                            : (14294, 0, 7.04, 0.0, 'ext'),
    'Malformações congênitas'             : (11540, 85502, 5.68, 42.1, 'mat'),
    'Miocardiopatias'                     : (11185, 14028, 5.51, 6.91, 'circ'),
    'Doença renal crônica'                : (10594, 96875, 5.22, 47.7, 'meta'),
    'AIDS'                                : (10531, 25613, 5.19, 12.61, 'inf'),
    'Apendicite, hérnia e obstrução'      : (10080, 473675, 4.96, 233.24, 'meta'),
    'Embolia pulmonar e cor pulmonale'    : (9474, 14561, 4.67, 7.17, 'circ'),
    'Pneumonite por aspiração'            : (7953, 3843, 3.92, 1.89, 'resp'),
    'Transtornos por álcool'              : (7456, 39766, 3.67, 19.58, 'neuro'),
    'Insuficiência renal aguda'           : (7253, 39491, 3.57, 19.45, 'meta'),
    'Tuberculose'                         : (5596, 21378, 2.76, 10.53, 'inf'),
    'Parkinson'                           : (5310, 1386, 2.61, 0.68, 'neuro'),
    'Diarreia e gastroenterite'           : (4686, 141683, 2.31, 69.77, 'inf'),
    'Úlcera péptica'                      : (4363, 11860, 2.15, 5.84, 'meta'),
    'Desnutrição'                         : (4215, 25906, 2.08, 12.76, 'meta'),
    'Afogamento'                          : (4204, 0, 2.07, 0.0, 'ext'),
    'Pancreatite'                         : (4141, 37682, 2.04, 18.56, 'meta'),
    'Epilepsia'                           : (4129, 63390, 2.03, 31.21, 'neuro'),
    'Doença de Chagas'                    : (3699, 604, 1.82, 0.3, 'inf'),
    'Obesidade'                           : (3344, 9469, 1.65, 4.66, 'meta'),
    'Asma'                                : (2573, 83424, 1.27, 41.08, 'resp'),
    'Hepatites virais'                    : (1596, 3596, 0.79, 1.77, 'inf'),
    'Gravidez, parto e puerpério'         : (1466, 2234475, 0.72, 1100.29, 'mat'),
}

# grupo: (óbitos com idade válida, média, mediana, mínima, máxima, p10, p90)
IDADE = {
    'Afecções perinatais'                 : (16603, 0.4, 0, 0, 104, 0, 0),
    'Malformações congênitas'             : (9493, 9.0, 0, 0, 114, 0, 42),
    'Homicídio'                           : (38071, 32.6, 30, 0, 115, 19, 51),
    'Gravidez, parto e puerpério'         : (1458, 29.9, 30, 12, 89, 20, 40),
    'Afogamento'                          : (4130, 35.1, 35, 0, 112, 4, 64),
    'Acidentes de transporte'             : (30452, 41.6, 40, 0, 115, 20, 67),
    'Suicídio'                            : (14162, 42.1, 40, 9, 114, 21, 67),
    'AIDS'                                : (10457, 45.8, 44, 0, 114, 28, 64),
    'Epilepsia'                           : (4104, 51.9, 54, 0, 109, 19, 82),
    'Transtornos por álcool'              : (7381, 54.9, 55, 10, 115, 38, 71),
    'Tuberculose'                         : (5528, 54.2, 55, 0, 115, 29, 78),
    'Obesidade'                           : (3319, 58.4, 59, 0, 111, 36, 81),
    'Cirrose e doenças do fígado'         : (26432, 59.8, 60, 0, 115, 41, 78),
    'Hepatites virais'                    : (1578, 61.6, 62, 0, 112, 43, 80),
    'Pancreatite'                         : (4092, 62.0, 63, 0, 110, 38, 85),
    'AVC hemorrágico'                     : (23244, 65.5, 67, 0, 115, 44, 86),
    'Miocardiopatias'                     : (11070, 66.9, 69, 0, 115, 41, 89),
    'Infarto agudo do miocárdio'          : (91897, 69.7, 70, 0, 115, 50, 88),
    'Asma'                                : (2555, 64.5, 70, 0, 114, 30, 90),
    'Embolia pulmonar e cor pulmonale'    : (9358, 67.7, 71, 0, 109, 41, 90),
    'Úlcera péptica'                      : (4319, 69.7, 71, 1, 113, 49, 88),
    'Diabetes'                            : (69276, 72.1, 73, 0, 115, 54, 89),
    'Doença de Chagas'                    : (3671, 72.0, 73, 1, 114, 54, 88),
    'Outras isquêmicas do coração'        : (20964, 72.9, 74, 0, 115, 55, 90),
    'Aterosclerose e aneurisma'           : (14628, 72.5, 74, 0, 114, 54, 90),
    'Doença renal crônica'                : (10476, 71.4, 74, 0, 114, 50, 90),
    'Septicemia'                          : (27880, 70.8, 75, 0, 115, 46, 91),
    'Apendicite, hérnia e obstrução'      : (9984, 71.2, 75, 0, 110, 48, 90),
    'Insuficiência renal aguda'           : (7183, 72.6, 76, 0, 111, 51, 91),
    'COVID-19'                            : (62367, 74.3, 77, 0, 115, 54, 92),
    'AVC isquêmico e não especificado'    : (45807, 75.2, 77, 0, 114, 58, 91),
    'Sequelas e outras cerebrovasculares' : (31765, 75.6, 77, 0, 113, 58, 91),
    'Diarreia e gastroenterite'           : (4621, 67.8, 77, 0, 110, 5, 92),
    'Doença hipertensiva'                 : (61313, 76.0, 78, 0, 115, 56, 93),
    'DPOC e enfisema'                     : (46621, 76.6, 78, 0, 115, 62, 91),
    'Insuficiência cardíaca'              : (32170, 76.1, 78, 0, 114, 57, 92),
    'Quedas'                              : (14796, 73.5, 78, 0, 115, 47, 92),
    'Pneumonia e gripe'                   : (87128, 75.4, 80, 0, 115, 53, 94),
    'Parkinson'                           : (5258, 80.5, 81, 21, 110, 68, 92),
    'Desnutrição'                         : (4157, 74.4, 81, 0, 115, 43, 95),
    'Pneumonite por aspiração'            : (7867, 77.2, 82, 0, 114, 55, 95),
    'Infecção do trato urinário'          : (26445, 79.9, 83, 0, 115, 63, 94),
    'Alzheimer e demências'               : (35344, 84.9, 86, 0, 115, 74, 95),
}

# mortes por faixa quinquenal: 0-4, 5-9, … 85-89, 90+
HIST = {
    'Afecções perinatais'                 : [16471, 13, 12, 17, 13, 9, 2, 4, 4, 4, 3, 9, 6, 8, 5, 6, 8, 4, 5],
    'Malformações congênitas'             : [7423, 230, 163, 194, 145, 107, 110, 120, 109, 112, 150, 112, 130, 106, 77, 76, 47, 37, 45],
    'Homicídio'                           : [121, 52, 249, 4219, 7803, 6563, 5228, 4166, 3254, 2145, 1428, 1071, 695, 456, 264, 167, 92, 45, 53],
    'Gravidez, parto e puerpério'         : [0, 0, 10, 119, 258, 327, 316, 279, 126, 15, 3, 2, 0, 0, 2, 0, 0, 1, 0],
    'Afogamento'                          : [443, 128, 159, 352, 335, 308, 337, 344, 326, 321, 252, 248, 183, 146, 103, 81, 39, 13, 12],
    'Acidentes de transporte'             : [245, 204, 294, 1763, 3479, 3231, 2939, 2961, 2942, 2543, 2258, 2127, 1722, 1315, 996, 711, 423, 190, 109],
    'Suicídio'                            : [0, 4, 173, 914, 1448, 1484, 1458, 1497, 1431, 1194, 1053, 1007, 745, 631, 441, 329, 184, 104, 65],
    'AIDS'                                : [25, 9, 6, 29, 349, 841, 1059, 1344, 1575, 1298, 1197, 978, 704, 479, 259, 145, 92, 36, 32],
    'Epilepsia'                           : [175, 68, 68, 112, 155, 174, 162, 256, 313, 273, 359, 354, 332, 320, 251, 211, 196, 174, 151],
    'Transtornos por álcool'              : [0, 0, 1, 7, 19, 112, 263, 497, 758, 926, 1062, 1131, 933, 726, 458, 242, 117, 72, 57],
    'Tuberculose'                         : [27, 5, 17, 76, 186, 248, 297, 372, 446, 503, 562, 605, 525, 491, 386, 307, 235, 149, 91],
    'Obesidade'                           : [4, 3, 4, 22, 46, 65, 124, 201, 260, 298, 330, 334, 353, 366, 308, 225, 197, 115, 64],
    'Cirrose e doenças do fígado'         : [80, 27, 29, 54, 97, 252, 516, 1083, 1745, 2402, 3111, 3455, 3528, 3379, 2505, 1835, 1178, 697, 459],
    'Hepatites virais'                    : [11, 0, 2, 11, 6, 8, 17, 50, 81, 103, 150, 207, 245, 232, 153, 133, 92, 53, 24],
    'Pancreatite'                         : [7, 2, 5, 18, 35, 84, 139, 194, 274, 312, 332, 359, 400, 432, 371, 353, 319, 262, 194],
    'AVC hemorrágico'                     : [67, 28, 51, 76, 118, 181, 294, 623, 1078, 1441, 1895, 2192, 2375, 2581, 2622, 2489, 2274, 1683, 1176],
    'Miocardiopatias'                     : [111, 27, 31, 64, 99, 132, 199, 291, 433, 539, 682, 839, 999, 1119, 1119, 1135, 1165, 1034, 1052],
    'Infarto agudo do miocárdio'          : [19, 4, 13, 93, 224, 356, 598, 1218, 2264, 3643, 5194, 7848, 10348, 11785, 12079, 11253, 10003, 7905, 7050],
    'Asma'                                : [49, 33, 28, 39, 44, 60, 69, 89, 112, 118, 112, 138, 183, 173, 205, 255, 307, 259, 282],
    'Embolia pulmonar e cor pulmonale'    : [71, 12, 13, 48, 87, 136, 193, 290, 405, 458, 458, 619, 741, 850, 934, 1120, 1006, 930, 987],
    'Úlcera péptica'                      : [1, 2, 3, 11, 17, 40, 40, 75, 95, 169, 221, 338, 442, 524, 533, 563, 502, 380, 363],
    'Diabetes'                            : [35, 15, 27, 80, 179, 285, 366, 661, 1134, 1776, 2954, 4633, 6379, 8547, 9849, 9748, 9100, 7300, 6208],
    'Doença de Chagas'                    : [1, 0, 1, 2, 3, 3, 1, 19, 51, 127, 164, 244, 361, 478, 545, 553, 513, 346, 259],
    'Outras isquêmicas do coração'        : [5, 4, 6, 9, 29, 59, 80, 130, 306, 521, 830, 1382, 1991, 2493, 3050, 2933, 2706, 2214, 2216],
    'Aterosclerose e aneurisma'           : [10, 3, 13, 10, 34, 72, 92, 173, 268, 363, 543, 833, 1300, 1758, 2070, 2112, 1933, 1534, 1507],
    'Doença renal crônica'                : [41, 6, 8, 34, 50, 74, 111, 146, 237, 326, 429, 741, 887, 1137, 1201, 1317, 1305, 1227, 1199],
    'Septicemia'                          : [721, 64, 71, 127, 177, 212, 251, 372, 539, 734, 1029, 1499, 2018, 2653, 3151, 3493, 3749, 3473, 3547],
    'Apendicite, hérnia e obstrução'      : [142, 19, 44, 49, 60, 89, 92, 133, 197, 263, 363, 512, 727, 950, 1189, 1409, 1424, 1264, 1058],
    'Insuficiência renal aguda'           : [62, 13, 8, 20, 26, 45, 61, 101, 155, 177, 249, 395, 489, 751, 833, 1000, 1014, 854, 930],
    'COVID-19'                            : [484, 95, 91, 146, 207, 307, 435, 632, 988, 1342, 1933, 2995, 4266, 5647, 6918, 8315, 9093, 8731, 9742],
    'AVC isquêmico e não especificado'    : [12, 6, 7, 30, 40, 93, 154, 248, 558, 837, 1325, 2284, 3368, 4785, 6106, 6861, 7184, 6127, 5782],
    'Sequelas e outras cerebrovasculares' : [20, 11, 10, 20, 41, 69, 89, 156, 338, 539, 866, 1384, 2216, 3293, 4270, 4882, 5076, 4379, 4106],
    'Diarreia e gastroenterite'           : [458, 29, 19, 18, 24, 15, 30, 40, 74, 101, 104, 167, 231, 332, 423, 535, 644, 654, 723],
    'Doença hipertensiva'                 : [10, 4, 6, 17, 46, 97, 184, 425, 797, 1388, 2144, 3181, 4507, 5850, 6886, 7667, 8589, 8498, 11017],
    'DPOC e enfisema'                     : [15, 11, 4, 9, 23, 31, 47, 77, 192, 343, 870, 1798, 3492, 5204, 6686, 7554, 7893, 6526, 5846],
    'Insuficiência cardíaca'              : [35, 15, 13, 30, 51, 107, 125, 219, 395, 583, 921, 1476, 2159, 2914, 3798, 4340, 4989, 4685, 5315],
    'Quedas'                              : [66, 22, 18, 32, 108, 147, 202, 285, 377, 461, 554, 717, 844, 1019, 1319, 1658, 2158, 2307, 2502],
    'Pneumonia e gripe'                   : [1648, 178, 155, 266, 345, 485, 632, 859, 1303, 1544, 2212, 3298, 4550, 6233, 8417, 10294, 12856, 13523, 18330],
    'Parkinson'                           : [0, 0, 0, 0, 4, 3, 2, 5, 6, 13, 29, 72, 157, 328, 632, 949, 1142, 1075, 841],
    'Desnutrição'                         : [176, 24, 28, 25, 23, 27, 30, 43, 68, 80, 81, 132, 162, 227, 331, 426, 566, 624, 1084],
    'Pneumonite por aspiração'            : [149, 11, 14, 31, 39, 41, 38, 74, 91, 140, 158, 241, 337, 456, 679, 853, 1211, 1316, 1988],
    'Infecção do trato urinário'          : [76, 17, 23, 33, 56, 58, 59, 109, 165, 264, 414, 709, 1098, 1673, 2440, 3401, 4473, 4845, 6532],
    'Alzheimer e demências'               : [11, 6, 12, 7, 12, 6, 11, 18, 39, 48, 86, 152, 394, 959, 2214, 4252, 6869, 8694, 11554],
}

SURFACE, FIG_BG = "#fcfcfb", "#f7f7f5"
TXT, TXT2, TXT3 = "#111111", "#555555", "#7b7b76"
ACENTO, FAIXA, GRID, REF = "#d1453b", "#e79c92", "#e6e6e2", "#b6b6ae"

# paleta categórica das famílias — validada para a superfície #fcfcfb:
# banda de luminosidade, piso de croma, separação CVD e contraste, todos PASS
FAMILIA = {
    "circ":  ("Aparelho circulatório", "#c0392b"),
    "resp":  ("Aparelho respiratório", "#c27508"),
    "inf":   ("Infecciosas", "#6f8f1e"),
    "meta":  ("Metabólicas, digestivas e renais", "#00826d"),
    "neuro": ("Neurológicas e mentais", "#2b6ca3"),
    "ext":   ("Causas externas", "#6247b5"),
    "mat":   ("Materno-infantis", "#b0446e"),
}


def mg(n):
    """milhar com ponto, como se escreve em português"""
    return f"{n:,}".replace(",", ".")


def vg(v, casas=1):
    return f"{v:.{casas}f}".replace(".", ",")


# ============================================================ figura 1
# a escala: quantas mortes cada causa produziu, com o câncer inteiro de régua
ORDEM1 = sorted(DADOS, key=lambda g: -DADOS[g][0])

fig = plt.figure(figsize=(12.4, 18.4), dpi=200, facecolor=FIG_BG)
ax = fig.add_axes((0.295, 0.085, 0.665, 0.754))
ax.set_facecolor(SURFACE)

n = len(ORDEM1)
# régua: o tumor que mais mata no país, para comparar causa com causa. O total
# de câncer somado (231.986) não serve de linha aqui — esmagaria a escala e
# compararia um capítulo inteiro contra doenças individuais
ax.axvline(MORTES_PULMAO, color=ACENTO, lw=1.6, ls=(0, (5, 3.5)), zorder=2)
ax.text(MORTES_PULMAO + 2600, 20,
        f"câncer de pulmão — {mg(MORTES_PULMAO)} mortes\no tumor que mais mata no país",
        color=ACENTO, fontsize=12, fontweight="bold", ha="left", va="center",
        linespacing=1.5, zorder=5)

for i, g in enumerate(ORDEM1):
    mortes, _int, _m100, _i100, fam = DADOS[g]
    y = n - 1 - i
    ax.barh(y, mortes, height=0.6, color=FAMILIA[fam][1], zorder=3)
    ax.text(mortes + 2200, y, mg(mortes), va="center", ha="left",
            fontsize=10.5, color=TXT2, zorder=3)

ax.set_yticks(range(n))
ax.set_yticklabels(list(reversed(ORDEM1)), fontsize=10.5, color=TXT2)
ax.set_ylim(-0.7, n - 0.3)
ax.set_xlim(0, 99_500)
ax.set_xticks([0, 20_000, 40_000, 60_000, 80_000])
ax.set_xticklabels(["0", "20 mil", "40 mil", "60 mil", "80 mil"])
ax.grid(axis="x", color=GRID, lw=0.8)
ax.set_axisbelow(True)
for sp in ax.spines.values():
    sp.set_visible(False)
ax.tick_params(colors=TXT3, labelsize=11.5, length=0)
ax.set_xlabel("mortes em 2022", fontsize=12.5, color=TXT2, labelpad=10)

ax.legend(handles=[Patch(facecolor=c, label=rot) for rot, c in FAMILIA.values()],
          loc="lower left", bbox_to_anchor=(-0.005, 1.005), ncol=3, frameon=False,
          fontsize=10.5, labelcolor=TXT2, handletextpad=0.8, columnspacing=2.0,
          handlelength=1.5, handleheight=1.0, borderpad=0.0, labelspacing=0.7)

fig.text(0.082, 0.974, "O que mata no Brasil quando não é câncer",
         ha="left", va="top", fontsize=25, fontweight="bold", color=TXT)
fig.text(0.082, 0.9525,
         "As 43 causas de morte com nome próprio fora do capítulo dos tumores, Brasil, 2022",
         ha="left", va="top", fontsize=13, color=TXT2)
fig.text(0.082, 0.9345,
         "Quatorze causas isoladas matam mais do que o câncer de pulmão, o tumor mais letal do país. Infarto mata\n"
         "92.815 — três vezes o pulmão, e mais do que os cinco piores tumores juntos. Somados, todos os cânceres dão\n"
         "231.986 mortes, 15,4% do país; estas 43 causas cobrem 77,4% de todo o resto.",
         ha="left", va="top", fontsize=13.5, color=TXT, linespacing=1.6)

fig.text(0.082, 0.040,
         "Fonte: Ministério da Saúde — Sistema de Informações sobre Mortalidade, óbitos de 2022 por causa básica. Agrupamento por blocos da CID-10.\n"
         "COVID-19 aparece em B34.2, e não em U07: é assim que o SIM brasileiro codificou a doença em 2022. Alzheimer soma G30–G31 e F00–F03, que descrevem a mesma\n"
         "doença em capítulos diferentes. Ficam de fora os códigos residuais de cada capítulo e as 91.888 mortes por sintomas mal definidos, que não nomeiam doença.",
         ha="left", va="top", fontsize=9.5, color=TXT3, linespacing=1.6)

out1 = "dataviz/nao_cancer_quantidades_2022.png"
fig.savefig(out1, facecolor=fig.get_facecolor())
print("ok:", out1)

# ============================================================ figura 2
# mata × interna, o mesmo cruzamento do gráfico do câncer
# fora: gravidez/parto (internação é parto, não tratamento), as causas externas
# desagregadas (o SIH não separa a causa da lesão) e seis causas pequenas que
# só apertariam os rótulos sem mudar a leitura
FORA_SCATTER = {
    "Gravidez, parto e puerpério",
    "Homicídio", "Acidentes de transporte", "Quedas", "Suicídio", "Afogamento",
    "Obesidade", "Hepatites virais", "Úlcera péptica",
    "Insuficiência renal aguda", "Embolia pulmonar e cor pulmonale",
    "Miocardiopatias",
}
EXTERNAS = ("Causas externas (lesões)", 141_944, 1_353_446)

PONTOS = {g: (m100, i100, mortes, fam)
          for g, (mortes, _i, m100, i100, fam) in DADOS.items()
          if g not in FORA_SCATTER}
PONTOS[EXTERNAS[0]] = (EXTERNAS[1] / POP * 1e5, EXTERNAS[2] / POP * 1e5,
                       EXTERNAS[1], "ext")

XLIM, YLIM = (0.95, 92.0), (0.185, 1050.0)

fig2 = plt.figure(figsize=(12.4, 13.8), dpi=200, facecolor=FIG_BG)
ax2 = fig2.add_axes((0.082, 0.125, 0.90, 0.625))
ax2.set_facecolor(SURFACE)

ax2.set_xscale("log")
ax2.set_yscale("log")
ax2.set_xlim(*XLIM)
ax2.set_ylim(*YLIM)
ax2.set_xticks([1, 2, 4, 8, 16, 32, 64])
ax2.set_yticks([0.25, 1, 4, 16, 64, 256, 1024])
ax2.set_xticklabels(["1", "2", "4", "8", "16", "32", "64"])
ax2.set_yticklabels(["0,25", "1", "4", "16", "64", "256", "1.024"])
ax2.minorticks_off()
ax2.grid(color=GRID, lw=0.8)
ax2.set_axisbelow(True)
for sp in ax2.spines.values():
    sp.set_visible(False)
ax2.tick_params(colors=TXT3, labelsize=12, length=0)

# linhas de razão internação/morte — paralelas em log-log
fixos = []
for razao, texto, cor in ((1, "1 internação por morte", ACENTO),
                          (5, "5 por morte", REF),
                          (25, "25 por morte", REF)):
    ax2.plot(list(XLIM), [x * razao for x in XLIM], color=cor,
             lw=1.5 if razao == 1 else 1.1, ls=(0, (5, 3.5)), zorder=1)
    x_ini = XLIM[0] * 1.06
    fixos.append(ax2.text(x_ini, x_ini * razao * 1.10, texto,
                          color=ACENTO if razao == 1 else TXT3,
                          fontweight="bold" if razao == 1 else "normal",
                          fontsize=11 if razao == 1 else 10.5,
                          ha="left", va="bottom", zorder=1))

# faixa sombreada abaixo da paridade — onde o hospital não tem o que oferecer
ax2.fill_between(list(XLIM), [YLIM[0]] * 2, list(XLIM), color="#f3e2df",
                 alpha=0.55, zorder=0)
fixos.append(ax2.text(1.03, 0.205,
                      "abaixo da linha: morre mais gente do que chega a internar",
                      color="#8f5049", fontsize=11.5, fontstyle="italic",
                      ha="left", va="bottom", zorder=1))


def area(mortes):
    """área da bolha em pt², proporcional ao número de mortes"""
    return 80 + mortes / 92_815 * 1250


for g, (mx, my, mortes, fam) in sorted(PONTOS.items(), key=lambda kv: -kv[1][2]):
    ax2.scatter(mx, my, s=area(mortes), color=FAMILIA[fam][1], alpha=0.85,
                edgecolors=SURFACE, linewidths=2, zorder=3)

ax2.set_xlabel("mortes por 100 mil habitantes  ·  escala dobrando a cada marca",
               fontsize=12.5, color=TXT2, labelpad=10)
ax2.set_ylabel("internações no SUS por 100 mil habitantes",
               fontsize=12.5, color=TXT2, labelpad=10)

leg_tam = [Line2D([], [], marker="o", ls="", markerfacecolor=TXT3, alpha=0.8,
                  markeredgecolor=SURFACE, markeredgewidth=1.5,
                  markersize=area(v) ** 0.5 * 0.72, label=rot)
           for v, rot in ((90_000, "90 mil mortes"), (30_000, "30 mil"),
                          (5_000, "5 mil"))]
l1 = ax2.legend(handles=leg_tam, loc="lower right", frameon=False, fontsize=11,
                labelcolor=TXT2, handletextpad=1.3, borderpad=1.0,
                labelspacing=1.4, title="tamanho da bolha = mortes no ano",
                title_fontsize=10.5, alignment="left")
ax2.add_artist(l1)
ax2.legend(handles=[Line2D([], [], marker="o", ls="", markerfacecolor=c,
                           markeredgecolor=SURFACE, markersize=9, label=rot)
                    for rot, c in FAMILIA.values()],
           loc="upper left", bbox_to_anchor=(-0.005, 1.055), ncol=4, frameon=False,
           fontsize=10.5, labelcolor=TXT2, handletextpad=0.6, columnspacing=1.6,
           borderpad=0.0)

# ------------------------------------------------- rótulos sem sobreposição
# mesmo algoritmo do gráfico do câncer: tenta oito direções ao redor de cada
# bolha, em cinco afastamentos, e fica na de menor custo — sair do painel é
# proibido, encostar em rótulo já posto ou em outra bolha é penalizado
QUEBRA = {
    "Infarto agudo do miocárdio": "Infarto agudo\ndo miocárdio",
    "AVC isquêmico e não especificado": "AVC isquêmico e\nnão especificado",
    "Sequelas e outras cerebrovasculares": "Sequelas e outras\ncerebrovasculares",
    "Infecção do trato urinário": "Infecção do\ntrato urinário",
    "Cirrose e doenças do fígado": "Cirrose e\ndoenças do fígado",
    "Outras isquêmicas do coração": "Outras isquêmicas\ndo coração",
    "Aterosclerose e aneurisma": "Aterosclerose\ne aneurisma",
    "Apendicite, hérnia e obstrução": "Apendicite, hérnia\ne obstrução",
    "Pneumonite por aspiração": "Pneumonite\npor aspiração",
    "Transtornos por álcool": "Transtornos\npor álcool",
    "Diarreia e gastroenterite": "Diarreia e\ngastroenterite",
    "Malformações congênitas": "Malformações\ncongênitas",
    "Alzheimer e demências": "Alzheimer\ne demências",
    "Doença renal crônica": "Doença\nrenal crônica",
    "Causas externas (lesões)": "Causas externas\n(lesões)",
    "Afecções perinatais": "Afecções\nperinatais",
    "Insuficiência cardíaca": "Insuficiência\ncardíaca",
    "Doença hipertensiva": "Doença\nhipertensiva",
    "Pneumonia e gripe": "Pneumonia\ne gripe",
    "DPOC e enfisema": "DPOC e\nenfisema",
    "Doença de Chagas": "Doença\nde Chagas",
}
DIRECOES = [(1, 0, "left", "center"), (-1, 0, "right", "center"),
            (0, 1, "center", "bottom"), (0, -1, "center", "top"),
            (0.72, 0.72, "left", "bottom"), (0.72, -0.72, "left", "top"),
            (-0.72, 0.72, "right", "bottom"), (-0.72, -0.72, "right", "top")]
AFASTAMENTO = (7, 14, 22, 32, 44, 58, 74, 92, 115, 145, 180, 220)

fig2.canvas.draw()
renderer = fig2.canvas.get_renderer()
inv = ax2.transData.inverted()
painel = ax2.get_window_extent(renderer)
ocupado = [lg.get_window_extent(renderer).expanded(1.02, 1.02)
           for lg in (l1, ax2.get_legend())]
ocupado += [t.get_window_extent(renderer).expanded(1.08, 1.4) for t in fixos]
bolhas = []
for g, (mx, my, mortes, _f) in PONTOS.items():
    px, py = ax2.transData.transform((mx, my))
    bolhas.append((px, py, area(mortes) ** 0.5 / 2 * fig2.dpi / 72))

for g, (mx, my, mortes, fam) in sorted(PONTOS.items(), key=lambda kv: -kv[1][2]):
    destaque = mortes >= 60_000
    px, py = ax2.transData.transform((mx, my))
    r = area(mortes) ** 0.5 / 2 * fig2.dpi / 72
    txt = ax2.text(mx, my, QUEBRA.get(g, g),
                   fontsize=12.5 if destaque else 10.5,
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
                if lado > 0:
                    custo += 9000 + lado
            for o in ocupado:
                if bb.overlaps(o):
                    custo += 20000
            for bx, by, br in bolhas:
                if (bb.x0 - br < bx < bb.x1 + br) and (bb.y0 - br < by < bb.y1 + br):
                    custo += 4000
            custo += {0: 0, 1: 5, 2: 3, 3: 3}.get(passo, 8) + afasta * 0.6
            if melhor_custo is None or custo < melhor_custo:
                melhor, melhor_custo = (ha, va, alvo, afasta), custo
        if melhor_custo is not None and melhor_custo < 8:
            break
    ha, va, alvo, afasta = melhor
    txt.set_ha(ha)
    txt.set_va(va)
    txt.set_position(inv.transform(alvo))
    ocupado.append(txt.get_window_extent(renderer).expanded(1.06, 1.3))
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
        ax2.plot([p0[0], p1[0]], [p0[1], p1[1]], color="#9d9d95", lw=1.0, zorder=2)

fig2.text(0.082, 0.964, "As doenças de que se morre sem passar pelo hospital",
          ha="left", va="top", fontsize=25, fontweight="bold", color=TXT)
fig2.text(0.082, 0.9345,
          "Causas de morte que não são câncer, 2022 — quanto cada uma mata (horizontal) contra quanto interna no SUS (vertical)",
          ha="left", va="top", fontsize=13, color=TXT2)
fig2.text(0.082, 0.9095,
          "No gráfico do câncer só o tumor de pulmão ficava abaixo da paridade. Fora do câncer são seis, e formam um grupo\n"
          "coerente: Chagas interna 0,16 vez por morte, Parkinson 0,26, Alzheimer 0,48, pneumonite por aspiração 0,48,\n"
          "sequelas de AVC 0,67 e doença hipertensiva 0,97 — doenças crônicas e degenerativas para as quais o hospital não\n"
          "tem oferta: não há cirurgia, não há ciclo de tratamento, não há alta.",
          ha="left", va="top", fontsize=13.5, color=TXT, linespacing=1.6)

fig2.text(0.082, 0.075,
          "Fonte: Ministério da Saúde — Sistema de Informações sobre Mortalidade (óbitos com causa básica) e Sistema de Informações Hospitalares (internações com\n"
          "diagnóstico principal), 2022. População: IBGE, Censo 2022. Taxas brutas, não padronizadas por idade — comparáveis entre si, não com séries internacionais.\n"
          "Internação conta episódio, não paciente. Causas externas entram agregadas porque o SIM registra a causa (agressão, queda) e o SIH, a lesão que ela produziu:\n"
          "o campo de causa externa do SIH está vazio em 2022. Gravidez, parto e puerpério fica fora — suas 2,2 milhões de internações são partos, não tratamento.",
          ha="left", va="top", fontsize=9.5, color=TXT3, linespacing=1.6)

out2 = "dataviz/nao_cancer_internacao_mortalidade_2022.png"
fig2.savefig(out2, facecolor=fig2.get_facecolor())
print("ok:", out2)

# ============================================================ figura 3
# mapa de calor: que fatia das mortes de cada causa cai em cada faixa etária
GRUPOS_ET = list(range(0, 95, 5))
ORDEM3 = sorted(IDADE, key=lambda g: (IDADE[g][2], IDADE[g][1]))

RAMPA = LinearSegmentedColormap.from_list("rodado_seq", [
    "#fdf6f4", "#f9dfd9", "#f2bdb2", "#e8968a", "#dc6c5f", "#c9402f", "#96271d"])

fig3 = plt.figure(figsize=(12.4, 13.4), dpi=200, facecolor=FIG_BG)
ax3 = fig3.add_axes((0.285, 0.225, 0.665, 0.600))
ax3.set_facecolor(SURFACE)

matriz = [[100 * n / sum(HIST[g]) for n in HIST[g]] for g in ORDEM3]

# o teto da rampa é a maior célula fora das duas linhas infantis (Alzheimer,
# 32,7% das mortes em 90+). Perinatais (99,2%) e malformações (78,2%) estouram
# a escala e saturam no tom mais escuro: sem esse corte as duas apagariam o
# miolo do mapa, que é onde está a informação
VMAX = 33
im = ax3.imshow(matriz, aspect="auto", cmap=RAMPA, norm=Normalize(0, VMAX),
                interpolation="nearest")

# risco branco na idade mediana — ancora o mapa à coluna da tabela
for i, g in enumerate(ORDEM3):
    x = min(IDADE[g][2] / 5, 18.5) - 0.5
    ax3.plot([x, x], [i - 0.45, i + 0.45], color="#ffffff", lw=2.2,
             solid_capstyle="butt", zorder=3)

ax3.set_yticks(range(len(ORDEM3)))
ax3.set_yticklabels(ORDEM3, fontsize=10.5, color=TXT2)
ax3.set_xticks(range(0, 19, 2))
ax3.set_xticklabels([f"{g}" for g in GRUPOS_ET[::2]], fontsize=11.5, color=TXT3)
ax3.tick_params(length=0)
for sp in ax3.spines.values():
    sp.set_visible(False)
ax3.set_xlabel("faixa etária no momento da morte  ·  última coluna = 90 anos ou mais",
               fontsize=12.5, color=TXT2, labelpad=10)

# as etiquetas do eixo Y ganham a cor da família, para amarrar às outras figuras
for tick, g in zip(ax3.get_yticklabels(), ORDEM3):
    tick.set_color(FAMILIA[DADOS[g][4]][1])

cb = fig3.colorbar(im, ax=ax3, orientation="horizontal", fraction=0.030,
                   pad=0.105, aspect=42)
cb.outline.set_visible(False)
cb.set_ticks([0, 5, 10, 15, 20, 25, 30])
cb.ax.tick_params(colors=TXT3, labelsize=10.5, length=0)
cb.set_label("fatia das mortes daquela causa que cai na faixa  ·  cada linha soma 100%  ·  as duas linhas infantis estouram a escala",
             fontsize=10.5, color=TXT3, labelpad=9)
cb.ax.xaxis.set_major_formatter(lambda v, _: f"{v:g}%".replace(".", ","))

fig3.text(0.082, 0.972, "De 0 a 86 anos: a idade separa mais fora do câncer",
          ha="left", va="top", fontsize=25, fontweight="bold", color=TXT)
fig3.text(0.082, 0.9455,
          "Cada linha é uma causa de morte e soma 100%: quanto mais escura a célula, mais mortes daquela causa naquela idade",
          ha="left", va="top", fontsize=13, color=TXT2)
fig3.text(0.082, 0.9235,
          "O câncer inteiro cabe entre a mediana de 33 anos do testículo e a de 78 da próstata. Fora dele a amplitude é o\n"
          "dobro: as perinatais matam no primeiro dia, o homicídio aos 30, o Alzheimer aos 86. Fora as causas infantis,\n"
          "homicídio é a mais jovem em volume: um terço das suas 38.874 mortes vem antes dos 25 anos.",
          ha="left", va="top", fontsize=13.5, color=TXT, linespacing=1.6)

fig3.text(0.082, 0.150,
          "Fonte: Ministério da Saúde — Sistema de Informações sobre Mortalidade, óbitos de 2022 por causa básica. Percentuais dentro de cada causa, não entre causas —\n"
          "a cor compara idades de uma mesma doença, nunca o tamanho de uma doença contra a outra. Fora os óbitos sem idade preenchida (2,4%), os 0,44% com idade\n"
          "impossível (116 a 220 anos) e os 0,07% com idade negativa. Afecções perinatais têm 60% dos óbitos sem idade em anos: a linha continua indicando corretamente\n"
          "que se morre no primeiro ano de vida, mas não sustenta comparação de volume com as demais. A cor do nome segue a família da doença, como nas outras figuras.",
          ha="left", va="top", fontsize=9.5, color=TXT3, linespacing=1.6)

out3 = "dataviz/nao_cancer_idade_perfil_2022.png"
fig3.savefig(out3, facecolor=fig3.get_facecolor())
print("ok:", out3)
