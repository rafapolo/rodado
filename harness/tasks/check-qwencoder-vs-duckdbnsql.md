# Qwen3-Coder ou DuckDB-NSQL trocaria o Gemma 4 no harness?

> Aberto em 2026-09-02, a pedido. **Nada abaixo foi rodado no beelink** — os
> números do Gemma são medidos ([`harness_gemma_dsh.md`](harness_gemma_dsh.md));
> os dos candidatos são benchmark publicado (BIRD/Spider/BFCL), não o harness.
> 🔵 plano de experimento, bloqueado pelo item 2 de [`backlog.md`](backlog.md).

## Por que perguntar

O gargalo do harness não é velocidade — é **acerto de SQL**. O Gemma erra
codificação de domínio em silêncio: `causa_basica BETWEEN 'X60' AND 'X84'` deu
**726** contra **789** reais, 8% a menos com número plausível (medição 6 de
`harness_gemma_dsh.md`; virou regra em [`regras.md`](regras.md), camada 6 do
portão). Isso é exatamente o que os modelos de text-to-SQL prometem melhorar.

## Os candidatos

| Modelo | Params (total/ativos) | Especialidade | Tool-calling |
|---|---|---|---|
| **Gemma 4 26B-A4B** (atual) | 26B / ~4B, MoE 128 experts | generalista | sim, via grammar do llama.cpp (template não tem `tools` nativo) |
| **Qwen3-Coder-30B-A3B** | 30,5B / 3,3B, MoE (8 de 128 ativos) | código/SQL + agente | **nativo**, treinado pra tool-use |
| **DuckDB-NSQL-7B** | 7B densa (Llama-2 + fine-tune) | só dialeto DuckDB | **não** — modelo de completion, sem chat template de agente |

Benchmarks publicados: Qwen3-30B-A3B (base do Coder) perde só pro QwQ-32B em
LiveCodeBench entre os abertos e fica atrás só do GPT-4o em BFCL;
DuckDB-NSQL-7B foi treinado em 200k pares text-to-SQL **no dialeto DuckDB**
(sintaxe + extensões), mas é de 2023. O XiYanSQL-QwenCoder-32B (67,1% BIRD,
89,2% Spider) foi descartado como agente: é fine-tune de SQL puro e denso de
32B — pode ter perdido o tool-calling do Qwen base, e BIRD/Spider medem SQL
isolado, nunca o laço de ferramentas.

## Dois papéis, não um substituto

- **Qwen3-Coder-30B-A3B — substituir o Gemma no laço agêntico inteiro**
  (dsh+MCP): mesma classe de MoE eficiente em CPU (3,3B ativos vs ~4B),
  tool-calling nativo, SQL mais forte nos benchmarks gerais.
- **DuckDB-NSQL-7B — apurador dentro do `laco.ts`**: sem agente, sem MCP.
  Outro modelo decide tabela/join e conduz o laço; ele só redige a query.

## O experimento

**Pré-requisito:** item 2 de [`backlog.md`](backlog.md) — rodar os 32 casos com
`n` conferido pelo dsh atual (e antes o item 0, a régua de `correto`). Sem
linha de base real, qualquer comparação é contra um número que não existe.

1. GGUF do `Qwen3-Coder-30B-A3B-Instruct`, quantizado no tamanho do Gemma atual
   (13,43 GiB q4_0) → mesmos 32 casos por `harness/compara.ts`, mesmo portão,
   mesmo beelink. Seleção de dataset isolada: `avalia_datasets.ts --fewshot`
   nas 274 perguntas.
2. GGUF do `DuckDB-NSQL-7B` → **só** a geração de SQL (tabela e colunas já
   resolvidas, sem tool-calling), nos casos onde o Gemma erra por codificação —
   ver se acerta `causa_basica` sem o portão corrigir.
3. Comparar: % SQL válida, % número bate com `respostas.md`, tokens/s
   **medidos** (a CPU do beelink não é H100 nem M4 Max).

## Veredito por ora

Nada agora. Medir o Gemma ponta a ponta primeiro. Depois, o Qwen3-Coder é o
teste de maior valor esperado (troca o agente inteiro, mesma classe de custo em
CPU); o DuckDB-NSQL é mais barato de rodar e vale como sonda isolada nos casos
que já sabemos que o Gemma erra.

## Fontes

- [Qwen3-Coder-30B-A3B-Instruct (OpenRouter)](https://openrouter.ai/qwen/qwen3-coder-30b-a3b-instruct)
- [DuckDB-NSQL-7B-v0.1 (HF)](https://huggingface.co/motherduckdb/DuckDB-NSQL-7B-v0.1) · [AI That Quacks (MotherDuck)](https://motherduck.com/blog/duckdb-text2sql-llm/)
- [XiYanSQL-QwenCoder (GitHub)](https://github.com/XGenerationLab/XiYanSQL-QwenCoder)
- [`harness_gemma_dsh.md`](harness_gemma_dsh.md), [`backlog.md`](backlog.md), [`regras.md`](regras.md) — o que já roda e o que falta medir
