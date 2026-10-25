-- Quadro de administradores da WT Administração desde 2021 (sem documento)
SELECT nome, qualificacao, data_entrada_sociedade, primeiro_retrato, ultimo_retrato
FROM br_me_cnpj.socios_historico
WHERE cnpj_basico = '05238819'
ORDER BY primeiro_retrato;
