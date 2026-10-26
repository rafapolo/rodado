-- Lista Suja (br_mte_listasuja.empregadores_historico) com o município da ação fiscal.
-- Um caso = (cpf_cnpj, estabelecimento, ano_acao_fiscal), uma vez só: o histórico soma os
-- retratos de cada coleta (gotcha historico_sao_retratos). O município sai do texto
-- `estabelecimento`, nesta ordem:
--   texto      o nome de município da UF que termina mais à direita no texto (o mais longo no
--              empate). A UF é a sigla no fim do texto ("…/TO", "…-PI"); sem ela, sigla_uf
--   parecido   sem nome exato: o último trecho antes da UF contra os nomes da UF, Jaro-Winkler
--              >= 0,93 ("COROMADEL" -> Coromandel)
--   df         UF = DF: Brasília, o único município
--   cnpj       texto sem lugar (as "RESIDÊNCIA DE …"): o município do CNPJ em br_me_cnpj
-- Vale o texto quando ele e o CNPJ divergem: o texto é o local da fiscalização, o CNPJ é a sede.
CREATE TEMP MACRO norm(s) AS ' ' || regexp_replace(trim(regexp_replace(strip_accents(upper(s)), '[^A-Z]+', ' ', 'g')), ' +', ' ', 'g') || ' ';
CREATE TEMP TABLE ls AS
  SELECT DISTINCT ON (cpf_cnpj, estabelecimento, ano_acao_fiscal)
    cpf_cnpj, tipo_documento, cnpj, sigla_uf, estabelecimento, ano_acao_fiscal, trabalhadores_envolvidos, cnae, cnae_subclasse,
    data_coleta, norm(estabelecimento) txt,
    coalesce(nullif(regexp_extract(upper(strip_accents(estabelecimento)), '[/\-–, ]\s*([A-Z]{2})\s*\.?\s*$', 1), ''), sigla_uf) uf,
    norm(regexp_extract(upper(strip_accents(estabelecimento)), '([^,/\-–]+)[/\-–, ]\s*[A-Z]{2}\s*\.?\s*$', 1)) ultimo
  FROM br_mte_listasuja.empregadores_historico
  ORDER BY cpf_cnpj, estabelecimento, ano_acao_fiscal, data_coleta DESC;
CREATE TEMP TABLE dir AS SELECT id_municipio, sigla_uf, norm(nome) n FROM br_bd_diretorios_brasil.municipio;
CREATE TEMP TABLE exato AS
  SELECT DISTINCT ON (ls.cpf_cnpj, ls.estabelecimento, ls.ano_acao_fiscal) ls.cpf_cnpj, ls.estabelecimento, ls.ano_acao_fiscal, d.id_municipio
  FROM ls JOIN dir d ON d.sigla_uf = ls.uf AND strpos(ls.txt, d.n) > 0
  ORDER BY ls.cpf_cnpj, ls.estabelecimento, ls.ano_acao_fiscal,
    length(ls.txt) - strpos(reverse(ls.txt), reverse(d.n)) DESC, length(d.n) DESC;
CREATE TEMP TABLE parecido AS
  SELECT DISTINCT ON (ls.cpf_cnpj, ls.estabelecimento, ls.ano_acao_fiscal) ls.cpf_cnpj, ls.estabelecimento, ls.ano_acao_fiscal, d.id_municipio
  FROM ls JOIN dir d ON d.sigla_uf = ls.uf AND jaro_winkler_similarity(trim(ls.ultimo), trim(d.n)) >= 0.93
  WHERE trim(ls.ultimo) <> ''
  ORDER BY ls.cpf_cnpj, ls.estabelecimento, ls.ano_acao_fiscal, jaro_winkler_similarity(trim(ls.ultimo), trim(d.n)) DESC;
CREATE TEMP TABLE sede AS
  SELECT cnpj, any_value(id_municipio) id_municipio FROM br_me_cnpj.estabelecimentos
  WHERE cnpj IN (SELECT cnpj FROM ls WHERE cnpj IS NOT NULL) GROUP BY cnpj;
CREATE TEMP TABLE r AS
  SELECT ls.* EXCLUDE (txt, ultimo),
    coalesce(e.id_municipio, p.id_municipio, CASE WHEN ls.uf = 'DF' THEN '5300108' END, s.id_municipio) id_municipio,
    CASE WHEN e.id_municipio IS NOT NULL THEN 'texto' WHEN p.id_municipio IS NOT NULL THEN 'parecido'
         WHEN ls.uf = 'DF' THEN 'df' WHEN s.id_municipio IS NOT NULL THEN 'cnpj' END origem_municipio,
    s.id_municipio id_municipio_cnpj
  FROM ls LEFT JOIN exato e USING (cpf_cnpj, estabelecimento, ano_acao_fiscal)
  LEFT JOIN parecido p USING (cpf_cnpj, estabelecimento, ano_acao_fiscal)
  LEFT JOIN sede s ON s.cnpj = ls.cnpj;
