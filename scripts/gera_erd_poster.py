#!/usr/bin/env python3
"""Generate Anatomy-of-AI-style PDF poster(s) of the mirror's ERD.

Produces two posters:
  ERD-poster-domain.pdf — aggregated by domain (hub network + domain cards)
  ERD-poster-full.pdf   — full dataset listing within domains

Usage:
    python3 scripts/gera_erd_poster.py
"""

import json
import math
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Arc
from matplotlib.lines import Line2D
import numpy as np

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "schemas.json"
DST_DIR = REPO

BEELINK_HOST = "beelink"
BEELINK_DB = "~/rodado/basedosdados.duckdb"

# ── Colours (dark theme) ──────────────────────────────────────────
BG = "#0D1117"
BG2 = "#161B22"
BG3 = "#21262D"
TEXT = "#E6EDF3"
TEXT_MUTED = "#8B949E"
TEXT_DIM = "#484F58"
ACCENT = "#58A6FF"
GREEN = "#3FB950"
ORANGE = "#D29922"
RED = "#F85149"
PURPLE = "#BC8CFF"
PINK = "#DB6D9A"
TEAL = "#56D4DD"

HUB_COLORS = {
    "MUNICIPIO":        "#00B894",
    "UF":               "#00A8A8",
    "SETOR_CENSITARIO": "#55CDFF",
    "CEP":              "#74E8D4",
    "EMPRESA_CNPJ":     "#58A6FF",
    "PESSOA_CPF":       "#79C0FF",
    "ESCOLA":           "#7EE787",
    "IES":              "#56D4DD",
    "CNES":             "#D2A8FF",
    "CNAE":             "#F0883E",
    "CBO":              "#F85149",
    "CID10":            "#FFA657",
    "NCM_SH":           "#E3B341",
    "PAIS":             "#D29922",
    "ORGAO":            "#BC8CFF",
    "UNIDADE_GESTORA":  "#DB6D9A",
    "FUNCAO_PROGRAMA":  "#F778BA",
    "PARTIDO":          "#FF7B72",
}

DOMAIN_COLORS = {
    "referencia":     "#3FB950",
    "saude":          "#F85149",
    "educacao":       "#58A6FF",
    "economia":       "#D29922",
    "governo":        "#BC8CFF",
    "politica":       "#DB6D9A",
    "justica":        "#A371F7",
    "territorio":     "#56D4DD",
    "demografia":     "#F0883E",
    "internacional":  "#79C0FF",
    "outros":         "#484F58",
}

DOMAIN_NAMES = {
    "referencia":    "Diretórios e Tabelas de Referência",
    "saude":         "Saúde",
    "educacao":      "Educação e Ciência",
    "economia":      "Trabalho, Empresas e Economia",
    "governo":       "Governo, Orçamento e Compras",
    "politica":      "Política e Eleições",
    "justica":       "Justiça, Segurança e Sanções",
    "territorio":    "Território, Ambiente e Infraestrutura",
    "demografia":    "Demografia e Indicadores Sociais",
    "internacional": "Internacional, Cultura e Esporte",
    "outros":        "Outros",
}

# ── Hub definitions (same logic as gera_erd.py) ───────────────────
_NOT_A_MUNICIPALITY_KEY = re.compile(
    r"conselho|fundo|plano|programa|iptu|parceria|servico|creche|ensino|"
    r"unidade_conservacao|arranjo|articulacao|percentual|populacao_|quantidade|"
    r"investimento|despesa|desp_|tx_|pct_|subsetor|subativ|indicador|"
    r"forma_contratacao|data_publicacao|contrato_municipio|conexao|dado_municipal|"
    r"registro_|existencia|size_municipalities|comunicacao", re.I)
_MUNICIPIO_ALIASES = {"MUNIC", "ID_MUNICIP", "territory_id", "territory_name",
                      "city", "Ente"}

def _municipio_bridge(col):
    if col in _MUNICIPIO_ALIASES:
        return True
    if col.startswith("id_municipio"):
        return False
    return bool(re.search(r"munic|ibge", col, re.I)) and not _NOT_A_MUNICIPALITY_KEY.search(col)

