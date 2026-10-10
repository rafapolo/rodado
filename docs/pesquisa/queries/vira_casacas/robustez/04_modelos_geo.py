"""AUC/R² por validação cruzada (base vs base+indicadores, elastic net), colinearidade, bloco CNAE, geografia."""
import numpy as np, pandas as pd, warnings
from scipy import stats
from sklearn.linear_model import LogisticRegressionCV, LogisticRegression, ElasticNetCV, LinearRegression
from sklearn.model_selection import StratifiedKFold, GroupKFold, cross_val_predict, KFold
from sklearn.metrics import roc_auc_score, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
warnings.filterwarnings("ignore")
SP = str(__import__('pathlib').Path(__file__).parent / 'out')
d = pd.read_parquet(f"{SP}/painel_analitico_pd.parquet")
res = pd.read_csv(f"{SP}/resultado_indicadores.csv")
DUP = {"rais_div_84","rais_div_85","rais_sec_T","rais_sec_U"}   # 84≡O, 85≡P; T/U ~0 em quase todo município
VARS = [v for v in res["var"] if v not in DUP]
X = d[VARS].replace([np.inf,-np.inf],np.nan)
X = X.apply(lambda s: pd.Series(stats.norm.ppf((s.rank()-0.5)/s.notna().sum()), index=s.index))
X = X.fillna(0.0)  # imputação na mediana (0 em escala rank-normal)
UF = pd.get_dummies(d.uf, prefix="uf", dtype=float)
base = pd.concat([d[["log_pop","margem22"]], UF], axis=1)
m = d.grupo.isin(["vira","LL"]); y = (d.grupo[m]=="vira").astype(int).values
g = d.nome_regiao_imediata[m].values
def auc(Xm, cv, groups=None, C=None):
    if C is None:
        mdl = make_pipeline(StandardScaler(), LogisticRegression(max_iter=5000, C=1e3))
    else:
        mdl = make_pipeline(StandardScaler(), LogisticRegressionCV(Cs=10, penalty="elasticnet", solver="saga", l1_ratios=[0.5,1.0], max_iter=4000, cv=5, scoring="roc_auc", n_jobs=-1))
    p = cross_val_predict(mdl, Xm, y, cv=cv, groups=groups, method="predict_proba")[:,1]
    return roc_auc_score(y, p)
skf = StratifiedKFold(5, shuffle=True, random_state=0); gkf = GroupKFold(5)
B = base[m].values; F = pd.concat([base[m], X[m]], axis=1).values; O = X[m].values
B0 = pd.concat([d[["log_pop"]], UF], axis=1)[m].values
out = {}
out["só log_pop+UF"] = auc(B0, skf)
out["base (margem22+log_pop+UF)"] = auc(B, skf)
out["só indicadores (EN)"] = auc(O, skf, C="en")
out["só indicadores+log_pop+UF (EN)"] = auc(np.hstack([B0,O]), skf, C="en")
out["base+indicadores (EN)"] = auc(F, skf, C="en")
out["base (CV espacial reg. imediata)"] = auc(B, gkf, g)
out["base+indicadores (EN, CV espacial)"] = auc(F, gkf, g, C="en")
out["só indicadores+log_pop+UF (EN, CV espacial)"] = auc(np.hstack([B0,O]), gkf, g, C="en")
for k,v in out.items(): print(f"AUC {k}: {v:.3f}")
# coeficientes do EN ajustado em tudo (seleção)
en = make_pipeline(StandardScaler(), LogisticRegressionCV(Cs=10, penalty="elasticnet", solver="saga", l1_ratios=[1.0], max_iter=5000, cv=skf, scoring="roc_auc", n_jobs=-1)).fit(F, y)
names = list(base.columns) + VARS
coef = pd.Series(en[-1].coef_[0], index=names)
sel = coef[[n for n in VARS]].loc[lambda s: s!=0].sort_values(key=abs, ascending=False)
print(f"\nlasso (base+indicadores) selecionou {len(sel)} indicadores; top 20:\n", sel.head(20).round(3).to_string())
sel.to_csv(f"{SP}/lasso_selecao.csv")
# --- contínuo d_lula: R² CV
ya = d.d_lula.values; ga = d.nome_regiao_imediata.values
Ba = pd.concat([d[["log_pop","plula22"]], UF], axis=1).values; Fa = np.hstack([Ba, X.values])
kf = KFold(5, shuffle=True, random_state=0)
def r2(Xm, cv, groups=None, en=False):
    mdl = make_pipeline(StandardScaler(), ElasticNetCV(l1_ratio=[.5,1], cv=5, n_jobs=-1, max_iter=5000) if en else LinearRegression())
    return r2_score(ya, cross_val_predict(mdl, Xm, ya, cv=cv, groups=groups))
print("\nd_lula (n=%d): média %.2f dp %.2f" % (len(ya), ya.mean(), ya.std()))
print("R² CV só UF:", round(r2(UF.values, kf),3), "| base (plula22+log_pop+UF):", round(r2(Ba, kf),3),
      "| base+indicadores EN:", round(r2(Fa, kf, en=True),3), "| idem CV espacial:", round(r2(Fa, gkf, ga, en=True),3),
      "| base CV espacial:", round(r2(Ba, gkf, ga),3))
print("R² CV indicadores sem UF (EN):", round(r2(np.hstack([d[['log_pop','plula22']].values, X.values]), kf, en=True),3))
# --- colinearidade entre os que sobrevivem
surv = res[res.sobrevive & ~res["var"].isin(DUP)]["var"].tolist()
C = d[surv].replace([np.inf,-np.inf],np.nan).corr(method="spearman")
pairs = [(a,b,C.loc[a,b]) for i,a in enumerate(surv) for b in surv[i+1:] if abs(C.loc[a,b])>=0.6]
print("\npares |rho|>=0.6 entre sobreviventes:")
for a,b,r in sorted(pairs, key=lambda t:-abs(t[2])): print(f"  {a} ~ {b}: {r:.2f}")
# --- bloco CNAE
cn = res[res["var"].str.startswith("rais_") & ~res["var"].isin(DUP)].copy()
cn["dl_t"] = cn.dl_b/cn.dl_se
cn = cn.sort_values("d_rank", key=abs, ascending=False)
cn.to_csv(f"{SP}/resultado_cnae.csv", index=False)
pd.set_option("display.width", 250)
print("\n=== CNAE/RAIS (vira vs LL) ===")
print(cn[["var","med_a","med_b","d_rank","q","d_rank_faixa","q_faixa","lpm_b","lpm_q","dl_b","dl_q","dlnoUF_b"]].round(4).to_string(index=False))
# --- geografia
g2 = d[d.grupo.isin(["vira","LL"])].groupby(["nome_regiao","uf"]).grupo.value_counts().unstack(fill_value=0)
g2["taxa"] = g2.vira/(g2.vira+g2.LL)
tot = d.groupby("uf").agg(n=("grupo","size"), pflavio=("pflavio26","mean"), pdir=("pdir","mean"), plula26=("plula26","mean"), plula22=("plula22","mean"), d_lula=("d_lula","mean"))
tot["flavio_sobre_dir"] = tot.pflavio/tot.pdir
geo = g2.join(tot, on="uf").sort_values("vira", ascending=False)
print("\n=== UF ===\n", geo.round(3).to_string())
r2 = d[d.grupo.isin(["vira","LL"])].groupby("nome_regiao").grupo.value_counts().unstack(fill_value=0); r2["taxa"]=r2.vira/(r2.vira+r2.LL)
print("\n=== região ===\n", r2.round(3).to_string())
geo.to_csv(f"{SP}/geografia_uf.csv")
