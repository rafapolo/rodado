#!/usr/bin/env python3
"""Treemap do setor de comunicação por UF — São Paulo, Distrito Federal, Fortaleza.

Um painel por praça, todos do mesmo tamanho: a área de cada bloco é a FATIA
daquela atividade no setor da própria cidade, não o número absoluto. São Paulo
tem 14x Fortaleza, e painéis proporcionais ao total transformariam a comparação
num exercício de enxergar um selo ao lado de um cartaz.

Hierarquia em dois níveis, como o CNAE: primeiro a família (Publicidade,
Audiovisual, Jornalismo, Fotografia, Design) ocupa seu retângulo, depois as
subclasses se dividem dentro dele. Ler de fora para dentro dá a composição;
comparar o mesmo bloco entre painéis dá a diferença entre as praças.

Cor = família, na mesma rampa por luminosidade do gráfico de composição desta
análise (a informação está no claro/escuro, então sobrevive a qualquer
daltonismo). O nome vai escrito no bloco: a cor reforça, não carrega sozinha.

Universo: as 24 subclasses de comunicação, estabelecimentos ATIVOS no CNPJ de
setembro de 2025. "Design" (7410-2/01) não gera bloco — tem zero empresas no
país. Recorte geográfico: município de São Paulo, município de Fortaleza e o
Distrito Federal inteiro (que é um município só, Brasília).

Consulta (beelink, via SSH — BEELINK_HOST, default 'beelink'):
  br_me_cnpj/estabelecimentos    CNAE principal, situação, município, UF

Controle: São Paulo 92.197 · Distrito Federal 12.668 · Fortaleza 6.518.
"""
import json
import os
import subprocess

import matplotlib.pyplot as plt
import squarify
from matplotlib.patches import Rectangle

CNAES = [
    ("7311400", "Agências de\npublicidade",     "Publicidade"),
    ("7319003", "Marketing\ndireto",            "Publicidade"),
    ("7319004", "Consultoria em\npublicidade",  "Publicidade"),
    ("7319099", "Outras ativ. de\npublicidade", "Publicidade"),
    ("5911101", "Estúdios",                     "Audiovisual"),
    ("5911102", "Filmes para\npublicidade",     "Audiovisual"),
    ("5911199", "Produção de cinema,\nvídeo e TV", "Audiovisual"),
    ("5912001", "Dublagem",                     "Audiovisual"),
    ("5912002", "Mixagem\nsonora",              "Audiovisual"),
    ("5912099", "Pós-produção\naudiovisual",    "Audiovisual"),
    ("5913800", "Distribuição",                 "Audiovisual"),
    ("5920100", "Gravação de som\ne música",    "Audiovisual"),
    ("5812301", "Jornais\ndiários",             "Jornalismo"),
    ("5812302", "Jornais não\ndiários",         "Jornalismo"),
    ("5813100", "Revistas",                     "Jornalismo"),
    ("6391700", "Agências de\nnotícias",        "Jornalismo"),
    ("7420001", "Produção de\nfotografias",     "Fotografia"),
    ("7420002", "Fotografia\naérea",            "Fotografia"),
    ("7420003", "Laboratórios\nfotográficos",   "Fotografia"),
    ("7420004", "Filmagem de festas\ne eventos", "Fotografia"),
    ("7420005", "Microfilmagem",                "Fotografia"),
    ("7410299", "Design\ngráfico",              "Design"),
    ("6201502", "Web\ndesign",                  "Design"),
    ("7410201", "Design",                       "Design"),
]
FAMILIAS = ["Publicidade", "Audiovisual", "Jornalismo", "Fotografia", "Design"]

# (rótulo, cláusula SQL de recorte)
PRACAS = [
    ("São Paulo",         "e.id_municipio = '3550308'"),
    ("Distrito Federal",  "e.sigla_uf = 'DF'"),
    ("Fortaleza",         "e.id_municipio = '2304400'"),
]

