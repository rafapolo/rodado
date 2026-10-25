-- Empresas em que Willer Tomaz de Souza consta pessoalmente no quadro desde 2021
SELECT s.cnpj_basico, e.razao_social, s.qualificacao, s.data_entrada_sociedade, s.primeiro_retrato, s.ultimo_retrato
FROM br_me_cnpj.socios_historico s LEFT JOIN br_me_cnpj.empresas e USING (cnpj_basico)
WHERE s.nome = 'WILLER TOMAZ DE SOUZA'
ORDER BY s.data_entrada_sociedade;
