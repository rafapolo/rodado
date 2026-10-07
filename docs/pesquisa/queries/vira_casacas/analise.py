"""Vira-casacas 2022->2026: perfil municipal.
uv run --with statsmodels --with polars --with scikit-learn --with scipy --with pandas --with pyarrow python analise.py
"""
import json, unicodedata, re
from pathlib import Path
import numpy as np, pandas as pd, polars as pl
from scipy.stats import mannwhitneyu
from scipy.spatial import cKDTree
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
import warnings; warnings.filterwarnings("ignore")

SP = Path(__file__).parent
OUT = SP / "out"; OUT.mkdir(exist_ok=True)
ELEI = Path.home() / "Projetos/xyz/dataviz/eleicoes/data_presidente_2026.json"
PAINEL = Path.home() / "Projetos/rodado/.hipoteses/20260906_blocof/painel.csv"

def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", s)

# ------------------------------------------------------------- eleição e grupos
cols = ["uf","nome","lat","lon","tot","lean","polar","ncand","w1","w1pct","w2","w2pct",
        "pesq","pcen","pdir","plula26","pflavio26","plula22","pbolso22"]
E = pd.DataFrame(json.load(open(ELEI)), columns=cols)
print("registros eleição:", len(E))
sem22 = E[E.plula22.isna() | E.pbolso22.isna()]
print("sem 2022 (excluídos):", sem22[["uf","nome"]].values.tolist())
E = E.dropna(subset=["plula22","pbolso22"]).copy()
E["lula22_venceu"] = E.plula22 > E.pbolso22
E["flavio26_venceu"] = E.pflavio26 > E.plula26
E["vira"] = E.lula22_venceu & E.flavio26_venceu
E["mantido"] = E.lula22_venceu & (E.plula26 > E.pflavio26)
empt = E[E.lula22_venceu & (E.plula26 == E.pflavio26)]
print("empates 2026 (1 casa) entre Lula22, excluídos dos grupos:", empt[["uf","nome","w1"]].values.tolist())
E["inverso"] = (E.pbolso22 > E.plula22) & (E.plula26 > E.pflavio26)
emp22 = int((E.plula22 == E.pbolso22).sum()); emp26 = int((E.plula26 == E.pflavio26).sum())
nv, nm, ninv = int(E.vira.sum()), int(E.mantido.sum()), int(E.inverso.sum())
# contagem independente: w1 começa com Flávio entre os que Lula ganhou em 2022
nv2 = int((E.lula22_venceu & E.w1.str.startswith("Flávio")).sum())
print(f"vira={nv} (via w1: {nv2}) mantido={nm} inverso={ninv} lula22={int(E.lula22_venceu.sum())} empates22={emp22} empates26={emp26}")
assert nv == 703 and nm == 2661 and ninv == 0 and nv + nm + len(empt) == E.lula22_venceu.sum()
E["margem22"] = E.plula22 - E.pbolso22
E["margem26"] = E.plula26 - E.pflavio26
E["margem26_dir"] = E.plula26 - E.pdir
E["d_lula"] = E.plula26 - E.plula22
E["d_margem"] = E.margem26 - E.margem22
E["d_margem_dir"] = E.margem26_dir - E.margem22

# ------------------------------------------------------------- pareamento
D = pd.read_csv(SP / "diretorio.csv", dtype={"id_municipio": str})
xy = D.centroide.str.extract(r"POINT \(([-\d.]+) ([-\d.]+)\)").astype(float)
D["lon"], D["lat"] = xy[0].round(4), xy[1].round(4)
tree = cKDTree(D[["lat","lon"]].values)
dist, idx = tree.query(E[["lat","lon"]].values)
E["id_geo"] = np.where(dist < 1e-3, D.id_municipio.values[idx], None)
D["k"] = D.sigla_uf + "|" + D.nome.map(norm)
kmap = D.drop_duplicates("k").set_index("k").id_municipio
E["id_nome"] = (E.uf + "|" + E.nome.map(norm)).map(kmap)
concord = int((E.id_geo == E.id_nome).sum())
print(f"pareamento: geo={E.id_geo.notna().sum()} nome={E.id_nome.notna().sum()} concordam={concord}")
diverg = E[(E.id_geo != E.id_nome)][["uf","nome","id_geo","id_nome"]]
print("divergentes/sem par:", diverg.values.tolist())
E["id_municipio"] = E.id_geo.fillna(E.id_nome)
assert E.id_municipio.is_unique, "id duplicado"

