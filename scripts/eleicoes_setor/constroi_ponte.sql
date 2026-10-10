-- Ponte entre seção eleitoral (2022 e 2026) e setor censitário de 2022.
-- Rodar por scripts/eleicoes_setor/constroi_ponte.sh; método e números em
-- docs/pesquisa/eleicoes_setor/schema.md.
--   br_rodado_eleicoes.secao_setor  o setor que contém o local de votação da seção
--   br_rodado_eleicoes.setor_local  os locais da faixa de 100 m mais próxima de cada setor,
--                                   com peso 1/distância ao centroide (método Colmeia/DeltaFolha)
SET enable_progress_bar=false;
LOAD spatial;
.mode list
-- 1. seções e coordenadas do arquivo oficial do TSE (1º turno de cada ano)
CREATE TEMP TABLE mun AS SELECT DISTINCT ltrim(id_municipio_tse,'0') tse, id_municipio FROM br_tse_eleicoes.perfil_eleitorado_local_votacao WHERE id_municipio IS NOT NULL
-- códigos do TSE que o espelho do BD traz sem município do IBGE
-- 73709 = Boa Esperança do Norte (MT), instalado em 2025, desmembrado de Nova Ubiratã e Sorriso
UNION SELECT * FROM (VALUES ('73709', '5101837'));
CREATE TEMP TABLE bruto AS
SELECT AA_ELEICAO::INT ano, SG_UF sigla_uf, ltrim(CD_MUNICIPIO,'0') id_municipio_tse, ltrim(NR_ZONA,'0') zona, ltrim(NR_SECAO,'0') secao,
       NR_LOCAL_VOTACAO local_numero, NM_LOCAL_VOTACAO local_nome, DS_ENDERECO endereco, NM_BAIRRO bairro, NR_CEP cep,
       TRY_CAST(QT_ELEITOR_SECAO AS BIGINT) eleitores_secao,
       TRY_CAST(replace(NR_LATITUDE,',','.') AS DOUBLE) lat0, TRY_CAST(replace(NR_LONGITUDE,',','.') AS DOUBLE) lon0
FROM read_csv(['/home/polo/duckdb_tmp/tse_locais/2026/*.csv','/home/polo/duckdb_tmp/tse_locais/2022/*.csv'], delim=';', header=true, encoding='latin-1', all_varchar=true, union_by_name=true)
WHERE NR_TURNO = '1';
CREATE TEMP TABLE l AS
SELECT ano, sigla_uf, id_municipio_tse, zona, secao, any_value(local_numero) local_numero, any_value(local_nome) local_nome,
       any_value(endereco) endereco, any_value(bairro) bairro, any_value(cep) cep, max(eleitores_secao) eleitores_secao,
       avg(lat0) FILTER (lat0 BETWEEN -34 AND 6 AND lon0 BETWEEN -74.5 AND -28) lat,
       avg(lon0) FILTER (lat0 BETWEEN -34 AND 6 AND lon0 BETWEEN -74.5 AND -28) lon
