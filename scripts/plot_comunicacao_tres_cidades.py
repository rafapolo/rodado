#!/usr/bin/env python3
"""O setor de comunicação em Fortaleza, Brasília e São Paulo — dois gráficos.

Universo: 24 subclasses CNAE 2.0 de trabalho em comunicação (jornalismo,
publicidade, audiovisual, design, fotografia, conteúdo digital), contadas como
estabelecimentos com situação cadastral ATIVA no CNPJ de setembro de 2025.

  o que entra   o ofício: agência, produtora, pós-produção, dublagem, mixagem,
                jornal, revista, agência de notícia, design gráfico e
                web design, fotografia e filmagem de evento.
  o que NÃO     a cadeia em volta dele — promoção de vendas (751.942 empresas,
  entra         é representante comercial autônomo, não comunicação),
                desenvolvimento de software sob encomenda, pesquisa de mercado,
                agenciamento de espaços publicitários, criação de estandes,
                design de interiores e "portais e provedores de conteúdo"
                (6319-4/00), que abriga holding e fintech, não redação.

Gráfico 1 — especialização (quociente locacional). Para cada CNAE, a fatia que
ele ocupa no setor da cidade dividida pela fatia que ocupa no setor no país.
1,00 = a cidade tem a composição média; 3,00 = tem o triplo da concentração
esperada para o seu tamanho. É a medida que sobrevive à diferença de porte —
São Paulo tem 14x Fortaleza, e comparar valor absoluto só repetiria isso.

Gráfico 2 — composição por família, em % do setor de cada cidade, com o Brasil
como régua.

Cor: três matizes categóricas (azul/laranja/violeta) validadas em todos os seis
checks de CVD contra a superfície #fcfcfb — pior par ΔE 13,0 (deutan), contraste
≥3:1. A identidade nunca depende só da cor: cada ponto do gráfico 1 tem o rótulo
da cidade na primeira linha, e o gráfico 2 rotula cada faixa por extenso.

Consulta (beelink, via SSH — BEELINK_HOST, default 'beelink'):
  br_me_cnpj/estabelecimentos            CNAE principal, situação, município
  br_bd_diretorios_brasil/cnae_2         descrição das subclasses

Controle: 466.106 ativas no país · São Paulo 92.197 · Brasília 12.668 ·
Fortaleza 6.518. Agências de notícia em Brasília: QL 3,16 — o maior do mapa.
"""
import json
import os
import subprocess

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

# ---------------------------------------------------------------- o universo
# (cnae, rótulo curto, família)
CNAES = [
    ("7311400", "Agências de publicidade",        "Publicidade"),
    ("7319003", "Marketing direto",               "Publicidade"),
    ("7319004", "Consultoria em publicidade",     "Publicidade"),
    ("7319099", "Outras ativ. de publicidade",    "Publicidade"),
    ("7410201", "Design",                         "Design"),
    ("7410299", "Design gráfico",                 "Design"),
    ("6201502", "Web design",                     "Design"),
    ("5911101", "Estúdios cinematográficos",      "Audiovisual"),
    ("5911102", "Filmes para publicidade",        "Audiovisual"),
    ("5911199", "Produção de cinema, vídeo e TV",  "Audiovisual"),
    ("5912001", "Dublagem",                       "Audiovisual"),
    ("5912002", "Mixagem sonora",                 "Audiovisual"),
    ("5912099", "Pós-produção audiovisual",       "Audiovisual"),
    ("5913800", "Distribuição de cinema e vídeo", "Audiovisual"),
    ("5920100", "Gravação de som e música",       "Audiovisual"),
    ("5812301", "Jornais diários",                "Jornalismo"),
    ("5812302", "Jornais não diários",            "Jornalismo"),
    ("5813100", "Revistas",                       "Jornalismo"),
    ("6391700", "Agências de notícias",           "Jornalismo"),
    ("7420001", "Produção de fotografias",        "Fotografia"),
    ("7420002", "Fotografia aérea e submarina",   "Fotografia"),
    ("7420003", "Laboratórios fotográficos",      "Fotografia"),
    ("7420004", "Filmagem de festas e eventos",   "Fotografia"),
    ("7420005", "Microfilmagem",                  "Fotografia"),
]

CIDADES = [
    ("3550308", "São Paulo"),
    ("2304400", "Fortaleza"),
    ("5300108", "Brasília"),
]

