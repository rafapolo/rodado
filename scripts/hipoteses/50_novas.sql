-- H41-H45 · trincas de 3+ famílias nunca cruzadas em H01-H19 (tasks/hipoteses.md,
-- Bloco I). Cada bloco extrai só o que os outros blocos ainda não leem.
SET enable_progress_bar=false;
CREATE OR REPLACE TEMP TABLE mun AS SELECT * FROM read_csv('__OUT__/br_municipio.csv');

-- H41 · comercio_exterior x transferencia_renda x trabalho_empresa
--   Choque 2019->2020 (queda de exportação pandêmica): é absorvido pelo PBF ou
--   pelo CAGED? HHI de SH4 em 2019 (pré-choque) mede concentração da pauta.
COPY (SELECT id_municipio,
        sum(valor_fob_dolar) FILTER (WHERE ano=2019) AS comex_fob_2019,
        sum(valor_fob_dolar) FILTER (WHERE ano=2020) AS comex_fob_2020
      FROM br_me_comex_stat.municipio_exportacao
      WHERE ano IN (2019,2020) AND id_municipio IS NOT NULL GROUP BY 1)
  TO '__OUT__/v_comex.csv' (HEADER);

COPY (
  WITH sh4 AS (
    SELECT id_municipio, id_sh4, sum(valor_fob_dolar) AS v
    FROM br_me_comex_stat.municipio_exportacao
    WHERE ano=2019 AND id_municipio IS NOT NULL GROUP BY 1,2
  ), tot AS (SELECT id_municipio, sum(v) AS total FROM sh4 GROUP BY 1)
  SELECT s.id_municipio, sum(pow(s.v/t.total,2)) AS comex_hhi_sh4_2019
  FROM sh4 s JOIN tot t ON t.id_municipio=s.id_municipio GROUP BY 1
) TO '__OUT__/v_comex_hhi.csv' (HEADER);

COPY (SELECT id_municipio,
        max(familias_beneficiarias_pbf) FILTER (WHERE ano=2020) AS pbf_2020
      FROM br_mc_indicadores.transferencias_municipio
      WHERE ano=2020 GROUP BY 1)
  TO '__OUT__/v_pbf_choque.csv' (HEADER);

-- caged_saldo_2019/2020 servem H41; 2017_2021/2022_2024 servem H45 (mesma tabela,
-- uma única varredura das duas janelas).
COPY (SELECT id_municipio,
        sum(saldo_movimentacao) FILTER (WHERE ano=2019) AS caged_saldo_2019,
        sum(saldo_movimentacao) FILTER (WHERE ano=2020) AS caged_saldo_2020,
        sum(saldo_movimentacao) FILTER (WHERE ano BETWEEN 2017 AND 2021) AS caged_saldo_2017_2021,
        sum(saldo_movimentacao) FILTER (WHERE ano BETWEEN 2022 AND 2024) AS caged_saldo_2022_2024
      FROM br_me_caged.microdados_movimentacao
      WHERE id_municipio IS NOT NULL AND ano BETWEEN 2017 AND 2024 GROUP BY 1)
  TO '__OUT__/v_caged_choque.csv' (HEADER);

