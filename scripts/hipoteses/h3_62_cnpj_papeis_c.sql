-- hipoteses3 · bloco 62 · MATRIZ DE PAPEIS POR CNPJ (c): setorial e cadastro.
-- br_ana_outorgas nao tem view no .duckdb -- so parquet em disco. Le-se por
-- read_parquet, como manda a regra do CLAUDE.md para esse caso. Idem SALIC.
-- O cadastro (CNPJ/RAIS) entra como ATRIBUTO, nao como papel: serve de
-- denominador honesto -- "16% das terceirizadas sao sancionadas" so significa
-- algo contra a taxa-base de sancao entre empresas ativas.
SET enable_progress_bar=false;
-- O .duckdbrc do beelink aponta temp_directory para /dev/shm (ramdisk com cota):
-- agrupar os 59M socios do snapshot estoura com "Disk quota exceeded". Este
-- bloco derrama em disco de verdade e recebe memoria suficiente para derramar
-- pouco -- limite baixo aumenta o spill, nao diminui.
SET temp_directory='/home/polo/tmp_duck';
SET memory_limit='16GB';
SET threads=8;

CREATE OR REPLACE TEMP MACRO d14(x) AS
  CASE WHEN length(regexp_replace(CAST(x AS VARCHAR), '[^0-9]', '', 'g')) = 14
       THEN regexp_replace(CAST(x AS VARCHAR), '[^0-9]', '', 'g') END;

COPY (
  WITH papeis AS (
    SELECT d14(cpf_cnpj_do_titular) AS cnpj, 'anm_titular_mineracao' AS papel,
           count(*) AS n, NULL::DOUBLE AS valor
    FROM br_anm.scm_portaria_de_lavra GROUP BY ALL
    UNION ALL SELECT d14(cpf_cnpj), 'cfem_arrecadador', count(*),
           sum(TRY_CAST(valorrecolhido AS DOUBLE))
    FROM br_anm.cfem_cfem_arrecadacao_2022_2026 GROUP BY ALL
    UNION ALL SELECT d14(NumCPFCNPJ), 'geracao_distribuida', count(*), NULL
    FROM br_aneel_dadosabertos.empreendimento_geracao_distribuida GROUP BY ALL
    UNION ALL SELECT d14(emp_nu_cpfcnpj), 'outorga_agua_captacao', count(*), NULL
    FROM read_parquet('/home/polo/rodado/br_ana_outorgas/captacoes/*.parquet') GROUP BY ALL
    UNION ALL SELECT d14(emp_nu_cpfcnpj), 'outorga_agua_lancamento', count(*), NULL
    FROM read_parquet('/home/polo/rodado/br_ana_outorgas/lancamentos/*.parquet') GROUP BY ALL
    UNION ALL SELECT d14(a.cnpj), 'ibama_ctf', count(*), NULL
    FROM br_ibama_ctf.app AS a GROUP BY ALL
    UNION ALL SELECT d14(cpf_cnpj), 'cnes_estabelecimento_saude', count(*), NULL
    FROM br_ms_cnes.estabelecimento GROUP BY ALL
    UNION ALL SELECT d14(cnpj_escola_privada), 'escola_privada', count(*), NULL
    FROM br_inep_censo_escolar.escola GROUP BY ALL
    UNION ALL SELECT d14(CNPJ_FUNDO), 'fundo_cvm', count(*), NULL
    FROM br_cvm_fundos.fundos GROUP BY ALL
    UNION ALL SELECT d14(pj.cnpj), 'administrador_carteira_cvm', count(*), NULL
    FROM br_cvm_administradores_carteira.pessoa_juridica AS pj GROUP BY ALL
    UNION ALL SELECT d14(cnpjcpf), 'salic_cultura', count(*), NULL
    FROM read_parquet('/home/polo/rodado/br_minc_salic/entidades/*.parquet') GROUP BY ALL
    UNION ALL SELECT d14(pr.cnpj), 'anvisa_cmed_farmaceutica', count(*), NULL
    FROM br_anvisa_cmed.precos AS pr GROUP BY ALL
    UNION ALL SELECT d14(cnpj_socia), 'holding_socia_pj', count(*), NULL
    FROM br_brasilio_holdings.holdings GROUP BY ALL
    UNION ALL SELECT d14(cnpj_revenda), 'revenda_combustivel', count(*), NULL
    FROM br_anp_precos_combustiveis.microdados GROUP BY ALL
  )
  SELECT cnpj, substr(cnpj, 1, 8) AS raiz, papel, n, valor
  FROM papeis WHERE cnpj IS NOT NULL
) TO '__OUT__/h3_cnpj_papeis_c.csv' (HEADER);

-- Atributos de cadastro: so para os CNPJ que aparecem em algum papel seria o
-- ideal, mas isso exigiria ler os blocos anteriores. Extrai-se o cadastro
-- inteiro em forma enxuta (5 colunas) e o cruzamento e feito na analise.
-- ATENCAO: br_me_cnpj guarda 43 SNAPSHOTS MENSAIS do cadastro inteiro
-- (2.540.728.606 linhas ao todo, ~59M por snapshot). Sem filtrar ano+mes esta
-- consulta despeja 2,4 BILHOES de linhas -- 120 GB de CSV, medido na marra.
COPY (
  SELECT cnpj,
         cnpj_basico                     AS raiz,
         id_municipio,
         cnae_fiscal_principal,
         situacao_cadastral,
         data_inicio_atividade
  FROM br_me_cnpj.estabelecimentos
  WHERE identificador_matriz_filial = '1'
    AND ano = (SELECT max(ano) FROM br_me_cnpj.estabelecimentos)
    AND mes = (SELECT max(mes) FROM br_me_cnpj.estabelecimentos
               WHERE ano = (SELECT max(ano) FROM br_me_cnpj.estabelecimentos))
) TO '__OUT__/h3_cnpj_cadastro.csv' (HEADER);

-- Quadro societario reduzido: quantos socios, quantos PF, quantos estrangeiros
COPY (
  SELECT cnpj_basico AS raiz,
         count(*)                                       AS socios_n,
         count(*) FILTER (WHERE tipo = '2')             AS socios_pf,
         count(*) FILTER (WHERE tipo = '3')             AS socios_estrangeiro,
         min(data_entrada_sociedade)                    AS socio_mais_antigo
  FROM br_me_cnpj.socios
  GROUP BY ALL
) TO '__OUT__/h3_cnpj_socios.csv' (HEADER);
