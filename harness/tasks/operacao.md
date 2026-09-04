# Operar o harness — o que quebra calado, e o detector de cada coisa

> Aberto em 2026-09-02, a pedido, destilado do diário de experimentos original
> de 2026-09-01/02 (removido depois que tudo o que ele tinha de acionável
> virou este arquivo, [`regras.md`](regras.md)
> e [`../README.md`](../README.md)). Tudo abaixo foi **medido no beelink**;
> onde há estimativa está dito.

O harness não falha com exceção. Ele falha devolvendo número plausível, ou
ficando 7x mais lento sem nada no log. Cada checagem abaixo existe porque a
coisa já aconteceu.

Duas metades: as **checagens** (o que conferir hoje, à mão) e as **tarefas**
(tirar cada uma dessas checagens da cabeça de quem opera). O dado de que todas
precisam já está exposto — o que falta é alguém consultá-lo automaticamente.

## Antes de confiar numa rodada

| Checar | Como | Se falhar |
|---|---|---|
| O raciocínio está mesmo desligado | `servidor.sh aquece` (automatizado — reprova se a resposta trouxer `reasoning`/`<think`), ou turno de tool calling > ~10 s | ver "Raciocínio" abaixo — três configs *parecem* resolver e não resolvem |
| O cache de prefixo está vivo | `timings.prompt_n` na resposta do `llama-server`: deve ser ~o tamanho da pergunta, não o do prefixo | algo variável entrou no prefixo (timestamp, ordem não determinística de ferramenta). Perde-se o 44x sem nenhum sinal no resultado |
| `-c` é o que se pensa | `n_slots` no log de boot do `llama-server` | `-c` é **por slot**: com os 4 slots padrão, `-c 65536` aloca 4x o KV. `-np` sempre explícito |
| Concorrência do script bate com o `-np` real | `configServidor()` (`acerto.ts`) contra o que o script dispara — `avalia_datasets.ts` lê via `paraleloEfetivo()` | disparar mais requisições que slots não só enfileira à toa: **derruba a cache do slot em rodízio**. Medido 2026-09-02 — `PARALELO=5` contra `-np 1` pagou prefill do prefixo inteiro a cada 5º caso, 18,1 s/pergunta em vez de ~2,5 s. Ver `regras.md`, seção "Prefixo e few-shot" |
| O modelo não tem saída lateral | não se aplica mais por checagem — o Gemma descobriu a ferramenta `bash` uma vez e consultou o DuckDB por fora do portão. Hoje o laço (`agente.ts`) só oferece as 7 ferramentas do MCP; não existe `bash`/`fs`/`web` para desligar num config, porque nunca são construídas | — |
| A régua mede a coisa certa | rodada onde o esperado é conhecido, conferido por fora | duas vezes o erro estava na medição, não no harness (ver `regras.md`, "Os quatro que valem para o próximo", item 2) |

## Raciocínio: o que resolve e o que só parece resolver

Ordem de descoberta, porque as três primeiras custaram tempo:

| Tentativa | O que faz de verdade |
|---|---|
| Declarar o modelo como não-raciocinante do lado do CLIENTE (`reasoning: false` hoje, era `reasoningEfforts: false` no CLI agêntico antigo) | declara o modelo como não-raciocinante **só para quem está chamando**. Não manda nada ao llama.cpp — o modelo segue raciocinando |
| `--reasoning off` no `llama-server` | não resolve |
| `reasoningEfforts: off:` (sem valor) | **nem carrega** — o plugin recusa com "offers no level beyond off" |
| `--chat-template-kwargs '{"enable_thinking":false}'` | **é o que resolve.** 20,9 s → 4,7 s por turno, tool call intacto |

`--dump-config` **não pega** nenhuma das três primeiras: ele valida a composição
do patch, não o carregamento do plugin. Só o boot pega, e só o comportamento
medido confirma.

## Estabilidade do prefixo é restrição, não otimização

Medido, prefixo de 1.165 tokens: 1ª chamada 19,5 s, 2ª **0,44 s** (5 tokens
novos). Com os 43 exemplos few-shot o prefixo vai a ~11k e o prefill medido
continua em ~45 tokens — o few-shot é grátis **por pergunta**.

Consequência prática, que vale para qualquer mudança no prompt de sistema:

- Nada variável entra no prefixo. Timestamp, ordem de iteração de dicionário,
  contagem que muda a cada sync — qualquer um evapora o 44x.
- O detector é `timings.prompt_n`. Não existe outro: a resposta continua certa,
  só sete vezes mais lenta.
- Divisão treino/teste de few-shot é **por tema, não por caso**. Dentro de um
  tema as 5 perguntas são variações do mesmo cruzamento; dividir por caso deixa
  o vizinho quase-idêntico no prefixo e passa a medir memória.

## Contexto é o gargalo, não velocidade bruta