-- H42 · compras_publicas x saude_producao x mortalidade
--   Terceirização (elemento_despesa 3.3.90.39 = "Outros Serviços de Terceiros -
--   PJ") na função 10 (Saúde) retém mais paciente e custa mais por AIH?
--   Mortalidade evitável usa obitos_infecciosos/infec_100k já no painel base
--   (10_base.sql) — não duplicado aqui.
COPY (SELECT id_municipio,
        sum(valor_final) FILTER (WHERE funcao='10') AS saude_empenho_total,
        sum(valor_final) FILTER (WHERE funcao='10' AND elemento_despesa LIKE '339039%') AS saude_empenho_terceirizado_pj
      FROM world_wb_mides.empenho
      WHERE ano>=2018 AND id_municipio IS NOT NULL GROUP BY 1)
  TO '__OUT__/v_mides_saude.csv' (HEADER);

-- SIH usa código SUS de 6 dígitos (ver 00_bridges.sql); m6 é a ponte.
COPY (
  SELECT m.id_municipio,
    count(*) AS sih_aih_n,
    count(*) FILTER (WHERE a.id_municipio_paciente = a.id_municipio_estabelecimento) AS sih_retencao_n,
    median(a.valor_aih) AS sih_valor_aih_mediano
  FROM br_ms_sih.aihs_reduzidas a
  JOIN mun m ON m.m6 = a.id_municipio_estabelecimento
  WHERE a.ano>=2022 GROUP BY 1
) TO '__OUT__/v_sih.csv' (HEADER);

-- H43 · politica x compras_publicas x sancao_integridade
--   Troca de partido na prefeitura (2016->2020) reduz a sobreposição de credores
--   MIDES em torno da posse (2019 vs 2021) mais que reeleição? Entrantes são mais
--   de fora e mais sancionados?
COPY (SELECT id_municipio,
        max(sigla_partido) FILTER (WHERE ano=2016) AS prefeito_partido_2016,
        max(sigla_partido) FILTER (WHERE ano=2020) AS prefeito_partido_2020,
        max(sigla_partido) FILTER (WHERE ano=2024) AS prefeito_partido_2024
      FROM br_tse_eleicoes.resultados_candidato_municipio
      WHERE cargo='prefeito' AND resultado='eleito' GROUP BY 1)
  TO '__OUT__/v_prefeito.csv' (HEADER);

CREATE OR REPLACE TEMP TABLE sanc AS
  SELECT DISTINCT regexp_replace(cpf_cnpj_sancionado,'[^0-9]','','g') AS doc
  FROM (SELECT cpf_cnpj_sancionado FROM br_cgu_sancoes.ceis
        UNION ALL SELECT cpf_cnpj_sancionado FROM br_cgu_sancoes.cnep)
  WHERE length(regexp_replace(cpf_cnpj_sancionado,'[^0-9]','','g'))=14;

CREATE OR REPLACE TEMP TABLE cnpj_local AS
  SELECT DISTINCT cnpj, id_municipio FROM br_me_cnpj.estabelecimentos WHERE ano=2025 AND mes=9;

-- Sem list_intersect: cada (municipio, credor) vira 1 linha com flag pre/pos,
-- e Jaccard/entrantes saem de count(*) FILTER — mesma tática de v_mides_credor.
COPY (
  WITH cred AS (
    SELECT DISTINCT id_municipio, ano,
           regexp_replace(CAST(documento_credor AS VARCHAR),'[^0-9]','','g') AS doc
    FROM world_wb_mides.pagamento
    WHERE ano IN (2019,2021) AND id_municipio IS NOT NULL AND documento_credor IS NOT NULL
  ),
  piv AS (
    SELECT id_municipio, doc, max(ano=2019) AS in_pre, max(ano=2021) AS in_pos
    FROM cred GROUP BY 1,2
  )
  SELECT p.id_municipio,
    count(*) FILTER (WHERE in_pre AND in_pos) AS credores_intersecao,
    count(*) FILTER (WHERE in_pre OR in_pos) AS credores_uniao,
    count(*) FILTER (WHERE in_pre) AS credores_pre_n,
    count(*) FILTER (WHERE in_pos) AS credores_pos_n,
    count(*) FILTER (WHERE in_pos AND NOT in_pre) AS entrantes_n,
    count(*) FILTER (WHERE in_pos AND NOT in_pre AND s.doc IS NOT NULL) AS entrantes_sancionados_n,
    count(*) FILTER (WHERE in_pos AND NOT in_pre AND c.id_municipio IS NOT NULL AND c.id_municipio <> p.id_municipio) AS entrantes_nao_local_n
  FROM piv p
  LEFT JOIN sanc s ON s.doc = p.doc
  LEFT JOIN cnpj_local c ON c.cnpj = p.doc
  GROUP BY 1
) TO '__OUT__/v_mides_jaccard.csv' (HEADER);

-- H44 · educacao x natalidade x trabalho_empresa
--   HHI ocupacional feminino (RAIS/CBO) prevê maternidade adolescente (SINASC)
--   melhor que IDEB?
COPY (SELECT id_municipio_residencia AS id_municipio,
        count(*) AS sinasc_nascidos,
        count(*) FILTER (WHERE idade_mae BETWEEN 10 AND 19) AS sinasc_mae_adolescente
      FROM br_ms_sinasc.microdados
      WHERE ano=2022 AND id_municipio_residencia IS NOT NULL AND idade_mae BETWEEN 10 AND 55
      GROUP BY 1)
  TO '__OUT__/v_sinasc.csv' (HEADER);

COPY (
  WITH f AS (
    SELECT id_municipio, cbo_2002, count(*) AS n
    FROM br_me_rais.microdados_vinculos
    WHERE ano=2022 AND vinculo_ativo_3112=1 AND sexo=2
    GROUP BY 1,2
  ), tot AS (SELECT id_municipio, sum(n) AS total FROM f GROUP BY 1)
  SELECT f.id_municipio, sum(pow(f.n*1.0/t.total,2)) AS rais_hhi_cbo_fem
  FROM f JOIN tot t ON t.id_municipio=f.id_municipio GROUP BY 1
) TO '__OUT__/v_rais_hhi_fem.csv' (HEADER);

COPY (SELECT id_municipio, ideb, taxa_aprovacao
      FROM br_inep_ideb.municipio
      WHERE rede='municipal' AND ensino='fundamental' AND anos_escolares='iniciais (1-5)'
        AND ano=(SELECT max(ano) FROM br_inep_ideb.municipio))
  TO '__OUT__/v_ideb.csv' (HEADER);

-- H45 · mineracao_energia x fiscal_municipal x trabalho_empresa
--   Queda de CFEM (2017-2021 -> 2022-2025) derruba CAGED (pouco emprego minerador)
--   ou só o CAUC (é choque de caixa)? cfem_valor 2022-2025 já está em v_cfem.csv
--   (20_conhecidos.sql); caged_saldo_2017_2021/2022_2024 em v_caged_choque.csv acima.
COPY (SELECT CAST(codigomunicipio AS BIGINT) AS id_municipio,
        sum(TRY_CAST(replace(CAST(valorrecolhido AS VARCHAR),',','.') AS DOUBLE)) AS cfem_valor_2017_2021
      FROM br_anm.cfem_cfem_arrecadacao_2017_2021 GROUP BY 1)
  TO '__OUT__/v_cfem_early.csv' (HEADER);

-- CAUC: "!" = pendente, data = regular até, "Desabilitado" = item não se aplica
-- (achado ao vivo em 2026-09-06 rodando contra o beelink). count(!) = pendências.
COPY (
  WITH long AS (
    UNPIVOT br_tesouro_cauc.situacao_municipios
    ON "1.1","1.2","1.3","1.4","1.5","2.1.1","2.1.2","3.1.1","3.1.2","3.2.1","3.2.2",
       "3.2.3","3.2.4","3.3","3.4.1","3.4.2","3.5","3.6","3.7","4.1","4.2",
       "5.1","5.2","5.3","5.4","5.5","5.6","5.7"
    INTO NAME item VALUE valor
  )
  SELECT CAST("Código IBGE" AS BIGINT) AS id_municipio,
         count(*) FILTER (WHERE valor='!') AS cauc_pendencias
  FROM long GROUP BY 1
) TO '__OUT__/v_cauc.csv' (HEADER);
