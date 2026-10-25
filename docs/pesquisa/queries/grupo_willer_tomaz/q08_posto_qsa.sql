-- Sócios do posto e razão social no período (sem documento)
SELECT 'socio' AS o_que, nome AS valor, data_entrada_sociedade::VARCHAR AS entrada, primeiro_retrato, ultimo_retrato
FROM br_me_cnpj.socios_historico WHERE cnpj_basico = '35711858'
UNION ALL
SELECT 'razao_social', razao_social, NULL, inicio, fim
FROM br_me_cnpj.empresas_historico WHERE cnpj_basico = '35711858'
ORDER BY o_que, primeiro_retrato;
