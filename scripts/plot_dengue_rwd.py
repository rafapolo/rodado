#!/usr/bin/env python3
"""Dengue no Brasil, da notificação ao óbito: as sete figuras da análise RWD em inglês.

Lê os CSVs que `docs/pesquisa/queries/dengue_rwd/roda.sh` grava ao lado de cada
qN_*.sql (SINAN dengue, SIH, SIM, população do IBGE, Atlas Esgotos, PIB municipal)
e escreve PNGs em pages/analises/img/dengue-*.png, no mesmo formato das figuras de
cancer-mata-interna: matplotlib, 12,4 pol. de largura, dpi 200, título, subtítulo,
leitura e fonte dentro da própria figura.

Paleta: o vermelho de destaque das análises e, quando há mais de uma série,
azul e verde-azulado — os três passam o validador de CVD em todos os pares
(skill dataviz, `validate_palette.js --pairs all`, superfície #fcfcfb).

Supressão: célula com menos de 10 óbitos não vira taxa (aparece como "n<10").
"""
from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl
from datetime import date, timedelta

RAIZ = Path(__file__).resolve().parent.parent
Q = RAIZ / "docs" / "pesquisa" / "queries" / "dengue_rwd"
OUT = RAIZ / "pages" / "analises" / "img"

SURFACE, FIG_BG = "#fcfcfb", "#f7f7f5"
TXT, TXT2, TXT3 = "#111111", "#555555", "#7b7b76"
RED, BLUE, TEAL = "#d1453b", "#2a78d6", "#1f9e89"
GRID, REF = "#e6e6e2", "#b6b6ae"
MIN_N = 10

FONTE_SINAN = "Ministry of Health / DATASUS: Notifiable Diseases Information System (SINAN), dengue"
FONTE_SIH = "Hospital Information System (SIH/SUS, principal diagnosis ICD-10 A90–A91)"
FONTE_SIM = "Mortality Information System (SIM, underlying cause A90–A91)"


def ler(nome):
    return pl.read_csv(Q / f"{nome}.csv", null_values=["NULL", ""])


def fmt(v, casas=0):
    return f"{v:,.{casas}f}"


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


# ------------------------------------------------------------------ 1. funil
def funil():
    d = ler("q1_funil_nacional")
    anos = d["ano"].to_list()
    fig = plt.figure(figsize=(12.4, 12.4), dpi=200, facecolor=FIG_BG)
    paineis = [
        ("provaveis", 1e6, "probable cases (millions)", "{:.1f}M"),
        ("sih_internacoes", 1e3, "SUS hospital admissions (thousands)", "{:.0f}k"),
        ("sinan_obitos", 1, "deaths from dengue (confirmed by surveillance)", "{:,.0f}"),
    ]
    altura, base = 0.18, 0.10
    for i, (col, div, rot, molde) in enumerate(paineis):
        ax = fig.add_axes((0.07, base + (2 - i) * (altura + 0.045), 0.9, altura))
        eixo(ax)
        vals = [v / div for v in d[col].to_list()]
        cores = [RED if a == 2024 else "#e8a29c" for a in anos]
        ax.bar(anos, vals, color=cores, width=0.72, edgecolor=SURFACE, linewidth=2)
        ax.set_xticks(anos)
        ax.set_xticklabels([str(a) for a in anos] if i == 2 else [])
        ax.set_ylim(0, max(vals) * 1.22)
        ax.text(0.0, 1.03, rot, transform=ax.transAxes, fontsize=12.5,
                color=TXT2, va="bottom")
        for a, v in zip(anos, vals):
            if a in (2015, 2019, 2024):
                ax.text(a, v + max(vals) * 0.03, molde.format(v), ha="center",
                        va="bottom", fontsize=11,
                        color=TXT if a == 2024 else TXT2,
                        fontweight="bold" if a == 2024 else "normal")
    r24 = d.filter(pl.col("ano") == 2024).row(0, named=True)
    moldura(
        fig,
        "2024 broke every step of the dengue funnel at once",
        "Brazil, 2014–2024: notified probable cases, SUS hospital admissions and deaths, by year",
        f"In 2024 surveillance recorded {fmt(r24['provaveis'])} probable cases — 3.8 times the previous peak (2015).\n"
        f"Public hospitals admitted {fmt(r24['sih_internacoes'])} patients and {fmt(r24['sinan_obitos'])} people died: "
        f"about 1 admission per 40 cases\nand 1 death per 1,000 cases. Deaths grew faster than cases — 6.2 times 2015, against 3.8.",
        f"Source: {FONTE_SINAN}; {FONTE_SIH}.\n"
        "Probable case = every notification except those discarded. Admissions counted by date of admission, episodes not patients, SUS only.",
        topo=0.965,
    )
    salva(fig, "dengue-funnel-2014-2024")


