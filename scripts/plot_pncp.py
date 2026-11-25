#!/usr/bin/env python3
"""O PNCP por dentro: as figuras da análise o-pncp-por-dentro.

Lê os CSVs de docs/pesquisa/queries/pncp/ (gerados por roda.py a partir de consultas.sql) e
escreve PNGs em pages/analises/img/pncp-*.png. Tema escuro (fundo #121211, os mesmos tokens de
plot_gastos_federais.py); esferas em azul, verde-água e laranja (validadas no fundo escuro) e
cinza para "outros".
"""
import json
from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl

plt.rcParams["text.parse_math"] = False

RAIZ = Path(__file__).resolve().parent.parent
Q = RAIZ / "docs" / "pesquisa" / "queries" / "pncp"
OUT = RAIZ / "pages" / "analises" / "img"

FIG = "#121211"
TXT, TXT2, TXT3 = "#f3f3ef", "#b8b8b1", "#8b8b84"
GRID, REF = "#2b2b29", "#5c5c57"
AZUL, LARANJA, AQUA, CINZA, VERMELHO = "#3987e5", "#d95926", "#199e70", "#6b6b66", "#e66767"

FONTE = "Fonte: Portal Nacional de Contratações Públicas (PNCP), API de consulta"
NUM = {}  # números citados no texto, gravados em numeros.json


def br(x, casas=0):
    return f"{x:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def reais(v):
    for lim, suf, d in [(1e12, "tri", 1e12), (1e9, "bi", 1e9), (1e6, "mi", 1e6), (1e3, "mil", 1e3)]:
        if abs(v) >= lim:
            x = v / d
            casas = 1 if x < 10 and abs(x - round(x)) > 0.05 else 0
            return f"R$ {br(x, casas)} {suf}"
    return f"R$ {br(v)}"


def moldura(fig, titulo, subtitulo, fonte):
    fig.text(0.05, 0.965, titulo, ha="left", va="top", fontsize=23, fontweight="bold", color=TXT)
    fig.text(0.05, 0.915, subtitulo, ha="left", va="top", fontsize=13, color=TXT2, linespacing=1.5)
    fig.text(0.05, 0.016, fonte, ha="left", va="bottom", fontsize=9.5, color=TXT3, linespacing=1.6)


def eixo(ax, grade="y"):
    ax.set_facecolor(FIG)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(colors=TXT3, labelsize=10.5, length=0)
    ax.grid(axis=grade, color=GRID, lw=0.8)
    ax.set_axisbelow(True)


def salva(fig, nome):
    d = OUT / f"pncp-{nome}.png"
    fig.savefig(d, facecolor=FIG)
    plt.close(fig)
    print("ok:", d.relative_to(RAIZ))


# ------------------------------------------------------------ 1. editais por mês e esfera
def fig_mes(ate):
    d = pl.read_csv(Q / "editais_mes.csv").filter(pl.col("mes").is_not_null() & (pl.col("mes") < ate))
    d = d.with_columns(pl.col("esfera").replace({"D": "O", "N": "O"}))
    p = d.pivot(on="esfera", index="mes", values="editais", aggregate_function="sum").fill_null(0).sort("mes")
    meses = p["mes"].to_list()
    x = list(range(len(meses)))
    camadas = [("M", "Municípios", LARANJA), ("E", "Estados", AQUA), ("F", "União", AZUL), ("O", "Distrito Federal e outros", CINZA)]
    fig = plt.figure(figsize=(12.4, 7.6), dpi=200, facecolor=FIG)
    ax = fig.add_axes((0.07, 0.12, 0.70, 0.66))
    eixo(ax)
    ys = [p[k].to_list() if k in p.columns else [0] * len(x) for k, _, _ in camadas]
    ax.stackplot(x, *ys, colors=[c for _, _, c in camadas], edgecolor=FIG, lw=0.6)
    tot = [sum(v) for v in zip(*ys)]
    base = 0
    for (k, nome, cor), y in zip(camadas, ys):  # rótulo direto à direita, no meio de cada camada
        ax.text(len(x) - 0.3, base + y[-1] / 2, f"{nome}", color=TXT, fontsize=11.5, va="center")
        base += y[-1]
    i24 = meses.index("2024-01")
    ax.axvline(i24, color=REF, lw=1.1, ls=(0, (4, 3)))
    ax.text(i24 - 0.6, max(tot) * 0.97, "jan/2024: a nova lei de licitações\nvira a única em vigor",
            color=TXT2, fontsize=10.5, ha="right", va="top")
    anos = [i for i, m in enumerate(meses) if m.endswith("-01")]
    ax.set_xticks(anos, [meses[i][:4] for i in anos])
    ax.yaxis.set_major_formatter(lambda v, _: br(v))
    ax.set_xlim(0, len(x) - 1)
    m25 = p.filter(pl.col("mes").str.starts_with("2025"))
    mun = m25["M"].sum() / sum(m25[k].sum() for k, _, _ in camadas if k in m25.columns)
    NUM["editais_mes_pico"] = max(tot)
    NUM["parte_municipal_2025"] = round(100 * mun, 1)
    moldura(fig, "Editais publicados por mês",
            f"Até 2023 o portal convivia com as leis antigas; em 2024 passou de uns 30 mil para mais de 100 mil editais por mês.\n"
            f"Em 2025, {br(100 * mun)}% vieram de prefeituras e câmaras municipais.",
            FONTE + f" · editais (contratações) publicados até {meses[-1][5:]}/{meses[-1][:4]}, pela esfera do órgão que publicou")
    salva(fig, "editais-por-mes")


