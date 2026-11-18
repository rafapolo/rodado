-- Referência externa: valor pago pela União na ação 4705 (medicamentos do Componente Especializado),
-- da execução da despesa do Portal da Transparência. Bate com o orçamento realizado em 2014–2024
-- (R$ 9,92 bi em 2024); a tabela de orçamento para antes de dezembro de 2025, a execução não.
SELECT left(ano_e_mes_do_lancamento::VARCHAR, 4)::INT ano, round(sum(valor_pago_r), 2) pago
FROM br_cgu_despesas_publicas.execucao
WHERE codigo_acao = '4705' AND left(ano_e_mes_do_lancamento::VARCHAR, 4)::INT BETWEEN 2014 AND 2025
GROUP BY 1 ORDER BY 1;
