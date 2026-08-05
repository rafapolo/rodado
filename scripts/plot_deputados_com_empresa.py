#!/usr/bin/env python3
"""Quantos dos 513 deputados federais eleitos em 2022 são donos ou sócios de empresa.

Gráfico de unidades: cada quadrado é um deputado da legislatura 57, colorido
pela quantidade de empresas em que consta do quadro societário da Receita
Federal na condição de proprietário — não de mero administrador contratado.

  quem entra   qualificações de titularidade no CNPJ: Sócio (22),
               Sócio-Administrador (49), Sócio com Capital (52), Sócio sem
               Capital (53) e Titular Pessoa Física (65, o caso do empresário
               individual e do MEI).
  quem NÃO     Administrador (5), Presidente (16), Diretor (10) e Conselheiro
  entra        de Administração (8) — cargos de gestão que podem ser exercidos
               por contratado sem nenhuma quota de capital. Ignorar essa
               distinção infla a conta: 65 deputados aparecem como Presidente
               de alguma pessoa jurídica sem que isso signifique propriedade.

Casamento de identidade: nome completo idêntico somado aos seis dígitos
centrais do CPF, que a Receita publica sob máscara (***NNNNNN**). Os seis
dígitos dão 1 em 1 milhão, e combinados com o nome completo tornam a
coincidência improvável — mas o casamento não substitui documento, e por isso
nenhum CPF ou CNPJ é reproduzido aqui.

Consulta (beelink, via SSH — BEELINK_HOST, default 'beelink'):
  br_tse_eleicoes/resultados_candidato_municipio   eleitos de 2022
  br_tse_eleicoes/candidatos                       CPF, nome, UF, partido
  br_me_cnpj/socios                                quadro societário

Controle: 513 eleitos, 253 com ao menos uma empresa (49,3%), 933 empresas.
"""
import json
import os
import subprocess

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

SQL = """SET enable_progress_bar=false;
WITH eleitos AS (
  SELECT DISTINCT sequencial_candidato AS seq
  FROM read_parquet('~/rodado/br_tse_eleicoes/resultados_candidato_municipio/*.parquet')
  WHERE ano=2022 AND cargo='deputado federal'
    AND resultado IN ('eleito por media','eleito por qp')
),
dep AS (
  SELECT DISTINCT c.cpf, c.nome, c.sigla_uf, c.sigla_partido
  FROM eleitos e
  JOIN read_parquet('~/rodado/br_tse_eleicoes/candidatos/*.parquet') c
    ON c.sequencial = e.seq AND c.ano = 2022
)
SELECT d.nome, d.sigla_uf AS uf, d.sigla_partido AS partido,
       COUNT(DISTINCT s.cnpj_basico) AS n_empresas
FROM dep d
LEFT JOIN read_parquet('~/rodado/br_me_cnpj/socios/*.parquet') s
  ON UPPER(TRIM(s.nome)) = UPPER(TRIM(d.nome))
 AND SUBSTR(s.documento,4,6) = SUBSTR(d.cpf,4,6)
 AND s.qualificacao IN ('22','49','52','53','65')
GROUP BY 1,2,3;
"""

host = os.environ.get("BEELINK_HOST", "beelink")
res = subprocess.run(["ssh", host, "~/bin/duckdb -json"],
                     input=SQL.encode(), capture_output=True, check=True)
rows = json.loads(res.stdout)

total = len(rows)
com = [r for r in rows if r["n_empresas"] >= 1]
n_empresas_total = sum(r["n_empresas"] for r in rows)
print(f"{total} deputados · {len(com)} com empresa "
      f"({100*len(com)/total:.1f}%) · {n_empresas_total} empresas")

SURFACE, FIG_BG = "#fcfcfb", "#f7f7f5"
TXT, TXT2, TXT3 = "#111111", "#555555", "#7b7b76"

# rampa sequencial de uma hue, separada por luminosidade — legível em qualquer
# tipo de daltonismo, porque a informação está no claro/escuro, não no matiz.
FAIXAS = [
    ("5 ou mais empresas", lambda n: n >= 5,            "#a32b1c"),
    ("2 a 4 empresas",     lambda n: 2 <= n <= 4,       "#d9705c"),
    ("1 empresa",          lambda n: n == 1,            "#eda092"),
    ("nenhuma",            lambda n: n == 0,            "#dcdcd8"),
]

celulas, legenda = [], []
for rot, teste, cor in FAIXAS:
    q = [r for r in rows if teste(r["n_empresas"])]
    celulas += [cor] * len(q)
    legenda.append((rot, cor, len(q)))

