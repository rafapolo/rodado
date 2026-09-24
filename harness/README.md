# `harness/` — apuração local com Gemma 4, sem API

Pergunta em pt-BR → datasets → schema → SQL → **portão** → número conferido → prosa.
Tudo no beelink, sem chamada de API paga.

Bun + TypeScript. As medições que sustentam cada escolha estão em
[`../gemma_stats.md`](../gemma_stats.md); o plano completo e o catálogo de
refino em [`tasks/`](tasks/README.md).

## O fluxo

Uma pergunta, do jeito que roda hoje (`pergunte.ts` → dsh → as ferramentas de
`mcp.ts`). Quem decide a ordem é o modelo, dentro do laço do dsh — ver "O papel
do dsh"; as setas abaixo são o caminho típico, não uma sequência fixa.

```mermaid
flowchart TD
    P["pergunta em pt-BR"] --> PRE

    subgraph PRE["prefixo estável — persona.md + ferramentas, ~4.400 tok, lido 1x e cacheado"]
        direction LR
        R["como trabalhar"] --- D["catálogo de 230 datasets<br/>com pistas de irmão"]
    end

    PRE --> S1["modelo escolhe o dataset<br/>pelo catálogo, sem ferramenta"]
    S1 --> S2["listar_tabelas<br/>+ descrição da tabela principal"]
    S2 -.->|"se precisar"| S3["descrever_tabela / definicao_de_calculo<br/>outras tabelas, códigos, cálculo verificado"]
    S2 --> S4["modelo escreve SQL"]
    S3 -.-> S4

    S4 --> G{{"consultar → PORTÃO<br/>portao.ts"}}
    G -->|"erro de forma<br/>(LIMIT, dataset sem tabela)"| FIX["repara() conserta<br/>e avisa"]
    FIX --> X
    G -->|"erro de significado<br/>(partição, CID, coluna)"| S4
    G -->|passa| X["executa no beelink<br/>beelink.ts · -readonly"]

    X --> A{{"alertas junto do resultado<br/>zero linhas, n=0, recorte da pergunta<br/>não aplicado, nota da tabela"}}
    A -->|"modelo corrige"| S4
    A --> OUT["resposta em prosa<br/>número, recorte, órgão de origem"]

    style G fill:#c0392b,color:#fff,stroke:#7b241c
    style A fill:#8e6f1e,color:#fff,stroke:#5c4813
    style PRE fill:#1a5276,color:#fff,stroke:#0b2e40
    style OUT fill:#1e6f42,color:#fff,stroke:#0f3d24
```

Recuperação, validação e execução são determinísticas — código, não julgamento
do modelo. O modelo escolhe o dataset, escreve a SQL, lê o que voltou e redige;
tudo que ele recebe de volta (rejeição, conserto, alerta) chega como resultado
de ferramenta, e é isso que o faz corrigir sem retry escrito à mão. Pergunta
direta: ~5 turnos, mediana de 63 s.

## O portão

`checkReadOnly` sozinho valida tipo de statement e palavra proibida. Isso basta
enquanto quem dirige é uma pessoa, porque a disciplina de partição e de
codificação está em prosa no docstring do `run_sql`. **Prosa em docstring não é
enforcement para um modelo autônomo.**

As camadas rodam em ordem de custo — as locais primeiro, para que as tentativas
de reparo sejam gastas em erro real e não em ida à rede:

```mermaid
flowchart LR
    SQL["SQL do modelo"] --> L1

    L1["1 · read-only<br/>sqlguard.ts"] --> L2
    L2["2 · tabela existe<br/>FROM dataset sem tabela"] --> L3
    L3["3 · coluna existe<br/>coluna inventada"] --> L4
    L4["4 · filtro de partição<br/>catalog.parquet: rows"] --> L5
    L5["5 · LIMIT<br/>se não agrega"] --> L6
    L6["6 · codificação<br/>CID, coded_differently"] --> L7
    L7["7 · EXPLAIN<br/>única ida ao beelink"] --> OK["executa"]

    L1 & L2 & L3 & L4 & L5 & L6 & L7 -.->|"rejeita"| REP["mensagem que<br/>ensina o conserto"]
    REP -.->|"máx. 3 tentativas"| SQL

    style L4 fill:#c0392b,color:#fff
    style L6 fill:#c0392b,color:#fff
    style REP fill:#8e6f1e,color:#fff
    style OK fill:#1e6f42,color:#fff
```

