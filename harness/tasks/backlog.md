# Backlog do harness — em ordem de retorno medido

> Movido em 2026-09-02 da seção "O que fazer a seguir" de `enhance-harness.md`
> (dissolvido; as regras dele estão em [`regras.md`](regras.md)). **Cada item
> sai de uma falha medida, não de intuição** — a ordem é por quanto cada um
> devolve, e é isso que o torna útil: quem pegar o harness sabe onde começar sem
> reconstruir o raciocínio.

Base de medição: Rodada 8, as **274 perguntas** inteiras, com exemplos few-shot
de fonte independente. Recall de dataset **91,2%**, casos perfeitos **86,9%**,
**0** erro de execução. Sobraram **36 falhas** — é a elas que a ordem abaixo
responde.

Tarefas de *operação* (config do servidor, detectores de falha silenciosa) não
estão aqui, estão em [`operacao.md`](operacao.md). Regras que ainda são só
disciplina, em [`regras.md`](regras.md).

**Esta é a única fila de próximos passos do harness.** A lista "Falta" de
`harness_gemma_dsh.md` foi migrada para cá (itens 6-8) justamente por manter uma
segunda fila, com contagem desatualizada, competindo com esta.

---

## 0. Consertar a régua do `correto` — **antes do item 2** ✅ fechado 2026-09-02

Achado ao auditar o backlog contra o código, 2026-09-02. **Não estava na lista, e
bloqueia o item 2.**

**Fechado**: `harness/acerto.ts` unifica a régua (fronteira de número, não
substring) e `lote.ts`/`compara.ts` foram trocados para usá-la —
`acerto.test.ts` trava o próprio caso do "fecha quando" abaixo. O item 2 pode
rodar contra ela agora.

A const `correto` em `lote.ts` (dentro de `roda()`) e o helper `bate()` em
`compara.ts` decidem se a resposta está certa por
**substring de dígitos**:

```ts
resposta.replace(/[.\s]/g, "").includes(esperado.replace(/[.\s]/g, ""))
```