# ------------------------------------------------------------- painel
P = pl.read_csv(PAINEL, infer_schema_length=20000, schema_overrides={"id_municipio": pl.Utf8}).to_pandas()
P["id_municipio"] = P.id_municipio.astype(str).str.zfill(7)
INTENSIVAS = [
 "pib_pc","share_agro","share_ind","formalidade","homic_100k","suic_100k","ip_100k",
 "transito_100k","infec_100k","homic_juv_100k","gap_sexo","relig_100k","templos_1000dom",
 "obras_1000dom","agro_1000dom","saude_1000dom","comercio_por_dom","dom_por_cep",
 "nbf_share_dom","pix_pag_pc","pix_ticket_pf","pix_penetracao","pix_razao_rec_pag",
 "cfem_pc","gd_por_domicilio","deter_share_area","autos_100k","credito_pc","credito_ha",
 "va_agro_ha","cafir_ha_por_imovel","pdm_share","defeso_share","div_nomes","sanc_100k",
 "cresc_pop","d_ivs","pbf_2019_2006","reclam_100k","mides_credores_pc","mides_valor_pc",
 "share_pago_sancionado","share_credor_local","fef_montante_pc","fef_share_grave",
 "comex_choque_pct","pbf_choque_pct","caged_pc_2019","caged_pc_2020","caged_pc_2017_2021",
 "caged_pc_2022_2024","saude_share_terceirizado","sih_share_retencao","sih_valor_aih_mediano",
 "mides_jaccard_credor","entrantes_share_sancionado","entrantes_share_nao_local",
 "sinasc_share_mae_adolescente","cfem_razao_2225_1721","d_caged_mineracao_pc",
 "rem_media","ibc","cobertura_pop_4g5g","fibra","densidade_smp","hhi_smp",
 "cob_ab","cob_esf","cob_priv","vac_polio","ivs_2000","ivs_2010","idhm_2010",
 "nota_consumidor","tempo_resposta","ebt_nota","share_nome_top","capital_social_mediano",
 "pncp_valor_mediano","comex_hhi_sh4_2019","rais_hhi_cbo_fem","ideb","taxa_aprovacao",
 "cauc_pendencias","troca_partido_2016_2020",
]
INTENSIVAS = [c for c in INTENSIVAS if c in P.columns]
P["share_serv"] = P.va_servicos / P.pib
P["log_area"] = np.log(P.area_total.where(P.area_total > 0))
P["log_densidade"] = np.log(P.populacao / P.area_total.where(P.area_total > 0))
base = P[["id_municipio","nome_regiao_imediata","populacao","area_total"] + INTENSIVAS + ["share_serv","log_area","log_densidade"]]

C = pd.read_csv(SP / "censo2022.csv", dtype={"id_municipio": str})

# RAIS 2024: seção CNAE a partir da divisão
R = pd.read_csv(SP / "rais2024_mun_divisao.csv", dtype={"id_municipio": str, "divisao": str})
R = R[R.id_municipio.str.len() == 7]
def secao(dv):
    if not isinstance(dv, str): return None
    d = int(dv)
    for lo, hi, s in [(1,3,"A_agro"),(5,9,"B_extrativa"),(10,33,"C_transformacao"),(35,35,"D_energia"),
                      (36,39,"E_saneamento"),(41,43,"F_construcao"),(45,47,"G_comercio"),(49,53,"H_transporte"),
                      (55,56,"I_alojamento_alim"),(58,63,"J_informacao"),(64,66,"K_financeiro"),(68,68,"L_imobiliario"),
                      (69,75,"M_profissional"),(77,82,"N_administrativo"),(84,84,"O_adm_publica"),(85,85,"P_educacao"),
                      (86,88,"Q_saude"),(90,93,"R_artes"),(94,96,"S_outros_serv"),(97,97,"T_domestico"),(99,99,"U_intl")]:
        if lo <= d <= hi: return s
