# Operar o harness — o que quebra calado, e o detector de cada coisa

> Aberto em 2026-09-02, a pedido, destilado do diário de experimentos de
> 2026-09-01/02 (`exp/harness-gemma-dsh.md`, removido depois que tudo o que
> ele tinha de acionável virou este arquivo, [`enhance-harness.md`](enhance-harness.md)
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
| O raciocínio está mesmo desligado | `reasoning-chunks` no log de sessão do dsh, ou turno de tool calling > ~10 s | ver "Raciocínio" abaixo — três configs *parecem* resolver e não resolvem |
| O cache de prefixo está vivo | `timings.prompt_n` na resposta do `llama-server`: deve ser ~o tamanho da pergunta, não o do prefixo | algo variável entrou no prefixo (timestamp, ordem não determinística de ferramenta). Perde-se o 44x sem nenhum sinal no resultado |
| `-c` é o que se pensa | `n_slots` no log de boot do `llama-server` | `-c` é **por slot**: com os 4 slots padrão, `-c 65536` aloca 4x o KV. `-np` sempre explícito |
| O modelo não tem saída lateral | grep por `bash`/`ssh` no trace da sessão | o Gemma descobriu a ferramenta `bash` e consultou o DuckDB por fora do portão — todo o portão vira decoração. Lista de ferramentas desligadas em [`../dsh/rodado.patch.yml`](../dsh/rodado.patch.yml) |
| A régua mede a coisa certa | rodada onde o esperado é conhecido, conferido por fora | duas vezes o erro estava na medição, não no harness (ver `enhance-harness.md`, "Padrões", item 2) |

## Raciocínio: o que resolve e o que só parece resolver

Ordem de descoberta, porque as três primeiras custaram tempo:

| Tentativa | O que faz de verdade |
|---|---|
| `reasoningEfforts: false` no dsh | declara o modelo como não-raciocinante **para o harness**. Não manda nada ao llama.cpp — o modelo segue raciocinando |
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
automatizar — o dado já está exposto, só ninguém o consulta. Nada abaixo foi
feito; nenhuma depende da Fase 4 fechar.

### 1. Asserção de cache de prefixo no `lote.ts` 🔴 nada feito

`modelo.ts:58` já devolve `prefilados` (o `timings.prompt_n`) em toda chamada, e
**nenhum consumidor olha**. Uma rodada com o prefixo quebrado continua correta e
fica ~7x mais lenta — passa por "o beelink hoje está pesado".

- **Onde:** `lote.ts` e `compara.ts`, no ponto onde já acumulam tempo por caso.
- **O quê:** depois do caso de aquecimento, reprovar (ou pelo menos berrar) se
  `prefilados` de qualquer caso for maior que a ordem de grandeza da pergunta.
- **Fecha quando:** uma mudança deliberada no prefixo (inserir um timestamp)
  faz a rodada acusar, em vez de só demorar mais.

### 2. `checa_servidor.ts` — as quatro invariantes de boot 🔴 nada feito

`-t 8`, `-np 1`, sem `-ctk/-ctv q8_0`, e `--chat-template-kwargs`. As quatro
vivem em prosa no [`../README.md`](../README.md) e **as quatro já foram
esquecidas uma vez**, cada uma custando entre 30% e 3x. Um `llama-server`
reiniciado à mão sem a linha inteira é o caminho normal para isso acontecer de
novo.

- **Onde:** script novo em `harness/`, chamado no começo de `lote.ts`/`compara.ts`.
- **O quê:** ler `/props` do servidor (ou o log de boot) e comparar com as
  invariantes; recusar a rodada com a diferença nomeada.
- **Fecha quando:** subir o servidor sem `-np 1` aborta a rodada em vez de
  produzir números 4x mais caros em KV.

### 3. Detector de raciocínio ligado, junto do aquecimento 🔴 nada feito

Hoje o único sinal é notar `reasoning-chunks` no log ou estranhar um turno de
20 s. É a config que mais vezes *pareceu* aplicada sem estar (ver a tabela do
raciocínio acima) e a que `--dump-config` não pega.

- **Onde:** mesmo script do item 2 — a chamada de aquecimento já existe por
  outro motivo, então é grátis.
- **O quê:** reprovar se a resposta trouxer campo de reasoning, ou se o turno
  de aquecimento passar do limiar medido (~10 s).
- **Fecha quando:** trocar `--chat-template-kwargs` por `--reasoning off` faz o
  harness recusar rodar.

### 4. Travar a superfície de ferramenta 🔴 nada feito

O corte de 14.213 → 6.849 tokens é edição manual em
[`../dsh/rodado.patch.yml`](../dsh/rodado.patch.yml). Nada impede a lista de
voltar a crescer — e uma das ferramentas desligadas (`bash`) não era peso, era
**buraco no portão**: o modelo consultava o DuckDB por fora.

- **Onde:** teste em `harness/`, ao lado de `portao.test.ts`.
- **O quê:** travar o conjunto de ferramentas habilitadas e o tamanho do prompt
  de sistema; qualquer acréscimo tem que ser deliberado e justificado no diff.
- **Fecha quando:** reabilitar `bash` no patch quebra o teste.

### 5. Varredura `Substitui \`X\`` → aposentar X 🟡 casos conhecidos mapeados

`br_ibama_embargos` tem 497 mil linhas, `status='done'` e valores vazios:
responde zero, e o zero passa por "não há embargos" em vez de "não há dado". O
único sinal no espelho é a nota do dataset que o substituiu — o que dá o
**mecanismo geral**, não só os dois casos já conhecidos.

- **Onde:** varrer `provenance_notes` de `_rodado_metadata` por ``Substitui `X` ``
  e propor `X` para aposentadoria.
- **Já feito:** o portão bloqueia os dois casos conhecidos localmente; o plano
  de execução deles está em [`../../tasks/higiene_espelho.md`](../../tasks/higiene_espelho.md).
- **Falta:** a varredura geral, e mudar o `status` em `_rodado_metadata` — que é
  **estado compartilhado**, então combinar antes de mexer.

### 6. Prosa citar o órgão, não a tabela 🔴 nada feito

As respostas mencionam `br_ibge_pib.municipio`; a convenção de
`pages/analises/results/` é citar o **órgão de origem**, nunca a tabela nem a
ferramenta. É ops de saída: hoje nenhum relatório gerado sai publicável sem
edição à mão.

- **Onde:** passo 9 do fluxo (a redação), no prompt.
- **Fecha quando:** uma amostra de respostas passa sem nome de tabela, mantendo
  a proveniência legível.

## Aberto — não é ops

- **Codificação do domínio é onde o modelo ainda erra plausível** — CID sem
  ponto, `coded_differently` (`sexo`, `raca_cor`, `estado_civil`). O portão pega
  os casos conhecidos; casos novos aparecem um a um, e cada um vira camada.
- A taxa de acerto ponta a ponta nos casos com `n` conferido fora do prefixo —
  o número que responde ao objetivo. Contagem corrente e método em
  [`enhance-harness.md`](enhance-harness.md), "Aberto"; é o item 1 de "Falta" em
  [`harness_gemma_dsh.md`](harness_gemma_dsh.md).

## Ver também

- [`../README.md`](../README.md) — o fluxo, os módulos, como rodar
- [`enhance-harness.md`](enhance-harness.md) — uma linha por medição, na ordem das rodadas
- [`harness_gemma_dsh.md`](harness_gemma_dsh.md) — o plano original, para comparar com o que saiu
- [`../../gemma_stats.md`](../../gemma_stats.md) — o benchmark do modelo isolado
