-- Completude dos campos-chave por fonte, 2022: fração de registros com valor utilizável
-- (NULL conta como vazio; não nulo, não vazio, não "ignorado"/"sem informação"). NULL na saída = campo não existe na fonte.
-- SIH: CID principal está em _categoria OU em _subcategoria, nunca nas duas (coalesce).
-- SINAN SRAG: residência só no código de 6 dígitos.
-- SIA: só registros individualizados (BPA-I, APAC, RAAS), junho de 2022; o BPA consolidado não tem paciente.
WITH sih AS (
  SELECT 'SIH · admissions' fonte, count(*) n,
    avg(coalesce((id_municipio_paciente IS NOT NULL), false)::INT) residencia,
    avg(coalesce((data_internacao IS NOT NULL), false)::INT) data_evento,
    avg(coalesce((idade_paciente IS NOT NULL), false)::INT) idade,
    avg(coalesce((sexo_paciente IN ('Feminino','Masculino')), false)::INT) sexo,
    avg(coalesce((raca_cor_paciente IS NOT NULL AND raca_cor_paciente <> 'Sem Informação'), false)::INT) raca,
    avg(coalesce((coalesce(cid_principal_categoria, cid_principal_subcategoria) IS NOT NULL), false)::INT) cid
  FROM br_ms_sih.aihs_reduzidas WHERE ano = 2022),
sia AS (
  SELECT 'SIA · outpatient (individual records)', count(*),
    avg(coalesce((coalesce(id_paciente_proto,'') <> ''), false)::INT),
    avg(coalesce((ano_realizacao_procedimento IS NOT NULL), false)::INT),
    avg(coalesce((idade_paciente IS NOT NULL), false)::INT),
    avg(coalesce((sexo_paciente IN ('F','M')), false)::INT),
    avg(coalesce((raca_cor_paciente IN ('1','2','3','4','5')), false)::INT),
    avg(coalesce((coalesce(cid_principal_categoria, cid_principal_subcategoria) IS NOT NULL), false)::INT)
  FROM br_ms_sia.producao_ambulatorial WHERE ano = 2022 AND mes = 6 AND instrumento_registro <> 'C'),
sim AS (
  SELECT 'SIM · deaths', count(*),
    avg(coalesce((id_municipio_residencia IS NOT NULL), false)::INT), avg(coalesce((data_obito IS NOT NULL), false)::INT),
    avg(coalesce((idade IS NOT NULL), false)::INT), avg(coalesce((sexo IN ('1','2')), false)::INT),
    avg(coalesce((raca_cor IN ('1.0','2.0','3.0','4.0','5.0','1','2','3','4','5')), false)::INT),
    avg(coalesce((causa_basica IS NOT NULL AND substr(causa_basica,1,1) <> 'R'), false)::INT)
  FROM br_ms_sim.microdados WHERE ano = 2022),
sinasc AS (
  SELECT 'SINASC · live births', count(*),
    avg(coalesce((id_municipio_residencia IS NOT NULL), false)::INT), avg(coalesce((data_nascimento IS NOT NULL), false)::INT),
    avg(coalesce((idade_mae IS NOT NULL), false)::INT), avg(coalesce((sexo IN ('1','2')), false)::INT),
    avg(coalesce((raca_cor IN ('1','2','3','4','5')), false)::INT), NULL
  FROM br_ms_sinasc.microdados WHERE ano = 2022),
dengue AS (
  SELECT 'SINAN · dengue', count(*),
    avg(coalesce((id_municipio_residencia IS NOT NULL), false)::INT), avg(coalesce((data_primeiros_sintomas IS NOT NULL), false)::INT),
    avg(coalesce((idade_paciente IS NOT NULL), false)::INT), avg(coalesce((sexo_paciente IN ('F','M')), false)::INT),
    avg(coalesce((raca_cor_paciente IN ('1','2','3','4','5')), false)::INT), NULL
  FROM br_ms_sinan.microdados_dengue WHERE ano = 2022),
srag AS (
  SELECT 'SINAN · SARI/influenza', count(*),
    avg(coalesce((id_municipio_6_residencia IS NOT NULL), false)::INT), avg(coalesce((data_primeiros_sintomas IS NOT NULL), false)::INT),
    avg(coalesce((data_nascimento IS NOT NULL), false)::INT), avg(coalesce((sexo IS NOT NULL), false)::INT),
    avg(coalesce((raca_cor IN ('1','2','3','4','5')), false)::INT), NULL
  FROM br_ms_sinan.microdados_influenza_srag WHERE ano = 2022),
viol AS (
  SELECT 'SINAN · violence', count(*),
    avg(coalesce((coalesce(ID_MN_RESI,'') <> ''), false)::INT), avg(coalesce((DT_OCOR IS NOT NULL AND DT_OCOR <> ''), false)::INT),
    avg(coalesce((coalesce(NU_IDADE_N,'') <> ''), false)::INT), avg(coalesce((CS_SEXO IN ('F','M')), false)::INT),
    avg(coalesce((CS_RACA IN ('1','2','3','4','5')), false)::INT), NULL
  FROM br_ms_sinan_violencia.microdados_violencia WHERE ano_sinan = '2022'),
sisvan AS (
  SELECT 'SISVAN · nutrition', count(*),
    avg(coalesce((id_municipio IS NOT NULL), false)::INT), avg(coalesce((data_acompanhamento IS NOT NULL), false)::INT),
    avg(coalesce((idade IS NOT NULL), false)::INT), avg(coalesce((sexo IN ('F','M')), false)::INT),
    avg(coalesce((raca_cor IN ('1','2','3','4','5')), false)::INT), NULL
  FROM br_ms_sisvan.microdados WHERE ano = 2022)
SELECT * FROM sih UNION ALL SELECT * FROM sia UNION ALL SELECT * FROM sim UNION ALL SELECT * FROM sinasc
UNION ALL SELECT * FROM dengue UNION ALL SELECT * FROM srag UNION ALL SELECT * FROM viol UNION ALL SELECT * FROM sisvan;
