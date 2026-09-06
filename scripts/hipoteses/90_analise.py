#!/usr/bin/env python3
"""Monta o painel municipal a partir dos CSV extraidos e roda a bateria de
correlacoes. Roda offline no beelink; so precisa de numpy + pandas.

Saidas em $OUT:
  painel.csv          painel municipal completo (1 linha por municipio)
  correlacoes.tsv     todos os pares, Spearman bruto e parcial, ranqueado
  hipoteses.tsv       so os pares nomeados em tasks/hipoteses.md
  quintis.txt         tabelas de quintil para os pares mais fortes
"""
import os, sys, glob, itertools
import numpy as np, pandas as pd

OUT = sys.argv[1] if len(sys.argv) > 1 else "."

def load(name, key="id_municipio"):
    p = os.path.join(OUT, name + ".csv")
    if not os.path.exists(p):
        print(f"  [pula] {name}.csv ausente"); return None
    d = pd.read_csv(p, low_memory=False)
    if key not in d.columns: return d
    d = d[d[key].notna()].copy()
    d[key] = d[key].astype("int64")
    return d.drop_duplicates(subset=[key])

# ---------------------------------------------------------------- painel
base = load("br_municipio")
base = base[["id_municipio","sigla_uf","nome","nome_regiao_imediata","capital_uf","amazonia_legal"]]
for f in ["v_populacao","v_populacao2010","v_pib","v_pib2010","v_rais","v_sim","v_anatel",
          "v_prodes","v_cnefe","v_pix","v_cfem","v_gd","v_deter","v_ibama_autos","v_embargos",
          "v_sicar","v_cafir","v_sicor","v_nbf","v_pncp","v_ieps","v_avs","v_mides","v_fef",
          "v_pbf_serie","v_consumidor","v_defeso","v_pdm","v_ebt","v_nomes","v_rais_ident",
          "v_mides_sancionado","v_mides_devedor","v_mides_local","v_sanc_emprego","v_sancoes_mun",
          "v_comex","v_comex_hhi","v_pbf_choque","v_caged_choque","v_mides_saude","v_sih",
          "v_prefeito","v_mides_jaccard","v_sinasc","v_rais_hhi_fem","v_ideb","v_cfem_early","v_cauc"]:
    d = load(f)
    if d is not None and "id_municipio" in d.columns:
        base = base.merge(d, on="id_municipio", how="left")
print(f"painel: {base.shape[0]} municipios x {base.shape[1]} colunas")

n = base
def div(a, b):
    return np.where((n[b].notna()) & (n[b] != 0), n[a] / n[b].replace(0, np.nan), np.nan)

