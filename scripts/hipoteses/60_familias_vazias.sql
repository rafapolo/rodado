-- H46-H62 · Blocos N-Q de tasks/hipoteses.md §5.5: as sete famílias com menos
-- combinações ocupadas (agropecuaria 10, saneamento_agua 10, fundiario 9,
-- natalidade 12, conectividade 14), todas com cobertura municipal quase total.
--
-- OUT dir próprio (~/rodado_hipoteses/familias) para não colidir com a sessão
-- paralela, que trabalha em ~/rodado_hipoteses/20260906_blocof/.
SET enable_progress_bar=false; SET memory_limit='6GB'; SET threads=4;
SET temp_directory='/home/polo/tmp_duck';

------------------------------------------------------------------ Bloco N
-- H46 · quebra de safra = área colhida ÷ área plantada (lavoura temporária)
COPY (SELECT id_municipio, ano,
        sum(TRY_CAST(area_plantada AS DOUBLE))  AS pam_plantada,
        sum(TRY_CAST(area_colhida AS DOUBLE))   AS pam_colhida,
        sum(TRY_CAST(valor_producao AS DOUBLE)) AS pam_valor
      FROM br_ibge_pam.lavoura_temporaria WHERE ano >= 2013 GROUP BY 1,2)
  TO '__O__/v_pam_ano.csv' (HEADER);

-- H47 · concentração da pauta agrícola (HHI sobre valor por produto)
COPY (WITH p AS (
        SELECT id_municipio, produto, sum(TRY_CAST(valor_producao AS DOUBLE)) v
        FROM (SELECT id_municipio, produto, valor_producao FROM br_ibge_pam.lavoura_temporaria WHERE ano BETWEEN 2018 AND 2022
              UNION ALL
              SELECT id_municipio, produto, valor_producao FROM br_ibge_pam.lavoura_permanente WHERE ano BETWEEN 2018 AND 2022)
        GROUP BY 1,2 HAVING sum(TRY_CAST(valor_producao AS DOUBLE)) > 0)
      SELECT id_municipio, sum(power(v/t,2)) AS pam_hhi, count(*) AS pam_produtos,
             max(v/t) AS pam_share_top, any_value(t) AS pam_valor_total
      FROM (SELECT *, sum(v) OVER (PARTITION BY id_municipio) t FROM p) GROUP BY 1)
  TO '__O__/v_pam_hhi.csv' (HEADER);

-- H48 · rendimento médio (kg/ha) já pronto na PAM, ponderado por área
COPY (SELECT id_municipio, ano,
        sum(TRY_CAST(rendimento_medio_producao AS DOUBLE)*TRY_CAST(area_colhida AS DOUBLE))
          / nullif(sum(TRY_CAST(area_colhida AS DOUBLE)),0) AS pam_rendimento
      FROM br_ibge_pam.lavoura_temporaria WHERE ano >= 2018 GROUP BY 1,2)
  TO '__O__/v_pam_rend.csv' (HEADER);

-- H49 · silvicultura e extração vegetal (PEVS)
COPY (SELECT id_municipio,
        sum(TRY_CAST(valor AS DOUBLE)) FILTER (WHERE src='silvi')   AS pevs_silvicultura,
        sum(TRY_CAST(valor AS DOUBLE)) FILTER (WHERE src='extracao') AS pevs_extracao
      FROM (SELECT id_municipio, valor, 'silvi' src FROM br_ibge_pevs.producao_silvicultura WHERE ano BETWEEN 2018 AND 2022
            UNION ALL
            SELECT id_municipio, valor, 'extracao' FROM br_ibge_pevs.producao_extracao_vegetal WHERE ano BETWEEN 2018 AND 2022)
      GROUP BY 1)
  TO '__O__/v_pevs.csv' (HEADER);

