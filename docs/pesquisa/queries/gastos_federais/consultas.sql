-- Para onde vai o dinheiro da União: consultas que geram os CSVs desta pasta.
-- Rodar no beelink: ssh beelink '~/bin/duckdb -readonly -csv ~/rodado/basedosdados.duckdb' < trecho > arquivo.csv
-- (SET enable_progress_bar=false; antes de cada uma). Figuras: scripts/plot_gastos_federais.py.

-- execucao_2025.csv — 2025 por função, subfunção, ação e natureza da despesa.
-- Pago = pago no exercício + restos a pagar pagos no ano. 2025 vem da execução, não de
-- br_cgu_orcamento_publico, cuja carga de 2025 parou antes de dezembro (ver gotchas).
SELECT codigo_funcao, nome_funcao, codigo_subfucao, nome_subfuncao, codigo_acao, any_value(nome_acao) nome_acao,
       codigo_grupo_de_despesa grupo, codigo_modalidade_da_despesa modalidade, codigo_elemento_de_despesa elemento,
       any_value(nome_elemento_de_despesa) nome_elemento, sum(valor_pago_r + valor_restos_a_pagar_pagos_r) pago
FROM br_cgu_despesas_publicas.execucao WHERE ano_e_mes_do_lancamento LIKE '2025/%'
GROUP BY codigo_funcao, nome_funcao, codigo_subfucao, nome_subfuncao, codigo_acao, grupo, modalidade, elemento
HAVING abs(pago) > 0;

-- execucao_2023.csv — 2023; pago_exercicio é comparável à receita do mesmo ano.
SELECT codigo_funcao, nome_funcao, codigo_grupo_de_despesa grupo, codigo_modalidade_da_despesa modalidade,
       codigo_elemento_de_despesa elemento, nome_elemento_de_despesa nome_elemento,
       sum(valor_pago_r) pago_exercicio, sum(valor_pago_r + valor_restos_a_pagar_pagos_r) pago
FROM br_cgu_despesas_publicas.execucao WHERE ano_e_mes_do_lancamento LIKE '2023/%' GROUP BY ALL;

-- execucao_serie.csv — 2014-2025.
SELECT left(ano_e_mes_do_lancamento,4)::INT ano, codigo_funcao, codigo_grupo_de_despesa grupo,
       codigo_modalidade_da_despesa modalidade, codigo_elemento_de_despesa elemento,
       sum(valor_pago_r + valor_restos_a_pagar_pagos_r) pago
FROM br_cgu_despesas_publicas.execucao WHERE ano_e_mes_do_lancamento < '2026'
GROUP BY ALL HAVING abs(pago) > 0;

-- receitas_2023.csv (total) e receitas_2023_detalhe.csv (por detalhamento, linhas > R$ 100 mi).
SELECT categoria_economica, origem, especie, sum(valor_realizado) realizado
FROM br_cgu_receitas_publicas.receitas WHERE ano_exercicio = 2023 GROUP BY ALL;
SELECT categoria_economica, origem, especie, detalhamento, sum(valor_realizado) realizado
FROM br_cgu_receitas_publicas.receitas WHERE ano_exercicio = 2023 GROUP BY ALL HAVING abs(realizado) > 1e8;

-- transferencias_2025.csv
SELECT tipo_transferencia, tipo_favorecido, uf, acao, any_value(nome_acao) nome_acao,
       any_value(linguagem_cidada) linguagem_cidada, nome_funcao, count(DISTINCT mes) meses, sum(valor_transferido) valor
FROM br_cgu_transferencias.transferencias WHERE ano = 2025
GROUP BY tipo_transferencia, tipo_favorecido, uf, acao, nome_funcao;

-- emendas_2025.csv
SELECT tipo_de_emenda, nome_funcao, regiao, nome_uf, sum(valor_pago + valor_restos_a_pagar_pagos) pago, sum(valor_empenhado) empenhado
FROM br_cgu_emendas_parlamentares.emendas WHERE ano_emenda = 2025 GROUP BY ALL;

-- ipca.csv — índice médio anual, para levar a série a preços de 2025.
SELECT ano, avg(indice) indice FROM br_ibge_ipca.mes_brasil WHERE ano BETWEEN 2014 AND 2025 GROUP BY 1 ORDER BY 1;

-- populacao_uf.csv
SELECT ano, sigla_uf, populacao FROM br_ibge_populacao.uf WHERE ano = 2025;
