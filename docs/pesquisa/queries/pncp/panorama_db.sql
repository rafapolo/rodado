-- PNCP (Portal Nacional de Contratações Públicas), panorama por ano: editais, contratos e atas (2026 até 24/11)
-- de União, estados e municípios, ligados pela chave do edital (numeroControlePNCP).
-- Valores em R$ mi, só registros abaixo de R$ 1 bi: a fonte aceita qualquer número e poucos
-- registros de trilhões dominariam a soma. Contratos: uma linha por contrato, a versão mais recente (a fonte repete).
WITH editais AS (
  SELECT numeroControlePNCP, try_cast(left(dataPublicacaoPncp, 10) AS DATE) publicado,
         valorTotalEstimado, valorTotalHomologado, orgaoEntidade.esferaId esfera, orgaoEntidade.cnpj orgao, unidadeOrgao.codigoIbge ibge
  FROM br_mgi_pncp.contratacao
), contratos AS (
  SELECT numeroControlePNCP, arg_max(numeroControlePncpCompra, dataAtualizacao) compra,
         arg_max(dataAssinatura, dataAtualizacao) assinado, arg_max(valorGlobal, dataAtualizacao) valor,
         arg_max(niFornecedor, dataAtualizacao) fornecedor
  FROM br_pncp.contratos GROUP BY 1
), e AS (
  SELECT year(publicado) ano, count(*) editais, count(DISTINCT orgao) orgaos,
         count(DISTINCT ibge) FILTER (WHERE esfera = 'M') municipios,
         round(median(valorTotalEstimado) FILTER (WHERE valorTotalEstimado > 0)) mediana_edital_rs,
         round(sum(valorTotalHomologado) FILTER (WHERE valorTotalHomologado < 1e9) / 1e6) homologado_rs_mi,
         count(*) FILTER (WHERE valorTotalEstimado >= 1e9) editais_acima_1bi
  FROM editais GROUP BY 1
), c AS (
  SELECT year(c.assinado) ano, count(*) contratos, count(DISTINCT c.fornecedor) fornecedores,
         round(sum(c.valor) FILTER (WHERE c.valor < 1e9) / 1e6) contratado_rs_mi,
         round(100.0 * count(*) FILTER (WHERE c.assinado < ed.publicado) / count(ed.numeroControlePNCP), 1) pct_assinado_antes_do_edital
  FROM contratos c LEFT JOIN editais ed ON ed.numeroControlePNCP = c.compra GROUP BY 1
), a AS (
  SELECT year(dataPublicacaoPncp) ano, count(*) atas FROM br_mgi_pncp.ata_registro_preco GROUP BY 1
)
SELECT e.ano, e.editais, c.contratos, a.atas, e.orgaos, e.municipios, c.fornecedores,
       e.mediana_edital_rs, e.homologado_rs_mi, c.contratado_rs_mi, e.editais_acima_1bi,
       c.pct_assinado_antes_do_edital
FROM e LEFT JOIN c USING (ano) LEFT JOIN a USING (ano)
WHERE e.ano >= 2021
ORDER BY e.ano
