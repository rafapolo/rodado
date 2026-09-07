-- hipoteses3 · bloco 93 · ESTBAN. 443.814.039 linhas.
-- Um mes so, e o valor fica por VERBETE (nao pivotado): os codigos de verbete
-- do BCB nao estao documentados no espelho, entao escolher aqui quais somar
-- seria chute -- a analise escolhe depois de ver quais aparecem.
SET enable_progress_bar=false; SET memory_limit='8GB'; SET threads=4;

COPY (
  WITH ult AS (SELECT max(ano) AS a FROM br_bcb_estban.agencia)
  SELECT id_municipio, id_verbete,
         sum(TRY_CAST(valor AS DOUBLE))     AS valor,
         approx_count_distinct(cnpj_agencia) AS agencias
  FROM br_bcb_estban.agencia, ult
  WHERE agencia.ano = ult.a
    AND mes = (SELECT max(mes) FROM br_bcb_estban.agencia WHERE ano = (SELECT a FROM ult))
  GROUP BY 1, 2
) TO '__OUT__/h3_estban.csv' (HEADER);
