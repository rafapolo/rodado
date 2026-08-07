#!/usr/bin/env python3
"""O outro lado da mesma régua: quantos deputados declaram ter menos do que o
mandato lhes pagou.

O gráfico dos múltiplos do subsídio olha para cima — os 47 cujo patrimônio
cresceu mais do que o cargo poderia ter pago. Este olha para baixo, e mede
outra coisa: não o crescimento, mas o **estoque**. Ao fim do mandato, quanto
cada deputado declara possuir no total, comparado com o que o mandato inteiro
lhe depositou em conta.

  universo   os mesmos 472 deputados federais eleitos em 2018 que voltaram a
             registrar candidatura em 2022.
  eixo y     patrimônio total declarado no registro de 2022 dividido pelo
             subsídio bruto do mandato (R$ 1.516.521). 1,0 = o deputado declara
             possuir exatamente o que o cargo lhe pagou em 42 meses.
  eixo x     os 472 ordenados do menor para o maior.

Por que a comparação não acusa ninguém: o subsídio é bruto. Descontado imposto
de renda e previdência sobram cerca de R$ 1,1 milhão, e sobre isso ainda incide
a vida — moradia, escola, viagem, o custo de manter presença em dois estados.
Declarar menos de 1× é o comportamento esperado de quem gasta o que ganha.

O que o gráfico mostra, então, é a **linha de base**: a forma que uma declaração
de bens tem quando o salário é a renda principal. É essa forma que torna os 47
do outro gráfico visíveis como exceção. E é ela que dá escala ao terceiro grupo,
o dos que declaram menos que o subsídio do mandato e ainda assim declararam
em 2022 menos do que tinham em 2018.

Ressalva de dado: bens_candidato traz ~1% de linhas byte-idênticas repetidas.
A consulta aplica DISTINCT, como no gráfico dos múltiplos.

Consulta (beelink, via SSH — BEELINK_HOST, default 'beelink'):
  br_tse_eleicoes/resultados_candidato_municipio   eleitos de 2018
  br_tse_eleicoes/candidatos                       CPF para casar 2018 e 2022
  br_tse_eleicoes/bens_candidato                   bens de 2018 e de 2022
"""
import json
import os
import subprocess

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

SUBSIDIO = 1_516_521.0   # bruto acumulado do mandato entre as duas declarações
# R$ 33.763,00/mês, fixado pelo Decreto Legislativo 276/2014 com efeitos a
# partir de 1º/02/2015 e congelado até 31/12/2022 — vigorou, portanto, no
# mandato inteiro. São 42 meses (fev/2019 a jul/2022) mais os décimos-terceiros
# de 2019 (proporcional), 2020 e 2021.
# Antes daqui havia R$ 1.764.767, derivado de R$ 39.293,32/mês "desde fevereiro
# de 2019". O valor existe, a data não: ele só passou a vigorar em 1º/01/2023,
# pelo Decreto Legislativo 172/2022. A régua estava 16,4% alta.

SQL = """SET enable_progress_bar=false;
WITH bens AS (
  SELECT DISTINCT ano, sequencial_candidato, tipo_item, descricao_item, valor_item
  FROM read_parquet('~/rodado/br_tse_eleicoes/bens_candidato/*.parquet')
  WHERE ano IN (2018, 2022)
),
b18 AS (SELECT sequencial_candidato seq, SUM(valor_item) v FROM bens WHERE ano=2018 GROUP BY 1),
b22 AS (SELECT sequencial_candidato seq, SUM(valor_item) v FROM bens WHERE ano=2022 GROUP BY 1),
eleitos AS (
  SELECT DISTINCT sequencial_candidato AS seq18
  FROM read_parquet('~/rodado/br_tse_eleicoes/resultados_candidato_municipio/*.parquet')
  WHERE ano=2018 AND cargo='deputado federal'
    AND resultado IN ('eleito por media','eleito por qp')
),
c18 AS (
  SELECT cpf, sequencial, nome, sigla_uf
  FROM read_parquet('~/rodado/br_tse_eleicoes/candidatos/*.parquet')
  WHERE ano=2018 AND cargo='deputado federal'
),
c22 AS (
  SELECT cpf, sequencial, sigla_partido p22
  FROM read_parquet('~/rodado/br_tse_eleicoes/candidatos/*.parquet')
  WHERE ano=2022
)
SELECT c18.nome, c18.sigla_uf AS uf, c22.p22 AS partido,
       COALESCE(b18.v,0) AS v18, COALESCE(b22.v,0) AS v22
FROM eleitos e
JOIN c18 ON c18.sequencial = e.seq18
JOIN c22 ON c22.cpf = c18.cpf
LEFT JOIN b18 ON b18.seq = c18.sequencial
LEFT JOIN b22 ON b22.seq = c22.sequencial;
"""


