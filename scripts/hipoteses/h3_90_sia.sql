-- hipoteses3 · bloco 90 · SIA producao ambulatorial.
-- 6.159.969.884 LINHAS -- a maior tabela do espelho. Roda por ultimo e sozinha.
-- Filtrada a UM ano (particao) e sem count(DISTINCT) exato: approx_count_distinct
-- resolve em uma passada; o exato precisaria de hash de 600M chaves.
SET enable_progress_bar=false; SET memory_limit='8GB'; SET threads=4;
SET temp_directory='/home/polo/tmp_duck';

COPY (
  SELECT id_municipio,
         count(*)                                          AS sia_procedimentos,
         approx_count_distinct(id_estabelecimento_cnes)     AS sia_estabelecimentos,
         approx_count_distinct(id_cbo_2002)                 AS sia_ocupacoes
  FROM br_ms_sia.producao_ambulatorial
  WHERE ano = (SELECT max(ano) FROM br_ms_sia.producao_ambulatorial)
  GROUP BY 1
) TO '__OUT__/h3_sia.csv' (HEADER);