As duas camadas em vermelho existem por causa de erros **que o Gemma cometeu de
verdade**, medidos no beelink em 2026-09-01:

| Camada | O que o modelo escreveu | Por que é caro |
|---|---|---|
| **4 · partição** | `SELECT COUNT(*) FROM br_ms_sim.microdados` — sua primeira tool call | Varredura completa segura o lock do DuckDB por horas. O incidente de 2h do `CLAUDE.md` tem exatamente esta forma. |
| **6 · codificação** | `causa_basica BETWEEN 'X60' AND 'X84'` | CID é guardado **sem ponto** (`X840`), e `'X840' > 'X84'` — o grupo X84 some inteiro. **726 contra 789 reais: 8% a menos, com número plausível.** |

O segundo é o modo de falha que importa: não dá erro, dá um número que passa
despercebido. `harness/portao.test.ts` trava os dois casos.

**Erro de forma o portão conserta sozinho** (2026-09-23). Falta de `LIMIT`,
amostra sem `COUNT(*) AS n` e `FROM dataset` sem tabela custavam um turno do
modelo cada (~15 s) para um conserto mecânico. `repara()` corrige antes de
rodar e avisa no resultado ("Ajustei a consulta antes de rodar: ..."). O que
muda o significado da SQL — partição, codificação, coluna inventada — continua
voltando ao modelo.

## Por que catálogo no prefixo, e não busca por embedding

Medido contra o conjunto dourado do projeto:

| Estratégia de recuperação de dataset | Recall | Casos perfeitos |
|---|---|---|
| `search_tables` — embedding doc2query | 52,9% | — |
| catálogo de 212 nomes no prefixo | 91,3% | 85,7% |
| **+ 43 exemplos resolvidos no prefixo** | **97,8%** | **96,4%** |

Medido em 28 casos de teste, com `bun harness/avalia_datasets.ts [--fewshot]`.
Os exemplos vêm de `respostas.md` — ele não é só gabarito, ensina qual dataset
serve qual tipo de pergunta. Divisão treino/teste **por tema**, não por caso:
dentro de um tema as 5 perguntas são variações do mesmo cruzamento, então
dividir por caso deixaria o vizinho quase-idêntico no prefixo e mediria memória.

O few-shot é grátis **por pergunta**: o prefixo cresce para ~11k tokens e o
`prefill` medido continua em ~45 — só a pergunta é prefilada.


Os nomes já são semânticos — `br_ms_sim` é Ministério da Saúde / Sistema de
Informação sobre Mortalidade. O embedding comprime isso num vetor e perde; ler a
lista literal não perde. E como o cache de prefixo do `llama-server` reaproveita
o KV do prefixo comum, os 212 nomes custam **uma vez**:

| chamada | tokens prefilados | tempo |
|---|---|---|
| 1ª (frio) | 1.165 | 19,5 s |
| 2ª | 5 | **0,44 s** |

Estabilidade do prefixo é, por isso, **restrição de arquitetura e não
otimização**: qualquer coisa variável no prefixo (timestamp, ordem não
determinística) evapora o 44x sem ninguém perceber.

## Por que laço agêntico, e não pipeline fixo

A comparação que decide o desenho — mesmas 5 perguntas, mesmo modelo, mesmo
portão, mesmo beelink; muda só quem decide a sequência de passos:

| | dsh + MCP (agêntico) | pipeline fixo (`laco.ts`) |
|---|---|---|
| **Correto** | **3/3 = 100%** | **0/3 = 0%** |
| Tempo | ~400 s | 61 s |

O pipeline fixo é 14x mais rápido e não serve. As três falhas dele nomeiam o que
o laço faz de essencial, e **nenhuma é erro de SQL**: respondeu 573 em vez de 789
(agrupou por sexo e reportou um grupo só); devolveu o código `3550308` em vez de
"São Paulo", por não ir ao diretório; e bateu 4x no portão sem recuperar. São
erros de não iterar.

Rode você mesmo com `bun harness/compara.ts <arquivo>` — em sequência, nunca em
paralelo, senão os dois disputam o mesmo `llama-server` e o tempo sai errado.

## O papel do dsh

