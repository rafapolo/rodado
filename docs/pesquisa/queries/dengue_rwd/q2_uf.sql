-- Por UF de residência, 2014-2024 somados: casos prováveis, óbitos (SINAN), internações SUS (SIH).
-- SIH guarda o município com 6 dígitos (sem verificador) e sigla_uf vem nula: UF sai do diretório.
WITH dir AS (SELECT id_municipio, id_municipio_6, sigla_uf FROM br_bd_diretorios_brasil.municipio),
sinan AS (
  SELECT d.sigla_uf,
    count(*) provaveis,
    count(*) FILTER (WHERE trim(classificacao_final) IN ('11','12')) alarme_ou_grave,
    count(*) FILTER (WHERE evolucao_caso = '2') sinan_obitos,
    count(*) FILTER (WHERE ano = 2024) provaveis_2024,
    count(*) FILTER (WHERE ano = 2024 AND evolucao_caso = '2') sinan_obitos_2024
  FROM br_ms_sinan.microdados_dengue x
  JOIN dir d ON d.id_municipio = x.id_municipio_residencia
  WHERE ano BETWEEN 2014 AND 2024 AND coalesce(trim(classificacao_final),'') <> '5'
  GROUP BY 1
),
sih AS (
  SELECT d.sigla_uf, count(*) sih_internacoes, sum(indicador_obito) sih_obitos
  FROM br_ms_sih.aihs_reduzidas x
  JOIN dir d ON d.id_municipio_6 = x.id_municipio_paciente
  WHERE ano BETWEEN 2014 AND 2025 AND cid_principal_categoria IN ('A90','A91') AND tipo_aih = '1'
    AND year(data_internacao) BETWEEN 2014 AND 2024
  GROUP BY 1
),
pop AS (
  SELECT d.sigla_uf, sum(populacao) / 11.0 populacao_media
  FROM br_ibge_populacao.municipio p JOIN dir d USING (id_municipio)
  WHERE ano BETWEEN 2014 AND 2024 GROUP BY 1
)
SELECT * FROM sinan LEFT JOIN sih USING (sigla_uf) LEFT JOIN pop USING (sigla_uf) ORDER BY sigla_uf;
