#!/usr/bin/env python3
"""Analisa a bateria H20-H40 (blocos 50_inedito.sql + intraurbano).

Junta as extrações de `tasks/hipoteses_resultado/inedito/` ao painel municipal
de `tasks/hipoteses_resultado/<data>/painel.csv` e roda cada hipótese com o seu
falseador. Imprime tudo; nada vai para os docs sem passar por leitura humana.

  python3 scripts/hipoteses/95_inedito.py
"""
import numpy as np, pandas as pd, unicodedata, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
INE  = REPO/"tasks"/"hipoteses_resultado"/"inedito"
PAN  = REPO/"tasks"/"hipoteses_resultado"/"20260906"/"painel.csv"
L = lambda n, **k: pd.read_csv(INE/f"{n}.csv", low_memory=False, **k)

d = pd.read_csv(PAN, low_memory=False).replace([np.inf,-np.inf], np.nan)
for f in ["v_snis","v_munic","v_siconfi","v_siconfi_rec","v_cnes_leito","v_cno",
          "v_capag","v_sisu","v_ies","v_mides_tcu"]:
    try:
        x = L(f)
        if "id_municipio" in x.columns:
            x = x[x.id_municipio.notna()].copy()
            x["id_municipio"] = x.id_municipio.astype("int64")
            d = d.merge(x.drop_duplicates("id_municipio"), on="id_municipio", how="left")
    except FileNotFoundError:
        print(f"[falta] {f}")
