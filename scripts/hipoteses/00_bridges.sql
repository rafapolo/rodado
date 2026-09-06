-- Pontes de chave. Rodar primeiro: os demais blocos dependem destes CSV.
-- Gotchas cobertos aqui (ver docs/achados_fortes.md, "Avisos de dado"):
--   * Portal da Transparência usa codigo_municipio_siafi, não id_municipio
--   * SIH e SINAN usam código de município do SUS (6 dígitos), não IBGE (7)
SET enable_progress_bar=false;
CREATE OR REPLACE TEMP MACRO nrm(s) AS upper(strip_accents(trim(CAST(s AS VARCHAR))));

-- SIAFI -> IBGE  (recupera 5.556 dos 5.571)
COPY (
  WITH siafi AS (
    SELECT DISTINCT uf, nome_municipio, codigo_municipio_siafi
    FROM br_cgu_novo_bolsa_familia.novo_bolsa_familia
  )
  SELECT s.codigo_municipio_siafi, d.id_municipio
  FROM siafi s
  JOIN br_bd_diretorios_brasil.municipio d
    ON nrm(s.nome_municipio)=nrm(d.nome) AND s.uf=d.sigla_uf
) TO '__OUT__/br_siafi.csv' (HEADER);

-- IBGE 6 dígitos (SUS) -> IBGE 7 dígitos
COPY (
  SELECT CAST(id_municipio_6 AS VARCHAR) AS m6, id_municipio, sigla_uf, nome,
         nome_regiao_imediata, nome_mesorregiao, capital_uf, amazonia_legal
  FROM br_bd_diretorios_brasil.municipio
) TO '__OUT__/br_municipio.csv' (HEADER);
