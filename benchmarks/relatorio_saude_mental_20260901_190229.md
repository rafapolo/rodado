# Benchmark — relatorio_saude_mental

- Modelo: `gemma-4-26B-A4B-it-qat` (q4_0), 13,43 GiB, MoE 128 experts / ~4B ativos
- Threads: **8** (fixo — ver gemma_stats.md)
- Task: `tasks/relatorio_saude_mental.md` (456 palavras)
- Data: 2026-09-01 19:06

## Sintetico (llama-bench)

| teste | t/s |
|---|---|
| pp128 | 73.83 ± 0.04 |
| pp512 | 69.87 ± 5.75 |
| tg128 | 16.55 ± 0.04 |
| tg128 | 16.62 ± 0.05 |

## Execucao real da task

| batch | tempo total | prefill (t/s) | geracao (t/s) | palavras |
|---|---|---|---|---|
| 512 | 77 s | 59.0 | 12.1 | 330 |
| 128 | 76 s | 59.1 | 12.3 | 342 |

## Tempo de parede por etapa

| batch | llama-bench | task real |
|---|---|---|
| 512 | 69 s | 77 s |
| 128 | 45 s | 76 s |

Log completo: `benchmarks/relatorio_saude_mental_20260901_190229.log`
Respostas geradas: `benchmarks/relatorio_saude_mental_20260901_190229_resposta_pp*.txt`
