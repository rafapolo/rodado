-- Dentro do SINAN, que é dado por registro: letalidade por faixa etária e comorbidade, 2024
-- (o ano da epidemia, com o campo de comorbidade preenchido em >98%).
-- idade_paciente vem como '<unidade>-<valor>': 4 = anos; outras unidades = menos de 1 ano.
WITH b AS (
  SELECT
    CASE WHEN idade_paciente LIKE '4-%' THEN try_cast(substr(idade_paciente,3) AS INT) ELSE 0 END idade,
    possui_diabetes = '1' diabetes, possui_hipertensao = '1' hipertensao,
    possui_doenca_renal = '1' renal,
    evolucao_caso = '2' obito
  FROM br_ms_sinan.microdados_dengue
  WHERE ano = 2024 AND coalesce(trim(classificacao_final),'') <> '5'
)
SELECT
  CASE WHEN idade < 15 THEN '00-14' WHEN idade < 40 THEN '15-39' WHEN idade < 60 THEN '40-59'
       WHEN idade < 80 THEN '60-79' ELSE '80+' END faixa,
  count(*) casos, sum(obito::INT) obitos,
  count(*) FILTER (WHERE diabetes) casos_diab, sum((obito AND diabetes)::INT) obitos_diab,
  count(*) FILTER (WHERE NOT diabetes) casos_sem_diab, sum((obito AND NOT diabetes)::INT) obitos_sem_diab,
  count(*) FILTER (WHERE hipertensao) casos_has, sum((obito AND hipertensao)::INT) obitos_has,
  count(*) FILTER (WHERE NOT hipertensao) casos_sem_has, sum((obito AND NOT hipertensao)::INT) obitos_sem_has,
  count(*) FILTER (WHERE renal) casos_renal, sum((obito AND renal)::INT) obitos_renal
FROM b GROUP BY 1 ORDER BY 1;
