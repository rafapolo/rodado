-- Variáveis NOVAS: datasets sem nenhuma pergunta em perguntas.md, mais os
-- destravamentos de 2026-09-06 (MIDES pagamento municipal, CGU FEF por sorteio).
SET enable_progress_bar=false;
CREATE OR REPLACE TEMP MACRO nrm(s) AS upper(strip_accents(trim(CAST(s AS VARCHAR))));
CREATE OR REPLACE TEMP TABLE siafi AS SELECT * FROM read_csv('__OUT__/br_siafi.csv');
CREATE OR REPLACE TEMP TABLE mun AS SELECT * FROM read_csv('__OUT__/br_municipio.csv');

-- H01-H04 · MIDES: 392M pagamentos MUNICIPAIS com CNPJ do credor.
--   Concentração de fornecedor, e a ponte para sanção. Bloco mais caro do script.
COPY (SELECT id_municipio,
        count(*) AS mides_pagamentos,
        count(DISTINCT documento_credor) AS mides_credores,
        sum(TRY_CAST(valor_final AS DOUBLE)) AS mides_valor
      FROM world_wb_mides.pagamento
      WHERE ano>=2018 AND id_municipio IS NOT NULL GROUP BY 1)
  TO '__OUT__/v_mides.csv' (HEADER);

COPY (SELECT id_municipio, documento_credor, sum(TRY_CAST(valor_final AS DOUBLE)) AS v
      FROM world_wb_mides.pagamento
      WHERE ano>=2018 AND id_municipio IS NOT NULL AND documento_credor IS NOT NULL
      GROUP BY 1,2 HAVING sum(TRY_CAST(valor_final AS DOUBLE))>0)
  TO '__OUT__/v_mides_credor.csv' (HEADER);

-- H05-H07 · CGU FEF: fiscalização por SORTEIO (quase-aleatória).
--   O único desenho próximo de experimento no espelho.
COPY (SELECT id_municipio,
        count(*) AS fef_ordens,
        count(DISTINCT sorteio_ciclo_fef) AS fef_ciclos,
        sum(TRY_CAST(montante_fiscalizado AS DOUBLE)) AS fef_montante,
        count(*) FILTER (WHERE tipo_constatacao ILIKE '%grave%') AS fef_graves,
        count(DISTINCT tipo_constatacao) AS fef_tipos
      FROM br_cgu_fef.microdados GROUP BY 1)
  TO '__OUT__/v_fef.csv' (HEADER);

COPY (SELECT tipo_constatacao, funcao, count(*) n,
        sum(TRY_CAST(montante_fiscalizado AS DOUBLE)) montante
      FROM br_cgu_fef.microdados GROUP BY 1,2)
  TO '__OUT__/v_fef_tipos.csv' (HEADER);

-- H08-H09 · Bolsa Família 2004-2020: efeito de LONGO PRAZO (hoje só medido em corte)
COPY (SELECT id_municipio,
        max(familias_beneficiarias_pbf) FILTER (WHERE ano=2006) AS pbf_2006,
        max(familias_beneficiarias_pbf) FILTER (WHERE ano=2013) AS pbf_2013,
        max(familias_beneficiarias_pbf) FILTER (WHERE ano=2019) AS pbf_2019,
        sum(TRY_CAST(valor_pago_pbf AS DOUBLE)) AS pbf_valor_acumulado
      FROM br_mc_indicadores.transferencias_municipio GROUP BY 1)
  TO '__OUT__/v_pbf_serie.csv' (HEADER);

-- H10-H11 · Censo 2022 raça × instrução
COPY (SELECT id_municipio, cor_raca, categoria_principal, sum(valor) AS valor
      FROM br_ibge_censo2022_raca.instrucao GROUP BY 1,2,3)
  TO '__OUT__/v_censo_raca.csv' (HEADER);

-- H12-H13 · Consumidor.gov: 10,2M reclamações, tem Cidade em texto
COPY (SELECT d.id_municipio,
        count(*) AS reclamacoes,
        avg(TRY_CAST(c."Nota do Consumidor" AS DOUBLE)) AS nota_consumidor,
        avg(TRY_CAST(c."Tempo Resposta" AS DOUBLE)) AS tempo_resposta,
        count(*) FILTER (WHERE c."Respondida"='S') AS respondidas
      FROM br_mj_consumidorgovbr.reclamacoes c
      JOIN mun d ON nrm(c."Cidade")=nrm(d.nome) AND c."UF"=d.sigla_uf
      GROUP BY 1)
  TO '__OUT__/v_consumidor.csv' (HEADER);

-- H14 · Seguro-Defeso: onde estão os pescadores artesanais
COPY (SELECT s.id_municipio, count(DISTINCT d.cpf_favorecido) AS defeso_pescadores
      FROM read_parquet('~/rodado/br_cgu_seguro_defeso/seguro_defeso/*.parquet') d
      JOIN siafi s ON s.codigo_municipio_siafi=d.codigo_municipio_siafi GROUP BY 1)
  TO '__OUT__/v_defeso.csv' (HEADER);

-- H15 · Pé-de-Meia
COPY (SELECT s.id_municipio, count(DISTINCT p.cpf_beneficiario) AS pdm_alunos
      FROM read_parquet('~/rodado/br_cgu_pe_de_meia/pe_de_meia/*.parquet') p
      JOIN siafi s ON s.codigo_municipio_siafi=p.codigo_municipio_siafi GROUP BY 1)
  TO '__OUT__/v_pdm.csv' (HEADER);

-- H16 · Garantia-Safra: proxy municipal de quebra de safra COM série (o SEDEC não tem)
COPY (SELECT s.id_municipio,
        substr(g.mes_referencia,1,4) AS ano,
        count(DISTINCT g.nis_favorecido) AS gs_beneficiarios
      FROM read_parquet('~/rodado/br_cgu_garantia_safra/garantia_safra/*.parquet') g
      JOIN siafi s ON s.codigo_municipio_siafi=g.codigo_municipio_siafi GROUP BY 1,2)
  TO '__OUT__/v_garantia_safra.csv' (HEADER);

-- H17 · EBT: nota de transparência
COPY (SELECT id_municipio, avg(nota) AS ebt_nota FROM br_cgu_ebt.municipio GROUP BY 1)
  TO '__OUT__/v_ebt.csv' (HEADER);

-- H18 · Diversidade onomástica
COPY (SELECT id_municipio, count(DISTINCT nome) AS nomes_distintos,
        sum(quantidade_nascimentos_ate_2010) AS nascimentos,
        max(quantidade_nascimentos_ate_2010)*1.0/sum(quantidade_nascimentos_ate_2010) AS share_nome_top
      FROM br_ibge_nomes_brasil.quantidade_municipio_nome_2010 GROUP BY 1)
  TO '__OUT__/v_nomes.csv' (HEADER);

-- H19 · RAIS identificada: capital social e porte do estabelecimento empregador
COPY (SELECT id_municipio, count(*) AS rais_estab,
        median(TRY_CAST(capital_social AS DOUBLE)) AS capital_social_mediano,
        sum(TRY_CAST(quantidade_vinculos_ativos AS INT)) AS rais_vinculos
      FROM br_me_rais_identificada.estabelecimentos WHERE ano=2021 GROUP BY 1)
  TO '__OUT__/v_rais_ident.csv' (HEADER);