R["secao"] = R.divisao.map(secao)
tot = R.groupby("id_municipio").agg(rais_vinc=("vinc","sum"), rais_vinc_pub=("vinc_pub","sum"), rais_estab=("estab_ativos","sum"))
sec = R.pivot_table(index="id_municipio", columns="secao", values="vinc", aggfunc="sum", fill_value=0)
sec = sec.div(tot.rais_vinc, axis=0).add_prefix("rais_sec_")
nat = R.groupby("divisao").vinc.sum() / R.vinc.sum()
pres = R[R.vinc > 0].groupby("divisao").id_municipio.nunique() / R.id_municipio.nunique()
divs_ok = sorted(set(nat[nat >= 0.005].index) | set(pres[pres >= 0.5].index))
dv = R[R.divisao.isin(divs_ok)].pivot_table(index="id_municipio", columns="divisao", values="vinc", aggfunc="sum", fill_value=0)
dv = dv.reindex(tot.index, fill_value=0).div(tot.rais_vinc, axis=0).add_prefix("rais_div_")
rais = tot.join(sec).join(dv).reset_index()
print(f"RAIS: {len(rais)} municípios, {len(divs_ok)} divisões no filtro, vinc total {R.vinc.sum():,}")

M = (E.merge(base, on="id_municipio", how="left").merge(C, on="id_municipio", how="left")
      .merge(rais, on="id_municipio", how="left"))
M["rais_share_publico"] = M.rais_vinc_pub / M.rais_vinc
M["rais_vinc_pc"] = M.rais_vinc / M.pop_censo22
M["log_pop"] = np.log(M.pop_censo22)
M["log_eleitores"] = np.log(M.tot)
M["log_pib_pc"] = np.log(M.pib_pc.where(M.pib_pc > 0))
print("casados com painel:", M.pib_pc.notna().sum(), "| censo:", M.pop_censo22.notna().sum(), "| rais:", M.rais_vinc.notna().sum())
M = M.merge(D[["id_municipio","nome_regiao"]], on="id_municipio", how="left")
M.to_csv(OUT / "painel_vira_casaca.csv", index=False)

FEATS = (INTENSIVAS + ["share_serv","log_area","log_densidade","log_pop"]
         + [c for c in C.columns if c.startswith("c22_")]
         + [c for c in M.columns if c.startswith("rais_sec_") or c.startswith("rais_div_")]
         + ["rais_share_publico","rais_vinc_pc"])
FEATS = [f for f in dict.fromkeys(FEATS) if f not in ("rais_sec_U_intl",)]
strs = [f for f in FEATS if not pd.api.types.is_numeric_dtype(M[f])]
print("não numéricas (coagidas):", strs)
for f in FEATS: M[f] = pd.to_numeric(M[f], errors="coerce")
M[FEATS] = M[FEATS].replace([np.inf, -np.inf], np.nan)
print("indicadores testados:", len(FEATS))

# ------------------------------------------------------------- distribuição de margens
G = M[M.vira | M.mantido].copy()
G["y"] = G.vira.astype(int)
q = lambda s: s.quantile([.1,.25,.5,.75,.9]).round(1).tolist()
with open(OUT / "margens.txt", "w") as f:
    for nm_, g in [("vira", G[G.y==1]), ("mantido", G[G.y==0])]:
        f.write(f"{nm_} n={len(g)} margem22 p10..p90={q(g.margem22)} margem26={q(g.margem26)} "
                f"margem26_vs_direita={q(g.margem26_dir)} d_lula={q(g.d_lula)}\n")
    v = G[G.y==1]
    f.write(f"vira: |margem26|<2pp: {(v.margem26.abs()<2).mean():.1%}; <5pp: {(v.margem26.abs()<5).mean():.1%}; "
            f"margem22<10pp: {(v.margem22<10).mean():.1%}; <20pp: {(v.margem22<20).mean():.1%}\n")
    f.write(f"vira: lula26 < pdir (direita somada > lula): {(v.plula26 < v.pdir).mean():.1%}\n")
    f.write(f"todos: d_lula mediana={M.d_lula.median():.1f} pp; vira={v.d_lula.median():.1f}; mantido={G[G.y==0].d_lula.median():.1f}\n")
    f.write(f"vira: d_lula<0: {(v.d_lula<0).mean():.1%}; pflavio26-pbolso22 mediana={(v.pflavio26-v.pbolso22).median():.1f}\n")
    f.write(f"faixa margem22 vira: min={v.margem22.min()} max={v.margem22.max()}; mantidos dentro dessa faixa: {(G[G.y==0].margem22<=v.margem22.max()).sum()}\n")
