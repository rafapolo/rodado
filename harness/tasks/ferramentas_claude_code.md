# O que o Claude Code faz com as próprias ferramentas — e o que disso serve aqui

> Aberto em 2026-09-04, a pedido, depois do item 12 do
> [`backlog.md`](backlog.md) (a pergunta de 5 fontes que rodou 40 min presa
> 38x na mesma junção). A pergunta feita foi literal: *"tens como analisar
> seus próprios tools e instruir esse nosso harness como fazer melhor?"*
>
> **O que este documento é:** o contrato de ferramenta que um agente da
> família Claude Code enxerga, lido diretamente do próprio contexto de uma
> sessão — não de documentação, não de memória — e mapeado contra as falhas
> que ESTE harness já mediu.
>
> **O que ele não é:** engenharia reversa do Claude Code. Nada aqui afirma
> como o produto está implementado por dentro. O que é inspecionável é a
> *superfície*: as descrições de ferramenta, as pré-condições declaradas e o
> formato das mensagens de erro. Isso basta, e é justamente a parte
> transferível — o Gemma também só enxerga uma superfície.

## A ideia central, em uma frase

Boa parte do que impede um agente de entrar em loop **não está no prompt de
sistema**: está grudada no resultado de cada chamada de ferramenta. É a única
metade que pode variar sem quebrar o cache de prefixo — e é exatamente onde
este harness tem espaço sobrando.

`regras.md` já cravou que *nada variável entra no prefixo* (prefixo instável
evapora o 44x sem sinal no resultado). A consequência que faltava tirar: se o
prefixo é imutável por construção, **todo conhecimento dependente de estado
tem que viajar no retorno da ferramenta**. O portão já faz isso para rejeição
(`REJEITADA (partição)`) e o disjuntor para repetição — o padrão é geral e
está subusado.

## A meta, medida — paridade de PASSOS, não de velocidade

Definida a pedido em 2026-09-04: *"tudo bem o Gemma ser lento, mas tem que ser
eficiente como você"*. Não é tokens/s (o 26B em q4 no beelink nunca vai
competir, e não precisa) — é **quantas chamadas de ferramenta são gastas até
chegar no mesmo SQL**.

Primeiro head-to-head real do projeto, mesma pergunta (a de 5 fontes do item
12), rodada pelo Gemma via `pergunte.ts` (sessão `53ac1869`) e por um agente
Claude pelas ferramentas do `mcp_server.py`, no mesmo dia:

| | Gemma | Claude |
|---|---|---|
| chamadas até o mesmo ponto da investigação | 21 (e seguia) | 8 |
| chamadas úteis | 12 (57%) | 8 (100%) |
| desperdício | **9 (43%)** | 0 |
| repetição idêntica da mesma chamada | 3× a mesma SQL | 0 |

**Contaminação declarada:** o traço Claude é piso otimista — quem o rodou já
tinha lido este backlog e o traço do Gemma. O que vale não é o 8 e sim a
**forma**: nenhuma das 8 re-obteve informação já em mãos.

### O desperdício é de TURNO, não de rede — a primeira contagem estava errada

A primeira versão desta seção dizia "43% das chamadas custaram ida ao beelink".
**Errado, e a correção importa mais que o número.** Lendo os RESULTADOS no log
(não só as chamadas), a maior parte do desperdício já era interceptada de
graça pelo portão:

| Chamada | O que era | Custou beelink? |
|---|---|---|
| 15, 17 | `FROM _rodado_metadata` (sem ponto) | **não** — camada `tabela`, local |
| 16 | `_rodado_metadata.catalog` | **não** — camada `tabela`, local |
| 20 | `PRAGMA table_info(...)` | **não** — camada `read-only`, local |
| 6 | `listar_datasets({"dataset":…})` | não (é local), mas devolveu os 212 datasets |
| 12 → 18 | `SELECT * … LIMIT 1` byte-idêntica | **sim, duas vezes** — 1.374 chars idênticos |
| 13 | `SELECT * FROM emendas LIMIT 1` | sim — e **não foi desperdício**: ver achado abaixo |

**O portão já estava fazendo o trabalho dele.** O que ele não faz — e não tem
como fazer, porque é sobre o diálogo e não sobre a SQL — é impedir o modelo de
**gastar turno** repetindo variações de algo já respondido. Como a meta aqui é
explicitamente eficiência de passos e não velocidade, turno É a moeda: 8 das
24 chamadas não produziram informação nova, mesmo as baratas.

