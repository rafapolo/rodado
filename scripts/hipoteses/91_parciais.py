#!/usr/bin/env python3
"""Parciais para as hipoteses nomeadas que a varredura de 90_analise.py nao cobre.

A varredura so roda sobre variaveis INTENSIVAS, entao todo par com uma ponta
extensiva (H01, H02, H04, H05, H08, H16, H17...) sai de hipoteses.tsv com
r_parcial em branco. Aqui o parcial e' calculado para TODOS os pares nomeados,
com um controle a mais que a varredura nao precisava: log(area_total).

Sem area no controle, "area de imovel rural x area desmatada" e' em boa parte
"municipio grande tem mais de tudo" — e log-populacao nao absorve isso, porque
os municipios de maior area da Amazonia sao justamente os de baixa populacao.

  python3 scripts/hipoteses/91_parciais.py <dir_do_resultado>

Grava <dir>/hipoteses_parciais.tsv com, por par:
  r_bruto              Spearman simples
  r_p_pop              parcial controlando log-pop, log-PIB pc, UF
  r_p_pop_area         idem + log-area  <- o numero que vale para par extensivo
"""
import os, sys
import numpy as np, pandas as pd

OUT = sys.argv[1]
d = pd.read_csv(os.path.join(OUT, "painel.csv"), low_memory=False)
d = d.replace([np.inf, -np.inf], np.nan)

NOMEADAS = [
 ("H01","mides_credores_pc","rais_estab"), ("H01b","mides_credores_pc","nbf_share_dom"),
 ("H02","share_credor_local","populacao"), ("H02b","share_credor_local","pib_pc"),
 ("H03","share_pago_sancionado","ebt_nota"), ("H03b","share_pago_sancionado","nbf_share_dom"),
 ("H04","credores_devedores","mides_credores"),
 ("H05","fef_ordens","share_pago_sancionado"), ("H05b","fef_ordens","ebt_nota"),
 ("H06","fef_share_grave","nbf_share_dom"), ("H06b","fef_share_grave","pib_pc"),
 ("H07","fef_montante_pc","nbf_share_dom"),
 ("H08","pbf_valor_acumulado","d_ivs"), ("H08b","pbf_valor_acumulado","infec_100k"),
 ("H09","pbf_2019_2006","formalidade"), ("H09b","pbf_2019_2006","cresc_pop"),
 ("H10","reclam_100k","pix_penetracao"), ("H10b","reclam_100k","nbf_share_dom"),
 ("H10c","reclam_100k","ibc"),
 ("H11","nota_consumidor","rais_estab"), ("H11b","nota_consumidor","pib_pc"),
 ("H12","defeso_share","formalidade"), ("H12b","defeso_share","credito_pc"),
 ("H12c","defeso_share","agro_1000dom"),
 ("H13","gap_sexo","pib_pc"),
 ("H15","capital_social_mediano","formalidade"),
 ("H16","imoveis_cafir","desmatado"), ("H16b","area_cafir","desmatado"),
 ("H17","credito_rural","desmatado"), ("H17b","credito_rural","deter_km2"),
 ("H18","share_nome_top","nbf_share_dom"), ("H18b","div_nomes","pib_pc"),
 ("H19","share_pago_sancionado","sanc_100k"),
 # densidades das mesmas hipoteses, imunes a escala por construcao
 ("H16c","cafir_share_area","desmat_share_area"),
 ("H17c","credito_ha","desmat_share_area"),
]

d["cafir_share_area"]  = d.area_cafir / d.area_total.replace(0, np.nan)
d["desmat_share_area"] = d.desmatado  / d.area_total.replace(0, np.nan)

uf = pd.get_dummies(d["sigla_uf"], drop_first=True).astype(float)
def ctrl(with_area):
    cols = {"lp": np.log(d.populacao.clip(lower=1)),
            "lpib": np.log(d.pib_pc.clip(lower=1)), "c": 1.0}
    if with_area:
        cols["larea"] = np.log(d.area_total.clip(lower=1))
    return pd.concat([pd.DataFrame(cols), uf], axis=1)
C0, C1 = ctrl(False), ctrl(True)

def parcial(a, b, C):
    m = d[a].notna() & d[b].notna() & C.notna().all(axis=1)
    if m.sum() < 200: return np.nan, int(m.sum())
    X = C[m].values
    r = []
    for col in (a, b):
        y = pd.Series(d.loc[m, col].values).rank().values
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        r.append(y - X @ beta)
    return float(np.corrcoef(r[0], r[1])[0, 1]), int(m.sum())

rows = []
for tag, a, b in NOMEADAS:
    if a not in d.columns or b not in d.columns:
        rows.append((tag, a, b, "variavel ausente", "", "", "", "")); continue
    s = d[[a, b]].dropna()
    if len(s) < 30:
        rows.append((tag, a, b, f"n insuficiente ({len(s)})", len(s), "", "", "")); continue
    rb = s[a].rank().corr(s[b].rank())
    p0, n0 = parcial(a, b, C0)
    p1, n1 = parcial(a, b, C1)
    rows.append((tag, a, b, "", len(s), round(rb, 4),
                 None if pd.isna(p0) else round(p0, 4),
                 None if pd.isna(p1) else round(p1, 4)))

df = pd.DataFrame(rows, columns=["hipotese","var_a","var_b","obs","n",
                                 "r_bruto","r_p_pop","r_p_pop_area"])
df.to_csv(os.path.join(OUT, "hipoteses_parciais.tsv"), sep="\t", index=False)
print(df.to_string(index=False))
