-- Espírito Santo: casos prováveis no SINAN nacional x internações por dengue na SIH, por ano, 2014-2024.
-- Entre 2021 e 2024 o estado notificou em sistema próprio e quase some do arquivo nacional.
WITH s AS (
  SELECT ano, count(*) sinan_provaveis FROM br_ms_sinan.microdados_dengue
  WHERE ano BETWEEN 2014 AND 2024 AND id_municipio_residencia LIKE '32%'
    AND coalesce(trim(classificacao_final),'') <> '5'
  GROUP BY 1
), h AS (
  SELECT year(data_internacao) ano, count(*) sih_internacoes FROM br_ms_sih.aihs_reduzidas
  WHERE ano BETWEEN 2014 AND 2025 AND cid_principal_categoria IN ('A90','A91') AND tipo_aih = '1'
    AND id_municipio_paciente LIKE '32%' AND year(data_internacao) BETWEEN 2014 AND 2024
  GROUP BY 1
)
SELECT * FROM s FULL JOIN h USING (ano) ORDER BY ano;