HUBS = {
    "MUNICIPIO":        dict(code="mun", direct=lambda c: c.startswith("id_municipio"),
                             dashed=_municipio_bridge),
    "UF":               dict(code="uf", direct=lambda c: c in ("sigla_uf","id_uf") or c.startswith("sigla_uf"),
                             dashed=lambda c: c.lower() in ("uf","sg_uf","ufsigla","codigo_uf","estado","estadocodigo","nmestado","nome_uf","sigla","origem_uf","destino_uf","state","state_code","p1_i_1")),
    "SETOR_CENSITARIO": dict(code="setor", direct=lambda c: c.startswith("id_setor_censitario"), dashed=lambda c: False),
    "CEP":              dict(code="cep", direct=lambda c: c=="cep", dashed=lambda c: False),
    "EMPRESA_CNPJ":     dict(code="cnpj", direct=lambda c: c.startswith("cnpj"),
                             dashed=lambda c: (not c.startswith("cnpj") and bool(re.search(r"cnpj",c,re.I))) or c=="documento"),
    "PESSOA_CPF":       dict(code="cpf", direct=lambda c: c=="cpf" or (c.startswith("cpf_") and not c.lower().startswith("cpf_cnpj")),
                             dashed=lambda c: (bool(re.search(r"cpf",c,re.I)) and not (c=="cpf" or (c.startswith("cpf_") and not c.lower().startswith("cpf_cnpj")))) or c.lower() in ("nis","numero_familia")),
    "ESCOLA":           dict(code="escola", direct=lambda c: c.startswith("id_escola"), dashed=lambda c: False),
    "IES":              dict(code="ies", direct=lambda c: c=="id_ies", dashed=lambda c: c=="cnpj_mantenedora"),
    "CNES":             dict(code="cnes", direct=lambda c: c.startswith("id_estabelecimento_cnes"),
                             dashed=lambda c: c in ("codigo_estabelecimento","id_estabelecimento")),
    "CNAE":             dict(code="cnae", direct=lambda c: c.startswith("cnae"),
                             dashed=lambda c: c in ("codigoCnae","id_subclasse","subclasse")),
    "CBO":              dict(code="cbo", direct=lambda c: c.startswith("cbo_"), dashed=lambda c: False),
    "CID10":            dict(code="cid", direct=lambda c: c.startswith("cid_"),
                             dashed=lambda c: c in ("subcategoria","categoria","CAT")),
    "NCM_SH":           dict(code="ncm", direct=lambda c: c in ("id_ncm","id_sh4","id_sh6","id_sh2"),
                             dashed=lambda c: bool(re.search(r"ncm|_sh[246]\b",c,re.I)) and not c.startswith("id_")),
    "PAIS":             dict(code="pais", direct=lambda c: c in ("id_pais","sigla_pais_iso3","sigla_pais_iso2","id_pais_m49"),
                             dashed=lambda c: c in ("country","country_code","pais")),
    "ORGAO":            dict(code="orgao", direct=lambda c: c.startswith(("id_orgao","codigo_orgao")),
                             dashed=lambda c: c.startswith("nome_orgao")),
    "UNIDADE_GESTORA":  dict(code="ug", direct=lambda c: c.startswith(("id_unidade_gestora","codigo_unidade_gestora","id_unidade_orcamentaria")),
                              dashed=lambda c: c.startswith(("nome_unidade_gestora","nome_unidade_orcamentaria"))),
    "FUNCAO_PROGRAMA":  dict(code="funcprog", direct=lambda c: c.startswith(("id_funcao","id_subfuncao","id_acao","id_programa")),
                              dashed=lambda c: c.startswith(("nome_funcao","nome_subfuncao","nome_acao","nome_programa"))),
    "PARTIDO":          dict(code="partido", direct=lambda c: c in ("sigla_partido","id_partido"),
                              dashed=lambda c: c=="partido"),
}

HUB_EXCLUDE = {"ORGAO": {"br_camara_dados_abertos", "br_inep_censo_escolar"}}

HUB_MODEL_EDGES = [
    ("UF", "MUNICIPIO"), ("MUNICIPIO", "SETOR_CENSITARIO"), ("MUNICIPIO", "CEP"),
    ("MUNICIPIO", "ESCOLA"), ("MUNICIPIO", "IES"), ("MUNICIPIO", "CNES"),
    ("MUNICIPIO", "EMPRESA_CNPJ"), ("CEP", "EMPRESA_CNPJ"),
    ("EMPRESA_CNPJ", "PESSOA_CPF"), ("EMPRESA_CNPJ", "CNAE"),
    ("PESSOA_CPF", "CBO"), ("PESSOA_CPF", "CID10"), ("CNES", "CID10"),
    ("PAIS", "NCM_SH"), ("PARTIDO", "MUNICIPIO"),
    ("ORGAO", "UNIDADE_GESTORA"), ("UNIDADE_GESTORA", "FUNCAO_PROGRAMA"),
]

HUB_GROUP = {
    "places": ["MUNICIPIO", "UF", "SETOR_CENSITARIO", "CEP"],
    "entities": ["EMPRESA_CNPJ", "PESSOA_CPF", "ESCOLA", "IES", "CNES"],
    "classifications": ["CNAE", "CBO", "CID10", "NCM_SH", "PAIS"],
    "government": ["ORGAO", "UNIDADE_GESTORA", "FUNCAO_PROGRAMA", "PARTIDO"],
}
HUB_GROUP_COLORS = {
    "places": "#00B894",
    "entities": "#58A6FF",
    "classifications": "#D29922",
    "government": "#BC8CFF",
}
HUB_GROUP_NAMES = {
    "places": "GEOGRÁFICOS",
    "entities": "ENTIDADES",
    "classifications": "CLASSIFICAÇÕES",
    "government": "GOVERNO",
}