-- H50 · rebanho bovino (PPM)
COPY (SELECT id_municipio,
        sum(TRY_CAST(quantidade AS DOUBLE)) FILTER (WHERE tipo_rebanho ILIKE '%bovin%') AS ppm_bovinos,
        sum(TRY_CAST(quantidade AS DOUBLE)) AS ppm_rebanho_total
      FROM br_ibge_ppm.efetivo_rebanhos WHERE ano = 2022 GROUP BY 1)
  TO '__O__/v_ppm.csv' (HEADER);

------------------------------------------------------------------ Bloco O
-- H51 · Atlas Esgotos da ANA: o mesmo fato modelado por terceiro
COPY (SELECT id_municipio,
        TRY_CAST(indice_sem_atendimento_sem_coleta_sem_tratamento AS DOUBLE) AS atlas_sem_nada,
        TRY_CAST(indice_atendimento_solucao_individual AS DOUBLE)            AS atlas_individual,
        TRY_CAST(indice_atendimento_com_coleta_sem_tratamento AS DOUBLE)     AS atlas_coleta_sem_trat,
        TRY_CAST(indice_atendimento_com_coleta_com_tratamento AS DOUBLE)     AS atlas_coleta_com_trat,
        TRY_CAST(populacao_urbana_2013 AS DOUBLE)                            AS atlas_pop_urb
      FROM br_ana_atlas_esgotos.municipio)
  TO '__O__/v_atlas.csv' (HEADER);

-- H52 · natureza jurídica do prestador (quem preenche o SNIS)
COPY (SELECT id_municipio,
        any_value(natureza_juridica) AS snis_natureza,
        any_value(abrangencia)       AS snis_abrangencia,
        count(DISTINCT id_prestador) AS snis_prestadores
      FROM br_mdr_snis.prestador_agua_esgoto WHERE ano = 2021 GROUP BY 1)
  TO '__O__/v_snis_prest.csv' (HEADER);

-- H53 · internação por doença infecciosa (SIH, capítulo A/B do CID-10)
COPY (SELECT id_municipio_paciente AS mun6,
        count(*) AS sih_total,
        count(*) FILTER (WHERE cid_principal_subcategoria LIKE 'A%' OR cid_principal_subcategoria LIKE 'B%') AS sih_infecciosa
      FROM br_ms_sih.aihs_reduzidas WHERE ano = 2023 GROUP BY 1)
  TO '__O__/v_sih_infec.csv' (HEADER);

-- H54 · lançamento outorgado pela ANA (município em texto)
COPY (SELECT upper(strip_accents(ing_nm_municipio)) AS mun_nome, ing_sg_ufmunicipio AS uf,
        count(*) AS ana_lanc_n,
        sum(TRY_CAST(int_qt_vazaomedia AS DOUBLE)) AS ana_lanc_vazao
      FROM read_parquet('~/rodado/br_ana_outorgas/lancamentos/*.parquet', union_by_name=true)
      WHERE ing_nm_municipio IS NOT NULL GROUP BY 1,2)
  TO '__O__/v_ana_lanc.csv' (HEADER);

------------------------------------------------------------------ Bloco P
-- H55 · concentração de tomador do crédito rural (HHI por município).
--   O município do SICOR vem do id_car: UF(2)+IBGE(7)+hash(32), só de 2019.
COPY (WITH m AS (
        SELECT substr(id_car,3,7) AS id_municipio,
               coalesce(cpf, cnpj_basico) AS tomador,
               count(*) AS n
        FROM br_bcb_sicor.recurso_publico_propriedade
        WHERE ano_emissao >= 2019 AND id_car IS NOT NULL
          AND coalesce(cpf, cnpj_basico) IS NOT NULL
        GROUP BY 1,2)
      SELECT id_municipio, sum(power(n::DOUBLE/t,2)) AS sicor_hhi_tomador,
             count(*) AS sicor_tomadores, max(n::DOUBLE/t) AS sicor_share_top
      FROM (SELECT *, sum(n) OVER (PARTITION BY id_municipio) t FROM m)
      GROUP BY 1 HAVING count(*) >= 5)
  TO '__O__/v_sicor_hhi.csv' (HEADER);

