-- A antiga Bonsucesso Consultoria S/A (58.311.064): nome, capital e quadro mês a mês (sem documento)
SELECT 'cadastro' AS o_que, razao_social AS valor, capital_social, inicio, fim
FROM br_me_cnpj.empresas_historico WHERE cnpj_basico = '58311064'
UNION ALL
SELECT 'quadro', nome || ' (qualif. ' || qualificacao || ', entrada ' || data_entrada_sociedade || ')', NULL, primeiro_retrato, ultimo_retrato
FROM br_me_cnpj.socios_historico WHERE cnpj_basico = '58311064'
ORDER BY o_que, inicio;
