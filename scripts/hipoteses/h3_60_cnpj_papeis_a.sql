-- hipoteses3 · bloco 60 · MATRIZ DE PAPEIS POR CNPJ (a): contratacao publica.
--
-- A cascata F0-F7 de tasks/hipoteses.md filtra "tem chave territorial", entao
-- ela NUNCA contou este espaco: 49 datasets carregam CNPJ, e a hipotese aqui
-- nao e uma correlacao entre municipios, e "a empresa que faz A tambem faz B".
--
-- Mesmo truque do painel municipal: em vez de uma query por par de papeis
-- (C(35,2) = 595 pares), extrai-se UMA tabela longa (cnpj, papel, n, valor) e
-- todos os pares saem depois, em numpy, de graca.
--
-- Normalizacao: so digitos, e so o que sobra com 14 -- as colunas `cpf_cnpj`
-- misturam PF e PJ, e comparar 11 com 14 digitos casa lixo. `raiz` (8 digitos)
-- fica ao lado porque grupo economico se detecta por ela, nao pelo CNPJ cheio.
SET enable_progress_bar=false;
SET memory_limit='6GB';
SET threads=4;

CREATE OR REPLACE TEMP MACRO d14(x) AS
  CASE WHEN length(regexp_replace(CAST(x AS VARCHAR), '[^0-9]', '', 'g')) = 14
       THEN regexp_replace(CAST(x AS VARCHAR), '[^0-9]', '', 'g') END;

COPY (
  WITH papeis AS (
    -- PNCP nao tem coluna `cnpj`: o identificador do fornecedor e `niFornecedor`
    -- (NI = numero de identificacao, CNPJ ou CPF conforme `tipoPessoa`).
    SELECT d14(t."niFornecedor") AS cnpj14, 'pncp_fornecedor' AS papel,
           count(*) AS n, sum(TRY_CAST(t."valorGlobal" AS DOUBLE)) AS valor
    FROM br_pncp.contratos AS t GROUP BY ALL

    UNION ALL SELECT d14(cpf_cnpj_contratado), 'cgu_contratado_federal',
           count(*), sum(TRY_CAST(valor_final_compra AS DOUBLE))
    FROM br_cgu_licitacao_contrato.contrato_compra GROUP BY ALL

    UNION ALL SELECT d14(cpf_cnpj_vencedor), 'cgu_licitacao_vencedor', count(*), NULL
    FROM br_cgu_licitacao_contrato.licitacao_item GROUP BY ALL

    UNION ALL SELECT d14(cpf_cnpj_participante), 'cgu_licitacao_participante', count(*), NULL
    FROM br_cgu_licitacao_contrato.licitacao_participante GROUP BY ALL

    UNION ALL SELECT d14(cnpj_favorecido_empenho), 'transferegov_favorecido', count(*), NULL
    FROM br_transferegov.transferencias GROUP BY ALL

    UNION ALL SELECT d14(CNPJ_FORNECEDOR_CONTRATO_ACOMPANHAMENTO_OBRA), 'siconv_fornecedor_obra', count(*), NULL
    FROM br_transferegov_siconv.siconv_acomp_obras_contratos_medicoes GROUP BY ALL

    UNION ALL SELECT d14(CNPJ_PARTICIPANTE), 'siconv_consorciado', count(*), NULL
    FROM br_transferegov_siconv.siconv_consorcios GROUP BY ALL

    UNION ALL SELECT d14(cnpj_cpf_favorecido), 'cartao_corporativo', count(*), NULL
    FROM br_cgu_cartao_pagamento.microdados_governo_federal GROUP BY ALL

    UNION ALL SELECT d14(cnpj_cpf_fornecedor), 'camara_fornecedor', count(*), NULL
    FROM br_camara_dados_abertos.despesa GROUP BY ALL

    UNION ALL SELECT d14(cpf_cnpj_fornecedor), 'senado_ceaps_fornecedor', count(*), NULL
    FROM br_senado_ceaps.despesas GROUP BY ALL

    UNION ALL SELECT d14(CNPJCPFContratado), 'tce_rj_contratado_municipio', count(*), NULL
    FROM br_tce_rj.contratos_municipio GROUP BY ALL

    UNION ALL SELECT d14(EmpresaCNPJ), 'tce_es_obra', count(*), NULL
    FROM br_tce_es.obras_publicas GROUP BY ALL

    UNION ALL SELECT d14(cnpj_do_fornecedor), 'bps_fornecedor_saude', count(*), NULL
    FROM br_saude_bps.dados GROUP BY ALL

    UNION ALL SELECT d14(cnpj_empresa), 'terceirizacao_federal', count(*), NULL
    FROM br_cgu_pessoal_executivo_federal.terceirizados GROUP BY ALL

    UNION ALL SELECT d14(s.cnpj), 'sicaf_habilitado', count(*), NULL
    FROM br_comprasgov_sicaf.fornecedores AS s GROUP BY ALL
  )
  SELECT cnpj14 AS cnpj, substr(cnpj14, 1, 8) AS raiz, papel, n, valor
  FROM papeis WHERE cnpj14 IS NOT NULL
) TO '__OUT__/h3_cnpj_papeis_a.csv' (HEADER);
