"""Testes: univariado (MW + BH), faixa de margem, LPM com controles (UF FE + log pop + margem22, SE cluster região imediata),
contínuo d_lula em todos os municípios, geografia, lasso/AUC."""
import numpy as np, polars as pl, pandas as pd, warnings
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
warnings.filterwarnings("ignore")
SP = str(__import__('pathlib').Path(__file__).parent / 'out')
d = pl.read_parquet(f"{SP}/painel_analitico.parquet").to_pandas()
d = d[d.grupo != "sem2022"].copy()
NON = {"uf","nome","lat","lon","tot","lean","polar","ncand","w1","w1pct","w2","w2pct","pesq","pcen","pdir","plula26","pflavio26",
       "plula22","pbolso22","id_municipio","lat_d","lon_d","id_ll","nome_regiao","capital_uf","amazonia_legal","lula22","lula26",
       "margem22","margem26","margem26_dir","grupo","d_margem","d_lula","nome_regiao_imediata","populacao","area_total",
       "pop_censo22","rais_vinc","rais_ruidoso","log_pop"}
VARS = [c for c in d.columns if c not in NON and pd.api.types.is_numeric_dtype(d[c])]
VARS = [c for c in VARS if d[c].replace([np.inf,-np.inf],np.nan).isna().mean() <= 0.30]
dropped = [c for c in d.columns if c not in NON and pd.api.types.is_numeric_dtype(d[c]) and c not in VARS]
print("indicadores testados:", len(VARS), "| descartados por >30% NaN:", dropped)
d[VARS] = d[VARS].replace([np.inf,-np.inf], np.nan)
d["log_pop"] = np.log(d.pop_censo22)
# transformação rank→normal (robusta a cauda), global
def rnorm(s):
    r = s.rank(pct=True); n = s.notna().sum()
    return pd.Series(stats.norm.ppf((s.rank()-0.5)/n), index=s.index)
Z = pd.DataFrame({v: rnorm(d[v]) for v in VARS}, index=d.index)

V = d.grupo.eq("vira"); L = d.grupo.eq("LL")
print("\nN vira", V.sum(), "LL", L.sum())
# ---- distribuição das margens
for g in ["vira","LL"]:
    x = d[d.grupo==g]
    print(g, "margem22 p.p. quantis 10/25/50/75/90:", np.percentile(x.margem22,[10,25,50,75,90]).round(1),
          "| margem26:", np.percentile(x.margem26,[10,25,50,75,90]).round(1),
          "| d_lula:", np.percentile(x.d_lula,[10,25,50,75,90]).round(1))
print("vira com |margem26|<5pp:", (d[V].margem26.abs()<5).mean().round(3), "| <2pp:", (d[V].margem26.abs()<2).mean().round(3))
print("vira com margem22<10pp:", (d[V].margem22<10).mean().round(3), "| LL com margem22<10pp:", (d[L].margem22<10).mean().round(3))

def cohen(a,b):
    a,b=a.dropna(),b.dropna(); sp=np.sqrt(((len(a)-1)*a.var()+(len(b)-1)*b.var())/(len(a)+len(b)-2)); return (a.mean()-b.mean())/sp
def univ(mask_a, mask_b, tag):
    rows=[]
    for v in VARS:
        a,b = d.loc[mask_a,v].dropna(), d.loc[mask_b,v].dropna()
        if len(a)<30 or len(b)<30: continue
        u,pv = stats.mannwhitneyu(a,b)
        rows.append(dict(var=v, n_a=len(a), n_b=len(b), med_a=a.median(), med_b=b.median(),
                         d_rank=cohen(Z.loc[mask_a,v],Z.loc[mask_b,v]), d_raw=cohen(a,b),
                         rbis=2*u/(len(a)*len(b))-1, p=pv))
    t=pd.DataFrame(rows); t["q"]=multipletests(t.p,method="fdr_bh")[1]; t["tag"]=tag
    return t.sort_values("d_rank", key=abs, ascending=False)
u1 = univ(V, L, "vira_vs_LL"); u2 = univ(V, d.grupo.isin(["LL","BF","empate"]), "vira_vs_todos")
band = L & d.margem22.between(d[V].margem22.min(), d[V].margem22.quantile(0.95))
print("faixa de margem22 para LL comparável:", d[V].margem22.min().round(1), "a", d[V].margem22.quantile(0.95).round(1), "-> LL n =", band.sum())
u3 = univ(V, band, "vira_vs_LL_mesma_margem22")

