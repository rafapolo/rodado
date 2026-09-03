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
| [`backlog.md`](backlog.md) | **O que fazer a seguir**, ordenado por retorno medido nas 284 perguntas — desambiguar dataset irmão (24 das 36 falhas), rodar os casos com `n` conferido (58 hoje, era 32 quando o item foi escrito), a prosa citando tabela | 🔴 aberto 2026-09-02 — 11 itens; 0, 1, 3, 5 e 6 fechados, 7 e 9 parciais, **2 rodando 2026-09-03 e ABORTADO no caso 6/58 — achou bug bloqueador (item 10): tool call do Gemma cai como texto solto em ~2/3 das sessões, `--no-jinja` testado e descartado, nada resolvido ainda**, 4 e 8 esperando o item 10 fechar |
| [`regras.md`](regras.md) | As regras que o harness já pagou para aprender, por subsistema (portão, prefixo, laço, medir) — cada uma com o erro observado atrás e onde está travada. Semente do Experience store de `harness_bpe.md` | 🟡 ativo — Rodadas 1-8; as 4 regras "só disciplina" viraram tarefa e fecharam 2026-09-03; achado novo bloqueador no laço (tool call do Gemma não reconhecido) — ver `backlog.md` item 10 |
| [`operacao.md`](operacao.md) | Checagens antes de confiar numa rodada (raciocínio desligado, cache de prefixo vivo, `-c` por slot, modelo sem saída lateral) e **6 tarefas para automatizá-las** — hoje toda checagem é inspeção manual de log | 🟢 aberto 2026-09-02 — 6 tarefas, todas fechadas 2026-09-03 (a varredura da 5 não achou candidato novo; falta só a verificação ao vivo das tarefas 1 e 3, adiada de propósito para não colidir com a rodada em background do item 2 de `backlog.md`) |
| [`check-qwencoder-vs-duckdbnsql.md`](check-qwencoder-vs-duckdbnsql.md) | Qwen3-Coder-30B-A3B (agente) e DuckDB-NSQL-7B (redator) trocariam/complementariam o Gemma 4? | 🔵 aberto 2026-09-02 — plano de experimento, nada rodado no beelink; espera o item 10 do `backlog.md` fechar (o bug bloqueia a linha de base do item 2 também) |

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
