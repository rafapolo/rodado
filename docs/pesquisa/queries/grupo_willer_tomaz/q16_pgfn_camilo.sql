-- Dívida ativa das empresas de Antônio Carlos Camilo Antunes, cada inscrição contada uma vez
WITH emp AS (
  SELECT DISTINCT cnpj_basico FROM br_me_cnpj.socios_historico WHERE nome = 'ANTONIO CARLOS CAMILO ANTUNES'
)
SELECT count(*) AS inscricoes, sum(valor) AS valor, count(DISTINCT devedor) AS empresas_devedoras
FROM (
  SELECT NUMERO_INSCRICAO, max(TRY_CAST(VALOR_CONSOLIDADO AS DOUBLE)) AS valor, any_value(NOME_DEVEDOR) AS devedor
  FROM br_pgfn_dividaativa.divida
  WHERE substr(regexp_replace(CPF_CNPJ, '[^0-9]', '', 'g'), 1, 8) IN (SELECT cnpj_basico FROM emp)
  GROUP BY NUMERO_INSCRICAO
);