DOMAIN_RULES = [
    (r"^br_bd_|^br_datasus_cid10|^br_ibge_cbo_2002|^br_brasilapi|^br_ibge_amc", "referencia"),
    (r"^br_ms_|^br_ans_|^br_anvisa_|^br_saude_|^br_ieps_", "saude"),
    (r"^br_inep_|^br_mec_|^br_capes_|^br_cnpq_|^br_simet_|^world_iea_|^world_oecd_pisa", "educacao"),
    (r"^br_tse_|^br_camara_|^br_senado_|^br_poder360_|^br_cgu_emendas", "politica"),
    (r"^br_cnj_|^br_stf_|^br_stj_|^br_mjsp_|^br_mj_|^br_pgfn_|^br_fbsp_|"
     r"^br_rj_isp_|^br_ipea_atlasviolencia|^br_ggb_|^br_tcu_inidoneos|"
     r"^br_bcb_penalidades|_sanctions$|^global_opensanctions|^global_icij_", "justica"),
    (r"^br_cgu_|^br_comprasgov_|^br_transferegov|^br_siop_|^br_tesouro_|^br_tcu_|"
     r"^br_tce_|^br_me_siconfi|^br_me_siape|^br_me_siorg|^br_mp_pep|^br_ok_|"
     r"^br_ba_feiradesantana|^br_me_estoque_divida", "governo"),
    (r"^br_me_|^br_rf_|^br_bcb_|^br_cvm_|^br_fipe_|^br_fgv_|^br_bndes_|"
     r"^br_brasilio_|^br_anp_|^br_mme_|^br_caixa_|^br_trase_|^br_ibge_ip|"
     r"^br_ibge_inpc|^br_ibge_pam|^br_ibge_pevs|^br_ibge_ppm|^br_ibge_pib|"
     r"^br_clp_|^br_firjan_|^br_mc_indicadores|^br_datahackers_", "economia"),
    (r"^br_ana_|^br_inpe_|^br_mapbiomas_|^br_sfb_|^br_ibama_|^br_seeg_|^br_mma_|"
     r"^br_mdr_|^br_inmet_|^br_geobr_|^world_wwf_|^global_ibge_tabua|^br_anatel_|"
     r"^br_anac_|^br_mobilidados_|^br_ipea_acesso", "territorio"),
    (r"^br_ibge_|^br_abrinq_|^br_ipea_|^br_ce_|^br_mg_|^br_sp_", "demografia"),
    (r"^world_|^us_|^mundo_|^global_", "internacional"),
]

DOMAIN_ORDER = ["referencia", "saude", "educacao", "economia", "governo",
                "politica", "justica", "territorio", "demografia", "internacional"]

# ── Data loading ──────────────────────────────────────────────────

def load_schema():
    if not SRC.exists():
        sys.exit(f"{SRC} not found — run scripts/gera_schemas.py first.")
    return json.loads(SRC.read_text(encoding="utf-8"))["tables"]

def probe_row_counts():
    sql = ('SET enable_progress_bar=false; '
           'SELECT dataset, "table" AS tbl, rows FROM _rodado_metadata')
    cmd = ["ssh", BEELINK_HOST, f"~/bin/duckdb -json -readonly {BEELINK_DB} -c {sql!r}"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        text = re.sub(r"\x1b\[[0-9;]*m", "", out.stdout)
        rows = json.loads(text[text.index("["):])
    except Exception:
        print("  ! row-count probe failed, continuing without", file=sys.stderr)
        return {}
    return {f"{r['dataset']}.{r['tbl']}": r["rows"] for r in rows if r["rows"] is not None}

def human(n):
    if n is None:
        return ""
    for limit, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "k")):
        if n >= limit:
            v = n / limit
            return f"{v:.1f}{suffix}".replace(".0", "")
    return str(n)

def domain_of(dataset):
    for pattern, name in DOMAIN_RULES:
        if re.search(pattern, dataset):
            return name
    return "outros"

def analyze(tables):
    info = defaultdict(lambda: {"tables": {}, "hubs": {}, "hub_cols": defaultdict(set)})
    for tid, meta in sorted(tables.items()):
        dataset, _, table = tid.partition(".")
        cols = [c["name"] for c in meta.get("columns", [])]
        codes = []
        for hub, spec in HUBS.items():
            if dataset in HUB_EXCLUDE.get(hub, ()):
                continue
            direct = [c for c in cols if spec["direct"](c)]
            dashed = [c for c in cols if not spec["direct"](c) and spec["dashed"](c)]
            if not direct and not dashed:
                continue
            codes.append(spec["code"])
            entry = info[dataset]
            was_dashed = entry["hubs"].get(hub, (None, True))[1]
            if direct:
                if was_dashed:
                    entry["hub_cols"][hub] = set()
                entry["hub_cols"][hub].update(direct)
                entry["hubs"][hub] = (None, False)
            elif was_dashed:
                entry["hub_cols"][hub].update(dashed)
                entry["hubs"][hub] = (None, True)
        lowered = {c.lower() for c in cols}
        codes += sorted({"ano" for c in lowered if c.startswith("ano")}
                        | {"mes" for c in lowered if c.startswith("mes")})
        info[dataset]["tables"][table] = {"codes": codes, "cols": len(cols)}
    return info

# ── Drawing helpers ──────────────────────────────────────────────

def add_bg(ax, w, h, color=BG):
    ax.add_patch(Rectangle((0, 0), w, h, facecolor=color, zorder=-10,
                           linewidth=0, transform=ax.transData))