# ---- LPM / logit com controles: y = vira (vs LL), x = z(var) + log_pop + margem22 + UF FE; cluster região imediata
sub = d[V|L].copy(); sub["y"]=V[V|L].astype(float)
UFD = pd.get_dummies(sub.uf, prefix="uf", drop_first=True, dtype=float)
cl = sub.nome_regiao_imediata.astype("category").cat.codes
def ctrl_reg(y, df, ufd, clus, extra_ctrl):
    rows=[]
    for v in VARS:
        X = pd.concat([Z.loc[df.index, v].rename("x"), df[extra_ctrl], ufd], axis=1)
        ok = X.notna().all(1) & y.notna()
        m = sm.OLS(y[ok], sm.add_constant(X[ok])).fit(cov_type="cluster", cov_kwds={"groups": clus[ok]})
        rows.append(dict(var=v, b=m.params["x"], se=m.bse["x"], p=m.pvalues["x"], n=int(ok.sum())))
    t=pd.DataFrame(rows); t["q"]=multipletests(t.p,method="fdr_bh")[1]; return t
c1 = ctrl_reg(sub.y, sub, UFD, cl, ["log_pop","margem22"]).rename(columns=lambda c: c if c=="var" else "lpm_"+c)
# contínuo: d_lula em todos (exceto sem2022), controles log_pop + plula22 + UF FE
UFA = pd.get_dummies(d.uf, prefix="uf", drop_first=True, dtype=float)
cla = d.nome_regiao_imediata.astype("category").cat.codes
c2 = ctrl_reg(d.d_lula, d, UFA, cla, ["log_pop","plula22"]).rename(columns=lambda c: c if c=="var" else "dl_"+c)
c3 = ctrl_reg(d.d_margem, d, UFA, cla, ["log_pop","margem22"]).rename(columns=lambda c: c if c=="var" else "dm_"+c)
# contínuo sem UF FE (para ver o que é só UF)
c4 = ctrl_reg(d.d_lula, d, pd.DataFrame(index=d.index), cla, ["log_pop","plula22"]).rename(columns=lambda c: c if c=="var" else "dlnoUF_"+c)
res = u1.merge(u3[["var","d_rank","q"]].rename(columns={"d_rank":"d_rank_faixa","q":"q_faixa"}), on="var") \
        .merge(u2[["var","d_rank","q"]].rename(columns={"d_rank":"d_rank_todos","q":"q_todos"}), on="var") \
        .merge(c1,on="var").merge(c2,on="var").merge(c3,on="var").merge(c4,on="var")
res["sobrevive"] = (res.q<0.05) & (res.lpm_q<0.05) & (np.sign(res.lpm_b)==np.sign(res.d_rank))
res.to_csv(f"{SP}/resultado_indicadores.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 300)
cols=["var","med_a","med_b","d_rank","q","d_rank_faixa","q_faixa","lpm_b","lpm_q","dl_b","dl_q","dlnoUF_b","sobrevive"]
print("\n=== top 40 por |d_rank| (vira vs LL) ===")
print(res[cols].head(40).round(4).to_string(index=False))
print("\nsignificativos univ q<.05:", (res.q<.05).sum(), "| LPM q<.05:", (res.lpm_q<.05).sum(), "| d_lula q<.05:", (res.dl_q<.05).sum(), "| sobrevivem:", res.sobrevive.sum())
print("\n=== top 25 por |t| LPM controlado ===")
res["lpm_t"]=res.lpm_b/res.lpm_se
print(res.sort_values("lpm_t",key=abs,ascending=False)[cols].head(25).round(4).to_string(index=False))
print("\n=== top 25 contínuo d_lula (UF FE) ===")
res["dl_t"]=res.dl_b/res.dl_se
print(res.sort_values("dl_t",key=abs,ascending=False)[["var","dl_b","dl_q","dlnoUF_b","dm_b","dm_q","d_rank","lpm_b"]].head(25).round(4).to_string(index=False))
d.to_parquet(f"{SP}/painel_analitico_pd.parquet")