# ------------------------------------------------------------ 2. semanal
def semanal():
    d = ler("q5_semana").with_columns(
        a=pl.col("semana_sintomas").str.slice(0, 4).cast(pl.Int32, strict=False),
        w=pl.col("semana_sintomas").str.slice(5, 2).cast(pl.Int32, strict=False),
    ).filter(pl.col("a").is_between(2014, 2025) & pl.col("w").is_between(1, 53))
    d = d.with_columns(
        dia=pl.struct("a", "w").map_elements(
            lambda r: date(r["a"], 1, 1) + timedelta(weeks=r["w"] - 1),
            return_dtype=pl.Date)).sort("dia")
    fig = plt.figure(figsize=(12.4, 8.6), dpi=200, facecolor=FIG_BG)
    ax = fig.add_axes((0.07, 0.14, 0.9, 0.60))
    eixo(ax)
    ax.fill_between(d["dia"].to_list(), [v / 1e3 for v in d["provaveis"]],
                    color=RED, alpha=0.18, lw=0)
    ax.plot(d["dia"].to_list(), [v / 1e3 for v in d["provaveis"]], color=RED, lw=2)
    ax.set_ylabel("probable cases per week (thousands)", fontsize=12, color=TXT2)
    picos = (d.with_columns(pl.col("dia").dt.year().alias("y"))
             .group_by("y").agg(pl.all().sort_by("provaveis").last())
             .filter(pl.col("y").is_in([2016, 2019, 2023, 2024, 2025])))
    for r in picos.iter_rows(named=True):
        ax.annotate(f"{r['y']}: {r['provaveis'] / 1e3:,.0f}k\n(week {r['w']})",
                    (r["dia"], r["provaveis"] / 1e3), xytext=(0, 10),
                    textcoords="offset points", ha="center", va="bottom",
                    fontsize=10.5, color=TXT if r["y"] == 2024 else TXT2)
    ax.set_ylim(0, d["provaveis"].max() / 1e3 * 1.18)
    moldura(
        fig,
        "Dengue is a summer disease — until it isn't",
        "Brazil, probable cases by week of symptom onset, 2014–2025",
        "Every year peaks between epidemiological weeks 8 and 19 (late February to mid-May), after the summer rains.\n"
        "The 2024 peak, in week 12, was four times taller than any earlier year: 424,000 new cases in seven days.",
        f"Source: {FONTE_SINAN}. Week = epidemiological week of symptom onset.\n"
        "Recent weeks are subject to reporting delay; 2025 is still being closed out by surveillance.",
    )
    salva(fig, "dengue-weekly-2014-2025")


