#!/usr/bin/env python3
"""Para onde vai o dinheiro da União: as figuras da análise gastos-federais.

Lê os CSVs agregados em docs/pesquisa/queries/gastos_federais/ (extraídos do espelho,
ver consultas.sql na mesma pasta) e escreve PNGs em pages/analises/img/gastos-federais-*.png.

Tema escuro (fundo #121211, tokens E_* de plot_vira_casacas.py) e os passos escuros da
paleta categórica validada. Os sankeys são desenhados à mão no matplotlib: faixas
de Bézier cúbicas entre colunas de nós empilhados, com a mesma escala de valor em
todas as colunas, para a altura de um nó ser comparável com a de qualquer outro.
"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.path import Path as MPath
import polars as pl

plt.rcParams["text.parse_math"] = False  # "R$ ... R$" não é LaTeX

RAIZ = Path(__file__).resolve().parent.parent
Q = RAIZ / "docs" / "pesquisa" / "queries" / "gastos_federais"
OUT = RAIZ / "pages" / "analises" / "img"

FIG, SUP = "#121211", "#1a1a19"
TXT, TXT2, TXT3 = "#f3f3ef", "#b8b8b1", "#8b8b84"
GRID, REF = "#2b2b29", "#5c5c57"
NEUTRO = "#4a4a46"

AZUL, LARANJA, AQUA, AMARELO = "#3987e5", "#d95926", "#199e70", "#c98500"
MAGENTA, VERDE, VIOLETA, VERMELHO = "#d55181", "#0ca30c", "#9085e9", "#e66767"
CINZA, CINZA_C = "#6b6b66", "#9c9c95"

FONTE_EXEC = "Fonte: Controladoria-Geral da União, Portal da Transparência · execução da despesa do Poder Executivo federal"

# ----------------------------------------------------------------- destinos
DESTINOS = [  # (chave, rótulo, cor) — a ordem é a ordem vertical nos sankeys
    ("rolagem", "Dívida: amortização e refinanciamento\n(quase tudo troca de títulos vencidos)", CINZA),
    ("juros", "Juros aos credores da dívida", VERMELHO),
    ("inss", "Aposentados e pensionistas do INSS", AZUL),
    ("familias", "Famílias: Bolsa Família, BPC,\nseguro-desemprego, abono", AQUA),
    ("serv_ativos", "Servidores e militares na ativa", VIOLETA),
    ("serv_inativos", "Servidores e militares\naposentados e pensionistas", MAGENTA),
    ("estados", "Estados e Distrito Federal", AMARELO),
    ("municipios", "Municípios", LARANJA),
    ("fornecedores", "Empresas: compras, serviços e obras", VERDE),
    ("emprestimos", "Empréstimos e participações\n(Fies, BNDES, fundos)", CINZA_C),
    ("outros", "Outros (subsídios, sentenças,\ncontas de anos anteriores)", NEUTRO),
]
ROT = {k: r for k, r, _ in DESTINOS}
COR = {k: c for k, _, c in DESTINOS}
ORDEM = [k for k, _, _ in DESTINOS]

FAMILIAS = {"06", "48", "10", "18", "08", "59", "20"}
INSS = {"53", "54", "55", "56", "57", "58"}
FORNEC = {"30", "32", "33", "35", "36", "37", "39", "40", "47", "51", "52", "61"}
SERVIDOR_3 = {"46", "49", "14", "19", "34", "04", "15"}  # auxílios e diárias pagos a servidores


def destino() -> pl.Expr:
    g, m, e = pl.col("grupo"), pl.col("modalidade"), pl.col("elemento")
    return (
        pl.when(g == "6").then(pl.lit("rolagem"))
        .when(g == "2").then(pl.lit("juros"))
        .when(m.is_in(["30", "31", "32", "35"])).then(pl.lit("estados"))
        .when(m.is_in(["40", "41", "42", "45", "71"])).then(pl.lit("municipios"))
        .when(m.is_in(["50", "60", "70", "80", "99", "72", "73", "74", "75", "76"])).then(pl.lit("outros"))
        .when(g == "5").then(pl.lit("emprestimos"))
        .when((g == "1") & e.is_in(["01", "03"])).then(pl.lit("serv_inativos"))
        .when(g == "1").then(pl.lit("serv_ativos"))
        .when(e.is_in(list(INSS))).then(pl.lit("inss"))
        .when(e.is_in(list(FAMILIAS))).then(pl.lit("familias"))
        .when(e.is_in(list(SERVIDOR_3))).then(pl.lit("serv_ativos"))
        .when(e.is_in(list(FORNEC)) | (g == "4")).then(pl.lit("fornecedores"))
        .otherwise(pl.lit("outros"))
    )


def le_exec(nome: str, valor: str = "pago") -> pl.DataFrame:
    d = pl.read_csv(Q / nome, infer_schema_length=0)
    return d.with_columns(pl.col(valor).cast(pl.Float64).alias("v")).with_columns(destino().alias("destino"))


# ----------------------------------------------------------------- formatos
def br(x: float, casas: int = 0) -> str:
    s = f"{x:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def bi(v: float) -> str:
    """v em reais → 'R$ 1.659 bi' / 'R$ 4,69 tri'."""
    b = v / 1e9
    if abs(b) >= 1000:
        return f"R$ {br(b / 1000, 2)} tri"
    if abs(b) >= 10:
        return f"R$ {br(b)} bi"
    return f"R$ {br(b, 1)} bi"


# ----------------------------------------------------------------- moldura
def moldura(fig, titulo, subtitulo, fonte, topo=0.965, x=0.05):
    fig.text(x, topo, titulo, ha="left", va="top", fontsize=25, fontweight="bold", color=TXT)
    fig.text(x, topo - 0.040, subtitulo, ha="left", va="top", fontsize=13.5, color=TXT2, linespacing=1.5)
    fig.text(x, 0.014, fonte, ha="left", va="bottom", fontsize=9.5, color=TXT3, linespacing=1.6)


def salva(fig, nome):
    destino_ = OUT / f"gastos-federais-{nome}.png"
    fig.savefig(destino_, facecolor=fig.get_facecolor())
    plt.close(fig)
    print("ok:", destino_.relative_to(RAIZ))


# ----------------------------------------------------------------- sankey
def sankey(ax, colunas, links, xs, larg=0.018, gap=0.012, rotulos=None, cor_no=None,
           min_rot=0.0, alpha=0.62, lado=None, fs=11.5):
    """colunas: lista de listas de (id, valor) na ordem vertical.
    links: lista de (origem, destino, valor, cor). xs: posição x de cada coluna (0..1).
    rotulos: id -> texto. lado: id -> 'esq'/'dir' (padrão: esquerda na 1ª coluna, direita no resto)."""
    rotulos = rotulos or {}
    cor_no = cor_no or {}
    lado = lado or {}
    total_max = max(sum(v for _, v in c) for c in colunas)
    n_max = max(len(c) for c in colunas)
    esc = (1 - gap * (n_max - 1)) / total_max
    pos, col_de = {}, {}
    for i, c in enumerate(colunas):
        tot = sum(v for _, v in c) * esc + gap * (len(c) - 1)
        y = 1 - (1 - tot) / 2  # centraliza a coluna
        for nid, v in c:
            h = v * esc
            pos[nid] = [xs[i], y, y - h]  # x, topo, base
            col_de[nid] = i
            y -= h + gap
    ordem_no = {nid: k for c in colunas for k, (nid, _) in enumerate(c)}
    saida = {nid: pos[nid][1] for nid in pos}
    entrada = {nid: pos[nid][1] for nid in pos}
    for o, d, v, cor in sorted(links, key=lambda l: (ordem_no[l[0]], ordem_no[l[1]])):
        pass
    # ordem das faixas: na saída pela ordem do destino, na entrada pela ordem da origem
    faixas = {}
    for o, d, v, cor in sorted(links, key=lambda l: (col_de[l[0]], ordem_no[l[0]], ordem_no[l[1]])):
        h = v * esc
        faixas[(o, d)] = [saida[o], saida[o] - h, None, None, cor]
        saida[o] -= h
    for o, d, v, cor in sorted(links, key=lambda l: (col_de[l[1]], ordem_no[l[1]], ordem_no[l[0]])):
        h = v * esc
        faixas[(o, d)][2:4] = [entrada[d], entrada[d] - h]
        entrada[d] -= h
    for (o, d), (a0, a1, b0, b1, cor) in faixas.items():
        xa = pos[o][0] + larg
        xb = pos[d][0]
        xm = (xa + xb) / 2
        verts = [(xa, a0), (xm, a0), (xm, b0), (xb, b0), (xb, b1), (xm, b1), (xm, a1), (xa, a1), (xa, a0)]
        codes = [MPath.MOVETO, MPath.CURVE4, MPath.CURVE4, MPath.CURVE4, MPath.LINETO,
                 MPath.CURVE4, MPath.CURVE4, MPath.CURVE4, MPath.CLOSEPOLY]
        ax.add_patch(PathPatch(MPath(verts, codes), fc=cor, ec="none", alpha=alpha, zorder=1))
    # nós
    for nid, (x, t, b) in pos.items():
        ax.add_patch(Rectangle((x, b), larg, max(t - b, 0.0015), fc=cor_no.get(nid, TXT2), ec=FIG, lw=0.6, zorder=3))
    # rótulos, empurrados para não se sobreporem
    for i, c in enumerate(colunas):
        itens = []
        for nid, v in c:
            if nid not in rotulos or v * esc < min_rot:
                continue
            x, t, b = pos[nid]
            lad = lado.get(nid, "esq" if i == 0 else "dir")
            itens.append([nid, (t + b) / 2, lad, rotulos[nid]])
        for lad in ("esq", "dir"):
            grupo = sorted([it for it in itens if it[2] == lad], key=lambda it: -it[1])
            bb = ax.get_position()
            unid = 1.04 / (bb.height * ax.figure.get_figheight())  # unidades do eixo por polegada
            linha = fs * 1.3 / 72 * unid
            alturas = [linha * (it[3].count("\n") + 1) + 0.3 * linha for it in grupo]
            ys = [it[1] for it in grupo]
            for k in range(1, len(ys)):  # de cima para baixo
                lim = ys[k - 1] - (alturas[k - 1] + alturas[k]) / 2
                ys[k] = min(ys[k], lim)
            if ys:
                ys[-1] = max(ys[-1], -0.02 + alturas[-1] / 2)  # não sai pelo pé da figura
            for k in range(len(ys) - 2, -1, -1):  # se desceu demais, sobe de volta
                lim = ys[k + 1] + (alturas[k] + alturas[k + 1]) / 2
                ys[k] = max(ys[k], lim)
            for it, y in zip(grupo, ys):
                nid, yc, _, txt = it
                x = pos[nid][0]
                if lad == "esq":
                    xt, ha = x - 0.008, "right"
                else:
                    xt, ha = x + larg + 0.008, "left"
                if abs(y - yc) > 0.004:
                    x0 = x if lad == "esq" else x + larg
                    ax.plot([x0, xt + (0.004 if lad == "esq" else -0.004)], [yc, y], color=REF, lw=0.7, zorder=2)
                ax.text(xt, y, txt, ha=ha, va="center", fontsize=fs, color=TXT, linespacing=1.25, zorder=4)
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.02, 1.02)
    ax.axis("off")
    return pos


def rot_no(nome, v, total=None, bold=True):
    pct = f" · {br(100 * v / total, 1)}%" if total else ""
    return f"{nome}\n{bi(v)}{pct}"


# ================================================================ figuras
FUNCOES = [("28", "Encargos especiais\n(dívida e repasses obrigatórios)"), ("09", "Previdência social"),
           ("08", "Assistência social"), ("10", "Saúde"), ("12", "Educação"), ("11", "Trabalho"),
           ("05", "Defesa nacional")]


def fig_total(ano=2025):
    d = le_exec(f"execucao_{ano}.csv")
    total = d["v"].sum()
    cods = [c for c, _ in FUNCOES]
    d = d.with_columns(pl.when(pl.col("codigo_funcao").is_in(cods)).then(pl.col("codigo_funcao")).otherwise(pl.lit("demais")).alias("f"))
    fx = d.group_by("f", "destino").agg(pl.col("v").sum()).filter(pl.col("v") > 0)
    por_f = {r["f"]: r["v"] for r in d.group_by("f").agg(pl.col("v").sum()).iter_rows(named=True)}
    por_d = {r["destino"]: r["v"] for r in d.group_by("destino").agg(pl.col("v").sum()).iter_rows(named=True)}
    n_dem = d.filter((pl.col("f") == "demais") & (pl.col("v") > 0))["codigo_funcao"].n_unique()
    nomes_f = dict(FUNCOES) | {"demais": f"Demais áreas ({n_dem} funções)"}
    col1 = [(f"f{c}", por_f[c]) for c in cods + ["demais"]]
    col2 = [(f"d{k}", por_d[k]) for k in ORDEM if por_d.get(k, 0) > 0]
    links = [("total", f"f{c}", por_f[c], "#3a3a37") for c in cods + ["demais"]]
    links += [(f"f{r['f']}", f"d{r['destino']}", r["v"], COR[r["destino"]]) for r in fx.iter_rows(named=True)]
    rot = {"total": rot_no(f"Total pago\nem {ano}", total)}
    rot |= {f"f{c}": rot_no(nomes_f[c], v, total) for c, v in [(k[1:], v) for k, v in col1]}
    rot |= {f"d{k}": rot_no(ROT[k], por_d[k], total) for k in ORDEM if k in por_d}
    rot = {k: v.replace("Encargos especiais\n(dívida e repasses obrigatórios)\n", "Encargos especiais\n(dívida e repasses\nobrigatórios)\n") for k, v in rot.items()}
    cor_no = {"total": TXT2} | {f"f{c}": "#8b8b84" for c in cods + ["demais"]} | {f"d{k}": COR[k] for k in ORDEM}
    fig = plt.figure(figsize=(14, 13), dpi=200, facecolor=FIG)
    ax = fig.add_axes((0.02, 0.05, 0.96, 0.82))
    sankey(ax, [[("total", total)], col1, col2], links, xs=[0.12, 0.44, 0.66], rotulos=rot, cor_no=cor_no,
           lado={f"f{c}": "esq" for c in cods + ["demais"]}, fs=10.5, larg=0.014)
    moldura(fig, f"Para onde foram {bi(total).replace('R$ ', 'R$ ').replace(' tri', ' trilhões')}",
            f"Tudo o que o Poder Executivo federal pagou em {ano}, pela área do orçamento (meio) e por quem recebeu o dinheiro (direita).\n"
            "Mais de um terço é amortização da dívida, quase toda feita trocando títulos vencidos por títulos novos.",
            FONTE_EXEC + f" ({ano}, pago no ano + restos a pagar pagos).\n"
            "Quem recebeu = classificação por grupo, modalidade e elemento de despesa. Não inclui Legislativo, Judiciário nem Ministério Público da União.\n"
            "Amortização inclui a cobertura do prejuízo do Banco Central (R$ 111 bi). Juros = só os pagos em dinheiro; a correção do principal fica na amortização.")
    salva(fig, f"sankey-total-{ano}")
    return d, total, por_d


def fig_cem_reais(d, por_d, ano=2025):
    sem = {k: v for k, v in por_d.items() if k != "rolagem" and v > 0}
    tot = sum(sem.values())
    # arredonda para 100 quadrados pelo maior resto
    bruto = {k: 100 * v / tot for k, v in sem.items()}
    inteiro = {k: int(x) for k, x in bruto.items()}
    falta = 100 - sum(inteiro.values())
    for k in sorted(bruto, key=lambda k: bruto[k] - inteiro[k], reverse=True)[:falta]:
        inteiro[k] += 1
    ordem = [k for k in ORDEM if k in inteiro]
    fig = plt.figure(figsize=(12.4, 10.6), dpi=200, facecolor=FIG)
    ax = fig.add_axes((0.05, 0.08, 0.50, 0.70))
    ax.set_aspect("equal")
    ax.axis("off")
    seq = [k for k in ordem for _ in range(inteiro[k])]
    for i, k in enumerate(seq):
        col, lin = i // 10, i % 10  # preenche por coluna, de cima para baixo
        ax.add_patch(Rectangle((col, 9 - lin), 0.86, 0.86, fc=COR[k], ec="none"))
    ax.set_xlim(-0.1, 10)
    ax.set_ylim(-0.1, 10)
    # legenda com valores, na ordem dos quadrados
    y = 0.765
    for k in ordem:
        fig.text(0.59, y, "■", color=COR[k], fontsize=20, va="center")
        fig.text(0.625, y + 0.004, f"R$ {inteiro[k]}", color=TXT, fontsize=17, fontweight="bold", va="center")
        nl = ROT[k].count("\n")
        fig.text(0.705, y + 0.012, ROT[k], color=TXT, fontsize=11.5, va="top", linespacing=1.2)
        fig.text(0.705, y - 0.010 - 0.019 * nl, f"{bi(sem[k])} no ano", color=TXT3, fontsize=10, va="top")
        y -= 0.066
    moldura(fig, "De cada R$ 100 que a União gasta…",
            f"Os {bi(tot)} pagos pelo Executivo federal em {ano}, sem a amortização da dívida. Cada quadrado é R$ 1 de cada R$ 100,\n"
            "e a ordem dos quadrados segue a da lista ao lado.",
            FONTE_EXEC + f" ({ano}).\nSem a amortização e o refinanciamento da dívida ({bi(por_d['rolagem'])}), quase toda feita com títulos novos; sai junto a cobertura do prejuízo\n"
            "do Banco Central (R$ 111 bi). Juros = só os pagos em dinheiro.")
    salva(fig, f"cem-reais-{ano}")
    return inteiro, sem, tot


def classifica_receita(r: pl.DataFrame) -> pl.DataFrame:
    dt = pl.col("detalhamento").str.to_uppercase()
    return r.with_columns(
        pl.when(pl.col("origem") == "Operações de Crédito").then(pl.lit("titulos"))
        .when(dt.str.contains("IRPJ|IRRF|IRPF")).then(pl.lit("ir"))
        .when(dt.str.contains("COFINS|PIS")).then(pl.lit("cofins"))
        .when(dt.str.contains("CSLL")).then(pl.lit("csll"))
        .when((pl.col("origem") == "Contribuições") & dt.str.contains("PREV|SEGURADO|SERVIDOR|PATRONAL|PENS"))
        .then(pl.lit("prev"))
        .when(pl.col("especie") == "Impostos").then(pl.lit("outros_imp"))
        .when(pl.col("especie") == "Exploração de recursos naturais").then(pl.lit("natureza"))
        .otherwise(pl.lit("outras_rec")).alias("fonte")
    )


FONTES = [("titulos", "Venda de títulos da dívida\n(empréstimos tomados no mercado)", CINZA),
          ("prev", "Contribuições previdenciárias\n(INSS e servidores)", AZUL),
          ("ir", "Imposto de Renda\n(empresas e pessoas)", VIOLETA),
          ("cofins", "Cofins e PIS", MAGENTA),
          ("csll", "CSLL (lucro das empresas)", AQUA),
          ("outros_imp", "IOF, IPI e imposto de importação", AMARELO),
          ("natureza", "Petróleo e minérios\n(royalties e participações)", LARANJA),
          ("outras_rec", "Demais receitas (rendimentos do\nTesouro, dividendos, taxas, multas)", CINZA_C)]


def fig_receita_despesa_2023():
    r = classifica_receita(pl.read_csv(Q / "receitas_2023_detalhe.csv"))
    total_rec = pl.read_csv(Q / "receitas_2023.csv")["realizado"].sum()
    por_fonte = {k: v for k, v in r.group_by("fonte").agg(pl.col("realizado").sum()).iter_rows()}
    por_fonte["outras_rec"] += total_rec - sum(por_fonte.values())  # linhas pequenas fora do detalhe
    d = le_exec("execucao_2023.csv", "pago_exercicio")
    total_desp = d["v"].sum()
    por_d = {k: v for k, v in d.group_by("destino").agg(pl.col("v").sum()).iter_rows() if v > 0}
    sobra = total_rec - total_desp
    col0 = [(f"r{k}", por_fonte[k]) for k, _, _ in FONTES]
    col2 = [(f"d{k}", por_d[k]) for k in ORDEM if k in por_d] + [("sobra", sobra)]
    links = [(f"r{k}", "caixa", por_fonte[k], c) for k, _, c in FONTES]
    links += [("caixa", f"d{k}", por_d[k], COR[k]) for k in ORDEM if k in por_d] + [("caixa", "sobra", sobra, "#3a3a37")]
    rot = {f"r{k}": rot_no(n, por_fonte[k]) for k, n, _ in FONTES}
    rot |= {f"d{k}": rot_no(ROT[k], por_d[k]) for k in por_d}
    rot |= {"sobra": rot_no("Ficou no caixa do Tesouro", sobra), "caixa": ""}
    cor_no = {f"r{k}": c for k, _, c in FONTES} | {f"d{k}": COR[k] for k in ORDEM} | {"caixa": TXT2, "sobra": "#3a3a37"}
    fig = plt.figure(figsize=(14, 12.6), dpi=200, facecolor=FIG)
    ax = fig.add_axes((0.02, 0.05, 0.96, 0.81))
    pos = sankey(ax, [col0, [("caixa", max(total_rec, total_desp + sobra))], col2], links, xs=[0.27, 0.48, 0.68],
                 rotulos=rot, cor_no=cor_no, fs=10.5, larg=0.014)
    x, t, b = pos["caixa"]
    ax.text(x + 0.007, t + 0.012, f"Caixa da União\n{bi(total_rec)}", ha="center", va="bottom", fontsize=11.5,
            color=TXT, fontweight="bold", linespacing=1.3)
    moldura(fig, "A dívida paga a dívida",
            "O que entrou nos cofres da União em 2023 (esquerda) e para onde saiu (direita). A maior fonte de dinheiro não foi imposto:\n"
            "foi a venda de títulos novos, e quase tudo voltou aos credores para resgatar títulos antigos.",
            "Fonte: Controladoria-Geral da União, Portal da Transparência · receitas da União e execução da despesa do Poder Executivo (2023, pago no exercício).\n"
            "A receita inclui todos os Poderes; a despesa, só o Executivo, por isso a sobra inclui o que foi gasto por Legislativo, Judiciário e MPU.")
    salva(fig, "sankey-receita-despesa-2023")
    return por_fonte, total_rec, por_d, total_desp, sobra


REGIAO = {**{u: "N" for u in ["AC", "AP", "AM", "PA", "RO", "RR", "TO"]},
          **{u: "NE" for u in ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"]},
          **{u: "SE" for u in ["ES", "MG", "RJ", "SP"]},
          **{u: "S" for u in ["PR", "RS", "SC"]},
          **{u: "CO" for u in ["DF", "GO", "MT", "MS"]}}
REG_NOME = {"NE": "Nordeste", "SE": "Sudeste", "N": "Norte", "S": "Sul", "CO": "Centro-Oeste", "sem": "Sem UF (nacional)"}


def mecanismo() -> pl.Expr:
    a, ln, na = pl.col("acao"), pl.col("linguagem_cidada").fill_null(""), pl.col("nome_acao").fill_null("")
    return (
        pl.when(a == "0045").then(pl.lit("fpm"))
        .when(a == "0044").then(pl.lit("fpe"))
        .when(a.is_in(["0C33", "00SB"])).then(pl.lit("fundeb"))
        .when(pl.col("nome_funcao") == "Saúde").then(pl.lit("sus"))
        .when(ln.str.contains("Royalties|CFEM") | na.str.contains("COMPENSACAO FINANCEIRA|PARTICIPACOES PELA PRODUCAO")).then(pl.lit("royalties"))
        .when(a == "0EC2").then(pl.lit("pix"))
        .otherwise(pl.lit("demais"))
    )


MECS = [("fpm", "FPM: fatia do IR e IPI\nque vai às prefeituras", LARANJA),
        ("fpe", "FPE: fatia do IR e IPI\nque vai aos estados", AMARELO),
        ("fundeb", "Fundeb e complementação\nda União (educação básica)", VIOLETA),
        ("sus", "SUS: hospitais, atenção\nprimária, vigilância", AZUL),
        ("royalties", "Royalties de petróleo\ne minérios", MAGENTA),
        ("pix", "Emendas \"Pix\"\n(transferências especiais)", VERMELHO),
        ("demais", "Demais repasses (salário-educação,\nmerenda, piso da enfermagem…)", CINZA_C)]


def le_transf(ano):
    t = pl.read_csv(Q / f"transferencias_{ano}.csv", infer_schema_length=0).with_columns(pl.col("valor").cast(pl.Float64))
    return t.with_columns(mecanismo().alias("mec"),
                          pl.col("uf").replace_strict(REGIAO, default="sem").alias("reg"))


def fig_transferencias(ano=2025):
    t = le_transf(ano)
    total = t["valor"].sum()
    mx = t.group_by("mec", "reg").agg(pl.col("valor").sum()).filter(pl.col("valor") > 0)
    por_m = {k: v for k, v in t.group_by("mec").agg(pl.col("valor").sum()).iter_rows()}
    por_r = {k: v for k, v in mx.group_by("reg").agg(pl.col("valor").sum()).iter_rows()}
    regs = [r for r in ["NE", "SE", "N", "S", "CO", "sem"] if r in por_r]
    col0 = [(f"m{k}", por_m[k]) for k, _, _ in MECS]
    col1 = [(f"g{r}", por_r[r]) for r in regs]
    corm = {k: c for k, _, c in MECS}
    links = [(f"m{r['mec']}", f"g{r['reg']}", r["valor"], corm[r["mec"]]) for r in mx.iter_rows(named=True)]
    rot = {f"m{k}": rot_no(n, por_m[k], total) for k, n, _ in MECS}
    rot |= {f"g{r}": rot_no(REG_NOME[r], por_r[r], total) for r in regs}
    cor_no = {f"m{k}": c for k, _, c in MECS} | {f"g{r}": TXT2 for r in regs}
    fig = plt.figure(figsize=(13.8, 11.4), dpi=200, facecolor=FIG)
    ax = fig.add_axes((0.02, 0.10, 0.96, 0.74))
    sankey(ax, [col0, col1], links, xs=[0.30, 0.68], rotulos=rot, cor_no=cor_no, fs=11, larg=0.016)
    moldura(fig, f"{bi(total)} para estados e prefeituras",
            f"O que a União repassou a governos estaduais e municipais em {ano}, por mecanismo (esquerda) e região de destino (direita).\n"
            "Dois terços são obrigação da Constituição: fatias de impostos e royalties que já nascem com dono.",
            f"Fonte: Controladoria-Geral da União, Portal da Transparência · transferências da União a estados, DF e municípios ({ano}).\n"
            "Inclui estornos. Região pela UF do ente favorecido. Esta fonte não traz as parcelas extras de 1% do FPM pagas em julho, setembro e dezembro\n"
            "(cerca de R$ 26 bi em 2025): pela execução do orçamento o FPM foi de R$ 198 bi.")
    salva(fig, f"sankey-transferencias-{ano}")
    return t, total, por_m, por_r


def fig_per_capita(t, ano=2025):
    pop = pl.read_csv(Q / "populacao_uf.csv")
    p = (t.filter(pl.col("uf").is_in(list(REGIAO))).group_by("uf").agg(pl.col("valor").sum())
         .join(pop.select(pl.col("sigla_uf").alias("uf"), "populacao"), on="uf")
         .with_columns((pl.col("valor") / pl.col("populacao")).alias("pc")).sort("pc"))
    media = p["valor"].sum() / p["populacao"].sum()
    fig = plt.figure(figsize=(12.4, 11.6), dpi=200, facecolor=FIG)
    ax = fig.add_axes((0.08, 0.08, 0.86, 0.72))
    ax.set_facecolor(FIG)
    for sp in ax.spines.values():
        sp.set_visible(False)
    regcor = {"N": AQUA, "NE": LARANJA, "SE": AZUL, "S": VIOLETA, "CO": AMARELO}
    ys = range(len(p))
    ax.barh(list(ys), p["pc"].to_list(), height=0.68, color=[regcor[REGIAO[u]] for u in p["uf"]])
    for y, (u, v) in enumerate(zip(p["uf"], p["pc"])):
        ax.text(v + 60, y, f"R$ {br(v)}", va="center", fontsize=10, color=TXT)
    ax.set_yticks(list(ys), p["uf"].to_list(), fontsize=10.5, color=TXT)
    ax.axvline(media, color=REF, lw=1.2, ls=(0, (4, 3)))
    ax.text(media + 60, len(p) - 0.2, f"média do país: R$ {br(media)} por habitante", color=TXT2, fontsize=11, va="bottom")
    ax.tick_params(axis="x", colors=TXT3, labelsize=10, length=0)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.xaxis.set_major_formatter(lambda x, _: f"R$ {br(x)}")
    ax.set_xlim(0, p["pc"].max() * 1.13)
    for i, (r, n) in enumerate([("N", "Norte"), ("NE", "Nordeste"), ("CO", "Centro-Oeste"), ("S", "Sul"), ("SE", "Sudeste")]):
        fig.text(0.08 + i * 0.15, 0.825, "■", color=regcor[r], fontsize=15, va="center")
        fig.text(0.10 + i * 0.15, 0.826, n, color=TXT, fontsize=11.5, va="center")
    topo, fundo = p.row(-1, named=True), p.row(0, named=True)
    moldura(fig, "Quem recebe mais por habitante",
            f"Repasses da União a estados e prefeituras em {ano}, divididos pela população de cada UF. \n{topo['uf']} recebe R$ {br(topo['pc'])} por pessoa; "
            f"{fundo['uf']}, R$ {br(fundo['pc'])}. A regra do FPM e do FPE favorece estados pouco populosos e de renda menor.",
            f"Fonte: Controladoria-Geral da União, Portal da Transparência · transferências da União ({ano}); IBGE · estimativa de população {ano}.\n"
            "Só repasses com UF identificada no favorecido. Sem as parcelas extras de 1% do FPM (julho, setembro e dezembro), que esta fonte não traz.")
    salva(fig, f"per-capita-uf-{ano}")
    return p, media


EMENDA_TIPO = [("Emenda Individual - Transferências com Finalidade Definida", "Individual com\nfinalidade definida", AZUL),
               ("Emenda Individual - Transferências Especiais", "Individual \"Pix\"\n(sem finalidade)", VERMELHO),
               ("Emenda de Comissão", "De comissão", AMARELO),
               ("Emenda de Bancada", "De bancada estadual", AQUA)]


def fig_emendas(ano=2025):
    e = pl.read_csv(Q / f"emendas_{ano}.csv", infer_schema_length=0).with_columns(pl.col("pago", "empenhado").cast(pl.Float64))
    e = e.filter(pl.col("pago") > 0)
    tot = e["pago"].sum()
    f_top = ["Saúde", "Encargos especiais"]
    e = e.with_columns(
        pl.when(pl.col("nome_funcao").is_in(f_top)).then(pl.col("nome_funcao")).otherwise(pl.lit("Demais")).alias("f"),
        pl.when(pl.col("regiao").is_in(["Nordeste", "Sudeste", "Norte", "Sul", "Centro-Oeste"])).then(pl.col("regiao"))
        .otherwise(pl.lit("Várias regiões ou nacional")).alias("r"),
        pl.col("tipo_de_emenda").replace_strict({k: k for k, _, _ in EMENDA_TIPO}, default="outro").alias("t"))
    tipos = [(k, n, c) for k, n, c in EMENDA_TIPO if k in set(e["t"])]
    por_t = {k: v for k, v in e.group_by("t").agg(pl.col("pago").sum()).iter_rows()}
    por_f = {k: v for k, v in e.group_by("f").agg(pl.col("pago").sum()).iter_rows()}
    por_r = {k: v for k, v in e.group_by("r").agg(pl.col("pago").sum()).iter_rows()}
    regs = [r for r in ["Nordeste", "Sudeste", "Norte", "Sul", "Centro-Oeste", "Várias regiões ou nacional"] if r in por_r]
    fs_ = [f for f in ["Saúde", "Encargos especiais", "Demais"] if f in por_f]
    cort = {k: c for k, _, c in tipos}
    tf = e.group_by("t", "f").agg(pl.col("pago").sum())
    fr = e.group_by("f", "r", "t").agg(pl.col("pago").sum())
    links = [(f"t{r['t']}", f"f{r['f']}", r["pago"], cort[r["t"]]) for r in tf.iter_rows(named=True)]
    # do meio para a direita a faixa mantém a cor do tipo de emenda
    links += [(f"f{r['f']}", f"r{r['r']}", r["pago"], cort[r["t"]]) for r in fr.iter_rows(named=True)]
    # faixas da 2ª etapa precisam ser únicas por par (origem, destino): soma por tipo dentro do par vira faixas separadas
    links2 = {}
    for o, d, v, c in links:
        links2.setdefault((o, d, c), 0)
        links2[(o, d, c)] += v
    # o motor indexa faixas por (origem, destino); quebramos o destino em sub-nós invisíveis? Não: agregamos por par e usamos cor neutra
    agreg = {}
    for (o, d, c), v in links2.items():
        agreg.setdefault((o, d), []).append((c, v))
    final = []
    cor_area = {"fSaúde": VIOLETA, "fEncargos especiais": MAGENTA, "fDemais": CINZA_C}
    for (o, d), lst in agreg.items():
        v = sum(x for _, x in lst)
        cor = cor_area[o] if o in cor_area else lst[0][0]
        final.append((o, d, v, cor))
    nome_f = {"Saúde": "Saúde", "Encargos especiais": "Encargos especiais\n(o \"Pix\" cai aqui)", "Demais": "Demais áreas\n(urbanismo, educação, esporte…)"}
    rot = {f"t{k}": rot_no(n, por_t[k], tot) for k, n, _ in tipos}
    rot |= {f"f{f}": rot_no(nome_f[f], por_f[f], tot) for f in fs_}
    rot |= {f"r{r}": rot_no(r, por_r[r], tot) for r in regs}
    cor_no = {f"t{k}": c for k, _, c in tipos} | {f"f{f}": cor_area[f"f{f}"] for f in fs_} | {f"r{r}": TXT2 for r in regs}
    fig = plt.figure(figsize=(13, 10.4), dpi=200, facecolor=FIG)
    ax = fig.add_axes((0.02, 0.06, 0.96, 0.77))
    sankey(ax, [[(f"t{k}", por_t[k]) for k, _, _ in tipos], [(f"f{f}", por_f[f]) for f in fs_], [(f"r{r}", por_r[r]) for r in regs]],
           [l for l in final if l[0].startswith("t")] + [l for l in final if l[0].startswith("f")],
           xs=[0.22, 0.50, 0.74], rotulos=rot, cor_no=cor_no, lado={f"f{f}": "esq" for f in fs_}, fs=11, larg=0.016)
    moldura(fig, f"O orçamento dos parlamentares: {bi(tot)}",
            f"Emendas parlamentares do orçamento de {ano} pagas até a última atualização da fonte, por tipo (esquerda), área (meio)\ne região indicada na emenda (direita). "
            f"{br(100 * por_f.get('Saúde', 0) / tot)}% foi para a saúde e {br(100 * por_t.get('Emenda Individual - Transferências Especiais', 0) / tot)}% saiu como \"Pix\", sem destinação definida.",
            f"Fonte: Controladoria-Geral da União, Portal da Transparência · emendas parlamentares (orçamento de {ano}, pago no ano e em restos a pagar).\n"
            "Do meio para a direita a cor é a da área. Região = localidade declarada na emenda, não o favorecido final.")
    salva(fig, f"sankey-emendas-{ano}")
    return tot, por_t, por_f, por_r


def fig_serie():
    s = pl.read_csv(Q / "execucao_serie.csv", infer_schema_length=0).with_columns(
        pl.col("pago").cast(pl.Float64).alias("v"), pl.col("ano").cast(pl.Int64)).with_columns(destino().alias("destino"))
    ipca = pl.read_csv(Q / "ipca.csv")
    base = ipca.filter(pl.col("ano") == 2025)["indice"][0]
    s = s.join(ipca, on="ano").with_columns((pl.col("v") * base / pl.col("indice")).alias("vr"))
    a = s.group_by("ano", "destino").agg(pl.col("vr").sum()).sort("ano")
    chaves = ["juros", "inss", "familias", "serv_ativos", "serv_inativos", "estados", "municipios", "fornecedores"]
    fig = plt.figure(figsize=(12.4, 12.2), dpi=200, facecolor=FIG)
    resumo = {}
    for i, k in enumerate(chaves):
        lin, col = divmod(i, 2)
        ax = fig.add_axes((0.07 + col * 0.47, 0.665 - lin * 0.19, 0.40, 0.10))
        x = a.filter(pl.col("destino") == k)
        anos, vals = x["ano"].to_list(), [v / 1e9 for v in x["vr"].to_list()]
        ax.set_facecolor(FIG)
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.fill_between(anos, vals, color=COR[k], alpha=0.18, lw=0)
        ax.plot(anos, vals, color=COR[k], lw=2.2)
        ax.scatter([anos[0], anos[-1]], [vals[0], vals[-1]], s=22, color=COR[k], zorder=3, edgecolor=FIG, lw=1.5)
        ax.set_ylim(0, max(vals) * 1.25)
        ax.set_xlim(2013.6, 2025.4)
        ax.grid(axis="y", color=GRID, lw=0.8)
        ax.tick_params(colors=TXT3, labelsize=9, length=0)
        ax.set_xticks([2014, 2017, 2020, 2023, 2025])
        ax.yaxis.set_major_locator(plt.MaxNLocator(3))
        ax.yaxis.set_major_formatter(lambda y, _: f"{br(y)}")
        var = 100 * (vals[-1] / vals[0] - 1)
        resumo[k] = (vals[0], vals[-1], var)
        sinal = "+" if var >= 0 else "−"
        ax.text(0, 1.36, ROT[k].replace("\n", " "), transform=ax.transAxes, fontsize=11.5, color=TXT, fontweight="bold", va="bottom")
        ax.text(0, 1.12, f"R$ {br(vals[0])} bi → R$ {br(vals[-1])} bi  ({sinal}{br(abs(var))}%)", transform=ax.transAxes,
                fontsize=10, color=TXT2, va="bottom")
    moldura(fig, "Doze anos de gasto, já descontada a inflação",
            "Quanto cada destino recebeu do Executivo federal por ano, de 2014 a 2025, em bilhões de reais de 2025.\n"
            "Cada painel tem sua própria escala: compare a forma da curva, não a altura entre painéis.",
            FONTE_EXEC + " (pago no ano + restos a pagar pagos).\nValores corrigidos pela média anual do IPCA (IBGE). 2020 inclui o auxílio emergencial da pandemia.")
    salva(fig, "serie-2014-2025")
    return resumo


ZOOMS = [
    ("encargos", ["28"], "Encargos especiais: a dívida e os repasses obrigatórios",
     "Os {total} da função \"encargos especiais\" em 2025, por ação do orçamento (meio) e por quem recebeu (direita).\n"
     "É aqui que mora a dívida pública e também a fatia de impostos que a Constituição manda entregar a estados e prefeituras.",
     [("0365", "Refinanciamento da dívida interna"), ("0455", "Serviço da dívida interna\n(juros e resgates)"),
      ("0045", "FPM (prefeituras)"), ("0044", "FPE (estados)"), ("0669", "Prejuízo do Banco Central\ncoberto pelo Tesouro"),
      ("0C33", "Fundeb"), ("0A53", "Royalties do petróleo"), ("0243", "Refinanciamento da\ndívida externa")]),
    ("protecao", ["09", "08", "11"], "Proteção social: previdência, assistência e trabalho",
     "As três funções que pagam benefícios a pessoas somaram {total} em 2025. Quase dois terços disso é um só item:\n"
     "as aposentadorias, pensões e auxílios do INSS.",
     [("00SJ", "Benefícios do INSS\n(aposentadorias, pensões, auxílios)"), ("8442", "Bolsa Família"),
      ("0181", "Aposentadorias e pensões\nde servidores civis"), ("00IN", "BPC à pessoa com deficiência"),
      ("00H4", "Seguro-desemprego"), ("00H5", "BPC à pessoa idosa"), ("0581", "Abono salarial (PIS)"),
      ("0158", "FAT emprestado ao BNDES")]),
    ("saude", ["10"], "Saúde: o SUS é, sobretudo, repasse",
     "Os {total} que o Executivo federal pagou na função saúde em 2025. A maior parte não é gasta pelo ministério:\n"
     "vai fundo a fundo para estados e municípios, que contratam hospitais, equipes e exames.",
     [("8585", "Média e alta complexidade\n(hospitais, exames, cirurgias)"), ("219A", "Piso da atenção primária\n(postos e equipes)"),
      ("4705", "Remédios de alto custo"), ("2E89", "Reforço temporário da atenção\nprimária (via emendas)"),
      ("2E90", "Reforço temporário de\nhospitais (via emendas)"), ("00UW", "Piso salarial da enfermagem"),
      ("00UC", "Salário dos agentes\ncomunitários de saúde"), ("20YE", "Vacinas e insumos")]),
    ("educacao", ["12"], "Educação: professores federais e o Fundeb",
     "Os {total} da função educação em 2025. Dois itens respondem por dois terços: a folha das universidades\n"
     "e institutos federais e a complementação da União ao Fundeb, que banca a educação básica de estados e municípios.",
     [("20TP", "Folha de servidores ativos\n(universidades, institutos)"), ("00SB", "Complementação da União\nao Fundeb"),
      ("09HB", "Contribuição patronal à\nprevidência dos servidores"), ("00IG", "Fies"), ("00PI", "Merenda escolar (PNAE)"),
      ("20RK", "Custeio das universidades\nfederais"), ("212B", "Benefícios obrigatórios\naos servidores"),
      ("0487", "Bolsas no ensino superior")]),
    ("defesa", ["05"], "Defesa: mais aposentado que avião",
     "Os {total} da função defesa nacional em 2025. Os militares da reserva já custam tanto quanto a tropa na ativa, e as pensões\n"
     "militares (R$ 26 bi) nem entram aqui: ficam em encargos especiais. Caças e submarinos somam cerca de 4%.",
     [("214H", "Militares inativos"), ("2867", "Militares na ativa"), ("2004", "Assistência médica\na militares e dependentes"),
      ("212B", "Benefícios obrigatórios\n(auxílios, fardamento)"), ("20XV", "Controle do espaço aéreo"),
      ("14T7|123G|123H|123I", "Submarinos e estaleiro\n(Prosub, inclui o nuclear)"), ("14T0", "Caças Gripen (FX-2)")]),
]


def fig_zooms(d):
    out = {}
    for chave, funcoes, titulo, sub, acoes in ZOOMS:
        s = d.filter(pl.col("codigo_funcao").is_in(funcoes))
        total = s["v"].sum()
        # destinos com menos de 0,6% do total viram "outros", para os rótulos caberem
        pequenos = [k for k, v in s.group_by("destino").agg(pl.col("v").sum()).iter_rows() if v < 0.006 * total]
        s = s.with_columns(pl.when(pl.col("destino").is_in(pequenos)).then(pl.lit("outros")).otherwise(pl.col("destino")).alias("destino"))
        cods = [c for c, _ in acoes]
        apelido = {parte: c for c in cods for parte in c.split("|")}
        s = s.with_columns(pl.col("codigo_acao").replace(apelido))
        s = s.with_columns(pl.when(pl.col("codigo_acao").is_in(cods)).then(pl.col("codigo_acao")).otherwise(pl.lit("demais")).alias("a"))
        por_a = {k: v for k, v in s.group_by("a").agg(pl.col("v").sum()).iter_rows()}
        ad = s.group_by("a", "destino").agg(pl.col("v").sum()).filter(pl.col("v") > 0)
        por_d = {k: v for k, v in ad.group_by("destino").agg(pl.col("v").sum()).iter_rows()}
        n_dem = s.filter(pl.col("a") == "demais")["codigo_acao"].n_unique()
        nomes = dict(acoes) | {"demais": f"Demais ações ({br(n_dem)})"}
        lista_a = [c for c in cods if por_a.get(c, 0) > 0] + (["demais"] if por_a.get("demais", 0) > 0 else [])
        col1 = [(f"a{c}", por_a[c]) for c in lista_a]
        col2 = [(f"d{k}", por_d[k]) for k in ORDEM if por_d.get(k, 0) > 0]
        links = [("area", f"a{c}", por_a[c], "#3a3a37") for c in lista_a]
        links += [(f"a{r['a']}", f"d{r['destino']}", r["v"], COR[r["destino"]]) for r in ad.iter_rows(named=True)]
        rot = {"area": rot_no("Total", total)}
        rot |= {f"a{c}": rot_no(nomes[c], por_a[c], total) for c in lista_a}
        rot |= {f"d{k}": rot_no(ROT[k], por_d[k], total) for k in ORDEM if k in por_d}
        cor_no = {"area": TXT2} | {f"a{c}": "#8b8b84" for c in lista_a} | {f"d{k}": COR[k] for k in ORDEM}
        alt = 9.6 + 0.25 * max(len(col1), len(col2))
        fig = plt.figure(figsize=(14, alt), dpi=200, facecolor=FIG)
        ax = fig.add_axes((0.02, 0.06, 0.96, 1 - 0.06 - 2.0 / alt))
        sankey(ax, [[("area", total)], col1, col2], links, xs=[0.10, 0.42, 0.65], rotulos=rot, cor_no=cor_no,
               lado={f"a{c}": "esq" for c in lista_a}, fs=10.5, larg=0.014)
        moldura(fig, titulo, sub.format(total=bi(total)),
                FONTE_EXEC + " (2025, pago no ano + restos a pagar pagos).\nAções agrupadas pelo código do orçamento; nomes encurtados. Juros = só os pagos em dinheiro.",
                topo=1 - 0.45 / alt)
        salva(fig, f"zoom-{chave}-2025")
        out[chave] = {"total": total, "acoes": por_a, "destinos": por_d}
    return out


if __name__ == "__main__":
    import json
    d, total, por_d = fig_total(2025)
    zooms = fig_zooms(d)
    inteiro, sem, tot_sem = fig_cem_reais(d, por_d)
    rec = fig_receita_despesa_2023()
    t, tot_t, por_m, por_r = fig_transferencias()
    p, media = fig_per_capita(t)
    em = fig_emendas()
    resumo = fig_serie()
    numeros = {
        "total_2025": total, "por_destino_2025": por_d, "cem_reais": inteiro, "sem_rolagem_2025": tot_sem, "zooms": zooms,
        "receitas_2023": rec[0], "total_rec_2023": rec[1], "despesa_2023": rec[2], "total_desp_2023": rec[3], "sobra_2023": rec[4],
        "transf_total": tot_t, "transf_mec": por_m, "transf_reg": por_r, "per_capita": p.to_dicts(), "media_pc": media,
        "emendas": {"total": em[0], "tipo": em[1], "funcao": em[2], "regiao": em[3]}, "serie": resumo,
    }
    (Q / "numeros.json").write_text(json.dumps(numeros, ensure_ascii=False, indent=1, default=float))
    print("ok:", (Q / "numeros.json").relative_to(RAIZ))
