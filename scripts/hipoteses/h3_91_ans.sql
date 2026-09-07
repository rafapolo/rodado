-- hipoteses3 · bloco 91 · ANS beneficiarios. 2.307.338.481 linhas.
-- Filtra ano mais recente E o ULTIMO MES DISPONIVEL nele: o dado e um estoque
-- mensal repetido, e somar o ano inteiro multiplicaria a carteira por 12.
-- Nao da para cravar `mes = 12`: o ano corrente (2025) vai so ate outubro, e o
-- filtro fixo devolveu ZERO linha na primeira corrida.
SET enable_progress_bar=false; SET memory_limit='8GB'; SET threads=4;
SET temp_directory='/home/polo/tmp_duck';

COPY (
  WITH ult AS (SELECT max(ano) AS ano FROM br_ans_beneficiario.informacao_consolidada)
  SELECT id_municipio,
         sum(TRY_CAST(quantidade_beneficiario_ativo AS DOUBLE))     AS ans_ativos,
         sum(TRY_CAST(quantidade_beneficiario_cancelado AS DOUBLE)) AS ans_cancelados,
         approx_count_distinct(codigo_operadora)                    AS ans_operadoras,
         sum(TRY_CAST(quantidade_beneficiario_ativo AS DOUBLE))
           FILTER (WHERE contratacao_beneficiario ILIKE '%ndividual%') AS ans_individual
  FROM br_ans_beneficiario.informacao_consolidada, ult
  WHERE informacao_consolidada.ano = ult.ano
    AND mes = (SELECT max(mes) FROM br_ans_beneficiario.informacao_consolidada
               WHERE ano = (SELECT max(ano) FROM br_ans_beneficiario.informacao_consolidada))
  GROUP BY 1
) TO '__OUT__/h3_ans.csv' (HEADER);