d = base.copy()
d["pib_pc"]       = div("pib","populacao")
d["share_agro"]   = div("va_agropecuaria","pib")
d["share_ind"]    = div("va_industria","pib")
d["formalidade"]  = div("vinculos","populacao")
d["homic_100k"]   = div("homicidios","populacao")*1e5/3
d["suic_100k"]    = div("suicidios","populacao")*1e5/3
d["ip_100k"]      = div("interv_policial","populacao")*1e5/3
d["transito_100k"]= div("mortes_transito","populacao")*1e5/3
d["infec_100k"]   = div("obitos_infecciosos","populacao")*1e5/3
d["homic_juv_100k"]=div("homic_juvenis","populacao")*1e5/3
d["gap_sexo"]     = 1 - div("rem_fem","rem_masc")
d["relig_100k"]   = div("vinc_religioso","populacao")*1e5
d["templos_1000dom"]  = div("cnefe_religioso","cnefe_dom")*1000
d["obras_1000dom"]    = div("cnefe_construcao","cnefe_dom")*1000
d["agro_1000dom"]     = div("cnefe_agro","cnefe_dom")*1000
d["saude_1000dom"]    = div("cnefe_saude","cnefe_dom")*1000
d["comercio_por_dom"] = div("cnefe_outros","cnefe_dom")
d["dom_por_cep"]      = div("cnefe_dom","cnefe_ceps")
d["nbf_share_dom"]    = div("nbf_familias","cnefe_dom")
d["pix_pag_pc"]       = (d.pix_vl_pag_pf + d.pix_vl_pag_pj)*1e6/d.populacao
d["pix_ticket_pf"]    = d.pix_vl_pag_pf*1e6/d.pix_qt_pag_pf
d["pix_penetracao"]   = div("pix_pes_pag_pf","populacao")
d["pix_razao_rec_pag"]= (d.pix_vl_rec_pf+d.pix_vl_rec_pj)/(d.pix_vl_pag_pf+d.pix_vl_pag_pj)
d["cfem_pc"]          = div("cfem_valor","populacao")
d["gd_por_domicilio"] = div("gd_n","cnefe_dom")
d["deter_share_area"] = div("deter_km2","area_total")
d["autos_100k"]       = div("ibama_autos_n","populacao")*1e5
d["credito_pc"]       = div("credito_rural","populacao")
d["credito_ha"]       = div("credito_rural","sicar_area")
d["va_agro_ha"]       = div("va_agropecuaria","sicar_area")
d["cafir_ha_por_imovel"] = div("area_cafir","imoveis_cafir")
d["pdm_share"]        = div("pdm_alunos","populacao")
d["defeso_share"]     = div("defeso_pescadores","populacao")
d["div_nomes"]        = div("nomes_distintos","nascimentos")
d["sanc_100k"]        = div("sanc_n","populacao")*1e5
d["cresc_pop"]        = div("populacao","pop2010") - 1
d["d_ivs"]            = d.ivs_2010 - d.ivs_2000
d["pbf_2019_2006"]    = div("pbf_2019","pbf_2006")
d["reclam_100k"]      = div("reclamacoes","populacao")*1e5
# --- variaveis novas das cadeias
d["mides_credores_pc"]   = div("mides_credores","populacao")*1e5
d["mides_valor_pc"]      = div("mides_valor","populacao")
d["share_pago_sancionado"]= div("pag_sancionado_valor","pag_total_valor")
d["share_credor_local"]  = div("credor_local","n")
d["fef_montante_pc"]     = div("fef_montante","populacao")
d["fef_share_grave"]     = div("fef_graves","fef_ordens")
# --- variaveis novas H41-H45 (tasks/hipoteses.md, Bloco I)
d["comex_choque_pct"]    = div("comex_fob_2020","comex_fob_2019") - 1
d["pbf_choque_pct"]      = div("pbf_2020","pbf_2019") - 1
d["caged_pc_2019"]       = div("caged_saldo_2019","populacao")*1000
d["caged_pc_2020"]       = div("caged_saldo_2020","populacao")*1000
d["caged_pc_2017_2021"]  = div("caged_saldo_2017_2021","populacao")*1000
d["caged_pc_2022_2024"]  = div("caged_saldo_2022_2024","populacao")*1000
d["saude_share_terceirizado"] = div("saude_empenho_terceirizado_pj","saude_empenho_total")
d["sih_share_retencao"]  = div("sih_retencao_n","sih_aih_n")
d["mides_jaccard_credor"]     = div("credores_intersecao","credores_uniao")
d["entrantes_share_sancionado"] = div("entrantes_sancionados_n","entrantes_n")
d["entrantes_share_nao_local"]  = div("entrantes_nao_local_n","entrantes_n")
d["troca_partido_2016_2020"] = np.where(
    d.prefeito_partido_2016.notna() & d.prefeito_partido_2020.notna(),
    (d.prefeito_partido_2016 != d.prefeito_partido_2020).astype(float), np.nan)
d["sinasc_share_mae_adolescente"] = div("sinasc_mae_adolescente","sinasc_nascidos")
d["cfem_razao_2225_1721"] = div("cfem_valor","cfem_valor_2017_2021")
d["d_caged_mineracao_pc"] = d.caged_pc_2022_2024 - d.caged_pc_2017_2021

d.to_csv(os.path.join(OUT,"painel.csv"), index=False)
print(f"painel.csv gravado ({d.shape[1]} colunas)")

