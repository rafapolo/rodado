# MCP — o servidor de ferramentas sobre o espelho

`mcp_server.py`, na raiz do repo. Expõe o catálogo (`docs/context/`) e o
espelho DuckDB do beelink como ferramentas MCP para um agente (Claude
Desktop/Claude Code) — não é uma API REST, é uma lista de funções que um
modelo de linguagem chama em sequência, decidindo a cada passo qual chamar a
seguir a partir do resultado da anterior.

Números de hoje: 212 datasets, 904 tabelas (índice doc2query ainda cobre as 832 de 2026-08-23), índice doc2query com 6.464
perguntas sintéticas (uma por tabela em média ~8), 60 conceitos de join
documentados, 20 false friends, 7 métricas nomeadas, 3 hierarquias de rollup,
18 ferramentas ao todo. Nunca abre conexão DuckDB local — toda query roda no
`~/bin/duckdb` do beelink via SSH (ver `_run_sql_ssh`). Tudo local: parquet
em disco no beelink, sem storage em nuvem — é lá que dado recém-raspado
aparece primeiro.

## Como ler este documento

Três diagramas, cada um respondendo uma pergunta diferente:

1. **Arquitetura** — de onde cada ferramenta puxa dado (arquivo local vs SSH).
2. **Retrieval do `search_tables`** — como uma pergunta em português vira uma
   tabela candidata.
3. **O loop de iteração** — o que faz uma tentativa falha virar uma tentativa
   nova, e a diferença entre o que o *servidor* corrige sozinho e o que só o
   *agente* corrige.

---

## 1 · Arquitetura

Duas fontes de dado completamente separadas: arquivos estáticos carregados
uma vez na inicialização (`docs/context/*`, pequenos, cabem em memória) e o
SSH para beelink (a única forma de tocar dado real — parquet ou o catálogo
DuckDB de views).

```mermaid
flowchart LR
    subgraph client["Agente (Claude)"]
        LLM["LLM decide qual\nferramenta chamar"]
    end

    subgraph server["mcp_server.py"]
        direction TB
        T1["list_datasets\nlist_tables\ndescribe_table"]
        T2["search_tables"]
        T3["get_join_keys\nresolve_join\nexplain_column"]
        T4["get_metric\nlist_metrics\nrollup"]
        T5["run_sql"]
        T6["consultar_*\n(7 wrappers)"]
    end

    subgraph ctx["docs/context/ — carregado 1x no import"]
        direction TB
        C1["basedosdados-schema.json\n(_SCHEMA: 207 ds / 895 tbl)"]
        C2["doc2query_index.json +\ndoc2query_vectors.npy\n(6.464 perguntas sintéticas)"]
        C3["bridges.yaml\n(concepts / false_friends /\ncoded_differently / concept_aliases)"]
        C4["metrics.yaml · hierarchies.yaml"]
        C5["join_keys.md\n(152 seções, 92 auto-detectadas)"]
        C6["dicionario_coverage.json\n(168 tabelas, 45 datasets)"]
    end

    subgraph beelink["beelink (SSH)"]
        direction TB
        D1["basedosdados.duckdb\n(views sobre parquet)"]
        D2["~/rodado/&lt;dataset&gt;/&lt;tabela&gt;/*.parquet\n(fallback quando não há view)"]
        D3["curl ao vivo\n(CEP, Painel de Preços —\nnão dá pra espelhar)"]
    end

    LLM --> T1 & T2 & T3 & T4 & T5 & T6

    T1 --> C1
    T2 --> C2
    T3 --> C3 & C5
    T4 --> C4
    T5 --> D1
    T5 -. "Catalog Error /\nview antiga aponta pra\nbucket morto" .-> D2
    T6 -->|"cnpj, divida_ativa,\nstj, sisdepen, combustivel"| D2
    T6 -->|"cep, painelprecos"| D3

    style ctx fill:#eef,stroke:#88a
    style beelink fill:#efe,stroke:#8a8
```

