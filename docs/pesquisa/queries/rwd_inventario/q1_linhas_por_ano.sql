-- Inventário do RWD de saúde do espelho: linhas por ano, por fonte.
-- SINAN raspado (chikungunya etc.) guarda o ano como texto em NU_ANO/ano_sinan.
SELECT 'SIH · admissions (AIH)' fonte, ano::INT ano, count(*) linhas FROM br_ms_sih.aihs_reduzidas GROUP BY ALL
UNION ALL SELECT 'SIH · professional services', ano::INT, count(*) FROM br_ms_sih.servicos_profissionais GROUP BY ALL
UNION ALL SELECT 'SIA · outpatient production', ano::INT, count(*) FROM br_ms_sia.producao_ambulatorial GROUP BY ALL
UNION ALL SELECT 'SIA · psychosocial care (RAAS)', ano::INT, count(*) FROM br_ms_sia.psicossocial GROUP BY ALL
UNION ALL SELECT 'SIM · deaths', ano::INT, count(*) FROM br_ms_sim.microdados GROUP BY ALL
UNION ALL SELECT 'SINASC · live births', ano::INT, count(*) FROM br_ms_sinasc.microdados GROUP BY ALL
UNION ALL SELECT 'SINAN · dengue', ano::INT, count(*) FROM br_ms_sinan.microdados_dengue GROUP BY ALL
UNION ALL SELECT 'SINAN · SARI/influenza', ano::INT, count(*) FROM br_ms_sinan.microdados_influenza_srag GROUP BY ALL
UNION ALL SELECT 'SINAN · chikungunya', try_cast(NU_ANO AS INT), count(*) FROM br_ms_sinan_chikungunya.microdados_chikungunya GROUP BY ALL
UNION ALL SELECT 'SINAN · zika', try_cast(ano_sinan AS INT), count(*) FROM br_ms_sinan_zika.microdados_zika GROUP BY ALL
UNION ALL SELECT 'SINAN · yellow fever', try_cast(ano_sinan AS INT), count(*) FROM br_ms_sinan_febre_amarela.microdados_febre_amarela GROUP BY ALL
UNION ALL SELECT 'SINAN · malaria (extra-Amazon)', try_cast(ano_sinan AS INT), count(*) FROM br_ms_sinan_malaria.microdados_malaria GROUP BY ALL
UNION ALL SELECT 'SINAN · violence', try_cast(ano_sinan AS INT), count(*) FROM br_ms_sinan_violencia.microdados_violencia GROUP BY ALL
UNION ALL SELECT 'SISVAN · nutrition records', ano::INT, count(*) FROM br_ms_sisvan.microdados GROUP BY ALL
UNION ALL SELECT 'CNES · facilities (monthly)', ano::INT, count(*) FROM br_ms_cnes.estabelecimento GROUP BY ALL
UNION ALL SELECT 'CNES · beds (monthly)', ano::INT, count(*) FROM br_ms_cnes.leito GROUP BY ALL
UNION ALL SELECT 'CNES · professionals (monthly)', ano::INT, count(*) FROM br_ms_cnes.profissional GROUP BY ALL
UNION ALL SELECT 'ANS · private plan enrolment', ano::INT, count(*) FROM br_ans_beneficiario.informacao_consolidada GROUP BY ALL
UNION ALL SELECT 'Vaccination coverage (municipal)', ano::INT, count(*) FROM br_ms_imunizacoes.municipio GROUP BY ALL
UNION ALL SELECT 'Primary care teams (municipal)', ano::INT, count(*) FROM br_ms_atencao_basica.municipio GROUP BY ALL
UNION ALL SELECT 'Controlled-drug sales (SNGPC)', ano::INT, count(*) FROM br_anvisa_medicamentos_industrializados.microdados GROUP BY ALL
UNION ALL SELECT 'Population (MS/IBGE)', ano::INT, count(*) FROM br_ms_populacao.municipio GROUP BY ALL
ORDER BY 1, 2;
