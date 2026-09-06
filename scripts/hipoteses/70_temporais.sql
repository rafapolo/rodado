-- H05, H08, H14, H15 de tasks/hipoteses.md — as quatro que precisam de recorte
-- TEMPORAL (nao acumulado por municipio), que os blocos 00-50 nao extraem.
-- Rodar isolado: sed 's#__OUT__#<dir>#g' | duckdb -readonly ~/rodado/basedosdados.duckdb
-- Nao mexe em nenhum OUT dir de outra sessao.

-- ============================================================ H05 ========
-- CGU FEF: ano do sorteio por municipio (1o ciclo em que caiu) + pagamento
-- MIDES a sancionado por municipio x ANO (a bateria de 40_cadeias.sql so tem
-- o acumulado 2018+; aqui precisa de serie pra montar pre x pos sorteio).
-- CAUC ficou fora: br_tesouro_cauc.situacao_municipios e' fotografia unica
-- (data_pesquisa fixa), sem dimensao de tempo -- essa perna do H05 nao da.
COPY (SELECT id_municipio, min(ano_evento) AS ano_sorteio
      FROM br_cgu_fef.microdados
      WHERE id_municipio IS NOT NULL GROUP BY 1)
  TO '__OUT__/v_fef_evento.csv' (HEADER);

CREATE OR REPLACE TEMP TABLE sanc AS
  SELECT DISTINCT regexp_replace(cpf_cnpj_sancionado,'[^0-9]','','g') AS doc
  FROM (SELECT cpf_cnpj_sancionado FROM br_cgu_sancoes.ceis
        UNION ALL SELECT cpf_cnpj_sancionado FROM br_cgu_sancoes.cnep)
  WHERE length(regexp_replace(cpf_cnpj_sancionado,'[^0-9]','','g'))=14;

COPY (SELECT p.id_municipio, p.ano,
        sum(TRY_CAST(p.valor_final AS DOUBLE)) FILTER (WHERE s.doc IS NOT NULL) AS pag_sancionado_valor,
        sum(TRY_CAST(p.valor_final AS DOUBLE)) AS pag_total_valor
      FROM world_wb_mides.pagamento p
      LEFT JOIN sanc s ON s.doc = regexp_replace(CAST(p.documento_credor AS VARCHAR),'[^0-9]','','g')
      WHERE p.ano BETWEEN 2004 AND 2024 AND p.id_municipio IS NOT NULL
      GROUP BY 1,2)
  TO '__OUT__/v_mides_sancionado_ano.csv' (HEADER);

-- ============================================================ H08 ========
-- Desfecho POS-2020 para a dose acumulada de PBF (2004-2020, ja em
-- pbf_valor_acumulado do painel principal): mortalidade infantil 2021-2024,
-- municipio de RESIDENCIA (nao de ocorrencia). idade e' sujo (ver notas do
-- lookup: valores negativos e >100 no SIM) -- filtrar 0<=idade<=1 no Python,
-- nao aqui, pra nao perder a distribuicao bruta.
COPY (SELECT id_municipio_residencia AS id_municipio, ano, idade
      FROM br_ms_sim.microdados
      WHERE ano BETWEEN 2021 AND 2024 AND id_municipio_residencia IS NOT NULL)
  TO '__OUT__/v_sim_obitos_pos2020.csv' (HEADER);

COPY (SELECT id_municipio_residencia AS id_municipio, ano, count(*) AS nascidos
      FROM br_ms_sinasc.microdados
      WHERE ano BETWEEN 2021 AND 2024 AND id_municipio_residencia IS NOT NULL
      GROUP BY 1,2)
  TO '__OUT__/v_sinasc_nascidos_ano.csv' (HEADER);

-- ============================================================ H14 ========
-- SCR.data: inadimplencia da carteira de credito RURAL por UF x mes.
-- Numeros vem em VARCHAR com virgula decimal E ponto de milhar -- casts na
-- 91_parciais/40_cadeias ja usam esse padrao, replicado aqui.
COPY (SELECT uf, data_base,
        replace(replace(carteira_inadimplencia,'.',''),',','.') AS inadimplencia_raw,
        replace(replace(carteira_ativa,'.',''),',','.') AS ativa_raw
      FROM br_bcb_scrdata.dados
      WHERE modalidade = 'Financiamentos rurais  (ex-financiamentos rurais e agroindustriais)'
        AND uf IS NOT NULL)
  TO '__OUT__/v_scr_rural_uf.csv' (HEADER);
-- Garantia-Safra ja extraido por outra sessao em
-- tasks/hipoteses_resultado/inedito/v_garantia_safra.csv (long, municipio x
-- ano) -- nao reextrair, so ler e agregar por UF no Python.

-- ============================================================ H15 ========
-- RAIS: vinculos por municipio, 2019 e 2020 separados (10_base.sql so tem o
-- acumulado/ano mais recente).
COPY (SELECT id_municipio, ano, count(*) AS vinculos
      FROM br_me_rais.microdados_vinculos
      WHERE ano IN (2019,2020) AND id_municipio IS NOT NULL
      GROUP BY 1,2)
  TO '__OUT__/v_rais_vinculos_1920.csv' (HEADER);