**Por que dois caminhos para `run_sql`** — nem toda tabela do catálogo tem
view dentro de `basedosdados.duckdb` (dataset raspado independente do
espelho oficial da Base dos Dados cai primeiro em parquet puro). Quando o
DuckDB devolve `Catalog Error` ou uma view é um resquício de antes da
migração pra parquet local e aponta pra um bucket que não existe mais,
`run_sql` reescreve as referências `dataset.tabela` da própria query pra
`read_parquet(...)` e tenta de novo uma vez — automático, sem o agente
precisar perceber a distinção.

**Por que `-readonly` na conexão** — DuckDB toma um lock exclusivo no
arquivo `.duckdb` mesmo para um `SELECT` puro, a menos que a conexão seja
aberta com `-readonly`; qualquer conexão read-write bloqueia TODAS as
outras, inclusive tentativas read-only, até desconectar (várias sessões
deste projeto — humanas e de agente — costumam consultar o mesmo beelink ao
mesmo tempo). `_run_sql_ssh` já garante no nível SQL que nada escreve
(`_check_read_only`), então abrir a conexão em `-readonly` não perde nada e
elimina o lock exclusivo — corrigido em 2026-08-24 depois de um lock real de
outra sessão travar um teste cego por >1h (ver `tasks/done/mcp_search_refino.md`).
Um erro de lock depois desse fix significa que OUTRO processo abriu a
conexão sem `-readonly` — esperar, nunca `kill`: é quase sempre trabalho
real de outra sessão, não uma query travada.

---

## 2 · Retrieval do `search_tables` — doc2query, não keyword match

A versão anterior indexava um embedding por tabela sobre o texto
`"nome_coluna (TIPO), nome_coluna (TIPO)..."` — sopa de schema, quase
ortogonal a uma pergunta real (cosseno 0,08 contra 0,39 de prosa
equivalente). A versão atual indexa **uma pergunta sintética por vez**: um
LLM gerou ~8 perguntas que cada tabela responde, cada uma embedada
separadamente, no mesmo espaço da pergunta do usuário.

```mermaid
flowchart TD
    Q["pergunta do usuário\n(ex: gastos de campanha eleitoral)"]
    EMB["embed com o mesmo modelo\nque gerou o índice\n(paraphrase-multilingual-MiniLM-L12-v2)"]
    IDX[("6.464 perguntas sintéticas\nembedadas offline\n~8 por tabela")]
    SIM["cosseno contra cada uma\ndas 6.464"]
    MAX["por tabela: pega o MÁXIMO\nentre as perguntas dela\n(não a média)"]
    TOPK["ordena, corta em top_k\nacima de min_similarity\n(default 0.35)"]

    Q --> EMB --> SIM
    IDX -.-> SIM
    SIM --> MAX --> TOPK
```

**Por que máximo e não média** — uma tabela responde muitas perguntas
sintéticas diferentes; é a que casa com a pergunta real que importa. Média
dilui o melhor match com os irrelevantes da mesma tabela — testado e medido
pior (uma tentativa anterior com prosa+colunas juntas ficou em 2/15 de
recall). O resultado devolve o `text` da pergunta sintética que bateu, não
uma descrição da tabela — é assim que o agente lê "esta tabela responde:
`<text>`" em vez de confiar cegamente no nome.

Isso resolveu o recall **por tabela** (1/15 → 11/15 no conjunto de teste de
uma tabela só). Não resolve sozinho o recall **por conjunto de tabelas**: uma
pergunta que precisa de 3+ datasets ao mesmo tempo no mesmo `top_k` é uma
barra mais alta, medida em ~51% no conjunto-dourado dataset-level
(`tasks/douradas_perguntas.json` + `scripts/avalia_douradas_perguntas.py`) —
ver seção 4.

---

## 3 · O loop de iteração

Isto é o que a seção 2 sozinha não mostra: uma chamada de `search_tables`
que erra não é o fim da história para um agente real. Há dois tipos de
correção bem diferentes — uma automática dentro do próprio servidor, outra
que só existe porque o agente decide tentar de novo.

