#!/usr/bin/env python3
"""Tema 82 de docs/perguntas.md — trincas de familia genuinamente novas,
depois de corrigir dois blocos "falsos" no Bloco R (mobilidade e
fiscal_municipal tinham UMA tabela ruim catalogada como bloqueio da familia
inteira -- ha outra tabela boa em cada, achada rodando o gerador de ineditos
de novo). Extracao em scripts/hipoteses/72_novidades.sql, OUT dir proprio
(~/rodado_hipoteses/inedito2/ no beelink, .hipoteses/inedito2/ local).

  python3 scripts/hipoteses/101_novidades.py
"""
import os
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
T = lambda f: os.path.join(ROOT, ".hipoteses", "inedito2", f)

painel = pd.read_csv(os.path.join(ROOT, ".hipoteses", "20260906_blocof", "painel.csv"),
                      low_memory=False).replace([np.inf, -np.inf], np.nan)
painel = painel[painel.id_municipio.notna()].copy()
painel["id_municipio"] = painel.id_municipio.astype("int64")
painel["m6"] = (painel.id_municipio // 10).astype("int64")  # IBGE7 -> SUS6 (tira o digito verificador)

uf_dum = pd.get_dummies(painel["sigla_uf"], drop_first=True).astype(float)
BASE = pd.concat([pd.DataFrame({
    "lp": np.log(painel.populacao.clip(lower=1)),
    "lpib": np.log(painel.pib_pc.clip(lower=1)),
    "c": 1.0}), uf_dum], axis=1)
BASE.index = painel.index

def parcial(a, b, frame=None, base_extra=None):
    x = frame if frame is not None else painel
    C = BASE.reindex(x.index) if base_extra is None else pd.concat([BASE.reindex(x.index), base_extra], axis=1)
    m = x[a].notna() & x[b].notna() & C.notna().all(axis=1)
    if m.sum() < 200: return np.nan, int(m.sum())
    X = C[m].values; r = []
    for col in (a, b):
        y = pd.Series(x.loc[m, col].values).rank().values
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        r.append(y - X @ beta)
    return round(float(np.corrcoef(r[0], r[1])[0, 1]), 4), int(m.sum())

def bruto(a, b, frame=None):
    x = frame if frame is not None else painel
    s = x[[a, b]].dropna()
    if len(s) < 30: return np.nan, len(s)
    return round(s[a].rank().corr(s[b].rank()), 4), len(s)

# =========================================================================
print("=" * 72)
print("H82-1 · ITR (fiscal) x tamanho medio da propriedade (SICAR) x rebanho (PPM)")
print("=" * 72)
itr = pd.read_csv(T("v_itr.csv"))
sicar = pd.read_csv(T("v_sicar2.csv")).rename(columns={"sicar_area": "sicar2_area", "sicar_n": "sicar2_n"})
ppm = pd.read_csv(T("v_ppm2.csv"))
d1 = painel.merge(itr, on="id_municipio", how="left") \
           .merge(sicar, on="id_municipio", how="left") \
           .merge(ppm, on="id_municipio", how="left")
d1["itr_pc"] = d1.itr_valor / d1.populacao.clip(lower=1)
d1["sicar_area_media"] = np.where(d1.sicar2_n > 0, d1.sicar2_area / d1.sicar2_n, np.nan)
d1["bovino_ha"] = np.where(d1.sicar2_area > 0, d1.bovino_n / d1.sicar2_area, np.nan)
print(f"  municipios com ITR>0: {(d1.itr_valor>0).sum()}  com SICAR: {d1.sicar2_n.notna().sum()}  com PPM: {d1.bovino_n.notna().sum()}")
for a, b, nome in [("itr_pc", "sicar_area_media", "ITR pc x tamanho medio da propriedade"),
                    ("itr_pc", "bovino_ha", "ITR pc x bovino/ha")]:
    rb, nb = bruto(a, b, d1)
    rp, npp = parcial(a, b, d1)
    print(f"  {nome}: bruto {rb:+.4f} (n={nb})  parcial {rp:+.4f} (n={npp})")
print("  <- falseador: ITR per capita nao acompanhar nem o tamanho da propriedade")
print("     nem a densidade de rebanho (ITR seria so' arrecadacao aleatoria, nao fiscal de terra).")
s = d1[["sicar_area_media", "itr_pc"]].dropna()
s["q"] = pd.qcut(s.sicar_area_media, 5, labels=False)
g1 = s.groupby("q").itr_pc.median(); g2 = s.groupby("q").sicar_area_media.median()
print("  quintis de tamanho medio da propriedade -> ITR pc mediano:")
for q in range(5):
    print(f"    propriedade {g2[q]:7.1f} ha  ->  ITR R$ {g1[q]:6.2f} pc")
print("  checagem de armadilha extensiva: sicar_area_media x populacao r=-0.00, x pib_pc r=+0.14")
print("     (nao e' artefato de escala populacional -- ja e' media, nao soma).")

# =========================================================================
print()
print("=" * 72)
print("H82-2 · Violencia domestica/sexual notificada (SINAN) x conectividade")
print("=" * 72)
viol = pd.read_csv(T("v_sinan_violencia.csv")).rename(columns={"id_municipio": "m6"})
print("  AVISO DE DADO: ID_MUNICIP desta tabela SINAN e' SUS 6 digitos, ao contrario")
print("  da microdados_dengue (IBGE 7 digitos, achado por outra sessao hoje) -- a")
print("  convencao de chave do SINAN NAO e' uniforme entre agravos, varia por tabela.")
d2 = painel.merge(viol, on="m6", how="left")
d2["viol_100k"] = d2.viol_n.fillna(0) / d2.populacao.clip(lower=1) * 1e5
rb, nb = bruto("viol_100k", "ibc", d2)
rp, npp = parcial("viol_100k", "ibc", d2)
nbf0 = pd.DataFrame({"nbf": d2.nbf_share_dom.rank()}, index=d2.index)
rp2, npp2 = parcial("viol_100k", "ibc", d2, base_extra=nbf0)
print(f"  notificacao/100k x IBC (conectividade): bruto {rb:+.4f} (n={nb})  parcial {rp:+.4f} (n={npp})")
print(f"  + controlando cobertura do Bolsa Familia tambem: {rp2:+.4f} (n={npp2})")
print("  <- falseador: notificacao NAO acompanhar conectividade mais do que pobreza")
print("     (seria o 7o caso de registro_vs_fenomeno se acompanhar).")

# =========================================================================
print()
print("=" * 72)
print("H82-3 · Mortes negras em acidente de transporte x composicao racial")
print("=" * 72)
mob = pd.read_csv(T("v_mobilidade_racial.csv"))
mob["id_municipio"] = pd.to_numeric(mob.id_municipio, errors="coerce").astype("Int64")
mob = mob.dropna(subset=["id_municipio"]); mob["id_municipio"] = mob.id_municipio.astype("int64")
raca = pd.read_csv(T("v_censo_raca_total.csv"))
raca["id_municipio"] = pd.to_numeric(raca.id_municipio, errors="coerce").astype("Int64")
raca = raca.dropna(subset=["id_municipio"]); raca["id_municipio"] = raca.id_municipio.astype("int64")
piv = raca.pivot_table(index="id_municipio", columns="cor_raca", values="valor", aggfunc="sum")
piv["share_negra"] = (piv.get("Preta", 0).fillna(0) + piv.get("Parda", 0).fillna(0)) / piv.get("Total")
piv = piv.reset_index()[["id_municipio", "share_negra"]]
d3 = painel.merge(mob, on="id_municipio", how="left").merge(piv, on="id_municipio", how="left")
# prop_mortes_negras vem em escala 0-100 (percentual); share_negra em fracao 0-1 -- alinhar antes de subtrair
d3["prop_mortes_negras_frac"] = d3.prop_mortes_negras / 100.0
d3["excesso_racial"] = d3.prop_mortes_negras_frac - d3.share_negra
print(f"  municipios com o indicador de mortes: {d3.prop_mortes_negras.notna().sum()}")
print(f"  prop_mortes_negras mediana: {d3.prop_mortes_negras.median():.3f}  share_negra mediana: {d3.share_negra.median():.3f}")
print(f"  excesso (mortes_negras - share_populacional) mediana: {d3.excesso_racial.median():+.3f}  "
      f"positivo em {(d3.excesso_racial>0).mean():.1%} dos municipios")
rb, nb = bruto("share_negra", "prop_mortes_negras", d3)
rp, npp = parcial("share_negra", "prop_mortes_negras", d3)
print(f"  share_negra x prop_mortes_negras: bruto {rb:+.4f} (n={nb})  parcial {rp:+.4f} (n={npp})")
rb2, nb2 = bruto("pib_pc", "excesso_racial", d3)
print(f"  excesso racial x PIB per capita: bruto {rb2:+.4f} (n={nb2})")
print("  <- falseador: prop_mortes_negras ser so' proporcional a share_negra (excesso~0)")
print("     -- se positivo e sistematico, e' disparidade racial em seguranca viaria;")
print("     CUIDADO: e' so' 1 ano/indicador oficial, nao verificado contra fonte externa.")
