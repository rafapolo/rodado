"""Robustez: suporte comum de margem 2022 + dummies de faixa de margem (2,5 pp) + FE UF.
Lê out/painel_vira_casaca.csv e out/univariado.csv gerados por analise.py."""
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
import warnings; warnings.filterwarnings("ignore")
SP = Path(__file__).parent; OUT = SP / "out"
M = pd.read_csv(OUT / "painel_vira_casaca.csv", dtype={"id_municipio": str}, low_memory=False)
T = pd.read_csv(OUT / "univariado.csv")
print("caged_pc_2019 não nulos:", M.caged_pc_2019.notna().sum())
G = M[M.vira | M.mantido].copy(); G["y"] = G.vira.astype(int)
S = G[G.margem22 <= G.loc[G.y == 1, "margem22"].max()].copy()
S["faixa"] = (S.margem22 // 2.5).astype(int).astype(str)
print(f"suporte comum: vira={S.y.sum()} mantido={(S.y==0).sum()}")
DROP = {"log_densidade"}
CTRL = ["log_pop", "log_pib_pc", "log_area"]
rows = []
for x in T.indicador:
    if x in DROP: continue
    ctrl = [c for c in CTRL if c != x]
    d = S[["y", x, "uf", "faixa"] + ctrl].dropna()
    if len(d) < 100 or d[x].std() == 0: continue
    X = pd.DataFrame({"x": (d[x] - d[x].mean()) / d[x].std()}).join(d[ctrl])
    X = X.join(pd.get_dummies(d.uf, prefix="uf", drop_first=True, dtype=float))
    X = X.join(pd.get_dummies(d.faixa, prefix="f", drop_first=True, dtype=float))
    r = sm.OLS(d.y.astype(float), sm.add_constant(X)).fit(cov_type="HC1")
    rows.append(dict(indicador=x, n_suporte=len(d), coef_suporte_faixas=r.params["x"], p_suporte=r.pvalues["x"]))
R = pd.DataFrame(rows); R["p_suporte_adj"] = multipletests(R.p_suporte, method="fdr_bh")[1]
T = T.merge(R, on="indicador", how="left")
T["sobrevive_suporte"] = (T.p_adj < .05) & (np.sign(T.coef_suporte_faixas) == np.sign(T.rank_biserial)) & (T.p_suporte_adj < .05)
T.to_csv(OUT / "univariado_robusto.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
c = ["indicador","n_vira","n_mantido","mediana_vira","mediana_mantido","rank_biserial","rb_faixa_margem","p_adj",
     "sobrevive_uf_porte","coef_suporte_faixas","p_suporte_adj","sobrevive_suporte"]
print("sobrevivem suporte+faixas:", T.sobrevive_suporte.sum())
print(T[T.sobrevive_suporte][c].round(3).to_string())
print("\nRAIS/econ:")
econ = T[T.indicador.str.startswith("rais_") | T.indicador.isin(["share_agro","share_ind","share_serv","credito_pc","credito_ha","va_agro_ha","cfem_pc","pib_pc","rem_media","agro_1000dom","formalidade","caged_pc_2017_2021","caged_pc_2022_2024"])]
print(econ[c].head(30).round(3).to_string())

# contínuo: R2 ajustado nos dois modelos
K = pd.read_csv(OUT / "continuo.csv")
inds = [f for f in T.indicador if f not in DROP and M[f].notna().mean() >= .7 and f not in ("log_pop","log_area")]
d = M.dropna(subset=["d_lula", "log_pop"])
FE = pd.get_dummies(d.uf, drop_first=True, dtype=float)
r_uf = sm.OLS(d.d_lula, sm.add_constant(FE)).fit().rsquared_adj
r_b = sm.OLS(d.d_lula, sm.add_constant(FE.join(d[["log_pop","plula22"]]))).fit().rsquared_adj
r_f = sm.OLS(d.d_lula, sm.add_constant(FE.join(d[["log_pop","plula22"]]).join(d[inds].fillna(d[inds].median())))).fit().rsquared_adj
print(f"\nΔlula R2 ajustado: UF={r_uf:.3f}; +porte+plula22={r_b:.3f}; +{len(inds)} indicadores={r_f:.3f}; n={len(d)}")
print("Δlula médio vira / mantido / Lula-perdeu-2022:", G[G.y==1].d_lula.mean().round(2), G[G.y==0].d_lula.mean().round(2), M[~M.lula22_venceu].d_lula.mean().round(2))
Kc = K[~K.indicador.isin(DROP)]
print(Kc[Kc.indicador.str.startswith("rais_") | Kc.indicador.isin(["share_agro","credito_pc","share_ind","share_serv","cfem_pc","pib_pc"])].head(20).round(3).to_string())
