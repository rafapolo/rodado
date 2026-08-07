#!/usr/bin/env python3
"""Evolução patrimonial dos deputados federais entre as declarações de 2018 e 2022.

Compara o que cada deputado eleito em 2018 declarou de bens à Justiça Eleitoral
naquele registro com o que declarou no registro de 2022, e mede a diferença
contra o teto do que o mandato poderia ter pago: o subsídio bruto integral do
período, sem descontar imposto, previdência ou qualquer despesa de vida.

  universo   472 deputados federais eleitos em 2018 que voltaram a registrar
             candidatura em 2022 (qualquer cargo) — só quem tem os dois pontos
             da série pode ser comparado.
  eixo do    crescimento patrimonial declarado dividido pelo subsídio bruto
  gráfico A  acumulado do mandato. 1,0 = o deputado teria de ter poupado cada
             centavo recebido, por 42 meses, e não gasto nada. Cada barra vem
             partida em duas cores: o trecho que o capital social das empresas
             do próprio deputado já daria conta de explicar, e o que sobra sem
             nenhuma contrapartida empresarial.
  gráfico B  distribuição desse mesmo múltiplo entre os 472, para situar os
             casos extremos no conjunto.

Sobre a segunda cor: quem é sócio de empresa tem origem de renda fora do
subsídio, e cobrá-lo pelo salário do cargo seria injusto. A régua usada aqui é
deliberadamente generosa — soma o capital social **integral** de toda empresa em
que o deputado consta como sócio ou titular, sem descontar a fração que cabe aos
demais sócios e sem exigir que o capital tenha virado renda. Se nem essa régua
cobre o crescimento declarado, o excedente não tem, no dado público, de onde ter
vindo. Onde ela cobre, o caso deixa de ser anomalia de salário e vira pergunta
de contabilidade empresarial — outra apuração, com outros documentos.

Subsídio: R$ 33.763,00/mês (Decreto Legislativo 276/2014, efeitos desde 1º/02/2015).
Entre a declaração de 2018 (registro em agosto) e a de 2022 (idem) o eleito
exerceu mandato de fev/2019 a jul/2022 — 42 meses — mais os décimos-terceiros
de 2019 (proporcional), 2020 e 2021. Total bruto: R$ 1.516.521.

Por que a comparação faz sentido: a declaração de bens do TSE segue a regra do
imposto de renda e registra bens pelo **custo de aquisição**, não pelo valor de
mercado. Um imóvel comprado em 1990 continua declarado a preço de 1990 e não
sobe com a inflação nem com a valorização do bairro. Crescimento no total
declarado é, portanto, dinheiro novo efetivamente gasto em bens novos — não
reavaliação de patrimônio antigo.

O que o gráfico NÃO afirma: que o excedente é ilícito. Deputado pode ter renda
de empresa, aluguel, herança, venda de bem, ganho de capital ou renda do
cônjuge. O múltiplo mede o quanto a remuneração do mandato deixa de explicar —
é onde a checagem começa, não onde ela termina.

Consulta (beelink, via SSH — BEELINK_HOST, default 'beelink'):
  br_tse_eleicoes/resultados_candidato_municipio   eleitos de 2018
  br_tse_eleicoes/candidatos                       CPF, nome, UF, partido
  br_tse_eleicoes/bens_candidato                   bens de 2018 e de 2022
  br_me_cnpj/socios                                quadro societário
  br_me_cnpj/empresas                              capital social

Casamento com o CNPJ: nome completo (sem acento, em caixa alta) mais os seis
dígitos centrais do CPF, que a Receita publica sob máscara. Só qualificações de
propriedade entram — sócio (22), sócio-administrador (49), sócio com e sem
capital (52, 53) e titular pessoa física (65); administrador, presidente e
diretor contratados ficam de fora porque não implicam quota alguma.

Ressalva de dado: bens_candidato traz ~1% de linhas byte-idênticas repetidas
(mesmo candidato, mesmo item, mesmo valor, sem nenhuma coluna que as
distinga). A consulta aplica DISTINCT, o que também colapsa o caso raro de
alguém declarar dois bens genuinamente idênticos pelo mesmo valor.
"""
import json
import os
import subprocess

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

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

