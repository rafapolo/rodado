-- SI-PNI: doses aplicadas (agregado histórico) e microdados 2020. Leitura remota (bucket público
-- healthbr-data, views no .duckdb), lenta: minutos.
SELECT 'SI-PNI · historical doses (aggregated)' fonte, try_cast(ANO AS INT) ano, count(*) linhas FROM br_ms_sipni_doses_historicas.doses_agregadas GROUP BY ALL
UNION ALL SELECT 'SI-PNI · vaccination microdata', ano::INT, count(*) FROM br_ms_sipni_microdados.vacinacao_2020 GROUP BY ALL
ORDER BY 1, 2;