def fancy_box(ax, x, y, w, h, color, alpha=0.15, lw=1, radius=0.03, zorder=0):
    """Draw a rounded rectangle with a border."""
    box = FancyBboxPatch((x, y), w, h,
                          boxstyle=f"round,pad=0,rounding_size={radius}",
                          facecolor=color, edgecolor=color,
                          linewidth=lw, alpha=alpha, zorder=zorder)
    ax.add_patch(box)
    # border on top
    border = FancyBboxPatch((x, y), w, h,
                             boxstyle=f"round,pad=0,rounding_size={radius}",
                             facecolor="none", edgecolor=color,
                             linewidth=lw, alpha=0.5, zorder=zorder+1)
    ax.add_patch(border)

def text(ax, x, y, s, size=10, color=TEXT, ha="left", va="center",
         weight="normal", family=None, alpha=1, rotation=0):
    ax.text(x, y, s, fontsize=size, color=color, ha=ha, va=va,
            fontweight=weight, fontfamily=family or "sans-serif",
            alpha=alpha, rotation=rotation)

def draw_connection_line(ax, x1, y1, x2, y2, color=TEXT_MUTED, lw=0.5, alpha=0.3,
                         style="solid"):
    ls = "--" if style == "dashed" else "-"
    ax.plot([x1, x2], [y1, y2], color=color, linewidth=lw, alpha=alpha,
            linestyle=ls, zorder=0)

def draw_hub_circle(ax, x, y, label, size=0.06, color=ACCENT, text_color=TEXT):
    circle = plt.Circle((x, y), size, facecolor=color, edgecolor=color,
                        linewidth=2, alpha=0.3, zorder=5)
    ax.add_patch(circle)
    circle2 = plt.Circle((x, y), size, facecolor=(0,0,0,0), edgecolor=color,
                         linewidth=1, alpha=0.7, zorder=6)
    ax.add_patch(circle2)
    text(ax, x, y - size - 0.015, label, size=7, color=text_color, ha="center")

def draw_hub_node(ax, x, y, name, color, fontsize=8):
    """Draw a hub as a labeled circle."""
    r = 0.035
    circle = plt.Circle((x, y), r, facecolor=color, edgecolor=color,
                        linewidth=0, alpha=0.2, zorder=5)
    ax.add_patch(circle)
    circle2 = plt.Circle((x, y), r, facecolor="none", edgecolor=color,
                         linewidth=1.5, alpha=0.8, zorder=6)
    ax.add_patch(circle2)
    short = name.replace("_", " ").title()
    if len(short) > 10:
        short = name[:10]
    text(ax, x, y, name[:6], size=5.5, color=TEXT, ha="center", va="center", weight="bold")

def rounded_rect(ax, x, y, w, h, color, alpha=0.12, lw=1, zorder=0):
    """Simpler rounded rect."""
    r = min(w, h) * 0.08
    box = FancyBboxPatch((x, y), w, h,
                          boxstyle=f"round,pad=0,rounding_size={r}",
                          facecolor=color, edgecolor=color,
                          linewidth=lw, alpha=alpha, zorder=zorder)
    ax.add_patch(box)
    border = FancyBboxPatch((x, y), w, h,
                             boxstyle=f"round,pad=0,rounding_size={r}",
                             facecolor="none", edgecolor=color,
                             linewidth=lw, alpha=0.5, zorder=zorder+1)
    ax.add_patch(border)

# ── Poster generation ────────────────────────────────────────────

