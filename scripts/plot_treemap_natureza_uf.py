#!/usr/bin/env python3
"""Treemap da natureza jurídica do setor de comunicação, por praça.

Companheiro de plot_treemap_cnaes_uf.py, e de leitura invertida: lá a
hierarquia era família -> subclasse, aqui é NATUREZA JURÍDICA -> família. A cor
é a mesma nos dois (rampa de família por luminosidade), então dá para pular de
um para o outro sem reaprender a legenda.

O que a peça responde: quanto do setor é uma PESSOA e quanto é uma SOCIEDADE.
No CNPJ isso não é heurística — o campo `natureza_juridica` diz. "Empresário
(Individual)" (2135) é uma pessoa física que abriu inscrição para faturar;
"Sociedade Empresária Limitada" (2062) é empresa constituída. As duas somam
98,4% do universo, e a razão social NÃO serve de atalho: só metade dos
empresários individuais usa o formato numerado com CPF, a outra metade
registra um nome de fantasia e passaria por sociedade num teste de texto.

Painéis do mesmo tamanho de propósito: mostram composição, não escala.

Universo: as 24 subclasses de comunicação, estabelecimentos ATIVOS no CNPJ de
setembro de 2025, no município de São Paulo, no de Fortaleza e no Distrito
Federal inteiro.

Consulta (beelink, via SSH — BEELINK_HOST, default 'beelink'):
  br_me_cnpj/estabelecimentos             CNAE, situação, município, UF
  br_me_cnpj/empresas                     natureza jurídica
  br_bd_diretorios_brasil/natureza_juridica   descrição oficial (CONCLA)

Controle: São Paulo 92.197 · Distrito Federal 12.668 · Fortaleza 6.518.
Empresário (Individual) = 57,5% do universo das três praças somadas.
"""
import json
import os
import subprocess

import matplotlib.pyplot as plt
import squarify
from matplotlib.patches import Rectangle

FAMILIA = {
    "7311400": "Publicidade", "7319003": "Publicidade",
    "7319004": "Publicidade", "7319099": "Publicidade",
    "5911101": "Audiovisual", "5911102": "Audiovisual", "5911199": "Audiovisual",
    "5912001": "Audiovisual", "5912002": "Audiovisual", "5912099": "Audiovisual",
    "5913800": "Audiovisual", "5920100": "Audiovisual",
    "5812301": "Jornalismo", "5812302": "Jornalismo",
    "5813100": "Jornalismo", "6391700": "Jornalismo",
    "7420001": "Fotografia", "7420002": "Fotografia", "7420003": "Fotografia",
    "7420004": "Fotografia", "7420005": "Fotografia",
    "7410299": "Design", "6201502": "Design", "7410201": "Design",
}
FAMILIAS = ["Publicidade", "Audiovisual", "Jornalismo", "Fotografia", "Design"]

# natureza jurídica -> grupo exibido. Só 2135 e 2062 têm peso; o resto some
# numa faixa "outras" para não virar um cardume de lascas ilegíveis.
NATUREZAS = [
    ("2135", "Empresário\n(Individual)"),
    ("2062", "Sociedade Empresária\nLimitada"),
]
ROT_OUTRAS = "Outras naturezas"

PRACAS = [
    ("São Paulo",        "e.id_municipio = '3550308'"),
    ("Distrito Federal", "e.sigla_uf = 'DF'"),
    ("Fortaleza",        "e.id_municipio = '2304400'"),
]

lista = ",".join(f"'{c}'" for c in FAMILIA)
casos = "\n".join(f"  SUM(CASE WHEN {cl} THEN 1 ELSE 0 END) AS p{i},"
                  for i, (_, cl) in enumerate(PRACAS))