O **dsh** (DeepSeek Harness) é o laço agêntico — e **não sabe que o portão
existe**. Não valida nada, não conhece SQL, CID nem partição. O trabalho dele é
só repassar mensagens entre o modelo e as ferramentas até sair uma resposta
final: manda o turno ao modelo, executa a chamada de ferramenta que vier,
devolve o resultado, repete. Guarda cada sessão em disco, que é o que
`sessao.ts` lê.

Onde cada peça fica, de fora para dentro:

```mermaid
flowchart TD
    L["pergunte.ts / lote.ts<br/>um processo dsh por pergunta;<br/>sessão nova se ele morrer"] --> D
    D["dsh — o laço<br/>turno do modelo → executa ferramenta → devolve → repete"]
    D <-->|"cada turno"| G["guarda.ts<br/>repete o turno que volta vazio"]
    G <--> M["llama-server (Gemma)"]
    D <-->|"chamada de ferramenta"| T["mcp.ts — as ferramentas"]
    T --> C["consultar"]
    C --> P{{"PORTÃO<br/>7 camadas"}}
    P -->|passa| B["DuckDB no beelink"]
    P -.->|"rejeita: texto que<br/>ensina o conserto"| T

    style P fill:#c0392b,color:#fff,stroke:#7b241c
    style D fill:#1a5276,color:#fff,stroke:#0b2e40
```

O portão mora **dentro da ferramenta `consultar`**, e quem o roda é o `mcp.ts`.
Na pergunta dos óbitos por suicídio no RJ em 2020:

1. O dsh manda a pergunta ao Gemma.
2. O Gemma responde "chame `consultar` com `causa_basica BETWEEN 'X60' AND 'X84'`".
3. O dsh repassa ao `mcp.ts`; o portão reprova e devolve um texto: "CID é
   guardado sem ponto, use `substr(...)`".
4. O dsh **não sabe que aquilo é uma rejeição** — para ele é só o resultado da
   ferramenta, e ele entrega ao Gemma como entregaria qualquer resultado.
5. O Gemma lê, reescreve a SQL e chama `consultar` de novo. Passa, roda, volta 789.
6. O Gemma redige a resposta; o dsh termina.

É por isso que o portão não precisa de retry escrito à mão: a rejeição chega ao
modelo como resultado de ferramenta, o laço do dsh continua girando e o conserto
acontece sozinho. O `laco.ts` era a versão sem o dsh, com a sequência fixa — 0/3
contra 3/3 (ver "Por que laço agêntico" acima).

**Divisão de trabalho: o dsh decide a sequência dos passos; o harness — portão,
guarda, persona — decide o que é permitido e o que vale.**

Tudo que é do rodado entra pelo patch (`dsh/rodado.patch.yml`), rodado como
`bunx dsh --profile headless --patch harness/dsh/rodado.patch.yml "<pergunta>"`:

| O patch | Para quê |
|---|---|
| provider `beelink-local` | aponta o dsh para o Gemma local (pela `guarda.ts`, via `HARNESS_LLM_URL`), com `reasoningEfforts: false` |
| `mcp-rodado` | monta `harness/mcp.ts` como único servidor de ferramentas |
| `bash`, `fs`, `web`, subagentes, skills, todo… desligados | o dsh vem com shell, e o Gemma já usou `bash` para chamar o DuckDB direto por SSH, **por fora do portão**. Sem eles, o único caminho até o dado é o `consultar` |
| `agent-instructions` com `maxBytes: 0`, sem título de sessão por LLM, sem `plan-mode` | tira do prompt o `CLAUDE.md` que o dsh injetava sozinho e as chamadas extras ao único slot |
| `system-prompt` lido de `dsh/persona.md` | papel, como trabalhar e o catálogo, gerados por `persona.ts` |

As duas camadas em volta existem porque o dsh falha em dois lugares:

- **`guarda.ts`** — às vezes o Gemma devolve um turno vazio e o dsh encerra a
  sessão como se tivesse terminado. A guarda fica no meio, vê o turno vazio e
  repete a requisição antes que o dsh perceba (ver "A guarda").
- **`lote.ts`** — se mesmo assim a sessão morrer, abre outro dsh do zero. Última
  linha.

## O contexto é o gargalo

| | 2k de contexto | ~18k (dentro do laço) |
|---|---|---|
| Prefill | 50,5 t/s | 15 t/s |
| Geração | 13,3 t/s | 9 t/s |