lista = ",".join(f"'{c}'" for c, _, _ in CNAES)
casos = "\n".join(
    f"  SUM(CASE WHEN {cl} THEN 1 ELSE 0 END) AS p{i},"
    for i, (_, cl) in enumerate(PRACAS))
SQL = f"""SET enable_progress_bar=false;
SELECT e.cnae_fiscal_principal AS cnae,
{casos}
FROM read_parquet('~/rodado/br_me_cnpj/estabelecimentos/*.parquet') e
WHERE e.ano = 2025 AND e.mes = 9
  AND e.situacao_cadastral = '2'
  AND e.cnae_fiscal_principal IN ({lista})
GROUP BY 1;
"""

host = os.environ.get("BEELINK_HOST", "beelink")
res = subprocess.run(["ssh", host, "~/bin/duckdb -readonly -json ~/rodado/basedosdados.duckdb"],
                     input=SQL.encode(), capture_output=True, check=True)
dados = {r["cnae"]: r for r in json.loads(res.stdout)}

n = {}
for i, (praca, _) in enumerate(PRACAS):
    # SUM() volta do DuckDB como string no JSON (BIGINT), então converte
    n[praca] = {c: int(dados.get(c, {}).get(f"p{i}", 0) or 0) for c, _, _ in CNAES}
TOT = {p: sum(n[p].values()) for p, _ in PRACAS}
print(" · ".join(f"{p} {TOT[p]}" for p, _ in PRACAS))

# ------------------------------------------------------------------- paleta
SURFACE, FIG_BG = "#fcfcfb", "#f7f7f5"
TXT, TXT2, TXT3 = "#111111", "#555555", "#7b7b76"
# mesma rampa de família do gráfico de composição desta análise
RAMPA = dict(zip(FAMILIAS,
                 ["#7c2d1d", "#a8462c", "#c46b4c", "#d9927a", "#eab9a8"]))
CLARO = {"Publicidade", "Audiovisual", "Jornalismo"}   # onde o texto vai branco


def blocos(valores, x, y, dx, dy):
    """Retângulos squarificados para `valores` dentro do quadro dado."""
    v = squarify.normalize_sizes(valores, dx, dy)
    return squarify.squarify(v, x, y, dx, dy)


