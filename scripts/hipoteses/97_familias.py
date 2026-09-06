#!/usr/bin/env python3
"""Analisa H46-H62 (blocos N-Q de tasks/hipoteses.md §5.5) — as sete famílias
com menos combinações ocupadas no gerador de inéditos.

Extração: scripts/hipoteses/60_familias_vazias.sql -> tasks/hipoteses_resultado/familias/
Painel base: tasks/hipoteses_resultado/20260906/painel.csv (OUT dir desta sessão).

  python3 scripts/hipoteses/97_familias.py
"""
import numpy as np, pandas as pd, unicodedata
from pathlib import Path

REPO=Path(__file__).resolve().parent.parent.parent
F=REPO/"tasks"/"hipoteses_resultado"/"familias"
d=pd.read_csv(REPO/"tasks"/"hipoteses_resultado"/"20260906"/"painel.csv",low_memory=False)
d=d.replace([np.inf,-np.inf],np.nan)

def mg(f, key="id_municipio"):
    x=pd.read_csv(F/f"{f}.csv",low_memory=False)
    x=x[x[key].notna()].copy(); x[key]=x[key].astype("int64")
    return x.drop_duplicates(key)
for f in ["v_pam_hhi","v_pevs","v_ppm","v_atlas","v_snis_prest","v_sicor_hhi",
          "v_fogo","v_sinasc","v_simet"]:
    d=d.merge(mg(f),on="id_municipio",how="left")