Isso casa `789` dentro de `1789`, e um `n=2022` casa com o **ano escrito na
própria pergunta**. É falso positivo silencioso — exatamente a classe que já
mordeu duas vezes ("o benchmark contava resposta errada como acerto", "84 casos
quando havia 274"), e as duas passaram despercebidas por rodadas.

**Por que agora:** o item 2 são **3,2 h** de rodada contra essa régua. Consertar
depois significa jogar as 3,2 h fora ou, pior, publicar o número.

- **Ação:** comparar número com fronteira (não substring), e **unificar** — a
  régua está copiada em dois arquivos, então consertar um e esquecer o outro é o
  desfecho provável.
- **Fecha quando:** um caso com `n=789` cuja resposta contenha só `1789` é
  contado como erro.

## 1. Desambiguar dataset irmão — **24 das 36 falhas** ✅ medido 2026-09-02 — funcionou

A maior classe de longe, e sempre a mesma forma: o modelo escolhe o parente
errado porque **os nomes não distinguem**. Nome semântico separa domínio, não
separa irmão.

| Pediu | Deu |
|---|---|
| `ibge_ppm` (pecuária municipal) | `ibge_pam` (agrícola municipal) |
| `anp_combustiveis` | `anp_precos_combustiveis` |
| `me_caged` | `me_rais` |
| `tesouro_capag` | `firjan_ifgf`, `me_siconfi` |

**Ação:** uma linha de descrição por dataset no catálogo do prefixo, **só onde
há ambiguidade** — ~40 tokens por par, não as `provenance_notes` inteiras (76%
boilerplate, descartadas na Rodada 3 por isso mesmo).

**Como medir se valeu:** a classe `vizinho` tem que cair. **Se cair e a
`nada_perto` subir, a descrição está confundindo em vez de esclarecer** — esse é
o teste que separa ganho real de troca de erro.

**Feito**: `harness/desambigua.ts` detecta os pares por regra sobre
`listaDatasets()`, `harness/dados/desambiguacao.json` traz a frase contrastiva
(mais os `grupos_semanticos` que nenhuma regra de string pega), e
`prefixo.ts` gruda a pista na linha do `CATÁLOGO` só dos datasets ambíguos —
`prefixo.test.ts` tranca a regra de entrada do JSON.

**Medido**: achado no meio do caminho — `avalia_datasets.ts` tinha sua
PRÓPRIA cópia do catálogo, sem a pista nenhuma; teria medido a régua de
antes do conserto (corrigido, commit separado, antes de rodar). Com o
conserto de verdade em vigor, rodada completa contra as 284 perguntas de
`perguntas.md` (cresceu de 274; `HARNESS_PARALELO=1` — ver a nota de
`operacao.md` sobre `-np` real vs. concorrência do script):

| | antes (Rodada 8, 274 perguntas) | depois (2026-09-02, 284 perguntas) |
|---|---|---|
| RECALL (datasets obrigatórios) | 91,2% | **93,9%** |
| CASOS PERFEITOS | 86,9% | **90,5%** |
| falhas `vizinho` | 24 | **18** |
| falhas `nada_perto` | (dentro das 12 não-vizinho) | 9 — não subiu, o teste do parágrafo acima passa |

Não é 24→0: `ibge_pib` sozinho ainda perde 4x contra `ibge_pam`/`bcb_sicor`/
`inpe_prodes`/`sfb_sicar` — datasets de domínios genuinamente diferentes que
só compartilham o prefixo `ibge`/mesmo tema agrícola-fundiário, então a
ressalva do classificador (próximo parágrafo) provavelmente conta parte
disso como falso "vizinho". `anp_combustiveis` também ainda perdeu 1x apesar
da descrição já existir — caso a acompanhar, não a investigar agora.

Achado de bônus: `cnpq_bolsas` perdeu 3x (classe `nada_perto`, não
`vizinho` — o classificador só compara o primeiro segmento do nome, e
`cnpq`≠`capes`) contra `capes_bolsas`. Não estava no JSON; adicionado como
novo `grupo_semantico` (`bolsas_de_pesquisa`) no mesmo commit desta medição,
mas **ainda não remedido** — entra na próxima rodada.

A taxonomia que mede está na função `classe()` de `avalia_datasets.ts`. Uma ressalva na leitura do número: o classificador
`vizinho` compara só o **primeiro segmento** do nome (`d.split("_")[0]`), então
agrupa por **órgão**, não por irmão de verdade — `me_caged`↔`me_rais` cai na
mesma classe que `ibge_ppm`↔`ibge_pam`. A classe cair é sinal bom, mas mistura
duas confusões diferentes.

**Custo do prefixo:** a descrição entra no prefixo estável, então é grátis por
pergunta — mas conta para o gargalo de contexto (item 4). Só onde há par
ambíguo.

## 2. Rodar o laço nos casos com `n` conferido 🟡 rodada em andamento 2026-09-03 (4ª tentativa, amostra de 20/58) — ver item 10

O número que responde ao objetivo do harness, e **o único ainda não medido**.
Tudo o que existe hoje mede *escolha de dataset*, não resposta ponta a ponta.

- A contagem cresceu desde que este item foi escrito: eram 32, `bun harness/casos.ts`
  reporta **58** em 2026-09-02 (mais casos com `n` conferido entraram desde
  então). A ~6 min por pergunta isso é **~5,8 h**, não as 3,2 h originais —
  conferir a contagem de novo antes de estimar o tempo da rodada.
- Ferramenta pronta: `bun harness/pergunte.ts "<pergunta>"` já roda o caminho
  agêntico (testado: 789 com a decomposição por sexo correta, 5,9 min).

**A ponte de 5 linhas está feita**: `casos.ts --tsv` (função `tsvComN()`)
emite o TSV `pergunta <TAB> esperado` que `lote.ts` lê —
`bun harness/casos.ts --tsv > /tmp/casos.tsv && bun harness/lote.ts /tmp/casos.tsv`.

**1ª tentativa: 2026-09-03 00:19, abortada no caso 6/58.** As invariantes de
`operacao.md` estavam ok (`confereBoot()` aprovou, `-np 1 -c 32768` confirmado).
0/6 casos corretos — mas **4 dos 6 não são falha de raciocínio, são a chamada
de ferramenta caindo como texto solto** por causa de um bug de parsing só
agora exposto porque é a primeira vez que o laço roda tantas sessões `dsh`
reais em sequência. Detalhe completo, causa provável e o workaround: **item
10**, abaixo.

**2ª tentativa: 2026-09-03 09:11**, com o workaround de retentativa no ar —
interrompida de propósito no caso 3/58 pra testar `TEMP=0` (ver item 10);
2 casos completos (`respondeu` 100%, `correto` 0/2 por raciocínio, não bug).

**3ª tentativa: 2026-09-03 10:07**, `temp` revertido ao default (0,80) depois
do teste de `TEMP=0` sair pior — **interrompida a pedido no caso 6/58**. Os
5 casos completos mostraram o custo real da retentativa: ritmo caindo de
~24 min/caso pra **~36 min/caso** (5 casos, 10.850 s = ~3 h), com um caso
(5/58) gastando **85 min em 3 tentativas e voltando vazio mesmo assim** —
extrapolado, ~30+ h pras 58, contra a estimativa original de 5,8 h. RESPONDEU
4/5 mesmo com o bug (bom sinal do workaround), CORRETO 0/5 (nenhum bateu o
número, todos por raciocínio — nenhum dos 5 caiu no bug depois de recuperado).

**4ª tentativa: 2026-09-03 ~13:10**, amostra menor a pedido — **20 dos 58
casos** (`awk 'NR % 3 == 1' /tmp/casos.tsv`, um a cada 3 pra manter
diversidade temática em vez dos primeiros 20 corridos), pra ter um número de
correção utilizável sem esperar 30 h. Os 58 completos ficam pra depois do
item 10/11 resolver de verdade. Em background — rodando.

## 3. A prosa cita a ferramenta, não o órgão ✅ fechado 2026-09-03

As respostas mencionam `br_ibge_pib.municipio`. A convenção de
`pages/analises/results/` é citar o **órgão de origem** — nunca a tabela, nunca o
SQL. Hoje nenhuma resposta gerada sai publicável sem edição à mão.

**Conserto (duas metades):** instrução na etapa de prosa, **mais** uma checagem
que rejeite resposta contendo `br_[a-z_]+\.` — a instrução sozinha é do tipo que
o modelo obedece na maioria das vezes, e a checagem transforma "maioria" em
todas.

**Fechado.** Metade 1: `system-prompt` (persona) em `dsh/rodado.patch.yml`
instrui citar o órgão, nunca tabela/dataset/SQL. Metade 2: `checaCitacaoTabela`
(`portao.ts`) roda como ferramenta MCP nova, `revisar_resposta` (`mcp.ts`) — o
modelo é instruído a chamá-la com o parágrafo pronto antes de responder, e a
rejeição volta como resultado de ferramenta (mesmo mecanismo do portão de
SQL). Testado em `portao.test.ts` (3 casos: cita `br_x.y`, cita `world_x.y`,
prosa limpa passa).

**Verificado ao vivo** (`bun harness/pergunte.ts "Quantos óbitos por suicídio
houve no RJ em 2020?"`, 5,5 min): resposta final — "Em 2020, houve 749 óbitos
por suicídio no estado do Rio de Janeiro, de acordo com dados do Ministério
da Saúde/SIM." Citação funcionou (chamou `revisar_resposta`, órgão citado,
nenhum `br_x.y` na prosa). **O número não bate com o caso canônico (789)** —
achado à parte, documentado no item 9 abaixo: desta vez o modelo usou
`circunstancia_obito` em vez de `causa_basica`/CID, um campo que subconta.

## 4. Encurtar mais o contexto 🔴

O prompt do dsh está em **6.849** tokens (era 14.213). O throughput cai ~3x entre
2k e 18k, então cada corte se paga duas vezes — em tempo e em qualidade de
escolha (um 26B em q4 acerta mais entre 5 ferramentas que entre 20).

**Falta examinar** quanto das ferramentas restantes é descrição que o modelo não
usa. Tensão real com o item 1, que **adiciona** tokens ao prefixo: os dois
disputam o mesmo orçamento, e o item 1 tem retorno medido enquanto este é
especulativo. Fazer o 1 primeiro.

**Item 1 feito (2026-09-02) — ainda não retomado.** Examinar "o que o modelo
não usa" exige transcrição real de sessão agêntica, que só existe depois do
item 2 rodar (o laço via dsh, não a escolha de dataset isolada). Continua
adiado, mas agora pelo motivo certo — falta o dado, não falta prioridade.

## 5. Seis datasets concentram 20 das 38 perdas ✅ diagnosticado 2026-09-02, após o item 1

`ibge_ppm` (4x), `ms_sinan_violencia` (4x), `ibge_pib` (3x),
`inep_avaliacao_alfabetizacao` (3x), `mp_pep` (3x), `ms_atencao_basica` (3x).

**Era diagnóstico antes de ação:** se for sempre a mesma confusão de irmão, o
item 1 resolve e este some junto. Se for nome opaco, o dataset precisa de
alias — que é outro conserto. Conferir depois do item 1, não antes.

**Diagnosticado, com a lista dos 6 originais confrontada contra a rodada
pós-item-1 (284 perguntas):**

