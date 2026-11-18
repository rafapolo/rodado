-- População por UF, 2024 (denominador das taxas por UF).
SELECT substr(id_municipio, 1, 2) id_uf, sum(populacao) populacao
FROM br_ibge_populacao.municipio WHERE ano = 2024 GROUP BY 1 ORDER BY 1;