| | 2k de contexto | ~18k (dentro do laço) | ~25k |
|---|---|---|---|
| Prefill | 50,5 t/s | 15 t/s | pior |
| Geração | 13,3 t/s | 9 t/s | pior |

Cortar superfície de ferramenta é, por isso, ganho duplo: menos tokens **e**
escolha melhor — um 26B em q4 acerta mais entre 5 ferramentas do que entre 20.
O corte medido (14.213 → 6.849 tokens de system prompt, −52%) rendeu suicídios
RJ 645 → 490 s e PIB per capita MG 504 → 293 s, com a correção intacta.

**Ao adicionar ferramenta nova ao harness, o custo não é o token dela — é a
diluição.** Só entra ferramenta que resolve uma classe de erro observada.

## MCP é o transporte, não o custo nem o benefício

O primeiro teste de tool calling não usou MCP nenhum e funcionou; o protocolo
custa milissegundos contra turnos de 20 s. O que o MCP entrega, e o que
justifica mantê-lo, são duas coisas só: **o portão como ferramenta** (a rejeição
volta ao modelo como resultado de tool call, então o reparo é do laço e não
código nosso — foi assim que 726 virou 789) e o log auditável.

Corolário: se algum dia o MCP sair do caminho por outro motivo, essas duas
propriedades têm que sobreviver à troca, ou a troca não vale.

## Convivência — o que custou tempo fora do código

- **O hook do `rtk` trunca a saída do git, calado.** `git add harness/` seguido
  de `git diff --cached --name-only` listou 2 arquivos; eram 9, e o commit levou
  os 9. `git show --stat` repetiu a mentira. É exatamente o comando que a regra
  do projeto manda usar para conferir staging, e ele erra na direção
  tranquilizadora. Conferir com `git ls-files`, `git ls-tree -r HEAD --name-only`
  ou `rtk proxy git <cmd>`.
- **Duas sessões no mesmo branch se atropelam.** Um merge de `harness-gemma` em
  `main` feito por outra sessão engoliu um commit sem aviso. Protocolo que
  funcionou depois: **um dono por diretório, e avisar antes de qualquer
  merge/push para `main`** — mesmo mudança pequena fora de `harness/`.

## Tarefas — tirar as checagens acima da cabeça de quem opera

Toda checagem da primeira tabela é hoje **manual e por inspeção de log**. Cada
uma delas já falhou em silêncio pelo menos uma vez, e todas são baratas de
automatizar — o dado já está exposto, só ninguém o consulta. Nenhuma depende da
Fase 4 fechar; a 2 já foi feita por outra sessão, as demais não.

### 1. Asserção de cache de prefixo no `lote.ts` ✅ feito — `harness/acerto.ts`

`modelo.ts` já devolvia `prefilados` (o `timings.prompt_n`) em toda chamada e
nenhum consumidor olhava. `acerto.ts` centraliza a checagem (`avisaPrefill`,
`LIMIAR_PREFILL=2000`) e `lote.ts`/`compara.ts` agora chamam depois de cada
caso — `lote.ts` lê o prefill de fora, do log do `llama-server`
(`prefillsDesde`/`marcaDoLog`), porque a API unificada entre providers que
`agente.ts` usa (`pi-ai`) não expõe o `timings.prompt_n` específico do
llama.cpp; `compara.ts` já roda no mesmo processo e usa o valor direto.

**Fecha quando** (verificado por teste, não por rodada ao vivo): uma mudança
deliberada no prefixo faz a rodada acusar em vez de só demorar mais —
`acerto.test.ts` simula exatamente isso (`avisaPrefill([97, 6849])` acusa o
prefill do tamanho do prefixo). Falta a verificação ao vivo: inserir um
timestamp de propósito no prefixo e confirmar que uma rodada real acusa, não
só o teste unitário.

### 2. Invariantes de boot ✅ feito — `harness/servidor.sh`

Resolvido por outra sessão em `f8a7033`, e por um motivo pior do que o que eu
tinha previsto: reiniciar o servidor à mão falhou **três vezes seguidas do mesmo
jeito** — o processo antigo ainda segura a porta, o novo morre com
"couldn't bind" em silêncio, **o antigo segue servindo com a config velha**, e a
medição seguinte sai errada sem aviso.

O script sobe com a config medida (`-t 8`, `--chat-template-kwargs`, KV em f16),
espera a **porta** liberar — não o processo sumir, porque é o bind que falha — e
**confere `n_slots`/`n_ctx_slot` contra o que foi pedido**, saindo com erro se
divergir. `./harness/servidor.sh status` informa o que está no ar.

**Fica de resto — fechado 2026-09-03:** `confereBoot()` (`acerto.ts`) chama
`servidor.sh aquece` e agora roda no começo de `lote.ts`/`compara.ts`, antes
de gastar tempo com um servidor mal configurado — a rodada aborta se o
raciocínio estiver ligado ou o servidor não responder. Verificado ao vivo
contra o servidor no ar: `456 ms (limiar 10000), cache_n=51`, aprovado.

