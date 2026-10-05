-- Exemplo de integração: mortalidade infantil = óbitos < 1 ano (SIM) / nascidos vivos (SINASC),
-- por UF de residência e ano, 1996-2022. Duas bases sem ID comum, ligadas por UF x ano.
-- idade do SIM vem em anos com fração; há valores negativos e > 120, descartados.
WITH uf AS (SELECT DISTINCT substr(id_municipio,1,2) id_uf, sigla_uf FROM br_bd_diretorios_brasil.municipio),
ob AS (
  SELECT uf.sigla_uf, ano, count(*) obitos_infantis,
    count(*) FILTER (WHERE idade * 365.25 < 28) obitos_neonatais
  FROM br_ms_sim.microdados m JOIN uf ON uf.id_uf = substr(m.id_municipio_residencia,1,2)
  WHERE idade >= 0 AND idade < 1 GROUP BY ALL
),
nv AS (
  SELECT uf.sigla_uf, ano, count(*) nascidos_vivos
  FROM br_ms_sinasc.microdados s JOIN uf ON uf.id_uf = substr(s.id_municipio_residencia,1,2)
  WHERE ano BETWEEN 1996 AND 2022 GROUP BY ALL
)
SELECT * FROM nv LEFT JOIN ob USING (sigla_uf, ano) ORDER BY ano, sigla_uf;