# capital social das empresas de quem passou da linha de 1×. Repete os CTEs de
# patrimônio porque a consulta precisa se bastar: o vínculo com o CNPJ sai do
# CPF, que não é reproduzido em lugar nenhum — o resultado volta chaveado pelo
# nome, e os 39 têm nome único entre si.
SQL_CAPITAL = """SET enable_progress_bar=false;
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
  SELECT cpf, sequencial, nome
  FROM read_parquet('~/rodado/br_tse_eleicoes/candidatos/*.parquet')
  WHERE ano=2018 AND cargo='deputado federal'
),
c22 AS (SELECT cpf, sequencial FROM read_parquet('~/rodado/br_tse_eleicoes/candidatos/*.parquet')
        WHERE ano=2022),
alvo AS (
  SELECT c18.nome, c18.cpf
  FROM eleitos e
  JOIN c18 ON c18.sequencial = e.seq18
  JOIN c22 ON c22.cpf = c18.cpf
  LEFT JOIN b18 ON b18.seq = c18.sequencial
  LEFT JOIN b22 ON b22.seq = c22.sequencial
  WHERE COALESCE(b22.v,0) - COALESCE(b18.v,0) > {subsidio}
),
soc AS (
  SELECT DISTINCT a.nome, a.cpf, s.cnpj_basico
  FROM alvo a
  JOIN read_parquet('~/rodado/br_me_cnpj/socios/*.parquet') s
    ON UPPER(strip_accents(TRIM(s.nome))) = UPPER(strip_accents(TRIM(a.nome)))
   AND SUBSTR(s.documento,4,6) = SUBSTR(a.cpf,4,6)
   AND s.qualificacao IN ('22','49','52','53','65')
),
-- capital social do retrato mais recente em que a empresa aparece
ult AS (
  SELECT cnpj_basico, MAX(ano*100+mes) AS snap
  FROM read_parquet('~/rodado/br_me_cnpj/empresas/*.parquet')
  WHERE cnpj_basico IN (SELECT cnpj_basico FROM soc) GROUP BY 1
),
cap AS (
  SELECT e.cnpj_basico, ANY_VALUE(e.capital_social) AS capital
  FROM read_parquet('~/rodado/br_me_cnpj/empresas/*.parquet') e
  JOIN ult ON ult.cnpj_basico = e.cnpj_basico AND ult.snap = e.ano*100 + e.mes
  GROUP BY 1
)
SELECT a.nome,
       COUNT(DISTINCT s.cnpj_basico) AS n_empresas,
       COALESCE(SUM(cap.capital), 0) AS capital
FROM alvo a
LEFT JOIN soc s ON s.cpf = a.cpf
LEFT JOIN cap ON cap.cnpj_basico = s.cnpj_basico
GROUP BY 1;
"""


def consulta(sql):
    host = os.environ.get("BEELINK_HOST", "beelink")
    res = subprocess.run(["ssh", host, "~/bin/duckdb -json"],
                         input=sql.encode(), capture_output=True, check=True)
    return json.loads(res.stdout)


rows = consulta(SQL)

for r in rows:
    r["delta"] = r["v22"] - r["v18"]
    r["mult"] = r["delta"] / SUBSIDIO
rows.sort(key=lambda r: -r["delta"])

acima = [r for r in rows if r["delta"] > SUBSIDIO]
print(f"universo: {len(rows)} deputados · acima do teto do subsídio: {len(acima)}")

empresas = {e["nome"]: e for e in
            consulta(SQL_CAPITAL.format(subsidio=int(SUBSIDIO)))}
for r in rows:
    e = empresas.get(r["nome"], {})
    r["n_empresas"] = e.get("n_empresas", 0)
    r["capital"] = e.get("capital", 0.0)
    r["capmult"] = r["capital"] / SUBSIDIO

cobertos = [r for r in acima if r["capital"] >= r["delta"]]
print(f"capital social das próprias empresas já cobre o crescimento: "
      f"{len(cobertos)} dos {len(acima)} · sem cobertura: "
      f"R$ {sum(r['delta'] for r in acima if r not in cobertos)/1e6:.1f} mi")