# --------------------------------------------------------------- 3. por UF
def por_uf():
    d = ler("q2_uf").with_columns(
        inc=pl.col("provaveis") / pl.col("populacao_media") / 11 * 1e5,
        cfr=pl.when(pl.col("sinan_obitos") >= MIN_N)
        .then(pl.col("sinan_obitos") / pl.col("provaveis") * 1e4)
        .otherwise(None),
    ).sort("inc")
    fig = plt.figure(figsize=(12.4, 13.0), dpi=200, facecolor=FIG_BG)
    ax1 = fig.add_axes((0.10, 0.10, 0.40, 0.68))
    ax2 = fig.add_axes((0.58, 0.10, 0.38, 0.68))
    ys = list(range(d.height))
    ufs = d["sigla_uf"].to_list()
    for ax in (ax1, ax2):
        eixo(ax, grid_y=False)
        ax.grid(axis="x", color=GRID, lw=0.8)
        ax.set_yticks(ys)
        ax.set_ylim(-0.7, d.height - 0.3)
    ax1.set_yticklabels(ufs, fontsize=11, color=TXT2)
    ax2.set_yticklabels([])
    cores = [RED if u in ("GO", "DF", "MG", "PR", "SP") else "#e8a29c" for u in ufs]
    ax1.barh(ys, d["inc"].to_list(), color=cores, height=0.7,
             edgecolor=SURFACE, linewidth=2)
    for y, v, u in zip(ys, d["inc"].to_list(), ufs):
        lab = f"{v:,.0f}" + ("  · gap 2021–24" if u == "ES" else "")
        ax1.text(v + 25, y, lab, va="center", fontsize=9.5, color=TXT2)
    ax1.set_xlabel("probable cases per 100,000 people per year", fontsize=11.5,
                   color=TXT2, labelpad=8)
    for y, v, u in zip(ys, d["cfr"].to_list(), ufs):
        if v is None:
            ax2.text(0.3, y, "n<10 deaths", va="center", fontsize=9.5, color=TXT3)
            continue
        ax2.plot([0, v], [y, y], color=GRID, lw=2, zorder=1)
        ax2.scatter([v], [y], s=70, color=RED, edgecolors=SURFACE, linewidths=1.5,
                    zorder=3)
        ax2.text(v + 0.5, y, f"{v:.1f}", va="center", fontsize=9.5, color=TXT2)
    nac = d["sinan_obitos"].sum() / d["provaveis"].sum() * 1e4
    ax2.axvline(nac, color=REF, lw=1.1, ls=(0, (5, 3.5)))
    ax2.text(nac + 0.3, -0.55, f"Brazil {nac:.1f}", fontsize=10,
             color=TXT3, va="center")
    ax2.set_xlabel("deaths per 10,000 probable cases", fontsize=11.5, color=TXT2,
                   labelpad=8)
    moldura(
        fig,
        "Where dengue strikes most is not where it kills most",
        "States of residence, 2014–2024 pooled: incidence (left) and case fatality (right)",
        "The five Centre-South states in red concentrate the epidemics: Goiás notified 1,850 cases per 100,000 a year,\n"
        "the Federal District 1,580. Fatality ranks differently — Sergipe, Rio Grande do Sul and Maranhão see few cases but\n"
        "lose more patients per case than São Paulo. Espírito Santo is low because it is missing, not because it is safe.",
        f"Source: {FONTE_SINAN}; population: IBGE municipal estimates and Census 2022.\n"
        "Rates use the 2014–2024 mean population. Cells with fewer than 10 deaths are suppressed. Espírito Santo reported\n"
        "in a state system between 2021 and 2024 and is nearly absent from the national file in those years.",
    )
    salva(fig, "dengue-states-2014-2024")


