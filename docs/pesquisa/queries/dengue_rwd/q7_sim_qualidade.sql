-- Qualidade do SIM: proporção de óbitos com causa mal definida (R00-R99), por UF, 2022,
-- e concordância SINAN x SIM nos óbitos por dengue por UF, 2014-2022.
SELECT sigla_uf, count(*) obitos,
  avg((substr(causa_basica,1,1) = 'R')::INT) pct_mal_definida,
  count(*) FILTER (WHERE substr(causa_basica,1,3) IN ('A90','A91')) obitos_dengue
FROM br_ms_sim.microdados WHERE ano = 2022 GROUP BY 1 ORDER BY 1;