Cai ~3x, e o system prompt do dsh eram **14.213 tokens**. Desligar as ferramentas
que este harness não usa levou a **6.849** — corte de 52%, com a correção intacta
e ~30% menos tempo por pergunta.

Duas dessas ferramentas eram um buraco, não só peso: o modelo descobriu a `bash`
e escreveu `ssh beelink '~/bin/duckdb ...'` direto, **passando por cima do portão
inteiro**. Todo o trabalho de validação vira decoração se o modelo tem shell.

**2026-09-22, o que o prompt tinha virado.** Medido com o `/tokenize` do próprio
servidor no 1º turno real: 9.475 tokens, dos quais **8.424 (89%) eram o
`CLAUDE.md` da raiz**, injetado pelo plugin `agent-instructions` do dsh —
instruções para o Claude Code, com ferramentas que este servidor MCP nem tem.
Desligado (`maxBytes: 0` no patch), junto com o título de sessão por LLM e o
`plan-mode`. No lugar entrou o que o modelo usa: `dsh/persona.md` (papel, como
trabalhar e o catálogo com as pistas de irmão, 3,5 mil tokens, no prefixo
cacheado). O contexto máximo por pergunta caiu de ~19k para ~5–9k, e os turnos
que degeneravam estavam todos acima de 17k.

As saídas das ferramentas também encolheram (`formato.ts`): a descrição de uma
tabela larga resume as colunas por prefixo e lista por inteiro só as que decidem
a SQL (partição, chave, codificadas) — `escola` caiu de 5.660 para 1.841 tokens,
com `filtro` para abrir um grupo —, e o resultado de `consultar` vai como tabela
de texto em vez de JSON com a chave repetida em cada linha.

**2026-09-23, menos turnos.** Cada turno custa ~14,5 s e as ferramentas ~1 s
por pergunta inteira: o que pesa é o número de turnos e os tokens novos em cada
um, não a consulta. Detalhe em [`tasks/velocidade.md`](tasks/velocidade.md):

- `listar_tabelas` já traz a descrição da tabela principal do dataset, e o
  `descrever_tabela` que vinha logo depois sumiu.
- `revisar_resposta` saiu (151 chamadas, **nenhuma** rejeição). O recorte da
  pergunta (ano, estado, bioma) passou a ser conferido no resultado de
  `consultar`, na hora.
- `listar_datasets` saiu: o catálogo já está no system prompt.
- Em tabela com mais de 8 colunas codificadas, a lista de códigos vai inteira
  só nas colunas ligadas à pergunta (raiz do nome ou de um rótulo: "rurais" ↔
  "Rural"); as outras mostram a marca `(códigos)` e abrem com `filtro`. **Nenhuma
  coluna some** — o `filtro` que escondia `tipo_localizacao` fez o modelo
  concluir que o Censo Escolar não classifica escola rural. SIM 3.506 → 1.580
  tokens, RAIS 3.601 → 1.369.

## A guarda

