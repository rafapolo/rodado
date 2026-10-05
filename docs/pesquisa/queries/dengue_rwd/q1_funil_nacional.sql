-- Funil nacional da dengue, 2014-2024: notificação (SINAN) -> internação (SIH) -> óbito (SINAN, SIH, SIM).
-- "Provável" = toda notificação menos descartado ('5'). A partir de 2022 o arquivo público
-- do SINAN já vem sem descartados, então o filtro iguala a série. trim() porque
-- classificacao_final ganhou espaço à direita em 2014 ('5 ', '8 ').
WITH sinan AS (
  SELECT ano,
    count(*) FILTER (WHERE coalesce(trim(classificacao_final),'') <> '5') provaveis,
    count(*) FILTER (WHERE trim(classificacao_final) IN ('10','11','12')) confirmados,
    count(*) FILTER (WHERE trim(classificacao_final) IN ('11','12')) alarme_ou_grave,
    count(*) FILTER (WHERE trim(classificacao_final) = '12') grave,
    count(*) FILTER (WHERE coalesce(trim(classificacao_final),'') <> '5' AND internacao = '1') sinan_internados,
    count(*) FILTER (WHERE coalesce(trim(classificacao_final),'') <> '5' AND evolucao_caso = '2') sinan_obitos,
    count(*) FILTER (WHERE coalesce(trim(classificacao_final),'') <> '5' AND evolucao_caso = '4') sinan_obitos_investigacao
  FROM br_ms_sinan.microdados_dengue
  WHERE ano BETWEEN 2014 AND 2024
  GROUP BY ano
),
-- SIH: ano de internação, não o ano de competência (2024 tem AIH processada em 2025).
sih AS (
  SELECT year(data_internacao) ano,
    count(*) sih_internacoes,
    count(*) FILTER (WHERE cid_principal_categoria = 'A91') sih_internacoes_a91,
    sum(indicador_obito) sih_obitos,
    sum(valor_aih) sih_valor_aih,
    sum(quantidade_dias_permanencia) sih_dias
  FROM br_ms_sih.aihs_reduzidas
  WHERE ano BETWEEN 2014 AND 2025
    AND cid_principal_categoria IN ('A90','A91')
    AND tipo_aih = '1'
    AND year(data_internacao) BETWEEN 2014 AND 2024
  GROUP BY 1
),
sim AS (
  SELECT ano, count(*) sim_obitos
  FROM br_ms_sim.microdados
  WHERE ano BETWEEN 2014 AND 2022
    AND substr(causa_basica,1,3) IN ('A90','A91','A97')
  GROUP BY ano
),
pop AS (
  SELECT ano, sum(populacao) populacao FROM br_ibge_populacao.municipio
  WHERE ano BETWEEN 2014 AND 2024 GROUP BY ano
)
SELECT s.*, h.sih_internacoes, h.sih_internacoes_a91, h.sih_obitos, round(h.sih_valor_aih) sih_valor_aih, h.sih_dias,
       m.sim_obitos, p.populacao
FROM sinan s
LEFT JOIN sih h USING (ano)
LEFT JOIN sim m USING (ano)
LEFT JOIN pop p USING (ano)
ORDER BY ano;
