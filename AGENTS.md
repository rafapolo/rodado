# AGENTS.md

This file provides guidance to coding agents (Claude Code, Pi, and others) when working with code in this repository.

## Project Overview

**baseldosdados** mirrors public Brazilian government tables from [Base dos Dados](https://basedosdados.org) — stored as Parquet+zstd in `~/rodado` on beelink — and extends that mirror with independently-scraped sources that fill the remaining gaps (sanctions lists, SICAF, SINAN microdata, consumer complaints and more — see `tasks/done/datasets_to_scrap_done.md` for the provenance of every scraped source and `tasks/plans/datasets_to_scrap.md` for the queue). 1.612 tabelas · 276 datasets · 116 fontes · 571 GB (34,67 bilhões de linhas) as of 2026-10-28. DuckDB queries the data on-demand without local imports.

## Commands

### Querying data
```bash
ssh beelink '~/bin/duckdb -readonly -json ~/rodado/basedosdados.duckdb' <<'SQL'
SET enable_progress_bar=false;
SELECT ...;
SQL
```

### Scripts that regenerate derived files
```bash
python scripts/gera_schemas.py        # extract table schemas → JSON/text
python scripts/gera_join_keys.py      # schemas.json → docs/context/join_keys.md
python scripts/gera_erd.py            # schemas.json → docs/mapa/ERD.md (pt-BR) + ERD_EN.md
```
Ordem completa de regen (rodar depois de qualquer sync que mude tabelas): `docs/context/README.md`.

## Architecture

Everything is local: parquet on beelink (`~/rodado/<dataset>/<tabela>/*.parquet`), queried through DuckDB over SSH — no live web service, no cloud object storage by default. `mcp/mcp_server.py` is the agent interface — see `mcp/MCP.md`.

Since 2026-10-09 the same data is also reachable at `https://db.rodado.xyz`
(password, read-only): a browser SQL terminal and `POST /query` for curl. Since
2026-10-11 it runs entirely in a haloy container on finland reading the
`s3://baseldosdados` copy (no SSH tunnel to beelink anymore) — see
`db/README.md`. It is a locked-down Python front end, not the DuckDB CLI.

O harness TS de apuração (pi + Gemma 4 local) vive no branch `harness-gemma`, fora de `main`.

## Onde fica cada coisa

- `docs/mapa/ERD.md` / `ERD_EN.md` — diagrama mermaid de join por domínio, as 1.612 tabelas (pt-BR / inglês, mesma fonte).
- `docs/context/` — a camada semântica do espelho: joins (`bridges.yaml`), métricas nomeadas (`metrics.yaml`), hierarquias (`hierarchies.yaml`), armadilhas por dataset (`gotchas/<dataset>.yml`), decode de código (`column_codes.yaml`, `dicionario_coverage.json`). **Leia `docs/context/README.md` antes de escrever join ou métrica à mão** — `resolve_join()`/`get_metric()`/`explain_column()` existem porque isso já saiu errado em produção (ver as 3 regras lá).
- `docs/pesquisa/hipoteses/` — perguntas e respostas de pesquisa sobre o espelho, incluindo o espaço de trincas de família e o grafo de identificadores CNPJ/CPF. Ver `docs/pesquisa/hipoteses/README.md`.
- `_rodado_metadata/catalog.parquet` — o catálogo de tabelas (linhas, status, procedência). Colunas e armadilhas conhecidas: `docs/mapa/metadata_catalog.md`.
- `pages/atlas/` (rodado.xyz/atlas) — mapa navegável de tabelas e join keys. Como é construído: `docs/mapa/atlas.md`. Como ligar um dataset novo nele: `docs/tecnico/housekeeping.md`, item 9.
- `docs/tecnico/housekeeping.md` — checklist a rodar depois de qualquer scrape novo (view existe? regen de metadados? atlas ligado? contagens no texto atualizadas?).
- `docs/tecnico/beelink_duckdbrc.md` — tuning do `~/.duckdbrc` no beelink, toggle do llama-server, o que nunca fazer com `temp_directory`.

## O que é só local — fora do git

- `scripts/scrap/` e `docs/context/privado/` (endpoints não documentados, contornos de WAF, proxy BR): fora do git desde 2026-10-07, a pedido — meses de trabalho para chegar a cada fonte, repositório é público. Histórico reescrito para tirá-los dos commits antigos também. Nada que dependa deles pode ser obrigatório no caminho de quem só consulta o espelho.
- `tasks/`: gitignored desde 2026-09-24, sem histórico no git — **apagar um arquivo de lá é definitivo**. `tasks/README.md` é o índice único do que está em andamento. O que um arquivo ensinou vai para um lugar versionado (`docs/`) antes de ser removido.
- `schemas.json` e `docs/context/rodado-schema.json`: fora do git (purgados do histórico em 2026-09-24) — um clone novo não os tem, e `mcp_server.py` só funciona depois de `gera_schemas.py` + `sync_mcp_schema.py`.
- `join_keys.md` e `metrics.json` são **gerados** — editar o YAML de origem, nunca a saída.

## Environment Variables

| Variable | Used by | Purpose |
|----------|---------|---------|
| `BEELINK_HOST` | scripts, mcp_server | SSH hostname for beelink (default: `beelink`) |

## Data Querying (DuckDB)

- Always include partition filters on large tables to avoid timeouts.
- **Check `list_metrics()`/`get_metric()` before hand-writing a per-capita/rate/ratio.** `metrics.yaml` exists specifically because unit assumptions are easy to get wrong and the wrong number still looks plausible — `pib_per_capita` is pre-verified (`SUM(pib)/NULLIF(SUM(populacao),0)`, no scaling factor) precisely because `pib` is stored in whole BRL, not thousands, and assuming otherwise silently inflates results 1.000x.
- **Check `docs/context/gotchas/<dataset>.yml` before querying a dataset.** E.g. `br_me_cnpj`: `empresas`/`estabelecimentos`/`socios` hold only the latest snapshot — history lives in `*_historico`, and filtering an old `ano`/`mes` on the current tables silently returns zero rows. Monthly-refresh procedure: `docs/tecnico/mes_novo_cnpj.md`.
- **Classifying `br_me_cnpj.estabelecimentos` by name never needs a join to `.empresas`** — `nome_fantasia` already lives on `estabelecimentos`. An unbounded multi-`ILIKE` join against the full `.empresas` table is both unnecessary and the most expensive mistake available in this mirror — a hung one held an exclusive DuckDB lock on beelink for 2+ hours on 2026-08-24.
- Validate query results against sanity bounds (e.g., contract values, row counts) before reporting; flag anomalies like trillion-real totals.
- Prefer name-based filtering combined with CPF when CPF joins alone produce implausible cardinality.
- Before presenting query results: (1) state the expected order of magnitude, (2) flag any row that exceeds it, (3) verify the count two independent ways. Only report numbers that pass all three checks.

## ⚠️ BigQuery, GCP e S3: fora do caminho das consultas — SEM EXCEÇÕES

**NUNCA usar BigQuery, GCP ou a CLI `bq` para consultar dados. JAMAIS.** Não importa o tamanho da tabela ou a complexidade do join — toda consulta vai pelo DuckDB no beelink via SSH (`ssh beelink`).

**NUNCA consultar por S3/Hetzner diretamente fora do `db.rodado.xyz`.** O bucket `s3://baseldosdados` é a cópia do espelho que o beelink envia; desde 2026-10-11 o **único** consumidor que consulta por ele é `db.rodado.xyz` (`db/`, roda no finland, sem túnel para o beelink). Desde 2026-10-28 `mcp_server.py` pode chegar ao S3 **através** do db.rodado.xyz (`MCP_BACKEND=http`, manda a SQL ao `/query`, nunca abre o bucket ele mesmo). Todo o resto — agentes por SSH, harness, scripts, análises — consulta pelo beelink; toda view do DuckDB que ainda referencie `s3://baseldosdados` está obsoleta (use `read_parquet('~/rodado/<dataset>/<table>/*.parquet')` com o caminho local).

Essa regra é sobre **servir consultas de dado** — nunca usar BigQuery pra isso, sem exceção. **Única exceção, estritamente escopada**: manutenção do mirror (`scripts/sync-with-source.md`), usando **somente** consulta interativa em modo Sandbox gratuito do BigQuery (sem conta de billing, cota mensal ~900GB/1TB) — `bq query` ou a Storage Read API sem billing —, nunca `bq extract` nem operação que dependa de billing ativo. **Se billing for ativado em qualquer projeto GCP usado aqui, essa exceção acaba imediatamente** — volta a ser JAMAIS, sem exceção nenhuma.

`mcp_server.py` (`MCP_BACKEND=ssh`, `_run_sql_ssh`) e `harness/beelink.ts` (branch `harness-gemma`) abrem cada sessão com `allowed_directories` restrito a `~/rodado` e `~/duckdb_tmp` (+ o prefixo `s3://healthbr-data/`), `enable_external_access=false` e `lock_configuration=true`: a SQL vem de um modelo, e um `SELECT * FROM read_text('~/.ssh/...')` passa pela checagem de somente-leitura. Ferramenta nova que leia fora de `~/rodado` precisa entrar na lista, não desligar a trava.

---

## Key Conventions

- **Never use GCP, BigQuery, or `bq` CLI for queries** — all data access goes through DuckDB only.
- **Never query through S3/Hetzner** — the only exception is the `db.rodado.xyz` front end (`db/`), which may read `s3://baseldosdados` instead of tunneling to beelink; the MCP's `http` backend reaches it only through db.rodado.xyz's `/query`. Agents, harness and scripts otherwise go through beelink.
- **SSH to beelink** for all SQL queries — `ssh beelink '~/bin/duckdb -readonly -json ~/rodado/basedosdados.duckdb'` (SQL piped over stdin, SET enable_progress_bar=false first). Always pass `-readonly`: DuckDB takes an exclusive file lock even for a bare SELECT unless told otherwise, and multiple sessions query this same file concurrently — a non-readonly connection blocks every other one until it disconnects. Never kill the process holding the lock, it's very likely another session's real work, not a stuck query. beelink is the project's only data source by default. Set `BEELINK_HOST` if the hostname differs.
- DuckDB always runs read-only; no writes to the database from queries.
- Queries on large tables must filter on partition columns (`ano`, `mes`, `sigla_uf`).
- SQL dialect is DuckDB; BigQuery syntax does not apply.
- `docs/mapa/overview/` contains per-theme markdown summaries used as LLM context.
- `docs/pesquisa/queries/` contains example SQL and CNAE audit analysis files.