SQL = f"""SET enable_progress_bar=false;
SELECT e.cnae_fiscal_principal AS cnae,
       em.natureza_juridica    AS nj,
{casos}
FROM read_parquet('~/rodado/br_me_cnpj/estabelecimentos/*.parquet') e
JOIN read_parquet('~/rodado/br_me_cnpj/empresas/*.parquet') em
  ON em.cnpj_basico = e.cnpj_basico AND em.ano = 2025 AND em.mes = 9
WHERE e.ano = 2025 AND e.mes = 9
  AND e.situacao_cadastral = '2'
  AND e.cnae_fiscal_principal IN ({lista})
GROUP BY 1, 2;
"""

host = os.environ.get("BEELINK_HOST", "beelink")
res = subprocess.run(["ssh", host, "~/bin/duckdb -readonly -json ~/rodado/basedosdados.duckdb"],
                     input=SQL.encode(), capture_output=True, check=True)

# praça -> grupo de natureza -> família -> n
n = {p: {} for p, _ in PRACAS}
for r in json.loads(res.stdout):
    fam = FAMILIA.get(r["cnae"])
    if fam is None:
        continue
    grupo = next((rot for cod, rot in NATUREZAS if cod == r["nj"]), ROT_OUTRAS)
    for i, (praca, _) in enumerate(PRACAS):
        v = int(r.get(f"p{i}", 0) or 0)          # SUM() volta como string no JSON
        if v:
            n[praca].setdefault(grupo, {}).setdefault(fam, 0)
            n[praca][grupo][fam] += v

TOT = {p: sum(v for g in n[p].values() for v in g.values()) for p, _ in PRACAS}
ORDEM_NAT = [rot for _, rot in NATUREZAS] + [ROT_OUTRAS]
print(" · ".join(f"{p} {TOT[p]}" for p, _ in PRACAS))
for p, _ in PRACAS:
    ind = sum(n[p].get("Empresário\n(Individual)", {}).values())
    print(f"  {p}: empresário individual {ind} ({100*ind/TOT[p]:.1f}%)")

# ------------------------------------------------------------------- paleta
FIG_BG = "#f7f7f5"
TXT, TXT2, TXT3 = "#111111", "#555555", "#7b7b76"
RAMPA = dict(zip(FAMILIAS, ["#7c2d1d", "#a8462c", "#c46b4c", "#d9927a", "#eab9a8"]))
CLARO = {"Publicidade", "Audiovisual", "Jornalismo"}

FIG_W, FIG_H = 16.4, 9.3
LARG, ALT = 0.284, 0.622
Y0 = 0.150
PT_X = LARG * FIG_W * 72 / 100      # pontos por unidade do eixo (0–100)
PT_Y = ALT * FIG_H * 72 / 100


def blocos(valores, x, y, dx, dy):
    return squarify.squarify(squarify.normalize_sizes(valores, dx, dy), x, y, dx, dy)


