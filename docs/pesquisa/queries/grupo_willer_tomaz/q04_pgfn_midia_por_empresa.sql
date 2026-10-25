-- O mesmo, por empresa e papel (principal ou corresponsável)
SELECT NOME_DEVEDOR, upper(TIPO_DEVEDOR) AS papel, count(*) AS inscricoes, sum(TRY_CAST(VALOR_CONSOLIDADO AS DOUBLE)) AS valor
FROM br_pgfn_dividaativa.divida
WHERE substr(regexp_replace(CPF_CNPJ, '[^0-9]', '', 'g'), 1, 8)
      IN ('06275598', '08661220', '07158751', '63432751', '23412791')
GROUP BY ALL
ORDER BY NOME_DEVEDOR, papel;