# ----------------------------------------------------- 4. óbitos por fonte
def obitos_fontes():
    d = ler("q1_funil_nacional")
    anos = d["ano"].to_list()
    fig = plt.figure(figsize=(12.4, 8.8), dpi=200, facecolor=FIG_BG)
    ax = fig.add_axes((0.07, 0.15, 0.80, 0.57))
    eixo(ax)
    series = [
        ("sinan_obitos", RED, "Surveillance (SINAN):\nconfirmed dengue deaths", "o"),
        ("sim_obitos", BLUE, "Death certificates (SIM):\nunderlying cause dengue", "s"),
        ("sih_obitos", TEAL, "SUS hospitals (SIH):\nin-hospital deaths", "D"),
    ]
    for col, cor, rot, mk in series:
        pts = [(a, v) for a, v in zip(anos, d[col].to_list()) if v is not None]
        xs, ys = zip(*pts)
        ax.plot(xs, ys, color=cor, lw=2, marker=mk, ms=8,
                markeredgecolor=SURFACE, markeredgewidth=1.5)
        if col == "sim_obitos":    # acima do ponto, para não cruzar a linha do SINAN
            ax.text(xs[-1], ys[-1] * 1.18, rot, color=TXT2, fontsize=10.5,
                    ha="center", va="bottom", linespacing=1.3)
        else:
            ax.text(xs[-1] + 0.25, ys[-1], rot, color=TXT2, fontsize=10.5,
                    va="center", linespacing=1.3)
    ax.set_yscale("log")
    ax.set_yticks([100, 200, 500, 1000, 2000, 5000])
    ax.set_yticklabels(["100", "200", "500", "1,000", "2,000", "5,000"])
    ax.minorticks_off()
    ax.set_xticks(anos)
    ax.set_xlim(2013.6, 2026.2)
    ax.set_ylabel("deaths (log scale)", fontsize=12, color=TXT2)
    r22 = d.filter(pl.col("ano") == 2022).row(0, named=True)
    moldura(
        fig,
        "Three systems, three death counts for the same disease",
        "Brazil, deaths from dengue as recorded by each national system, 2014–2024",
        f"In 2022 surveillance closed {fmt(r22['sinan_obitos'])} cases as deaths, death certificates named dengue\n"
        f"{fmt(r22['sim_obitos'])} times, and SUS hospitals recorded {fmt(r22['sih_obitos'])} in-hospital deaths. "
        "None of them is wrong: each counts a\ndifferent event, and the systems share no patient identifier to reconcile them.",
        f"Sources: {FONTE_SINAN} (outcome = death from the disease);\n"
        f"{FONTE_SIM}; {FONTE_SIH}, deaths during the admission.\n"
        "Death certificate microdata are available up to 2022.",
    )
    salva(fig, "dengue-deaths-by-source-2014-2024")


# ------------------------------------------------ 5. idade x comorbidade
def comorbidade():
    d = ler("q6_risco_individual")
    faixas = d["faixa"].to_list()
    fig = plt.figure(figsize=(12.4, 9.4), dpi=200, facecolor=FIG_BG)
    paineis = [("diab", "sem_diab", "Diabetes"), ("has", "sem_has", "Hypertension")]
    for i, (com, sem, nome) in enumerate(paineis):
        ax = fig.add_axes((0.07 + i * 0.47, 0.19, 0.42, 0.52))
        eixo(ax)
        for chave, cor, rot, mk in ((com, RED, f"with {nome.lower()}", "o"),
                                    (sem, BLUE, f"without", "s")):
            xs, ys = [], []
            for j, r in enumerate(d.iter_rows(named=True)):
                if r[f"obitos_{chave}"] >= MIN_N:
                    xs.append(j)
                    ys.append(r[f"obitos_{chave}"] / r[f"casos_{chave}"] * 1e3)
            ax.plot(xs, ys, color=cor, lw=2, marker=mk, ms=8,
                    markeredgecolor=SURFACE, markeredgewidth=1.5)
            ax.text(xs[-1] + 0.12, ys[-1], rot, color=TXT2, fontsize=10.5,
                    va="center")
        ax.text(0, 0.02, "n<10", transform=ax.get_xaxis_transform(),
                fontsize=9, color=TXT3, ha="center")
        ax.set_yscale("log")
        ax.set_yticks([0.1, 0.3, 1, 3, 10, 30])
        ax.set_yticklabels(["0.1", "0.3", "1", "3", "10", "30"])
        ax.minorticks_off()
        ax.set_ylim(0.12, 40)
        ax.set_xticks(range(len(faixas)))
        ax.set_xticklabels(faixas)
        ax.set_xlim(-0.3, len(faixas) + 0.6)
        ax.text(0, 1.03, nome, transform=ax.transAxes, fontsize=13.5,
                fontweight="bold", color=TXT)
        if i == 0:
            ax.set_ylabel("deaths per 1,000 probable cases (log)", fontsize=11.5,
                          color=TXT2)
        ax.set_xlabel("age group", fontsize=11.5, color=TXT2)
    r = d.filter(pl.col("faixa") == "60-79").row(0, named=True)
    rd = (r["obitos_diab"] / r["casos_diab"]) / (r["obitos_sem_diab"] / r["casos_sem_diab"])
    moldura(
        fig,
        "Age sets the risk; diabetes and hypertension multiply it",
        "Brazil 2024, case fatality of probable dengue cases by age group and recorded comorbidity",
        "Fatality climbs more than seventyfold from children to people over 80. Within the same age group,\n"
        f"a recorded comorbidity still adds risk: at 60–79, diabetic patients died {rd:.1f} times as often as non-diabetic ones.",
        f"Source: {FONTE_SINAN}, 2024.\n"
        "Comorbidity field filled in 98% of 2024 records, as recorded on the notification form — which is more thoroughly filled\n"
        "for severe cases, so part of the gap may be recording, not biology.\n"
        "Crude rates within each age band; no further adjustment. Cells with fewer than 10 deaths suppressed.",
    )
    salva(fig, "dengue-age-comorbidity-2024")


