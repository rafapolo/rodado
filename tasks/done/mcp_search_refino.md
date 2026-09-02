# mcp_search_refino.md — o que a investigação do ask-web (22-24/08) ensina pro MCP

**Status: fechado em 2026-08-24.** Os 3 achados abaixo foram corrigidos em
`mcp_server.py`: item 1 no commit `a64558a` (índice doc2query substituiu o índice
quebrado), itens 2 e 3 no commit `dcf0404` (`describe_table` agora carrega `warning`
para tabela duplicada e `dicionario_coverage` para coluna decodificável). Item 4 e 5
eram observações, não pendências — seguem válidas como registro.

**Item 6, adicionado 2026-08-24 (mesmo dia, achado num teste cego separado):**
rodando o MCP às cegas (sem contexto do repo, só as ferramentas) contra as 99
perguntas verificadas de `docs/perguntas.md`, um agente reusou `sexo='2'` (feminino
no RAIS) numa query contra o CAGED — onde `'2'` não existe, feminino é `'3'` — e
recebeu `0,0%` em silêncio em vez de erro, quase virando um "achado" fabricado
(mulheres nunca contratadas em cargos bem pagos). Investigação sistemática sobre os
44 datasets com tabela `dicionario` própria confirmou que isso não é caso isolado:
7 conceitos (`sexo`, `raca_cor`, `estado_civil`, `faixa_etaria`, `nacionalidade`,
`rede`, `tipo_estabelecimento`) têm código numérico que diverge por dataset — pior,
`br_inep_enem` usa DUAS convenções diferentes pra `sexo` em anos diferentes da MESMA
tabela. Corrigido: `gera_dicionario_coverage.py` generalizado de 1 dataset (censo
IBGE, item 3 acima) pra 45 (168 tabelas, 6.256 colunas); `bridges.yaml` ganhou a
seção `coded_differently`; `describe_table` ganhou o bloco `coded_value_warning` e
`explain_column` passou a reconhecer esses 7 conceitos. Detalhe completo em
`docs/MCP.md` seção 6, item 4.

**Item 7, mesmo dia:** rodando os lotes seguintes do mesmo teste cego, um agente
travou >1h esperando uma query que nunca voltava — `_run_sql_ssh` abria a conexão
DuckDB sem `-readonly`, então mesmo um `SELECT` puro tomava lock exclusivo no
arquivo `.duckdb` e bloqueava qualquer outra sessão (este repo tem várias sessões
concorrentes na prática). Corrigido: `-readonly` adicionado à conexão em
`mcp_server.py` — não perde nada, já que `_check_read_only` garante no nível SQL
que nada escreve. Registrado também como `feedback_duckdb_readonly_no_kill` na
memória: o processo que segura o lock quase sempre é trabalho real de outra
sessão, nunca `kill`. Detalhe em `docs/MCP.md` seção 1.

Arquivo mantido em `done/` como histórico da investigação.

Não é retrospectiva — é tarefa pendente. Nasceu de testar `mcp_server.py` ao vivo em
2026-08-24 contra perguntas complexas (`tasks/done/ask_web.md` tem o contexto de por que
o ask-web foi retirado). Cada achado abaixo foi **confirmado no código-fonte de
`mcp_server.py`**, não suposto por analogia com o ask-web.

## 1. `search_tables` usa o índice quebrado — maior alavanca única

`mcp_server.py:_load_embeddings()` carrega `docs/context/table_embeddings.json`
diretamente. É o MESMO índice que a investigação de 2026-08-23 mediu quebrado: texto
indexado é sopa de nome de coluna com tipo (`"br_ms_sim.microdados: ano (INTEGER), sigla_uf
(STRING)…"`), cosseno 0,0755 contra 0,3905 de uma prosa curta equivalente — recall@5 de
1/15 nas perguntas douradas de uma tabela só.

**Confirmado ao vivo, 2026-08-24, três misses reproduzíveis com perguntas reais** (não
hipotéticas — vêm de `tasks/douradas_multi.json`, que sobrevive em `origin/ask-web`):

| busca | tabela certa | apareceu? |
|---|---|---|
| "IDEB indicadores de qualidade educacional por município" | `br_inep_ideb.municipio` | não, nem no top-5 — nem o acrônimo "IDEB" bate |
| "remuneração de professores, despesas municipais com educação" | `br_me_siconfi.municipio_despesas_funcao` | zero resultados a 0,35; a 0,1 o melhor é uma tabela do TCE-PI errada |
| "taxa de fecundidade adolescente por raça, nascidos vivos" | `br_ms_sinasc.microdados` | não — SINASC = Sistema de Informações sobre **Nascidos Vivos**, o termo está literal na pergunta |

O fix já existe e já foi medido: o índice doc2query construído pro ask-web (824/824
tabelas, 6.562 perguntas sintéticas geradas por LLM, um vetor por pergunta, score por
tabela = MÁXIMO entre as perguntas dela) subiu o recall de 1/15 pra 11/15 (73%) no mesmo
conjunto de teste. **Nunca foi portado pro MCP.**

**Nuance de formato, pra quem for portar**: `table_embeddings.json` guarda embedding
INLINE por tabela (`{"tables":[{"id","text","embedding":[...]}]}`). O índice doc2query é
armazenado diferente — `web/static/index/perguntas.json` (metadados: `{"entradas":
[{"id","q"}, ...]}`) **separado** de `perguntas_vetores.bin` (os vetores em float32 cru,
na mesma ordem de `entradas`). Portar exige reconstruir o par id→vetor em Python lendo os
dois arquivos juntos, não é troca de caminho de arquivo. Se preferir, regenerar direto em
formato Python-friendly com `scripts/doc2query_*.ts` do `origin/ask-web` como referência do
pipeline (já roda: 33 lotes via LLM, valida cada saída, é retomável).

