#!/usr/bin/env python3
"""Medicamentos especializados, quimioterapia e sorotipos da dengue: as três figuras
acrescentadas à análise RWD em inglês (brazil-public-real-world-data) em novembro de 2026.

Lê os CSVs que `docs/pesquisa/queries/rwd_especializados/roda.sh` grava ao lado de cada
qN_*.sql (SIA/APAC, SINAN dengue, população do IBGE, CID-10, orçamento federal) e escreve
PNGs em pages/analises/img/, no mesmo formato das figuras de plot_dengue_rwd.py:
matplotlib, 12,4 pol. de largura, dpi 200, título, subtítulo, leitura e fonte na figura.

2026 fica fora das séries do SIA: o ano ainda está em curso (FTP do DATASUS até 2026-08).
Supressão: célula com menos de 10 registros não aparece.

`--pt` gera as mesmas figuras em português, com sufixo -pt, para o par
dados-de-mundo-real-do-sus.
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl

RAIZ = Path(__file__).resolve().parent.parent
Q = RAIZ / "docs" / "pesquisa" / "queries" / "rwd_especializados"
OUT = RAIZ / "pages" / "analises" / "img"

SURFACE, FIG_BG = "#fcfcfb", "#f7f7f5"
TXT, TXT2, TXT3 = "#111111", "#555555", "#7b7b76"
RED, BLUE, TEAL = "#d1453b", "#2a78d6", "#1f9e89"
PALE_RED, PALE_BLUE = "#e8a29c", "#a9c7ef"
GRID, REF = "#e6e6e2", "#b6b6ae"
MIN_N = 10
PT = "--pt" in sys.argv


def T(en, pt):
    """Texto no idioma da rodada."""
    return pt if PT else en


def num(v, molde):
    """Formata com o molde em inglês e troca os separadores em português."""
    txt = molde.format(v)
    return txt.replace(",", "\0").replace(".", ",").replace("\0", ".") if PT else txt

ULTIMO_ANO_SIA = 2025
NOME_UF = {"AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá", "BA": "Bahia", "CE": "Ceará",
           "DF": T("the Federal District", "o Distrito Federal"), "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão",
           "MG": "Minas Gerais", "MS": "Mato Grosso do Sul", "MT": "Mato Grosso", "PA": "Pará", "PB": "Paraíba",
           "PE": "Pernambuco", "PI": "Piauí", "PR": "Paraná", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
           "RO": "Rondônia", "RR": "Roraima", "RS": "Rio Grande do Sul", "SC": "Santa Catarina", "SE": "Sergipe",
           "SP": "São Paulo", "TO": "Tocantins"}

FONTE_SIA = T("Ministry of Health / DATASUS: Outpatient Information System (SIA/SUS), "
              "high-complexity authorisations (APAC)",
              "Ministério da Saúde / DATASUS, Sistema de Informações Ambulatoriais (SIA/SUS), APAC")
FONTE_SINAN = T("Ministry of Health / DATASUS: Notifiable Diseases Information System (SINAN), dengue",
                "Ministério da Saúde / DATASUS: Sistema de Informação de Agravos de Notificação (SINAN), dengue")

UF = {"11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
      "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
      "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP", "41": "PR",
      "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF"}

# Nomes em inglês das categorias CID-10 que aparecem nas figuras.
CID_EN = {
    "E78": "Lipid disorders", "H40": "Glaucoma", "F20": "Schizophrenia",
    "N18": "Chronic kidney disease", "J45": "Asthma", "J44": "COPD",
    "M05": "Rheumatoid arthritis, seropositive", "Z94": "Organ transplant",
    "G40": "Epilepsy", "F31": "Bipolar disorder", "E11": "Type 2 diabetes",
    "R52": "Pain, not elsewhere classified", "G30": "Alzheimer's disease",
    "M32": "Systemic lupus", "E10": "Type 1 diabetes",
    "C50": "Breast", "C61": "Prostate", "C92": "Myeloid leukaemia", "C18": "Colon",
    "C90": "Multiple myeloma", "D47": "Myeloproliferative/uncertain", "C34": "Lung",
    "C20": "Rectum", "C53": "Cervix", "C16": "Stomach", "C91": "Lymphoid leukaemia",
    "C67": "Bladder",
}

CID_PT = {
    "E78": "Dislipidemias", "H40": "Glaucoma", "F20": "Esquizofrenia",
    "N18": "Doença renal crônica", "J45": "Asma", "J44": "DPOC",
    "M05": "Artrite reumatoide soropositiva", "Z94": "Transplante de órgão",
    "G40": "Epilepsia", "F31": "Transtorno bipolar", "E11": "Diabetes tipo 2",
    "R52": "Dor não classificada", "G30": "Doença de Alzheimer",
    "M32": "Lúpus sistêmico", "E10": "Diabetes tipo 1",
    "C50": "Mama", "C61": "Próstata", "C92": "Leucemia mieloide", "C18": "Cólon",
    "C90": "Mieloma múltiplo", "D47": "Mieloproliferativas/incertas", "C34": "Pulmão",
    "C20": "Reto", "C53": "Colo do útero", "C16": "Estômago", "C91": "Leucemia linfoide",
    "C67": "Bexiga",
}
CID_NOME = CID_PT if PT else CID_EN

# Doenças da série: CIDs somados sob um rótulo.
SERIE = [
    (T("Psoriasis", "Psoríase"), ["L40"]),
    (T("Systemic lupus", "Lúpus sistêmico"), ["M32"]),
    (T("Ankylosing spondylitis", "Espondilite anquilosante"), ["M45"]),
    (T("Rheumatoid arthritis", "Artrite reumatoide"), ["M05", "M06"]),
    (T("Multiple sclerosis", "Esclerose múltipla"), ["G35"]),
    (T("Inflammatory bowel disease", "Doença inflamatória intestinal"), ["K50", "K51"]),
    (T("Asthma", "Asma"), ["J45"]),
    (T("Schizophrenia", "Esquizofrenia"), ["F20"]),
    (T("Alzheimer's disease", "Doença de Alzheimer"), ["G30"]),
]


def ler(nome, **kw):
    return pl.read_csv(Q / f"{nome}.csv", null_values=["NULL", ""], **kw)


def apac():
    return ler("q1_apac_cid_ano", schema_overrides={
        "grupo": pl.Utf8, "cid3": pl.Utf8, "id_uf": pl.Utf8, "instrumento": pl.Utf8})


def eixo(ax, grid_y=True):
    ax.set_facecolor(SURFACE)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(colors=TXT3, labelsize=11, length=0)
    if grid_y:
        ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)


def moldura(fig, titulo, subtitulo, leitura, fonte, topo=0.955):
    fig.text(0.07, topo, titulo, ha="left", va="top", fontsize=23,
             fontweight="bold", color=TXT)
    fig.text(0.07, topo - 0.043, subtitulo, ha="left", va="top", fontsize=13,
             color=TXT2)
    fig.text(0.07, topo - 0.080, leitura, ha="left", va="top", fontsize=13,
             color=TXT, linespacing=1.6)
    fig.text(0.07, 0.015, fonte, ha="left", va="bottom", fontsize=9.5,
             color=TXT3, linespacing=1.6)


def transborda(fig):
    """Avisa de texto que passa da borda da figura (o português é ~15% mais longo)."""
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    for t in fig.findobj(plt.Text):
        if t.get_visible() and t.get_text().strip():
            bb = t.get_window_extent(rend)
            if bb.x1 > fig.bbox.width + 1 or bb.x0 < -1:
                print(f"  TRANSBORDA ({bb.x1 - fig.bbox.width:+.0f}px):", t.get_text()[:70].replace("\n", " | "))


def salva(fig, nome):
    transborda(fig)
    destino = OUT / f"{nome}{'-pt' if PT else ''}.png"
    fig.savefig(destino, facecolor=fig.get_facecolor())
    plt.close(fig)
    print("ok:", destino.relative_to(RAIZ))


def barras(ax, rotulos, vals, destaque, molde, cor, cor_palida):
    ys = list(range(len(vals)))[::-1]
    eixo(ax, grid_y=False)
    ax.grid(axis="x", color=GRID, lw=0.8)
    cores = [cor if d else cor_palida for d in destaque]
    ax.barh(ys, vals, color=cores, height=0.72, edgecolor=SURFACE, linewidth=2)
    ax.set_yticks(ys)
    ax.set_yticklabels(rotulos, fontsize=11, color=TXT2)
    for y, v in zip(ys, vals):
        ax.text(v + max(vals) * 0.015, y, num(v, molde), va="center",
                fontsize=10, color=TXT2)
    ax.set_xlim(0, max(vals) * 1.18)
    ax.set_ylim(-0.7, len(vals) - 0.3)


# ------------------------------------------------- 1. ranking do último ano
def ranking_ultimo_ano():
    a = apac().filter(pl.col("ano") == ULTIMO_ANO_SIA)
    med = (a.filter(pl.col("grupo") == "0604").group_by("cid3")
           .agg(pl.sum("linhas"), pl.sum("valor")).sort("linhas", descending=True))
    qt = (a.filter(pl.col("grupo") == "0304").group_by("cid3")
          .agg(pl.sum("linhas"), pl.sum("valor")).sort("linhas", descending=True))
    tot_med, tot_qt = med["linhas"].sum(), qt["linhas"].sum()
    m15, q12 = med.head(15), qt.head(12)
    zero = m15.filter(pl.col("valor") == 0).height

    fig = plt.figure(figsize=(12.4, 11.2), dpi=200, facecolor=FIG_BG)
    ax1 = fig.add_axes((0.30, 0.10, 0.25, 0.62))
    ax2 = fig.add_axes((0.71, 0.10, 0.25, 0.62))
    barras(ax1, [CID_NOME.get(c, c) for c in m15["cid3"]],
           [v / 1e6 for v in m15["linhas"]],
           [v == 0 for v in m15["valor"]], T("{:.1f}M", "{:.1f} mi"), BLUE, PALE_BLUE)
    ax1.set_xlabel(T("monthly dispensing records, millions", "registros mensais de dispensação, milhões"), fontsize=11, color=TXT2,
                   labelpad=8)
    ax1.text(-0.62, 1.07, T("Specialised-component drugs", "Medicamentos do Componente Especializado"), transform=ax1.transAxes,
             fontsize=13, color=TXT, fontweight="bold")
    ax1.text(-0.62, 1.03, T("dark bar = R$ 0 billed for the whole year", "barra escura = R$ 0 faturado no ano inteiro"),
             transform=ax1.transAxes, fontsize=10, color=BLUE)
    barras(ax2, [CID_NOME.get(c, c) for c in q12["cid3"]],
           [v / 1e3 for v in q12["linhas"]],
           [c == "C50" for c in q12["cid3"]], T("{:,.0f}k", "{:,.0f} mil"), RED, PALE_RED)
    ax2.set_xlabel(T("monthly chemotherapy authorisations, thousands", "autorizações mensais de quimioterapia, milhares"), fontsize=11,
                   color=TXT2, labelpad=8)
    ax2.text(-0.62, 1.07, T("Cancer drug therapy, by site", "Quimioterapia, por localização do câncer"), transform=ax2.transAxes,
             fontsize=13, color=TXT, fontweight="bold")
    ax2.text(-0.62, 1.03, T("red = breast cancer", "vermelho = câncer de mama"), transform=ax2.transAxes,
             fontsize=10, color=RED)
    mama = qt.filter(pl.col("cid3") == "C50")["linhas"][0] / tot_qt
    if PT:
        moldura(
            fig,
            "Que doenças o SUS trata com medicamentos de alto custo",
            f"Brasil, {ULTIMO_ANO_SIA}, APACs ambulatoriais do SUS pelo CID-10 do paciente, doenças principais",
            f"{num(tot_med / 1e6, '{:.1f}')} milhões de registros mensais de medicamentos especializados e {num(tot_qt / 1e6, '{:.1f}')} milhões de quimioterapia, "
            "todos com CID.\n"
            f"Só o câncer de mama soma {num(mama * 100, '{:.0f}')}% da quimioterapia: em geral, tratamento adjuvante pós-cirurgia, autorizado mês a mês.\n"
            f"Em {zero} dos 15 diagnósticos principais a conta é R$ 0: o Ministério compra esses medicamentos de forma centralizada.",
            f"Fonte: {FONTE_SIA}, por ano de processamento.\n"
            "Especializados = grupo SIGTAP 06.04 (CEAF); quimioterapia = grupo 03.04. "
            "Registro = um procedimento, um paciente, um mês.",
            topo=0.965,
        )
        return salva(fig, f"rwd-specialty-drugs-{ULTIMO_ANO_SIA}")
    moldura(
        fig,
        "Which diseases the public system treats with high-cost drugs",
        f"Brazil {ULTIMO_ANO_SIA}, SUS outpatient authorisations by ICD-10 of the patient, top diseases",
        f"{tot_med / 1e6:.1f} million monthly records of specialised drugs and {tot_qt / 1e6:.1f} million of cancer drug therapy, "
        "each carrying a diagnosis.\n"
        f"Breast cancer alone is {mama:.0%} of cancer authorisations: most are adjuvant treatment after surgery, authorised month after month.\n"
        f"For {zero} of the 15 leading drug diagnoses the bill is R$ 0, because the Ministry buys those drugs centrally.",
        f"Source: {FONTE_SIA}, by year of processing.\n"
        "Specialised drugs = SIGTAP group 06.04 (Specialised Component of Pharmaceutical Care); cancer = group 03.04. "
        "Record = one procedure, one patient, one month.",
        topo=0.965,
    )
    salva(fig, f"rwd-specialty-drugs-{ULTIMO_ANO_SIA}")


# ------------------------------------------- 2. crescimento e desigualdade
def crescimento():
    a = apac().filter((pl.col("grupo") == "0604") & (pl.col("ano") <= ULTIMO_ANO_SIA))
    fig = plt.figure(figsize=(12.4, 11.6), dpi=200, facecolor=FIG_BG)
    ax1 = fig.add_axes((0.07, 0.10, 0.40, 0.60))
    ax2 = fig.add_axes((0.72, 0.10, 0.25, 0.60))

    eixo(ax1)
    finais = []
    for rot, cids in SERIE:
        t = (a.filter(pl.col("cid3").is_in(cids)).group_by("ano").agg(pl.sum("linhas"))
             .sort("ano"))
        base = t.filter(pl.col("ano") == 2014)["linhas"][0]
        idx = [v / base for v in t["linhas"]]
        forte = idx[-1] >= 3
        ax1.plot(t["ano"].to_list(), idx, color=BLUE if forte else REF,
                 lw=2.6 if forte else 1.5, zorder=3 if forte else 2)
        finais.append((idx[-1], rot, forte))
    # rótulos à direita, afastados para não encavalar
    finais.sort()
    ult = -1.0
    for v, rot, forte in finais:
        y = max(v, ult + 0.22)
        ax1.text(ULTIMO_ANO_SIA + 0.25, y, f"{rot} ×{num(v, '{:.1f}')}", va="center", fontsize=10,
                 color=TXT if forte else TXT3, fontweight="bold" if forte else "normal")
        ult = y
    ax1.axhline(1, color=REF, lw=1, ls=(0, (5, 3.5)))
    ax1.set_xlim(2014, ULTIMO_ANO_SIA)
    ax1.set_xticks(list(range(2014, ULTIMO_ANO_SIA + 1, 2)))
    ax1.text(0.0, 1.03, T("Dispensing records, 2014 = 1", "Registros de dispensação, 2014 = 1"), transform=ax1.transAxes,
             fontsize=12.5, color=TXT2)

    pop = ler("q3_populacao_uf", schema_overrides={"id_uf": pl.Utf8})
    ra = (a.filter((pl.col("ano") == ULTIMO_ANO_SIA) & pl.col("cid3").is_in(["M05", "M06"]))
          .group_by("id_uf").agg(pl.sum("linhas")).join(pop, on="id_uf")
          .with_columns(taxa=pl.col("linhas") / 12 / pl.col("populacao") * 1e5)
          .sort("taxa"))
    ys = list(range(ra.height))
    eixo(ax2, grid_y=False)
    ax2.grid(axis="x", color=GRID, lw=0.8)
    siglas = [UF[u] for u in ra["id_uf"]]
    taxas = ra["taxa"].to_list()
    alto, baixo = siglas[-1], siglas[0]
    ax2.barh(ys, taxas, color=[BLUE if s in (alto, baixo) else PALE_BLUE for s in siglas],
             height=0.72, edgecolor=SURFACE, linewidth=2)
    ax2.set_yticks(ys)
    ax2.set_yticklabels(siglas, fontsize=10, color=TXT2)
    for y, v in zip(ys, taxas):
        ax2.text(v + 4, y, f"{v:.0f}", va="center", fontsize=9.5, color=TXT2)
    ax2.set_ylim(-0.7, ra.height - 0.3)
    ax2.set_xlim(0, max(taxas) * 1.15)
    ax2.set_xlabel(T("patients per month per 100,000", "pacientes por mês por 100 mil hab."), fontsize=10.5,
                   color=TXT2, labelpad=8)
    nac = ra["linhas"].sum() / 12 / ra["populacao"].sum() * 1e5
    ax2.axvline(nac, color=REF, lw=1.1, ls=(0, (5, 3.5)))
    ax2.text(nac + 4, -0.55, f"{T('Brazil', 'Brasil')} {nac:.0f}", fontsize=10, color=TXT3, va="center")
    ax2.text(0.0, 1.03, T(f"Rheumatoid arthritis by state, {ULTIMO_ANO_SIA}", f"Artrite reumatoide por UF, {ULTIMO_ANO_SIA}"), transform=ax2.transAxes,
             fontsize=12.5, color=TXT2)
    pr, al = taxas[-1], taxas[0]
    if PT:
        moldura(
            fig,
            "Imunobiológicos cresceram mais, e chegam de forma desigual",
            f"Dispensação do Componente Especializado do SUS por diagnóstico, 2014–{ULTIMO_ANO_SIA} (esq.) e artrite reumatoide por UF (dir.)",
            "Psoríase, lúpus e espondilite anquilosante cresceram de quatro a sete vezes em uma década, com a entrada\n"
            "de novos medicamentos, muitos deles biológicos, nos protocolos do SUS; Alzheimer ficou estável.\n"
            f"Para a mesma doença, {NOME_UF[alto]} atende {pr:.0f} pacientes por 100 mil e {NOME_UF[baixo]}, {al:.0f}:\n"
            f"uma diferença de {pr / al:.0f} vezes, que mede acesso, não prevalência.",
            f"Fonte: {FONTE_SIA}, grupo SIGTAP 06.04; população do IBGE, {ULTIMO_ANO_SIA}.\n"
            "UF do estabelecimento. Registros mensais ÷ 12 ≈ pacientes em tratamento num mês médio "
            "(quem usa dois medicamentos conta duas vezes).",
            topo=0.965,
        )
        return salva(fig, "rwd-specialty-drugs-trend")
    moldura(
        fig,
        "Immunology drugs grew fastest, and reach patients unevenly",
        f"SUS specialised-component dispensing by diagnosis, 2014–{ULTIMO_ANO_SIA} (left) and rheumatoid arthritis by state (right)",
        "Records for psoriasis, lupus and ankylosing spondylitis grew four to seven times in a decade, as new drugs, many of them\n"
        "biologics, entered the public treatment protocols; Alzheimer's stayed flat. For the same disease, "
        f"{NOME_UF[alto]} dispenses to\n{pr:.0f} patients per 100,000 and {NOME_UF[baixo]} to {al:.0f}: a {pr / al:.0f}-fold gap "
        "that measures access, not prevalence.",
        f"Source: {FONTE_SIA}, SIGTAP group 06.04; IBGE population estimates {ULTIMO_ANO_SIA}.\n"
        "State of the dispensing facility. Monthly records ÷ 12 ≈ patients on treatment in an average month "
        "(one record per drug, so patients on two drugs count twice).",
        topo=0.965,
    )
    salva(fig, "rwd-specialty-drugs-trend")


# --------------------------------------------------------- 3. sorotipos
def sorotipos():
    s = ler("q2_sorotipo").group_by("ano").agg(
        pl.sum("provaveis", "denv1", "denv2", "denv3", "denv4")).sort("ano")
    s = s.with_columns(tipados=pl.sum_horizontal("denv1", "denv2", "denv3", "denv4"))
    anos = s["ano"].to_list()
    fig = plt.figure(figsize=(12.4, 11.0), dpi=200, facecolor=FIG_BG)
    ax1 = fig.add_axes((0.07, 0.36, 0.86, 0.34))
    ax2 = fig.add_axes((0.07, 0.10, 0.86, 0.17))

    eixo(ax1)
    cores = {"denv1": BLUE, "denv2": TEAL, "denv3": RED, "denv4": "#8a8a84"}
    base = [0.0] * len(anos)
    for c in ("denv1", "denv2", "denv3", "denv4"):
        frac = [v / t * 100 if t else 0 for v, t in zip(s[c], s["tipados"])]
        ax1.bar(anos, frac, bottom=base, color=cores[c], width=0.74,
                edgecolor=SURFACE, linewidth=1.5, label=c.upper().replace("DENV", "DENV-"))
        base = [b + f for b, f in zip(base, frac)]
    for a, v, t in zip(anos, s["denv3"], s["tipados"]):
        if a >= 2024:
            ax1.text(a, 101.5, f"DENV-3\n{num(v / t * 100, '{:.0f}')}%", ha="center", va="bottom",
                     fontsize=10, color=RED, fontweight="bold")
    ax1.set_ylim(0, 118)
    ax1.set_yticks([0, 25, 50, 75, 100])
    ax1.set_xticks(anos)
    ax1.set_xticklabels([str(a) if a < 2026 else "2026*" for a in anos])
    ax1.legend(loc="upper left", bbox_to_anchor=(0, 1.16), ncol=4, frameon=False,
               fontsize=11, labelcolor=TXT2)
    ax1.text(1.0, 1.03, T("serotype mix among typed cases, %", "composição de sorotipos entre os casos tipados, %"), transform=ax1.transAxes,
             fontsize=12, color=TXT2, ha="right")

    eixo(ax2)
    pct = [t / p * 100 for t, p in zip(s["tipados"], s["provaveis"])]
    ax2.bar(anos, pct, color=[PALE_RED if a < 2026 else REF for a in anos], width=0.74)
    for a, v, t in zip(anos, pct, s["tipados"]):
        ax2.text(a, v + 0.2, f"{num(v, '{:.1f}')}%", ha="center", va="bottom", fontsize=9.5,
                 color=TXT2)
    ax2.set_xticks(anos)
    ax2.set_xticklabels([str(a) if a < 2026 else "2026*" for a in anos])
    ax2.set_ylim(0, max(pct) * 1.35)
    ax2.text(0.0, 1.06, T("share of probable cases with a serotype recorded", "parcela dos casos prováveis com sorotipo registrado"),
             transform=ax2.transAxes, fontsize=12, color=TXT2)
    r24 = s.filter(pl.col("ano") == 2024).row(0, named=True)
    r25 = s.filter(pl.col("ano") == 2025).row(0, named=True)
    if PT:
        moldura(
            fig,
            "O único sinal molecular no registro público",
            "Brasil, casos prováveis de dengue com sorotipo do vírus na ficha de notificação, 2014–2026",
            "O sorotipo é o único resultado de laboratório que chega à base nacional, e só para um caso em 35. "
            f"Mesmo assim ele mostra\na volta do DENV-3 depois de uma década quase ausente: {num(r24['denv3'], '{:,}')} casos tipados em 2024, "
            f"{num(r25['denv3'], '{:,}')} em 2025 ({num(r25['denv3'] / r25['tipados'] * 100, '{:.0f}')}% dos tipados),\n"
            "enquanto o DENV-2 ultrapassou o DENV-1. Quem só teve um sorotipo não tem imunidade ao recém-chegado.",
            f"Fonte: {FONTE_SINAN}.\n"
            "Caso provável = toda notificação exceto as descartadas. Sorotipo por RT-PCR ou isolamento viral, como preenchido "
            "na ficha. *2026 é parcial.",
            topo=0.965,
        )
        return salva(fig, "dengue-serotypes-2014-2026")
    moldura(
        fig,
        "The only molecular signal in the public record",
        "Brazil, dengue probable cases with a virus serotype on the notification form, 2014–2026",
        f"Serotype is the one laboratory result that reaches the national file, and only for one case in 35. "
        f"Even so it shows\nDENV-3 returning after a decade of near absence: {r24['denv3']:,} typed cases in 2024, "
        f"{r25['denv3']:,} in 2025 ({r25['denv3'] / r25['tipados']:.0%} of the mix),\n"
        "while DENV-2 overtook DENV-1. People infected with only one serotype have no immunity to the newcomer.",
        f"Source: {FONTE_SINAN}.\n"
        "Probable case = every notification except those discarded. Serotype by RT-PCR or viral isolation as filled "
        "on the form. *2026 is partial.",
        topo=0.965,
    )
    salva(fig, "dengue-serotypes-2014-2026")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for f in (ranking_ultimo_ano, crescimento, sorotipos):
        f()
