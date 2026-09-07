-- hipoteses3 · bloco 92 · pagamento do Bolsa Familia. 1.495.223.596 linhas.
-- UM mes de competencia, nunca a serie: sao pagamentos mensais e a soma anual
-- conta a mesma familia 12 vezes.
SET enable_progress_bar=false; SET memory_limit='8GB'; SET threads=4;
SET temp_directory='/home/polo/tmp_duck';

COPY (
  WITH ult AS (
    SELECT max(ano_competencia) AS a FROM br_cgu_beneficios_cidadao.bolsa_familia_pagamento
  )
  SELECT id_municipio,
         approx_count_distinct(cpf_favorecido)          AS bf_familias,
         sum(TRY_CAST(valor_parcela AS DOUBLE))         AS bf_valor,
         avg(TRY_CAST(valor_parcela AS DOUBLE))         AS bf_parcela_media
  FROM br_cgu_beneficios_cidadao.bolsa_familia_pagamento, ult
  WHERE ano_competencia = ult.a
    AND mes_competencia = (
      SELECT max(mes_competencia) FROM br_cgu_beneficios_cidadao.bolsa_familia_pagamento
      WHERE ano_competencia = (SELECT a FROM ult))
  GROUP BY 1
) TO '__OUT__/h3_bolsa_familia.csv' (HEADER);
