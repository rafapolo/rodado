-- Contato cadastral da Voga Serviços Contábeis (10.943.907), da Aragão e Tomaz Advogados (31.624.699),
-- da Trinca (58.311.092) e da Neoverde (58.311.064)
SELECT e.razao_social, t.cnpj, t.logradouro, t.numero, t.complemento, t.ddd_1, t.telefone_1, t.email
FROM br_me_cnpj.estabelecimentos t JOIN br_me_cnpj.empresas e USING (cnpj_basico)
WHERE t.cnpj_basico IN ('10943907', '31624699', '58311092', '58311064')
ORDER BY e.razao_social;
