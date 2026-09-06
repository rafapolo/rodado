-- Variáveis já usadas em achados anteriores (B*, C*, D*), refeitas para o painel.
SET enable_progress_bar=false;
CREATE OR REPLACE TEMP MACRO nrm(s) AS upper(strip_accents(trim(CAST(s AS VARCHAR))));
CREATE OR REPLACE TEMP TABLE siafi AS SELECT * FROM read_csv('__OUT__/br_siafi.csv');

COPY (SELECT CAST(Municipio_Ibge AS BIGINT) AS id_municipio,
        sum(VL_PagadorPF)/1e6 AS pix_vl_pag_pf, sum(VL_PagadorPJ)/1e6 AS pix_vl_pag_pj,
        sum(VL_RecebedorPF)/1e6 AS pix_vl_rec_pf, sum(VL_RecebedorPJ)/1e6 AS pix_vl_rec_pj,
        sum(QT_PagadorPF) AS pix_qt_pag_pf, avg(QT_PES_PagadorPF) AS pix_pes_pag_pf
      FROM br_bcb_pix_municipio.transacoes WHERE AnoMes BETWEEN 202501 AND 202512 GROUP BY 1)
  TO '__OUT__/v_pix.csv' (HEADER);

COPY (SELECT CAST(codigomunicipio AS BIGINT) AS id_municipio,
        sum(TRY_CAST(replace(CAST(valorrecolhido AS VARCHAR),',','.') AS DOUBLE)) AS cfem_valor,
        count(DISTINCT cpf_cnpj) AS cfem_titulares, mode(substancia) AS cfem_substancia
      FROM br_anm.cfem_cfem_arrecadacao
      WHERE TRY_CAST(ano AS INT) BETWEEN 2022 AND 2025 GROUP BY 1)
  TO '__OUT__/v_cfem.csv' (HEADER);

COPY (SELECT CAST(CodMunicipioIbge AS BIGINT) AS id_municipio,
        count(*) AS gd_n, sum(MdaPotenciaInstaladaKW) AS gd_kw,
        count(*) FILTER (WHERE DscClasseConsumo ILIKE 'Rural%') AS gd_rural
      FROM read_parquet('~/rodado/br_aneel_dadosabertos/empreendimento_geracao_distribuida/*.parquet')
      GROUP BY 1)
  TO '__OUT__/v_gd.csv' (HEADER);

COPY (SELECT CAST(GEOCODIBGE AS BIGINT) AS id_municipio,
        sum(TRY_CAST(AREAMUNKM AS DOUBLE)) AS deter_km2, count(*) AS deter_n,
        sum(TRY_CAST(AREAMUNKM AS DOUBLE)) FILTER (WHERE CLASSNAME ILIKE '%MINER%') AS deter_km2_garimpo
      FROM br_inpe_deter.avisos WHERE VIEW_DATE >= '2023-01-01' GROUP BY 1)
  TO '__OUT__/v_deter.csv' (HEADER);

COPY (SELECT CAST(cod_municipio AS BIGINT) AS id_municipio, count(*) AS ibama_autos_n
      FROM br_ibama_autos.auto_infracao WHERE dat_hora_auto_infracao >= '2015-01-01' GROUP BY 1)
  TO '__OUT__/v_ibama_autos.csv' (HEADER);

-- qtd_area_embargada é 100% nula: só a contagem de termos é utilizável
COPY (SELECT CAST(cod_municipio AS BIGINT) AS id_municipio, count(*) AS emb_n
      FROM br_ibama_embargos_novo.termo_embargo GROUP BY 1)
  TO '__OUT__/v_embargos.csv' (HEADER);

COPY (SELECT id_municipio, count(*) AS sicar_imoveis, sum(area) AS sicar_area
      FROM br_sfb_sicar.area_imovel GROUP BY 1)
  TO '__OUT__/v_sicar.csv' (HEADER);

COPY (SELECT id_municipio, count(*) AS imoveis_cafir, sum(TRY_CAST(area AS DOUBLE)) AS area_cafir
      FROM br_rf_cafir.imoveis_rurais
      WHERE data_referencia=(SELECT max(data_referencia) FROM br_rf_cafir.imoveis_rurais) GROUP BY 1)
  TO '__OUT__/v_cafir.csv' (HEADER);

-- SICOR -> município pelo id_car (UF+IBGE7+hash). Só existe de 2019 em diante.
COPY (SELECT TRY_CAST(substr(p.id_car,3,7) AS BIGINT) AS id_municipio,
        sum(o.valor_parcela_credito) AS credito_rural,
        count(DISTINCT p.id_car) AS cars_financiados,
        sum(o.valor_parcela_credito) FILTER (WHERE p.ano_emissao=2019) AS credito_2019,
        sum(o.valor_parcela_credito) FILTER (WHERE p.ano_emissao=2024) AS credito_2024
      FROM br_bcb_sicor.recurso_publico_propriedade p
      JOIN br_bcb_sicor.operacao o
        ON o.id_referencia_bacen=p.id_referencia_bacen AND o.numero_ordem=p.numero_ordem
      WHERE p.ano_emissao BETWEEN 2020 AND 2024 AND p.id_car IS NOT NULL
        AND TRY_CAST(substr(p.id_car,3,7) AS BIGINT) BETWEEN 1100000 AND 5400000
      GROUP BY 1)
  TO '__OUT__/v_sicor.csv' (HEADER);

COPY (SELECT s.id_municipio, count(DISTINCT n.cpf_favorecido) AS nbf_familias,
        sum(TRY_CAST(replace(replace(n.valor_parcela,'.',''),',','.') AS DOUBLE)) AS nbf_valor
      FROM read_parquet('~/rodado/br_cgu_novo_bolsa_familia/novo_bolsa_familia/202607.parquet') n
      JOIN siafi s ON s.codigo_municipio_siafi = n.codigo_municipio_siafi GROUP BY 1)
  TO '__OUT__/v_nbf.csv' (HEADER);

COPY (SELECT unidadeOrgao.codigoIbge::BIGINT AS id_municipio, count(*) AS pncp_n,
        count(DISTINCT niFornecedor) AS pncp_fornecedores,
        median(TRY_CAST(valorGlobal AS DOUBLE)) AS pncp_valor_mediano
      FROM br_pncp.contratos GROUP BY 1)
  TO '__OUT__/v_pncp.csv' (HEADER);

COPY (SELECT id_municipio, arg_max(cob_ab,ano) AS cob_ab, arg_max(cob_esf,ano) AS cob_esf,
        arg_max(cob_priv,ano) AS cob_priv, arg_max(cob_vac_polio,ano) AS vac_polio
      FROM br_ieps_saude.municipio WHERE ano>=2019 GROUP BY 1)
  TO '__OUT__/v_ieps.csv' (HEADER);

COPY (SELECT id_municipio,
        any_value(ivs) FILTER (WHERE ano=2000) AS ivs_2000,
        any_value(ivs) FILTER (WHERE ano=2010) AS ivs_2010,
        any_value(idhm) FILTER (WHERE ano=2010) AS idhm_2010
      FROM br_ipea_avs.municipio
      WHERE raca_cor='total' AND sexo='total' AND localizacao='total' GROUP BY 1)
  TO '__OUT__/v_avs.csv' (HEADER);