Score por MÁXIMO é o detalhe que importa mais que o resto: uma tabela responde muitas
perguntas sintéticas diferentes, e é a que casa com a pergunta REAL que importa — média
dilui e foi o que derrubou uma tentativa anterior (prosa+colunas juntas, só 2/15).

## 2. `describe_table` não avisa sobre tabela duplicada — só `resolve_join` avisa, e só reativamente

Confirmado lendo o código: o aviso "retorna cada linha duas vezes" (mcp_server.py:660-661)
só dispara **dentro de `resolve_join`**, quando a tabela duplicada é um dos dois
argumentos. Chamar `describe_table("br_bd_diretorios_brasil.municipio")` direto — o
caminho mais natural pra uma tabela de 1 tabela só, sem join — não avisa nada. É
exatamente a mesma lacuna que o ask-web teve que resolver escrevendo o aviso na própria
DDL (`montarDDL`: `if (t.duplicada) l += "-- ATENÇÃO: retorna toda linha DUAS VEZES"`).

**Fix**: `describe_table` checar a mesma lista de tabelas duplicadas que `resolve_join`
já usa (`gera_join_keys.py` já sonda beelink por `tmp*.parquet` leftover) e incluir o
aviso na resposta, não só quando outra tabela é citada ao lado.

## 3. Colunas opacas do censo histórico — nem `explain_column` nem `describe_table` cobrem

`explain_column` cobre exatamente um tipo de opacidade: nome de coluna que SIGNIFICA
coisas diferentes em tabelas diferentes (`valor`, `id`, `numero` — 91 tabelas, 56
datasets). Não cobre o outro tipo, que é diferente: coluna cujo NOME em si não diz nada,
mesmo dentro de uma tabela só.

Confirmado por amostragem real em 2026-08-24: a maior parte do mirror do IBGE já vem
com nome de coluna E valor normalizados em português pelo próprio Base dos Dados
(`tipo_destino_lixo` → `"Coletado"`, não código). Mas `br_ibge_censo_demografico.
microdados_pessoa_{1970,1980,1991,2000,2010}` e os `microdados_domicilio_*` equivalentes
(10 tabelas, ~244 colunas cada) usam código cru do IBGE (`v0502`, `v6033`...). O dado pra
resolver EXISTE — `br_ibge_censo_demografico.dicionario` tem `chave→valor` de verdade
(306 linhas só pra `pessoa_2010`, 1.360 pra `pessoa_1991`) — mas nada aponta pra ele:
`describe_table` devolve os nomes crus sem aviso, e não existe rótulo de COLUNA (o que
`v0502` representa como conceito — "condição no domicílio") derivável do dicionário atual,
só rótulo de VALOR (o que `v0502=1` significa).

**Fix, escopo pequeno de propósito** (não é "comentar as 824 tabelas" — é ~10):
1. `describe_table` checar se `{dataset}.dicionario` existe E tem linhas para aquela
   tabela; se sim, listar quais colunas têm decodificação disponível.
2. Opcional, mais trabalho: gerar rótulo de coluna a partir do PADRÃO de valores no
   dicionário (ex.: se os `valor` de `v0502` são todos papéis familiares, o rótulo é
   "condição no domicílio") — precisa de uma passada offline, não é runtime barato.

## 4. O que já está bem desenhado — não mexer

Vale registrar o que a comparação NÃO encontrou problema, porque evita reinventar:

- **`get_metric(name)`** é lookup direto por nome/sinônimo já normalizado, chamado pelo
  agente com o CONCEITO já extraído — não é um parser de frase inteira. A classe de bug
  que o ask-web teve (`resolverMetrica` tratando "brasil" e "?" como "termo não
  explicado", corrigido em 2026-08-23) não existe aqui por desenho: não há pipeline
  automático de frase→filtro pra confundir. Deixar como está.
- **`run_sql` devolve o erro cru do DuckDB**, não uma versão resumida. Foi exatamente
  esse texto (`"Binder Error: ... Candidate bindings: ..."`) que permitiu resolver ao
  vivo, em 2026-08-24, os dois casos que o ask-web não conseguiu resolver nem com 2
  tentativas de reparo. Simplificar essa mensagem pra "ficar mais amigável" removeria a
  informação que faz o laço de correção funcionar de verdade. Não simplificar.
- **`resolve_join` com `rejected` explícito** (não silencioso) é o desenho certo pro
  problema de false friends — o ask-web replicou a mesma ideia (`montarFalseFriends`)
  porque funciona.

## 5. Por que "MCP + agente" ganhou do ask-web sem precisar de índice melhor

Duas perguntas que travaram a noite inteira no ask-web (3B e 7B) foram resolvidas ao vivo
via MCP em minutos — **mesmo com o `search_tables` quebrado descrito no item 1**, porque
um agente pode iterar (buscar, olhar, perceber que a fonte não serve, buscar de novo,
verificar com SQL) enquanto o ask-web fazia uma busca e no máximo 2 reparos cegos. Isso
não invalida o item 1 — turbina ele: se a recuperação já funciona mal e AINDA ASSIM o
MCP ganha por causa da iteração, consertar a recuperação (item 1) só aumenta a vantagem,
não é a única coisa que sustenta o MCP hoje.

Contexto completo, incluindo as duas perguntas resolvidas e as causas raiz encontradas
(regra de maiúsculas errada no ANP, fonte sem granularidade estadual no Atlas da
Violência), está em `tasks/done/ask_web.md`.
