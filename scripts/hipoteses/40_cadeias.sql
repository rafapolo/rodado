-- Cadeias por CNPJ/CPF: perguntas que não são correlação municipal, e sim
-- contagem de interseção entre cadastros. Cada COPY já é a resposta.
SET enable_progress_bar=false;

CREATE OR REPLACE TEMP TABLE sanc AS
  SELECT DISTINCT regexp_replace(cpf_cnpj_sancionado,'[^0-9]','','g') AS doc
  FROM (SELECT cpf_cnpj_sancionado FROM br_cgu_sancoes.ceis
        UNION ALL SELECT cpf_cnpj_sancionado FROM br_cgu_sancoes.cnep)
  WHERE length(regexp_replace(cpf_cnpj_sancionado,'[^0-9]','','g'))=14;

-- H20 · Pagamento municipal (MIDES) a fornecedor sancionado — nunca medido.
--   D13 mostrou 2.755 sancionados CITADOS em diário; aqui é dinheiro PAGO.
COPY (SELECT p.id_municipio,
        count(*) FILTER (WHERE s.doc IS NOT NULL) AS pag_sancionado_n,
        sum(TRY_CAST(p.valor_final AS DOUBLE)) FILTER (WHERE s.doc IS NOT NULL) AS pag_sancionado_valor,
        count(*) AS pag_total_n,
        sum(TRY_CAST(p.valor_final AS DOUBLE)) AS pag_total_valor
      FROM world_wb_mides.pagamento p
      LEFT JOIN sanc s ON s.doc = regexp_replace(CAST(p.documento_credor AS VARCHAR),'[^0-9]','','g')
      WHERE p.ano>=2018 AND p.id_municipio IS NOT NULL GROUP BY 1)
  TO '__OUT__/v_mides_sancionado.csv' (HEADER);

-- H21 · Devedor da PGFN recebendo pagamento municipal (T37-2 mediu só o federal)
CREATE OR REPLACE TEMP TABLE pgfn AS
  SELECT regexp_replace(CAST(CPF_CNPJ AS VARCHAR),'[^0-9]','','g') AS doc,
         sum(TRY_CAST(replace(CAST(VALOR_CONSOLIDADO AS VARCHAR),',','.') AS DOUBLE)) AS divida
  FROM br_pgfn_dividaativa.divida WHERE TIPO_PESSOA ILIKE '%jur%' GROUP BY 1
  HAVING length(regexp_replace(CAST(CPF_CNPJ AS VARCHAR),'[^0-9]','','g'))=14;

COPY (SELECT p.id_municipio,
        count(DISTINCT g.doc) AS credores_devedores,
        sum(TRY_CAST(p.valor_final AS DOUBLE)) FILTER (WHERE g.doc IS NOT NULL) AS pago_a_devedor
      FROM world_wb_mides.pagamento p
      JOIN pgfn g ON g.doc = regexp_replace(CAST(p.documento_credor AS VARCHAR),'[^0-9]','','g')
      WHERE p.ano>=2018 AND p.id_municipio IS NOT NULL GROUP BY 1)
  TO '__OUT__/v_mides_devedor.csv' (HEADER);

-- H22 · CNPJ do fornecedor municipal está SEDIADO no município que paga?
--   Mede fuga de compra pública local — nunca testado.
COPY (SELECT p.id_municipio,
        count(*) AS n,
        count(*) FILTER (WHERE e.id_municipio = p.id_municipio) AS credor_local
      FROM (SELECT id_municipio, regexp_replace(CAST(documento_credor AS VARCHAR),'[^0-9]','','g') AS doc
            FROM world_wb_mides.pagamento WHERE ano>=2018 AND id_municipio IS NOT NULL) p
      JOIN (SELECT DISTINCT cnpj, id_municipio FROM br_me_cnpj.estabelecimentos
            WHERE ano=2025 AND mes=9) e ON e.cnpj = p.doc
      GROUP BY 1)
  TO '__OUT__/v_mides_local.csv' (HEADER);

-- H23 · Sancionado ainda empregando (T37-4 refeito com o painel)
COPY (SELECT r.id_municipio, count(DISTINCT r.cnpj_completo) AS sanc_empregadoras,
        sum(TRY_CAST(r.quantidade_vinculos_ativos AS INT)) AS sanc_vinculos
      FROM br_me_rais_identificada.estabelecimentos r
      JOIN sanc s ON s.doc = r.cnpj_completo WHERE r.ano=2021 GROUP BY 1)
  TO '__OUT__/v_sanc_emprego.csv' (HEADER);

-- H24 · Empresas sancionadas ativas por município (base de B13/T63-1)
COPY (SELECT e.id_municipio, count(*) AS sanc_n
      FROM sanc s
      JOIN (SELECT DISTINCT cnpj, id_municipio FROM br_me_cnpj.estabelecimentos
            WHERE ano=2025 AND mes=9) e ON e.cnpj = s.doc
      GROUP BY 1)
  TO '__OUT__/v_sancoes_mun.csv' (HEADER);