Conserto por classe, com a justificativa corrigida:

| Classe | Chamadas | Conserto | Evidência |
|---|---|---|---|
| **Repetição literal executada** | 12→18 (→21) | proposta 5 (curto-circuito) | forte — ida dupla medida |
| **Repetição de algo já rejeitado** | 15, 17, 20 | proposta 4 (instrução negativa) + proposta 3 (placar no resultado) | média — barato, mas gasta turno |
| **Ferramenta errada em silêncio** | 6 | proposta 6 | forte — retorno grande e inútil |

### Achado sério, fora do escopo do harness: parquet corrompido

A chamada 13 (`SELECT * FROM br_cgu_emendas_parlamentares.microdados LIMIT 1`)
não voltou dado — voltou:

```
IO Error: Corrupt database file: computed checksum ... does not match stored checksum
```

Isso não é erro do modelo nem do portão: é **integridade do espelho**.
`br_cgu_emendas_parlamentares.microdados` é justamente a tabela central da
pergunta do item 12 — e explica parte do porquê aquela investigação nunca
fechava, em qualquer harness. Precisa de re-sync/verificação do parquet,
independente de tudo o que este documento propõe.

### E a maior alavanca isolada: perguntar estrutura sem executar SQL

A diferença que mais pesa nos 21×8 **não é raciocínio, é contrato de
ferramenta**. `resolve_join(emendas, licitacao_empenho)` devolveu em UMA
chamada local — sem tocar o beelink — *"nenhuma junção documentada; procure
uma terceira tabela que faça ponte"*. É exatamente a conclusão a que o Gemma
chegou gastando as chamadas 10, 11, 14 e 19 contra o beelink (e, na sessão
que morreu, 38 tentativas).

O harness **não tem essa ferramenta**. Ele descobre junção por tentativa e
erro: escreve o `ON`, executa, lê zero linhas, infere. O aviso proativo do
commit `572d64e` cobre metade disso (a direção negativa: *não há ponte*); o
que falta é a positiva — *a expressão que junta, já conferida*, sob demanda
para um par arbitrário.

**Isso contraria em letra a regra de `regras.md`** (*um 26B acerta mais entre
5 ferramentas do que entre 20*), e não em espírito: uma ferramenta local a
mais que elimina 4+ idas ao beelink é o mesmo trade que fez o portão valer a
pena. Mas é a única proposta deste documento que **precisa ser medida antes
de ser adotada** — o risco de diluir a escolha de ferramenta é real e já foi
medido uma vez.

## O que dá pra inspecionar de mim mesmo, verbatim

Cinco mecanismos, todos lidos das descrições das minhas próprias ferramentas
nesta sessão:

| Mecanismo | Texto do contrato | O que ele impede |
|---|---|---|
| **Pré-condição de estado** | `Edit`: *"You must Read the file in this conversation before editing, or the call will fail."* / `Write`: *"Overwriting an existing file you haven't Read will fail."* | Editar às cegas. Não é conselho — é rejeição |
| **Ambiguidade é erro, não escolha** | `Edit`: *"`old_string` must match the file exactly … and be unique — the edit fails otherwise"*, com `replace_all` como saída explícita | Acertar por sorte uma entre N ocorrências |
| **Instrução negativa na própria descrição** | `Read`: *"Do NOT re-read a file you just edited to verify — Edit/Write would have errored if the change failed"* | Queimar turno confirmando o que já é garantido |
| **Estado injetado no resultado** | `<system-reminder>` — *"injected by the harness, not the user"*, chegando junto de resultados de ferramenta | Que o modelo esqueça o que já fez, sem tocar no prompt de sistema |
| **Divulgação progressiva** | Ferramentas deferidas: existem por nome, mas *"only the name is known — there is no parameter schema, so the tool cannot be invoked"* até serem buscadas | Pagar contexto por ferramenta que esta pergunta não usa |

Nenhum é sofisticado. Os cinco são a mesma disciplina que este harness já
aplica no portão, aplicada a **quando** e a **o que se sabe**, não só a
*se a SQL é válida*.

## Propostas, ordenadas por retorno esperado

Cada uma amarrada a uma falha já medida aqui — nenhuma é especulativa, pela
mesma regra que governa o portão (*toda camada nasce de um erro observado*).

