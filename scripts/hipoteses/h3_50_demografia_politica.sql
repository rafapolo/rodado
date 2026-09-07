-- hipoteses3 · bloco 50 · demografia, religiao e POLITICA.
-- A filiacao partidaria e a unica extracao deste lote que abre uma FAMILIA
-- INTEIRA: `politica` nao tem nenhuma coluna no painel atual, e sozinha ela
-- adiciona C(22,3)-C(21,3) = 210 trincas novas.
SET enable_progress_bar=false; SET memory_limit='6GB'; SET threads=4;

COPY (
  SELECT id_municipio,
         sum(TRY_CAST(populacao AS DOUBLE))                                      AS msp_populacao,
         sum(TRY_CAST(populacao AS DOUBLE)) -- os rotulos usam hifen ('60-64 anos', '80-mais'), nao ' a '
         FILTER (WHERE grupo_idade IN ('60-64 anos','65-69 anos','70-74 anos',
                                       '75-79 anos','80-mais')) AS msp_pop_60mais,
         sum(TRY_CAST(populacao AS DOUBLE)) FILTER (WHERE sexo = 'feminino')      AS msp_pop_fem
  FROM br_ms_populacao.municipio
  WHERE ano = (SELECT max(ano) FROM br_ms_populacao.municipio)
  GROUP BY 1
) TO '__OUT__/h3_ms_populacao.csv' (HEADER);

-- Censo 2022 religiao: formato longo (variavel/valor). Emite por religiao e a
-- analise calcula share -- fazer o pivo aqui exigiria adivinhar os rotulos.
COPY (
  SELECT id_municipio, religiao, sum(TRY_CAST(valor AS DOUBLE)) AS valor
  FROM br_ibge_censo2022_religiao.mulheres_fecundidade_completa
  GROUP BY 1, 2
) TO '__OUT__/h3_censo_religiao.csv' (HEADER);

COPY (
  SELECT id_municipio,
         avg(TRY_CAST(taxa_liquida_matricula_pre_escola AS DOUBLE)) AS abrinq_pre_escola_liquida,
         avg(TRY_CAST(taxa_bruta_matricula_pre_escola AS DOUBLE))   AS abrinq_pre_escola_bruta
  FROM br_abrinq_oca.municipio_primeira_infancia
  WHERE ano = (SELECT max(ano) FROM br_abrinq_oca.municipio_primeira_infancia)
  GROUP BY 1
) TO '__OUT__/h3_abrinq.csv' (HEADER);

-- FILIACAO PARTIDARIA -- familia `politica`, hoje ausente do painel.
-- Filiado cancelado/desfiliado nao conta: a pergunta e sobre filiacao viva.
COPY (
  WITH viv AS (
    SELECT id_municipio, sigla_partido
    FROM br_tse_filiacao_partidaria.microdados_antigos
    WHERE data_cancelamento IS NULL AND data_desfiliacao IS NULL
  ), por_part AS (
    SELECT id_municipio, sigla_partido, count(*) AS n FROM viv GROUP BY 1, 2
  ), com_total AS (
    -- a janela precisa sair ANTES do agregado: window dentro de sum() nao liga
    SELECT id_municipio, n, sum(n) OVER (PARTITION BY id_municipio) AS tot
    FROM por_part
  )
  SELECT id_municipio,
         max(tot)                              AS fil_total,
         count(*)                              AS fil_partidos,
         max(n) / NULLIF(max(tot), 0)          AS fil_share_maior,
         sum(pow(n / NULLIF(tot, 0), 2))       AS fil_hhi
  FROM com_total GROUP BY 1
) TO '__OUT__/h3_filiacao.csv' (HEADER);
