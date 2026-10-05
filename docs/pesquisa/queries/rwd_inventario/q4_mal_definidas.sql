-- Qualidade da causa de morte: fração de óbitos com causa básica mal definida (CID-10 cap. XVIII, R00-R99),
-- por UF de residência e ano, 1996-2022. A UF sai dos 2 primeiros dígitos do município: nos anos 1990 muitos
-- óbitos têm município ignorado ('1700000' = UF 17, município desconhecido) e sumiriam num join por município.
WITH uf AS (SELECT DISTINCT substr(id_municipio,1,2) id_uf, sigla_uf FROM br_bd_diretorios_brasil.municipio)
SELECT uf.sigla_uf, m.ano, count(*) obitos,
  count(*) FILTER (WHERE substr(m.causa_basica,1,1) = 'R') mal_definidas
FROM br_ms_sim.microdados m
JOIN uf ON uf.id_uf = substr(m.id_municipio_residencia,1,2)
GROUP BY ALL ORDER BY 1, 2;