# --------------------------------------------------------- correlacoes
# So variaveis INTENSIVAS entram na varredura. Contagem bruta (extensiva) escala
# com populacao e produz um ranking inteiro de "municipio grande tem mais de tudo"
# — o residuo em rank de log-pop nao absorve isso. As extensivas ficam em
# painel.csv para quem quiser, mas nao sao correlacionadas entre si.
INTENSIVAS = [
 # derivadas neste script
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
 "mides_jaccard_credor",
 "entrantes_share_sancionado","entrantes_share_nao_local","sinasc_share_mae_adolescente",
 "cfem_razao_2225_1721","d_caged_mineracao_pc",
 # ja intensivas na origem
 "rem_media","ibc","cobertura_pop_4g5g","fibra","densidade_smp","hhi_smp",
 "cob_ab","cob_esf","cob_priv","vac_polio","ivs_2000","ivs_2010","idhm_2010",
 "nota_consumidor","tempo_resposta","ebt_nota","share_nome_top","capital_social_mediano",
 "pncp_valor_mediano","comex_hhi_sh4_2019","rais_hhi_cbo_fem","ideb","taxa_aprovacao",
 "cauc_pendencias","troca_partido_2016_2020",
]
NUM = [c for c in INTENSIVAS if c in d.columns and pd.api.types.is_numeric_dtype(d[c])]
print(f"varredura sobre {len(NUM)} variaveis intensivas "
      f"({len(d.columns)-len(NUM)} extensivas ficam so no painel)")
d = d.replace([np.inf,-np.inf], np.nan)

uf = pd.get_dummies(d["sigla_uf"], drop_first=True).astype(float)
CTRL = pd.concat([pd.DataFrame({
    "lp": np.log(d.populacao.clip(lower=1)),
    "lpib": np.log(d.pib_pc.clip(lower=1)),
    "c": 1.0}), uf], axis=1)

_cache = {}
def resid(col):
    if col in _cache: return _cache[col]
    y = d[col]
    m = y.notna() & CTRL.notna().all(axis=1)
    r = pd.Series(np.nan, index=d.index)
    if m.sum() >= 200:
        yy = pd.Series(y[m].values).rank().values
        XX = CTRL[m].values
        b, *_ = np.linalg.lstsq(XX, yy, rcond=None)
        r[m] = yy - XX @ b
    _cache[col] = r
    return r

