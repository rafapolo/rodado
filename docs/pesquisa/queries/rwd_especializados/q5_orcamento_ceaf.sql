-- Referência externa: gasto federal realizado na ação 4705 (medicamentos do Componente Especializado).
-- 2025 fica de fora: a carga do orçamento parou antes de dezembro (ver gotcha do dataset).
SELECT ano_exercicio ano, round(sum(orcamento_realizado), 2) realizado
FROM br_cgu_orcamento_publico.orcamento
WHERE id_acao = '4705' AND ano_exercicio BETWEEN 2014 AND 2024
GROUP BY 1 ORDER BY 1;
