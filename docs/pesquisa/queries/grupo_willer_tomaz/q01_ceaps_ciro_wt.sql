-- Reembolsos da cota do Senado (CEAPS) pagos à WT Administração de Imóveis e Bens (CNPJ 05.238.819)
SELECT nome_senador, ano, count(*) AS reembolsos, sum(valor_reembolsado) AS valor,
       min(data) AS primeiro, max(data) AS ultimo, any_value(tipo_despesa) AS tipo_despesa
FROM br_senado_ceaps.despesas
WHERE regexp_replace(cpf_cnpj_fornecedor, '[^0-9]', '', 'g') LIKE '05238819%'
GROUP BY nome_senador, ano
ORDER BY ano;