O item 10 de `tasks/backlog.md` — o turno que "volta vazio" e mata a sessão
inteira — foi visto no byte bruto em 2026-09-22 (log verboso do llama-server).
Não é um parser engolindo a chamada: o Gemma decodifica **3 tokens**,
`<|channel>` `thought` `<tool_call|>` (a tag de fechamento, sem abertura), e
para em EOS. Não há chamada nenhuma a resgatar. O upstream `f072b10`
(PR #29115, conserto da gramática de tool call do Gemma 4) foi aplicado no
beelink e **não muda isso** — reproduziu igual depois do rebuild.

`guarda.ts` fica entre o dsh e o llama-server (`HARNESS_LLM_URL`, que
`pergunte.ts` e `lote.ts` apontam para ela):

- segura os pedaços do turno até aparecer `content` não vazio ou `tool_calls` —
  com o raciocínio desligado, um turno saudável sempre produz um dos dois;
- se o turno termina sem nenhum, **repete a mesma requisição**. O prefixo já está
  no cache do servidor, então repetir custa segundos, não os 5–7 min de uma
  sessão nova (o workaround anterior, em `lote.ts`, que continua como última linha);
- se o pensamento contém uma chamada inteira (`<|tool_call>call:nome{...}<tool_call|>`,
  os casos 4/6 do item 10), extrai e devolve como `tool_calls`.

- da 2ª tentativa em diante, **proíbe `<|channel>`** (token 100, `logit_bias`):
  todo turno degenerado começa por ele e, com o raciocínio desligado, o modelo
  nunca precisa gerá-lo. Repetir a requisição idêntica às vezes caía no mesmo
  caminho 4 vezes seguidas.

Em 144 perguntas medidas (1.024 turnos): 47 turnos repetidos (4,6%), 4
resgatados, 4 perdidos — todos antes da proibição do `<|channel>` entrar, e as
duas perguntas afetadas terminaram certas na sessão nova. Nenhuma ficou sem
resposta. Detalhe em [`tasks/avaliacao_diretas.md`](tasks/avaliacao_diretas.md).

## Módulos

| Arquivo | Papel |
|---|---|
| `catalogo.ts` | `catalog.parquet` (linhas por tabela → camada 4) + schema local (colunas). Cache em `dados/catalogo.json`; `bun harness/catalogo.ts --atualiza` |
| `portao.ts` | as 7 camadas, e `repara()` para o erro de forma |
| `sqlguard.ts` | `checkReadOnly` + `capRows` — porte fiel de `mcp_server.py`, trazido de `ask-web` |
| `beelink.ts` | executor SSH+DuckDB, **com `-readonly`** |
| `metricas.ts` | os 12 cálculos verificados de `metrics.yaml` — busca exata por nome ou sinônimo, nunca por similaridade |
| `anos.ts` | faixa de anos por tabela (377 cacheadas) |
| `pontes.ts` | dicas de join das pontes conferidas de `bridges.yaml` |
| `mcp.ts` | servidor MCP: 4 ferramentas (`listar_tabelas`, `descrever_tabela`, `definicao_de_calculo`, `consultar`), o portão entre elas |
| `guarda.ts` | proxy entre o dsh e o llama-server: repete o turno degenerado e resgata a chamada presa no pensamento (ver "A guarda") |
| `persona.ts` | gera `dsh/persona.md`, o system prompt do laço; `--confere` acusa quando está velho |
| `dicionarios.ts` | o significado dos códigos (`'2'=Rural`) ao lado da coluna, de `{dataset}.dicionario`. Cache em `dados/dicionarios.json`; `--atualiza` |
| `valores.ts` | os valores reais das colunas de texto sem dicionário (`'estadual'`, `'prefeito'`), calculados na 1ª descrição e guardados em `dados/valores.json` |
| `semantica.ts` | notas curadas (`dados/notas.json`), o cálculo verificado da tabela (`metrics.yaml`) e as tabelas reais mais parecidas com um nome inventado |
| `recortes.ts` | ano, estado e bioma que a pergunta nomeia — o resultado de `consultar` avisa quando a SQL não os aplicou |
| `formato.ts` | como as ferramentas escrevem para o modelo: descrição compacta (códigos só nas colunas ligadas à pergunta), resultado em tabela de texto |
| `sessao.ts` | lê uma sessão do dsh como transcrição (cada chamada, a SQL inteira, o resultado) |
| `laco.ts` | o pipeline fixo — **não é caminho de produção** (0/3 contra 3/3 do agêntico). Sobrevivia como esqueleto do experimento DuckDB-NSQL-7B, que saiu do plano em 2026-09-24 — **remoção pendente**; a comparação que ele provou já está registrada aqui e em `tasks/regras.md`, e o código sai por `git show` |
| `lote.ts` / `compara.ts` | benchmark de perguntas abertas |

## Procedência e uma correção

`sqlguard.ts` e `beelink.ts` vêm do branch `ask-web`, onde já eram porte fiel do
`mcp_server.py`. As camadas 2 e 3 do portão são porte de
`validarTabelas`/`validarColunas` de `web/static/ask.js` do mesmo branch — lá
elas apanharam desses erros em produção primeiro.

**Uma correção aplicada na cópia:** `web/src/beelink.ts` do `ask-web` invoca o
DuckDB **sem `-readonly`**. A CLI pega lock exclusivo do arquivo mesmo num
`SELECT` puro, e uma conexão read-write bloqueia toda outra sessão no mesmo
`.duckdb` — inclusive as read-only. O `mcp_server.py:310` tem a flag com
comentário explicando; o porte a perdeu. Aqui está corrigida — **vale levar de
volta ao `ask-web`**.

## Rodar uma pergunta

```bash
bun harness/pergunte.ts "Quantos óbitos por suicídio houve no RJ em 2020, por sexo?"
```

Sai a resposta em prosa, com os números que o modelo apurou. Pergunta direta
leva **~1 a 1,5 min** — na rodada de 2026-09-23 (`benchmarks/lote_2026-09-231049.json`,
43 perguntas): 41/43 certas, média 96 s, **mediana 63 s** (76 s na rodada 5 de
[`tasks/avaliacao_diretas.md`](tasks/avaliacao_diretas.md); eram 5–10 min antes
do corte de contexto). Pergunta de pesquisa, cruzando três ou quatro fontes,
~10 min. Se o `llama-server` não estiver de pé, o comando diz exatamente o que
subir. Para ver o que o modelo fez: `bun harness/sessao.ts`.

Passa pelo caminho agêntico de propósito — ver a comparação acima.

## Rodar

```bash
bun test harness/                    # 169 testes
bun harness/catalogo.ts              # 230 datasets, 1024 tabelas
bun harness/catalogo.ts --atualiza   # rebusca no beelink após um sync
bun harness/anos.ts --atualiza       # faixa de anos por tabela

bun harness/avalia_datasets.ts       # escolha de dataset nas 274 perguntas
bun harness/lote.ts <arquivo>        # perguntas abertas pelo dsh, com gabarito
bun harness/compara.ts <arquivo>     # agêntico contra pipeline fixo
```

O arquivo de perguntas do `lote.ts` e do `compara.ts` é uma por linha, com o
valor esperado depois de um TAB quando houver:

```
Quantos óbitos por suicídio houve no RJ em 2020?	789
Qual foi o PIB per capita médio dos municípios de MG em 2020?	32066
Quantos CAPS existem por estado no CNES?
```

Sem o valor esperado o caso ainda roda, mas só mede se **respondeu** — nunca se
acertou. Foi assim que uma resposta "não foram encontrados óbitos" entrou como
sucesso quando o certo era 789.

O modelo é servido pelo `llama-server` no beelink. `./harness/servidor.sh` sobe
(ou reinicia) com a config abaixo, abre o túnel e aquece o prefixo do laço com
uma pergunta trivial — sem isso a 1ª pergunta depois de subir paga ~75 s a mais.
Depois de mudar `persona.md`, `./harness/servidor.sh aquece-laco` refaz só o
aquecimento (`SEM_LACO=1` pula). A linha que ele roda:

```bash
llama-server -m ~/llm/gemma-4-26B_q4_0-it.gguf \
  -t 8 -c 32768 -np 1 --cache-ram 1024 \
  --chat-template-kwargs '{"enable_thinking":false}' \
  --host 127.0.0.1 --port 8099
```

Cada flag aí é uma medição, não gosto:

- **`-t 8`**, nunca 16: os 8 núcleos físicos já saturam a banda; com 16 o prefill
  cai 32%, a geração 31%, e o desvio-padrão cresce 10x.
- **`-np 1`**: o `-c` é **por slot**. Com os 4 slots padrão, `-c 65536` aloca 4x
  o KV sem avisar.
- **`--chat-template-kwargs`**: é o único jeito de desligar o raciocínio do Gemma.
  `reasoningEfforts: false` no dsh declara o modelo como não-raciocinante *para o
  harness* e não manda nada ao llama.cpp; `--reasoning off` também não resolve.
  Medido: 20,9 s → 4,7 s por turno de tool calling, com o tool call intacto.
- **sem `-ctk/-ctv q8_0`**: KV quantizado sai caro em CPU — desquantizar a cada
  operação de atenção domina o que economiza em banda. Prefill 15,8 → 50,5 t/s.
- **`--cache-ram 1024`**: o padrão (8 GiB de conversas guardadas na RAM do host)
  levou o servidor ao OOM killer em 2026-09-22 — ver `tasks/operacao.md`,
  "Memória do beelink". O binário é o do llama.cpp `f072b10`.

Do mac, abra o túnel antes (o servidor escuta só em loopback, de propósito):

```bash
ssh -f -N -L 8099:127.0.0.1:8099 beelink
```

As checagens de operação — o que quebra calado e o detector de cada coisa — estão
em [`tasks/operacao.md`](tasks/operacao.md).