print(open(OUT / "margens.txt").read())

# ------------------------------------------------------------- geografia
geo_uf = (G.groupby("uf").agg(lula22=("y","size"), vira=("y","sum")).assign(taxa=lambda d: d.vira/d.lula22)
          .join(M.groupby("uf").size().rename("municipios")).sort_values("vira", ascending=False))
geo_reg = (G.groupby("nome_regiao").agg(lula22=("y","size"), vira=("y","sum")).assign(taxa=lambda d: d.vira/d.lula22)
           .join(M.groupby("nome_regiao").size().rename("municipios")).sort_values("vira", ascending=False))
geo_uf.to_csv(OUT / "geo_uf.csv"); geo_reg.to_csv(OUT / "geo_regiao.csv")
print(geo_reg); print(geo_uf)

# ------------------------------------------------------------- univariado + controles
uf_mixed = geo_uf[(geo_uf.vira > 0) & (geo_uf.vira < geo_uf.lula22)].index
def ols_coef(df, x, ctrl, y="y", fe=True):
    d = df[[y, x, "uf"] + ctrl].dropna()
    if d[x].std() == 0 or len(d) < 50: return np.nan, np.nan, len(d)
    X = pd.DataFrame({"x": (d[x] - d[x].mean()) / d[x].std()})
    for c in ctrl: X[c] = d[c]
    if fe: X = X.join(pd.get_dummies(d.uf, prefix="uf", drop_first=True, dtype=float))
    X = sm.add_constant(X)
    r = sm.OLS(d[y].astype(float), X).fit(cov_type="HC1")
    return r.params["x"], r.pvalues["x"], len(d)

Gm = G[G.uf.isin(uf_mixed)]
band = G[(G.margem22 <= G[G.y==1].margem22.quantile(.95))]
rows = []
CTRL = ["log_pop", "log_pib_pc", "log_area"]
for x in FEATS:
    a, b = G.loc[G.y==1, x].dropna(), G.loc[G.y==0, x].dropna()
    if len(a) < 30 or len(b) < 30 or pd.concat([a, b]).nunique() < 3: continue
    U, p = mannwhitneyu(a, b, alternative="two-sided")
    rb = 2 * U / (len(a) * len(b)) - 1                   # rank-biserial (>0: vira maior)
    ra, rbk = np.log1p(a - min(a.min(), b.min())), np.log1p(b - min(a.min(), b.min()))
    d_log = (ra.mean() - rbk.mean()) / np.sqrt((ra.var() + rbk.var()) / 2)
    ab, bb = band.loc[band.y==1, x].dropna(), band.loc[band.y==0, x].dropna()
    rb_band = 2 * mannwhitneyu(ab, bb).statistic / (len(ab) * len(bb)) - 1 if len(bb) > 30 else np.nan
    c1, p1, n1 = ols_coef(Gm, x, [c for c in CTRL if c != x])
    c2, p2, _ = ols_coef(Gm, x, [c for c in CTRL if c != x] + ["margem22"])
    rows.append(dict(indicador=x, n_vira=len(a), n_mantido=len(b), mediana_vira=a.median(), mediana_mantido=b.median(),
                     rank_biserial=rb, d_cohen_log=d_log, p_mw=p, rb_faixa_margem=rb_band,
                     lpm_coef_uf_porte=c1, p_lpm=p1, n_lpm=n1, lpm_coef_mais_margem22=c2, p_lpm_marg=p2))