# ---------------------------------------------------------------- 6. SDOH
def quintil_pop(df, var, por=None):
    """quintis ponderados por população: cada quintil tem ~1/5 das pessoas"""
    chave = [por] if por else []
    df = df.drop_nulls(var).sort(chave + [var])
    tot = pl.col("populacao_2021").sum()
    acum = pl.col("populacao_2021").cum_sum()
    if por:
        tot, acum = tot.over(por), acum.over(por)
    return df.with_columns(
        q=((acum - pl.col("populacao_2021") / 2) / tot * 5).floor().clip(0, 4)
        .cast(pl.Int8) + 1)


def sdoh():
    d = ler("q3_sdoh_municipio").filter(pl.col("sigla_uf") != "ES")
    fig = plt.figure(figsize=(12.4, 11.6), dpi=200, facecolor=FIG_BG)
    vars_ = [("pib_per_capita", "GDP per capita quintile"),
             ("esgoto_tratado", "sewage collected and treated, quintile")]
    linhas = [("inc", "probable cases per 100,000 per year"),
              ("cfr", "deaths per 10,000 probable cases")]
    for c, (var, xl) in enumerate(vars_):
        for r, (met, yl) in enumerate(linhas):
            ax = fig.add_axes((0.08 + c * 0.47, 0.15 + (1 - r) * 0.33, 0.40, 0.27))
            eixo(ax)
            for por, cor, rot, mk in ((None, BLUE, "nationwide", "s"),
                                      ("sigla_uf", RED, "within each state", "o")):
                g = (quintil_pop(d, var, por).group_by("q").agg(
                    pop=pl.col("populacao_2021").sum(), casos=pl.col("provaveis").sum(),
                    ob=pl.col("sinan_obitos").sum()).sort("q").with_columns(
                    inc=pl.col("casos") / pl.col("pop") / 11 * 1e5,
                    cfr=pl.col("ob") / pl.col("casos") * 1e4))
                ax.plot(g["q"].to_list(), g[met].to_list(), color=cor, lw=2,
                        marker=mk, ms=8, markeredgecolor=SURFACE, markeredgewidth=1.5)
                if c == 1 and r == 0:
                    ax.text(5.15, g[met].to_list()[-1], rot, color=TXT2,
                            fontsize=10, va="center")
            ax.set_xticks([1, 2, 3, 4, 5])
            ax.set_xticklabels(["1\nlowest", "2", "3", "4", "5\nhighest"] if r == 1 else [])
            ax.set_xlim(0.7, 5.3 if c == 0 else 6.6)
            ax.set_ylim(0, None)
            if c == 0:
                ax.set_ylabel(yl, fontsize=10.5, color=TXT2)
            if r == 1:
                ax.set_xlabel(xl, fontsize=11, color=TXT2)
    moldura(
        fig,
        "The obvious social gradient is mostly geography",
        "Municipalities grouped into fifths of the population by income and by sanitation; 2014–2024 pooled",
        "Nationwide, richer places notify more dengue and lose more patients per case. Compare municipalities\n"
        "within the same state and the fatality gradient by income mostly flattens — the national slope tracks which\n"
        "states had epidemics. Sanitation shows no fatality gradient at all: Aedes breeds in clean standing water.",
        f"Source: {FONTE_SINAN};\n"
        "IBGE municipal GDP and population, 2021; National Water Agency (ANA), Atlas Esgotos (2013).\n"
        "Ecological comparison — it relates places, not people. Quintiles weighted by population. Espírito Santo excluded (reporting gap).\n"
        "Crude rates, not age-standardised: richer municipalities are older, and age is the strongest driver of fatality.",
    )
    salva(fig, "dengue-sdoh-2014-2024")