```mermaid
flowchart TD
    START(["pergunta do usuário"])
    SEARCH["search_tables(pergunta)"]
    GOODHIT{"algum resultado\nrelevante?"}
    DESC["describe_table\nnas 1-3 melhores candidatas"]
    OKCOLS{"colunas batem\ncom o que precisa?"}
    JOIN["resolve_join(a, b)\nse são 2+ tabelas"]
    SQL["run_sql(query)"]
    DBERR{"DuckDB\nretornou erro?"}
    CATERR{"Catalog Error /\nview antiga (bucket morto)?"}
    AUTORETRY["servidor reescreve pra\nread_parquet() e tenta de novo\n— automático, o agente\nnem precisa perceber"]
    OTHERERR["erro cru do DuckDB volta\npro agente\n(Binder Error...\nCandidate bindings: ...)"]
    FIX["agente lê o erro,\najusta a query\n(nome de coluna, join, cast)"]
    DONE(["resultado real"])
    REPHRASE["agente reformula a pergunta\nou tenta list_tables/browse\nmanual num dataset suspeito"]

    START --> SEARCH --> GOODHIT
    GOODHIT -- não --> REPHRASE -. "tentativa nova" .-> SEARCH
    GOODHIT -- sim --> DESC --> OKCOLS
    OKCOLS -- não, tabela errada --> REPHRASE
    OKCOLS -- sim --> JOIN --> SQL
    SQL --> DBERR
    DBERR -- não --> DONE
    DBERR -- sim --> CATERR
    CATERR -- sim --> AUTORETRY --> DONE
    CATERR -- não --> OTHERERR --> FIX -. "tentativa nova" .-> SQL

    style AUTORETRY fill:#dfd,stroke:#4a4
    style OTHERERR fill:#fed,stroke:#c84
    style REPHRASE fill:#fed,stroke:#c84
```

Verde = o servidor resolve sozinho (`_rewrite_to_read_parquet`, automático,
sem envolver o modelo). Laranja = correção que só acontece porque o agente
tem raciocínio e paciência para tentar de novo — nada no código força essa
volta, ela existe só quando quem está do outro lado é um agente e não um
único call-and-forget. É por isso que `run_sql` devolve o erro **cru** do
DuckDB (`tasks/done/mcp_search_refino.md` item 4): resumir a mensagem pra "mais
amigável" quebraria exatamente esse laço de correção laranja.

---

## 4 · O que já foi medido, e o que isso realmente prova

Duas métricas existem hoje para este servidor, e é fácil confundir uma pela
outra:

| Métrica | O que mede | Resultado | O que NÃO prova |
|---|---|---|---|
| `docs/respostas.md` (106 perguntas ✅/◐ de `docs/perguntas.md`) | Se o **dado** existe e junta corretamente, dado que quem escreveu a query já sabia o nome das tabelas (schema lido, não descoberto) | ~106/220 respondidas com query real no beelink | Nada sobre `search_tables` — a descoberta nunca passou pelas ferramentas do MCP |
| `scripts/avalia_douradas_perguntas.py` contra `tasks/douradas_perguntas.json` | Se `search_tables`, sozinho, numa única chamada, devolve TODOS os datasets exigidos por uma pergunta no mesmo `top_k` | ~51% dos datasets recuperados | Não testa o loop da seção 3 — é uma chamada isolada, sem describe_table/resolve_join/run_sql depois, sem reformular em caso de erro |

O espaço entre essas duas linhas — quanto da distância de 106→51% a
iteração completa (seção 3) recupera de volta — nunca foi medido até este
documento existir. É exatamente o teste em andamento nesta sessão: um agente
sem contexto do repositório, só com as ferramentas MCP e o texto da
pergunta, tentando as 99 perguntas verificadas de `docs/respostas.md` do
zero.

---

## 5 · Inventário de ferramentas

