-- Diretoria da Jota Comunicação S/A (sem documento)
SELECT nome, qualificacao, data_entrada_sociedade, primeiro_retrato, ultimo_retrato
FROM br_me_cnpj.socios_historico
WHERE cnpj_basico = '23412791'
ORDER BY primeiro_retrato;