### 1. `consultar` exige que a tabela tenha sido descrita nesta pergunta

**Análogo direto:** `Edit` exigir `Read` antes.

**⚠ Justificativa rebaixada em 2026-09-04, depois de reler os resultados no
log.** A versão original desta proposta dizia que ela salvaria as idas ao
beelink dos chutes de nome (item 12, turnos 1-19: `br_cgu_sancoes.ceis`,
`.cepim`, `.cnep`…). **Não salva:** tabela inexistente já é rejeitada de graça
pela camada `tabela` do portão, sem tocar a rede — conferido nos resultados 15,
16 e 17 da sessão `53ac1869`.

O que sobra pra esta camada é o outro caso, que o portão **não** cobre: tabela
que EXISTE e que o modelo nunca olhou — ele estaria chutando nome de coluna, e
o erro só aparece depois de gastar a consulta. Mais o efeito de segunda ordem
abaixo. **É a única proposta deste documento sem uma falha medida atrás dela**
— pela regra da casa (*toda camada nasce de um erro observado*), deveria
esperar seu próprio caso observado antes de entrar em produção. Está
implementada e testada (`checaDescritaAntes`, 5 casos em `portao.test.ts`),
mas ligá-la ou não é decisão de quem mantém, não conclusão deste documento.

**A camada:** antes de tudo (é local, sem rede), `consultar` extrai os
`dataset.tabela` da SQL — a máquina de escopo/apelido de `juncoesSemPonte` já
faz isso — e rejeita os que não passaram por `descrever_tabela` nesta
pergunta, com a mensagem dizendo qual chamar.

**O efeito de segunda ordem é o maior:** se não dá pra consultar um par sem
ter descrito os dois, então o aviso proativo de junção (`semColunaComum`,
commit `572d64e`) **sempre** precede a primeira SQL do par, em vez de depender
de o modelo ter descrito as duas por acaso. Vira invariante, deixa de ser
heurística.

**Custo:** zero de beelink. `descrever_tabela` é local e o modelo já a chama
naturalmente (o log do item 13 mostra `descrever_tabela` ×2 antes de qualquer
coisa). Risco de falso positivo: nenhum — a correção é chamar uma ferramenta
grátis.

**Cuidado na implementação:** ignorar nomes de CTE (a camada 2 do portão já
tropeçou nisso uma vez — `WITH … AS` não é tabela inexistente).

### 2. `descrever_tabela` aceita lista de tabelas — ✅ implementado 2026-09-04

**Análogo:** onde a multiplicidade é esperada, o parâmetro é array
(`ToolSearch` recebe `select:a,b,c`; `SendUserFile` recebe `files[]`).

**Falha observada:** item 12, ponto 2 — `dicasDeJoin` foi escrita pra comparar
duas tabelas, mas *"o modelo sempre chama uma tabela por chamada"*, então a
dica nunca disparou. O commit `572d64e` contornou isso lembrando as últimas 6
tabelas descritas; **é workaround**. A correção na interface é aceitar
`tabelas: string[]` e deixar o plural ser o caminho natural: quem vai juntar
duas tabelas as descreve juntas, e a dica de junção sai na mesma resposta.

Mantém-se a memória de sessão do `572d64e` como rede de segurança para quando
o modelo ainda chamar uma de cada vez — o caminho singular ficou byte-a-byte
igual em `mcp.ts`, a forma plural é um `if` novo antes dele.

### 3. Lembretes de estado grudados no resultado, como o `system-reminder` — ✅ implementado 2026-09-04

**Falha observada:** três, todas da mesma família — 38 repetições da mesma
junção (item 12), parar num plano esperando aprovação humana que não existe
(`regras.md`, laço), e aprovar 467 inventado sem nunca ter consultado (item
13). As três foram tratadas com uma checagem dedicada cada. O padrão geral é
mais barato: **um bloco curto de estado anexado ao retorno das ferramentas**,
quando (e só quando) a condição vale.

O que valeria a pena carregar, tudo já em memória no processo:

- `consultas: 12/30` — o orçamento existe, mas hoje o modelo só descobre que
  existe quando estoura;
- `tabelas descritas: A, B` — torna visível o que a proposta 1 exige;
- `junções já tentadas sem linha: <assinatura> ×2` — o disjuntor conta isso
  desde o item 12, mas só fala na 3ª. Mostrar o placar desde a 1ª é a
  diferença entre avisar e deixar reincidir.