### 3. Detector de raciocínio ligado, junto do aquecimento ✅ feito — `harness/servidor.sh aquece`

`servidor.sh` **passava** a flag certa, mas ninguém conferia que ela **fez
efeito** — e essa distinção é exatamente o modo de falha desta config (ver a
tabela do raciocínio acima).

Dois turnos idênticos logo depois do `/health` (o primeiro paga o prefill
frio, o segundo mede regime): reprova se a resposta trouxer campo de
`reasoning`/`<think`, ou se o turno passar do limiar medido (10.000 ms —
2.140 ms frio, 530 ms quente contra 20,9 s com raciocínio ligado). De brinde,
acusa `cache_n=0` no segundo turno como prefixo instável. Chamado
automaticamente no fim de `servidor.sh` (sem argumento) e disponível avulso
via `servidor.sh aquece`.

**Verificado ao vivo em 2026-09-02** contra o servidor no ar: 470 ms,
`cache_n=51`, aprovado. **Não verificado**: o outro lado do "fecha quando"
original (trocar a flag por `--reasoning off` e confirmar que o detector
recusa) — exigiria reiniciar o servidor com a config ruim de propósito, e
isso não foi feito ainda.

### 4. Travar a superfície de ferramenta ✅ fechado 2026-09-03 — mecanismo trocado depois

Original: o CLI agêntico usado então trazia `bash`/`fs`/`subagent`/etc.
disponíveis por padrão, e um teste (`harness/patch.test.ts`, lendo o YAML de
config daquele CLI) travava as 19 entradas em `disabled: true`, conferindo que
`mcp-rodado` (o caminho pelo portão) não estava entre elas.

**Superado, não só fechado**, quando esse CLI foi trocado por `agente.ts`: o
laço agêntico próprio nunca constrói `bash`/`fs`/`subagent` — as únicas
ferramentas que existem para o modelo são as que `client.listTools()` devolve
do servidor MCP (`mcp.ts`, hoje 7). Não há mais config para reabilitar por
engano, então não há mais o que travar por YAML; `harness/agente.test.ts`
(sucessor de `patch.test.ts`) trava outra coisa — a persona e os valores do
modelo — que é o que ainda pode regredir calado.

### 5. Varredura `Substitui \`X\`` → aposentar X ✅ fechado 2026-09-03

`br_ibama_embargos` tem 497 mil linhas, `status='done'` e valores vazios:
responde zero, e o zero passa por "não há embargos" em vez de "não há dado". O
único sinal no espelho é a nota do dataset que o substituiu — o que dá o
**mecanismo geral**, não só os dois casos já conhecidos.

- **Onde:** varrer `provenance_notes` de `_rodado_metadata` por ``Substitui `X` ``
  e propor `X` para aposentadoria.
- **Fechado desde então:** `br_ibama_embargos` e `br_seeg` **foram removidos do
  espelho**. Hoje caem na camada `tabela` do portão — desfecho melhor do que ser
  desviado para o vizinho. A camada `inservivel` segue guardando as duas tabelas
  vazias que restam. Plano original em
  [`../../tasks/done/higiene_espelho.md`](../../tasks/done/higiene_espelho.md)
  (arquivado — os 4 itens do plano foram concluídos em 2026-09-02).
- **Varredura geral feita 2026-09-03**: `SELECT ... WHERE provenance_notes
  ILIKE '%Substitui \`%'` no beelink devolve só as 8 tabelas de
  `br_ibama_embargos_novo` citando o `br_ibama_embargos` já removido — nenhum
  candidato novo. Uma segunda varredura mais larga (`substitui`, `redundante`,
  `obsoleto`, `aposentad`) achou só `br_transferegov_siconv`, e a nota lá é
  sobre um **zip pulado dentro do mesmo dataset** (`siconv.zip`, consolidado
  redundante das próprias tabelas), não uma tabela-irmã para aposentar — não é
  o padrão que este mecanismo procura. **Sem candidato pendente hoje.**

## Aberto — não é ops

- **Codificação do domínio é onde o modelo ainda erra plausível** — CID sem
  ponto, `coded_differently` (`sexo`, `raca_cor`, `estado_civil`). O portão pega
  os casos conhecidos; casos novos aparecem um a um, e cada um vira camada.
- O que fazer a seguir no harness em si — escolha de dataset, prosa, contexto —
  está em [`backlog.md`](backlog.md), ordenado por retorno medido.

## Ver também

- [`../README.md`](../README.md) — o fluxo, os módulos, como rodar
- [`regras.md`](regras.md) — as regras que cada medição gerou, por subsistema
- [`backlog.md`](backlog.md) — o que fazer a seguir no harness, por retorno medido
- [`harness_gemma_agente.md`](harness_gemma_agente.md) — o plano original, para comparar com o que saiu
- [`../../gemma_stats.md`](../../gemma_stats.md) — o benchmark do modelo isolado
