-- Endereço da Jota Comunicação (23.412.791) e da Rocha Holding Patrimonial (50.570.260) mês a mês
SELECT cnpj_basico, inicio, fim, logradouro, numero, complemento, cep, email
FROM br_me_cnpj.estabelecimentos_historico
WHERE cnpj_basico IN ('23412791', '50570260')
ORDER BY cnpj_basico, inicio;