COLS = 38
LINHAS = -(-total // COLS)

fig = plt.figure(figsize=(12.4, 9.7), dpi=200, facecolor=FIG_BG)
ax = fig.add_axes((0.082, 0.225, 0.836, 0.394))
ax.set_facecolor(FIG_BG)
ax.set_xlim(-0.5, COLS - 0.5)
ax.set_ylim(LINHAS - 0.5, -0.5)
ax.set_aspect("equal")
ax.axis("off")

for i, cor in enumerate(celulas):
    lin, col = divmod(i, COLS)
    ax.add_patch(FancyBboxPatch(
        (col - 0.40, lin - 0.40), 0.80, 0.80,
        boxstyle="round,pad=0,rounding_size=0.16",
        facecolor=cor, edgecolor=SURFACE, linewidth=1.4, zorder=3))

# a fronteira entre quem tem e quem não tem empresa
corte = len(com)
lin_c, col_c = divmod(corte, COLS)
ax.plot([col_c - 0.5, COLS - 0.5], [lin_c - 0.5, lin_c - 0.5],
        color=TXT, lw=2.0, zorder=5, solid_capstyle="butt")
ax.plot([-0.5, col_c - 0.5], [lin_c + 0.5, lin_c + 0.5],
        color=TXT, lw=2.0, zorder=5, solid_capstyle="butt")
ax.plot([col_c - 0.5, col_c - 0.5], [lin_c - 0.5, lin_c + 0.5],
        color=TXT, lw=2.0, zorder=5, solid_capstyle="butt")

pct = f"{100*len(com)/total:.1f}".replace(".", ",")
ax.annotate(f"{len(com)} deputados — {pct}% da Câmara",
            xy=(col_c - 0.5, lin_c + 0.5), xytext=(COLS * 0.44, lin_c + 2.6),
            fontsize=13, color=TXT, fontweight="bold", ha="left", va="center",
            zorder=6,
            bbox=dict(boxstyle="round,pad=0.45", facecolor=FIG_BG,
                      edgecolor="none"),
            arrowprops=dict(arrowstyle="-", color=TXT, lw=1.2,
                            shrinkA=6, shrinkB=4,
                            connectionstyle="angle,angleA=0,angleB=90,rad=0"))

# legenda com o número em cada faixa — identidade nunca só pela cor
x0, y0 = 0.082, 0.152
for i, (rot, cor, n) in enumerate(legenda):
    x = x0 + i * 0.222
    fig.patches.append(Rectangle((x, y0), 0.019, 0.023, transform=fig.transFigure,
                                 facecolor=cor, edgecolor=SURFACE, linewidth=1.2,
                                 zorder=4))
    fig.text(x + 0.028, y0 + 0.0115, f"{rot}", fontsize=11.5, color=TXT2,
             va="center", ha="left")
    fig.text(x + 0.028, y0 - 0.017, f"{n} deputados", fontsize=11.5, color=TXT,
             va="center", ha="left", fontweight="bold")

fig.text(0.082, 0.963, "Metade da Câmara é dona de empresa",
         ha="left", va="top", fontsize=25, fontweight="bold", color=TXT)
fig.text(0.082, 0.928,
         "Cada quadrado é um dos 513 deputados federais eleitos em 2022",
         ha="left", va="top", fontsize=13, color=TXT2)
fig.text(0.082, 0.892,
         "253 deputados constam do quadro societário de alguma empresa como sócio ou titular — 933 empresas\n"
         "ao todo, uma média de 3,7 por deputado que tem alguma. Cinquenta e dois deles são sócios de cinco ou\n"
         "mais. O recordista, um deputado baiano, aparece em 140: uma rede de postos de combustível com uma\n"
         "holding de participações no topo.",
         ha="left", va="top", fontsize=13.5, color=TXT, linespacing=1.6)

fig.text(0.082, 0.100,
         "Fonte: Receita Federal, Cadastro Nacional da Pessoa Jurídica (quadro societário); Tribunal Superior Eleitoral, eleitos de 2022.\n"
         "Conta apenas qualificações de propriedade — sócio, sócio-administrador, sócio com e sem capital, titular pessoa física. Cargos de gestão sem\n"
         "quota de capital (administrador, presidente, diretor, conselheiro) ficam de fora: 65 deputados presidem alguma pessoa jurídica sem serem donos.\n"
         "O vínculo é estabelecido por nome completo mais os seis dígitos centrais do CPF, que a Receita publica sob máscara — robusto, mas não é documento.",
         ha="left", va="top", fontsize=9.5, color=TXT3, linespacing=1.6)

out = "pages/analises/img/deputados-com-empresa.png"
fig.savefig(out, facecolor=fig.get_facecolor())
print("ok:", out)
