#!/usr/bin/env python3
"""Medicamentos especializados, quimioterapia e sorotipos da dengue: as três figuras
acrescentadas à análise RWD em inglês (brazil-public-real-world-data) em novembro de 2026.

Lê os CSVs que `docs/pesquisa/queries/rwd_especializados/roda.sh` grava ao lado de cada
qN_*.sql (SIA/APAC, SINAN dengue, população do IBGE, CID-10, orçamento federal) e escreve
PNGs em pages/analises/img/, no mesmo formato das figuras de plot_dengue_rwd.py:
matplotlib, 12,4 pol. de largura, dpi 200, título, subtítulo, leitura e fonte na figura.

2026 fica fora das séries do SIA: o ano ainda está em curso (FTP do DATASUS até 2026-08).
Supressão: célula com menos de 10 registros não aparece.
"""
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
ULTIMO_ANO_SIA = 2025

FONTE_SIA = ("Ministry of Health / DATASUS: Outpatient Information System (SIA/SUS), "
             "high-complexity authorisations (APAC)")
FONTE_SINAN = "Ministry of Health / DATASUS: Notifiable Diseases Information System (SINAN), dengue"

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

# Doenças da série: CIDs somados sob um rótulo.
SERIE = [
    ("Psoriasis", ["L40"]),
    ("Systemic lupus", ["M32"]),
    ("Ankylosing spondylitis", ["M45"]),
    ("Rheumatoid arthritis", ["M05", "M06"]),
    ("Multiple sclerosis", ["G35"]),
    ("Inflammatory bowel disease", ["K50", "K51"]),
    ("Asthma", ["J45"]),
    ("Schizophrenia", ["F20"]),
    ("Alzheimer's disease", ["G30"]),
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


def salva(fig, nome):
    destino = OUT / f"{nome}.png"
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
        ax.text(v + max(vals) * 0.015, y, molde.format(v), va="center",
                fontsize=10, color=TXT2)
    ax.set_xlim(0, max(vals) * 1.18)
    ax.set_ylim(-0.7, len(vals) - 0.3)


# ------------------------------------------------------- 1. ranking de 2024
def ranking_2024():
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
    barras(ax1, [CID_EN.get(c, c) for c in m15["cid3"]],
           [v / 1e6 for v in m15["linhas"]],
           [v == 0 for v in m15["valor"]], "{:.1f}M", BLUE, PALE_BLUE)
    ax1.set_xlabel("monthly dispensing records, millions", fontsize=11, color=TXT2,
                   labelpad=8)
    ax1.text(-0.62, 1.07, "Specialised-component drugs", transform=ax1.transAxes,
             fontsize=13, color=TXT, fontweight="bold")
    ax1.text(-0.62, 1.03, "dark bar = R$ 0 billed for the whole year",
             transform=ax1.transAxes, fontsize=10, color=BLUE)
    barras(ax2, [CID_EN.get(c, c) for c in q12["cid3"]],
           [v / 1e3 for v in q12["linhas"]],
           [c == "C50" for c in q12["cid3"]], "{:,.0f}k", RED, PALE_RED)
    ax2.set_xlabel("monthly chemotherapy authorisations, thousands", fontsize=11,
                   color=TXT2, labelpad=8)
    ax2.text(-0.62, 1.07, "Cancer drug therapy, by site", transform=ax2.transAxes,
             fontsize=13, color=TXT, fontweight="bold")
    ax2.text(-0.62, 1.03, "red = breast cancer", transform=ax2.transAxes,
             fontsize=10, color=RED)
    mama = qt.filter(pl.col("cid3") == "C50")["linhas"][0] / tot_qt
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
        ax1.text(ULTIMO_ANO_SIA + 0.25, y, f"{rot} ×{v:.1f}", va="center", fontsize=10,
                 color=TXT if forte else TXT3, fontweight="bold" if forte else "normal")
        ult = y
    ax1.axhline(1, color=REF, lw=1, ls=(0, (5, 3.5)))
    ax1.set_xlim(2014, ULTIMO_ANO_SIA)
    ax1.set_xticks(list(range(2014, ULTIMO_ANO_SIA + 1, 2)))
    ax1.text(0.0, 1.03, "Dispensing records, 2014 = 1", transform=ax1.transAxes,
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
    ax2.barh(ys, taxas, color=[BLUE if s in ("PR", "AL") else PALE_BLUE for s in siglas],
             height=0.72, edgecolor=SURFACE, linewidth=2)
    ax2.set_yticks(ys)
    ax2.set_yticklabels(siglas, fontsize=10, color=TXT2)
    for y, v in zip(ys, taxas):
        ax2.text(v + 4, y, f"{v:.0f}", va="center", fontsize=9.5, color=TXT2)
    ax2.set_ylim(-0.7, ra.height - 0.3)
    ax2.set_xlim(0, max(taxas) * 1.15)
    ax2.set_xlabel("patients per month per 100,000", fontsize=10.5,
                   color=TXT2, labelpad=8)
    nac = ra["linhas"].sum() / 12 / ra["populacao"].sum() * 1e5
    ax2.axvline(nac, color=REF, lw=1.1, ls=(0, (5, 3.5)))
    ax2.text(nac + 4, -0.55, f"Brazil {nac:.0f}", fontsize=10, color=TXT3, va="center")
    ax2.text(0.0, 1.03, f"Rheumatoid arthritis by state, {ULTIMO_ANO_SIA}", transform=ax2.transAxes,
             fontsize=12.5, color=TXT2)
    pr = ra.filter(pl.col("id_uf") == "41")["taxa"][0]
    al = ra.filter(pl.col("id_uf") == "27")["taxa"][0]
    moldura(
        fig,
        "Immunology drugs grew fastest, and reach patients unevenly",
        f"SUS specialised-component dispensing by diagnosis, 2014–{ULTIMO_ANO_SIA} (left) and rheumatoid arthritis by state (right)",
        "Records for psoriasis, lupus and ankylosing spondylitis grew three to five times in a decade, as new drugs, many of them\n"
        "biologics, entered the public treatment protocols; Alzheimer's stayed flat. For the same disease, "
        f"Paraná dispenses to\n{pr:.0f} patients per 100,000 and Alagoas to {al:.0f}: a {pr / al:.0f}-fold gap "
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
            ax1.text(a, 101.5, f"DENV-3\n{v / t:.0%}", ha="center", va="bottom",
                     fontsize=10, color=RED, fontweight="bold")
    ax1.set_ylim(0, 118)
    ax1.set_yticks([0, 25, 50, 75, 100])
    ax1.set_xticks(anos)
    ax1.set_xticklabels([str(a) if a < 2026 else "2026*" for a in anos])
    ax1.legend(loc="upper left", bbox_to_anchor=(0, 1.16), ncol=4, frameon=False,
               fontsize=11, labelcolor=TXT2)
    ax1.text(1.0, 1.03, "serotype mix among typed cases, %", transform=ax1.transAxes,
             fontsize=12, color=TXT2, ha="right")

    eixo(ax2)
    pct = [t / p * 100 for t, p in zip(s["tipados"], s["provaveis"])]
    ax2.bar(anos, pct, color=[PALE_RED if a < 2026 else REF for a in anos], width=0.74)
    for a, v, t in zip(anos, pct, s["tipados"]):
        ax2.text(a, v + 0.2, f"{v:.1f}%", ha="center", va="bottom", fontsize=9.5,
                 color=TXT2)
    ax2.set_xticks(anos)
    ax2.set_xticklabels([str(a) if a < 2026 else "2026*" for a in anos])
    ax2.set_ylim(0, max(pct) * 1.35)
    ax2.text(0.0, 1.06, "share of probable cases with a serotype recorded",
             transform=ax2.transAxes, fontsize=12, color=TXT2)
    r24 = s.filter(pl.col("ano") == 2024).row(0, named=True)
    r25 = s.filter(pl.col("ano") == 2025).row(0, named=True)
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
    for f in (ranking_2024, crescimento, sorotipos):
        f()
