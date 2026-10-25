-- Dívida ativa da União do grupo de mídia (Difusora TV, Difusora Comunicação, Curimã, Caxias, Jota):
-- cada inscrição contada uma vez, com quantas das cinco empresas respondem por ela
WITH d AS (
  SELECT NUMERO_INSCRICAO, substr(regexp_replace(CPF_CNPJ, '[^0-9]', '', 'g'), 1, 8) AS raiz,
         SITUACAO_INSCRICAO, TRY_CAST(VALOR_CONSOLIDADO AS DOUBLE) AS valor
  FROM br_pgfn_dividaativa.divida
  WHERE substr(regexp_replace(CPF_CNPJ, '[^0-9]', '', 'g'), 1, 8)
        IN ('06275598', '08661220', '07158751', '63432751', '23412791')
)
SELECT count(*) AS inscricoes, sum(valor) AS valor,
       count(*) FILTER (WHERE empresas = 5) AS inscricoes_com_as_cinco,
       sum(valor) FILTER (WHERE empresas = 5) AS valor_com_as_cinco,
       count(*) FILTER (WHERE negociada) AS inscricoes_negociadas
FROM (
  SELECT NUMERO_INSCRICAO, max(valor) AS valor, count(DISTINCT raiz) AS empresas,
         bool_or(SITUACAO_INSCRICAO ILIKE '%NEGOCIAD%' OR SITUACAO_INSCRICAO ILIKE '%PARCELAD%') AS negociada
  FROM d GROUP BY NUMERO_INSCRICAO
);
