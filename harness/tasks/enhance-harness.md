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

## Rodada 8 — as 274 perguntas, e três bugs meus (2026-09-02)

Primeira medição no conjunto inteiro, com exemplos de fonte independente.

| | antes dos consertos | depois |
|---|---|---|
| Recall de dataset | 89,5% (384/429) | **91,2%** (393/431) |
| Casos perfeitos | 84,3% (231/274) | **86,9%** (238/274) |
| Erros de execução | 5 | **0** |
| Tempo (5 paralelos) | 20,9 min | 15,2 min |

Os 2,5 pontos vieram de consertar a régua, não o modelo:

| Bug meu | Efeito |
|---|---|
| Gabarito engolia `chaves: id_municipio, sigla_uf` como se fossem datasets | 3ª e 7ª "falha" mais comum eram fantasma |
| `resolveDataset` só tentava `br_`; o espelho tem `br_`, `world_`, `us_` | `olympedia_olympics` contava como erro |
| Testes apontando para `br_seeg`/`br_ibama_embargos`, removidos do espelho | 3 testes vermelhos por motivo bom |

**Paralelismo não multiplica.** Com `-np 5` cada caso passou de ~2 s para ~12 s e
o total caiu só de 20,9 para 15,2 min: o modelo é limitado por CPU em 8 threads e
5 requisições dividem o mesmo compute. O ganho vem do batch de decode do
llama.cpp, não de concorrência de verdade — vale usar, mas não espere 5x.

**Abstração nova, `harness/servidor.sh`.** Reiniciar o llama-server à mão falhou
**três vezes seguidas do mesmo jeito**: o processo antigo ainda segura a porta, o
novo morre com "couldn't bind" em silêncio, o antigo segue servindo com a config
velha, e a medição seguinte sai errada sem aviso. O script espera a **porta**
liberar (não o processo sumir) e **confere que subiu com o que foi pedido**.

---

## O que fazer a seguir, em ordem de retorno

Cada item sai de uma falha medida, não de intuição.

### 1. Desambiguar dataset irmão — **24 das 36 falhas**

A classe `vizinho` é a maior e é sempre a mesma forma: o modelo escolhe o parente
errado, e os nomes não distinguem.

| Pediu | Deu |
|---|---|
| `ibge_ppm` (pecuária municipal) | `ibge_pam` (agrícola municipal) |
| `anp_combustiveis` | `anp_precos_combustiveis` |
| `me_caged` | `me_rais` |
| `tesouro_capag` | `firjan_ifgf`, `me_siconfi` |

**Ação:** uma linha de descrição por dataset no catálogo do prefixo, só onde há
ambiguidade — ~40 tokens por par, não os 14k das `provenance_notes` inteiras (76%
boilerplate, já descartadas na rodada 3).

**Como medir se valeu:** a classe `vizinho` tem que cair. Se cair e a
`nada_perto` subir, a descrição está confundindo em vez de esclarecer.

### 2. Rodar o laço nos 32 casos com `n` conferido

O número que responde ao objetivo, e o único ainda não medido: 30 dos 32 exigem
2+ datasets. A ~6 min por pergunta dá ~3,2 h. **É o próximo trabalho pesado.**

### 3. A prosa cita a ferramenta

As respostas mencionam `br_ibge_pib.municipio`. A convenção de
`pages/analises/results/` é citar o **órgão de origem**, nunca a tabela ou o SQL.
Conserto: instrução na etapa de prosa mais uma checagem que rejeite resposta
contendo `br_[a-z_]+\.`.

### 4. Encurtar mais o contexto

O prompt do dsh está em 6.849 tokens (era 14.213). O throughput cai ~3x entre 2k
e 18k, então cada corte se paga. Falta examinar quanto das ferramentas restantes
é descrição que o modelo não usa.

### 5. Seis datasets concentram 20 das 38 perdas

`ibge_ppm` (4x), `ms_sinan_violencia` (4x), `ibge_pib` (3x),
`inep_avaliacao_alfabetizacao` (3x), `mp_pep` (3x), `ms_atencao_basica` (3x). Se
for sempre a mesma confusão, o item 1 resolve; se for nome opaco, o dataset
talvez precise de alias.

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

## Fechado desde a última revisão

- `br_ibama_embargos` e `br_seeg` **foram removidos do espelho** depois que o
  levantamento os expôs. Hoje caem na camada `tabela` do portão, desfecho melhor
  do que ser desviado. A camada `inservivel` segue guardando as duas tabelas
  vazias que restam.
- O emparelhamento de `docs/respostas.md` foi corrigido por revisão humana: 81
  confiáveis e 3 suspeitos, contra 71 e 8.
