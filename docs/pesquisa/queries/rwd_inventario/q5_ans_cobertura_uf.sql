-- Quem o SUS não vê: beneficiários de plano privado médico-hospitalar (ANS) por UF, dezembro de cada ano,
-- só a carga mais recente de cada (ano, mês) — cargas diferentes convivem no mesmo mês e dobram a soma.
WITH ult AS (
  SELECT ano, mes, max(data_carga) data_carga FROM br_ans_beneficiario.informacao_consolidada
  WHERE mes = 12 GROUP BY ALL
), ans AS (
  SELECT b.ano, b.sigla_uf,
    sum(quantidade_beneficiario_ativo) FILTER (WHERE cobertura_assistencia_beneficiario ILIKE '%dico%ospital%') beneficiarios
  FROM br_ans_beneficiario.informacao_consolidada b JOIN ult USING (ano, mes, data_carga)
  GROUP BY ALL
), pop AS (
  SELECT p.ano, d.sigla_uf, sum(p.populacao) populacao FROM br_ibge_populacao.municipio p
  JOIN br_bd_diretorios_brasil.municipio d USING (id_municipio) GROUP BY ALL
)
SELECT ans.*, pop.populacao, ans.beneficiarios / pop.populacao cobertura
FROM ans JOIN pop USING (ano, sigla_uf) ORDER BY ano, sigla_uf;
