-- hipoteses3 · bloco 61 · MATRIZ DE PAPEIS POR CNPJ (b): integridade, credito,
-- politica. Arquivo separado do bloco (a) de proposito: se um papel quebrar por
-- mudanca de schema, o runner perde um bloco, nao a matriz inteira.
SET enable_progress_bar=false;
SET memory_limit='6GB';
SET threads=4;

CREATE OR REPLACE TEMP MACRO d14(x) AS
  CASE WHEN length(regexp_replace(CAST(x AS VARCHAR), '[^0-9]', '', 'g')) = 14
       THEN regexp_replace(CAST(x AS VARCHAR), '[^0-9]', '', 'g') END;

COPY (
  WITH papeis AS (
    -- integridade
    SELECT d14(cpf_cnpj_sancionado) AS cnpj, 'ceis' AS papel, count(*) AS n, NULL::DOUBLE AS valor
    FROM br_cgu_sancoes.ceis GROUP BY ALL
    UNION ALL SELECT d14(cpf_cnpj_sancionado), 'cnep', count(*), NULL
    FROM br_cgu_sancoes.cnep GROUP BY ALL
    UNION ALL SELECT d14(cnpj_entidade), 'cepim', count(*), NULL
    FROM br_cgu_sancoes.cepim GROUP BY ALL
    UNION ALL SELECT d14(cnpj_sancionado), 'leniencia', count(*), NULL
    FROM br_cgu_sancoes.acordos_leniencia GROUP BY ALL
    UNION ALL SELECT d14(CPF_CNPJ), 'tcu_inidoneo', count(*), NULL
    FROM br_tcu_inidoneos.empresas GROUP BY ALL
    UNION ALL SELECT d14(CPF_CNPJ), 'bcb_penalidade', count(*), NULL
    FROM br_bcb_penalidades.penalidades GROUP BY ALL
    UNION ALL SELECT d14(CPF_CNPJ), 'pgfn_divida_ativa', count(*),
           sum(TRY_CAST(replace(CAST(VALOR_CONSOLIDADO AS VARCHAR), ',', '.') AS DOUBLE))
    FROM br_pgfn_dividaativa.divida GROUP BY ALL
    UNION ALL SELECT d14(cpf_cnpj_infrator), 'ibama_autuado', count(*),
           sum(TRY_CAST(val_auto_infracao AS DOUBLE))
    FROM br_ibama_autos.auto_infracao GROUP BY ALL
    UNION ALL SELECT d14(cpf_cnpj_embargado), 'ibama_embargado', count(*), NULL
    FROM br_ibama_embargos_novo.termo_embargo GROUP BY ALL

    -- credito e fomento
    UNION ALL SELECT d14(cnpj_cliente), 'bndes_automatica', count(*),
           sum(TRY_CAST(valor_desembolsado AS DOUBLE))
    FROM br_bndes_operacoes_contratadas.operacoes_indiretas_automaticas GROUP BY ALL
    UNION ALL SELECT d14(cnpj_cliente), 'bndes_nao_automatica', count(*),
           sum(TRY_CAST(valor_desembolsado AS DOUBLE))
    FROM br_bndes_operacoes_contratadas.operacoes_nao_automaticas GROUP BY ALL
    UNION ALL SELECT d14(cnpj), 'sicor_mutuario_rural', count(*), NULL
    FROM br_bcb_sicor.recurso_publico_mutuario GROUP BY ALL

    -- politica: o doador de campanha PJ (so ate 2014, o STF proibiu depois --
    -- reaparecer aqui e a marca de quem doou no ultimo ciclo em que era legal)
    UNION ALL SELECT d14(cpf_cnpj_doador), 'doador_campanha', count(*),
           sum(TRY_CAST(valor_receita AS DOUBLE))
    FROM br_tse_eleicoes.receitas_candidato GROUP BY ALL
    UNION ALL SELECT d14(cpf_cnpj_doador), 'doador_partido', count(*),
           sum(TRY_CAST(valor_receita AS DOUBLE))
    FROM br_tse_eleicoes.receitas_orgao_partidario GROUP BY ALL
    UNION ALL SELECT d14(cnpj_candidato), 'comite_candidato', count(*), NULL
    FROM br_tse_eleicoes.despesas_candidato GROUP BY ALL
  )
  SELECT cnpj, substr(cnpj, 1, 8) AS raiz, papel, n, valor
  FROM papeis WHERE cnpj IS NOT NULL
) TO '__OUT__/h3_cnpj_papeis_b.csv' (HEADER);
