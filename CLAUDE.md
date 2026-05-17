# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**baseldosdados** mirrors the [Base dos Dados](https://basedosdados.org) project — 533 public BigQuery tables exported as Parquet+zstd to Hetzner Object Storage (S3-compatible). DuckDB queries the data on-demand without local imports. An AI-powered TUI converts Portuguese natural language to SQL.

## Commands

### Rust (`ask/` and `dbquery/`)
```bash
cd ask && cargo build --release        # build TUI
cd ask && cargo build                  # dev build
cd ask && cargo test                   # run tests
./ask/target/release/ask               # interactive TUI
./ask/target/release/ask "Quantos municípios tem SP?"  # CLI mode
cd dbquery && cargo build --release
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

### Querying data (preferred)
```bash
# Use the remote endpoint — collocated with S3, persistent connection, faster than local
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

LLM backend is selected by `SQL_GENERATOR` env var (`gemini`/`openrouter`/`sqlcoder`). Schema metadata lives in `context/`.

### `auth.py` — Auth & Query Service
HMAC-SHA256 cookie auth. Holds a **persistent DuckDB Python connection** (in-memory + ATTACH read-only) initialized once at startup with S3 credentials and httpfs. Returns JSON. Use `X-Password` header matching `BASIC_AUTH_PASSWORD`.

### Data flow
BigQuery → Google Cloud Storage (Parquet) → Hetzner S3 (via `scripts/roda.sh` + rclone) → DuckDB httpfs reads on query.

### `context/` — Schema metadata
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
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | auth.py, duckdb | Hetzner S3 credentials |
| `HETZNER_S3_ENDPOINT` | auth.py, duckdb | S3 endpoint URL |
| `BUCKET_REGION` | auth.py | S3 bucket region |
| `OLLAMA_HOST` / `OLLAMA_MODEL` | ask | Local Ollama config |

## Key Conventions

- **Never use GCP, BigQuery, or `bq` CLI for queries** — all data access goes through DuckDB only.
- **Prefer the remote endpoint** `https://db.xn--2dk.xyz/query` for all SQL queries — it is collocated with Hetzner S3 and has a persistent warmed connection. Local DuckDB is only a fallback when the server is unreachable.
- DuckDB always runs read-only; no writes to the database from queries.
- Queries on large tables must filter on partition columns (`ano`, `mes`, `sigla_uf`) — this is enforced in prompts.
- SQL dialect is DuckDB; BigQuery syntax does not apply.
- `overview/` contains per-dataset markdown summaries used as LLM context.
- `queries/` contains example SQL and CNAE audit analysis files.
