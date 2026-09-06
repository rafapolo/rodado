-- H24-H36 · Moldes de docs/context/moldes.yaml aplicados a fontes que nunca os
-- receberam. Cada COPY é uma perna de hipótese; a análise é 95_inedito.py.
SET enable_progress_bar=false;

-- H24 · SNIS: declarado pelo prestador × base IBGE, NA MESMA TABELA.
--   populacao_urbana_atendida_agua        = o que o prestador informa
--   populacao_urbana_atendida_agua_ibge   = o mesmo ajustado pela base do IBGE
COPY (SELECT id_municipio,
        max(ano) AS snis_ano,
        max(TRY_CAST(populacao_urbana_atendida_agua AS DOUBLE))      AS snis_agua_decl,
        max(TRY_CAST(populacao_urbana_atendida_agua_ibge AS DOUBLE)) AS snis_agua_ibge,
        max(TRY_CAST(populacao_urbana_atendida_esgoto AS DOUBLE))    AS snis_esg_decl,
        max(TRY_CAST(populacao_urbana_atendida_esgoto_ibge AS DOUBLE)) AS snis_esg_ibge,
        max(TRY_CAST(populacao_urbana AS DOUBLE))                    AS snis_pop_urb,
        max(TRY_CAST(extensao_rede_agua AS DOUBLE))                  AS snis_rede_agua
      FROM br_mdr_snis.municipio_agua_esgoto
      WHERE ano >= 2020 GROUP BY 1)
  TO '__OUT__/v_snis.csv' (HEADER);

-- H24b · ANA: outorga de captação, medida por terceiro (município em texto)
COPY (SELECT upper(strip_accents(ing_nm_municipio)) AS mun_nome, ing_sg_ufmunicipio AS uf,
        count(*) AS ana_captacoes,
        sum(TRY_CAST(int_qt_vazaomedia AS DOUBLE)) AS ana_vazao
      FROM br_ana_outorgas.captacoes
      WHERE ing_nm_municipio IS NOT NULL GROUP BY 1,2)
  TO '__OUT__/v_ana.csv' (HEADER);

-- H25 · MUNIC: o município descrevendo a si mesmo (quantos vínculos declara)
COPY (SELECT id_municipio, max(ano) AS munic_ano,
        sum(TRY_CAST(quantidade_vinculo AS DOUBLE)) AS munic_vinculos,
        count(DISTINCT tipo_vinculo) AS munic_tipos
      FROM br_ibge_munic.indicadores_quantidade_vinculo
      WHERE ano >= 2018 GROUP BY 1)
  TO '__OUT__/v_munic.csv' (HEADER);

-- H25b · SICONFI: o que o município EXECUTA (despesa liquidada, por função)
COPY (SELECT id_municipio,
        sum(TRY_CAST(valor AS DOUBLE)) FILTER (WHERE conta_bd ILIKE '%pessoal%') AS sic_pessoal,
        sum(TRY_CAST(valor AS DOUBLE)) AS sic_despesa_total
      FROM br_me_siconfi.municipio_despesas_orcamentarias
      WHERE ano = 2022 AND estagio_bd ILIKE '%liquidada%' GROUP BY 1)
  TO '__OUT__/v_siconfi.csv' (HEADER);

-- H26 · CNES leito DECLARADO × SIH internação FATURADA
COPY (SELECT id_municipio,
        sum(TRY_CAST(quantidade_total AS DOUBLE)) AS cnes_leitos,
        sum(TRY_CAST(quantidade_sus AS DOUBLE))   AS cnes_leitos_sus
      FROM br_ms_cnes.leito WHERE ano = 2023 GROUP BY 1)
  TO '__OUT__/v_cnes_leito.csv' (HEADER);

COPY (SELECT id_municipio_6 AS mun6, count(*) AS sih_internacoes
      FROM br_ms_sih.morbidade_hospitalar WHERE ano = 2023 GROUP BY 1)
  TO '__OUT__/v_sih.csv' (HEADER);

-- H27 · CNO: obra formalmente registrada (contra o domicílio em construção do CNEFE)
COPY (SELECT id_municipio, count(DISTINCT id_cno) AS cno_obras
      FROM br_rf_cno.microdados WHERE id_municipio IS NOT NULL GROUP BY 1)
  TO '__OUT__/v_cno.csv' (HEADER);

-- H28 · CAPAG: a nota que deveria limitar endividamento
COPY (SELECT TRY_CAST("Código Município Completo" AS BIGINT) AS id_municipio,
        max(CAPAG) AS capag, max(TRY_CAST("Indicador 1" AS DOUBLE)) AS capag_ind1,
        max(TRY_CAST("Indicador 2" AS DOUBLE)) AS capag_ind2,
        max(TRY_CAST("Indicador 3" AS DOUBLE)) AS capag_ind3
      FROM br_tesouro_capag.municipios GROUP BY 1)
  TO '__OUT__/v_capag.csv' (HEADER);

-- H28b · operação de crédito efetivamente contratada (receita de capital, SICONFI)
COPY (SELECT id_municipio,
        sum(TRY_CAST(valor AS DOUBLE)) FILTER (WHERE conta_bd ILIKE '%operac%credito%') AS sic_op_credito,
        sum(TRY_CAST(valor AS DOUBLE)) AS sic_receita_total
      FROM br_me_siconfi.municipio_receitas_orcamentarias
      WHERE ano = 2022 AND estagio_bd ILIKE '%realizada%' GROUP BY 1)
  TO '__OUT__/v_siconfi_rec.csv' (HEADER);

-- H29 · TCU inidôneos: outra lista de impedimento, testada contra pagamento municipal
COPY (SELECT DISTINCT regexp_replace(CAST("CPF_CNPJ" AS VARCHAR),'[^0-9]','','g') AS doc
      FROM br_tcu_inidoneos.empresas
      WHERE length(regexp_replace(CAST("CPF_CNPJ" AS VARCHAR),'[^0-9]','','g')) = 14)
  TO '__OUT__/v_tcu_docs.csv' (HEADER);

-- H32 · SISU: vaga onde há aluno ou onde há campus?
COPY (SELECT id_municipio_campus AS id_municipio,
        sum(TRY_CAST(quantidade_vagas_concorrencia AS DOUBLE)) AS sisu_vagas,
        count(DISTINCT id_ies) AS sisu_ies
      FROM br_mec_sisu.microdados WHERE ano >= 2019 GROUP BY 1)
  TO '__OUT__/v_sisu.csv' (HEADER);

COPY (SELECT id_municipio, count(DISTINCT id_ies) AS ies_n
      FROM br_inep_censo_educacao_superior.ies WHERE ano = 2022 GROUP BY 1)
  TO '__OUT__/v_ies.csv' (HEADER);

-- H33 · Farmácia Popular: a rede credenciada (não há volume dispensado no espelho)
COPY (SELECT substr(regexp_replace(CAST(codigo_cep_estabelecimento AS VARCHAR),'[^0-9]','','g'),1,8) AS cep,
        count(*) AS fp_estab
      FROM br_saude_farmaciapopular.estabelecimentos GROUP BY 1)
  TO '__OUT__/v_farmpop_cep.csv' (HEADER);

-- H36 · CNJ improbidade: a série mede alimentação do cadastro?
COPY (SELECT sigla_uf, count(*) AS cnj_condenacoes,
        count(DISTINCT id_pessoa) AS cnj_pessoas,
        count(DISTINCT comarca) AS cnj_comarcas
      FROM br_cnj_improbidade_administrativa.condenacao GROUP BY 1)
  TO '__OUT__/v_cnj_uf.csv' (HEADER);