lista_sql = ",".join(f"'{c}'" for c, _, _ in CNAES)
SQL = f"""SET enable_progress_bar=false;
SELECT cnae_fiscal_principal AS cnae,
       id_municipio,
       COUNT(*) AS n
FROM read_parquet('~/rodado/br_me_cnpj/estabelecimentos/*.parquet')
WHERE ano = 2025 AND mes = 9
  AND situacao_cadastral = '2'
  AND cnae_fiscal_principal IN ({lista_sql})
GROUP BY 1, 2;
"""

host = os.environ.get("BEELINK_HOST", "beelink")
res = subprocess.run(["ssh", host, "~/bin/duckdb -readonly -json ~/rodado/basedosdados.duckdb"],
                     input=SQL.encode(), capture_output=True, check=True)
rows = json.loads(res.stdout)

# cnae -> total nacional, e cnae -> {municipio: n}
nac = {c: 0 for c, _, _ in CNAES}
mun = {c: {m: 0 for m, _ in CIDADES} for c, _, _ in CNAES}
for r in rows:
    c = r["cnae"]
    if c not in nac:
        continue
    nac[c] += r["n"]
    if r["id_municipio"] in mun[c]:
        mun[c][r["id_municipio"]] = r["n"]

TOT_NAC = sum(nac.values())
TOT_MUN = {m: sum(mun[c][m] for c, _, _ in CNAES) for m, _ in CIDADES}
print(f"Brasil {TOT_NAC} · " + " · ".join(f"{n} {TOT_MUN[m]}" for m, n in CIDADES))

# ------------------------------------------------------------------- paleta
SURFACE, FIG_BG = "#fcfcfb", "#f7f7f5"
TXT, TXT2, TXT3 = "#111111", "#555555", "#7b7b76"
GRID = "#e2e2dd"
# três matizes categóricas — validadas por scripts/validate_palette.js da skill
# dataviz: pior par ΔE 13,0 (deutan) / 16,3 (visão normal), contraste ≥3:1
COR = {"São Paulo": "#2a78d6", "Fortaleza": "#eb6834", "Brasília": "#4a3aa7"}

FAMILIAS = ["Publicidade", "Audiovisual", "Jornalismo", "Fotografia", "Design"]


def ql(cnae, muni):
    """Quociente locacional: fatia na cidade ÷ fatia no país."""
    if nac[cnae] == 0 or TOT_MUN[muni] == 0:
        return None
    return (mun[cnae][muni] / TOT_MUN[muni]) / (nac[cnae] / TOT_NAC)


# =========================================================== GRÁFICO 1 — QL
# uma linha por CNAE, agrupada por família, três pontos por linha.
linhas = []          # (tipo, conteudo)
PISO = 500          # base pequena demais dá quociente instável (ver rodapé)
for fam in FAMILIAS:
    doFam = [(c, rot) for c, rot, f in CNAES if f == fam and nac[c] >= PISO]
    doFam.sort(key=lambda t: -nac[t[0]])
    linhas.append(("fam", fam))
    for c, rot in doFam:
        linhas.append(("cnae", (c, rot)))

n_lin = len(linhas)
fig = plt.figure(figsize=(12.6, 14.6), dpi=200, facecolor=FIG_BG)
AX_L, AX_W = 0.375, 0.585
ax = fig.add_axes((AX_L, 0.107, AX_W, 0.700))
ax.set_facecolor(FIG_BG)

XMAX = 3.35
ax.set_xlim(0, XMAX)
ax.set_ylim(n_lin - 0.4, -2.1)
ax.axis("off")

# régua vertical: 1,00 é a linha da média nacional
for v in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0):
    forte = v == 1.0
    ax.axvline(v, color=TXT if forte else GRID, lw=1.6 if forte else 1.0,
               ymin=0, ymax=0.94, zorder=1)
    ax.text(v, -1.42, f"{v:.1f}".replace(".", ","), ha="center", va="center",
            fontsize=10.5, color=TXT if forte else TXT3,
            fontweight="bold" if forte else "normal")
ax.text(1.0, -1.92, "média nacional", ha="center", va="center", fontsize=10,
        color=TXT, style="italic")

# a linha onde as três cidades estão mais separadas ganha o rótulo direto
alvo = max((i for i, (t, _) in enumerate(linhas) if t == "cnae"),
           key=lambda i: (lambda vs: max(vs) - min(vs))(
               [ql(linhas[i][1][0], m) for m, _ in CIDADES]))