fig = plt.figure(figsize=(16.4, 9.3), dpi=200, facecolor=FIG_BG)  # = FIG_W, FIG_H
LARG, ALT = 0.284, 0.650
Y0 = 0.118
FIG_W, FIG_H = 16.4, 9.3
# quantos pontos tipográficos vale 1 unidade do eixo (que vai de 0 a 100)
PT_X = LARG * FIG_W * 72 / 100
PT_Y = ALT * FIG_H * 72 / 100
for k, (praca, _) in enumerate(PRACAS):
    x0 = 0.045 + k * (LARG + 0.034)
    ax = fig.add_axes((x0, Y0, LARG, ALT))
    ax.set_xlim(0, 100); ax.set_ylim(0, 100)
    ax.invert_yaxis(); ax.axis("off")
    ax.set_facecolor(FIG_BG)

    # nível 1: as famílias
    fam_val = [sum(n[praca][c] for c, _, f in CNAES if f == fam) for fam in FAMILIAS]
    ordem = sorted(range(len(FAMILIAS)), key=lambda i: -fam_val[i])
    fams = [FAMILIAS[i] for i in ordem if fam_val[i] > 0]
    vals = [fam_val[i] for i in ordem if fam_val[i] > 0]

    for fam, quadro in zip(fams, blocos(vals, 0, 0, 100, 100)):
        # nível 2: as subclasses dentro da família
        itens = [(rot, n[praca][c]) for c, rot, f in CNAES if f == fam and n[praca][c] > 0]
        itens.sort(key=lambda t: -t[1])
        sub = blocos([v for _, v in itens],
                     quadro["x"], quadro["y"], quadro["dx"], quadro["dy"])

        for (rot, v), r in zip(itens, sub):
            ax.add_patch(Rectangle((r["x"], r["y"]), r["dx"], r["dy"],
                                   facecolor=RAMPA[fam], edgecolor=FIG_BG,
                                   linewidth=1.8, zorder=3))
            pct = 100 * v / TOT[praca]
            dx, dy = r["dx"], r["dy"]

            def cabe(txt, fs):
                """O bloco comporta este texto neste corpo?

                Limiar fixo em unidades do eixo não serve: a largura necessária
                depende do texto. Converte pt -> unidade do painel (o eixo vai
                de 0 a 100 sobre LARG/ALT da figura) e mede a maior linha.
                """
                linhas = txt.split("\n")
                larg_pt = max(len(l) for l in linhas) * fs * 0.55
                alt_pt = len(linhas) * fs * 1.28
                return (larg_pt / PT_X + 1.6 <= dx) and (alt_pt / PT_Y + 1.4 <= dy)

            cor = "#ffffff" if fam in CLARO else TXT
            comp = f"{rot}\n{pct:.1f}%".replace(".", ",")
            curto = rot.replace("\n", " ")
            for txt, fs in ((comp, 9.5), (comp, 8.4), (curto, 8.0), (curto, 7.2)):
                if cabe(txt, fs):
                    ax.text(r["x"] + dx / 2, r["y"] + dy / 2, txt,
                            ha="center", va="center", fontsize=fs, color=cor,
                            linespacing=1.28, zorder=5)
                    break

        # contorno da família por cima, para o agrupamento ficar legível
        ax.add_patch(Rectangle((quadro["x"], quadro["y"]), quadro["dx"], quadro["dy"],
                               facecolor="none", edgecolor=FIG_BG,
                               linewidth=4.2, zorder=6))

    fig.text(x0, Y0 + ALT + 0.052, praca, ha="left", va="bottom",
             fontsize=17, fontweight="bold", color=TXT)
    fig.text(x0, Y0 + ALT + 0.020,
             f"{TOT[praca]:,}".replace(",", ".") + " empresas ativas",
             ha="left", va="bottom", fontsize=11.5, color=TXT3)

# legenda das famílias — nome por extenso, nunca só a cor
for k, fam in enumerate(FAMILIAS):
    x = 0.045 + k * 0.116
    fig.patches.append(Rectangle((x, 0.878), 0.0135, 0.020,
                                 transform=fig.transFigure, facecolor=RAMPA[fam],
                                 edgecolor="none", zorder=4))
    fig.text(x + 0.020, 0.888, fam, fontsize=11.5, color=TXT2,
             va="center", ha="left")

fig.text(0.045, 0.978, "O setor de comunicação, praça por praça",
         ha="left", va="top", fontsize=27, fontweight="bold", color=TXT)
fig.text(0.045, 0.938,
         "Cada painel é uma cidade inteira: a área de um bloco é a fatia daquela atividade no setor local, agrupada pela família do CNAE",
         ha="left", va="top", fontsize=13, color=TXT2)

fig.text(0.045, 0.016,
         "Fonte: Receita Federal, Cadastro Nacional da Pessoa Jurídica — estabelecimentos ativos em setembro de 2025, por atividade econômica principal (CNAE 2.0). Universo de 24\n"
         "subclasses de comunicação. Os painéis têm o mesmo tamanho de propósito: mostram composição, não escala — São Paulo tem 14 vezes as empresas de Fortaleza. Blocos pequenos\n"
         "demais para caber o rótulo ficam sem texto. \"Design\" (7410-2/01) não aparece porque tem zero empresas ativas no país; quem faz design se registra em design gráfico.",
         ha="left", va="bottom", fontsize=9.2, color=TXT3, linespacing=1.62)

out = "pages/analises/img/treemap_cnaes_por_uf.png"
fig.savefig(out, facecolor=fig.get_facecolor())
print("ok:", out)