T = pd.DataFrame(rows)
T["p_adj"] = multipletests(T.p_mw, method="fdr_bh")[1]
for pc in ["p_lpm", "p_lpm_marg"]:
    ok = T[pc].notna()
    T.loc[ok, pc + "_adj"] = multipletests(T.loc[ok, pc], method="fdr_bh")[1]
T["sobrevive_uf_porte"] = (np.sign(T.lpm_coef_uf_porte) == np.sign(T.rank_biserial)) & (T.p_lpm_adj < .05) & (T.p_adj < .05)
T["sobrevive_mais_margem22"] = T.sobrevive_uf_porte & (np.sign(T.lpm_coef_mais_margem22) == np.sign(T.rank_biserial)) & (T.p_lpm_marg_adj < .05)
T = T.sort_values("rank_biserial", key=abs, ascending=False)
T.to_csv(OUT / "univariado.csv", index=False)
print(f"testes: {len(T)}; p_adj<.05: {(T.p_adj<.05).sum()}; sobrevivem UF+porte: {T.sobrevive_uf_porte.sum()}; +margem22: {T.sobrevive_mais_margem22.sum()}")
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 20)
print(T.head(30)[["indicador","n_vira","n_mantido","mediana_vira","mediana_mantido","rank_biserial","rb_faixa_margem","p_adj","lpm_coef_uf_porte","p_lpm_adj","lpm_coef_mais_margem22","p_lpm_marg_adj","sobrevive_uf_porte","sobrevive_mais_margem22"]].round(3).to_string())
print("\nRAIS/CNAE:")
print(T[T.indicador.str.startswith("rais_")][["indicador","mediana_vira","mediana_mantido","rank_biserial","rb_faixa_margem","p_adj","lpm_coef_uf_porte","p_lpm_adj","lpm_coef_mais_margem22","p_lpm_marg_adj","sobrevive_uf_porte","sobrevive_mais_margem22"]].head(20).round(4).to_string())

# ------------------------------------------------------------- AUC (CV por região imediata)
def cv_auc(df, feats, l1=0.5, C=0.1, uf=True):
    d = df.copy()
    X = d[feats].copy()
    X = X.fillna(X.median())
    if uf: X = X.join(pd.get_dummies(d.uf, prefix="uf", dtype=float))
    y, grp = d.y.values, d.nome_regiao_imediata.fillna(d.uf).values
    pred = np.zeros(len(d))
    for tr, te in GroupKFold(n_splits=5).split(X, y, grp):
        m = make_pipeline(StandardScaler(), LogisticRegression(penalty="elasticnet", solver="saga", l1_ratio=l1, C=C, max_iter=5000))
        m.fit(X.iloc[tr], y[tr]); pred[te] = m.predict_proba(X.iloc[te])[:, 1]
    return roc_auc_score(y, pred)
inds = [f for f in FEATS if G[f].notna().mean() >= 0.7 and f not in ("log_pop","log_area")]
porte = ["log_pop", "log_area", "log_pib_pc"]
res = {}
for C_ in [0.02, 0.1, 0.5]:
    res[C_] = dict(
        so_uf=cv_auc(G, [], C=C_),
        porte_uf=cv_auc(G, porte, C=C_),
        porte_uf_indic=cv_auc(G, porte + inds, C=C_),
        indic_sem_uf=cv_auc(G, porte + inds, C=C_, uf=False),
        margem22=cv_auc(G, ["margem22"], C=C_, uf=False),
        margem22_porte_uf=cv_auc(G, ["margem22"] + porte, C=C_),
        margem22_porte_uf_indic=cv_auc(G, ["margem22"] + porte + inds, C=C_),
    )
