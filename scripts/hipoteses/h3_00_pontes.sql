-- hipoteses3 · bloco 00 · pontes de chave. Roda primeiro; os outros dependem.
-- Mesmas duas pontes de scripts/hipoteses/00_bridges.sql, repetidas aqui para
-- este lote ser autocontido: SIAFI->IBGE (Portal da Transparencia) e o codigo
-- do SUS de 6 digitos -> IBGE de 7 (SIH e SINAN).
SET enable_progress_bar=false;
CREATE OR REPLACE TEMP MACRO nrm(s) AS upper(strip_accents(trim(CAST(s AS VARCHAR))));

COPY (
  WITH siafi AS (
    SELECT DISTINCT uf, nome_municipio, codigo_municipio_siafi
    FROM br_cgu_novo_bolsa_familia.novo_bolsa_familia
  )
  SELECT s.codigo_municipio_siafi, d.id_municipio
  FROM siafi s JOIN br_bd_diretorios_brasil.municipio d
    ON nrm(s.nome_municipio)=nrm(d.nome) AND s.uf=d.sigla_uf
) TO '__OUT__/h3_ponte_siafi.csv' (HEADER);

COPY (
  SELECT CAST(id_municipio_6 AS VARCHAR) AS m6, id_municipio, sigla_uf, nome
  FROM br_bd_diretorios_brasil.municipio
) TO '__OUT__/h3_ponte_mun6.csv' (HEADER);