fig = plt.figure(figsize=(FIG_W, FIG_H), dpi=200, facecolor=FIG_BG)
for k, (praca, _) in enumerate(PRACAS):
    x0 = 0.045 + k * (LARG + 0.034)
    ax = fig.add_axes((x0, Y0, LARG, ALT))
    ax.set_xlim(0, 100); ax.set_ylim(0, 100)
    ax.invert_yaxis(); ax.axis("off")
    ax.set_facecolor(FIG_BG)

    grupos = [g for g in ORDEM_NAT if n[praca].get(g)]
    vals = [sum(n[praca][g].values()) for g in grupos]

    # nível 1 em FAIXAS horizontais, não squarificado: são só três categorias,
    # os nomes são longos, e blocos lado a lado faziam os rótulos colidirem.
    # Como faixa, a altura é diretamente comparável entre os painéis.
    topo = 0.0
    for g, tot_g in zip(grupos, vals):
        h = 100 * tot_g / TOT[praca]
        itens = sorted(n[praca][g].items(), key=lambda t: -t[1])
        sub = blocos([v for _, v in itens], 0, topo, 100, h)
        for (fam, v), r in zip(itens, sub):
            ax.add_patch(Rectangle((r["x"], r["y"]), r["dx"], r["dy"],
                                   facecolor=RAMPA[fam], edgecolor=FIG_BG,
                                   linewidth=1.6, zorder=3))
            dx, dy = r["dx"], r["dy"]
            pct = 100 * v / TOT[praca]

            def cabe(txt, fs):
                ls = txt.split("\n")
                return (max(len(l) for l in ls) * fs * 0.55 / PT_X + 1.6 <= dx
                        and len(ls) * fs * 1.28 / PT_Y + 1.4 <= dy)

            cor = "#ffffff" if fam in CLARO else TXT
            comp = f"{fam}\n{pct:.1f}%".replace(".", ",")
            for txt, fs in ((comp, 9.4), (comp, 8.3), (fam, 8.0), (fam, 7.2)):
                if cabe(txt, fs):
                    ax.text(r["x"] + dx / 2, r["y"] + dy / 2, txt, ha="center",
                            va="center", fontsize=fs, color=cor,
                            linespacing=1.28, zorder=5)
                    break

        ax.add_patch(Rectangle((0, topo), 100, h, facecolor="none",
                               edgecolor=TXT, linewidth=1.6, zorder=7))
        # a faixa "outras" fica com ~1% da altura: fina demais para texto dentro,
        # e o número dela vai no rodapé em vez de virar um rótulo espremido
        if h * PT_Y / 100 * 100 >= 26:
            ax.text(1.6, topo + 1.4,
                    f"{g.replace(chr(10), ' ')} · {h:.1f}%".replace(".", ","),
                    ha="left", va="top", fontsize=10.2, color=TXT,
                    fontweight="bold", zorder=9,
                    bbox=dict(boxstyle="round,pad=0.32", facecolor=FIG_BG,
                              edgecolor="none"))
        topo += h

    fig.text(x0, Y0 + ALT + 0.052, praca, ha="left", va="bottom",
             fontsize=17, fontweight="bold", color=TXT)
    fig.text(x0, Y0 + ALT + 0.020,
             f"{TOT[praca]:,}".replace(",", ".") + " empresas ativas",
             ha="left", va="bottom", fontsize=11.5, color=TXT3)

for k, fam in enumerate(FAMILIAS):
    x = 0.045 + k * 0.116
    fig.patches.append(Rectangle((x, 0.878), 0.0135, 0.020, transform=fig.transFigure,
                                 facecolor=RAMPA[fam], edgecolor="none", zorder=4))
    fig.text(x + 0.020, 0.888, fam, fontsize=11.5, color=TXT2, va="center", ha="left")

fig.text(0.045, 0.978, "Metade do setor de comunicação é uma pessoa, não uma empresa",
         ha="left", va="top", fontsize=26, fontweight="bold", color=TXT)
fig.text(0.045, 0.938,
         "Natureza jurídica das empresas ativas de comunicação, com a família do CNAE dentro de cada uma — a área é a fatia no setor local",
         ha="left", va="top", fontsize=13, color=TXT2)

outras_txt = " · ".join(
    f"{p} {100*sum(n[p].get(ROT_OUTRAS, {}).values())/TOT[p]:.1f}%".replace(".", ",")
    for p, _ in PRACAS)
fig.text(0.045, 0.020,
         "Fonte: Receita Federal, Cadastro Nacional da Pessoa Jurídica — estabelecimentos ativos em setembro de 2025; natureza jurídica conforme a tabela da Comissão Nacional de Classificação\n"
         "(Concla/IBGE). \"Empresário (Individual)\" é uma pessoa física com inscrição para faturar; \"Sociedade Empresária Limitada\" é empresa constituída — as duas somam 98,4% do universo. O\n"
         f"restante (sociedade simples, S.A., associação, cooperativa e mais treze naturezas) está na faixa \"outras naturezas\", fina demais para caber rótulo: {outras_txt}. Os painéis têm o mesmo\n"
         "tamanho de propósito: mostram composição, não escala — São Paulo tem 14 vezes as empresas de Fortaleza.",
         ha="left", va="bottom", fontsize=9.2, color=TXT3, linespacing=1.62)

out = "pages/analises/img/treemap_natureza_por_uf.png"
fig.savefig(out, facecolor=fig.get_facecolor())
print("ok:", out)
