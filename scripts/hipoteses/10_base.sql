-- Painel base: covariáveis de controle e desfechos já validados.
-- Reconstrói do zero para o script ser reprodutível sem estado anterior.
SET enable_progress_bar=false;

COPY (SELECT id_municipio, populacao FROM br_ibge_populacao.municipio WHERE ano=2022)
  TO '__OUT__/v_populacao.csv' (HEADER);

COPY (SELECT id_municipio, populacao AS pop2010 FROM br_ibge_populacao.municipio WHERE ano=2010)
  TO '__OUT__/v_populacao2010.csv' (HEADER);

COPY (SELECT id_municipio, pib, va_agropecuaria, va_industria, va_servicos, impostos_liquidos
      FROM br_ibge_pib.municipio WHERE ano=2021)
  TO '__OUT__/v_pib.csv' (HEADER);

COPY (SELECT id_municipio, sum(pib) AS pib_2010 FROM br_ibge_pib.municipio WHERE ano=2010 GROUP BY 1)
  TO '__OUT__/v_pib2010.csv' (HEADER);

-- RAIS 2022: vínculos, remuneração e recorte por sexo
COPY (SELECT id_municipio,
        count(*) AS vinculos,
        avg(valor_remuneracao_media) AS rem_media,
        avg(valor_remuneracao_media) FILTER (WHERE sexo=1) AS rem_masc,
        avg(valor_remuneracao_media) FILTER (WHERE sexo=2) AS rem_fem,
        count(*) FILTER (WHERE sexo=2) AS vinc_fem,
        count(*) FILTER (WHERE CAST(cnae_2 AS VARCHAR) LIKE '9491%') AS vinc_religioso
      FROM br_me_rais.microdados_vinculos
      WHERE ano=2022 AND vinculo_ativo_3112=1 GROUP BY 1)
  TO '__OUT__/v_rais.csv' (HEADER);

-- SIM: mortalidade por causa. RJ 2022 incompleto -> a análise usa 2020-2021 onde a série importa.
COPY (SELECT id_municipio_residencia AS id_municipio,
        count(*) AS obitos,
        count(*) FILTER (WHERE causa_basica BETWEEN 'X85' AND 'Y099') AS homicidios,
        count(*) FILTER (WHERE causa_basica BETWEEN 'X60' AND 'X849') AS suicidios,
        count(*) FILTER (WHERE causa_basica BETWEEN 'Y35' AND 'Y359') AS interv_policial,
        count(*) FILTER (WHERE causa_basica BETWEEN 'V01' AND 'V999') AS mortes_transito,
        count(*) FILTER (WHERE causa_basica BETWEEN 'A00' AND 'B999') AS obitos_infecciosos,
        count(*) FILTER (WHERE causa_basica BETWEEN 'J00' AND 'J999') AS obitos_respiratorios,
        count(*) FILTER (WHERE idade BETWEEN 15 AND 24 AND causa_basica BETWEEN 'X85' AND 'Y099') AS homic_juvenis,
        count(*) FILTER (WHERE sexo=2 AND idade BETWEEN 20 AND 59) AS ob_fem_precoce
      FROM br_ms_sim.microdados WHERE ano BETWEEN 2020 AND 2022 GROUP BY 1)
  TO '__OUT__/v_sim.csv' (HEADER);

COPY (SELECT id_municipio, ibc, cobertura_pop_4g5g, fibra, densidade_smp, hhi_smp
      FROM br_anatel_indice_brasileiro_conectividade.municipio
      WHERE ano=(SELECT max(ano) FROM br_anatel_indice_brasileiro_conectividade.municipio))
  TO '__OUT__/v_anatel.csv' (HEADER);

COPY (SELECT id_municipio, sum(desmatado) AS desmatado, sum(area_total) AS area_total,
        sum(vegetacao_natural) AS vegetacao_natural
      FROM br_inpe_prodes.municipio_bioma
      WHERE ano=(SELECT max(ano) FROM br_inpe_prodes.municipio_bioma) GROUP BY 1)
  TO '__OUT__/v_prodes.csv' (HEADER);

-- CNEFE: o território lido pelo endereço (111M linhas, ~10 min)
COPY (SELECT COD_MUNICIPIO::BIGINT AS id_municipio,
        count(*) AS cnefe_n,
        count(*) FILTER (WHERE COD_ESPECIE=1) AS cnefe_dom,
        count(*) FILTER (WHERE COD_ESPECIE=3) AS cnefe_agro,
        count(*) FILTER (WHERE COD_ESPECIE=4) AS cnefe_ensino,
        count(*) FILTER (WHERE COD_ESPECIE=5) AS cnefe_saude,
        count(*) FILTER (WHERE COD_ESPECIE=6) AS cnefe_outros,
        count(*) FILTER (WHERE COD_ESPECIE=7) AS cnefe_construcao,
        count(*) FILTER (WHERE COD_ESPECIE=8) AS cnefe_religioso,
        count(DISTINCT CEP) AS cnefe_ceps
      FROM br_ibge_cnefe.enderecos GROUP BY 1)
  TO '__OUT__/v_cnefe.csv' (HEADER);