# pares tautologicos: derivada x sua fonte, ou duas medidas do mesmo objeto
FONTES = {
 "pib_pc":{"pib","populacao"}, "share_agro":{"va_agropecuaria","pib"},
 "share_ind":{"va_industria","pib"}, "formalidade":{"vinculos","populacao"},
 "homic_100k":{"homicidios","populacao"}, "suic_100k":{"suicidios","populacao"},
 "ip_100k":{"interv_policial","populacao"}, "transito_100k":{"mortes_transito","populacao"},
 "infec_100k":{"obitos_infecciosos","populacao"}, "homic_juv_100k":{"homic_juvenis","populacao"},
 "gap_sexo":{"rem_fem","rem_masc"}, "relig_100k":{"vinc_religioso","populacao"},
 "templos_1000dom":{"cnefe_religioso","cnefe_dom"}, "obras_1000dom":{"cnefe_construcao","cnefe_dom"},
 "agro_1000dom":{"cnefe_agro","cnefe_dom"}, "saude_1000dom":{"cnefe_saude","cnefe_dom"},
 "comercio_por_dom":{"cnefe_outros","cnefe_dom"}, "dom_por_cep":{"cnefe_dom","cnefe_ceps"},
 "nbf_share_dom":{"nbf_familias","cnefe_dom"},
 "pix_pag_pc":{"pix_vl_pag_pf","pix_vl_pag_pj","populacao"},
 "pix_ticket_pf":{"pix_vl_pag_pf","pix_qt_pag_pf"}, "pix_penetracao":{"pix_pes_pag_pf","populacao"},
 "pix_razao_rec_pag":{"pix_vl_rec_pf","pix_vl_rec_pj","pix_vl_pag_pf","pix_vl_pag_pj"},
 "cfem_pc":{"cfem_valor","populacao"}, "gd_por_domicilio":{"gd_n","cnefe_dom"},
 "deter_share_area":{"deter_km2","area_total"}, "autos_100k":{"ibama_autos_n","populacao"},
 "credito_pc":{"credito_rural","populacao"}, "credito_ha":{"credito_rural","sicar_area"},
 "va_agro_ha":{"va_agropecuaria","sicar_area"},
 "cafir_ha_por_imovel":{"area_cafir","imoveis_cafir"},
 "pdm_share":{"pdm_alunos","populacao"}, "defeso_share":{"defeso_pescadores","populacao"},
 "div_nomes":{"nomes_distintos","nascimentos"}, "sanc_100k":{"sanc_n","populacao"},
 "cresc_pop":{"populacao","pop2010"}, "d_ivs":{"ivs_2010","ivs_2000"},
 "pbf_2019_2006":{"pbf_2019","pbf_2006"}, "reclam_100k":{"reclamacoes","populacao"},
 "mides_credores_pc":{"mides_credores","populacao"}, "mides_valor_pc":{"mides_valor","populacao"},
 "share_pago_sancionado":{"pag_sancionado_valor","pag_total_valor"},
 "share_credor_local":{"credor_local","n"},
 "fef_montante_pc":{"fef_montante","populacao"}, "fef_share_grave":{"fef_graves","fef_ordens"},
 "comex_choque_pct":{"comex_fob_2020","comex_fob_2019"},
 "pbf_choque_pct":{"pbf_2020","pbf_2019"},
 "caged_pc_2019":{"caged_saldo_2019","populacao"}, "caged_pc_2020":{"caged_saldo_2020","populacao"},
 "caged_pc_2017_2021":{"caged_saldo_2017_2021","populacao"},
 "caged_pc_2022_2024":{"caged_saldo_2022_2024","populacao"},
 "d_caged_mineracao_pc":{"caged_pc_2022_2024","caged_pc_2017_2021"},
 "saude_share_terceirizado":{"saude_empenho_terceirizado_pj","saude_empenho_total"},
 "sih_share_retencao":{"sih_retencao_n","sih_aih_n"},
 "mides_jaccard_credor":{"credores_intersecao","credores_uniao"},
 "entrantes_share_sancionado":{"entrantes_sancionados_n","entrantes_n"},
 "entrantes_share_nao_local":{"entrantes_nao_local_n","entrantes_n"},
 "sinasc_share_mae_adolescente":{"sinasc_mae_adolescente","sinasc_nascidos"},
 "cfem_razao_2225_1721":{"cfem_valor","cfem_valor_2017_2021"},
}
# mesmas quantidades sob nomes diferentes (extracoes que se sobrepoem)
# grupos onde QUALQUER par interno mede o mesmo objeto sob outro nome/unidade
ESPELHO = [
 {"mides_valor","pag_total_valor","mides_valor_pc"},
 {"mides_pagamentos","pag_total_n","mides_credores","mides_credores_pc","n","credor_local"},
 {"sanc_n","sanc_empregadoras","sanc_vinculos"},
 {"pncp_n","pncp_fornecedores"},
 {"deter_km2","deter_n","deter_share_area","deter_km2_garimpo"},
 {"area_total","sicar_area","area_cafir","sicar_imoveis","imoveis_cafir"},
 {"credito_rural","credito_2019","credito_2024","credito_pc","cars_financiados"},
 {"nomes_distintos","nascimentos","populacao","pop2010","cnefe_n","cnefe_dom","cnefe_ceps"},
 # H38 (tasks/hipoteses.md §5.2 Bloco H): nao e' confound, e' definicional —
 # as duas vem da mesma tabela br_ibge_nomes_brasil e sao dois resumos
 # (diversidade x dominancia) da mesma distribuicao categorica, ligados por
 # combinatoria; adicionar log(nascimentos) ao controle so piora o parcial
 # (-0,40 -> -0,51), nao remove — testado em scripts/hipoteses/97_h38_h40.py
 {"nomes_distintos","share_nome_top","div_nomes"},
 {"rem_media","rem_masc","rem_fem"},
 {"pix_vl_pag_pf","pix_vl_pag_pj","pix_vl_rec_pf","pix_vl_rec_pj","pix_qt_pag_pf","pix_pes_pag_pf"},
 {"vinculos","vinc_fem","rais_vinculos","rais_estab"},
 {"obitos","homicidios","suicidios","interv_policial","mortes_transito",
  "obitos_infecciosos","obitos_respiratorios","homic_juvenis","ob_fem_precoce"},
 {"pib","va_agropecuaria","va_industria","va_servicos","impostos_liquidos","pib_2010"},
 {"reclamacoes","respondidas"},
 {"fef_ordens","fef_ciclos","fef_montante","fef_graves","fef_tipos","fef_montante_pc"},
 {"pbf_2006","pbf_2013","pbf_2019","pbf_valor_acumulado"},
 {"nbf_familias","nbf_valor"},
 {"cfem_valor","cfem_titulares","cfem_pc","cfem_valor_2017_2021","cfem_razao_2225_1721"},
 {"gd_n","gd_kw","gd_rural"},
 {"ivs_2000","ivs_2010","idhm_2010"},
 {"comex_fob_2019","comex_fob_2020","comex_choque_pct","comex_hhi_sh4_2019"},
 {"pbf_2020","pbf_choque_pct"},
 {"caged_saldo_2019","caged_saldo_2020","caged_saldo_2017_2021","caged_saldo_2022_2024",
  "caged_pc_2019","caged_pc_2020","caged_pc_2017_2021","caged_pc_2022_2024","d_caged_mineracao_pc"},
 {"saude_empenho_total","saude_empenho_terceirizado_pj"},
 {"sih_aih_n","sih_retencao_n"},
 {"credores_intersecao","credores_uniao","credores_pre_n","credores_pos_n","entrantes_n"},
 {"entrantes_sancionados_n","entrantes_nao_local_n"},
 {"prefeito_partido_2016","prefeito_partido_2020","prefeito_partido_2024","troca_partido_2016_2020"},
 {"sinasc_nascidos","sinasc_mae_adolescente"},
]
def tautologico(a, b):
    if b in FONTES.get(a, ()) or a in FONTES.get(b, ()): return True
    if FONTES.get(a) and FONTES.get(a) == FONTES.get(b): return True
    for e in ESPELHO:
        if a in e and b in e: return True
    return False