def generate_domain_poster(info, rows, output_path):
    """Domain-level poster: hubs + domain cards + connection matrix."""
    print(f"  Generating domain-level poster...")

    W, H = 44, 28  # inches
    dpi = 150
    fig, ax = plt.subplots(1, 1, figsize=(W, H))
    fig.patch.set_facecolor(BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    add_bg(ax, 1, 1)

    # layout grid (fractions)
    MARGIN = 0.015
    TITLE_H = 0.065
    HEADER_H = 0.025
    FOOTER_H = 0.02
    MAIN_Y = MARGIN + FOOTER_H
    MAIN_H = 1 - TITLE_H - HEADER_H - FOOTER_H - 3 * MARGIN - 0.01

    # ── Title ──
    ty = 1 - MARGIN - TITLE_H
    text(ax, 0.5, ty + TITLE_H * 0.55, "ANATOMIA DO ESPELHO DE DADOS",
         size=28, color=TEXT, ha="center", va="center", weight="bold")
    text(ax, 0.5, ty + TITLE_H * 0.2,
         "O espelho de dados como um mapa anatômico  ·  195 datasets  ·  825 tabelas  ·  18 hubs de referência",
         size=11, color=TEXT_MUTED, ha="center", va="center")

    # ── Header bar with domain color legend ──
    hy = ty - MARGIN - HEADER_H
    x0 = 0.04
    for i, dom in enumerate(DOMAIN_ORDER):
        if dom not in DOMAIN_NAMES:
            continue
        dx = x0 + i * 0.092
        c = DOMAIN_COLORS.get(dom, "#484F58")
        ax.add_patch(Rectangle((dx, hy+0.003), 0.015, 0.018, facecolor=c,
                               linewidth=0, alpha=0.8))
        text(ax, dx + 0.02, hy + 0.012, DOMAIN_NAMES[dom].split(",")[0],
             size=6, color=TEXT_MUTED, ha="left", va="center")

    # ── Main area: hub network (left) + connection matrix (center) + domain cards (right) ──
    my = MAIN_Y
    mh = MAIN_H

    left_w = 0.22
    matrix_w = 0.12
    right_w = 1 - left_w - matrix_w - MARGIN * 4
    gap_m = 0.008

    # ── Hub network (left panel) ──
    hx = MARGIN
    hw = left_w

    rounded_rect(ax, hx, my, hw, mh, ACCENT, alpha=0.06, lw=0.5)

    # Hub network title
    text(ax, hx + 0.008, my + mh - 0.015, "ESQUELETO — HUBS",
         size=8, color=ACCENT, ha="left", va="top", weight="bold")
    text(ax, hx + 0.008, my + mh - 0.030,
         "18 hubs de referência",
         size=5.5, color=TEXT_MUTED, ha="left", va="top")

    # Compute hub connection counts (how many datasets each hub connects to)
    hub_dataset_count = defaultdict(int)
    hub_domain_count = defaultdict(int)
    for ds, entry in info.items():
        domains_covered = set()
        for hub in entry["hubs"]:
            hub_dataset_count[hub] += 1
            domains_covered.add(domain_of(ds))
        for hub in entry["hubs"]:
            hub_domain_count[hub] = len(domains_covered)

    hub_list = list(HUBS.keys())
    n_hubs = len(hub_list)
    hub_net_y0 = my + 0.015
    hub_net_h = mh - 0.045
    hub_spacing = hub_net_h / n_hubs

    hub_positions = {}
    for i, hub_name in enumerate(hub_list):
        hx_center = hx + hw * 0.25
        hy_pos = hub_net_y0 + hub_spacing * (i + 0.5)
        hub_positions[hub_name] = (hx_center, hy_pos)
        color = HUB_COLORS.get(hub_name, ACCENT)

        # Hub circle
        r = 0.028
        circle = plt.Circle((hx_center, hy_pos), r, facecolor=color,
                            edgecolor=color, linewidth=0, alpha=0.2, zorder=5)
        ax.add_patch(circle)
        ax.add_patch(plt.Circle((hx_center, hy_pos), r, facecolor="none",
                                edgecolor=color, linewidth=1.2, alpha=0.7, zorder=6))

        # Short hub name (first 4-6 chars)
        short = hub_name.replace("_", " ").title()
        text(ax, hx_center, hy_pos, short[:5], size=4.5, color=TEXT,
             ha="center", va="center", weight="bold")

        # Connection count label to the right
        cnt = hub_dataset_count.get(hub_name, 0)
        text(ax, hx + hw * 0.55, hy_pos, f"{cnt} ds", size=4.5,
             color=TEXT_MUTED, ha="left", va="center")

    # Draw hub-to-hub connections
    for src, dst in HUB_MODEL_EDGES:
        if src in hub_positions and dst in hub_positions:
            x1, y1 = hub_positions[src]
            x2, y2 = hub_positions[dst]
            color = HUB_COLORS.get(src, ACCENT)
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2 + 0.005
            ax.plot([x1, mid_x, x2], [y1, mid_y, y2],
                    color=color, linewidth=0.4, alpha=0.2, zorder=0)

    # Hub group labels (right side of left panel)
    group_x = hx + hw * 0.62
    group_y_start = hub_net_y0 + hub_net_h + 0.005
    gstep = hub_net_h / 4
    for gidx, (gname, hubs_in_group) in enumerate(HUB_GROUP.items()):
        gcolor = HUB_GROUP_COLORS[gname]
        gy = group_y_start - gidx * gstep
        text(ax, group_x, gy, HUB_GROUP_NAMES[gname], size=4.5, color=gcolor,
             ha="left", va="center", alpha=0.7)
        # Count for this group
        gcount = sum(hub_dataset_count.get(h, 0) for h in hubs_in_group)
        text(ax, group_x, gy - 0.008, f"{gcount} conexões", size=3.8,
             color=TEXT_DIM, ha="left", va="center")

    # ── Connection matrix (center) ──
    mx = hx + hw + gap_m
    mw = matrix_w

    rounded_rect(ax, mx, my, mw, mh, PURPLE, alpha=0.04, lw=0.5)
    text(ax, mx + 0.005, my + mh - 0.015, "CONEXÕES", size=6.5, color=PURPLE,
         ha="left", va="top", weight="bold")

    # Prepare domain data
    domain_data = {}
    for dom in DOMAIN_ORDER:
        dss = [ds for ds in info if domain_of(ds) == dom]
        if not dss:
            continue
        tbl_count = sum(len(info[ds]["tables"]) for ds in dss)
        conn_count = sum(1 for ds in dss if info[ds]["hubs"])
        hub_connections = defaultdict(int)
        for ds in dss:
            for hub in info[ds]["hubs"]:
                hub_connections[hub] += 1
        row_count = sum(rows.get(f"{ds}.{tbl}", 0) or 0
                       for ds in dss for tbl in info[ds]["tables"])
        domain_data[dom] = {
            "datasets": dss,
            "n_datasets": len(dss),
            "n_tables": tbl_count,
            "n_connected": conn_count,
            "hub_connections": dict(hub_connections),
            "row_count": row_count,
        }

    # Build hub × domain connection data
    dom_order_reduced = [d for d in DOMAIN_ORDER if domain_data.get(d)]
    n_domains = len(dom_order_reduced)

    cell_w = (mw - 0.015) / max(n_domains, 1)
    cell_h = (mh - 0.04) / max(n_hubs, 1)

    # Count connections per hub per domain
    conn_matrix = defaultdict(lambda: defaultdict(int))
    for ds, entry in info.items():
        dom = domain_of(ds)
        for hub in entry["hubs"]:
            conn_matrix[hub][dom] += 1

    matrix_x0 = mx + 0.008
    matrix_y0 = my + 0.01

    # Max connections for normalization
    all_vals = [conn_matrix[h][d] for h in hub_list for d in dom_order_reduced]
    max_val = max(all_vals) if all_vals else 1

    # Draw cells
    for hi, hub_name in enumerate(hub_list):
        for di, dom in enumerate(dom_order_reduced):
            val = conn_matrix[hub_name].get(dom, 0)
            if val == 0:
                continue
            cx = matrix_x0 + di * cell_w
            cy = matrix_y0 + (n_hubs - 1 - hi) * cell_h  # flip so hub order matches
            intensity = val / max_val
            # Color: interpolate from dark to hub color
            hc = HUB_COLORS.get(hub_name, PURPLE)
            alpha_val = 0.15 + intensity * 0.6
            bw = max(cell_w * 0.7, 0.002)
            bh = max(cell_h * 0.7, 0.003)
            ax.add_patch(Rectangle((cx + cell_w * 0.15, cy + cell_h * 0.15),
                                    bw, bh, facecolor=hc, alpha=alpha_val,
                                    linewidth=0, zorder=2))

    # Domain column labels (top of matrix)
    for di, dom in enumerate(dom_order_reduced):
        cx = matrix_x0 + di * cell_w + cell_w * 0.5
        label = dom[:4].upper()
        dc = DOMAIN_COLORS.get(dom, TEXT_MUTED)
        text(ax, cx, matrix_y0 + (n_hubs) * cell_h + 0.003, label,
             size=3.8, color=dc, ha="center", va="bottom", rotation=30)

    # Hub row labels (on right side of matrix)
    for hi, hub_name in enumerate(hub_list):
        cy = matrix_y0 + (n_hubs - 1 - hi) * cell_h + cell_h * 0.5
        # small label
        text(ax, matrix_x0 + n_domains * cell_w + 0.002, cy,
             hub_name[:4], size=3.5, color=TEXT_DIM, ha="left", va="center")

    # ── Domain cards (right panel) ──
    dx0 = mx + mw + gap_m
    dw = right_w
    n_cols = 2
    n_rows = math.ceil(len(DOMAIN_ORDER) / n_cols)
    card_w = (dw - 0.01 * (n_cols - 1)) / n_cols
    card_h = (mh - 0.01 * (n_rows - 1)) / n_rows

    for i, dom in enumerate(DOMAIN_ORDER):
        if dom not in domain_data:
            continue
        dd = domain_data[dom]
        col = i % n_cols
        row = i // n_cols
        cx = dx0 + col * (card_w + 0.01)
        cy = my + mh - card_h - row * (card_h + 0.01)

        color = DOMAIN_COLORS.get(dom, "#484F58")

        # Card background
        rounded_rect(ax, cx, cy, card_w, card_h, color, alpha=0.08, lw=0.5)

        # Domain name
        text(ax, cx + 0.01, cy + card_h - 0.015, DOMAIN_NAMES.get(dom, dom),
             size=9, color=color, ha="left", va="top", weight="bold")

        # Stats line
        stats = f"{dd['n_datasets']} datasets  ·  {dd['n_tables']} tabelas  ·  {human(dd['row_count'])} linhas"
        text(ax, cx + 0.01, cy + card_h - 0.035, stats,
             size=6, color=TEXT_MUTED, ha="left", va="top")

        # Connection bar: which hubs connect
        conn_line_y = cy + card_h - 0.050
        conn_text = f"{dd['n_connected']}/{dd['n_datasets']} conectados"
        text(ax, cx + 0.01, conn_line_y, conn_text,
             size=5.5, color=GREEN if dd['n_connected'] == dd['n_datasets'] else ORANGE,
             ha="left", va="top")

        # Hub connection dots
        dot_y = conn_line_y - 0.010
        dot_x_start = cx + 0.01
        hub_order = list(HUBS.keys())
        dot_size = 0.006
        gap = 0.023
        used = 0
        for hub_name in hub_order:
            if hub_name in dd["hub_connections"]:
                cnt = dd["hub_connections"][hub_name]
                hc = HUB_COLORS.get(hub_name, ACCENT)
                dx_pos = dot_x_start + used * gap
                if dx_pos + gap > cx + card_w - 0.01:
                    break
                ax.add_patch(Rectangle((dx_pos, dot_y), 0.018, 0.007,
                                       facecolor=hc, alpha=0.6, linewidth=0))
                text(ax, dx_pos + 0.009, dot_y - 0.005, str(cnt),
                     size=4.5, color=TEXT_MUTED, ha="center", va="top")
                used += 1

        # Dataset list (compact, 2-3 per domain)
        ds_list_y = dot_y - 0.018
        max_ds_show = min(len(dd["datasets"]), 6)
        short_list = sorted(dd["datasets"])[:max_ds_show]
        for j, ds in enumerate(short_list):
            n_t = len(info[ds]["tables"])
            hubs_in_ds = [h for h in hub_order if h in info[ds]["hubs"]]
            hub_codes = ",".join(HUBS[h]["code"] for h in hubs_in_ds[:4])
            extra = f" (+{len(hubs_in_ds)-4})" if len(hubs_in_ds) > 4 else ""
            label = f"{ds}  ({n_t} tbl, {hub_codes}{extra})"
            text(ax, cx + 0.015, ds_list_y, label,
                 size=4.5, color=TEXT, ha="left", va="top", alpha=0.8)
            ds_list_y -= 0.012
        if len(dd["datasets"]) > max_ds_show:
            text(ax, cx + 0.015, ds_list_y,
                 f"+ {len(dd['datasets']) - max_ds_show} datasets …",
                 size=4.5, color=TEXT_MUTED, ha="left", va="top")

    # ── Stats panel (below hub network) ──
    stats_y = MARGIN
    stats_h = FOOTER_H
    stats_w = 1 - 2 * MARGIN
    rounded_rect(ax, MARGIN, stats_y, stats_w, stats_h, ACCENT, alpha=0.05, lw=0.3)
    text(ax, MARGIN + 0.01, stats_y + stats_h * 0.6,
         f"Total: {len(info)} datasets  ·  825 tabelas  ·  {human(sum((rows.get(f'{ds}.{tbl}', 0) or 0) for ds in info for tbl in info[ds]['tables']))} linhas",
         size=6, color=TEXT, ha="left", va="center")
    orphan_ds = sorted(ds for ds in info if not info[ds]["hubs"])
    orphan_tbl = sorted(f"{ds}.{tbl}" for ds in info
                        for tbl, m in info[ds]["tables"].items() if not m["codes"])
    text(ax, MARGIN + 0.35, stats_y + stats_h * 0.6,
         f"Datasets órfãos: {len(orphan_ds)}  ·  Tabelas sem chave: {len(orphan_tbl)}",
         size=6, color=ORANGE, ha="left", va="center")
    text(ax, MARGIN + 0.68, stats_y + stats_h * 0.6,
         f"Gerado por scripts/gera_erd_poster.py  ·  {date.today().isoformat()}",
         size=5, color=TEXT_DIM, ha="left", va="center")

    # Legend: connection types
    text(ax, MARGIN + 0.01, stats_y + stats_h * 0.15,
         "Conexões: sólida = chave canônica · tracejada = chave alternativa (ver join_keys.md)",
         size=5, color=TEXT_MUTED, ha="left", va="center")
    # solid line example
    ax.plot([MARGIN + 0.55, MARGIN + 0.58], [stats_y + stats_h * 0.15, stats_y + stats_h * 0.15],
            color=TEXT_MUTED, linewidth=0.8, alpha=0.5)
    # dashed line example
    ax.plot([MARGIN + 0.62, MARGIN + 0.65], [stats_y + stats_h * 0.15, stats_y + stats_h * 0.15],
            color=TEXT_MUTED, linewidth=0.8, alpha=0.5, linestyle="--")

    fig.savefig(output_path, dpi=dpi, facecolor=BG, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)
    print(f"  → {output_path} ({os.path.getsize(output_path) / 1024:.0f} KB)")


def generate_full_poster(info, rows, output_path):
    """Full poster: all datasets listed within their domains."""
    print(f"  Generating full poster (all datasets)...")

    W, H = 48, 36  # inches (large format)
    dpi = 150
    fig, ax = plt.subplots(1, 1, figsize=(W, H))
    fig.patch.set_facecolor(BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    add_bg(ax, 1, 1)

    MARGIN = 0.012
    TITLE_H = 0.05

    # ── Title ──
    text(ax, 0.5, 1 - MARGIN - TITLE_H * 0.6,
         "ANATOMIA DO ESPELHO DE DADOS — CATÁLOGO COMPLETO",
         size=24, color=TEXT, ha="center", va="center", weight="bold")
    text(ax, 0.5, 1 - MARGIN - TITLE_H * 0.25,
         "Todos os 195 datasets com suas 825 tabelas e conexões aos hubs de referência",
         size=10, color=TEXT_MUTED, ha="center", va="center")

    # ── Domains grid ──
    my = MARGIN
    mh = 1 - TITLE_H - 2 * MARGIN - 0.01

    n_cols = 2
    n_rows = math.ceil(len(DOMAIN_ORDER) / n_cols)
    gap_x = 0.008
    gap_y = 0.008
    card_w = (1 - 2 * MARGIN - gap_x * (n_cols - 1)) / n_cols
    card_h = (mh - gap_y * (n_rows - 1)) / n_rows

    # Prepare domain data (same as before)
    domain_data = {}
    for dom in DOMAIN_ORDER:
        dss = [ds for ds in info if domain_of(ds) == dom]
        if not dss:
            continue
        hub_connections = defaultdict(int)
        for ds in dss:
            for hub in info[ds]["hubs"]:
                hub_connections[hub] += 1
        row_count = sum(rows.get(f"{ds}.{tbl}", 0) or 0
                       for ds in dss for tbl in info[ds]["tables"])
        domain_data[dom] = {
            "datasets": sorted(dss),
            "hub_connections": dict(hub_connections),
            "row_count": row_count,
        }

    hub_order = list(HUBS.keys())

    for i, dom in enumerate(DOMAIN_ORDER):
        if dom not in domain_data:
            continue
        dd = domain_data[dom]
        col = i % n_cols
        row = i // n_cols
        cx = MARGIN + col * (card_w + gap_x)
        cy = MARGIN + mh - card_h - row * (card_h + gap_y)

        color = DOMAIN_COLORS.get(dom, "#484F58")
        dss = dd["datasets"]

        # Card background
        rounded_rect(ax, cx, cy, card_w, card_h, color, alpha=0.06, lw=0.5)

        # Domain header
        header_h = 0.022
        text(ax, cx + 0.008, cy + card_h - 0.005,
             DOMAIN_NAMES.get(dom, dom).upper(),
             size=11, color=color, ha="left", va="top", weight="bold")

        tbl_count = sum(len(info[ds]["tables"]) for ds in dss)
        conn_count = sum(1 for ds in dss if info[ds]["hubs"])
        stats = f"{len(dss)} datasets · {tbl_count} tabelas · {human(dd['row_count'])} linhas · {conn_count}/{len(dss)} conectados"
        text(ax, cx + 0.008, cy + card_h - 0.021, stats,
             size=6.5, color=TEXT_MUTED, ha="left", va="top")

        # Hub connection bar
        bar_y = cy + card_h - 0.033
        hub_bar_x = cx + 0.008
        for hub_name in hub_order:
            cnt = dd["hub_connections"].get(hub_name, 0)
            hc = HUB_COLORS.get(hub_name, ACCENT)
            if cnt > 0:
                w = max(0.003, cnt * 0.001)
                ax.add_patch(Rectangle((hub_bar_x, bar_y), w, 0.005,
                                       facecolor=hc, alpha=0.5, linewidth=0))
                hub_bar_x += w + 0.001

        # Dataset list
        list_y = cy + card_h - 0.042
        ds_font = 5
        line_h = 0.0105

        for ds in dss:
            n_t = len(info[ds]["tables"])
            hubs_in_ds = [h for h in hub_order if h in info[ds]["hubs"]]
            codes = ",".join(sorted(set(HUBS[h]["code"] for h in hubs_in_ds)))
            ds_row_count = sum(rows.get(f"{ds}.{tbl}", 0) or 0
                              for tbl in info[ds]["tables"])

            # Dataset name with link indicator
            is_connected = bool(hubs_in_ds)
            name_color = color if is_connected else TEXT_DIM

            # Truncate name if needed
            display_name = ds
            max_name_len = 50
            if len(display_name) > max_name_len:
                display_name = display_name[:max_name_len-3] + "..."

            # Count tables per dataset
            tbl_detail = ", ".join(f"{tbl}({m['cols']}col)" for tbl, m in
                                   list(info[ds]["tables"].items())[:2])
            if len(info[ds]["tables"]) > 2:
                tbl_detail += f" +{len(info[ds]['tables'])-2}"

            conn_indicator = " ●" if is_connected else " ○"
            conn_color = GREEN if is_connected else TEXT_DIM

            line = f"{display_name}{conn_indicator}  {n_t} tbl"
            if codes:
                line += f"  [{codes}]"

            # Check if we're past the card bottom
            if list_y < cy + 0.005:
                remaining = len(dss) - dss.index(ds)
                text(ax, cx + 0.008, list_y,
                     f"+ {remaining} datasets …",
                     size=ds_font, color=TEXT_MUTED, ha="left", va="top", alpha=0.6)
                break

            text(ax, cx + 0.008, list_y, line,
                 size=ds_font, color=name_color, ha="left", va="top",
                 alpha=0.85 if is_connected else 0.4)
            list_y -= line_h

    # ── Footer ──
    footer_y = 0.005
    text(ax, 0.5, footer_y,
         f"Gerado por scripts/gera_erd_poster.py  ·  Dados de {date.today().isoformat()}  ·  "
         f"{len(info)} datasets · 825 tabelas · 18 hubs",
         size=7, color=TEXT_DIM, ha="center", va="bottom")

    orphan_ds = sorted(ds for ds in info if not info[ds]["hubs"])
    orphan_tbl = sorted(f"{ds}.{tbl}" for ds in info
                        for tbl, m in info[ds]["tables"].items() if not m["codes"])
    text(ax, 0.5, footer_y + 0.008,
         f"Datasets órfãos: {len(orphan_ds)}  ·  Tabelas sem chave: {len(orphan_tbl)}  ·  "
         f"Veja ERD.md para lista completa e join_keys.md para expressões de join",
         size=6, color=TEXT_DIM, ha="center", va="bottom")

    fig.savefig(output_path, dpi=dpi, facecolor=BG, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)
    print(f"  → {output_path} ({os.path.getsize(output_path) / 1024:.0f} KB)")


def main():
    tables = load_schema()
    info = analyze(tables)
    rows = probe_row_counts()

    print(f"Loaded {len(info)} datasets, {len(tables)} tables, {len(rows)} row counts")

    dst_domain = DST_DIR / "ERD-poster-domain.pdf"
    dst_full = DST_DIR / "ERD-poster-full.pdf"

    generate_domain_poster(info, rows, dst_domain)
    generate_full_poster(info, rows, dst_full)

    print("Done.")


if __name__ == "__main__":
    main()
