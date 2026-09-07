-- hipoteses3 · bloco 94 · SISVAN. 406.253.792 linhas.
-- Estado nutricional do adulto por municipio, um ano. O campo e texto livre
-- ("Obesidade Grau I" etc.), entao o filtro e por ILIKE e a analise confere os
-- rotulos que sairam antes de calcular share.
SET enable_progress_bar=false; SET memory_limit='8GB'; SET threads=4;

COPY (
  SELECT id_municipio,
         count(*)                                                          AS sisvan_n,
         count(*) FILTER (WHERE estado_nutricional_adulto ILIKE '%besidade%') AS sisvan_obesidade,
         count(*) FILTER (WHERE estado_nutricional_adulto ILIKE '%sobrepeso%') AS sisvan_sobrepeso,
         count(*) FILTER (WHERE estado_nutricional_adulto ILIKE '%baixo peso%') AS sisvan_baixo_peso,
         avg(TRY_CAST(imc AS DOUBLE))                                      AS sisvan_imc
  FROM br_ms_sisvan.microdados
  WHERE ano = (SELECT max(ano) FROM br_ms_sisvan.microdados)
  GROUP BY 1
) TO '__OUT__/h3_sisvan.csv' (HEADER);