rows, taut = [], []
for a, b in itertools.combinations(NUM, 2):
    s = d[[a,b]].dropna()
    if len(s) < 300: continue
    if s[a].nunique() < 5 or s[b].nunique() < 5: continue
    rb = s[a].rank().corr(s[b].rank())
    if pd.isna(rb): continue
    ra, rbb = resid(a), resid(b)
    sp = pd.concat([ra,rbb], axis=1).dropna()
    rp = sp.iloc[:,0].corr(sp.iloc[:,1]) if len(sp) >= 300 else np.nan
    reg = (a, b, len(s), round(rb,4), len(sp), None if pd.isna(rp) else round(rp,4))
    # |r|>0.98 sem relacao declarada tambem e' quase sempre a mesma medida duas vezes
    if tautologico(a, b) or abs(rb) > 0.98:
        taut.append(reg)
    else:
        rows.append(reg)

COLS = ["var_a","var_b","n_bruto","r_bruto","n_parcial","r_parcial"]
pd.DataFrame(taut, columns=COLS).to_csv(os.path.join(OUT,"tautologias.tsv"), sep="\t", index=False)
print(f"tautologias.tsv: {len(taut)} pares descartados (derivada x fonte, ou r>0.98)")
res = pd.DataFrame(rows, columns=COLS)
res["abs_parcial"] = res.r_parcial.abs()
res = res.sort_values("abs_parcial", ascending=False, na_position="last")
res.to_csv(os.path.join(OUT,"correlacoes.tsv"), sep="\t", index=False)
print(f"correlacoes.tsv: {len(res)} pares")

