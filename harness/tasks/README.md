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
| [`backlog.md`](backlog.md) | **O que fazer a seguir**, ordenado por retorno medido nas 284 perguntas — desambiguar dataset irmão (24 das 36 falhas), rodar os casos com `n` conferido (58 hoje, era 32 quando o item foi escrito), a prosa citando tabela | 🟡 aberto 2026-09-02 — 9 itens; 0, 1 e 6 fechados (1 medido: recall 91,2%→93,9%, vizinho 24→18), 3 e 7 parciais (3: reescreve e sanitiza a prosa; 7: só o caso sem leitura legítima virou rejeição dura), 2 tem a ponte pronta mas a rodada (~5,8h) ainda não começou; 4, 5, 8 nada feito |
| [`regras.md`](regras.md) | As regras que o harness já pagou para aprender, por subsistema (portão, prefixo, laço, medir) — cada uma com o erro observado atrás e onde está travada. Semente do Experience store de `harness_bpe.md` | 🟡 ativo — Rodadas 1-8; 4 regras ainda só disciplina, viradas em tarefa |
| [`operacao.md`](operacao.md) | Checagens antes de confiar numa rodada (raciocínio desligado, cache de prefixo vivo, `-c` por slot, modelo sem saída lateral) e **6 tarefas para automatizá-las** — hoje toda checagem é inspeção manual de log | 🟡 aberto 2026-09-02 — 6 tarefas: 1, 2 e 3 feitas (a 3 verificada ao vivo 2026-09-02), 4 e 5 nada feito |
| [`check-qwencoder-vs-duckdbnsql.md`](check-qwencoder-vs-duckdbnsql.md) | Qwen3-Coder-30B-A3B (agente) e DuckDB-NSQL-7B (redator) trocariam/complementariam o Gemma 4? | 🔵 aberto 2026-09-02 — plano de experimento, nada rodado no beelink; espera a linha de base do item 2 de `backlog.md` |

## Convenção

Mesma do `tasks/` raiz: cada arquivo carrega no topo quando foi aberto, a
pedido de quem, e o estado real do que já rodou no beelink versus o que é só
plano — nenhum destes documentos assume que algo funciona sem uma medição
citada. Quando um item fechar de vez (não só "respondido", mas sem mais
desdobramento esperado), `git mv` para [`done/`](done/) — o `done/` local, não o
do `tasks/` raiz. A versão anterior desta linha mandava o contrário; mudou a
pedido, em 2026-09-02, e o motivo é de leitura: uma tarefa fechada do harness
lida ao lado das outras seis do harness diz mais do que arquivada entre as do
projeto inteiro, e mantém a tabela acima curta — quem chega vê só o que está
aberto.
