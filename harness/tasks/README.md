# harness/tasks/ — índice

Tarefas do subsistema `harness/` (o apurador local com Gemma 4 — ver
[`../README.md`](../README.md)): plano de arquitetura, medições, catálogo de
refino, avaliação de modelo candidato. Separado de [`../../tasks/`](../../tasks/README.md),
que é o índice do projeto como um todo (datasets, raspagem, camada
semântica, o espelho) — nada aqui depende de tabela nova no mirror, e nada em
`tasks/` depende de código em `harness/`.

Ordenados por atividade recente, não por tema.

| Arquivo | Descrição | Status |
|---|---|---|
| [`harness_gemma_dsh.md`](harness_gemma_dsh.md) | Plano de arquitetura (fases 0-5) e as medições no beelink que sustentam cada escolha — portão, cache de prefixo, laço agêntico vs. pipeline fixo | 🟢 ativo — fases 0-3 feitas (5 commits, 51 testes), Fase 4 em andamento |
| [`harness_bpe.md`](harness_bpe.md) | Belief/Progress/Experience (EvoHarness-RL, arxiv 2608.05446) como scaffold estático para a Fase 5 (relatório) — sem treino, três acréscimos concretos ao portão | 🔵 aberto 2026-09-02 — mapeamento feito, nada implementado; depende da Fase 4 fechar primeiro |
| [`enhance-harness.md`](enhance-harness.md) | Catálogo vivo — uma linha por medição, o que ela implicou, se já virou código. Semente do Experience store de `harness_bpe.md` | 🟢 ativo — 7 rodadas registradas |
| [`check-dspark-replacement.md`](check-dspark-replacement.md) | LFM2.5 + DSpark trocaria o Gemma 4 no harness? | ✅ respondido 2026-09-02 — não como está; nada rodado no beelink ainda |
| [`check-qwencoder-vs-duckdbnsql.md`](check-qwencoder-vs-duckdbnsql.md) | Qwen3-Coder-30B-A3B (agente) e DuckDB-NSQL-7B (redator) trocariam/complementariam o Gemma 4? | 🔵 aberto 2026-09-02 — plano de experimento, nada rodado no beelink; espera medição do Gemma (item 1 de `harness_gemma_dsh.md`) |

## Convenção

Mesma do `tasks/` raiz: cada arquivo carrega no topo quando foi aberto, a
pedido de quem, e o estado real do que já rodou no beelink versus o que é só
plano — nenhum destes documentos assume que algo funciona sem uma medição
citada. Quando um item fechar de vez (não só "respondido", mas sem mais
desdobramento esperado), mover para `../../tasks/done/` segue sendo o lugar
certo — não criar um `done/` paralelo aqui só por este subsistema ser pequeno.
