SET enable_progress_bar=false;
COPY (
SELECT id_municipio, substr(lpad(cnae_2,4,'0'),1,2) AS divisao,
       sum(quantidade_vinculos_ativos) AS vinc,
       sum(CASE WHEN natureza_juridica LIKE '1%' THEN quantidade_vinculos_ativos ELSE 0 END) AS vinc_pub,
       sum(quantidade_vinculos_estatutarios) AS vinc_estat,
       count(*) FILTER (WHERE quantidade_vinculos_ativos>0) AS estab_ativos
FROM read_parquet('~/rodado/br_me_rais/microdados_estabelecimentos/*.parquet')
WHERE ano = 2024
GROUP BY 1,2
) TO '/dev/stdout' (FORMAT csv, HEADER);
