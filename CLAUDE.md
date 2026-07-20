# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**baseldosdados** mirrors the [Base dos Dados](https://basedosdados.org) project — public BigQuery tables exported as Parquet+zstd to Hetzner Object Storage (S3-compatible) — and extends it with independently-scraped sources that fill gaps Base dos Dados doesn't cover (sanctions lists, SICAF, SINAN microdata, consumer complaints and more — see `tasks/datasets_to_scrap.md` for the full catalog and provenance of every source). 760+ tables total as of 2026-07-16. DuckDB queries the data on-demand without local imports. An AI-powered TUI converts Portuguese natural language to SQL.

## Commands

### Rust (`ask/`)
```bash
cd ask && cargo build --release        # build TUI
cd ask && cargo build                  # dev build
cd ask && cargo test                   # run tests
./ask/target/release/ask               # interactive TUI
./ask/target/release/ask "Quantos municípios tem SP?"  # CLI mode
```

### Python services
```bash
python auth.py                         # auth + query HTTP server on :8081
python scripts/prepara_db.py          # generate DuckDB with views
python scripts/gera_schemas.py        # extract table schemas → JSON/text
```

### DuckDB
```bash
duckdb data/basedosdados.duckdb       # interactive shell (requires S3 env vars)
```

### Data export pipeline
```bash
./scripts/roda.sh --dry-run           # estimate costs, no writes
./scripts/roda.sh                     # run locally (needs gcloud + rclone)
./scripts/roda.sh --gcloud-run        # spin up GCP VM and run there
```

### Querying data
```bash
# Preferred: SSH to beelink (freshest data, no S3 dependency)
ssh beelink '~/bin/duckdb -json ~/rodado/basedosdados.duckdb' <<'SQL'
SET enable_progress_bar=false;
SELECT ...;
SQL

# Fallback: remote endpoint (if beelink is unavailable)
curl "https://db.xn--2dk.xyz/query?q=SELECT+..." -H "X-Password: $BASIC_AUTH_PASSWORD"
# or POST for longer queries
curl -X POST "https://db.xn--2dk.xyz/query" -H "X-Password: $BASIC_AUTH_PASSWORD" --data-raw "SELECT ..."
```

### Docker / deployment
```bash
docker build -t baseldosdados .       # multi-stage build (Rust + Python)
haloy deploy -c haloy.yml             # deploy via haloy
```

## Architecture

### Services (started by `start.sh`)
| Port | Service | Purpose |
|------|---------|---------|
| 7681 | ttyd → duckdb | Browser-accessible DuckDB shell |
| 7682 | ttyd → ask | Browser-accessible NL→SQL TUI |
| 8081 | auth.py | Cookie auth + SQL execution proxy |
| 8080 | Caddy | Public reverse proxy, forward auth |

Caddy routes by hostname: `ask.xn--2dk.xyz` → port 7682, `db.xn--2dk.xyz` → port 7681. The `/query` endpoint on `db.xn--2dk.xyz` is unauthenticated for read-only SQL via HTTP.

### `ask/` — Natural Language → SQL (Rust)
- `src/main.rs` — TUI entry point, ratatui/crossterm event loop
- `src/sql_generator.rs` — LLM backends: Gemini, OpenRouter, Ollama (sqlcoder)
- `src/table_selector.rs` — semantic table selection from embeddings before prompting
- `src/schema_filter.rs` — trims schema to relevant tables (controlled by `TOP_K_TABLES`)

LLM backend is selected by `SQL_GENERATOR` env var (`gemini`/`openrouter`/`sqlcoder`). Schema metadata lives in `docs/context/`.

### `auth.py` — Auth & Query Service
HMAC-SHA256 cookie auth. Holds a **persistent DuckDB Python connection** (in-memory + ATTACH read-only) initialized once at startup with S3 credentials and httpfs. Returns JSON. Use `X-Password` header matching `BASIC_AUTH_PASSWORD`.

### Data flow
BigQuery → Google Cloud Storage (Parquet) → Hetzner S3 (via `scripts/roda.sh` + rclone) → DuckDB httpfs reads on query.

