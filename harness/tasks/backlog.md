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

## 2. Rodar o laço nos casos com `n` conferido 🔴 rodada iniciada e ABORTADA 2026-09-03 — achou bug bloqueador, ver item 10

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

**Rodada começou 2026-09-03 00:19, abortada no caso 6/58.** As invariantes de
`operacao.md` estavam ok (`confereBoot()` aprovou, `-np 1 -c 32768` confirmado).
0/6 casos corretos — mas **4 dos 6 não são falha de raciocínio, são a chamada
de ferramenta caindo como texto solto** por causa de um bug de parsing só
agora exposto porque é a primeira vez que o laço roda tantas sessões `dsh`
reais em sequência. Detalhe completo, causa provável e o que já foi
descartado: **item 10**, abaixo. **Não rodar de novo até o item 10 fechar** —
qualquer número coletado sem o conserto mede o bug, não o modelo.

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

## 10. Tool call cai como texto solto — bloqueia o item 2 🔴 achado 2026-09-03, bloqueador — nada resolvido ainda

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

**Não investigado ainda:**
- Versão do llama-server é `0.3.0-dev` (build `8887a48`) — conferir se é uma
  versão conhecidamente afetada, ou se uma mais nova tem o parser do Gemma
  corrigido.
- `--chat-template`/`--chat-template-file` custom, explicitamente ensinando o
  parser a reconhecer `<|tool_call>...<tool_call|>` — ou forçando um
  `--grammar` estático que não dependa do parser nativo do modelo (o que o
  README já supunha estar acontecendo: "tool-calling, via grammar do
  llama.cpp" — aparentemente não é garantido, só parcial).
  `--grammar`/`--grammar-file` existem como flag do `llama-server` (conferido
  no `--help`), não testados.
  `--jinja` (mantendo jinja) + template customizado é o caminho mais provável
  — `--no-jinja` só provou que o template do Gemma não roda sem jinja, não
  disse nada sobre o parser de tool-call em si.
- Taxa de falha real: 4/6 é a amostra que existe. Pode ser mais alto ou mais
  baixo em 58 casos — não dá para saber sem rodar de novo, e rodar de novo sem
  conserto é o desperdício que este item existe para evitar.
- Se o parser tem algum jeito de RECUPERAR desse estado (reenviar o turno,
  pedir para o modelo tentar de novo) em vez de simplesmente terminar — hoje o
  `turn/end` marca `"reason":{"kind":"completed"}` como se tivesse dado certo,
  o que é **por si só um bug a reportar** (achar isto pode ser trabalho do
  dsh, não do harness deste projeto).

**Bloqueia:** item 2 (a rodada em si), item 4, item 8, e o experimento de
`check-qwencoder-vs-duckdbnsql.md` (todos esperam uma linha de base
confiável). **Não bloqueia:** os itens 0/1/3/5/6/7/9, que não dependem de
rodar 58 sessões `dsh` completas.

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

## Ver também

- [`regras.md`](regras.md) — as regras que cada medição gerou, e o que ainda é só disciplina
- [`operacao.md`](operacao.md) — as checagens antes de confiar numa rodada
- [`harness_gemma_dsh.md`](harness_gemma_dsh.md) — o plano (fases 0-5) e a lista "Falta"