| Original | Hoje |
|---|---|
| `ibge_ppm` 4x | **0x** — resolvido pela descrição contrastiva |
| `ms_sinan_violencia` 4x | **0x** — some da lista; `ms_sinan` (sem `_violencia`) aparece 3x, caso distinto |
| `mp_pep` 3x | **0x** — resolvido |
| `ms_atencao_basica` 3x | **0x** — resolvido |
| `inep_avaliacao_alfabetizacao` 3x | **0x** — resolvido |
| `ibge_pib` 3x | **4x** — não resolvido, piorou 1 caso |

Cinco dos seis eram exatamente "sempre a mesma confusão de irmão" — o item 1
resolveu e eles somem, como a hipótese previa. `ibge_pib` é o contraexemplo:
não é um par, é um ímã. Perde contra `bcb_sicor`, `ibge_pam`, `ibge_ppm`,
`inpe_prodes`, `sfb_sicar` — cinco datasets de domínios genuinamente
diferentes (crédito rural, agropecuária, desmatamento, cadastro rural), sem
nada em comum além de aparecerem em perguntas sobre município. A descrição
contrastiva já existe (`financas_municipais`) e não ajuda porque o problema
não é confundir PIB com outra coisa — é o modelo **incluir** PIB como apoio
em perguntas que não pedem produto econômico. Isso não é o defeito que a
descrição contrastiva resolve; é mais parecido com o modelo usar PIB como
palpite genérico de "algo econômico municipal". Sem conserto óbvio de
catálogo — fica em aberto, não é mais prioridade de fila (a classe que
motivou o item já foi resolvida 5 de 6).

Achado à parte, fora da lista original: `cnpq_bolsas` (3x) entrou no top-10
novo — não é dataset repetido da lista de 2026-09-01, é falha nova exposta
pela medição fresca. Já endereçado no item 1 (grupo `bolsas_de_pesquisa`),
remedição pendente.

## 9. `circunstancia_obito` subconta suicídio contra `causa_basica` (CID) 🟡 achado 2026-09-03, alerta feito — sem verificação ao vivo

Achado testando o item 3 (não procurado — apareceu na primeira pergunta
rodada depois do conserto). O caso canônico de suicídio RJ 2020 (789, o
número que sustenta a camada 6 do portão) voltou **749** — sem erro, sem
rejeição do portão, prosa corretamente citando "Ministério da Saúde/SIM" (o
item 3 funcionou). O modelo não usou `causa_basica`/CID desta vez: explorou
`br_ms_sim.dicionario`, achou `circunstancia_obito` (campo já decodificado,
"Suicídio" em vez de um código CID) e filtrou por ele.

**Medido no beelink, RJ 2020:**

| Filtro | n |
|---|---|
| `substr(causa_basica,1,3) BETWEEN 'X60' AND 'X84'` (CID-10) | **789** |
| `circunstancia_obito = '2'` ("Suicídio") | **749** |
| interseção | 749 — `circunstancia_obito='2'` é subconjunto estrito do CID |
| CID diz suicídio, `circunstancia_obito` diz outra coisa | **40** |

`circunstancia_obito` está sub-preenchido em 40 dos 789 óbitos por suicídio
reais — não é erro de sintaxe (como o `BETWEEN` cru que motivou a camada 6),
é um **segundo campo, plausível e mais fácil de achar** (decodificado via
`dicionario`, enquanto CID exige saber a convenção X60-X84), que dá número
menor e igualmente crível. É exatamente a classe que a camada 6 existe para
pegar, só que num campo que a camada 6 não olha — `CODIFICADAS` cobre `sexo`,
`raca_cor`, `estado_civil`, não `circunstancia_obito`.

**Por que não virou camada agora:** um caso medido é a barra que este projeto
já usa para as duas camadas centrais (partição, CID cru) — mas as duas eram
erro de *sintaxe* (portão vê a SQL e decide sem precisar saber estatística
médica). Aqui a SQL é sintaticamente perfeita nas duas versões; a camada
teria que saber que **CID é a fonte mais completa para causa de óbito no SIM**,
que é conhecimento de domínio específico, não um padrão sintático. Rejeitar
duro seria arriscado sem medir outros datasets/causas primeiro (mesma
disciplina do item 7: alerta primeiro, reparo depois de provado).

**Feito, mesma sessão:** `alertasDeSanidade` (`portao.ts`) avisa — não rejeita
— quando a SQL usa `circunstancia_obito` sem `causa_basica` junto, citando o
749×789 medido. Mesmo padrão não-bloqueante do item 7: volta grudado no
resultado da ferramenta `consultar`, o modelo vê antes de escrever a prosa.
Coberto por `portao.test.ts` (3 casos: avisa sozinho, cala com `causa_basica`
junto, cala quando a coluna nem aparece).

