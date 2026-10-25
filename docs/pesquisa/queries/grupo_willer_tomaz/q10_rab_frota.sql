-- Aeronaves da Jet Line (10.332.184) e da Direção Táxi Aéreo (43.143.216) no Registro Aeronáutico Brasileiro,
-- com número de série e operador
SELECT MARCAS, NR_SERIE, DS_MODELO, NR_ANO_FABRICACAO,
       PROPRIETARIOS::JSON -> 0 ->> 'NOME' AS proprietario,
       OPERADORES AS operadores,
       DS_GRAVAME
FROM br_anac_dadosabertos.rab
WHERE PROPRIETARIOS LIKE '%10332184%' OR PROPRIETARIOS LIKE '%43143216%'
   OR OPERADORES LIKE '%10332184%' OR OPERADORES LIKE '%43143216%'
ORDER BY proprietario, MARCAS;