FROM bruto GROUP BY ALL;
-- coordenadas de outros anos (espelho do BD: 2020 e 2024) para completar
CREATE TEMP TABLE outros AS
SELECT ano, sigla_uf, ltrim(id_municipio_tse,'0') id_municipio_tse, ltrim(zona,'0') zona, ltrim(secao,'0') secao, numero local_numero, latitude lat, longitude lon
FROM br_tse_eleicoes.perfil_eleitorado_local_votacao WHERE ano IN (2020, 2024) AND latitude BETWEEN -34 AND 6 AND longitude BETWEEN -74.5 AND -28
UNION ALL SELECT ano, sigla_uf, id_municipio_tse, zona, secao, local_numero, lat, lon FROM l WHERE lat IS NOT NULL;
CREATE TEMP TABLE secao_geo AS SELECT sigla_uf, id_municipio_tse, zona, secao, arg_max(lat, ano) lat, arg_max(lon, ano) lon, max(ano) ano_coord FROM outros GROUP BY ALL;
CREATE TEMP TABLE local_geo AS SELECT sigla_uf, id_municipio_tse, zona, local_numero, arg_max(lat, ano) lat, arg_max(lon, ano) lon, max(ano) ano_coord FROM outros GROUP BY ALL;
CREATE TEMP TABLE s AS
SELECT l.ano, l.sigla_uf, m.id_municipio, l.id_municipio_tse, l.zona, l.secao, l.local_numero, l.local_nome, l.endereco, l.bairro, l.cep, l.eleitores_secao,
       coalesce(l.lat, sg.lat, lg.lat) latitude, coalesce(l.lon, sg.lon, lg.lon) longitude,
       CASE WHEN l.lat IS NOT NULL THEN 'tse_' || l.ano WHEN sg.lat IS NOT NULL THEN 'mesma_secao_' || sg.ano_coord
            WHEN lg.lat IS NOT NULL THEN 'mesmo_local_' || lg.ano_coord ELSE 'sem_coordenada' END origem_coordenada
FROM l LEFT JOIN mun m ON m.tse = l.id_municipio_tse
       LEFT JOIN secao_geo sg USING (sigla_uf, id_municipio_tse, zona, secao)
       LEFT JOIN local_geo lg USING (sigla_uf, id_municipio_tse, zona, local_numero);
.print == origem da coordenada
SELECT ano, regexp_replace(origem_coordenada,'_[0-9]+$','') origem, count(*) secoes, sum(eleitores_secao) eleitores FROM s GROUP BY ALL ORDER BY 1,3 DESC;

-- 2. projeção local em metros por município: x = lon*cos(lat0)*111320, y = lat*110574
CREATE TEMP TABLE g0 AS SELECT id_municipio, id_setor_censitario, geometria FROM br_ibge_censo_2022.setor_censitario;
CREATE TEMP TABLE mlat AS SELECT id_municipio, cos(radians(avg(ST_Y(ST_Centroid(geometria))))) k FROM g0 GROUP BY 1;
CREATE TEMP TABLE g AS
SELECT g0.id_municipio, id_setor_censitario, k, geometria,
       ST_Affine(geometria, k*111320, 0, 0, 110574, 0, 0) gm
FROM g0 JOIN mlat USING (id_municipio);
ALTER TABLE g ADD COLUMN cx DOUBLE; ALTER TABLE g ADD COLUMN cy DOUBLE; ALTER TABLE g ADD COLUMN r DOUBLE;
UPDATE g SET cx = ST_X(ST_Centroid(gm)), cy = ST_Y(ST_Centroid(gm)),
             r = sqrt(pow(ST_XMax(gm)-ST_XMin(gm),2) + pow(ST_YMax(gm)-ST_YMin(gm),2));
-- id_municipio_malha: o município da seção como ele existe na malha de 2022. É o próprio
-- id_municipio, menos em município criado depois do Censo, que não tem setor com o seu código:
-- aí vale o município da malha que contém o ponto, procurado na mesma UF.
ALTER TABLE s ADD COLUMN id_municipio_malha VARCHAR;
UPDATE s SET id_municipio_malha = id_municipio WHERE id_municipio IN (SELECT id_municipio FROM mlat);
CREATE TEMP TABLE novo AS
SELECT s.id_municipio, s.latitude, s.longitude, min(g0.id_municipio) malha
FROM (SELECT DISTINCT id_municipio, latitude, longitude FROM s WHERE id_municipio_malha IS NULL AND id_municipio IS NOT NULL AND latitude IS NOT NULL) s
JOIN g0 ON substr(g0.id_municipio,1,2) = substr(s.id_municipio,1,2) AND ST_Contains(g0.geometria, ST_Point(s.longitude, s.latitude))
GROUP BY ALL;
UPDATE s SET id_municipio_malha = n.malha FROM novo n
WHERE s.id_municipio_malha IS NULL AND s.id_municipio = n.id_municipio AND s.latitude = n.latitude AND s.longitude = n.longitude;
SELECT 'municipio fora da malha', id_municipio, id_municipio_malha, count(*) secoes FROM s WHERE id_municipio IS DISTINCT FROM id_municipio_malha AND id_municipio IS NOT NULL GROUP BY ALL;
CREATE TEMP TABLE p AS
SELECT DISTINCT s.ano, s.id_municipio_malha id_municipio, s.latitude, s.longitude, s.longitude*k*111320 px, s.latitude*110574 py
FROM s JOIN mlat ON mlat.id_municipio = s.id_municipio_malha WHERE s.latitude IS NOT NULL;
SELECT 'pontos', ano, count(*) FROM p GROUP BY 2 ORDER BY 2;

