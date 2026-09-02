# Harness de relatório: DeepSeek Harness + mcp_server.py + Gemma 4 local

> Aberto em 2026-09-01. Plano para transformar o Gemma 4 26B-A4B rodando no
> beelink num harness de produção que responde perguntas em pt-BR consultando o
> espelho via DuckDB. O plano original abaixo (fases 0-5) **já foi implementado**
> — ver "Status em 2026-09-01, fim do dia" logo abaixo antes de ler o resto como
> se fosse projeto futuro. As medições da seção seguinte continuam válidas como
> registro do que motivou cada decisão de arquitetura.

## Status em 2026-09-01, fim do dia — o que saiu do papel

Trabalho de duas sessões (`gemma4-moe-quantization-benchmark`, dona do branch
`harness-gemma`/`harness/`; `fix-answer-label-swap`, ajudando fora de `harness/`
no mesmo checkout), coordenadas por uma terceira. Consolidado aqui pra quem
retomar não precisar reconstruir o histórico de mensagens.

**Fases 0-3 do plano abaixo: feitas.** 5 commits em `harness-gemma`, 51 testes.
- `portao.ts` — as 7 camadas da Fase 0, ciente de CTE (não só `_check_read_only`
  ingênuo).
- `mcp.ts` — 4 ferramentas; o portão em si é ferramenta MCP, então a rejeição
  volta como resultado de tool call e o laço agêntico do dsh repara sozinho (ver
  achado abaixo — não é só teoria, rodou de verdade).
- `anos.ts` — faixa de ano real por tabela, 377 tabelas cacheadas. Resolveu um
  `n=0`: o modelo montou CAGED×RAIS×PIB corretamente e filtrou `ano=2022`, mas
  `br_ibge_pib.municipio` termina em 2021 — sem essa checagem o harness
  reportaria zero como se fosse resposta real.
- `avalia_datasets.ts` — seleção de dataset por few-shot: **97,8%**, contra
  **52,9%** do `search_tables` por embedding (ver `avalia_douradas_perguntas.py`
  pro método de medição equivalente).
- `dsh/rodado.patch.yml` — `llama-server` local plugado no dsh.

**Fase 4 (medir com pergunta real): primeira rodada ponta a ponta validou a
arquitetura inteira, não só o código isolado.** Pergunta: óbitos por suicídio
(X60–X84) no RJ em 2020, por sexo. Sem o portão, o Gemma escreve `causa_basica
BETWEEN 'X60' AND 'X84'` e erra por 8% (726 em vez de 789) — o bug de codificação
CID já registrado na seção "Medições" abaixo. **Com o portão como ferramenta MCP,
a rejeição voltou ao modelo, que reescreveu com `substr()` e chegou nos 789
corretos** — conferido por fora, decomposição por sexo bateu também (573
masculino, 215 feminino, 1 não informado). O cache de prefixo sobreviveu ao
laço agêntico: 16.397 de 16.585 tokens do prompt vieram do cache.

**Bloqueio de contexto resolvido**: `-c` do `llama-server` é **por slot**, não
global — com os 4 slots padrão o KV cache real era 4x o que parecia. Fix:
`-c 65536 -np 1`.

### Falta → migrado para [`backlog.md`](backlog.md)

A lista que ficava aqui saiu em 2026-09-02: mantinha uma segunda fila de
próximos passos, com contagens já desatualizadas (falava em "53 casos" quando
são **32** com `n` conferido), competindo com a fila medida do `backlog.md`.
Duas listas divergindo é como se lê o número errado.

Onde cada item foi parar: rodar a avaliação completa → **item 2**; camada de ano
no portão → **item 6**; alerta de sanidade virar reparo → **item 7**; medir a
prosa contra as 9 análises → **item 8**.

### Achados fora do harness, mas achados *por causa* dele