Não toca no prefixo, portanto **não custa o 44x**. Não gasta turno: viaja em
resultado que já ia voltar.

`estadoFooter()` em `mcp.ts` grudou `consultas: N/30` e `tabelas descritas: …`
em toda resposta de `consultar` (sucesso, replay idempotente e zero-linhas). O
placar da MESMA junção também mudou de "só fala na 3ª" para "fala desde a 2ª"
(`repeticoes > 1`) — o `⚠ pare` continua reservado para `LIMIAR_REPETICAO`,
que é a única frase com força de parar.

### 4. Instrução negativa nas descrições que já existem — ✅ implementado 2026-09-04

O texto *"Do NOT re-read a file you just edited"* custa 15 tokens e mata uma
classe inteira de turno desperdiçado. Os equivalentes aqui, para colar nas
descrições de `harness/mcp.ts`:

- `descrever_tabela`: *"o resultado não muda dentro desta pergunta — não chame
  duas vezes para a mesma tabela"*;
- `consultar`: *"não reenvie a mesma junção variando só `SELECT`, `WHERE` ou
  `LIMIT` — se voltou zero linhas, o que precisa mudar é o `ON`"*.

É a intervenção mais barata do documento e a que mais depende de o modelo
obedecer prosa — ou seja: fazer, mas não contar com ela sozinha (é o mesmo
raciocínio que criou o `revisar_resposta` ao lado da instrução de persona).
As duas frases entraram nas descrições de `descrever_tabela` e `consultar` em
`mcp.ts` — cobertas em código pela proposta 5 (que não depende de prosa), a
descrição é a segunda camada, não a única.

### 5. Curto-circuito idempotente — a chamada repetida devolve o que já devolveu

**Análogo:** `Read` dizer *"do NOT re-read a file you just edited — a harness
rastreia o estado do arquivo pra você"*. A instrução só é honesta porque o
lado do servidor de fato sabe.

**Falha observada:** a classe mais cara do head-to-head — **5 de 21 chamadas**
(12, 13, 18, 20, 21), sendo três byte-idênticas entre si. O modelo não estava
confuso: estava reconstruindo por SQL um schema que `descrever_tabela` já
tinha dado, porque nada no diálogo lembra que ele já o tem.

**A camada:** `mcp.ts` já guarda `tabelasDescritas` (commit `572d64e`).
Basta:

- `descrever_tabela` de tabela já descrita → devolve o mesmo texto com um
  prefixo *"você já descreveu esta tabela no passo N; o resultado não muda
  nesta pergunta"* (custo: zero, é tudo local);
- `consultar` com SQL byte-idêntica a uma já executada → recusa **sem ir ao
  beelink**, devolvendo o resultado anterior e dizendo que é o mesmo. É o
  disjuntor do item 12 generalizado de "mesma junção" para "mesma consulta",
  e mais barato, porque não gasta a ida.

Uma variante de `SELECT * … LIMIT 1` sobre tabela já descrita pode ainda ser
rejeitada com a mensagem *"o schema você já tem; se o que falta é ver VALOR de
exemplo, diga isso projetando as colunas"* — mas isso já é heurística, então
fica separado do curto-circuito exato, que é seguro.

### 6. Argumento não declarado é erro, não silêncio

**Falha observada:** chamada 6 — `listar_datasets({"dataset":"br_transferegov"})`.
O schema da ferramenta não tem `dataset`; o argumento foi ignorado calado e
voltaram os 212 datasets. O modelo queria `listar_tabelas` e recebeu uma
resposta grande e plausível, que é o pior retorno possível: não corrige e
ainda enche o contexto.

