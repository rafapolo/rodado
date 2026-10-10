"""Robustez da análise vira-casacas (segunda passada, independente de ../analise.py).

Diferenças de método em relação a ../analise.py: indicadores em escala normal por posto
(menos sensível a cauda), erro-padrão agrupado por região imediata, controle pela margem
de 2022 no modelo binário, modelos esparsos (L1) e checagem dentro de MG.

Entradas em out/: diretorio.csv (id_municipio, nome, sigla_uf, nome_regiao, capital_uf,
amazonia_legal, centroide de br_bd_diretorios_brasil.municipio), censo2022.csv
(../q_censo.sql) e rais2024_mun_divisao.csv (../q_rais.sql).
Ordem: 01 -> 02 -> 03 -> 04 -> 05; os CSV desta pasta são as saídas de 03/04.
uv run --with statsmodels --with scikit-learn --with scipy --with pandas --with polars --with pyarrow python 0X_*.py
"""
import json, unicodedata, re, polars as pl
SP = str(__import__('pathlib').Path(__file__).parent / 'out')
J = "/Users/polux/Projetos/xyz/dataviz/eleicoes/data_presidente_2026.json"
cols = ["uf","nome","lat","lon","tot","lean","polar","ncand","w1","w1pct","w2","w2pct",
        "pesq","pcen","pdir","plula26","pflavio26","plula22","pbolso22"]
raw = json.load(open(J))
e = pl.DataFrame([dict(zip(cols, r)) for r in raw], infer_schema_length=None)
print("registros JSON:", e.height)
def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", s)
e = e.with_columns(pl.col("nome").map_elements(norm, return_dtype=pl.Utf8).alias("k"))
dr = pl.read_csv(f"{SP}/diretorio.csv", schema_overrides={"id_municipio": pl.Utf8})
dr = dr.with_columns(
    pl.col("centroide").str.extract(r"POINT \(([-\d.]+) ").cast(pl.Float64).round(4).alias("lon_d"),
    pl.col("centroide").str.extract(r" ([-\d.]+)\)").cast(pl.Float64).round(4).alias("lat_d"),
    pl.col("nome").map_elements(norm, return_dtype=pl.Utf8).alias("k"))
# casamento 1: (uf, nome normalizado)
m1 = e.join(dr.select("id_municipio","sigla_uf","k","nome_regiao","capital_uf","amazonia_legal","lat_d","lon_d"),
            left_on=["uf","k"], right_on=["sigla_uf","k"], how="left")
print("casados por (uf,nome):", m1["id_municipio"].is_not_null().sum(), "| duplicatas:", m1.height - e.height)
# casamento 2 independente: (lat, lon) exatos (o build usou o centroide do mesmo diretório)
m2 = e.join(dr.select(pl.col("id_municipio").alias("id_ll"), "lat_d","lon_d"),
            left_on=["lat","lon"], right_on=["lat_d","lon_d"], how="left")
print("casados por (lat,lon):", m2["id_ll"].is_not_null().sum(), "| duplicatas:", m2.height - e.height)
both = m1.with_columns(m2["id_ll"])
print("sem casar por nome:", both.filter(pl.col("id_municipio").is_null()).select("uf","nome").to_dicts())
print("divergência nome×latlon:", both.filter(pl.col("id_municipio") != pl.col("id_ll")).height)
both = both.with_columns(pl.coalesce("id_municipio","id_ll").alias("id_municipio"))
# grupos
both = both.with_columns(
    (pl.col("plula22") > pl.col("pbolso22")).alias("lula22"),
    (pl.col("plula26") > pl.col("pflavio26")).alias("lula26"),
    (pl.col("plula22") - pl.col("pbolso22")).alias("margem22"),
    (pl.col("plula26") - pl.col("pflavio26")).alias("margem26"),
    (pl.col("plula26") - pl.col("pdir")).alias("margem26_dir"),
)
both = both.with_columns(
    pl.when(pl.col("plula22").is_null()).then(pl.lit("sem2022"))
     .when((pl.col("plula22") > pl.col("pbolso22")) & (pl.col("pflavio26") > pl.col("plula26"))).then(pl.lit("vira"))
     .when((pl.col("plula22") > pl.col("pbolso22")) & (pl.col("plula26") > pl.col("pflavio26"))).then(pl.lit("LL"))
     .when((pl.col("pbolso22") > pl.col("plula22")) & (pl.col("pflavio26") > pl.col("plula26"))).then(pl.lit("BF"))
     .when((pl.col("pbolso22") > pl.col("plula22")) & (pl.col("plula26") > pl.col("pflavio26"))).then(pl.lit("inverso"))
     .otherwise(pl.lit("empate")).alias("grupo"),
    (pl.col("margem26") - pl.col("margem22")).alias("d_margem"),
    (pl.col("plula26") - pl.col("plula22")).alias("d_lula"))
print(both["grupo"].value_counts().sort("grupo"))
# conferência independente do 703 (contagem direta no JSON cru)
n2 = sum(1 for r in raw if r[17] is not None and r[17] > r[18] and r[16] > r[15])
print("vira-casacas contagem direta no JSON:", n2, "| empates 2026:", sum(1 for r in raw if r[17] is not None and r[15]==r[16]), "| empates 2022:", sum(1 for r in raw if r[17] is not None and r[17]==r[18]))
both.drop("k").write_parquet(f"{SP}/eleicao_grupos.parquet")