SURFACE, FIG_BG = "#fcfcfb", "#f7f7f5"
TXT, TXT2, TXT3 = "#111111", "#555555", "#7b7b76"
ACENTO, GRID, REF = "#d1453b", "#e6e6e2", "#b6b6ae"
NEUTRO = "#c8c8c2"
EMPRESA = "#5d7f88"   # trecho do crescimento que o capital das empresas cobre


def brl(v):
    """R$ em milhões com vírgula decimal, como se escreve em português."""
    if abs(v) >= 1e6:
        return f"R$ {v/1e6:.1f}".replace(".", ",") + " mi"
    return f"R$ {v/1e3:.0f} mil"


def primeiro_ultimo(nome):
    """'José Nelto Lagares Das Mercez' -> 'José Nelto Mercez'"""
    p = [w for w in nome.split() if len(w) > 2 or w.isupper()]
    return nome if len(p) <= 2 else f"{p[0]} {p[1]} {p[-1]}"


# ═══════════════════════════════════════════════════════ A · barras, top 20
TOP = 20
dados = rows[:TOP]

fig = plt.figure(figsize=(12.4, 12.9), dpi=200, facecolor=FIG_BG)
ax = fig.add_axes((0.315, 0.158, 0.645, 0.542))
ax.set_facecolor(SURFACE)

ys = list(range(TOP - 1, -1, -1))
xmax = max(r["mult"] for r in dados) * 1.26
ax.set_xlim(0, xmax)
ax.set_ylim(-0.75, TOP + 1.15)

ax.grid(axis="x", color=GRID, lw=0.8)
ax.set_axisbelow(True)
for sp in ax.spines.values():
    sp.set_visible(False)
ax.tick_params(colors=TXT3, labelsize=12, length=0)
ax.set_yticks([])
ax.set_xticks([0, 5, 10, 15, 20])
ax.set_xticklabels(["0", "5×", "10×", "15×", "20×"])

# barras com ponta arredondada (4px), ancoradas na linha de base. A barra vem
# partida: o começo, em azul, é o quanto o capital social das empresas do
# próprio deputado já explicaria; o resto, em vermelho, é o que não tem
# contrapartida nenhuma no dado público. Barra inteira azul = a régua generosa
# cobre o crescimento todo.
for y, r in zip(ys, dados):
    h = 0.52
    coberto = min(r["capmult"], r["mult"])
    ax.add_patch(FancyBboxPatch(
        (0, y - h / 2), r["mult"], h,
        boxstyle="round,pad=0,rounding_size=0.055",
        mutation_aspect=xmax / TOP * 0.42,
        facecolor=EMPRESA if coberto >= r["mult"] else ACENTO,
        edgecolor="none", zorder=3))
    if 0 < coberto < r["mult"]:
        ax.add_patch(Rectangle((0, y - h / 2), coberto, h,
                               facecolor=EMPRESA, edgecolor="none", zorder=4))
    ax.text(r["mult"] + xmax * 0.014, y + (0.16 if r["n_empresas"] else 0),
            f'{brl(r["delta"])}', va="center", ha="left", fontsize=11.5,
            color=TXT2, zorder=5)
    if r["n_empresas"]:
        emp = "1 empresa" if r["n_empresas"] == 1 else f'{r["n_empresas"]} empresas'
        ax.text(r["mult"] + xmax * 0.014, y - 0.24,
                f'{emp} · {brl(r["capital"])}', va="center", ha="left",
                fontsize=9.5, color=EMPRESA, zorder=5)
    rot = f'{primeiro_ultimo(r["nome"])}'
    ax.text(-xmax * 0.020, y + 0.19, rot, va="center", ha="right",
            fontsize=12.5, color=TXT, zorder=4)
    ax.text(-xmax * 0.020, y - 0.22, f'{r["uf"]} · {r["partido"]}',
            va="center", ha="right", fontsize=10, color=TXT3, zorder=4)

# a linha de 1× — todo o salário bruto do mandato, sem gastar nada
ax.axvline(1, color=TXT2, lw=1.4, ls=(0, (5, 3.5)), zorder=5)
ax.text(1.22, TOP + 0.42, "1× = todo o subsídio bruto do mandato, sem gastar nada",
        fontsize=11.5, color=TXT2, va="center", ha="left", zorder=6)

