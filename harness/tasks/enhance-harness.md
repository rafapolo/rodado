# Refino do harness — o que cada medição mandou mudar

Catálogo vivo. Uma linha por coisa aprendida, o que ela implicou, e se já virou
código. A ordem é a das rodadas, para dar para ver o raciocínio evoluindo (e os
becos sem saída).

**Regra de trabalho que emergiu daqui:** toda rodada termina classificando as
falhas, não só contando acertos. Um número diz se está bom; a classe das falhas
diz o que consertar. `avalia_datasets.ts` faz isso desde 2026-09-02.

---

## Rodada 1 — o modelo isolado (2026-09-01)

| Aprendido | Refino |
|---|---|
| 16 threads é 31% pior que 8 e com desvio 10x maior | `-t 8` fixo em `bench_gemma.sh` e no README, com o porquê medido junto |
| Prefill cai de 70 para 54 t/s entre 512 e 4096 tokens | primeiro sinal de que **contexto** seria o gargalo — não foi seguido na hora, e voltou a morder na rodada 5 |

## Rodada 2 — a primeira SQL gerada

| Aprendido | Refino |
|---|---|
| Primeira tool call foi `COUNT(*)` sem filtro de partição | camada de partição no portão, usando `rows` do `catalog.parquet` |
| `causa_basica BETWEEN 'X60' AND 'X84'` deu **726** contra **789** reais | camada de codificação: `BETWEEN` sobre coluna crua de CID é rejeitado |
| O erro não dá exceção, dá número plausível | **princípio que passou a valer para tudo:** o modo de falha que importa aqui é silencioso, então cada camada nova nasce de um erro observado, nunca de imaginação |

## Rodada 3 — recuperação

| Aprendido | Refino |
|---|---|
| Catálogo de 212 nomes no prefixo: 91,3% contra 52,9% do embedding | `search_tables` sai do caminho do Gemma; o catálogo entra no prefixo |
| Few-shot leva a 97,8% e é **grátis** por causa do cache de prefixo | exemplos passam a fazer parte do prefixo estável |
| `provenance_notes` são 76% boilerplate | não entram no prompt; do `catalog.parquet` só `rows` e `status` importam |
| `br_seeg` e `br_seeg_emissoes` existem os dois | **desfiz** um casamento por prefixo que eu tinha escrito: trocaria uma escolha legítima por outra, calado. `resolveDataset` corrige só grafia |

## Rodada 4 — o laço

| Aprendido | Refino |
|---|---|
| Exemplos few-shot dominavam a instrução (o modelo respondia datasets quando se pedia tabelas) | exemplos passam a carregar a marca da etapa a que pertencem |
| O prompt de reparo não carregava contexto — cada chamada é independente | reparo reenvia pergunta, schema, pontes, a SQL rejeitada e o motivo |
| Portão tratava nome de CTE como tabela inexistente | portão fica ciente de `WITH ... AS`, que é como se escreve join entre datasets |
| `EXPLAIN` devolve plano em arte-ASCII, e meu executor tratava como erro | só assinatura de erro do DuckDB reprova |
| `n` saía do "primeiro número da linha" e apanhava o coeficiente | consulta obrigada a devolver `COUNT(*) AS n` |
| `n=0` era reportado como resultado | join vazio vira reparo, com as causas prováveis na mensagem |

## Rodada 5 — o dsh de verdade

| Aprendido | Refino |
|---|---|
| **O modelo usava a ferramenta `bash` para consultar o DuckDB por fora do portão** | desligadas `bash`, `pwsh`, `fs`, `web`, `subagent`, `skill`, `workflow`, `todo`, `goal`, `ralph`, `jobs` |
| Prompt do dsh eram 14.213 tokens; throughput cai ~3x de 2k a 18k | o corte acima levou a 6.849 (−52%): suicídios RJ 645→490 s, PIB MG 504→293 s |
| Raciocínio continuava ligado apesar de `reasoningEfforts: false` | `--chat-template-kwargs '{"enable_thinking":false}'` no servidor — 20,9 → 4,7 s por turno |
| KV quantizado custa caro em CPU | sem `-ctk/-ctv q8_0`: prefill 15,8 → 50,5 t/s |
| `-c` é **por slot** | `-np` explícito sempre |
| PIB per capita deu 23.704; a métrica verificada dá 32.066 | ferramenta `definicao_de_calculo` sobre `metrics.yaml` |
| Modelo gastou 991 s em 31 palpites de nome de coluna | rejeição de coluna passa a **listar as parecidas** em vez de só acusar |
| **O benchmark contava resposta errada como acerto** | `lote.ts` passa a exigir o valor esperado; RESPONDEU e CORRETO viram colunas separadas |

## Rodada 6 — agêntico contra pipeline fixo

Mesmas perguntas, mesmo modelo, mesmo portão:

| | dsh + MCP | pipeline fixo |
|---|---|---|
| Correto | **3/3** | **0/3** |
| Tempo | ~400 s | 61 s |

As três falhas do fixo — 573 em vez de 789 (um grupo do `GROUP BY` reportado como
total), código `3550308` em vez de "São Paulo", e desistir depois de 4 rejeições —
**não são erro de SQL, são erro de não iterar**.

**Refino:** o pipeline fixo (`laco.ts`) deixa de ser candidato a produção e fica
como base de comparação. Todo ganho de tempo daqui em diante tem que preservar a
capacidade de iterar.

## Rodada 7 — o conjunto de avaliação (2026-09-02)

| Aprendido | Refino |
|---|---|
| A numeração de `respostas.md` não batia com `perguntas.md` em 8 de 79 | não reatribuí por heurística (o casador erra sozinho); marquei suspeitos e a correção veio de revisão humana — 81 confiáveis, 3 suspeitos |
| **Eu usava 84 perguntas quando havia 274** | escolha de dataset não precisa de resposta conferida, só dos datasets citados. As 178 sem resposta entram |
| Metade do conjunto ia para o prefixo como few-shot | exemplos passam a vir de fonte **independente** (`docs/relatorio-social/`, 50 exemplos), e as 274 inteiras viram teste |
| Um `TimeoutError` derrubava a avaliação inteira | cada caso é isolado; erro conta e a rodada segue |
| Requisições paralelas com `-np 1` só enfileiram | servidor com `-np 5`, e uma chamada de aquecimento antes de abrir as paralelas — senão as 5 pagam o prefill inteiro juntas |

---

## Padrões que valem para o próximo

1. **Toda camada do portão nasce de um erro observado.** Nenhuma foi imaginada, e
   as duas que mais pegam (partição, codificação) vieram das duas primeiras SQLs
   que o modelo escreveu.
2. **Medir a medição.** Dois erros meus estavam na régua, não no harness: o
   benchmark premiando resposta errada, e o conjunto de teste com 84 casos quando
   havia 274. Os dois passaram despercebidos por rodadas.
3. **Config que "parece" aplicada não está.** `reasoningEfforts: false`,
   `--reasoning off` e `--dump-config` deram todos a impressão de resolver.
   Só o comportamento medido conta.
4. **Desfazer também é refino.** O casamento por prefixo de dataset e o KV
   quantizado eram "melhorias" minhas que pioravam.

## Aberto

- Taxa de acerto ponta a ponta nos **32** casos com `n` conferido fora do prefixo
  (30 deles multi-dataset) — o número que responde ao objetivo.
- A prosa cita nome de tabela; a convenção de `pages/analises/results/` é citar o
  órgão de origem.
- `br_ibama_embargos` e `br_seeg` precisam de status novo no `_rodado_metadata`,
  que é estado compartilhado — o portão já os bloqueia localmente.