for i, (tipo, conteudo) in enumerate(linhas):
    if tipo == "fam":
        ax.text(-0.550, i, conteudo.upper(), transform=ax.get_yaxis_transform(),
                ha="left", va="center", fontsize=11.5, color=TXT,
                fontweight="bold", clip_on=False)
        continue
    c, rot = conteudo
    ax.text(-0.525, i, rot, transform=ax.get_yaxis_transform(),
            ha="left", va="center", fontsize=10.5, color=TXT2, clip_on=False)
    ax.text(-0.022, i, f"{nac[c]:,}".replace(",", "."),
            transform=ax.get_yaxis_transform(), ha="right", va="center",
            fontsize=9.5, color=TXT3, clip_on=False)

    vals = [(nome, ql(c, m)) for m, nome in CIDADES]
    vals = [(n, v) for n, v in vals if v is not None]
    if len(vals) > 1:                       # haste ligando o menor ao maior
        lo, hi = min(v for _, v in vals), max(v for _, v in vals)
        ax.plot([lo, hi], [i, i], color=GRID, lw=2.6, zorder=2,
                solid_capstyle="round")
    for nome, v in vals:
        vx = min(v, XMAX - 0.02)
        ax.plot(vx, i, "o", ms=9.5, color=COR[nome], zorder=4,
                markeredgecolor=SURFACE, markeredgewidth=1.6)
        if i == alvo:                       # identidade sem depender da cor
            ax.annotate(nome, xy=(vx, i), xytext=(vx, i - 0.95),
                        ha="center", va="bottom", fontsize=10,
                        color=COR[nome], fontweight="bold", zorder=6,
                        arrowprops=dict(arrowstyle="-", color=COR[nome],
                                        lw=1.0, shrinkA=1, shrinkB=5))

# faixa cinza por trás das linhas de família, pra separar os blocos
for i, (tipo, _) in enumerate(linhas):
    if tipo == "fam":
        ax.add_patch(Rectangle((0, i - 0.5), XMAX, 1.0, facecolor="#eeeee9",
                               edgecolor="none", zorder=0))

fig.legend(handles=[Line2D([], [], marker="o", ls="", ms=9.5, color=COR[n],
                           markeredgecolor=SURFACE, markeredgewidth=1.6, label=n)
                    for _, n in CIDADES],
           loc="lower left", bbox_to_anchor=(AX_L, 0.818), ncol=3,
           frameon=False, fontsize=12, handletextpad=0.4, columnspacing=2.0)

fig.text(0.053, 0.982, "Cada cidade faz um tipo de comunicação",
         ha="left", va="top", fontsize=26, fontweight="bold", color=TXT)
fig.text(0.053, 0.955,
         "Concentração de cada atividade na cidade, em relação à média do país",
         ha="left", va="top", fontsize=13.5, color=TXT2)
fig.text(0.053, 0.930,
         "Um valor de 1,0 significa que a atividade ocupa na cidade a mesma fatia do setor que ocupa no Brasil. Brasília tem 3,2 em\n"
         "agências de notícias — mais que o triplo do esperado para o seu tamanho — e passa da média em jornal diário e jornal não diário.\n"
         "São Paulo se destaca nas etapas técnicas do audiovisual: mixagem sonora 2,4, dublagem 1,8, estúdios 1,7. Fortaleza puxa para o\n"
         "que é presencial — gravação de som e música 1,7, filmagem de festas e eventos 1,3 — e quase não registra dublagem: 0,1.",
         ha="left", va="top", fontsize=12.5, color=TXT, linespacing=1.62)
fig.text(0.053, 0.820, "número = empresas ativas no Brasil",
         ha="left", va="bottom", fontsize=10, color=TXT3)

fig.text(0.053, 0.012,
         "Fonte: Receita Federal, Cadastro Nacional da Pessoa Jurídica — estabelecimentos ativos em setembro de 2025, por atividade econômica principal (CNAE 2.0).\n"
         "Universo de 24 subclasses de comunicação: 466.106 empresas no país, 92.197 em São Paulo, 12.668 em Brasília e 6.518 em Fortaleza. Ficam de fora promoção de\n"
         "vendas (751.942 ativas, que é representante comercial autônomo), software sob encomenda, pesquisa de mercado, agenciamento de espaço publicitário, design de\n"
         "interiores e \"portais e provedores de conteúdo\" (28.902), guarda-chuva fiscal que abriga holding e fintech, não redação. Duas subclasses do universo não cabem no gráfico: microfilmagem, com 138 empresas — base pequena demais para um índice estável — e a 7410-2/01\n"
         "(\"Design\"), que tem zero empresas ativas no país inteiro, porque quem faz design se registra em \"outras atividades de design\".",
         ha="left", va="bottom", fontsize=9.3, color=TXT3, linespacing=1.62)

out1 = "pages/analises/img/comunicacao-especializacao.png"
fig.savefig(out1, facecolor=fig.get_facecolor())
print("ok:", out1)
plt.close(fig)