A = pd.DataFrame(res).round(3); A.to_csv(OUT / "auc.csv"); print("\nAUC (GroupKFold por região imediata; colunas = C):\n", A)
# coeficientes do modelo completo (seleção)
X = G[porte + inds].fillna(G[porte + inds].median()).join(pd.get_dummies(G.uf, prefix="uf", dtype=float))
m = make_pipeline(StandardScaler(), LogisticRegression(penalty="elasticnet", solver="saga", l1_ratio=0.5, C=0.1, max_iter=5000)).fit(X, G.y)
coef = pd.Series(m[-1].coef_[0], index=X.columns)
coef = coef[coef != 0].sort_values(key=abs, ascending=False)
coef.to_csv(OUT / "enet_coef.csv"); print("\nelastic-net (C=.1) coef não nulos sem UF:", coef[~coef.index.str.startswith("uf_")].head(25).round(3).to_dict())
X2 = G[["margem22"] + porte + inds].fillna(G[["margem22"] + porte + inds].median()).join(pd.get_dummies(G.uf, prefix="uf", dtype=float))
m2 = make_pipeline(StandardScaler(), LogisticRegression(penalty="elasticnet", solver="saga", l1_ratio=0.5, C=0.1, max_iter=5000)).fit(X2, G.y)
coef2 = pd.Series(m2[-1].coef_[0], index=X2.columns); coef2 = coef2[coef2 != 0].sort_values(key=abs, ascending=False)
coef2.to_csv(OUT / "enet_coef_com_margem.csv"); print("\nelastic-net + margem22:", coef2[~coef2.index.str.startswith("uf_")].head(20).round(3).to_dict())

# ------------------------------------------------------------- contínuo (todos os municípios)
M["y_dl"] = M.d_lula; M["y_dm"] = M.d_margem_dir
rows = []
for x in FEATS:
    b1, p1, n1 = ols_coef(M, x, [c for c in ["log_pop", "plula22"] if c != x], y="y_dl")
    b2, p2, _ = ols_coef(M, x, [c for c in ["log_pop", "plula22"] if c != x], y="y_dm")
    r0 = M[[x, "d_lula"]].corr(method="spearman").iloc[0, 1]
    rows.append(dict(indicador=x, n=n1, spearman_bruto=r0, beta_dlula_pp_por_dp=b1, p_dlula=p1, beta_dmargem_dir=b2, p_dmargem=p2))
K = pd.DataFrame(rows).dropna(subset=["p_dlula"])
K["p_dlula_adj"] = multipletests(K.p_dlula, method="fdr_bh")[1]
K["p_dmargem_adj"] = multipletests(K.p_dmargem.fillna(1), method="fdr_bh")[1]
K = K.sort_values("beta_dlula_pp_por_dp", key=abs, ascending=False); K.to_csv(OUT / "continuo.csv", index=False)
print("\nContínuo Δ voto Lula (pp por 1 DP; FE UF + log_pop + plula22):")
print(K.head(25).round(3).to_string())
# R2 do contínuo
d = M[["d_lula", "uf", "log_pop", "plula22"] + inds].dropna(subset=["d_lula", "log_pop"])
Xb = sm.add_constant(pd.get_dummies(d.uf, drop_first=True, dtype=float).join(d[["log_pop", "plula22"]]))
r_base = sm.OLS(d.d_lula, Xb).fit().rsquared
Xf = Xb.join(d[inds].fillna(d[inds].median()))
r_full = sm.OLS(d.d_lula, Xf).fit().rsquared_adj
print(f"\nR2 Δlula: só UF={sm.OLS(d.d_lula, sm.add_constant(pd.get_dummies(d.uf, drop_first=True, dtype=float))).fit().rsquared:.3f}; UF+porte+plula22={r_base:.3f}; +{len(inds)} indicadores (R2 aj)={r_full:.3f}")

# ------------------------------------------------------------- colinearidade do top
top = T[T.sobrevive_uf_porte].indicador.head(15).tolist() or T.indicador.head(15).tolist()
Cm = G[top].corr(method="spearman").round(2); Cm.to_csv(OUT / "corr_top15.csv")
pares = [(a, b, Cm.loc[a, b]) for i, a in enumerate(top) for b in top[i+1:] if abs(Cm.loc[a, b]) > .7]
print("\npares |rho|>0.7 no top:", pares)
