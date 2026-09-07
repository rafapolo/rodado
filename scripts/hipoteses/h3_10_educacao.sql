-- hipoteses3 · bloco 10 · INEP -- as 7 fontes de educacao fora do painel.
-- Todas filtram pelo ano mais recente da propria tabela: `ano` e coluna de
-- particao, entao o max() e barato e a extracao nao envelhece sozinha.
SET enable_progress_bar=false;
SET memory_limit='6GB';
SET threads=4;

-- INSE: nivel socioeconomico medio das escolas do municipio
COPY (
  SELECT id_municipio,
         avg(TRY_CAST(inse AS DOUBLE))                AS inse_medio,
         count(*)                                     AS inse_escolas,
         avg(TRY_CAST(percentual_nivel_1 AS DOUBLE))  AS inse_share_nivel1
  FROM br_inep_indicador_nivel_socioeconomico.escola
  WHERE ano = (SELECT max(ano) FROM br_inep_indicador_nivel_socioeconomico.escola)
  GROUP BY 1
) TO '__OUT__/h3_inep_inse.csv' (HEADER);

-- Indicadores educacionais: alunos por turma (atu) no fundamental e no medio
COPY (
  SELECT id_municipio,
         avg(TRY_CAST(atu_ef AS DOUBLE)) AS atu_ef,
         avg(TRY_CAST(atu_em AS DOUBLE)) AS atu_em,
         count(*)                        AS ind_escolas
  FROM br_inep_indicadores_educacionais.escola
  WHERE ano = (SELECT max(ano) FROM br_inep_indicadores_educacionais.escola)
  GROUP BY 1
) TO '__OUT__/h3_inep_indicadores.csv' (HEADER);

-- Sinopse: docentes por municipio, e a fatia deles que esta na zona rural
COPY (
  SELECT id_municipio,
         sum(TRY_CAST(quantidade_docente AS DOUBLE))                                      AS docentes,
         sum(TRY_CAST(quantidade_docente AS DOUBLE)) FILTER (WHERE localizacao ILIKE '%ural%') AS docentes_rural
  FROM br_inep_sinopse_estatistica_educacao_basica.docente_localizacao
  WHERE ano = (SELECT max(ano) FROM br_inep_sinopse_estatistica_educacao_basica.docente_localizacao)
  GROUP BY 1
) TO '__OUT__/h3_inep_docentes.csv' (HEADER);

-- Educacao especial: matriculas, e quanto delas e em classe comum (inclusao)
COPY (
  SELECT id_municipio,
         sum(TRY_CAST(quantidade_matricula AS DOUBLE))                                   AS esp_matriculas,
         -- o rotulo e "Classes Comuns", plural: '%comum%' nao casa
         sum(TRY_CAST(quantidade_matricula AS DOUBLE))
           FILTER (WHERE tipo_classe ILIKE '%comu%') AS esp_classe_comum
  FROM br_inep_educacao_especial.etapa_ensino
  WHERE ano = (SELECT max(ano) FROM br_inep_educacao_especial.etapa_ensino)
  GROUP BY 1
) TO '__OUT__/h3_inep_especial.csv' (HEADER);

-- Alfabetizacao (2o ano): proficiencia media e taxa de alfabetizados
COPY (
  SELECT id_municipio,
         avg(TRY_CAST(proficiencia AS DOUBLE))  AS alfab_proficiencia,
         avg(TRY_CAST(alfabetizado AS DOUBLE))  AS alfab_taxa,
         count(*)                               AS alfab_n
  FROM br_inep_avaliacao_alfabetizacao.alunos
  WHERE ano = (SELECT max(ano) FROM br_inep_avaliacao_alfabetizacao.alunos)
  GROUP BY 1
) TO '__OUT__/h3_inep_alfabetizacao.csv' (HEADER);

-- Censo Escolar (39M linhas, filtrado a 1 ano): matriculas e turmas
COPY (
  SELECT id_municipio,
         sum(TRY_CAST(quantidade_matriculas AS DOUBLE)) AS ce_matriculas,
         count(*)                                       AS ce_turmas,
         count(DISTINCT id_escola)                      AS ce_escolas
  FROM br_inep_censo_escolar.turma
  WHERE ano = (SELECT max(ano) FROM br_inep_censo_escolar.turma)
  GROUP BY 1
) TO '__OUT__/h3_censo_escolar.csv' (HEADER);

-- ENEM (108M linhas, filtrado a 1 ano) por municipio de PROVA.
--
-- NAO por residencia: `id_municipio_residencia` existe no schema e esta 100%
-- NULO em todos os anos do espelho (conferido de 2015 a 2023) -- agregar por
-- ela devolve UMA linha, tudo no grupo NULL. `id_municipio_prova` esta 100%
-- preenchida. O vies e conhecido e precisa acompanhar qualquer leitura: quem
-- mora em cidade pequena viaja para prestar prova no polo regional, entao o
-- polo aparece inflado e o entorno, vazio.
COPY (
  SELECT id_municipio_prova AS id_municipio,
         count(*)                                                            AS enem_inscritos,
         avg(TRY_CAST(nota_redacao AS DOUBLE))                               AS enem_redacao,
         avg(TRY_CAST(nota_matematica AS DOUBLE))                   AS enem_matematica,
         -- presenca_objetiva e indicador_treineiro mudam de tipo entre os anos
         -- (BOOLEAN num, VARCHAR noutro): compara-se sempre como texto.
         avg(CASE WHEN CAST(presenca_objetiva AS VARCHAR) IN ('1','Presente','true') THEN 1.0 ELSE 0.0 END) AS enem_presenca,
         avg(CASE WHEN CAST(indicador_treineiro AS VARCHAR) IN ('1','Sim','true') THEN 1.0 ELSE 0.0 END) AS enem_treineiro
  FROM br_inep_enem.microdados
  WHERE ano = (SELECT max(ano) FROM br_inep_enem.microdados)
  GROUP BY 1
) TO '__OUT__/h3_enem.csv' (HEADER);