ax.set_xlabel("crescimento do patrimônio declarado, em múltiplos do subsídio bruto do mandato",
              fontsize=12.5, color=TXT2, labelpad=12)

fig.text(0.082, 0.968, "Vinte deputados, e o salário não explica nenhum deles",
         ha="left", va="top", fontsize=25, fontweight="bold", color=TXT)
fig.text(0.082, 0.934,
         "Quanto o patrimônio declarado cresceu entre os registros de 2018 e 2022, em salários integrais de deputado",
         ha="left", va="top", fontsize=13, color=TXT2)
fig.text(0.082, 0.900,
         "Entre uma declaração e outra o deputado recebeu R$ 1,76 milhão de subsídio bruto — 42 meses\n"
         "de mandato mais três décimos-terceiros, antes de imposto, previdência e de qualquer despesa.\n"
         "José Nelto declarou um crescimento de R$ 40,6 milhões: vinte e três vezes tudo o que o cargo\n"
         "pagou no período. Dos 472 deputados eleitos em 2018 que voltaram a se registrar em 2022, 39\n"
         "cresceram mais do que o mandato inteiro poderia ter pago. Mas quem é sócio de empresa tem\n"
         "de onde tirar renda além do salário — e a segunda cor desconta isso da conta.",
         ha="left", va="top", fontsize=13.5, color=TXT, linespacing=1.6)

# legenda das duas cores: identidade nunca só pelo matiz, sempre com o rótulo
for x, cor, rot in ((0.082, EMPRESA, "cabe no capital social das empresas do próprio deputado"),
                    (0.560, ACENTO, "não cabe: nem as empresas dele explicam")):
    fig.patches.append(Rectangle((x, 0.722), 0.017, 0.021,
                                 transform=fig.transFigure, facecolor=cor,
                                 edgecolor="none", zorder=4))
    fig.text(x + 0.026, 0.7325, rot, fontsize=11, color=TXT2,
             va="center", ha="left")

fig.text(0.082, 0.096,
         "Fonte: Tribunal Superior Eleitoral — declarações de bens nos registros de candidatura de 2018 e 2022. Subsídio: Câmara dos Deputados.\n"
         "Capital social: Receita Federal, Cadastro Nacional da Pessoa Jurídica — entra integral, sem descontar a parte dos demais sócios, e conta\n"
         "toda empresa em que o deputado é sócio ou titular: é o teto do negócio que ele tem, não a renda que tirou dele.\n"
         "A declaração do TSE segue a regra do imposto de renda e registra bens pelo custo de aquisição, não pelo valor de mercado: o crescimento\n"
         "é compra nova, não valorização. O múltiplo mede o que o salário deixa de explicar; a segunda cor, o que nem a empresa própria explica.",
         ha="left", va="top", fontsize=9.5, color=TXT3, linespacing=1.6)

out_a = "pages/analises/img/patrimonio-multiplos-subsidio.png"
fig.savefig(out_a, facecolor=fig.get_facecolor())
print("ok:", out_a)

# ═════════════════════════════════════════════ B · distribuição dos 472
fig2 = plt.figure(figsize=(12.4, 9.6), dpi=200, facecolor=FIG_BG)
ax2 = fig2.add_axes((0.088, 0.205, 0.888, 0.455))
ax2.set_facecolor(SURFACE)

LO, HI, PASSO = -3.0, 6.0, 0.5
bins = [LO + i * PASSO for i in range(int((HI - LO) / PASSO) + 1)]
contagem = [0] * (len(bins) - 1)
abaixo = acima_hi = 0
for r in rows:
    m = r["mult"]
    if m < LO:
        abaixo += 1
    elif m >= HI:
        acima_hi += 1
    else:
        contagem[min(int((m - LO) / PASSO), len(contagem) - 1)] += 1

ymax = max(max(contagem), abaixo, acima_hi) * 1.22
ax2.set_xlim(LO - PASSO * 2.2, HI + PASSO * 2.2)
ax2.set_ylim(0, ymax)
ax2.grid(axis="y", color=GRID, lw=0.8)
ax2.set_axisbelow(True)
for sp in ax2.spines.values():
    sp.set_visible(False)
