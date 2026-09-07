-- hipoteses3 · bloco 55 · vigilancia (SINAN) e infraestrutura.
-- Os tres SINAN novos usam o layout CRU do DATASUS: coluna `COMUNINF` com o
-- codigo do SUS de 6 digitos, e `NU_ANO` como texto -- o mesmo campo que no
-- SINAN violencia vem VAZIO em 2020 e faz um GROUP BY pular o ano inteiro em
-- silencio (ver reference_sinan_violencia_nu_ano_2020). Por isso agrega-se sem
-- filtro de ano e o ano fica como coluna, para a analise ver o buraco.
SET enable_progress_bar=false; SET memory_limit='6GB'; SET threads=4;

COPY (
  SELECT id_municipio_residencia AS id_municipio, ano, count(*) AS dengue_casos
  FROM br_ms_sinan.microdados_dengue GROUP BY 1, 2
) TO '__OUT__/h3_sinan_dengue.csv' (HEADER);

COPY (
  SELECT CAST(COMUNINF AS VARCHAR) AS m6, CAST(NU_ANO AS VARCHAR) AS ano, count(*) AS chik_casos
  FROM br_ms_sinan_chikungunya.microdados_chikungunya GROUP BY 1, 2
) TO '__OUT__/h3_sinan_chikungunya.csv' (HEADER);

COPY (
  SELECT CAST(COMUNINF AS VARCHAR) AS m6, CAST(NU_ANO AS VARCHAR) AS ano, count(*) AS zika_casos
  FROM br_ms_sinan_zika.microdados_zika GROUP BY 1, 2
) TO '__OUT__/h3_sinan_zika.csv' (HEADER);

COPY (
  SELECT CAST(COMUNINF AS VARCHAR) AS m6, CAST(NU_ANO AS VARCHAR) AS ano, count(*) AS esquisto_casos
  FROM br_ms_sinan_esquistossomose.microdados_esquistossomose GROUP BY 1, 2
) TO '__OUT__/h3_sinan_esquistossomose.csv' (HEADER);

-- Banda larga fixa: 57M linhas, particionada por ano. Acessos por tecnologia.
COPY (
  SELECT id_municipio,
         sum(TRY_CAST(acessos AS DOUBLE))                                     AS bl_acessos,
         sum(TRY_CAST(acessos AS DOUBLE)) -- fibra aparece como FTTH/FTTB/FTTx; a palavra "fibra" nao existe na coluna
         FILTER (WHERE tecnologia ILIKE 'FTT%') AS bl_fibra,
         count(DISTINCT cnpj)                                                 AS bl_empresas
  FROM br_anatel_banda_larga_fixa.microdados
  WHERE ano = (SELECT max(ano) FROM br_anatel_banda_larga_fixa.microdados)
  GROUP BY 1
) TO '__OUT__/h3_banda_larga.csv' (HEADER);

COPY (
  SELECT id_municipio,
         avg(TRY_CAST(indice_firjan_gestao_fiscal AS DOUBLE)) AS ifgf,
         avg(TRY_CAST(ranking_nacional AS DOUBLE))            AS ifgf_ranking
  FROM br_firjan_ifgf.ranking
  WHERE ano = (SELECT max(ano) FROM br_firjan_ifgf.ranking)
  GROUP BY 1
) TO '__OUT__/h3_ifgf.csv' (HEADER);