-- 3. setor que contém o ponto (ponte direta seção -> setor)
CREATE TEMP TABLE dentro AS
SELECT p.ano, p.id_municipio, p.latitude, p.longitude, min(g.id_setor_censitario) id_setor_censitario
FROM p JOIN g ON g.id_municipio = p.id_municipio AND ST_Contains(g.gm, ST_Point(p.px, p.py)) GROUP BY ALL;
COPY (
  SELECT s.*, d.id_setor_censitario,
         CASE WHEN d.id_setor_censitario IS NOT NULL THEN 'ponto_no_setor' WHEN s.latitude IS NULL THEN 'sem_coordenada'
              WHEN s.id_municipio IS NULL THEN 'sem_municipio_ibge' ELSE 'fora_do_municipio' END metodo_setor
  FROM s LEFT JOIN dentro d ON d.ano = s.ano AND d.id_municipio = s.id_municipio_malha AND d.latitude = s.latitude AND d.longitude = s.longitude
  ORDER BY ano, sigla_uf, id_municipio_tse, zona, secao
) TO '/home/polo/rodado/br_rodado_eleicoes/secao_setor/dados.parquet' (FORMAT parquet, COMPRESSION zstd, ROW_GROUP_SIZE 122880);

-- 4. método Colmeia/DeltaFolha: para cada setor, os locais da faixa de 100 m mais próxima
--    candidatos pela distância ao centroide: dc <= min(dc) + diagonal do setor + 100
CREATE TEMP TABLE mindc AS
SELECT p.ano, g.id_setor_censitario, min(sqrt(pow(p.px-g.cx,2)+pow(p.py-g.cy,2))) mdc
FROM g JOIN p USING (id_municipio) GROUP BY ALL;
CREATE TEMP TABLE cand AS
SELECT p.ano, g.id_municipio, g.id_setor_censitario, p.latitude, p.longitude,
       sqrt(pow(p.px-g.cx,2)+pow(p.py-g.cy,2)) dc,
       ST_Distance(g.gm, ST_Point(p.px, p.py)) dp
FROM g JOIN p USING (id_municipio) JOIN mindc m ON m.ano = p.ano AND m.id_setor_censitario = g.id_setor_censitario
WHERE sqrt(pow(p.px-g.cx,2)+pow(p.py-g.cy,2)) <= m.mdc + g.r + 100;
SELECT 'candidatos', count(*) FROM cand;
COPY (
  SELECT ano, id_municipio, id_setor_censitario, latitude, longitude,
         round(dp, 1) distancia_poligono_m, (floor(dp/100)+1)::INT faixa_100m, round(dc, 1) distancia_centroide_m,
         1.0/greatest(dc, 1.0) peso
  FROM cand QUALIFY floor(dp/100) = min(floor(dp/100)) OVER (PARTITION BY ano, id_setor_censitario)
  ORDER BY ano, id_setor_censitario, dc
) TO '/home/polo/rodado/br_rodado_eleicoes/setor_local/dados.parquet' (FORMAT parquet, COMPRESSION zstd, ROW_GROUP_SIZE 122880);
.print == fim
