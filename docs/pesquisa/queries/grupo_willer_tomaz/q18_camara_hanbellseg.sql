-- Cota parlamentar da Câmara paga à Hanbellseg (61.300.011), fornecedora da campanha de Flávio em 2026
SELECT nome_parlamentar, sigla_partido, categoria_despesa, count(*) AS lancamentos,
       sum(valor_liquido) AS valor, min(data_emissao) AS primeiro, max(data_emissao) AS ultimo
FROM br_camara_dados_abertos.despesa
WHERE regexp_replace(cnpj_cpf_fornecedor, '[^0-9]', '', 'g') LIKE '61300011%'
GROUP BY ALL;
