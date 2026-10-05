#!/usr/bin/env python3
"""O RWD de saúde pública do espelho: as figuras da análise em inglês
`brazil-public-real-world-data`.

Lê os CSVs de docs/pesquisa/queries/rwd_inventario/ (gerados por roda.sh, um
qN_*.sql por figura) e escreve pages/analises/img/rwd-*.png no formato das
figuras de cancer-mata-interna: matplotlib, 12,4 pol. de largura, dpi 200,
título, subtítulo, leitura e fonte dentro da figura. O exemplo da dengue reusa
dengue-deaths-by-source-2014-2024.png, de scripts/plot_dengue_rwd.py.

Cor: vermelho de destaque das análises; rampa sequencial azul de um só matiz
(#cde2fb -> #0d366b, a padrão do skill dataviz) nos mapas de calor.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl
from matplotlib.colors import LinearSegmentedColormap, LogNorm, Normalize
from matplotlib.patches import FancyBboxPatch

RAIZ = Path(__file__).resolve().parent.parent
Q = RAIZ / "docs" / "pesquisa" / "queries" / "rwd_inventario"
OUT = RAIZ / "pages" / "analises" / "img"

SURFACE, FIG_BG = "#fcfcfb", "#f7f7f5"
TXT, TXT2, TXT3 = "#111111", "#555555", "#7b7b76"
RED, BLUE = "#d1453b", "#2a78d6"
GRID, REF, VAZIO = "#e6e6e2", "#b6b6ae", "#ecece8"
SEQ = LinearSegmentedColormap.from_list(
    "azul", ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])

MS = "Ministry of Health / DATASUS"

# fonte -> (classe no vocabulário de pharma, unidade de registro)
FONTES = [
    ("SIH · admissions (AIH)", "Claims-like", "one hospital admission (public payer)"),
    ("SIH · professional services", "Claims-like", "one billed professional act in an admission"),
    ("SIA · outpatient production", "Claims-like", "one outpatient procedure line (BPA/APAC)"),
    ("SIA · psychosocial care (RAAS)", "Claims-like", "one month of community mental-health care"),
    ("SIM · deaths", "Registry", "one death certificate"),
    ("SINASC · live births", "Registry", "one live-birth declaration"),
    ("SINAN · dengue", "Surveillance", "one case report form"),
    ("SINAN · chikungunya", "Surveillance", "one case report form"),
    ("SINAN · zika", "Surveillance", "one case report form"),
    ("SINAN · yellow fever", "Surveillance", "one case report form"),
    ("SINAN · malaria (extra-Amazon)", "Surveillance", "one case report form"),
    ("SINAN · SARI/influenza", "Surveillance", "one hospitalised SARI case"),
    ("SINAN · violence", "Surveillance", "one violence notification"),
    ("SISVAN · nutrition records", "EHR-like", "one anthropometric visit in primary care"),
    ("SI-PNI · vaccination microdata", "Registry", "one vaccine dose"),
    ("SI-PNI · historical doses (aggregated)", "Aggregate", "doses by vaccine x municipality x month"),
    ("Controlled-drug sales (SNGPC)", "Dispensing", "one pharmacy sale of a controlled drug"),
    ("CNES · facilities (monthly)", "Provider file", "one facility-month"),
    ("CNES · beds (monthly)", "Provider file", "one bed type in a facility-month"),
    ("CNES · professionals (monthly)", "Provider file", "one professional link in a facility-month"),
    ("ANS · private plan enrolment", "Enrolment", "beneficiary counts by plan x municipality x month"),
    ("Vaccination coverage (municipal)", "Aggregate", "one municipality-year"),
    ("Primary care teams (municipal)", "Aggregate", "one municipality-month"),
    ("Population (MS/IBGE)", "Denominator", "population by municipality x sex x age"),
]


def ler(nome):
    return pl.read_csv(Q / f"{nome}.csv", null_values=["NULL", ""])


def eixo(ax, grid=True):
    ax.set_facecolor(SURFACE)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(colors=TXT3, labelsize=11, length=0)
    if grid:
        ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)


def moldura(fig, titulo, subtitulo, leitura, fonte, topo=0.955):
    fig.text(0.05, topo, titulo, ha="left", va="top", fontsize=23,
             fontweight="bold", color=TXT)
    fig.text(0.05, topo - 0.040, subtitulo, ha="left", va="top", fontsize=13,
             color=TXT2)
    fig.text(0.05, topo - 0.075, leitura, ha="left", va="top", fontsize=13,
             color=TXT, linespacing=1.6)
    fig.text(0.05, 0.012, fonte, ha="left", va="bottom", fontsize=9.5,
             color=TXT3, linespacing=1.6)


def salva(fig, nome):
    destino = OUT / f"{nome}.png"
    fig.savefig(destino, facecolor=fig.get_facecolor())
    plt.close(fig)
    print("ok:", destino.relative_to(RAIZ))


def compacto(n):
    for lim, suf in ((1e9, "B"), (1e6, "M"), (1e3, "k")):
        if n >= lim:
            return f"{n / lim:.1f}{suf}".replace(".0", "")
    return f"{n:,.0f}"


# ------------------------------------------------------- 1. linha do tempo
def linha_do_tempo():
    d = ler("q1_linhas_por_ano")
    sipni = Q / "q6_sipni_por_ano.csv"   # leitura remota lenta: entra quando existir
    if sipni.exists() and sipni.stat().st_size > 20:
        d = pl.concat([d, ler("q6_sipni_por_ano")], how="vertical_relaxed")
    d = d.filter(pl.col("ano").is_between(1994, 2026))
    fontes = [f for f in FONTES if f[0] in set(d["fonte"].to_list())]
    anos = list(range(1994, 2027))
    fig = plt.figure(figsize=(12.4, 13.6), dpi=200, facecolor=FIG_BG)
    ax = fig.add_axes((0.30, 0.125, 0.44, 0.68))
    eixo(ax, grid=False)
    norm = LogNorm(vmin=1e3, vmax=2e9)
    for i, (nome, classe, unidade) in enumerate(fontes):
        s = d.filter(pl.col("fonte") == nome)
        mapa = dict(zip(s["ano"].to_list(), s["linhas"].to_list()))
        for a in anos:
            v = mapa.get(a)
            cor = SEQ(norm(max(v, 1e3))) if v else VAZIO
            ax.add_patch(plt.Rectangle((a - 0.5, i - 0.42), 1, 0.84, color=cor,
                                       lw=0))
        tot = s["linhas"].sum()
        anos_txt = str(min(mapa)) if min(mapa) == max(mapa) else f"{min(mapa)}–{max(mapa)}"
        ax.text(2027.0, i, f"{compacto(tot)} rows · {anos_txt}",
                va="center", fontsize=9.5, color=TXT2)
        ax.text(2027.0, i + 0.36, unidade, va="center", fontsize=7.8, color=TXT3)
    ax.set_xlim(1993.5, 2026.5)
    ax.set_ylim(len(fontes) - 0.5, -0.5)
    ax.set_yticks(range(len(fontes)))
    ax.set_yticklabels([f"{n}  [{c}]" for n, c, _ in fontes], fontsize=10,
                       color=TXT2)
    ax.set_xticks([1995, 2000, 2005, 2010, 2015, 2020, 2025])
    # barra de cor
    cax = fig.add_axes((0.30, 0.078, 0.30, 0.010))
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=SEQ), cax=cax,
                      orientation="horizontal")
    cb.outline.set_visible(False)
    cb.set_ticks([1e3, 1e5, 1e7, 1e9])
    cb.set_ticklabels(["1k", "100k", "10M", "1B rows a year"])
    cax.tick_params(labelsize=9.5, colors=TXT3, length=0)
    moldura(
        fig,
        f"Thirty years of public health data, in {len(fontes)} tables",
        "Rows per year in each health source held in this copy; its class in pharma vocabulary in brackets",
        "Death and birth registries reach back to the 1990s; hospital and outpatient billing to 2008–09. Billing\n"
        "is the bulk — 6.2 billion outpatient lines, 2.4 billion professional acts. Each source stops at a different\n"
        "year: deaths at 2022, births at 2023, hospital billing at mid-2025. Grey = no data in this copy.",
        f"Sources: {MS} (SIH, SIA, SIM, SINASC, SINAN, SISVAN, SI-PNI, CNES); ANS; Anvisa (SNGPC); IBGE.\n"
        "Rows are records as published, not people. SI-PNI read from a public third-party mirror of the official files.",
    )
    salva(fig, "rwd-coverage-timeline")


# ------------------------------------------------------------ 2. ligação
def ligacao():
    lg = ler("q7_ligacao")
    pct = {r["fonte"]: r for r in lg.iter_rows(named=True)}
    # fonte, rótulo, tempo, armadilha. Células de casamento vêm de q7_ligacao.csv;
    # None = a chave não existe na fonte; "agg" = existe, mas a fonte é agregada
    linhas = [
        ("SIH", "SIH · hospital admissions", "admission date", "ICD sits in a 3-character OR a 4-character field,\nnever both; 6-digit municipality; sex as 'Feminino'"),
        ("SIA", "SIA · outpatient (individual)", "month of care", "residence hides in a field labelled as a patient ID;\n'parda' = 3 here, 4 elsewhere"),
        ("SIM", "SIM · deaths", "date of death", "CNES stored as '2000733.0'; race as '4.0';\nhome deaths have no facility"),
        ("SINASC", "SINASC · live births", "date of birth", "sex coded 1/2, not M/F"),
        ("SINAN dengue", "SINAN · dengue", "symptom onset, epi week", "classification codes padded with a space\nfrom 2014; no discarded cases from 2022"),
        ("SISVAN", "SISVAN · primary-care anthropometry", "visit date", "'amarela' (East Asian) at 16% — implausible"),
        ("CNES", "CNES · facilities, beds, staff", "month", "the reference list for every facility code"),
        ("ANS", "ANS · private plan enrolment", "month", "several data loads per month: keep the latest"),
    ]
    cols = [("municipio_casa", "Municipality\n(IBGE code)"), ("cnes_casa", "Facility\n(CNES code)"),
            ("cid_casa", "Diagnosis\n(ICD-10)"), (None, "Patient ID")]
    fig = plt.figure(figsize=(12.4, 10.6), dpi=200, facecolor=FIG_BG)
    ax = fig.add_axes((0.25, 0.10, 0.40, 0.60))
    ax.set_xlim(-0.5, len(cols) - 0.5)
    ax.set_ylim(len(linhas) - 0.5, -0.5)
    ax.axis("off")
    norm = Normalize(0, 1)
    for i, (k, rot, tempo, nota) in enumerate(linhas):
        for j, (c, _) in enumerate(cols):
            v = pct.get(k, {}).get(c) if c else None
            if c == "cid_casa" and k in pct and not pct[k]["cid_preenchido"]:
                v = None
            if k in ("CNES",) and c in ("municipio_casa", "cnes_casa"):
                v = "ref"
            if k == "ANS" and c == "municipio_casa":
                v = "agg"
            if isinstance(v, float):
                fc, txt, cor = SEQ(norm(v)), f"{v * 100:.0f}%", "white" if v > 0.55 else TXT
            elif v == "ref":
                fc, txt, cor = VAZIO, "reference", TXT2
            elif v == "agg":
                fc, txt, cor = VAZIO, "aggregate", TXT2
            else:
                fc, txt, cor = SURFACE, "none" if c is None else "—", RED if c is None else TXT3
            ax.add_patch(FancyBboxPatch((j - 0.45, i - 0.40), 0.90, 0.80,
                                        boxstyle="round,pad=0,rounding_size=0.08",
                                        fc=fc, ec=GRID if fc == SURFACE else "none", lw=1))
            ax.text(j, i, txt, ha="center", va="center", fontsize=11.5, color=cor,
                    fontweight="bold" if c is None or (isinstance(v, float) and v < 0.95) else "normal")
        fig.text(0.245, 0.70 - (i + 0.5) * 0.60 / len(linhas) + 0.008, rot, ha="right",
                 va="center", fontsize=10.5, color=TXT)
        fig.text(0.245, 0.70 - (i + 0.5) * 0.60 / len(linhas) - 0.014, tempo, ha="right",
                 va="center", fontsize=8.8, color=TXT3)
        fig.text(0.665, 0.70 - (i + 0.5) * 0.60 / len(linhas), nota, ha="left",
                 va="center", fontsize=9.3, color=TXT2, linespacing=1.35)
    for j, (_, t) in enumerate(cols):
        ax.text(j, -0.62, t, ha="center", va="bottom", fontsize=11, color=TXT2)
    fig.text(0.665, 0.715, "Coding traps found on the way", fontsize=11, color=TXT,
             fontweight="bold", va="bottom")
    fig.text(0.245, 0.715, "time key", fontsize=9.5, color=TXT3, ha="right", va="bottom")
    moldura(
        fig,
        "No patient ID: the systems meet on place and facility",
        "Share of 2022 records whose key matches the official reference list, by source",
        "Every source carries the IBGE municipality code, and all but death certificates carry a valid facility code\n"
        "in 98–100% of records. None carries a patient identifier, so linkage is ecological (place x time) or\n"
        "facility-level, never person-level. The same concept is coded differently across systems, without errors.",
        f"Sources: {MS}, 2022 (SIA individual records and SISVAN: June 2022); ANS; IBGE municipality directory; official ICD-10\n"
        "table. Diagnosis = valid 3- or 4-character ICD-10 code; the SIA share is low because most outpatient records carry none.",
    )
    salva(fig, "rwd-linkage-map")


# --------------------------------------------------------- 3. completude
def completude():
    d = ler("q3_completude")
    campos = [("residencia", "municipality\nof residence"), ("data_evento", "event date"),
              ("idade", "age"), ("sexo", "sex"), ("raca", "race/colour"),
              ("cid", "ICD-10\ndiagnosis")]
    fontes = d["fonte"].to_list()
    fig = plt.figure(figsize=(12.4, 9.6), dpi=200, facecolor=FIG_BG)
    ax = fig.add_axes((0.30, 0.12, 0.66, 0.58))
    eixo(ax, grid=False)
    norm = Normalize(0, 1)
    for i, r in enumerate(d.iter_rows(named=True)):
        for j, (c, _) in enumerate(campos):
            v = r[c]
            if v is None:
                ax.add_patch(plt.Rectangle((j - 0.47, i - 0.45), 0.94, 0.9, fc=VAZIO,
                                           hatch="///", ec="#d9d9d4", lw=0))
                ax.text(j, i, "n/a", ha="center", va="center", fontsize=10, color=TXT3)
                continue
            ax.add_patch(plt.Rectangle((j - 0.47, i - 0.45), 0.94, 0.9,
                                       fc=SEQ(norm(v)), lw=0))
            cor = "white" if v > 0.55 else TXT
            ax.text(j, i, f"{v * 100:.0f}%", ha="center", va="center", fontsize=11.5,
                    color=cor, fontweight="bold" if v < 0.9 else "normal")
    ax.set_xlim(-0.5, len(campos) - 0.5)
    ax.set_ylim(len(fontes) - 0.5, -0.5)
    ax.set_xticks(range(len(campos)))
    ax.set_xticklabels([t for _, t in campos], fontsize=11, color=TXT2)
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(fontes)))
    ax.set_yticklabels([f"{f}\n{n:,.0f} records" for f, n in zip(fontes, d["n"].to_list())],
                       fontsize=10.5, color=TXT2)
    moldura(
        fig,
        "Where, when, who, what: how complete the key fields are",
        "Share of 2022 records with a usable value (not blank, not 'unknown'); n/a = the field does not exist in that source",
        "Place, date, age and sex are close to complete everywhere, with one exception: sex is empty in every SARI\n"
        "record. Race/colour is the weak field (75–85% in most files). Only one individual outpatient record in\n"
        "three carries a diagnosis, and 6% of death certificates name no real cause (ICD-10 chapter R, counted as missing).",
        f"Source: {MS}: SIH, SIA (individual records — BPA-I, APAC, RAAS — June 2022), SIM, SINASC, SINAN, SISVAN.\n"
        "Age for SINASC is the mother's; for SARI, date of birth. SIM diagnosis = underlying cause outside chapter R (ill-defined).",
    )
    salva(fig, "rwd-completeness-2022")


# ---------------------------------------------------- 4. mal definidas
def mal_definidas():
    d = ler("q4_mal_definidas").with_columns(p=pl.col("mal_definidas") / pl.col("obitos"))
    ordem = (d.filter(pl.col("ano") == 2022).sort("p", descending=True)["sigla_uf"].to_list())
    anos = sorted(d["ano"].unique().to_list())
    nac = d.group_by("ano").agg(pl.col("obitos").sum(), pl.col("mal_definidas").sum()).sort("ano")
    fig = plt.figure(figsize=(12.4, 13.0), dpi=200, facecolor=FIG_BG)
    ax = fig.add_axes((0.08, 0.10, 0.80, 0.56))
    eixo(ax, grid=False)
    norm = Normalize(0, 0.35)
    for i, uf in enumerate(ordem):
        s = d.filter(pl.col("sigla_uf") == uf)
        for a, v in zip(s["ano"].to_list(), s["p"].to_list()):
            ax.add_patch(plt.Rectangle((a - 0.5, i - 0.5), 1, 1, fc=SEQ(norm(v)), ec=SURFACE, lw=0.6))
        fim = s.filter(pl.col("ano") == 2022)["p"][0]
        ax.text(2022.9, i, f"{fim * 100:.1f}%", va="center", fontsize=9.5, color=TXT2)
    ax.set_xlim(1995.5, 2022.5)
    ax.set_ylim(len(ordem) - 0.5, -0.5)
    ax.set_yticks(range(len(ordem)))
    ax.set_yticklabels(ordem, fontsize=10, color=TXT2)
    ax.set_xticks([1996, 2000, 2005, 2010, 2015, 2020, 2022])
    ax.text(2023.0, -1.1, "2022", fontsize=9.5, color=TXT3)
    # série nacional acima do mapa
    ax2 = fig.add_axes((0.08, 0.69, 0.80, 0.10))
    eixo(ax2)
    ax2.plot(nac["ano"].to_list(), (nac["mal_definidas"] / nac["obitos"] * 100).to_list(),
             color=RED, lw=2, marker="o", ms=5, markeredgecolor=SURFACE)
    ax2.set_xlim(1995.5, 2022.5)
    ax2.set_ylim(0, 18)
    ax2.set_xticks([])
    ax2.set_yticks([0, 5, 10, 15])
    ax2.set_yticklabels(["0", "5", "10", "15%"])
    ax2.text(1996, 16.8, "Brazil", fontsize=10.5, color=TXT, fontweight="bold", va="top")
    cax = fig.add_axes((0.08, 0.055, 0.30, 0.012))
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=SEQ), cax=cax, orientation="horizontal")
    cb.outline.set_visible(False)
    cb.set_ticks([0, 0.1, 0.2, 0.3])
    cb.set_ticklabels(["0%", "10%", "20%", "30% of deaths ill-defined"])
    cax.tick_params(labelsize=9.5, colors=TXT3, length=0)
    moldura(
        fig,
        "Deaths without a cause: 15% in 1996, still 6% in 2022",
        "Share of deaths with an ill-defined underlying cause (ICD-10 R00–R99), by state of residence, 1996–2022",
        "The national share fell from 15.1% to 6.1%, mostly between 2004 and 2007, as the North and Northeast built\n"
        "death-investigation services. Rio de Janeiro barely moved (9.6% to 9.4%) and is now among the worst. Any\n"
        "cause-specific mortality study that compares states or decades has to adjust for this, or it measures coding.",
        f"Source: {MS}: Mortality Information System (SIM), 1996–2022. State taken from the municipality-of-residence code\n"
        "(deaths with an unknown municipality but a known state are kept). States sorted by the 2022 share.",
    )
    salva(fig, "rwd-ill-defined-deaths-1996-2022")


# --------------------------------------------------------- 5. SUS x ANS
def cobertura_privada():
    d = ler("q5_ans_cobertura_uf")
    a = d.filter(pl.col("ano") == 2024).sort("cobertura")
    nac = d.group_by("ano").agg(pl.col("beneficiarios").sum(), pl.col("populacao").sum()).sort("ano")
    fig = plt.figure(figsize=(12.4, 11.8), dpi=200, facecolor=FIG_BG)
    ax = fig.add_axes((0.08, 0.10, 0.55, 0.64))
    eixo(ax, grid=False)
    ax.grid(axis="x", color=GRID, lw=0.8)
    ys = range(a.height)
    vals = [v * 100 for v in a["cobertura"].to_list()]
    ax.barh(list(ys), vals, height=0.72, color=RED, edgecolor=SURFACE, lw=2)
    ax.barh(list(ys), [100 - v for v in vals], left=vals, height=0.72, color="#f1d6d3",
            edgecolor=SURFACE, lw=2)
    for y, v in zip(ys, vals):
        ax.text(v + 1, y, f"{v:.0f}%", va="center", fontsize=9.5, color=TXT, fontweight="bold")
    ax.set_yticks(list(ys))
    ax.set_yticklabels(a["sigla_uf"].to_list(), fontsize=10, color=TXT2)
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0", "25", "50", "75", "100%"])
    ax.text(0, a.height + 0.1, "private medical plan", fontsize=10.5, color=RED, fontweight="bold")
    ax.text(100, a.height + 0.1, "SUS only", fontsize=10.5, color=TXT2, ha="right")
    ax.set_ylim(-0.6, a.height + 0.9)
    ax2 = fig.add_axes((0.71, 0.48, 0.25, 0.26))
    eixo(ax2)
    ax2.plot(nac["ano"].to_list(), (nac["beneficiarios"] / 1e6).to_list(), color=RED, lw=2,
             marker="o", ms=6, markeredgecolor=SURFACE)
    ax2.set_ylim(0, 60)
    ax2.set_xticks([2014, 2019, 2024])
    ax2.text(0, 1.05, "Brazil, millions with a plan (Dec.)", transform=ax2.transAxes,
             fontsize=10.5, color=TXT, fontweight="bold")
    moldura(
        fig,
        "The public billing data sees everyone — except one in four",
        "Share of residents with a private medical plan, by state, December 2024",
        "SUS billing (SIH, SIA) records only care paid by the public system. Brazilians with private plans are still\n"
        "in the death, birth and notification registries, but their hospital stays are invisible. The blind spot runs from\n"
        "4% of residents in Roraima to 40% in São Paulo — so the bias in any hospital-based estimate differs by state.",
        "Source: National Supplementary Health Agency (ANS), active beneficiaries of medical-hospital plans, December, latest data load;\n"
        "population: IBGE. Dental-only plans excluded. 2022–2023 denominators are the 2022 Census.",
    )
    salva(fig, "rwd-private-coverage-2024")


# ------------------------------------------------- 6. mortalidade infantil
def mortalidade_infantil():
    d = ler("q8_mortalidade_infantil")
    nac = (d.group_by("ano").agg(pl.col("nascidos_vivos", "obitos_infantis", "obitos_neonatais").sum())
           .sort("ano").with_columns(tmi=pl.col("obitos_infantis") / pl.col("nascidos_vivos") * 1e3,
                                     neo=pl.col("obitos_neonatais") / pl.col("nascidos_vivos") * 1e3))
    uf = (d.filter(pl.col("ano") == 2022)
          .with_columns(t=pl.col("obitos_infantis") / pl.col("nascidos_vivos") * 1e3).sort("t"))
    fig = plt.figure(figsize=(12.4, 10.6), dpi=200, facecolor=FIG_BG)
    ax = fig.add_axes((0.07, 0.12, 0.50, 0.56))
    eixo(ax)
    for col, cor, rot, mk in (("tmi", RED, "infant\n(under 1 year)", "o"),
                              ("neo", BLUE, "neonatal\n(under 28 days)", "s")):
        ax.plot(nac["ano"].to_list(), nac[col].to_list(), color=cor, lw=2, marker=mk, ms=6,
                markeredgecolor=SURFACE)
        ax.text(2022.6, nac[col].to_list()[-1], rot, color=TXT2, fontsize=10.5, va="center")
    ax.set_ylim(0, 30)
    ax.set_xlim(1995, 2027)
    ax.set_xticks([1996, 2002, 2008, 2014, 2022])
    ax.set_ylabel("deaths per 1,000 live births", fontsize=11.5, color=TXT2)
    ax.text(0, 1.04, "Brazil", transform=ax.transAxes, fontsize=13, fontweight="bold", color=TXT)
    ax2 = fig.add_axes((0.67, 0.12, 0.29, 0.56))
    eixo(ax2, grid=False)
    ax2.grid(axis="x", color=GRID, lw=0.8)
    ys = list(range(uf.height))
    for y, v in zip(ys, uf["t"].to_list()):
        ax2.plot([0, v], [y, y], color=GRID, lw=2, zorder=1)
        ax2.scatter([v], [y], s=55, color=RED, edgecolors=SURFACE, linewidths=1.3, zorder=3)
        ax2.text(v + 0.4, y, f"{v:.1f}", va="center", fontsize=9, color=TXT2)
    ax2.set_yticks(ys)
    ax2.set_yticklabels(uf["sigla_uf"].to_list(), fontsize=9.5, color=TXT2)
    ax2.set_xlim(0, 20)
    ax2.set_ylim(-0.7, uf.height - 0.3)
    ax2.text(0, 1.04, "States, 2022", transform=ax2.transAxes, fontsize=13, fontweight="bold", color=TXT)
    t22 = nac.filter(pl.col("ano") == 2022).row(0, named=True)
    t96 = nac.filter(pl.col("ano") == 1996).row(0, named=True)
    moldura(
        fig,
        "Infant mortality from two registries, no shared ID",
        "Deaths under one year (death certificates) divided by live births (birth declarations), by year and state of residence",
        f"The direct ratio fell from {t96['tmi']:.1f} to {t22['tmi']:.1f} per 1,000 between 1996 and 2022. Neonatal deaths, which depend on hospital\n"
        "care, fell by about half and are now two thirds of the total. The state gap is still almost twofold. Where registration is\n"
        "weaker the direct ratio undercounts, which is why official estimates for the North and Northeast are corrected upward.",
        f"Sources: {MS}: SIM and SINASC, 1996–2022, linked by state of residence and year. Records with impossible ages\n"
        "(negative; 1,006 in 2022) are excluded. Direct calculation, no correction for under-registration.",
    )
    salva(fig, "rwd-infant-mortality-1996-2022")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for f in (linha_do_tempo, ligacao, completude, mal_definidas, cobertura_privada,
              mortalidade_infantil):
        f()
