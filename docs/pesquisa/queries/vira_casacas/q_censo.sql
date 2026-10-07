SET enable_progress_bar=false;
COPY (
WITH p AS (
  SELECT id_municipio, sum(populacao) pop,
    sum(populacao) FILTER (WHERE cor_raca='Branca') br,
    sum(populacao) FILTER (WHERE cor_raca='Parda') pa,
    sum(populacao) FILTER (WHERE cor_raca='Preta') pr,
    sum(populacao) FILTER (WHERE cor_raca='Indígena') ind,
    sum(populacao) FILTER (WHERE grupo_idade IN ('60 a 64 anos','65 a 69 anos','70 a 74 anos','75 a 79 anos','80 a 84 anos','85 a 89 anos','90 a 94 anos','95 a 99 anos','100 anos ou mais')) i60,
    sum(populacao) FILTER (WHERE grupo_idade IN ('0 a 4 anos','5 a 9 anos','10 a 14 anos')) i0_14,
    sum(populacao) FILTER (WHERE sexo='Homens') hom
  FROM read_parquet('~/rodado/br_ibge_censo_2022/populacao_grupo_idade_sexo_raca/*.parquet') WHERE ano=2022 GROUP BY 1),
a AS (
  SELECT id_municipio, sum(populacao) a_tot, sum(populacao) FILTER (WHERE alfabetizacao='Não alfabetizadas') a_nao
  FROM read_parquet('~/rodado/br_ibge_censo_2022/alfabetizacao_grupo_idade_sexo_raca/*.parquet') GROUP BY 1)
SELECT p.id_municipio, pop AS pop_censo22, br/pop AS c22_share_branca, pa/pop AS c22_share_parda, pr/pop AS c22_share_preta,
  ind/pop AS c22_share_indigena, i60/pop AS c22_share_60mais, i0_14/pop AS c22_share_0a14, hom/pop AS c22_razao_homens,
  a_nao/a_tot AS c22_analfabetismo_15mais
FROM p LEFT JOIN a USING (id_municipio)) TO '/dev/stdout' (FORMAT csv, HEADER);