-- H56 · embargo do IBAMA: quem é embargado (a área é 100% nula, só contagem)
COPY (SELECT TRY_CAST(cod_municipio AS BIGINT) AS cod_municipio,
        count(*) AS emb_termos,
        count(DISTINCT cpf_cnpj_embargado) AS emb_pessoas,
        count(*) FILTER (WHERE length(regexp_replace(CAST(cpf_cnpj_embargado AS VARCHAR),'[^0-9]','','g'))=14) AS emb_pj
      FROM br_ibama_embargos_novo.termo_embargo
      WHERE cod_municipio IS NOT NULL GROUP BY 1)
  TO '__O__/v_embargos.csv' (HEADER);

-- H58 · fogo de manejo × fogo climático: o INPE traz dias_sem_chuva na linha
COPY (SELECT id_municipio,
        count(*) AS fogo_n,
        count(*) FILTER (WHERE TRY_CAST(dias_sem_chuva AS DOUBLE) <= 3) AS fogo_com_chuva,
        median(TRY_CAST(dias_sem_chuva AS DOUBLE)) AS fogo_dias_sem_chuva_med
      FROM br_inpe_queimadas.microdados
      WHERE ano BETWEEN 2020 AND 2023 AND id_municipio IS NOT NULL GROUP BY 1)
  TO '__O__/v_fogo.csv' (HEADER);

------------------------------------------------------------------ Bloco Q
-- H59/H60 · SINASC: cesárea por hora, baixo peso, mãe adolescente.
--   ATENÇÃO: `hora_nascimento` é 100% NULA em 2022 (e 2023 é ano parcial:
--   986k contra ~2,6M). Usar 2021.
COPY (SELECT id_municipio_nascimento AS id_municipio,
        count(*) AS nasc_n,
        count(*) FILTER (WHERE TRY_CAST(tipo_parto AS INT) = 2) AS nasc_cesarea,
        count(*) FILTER (WHERE TRY_CAST(tipo_parto AS INT) = 2
                           AND TRY_CAST(substr(lpad(CAST(hora_nascimento AS VARCHAR),4,'0'),1,2) AS INT) BETWEEN 8 AND 17)
          AS nasc_cesarea_comercial,
        count(*) FILTER (WHERE TRY_CAST(substr(lpad(CAST(hora_nascimento AS VARCHAR),4,'0'),1,2) AS INT) BETWEEN 8 AND 17)
          AS nasc_comercial,
        count(*) FILTER (WHERE TRY_CAST(peso AS DOUBLE) < 2500) AS nasc_baixo_peso,
        count(*) FILTER (WHERE TRY_CAST(idade_mae AS INT) < 20)  AS nasc_mae_adolescente
      FROM br_ms_sinasc.microdados WHERE ano = 2021 GROUP BY 1)
  TO '__O__/v_sinasc.csv' (HEADER);

-- H62 · escola sem internet (SIMET) × IDEB municipal
COPY (SELECT id_municipio,
        count(*) AS simet_escolas,
        count(*) FILTER (WHERE indicador_internet) AS simet_com_internet,
        sum(TRY_CAST(quantidade_matricula AS DOUBLE)) AS simet_matriculas
      FROM br_simet_educacao_conectada.escola GROUP BY 1)
  TO '__O__/v_simet.csv' (HEADER);

COPY (SELECT id_municipio, anos_escolares,
        avg(TRY_CAST(ideb AS DOUBLE)) AS ideb
      FROM br_inep_ideb.municipio
      WHERE ano = (SELECT max(ano) FROM br_inep_ideb.municipio) AND rede = 'publica'
      GROUP BY 1,2)
  TO '__O__/v_ideb.csv' (HEADER);