# ------------------------------------------------------------ 2. municípios com edital por UF
def fig_municipios():
    d = pl.read_csv(Q / "municipios_uf_2025.csv").filter(pl.col("sigla_uf") != "DF").with_columns((100 * pl.col("com_edital") / pl.col("municipios")).alias("pct")).sort("pct")
    br_pct = 100 * d["com_edital"].sum() / d["municipios"].sum()
    NUM["municipios_com_edital_2025"] = int(d["com_edital"].sum())
    NUM["municipios_total"] = int(d["municipios"].sum())
    fig = plt.figure(figsize=(12.4, 10.4), dpi=200, facecolor=FIG)
    ax = fig.add_axes((0.07, 0.08, 0.85, 0.74))
    eixo(ax, "x")
    ys = range(len(d))
    ax.barh(list(ys), d["pct"].to_list(), height=0.68, color=AZUL)
    for y, r in enumerate(d.iter_rows(named=True)):
        ax.text(r["pct"] + 0.6, y, f"{br(r['pct'], 1)}%  ({r['com_edital']} de {r['municipios']})", va="center", fontsize=9.8, color=TXT)
    ax.set_yticks(list(ys), d["sigla_uf"].to_list(), fontsize=10.5, color=TXT)
    ax.axvline(br_pct, color=REF, lw=1.1, ls=(0, (4, 3)))
    ax.text(br_pct, len(d) - 0.2, f"Brasil: {br(br_pct, 1)}%", color=TXT2, fontsize=11, ha="center", va="bottom")
    ax.set_xlim(0, 118)
    ax.set_xticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"])
    pior = d.row(0, named=True)
    moldura(fig, "Quase toda prefeitura já publica no portal",
            f"Municípios com ao menos um edital municipal publicado em 2025: {br(d['com_edital'].sum())} de {br(d['municipios'].sum())}.\n"
            f"O menor alcance é em {pior['sigla_uf']}, com {br(pior['pct'])}%, e em São Paulo, com 84%. O Distrito Federal, sem prefeitura, fica de fora.",
            FONTE + " · editais de órgãos da esfera municipal em 2025, pelo código IBGE da unidade; IBGE · lista de municípios")
    salva(fig, "municipios-por-uf")


# ------------------------------------------------------------ 3. modalidade: quantidade x valor
CURTO = {"Pregão - Eletrônico": "Pregão eletrônico", "Concorrência - Eletrônica": "Concorrência eletrônica",
         "Pregão - Presencial": "Pregão presencial", "Concorrência - Presencial": "Concorrência presencial"}


