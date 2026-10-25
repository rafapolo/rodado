-- Aurea Tecnologia e Soluções (57.780.367): capital, dívida ativa e contratos de campanha em 2026
SELECT 'capital social' AS o_que, NULL::DATE AS data, capital_social AS valor, razao_social AS detalhe
FROM br_me_cnpj.empresas_historico WHERE cnpj_basico = '57780367'
UNION ALL
SELECT 'dívida ativa: ' || RECEITA_PRINCIPAL, strptime(DATA_INSCRICAO, '%d/%m/%Y')::DATE, TRY_CAST(VALOR_CONSOLIDADO AS DOUBLE), SITUACAO_INSCRICAO
FROM br_pgfn_dividaativa.divida WHERE regexp_replace(CPF_CNPJ, '[^0-9]', '', 'g') LIKE '57780367%'
UNION ALL
SELECT 'campanha 2026: ' || sigla_partido || ' / ' || cargo, data_despesa, valor_despesa, descricao_despesa
FROM br_tse_eleicoes.despesas_candidato
WHERE ano = 2026 AND regexp_replace(cpf_cnpj_fornecedor, '[^0-9]', '', 'g') LIKE '57780367%'
ORDER BY data NULLS FIRST;
