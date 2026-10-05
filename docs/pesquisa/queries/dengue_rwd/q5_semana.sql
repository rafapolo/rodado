-- Série semanal de casos prováveis por semana epidemiológica de início dos sintomas, 2014-2025.
SELECT semana_sintomas, count(*) provaveis
FROM br_ms_sinan.microdados_dengue
WHERE ano BETWEEN 2014 AND 2025 AND coalesce(trim(classificacao_final),'') <> '5'
  AND semana_sintomas IS NOT NULL
GROUP BY 1 ORDER BY 1;
