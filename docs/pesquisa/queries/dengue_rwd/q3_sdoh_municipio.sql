-- Camada SDOH: por município de residência, 2014-2024 somados, casos prováveis e óbitos (SINAN)
-- ao lado de saneamento (Atlas Esgotos/ANA, retrato de 2013) e PIB per capita 2021 (IBGE).
-- Ecológico: relaciona municípios, não pessoas.
WITH sinan AS (
  SELECT id_municipio_residencia id_municipio,
    count(*) provaveis,
    count(*) FILTER (WHERE trim(classificacao_final) IN ('11','12')) alarme_ou_grave,
    count(*) FILTER (WHERE evolucao_caso = '2') sinan_obitos
  FROM br_ms_sinan.microdados_dengue
  WHERE ano BETWEEN 2014 AND 2024 AND coalesce(trim(classificacao_final),'') <> '5'
    AND id_municipio_residencia IS NOT NULL
  GROUP BY 1
),
pib AS (
  SELECT p.id_municipio, p.pib / NULLIF(q.populacao, 0) pib_per_capita, q.populacao populacao_2021
  FROM br_ibge_pib.municipio p
  JOIN br_ibge_populacao.municipio q ON q.id_municipio = p.id_municipio AND q.ano = p.ano
  WHERE p.ano = 2021
),
esg AS (
  SELECT id_municipio, indice_atendimento_com_coleta_com_tratamento esgoto_tratado,
         indice_sem_atendimento_sem_coleta_sem_tratamento sem_esgoto
  FROM br_ana_atlas_esgotos.municipio
)
SELECT pib.id_municipio, d.sigla_uf, pib.populacao_2021, pib.pib_per_capita, esg.esgoto_tratado, esg.sem_esgoto,
       coalesce(provaveis,0) provaveis, coalesce(alarme_ou_grave,0) alarme_ou_grave, coalesce(sinan_obitos,0) sinan_obitos
FROM pib
JOIN br_bd_diretorios_brasil.municipio d USING (id_municipio)
LEFT JOIN esg USING (id_municipio)
LEFT JOIN sinan USING (id_municipio);
