-- Fit-for-purpose: completude e atraso dos campos-chave do SINAN dengue, por ano (casos prováveis).
SELECT ano,
  count(*) provaveis,
  avg((internacao IS NULL OR internacao IN ('9','')) ::INT) pct_internacao_ignorada,
  avg((evolucao_caso IS NULL OR evolucao_caso IN ('9',''))::INT) pct_evolucao_ignorada,
  avg((raca_cor_paciente IS NULL OR raca_cor_paciente IN ('9',''))::INT) pct_raca_ignorada,
  avg((criterio_confirmacao = '1')::INT) pct_confirmacao_laboratorial,
  avg((id_municipio_residencia IS NULL)::INT) pct_sem_municipio,
  avg((possui_diabetes IS NULL OR possui_diabetes IN ('9',''))::INT) pct_diabetes_ignorado,
  avg((trim(classificacao_final) = '8')::INT) pct_inconclusivo,
  quantile_cont(date_diff('day', data_primeiros_sintomas, data_notificacao), 0.5) mediana_dias_sintoma_notificacao,
  quantile_cont(date_diff('day', data_notificacao, data_encerramento), 0.5) mediana_dias_notificacao_encerramento
FROM br_ms_sinan.microdados_dengue
WHERE ano BETWEEN 2014 AND 2025 AND coalesce(trim(classificacao_final),'') <> '5'
GROUP BY ano ORDER BY ano;
