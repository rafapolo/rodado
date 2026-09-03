# Regras que o harness já pagou para aprender

> Reindexado em 2026-09-02, a pedido, a partir do catálogo cronológico
> `enhance-harness.md` (Rodadas 1–8, dissolvido neste arquivo — última versão
> lida: commit `25aeeb2`). O "o que fazer a seguir" de lá, que é medido e
> ordenado por retorno, virou [`backlog.md`](backlog.md). A ordem deixou
> de ser a das rodadas e passou a ser **por subsistema**: uma regra é consultada
> quando se mexe no portão ou no prefixo, nunca "pela data em que foi
> aprendida". Todo número abaixo foi **medido no beelink**.

Nenhuma destas regras foi imaginada. Cada uma tem um erro observado atrás, e o
custo está na coluna do meio — é o que separa regra de preferência.

A coluna **Travada em** é a que importa na prática: regra que só vive em prosa
volta a ser quebrada. As marcadas 🔴 são as [tarefas](#tarefas--travar-o-que-ainda-é-só-disciplina)
do fim do arquivo.

**Regra de trabalho que gerou todas as outras:** toda rodada termina
**classificando as falhas**, não só contando acertos. Um número diz se está bom;
a classe das falhas diz o que consertar. `avalia_datasets.ts` faz isso desde
2026-09-02.

## Portão

| Regra | O que custou aprender | Travada em |
|---|---|---|
| Toda camada nasce de um **erro observado**, nunca de imaginação | as duas camadas que mais pegam (partição, codificação) vieram das **duas primeiras** SQLs que o modelo escreveu | princípio — governa o que entra |
| Consulta sem filtro de partição é rejeitada | 1ª tool call foi `COUNT(*) FROM br_ms_sim.microdados`; varredura segura o lock do DuckDB por horas | `portao.ts` camada 4, `portao.test.ts` |
| `BETWEEN` sobre coluna crua de CID é rejeitado | `causa_basica BETWEEN 'X60' AND 'X84'` deu **726** contra **789** reais — CID é guardado sem ponto | `portao.ts` camada 6, `portao.test.ts` |
| Nome de CTE não é tabela inexistente | o portão reprovava `WITH ... AS`, que é exatamente como se escreve join entre datasets | `portao.ts` camada 2 |
| Só assinatura de erro do DuckDB reprova um `EXPLAIN` | `EXPLAIN` devolve plano em arte-ASCII e o executor tratava como erro | `portao.ts` camada 7 |
| Rejeição de coluna **lista as parecidas** | o modelo gastou **991 s em 31 consultas** caçando `causa_basica` (tentou `causa_materia`, `causa_materna`, `cid_causa_morte`) — `descrever_tabela` devolve na 5ª linha, em 619 tokens | `portao.ts` camada 3 |
| Consulta obrigada a devolver `COUNT(*) AS n` | `n` saía do "primeiro número da linha" e apanhava o coeficiente | ✅ `portao.ts` camada 8 (`checaAmostra`), `portao.test.ts` — ver tarefa 1 |
| `n=0` vira reparo, com as causas prováveis na mensagem | join vazio era reportado como resultado | ✅ `mcp.ts` (`consultar`, zero linhas + `faixasCitadas`) |

**O princípio que vale acima de todos:** o modo de falha que importa aqui é
**silencioso** — não dá exceção, dá número plausível. É por isso que nenhuma
camada pode ser especulativa: uma camada errada rejeita trabalho legítimo de
forma igualmente calada.

## Prefixo e few-shot

| Regra | O que custou aprender | Travada em |
|---|---|---|
| Recuperação de dataset é catálogo literal no prefixo, não embedding | 212 nomes no prefixo: **91,3%** contra **52,9%** do `search_tables` | `catalogo.ts`; `search_tables` fora do caminho do Gemma |
| Few-shot é grátis por pergunta e leva a **97,8%** | o cache de prefixo reaproveita o KV; prefixo vai a ~11k e o prefill medido continua em ~45 | prefixo estável, `avalia_datasets.ts --fewshot` |
| Nada variável entra no prefixo | prefixo instável evapora o 44x sem sinal no resultado | detector é `timings.prompt_n` — ver [`operacao.md`](operacao.md) tarefa 1 |
| Concorrência maior que `-np` não só enfileira à toa, **derruba a cache do slot em rodízio** | medido 2026-09-02: `avalia_datasets.ts` com `PARALELO` fixo em 5 contra servidor em `-np 1` — a partir do caso ~106/284, todo 5º caso pagou prefill do tamanho do prefixo inteiro (~5.000 tokens em vez de ~40), cadência batendo exatamente com `PARALELO`. 18,1 s/pergunta em vez dos ~2,5 s reais | `avalia_datasets.ts`, `paraleloEfetivo()` lê o `-np` real via `configServidor()` e cai para 1 (nunca um número chutado) se o servidor não responder |
| `provenance_notes` não entram no prompt | são **76% boilerplate**; do `catalog.parquet` só `rows` e `status` importam | `catalogo.ts` |
| Exemplo few-shot carrega a **marca da etapa** a que pertence | os exemplos dominavam a instrução: pedia-se tabelas e o modelo respondia datasets, chegando a ecoar `ETAPA datasets` na resposta | `prefixo.ts`, bloco `if (exemplos.length)` de `montaPrefixo()` — sem teste |
| Divisão treino/teste **por tema**, nunca por caso | dentro de um tema as 5 perguntas são variações do mesmo cruzamento — dividir por caso deixa o quase-idêntico no prefixo e mede memória | `avalia_datasets.ts` |
| Few-shot vem de fonte **independente** do conjunto de teste | metade do conjunto ia para o prefixo; os exemplos passaram a vir de `docs/relatorio-social/` (50), e as 274 inteiras viram teste | ✅ `harness/casos.test.ts` |
| Nome semântico distingue domínio, **não distingue irmão** | no conjunto inteiro, **24 das 36 falhas** são o parente errado: `ibge_ppm`↔`ibge_pam`, `anp_combustiveis`↔`anp_precos_combustiveis`, `me_caged`↔`me_rais` | ✅ codado e medido — `desambigua.ts` + `dados/desambiguacao.json`, wireado em `prefixo.ts` e `avalia_datasets.ts` — item 1 do [`backlog.md`](backlog.md), fechado 2026-09-02: recall 91,2%→93,9%, vizinho 24→18 |
| Cache de prefixo entre PROCESSOS `dsh` separados nem sempre pega, mesmo com system+tools byte-idênticos | medido 2026-09-03, rodada real do item 2 de `backlog.md` (dsh+MCP, não `avalia_datasets.ts`): dentro de uma sessão o cache funciona perfeito (cada turno paga só o incremento genuíno); ao trocar de PERGUNTA — processo `dsh` novo — o slot único (`-np 1`) reprocessa o prefixo inteiro (~7.100–7.200 tokens) em vez dos ~5–45 tokens do caso isolado que sustentava o "44x". Confirmado por log do `llama-server`: o `system`+`tools` das duas sessões são **byte-idênticos** (JSON comparado direto), então não é o "nada variável entra no prefixo" de cima — é limite do jeito como o `llama-server` reaproveita KV entre sequências que DIVERGEM logo após o prefixo comum (a conversa anterior é longa e específica do caso; a nova é curta), não só entre sequências que uma é extensão da outra | 🔴 aberto — não derruba o total por caso na prática (o tempo observado por caso, 170–303 s, ainda bate com a estimativa de ~6 min), mas invalida a suposição de que a rodada inteira herda o 44x depois do primeiro caso; a estimativa de tempo de qualquer rodada multi-pergunta pelo dsh deveria contar com isso, não com o "quase grátis" medido em `avalia_datasets.ts` (que chama o modelo direto, sem processo `dsh` novo por caso) |

Medido no conjunto inteiro (274 perguntas, Rodada 8): **91,2%** de recall de
dataset e **86,9%** de casos perfeitos, com **0** erro de execução. Os 97,8% da
tabela acima são do conjunto de 28 casos — números de réguas diferentes, não
comparáveis entre si.

## O laço e o reparo

| Regra | O que custou aprender | Travada em |
|---|---|---|
| Laço agêntico, não pipeline fixo | mesmas perguntas: **3/3** contra **0/3**. O fixo é 14x mais rápido e não serve | decidido; `laco.ts` sobrevive só como esqueleto do experimento DuckDB-NSQL ([`check-qwencoder-vs-duckdbnsql.md`](check-qwencoder-vs-duckdbnsql.md)) |
| Todo ganho de tempo tem que **preservar a capacidade de iterar** | as 3 falhas do pipeline fixo (573 em vez de 789; código `3550308` em vez de "São Paulo"; desistir após 4 rejeições) não são erro de SQL, são **erro de não iterar** | critério de aceite de qualquer otimização |
| O prompt de reparo reenvia o contexto inteiro | cada chamada é independente — o reparo não carregava pergunta, schema, pontes, a SQL rejeitada nem o motivo | `laco.ts`; no laço agêntico o contexto vem de graça |
| O modelo **não pode ter shell** | descobriu a ferramenta `bash` e consultou o DuckDB por fora do portão — validação inteira vira decoração | `dsh/rodado.patch.yml`; ✅ travado — `harness/patch.test.ts` ([`operacao.md`](operacao.md) tarefa 4) |
| Cálculo nomeado vem de `metrics.yaml`, nunca da cabeça do modelo | PIB per capita deu **23.704**; a métrica verificada dá **32.066** — nenhuma das duas dá erro | ferramenta `definicao_de_calculo`, `metricas.ts` |
| Menos ferramentas é escolha melhor, não só menos token | um 26B em q4 acerta mais entre 5 ferramentas do que entre 20 | corte de 14.213 → 6.849 tokens (−52%) |
| Tool call do Gemma nem sempre é reconhecido pelo parser do `llama-server` | medido 2026-09-03, rodada real do item 2 de `backlog.md` (a primeira vez que o laço encadeou muitas sessões `dsh` de verdade): 4 de 6 sessões terminaram com a chamada de ferramenta em formato NATIVO do Gemma (`<\|tool_call>call:nome{...}<tool_call\|>`, tags na ordem trocada) caindo como bloco de `reasoning` — texto solto, não executado — em vez de tool call reconhecido. Não é erro de raciocínio: o conteúdo (inclusive SQL) costuma estar correto | 🔴 aberto, bloqueador — item 10 do [`backlog.md`](backlog.md). `--no-jinja` testado e descartado (quebra o servidor inteiro pra este checkpoint); `--chat-template`/`--grammar` explícitos ainda não tentados |

## Medir — a régua também erra

Dois dos piores erros da série inteira estavam na **medição**, não no harness, e
os dois passaram despercebidos por rodadas.

| Regra | O que custou aprender | Travada em |
|---|---|---|
| O benchmark exige o **valor esperado**; RESPONDEU e CORRETO são colunas separadas | "não foram encontrados óbitos" era contado como acerto — **por um tempo eu otimizava contra uma medição quebrada** | `lote.ts` |
| Usar o conjunto inteiro, não o pedaço conveniente | eu usava **84 perguntas quando havia 274** — escolha de dataset não precisa de resposta conferida, só dos datasets citados | `casos.ts` |
| Erro de um caso não derruba a rodada | um `TimeoutError` derrubava a avaliação inteira | `lote.ts` — cada caso isolado, erro conta e a rodada segue |
| Desencontro de gabarito **não** se resolve por heurística | a numeração de `respostas.md` não batia com `perguntas.md` em 8 de 79; marcar suspeitos e deixar a correção para revisão humana levou de 71/8 a **81 confiáveis / 3 suspeitos** | `casos.ts` — o casador acusa, não reatribui |
| O parser do gabarito não pode engolir linha que não é dataset | a linha `chaves: id_municipio, sigla_uf` entrava como se fossem datasets: a 3ª e a 7ª "falha mais comum" eram **fantasma** | `casos.ts` |
| O espelho não é só `br_` | `resolveDataset` só tentava o prefixo `br_`; há `world_` e `us_` — `olympedia_olympics` contava como erro do modelo | `catalogo.ts` |
| Teste que aponta para dataset removido é vermelho por motivo bom | 3 testes quebraram quando `br_seeg`/`br_ibama_embargos` saíram do espelho — sinal correto, não ruído | `portao.test.ts` |
| Acerto de número se confere com **fronteira**, não com substring | `resposta.includes('789')` casa dentro de `1789`, e um `n=2022` casa com o ano da própria pergunta — falso positivo silencioso | 🔴 nada feito — item 0 do [`backlog.md`](backlog.md) |

**Os 2,5 pontos de ganho da Rodada 8 vieram da régua, não do modelo.** É a
terceira vez que consertar a medição rende mais que mexer no harness.

**Paralelismo não multiplica.** Com `-np 5` cada caso passou de ~2 s para ~12 s e
o total caiu só de 20,9 para 15,2 min (−27%): o modelo é limitado por CPU em 8
threads, e 5 requisições dividem o mesmo compute. O ganho vem do batch de decode
do llama.cpp, não de concorrência de verdade — vale usar, **não vale esperar 5x**,
e comparar tempo entre rodadas com `-np` diferente é comparar coisas distintas.

## Desfazer também é refino

Duas "melhorias" minhas que pioravam, e foram removidas:

- **Casamento de dataset por prefixo.** `br_seeg` e `br_seeg_emissoes` existiam
  os dois — o casamento trocaria uma escolha legítima por outra, calado. Hoje
  `resolveDataset` corrige **só grafia**. (O par sumiu depois: `br_seeg` e
  `br_ibama_embargos` **foram removidos do espelho**, e hoje caem na camada
  `tabela` do portão — desfecho melhor que ser desviado. A regra continua
  valendo; o que mudou foi o exemplo.)
- **KV quantizado** (`-ctk/-ctv q8_0`). Desquantizar a cada operação de atenção
  domina o que se economiza em banda: prefill **15,8 → 50,5 t/s** em CPU.
- **`--no-jinja`** (2026-09-03, testando a hipótese do item 10 de
  `backlog.md`). Quebra o servidor inteiro para este checkpoint do Gemma:
  toda chamada volta `{"error":{"message":"this custom template is not
  supported, try using --jinja"}}`. O template do modelo exige o motor jinja
  para qualquer coisa, não só para tool-calling — a hipótese era plausível
  (o parser genérico sem-jinja podia reconhecer melhor as tags nativas do
  Gemma) e o teste ao vivo matou ela em menos de um minuto. Revertido
  na hora; flag fica em `servidor.sh` (`NOJINJA=1`) só documentada como
  descartada.
- **`--temp 0`** (2026-09-03, mesma investigação). O llama-server tem default
  de **0,80** quando o cliente não manda `temperature` — hipótese: variância
  de amostragem explicava a falha probabilística do tool-call nativo do
  Gemma4 (item 10). Testado ao vivo: a MESMA pergunta bateu o MESMO bug, byte
  a byte, no mesmo turno — decodificação gulosa é determinística, então se o
  caminho de maior probabilidade passa pelo bug NESTE contexto, passa
  **sempre**. Pior que o padrão: com `temp=0,80` a variância real já foi
  observada recuperando os mesmos casos numa segunda tentativa; com `temp=0`
  a retentativa perderia essa saída. Revertido na hora; flag fica em
  `servidor.sh` (`TEMP=<n>`) só documentada como descartada.

## Tarefas — travar o que ainda é só disciplina

As 🔴 acima, em ordem de custo se voltarem a ser quebradas. Nenhuma feita.

### 1. `COUNT(*) AS n` e `n=0` no caminho agêntico ✅ fechado 2026-09-02

Feito no mesmo commit que a tarefa 6 de `backlog.md` (`26a73cb`), mas não
registrado aqui até 2026-09-03 (doc drift — o código chegou antes da nota).

**Fechado**: `checaAmostra` (camada 8 de `portao.ts`) rejeita, ANTES de
executar, toda estatística derivada (`AVG`, `MEDIAN`, `STDDEV`, `CORR`, razão
entre agregados) no SELECT final sem uma coluna chamada exatamente `n` — é
forma da consulta, não julgamento do número, então não há falso positivo
legítimo a proteger. `mcp.ts` (`consultar`) trata `n=0` como reparo: zero
linhas volta como erro de ferramenta com `faixasCitadas()` listando a faixa de
anos real das tabelas citadas, para o modelo saber se o zero é join errado ou
ano fora do intervalo disponível.

**Fecha quando** (verificado por teste, `portao.test.ts` "camada amostra"):
uma consulta agregada sem `n` explícito é rejeitada — `AVG(pib) AS media` sem
`COUNT(*) AS n` falha camada `amostra`; com ela, passa. Falta a verificação
ao vivo (rodar o caso "573 em vez de 789" pelo dsh de novo e confirmar que o
portão intercepta antes da prosa) — isso só existe depois do item 2 de
`backlog.md` rodar.

### 2. Few-shot independente do conjunto de teste ✅ fechado 2026-09-03

`harness/casos.test.ts` (novo) compara o texto de `exemplosIndependentes()`
contra `carregaTodasPerguntas()` pergunta a pergunta — não pelo caminho do
arquivo, pelo **conteúdo**, então pega o erro mesmo que alguém troque a fonte
por outra que acidentalmente se sobreponha ao teste.

**Fecha quando:** apontar a fonte de few-shot para o conjunto de teste quebra
o teste. Verificado ao vivo: redirecionando `exemplosIndependentes` para
`docs/perguntas.md` (a fonte do teste) em vez de `docs/relatorio-social/`, o
teste falha — nesse caso pelo formato (`docs/perguntas.md` não tem o padrão
`**Fontes:**` que o parser espera, então `exemplosIndependentes()` volta
vazio e o teste "não fica vazio" acusa; se algum dia o formato bater, é o
teste de sobreposição que pega).

### 3. Marca de etapa nos exemplos few-shot ✅ feito — `montaPrefixo()`

Está implementada e documentada no lugar certo: cada exemplo entra prefixado por
`ETAPA datasets`, e o bloco fecha com "os exemplos acima valem SÓ para a ETAPA
datasets". O comentário registra o sintoma medido — o modelo chegou a **ecoar
`ETAPA datasets` na resposta** porque todo exemplo do prefixo tinha essa forma.

**Fica de resto:** nenhum teste trava isso. Cabe no mesmo teste do item 2, que
já vai olhar a montagem do prefixo.

### 4. Registrar `-np` junto de todo tempo medido ✅ fechado (achado já feito 2026-09-03, não registrado até agora)

`acerto.ts` (`configServidor`, `rotuloConfig`, `avisaConfigDivergente`) e
`lote.ts` já implementam isto: toda `Rodada` grava `config` (lido de `/props`
do servidor) junto dos casos, e `lote.ts --diff a.json b.json` chama
`avisaConfigDivergente` — que emite o aviso exato pedido aqui quando `-np`,
`-c` ou o modelo diferem entre dois arquivos comparados.

**Fecha quando:** todo tempo registrado carrega o `-np` que o produziu (sim —
campo `config` em `Rodada`), e comparar rodadas com `-np` diferente aparece
como aviso (sim — `diff()` em `lote.ts` imprime `avisaConfigDivergente`).

## Os quatro que valem para o próximo

Se só quatro linhas deste arquivo sobrevivessem:

1. **Toda camada do portão nasce de um erro observado.** Nenhuma foi imaginada,
   e as duas que mais pegam vieram das duas primeiras SQLs do modelo.
2. **Medir a medição.** Dois erros meus estavam na régua: o benchmark premiando
   resposta errada, e 84 casos quando havia 274. Os dois passaram por rodadas.
3. **Config que "parece" aplicada não está.** `reasoningEfforts: false`,
   `--reasoning off` e `--dump-config` deram todos a impressão de resolver. Só o
   comportamento medido conta — ver [`operacao.md`](operacao.md).
4. **Desfazer também é refino.** O casamento por prefixo e o KV quantizado eram
   melhorias minhas que pioravam.

## Ver também

- [`operacao.md`](operacao.md) — as checagens de operação e as 6 tarefas de automatizá-las
- [`harness_gemma_dsh.md`](harness_gemma_dsh.md) — o plano (fases 0-5) e a lista "Falta"
- [`harness_bpe.md`](harness_bpe.md) — este arquivo é a semente do **Experience store** de lá; reindexá-lo por subsistema é o passo que o aproxima de um store consultável, já que experiência se recupera por situação, não por data
- [`../README.md`](../README.md) — o fluxo e os módulos
