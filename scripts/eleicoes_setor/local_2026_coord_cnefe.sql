-- Coordenada estimada pelo CNEFE (cadastro de endereços do Censo 2022) para os locais de votação
-- de 2026 que o TSE não georreferenciou — nem no arquivo de 2026 (br_rodado_eleicoes.secao_setor)
-- nem no mesmo local ou endereço em 2022/2024. ~760 dos 95.570 locais; o resto tem coordenada
-- oficial. Gravada à parte porque, ao vivo, a estimativa lê os 111 mi endereços do CNEFE três
-- vezes e estoura o tempo do db.rodado.xyz (2026-10-26). Os dados de origem não mudam (CNEFE 2022,
-- locais do 1º turno de 2026): rodar de novo só se o TSE republicar os locais.
--   ssh beelink '~/bin/duckdb -readonly ~/rodado/basedosdados.duckdb' < scripts/eleicoes_setor/local_2026_coord_cnefe.sql
-- Método e erro medido de cada origem_coord, na ordem em que se tenta:
--  'CNEFE estabelecimento': escola/igreja/etc. de mesmo nome no município (só nome único, ou candidatos
--     a ~1 km entre si, ou no mesmo CEP; rede municipal x estadual tem que bater) — 94% a menos de 300 m
--  'CNEFE centro do CEP': mediana dos endereços do CEP (CEP não genérico) — mediana de erro 170 m
--  'CNEFE centro do bairro/povoado': mediana dos endereços da localidade — mediana de erro 360 m
SET enable_progress_bar=false;
COPY (
WITH l26 AS (
  SELECT sigla_uf, id_municipio, id_municipio_tse, zona, numero,
         any_value(nome) AS nome, any_value(tipo) AS tipo, any_value(endereco) AS endereco,
         any_value(bairro) AS bairro, any_value(cep) AS cep,
         count(*) AS secoes, sum(eleitores_secao) AS eleitores
  FROM br_tse_eleicoes.perfil_eleitorado_local_votacao
  WHERE ano = 2026 AND turno = 1
  GROUP BY ALL
),
ant AS (
  SELECT ano, id_municipio_tse, zona, numero, nome, endereco, latitude, longitude
  FROM br_tse_eleicoes.perfil_eleitorado_local_votacao
  WHERE ano IN (2022, 2024) AND turno = 1
    AND latitude IS NOT NULL AND latitude NOT IN (-1, 0)
  QUALIFY row_number() OVER (PARTITION BY id_municipio_tse, zona, numero ORDER BY ano DESC) = 1
),
por_end AS (
  SELECT id_municipio_tse, endereco, arg_max(latitude, ano) AS latitude, arg_max(longitude, ano) AS longitude
  FROM ant GROUP BY ALL
),
oficial AS (
  -- um ponto por local; havendo seções de origens diferentes, vale a do próprio arquivo de 2026
  SELECT id_municipio_tse, zona, local_numero AS numero,
         arg_max(latitude,  (origem_coordenada = 'tse_2026')::INT) AS latitude,
         arg_max(longitude, (origem_coordenada = 'tse_2026')::INT) AS longitude,
         arg_max(origem_coordenada, (origem_coordenada = 'tse_2026')::INT) AS origem
  FROM br_rodado_eleicoes.secao_setor
  WHERE ano = 2026 AND latitude IS NOT NULL
  GROUP BY ALL
),
-- joins só por igualdade de chave: com OR no ON o DuckDB faz laço aninhado
casa AS (
  SELECT l.*, o.latitude AS o_lat, o.longitude AS o_lon, o.origem AS o_origem, a.ano AS a_ano,
         CASE WHEN a.nome = l.nome OR a.endereco = l.endereco THEN a.latitude END AS a_lat,
         CASE WHEN a.nome = l.nome OR a.endereco = l.endereco THEN a.longitude END AS a_lon
  FROM l26 l
  LEFT JOIN oficial o ON o.id_municipio_tse = l.id_municipio_tse AND o.zona = l.zona AND o.numero = l.numero
  LEFT JOIN ant a ON a.id_municipio_tse = l.id_municipio_tse AND a.zona = l.zona AND a.numero = l.numero
),
tse AS (
  SELECT l.* EXCLUDE (o_lat, o_lon, o_origem, a_ano, a_lat, a_lon),
         coalesce(l.o_lat, l.a_lat, e.latitude)  AS latitude,
         coalesce(l.o_lon, l.a_lon, e.longitude) AS longitude,
         CASE WHEN l.o_lat IS NOT NULL THEN
                CASE WHEN l.o_origem = 'tse_2026' THEN 'TSE 2026'
                     ELSE 'TSE ' || regexp_extract(l.o_origem, '[0-9]{4}') || ', mesma seção' END
              WHEN l.a_lat IS NOT NULL THEN 'TSE ' || l.a_ano
              WHEN e.latitude IS NOT NULL THEN 'TSE mesmo endereço' END AS origem_coord
  FROM casa l
  LEFT JOIN por_end e ON e.id_municipio_tse = l.id_municipio_tse AND e.endereco = l.endereco
),
falta AS (
  SELECT id_municipio, id_municipio_tse, zona, numero, nome, cep,
         array_to_string(list_filter(string_split(trim(regexp_replace(strip_accents(upper(coalesce(nome, ''))), '[^A-Z0-9]+', ' ', 'g')), ' '), lambda t: length(t) > 1 AND t NOT IN ('ESCOLA','ESC','EE','EM','EMEF','EMEI','EMEIEF','EEF','EEEF','EEEFM','EEFM','CEI','CMEI','COLEGIO','COL','MUNICIPAL','MUN','ESTADUAL','EST','ENSINO','FUNDAMENTAL','FUND','MEDIO','INFANTIL','EDUCACAO','EDUCACIONAL','EDUC','CENTRO','DE','DA','DO','DAS','DOS','PROF','PROFESSOR','PROFESSORA','PROFA','UNIDADE','ESCOLAR','PREDIO','INTEGRAL','TEMPO','CRECHE','INSTITUTO','GRUPO','REUNIDAS','REUNIDA','NUCLEO','FEDERAL','UE','ETI','CIVICO','MILITAR','MUNIC','ESTAD','ED','DR','DONA','DOM','SAO','SANTA','SANTO','EMR','EMEB','EEB','EB','CE','CIEP','UNID','ESCOLAS')), ' ') AS nl,
         CASE WHEN regexp_matches(strip_accents(upper(nome)), '\b(MUNICIPAL|MUN|EMEF|EMEI|EM|CMEI|EMEB)\b') THEN 'M' WHEN regexp_matches(strip_accents(upper(nome)), '\b(ESTADUAL|EST|EE|EEEF|EEEFM|EEFM|CE)\b') THEN 'E' END AS rede,
         trim(regexp_replace(regexp_replace(strip_accents(upper(coalesce(bairro, ''))), '[^A-Z0-9]+', ' ', 'g'), '^(POVOADO|POV|DISTRITO|DIST|VILA|LOCALIDADE|COMUNIDADE|SITIO|FAZENDA|ASSENTAMENTO) (DE |DO |DA |DOS |DAS )?', '')) AS lb,
         trim(regexp_replace(regexp_replace(strip_accents(upper(coalesce(regexp_replace(endereco, ' - ZONA (RURAL|URBANA)$', ''), ''))), '[^A-Z0-9]+', ' ', 'g'), '^(POVOADO|POV|DISTRITO|DIST|VILA|LOCALIDADE|COMUNIDADE|SITIO|FAZENDA|ASSENTAMENTO) (DE |DO |DA |DOS |DAS )?', '')) AS le
  FROM tse WHERE latitude IS NULL AND sigla_uf <> 'ZZ'
),
cnefe AS NOT MATERIALIZED (
  SELECT COD_MUNICIPIO AS id_municipio, CEP AS cep, COD_ESPECIE AS esp, DSC_ESTABELECIMENTO AS dsc,
         DSC_LOCALIDADE AS localidade, LATITUDE::DOUBLE AS lat, LONGITUDE::DOUBLE AS lon
  FROM br_ibge_cnefe.enderecos
  WHERE COD_MUNICIPIO IN (SELECT id_municipio FROM falta)
),
est AS (
  SELECT id_municipio, cep, esp, lat, lon,
         array_to_string(list_filter(string_split(trim(regexp_replace(strip_accents(upper(coalesce(dsc, ''))), '[^A-Z0-9]+', ' ', 'g')), ' '), lambda t: length(t) > 1 AND t NOT IN ('ESCOLA','ESC','EE','EM','EMEF','EMEI','EMEIEF','EEF','EEEF','EEEFM','EEFM','CEI','CMEI','COLEGIO','COL','MUNICIPAL','MUN','ESTADUAL','EST','ENSINO','FUNDAMENTAL','FUND','MEDIO','INFANTIL','EDUCACAO','EDUCACIONAL','EDUC','CENTRO','DE','DA','DO','DAS','DOS','PROF','PROFESSOR','PROFESSORA','PROFA','UNIDADE','ESCOLAR','PREDIO','INTEGRAL','TEMPO','CRECHE','INSTITUTO','GRUPO','REUNIDAS','REUNIDA','NUCLEO','FEDERAL','UE','ETI','CIVICO','MILITAR','MUNIC','ESTAD','ED','DR','DONA','DOM','SAO','SANTA','SANTO','EMR','EMEB','EEB','EB','CE','CIEP','UNID','ESCOLAS')), ' ') AS nc,
         CASE WHEN regexp_matches(strip_accents(upper(dsc)), '\b(MUNICIPAL|MUN|EMEF|EMEI|EM|CMEI|EMEB)\b') THEN 'M' WHEN regexp_matches(strip_accents(upper(dsc)), '\b(ESTADUAL|EST|EE|EEEF|EEEFM|EEFM|CE)\b') THEN 'E' END AS rede
  FROM cnefe WHERE dsc IS NOT NULL AND esp IN ('2', '4', '5', '6', '8')
),
por_nome AS (
  SELECT f.id_municipio_tse, f.zona, f.numero,
         arg_max(e.lat, (e.cep = f.cep)::INT * 4 + (e.esp = '4')::INT * 2 + jaro_winkler_similarity(f.nl, e.nc)) AS lat,
         arg_max(e.lon, (e.cep = f.cep)::INT * 4 + (e.esp = '4')::INT * 2 + jaro_winkler_similarity(f.nl, e.nc)) AS lon,
         count(*) AS n, bool_or(e.cep = f.cep) AS mesmo_cep,
         max(e.lat) - min(e.lat) + max(e.lon) - min(e.lon) AS espalhamento
  FROM falta f JOIN est e ON e.id_municipio = f.id_municipio
  WHERE length(f.nl) >= 4 AND length(e.nc) >= least(4, length(f.nl))  -- = 4, mas depende de f: não desce para a leitura
    AND jaro_winkler_similarity(f.nl, e.nc) >= 0.95
    AND coalesce(f.rede = e.rede, true)
  GROUP BY ALL
  HAVING n = 1 OR mesmo_cep OR espalhamento < 0.01
),
por_cep AS (
  SELECT cep, median(lat) AS lat, median(lon) AS lon
  FROM cnefe WHERE cep NOT LIKE '%000' AND cep IN (SELECT cep FROM falta)
  GROUP BY ALL
),
loc_alvo AS (
  -- o nome normalizado só dos valores distintos de localidade (milhares, não milhões de linhas),
  -- e só os que algum local procura (lb/le)
  SELECT id_municipio, localidade, l FROM (
    SELECT id_municipio, localidade, trim(regexp_replace(regexp_replace(strip_accents(upper(coalesce(localidade, ''))), '[^A-Z0-9]+', ' ', 'g'), '^(POVOADO|POV|DISTRITO|DIST|VILA|LOCALIDADE|COMUNIDADE|SITIO|FAZENDA|ASSENTAMENTO) (DE |DO |DA |DOS |DAS )?', '')) AS l
    FROM (SELECT DISTINCT id_municipio, localidade FROM cnefe WHERE localidade IS NOT NULL))
  -- o length >= 4 fica do lado dos locais (l = lb/le pelo IN): um filtro com regexp sobre a coluna do
  -- CNEFE o DuckDB empurra para a leitura, e ele rodava nas 111 mi linhas antes do filtro de município
  WHERE (id_municipio, l) IN (SELECT id_municipio, lb FROM falta WHERE length(lb) >= 4
                              UNION SELECT id_municipio, le FROM falta WHERE length(le) >= 4)
),
por_localidade AS (
  SELECT c.id_municipio, a.l, median(c.lat) AS lat, median(c.lon) AS lon
  FROM cnefe c JOIN loc_alvo a ON a.id_municipio = c.id_municipio AND a.localidade = c.localidade
  GROUP BY 1, 2
),
cnefe_coord AS (
  SELECT f.id_municipio_tse, f.zona, f.numero,
         coalesce(n.lat, c.lat, lb.lat, le.lat) AS latitude,
         coalesce(n.lon, c.lon, lb.lon, le.lon) AS longitude,
         CASE WHEN n.lat IS NOT NULL THEN 'CNEFE estabelecimento'
              WHEN c.lat IS NOT NULL THEN 'CNEFE centro do CEP'
              WHEN coalesce(lb.lat, le.lat) IS NOT NULL THEN 'CNEFE centro do bairro/povoado' END AS origem_coord
  FROM falta f
  LEFT JOIN por_nome n USING (id_municipio_tse, zona, numero)
  LEFT JOIN por_cep c ON c.cep = f.cep
  LEFT JOIN por_localidade lb ON lb.id_municipio = f.id_municipio AND lb.l = f.lb
  LEFT JOIN por_localidade le ON le.id_municipio = f.id_municipio AND le.l = f.le
)
SELECT c.id_municipio_tse, c.zona, c.numero,
       round(c.latitude, 6) AS latitude, round(c.longitude, 6) AS longitude, c.origem_coord
FROM cnefe_coord c
WHERE c.latitude IS NOT NULL
ORDER BY 1, 2, 3
) TO '/home/polo/rodado/br_rodado_eleicoes/local_2026_coord_cnefe/dados.parquet' (FORMAT parquet, COMPRESSION zstd);