def fig_modalidade():
    d = pl.read_csv(Q / "modalidade_2025.csv").with_columns(pl.col("homologado").fill_null(0))
    top = ["Dispensa", "Pregão - Eletrônico", "Inexigibilidade", "Concorrência - Eletrônica", "Credenciamento"]
    d = d.with_columns(pl.when(pl.col("modalidade").is_in(top)).then(pl.col("modalidade")).otherwise(pl.lit("Outras")).alias("m"))
    g = d.group_by("m").agg(pl.col("editais", "homologado").sum())
    g = g.with_columns((100 * pl.col("editais") / pl.col("editais").sum()).alias("p_n"),
                       (100 * pl.col("homologado") / pl.col("homologado").sum()).alias("p_v"))
    ordem = top[::-1] + []
    ordem = ["Outras"] + ordem
    g = g.with_columns(pl.col("m").replace_strict({m: i for i, m in enumerate(ordem)}).alias("o")).sort("o")
    for r in g.iter_rows(named=True):
        NUM[f"mod_{r['m']}"] = {"pct_editais": round(r["p_n"], 1), "pct_valor": round(r["p_v"], 1)}
    fig = plt.figure(figsize=(12.4, 7.4), dpi=200, facecolor=FIG)
    for j, (col, tit, cor) in enumerate([("p_n", "parte dos editais", AZUL), ("p_v", "parte do valor homologado", LARANJA)]):
        ax = fig.add_axes((0.25 + j * 0.37, 0.10, 0.31, 0.68))
        eixo(ax, "x")
        ys = range(len(g))
        ax.barh(list(ys), g[col].to_list(), height=0.66, color=cor)
        for y, v in enumerate(g[col]):
            ax.text(v + 1, y, f"{br(v)}%", va="center", fontsize=11, color=TXT)
        ax.set_yticks(list(ys), [CURTO.get(m, m) for m in g["m"]] if j == 0 else [], fontsize=11.5, color=TXT)
        ax.set_xlim(0, 75)
        ax.set_xticks([])
        ax.set_title(tit, color=TXT2, fontsize=12.5, loc="left", pad=8)
    dis = g.filter(pl.col("m") == "Dispensa").row(0, named=True)
    pre = g.filter(pl.col("m") == "Pregão - Eletrônico").row(0, named=True)
    moldura(fig, "Muitas dispensas, pouco dinheiro",
            f"Em 2025, metade dos editais foi dispensa de licitação ({br(dis['p_n'])}%), que ficou com {br(dis['p_v'])}% do valor.\n"
            f"O pregão eletrônico teve {br(pre['p_n'])}% dos editais e {br(pre['p_v'])}% do dinheiro.",
            FONTE + " · editais publicados em 2025\nValor homologado só dos editais abaixo de R$ 1 bi: a fonte aceita qualquer número, e os poucos acima dele dominariam a soma")
    salva(fig, "modalidades")


# ------------------------------------------------------------ 4. valores: quantos x quanto
def fig_valores():
    d = pl.read_csv(Q / "valores_2025.csv").sort("faixa_log10")
    tot_n, tot_s = d["editais"].sum(), d["soma"].sum()
    acima = d.filter(pl.col("faixa_log10") >= 9)
    NUM["estimado_2025_soma"] = tot_s
    NUM["estimado_2025_acima_1bi_n"] = int(acima["editais"].sum())
    NUM["estimado_2025_acima_1bi_pct_soma"] = round(100 * acima["soma"].sum() / tot_s, 2)
    NUM["estimado_2025_abaixo_1bi_soma"] = tot_s - acima["soma"].sum()
    fig = plt.figure(figsize=(12.4, 9.6), dpi=200, facecolor=FIG)
    x = d["faixa_log10"].to_list()
    cores = [VERMELHO if v >= 9 else AZUL for v in x]
    for j, (col, tit, fmt) in enumerate([("editais", "quantos editais em cada faixa de valor", lambda v: br(v)),
                                         ("soma", "quanto essa faixa soma", lambda v: reais(v))]):
        ax = fig.add_axes((0.08, 0.50 - j * 0.40, 0.88, 0.30))
        eixo(ax)
        ax.bar(x, d[col].to_list(), width=0.23, align="edge", color=cores)
        ax.set_title(tit, color=TXT2, fontsize=12.5, loc="left", pad=6)
        ax.yaxis.set_major_formatter(lambda v, _, f=fmt: f(v) if v else "0")
        ticks = list(range(0, 16, 2))
        ax.set_xticks(ticks, [reais(10 ** t).replace("R$ 1 ", "R$ 1 ") if t else "R$ 1" for t in ticks] if j == 1 else [])
        ax.set_xlim(-0.2, max(x) + 0.5)
        ax.axvline(9, color=REF, lw=1.1, ls=(0, (4, 3)))
    fig.text(0.665, 0.78, f"R$ 1 bi ou mais: {br(acima['editais'].sum())} editais\n({br(100 * acima['editais'].sum() / tot_n, 2)}% do total)",
             color=TXT2, fontsize=11)
    fig.text(0.665, 0.38, f"…e {br(100 * acima['soma'].sum() / tot_s, 1)}% de todo o valor", color=TXT2, fontsize=11)
    moldura(fig, f"{reais(tot_s)} em editais, 99% do valor em {br(acima['editais'].sum())} editais",
            f"Somados, os editais de 2025 valem {reais(tot_s)}, mais de 20 vezes o PIB. Um punhado acima de R$ 1 bi faz a soma;\n"
            f"sem eles, sobram {reais(tot_s - acima['soma'].sum())}. O edital típico vale entre R$ 1 mil e R$ 100 mil.",
            FONTE + " · valor total estimado dos editais publicados em 2025\nFaixas de um quarto de ordem de grandeza, em escala logarítmica; em vermelho, R$ 1 bi ou mais")
    salva(fig, "valores")