O item 2 do TODO informal ("datasets quase-duplicados confundindo o matching de
avaliação") gerou um levantamento à parte — ver `tasks/datasets_quase_duplicados.md`
(gitignored, não versionado) pro detalhe completo. Dois achados de lá viraram
prioridade maior que o próprio dedup:

- **`br_ibama_embargos` está silenciosamente VAZIO** — bug de parsing no scrape
  original zerou os bytes de toda subtabela. Já diagnosticado no próprio
  `provenance_notes` de `br_ibama_embargos_novo` ("deve ser removido ou marcado
  obsoleto"), mas o `status` continua `'done'` em `_rodado_metadata` — não
  `blocked`. Consequência prática: uma pergunta contra a tabela errada roda sem
  erro e devolve zero linhas, que parece "não há dado" quando na verdade há dado,
  só que na tabela certa (`br_ibama_embargos_novo`). **Ação pendente, não feita
  ainda**: mudar o `status` em `_rodado_metadata`/`build_metadata_catalog.py` de
  `'done'` pra algo que o catálogo trate como bloqueado, e (proposta de
  `gemma4-moe-quantization-benchmark`) o `portao.ts` rejeitar consultas contra
  tabela com `status` bloqueado, apontando a canônica na mensagem de erro.
- **`br_seeg`** tem o mesmo problema de status — já marcado
  `'redundante — remover'` em `_rodado_metadata`, ainda ativo/consultável.
  Canônico: `br_seeg_emissoes.municipio`. Mesma ação pendente do item acima.
- `br_anp_combustiveis.precos` × `br_anp_precos_combustiveis.microdados`: **não**
  são duplicata — janelas e colunas diferentes (raspagem própria 2024-03→2026-07
  sem `id_municipio`, `cnpj` sem padding; espelho BD 2004→2026-02 com
  `id_municipio`, `preco_compra` e `preco_venda`). Ação sugerida: documentar a
  distinção (nota em `bridges.yaml` ou `docs/overview/`, no espírito de
  `false_friends`), não fundir.

Item separado, achado ao medir o golden set (`tasks/douradas_perguntas.json`)
contra a avaliação de datasets: **T05-2/T05-3 estavam trocados** em
`docs/respostas.md` (pergunta do Senado com resposta pendente rotulada T05-3, e
uma resposta sobre empresários — sem relação — ocupando T05-2). Confirmado via
`bun harness/casos.ts` (contador de suspeitos caiu de 8 pra 7) e corrigido em
`main` (commit `2aa6a9e`) — esse era, coincidentemente, o par de teste que a
sessão do harness estava usando pra validar resultado, então havia risco real de
estar conferindo contra gabarito errado. Dos outros 7 pares suspeitos, um cluster
do tema 02 (IDEB/ENEM/PIB) ficou genuinamente ambíguo — não foi forçado, só
anotado como incerto (commit `8436356`, blockquote acima do bloco T02 em
`docs/respostas.md`) pra decisão humana.

**Lição de processo, não de código**: duas sessões no mesmo checkout já
colidiram uma vez (merge de `harness-gemma` pra `main` engoliu um commit da
sessão do harness sem aviso). Protocolo estabelecido depois: avisar antes de
qualquer merge/push pra `main`, mesmo mudança pequena fora de `harness/`.

## O que já existe (não construir de novo)

O projeto já tem a camada difícil pronta. `mcp_server.py` (1.379 linhas) expõe 18
ferramentas MCP, entre elas as que importam aqui:

| Ferramenta | Papel no harness |
|---|---|
| `search_tables` | recuperação por embedding (índice doc2query, ~8 perguntas sintéticas por tabela) |
| `describe_table` | colunas + `dicionario_coverage` + `coded_value_warning` |
| `resolve_join` | cláusula `ON` pronta, com as 78 pontes de `bridges.yaml` |
| `get_metric` / `list_metrics` | SQL já verificada para 12 cálculos nomeados |
| `rollup` | município→UF→região, CNAE, CID-10 |
| `run_sql` | execução read-only no beelink, com `_check_read_only`, fallback `read_parquet` e cap de linhas |

E dois conjuntos de avaliação já montados: `tasks/douradas_perguntas.json` (por
dataset) e `tasks/douradas_multi.json` (por tabela), com os scripts `avalia_*.py`.

**Consequência de projeto:** o modelo não deve reescolher tabela nem redescobrir
join. Isso já é determinístico e já foi medido contra conjunto dourado. Um modelo
de 12 t/s refazendo esse trabalho é estritamente pior.

## Medições feitas em 2026-09-01 (beelink, 8 threads, governor performance)

Estas quatro decidem a arquitetura e todas foram verificadas na máquina:

1. **Cache de prefixo do `llama-server` funciona, e vale 44x.**
   Mesmo prefixo de 1.165 tokens, três chamadas:
   | chamada | tokens prefilados | tempo |
   |---|---|---|
   | 1ª (frio) | 1.165 | 19,5 s |
   | 2ª | 5 | 0,44 s |
   | 3ª | 8 | 0,51 s |

   Só o sufixo novo é prefilado. É isto que torna um laço agêntico viável a 60 t/s
   de prefill — e transforma **estabilidade do prefixo numa restrição de
   arquitetura, não numa otimização**.

2. **Tool calling funciona**, apesar de o template do GGUF do Gemma 4 **não** ter
   suporte a `tools` (verificado: `tool_call` ausente do template embutido). O
   handler genérico do llama.cpp, constrangido por gramática, cobre o buraco:
   `finish_reason: tool_calls` com argumentos JSON válidos.

3. **O modelo gera SQL perigosa por padrão.** A primeiríssima tool call do teste
   foi `SELECT COUNT(*) FROM br_ms_sim.microdados` — sem filtro de partição, numa
   tabela enorme. É a forma exata do incidente de lock de 2h registrado no
   CLAUDE.md. Ver "Bloqueio" abaixo.

4. **Throughput:** prefill 60–70 t/s, geração 12–15 t/s, 8 threads (ver
   `gemma_stats.md` — 16 threads é 31% pior e instável).

5. **O modo de raciocínio precisa ficar desligado — 28x.** O Gemma 4 é modelo de
   *thinking*. Na pergunta de teste, ligado: 1.200 tokens e **94,8 s** gastos só
   em raciocínio, `finish_reason: length`, **nenhuma SQL produzida**. Com
   `reasoning: off` (aceito por requisição, sem reiniciar o servidor): **3,4 s** e
   SQL completa. Tensão a resolver na fase 4: desligar o raciocínio é o que torna
   o harness viável, e é plausivelmente o que teria pego o bug do item 6.

6. **A SQL gerada erra silencioso na codificação do domínio.** Pergunta:
   "suicídios (X60–X84) no RJ em 2020, por sexo". O modelo produziu filtros de
   partição corretos (`ano = 2020 AND sigla_uf = 'RJ'`) — e
   `causa_basica BETWEEN 'X60' AND 'X84'`. Como `causa_basica` guarda CID **sem
   ponto** (`X840`, `X849`) e `'X840' > 'X84'` lexicograficamente, todo o grupo
   X84 sai da conta. Medido no beelink:
   | query | óbitos |
   |---|---|
   | do modelo (`BETWEEN`) | 726 |
   | correta (`substr(causa_basica,1,3) BETWEEN`) | 789 |

   **8% a menos, com número plausível.** Não é erro de SQL — é erro de
   codificação do espelho, exatamente a classe que `bridges.yaml` e
   `dicionario_coverage.json` existem para documentar. É o que o portão precisa
   pegar, e não pega hoje.

## Arquitetura proposta

```
pergunta pt-BR
      │
      ▼
┌─────────────────────────────────────────────┐
│ DeepSeek Harness (dsh) — Cordis, Node.js    │
│  MIT, tudo é plugin, log de sessão append-only│
│                                               │
│  ├── plugin llm  ──────► llama-server         │
│  │   (dsh-llm-pi-ai,     beelink:8099         │
│  │    OpenAI-compat)     Gemma 4 26B-A4B      │
│  │                                            │
│  └── plugin mcp-client ─► mcp_server.py       │
│      (stdio)             18 ferramentas       │
└─────────────────────────────────────────────┘
      │
      ▼
relatório + SQL + proveniência (session log)
```

O dsh é MIT, em developer preview, e seu adaptador padrão fala OpenAI
chat-completions — então o `llama-server` entra sem adaptador novo. O
`dsh-mcp-client` monta um servidor MCP por instância, com transporte `stdio` ou
`streamable-http`, e expõe as ferramentas como `mcp__<server>__<tool>`. Hoje ele
faz ponte só da capability **Tools** (Resources e Prompts estão adiados) — o que
basta, porque `mcp_server.py` é só ferramentas.

### `cordis.yml` (esboço)

```yaml
plugins:
  - id: llm-local
    name: '@deepseek-ai/dsh-llm-pi-ai'
    config:
      baseUrl: http://beelink:8099/v1
      apiKeyEnv: DUMMY_KEY          # llama-server ignora
      model: gemma-4-26B-A4B-it-qat

  - id: mcp-rodado
    name: '@deepseek-ai/dsh-mcp-client'
    config:
      serverName: rodado
      transport: stdio
      command: python3
      args: ['/Users/polux/Projetos/rodado/mcp_server.py']
      env:
        BEELINK_HOST: beelink
```

## Bloqueio — o portão de partição (fazer ANTES de tudo)

`_check_read_only` valida **tipo de statement e palavras proibidas**. Não valida
filtro de partição. Isso é suficiente enquanto quem dirige o `run_sql` é uma
pessoa ou o Claude, porque a disciplina está em prosa no docstring. **Prosa em
docstring não é enforcement para um modelo autônomo** — e a medição 3 acima mostra
que o Gemma ignora essa disciplina na primeira oportunidade.

O que falta em `mcp_server.py`, antes de qualquer modelo dirigir o `run_sql`:

1. **Filtro de partição obrigatório.** Se a tabela tem `ano`/`mes`/`sigla_uf` e
   está acima de um limiar de linhas (o `catalog.parquet` já sabe o tamanho de
   cada uma), exigir predicado numa dessas colunas. Rejeitar com mensagem que
   ensina o conserto — o modelo reaproveita a mensagem no retry.
2. **`EXPLAIN` antes de executar.** DuckDB valida tabela e coluna sem ler dado.
   Erro de nome de coluna volta em milissegundos em vez de depois de um scan.
3. **`LIMIT` obrigatório** em query não agregada.
4. **Retry limitado (2–3) com o erro de volta no prompt.** É onde um modelo
   pequeno se sai bem: os erros são mecânicos (coluna errada, partição faltando).

Sem o item 1 o harness é uma máquina de travar o DuckDB do projeto.

## MCP ou tool calling direto?

Não são alternativas na mesma camada. No limite do modelo os dois terminam no
mesmo array `tools` do protocolo OpenAI — o teste da medição 2 usou tool calling
**direto, sem MCP**. MCP é descoberta e transporte, não o mecanismo que o modelo vê.

O custo do MCP aqui é pequeno: subprocesso e JSON-RPC somam milissegundos contra
3,4 s de latência do modelo, e os **3.482 tokens** de docstring (medidos: 13.931
chars nas 18 ferramentas, `run_sql` sozinho com 686) viram grátis após a primeira
chamada por causa do cache de prefixo.

O problema não é o protocolo, é a **superfície**. As docstrings de
`mcp_server.py` foram escritas para o Claude — prosa longa e cheia de nuance
(unidade do `pib`, join de CNPJ, checagem de ordem de grandeza). Um modelo de 26B
em q4 não aproveita essa nuance; ela dilui o prompt e aumenta a chance de
escolher ferramenta errada.

**Decisão proposta:** camada fina de tool calling direto que **importa as funções
de `mcp_server.py`** (não o protocolo), expondo 2–3 ferramentas com descrição
curta e imperativa. Reaproveita toda a lógica testada — `_check_read_only`,
`_rewrite_to_read_parquet`, `_cap_rows` —, pula o protocolo e controla a
superfície. O servidor MCP continua existindo para o Claude, onde as docstrings
ricas se pagam.

Isso torna o dsh opcional: ele agrega o log de sessão append-only, o replay e a
UI. Se o objetivo for só gerar relatório em lote, um laço próprio em Python/Bun
sobre o endpoint OpenAI do `llama-server` é menos peça móvel — e o dsh está em
developer preview.

## Fases

**Fase 0 — o portão.** Os quatro itens acima, mais um quinto que a medição 6
tornou obrigatório: **teste de resposta conhecida**. Toda query gerada por modelo
que toque coluna com codificação conhecida (CID, `sexo`, `raca_cor`,
`estado_civil` — o `coded_differently` de `bridges.yaml`) precisa ser conferida
contra um valor já verificado antes de o número entrar em relatório. Sem isso o
harness publica 726 no lugar de 789 e ninguém percebe.

**Fase 1 — servir.** `llama-server` como serviço (systemd user unit), `-t 8`,
prefixo estável. Medir que o cache de prefixo sobrevive entre requisições do dsh.

**Fase 2 — montar.** `cordis.yml` com os dois plugins. Perguntar algo trivial de
uma tabela só e conferir o laço inteiro ponta a ponta.

**Fase 3 — prompt de sistema estável.** Ferramentas + convenções do projeto, em
bytes idênticos entre turnos. Qualquer coisa variável (timestamp, ordem aleatória
de ferramenta) destrói o 44x.

**Fase 4 — medir com o que já existe.** `docs/perguntas.md` tem 43 temas × 5
perguntas em pt-BR e `docs/respostas.md` tem o gabarito de quais já foram
respondidas. Métricas: % que produz SQL válida, % que executa sem erro, % cujo
número bate com `respostas.md`. Rodar **com e sem** `reasoning`, para resolver a
tensão da medição 5 com dado em vez de palpite.

**Fase 5 — relatório.** Só depois que a fase 4 der número aceitável.

## Orçamento de tempo por relatório (estimado dos números medidos)

Por rodada de ferramenta, com prefixo em cache:
- modelo emite a tool call (~50 tok a 13 t/s): ~4 s
- query no DuckDB: 1–60 s conforme a tabela
- resultado volta ao contexto (~500 tok a 60 t/s): ~8 s

Um relatório com 5 consultas: **~2 a 6 min**, mais ~1 min da prosa final.
Serve para lote, não para interativo.

## Riscos honestos

- **dsh está em developer preview** — API instável, é alvo em movimento.
- **Gemma 26B em q4 fazendo raciocínio agêntico de múltiplos passos é não
  comprovado aqui.** A fase 4 existe para medir isso antes de confiar. Se o
  número for ruim, o plano B é o pipeline fixo: recuperação determinística,
  modelo chamado só em dois pontos (pergunta→SQL e números→prosa), sem laço.
- **`run_sql` com cap de linhas pode truncar o que o modelo precisa** sem que ele
  perceba — o campo `truncated` precisa virar erro visível no prompt, não nota de
  rodapé.
- **O modelo despeja o page cache do DuckDB** (medido: `buff/cache` caiu de 23 GiB
  para 12 GiB). LLM e mirror na mesma máquina competem.

## Fontes

- [DeepSeek Harness](https://www.deepseek.com/harness/en/) — página oficial
- [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) — repo (MIT)
- [MCP Integration](https://deepseekdocs.com/en/docs/features/mcp) — formato do `cordis.yml`
- [Configure models](https://deepseek-harness.github.io/deepseek-harness/en/guide/providers) — provider OpenAI-compat
