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

## 2. Rodar o laço nos casos com `n` conferido 🟡 ponte feita 2026-09-02, rodada ainda não começou

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
**A rodada em si não começou** — só o pré-requisito.

**Antes de rodar**, além do item 0: conferir as invariantes de
[`operacao.md`](operacao.md). Uma rodada de 3,2 h com o cache de prefixo
quebrado ou o raciocínio ligado é o desperdício mais caro disponível aqui — e a
tarefa 1 de lá (asserção de `prefilados`) existe exatamente para isso.

## 3. A prosa cita a ferramenta, não o órgão 🔴

As respostas mencionam `br_ibge_pib.municipio`. A convenção de
`pages/analises/results/` é citar o **órgão de origem** — nunca a tabela, nunca o
SQL. Hoje nenhuma resposta gerada sai publicável sem edição à mão.

**Conserto (duas metades):** instrução na etapa de prosa, **mais** uma checagem
que rejeite resposta contendo `br_[a-z_]+\.` — a instrução sozinha é do tipo que
o modelo obedece na maioria das vezes, e a checagem transforma "maioria" em
todas.

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