emb=mg("v_embargos","cod_municipio").rename(columns={"cod_municipio":"id_municipio"})
d=d.merge(emb,on="id_municipio",how="left")
sih=mg("v_sih_infec","mun6"); d["mun6"]=(d.id_municipio//10).astype("int64")
d=d.merge(sih,on="mun6",how="left")
ideb=pd.read_csv(F/"v_ideb.csv"); ideb=ideb[ideb.anos_escolares.astype(str).str.contains("iniciais",case=False,na=False)]
d=d.merge(ideb[["id_municipio","ideb"]].drop_duplicates("id_municipio"),on="id_municipio",how="left")
d=d.replace([np.inf,-np.inf],np.nan)
print(f"painel: {d.shape[0]} x {d.shape[1]}\n")

uf=pd.get_dummies(d["sigla_uf"],drop_first=True).astype(float)
def CTL(area=False):
    c={"lp":np.log(d.populacao.clip(lower=1)),"lpib":np.log(d.pib_pc.clip(lower=1)),"c":1.0}
    if area: c["larea"]=np.log(d.area_total.clip(lower=1))
    return pd.concat([pd.DataFrame(c),uf],axis=1)
def par(a,b,area=False):
    C=CTL(area); m=d[a].notna()&d[b].notna()&C.notna().all(axis=1)
    if m.sum()<150: return np.nan,int(m.sum())
    X=C[m].values; r=[]
    for col in (a,b):
        y=pd.Series(d.loc[m,col].values).rank().values
        beta,*_=np.linalg.lstsq(X,y,rcond=None); r.append(y-X@beta)
    return round(float(np.corrcoef(r[0],r[1])[0,1]),3),int(m.sum())
def L(tag,a,b,area=False):
    s=d[[a,b]].dropna()
    rb=round(s[a].rank().corr(s[b].rank()),3) if len(s)>2 else np.nan
    rp,n=par(a,b,area)
    print(f"  {tag:6s} {a:24s} × {b:22s} bruto {rb:+.3f} (n{len(s):5d})  parcial {rp:+.3f}")

# --- derivadas
pam=pd.read_csv(F/"v_pam_ano.csv")
pam["perda"]=1-pam.pam_colhida/pam.pam_plantada.replace(0,np.nan)
q=pam[(pam.ano>=2013)&(pam.pam_plantada>0)].groupby("id_municipio").agg(
    perda_med=("perda","median"), perda_max=("perda","max"), anos=("ano","size")).reset_index()
d=d.merge(q,on="id_municipio",how="left")
d["pevs_share"]=d.pevs_silvicultura/(d.pevs_silvicultura+d.pevs_extracao).replace(0,np.nan)
d["bov_por_ha"]=d.ppm_bovinos/d.area_total.replace(0,np.nan)
d["desmat_share"]=d.desmatado/d.area_total.replace(0,np.nan)
d["esgoto_ok"]=d.atlas_coleta_com_trat
d["snis_gap"]=None
d["emb_100k"]=d.emb_termos/d.populacao*1e5
d["cafir_ha_por_imovel"]=d.area_cafir/d.imoveis_cafir.replace(0,np.nan)
d["fogo_manejo"]=d.fogo_com_chuva/d.fogo_n.replace(0,np.nan)
# id_municipio_nascimento e' o municipio do HOSPITAL: municipio sem maternidade
# tem so' parto domiciliar (todos vaginais), e a mediana bruta cai a 3,5%.
# Com >=100 nascimentos a mediana vai a 59,7% e a agregada nacional e' 57,0%.
d.loc[d.nasc_n < 100, ["nasc_cesarea","nasc_cesarea_comercial","nasc_comercial",
                       "nasc_baixo_peso","nasc_mae_adolescente"]] = np.nan
d["cesarea"]=d.nasc_cesarea/d.nasc_n.replace(0,np.nan)
d["cesarea_comercial"]=d.nasc_cesarea_comercial/d.nasc_cesarea.replace(0,np.nan)
d["share_comercial"]=d.nasc_comercial/d.nasc_n.replace(0,np.nan)
d["baixo_peso"]=d.nasc_baixo_peso/d.nasc_n.replace(0,np.nan)
d["mae_adol"]=d.nasc_mae_adolescente/d.nasc_n.replace(0,np.nan)
d["sem_internet"]=1-d.simet_com_internet/d.simet_escolas.replace(0,np.nan)
d["sih_infec_share"]=d.sih_infecciosa/d.sih_total.replace(0,np.nan)

print("="*80);print("BLOCO N · AGROPECUÁRIA");print("="*80)
print("H46 · quebra de safra (1 - colhida/plantada), PAM 2013+")
p=d.perda_med.dropna(); print(f"  n={len(p)} mediana {p.median():.4f} p90 {p.quantile(.9):.4f}")
for b in ["defeso_share","credito_pc","nbf_share_dom"]: L("H46","perda_med",b)
print("H47 · concentração da pauta agrícola (HHI)")
for b in ["obitos_infecciosos","infec_100k","pib_pc","credito_pc"]: L("H47","pam_hhi",b)
print("H49 · silvicultura: estoque (PRODES) ou frente (DETER)?")
for b in ["desmat_share","deter_share_area","credito_ha"]: L("H49","pevs_share",b,area=True)
print("H50 · rebanho bovino por hectare")
for b in ["desmat_share","credito_ha","deter_share_area"]: L("H50","bov_por_ha",b,area=True)

print("\n"+"="*80);print("BLOCO O · SANEAMENTO");print("="*80)
print("H51 · Atlas ANA (modelado) × SNIS (declarado)")
print(f"  Atlas: n={int(d.atlas_coleta_com_trat.notna().sum())}, esgoto com coleta E tratamento mediana {d.atlas_coleta_com_trat.median():.1f}%")
for b in ["ibc","cobertura_pop_4g5g","pib_pc","nbf_share_dom"]: L("H51","esgoto_ok",b)
print("  (esgoto_ok e' 0 em 50% dos municipios — repetindo com atlas_sem_nada, continua)")
for b in ["ibc","cobertura_pop_4g5g","pib_pc","nbf_share_dom"]: L("H51b","atlas_sem_nada",b)
print("H52 · natureza jurídica do prestador")
if "snis_natureza" in d.columns:
    print(d.groupby("snis_natureza").agg(n=("snis_natureza","size"),
        esgoto_ok=("esgoto_ok","median"), pib=("pib_pc","median")).sort_values("n",ascending=False).head(6).to_string())
print("H53 · esgoto sem tratamento × internação infecciosa")
for b in ["sih_infec_share","infec_100k"]: L("H53","atlas_sem_nada",b)

print("\n"+"="*80);print("BLOCO P · FUNDIÁRIO E AMBIENTAL");print("="*80)
print("H55 · concentração de tomador do crédito rural")
h=d.sicor_hhi_tomador.dropna()
print(f"  n={len(h)} HHI mediana {h.median():.3f}; share do maior tomador mediana {d.sicor_share_top.median():.1%}")
for b in ["cafir_ha_por_imovel","credito_ha","pib_pc"]: L("H55","sicor_hhi_tomador",b)
print("H56 · embargo do IBAMA × tamanho da propriedade")
for b in ["cafir_ha_por_imovel","desmat_share","credito_ha"]: L("H56","emb_100k",b,area=True)
print("H58 · fogo de manejo (foco com chuva recente)")
f=d.fogo_manejo.dropna(); print(f"  n={len(f)} share de foco com ≤3 dias sem chuva: mediana {f.median():.3f}")
for b in ["credito_ha","desmat_share","bov_por_ha","pevs_share"]: L("H58","fogo_manejo",b)

print("\n"+"="*80);print("BLOCO Q · NATALIDADE E CONECTIVIDADE");print("="*80)
print("H59 · cesárea e horário comercial (SINASC 2021)")
print(f"  cesárea: mediana {d.cesarea.median():.1%} (n={int(d.cesarea.notna().sum())})")
print(f"  das cesáreas, share em horário comercial 8-17h: mediana {d.cesarea_comercial.median():.1%}")
print(f"  de TODOS os nascimentos, share 8-17h: mediana {d.share_comercial.median():.1%}  <- a linha de base")
for b in ["cob_priv","pib_pc","nbf_share_dom"]: L("H59","cesarea",b)
for b in ["cob_priv","pib_pc"]: L("H59b","cesarea_comercial",b)
print("H60 · baixo peso ao nascer")
for b in ["atlas_sem_nada","esgoto_ok","cob_ab","nbf_share_dom"]: L("H60","baixo_peso",b)
print("H62 · escola sem internet × IDEB")
print(f"  SIMET: n={int(d.sem_internet.notna().sum())}, share sem internet mediana {d.sem_internet.median():.1%}")
for b in ["ideb","pib_pc","nbf_share_dom"]: L("H62","sem_internet",b)
d.to_csv(F/"painel_familias.csv",index=False)
print(f"\npainel_familias.csv gravado ({d.shape[1]} colunas)")
