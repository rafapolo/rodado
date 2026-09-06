-- H30/H31 de tasks/hipoteses.md — Lei Rouanet (br_minc_salic), nunca antes
-- cruzada com sancao_integridade nem testada como funil regional.
-- Rodar isolado: sed 's#__OUT__#<dir>#g' | duckdb -readonly ~/rodado/basedosdados.duckdb

-- H30 · funil solicitado -> aprovado -> captado, por projeto (tem uf direto,
-- sem precisar de join com entidades).
COPY (SELECT id, entidade_id, uf, situacao, solicitado, aprovado, apoiado
      FROM read_parquet('~/rodado/br_minc_salic/projetos/*.parquet'))
  TO '__OUT__/v_rouanet_projetos.csv' (HEADER);

-- H31 · proponentes cruzados com CEIS/CNEP (sanc) e PGFN (pgfn) — mesmo
-- padrao de 40_cadeias.sql/50_novas.sql.
CREATE OR REPLACE TEMP TABLE sanc AS
  SELECT DISTINCT regexp_replace(cpf_cnpj_sancionado,'[^0-9]','','g') AS doc
  FROM (SELECT cpf_cnpj_sancionado FROM br_cgu_sancoes.ceis
        UNION ALL SELECT cpf_cnpj_sancionado FROM br_cgu_sancoes.cnep)
  WHERE length(regexp_replace(cpf_cnpj_sancionado,'[^0-9]','','g'))=14;

CREATE OR REPLACE TEMP TABLE pgfn AS
  SELECT regexp_replace(CAST(CPF_CNPJ AS VARCHAR),'[^0-9]','','g') AS doc,
         sum(TRY_CAST(replace(CAST(VALOR_CONSOLIDADO AS VARCHAR),',','.') AS DOUBLE)) AS divida
  FROM br_pgfn_dividaativa.divida WHERE TIPO_PESSOA ILIKE '%jur%'
  GROUP BY 1 HAVING length(regexp_replace(CAST(CPF_CNPJ AS VARCHAR),'[^0-9]','','g'))=14;

COPY (SELECT e.id AS entidade_id, e.proponente, e.patrocinador, e.uf,
        length(regexp_replace(e.cnpjcpf,'[^0-9]','','g')) AS doc_len,
        (s.doc IS NOT NULL) AS sancionado,
        (p.doc IS NOT NULL) AS devedor_pgfn,
        p.divida AS divida_pgfn
      FROM read_parquet('~/rodado/br_minc_salic/entidades/*.parquet') e
      LEFT JOIN sanc s ON s.doc = regexp_replace(e.cnpjcpf,'[^0-9]','','g')
      LEFT JOIN pgfn p ON p.doc = regexp_replace(e.cnpjcpf,'[^0-9]','','g'))
  TO '__OUT__/v_rouanet_integridade.csv' (HEADER);

-- Taxa-base correta (correcao da outra sessao: 7.893/6,68mi do D7/H29 e' o
-- universo ERRADO -- devedor da PGFN nao e' subconjunto do CEIS/CNEP, e o
-- 6,68mi e' a base da PGFN, nao o total de empresas do pais). O universo
-- certo e' CNPJ ATIVO em br_me_cnpj.estabelecimentos (mesmo recorte do
-- F4/F5/H29), sem controle de porte (opcao 'a' que a outra sessao sugeriu --
-- 'b', pareado por porte/setor, ficaria caro demais pra este item).
COPY (SELECT count(DISTINCT e.cnpj) AS total_ativos,
        count(DISTINCT e.cnpj) FILTER (WHERE s.doc IS NOT NULL) AS ativos_sancionados,
        count(DISTINCT e.cnpj) FILTER (WHERE p.doc IS NOT NULL) AS ativos_devedores_pgfn
      FROM br_me_cnpj.estabelecimentos e
      LEFT JOIN sanc s ON s.doc = e.cnpj
      LEFT JOIN pgfn p ON p.doc = e.cnpj
      WHERE e.ano=2025 AND e.mes=9)
  TO '__OUT__/v_cnpj_baseline.csv' (HEADER);
