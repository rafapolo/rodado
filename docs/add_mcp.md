# Build a real MCP server for the Base dos Dados catalog

> **Update 2026-07-10 — superseded on one point:** `run_sql` was shipped as planned below
> (HTTP `/query` endpoint), then switched to `ssh beelink` for query execution once
> beelink was confirmed as the project's official data source (see
> [[feedback-local-duckdb-only]] / TECHNICAL.md's "MCP server" section) — fresher than
> the S3-backed endpoint, and where newly-scraped datasets in `tasks/datasets_to_scrap.md`
> land first. Everything else below (catalog tools, read-only guard, config) shipped as
> designed. Treat the `run_sql`/registration details below as historical intent, not
> current behavior — TECHNICAL.md is the source of truth for what's actually running.

## Context

`mcp.html`/`mcp-en.html` present the 533-table catalog with "MCP-style" card UI, but there is no actual Model Context Protocol server behind it — confirmed by grepping the repo for `mcp`/`jsonrpc`/`stdio` (only the marketing pages match). The goal is a real MCP server so Claude Desktop/Claude Code can browse the catalog and run read-only queries as first-class tools, instead of hand-copying table IDs out of the static pages.

Decisions locked in:
- **One MCP server, many tools** — not 34 per-theme micro-servers, not a bare `run_sql`-only server.
- **stdio transport only for v1** — a local process added via `claude mcp add` / Claude Desktop config. No Caddy/Docker/`start.sh` changes, no remote deploy. (Built with FastMCP so HTTP/SSE remains a clean follow-up, not a rewrite.)
- **Structured catalog tools + `run_sql`** — no natural-language-to-SQL tool, no shelling out to the `ask` Rust binary. Claude reads schema via the tools and writes its own SQL.

All query execution reuses the existing `https://db.xn--2dk.xyz/query` HTTP contract (same one `dbquery`/`auth.py` already implement) — the server never opens its own DuckDB connection, per the project's hard rule that all query paths go through the existing endpoint.

## Environment blocker (fix first)

The ambient global interpreter (`python3` = pyenv 3.11.7) already has `mcp 1.28.1`, `sentence-transformers 5.6.0`, `torch`, `requests` installed — but `import mcp` currently fails:
```
SystemError: The installed pydantic-core version (2.47.0) is incompatible with the current pydantic version, which requires 2.46.4.
```
Confirmed live. Fix before writing code:
```bash
pip install --upgrade pydantic pydantic-core mcp
python3 -c "from mcp.server.fastmcp import FastMCP; print('ok')"
```

## New files

**`mcp_server.py`** (repo root, single file — matches this repo's flat-script convention used by `auth.py`/`scripts/*.py`, no package needed for ~6 tools). Sections: config/env → catalog loaders → search (embeddings) → join-key parsing → `run_sql` HTTP client + read-only guard → `FastMCP` app + tool registrations → `mcp.run()`.

**`requirements-mcp.txt`** (repo root, documentation only, since deps are already present):
```
mcp>=1.28.1
sentence-transformers>=5.6.0
torch>=2.13.0
requests>=2.34.0
```
Deliberately no `duckdb` — the server must never touch DuckDB directly.

## Tools

1. **`list_datasets()`** — all datasets + table counts, from `docs/context/basedosdados-schema.json` (180 datasets, 765 tables — the untruncated superset; better source than `docs/context/schema_compact.txt`).
2. **`list_tables(dataset)`** — tables in one dataset. Unknown dataset → `difflib.get_close_matches` suggestions, not a bare error.
3. **`describe_table(table)`** — `"dataset.table"` → full column list (name/type/description) from the same schema file. Same close-match fallback on miss.
4. **`search_tables(query, top_k=10, min_similarity=0.35)`** — semantic search reusing `docs/context/table_embeddings.json` as-is (765×384 float32 matrix, loaded once at startup; trivial memory cost). Embedding the *query* string needs `sentence-transformers`; mirrors what `ask/src/table_selector.rs`'s `LocalEmbedder` already does (it shells out to a Python one-liner for this same model — here it's just in-process). **Lazy-load the model on first call**, not at startup: first call triggers a one-time ~90MB Hugging Face download and is slow; document that in the tool docstring. Default threshold `0.35` matches the Rust constant `DEFAULT_SIMILARITY_THRESHOLD`.
5. **`get_join_keys(column=None)`** — parses `docs/context/join_keys.md` (regex over `### \`col\` — N tables` headers), cached after first parse. No arg → compact index of column names; with arg → full section for a case-insensitive substring match, or `{"error", "available_keys"}` on miss.
6. **`run_sql(sql, method="post", max_rows=500)`** — the only execution tool. Same HTTP contract as `dbquery`/`auth.py`: POST/GET to `MCP_QUERY_URL` (default `https://db.xn--2dk.xyz/query`) with header `X-Password: $BASIC_AUTH_PASSWORD`. **Must check for `{"error": ...}` in a 200 response body** — `auth.py`'s `_run_query` (auth.py:87-95) returns HTTP 200 even on a SQL error, only 401/400 are non-200. Truncate results to `max_rows` client-side (server has no pagination) and say so if truncated. 120s timeout. Tool docstring embeds this project's existing query discipline (CLAUDE.md "Data Querying" section): filter on partition columns for large tables, state expected order of magnitude, verify counts two ways before reporting.