# --------------------------------------------------------- quintis
with open(os.path.join(OUT,"quintis.txt"), "w") as fh:
    for _, r in res.head(60).iterrows():
        s = d[[r.var_a, r.var_b]].dropna()
        if len(s) < 500: continue
        try:
            s["q"] = pd.qcut(s[r.var_a], 5, labels=False, duplicates="drop")
        except Exception:
            continue
        g = s.groupby("q")[r.var_b].median()
        fh.write(f"{r.var_a} -> {r.var_b} (r_bruto {r.r_bruto}, r_parcial {r.r_parcial}, n {len(s)})\n")
        fh.write("  " + " | ".join(f"{v:.4g}" for v in g) + "\n\n")
print("quintis.txt gravado")

# --------------------------------------------------------- hipoteses nomeadas
# pares que respondem H01..H19 de tasks/hipoteses.md
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
 ("H41","comex_choque_pct","pbf_choque_pct"), ("H41b","comex_hhi_sh4_2019","pbf_choque_pct"),
 ("H41c","comex_choque_pct","d_caged_mineracao_pc"),
 ("H42","saude_share_terceirizado","sih_share_retencao"),
 ("H42b","saude_share_terceirizado","sih_valor_aih_mediano"),
 ("H42c","saude_share_terceirizado","infec_100k"),
 ("H43","troca_partido_2016_2020","mides_jaccard_credor"),
 ("H43b","troca_partido_2016_2020","entrantes_share_nao_local"),
 ("H43c","troca_partido_2016_2020","entrantes_share_sancionado"),
 ("H44","rais_hhi_cbo_fem","sinasc_share_mae_adolescente"),
 ("H44b","ideb","sinasc_share_mae_adolescente"),
 ("H44c","nbf_share_dom","sinasc_share_mae_adolescente"),
 ("H45","cfem_razao_2225_1721","d_caged_mineracao_pc"),
 ("H45b","cfem_razao_2225_1721","cauc_pendencias"),
]
idx = {(r.var_a, r.var_b): r for _, r in res.iterrows()}
idx.update({(r.var_b, r.var_a): r for _, r in res.iterrows()})
hip = []
for tag, a, b in NOMEADAS:
    if a not in d.columns or b not in d.columns:
        hip.append((tag, a, b, "variavel ausente", "", "", "")); continue
    r = idx.get((a, b))
    if r is None:
        s2 = d[[a,b]].dropna()
        if len(s2) < 30:
            hip.append((tag, a, b, f"n insuficiente ({len(s2)})", "", "", "")); continue
        hip.append((tag, a, b, "", len(s2), round(s2[a].rank().corr(s2[b].rank()),4), ""))
    else:
        hip.append((tag, a, b, "", r.n_bruto, r.r_bruto, r.r_parcial))
pd.DataFrame(hip, columns=["hipotese","var_a","var_b","obs","n","r_bruto","r_parcial"]) \
  .to_csv(os.path.join(OUT,"hipoteses.tsv"), sep="\t", index=False)
print("hipoteses.tsv gravado")

# --------------------------------------------------------- UF
ufp = d.groupby("sigla_uf").agg(
    pop=("populacao","sum"), pib=("pib","sum"), vinculos=("vinculos","sum"),
    homicidios=("homicidios","sum"), interv=("interv_policial","sum"),
    nbf=("nbf_familias","sum"), dom=("cnefe_dom","sum"),
    mides_valor=("mides_valor","sum"), fef=("fef_ordens","sum"),
    reclamacoes=("reclamacoes","sum"), defeso=("defeso_pescadores","sum")).reset_index()
ufp.to_csv(os.path.join(OUT,"painel_uf.csv"), index=False)
print("painel_uf.csv gravado")