### `docs/context/` — Schema metadata
- `basedosdados-schema.json` — full schema (3.8 MB), used by `ask`
- `schema_compact.txt` — text format for prompting
- `table_embeddings.json` — semantic vectors for table selection (11.4 MB)
- `join_keys.md` — foreign key relationships across datasets

## Environment Variables

| Variable | Used by | Purpose |
|----------|---------|---------|
| `SQL_GENERATOR` | ask | LLM backend (`gemini`/`openrouter`/`sqlcoder`) |
| `GEMINI_API_KEY` | ask | Google Gemini API key |
| `OPENROUTER_API_KEY` | ask | OpenRouter API key |
| `TOP_K_TABLES` | ask | Tables passed to LLM (default: 5) |
| `BASIC_AUTH_PASSWORD` | auth.py, Caddy | Web UI password |
| `BEELINK_HOST` | scripts, mcp_server | SSH hostname for beelink (default: `beelink`) |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | auth.py | Hetzner S3 credentials (server-side only) |
| `HETZNER_S3_ENDPOINT` | auth.py | S3 endpoint URL |
| `BUCKET_REGION` | auth.py | S3 bucket region |
| `OLLAMA_HOST` / `OLLAMA_MODEL` | ask | Local Ollama config |

## Data Querying (DuckDB/CNPJ datasets)

- Always include partition filters on large S3-backed tables to avoid timeouts.
- Validate query results against sanity bounds (e.g., contract values, row counts) before reporting; flag anomalies like trillion-real totals.
- Prefer name-based filtering combined with CPF when CPF joins alone produce implausible cardinality.
- Before presenting query results: (1) state the expected order of magnitude, (2) flag any row that exceeds it, (3) verify the count two independent ways. Only report numbers that pass all three checks.

## ⚠️ REGRA CRÍTICA — SEM EXCEÇÕES

**NUNCA usar BigQuery, GCP ou `bq` CLI. JAMAIS. Toda consulta de dados vai pelo DuckDB no beelink via SSH (`ssh beelink`). Não importa o tamanho da tabela, a complexidade do join ou se "é mais fácil" no BigQuery — DuckDB único.**

**NUNCA usar S3/Hetzner diretamente.** O bucket `s3://baseldosdados` não existe mais — todas as views no DuckDB que referenciam `s3://` estão obsoletas. Para queries em tabelas cujas views apontam para S3, use `read_parquet('~/rodado/<dataset>/<table>/*.parquet')` diretamente com o caminho local do beelink.

Essa regra é sobre **servir consultas de dado ao vivo/produção** (`ask`, `auth.py`, DuckDB) — nunca usar BigQuery pra isso, sem exceção.

Existe uma **única exceção, estritamente escopada**: manutenção do mirror do beelink (`scripts/sync-with-source.md`), usando **somente `bq query` em modo Sandbox gratuito** (sem conta de billing, cota mensal ~900GB/1TB), nunca `bq extract` nem qualquer operação que dependa de billing ativo. Essa exceção existe só porque o Sandbox sem billing tem custo zero garantido.

**Se billing for ativado em qualquer projeto GCP usado aqui, essa exceção acaba imediatamente — volta a ser JAMAIS, sem exceção nenhuma**, já que o que torna o uso pontual de BigQuery seguro hoje é justamente a impossibilidade de gerar custo.

---

## Key Conventions

- **Never use GCP, BigQuery, or `bq` CLI for queries** — all data access goes through DuckDB only.
- **Prefer SSH to beelink** for all SQL queries — `ssh beelink '~/bin/duckdb -json ~/rodado/basedosdados.duckdb'` (SQL piped over stdin, SET enable_progress_bar=false first). beelink is the project's official data source, fresher than the S3-backed endpoint. Set BEELINK_HOST env var if the hostname differs. Use the query endpoint `https://db.xn--2dk.xyz/query` only if beelink is unavailable.
- DuckDB always runs read-only; no writes to the database from queries.
- Queries on large tables must filter on partition columns (`ano`, `mes`, `sigla_uf`) — this is enforced in prompts.
- SQL dialect is DuckDB; BigQuery syntax does not apply.
- `docs/overview/` contains per-dataset markdown summaries used as LLM context.
- `docs/queries/` contains example SQL and CNAE audit analysis files.
