# Qwen Coder ou DuckDB-NSQL trocaria o Gemma 4 no harness?

> Aberto em 2026-09-02, a pedido, continuação de
> `check-dspark-replacement.md` (mesma pergunta de fundo — "dá pra trocar o
> Gemma por algo melhor em SQL/tool-calling?" — candidatos diferentes). **Nada
> abaixo foi rodado no beelink.** Os números do Gemma são medidos (ver
> `harness_gemma_dsh.md`); os dos candidatos são de benchmark publicado
> (BIRD/Spider/BFCL), não do harness real.

## Os candidatos

| Modelo | Params (total/ativos) | Arquitetura | Especialidade | Tool-calling |
|---|---|---|---|---|
| **Gemma 4 26B-A4B** (atual) | 26B / ~4B | MoE 128 experts | generalista | sim, via grammar do llama.cpp (template não tem `tools` nativo) |
| **Qwen3-Coder-30B-A3B** | 30,5B / 3,3B | MoE, 128 experts (8 ativos) | código/SQL + agente | sim, nativo — treinado pra tool-use |
| **XiYanSQL-QwenCoder-32B** | 32B / 32B (densa) | fine-tune do Qwen Coder | só text-to-SQL | não é o foco do fine-tune — checar se sobrevive |
| **DuckDB-NSQL-7B** | 7B / 7B (densa) | Llama-2 7B + fine-tune | só dialeto DuckDB | não — modelo de completion, sem chat template de agente |

Benchmarks publicados (não medidos aqui):
- XiYanSQL-QwenCoder-32B: **67,14%** BIRD Dev@M-Schema, **89,20%** Spider Test —
  acima do GPT-4o-0806 (58,47% no mesmo BIRD). Apache 2.0, também em 3B/7B/14B.
- Qwen3-30B-A3B (base do Coder): perde só pro QwQ-32B em LiveCodeBench/CodeForces
  entre os abertos, e fica atrás só do GPT-4o em BFCL (function calling).
- DuckDB-NSQL-7B: treinado em 200k pares text-to-SQL **especificamente no
  dialeto DuckDB** (sintaxe, extensões oficiais), não só `SELECT` — mas é
  2023/Llama-2, sem tool-calling.

## Por que isto pode importar mais que o DSpark

O `check-dspark-replacement.md` concluiu que o gargalo do harness não é
velocidade (a correção do `reasoning: off` já deu 4,4x de graça) — é
**acerto de SQL**: o Gemma erra codificação silenciosamente (`causa_basica
BETWEEN 'X60' AND 'X84'` → 726 em vez de 789, 8% a menos, número plausível).

Isso muda a pergunta de "modelo mais rápido" pra "modelo mais preciso em SQL",
que é exatamente o que XiYanSQL-QwenCoder e DuckDB-NSQL prometem — ao contrário
do LFM2.5/DSpark, que só prometia latência.

## O risco dos dois candidatos especializados

Nenhum dos dois foi feito pra rodar dentro do laço agêntico do dsh:

1. **XiYanSQL-QwenCoder** é um fine-tune de SQL puro — pode ter perdido parte
   da habilidade geral de tool-calling/instruction-following do Qwen Coder
   base ao ser especializado. Não documentado nos benchmarks publicados
   (BIRD/Spider medem SQL isolado, não o loop de ferramentas).
2. **DuckDB-NSQL-7B** é ainda mais restrito: sem chat template de agente, é
   modelo de *completion* (prompt → SQL, sem tool call, sem MCP). Não serve
   como "cérebro" do dsh — serve, na melhor hipótese, como **redator de SQL
   dentro do pipeline fixo** (`laco.ts`, sem MCP), com outro modelo (Gemma ou
   Qwen3-Coder) decidindo tabela/join e conduzindo o loop.

Isso aponta pra dois papéis diferentes, não um "substituto":

- **Qwen3-Coder-30B-A3B** — candidato a *substituir* o Gemma no laço agêntico
  inteiro (dsh+MCP): mesma classe de MoE eficiente em CPU (3,3B ativos vs 4B),
  tool-calling nativo, e código/SQL mais forte que o Gemma nos benchmarks
  gerais.
- **DuckDB-NSQL-7B** — candidato a *apurador* dentro do `laco.ts`: se escrever
  SQL no dialeto DuckDB com menos erro de codificação que o Gemma, vale medir
  como redator de query isolado, não como agente.

## O experimento

Pré-requisito ainda não feito (`harness_gemma_dsh.md`, item 1 da lista
"Falta"): rodar a avaliação completa dos 53 casos com `n` conferido pelo dsh
atual, pra ter linha de base real — sem isso qualquer comparação é contra um
número que não existe ainda.

Depois disso:

1. Baixar GGUF de `Qwen3-Coder-30B-A3B-Instruct` (quantizado, mirar tamanho
   parecido ao Gemma atual — 13,43 GiB q4_0) e rodar os mesmos 53 casos pelo
   `harness/compara.ts` (ou `avalia_datasets.ts --fewshot` pra seleção de
   dataset isolada), mesmo portão, mesmo beelink.
2. Baixar GGUF de `DuckDB-NSQL-7B` e testar **só** a etapa de geração de SQL
   (dado tabela+colunas já resolvidos, sem tool-calling) contra os casos onde
   o Gemma errou por codificação — ver se ele acerta `causa_basica` sem
   precisar do portão corrigir.
3. Comparar: % SQL válida, % número bate com `respostas.md`, tokens/s medidos
   (não o benchmark publicado — CPU do beelink não é H100 nem M4 Max).

## O que fazer com isto

Nada agora — mesmo veredito do DSpark: medir o Gemma ponta a ponta primeiro
(pré-requisito acima). Depois disso, o teste do Qwen3-Coder-30B-A3B é o de
maior valor esperado (troca o agente inteiro, mesma classe de custo em CPU);
o do DuckDB-NSQL é mais barato de rodar (só geração de SQL, sem agente) e vale
como teste rápido isolado nos casos que já sabemos que o Gemma erra.

## Fontes

- [XiYanSQL-QwenCoder (GitHub)](https://github.com/XGenerationLab/XiYanSQL-QwenCoder)
- [Qwen3-Coder-30B-A3B-Instruct (OpenRouter)](https://openrouter.ai/qwen/qwen3-coder-30b-a3b-instruct)
- [DuckDB-NSQL-7B-v0.1 (Hugging Face)](https://huggingface.co/motherduckdb/DuckDB-NSQL-7B-v0.1)
- [AI That Quacks: Introducing DuckDB-NSQL-7B (MotherDuck)](https://motherduck.com/blog/duckdb-text2sql-llm/)
- `check-dspark-replacement.md`, `harness_gemma_dsh.md` — contexto e medições do que já roda
