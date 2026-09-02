# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**baseldosdados** mirrors public Brazilian government tables from [Base dos Dados](https://basedosdados.org) — stored as Parquet+zstd in `~/rodado` on beelink — and extends that mirror with independently-scraped sources that fill the remaining gaps (sanctions lists, SICAF, SINAN microdata, consumer complaints and more — see `tasks/datasets_to_scrap.md` for the full catalog and provenance of every source). 1.024 tables (230 datasets, 39,2 bilhões de linhas) as of 2026-09-02 — 741 espelhadas do Base dos Dados, 283 raspadas pelo projeto. A DuckDB view `_rodado_metadata` on beelink tracks each table's rows, source, status, and provenance; `_rodado_datasets` aggregates by dataset. DuckDB queries the data on-demand without local imports.

## Commands

### Python services
```bash
python scripts/gera_schemas.py        # extract table schemas → JSON/text
python scripts/gera_join_keys.py      # schemas.json → docs/context/join_keys.md
python scripts/gera_erd.py            # schemas.json → ERD.md (pt-BR) + ERD_EN.md
```

### Querying data
```bash
ssh beelink '~/bin/duckdb -readonly -json ~/rodado/basedosdados.duckdb' <<'SQL'
SET enable_progress_bar=false;
SELECT ...;
SQL
```

## Architecture

Everything is local: parquet on beelink (`~/rodado/<dataset>/<tabela>/*.parquet`), queried through
DuckDB over SSH — no live web service, no cloud object storage. The former
`db.xn--2dk.xyz` HTTP endpoint (`auth.py`, a BigQuery → GCS → Hetzner Object
Storage pipeline via `scripts/roda.sh`, DuckDB httpfs reads on query) is
retired; the deployment files it left behind (`auth.py`, `start.sh`,
`Caddyfile`, `haloy.yml`, `Dockerfile`) are not part of the current
architecture and describe infrastructure that no longer runs.

`mcp_server.py` is the current interface — see `docs/MCP.md`.

### `docs/ERD.md` — the map
One mermaid `erDiagram` per domain covering all 893 tables: entity = dataset, attribute = table, edge = join key to a reference hub (solid = direct, dashed = needs normalization). Lists what connects to nothing. `ERD.md` is pt-BR (default), `ERD_EN.md` is the English twin — both generated from the same data by `scripts/gera_erd.py`.