ax2.tick_params(colors=TXT3, labelsize=12, length=0)
ax2.set_xticks([-3, -2, -1, 0, 1, 2, 3, 4, 5, 6])
ax2.set_xticklabels(["−3×", "−2×", "−1×", "0", "1×", "2×", "3×", "4×", "5×", "6×"])

# faixa sombreada: acima de 1× o mandato não paga o crescimento
ax2.axvspan(1, HI + PASSO * 2.2, color="#f7ebe7", zorder=0)

for i, n in enumerate(contagem):
    if not n:
        continue
    x0 = bins[i]
    cor = ACENTO if x0 >= 1 else NEUTRO
    ax2.add_patch(FancyBboxPatch(
        (x0 + PASSO * 0.07, 0), PASSO * 0.86, n,
        boxstyle="round,pad=0,rounding_size=0.09",
        mutation_aspect=(HI - LO + PASSO * 4.4) / ymax * 0.30,
        facecolor=cor, edgecolor="none", zorder=3))

# caixas de transbordo, destacadas do eixo contínuo
for x0, n, cor, rot in ((LO - PASSO * 1.9, abaixo, NEUTRO, "abaixo\nde −3×"),
                        (HI + PASSO * 0.55, acima_hi, ACENTO, "acima\nde 6×")):
    if not n:
        continue
    ax2.add_patch(FancyBboxPatch(
        (x0, 0), PASSO * 0.86, n,
        boxstyle="round,pad=0,rounding_size=0.09",
        mutation_aspect=(HI - LO + PASSO * 4.4) / ymax * 0.30,
        facecolor=cor, edgecolor="none", zorder=3))
    ax2.text(x0 + PASSO * 0.43, n + ymax * 0.028, str(n), ha="center",
             va="bottom", fontsize=12, color=TXT, fontweight="bold", zorder=4)
    ax2.text(x0 + PASSO * 0.43, -ymax * 0.055, rot, ha="center", va="top",
             fontsize=10, color=TXT3, linespacing=1.35, zorder=4)

ax2.axvline(1, color=TXT2, lw=1.4, ls=(0, (5, 3.5)), zorder=5)
ax2.text(1.12, ymax * 0.93,
         f"{len(acima)} deputados cresceram mais\ndo que todo o subsídio do mandato",
         fontsize=12, color=TXT, va="top", ha="left", linespacing=1.45, zorder=6)
ax2.text(0.88, ymax * 0.93, "os outros 433", fontsize=12, color=TXT2,
         va="top", ha="right", zorder=6)

ax2.set_ylabel("número de deputados", fontsize=12.5, color=TXT2, labelpad=10)
fig2.text(0.532, 0.132,
          "crescimento do patrimônio declarado entre 2018 e 2022,\nem múltiplos do subsídio bruto do mandato",
          ha="center", va="top", fontsize=12.5, color=TXT2, linespacing=1.5)

fig2.text(0.088, 0.962, "A regra é o patrimônio parado",
          ha="left", va="top", fontsize=25, fontweight="bold", color=TXT)
fig2.text(0.088, 0.925,
          "Distribuição dos 472 deputados eleitos em 2018 que voltaram a se registrar em 2022",
          ha="left", va="top", fontsize=13, color=TXT2)
fig2.text(0.088, 0.888,
          "A maior parte da Câmara se comporta como se espera de quem vive do salário: o crescimento\n"
          "declarado se acumula em torno do zero, e 150 deputados declararam em 2022 menos do que\n"
          "tinham em 2018. À direita da linha tracejada estão os 39 cujo crescimento supera todo o\n"
          "subsídio bruto do mandato — 8% do grupo.",
          ha="left", va="top", fontsize=13.5, color=TXT, linespacing=1.6)

fig2.text(0.088, 0.055,
          "Fonte: Tribunal Superior Eleitoral — declarações de bens nos registros de candidatura de 2018 e 2022. Subsídio: Câmara dos Deputados.\n"
          "Crescimento negativo pode ser venda de bem, partilha, correção de declaração anterior ou baixa de item — não significa empobrecimento real.",
          ha="left", va="top", fontsize=9.5, color=TXT3, linespacing=1.6)

out_b = "pages/analises/img/patrimonio-distribuicao-472.png"
fig2.savefig(out_b, facecolor=fig2.get_facecolor())
print("ok:", out_b)