**A camada:** validar as chaves recebidas contra o `inputSchema` e rejeitar as
desconhecidas nomeando a ferramenta provável (*"`listar_datasets` não aceita
`dataset` — você quis dizer `listar_tabelas`?"*). Vale para as 6 ferramentas.
Barato e sem falso positivo: um argumento que não existe no schema nunca é
intencional.

### 7. Portar `resolve_join` — a única que precisa ser medida antes de adotar

Descrita na seção da meta. Uma ferramenta local que responde *"como estas
duas se juntam, e se não se juntam, por quê"* sem ida ao beelink. Fonte já
existe em `docs/context/bridges.yaml`, e `pontes.ts` já lê o arquivo —
`conceitoDaColuna` e `semColunaComum` são metade da implementação.

**Por que fica por último apesar de ser a maior alavanca:** é a única que
aumenta a superfície de ferramenta (6→7), e `regras.md` tem medição contrária
a isso. O teste tem que ser A/B no conjunto dourado, não impressão: se o
recall de escolha de tabela cair, não compensa.

## Achado, não proposta: `capRows` não ensina no corte por linhas — ✅ corrigido 2026-09-04

Encontrado lendo `sqlguard.ts` para escrever este documento. `capRows` tem
duas formas de truncar e só uma ensina:

| Corte | Devolve | Tem `note`? |
|---|---|---|
| por tamanho (`size`) | linhas + `truncated`/`returned`/`total` | **sim** — *"Escolha as colunas em vez de `*`, ou agregue no SQL"* |
| por linhas (`total > 200`) | linhas + `truncated`/`returned`/`total` | **não** |

Os campos numéricos estão lá, então o dado não mente. Mas é a mesma forma dos
erros que este projeto já catalogou como perigosos: **silencioso e plausível**
— 200 linhas devolvidas onde havia 5.000 podem ser lidas como o conjunto
inteiro, que é a família do bug da Rodada 6 (573 reportado como total, um
grupo do `GROUP BY` lido como o todo). `alertasDeSanidade` cobre o caso do
`GROUP BY`, não cobre o do truncamento.

Conserto: uma linha em `sqlguard.ts`, `note` também no ramo `cappedBy ===
"rows"`, dizendo que há `total` linhas e que o número completo precisa sair de
uma agregação no SQL, não da contagem do que voltou. Feito; teste em
`sqlguard.test.ts` confere que o `note` existe e cita o `total`.

## O que NÃO copiar

Registrar isto importa tanto quanto as propostas — as três abaixo são boas no
Claude Code e **erradas aqui**, por motivo medido:

| Mecanismo | Por que não |
|---|---|
| **Divulgação progressiva de ferramenta** (`ToolSearch`) | Resolve contexto quando há dezenas de ferramentas. Aqui são 6, e `regras.md` já mediu que *um 26B em q4 acerta mais entre 5 ferramentas do que entre 20*. Buscar schema custaria um turno para economizar centenas de tokens que já cabem. Só passa a valer se o harness chegar a ~15+ ferramentas |
| **Chamadas independentes em paralelo no mesmo turno** | Minha instrução manda batelar chamadas independentes. Aqui seria **contraindicado**: o item 10 do `backlog.md` mede que o tool call do Gemma já cai como texto solto em 4 de 6 sessões, sem parser reconhecer. Pedir várias por turno compõe um bug bloqueador conhecido em vez de contorná-lo |
| **Subagentes** | O isolamento que eles dão aqui já vem de graça: um processo `dsh` por pergunta (`pergunte.ts`), estado nascendo e morrendo com ela. Delegação exigiria do 26B um julgamento de escopo que ele não demonstrou nem para escolher tabela irmã (24 das 36 falhas do conjunto são o parente errado) |

## Ordem, agora por contribuição MEDIDA no traço

Ordem revisada depois da correção de contagem acima — as duas primeiras são as
únicas com evidência forte e direta:

| # | Proposta | Evidência | Custo | Risco de falso positivo | Status |
|---|---|---|---|---|---|
| 1 | **5 — curto-circuito idempotente** | **forte** — 12→18 executou duas vezes a mesma SQL no beelink; com a 21, três tentativas da mesma coisa | baixo, estado já existe | nenhum no caso byte-idêntico | ✅ |
| 2 | **6 — argumento não declarado é erro** | **forte** — chamada 6 devolveu 212 datasets em silêncio | trivial | nenhum | ✅ |
| 3 | achado do `capRows` | análoga à Rodada 6 (573 como total), não medida aqui | 1 linha | nenhum | ✅ |
| 4 | 4 — instrução negativa | média — cobre a repetição do que já foi rejeitado (15, 17, 20) | tokens já pagos | — | ✅ |
| 5 | 3 — lembretes de estado | média — mesma classe da 4, mais caro | formato de resposta muda | — | ✅ |
| 6 | 2 — `descrever_tabela` plural | estrutural, sem falha nova atrás | assinatura muda | — | ✅ |
| 7 | **1 — pré-condição** | **fraca** — a evidência evaporou na releitura (ver ⚠ na proposta) | baixo | baixo, mas é camada sem caso observado | implementada, **desligada** (`HARNESS_EXIGE_DESCRICAO`) |
| 8 | **7 — portar `resolve_join`** | a maior alavanca isolada do traço | 6→7 ferramentas | **real** — exige A/B | 🔵 pendente — precisa medir antes |

Todas as linhas ✅ foram implementadas em 2026-09-04, testadas onde havia
suite pra testar (`sqlguard.test.ts`) e verificadas manualmente onde não havia
(`mcp.ts` não tem teste próprio — as peças que reusa, `dicasDeJoin`/`semColunaComum`/
`colunasDe`, já são testadas por `catalogo.test.ts`/`patch.test.ts`). Falta só
rodar de novo a pergunta de 5 fontes (item 12/13 do `backlog.md`) contra o
código atualizado para medir se o placar 74→24 chamadas melhora mais — nenhuma
dessas seis mudou o comportamento das camadas já medidas, só tornou o estado
existente visível mais cedo. A linha 8 continua a única que exige A/B antes de
entrar: não implementada.

## O placar de hoje, e o que ele não prova

Rodada do `pergunte.ts` em 2026-09-04 com o `572d64e` no ar, mesma pergunta
de 5 fontes (sessão `53ac1869`), contra a que morreu em 2026-09-03
(`358f388b`):

| | antes | depois |
|---|---|---|
| tool calls | 74 | **24** |
| SQLs | 55 | **15** |
| repetições da MESMA junção | **38** | **0** |
| aviso de junção antes da 1ª SQL | não existia | **disparou no passo 5** |
| desfecho | SIGKILL 40 min, sem resposta | SIGKILL 40 min, sem resposta |

**O modo de falha patológico acabou** — zero repetição da mesma junção, e o
modelo trocou de estratégia sozinho depois do aviso, indo achar
`br_transferegov` (a rota que a sessão morta nunca encontrou em 55 SQLs).

**E mesmo assim não convergiu.** Duas ressalvas que impedem declarar vitória:

1. O beelink caiu aos ~31 min da rodada; as chamadas 22-24 são sondas de
   conectividade (`SELECT 1`) e 11 dos 24 resultados são erro. O final é
   contaminado por infra, não por lógica.
2. O gabarito desta pergunta **não é um número**: `docs/respostas.md` marca
   T21-1/2/3/5 como ⏳ pendentes (*"exigem identificar fornecedor por CNPJ
   recorrente… fica para uma passada de resolução de entidade dedicada"*).
   O desfecho correto seria concluir com fundamento que não dá por junção
   direta — e o modelo não concluiu nada. **Não repetir não é o mesmo que
   terminar**, e é essa a distância que os itens 1, 5 e 6 atacam.

### Achado lateral que pode desbloquear o T21

Tanto o Gemma (passo 6, sozinho) quanto o traço Claude (chamada 3) chegaram à
mesma rota que o gabarito não considerou: `br_transferegov.planos_acao` tem
`valor_repasse_emenda_plano_acao` (marca o dinheiro de emenda) e liga por
`id_plano_acao` a `br_transferegov.transferencias`, que já carrega
`cnpj_favorecido_empenho` — **o CNPJ do fornecedor, sem passar por
`cgu_licitacao_contrato`**. São 25.969 + 4.248 linhas, contra os 100 mi+ que
`respostas.md` dá como o motivo do bloqueio. Não verificado: o beelink caiu
antes da consulta que compararia os formatos de CNPJ das três pontas
(transferegov × `br_tcu_inidoneos.empresas` × `br_pgfn_dividaativa.divida`,
ambas com `CPF_CNPJ`). **É a primeira coisa a rodar quando o beelink voltar** —
se casar, T21 sai de ⏳ por uma rota barata.

## Ver também

- [`backlog.md`](backlog.md) itens 12 e 13 — as falhas que sustentam as
  propostas 1, 3 e 4
- [`regras.md`](regras.md) — prefixo estável, superfície de ferramenta,
  laço vs. pipeline; as três restrições que descartam metade das ideias acima
- [`harness_bpe.md`](harness_bpe.md) — a proposta 3 é a mesma coisa que o
  paper chama de **Progress**, chegando por outro caminho: lá como scaffold
  treinável, aqui como campo no retorno da ferramenta
