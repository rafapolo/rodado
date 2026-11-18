-- Dengue: casos prováveis (classificação final diferente de descartado), tipados por sorotipo e
-- com PCR com resultado, por ano, mês de início dos sintomas e UF de residência.
SELECT ano, month(data_primeiros_sintomas) mes, substr(id_municipio_residencia, 1, 2) id_uf,
  count(*) provaveis,
  count(*) FILTER (WHERE resultado_pcr IN ('1', '2', '3')) pcr_com_resultado,
  count(*) FILTER (WHERE sorotipo = '1') denv1,
  count(*) FILTER (WHERE sorotipo = '2') denv2,
  count(*) FILTER (WHERE sorotipo = '3') denv3,
  count(*) FILTER (WHERE sorotipo = '4') denv4
FROM br_ms_sinan.microdados_dengue
WHERE ano BETWEEN 2014 AND 2026 AND coalesce(trim(classificacao_final), '') <> '5'
GROUP BY ALL;
