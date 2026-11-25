-- O PNCP por dentro: consultas que geram os CSVs desta pasta.
-- Rodar: python3 docs/pesquisa/queries/pncp/roda.py (cada bloco "-- arquivo: x.csv" vira um CSV,
-- pelo beelink, só leitura). Figuras: scripts/plot_pncp.py.
-- Editais = br_mgi_pncp.contratacao (uma linha por compra); contratos = br_pncp.contratos,
-- deduplicado por numeroControlePNCP (a fonte repete o contrato em 2025-2026); atas =
-- br_mgi_pncp.ata_registro_preco. Ano do edital = ano da publicação no portal.

-- arquivo: editais_mes.csv — editais publicados por mês e esfera do órgão
SELECT strftime(try_cast(left(dataPublicacaoPncp, 10) AS DATE), '%Y-%m') mes,
       orgaoEntidade.esferaId esfera, count(*) editais
FROM br_mgi_pncp.contratacao GROUP BY ALL ORDER BY 1, 2;

-- arquivo: volume_ano.csv — editais, contratos e atas por ano de publicação no portal
WITH c AS (SELECT numeroControlePNCP, min(dataPublicacaoPncp) pub FROM br_pncp.contratos GROUP BY 1)
SELECT 'editais' tipo, year(try_cast(left(dataPublicacaoPncp, 10) AS DATE)) ano, count(*) n FROM br_mgi_pncp.contratacao GROUP BY ALL
UNION ALL SELECT 'contratos', year(pub), count(*) FROM c GROUP BY ALL
UNION ALL SELECT 'atas', year(dataPublicacaoPncp), count(*) FROM br_mgi_pncp.ata_registro_preco GROUP BY ALL
ORDER BY 1, 2;

-- arquivo: municipios_uf_2025.csv — municípios com ao menos um edital municipal publicado em 2025
WITH pub AS (
  SELECT DISTINCT unidadeOrgao.codigoIbge id_municipio FROM br_mgi_pncp.contratacao
  WHERE orgaoEntidade.esferaId = 'M' AND dataPublicacaoPncp LIKE '2025%')
SELECT m.sigla_uf, count(*) municipios, count(p.id_municipio) com_edital
FROM br_bd_diretorios_brasil.municipio m LEFT JOIN pub p ON p.id_municipio = m.id_municipio
GROUP BY 1 ORDER BY 1;

-- arquivo: modalidade_2025.csv — editais de 2025 por modalidade: quantidade e valor homologado
-- (só registros abaixo de R$ 1 bi; ver valores_2025.csv)
SELECT modalidadeNome modalidade, count(*) editais,
       sum(valorTotalHomologado) FILTER (WHERE valorTotalHomologado > 0 AND valorTotalHomologado < 1e9) homologado
FROM br_mgi_pncp.contratacao WHERE dataPublicacaoPncp LIKE '2025%' GROUP BY 1 ORDER BY 2 DESC;

-- arquivo: valores_2025.csv — distribuição do valor estimado dos editais de 2025, em faixas de
-- um quarto de ordem de grandeza (log10), com a soma de cada faixa
SELECT floor(log10(valorTotalEstimado) * 4) / 4 faixa_log10, count(*) editais, sum(valorTotalEstimado) soma
FROM br_mgi_pncp.contratacao
WHERE dataPublicacaoPncp LIKE '2025%' AND valorTotalEstimado >= 1
GROUP BY 1 ORDER BY 1;

-- arquivo: antes_do_edital_2025.csv — contratos assinados em 2025 antes de o edital deles
-- aparecer no portal, pela modalidade do edital
WITH c AS (SELECT numeroControlePNCP, any_value(numeroControlePncpCompra) compra, any_value(dataAssinatura) assinado
           FROM br_pncp.contratos GROUP BY 1)
SELECT e.modalidadeNome modalidade, count(*) contratos,
       count(*) FILTER (WHERE c.assinado < try_cast(left(e.dataPublicacaoPncp, 10) AS DATE)) antes,
       median(try_cast(left(e.dataPublicacaoPncp, 10) AS DATE) - c.assinado)
         FILTER (WHERE c.assinado < try_cast(left(e.dataPublicacaoPncp, 10) AS DATE)) mediana_dias
FROM c JOIN br_mgi_pncp.contratacao e ON e.numeroControlePNCP = c.compra
WHERE year(c.assinado) = 2025 GROUP BY 1 ORDER BY 2 DESC;

-- arquivo: sistemas_2025.csv — de que sistema saiu cada edital de 2025 (o portal recebe por API)
SELECT usuarioNome sistema, count(*) editais, count(DISTINCT orgaoEntidade.cnpj) orgaos
FROM br_mgi_pncp.contratacao WHERE dataPublicacaoPncp LIKE '2025%' GROUP BY 1 ORDER BY 2 DESC;

-- arquivo: cobertura_estatais.csv — estatais (natureza 2011 empresa pública, 2038 sociedade de economia
-- mista) e Sistema S (pelo nome) com matriz ativa no CNPJ, e quantas aparecem como órgão no portal
WITH org AS (
  SELECT DISTINCT left(orgaoEntidade.cnpj, 8) cb FROM br_mgi_pncp.contratacao
  UNION SELECT DISTINCT left(orgaoEntidade.cnpj, 8) FROM br_pncp.contratos
  UNION SELECT DISTINCT left(cnpjOrgao, 8) FROM br_mgi_pncp.ata_registro_preco),
ativas AS (SELECT DISTINCT cnpj_basico FROM br_me_cnpj.estabelecimentos
           WHERE identificador_matriz_filial = '1' AND situacao_cadastral = '2'),
e AS (
  SELECT DISTINCT e.cnpj_basico,
    CASE WHEN e.natureza_juridica = '2011' THEN 'empresa pública'
         WHEN e.natureza_juridica = '2038' THEN 'sociedade de economia mista'
         WHEN regexp_matches(e.razao_social, '^(SERVICO (NACIONAL|SOCIAL) D[AEO]|SERVICO BRASILEIRO DE APOIO AS MICRO|SERVICO DE APOIO AS MICRO)') THEN 'Sistema S' END grupo
  FROM br_me_cnpj.empresas e JOIN ativas a USING (cnpj_basico))
SELECT grupo, count(*) ativas, count(org.cb) no_portal
FROM e LEFT JOIN org ON org.cb = e.cnpj_basico WHERE grupo IS NOT NULL GROUP BY 1 ORDER BY 1;
