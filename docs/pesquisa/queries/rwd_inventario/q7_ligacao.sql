-- Como os sistemas se ligam sem ID de paciente: taxa de casamento das chaves compartilhadas, 2022.
--  CNES   = código do estabelecimento presente no cadastro CNES de 2022 (qualquer mês)
--  CID-10 = código (3 ou 4 caracteres) presente na tabela oficial CID-10 (categorias ou subcategorias)
--  municipio = código presente no diretório IBGE (7 dígitos ou 6 sem verificador)
WITH cnes AS (SELECT DISTINCT id_estabelecimento_cnes c FROM br_ms_cnes.estabelecimento WHERE ano = 2022),
cid AS (SELECT CAT c FROM br_datasus_cid10.codigos UNION SELECT SUBCAT FROM br_datasus_cid10.subcategorias),
mun AS (SELECT id_municipio c FROM br_bd_diretorios_brasil.municipio UNION SELECT id_municipio_6 FROM br_bd_diretorios_brasil.municipio),
sih AS (SELECT id_estabelecimento_cnes e, coalesce(cid_principal_subcategoria, cid_principal_categoria) k, id_municipio_paciente m
        FROM br_ms_sih.aihs_reduzidas WHERE ano = 2022),
-- SIM guarda o CNES como texto de float ('2000733.0'): tira o '.0' e repõe o zero à esquerda
sim AS (SELECT lpad(regexp_replace(codigo_estabelecimento, '\.0$', ''), 7, '0') e, causa_basica k, id_municipio_residencia m FROM br_ms_sim.microdados WHERE ano = 2022),
sinasc AS (SELECT codigo_estabelecimento e, NULL k, id_municipio_residencia m FROM br_ms_sinasc.microdados WHERE ano = 2022),
den AS (SELECT id_estabelecimento e, NULL k, id_municipio_residencia m FROM br_ms_sinan.microdados_dengue WHERE ano = 2022),
sis AS (SELECT cnes e, NULL k, id_municipio m FROM br_ms_sisvan.microdados WHERE ano = 2022 AND mes = 6),
sia AS (SELECT id_estabelecimento_cnes e, coalesce(cid_principal_subcategoria, cid_principal_categoria) k, id_paciente_proto m
        FROM br_ms_sia.producao_ambulatorial WHERE ano = 2022 AND mes = 6 AND instrumento_registro <> 'C'),
todos AS (
  SELECT 'SIH' fonte, * FROM sih UNION ALL SELECT 'SIA', * FROM sia UNION ALL SELECT 'SIM', * FROM sim
  UNION ALL SELECT 'SINASC', * FROM sinasc UNION ALL SELECT 'SINAN dengue', * FROM den UNION ALL SELECT 'SISVAN', * FROM sis)
SELECT fonte, count(*) n,
  avg((e IS NOT NULL AND e <> '')::INT) cnes_preenchido,
  avg(coalesce(e IN (SELECT c FROM cnes), false)::INT) cnes_casa,
  avg((k IS NOT NULL)::INT) cid_preenchido,
  avg(coalesce(k IN (SELECT c FROM cid), false)::INT) cid_casa,
  avg(coalesce(m IN (SELECT c FROM mun), false)::INT) municipio_casa
FROM todos GROUP BY 1 ORDER BY 1;
