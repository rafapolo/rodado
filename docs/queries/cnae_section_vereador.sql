-- % of Economic Activities (CNAE Section) from Companies of Election Candidates
-- Position: Vereador - All years
SELECT 
  c2.secao,
  c2.descricao_secao,
  COUNT(DISTINCT d.cpf_cnpj_fornecedor) AS qtde_empresas,
  COUNT(DISTINCT ca.titulo_eleitoral) AS qtde_candidatos,
  COUNT(*) AS total_transacoes,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS percentage
FROM basedosdados.br_tse_eleicoes.candidatos ca
JOIN basedosdados.br_tse_eleicoes.despesas_candidato d ON ca.titulo_eleitoral = d.titulo_eleitoral_candidato
JOIN basedosdados.br_bd_diretorios_brasil.cnae_2 c2 ON d.cnae_2_fornecedor_subclasse = c2.subclasse
WHERE ca.cargo = 'vereador'
  AND d.cnae_2_fornecedor_subclasse IS NOT NULL
  AND d.ano >= 2020
GROUP BY c2.secao, c2.descricao_secao
ORDER BY total_transacoes DESC