### Read-only guard in `run_sql` (defense in depth)
Strip comments → reject multiple statements (stray `;` + trailing content) → only allow first token `SELECT`/`WITH` (covers CTEs) → reject everything else (`INSERT`/`UPDATE`/`DELETE`/`CREATE`/`DROP`/`ALTER`/`ATTACH`/`PRAGMA`/`SET`/`CALL`/`INSTALL`/`LOAD`/...) with a clear "read-only by design" message, fired **before** any network call. Don't whitelist `PRAGMA`/`SET` even as "safe" — the endpoint's DuckDB connection is shared across all callers via a global lock (auth.py:11,88), so session-state mutations would leak across users.

## Config (env vars, all optional except the password)

| Var | Default |
|---|---|
| `BASIC_AUTH_PASSWORD` | required, checked lazily only when `run_sql` is first called |
| `MCP_QUERY_URL` | `https://db.xn--2dk.xyz/query` |
| `MCP_CONTEXT_DIR` | `<repo_root>/docs/context`, resolved via `Path(__file__)` so cwd doesn't matter |
| `MCP_EMBEDDING_MODEL` | read from `table_embeddings.json["model"]` at load time, override allowed |
| `MCP_SEARCH_THRESHOLD` | `0.35` |

## Registration

```bash
claude mcp add rodado -e BASIC_AUTH_PASSWORD=<value> -- python3 /Users/polux/Projetos/rodado/mcp_server.py
claude mcp list
```
Claude Desktop equivalent goes in `claude_desktop_config.json` under `mcpServers.rodado` with the same command/args/env.

## Verification

1. **Unblock the environment**: `pip install --upgrade pydantic pydantic-core mcp`, confirm `from mcp.server.fastmcp import FastMCP` imports cleanly.
2. **Static check**: `python3 -c "import json; d=json.load(open('docs/context/basedosdados-schema.json')); print(len(d), sum(len(v) for v in d.values()))"` → expect `180 765`.
3. **MCP Inspector** (`mcp dev mcp_server.py`), exercise all 6 tools manually:
   - `list_datasets` → 180 entries.
   - `list_tables("br_tse_eleicoes")` → includes `candidatos`.
   - `describe_table("br_tse_eleicoes.candidatos")` → non-empty columns.
   - `search_tables("gastos de campanha eleitoral")` → `despesas_candidato`/`receitas_candidato` near top; confirm first call is slow (model download), later calls fast.
   - `get_join_keys("cep")` → matches `docs/context/join_keys.md`.
   - `run_sql("DROP TABLE x")` → rejected client-side, no network call made.
4. **Live registration + real query**, sanity-checked per this project's existing convention (state expected magnitude → flag outliers → verify two independent ways):
   ```sql
   SELECT ano, count(*) FROM basedosdados.br_tse_eleicoes.candidatos WHERE ano = 2022 GROUP BY ano
   ```
   Expect tens of thousands, not millions. Cross-check the same count via `dbquery` CLI and/or a direct `curl` to `/query` to confirm the MCP tool's numbers match known-good clients.