| Ferramenta | Fonte | Propósito |
|---|---|---|
| `list_datasets` | `_SCHEMA` (schema.json) | Catálogo completo, contagem de tabelas por dataset |
| `list_tables` | `_SCHEMA` | Tabelas de um dataset, com sugestão por proximidade em caso de erro de nome |
| `describe_table` | `_SCHEMA` + `_duplicated()` + `_DICIONARIO_COVERAGE` + `_CODED_DIFFERENTLY` | Colunas de uma tabela, mais três avisos que a lista nua esconderia (linha duplicada, coluna decodificável, código que diverge entre datasets) |
| `search_tables` | índice doc2query (seção 2) | Busca semântica: pergunta → tabelas candidatas |
| `get_join_keys` | `join_keys.md` (152 seções) | Índice de colunas de join documentadas, ou seção completa por coluna |
| `resolve_join` | `bridges.yaml` + `join_keys.md` | Cláusula `ON` pronta entre duas tabelas — bridges primeiro, depois match direto, com `rejected` explícito pra false friends |
| `explain_column` | `bridges.yaml` (`false_friends`/`coded_differently`/`concepts`) | Por que uma coluna comum (`valor`, `id`, `numero`) NÃO é chave de join; ou, pra `sexo`/`raca_cor`/etc., por que o CÓDIGO não atravessa datasets mesmo o conceito sendo o mesmo |
| `get_metric` | `metrics.yaml` (7 métricas) | Cálculo nomeado — SQL, grão, filtros obrigatórios — por nome ou sinônimo pt-BR |
| `list_metrics` | `metrics.yaml` | Todas as métricas nomeadas |
| `rollup` | `hierarchies.yaml` (3 hierarquias) | Expressão pra subir um código de classificação um nível (CNAE, CID-10) |
| `run_sql` | beelink via SSH | Execução real — só SELECT/WITH, fallback automático pra `read_parquet()` |
| `consultar_cnpj` | `br_me_cnpj/*` (parquet) | Empresa + estabelecimentos + sócios por CNPJ |
| `consultar_cep` | ViaCEP (live, via SSH) | Endereço por CEP — não há base bulk pra espelhar |
| `consultar_divida_ativa` | `br_pgfn_dividaativa/divida` | Dívida ativa federal por CPF/CNPJ |
| `consultar_precos_combustivel` | `br_anp_combustiveis/precos` | Preço de combustível por posto/produto/data |
| `consultar_jurisprudencia_stj` | `br_stj_dadosabertos/documentos` | Decisões do STJ por processo/ministro/assunto |
| `consultar_populacao_carceraria` | `br_mjsp_sisdepen/populacao_carceraria` | Censo prisional por UF/ciclo |
| `consultar_painelprecos` | ComprasGov (live, via SSH) | Preço de compra pública por código CATMAT/CATSER — API por item, sem "tabela completa" pra espelhar |

## 6 · Onde isso já quebrou, e o que foi corrigido

Achados confirmados em código (não por analogia) em `tasks/done/mcp_search_refino.md`,
todos fechados em 2026-08-24:

1. **Índice quebrado** (item 1) — trocado pelo doc2query da seção 2.
2. **`describe_table` mudo sobre tabela duplicada** (item 2) — hoje carrega
   `warning` mesmo fora de `resolve_join`.
3. **Colunas cruas do censo histórico** (item 3) — `dicionario_coverage`
   apontava só pras 10 tabelas do censo IBGE onde `v0502` etc. têm
   decodificação disponível.
4. **Código que diverge por dataset para o mesmo conceito** — achado ao vivo
   num teste cego do MCP em 2026-08-24: uma query reusou `sexo='2'`
   (feminino no RAIS) contra o CAGED, onde `'2'` não existe (feminino é
   `'3'`) — devolveu 0 linhas em silêncio, quase virando um "achado"
   fabricado. Investigação sistemática sobre os 44 datasets com tabela
   `dicionario` própria confirmou 7 conceitos com o mesmo problema (`sexo`,
   `raca_cor`, `estado_civil`, `faixa_etaria`, `nacionalidade`, `rede`,
   `tipo_estabelecimento`) — inclusive um caso pior: `br_inep_enem` usa DUAS
   convenções diferentes pra `sexo` em anos diferentes da MESMA tabela
   (`0`/`1` numérico invertido, depois `M`/`F` literal). Duas correções:
   `gera_dicionario_coverage.py` generalizado de 1 dataset (censo IBGE) pra
   45 (168 tabelas, 6.256 colunas decodificáveis — item 3 virou um caso
   particular deste); e `bridges.yaml` ganhou uma seção nova,
   `coded_differently`, servida por `explain_column` e por um bloco novo
   `coded_value_warning` em `describe_table` — para essas 7 colunas, avisa
   *antes* da query, não só quando perguntado.

O que ficou documentado como *não* mexer: `run_sql` devolve erro cru (seção
3), `get_metric` é lookup direto sem parser de frase, `resolve_join` rejeita
explicitamente em vez de silenciar false friends.
