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
| [`retomar_2026-09-04.md`](retomar_2026-09-04.md) | **Runbook** — o que ficou pendente em 2026-09-04 com os comandos exatos: commitar o que está pronto, conferir o parquet corrompido de `br_cgu_emendas_parlamentares.microdados`, verificar a rota `br_transferegov` que pode desbloquear o T21, e remedir o desperdício de turno | 🟢 aberto 2026-09-04 — passos 2, 3 e 4 bloqueados enquanto o beelink não voltar (TCP 22 `No route to host`); o passo 1 (commit) roda sem ele |
| [`ferramentas_claude_code.md`](ferramentas_claude_code.md) | **A meta de paridade de passos** (não de velocidade), com o primeiro head-to-head medido do projeto — Gemma 21 chamadas / 57% úteis contra Claude 8 / 100% na mesma pergunta — mais o contrato de ferramenta do Claude Code lido do próprio contexto (pré-condição de estado, idempotência, argumento inválido como erro, estado no resultado) mapeado contra esse desperdício: 7 propostas, 1 achado, 3 mecanismos descartados | 🟡 aberto 2026-09-04 — **6 das 7 propostas implementadas** em `mcp.ts`/`portao.ts`/`sqlguard.ts` (curto-circuito idempotente, argumento não declarado, `capRows` ensina no corte por linhas, instrução negativa nas descrições, estado grudado no resultado, `descrever_tabela` em lista); a pré-condição `descrever_tabela`→`consultar` está implementada mas **desligada** (`HARNESS_EXIGE_DESCRICAO`, sem caso observado atrás). Só falta portar `resolve_join` — a maior alavanca isolada, mas a única que exige A/B (6→7 ferramentas contraria medição de `regras.md`) — e remedir a pergunta de 5 fontes contra o código atualizado. Traz também o placar da rodada de 2026-09-04 com o `572d64e` no ar (74→24 chamadas, 38→0 repetições, mas ainda sem convergir) e um achado lateral que pode desbloquear o T21 de `respostas.md` pela rota `br_transferegov` |
| [`tabelas_hub.md`](tabelas_hub.md) | **Achado ao vivo 2026-09-04**, rodando T04-2 pela 2ª vez: o Gemma gastou 6 passos caçando a tabela que traduz `id_municipio` pra nome (`br_ibge_munic`, `br_ibge_nomes_brasil` — ambos chutes errados), porque o harness não tem busca semântica pra descobrir tabela de referência não citada na pergunta. Conserto pontual já aplicado (hint em `listar_datasets`); o plano é gerar a lista completa de tabelas-hub a partir de `canonical_table` em `bridges.yaml`, mesma disciplina de `join_keys.md` | 🔵 aberto 2026-09-04 — caso município consertado e validado (v2→v3 do mesmo dia não repetiu a caçada); o gerador (`gera_tabelas_hub.py`) ainda não existe |
| [`harness_gemma_agente.md`](harness_gemma_agente.md) | Plano de arquitetura (fases 0-5) e as medições no beelink que sustentam cada escolha — portão, cache de prefixo, laço agêntico vs. pipeline fixo | 🟢 ativo — fases 0-3 feitas (5 commits, 51 testes), Fase 4 em andamento |
| [`harness_bpe.md`](harness_bpe.md) | Belief/Progress/Experience (EvoHarness-RL, arxiv 2608.05446) como scaffold estático para a Fase 5 (relatório) — sem treino, três acréscimos concretos ao portão | 🔵 aberto 2026-09-02 — mapeamento feito, nada implementado; depende da Fase 4 fechar primeiro |
| [`backlog.md`](backlog.md) | **O que fazer a seguir**, ordenado por retorno medido nas 284 perguntas — desambiguar dataset irmão (24 das 36 falhas), rodar os casos com `n` conferido (58 hoje, era 32 quando o item foi escrito), a prosa citando tabela | 🟡 aberto 2026-09-02 — 13 itens; 0, 1, 3, 5, 6 e **12** fechados, 7 e 9 parciais, **2 em andamento (3ª tentativa) com o workaround de retentativa do item 10 no ar** — item 10 achou o bug bloqueador (tool call do Gemma cai como texto solto), `--no-jinja` e `--temp 0` testados e descartados, causa raiz upstream ainda aberta; item 11 é o plano de LoRA pra esse conserto (RunPod, ~US\$5–40, nada rodado — passo 0 é checar suporte de `transformers`/`peft` pra arquitetura); **item 12 fechado 2026-09-03** — pergunta de 5 fontes rodou 40 min e morreu sem resposta; agora `mcp.ts` detecta junção sem ponte conhecida e um disjuntor de repetição, validados contra o log da sessão real (disjuntor teria disparado no turno 27, não no 74) — o problema de DADO por trás (T21, sem chave real entre as tabelas) continua aberto, só o de harness fechou; 4 e 8 esperando o item 2 terminar |
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