# ------------------------------------------------------------ 5. contratos assinados antes do edital
def fig_antes():
    d = pl.read_csv(Q / "antes_do_edital_2025.csv")
    top = ["Pregão - Eletrônico", "Dispensa", "Inexigibilidade", "Credenciamento", "Concorrência - Eletrônica"]
    t = d.filter(pl.col("modalidade").is_in(top)).with_columns((100 * pl.col("antes") / pl.col("contratos")).alias("pct")).sort("pct")
    tot = 100 * d["antes"].sum() / d["contratos"].sum()
    direta = d.filter(pl.col("modalidade").is_in(["Dispensa", "Inexigibilidade"]))
    NUM["antes_total_pct"] = round(tot, 1)
    NUM["antes_direta_parte"] = round(100 * direta["antes"].sum() / d["antes"].sum(), 1)
    fig = plt.figure(figsize=(12.4, 7.0), dpi=200, facecolor=FIG)
    ax = fig.add_axes((0.25, 0.12, 0.68, 0.64))
    eixo(ax, "x")
    ys = range(len(t))
    ax.barh(list(ys), t["pct"].to_list(), height=0.64, color=AZUL)
    for y, r in enumerate(t.iter_rows(named=True)):
        ax.text(r["pct"] + 0.8, y, f"{br(r['pct'])}%  ·  {br(r['antes'])} de {br(r['contratos'])} contratos · mediana de {br(r['mediana_dias'])} dias",
                va="center", fontsize=10.5, color=TXT)
    ax.set_yticks(list(ys), [CURTO.get(m, m) for m in t["modalidade"]], fontsize=11.5, color=TXT)
    ax.axvline(tot, color=REF, lw=1.1, ls=(0, (4, 3)))
    ax.text(tot + 0.5, len(t) - 0.45, f"todos: {br(tot, 1)}%", color=TXT2, fontsize=11)
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50], ["0%", "25%", "50%"])
    moldura(fig, "Contrato assinado antes do edital aparecer",
            f"{br(tot, 1)}% dos contratos assinados em 2025 vieram antes de a compra deles ser publicada no portal.\n"
            f"{br(NUM['antes_direta_parte'])}% desses casos são contratação direta (dispensa e inexigibilidade), registrada depois do fato.",
            FONTE + " · contratos assinados em 2025, uma linha por contrato\nLigados ao edital pelo número de controle da compra; mediana = dias entre a assinatura e a publicação do edital")
    salva(fig, "antes-do-edital")


# ------------------------------------------------------------ 6. sistemas de origem
def fig_sistemas():
    d = pl.read_csv(Q / "sistemas_2025.csv").sort("editais", descending=True)
    n = 10
    tot = d["editais"].sum()
    top = d.head(n)
    resto = d.slice(n)
    NUM["sistemas_2025"] = d.height
    NUM["comprasgov_pct_2025"] = round(100 * d["editais"][0] / tot, 1)
    nomes = top["sistema"].to_list() + [f"outros {resto.height} sistemas"]
    vals = [100 * v / tot for v in top["editais"]] + [100 * resto["editais"].sum() / tot]
    fig = plt.figure(figsize=(12.4, 8.4), dpi=200, facecolor=FIG)
    ax = fig.add_axes((0.36, 0.10, 0.58, 0.68))
    eixo(ax, "x")
    ys = list(range(len(nomes)))[::-1]
    ax.barh(ys, vals, height=0.66, color=[AZUL] * n + [CINZA])
    for y, v in zip(ys, vals):
        ax.text(v + 0.6, y, f"{br(v, 1)}%", va="center", fontsize=10.5, color=TXT)
    ax.set_yticks(ys, [s if len(s) < 42 else s[:40] + "…" for s in nomes], fontsize=10.5, color=TXT)
    ax.set_xticks([])
    ax.set_xlim(0, max(vals) * 1.15)
    moldura(fig, f"{d.height} sistemas alimentam o portal",
            f"O PNCP não tem formulário: cada órgão publica pelo sistema de compras que contratou, por API.\n"
            f"O Compras.gov.br, do governo federal, mandou {br(vals[0], 1)}% dos editais de 2025; o resto se espalha por outros {d.height - 1}.",
            FONTE + " · sistema de compras que publicou cada edital de 2025")
    salva(fig, "sistemas")


if __name__ == "__main__":
    import sys
    ate = sys.argv[1] if len(sys.argv) > 1 else "2026-11"   # primeiro mês fora do gráfico mensal (mês aberto)
    fig_mes(ate)
    fig_municipios()
    fig_modalidade()
    fig_valores()
    fig_antes()
    fig_sistemas()
    (Q / "numeros.json").write_text(json.dumps(NUM, ensure_ascii=False, indent=1, default=float))
    print(json.dumps(NUM, ensure_ascii=False, default=float))
