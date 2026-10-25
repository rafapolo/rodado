-- Reembolsos da cota do Senado no Petro São José / F de A S Campos Combustíveis (35.711.858)
SELECT nome_senador, nome_fornecedor, count(*) AS reembolsos, sum(valor_reembolsado) AS valor,
       min(data) AS primeiro, max(data) AS ultimo
FROM br_senado_ceaps.despesas
WHERE regexp_replace(cpf_cnpj_fornecedor, '[^0-9]', '', 'g') LIKE '35711858%'
GROUP BY ALL;