def consulta(sql):
    host = os.environ.get("BEELINK_HOST", "beelink")
    res = subprocess.run(["ssh", host, "~/bin/duckdb -json"],
                         input=sql.encode(), capture_output=True, check=True)
    return json.loads(res.stdout)


rows = consulta(SQL)
for r in rows:
    r["mult"] = r["v22"] / SUBSIDIO
    r["delta"] = r["v22"] - r["v18"]
rows.sort(key=lambda r: r["mult"])

n = len(rows)
abaixo = [r for r in rows if r["mult"] < 1]
zeros = [r for r in rows if r["v22"] == 0]
encolheu = [r for r in abaixo if r["delta"] <= 0]
cresceu = [r for r in rows if r["delta"] > SUBSIDIO]   # os 39 do outro gráfico
mediana = rows[n // 2]["mult"]
print(f"universo {n} · abaixo de 1×: {len(abaixo)} ({100*len(abaixo)/n:.1f}%) · "
      f"zero bens: {len(zeros)} · abaixo e encolheu: {len(encolheu)} · "
      f"mediana {mediana:.2f}×")

# ═════════════════════════════════════════════════════════════════ gráfico
SURFACE, FIG_BG = "#fcfcfb", "#f7f7f5"
TXT, TXT2, TXT3 = "#111111", "#555555", "#7b7b76"
ACENTO, GRID = "#d1453b", "#e6e6e2"
NEUTRO = "#c8c8c2"
ABAIXO = "#5d7f88"     # o mesmo azul-ardósia do gráfico dos múltiplos
ABAIXO_BG = "#eef2f3"

TETO = 4.0             # o eixo corta aqui; acima ficam os casos do outro gráfico

fig = plt.figure(figsize=(12.4, 10.8), dpi=200, facecolor=FIG_BG)
ax = fig.add_axes((0.088, 0.215, 0.888, 0.455))
ax.set_facecolor(SURFACE)

ax.set_xlim(-6, n + 6)
ax.set_ylim(0, TETO)
ax.grid(axis="y", color=GRID, lw=0.8)
ax.set_axisbelow(True)
for sp in ax.spines.values():
    sp.set_visible(False)
ax.tick_params(colors=TXT3, labelsize=12, length=0)
ax.set_yticks([0, 1, 2, 3, 4])
ax.set_yticklabels(["0", "1×", "2×", "3×", "4×"])
ax.set_xticks([0, 100, 200, 300, 400, n])
ax.set_xticklabels(["0", "100", "200", "300", "400", str(n)])

# faixa de fundo marcando o território abaixo da linha do subsídio
ax.axhspan(0, 1, color=ABAIXO_BG, zorder=0)

# a curva: cada deputado uma coluna de 1 unidade de largura, sem vão entre elas
for i, r in enumerate(rows):
    h = min(r["mult"], TETO)
    if h <= 0:
        continue
    # vermelho = exatamente os 39 do gráfico de crescimento patrimonial, para
    # que as duas peças se leiam juntas. Não é o mesmo recorte de "os maiores
    # patrimônios": crescer muito e ter muito são coisas diferentes, e só 27
    # dos 39 estão entre os 39 maiores estoques.
    cor = ABAIXO if r["mult"] < 1 else (ACENTO if r["delta"] > SUBSIDIO else NEUTRO)
    ax.add_patch(Rectangle((i - 0.5, 0), 1.0, h, facecolor=cor,
                           edgecolor="none", zorder=3))

# os 17 que declararam patrimônio zero não têm barra — marca explícita
ax.plot([len(zeros) / 2 - 0.5], [0.045], marker="v", ms=7, color=ABAIXO, zorder=5)
ax.text(len(zeros) / 2 - 0.5 + 7, 0.10,
        f"{len(zeros)} declararam\npatrimônio zero", fontsize=10.5, color=ABAIXO,
        va="bottom", ha="left", linespacing=1.4, zorder=6)

# a linha do subsídio e o ponto em que a curva a cruza
ax.axhline(1, color=TXT2, lw=1.4, ls=(0, (5, 3.5)), zorder=6)
ax.plot([len(abaixo) - 0.5, len(abaixo) - 0.5], [0, 1], color=TXT2, lw=1.1,
        ls=(0, (2, 3)), zorder=6)
ax.text(len(abaixo) - 9, 1.30,
        f"a curva cruza a linha no deputado {len(abaixo)}",
        fontsize=11.5, color=TXT, va="bottom", ha="right", zorder=7)

ax.text(8, 1.09, f"1× = R\\$ {SUBSIDIO/1e6:.2f}".replace(".", ",")
        + " milhão, todo o subsídio bruto do mandato",
        fontsize=11.5, color=TXT2, va="bottom", ha="left", zorder=7)

# mediana
ax.plot([n // 2 - 0.5], [mediana], marker="o", ms=5.5, color=TXT,
        zorder=7, mec=SURFACE, mew=1.2)
ax.text(n // 2 - 12, mediana + 0.13,
        f"mediana: {('%.2f' % mediana).replace('.', ',')}× — R\\$ "
        + f"{mediana*SUBSIDIO/1e6:.2f}".replace(".", ",") + " milhão",
        fontsize=11, color=TXT2, va="bottom", ha="right", zorder=7)

ax.text(n - 66, 3.52,
        f"os {len(cresceu)} do gráfico anterior estão\ntodos aqui — nenhum deles declara\nmenos do que o mandato pagou",
        fontsize=11, color=ACENTO, va="top", ha="right", linespacing=1.45,
        zorder=7)

ax.set_ylabel("patrimônio declarado em 2022,\nem múltiplos do subsídio do mandato",
              fontsize=12.5, color=TXT2, labelpad=12, linespacing=1.5)
fig.text(0.532, 0.160,
         "os 472 deputados, ordenados do menor para o maior patrimônio declarado",
         ha="center", va="top", fontsize=12.5, color=TXT2)

fig.text(0.088, 0.972, "Sete em cada dez declaram menos do que o mandato pagou",
         ha="left", va="top", fontsize=22, fontweight="bold", color=TXT)
fig.text(0.088, 0.936,
         "Patrimônio total declarado ao fim do mandato, comparado ao subsídio bruto que o cargo depositou no período",
         ha="left", va="top", fontsize=13, color=TXT2)
fig.text(0.088, 0.902,
         f"O mandato de 2019 a 2022 pagou R\\$ 1,76 milhão bruto a cada deputado. Ao registrar a candidatura\n"
         f"seguinte, {len(abaixo)} dos 472 — {100*len(abaixo)/n:.0f}% — declararam possuir, somando tudo o que têm no mundo, menos do que\n"
         f"isso. A mediana da Câmara é R\\$ 1,05 milhão, seis décimos de um mandato, e {len(zeros)} deputados federais\n"
         f"declararam não possuir bem nenhum.\n"
         f"Não é acusação: o valor é bruto, e depois de imposto e de viver sobra pouco para virar patrimônio.\n"
         f"É a linha de base — a forma que uma declaração tem quando o salário é mesmo a renda principal.\n"
         f"É ela que faz dos {len(cresceu)} em vermelho — os do gráfico de crescimento — exceção, e não padrão.",
         ha="left", va="top", fontsize=13.2, color=TXT, linespacing=1.55)

for x, cor, rot in ((0.088, ABAIXO, f"declara menos do que o mandato pagou ({len(abaixo)})"),
                    (0.478, NEUTRO, f"declara mais ({n - len(abaixo) - len(cresceu)})"),
                    (0.672, ACENTO, f"cresceu mais do que o mandato pagou ({len(cresceu)})")):
    fig.patches.append(Rectangle((x, 0.694), 0.016, 0.019,
                                 transform=fig.transFigure, facecolor=cor,
                                 edgecolor="none", zorder=4))
    fig.text(x + 0.024, 0.7035, rot, fontsize=11, color=TXT2,
             va="center", ha="left")

fig.text(0.088, 0.124,
         "Fonte: Tribunal Superior Eleitoral — declarações de bens nos registros de candidatura de 2018 e 2022. Subsídio: Câmara dos Deputados,\n"
         "R\\$ 33.763,00 por mês de fevereiro de 2019 a julho de 2022, mais os décimos-terceiros — R\\$ 1.516.521 bruto, antes de imposto de renda,\n"
         "previdência e qualquer despesa. Universo: os 472 deputados eleitos em 2018 que voltaram a registrar candidatura em 2022, os únicos\n"
         "com os dois pontos da série. A declaração do TSE segue a regra do imposto de renda e registra bens pelo custo de aquisição.\n"
         "Em vermelho, os 39 cujo patrimônio cresceu mais do que todo o subsídio do mandato — o recorte do gráfico de crescimento patrimonial.\n"
         "Não é o mesmo que os 39 maiores patrimônios: só 27 estão nos dois grupos. O eixo corta em 4×; a maior barra chega a 37×.",
         ha="left", va="top", fontsize=9.1, color=TXT3, linespacing=1.55)

out = "pages/analises/img/patrimonio-abaixo-subsidio.png"
fig.savefig(out, facecolor=fig.get_facecolor())
print("ok:", out)
