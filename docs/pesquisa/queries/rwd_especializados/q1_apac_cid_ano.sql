-- APAC (principal P e secundária S) de quimioterapia (SIGTAP 0304) e de medicamentos do
-- Componente Especializado (0604), por ano de processamento, CID-10 de 3 caracteres e UF do
-- estabelecimento. id_processamento_ambulatorial é o código SIGTAP de 10 dígitos.
-- O CID vem em cid_principal_categoria OU em cid_principal_subcategoria, nunca nos dois.
SELECT ano,
  substr(id_processamento_ambulatorial, 1, 4) grupo,
  instrumento_registro instrumento,
  coalesce(nullif(cid_principal_categoria, ''), substr(nullif(cid_principal_subcategoria, ''), 1, 3)) cid3,
  substr(id_municipio, 1, 2) id_uf,
  count(*) linhas,
  sum(quantidade_aprovada_procedimento) quantidade,
  round(sum(valor_aprovado_procedimento), 2) valor,
  count(DISTINCT mes) meses
FROM br_ms_sia.producao_ambulatorial
WHERE ano BETWEEN 2014 AND 2026 AND instrumento_registro IN ('P', 'S')
  AND substr(id_processamento_ambulatorial, 1, 4) IN ('0304', '0604')
GROUP BY ALL
HAVING count(*) >= 10;