**Falta:** verificação ao vivo — rodar a mesma pergunta de novo pelo dsh e
confirmar que o modelo, vendo o alerta, troca para `causa_basica` e chega em
789. Não feito ainda porque custaria outro turno de ~5 min só para isso;
qualquer caso do item 2 que toque `br_ms_sim` serve de verificação de graça.
Cruza com o mecanismo de `coded_differently`/`false_friends` de
`bridges.yaml`, mas não é bem o mesmo formato (não é "duas tabelas discordam
do código", é "dois campos da MESMA tabela respondem à mesma pergunta com
cobertura diferente") — por isso virou alerta ad-hoc em vez de entrada no
YAML.

## 10. Tool call cai como texto solto — bloqueia o item 2 🟡 achado 2026-09-03 — causa provável entendida, workaround feito, causa raiz não corrigida

**O achado mais caro desta sessão.** A rodada do item 2 (58 casos pelo dsh
real) nunca tinha rodado antes — é a primeira vez que o laço agêntico
encadeia muitas sessões `dsh` de verdade em sequência, não só os 3 casos
isolados do README ou testes avulsos. Em **4 das 6** primeiras sessões, a
chamada de ferramenta do modelo não foi reconhecida como tool call: caiu como
bloco de `reasoning` (texto solto que ninguém lê) e o turno terminou
("completed") sem executar nada. Não é o modelo raciocinando errado — o
conteúdo dos casos quebrados é coerente, às vezes é uma SQL correta e bem
construída (case 6: CTEs certas, comentário explicando a escolha de
agregação). **A ferramenta simplesmente nunca chega a rodar.**

**Evidência exata, dos logs de sessão do dsh** (`~/.dsh/sessions/`, lidos
localmente, sem custo de servidor):

```
case2, step 2:  '<tool_call|>'
case3, step 3:  '<tool_call|>'
case4, step 5:  '<|tool_call>call:mcp__rodado__descrever_tabela{tabela:<|"|>br_inep_ideb.escola<|"|>}<tool_call|>'
case6, step 10: '<|tool_call>call:mcp__rodado__consultar{sql:<|"|>\nWITH obitos_infantis AS (...) ...\n<|"|>}<tool_call|>'
```

O padrão `<|tool_call>call:NOME{arg:<|"|>VALOR<|"|>}<tool_call|>` é a
convenção NATIVA de tool-call do próprio Gemma (tags com o `|` na posição
trocada) — **diferente** do `<tool_call>{"name":...}</tool_call>` que o
parser de tool-call do llama-server reconhece para outros modelos. Casos 1 e
5 completaram normalmente (respostas erradas, mas por SQL/raciocínio — falha
"de verdade"); casos 2, 3, 4, 6 morreram neste bug.

**Descartado, testado ao vivo** (com autorização explícita antes de mexer no
servidor compartilhado): `NOJINJA=1 ./harness/servidor.sh` (desliga o motor
jinja, hipótese de que o parser genérico sem-jinja reconheceria o formato) —
**quebra o servidor inteiro** para este modelo, toda chamada volta
`{"error":{"code":500,"message":"this custom template is not supported, try
using --jinja"}}`. O template do Gemma exige jinja para qualquer coisa, não só
tool-calling. Reversão imediata, servidor voltou ao normal
(`./harness/servidor.sh`, sem `NOJINJA`) e confirmado saudável. A flag
`NOJINJA` fica em `servidor.sh` só documentada como descartada, para não
repetir o experimento.

### Causa provável, encontrada lendo o código do llama.cpp no beelink (`~/llama.cpp`, sem custo de servidor)

O llama.cpp **já tem** suporte dedicado ao tool-calling nativo do Gemma4:
`common_chat_params_init_gemma4` em `common/chat.cpp` monta um parser PEG
inteiro (`common_chat_peg_gemma4_mapper`, `common/chat-peg-parser.h/.cpp`)
que reconhece exatamente `<|tool_call>call:NOME{...}<tool_call|>` — não é
genérico nem incompleto, é escrito pra este formato. Confirmado: o
`chat_template` embutido no GGUF (lido via `/props`) contém a string literal
que o detector procura (`'<|tool_call>call:'`) e o marcador de template
oficial (`{#- OpenAI Chat Completions:`), então o llama-server ESTÁ usando
esse parser, não um genérico.

**O mecanismo suspeito — grammar "lazy" com gatilho por substring.** Em
`common_chat_params_init_gemma4`:

```cpp
data.grammar_lazy = !(has_response_format || (has_tools && inputs.tool_choice == COMMON_CHAT_TOOL_CHOICE_REQUIRED));
```

Com ferramentas presentes e `tool_choice` em `auto` (o normal de um laço
agêntico — o modelo decide se chama ferramenta ou responde em texto),
`grammar_lazy = true`: a geração roda **sem nenhuma restrição de gramática**
até o texto bruto conter o gatilho exato `<|tool_call>call:`; só a partir
daí a gramática PEG passa a forçar sintaxe válida. Antes do gatilho, o
modelo gera livre — e é exatamente aí que uma tentativa mal-formada de tool
call pode nunca disparar o gatilho (casos 2/3: só a tag de fechamento
sobrou, o `<|tool_call>call:` nunca apareceu) ou disparar mas ainda assim
falhar no parse final quando a geração completa é reprocessada pela
gramática PEG completa (casos 4/6: o texto tem as duas tags e parece
correto, mas ainda cai como `reasoning`). As duas hipóteses continuam
**não confirmadas** — precisaria de log verboso do `llama-server` capturando
o corpo bruto da resposta, não tentado (custaria outra rodada do servidor
compartilhado só para diagnóstico).

**Descartado #2, testado ao vivo:** `TEMP=0 ./harness/servidor.sh`
(`--temp 0`, sobrepondo o default de 0,80 do llama-server). Hipótese: com
temperatura alta e sem o cliente mandar `temperature` próprio, o modelo tinha
variância real token a token, e reproduzir o gatilho `<|tool_call>call:` por
sorte explicava a taxa de falha. **Confirmado o oposto**: a mesma pergunta
("Escolas rurais...", a que quebrou como case3 na rodada) bateu o **mesmo bug,
byte a byte** (`<tool_call|>` sozinho, no mesmo step 2, logo depois do
resultado de `listar_datasets`) — 2,7 min, bem mais rápido que o normal,
confirmando falha rápida e reproduzível. Decodificação gulosa (`temp=0`) é
**determinística**: se o caminho de maior probabilidade passa pelo bug NESTE
contexto, ele passa por ele **sempre**, e retentativa não ajudaria mais
(diferente do `temp=0,80` padrão, onde a variância real já foi observada
recuperando os mesmos 2 casos sem bater o bug de novo). `temp=0` é **pior**
para o workaround de retentativa, não melhor. Revertido na hora
(`./harness/servidor.sh` sem `TEMP`), servidor confirmado saudável de novo.
Flag `TEMP` fica em `servidor.sh` só documentada como descartada.

**Diagnóstico #3, com log verboso** (`LOGPROMPTS=1 ./harness/servidor.sh` —
`--verbose --log-prompts-dir`, novo em `servidor.sh`, não descartado):
não reproduziu o bug na tentativa (esperado — é probabilístico). Achado à
parte, valioso mesmo sem confirmar a hipótese: a mesma pergunta ("CBOs
dominadas por admissões precárias...") terminou com o modelo apresentando
um **plano de investigação e pedindo aprovação** em vez de executar — 2ª vez
que isso aparece em rodadas diferentes. Não é o bug do item 10 (a ferramenta
FOI reconhecida; o modelo só decidiu parar sozinho) — é comportamento de
assistente interativo vazando pra um contexto sem humano nenhum pra aprovar
nada. **Consertado**: `persona` em `dsh/rodado.patch.yml` agora instrui
explicitamente a nunca parar num plano. Testado ao vivo, mesma pergunta:
desta vez executou de verdade e concluiu (não confirmou a hipótese por
limite real dos dados — CAGED só cobre 2020-2025, a pergunta assumia
2012-2022 — mas é uma resposta completa, não um plano parado). Detalhe em
`regras.md`, "O laço e o reparo".

**Não investigado ainda:**
- Log verboso do `llama-server` numa chamada ao vivo, pra ver se o campo
  `tool_calls` da resposta HTTP vem vazio (confirmaria: falha é do parser
  server-side, não do dsh) — a suspeita forte, mas não verificada byte a byte
  (a tentativa de diagnóstico acima não bateu o bug, então não deu pra olhar
  a resposta bruta do caso quebrado — `LOGPROMPTS=1` fica pronto pra próxima
  vez que reproduzir).
- Forçar `tool_choice: required` desativa o `grammar_lazy`, mas também
  impediria o modelo de terminar com texto livre (a resposta final) —
  não dá pra usar sem repensar como o laço encerra o turno.
- `--grammar`/`--grammar-file` (flags existem, conferido no `--help`) para
  forçar uma gramática não-lazy por fora do mecanismo nativo do Gemma4 — não
  tentado, exigiria replicar a gramática PEG à mão.
- Taxa de falha real: 4/6 (rodada abortada) e agora mais casos na rodada 2
  também bateram (case2, case3 de novo, ambos recuperados por retentativa) —
  parece alta e consistente, não um acaso da amostra pequena. O workaround
  supre a necessidade de saber a taxa exata pra rodar o item 2, mas não
  decide se vale investir mais na causa raiz.
- **Achado junto com o teste de temperatura, ainda mais interessante que o
  resultado em si:** o mesmo caso (case3) bate o MESMO bug no MESMO step
  (step 2, logo após `listar_datasets`) em duas rodadas diferentes, com
  configs diferentes — sugere que o gatilho de falha pode estar ligado ao
  CONTEXTO específico daquele ponto (o resultado de `listar_datasets`, uma
  lista de ~212 nomes, ~2000 tokens) mais do que a aleatoriedade pura. Não
  confirmado — outras perguntas falharam em steps diferentes (step 3, 5, 10),
  então não é *só* isso. Pista para quem continuar a investigação.

### Workaround feito — retentativa automática em `lote.ts`

`respondeu` já detectava isto sem querer: o dsh não imprime NADA quando o
turno termina só com bloco `reasoning`, então `texto.trim().length > 40` já
dava `false` para os 4 casos quebrados. `roda()` agora tenta a MESMA pergunta
de novo, num processo `dsh` novo, até `HARNESS_TENTATIVAS` vezes (padrão 3,
`rodaUmaVez()`/`MAX_TENTATIVAS` em `lote.ts`) — só quando a tentativa veio
**vazia**, nunca quando veio uma resposta errada (isso é falha de raciocínio
de verdade, repetir esconderia a taxa de acerto real). `Saida.tentativas`
registra quantas vezes cada caso precisou, pra retentativa aparecer no
relatório em vez de desaparecer calada.

**Por que é aceitável não ser a causa raiz:** casos 1 e 5 (sessões do mesmo
tamanho ou maiores que os que quebraram) completaram normalmente — o bug
parece ser por-turno, não por-conteúdo fixo, então repetir a pergunta numa
sessão nova tem chance real de não bater o mesmo problema. Não é garantido.

**Testado ao vivo 2026-09-03** contra os 2 casos que romperam com o padrão
mais curto (`<tool_call|>` sozinho, casos 2 e 3 da rodada abortada,
`benchmarks/lote_2026-09-030710.json`): as duas sessões completaram no
`tentativas: 1` — nenhuma bateu o bug de novo desta vez (confirma a hipótese
de que é por-turno, não determinístico pelo conteúdo da pergunta; não prova
que a retentativa em si recupera um caso, só que o mecanismo não atrapalha
quando não precisa). RESPONDEU 2/2 = 100%, CORRETO 0/2 — os dois erraram o
número por raciocínio de verdade, não pelo bug: um caso divergiu do
cruzamento pedido, o outro devolveu um **plano de investigação** em vez de
executá-lo (agente parou cedo, achado à parte — não é o bug do item 10, é
"não completar o laço", mesma família da regra "todo ganho de tempo tem que
preservar a capacidade de iterar" de `regras.md`). Tempo médio 1096 s/caso —
bem acima da linha de base de ~6 min, porque ambos os casos são dos mais
difíceis do conjunto (múltiplos cruzamentos), não porque a retentativa
disparou.

**Bloqueia** (a causa raiz, não o workaround): nada mais — o workaround
libera o item 2 pra rodar de novo, e a rodada plena começou logo depois
deste teste. Fica em aberto **conserto de verdade**: entender por que o
parser nativo do Gemma4 falha em ~2/3 dos turnos, e se dá pra reduzir a taxa
(`tool_choice`, gramática forçada, ou upstream do llama.cpp). O item 11
propõe um caminho pra esse conserto de verdade — LoRA em vez de patch em
C++/upstream.

## 11. LoRA pra estabilizar o tool call nativo do Gemma4 🟡 passo 0 feito 2026-09-03 — resto do plano não rodado

Nasce direto do item 10: o Gemma4 já FOI treinado pro formato nativo
`<|tool_call>call:nome{...}<tool_call|>` — o llama.cpp tem parser PEG
dedicado pra ele — mas sob `tool_choice=auto` a geração roda em gramática
"lazy" (sem restrição até bater um gatilho por substring, ver item 10) e o
modelo erra a própria sintaxe treinada em boa parte dos turnos. Isso é
**consistência de comportamento**, não conhecimento novo — exatamente o tipo
de coisa que LoRA resolve bem, ao contrário de saber o schema do espelho
(camadas do portão), que é conhecimento específico e muda a cada sync.

### Por que Gemma continua sendo a base certa

- É o modelo já em produção — treinar um LoRA pra ele não muda nada da
  ferramenta de servir (`servidor.sh`), só adiciona uma flag (`--lora`).
- Ele já tem o comportamento-alvo internalizado; o LoRA teria que
  **reforçar**, não ensinar do zero — dataset pequeno, alvo estreito.
- **Passo 0 confirmado ao vivo, neste Mac, sem baixar o checkpoint real**
  (`transformers` 5.15.0 e `peft` 0.20.0, ambos já instalados/instaláveis
  localmente): `transformers` tem a arquitetura registrada —
  `gemma4_assistant` → `Gemma4AssistantForCausalLM`/`Gemma4AssistantConfig`,
  importam e instanciam limpo. `peft.get_peft_model()` com `LoraConfig`
  (`target_modules=[q_proj, o_proj, gate_proj, up_proj, down_proj]`) anexou
  adapters sem erro, trainable% na faixa normal de LoRA (~0,09% numa config
  de teste pequena, não o checkpoint de 26B real). Verificado só na
  estrutura (config em `meta`/CPU, sem baixar os pesos de 13–52 GB), mas
  confirma que o resto do plano pode prosseguir sem risco de arquitetura.
- **Achado de bônus, corrige uma suposição do projeto:** o validador da
  config (`Gemma4AssistantConfig.validate_architecture` em
  `configuration_gemma4_assistant.py`) **exige** `enable_moe_block=False` —
  erra se não for. O checkpoint "assistant" (o que o `llama-server` serve e
  cujo tool-call nativo é o alvo deste item) roda em modo **denso, não
  MoE-roteado**, ao contrário do "26B / ~4B ativos, 128 experts" descrito em
  `check-qwencoder-vs-duckdbnsql.md` (que provavelmente descreve um
  checkpoint-irmão, não este). Na prática isso **remove** o risco de
  "roteamento de MoE se comportando estranho sob LoRA" da tabela de custo
  abaixo — LoRA em transformer denso é o caso mais bem suportado que existe.

### Por que NÃO expandir para as camadas do portão

Princípio já em vigor no projeto (`bridges.yaml`/`catalog.parquet`/
`metrics.yaml` como **dado regenerável**, não prosa que o modelo memoriza —
ver CLAUDE.md): schema muda a cada sync, e conhecimento em peso vai ficando
velho até alguém lembrar de retreinar. Código+dado lido em tempo de execução
não tem esse problema — é sempre a versão mais recente.

**Ressalva, levantada e aceita durante a conversa:** essa objeção só vale
para um LoRA treinado uma vez e esquecido. Se o escopo um dia **expandir**
para conhecimento de schema, e o retreino virar **outro passo automático do
pipeline de sync** — ao lado de `gera_join_keys.py`, `gera_metrics_json.py`
etc. — a "ficar velho" deixa de ser argumento, vira só mais um regen. Esse
plano, porém, fica **escopado ao alvo estreito do item 10** (formato de tool
call, independente de schema) — expandir o escopo é decisão futura separada,
não parte deste item.

### Fonte de dado de treino — já existe, de graça

Toda sessão `dsh` que bateu o bug do item 10 (o texto solto `<tool_call|>` ou
`<|tool_call>call:...<tool_call|>` mal-classificado) e toda rejeição do
portão seguida de correção (`~/.dsh/sessions/*.jsonl.zstd`, mais os
`benchmarks/lote_*.json` do item 2) é um par (tentativa ruim → o que devia
ter saído) sem custo de rotulagem — já está logado. Não precisa gerar
sintético do zero, só extrair.

### Hardware — testado ao vivo, os dois descartados

| Onde | Achado | Veredito |
|---|---|---|
| Este Mac (M4, 16 GB) | `mlx-lm` 0.31.3 já instalado, mas `vm_stat`/`top` mostram **14 GB de 16 GB já em uso** só rodando esta sessão — 1,8 GB livre. O GGUF q4_0 sozinho é 13,4 GB. Não cabe, e esta máquina é o ambiente de trabalho ativo — travar ela trava tudo o mais | ❌ descartado |
| beelink | `nvidia-smi` ausente, só iGPU AMD Vega (`lspci`); 27 GB RAM com 21 GB já em uso servindo o `llama-server` | ❌ descartado (já sabíamos que não tinha GPU; confirmado de novo aqui) |

### Plano — RunPod.io, treino só, base continua local

**Passo 0 ✅ feito 2026-09-03, sem GPU.** `transformers`/`peft` carregam a
arquitetura (`Gemma4AssistantForCausalLM`) e `peft` anexa LoRA sem erro —
ver achado acima. Não testado: carregar os PESOS REAIS do checkpoint de 26B
(exigiria baixar 13–52 GB e não coube na checagem estrutural feita aqui) —
fica pro passo 2, já dentro do pod alugado, não antes.

**Passo 1 — extrair o dataset.** Script novo (não escrito ainda),
`harness/dados/lora_toolcall.jsonl` ou similar: varre as sessões `dsh` já
logadas, extrai pares (contexto até o ponto da falha → tool call correto que
deveria ter saído), few centenas a ~2 mil exemplos esperados dado o volume já
logado.

**Passo 2 — treinar.** GPU alugada, LoRA (não fine-tune completo: só as
matrizes de adaptação, base congelada).

| Etapa | GPU | Tempo | Custo |
|---|---|---|---|
| Subir o pod + baixar pesos base (bf16, ~52 GB pros 26B) | — | 10–20 min | incluso |
| Treino LoRA (algumas centenas a ~2 mil exemplos, 2–4 épocas) | 1× A100 80GB (~US$1,50–2/h) ou H100 80GB (~US$2,50–4/h); QLoRA 4-bit caberia numa placa mais barata (24–48 GB) se bf16 não for necessário | **~1–3 h** (estimativa — sem benchmark de MoE nesta escala; medir com `--iters 20` antes de comprometer a rodada inteira) | **US$3–12** |
| Salvar/baixar o adapter (LoRA é dezenas de MB, não GB) | — | poucos min | — |
| Aplicar no beelink | — | segundos — `llama-server --lora adapter.gguf`, sem requantizar o GGUF base atual | grátis |

**Total estimado para uma tentativa limpa: US$5–15, 2–4 h.** Realisticamente
orçar **2–3 tentativas** (formato de dado errado, hiperparâmetro pra ajustar
— o risco de roteamento de MoE saiu da lista, ver achado do passo 0 acima:
o checkpoint "assistant" é denso) — mais perto de **US$20–40, uma tarde**.

**Passo 3 — validar.** Reverter é só tirar a flag `--lora`. Medir contra os
casos que já bateram o bug (as sessões do item 10 e do item 2 com
`tentativas > 1` em `benchmarks/lote_*.json`) — se o LoRA funcionou, esses
mesmos casos devem responder na 1ª tentativa, sem precisar do workaround de
`lote.ts`. Não é um "não bloqueia mais nada" solto: é uma régua concreta, os
mesmos casos que já têm gabarito de falha registrado.

**Fecha quando:** rodando os casos que hoje precisam de retentativa (item 2)
contra o servidor com o LoRA aplicado, a taxa de `tentativas > 1` cai — não
precisa chegar a zero, só cair o bastante pra a retentativa deixar de ser o
caminho normal.

---

## Sem retorno medido — herdados do plano original

Vieram da lista "Falta" de `harness_gemma_dsh.md`, removida de lá para não
manter duas filas divergindo. Ficam **abaixo** dos itens 0-5 de propósito:
nenhum tem falha medida atrás, então a ordem entre eles é julgamento, não dado.

### 6. Camada de ano no portão ✅ fechado 2026-09-02

`anos.ts` já sabia a faixa real de cada tabela (377 cacheadas) e **não bloqueava** —
só serviu uma vez para explicar um `n=0` depois do fato. O caso que a motivou: o
modelo montou CAGED×RAIS×PIB corretamente e filtrou `ano=2022`, mas
`br_ibge_pib.municipio` termina em **2021**.

Mesma família da tarefa 1 de [`regras.md`](regras.md) (`COUNT(*) AS n` e `n=0`
só valem no pipeline aposentado): o portão sabia a coisa e não agia.

**Fechado**: `checaAno` em `portao.ts` rejeita antes de executar, dividindo a
SQL em escopos (CTE/subconsulta) para não cobrar filtro de uma tabela pelo
predicado de outra. `mcp.ts` também usa `faixasCitadas()` na mensagem de zero
linhas, no lugar de mandar chamar `listar_tabelas` de novo. Coberto por
`portao.test.ts`, não medido numa rodada ao vivo ainda.

### 7. Alerta de sanidade virar reparo 🟡 parcial 2026-09-02

Hoje `corr=0,97` só avisa. O mecanismo que funciona já existe e está provado — a
rejeição do portão volta ao modelo como resultado de tool call e ele conserta
sozinho (foi assim que 726 virou 789). Falta aplicá-lo aos alertas.

**Parcial**: só o caso sem leitura legítima — estatística derivada (`AVG`,
`MEDIAN`, `STDDEV`, `CORR`, razão entre agregados) sem `COUNT(*) AS n` —
virou rejeição dura (`checaAmostra` em `portao.ts`). Os outros três alertas
(`GROUP BY` reportado como total, `n` acima dos 5.570 municípios, correlação
suspeita) continuam soft de propósito — todos têm leitura legítima, e
rejeitar duro rejeitaria trabalho correto. Eles voltam grudados no resultado
via `alertasDeSanidade()` em `mcp.ts`, então o modelo pelo menos vê antes de
escrever a prosa; não viram reparo automático.

### 8. O Gemma redige relatório, ou só apura número? 🔴

Medir a prosa gerada contra as 9 análises de `pages/analises/results/`. É a
pergunta que decide a **Fase 5**, e é diferente do item 3 (que é sobre *como* a
prosa cita a fonte, não sobre se ela se sustenta).

**Expectativa registrada na época, não medida:** provavelmente não redige — o
alvo são 3-4 mil palavras com contra-argumento steelmanado, e um 26B em q4 nunca
foi testado nisso. O scaffold proposto para essa fase está em
[`harness_bpe.md`](harness_bpe.md).

## 12. Falta a mensagem "não há ponte" — o modelo repete uma chave inexistente 38x sem escalar ✅ fechado 2026-09-03 (a ação de harness — a de dado, T21, continua aberta)

Medido rodando a pergunta mais rica de `perguntas.md` em nº de fontes
(emendas parlamentares → contratos → CNPJ → TCU → PGFN, seção "Perguntas
multi-dataset simultâneos", item 3) por `bun harness/pergunte.ts`. **40 min,
`SIGKILL` pelo timeout do próprio harness, zero resposta.** Log completo em
`~/.dsh/sessions/--Users-polux-Projetos-rodado--/session-358f388b-.../session.jsonl.zstd`
(75 turnos, 74 tool calls, 55 SQL).

**O que aconteceu, turno a turno:**

- Turnos 1-19: reconhecimento normal — achou as duas tabelas certas
  (`br_cgu_emendas_parlamentares.microdados`, `br_cgu_licitacao_contrato.licitacao_item`),
  mas bateu 6 erros seguidos tentando `br_cgu_sancoes.ceis/cepim/cnep/...`
  (nomes errados — a tabela certa é `br_tcu_inidoneos`) e abandonou essa
  ponta da pergunta pro resto da sessão.
- Turnos 20-74 (quase todo o tempo): **38 das 55 SQLs (69%) tentam a mesma
  hipótese de join**, `l.id_emenda = p.id_licitacao`, sempre com o mesmo
  resultado — 9x rejeitado por faltar filtro de partição, 29x "ZERO linhas"
  depois de corrigir. O modelo varia cosmético (coluna selecionada, `WHERE`,
  `LIMIT`) sem nunca abandonar a hipótese. No turno 20, o **próprio
  comentário da primeira tentativa** já registra a dúvida certa —
  `-- Tentativa de join por ID, mas emendas e licitacoes podem não ter a
  mesma chave direta` — e mesmo assim insiste mais 37 vezes.
- Turno 72-73: desespero visível — tenta `ON l.id_emenda = p.cpf_cnpj_vencedor`
  (join sem sentido nenhum, ID de emenda contra CNPJ), com comentário
  `-- Testing if join is on CNPJ`.
- Turno 75: morre por infra, não por lógica — `pi-ai stream idle timeout` no
  meio da geração, dispara retentativa, o `SIGKILL` de 40 min do
  `pergunte.ts` chega antes dela terminar.

**Causa raiz, não só sintoma — checado nos dois lados:**

1. **A mensagem de "zero linhas" não sugere, e as que sugerem não cobrem
   este caso.** `rejeitada (particao)` e `rejeitada (coluna)` já ensinam o
   conserto (mensagem cita a coluna certa/o predicado certo — funcionou pro
   caso do suicídio RJ, 726→789). `zero linhas` só diz "confira o tipo das
   duas pontas da chave" — nenhuma sugestão concreta.
2. **O harness TEM um mecanismo de sugestão de join** (`pontes.ts` →
   `dicasDeJoin`, plugado em `descrever_tabela`, com fallback genérico
   "junte por `id_municipio`/`sigla_uf`/`ano`/`id_uf` quando as duas
   tiverem") — mas só dispara quando `descrever_tabela` é chamado com as
   duas tabelas de uma vez, e nesta sessão (e provavelmente em geral) o
   modelo sempre chama uma tabela por chamada. Nunca disparou.
3. **Mesmo se disparasse, não ajudaria neste par específico** — conferido
   direto no beelink: `licitacao_item` não tem `id_municipio` nem
   `sigla_uf` (só `ano`, `id_orgao`, `id_unidade_gestora`); `emendas.microdados`
   não tem `id_orgao` nem `id_unidade_gestora` (só `id_municipio_gasto`).
   **As duas tabelas não compartilham nenhuma coluna real**, e `bridges.yaml`
   não tem ponte entre elas (só existe `emendas_parlamentares` → `municipio`).
4. **Isto não é bug do harness — é o mesmo buraco já catalogado em
   `respostas.md` (T21-1/T21-2/T21-3/T21-5 ⏳):** "exige identificar
   fornecedor por CNPJ recorrente entre `cgu_cartao_pagamento`/
   `cgu_licitacao_contrato`... fica para uma passada de resolução de
   entidade dedicada." Essa cadeia de `perguntas.md` pode genuinamente não
   ser respondível por join direto neste espelho — nem um modelo perfeito
   acharia uma chave que não existe.

**Duas ações, não uma — não confundir "consertar a mensagem" com "consertar
o dado":**

- **Ação de harness (barata, faz o modelo desistir mais cedo):** a rejeição
  de `zero_linhas` devia checar `bridges.yaml` para o par de tabelas do
  `JOIN` e, se não achar ponte nenhuma **e** nenhuma coluna em comum,
  responder algo como *"Nenhuma ponte conhecida entre estas duas tabelas —
  provavelmente não há chave direta neste espelho; considere responder pela
  parte que tem dado, ou avisar que esta pergunta não é resolvível por SQL
  simples"* em vez de convidar a tentar de novo. Isso é o que teria parado o
  modelo no turno ~30, não no timeout do turno 75.
- **Ação de dado (cara, não deste item):** se a cadeia emenda→contrato
  realmente importa, precisaria de uma tabela-ponte real (ex.: cruzar por
  CNPJ do fornecedor entre `licitacao_item.cpf_cnpj_vencedor` e algum
  identificador de execução orçamentária que também apareça em
  `emendas_parlamentares` — não óbvio que exista na fonte). Ficaria junto
  do T21 pendente, não é problema novo. **Continua aberta** — nada aqui
  resolve isso, só faz o harness desistir rápido em vez de devagar.

### Implementado 2026-09-03 — três conserto de harness, nenhum de dado

**1. `juncoesSemPonte()` + `mensagemSemPonte()` (`portao.ts`).** NÃO é camada
de `portao()` — roda só depois que a consulta já executou e voltou zero
linhas (dentro de `mcp.ts`), de propósito: checar a ponte ANTES de executar
arriscaria bloquear uma junção legítima que só ainda não está documentada em
`bridges.yaml`, o mesmo risco de falso positivo que a camada `ano` evita
calando-se (ver o comentário dela). Reaproveita a máquina de escopo/apelido
que a camada `ano` já tinha (`segmentos`, `refsDoEscopo`) — extrai os pares
`alias.coluna = alias.coluna` de cada `ON`, resolve os apelidos pra
`dataset.tabela`, e pergunta pra `conceitoDaColuna()` (nova, `pontes.ts`) se
cada lado tem ponte curada ou é chave canônica (`id_municipio`, `sigla_uf`,
`ano`, `id_uf`) — se os dois lados não convergem no mesmo conceito, a junção
entra na lista.

**2. Disjuntor de repetição (`assinaturaJuncao()` + `Map` em `mcp.ts`).** A
assinatura é o `FROM…JOIN…ON` com literais apagados — o que ficou constante
nas 38 tentativas reais foi exatamente isso, só o resto (`WHERE`, colunas do
`SELECT`, `LIMIT`) variava. Na 3ª vez que a MESMA assinatura devolve zero
linhas, a mensagem escala de "confira o tipo da chave" pra "pare de tentar
isto". Estado é `Map` de módulo em `mcp.ts` — nasce e morre com o processo,
que é um por pergunta (`pergunte.ts` spawna um `dsh` novo a cada chamada).

**3. Orçamento de consultas (`ORCAMENTO_CONSULTAS`, `mcp.ts`).** Teto de 30
chamadas de `consultar` por pergunta (`HARNESS_ORCAMENTO_CONSULTAS`, env),
bem abaixo do que os 40 min de parede do `pergunte.ts` deixariam rodar. Corte
é local — sem ida ao beelink — e a mensagem instrui a responder com o que já
tem, não a insistir.

**Verificado contra a sessão real que morreu** (as 55 SQLs de
`session-358f388b-...jsonl.zstd`, rodadas pelo `portao()`/`juncoesSemPonte()`/
`assinaturaJuncao()` novos, fora do laço agêntico — não uma rodada nova no
beelink):

| Métrica | Sem os 3 consertos | Com eles |
|---|---|---|
| Turno em que o disjuntor dispara (3ª repetição da mesma junção) | nunca — seguiu até o turno 74 | **turno 27** |
| SQLs com "sem ponte conhecida" anexado | 0 (mensagem não existia) | **28 de 55** |
| Assinaturas de junção distintas tentadas | — | 7 (duas dominantes: 27x e 10x) |

Ou seja: o mesmo caso que morreu em 40 minutos sem resposta teria escalado
pro modelo desistir por volta do **turno 27** (~7 min, pela cadência medida
de ~30s/turno) em vez do turno 75. Não testado ainda **rodando de novo pelo
laço agêntico** (custaria outros ~10-40 min de beelink) — a validação acima é
contra o log gravado, não uma repetição ao vivo; fica pra quando o item 2
rodar de novo.

**Testes:** `portao.test.ts`, describe `juncoesSemPonte` (5 casos: acusa o
par emendas/licitação sem ponte, a mensagem nomeia as duas colunas, não
acusa chave canônica em comum, não acusa junção dentro do mesmo dataset,
reconhece a ponte curada `id_municipio_gasto`) e `assinaturaJuncao` (2 casos:
mesma junção com cosmético diferente tem assinatura igual; junção genuinamente
diferente tem assinatura diferente). `bun test harness/`: 108 passam.

## 13. Resposta final sem consulta nenhuma — 467 aprovado no lugar de 789 ✅ fechado 2026-09-04

Achado ao vivo testando `THINKING=1` (não era o que se procurava). Pergunta
canônica do suicídio RJ 2020 (gabarito 789, já verificado várias vezes neste
projeto): o modelo chamou `listar_datasets` → `listar_tabelas` →
`descrever_tabela` ×2 e foi direto pra `revisar_resposta` com **"467 óbitos
(355 masculino, 112 feminino)"** — número inventado, **`consultar` nunca foi
chamado**. `revisar_resposta` aprovou, porque `checaCitacaoTabela` (item 3)
só olha se a prosa cita tabela/dataset — nunca se ela veio de dado real.

Pior classe de erro que existe no harness até agora: SQL errado pelo menos
toca o beelink e pode ser pego por partição/coluna/ano/zero-linhas; isto pula
a execução inteira e sai com aparência de resposta apurada.

**Conserto:** `checaExecutouConsulta()` (`portao.ts`) — incondicional, sem
tentar regex sobre "isto parece número inventado" (frágil, teria que
distinguir estatística fabricada de ano citado da pergunta). `mcp.ts` conta
`consultasComResultado` (incrementado só quando `consultar` volta linha de
verdade) e `revisar_resposta` rejeita de cara se o contador é zero — ANTES
da checagem de citação, porque sem dado real a forma da prosa não importa.
2 testes novos em `portao.test.ts`. `bun test harness/`: 109 de 110 passam
(a 1 falha é pré-existente, de trabalho concorrente nesta branch — dataset
`br_ibama_embargos` saiu do catálogo num commit fora deste item; confirmado
isolado via `git stash`, não é regressão deste conserto).

## Ver também

- [`regras.md`](regras.md) — as regras que cada medição gerou, e o que ainda é só disciplina
- [`operacao.md`](operacao.md) — as checagens antes de confiar numa rodada
- [`harness_gemma_dsh.md`](harness_gemma_dsh.md) — o plano (fases 0-5) e a lista "Falta"