### `docs/context/` — Schema metadata
Um `README.md` na própria pasta descreve arquivo por arquivo, quem gera cada um e a ordem do regen.
- `all_tables.txt` — as 900 `dataset.tabela`, uma por linha, incluindo as 8 nativas do `.duckdb` que não têm parquet. Gerado por `scripts/build_metadata_catalog.py` — era um despejo do `bq ls` da era BigQuery que ninguém regenerava
- `basedosdados-schema.json` — full schema (2.0 MB, 226 datasets / 1017 tabelas)
- `doc2query_index.json` / `doc2query_vectors.npy` — the `search_tables` index: one embedding per synthetic question a table answers (~8/table, 832 tables, `paraphrase-multilingual-MiniLM-L12-v2`), not one per table (replaces a deleted `table_embeddings.json`, which held one vector per table over column-name text — measured nearly orthogonal to a real question, recall@5 1/15 on a single-table golden set; see `tasks/done/mcp_search_refino.md` item 1. `scripts/update_embeddings.py`, its generator, was deleted with it). `search_tables` scores a table by the MAX cosine similarity across its own questions. `.json` holds `id`/`table`/`text` per row in the `.npy`'s row order; `.npy` is a float32 `(n_questions, dim)` array. Generation is two separable steps: the LLM pass (`scripts/doc2query_lotes.py` → `scripts/doc2query_roda.py` against `scripts/prompts/doc2query.md`, ~34 `opencode run` batches — expensive, one-time, resumable) produces `docs/context/doc2query_corpus.jsonl` (via `scripts/gera_doc2query_corpus.py`, not gitignored — the raw batches under `tasks/` are); `scripts/gera_doc2query_index.py` embeds it — cheap, rerun freely after editing the corpus or changing the embedding model
- `bridges.yaml` — **a fonte única do conhecimento de join**. Conceitos-hub, as 81 pontes (coluna que significa a mesma coisa sob outro nome), os `false_friends`, os `coded_differently` (mesmo conceito, código numérico diverge por dataset/ano — `sexo`, `raca_cor`, `estado_civil`... achado ao vivo num teste cego do MCP, ver `tasks/done/mcp_search_refino.md`) e os `concept_aliases`. Editar aqui; `join_keys.md` é gerado
- `join_keys.md` — o render de `bridges.yaml` + as chaves auto-detectadas do `schemas.json`: 430 colunas de join ao todo. Gerado por `scripts/gera_join_keys.py` — regenerar, nunca editar à mão
- `metrics.yaml` / `metrics.json` — 13 cálculos nomeados (expressão DuckDB, grain, unidade, sinônimos pt-BR, `required_filters`, `verified`). O `.json` é gerado do `.yaml` por `scripts/gera_metrics_json.py`; `mcp_server.py` lê o `.yaml` diretamente. A TUI Rust que lia o `.json` foi removida (`ask/` apagado em `58ab7c7`, 2026-08-23); hoje quem consome o `.json` é `scripts/build_ask_web_assets.ts`, que empacota `metrics.json` + `bridges.yaml` em `web/static/index/semantica.json` — vive só no branch `ask-web` (remoto, não mesclado), não neste checkout em `main`
- `hierarchies.yaml` — rollup de município→UF→região, CNAE e CID-10. CNAE e CID são prefixais: o pai sai de `substr()`, sem join
- `schema_ddl.sql` — snapshot DDL parcial (527 tabelas, 109 datasets) da porção espelhada do **Base dos Dados**; serve de referência de procedência para `scripts/build_metadata_catalog.py`. Cobre parte do mirror, não todo ele
- `dicionario_coverage.json` — quais colunas de quais tabelas têm decode chave→valor disponível em `{dataset}.dicionario`, escaneado em **45 datasets** (168 tabelas, 6.256 colunas) — não só o censo IBGE histórico (`v0502` etc.) que motivou o mecanismo, generalizado 2026-08-24 depois que um teste cego do MCP achou o mesmo padrão em RAIS/CAGED/ENEM/SIM e outros 40. Gerado por `scripts/gera_dicionario_coverage.py`; `describe_table` lê pra avisar quais colunas de uma tabela são decodificáveis (`dicionario_coverage`) e quais têm código que **diverge entre datasets** pro mesmo conceito (`coded_value_warning`, cruzado com `bridges.yaml`'s `coded_differently`)

### Camada semântica — `bridges.yaml`, `metrics.yaml`, `hierarchies.yaml`

O espelho não tem foreign key, não tem métrica nomeada e não tem hierarquia declarada. Os três YAML em `docs/context/` são onde isso passa a existir como **dado**, não como prosa que o modelo tem que interpretar.

| Arquivo | Responde | Ferramenta MCP |
|---|---|---|
| `bridges.yaml` | como duas tabelas se ligam, e qual expressão converte uma ponta na outra | `resolve_join(a, b)`, `explain_column(col)`, `get_join_keys(col)` |
| `metrics.yaml` | qual é *a* definição de "população", "saldo do CAGED" | `get_metric(nome)`, `list_metrics()` |
| `hierarchies.yaml` | como subir de subclasse CNAE para divisão, de subcategoria CID para categoria | `rollup(coluna, nivel)` |

Três regras que valem mais que o resto:

1. **`resolve_join` antes de escrever join à mão.** Ele devolve a cláusula `ON` pronta e, quando existe ponte, ela **substitui** a igualdade ingênua em vez de concorrer com ela — `br_anp_combustiveis.precos` guarda `cnpj` sem padding, então `a.cnpj = b.cnpj` está errado e é exatamente o que um match por nome devolveria. Ele também avisa quando uma das pontas está duplicada por sobra de sync — hoje nenhuma está: as 80 sobras de `tmp*.parquet` do sync abortado de 2026-07-05 foram triadas e removidas em 2026-08-23.
2. **`false_friends` são silenciosos e caros.** `valor` aparece em 91 tabelas de 56 datasets significando coisas diferentes; juntar por ele dá resultado grande, plausível e errado. `explain_column` diz o porquê.
3. **`verified` não é enfeite.** Toda ponte, métrica e `parent_expr` carrega o que casou quando foi rodado no beelink, com data. Sem isso a linha é aspiracional — trate como não conferida.

Regenerar, na ordem, depois de qualquer sync que mude tabelas:

```bash
python3 scripts/gera_schemas.py            # beelink        -> schemas.json
python3 scripts/sync_mcp_schema.py         # schemas.json   -> docs/context/basedosdados-schema.json
python3 scripts/build_metadata_catalog.py  # beelink        -> catalog.parquet + views + all_tables.txt
python3 scripts/gera_join_keys.py          # bridges.yaml   -> docs/context/join_keys.md
python3 scripts/gera_metrics_json.py       # metrics.yaml   -> docs/context/metrics.json
python3 scripts/valida_metrics.py          # confere metrics.yaml + hierarchies.yaml
python3 scripts/gera_schema_graph.py       # -> pages/atlas/schema_graph.json
python3 scripts/build_atlas.py             # -> pages/atlas/index.html
python3 scripts/gera_dicionario_coverage.py  # beelink -> docs/context/dicionario_coverage.json (rerodar quando um dicionario mudar)
```

`sync_mcp_schema.py` é o passo que se esquece: sem ele `mcp_server.py` continua lendo o
schema antigo em `docs/context/basedosdados-schema.json` e não enxerga nenhuma coluna
nova — `describe_table` mente calado.

Antes desse regen, depois de qualquer scraper novo ou job resumido sem supervisão,
ver [`docs/housekeeping.md`](docs/housekeeping.md) — checklist do que não acontece
sozinho (view faltando no `.duckdb` com parquet já completo no disco, job que parou
por rate limit sem erro fatal, contagem duplicada entre sessões concorrentes, zip com
mais de um CSV membro), com os comandos exatos e os casos reais que motivaram cada item.

`join_keys.md` e `metrics.json` são **gerados** — editar o YAML, nunca a saída. `valida_metrics.py` separa hard de soft como o firewall de `run_sql`: DML na expressão rejeita, coluna ausente só avisa, porque `_check_read_only` revalida antes de executar.

`doc2query_index.json`/`doc2query_vectors.npy` **não** entram nesse regen automático — a geração via LLM (`scripts/doc2query_lotes.py` + `scripts/doc2query_roda.py`) é cara e não deve rodar a cada sync; só o passo de embedding (`scripts/gera_doc2query_index.py`, a partir de `docs/context/doc2query_corpus.jsonl` já gerado) é barato o bastante pra rerodar sem pensar. Regenerar tudo só quando o schema mudar o bastante pra `search_tables` começar a perder tabela nova.

### Conjuntos-dourados — medir a qualidade do `search_tables`

Duas fontes independentes, mesma limitação conhecida: perguntas que cruzam 2+
tabelas/datasets, contra as quais `search_tables` (uma tabela por chamada) nunca
vai ter recall alto — não é bug, está documentado no docstring de cada `avalia_*.py`.

| Conjunto | Fonte | Constrói | Mede |
|---|---|---|---|
| `tasks/douradas_multi.json` | `docs/relatorio-social/perguntas.md` (tabelas citadas em backtick, `**Fontes:**`) | `scripts/build_douradas_multi.py` | `scripts/avalia_douradas_multi.py` — recall@K por TABELA exata |
| `tasks/douradas_perguntas.json` | `docs/perguntas.md` (43 temas × 5 perguntas, `n=X: dataset_a, dataset_b*`) cruzado com `docs/respostas.md` (status `✅`/`◐`/`⏳` por `T<tema>-<item>`) | `scripts/build_douradas_perguntas.py` | `scripts/avalia_douradas_perguntas.py` — recall@K por DATASET (qualquer tabela do dataset conta como acerto) |

`docs/perguntas.md` é a fonte fixa (43 temas, nunca editado pelos scripts);
`docs/respostas.md` é o log de trabalho vivo — cada pergunta respondida no
beelink muda o status ali e alimenta o próximo `build_douradas_perguntas.py`
automaticamente, sem editar código. Só `✅`/`◐` entram no conjunto: um item
`⏳` costuma vir com o motivo exato no próprio texto (dado corrompido, tabela
ausente, sem chave compartilhada), e incluir "pendente" envenenaria o teste
com uma expectativa nunca verificada — a seção "Bloqueios mapeados" ao fim de
`respostas.md` cataloga o que está estruturalmente bloqueado (precisa de
re-scraping ou campo novo), separado do que só ainda não foi tentado.

Regenerar depois de qualquer resposta nova em `respostas.md`:

```bash
python3 scripts/build_douradas_perguntas.py    # respostas.md -> tasks/douradas_perguntas.json
python3 scripts/avalia_douradas_perguntas.py   # mede search_tables contra ele
```

A TUI Rust `ask` que fazia isto foi removida (`ask/` apagado em `58ab7c7`, 2026-08-23). A mesma lógica de Tier 1 sobrevive reimplementada em JS — `resolverMetrica()` em `web/static/prompt.js` —, parte do app web `ask-web` que vive só no branch `ask-web` (remoto, não mesclado em `main`, sem worktree local no momento). Ela resolve métrica **antes** da seleção por embedding, por match exato de nome ou sinônimo — nunca por similaridade, porque "população de SP" e "população carcerária" ficam perto no espaço vetorial e querem tabelas diferentes. **Isto não é `mcp_server.py`**: o `get_metric()` do MCP é um lookup direto sem parser de frase (confirmado em `docs/MCP.md`) — não faz longest-match sobre uma pergunta em texto livre, não tem Tier 2/3. Três detalhes do Tier 1 que custaram trabalho na versão Rust e não devem ser redescobertos:

1. O match é por nome **ou sinônimo**, exato, depois de normalizar acento e caixa, e **o mais longo vence** — sem isso "pib per capita" resolve como "pib".
2. O Tier 1 roda **antes** do embedding. Depois dele economiza a chamada ao modelo mas ainda paga o embedding inteiro (~18s → 0,00s).
3. Cai para o modelo quando sobra **qualquer** termo não explicado na pergunta. "população por município em 2022" tem que cair: responder o agregado nacional a uma pergunta sobre municípios é errado e silencioso.

### `_rodado_metadata/catalog.parquet` — o catálogo
Gerado por `scripts/build_metadata_catalog.py`, que também recria as views `_rodado_metadata` (1 linha por tabela) e `_rodado_datasets` (1 linha por dataset) no beelink. Rode-o depois de qualquer sync que mude tabelas — nunca edite o parquet à mão.

| Coluna | O que é |
|---|---|
| `dataset`, `table` | identificação; `dataset.table` é o caminho DuckDB |
| `source_name` / `source_url` / `source_type` | procedência. `Base dos Dados` + `mirror` para o espelho; nome do órgão + formato para o que o projeto raspa |
| `rows`, `num_files`, `size_bytes` | medidos via `parquet_metadata`, incluindo tabelas particionadas; para `duckdb_native` o `rows` vem de um `count(*)` no DuckDB |
| `scrape_date` | data do `datasets_to_scrap.md`, ou o mtime do parquet mais recente |
| `status` | `mirrored`, `done`, `blocked → mcp-todo`, `view_orfa`… |
| `source` | `disk` (parquet local, contado por `parquet_metadata`), `duckdb_native` (sem parquet, mas a view lê tabela nativa dentro do `.duckdb` — contado pelo próprio DuckDB) ou `view_only` (sem parquet **e** sem linhas) |
| `provenance_notes` | notas do `datasets_to_scrap.md`, truncadas em 500 chars |

Ao contar tabelas ou linhas, filtre **`source <> 'view_only'`** — nunca `source = 'disk'`.

As 8 tabelas que eram registradas como `view_orfa` com `rows=0` não estavam quebradas: leem tabelas nativas dentro do próprio `basedosdados.duckdb`, e `parquet_metadata` devolvia 0 porque não existe parquet, não porque não existe dado. São 250.126.810 linhas reais (`br_ms_sipni_microdados.vacinacao_2020` sozinha tem 115,7M). Hoje elas são `duckdb_native` e **nenhuma** linha é `view_only`. Consulte-as pela view, não por `read_parquet`.

### `pages/atlas/` — Rodado Atlas (rodado.xyz/atlas)
Mapa navegável das tabelas e das colunas de join que as conectam. O espelho não tem foreign key — o que o liga são colunas que significam a mesma coisa em mais de uma tabela, a mesma seleção que `gera_join_keys.py` faz.

```bash
python3 scripts/gera_schema_graph.py   # schemas.json + catalog.parquet -> pages/atlas/schema_graph.json
python3 scripts/build_atlas.py         # + pages/atlas/_page.html       -> pages/atlas/index.html
python3 scripts/build_atlas.py /tmp/atlas.html   # também emite a cópia autocontida pra Artifact
```

- `_page.html` é a **única fonte**; `index.html` é gerado — não edite o gerado.
- O grafo é **bipartido**: tabela→chave, nunca tabela→tabela. Par a par seriam 89.598 arestas (novelo); pela chave são 2.151.
- Duas distribuições, ambas pré-calculadas em Python e embarcadas no JSON: `grade` (cartões de dataset empacotados) e `temas` (um território por tema, chaves flutuando entre os que ligam).
- `?db=<dataset>` abre o atlas já centrado naquele dataset com o painel aberto (`rodado.xyz/atlas?db=br_me_rais`); o parâmetro acompanha a seleção via `replaceState`, então a barra de endereço é sempre um link pro que está na tela.
- **Cor = tema**, nunca chave. Só 4 matizes passam o gate all-pairs de CVD, então os 10 temas dependem de território rotulado + isolamento por clique; a cor reforça, não carrega sozinha.
- Depois de qualquer sync que mude tabelas: `gera_schemas.py` → `build_metadata_catalog.py` → `gera_schema_graph.py` → `build_atlas.py`.

## Environment Variables

| Variable | Used by | Purpose |
|----------|---------|---------|
| `BEELINK_HOST` | scripts, mcp_server | SSH hostname for beelink (default: `beelink`) |

## Data Querying (DuckDB/CNPJ datasets)

- Always include partition filters on large tables to avoid timeouts.
- **Check `list_metrics()`/`get_metric()` before hand-writing a per-capita/rate/ratio.** `metrics.yaml` exists specifically because unit assumptions are easy to get wrong and the wrong number still looks plausible — `pib_per_capita` is pre-verified (`SUM(pib)/NULLIF(SUM(populacao),0)`, no scaling factor) precisely because `pib` is stored in whole BRL, not thousands, and assuming otherwise silently inflates results 1,000x.
- **Classifying `br_me_cnpj.estabelecimentos` by name never needs a join to `.empresas`** — `nome_fantasia` already lives on `estabelecimentos`. An unbounded multi-`ILIKE` join against the full `.empresas` table (tens of millions of rows) is both unnecessary and the most expensive mistake available in this mirror — a hung one held an exclusive DuckDB lock on beelink for 2+ hours on 2026-08-24 (see `tasks/done/mcp_search_refino.md` item 7).
- Validate query results against sanity bounds (e.g., contract values, row counts) before reporting; flag anomalies like trillion-real totals.
- Prefer name-based filtering combined with CPF when CPF joins alone produce implausible cardinality.
- Before presenting query results: (1) state the expected order of magnitude, (2) flag any row that exceeds it, (3) verify the count two independent ways. Only report numbers that pass all three checks.

## ⚠️ REGRA CRÍTICA — SEM EXCEÇÕES

**NUNCA usar BigQuery, GCP ou `bq` CLI. JAMAIS. Toda consulta de dados vai pelo DuckDB no beelink via SSH (`ssh beelink`). Não importa o tamanho da tabela, a complexidade do join ou se "é mais fácil" no BigQuery — DuckDB único.**

**NUNCA usar S3/Hetzner diretamente.** O bucket `s3://baseldosdados` não existe mais — todas as views no DuckDB que referenciam `s3://` estão obsoletas. Para queries em tabelas cujas views apontam para S3, use `read_parquet('~/rodado/<dataset>/<table>/*.parquet')` diretamente com o caminho local do beelink.

Essa regra é sobre **servir consultas de dado** — nunca usar BigQuery pra isso, sem exceção.

Existe uma **única exceção, estritamente escopada**: manutenção do mirror do beelink (`scripts/sync-with-source.md`), usando **somente `bq query` em modo Sandbox gratuito** (sem conta de billing, cota mensal ~900GB/1TB), nunca `bq extract` nem qualquer operação que dependa de billing ativo. Essa exceção existe só porque o Sandbox sem billing tem custo zero garantido.

**Se billing for ativado em qualquer projeto GCP usado aqui, essa exceção acaba imediatamente — volta a ser JAMAIS, sem exceção nenhuma**, já que o que torna o uso pontual de BigQuery seguro hoje é justamente a impossibilidade de gerar custo.

---

## Key Conventions

- **Never use GCP, BigQuery, or `bq` CLI for queries** — all data access goes through DuckDB only.
- **SSH to beelink** for all SQL queries — `ssh beelink '~/bin/duckdb -readonly -json ~/rodado/basedosdados.duckdb'` (SQL piped over stdin, SET enable_progress_bar=false first). Always pass `-readonly`: DuckDB takes an exclusive file lock even for a bare SELECT unless told otherwise, and multiple sessions query this same file concurrently — a non-readonly connection blocks every other one, including read-only attempts, until it disconnects. See `feedback_duckdb_readonly_no_kill` — never kill the process holding the lock, it's very likely another session's real work, not a stuck query. beelink is the project's only data source — everything is local parquet + DuckDB, no live web service. Set BEELINK_HOST env var if the hostname differs.
- DuckDB always runs read-only; no writes to the database from queries.
- Queries on large tables must filter on partition columns (`ano`, `mes`, `sigla_uf`) — this is enforced in prompts.
- SQL dialect is DuckDB; BigQuery syntax does not apply.
- `docs/overview/` contains per-dataset markdown summaries used as LLM context.
- `docs/queries/` contains example SQL and CNAE audit analysis files.
