-- Mesmo conceito, códigos diferentes: valores brutos de sexo e raça/cor por fonte, 2022.
WITH x AS (
  SELECT 'SIH' fonte, 'sex' campo, sexo_paciente v, count(*) n FROM br_ms_sih.aihs_reduzidas WHERE ano = 2022 GROUP BY ALL
  UNION ALL SELECT 'SIH','race', raca_cor_paciente, count(*) FROM br_ms_sih.aihs_reduzidas WHERE ano = 2022 GROUP BY ALL
  UNION ALL SELECT 'SIA','sex', sexo_paciente, count(*) FROM br_ms_sia.producao_ambulatorial WHERE ano = 2022 GROUP BY ALL
  UNION ALL SELECT 'SIA','race', raca_cor_paciente, count(*) FROM br_ms_sia.producao_ambulatorial WHERE ano = 2022 GROUP BY ALL
  UNION ALL SELECT 'SIM','sex', sexo, count(*) FROM br_ms_sim.microdados WHERE ano = 2022 GROUP BY ALL
  UNION ALL SELECT 'SIM','race', raca_cor, count(*) FROM br_ms_sim.microdados WHERE ano = 2022 GROUP BY ALL
  UNION ALL SELECT 'SINASC','sex', sexo, count(*) FROM br_ms_sinasc.microdados WHERE ano = 2022 GROUP BY ALL
  UNION ALL SELECT 'SINASC','race', raca_cor, count(*) FROM br_ms_sinasc.microdados WHERE ano = 2022 GROUP BY ALL
  UNION ALL SELECT 'SINAN dengue','sex', sexo_paciente, count(*) FROM br_ms_sinan.microdados_dengue WHERE ano = 2022 GROUP BY ALL
  UNION ALL SELECT 'SINAN dengue','race', raca_cor_paciente, count(*) FROM br_ms_sinan.microdados_dengue WHERE ano = 2022 GROUP BY ALL
  UNION ALL SELECT 'SINAN SARI','sex', sexo, count(*) FROM br_ms_sinan.microdados_influenza_srag WHERE ano = 2022 GROUP BY ALL
  UNION ALL SELECT 'SINAN SARI','race', raca_cor, count(*) FROM br_ms_sinan.microdados_influenza_srag WHERE ano = 2022 GROUP BY ALL
  UNION ALL SELECT 'SINAN violence','sex', CS_SEXO, count(*) FROM br_ms_sinan_violencia.microdados_violencia WHERE ano_sinan = '2022' GROUP BY ALL
  UNION ALL SELECT 'SINAN violence','race', CS_RACA, count(*) FROM br_ms_sinan_violencia.microdados_violencia WHERE ano_sinan = '2022' GROUP BY ALL
  UNION ALL SELECT 'SISVAN','sex', sexo, count(*) FROM br_ms_sisvan.microdados WHERE ano = 2022 GROUP BY ALL
  UNION ALL SELECT 'SISVAN','race', raca_cor, count(*) FROM br_ms_sisvan.microdados WHERE ano = 2022 GROUP BY ALL
  UNION ALL SELECT 'ANS','sex', sexo, count(*) FROM br_ans_beneficiario.informacao_consolidada WHERE ano = 2022 AND mes = 12 GROUP BY ALL
)
SELECT fonte, campo, v, n, round(n / sum(n) OVER (PARTITION BY fonte, campo), 4) AS fracao FROM x ORDER BY fonte, campo, n DESC;