sih = L("v_sih"); sih = sih[sih.mun6.notna()]
sih["mun6"] = sih.mun6.astype("int64")
d["mun6"] = (d.id_municipio // 10).astype("int64")
d = d.merge(sih.drop_duplicates("mun6"), on="mun6", how="left")
print(f"painel: {d.shape[0]} x {d.shape[1]}\n")

uf = pd.get_dummies(d["sigla_uf"], drop_first=True).astype(float)
def CTL(area=False):
    c = {"lp": np.log(d.populacao.clip(lower=1)),
         "lpib": np.log(d.pib_pc.clip(lower=1)), "c": 1.0}
    if area: c["larea"] = np.log(d.area_total.clip(lower=1))
    return pd.concat([pd.DataFrame(c), uf], axis=1)
def par(a, b, area=False, x=None):
    x = d if x is None else x; C = CTL(area).reindex(x.index)
    m = x[a].notna() & x[b].notna() & C.notna().all(axis=1)
    if m.sum() < 150: return np.nan, int(m.sum())
    X = C[m].values; r = []
    for col in (a, b):
        y = pd.Series(x.loc[m, col].values).rank().values
        beta,*_ = np.linalg.lstsq(X, y, rcond=None); r.append(y - X@beta)
    return round(float(np.corrcoef(r[0], r[1])[0,1]), 3), int(m.sum())
def bru(a, b, x=None):
    x = d if x is None else x; s = x[[a,b]].dropna()
    return (round(s[a].rank().corr(s[b].rank()),3), len(s)) if len(s)>2 else (np.nan,len(s))
def linha(tag, a, b, area=False):
    rb,nb = bru(a,b); rp,np_ = par(a,b,area)
    print(f"  {tag:6s} {a:22s} × {b:22s} bruto {rb:+.3f} (n{nb:5d})  parcial {rp:+.3f}")

print("="*78); print("H24 · SNIS auto-declarado × base IBGE (2021)"); print("="*78)
d["snis_gap_agua"] = d.snis_agua_decl / d.snis_agua_ibge.replace(0,np.nan)
d["snis_cob_agua"] = d.snis_agua_decl / d.snis_pop_urb.replace(0,np.nan)
g = d.snis_gap_agua.dropna()
print(f"  razão declarado/IBGE: n={len(g)}  mediana {g.median():.3f}  "
      f"p10 {g.quantile(.1):.3f}  p90 {g.quantile(.9):.3f}")
print(f"  municípios que declaram MAIS que o IBGE: {(g>1.02).sum()} ({(g>1.02).mean():.1%})")
print(f"  que declaram MENOS: {(g<0.98).sum()} ({(g<0.98).mean():.1%})")
for b in ["ibc","pib_pc","nbf_share_dom","formalidade","munic_vinculos"]:
    if b in d.columns: linha("H24", "snis_gap_agua", b)

print("\n"+"="*78); print("H25 · MUNIC declarado × SICONFI executado"); print("="*78)
d["munic_vinc_pc"] = d.munic_vinculos/d.populacao
d["sic_pessoal_pc"] = d.sic_pessoal/d.populacao
d["custo_por_vinculo"] = d.sic_pessoal/d.munic_vinculos.replace(0,np.nan)
for b in ["sic_pessoal_pc","pib_pc","nbf_share_dom"]: linha("H25","munic_vinc_pc",b)
c = d.custo_por_vinculo.dropna()
print(f"  custo anual por vínculo declarado: mediana R$ {c.median():,.0f}  "
      f"p10 {c.quantile(.1):,.0f}  p90 {c.quantile(.9):,.0f}  (razão p90/p10 {c.quantile(.9)/c.quantile(.1):.1f}×)")

print("\n"+"="*78); print("H26 · CNES leito DECLARADO × SIH internação FATURADA"); print("="*78)
d["prod_por_leito"] = d.sih_internacoes/d.cnes_leitos.replace(0,np.nan)
d["leitos_1000"] = d.cnes_leitos/d.populacao*1000
print(f"  municípios com leito declarado: {int(d.cnes_leitos.notna().sum())}; "
      f"com internação faturada: {int(d.sih_internacoes.notna().sum())}")
z = d[(d.cnes_leitos>0)&(d.sih_internacoes.isna()|(d.sih_internacoes==0))]
print(f"  com leito declarado e ZERO internação: {len(z)}")
p = d.prod_por_leito.dropna()
print(f"  internações por leito/ano: mediana {p.median():.1f}  p10 {p.quantile(.1):.1f}  p90 {p.quantile(.9):.1f}")
for b in ["pib_pc","nbf_share_dom","cob_ab"]: linha("H26","prod_por_leito",b)

print("\n"+"="*78); print("H27 · CNO obra registrada × CNEFE domicílio em construção"); print("="*78)
d["cno_1000dom"] = d.cno_obras/d.cnefe_dom*1000
d["formal_obra"] = d.cno_obras/d.cnefe_construcao.replace(0,np.nan)
f = d.formal_obra.dropna()
print(f"  obras CNO por domicílio-em-construção do CNEFE: n={len(f)} mediana {f.median():.2f}")
for b in ["pib_pc","nbf_share_dom","obras_1000dom","formalidade"]: linha("H27","formal_obra",b)

print("\n"+"="*78); print("H28 · CAPAG × operação de crédito efetivamente contratada"); print("="*78)
d["op_cred_share"] = d.sic_op_credito/d.sic_receita_total.replace(0,np.nan)
ordem = {"A":4,"B":3,"B+":3,"C":2,"C+":2,"D":1}
d["capag_num"] = d.capag.map(ordem)
print(d.groupby("capag").agg(n=("capag","size"),
      op_cred_mediana=("op_cred_share","median"), pib_pc=("pib_pc","median")).to_string())
linha("H28","capag_num","op_cred_share")

print("\n"+"="*78); print("H29 · inidôneos do TCU recebendo pagamento municipal"); print("="*78)
d["share_pago_tcu"] = d.pag_tcu_valor/d.pag_total_valor.replace(0,np.nan)
print(f"  municípios com pagamento MIDES: {int(d.pag_total_valor.notna().sum())}; "
      f"que pagaram a inidôneo do TCU: {int((d.pag_tcu_n>0).sum())}")
print(f"  valor total pago a inidôneo: R$ {d.pag_tcu_valor.sum()/1e9:,.2f} bi "
      f"({100*d.pag_tcu_valor.sum()/d.pag_total_valor.sum():.3f}% do valor)")
for b in ["ebt_nota","nbf_share_dom","sanc_100k","share_pago_sancionado"]:
    if b in d.columns: linha("H29","share_pago_tcu",b)

print("\n"+"="*78); print("H32 · SISU: vaga onde há aluno ou onde há campus?"); print("="*78)
d["sisu_pc"] = d.sisu_vagas/d.populacao*1000
d["ies_pc"] = d.ies_n/d.populacao*1e5
print(f"  municípios com vaga SISU: {int(d.sisu_vagas.notna().sum())} de 5.570")
for b in ["nbf_share_dom","pib_pc","ies_n","formalidade"]: linha("H32","sisu_pc",b)

print("\n"+"="*78); print("H36 · CNJ improbidade por UF × capacidade de registro"); print("="*78)
cnj = L("v_cnj_uf")
ufp = d.groupby("sigla_uf").agg(pop=("populacao","sum"), pib=("pib","sum"),
        sanc=("sanc_n","sum"), cauc=("nbf_familias","sum")).reset_index()
u = cnj.merge(ufp, on="sigla_uf")
u["cnj_100k"] = u.cnj_condenacoes/u["pop"]*1e5
u["pib_pc"] = u["pib"]/u["pop"]
print(u[["sigla_uf","cnj_condenacoes","cnj_comarcas","cnj_100k"]]
      .sort_values("cnj_100k",ascending=False).head(6).to_string(index=False))
for b in ["pib_pc","cnj_comarcas"]:
    s = u[["cnj_100k",b]].dropna()
    print(f"  cnj_100k × {b:14s} r = {s.cnj_100k.rank().corr(s[b].rank()):+.3f} (n={len(s)})")

d.to_csv(INE/"painel_inedito.csv", index=False)
print(f"\npainel_inedito.csv gravado ({d.shape[1]} colunas)")
