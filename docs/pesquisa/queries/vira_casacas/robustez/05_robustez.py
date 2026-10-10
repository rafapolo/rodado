"""Modelos esparsos (~10 indicadores), AUC na faixa de margem, MG sozinho, porte na faixa."""
import numpy as np, pandas as pd, warnings
from scipy import stats
from sklearn.linear_model import LogisticRegression, Lasso, LinearRegression
from sklearn.model_selection import StratifiedKFold, KFold, GroupKFold, cross_val_predict
from sklearn.metrics import roc_auc_score, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
warnings.filterwarnings("ignore")
SP = str(__import__('pathlib').Path(__file__).parent / 'out')
d = pd.read_parquet(f"{SP}/painel_analitico_pd.parquet")
res = pd.read_csv(f"{SP}/resultado_indicadores.csv")
DUP = {"rais_div_84","rais_div_85","rais_sec_T","rais_sec_U"}
REG = {"reclam_100k","tempo_resposta","nota_consumidor","autos_100k","sanc_100k","ebt_nota","fef_share_grave"}
VARS = [v for v in res["var"] if v not in DUP and v not in REG]
X = d[VARS].replace([np.inf,-np.inf],np.nan).apply(lambda s: pd.Series(stats.norm.ppf((s.rank()-0.5)/s.notna().sum()), index=s.index)).fillna(0.0)
UF = pd.get_dummies(d.uf, prefix="uf", dtype=float)
m = d.grupo.isin(["vira","LL"]); y = (d.grupo[m]=="vira").astype(int).values
skf = StratifiedKFold(5, shuffle=True, random_state=0)
sc = StandardScaler().fit(X[m]); Xs = sc.transform(X[m])
# caminho L1 só nos indicadores, procura C com ~10 não nulos
for C in [0.002,0.003,0.004,0.005,0.007,0.01]:
    lr = LogisticRegression(penalty="l1", solver="liblinear", C=C).fit(Xs, y)
    nz = (lr.coef_[0]!=0).sum()
    if nz >= 8: break
coef = pd.Series(lr.coef_[0], index=VARS); sel = coef[coef!=0].sort_values(key=abs, ascending=False)
print(f"L1 esparso (C={C}) -> {len(sel)} indicadores:\n", sel.round(3).to_string())
S = list(sel.index)
B0 = pd.concat([d[["log_pop"]], UF], axis=1)
def auc(M, mask, yy):
    mdl = make_pipeline(StandardScaler(), LogisticRegression(max_iter=5000, C=1.0))
    return roc_auc_score(yy, cross_val_predict(mdl, M[mask].values, yy, cv=skf, method="predict_proba")[:,1])
print("\nAUC (sem margem22) log_pop+UF:", round(auc(B0, m, y),3), "| só os esparsos:", round(auc(X[S], m, y),3),
      "| log_pop+UF+esparsos:", round(auc(pd.concat([B0, X[S]],axis=1), m, y),3))
# faixa: LL com margem22 na faixa dos vira (<= p95 dos vira)
hi = d.loc[d.grupo=="vira","margem22"].quantile(0.95)
f = d.grupo.isin(["vira","LL"]) & (d.margem22>0) & (d.margem22<=hi)
yf = (d.grupo[f]=="vira").astype(int).values
print(f"\nfaixa margem22 (0,{hi:.1f}]: vira={yf.sum()} LL={len(yf)-yf.sum()}")
print("  mediana log_pop vira/LL:", d[f&(d.grupo=='vira')].log_pop.median().round(2), d[f&(d.grupo=='LL')].log_pop.median().round(2),
      "| pop mediana:", int(d[f&(d.grupo=='vira')].pop_censo22.median()), int(d[f&(d.grupo=='LL')].pop_censo22.median()))
print("  AUC margem22 só:", round(auc(d[["margem22"]], f, yf),3), "| log_pop+UF:", round(auc(B0, f, yf),3),
      "| margem22+log_pop+UF:", round(auc(pd.concat([d[['margem22']],B0],axis=1), f, yf),3),
      "| margem22+log_pop+UF+esparsos:", round(auc(pd.concat([d[['margem22']],B0,X[S]],axis=1), f, yf),3))
# contínuo esparso
ya = d.d_lula.values; kf = KFold(5, shuffle=True, random_state=0)
Xa = StandardScaler().fit_transform(X)
for a in [0.2,0.15,0.1,0.08,0.06]:
    la = Lasso(alpha=a).fit(Xa, ya); nz=(la.coef_!=0).sum()
    if nz>=8: break
ca = pd.Series(la.coef_, index=VARS); sa = ca[ca!=0].sort_values(key=abs, ascending=False)
print(f"\nLasso contínuo d_lula (alpha={a}) -> {len(sa)} indicadores (p.p. por DP):\n", sa.round(3).to_string())
def r2(M):
    return r2_score(ya, cross_val_predict(make_pipeline(StandardScaler(), LinearRegression()), M, ya, cv=kf))
Ba = pd.concat([d[["log_pop","plula22"]], UF], axis=1)
print("R² CV base:", round(r2(Ba.values),3), "| base+esparsos:", round(r2(pd.concat([Ba, X[list(sa.index)]],axis=1).values),3),
      "| só esparsos+log_pop+plula22 (sem UF):", round(r2(pd.concat([d[['log_pop','plula22']], X[list(sa.index)]],axis=1).values),3))
# MG sozinho
REP = ["nbf_share_dom","c22_share_branca","pix_ticket_pf","credito_pc","pib_pc","share_agro","rais_sec_A","rais_share_publico","rais_sec_C","c22_share_60mais","log_densidade","rais_emprego_formal_pc"]
mg = d[d.uf=="MG"]; a_ = mg[mg.grupo=="vira"]; b_ = mg[mg.grupo=="LL"]
print(f"\nMG: vira={len(a_)} LL={len(b_)} | margem22 mediana vira/LL: {a_.margem22.median():.1f} / {b_.margem22.median():.1f}")
from statsmodels.stats.multitest import multipletests
rows=[]
for v in REP:
    x,z = a_[v].dropna(), b_[v].dropna(); u,p = stats.mannwhitneyu(x,z)
    rows.append((v, x.median(), z.median(), 2*u/(len(x)*len(z))-1, p))
t = pd.DataFrame(rows, columns=["var","med_vira","med_LL","rbis","p"]); t["q"]=multipletests(t.p,method="fdr_bh")[1]
print(t.round(4).to_string(index=False))
# fragmentação: Flávio/direita por grupo
print("\npflavio/pdir por grupo:", d.groupby("grupo").apply(lambda g: (g.pflavio26/g.pdir).median()).round(3).to_dict())