# ---------------------------------------------------------- 7. qualidade
def qualidade():
    d = ler("q4_qualidade")
    es = ler("q8_es_lacuna")
    anos = d["ano"].to_list()
    fig = plt.figure(figsize=(12.4, 11.8), dpi=200, facecolor=FIG_BG)
    paineis = [
        ("pct_internacao_ignorada", "hospitalisation field blank or 'unknown'"),
        ("pct_evolucao_ignorada", "outcome blank or 'unknown'"),
        ("pct_raca_ignorada", "race/colour blank or 'unknown'"),
        ("pct_diabetes_ignorado", "diabetes field blank or 'unknown'"),
        ("pct_confirmacao_laboratorial", "confirmed by laboratory test"),
    ]
    for k, item in enumerate(paineis + [None]):
        col, rot = item if item else (None, None)
        lin, colu = divmod(k, 3)
        ax = fig.add_axes((0.07 + colu * 0.315, 0.10 + (1 - lin) * 0.335, 0.26, 0.245))
        eixo(ax)
        if col is None:
            ax.bar([a - 0.2 for a in es["ano"]], es["sinan_provaveis"], width=0.4,
                   color=RED, label="probable cases (SINAN)")
            ax.bar([a + 0.2 for a in es["ano"]], es["sih_internacoes"], width=0.4,
                   color=BLUE, label="SUS admissions (SIH)")
            ax.set_yscale("log")
            ax.set_ylim(10, 1e6)
            ax.set_yticks([10, 100, 1000, 10000, 100000])
            ax.set_yticklabels(["10", "100", "1k", "10k", "100k"])
            ax.minorticks_off()
            ax.set_xticks([2014, 2017, 2020, 2024])
            ax.legend(loc="upper right", frameon=False, fontsize=8.5,
                      labelcolor=TXT2)
            ax.text(0, 1.06, "Espírito Santo: cases vanish,\nadmissions don't",
                    transform=ax.transAxes, fontsize=11, color=TXT,
                    fontweight="bold", va="bottom")
            continue
        vals = [v * 100 for v in d[col].to_list()]
        ax.plot(anos, vals, color=RED, lw=2, marker="o", ms=6,
                markeredgecolor=SURFACE, markeredgewidth=1.2)
        ax.set_ylim(0, 105)
        ax.set_yticks([0, 25, 50, 75, 100])
        ax.set_yticklabels(["0", "25", "50", "75", "100%"])
        ax.set_xticks([2014, 2017, 2020, 2025])
        ax.text(0, 1.06, rot, transform=ax.transAxes, fontsize=11, color=TXT,
                va="bottom", fontweight="bold", wrap=True)
        ax.text(anos[-1], vals[-1] + 6, f"{vals[-1]:.0f}%", ha="center",
                fontsize=10, color=TXT2)
    moldura(
        fig,
        "Fit for purpose? What the dengue record can and cannot carry",
        "Brazil, share of probable cases with key fields filled, by year of notification, 2014–2025",
        "Comorbidity went from never recorded to almost always recorded. Hospitalisation is still unknown for\n"
        "a quarter to a third of cases, and about two in three probable cases are never confirmed by a laboratory test.\n"
        "A whole state can drop out of the national file for four years while its hospitals keep admitting patients.",
        f"Source: {FONTE_SINAN}; {FONTE_SIH}.\n"
        "'Unknown' = field empty or coded 9. Espírito Santo panel on a log scale; residents of the state by year of notification or admission.",
    )
    salva(fig, "dengue-data-quality-2014-2025")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for f in (funil, semanal, por_uf, obitos_fontes, comorbidade, sdoh, qualidade):
        f()
