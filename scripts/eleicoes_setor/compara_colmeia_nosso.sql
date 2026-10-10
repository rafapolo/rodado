SET enable_progress_bar=false;
.mode list
SELECT numero_candidato, any_value(sigla_partido), sum(votos) v FROM br_tse_eleicoes.resultados_candidato_secao WHERE ano=2026 AND turno=1 AND cargo='presidente' GROUP BY 1 ORDER BY 3 DESC LIMIT 4;
CREATE TEMP TABLE sec AS
SELECT b.id_municipio, b.latitude, b.longitude,
       sum(v.l) l, sum(v.f) f, sum(d.votos_nominais) validos, sum(d.aptos) aptos, sum(d.abstencoes) abst, sum(d.votos_brancos) brancos, sum(d.votos_nulos) nulos
FROM br_rodado_eleicoes.secao_setor b
JOIN (SELECT sigla_uf, ltrim(id_municipio_tse,'0') m, ltrim(zona,'0') z, ltrim(secao,'0') s, sum(votos) FILTER (numero_candidato='13') l, sum(votos) FILTER (numero_candidato='22') f
      FROM br_tse_eleicoes.resultados_candidato_secao WHERE ano=2026 AND turno=1 AND cargo='presidente' GROUP BY ALL) v
  ON v.sigla_uf=b.sigla_uf AND v.m=b.id_municipio_tse AND v.z=b.zona AND v.s=b.secao
JOIN (SELECT sigla_uf, ltrim(id_municipio_tse,'0') m, ltrim(zona,'0') z, ltrim(secao,'0') s, votos_nominais, aptos, abstencoes, votos_brancos, votos_nulos
      FROM br_tse_eleicoes.detalhes_votacao_secao WHERE ano=2026 AND turno=1 AND cargo='presidente') d
  ON d.sigla_uf=b.sigla_uf AND d.m=b.id_municipio_tse AND d.z=b.zona AND d.s=b.secao
WHERE b.ano=2026 AND b.latitude IS NOT NULL AND b.origem_coordenada='tse_2026'
GROUP BY ALL;
COPY (
 SELECT r.id_setor_censitario, count(*) n_locais, min(r.distancia_poligono_m) dist,
        string_agg(printf('%.5f,%.5f', r.latitude, r.longitude), ';' ORDER BY r.latitude, r.longitude) pontos,
        sum(coalesce(s.l,0)) l, sum(coalesce(s.f,0)) f, sum(s.validos) validos, sum(s.aptos) aptos,
        sum(r.peso*coalesce(s.l,0)) lw, sum(r.peso*coalesce(s.f,0)) fw, sum(r.peso*s.validos) vw,
        sum(r.peso*(s.abst+s.brancos+s.nulos)) abnw, sum(r.peso*s.aptos) aptw
 FROM br_rodado_eleicoes.setor_local r LEFT JOIN sec s ON s.id_municipio=r.id_municipio AND s.latitude=r.latitude AND s.longitude=r.longitude
 WHERE r.ano=2026 GROUP BY 1
) TO '/home/polo/duckdb_tmp/cmp_nosso_setor.csv.gz' (FORMAT csv, COMPRESSION gzip);
COPY (SELECT b.id_municipio, sum(v.l) l, sum(v.f) f, sum(d.votos_nominais) validos, sum(d.aptos) aptos, sum(d.abstencoes) abst, sum(d.votos_brancos+d.votos_nulos) bn, sum(d.comparecimento) comp
 FROM (SELECT DISTINCT sigla_uf, id_municipio, id_municipio_tse, zona, secao FROM br_rodado_eleicoes.secao_setor WHERE ano=2026) b
 JOIN (SELECT sigla_uf, ltrim(id_municipio_tse,'0') m, ltrim(zona,'0') z, ltrim(secao,'0') s, sum(votos) FILTER (numero_candidato='13') l, sum(votos) FILTER (numero_candidato='22') f FROM br_tse_eleicoes.resultados_candidato_secao WHERE ano=2026 AND turno=1 AND cargo='presidente' GROUP BY ALL) v ON v.sigla_uf=b.sigla_uf AND v.m=b.id_municipio_tse AND v.z=b.zona AND v.s=b.secao
 JOIN (SELECT sigla_uf, ltrim(id_municipio_tse,'0') m, ltrim(zona,'0') z, ltrim(secao,'0') s, votos_nominais, aptos, abstencoes, votos_brancos, votos_nulos, comparecimento FROM br_tse_eleicoes.detalhes_votacao_secao WHERE ano=2026 AND turno=1 AND cargo='presidente') d ON d.sigla_uf=b.sigla_uf AND d.m=b.id_municipio_tse AND d.z=b.zona AND d.s=b.secao
 WHERE b.id_municipio IS NOT NULL GROUP BY 1) TO '/home/polo/duckdb_tmp/cmp_nosso_mun.csv.gz' (FORMAT csv, COMPRESSION gzip);