# ================================================= GRÁFICO 2 — composição
fam_tot = {}
for m, nome in CIDADES:
    fam_tot[nome] = {f: sum(mun[c][m] for c, _, ff in CNAES if ff == f)
                     for f in FAMILIAS}
fam_tot["Brasil"] = {f: sum(nac[c] for c, _, ff in CNAES if ff == f)
                     for f in FAMILIAS}
tot_de = dict(TOT_MUN)
totais = {nome: TOT_MUN[m] for m, nome in CIDADES}
totais["Brasil"] = TOT_NAC

ORDEM = ["São Paulo", "Fortaleza", "Brasília", "Brasil"]
# rampa de uma hue por luminosidade — a informação está no claro/escuro, então
# sobrevive a qualquer daltonismo; cada faixa ainda é rotulada por extenso.
RAMPA = ["#7c2d1d", "#a8462c", "#c46b4c", "#d9927a", "#eab9a8"]

fig2 = plt.figure(figsize=(12.6, 7.5), dpi=200, facecolor=FIG_BG)
ax2 = fig2.add_axes((0.150, 0.150, 0.812, 0.492))
ax2.set_facecolor(FIG_BG)
ax2.set_xlim(0, 100)
ax2.set_ylim(len(ORDEM) - 0.45, -0.55)
ax2.axis("off")

for j, nome in enumerate(ORDEM):
    x = 0.0
    for k, f in enumerate(FAMILIAS):
        pct = 100 * fam_tot[nome][f] / totais[nome]
        ax2.add_patch(Rectangle((x + 0.16, j - 0.29), max(pct - 0.32, 0.1), 0.58,
                                facecolor=RAMPA[k], edgecolor="none", zorder=3))
        if pct >= 4.4:
            ax2.text(x + pct / 2, j, f"{pct:.1f}".replace(".", ",") + "%",
                     ha="center", va="center", fontsize=11,
                     color="#ffffff" if k <= 2 else TXT, fontweight="bold",
                     zorder=5)
        x += pct
    ax2.text(-0.012, j, nome, transform=ax2.get_yaxis_transform(), ha="right",
             va="center", fontsize=13.5, color=TXT,
             fontweight="bold" if nome != "Brasil" else "normal", clip_on=False)
    ax2.text(-0.012, j + 0.33, f"{totais[nome]:,}".replace(",", ".") + " empresas",
             transform=ax2.get_yaxis_transform(), ha="right", va="center",
             fontsize=9.5, color=TXT3, clip_on=False)

# legenda: nome por extenso, nunca só a cor
x0, y0 = 0.150, 0.688
for k, f in enumerate(FAMILIAS):
    x = x0 + k * 0.150
    y = y0
    fig2.patches.append(Rectangle((x, y), 0.018, 0.022, transform=fig2.transFigure,
                                  facecolor=RAMPA[k], edgecolor="none", zorder=4))
    fig2.text(x + 0.026, y + 0.011, f, fontsize=10.8, color=TXT2,
              va="center", ha="left")

fig2.text(0.062, 0.968, "O mesmo setor, três misturas",
          ha="left", va="top", fontsize=26, fontweight="bold", color=TXT)
fig2.text(0.062, 0.918,
          "Composição do setor de comunicação em cada cidade, em % das empresas ativas",
          ha="left", va="top", fontsize=13.5, color=TXT2)
fig2.text(0.062, 0.868,
          "No grosso as três se parecem: audiovisual e publicidade dominam em toda parte. A diferença está nas bordas — Fortaleza pende\n"
          "para fotografia e evento, Brasília para jornalismo, São Paulo para publicidade e para a especialização técnica.",
          ha="left", va="top", fontsize=12.5, color=TXT, linespacing=1.62)

fig2.text(0.062, 0.022,
          "Fonte: Receita Federal, Cadastro Nacional da Pessoa Jurídica — estabelecimentos ativos em setembro de 2025, por atividade econômica principal (CNAE 2.0).\n"
          "As mesmas 24 subclasses do gráfico anterior. O universo conta empresas, não pessoas: um jornalista com carteira assinada aparece como o jornal que o emprega,\n"
          "e o mesmo jornalista aparece como uma linha própria se prestar o serviço por CNPJ — o mapa enxerga bem a parte do setor que trabalha por pessoa jurídica.",
          ha="left", va="bottom", fontsize=9.3, color=TXT3, linespacing=1.62)

out2 = "pages/analises/img/comunicacao-composicao.png"
fig2.savefig(out2, facecolor=fig2.get_facecolor())
print("ok:", out2)
