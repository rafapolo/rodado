-- hipoteses3 · bloco 20 · saude (as tabelas pequenas; SIA, ANS e SISVAN tem
-- arquivo proprio no fim da fila por causa do tamanho).
-- ATENCAO na analise: cobertura de atencao basica e de vacina ja existem no
-- painel vindas do IEPS. Estas sao SEGUNDA FONTE do mesmo conceito -- entram
-- como duplicata_conceitual, nao como perna nova de hipotese.
SET enable_progress_bar=false; SET memory_limit='6GB'; SET threads=4;

COPY (
  SELECT id_municipio,
         avg(TRY_CAST(proporcao_cobertura_estrategia_saude_familia AS DOUBLE)) AS ab_cob_esf,
         avg(TRY_CAST(proporcao_cobertura_total_atencao_basica AS DOUBLE))     AS ab_cob_total,
         avg(TRY_CAST(quantidade_equipes_saude_familia AS DOUBLE))             AS ab_equipes_esf,
         avg(TRY_CAST(carga_horaria_medica_atencao_basica_tradicional AS DOUBLE)) AS ab_ch_medica
  FROM br_ms_atencao_basica.municipio
  WHERE ano = (SELECT max(ano) FROM br_ms_atencao_basica.municipio)
  GROUP BY 1
) TO '__OUT__/h3_atencao_basica.csv' (HEADER);

COPY (
  SELECT id_municipio,
         avg(TRY_CAST(cobertura_total AS DOUBLE))         AS imu_cobertura_total,
         avg(TRY_CAST(cobertura_poliomielite AS DOUBLE))  AS imu_polio,
         -- cobertura_sarampo removida: 0 nao-nulos em 5.570 municipios no ano
         -- mais recente. A coluna existe e esta vazia.
         avg(TRY_CAST(cobertura_penta AS DOUBLE))         AS imu_penta
  FROM br_ms_imunizacoes.municipio
  WHERE ano = (SELECT max(ano) FROM br_ms_imunizacoes.municipio)
  GROUP BY 1
) TO '__OUT__/h3_imunizacoes.csv' (HEADER);

COPY (
  SELECT id_municipio, count(*) AS covid_estabelecimentos
  FROM br_ms_vacinacao_covid19.microdados_estabelecimento GROUP BY 1
) TO '__OUT__/h3_covid_estab.csv' (HEADER);
