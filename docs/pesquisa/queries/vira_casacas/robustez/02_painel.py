"""Monta o painel analítico: eleição + painel.csv (84 intensivas) + Censo 2022 + RAIS 2024 (seções/divisões)."""
import numpy as np, polars as pl
SP = str(__import__('pathlib').Path(__file__).parent / 'out')
PAINEL = "/Users/polux/Projetos/rodado/.hipoteses/20260906_blocof/painel.csv"
U = {"id_municipio": pl.Utf8}
e = pl.read_parquet(f"{SP}/eleicao_grupos.parquet")
p = pl.read_csv(PAINEL, schema_overrides=U, infer_schema_length=20000)
c = pl.read_csv(f"{SP}/censo2022.csv", schema_overrides=U)
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
 "mides_jaccard_credor","entrantes_share_sancionado","entrantes_share_nao_local","sinasc_share_mae_adolescente",
 "cfem_razao_2225_1721","d_caged_mineracao_pc",
 "rem_media","ibc","cobertura_pop_4g5g","fibra","densidade_smp","hhi_smp",
 "cob_ab","cob_esf","cob_priv","vac_polio","ivs_2000","ivs_2010","idhm_2010",
 "nota_consumidor","tempo_resposta","ebt_nota","share_nome_top","capital_social_mediano",
 "pncp_valor_mediano","comex_hhi_sh4_2019","rais_hhi_cbo_fem","ideb","taxa_aprovacao","cauc_pendencias",
]
p = p.with_columns(
    (pl.col("va_servicos")/pl.col("pib")).alias("share_serv"),
    (pl.col("populacao")/pl.col("area_total")).log().alias("log_densidade"),
    (pl.col("vegetacao_natural")/pl.col("area_total")).alias("share_veg_natural"),
)
EXTRA = ["share_serv","log_densidade","share_veg_natural"]
p = p.select(["id_municipio","nome_regiao_imediata","populacao","area_total"] + INTENSIVAS + EXTRA)
# RAIS 2024 → seção/divisão
r = pl.read_csv(f"{SP}/rais2024_mun_divisao.csv", schema_overrides={"id_municipio": pl.Utf8, "divisao": pl.Utf8})
r = r.filter(pl.col("id_municipio").is_not_null() & pl.col("divisao").is_not_null())
SEC = [("A",1,3),("B",5,9),("C",10,33),("D",35,35),("E",36,39),("F",41,43),("G",45,47),("H",49,53),
       ("I",55,56),("J",58,63),("K",64,66),("L",68,68),("M",69,75),("N",77,82),("O",84,84),("P",85,85),
       ("Q",86,88),("R",90,93),("S",94,96),("T",97,97),("U",99,99)]
def sec(dv):
    d = int(dv)
    for s,a,b in SEC:
        if a <= d <= b: return s
r = r.with_columns(pl.col("divisao").map_elements(sec, return_dtype=pl.Utf8).alias("secao"))
tot = r.group_by("id_municipio").agg(pl.col("vinc").sum().alias("rais_vinc"), pl.col("vinc_pub").sum().alias("rais_pub"),
                                     pl.col("vinc_estat").sum().alias("rais_estat"))
s = r.group_by("id_municipio","secao").agg(pl.col("vinc").sum()).pivot(on="secao", index="id_municipio", values="vinc").fill_null(0)
dv = r.group_by("id_municipio","divisao").agg(pl.col("vinc").sum())
nat = dv.group_by("divisao").agg(pl.col("vinc").sum()).with_columns((pl.col("vinc")/pl.col("vinc").sum()).alias("sh"))
nz = dv.filter(pl.col("vinc")>0).group_by("divisao").agg(pl.len().alias("nmun"))
keep = nat.join(nz, on="divisao").filter((pl.col("sh")>=0.005) | (pl.col("nmun")>=2785))["divisao"].sort().to_list()
print("divisões mantidas:", len(keep), keep)
dvp = dv.filter(pl.col("divisao").is_in(keep)).pivot(on="divisao", index="id_municipio", values="vinc").fill_null(0)
rr = tot.join(s, on="id_municipio", how="left").join(dvp, on="id_municipio", how="left").fill_null(0)
secs = [x for x,_,_ in SEC if x in rr.columns]
rr = rr.with_columns([(pl.col(x)/pl.col("rais_vinc")).alias(f"rais_sec_{x}") for x in secs] +
                     [(pl.col(x)/pl.col("rais_vinc")).alias(f"rais_div_{x}") for x in keep] +
                     [(pl.col("rais_pub")/pl.col("rais_vinc")).alias("rais_share_publico"),
                      (pl.col("rais_estat")/pl.col("rais_vinc")).alias("rais_share_estatutario")])
# HHI setorial (divisões, todas)
h = dv.join(tot.select("id_municipio","rais_vinc"), on="id_municipio").with_columns(((pl.col("vinc")/pl.col("rais_vinc"))**2).alias("s2")).group_by("id_municipio").agg(pl.col("s2").sum().alias("rais_hhi_divisao"))
rr = rr.join(h, on="id_municipio", how="left")
rr = rr.select(["id_municipio","rais_vinc"] + [c for c in rr.columns if c.startswith("rais_") and c!="rais_vinc" and c not in ("rais_pub","rais_estat")])
print("rais municípios:", rr.height, "| soma vínculos:", rr["rais_vinc"].sum())
d = e.join(p, on="id_municipio", how="left").join(c, on="id_municipio", how="left").join(rr, on="id_municipio", how="left")
d = d.with_columns((pl.col("rais_vinc")/pl.col("pop_censo22")).alias("rais_emprego_formal_pc"),
                   pl.col("pop_censo22").log().alias("log_pop"),
                   (pl.col("rais_vinc") < 50).alias("rais_ruidoso"))
for nm, col in [("painel", "nome_regiao_imediata"), ("censo", "pop_censo22"), ("rais", "rais_vinc")]:
    miss = d.filter(pl.col(col).is_null())
    print(f"sem {nm}: {miss.height}", miss.select("uf","nome","grupo").to_dicts()[:5])
print("rais <50 vínculos:", d["rais_ruidoso"].sum())
d.write_parquet(f"{SP}/painel_analitico.parquet")
print("painel analítico:", d.shape)
