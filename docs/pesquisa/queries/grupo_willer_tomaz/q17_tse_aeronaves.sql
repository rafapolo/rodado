-- Despesas de campanha com a Jet Line (10.332.184) e a Direção Táxi Aéreo (43.143.216): a descrição traz a aeronave
SELECT d.ano, c.nome_urna, d.sigla_partido, d.cargo, d.data_despesa, d.valor_despesa, d.descricao_despesa
FROM br_tse_eleicoes.despesas_candidato d
LEFT JOIN (SELECT DISTINCT ano, sequencial, nome_urna FROM br_tse_eleicoes.candidatos) c
  ON c.ano = d.ano AND c.sequencial = d.sequencial_candidato
WHERE substr(lpad(regexp_replace(d.cpf_cnpj_fornecedor, '[^0-9]', '', 'g'), 14, '0'), 1, 8) IN ('10332184', '43143216')
  AND d.valor_despesa >= 100000
ORDER BY d.ano;
