#!/usr/bin/env python3
"""Hipóteses novas sobre datasets JÁ mirrorados, nunca cruzados um com o
outro — diferente do padrão do dia (dataset novo x covariável já conhecida).
Roda direto sobre o painel já extraído (`.hipoteses/20260906_blocof/painel.csv`),
sem SQL nova: todas as variáveis já estavam lá, só não tinham sido cruzadas
entre si. Tema novo em docs/perguntas.md, respostas em docs/respostas.md.

  python3 scripts/hipoteses/100_pares_existentes.py
"""
import os
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
d = pd.read_csv(os.path.join(ROOT, ".hipoteses", "20260906_blocof", "painel.csv"),
                 low_memory=False).replace([np.inf, -np.inf], np.nan)

uf_dum = pd.get_dummies(d["sigla_uf"], drop_first=True).astype(float)
BASE = pd.concat([pd.DataFrame({
    "lp": np.log(d.populacao.clip(lower=1)),
    "lpib": np.log(d.pib_pc.clip(lower=1)),
    "c": 1.0}), uf_dum], axis=1)
BASE.index = d.index

def parcial(a, b, extra=None):
    C = BASE if extra is None else pd.concat([BASE, extra], axis=1)
    m = d[a].notna() & d[b].notna() & C.notna().all(axis=1)
    if m.sum() < 200: return np.nan, int(m.sum())
    X = C[m].values; r = []
    for col in (a, b):
        y = pd.Series(d.loc[m, col].values).rank().values
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        r.append(y - X @ beta)
    return round(float(np.corrcoef(r[0], r[1])[0, 1]), 4), int(m.sum())

def bruto(a, b):
    s = d[[a, b]].dropna()
    if len(s) < 30: return np.nan, len(s)
    return round(s[a].rank().corr(s[b].rank()), 4), len(s)

pares = [
    ("N1", "vac_polio", "ivs_2010",
     "Cobertura vacinal (polio) x vulnerabilidade social"),
    ("N2", "hhi_smp", "nbf_share_dom",
     "Concentracao do mercado de telefonia movel x pobreza"),
    ("N3", "cob_esf", "ideb",
     "Cobertura da Estrategia Saude da Familia x desempenho escolar"),
    ("N4", "pncp_valor_mediano", "ebt_nota",
     "Valor mediano de contrato do PNCP x nota de transparencia"),
    ("N5", "cauc_pendencias", "capital_social_mediano",
     "Pendencias fiscais do municipio (CAUC) x capital social do estabelecimento"),
]

for tag, a, b, desc in pares:
    print("=" * 72)
    print(f"{tag} · {desc} ({a} x {b})")
    print("=" * 72)
    rb, nb = bruto(a, b)
    rp, npp = parcial(a, b)
    print(f"  bruto                     {rb:+.4f} (n={nb})")
    print(f"  parcial (log-pop/pib/UF)  {rp:+.4f} (n={npp})")
    s = d[[a, b]].dropna()
    if len(s) >= 500:
        try:
            s = s.copy()
            s["q"] = pd.qcut(s[a], 5, labels=False, duplicates="drop")
            g = s.groupby("q")[b].median()
            print("  quintis de", a, "-> mediana de", b, ":", " | ".join(f"{v:.4g}" for v in g))
        except Exception:
            pass
    print()
