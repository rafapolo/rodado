#!/usr/bin/env python3
"""MCP server exposing the Base dos Dados catalog (docs/context/) and the
beelink DuckDB mirror as tools for Claude Desktop/Claude Code.

Never opens its own DuckDB connection locally — all SQL execution is
delegated to the DuckDB CLI on beelink over SSH (the project's official data
source as of 2026-07-09: fresher than the S3-backed remote endpoint and the
only place newly-scraped datasets land first).
"""
import difflib
import json
import os
import re
import subprocess
import threading
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent
CONTEXT_DIR = Path(os.environ.get("MCP_CONTEXT_DIR", REPO_ROOT / "docs" / "context"))
BEELINK_HOST = os.environ.get("MCP_BEELINK_HOST", "beelink")
BEELINK_DUCKDB_BIN = os.environ.get("MCP_BEELINK_DUCKDB_BIN", "~/bin/duckdb")
BEELINK_DUCKDB_PATH = os.environ.get("MCP_BEELINK_DUCKDB_PATH", "~/rodado/basedosdados.duckdb")
SEARCH_THRESHOLD = float(os.environ.get("MCP_SEARCH_THRESHOLD", "0.35"))

SCHEMA_PATH = CONTEXT_DIR / "basedosdados-schema.json"
EMBEDDINGS_PATH = CONTEXT_DIR / "table_embeddings.json"
JOIN_KEYS_PATH = CONTEXT_DIR / "join_keys.md"

# ---------------------------------------------------------------------------
# Catalog loaders (loaded once at startup — small enough to hold in memory)
# ---------------------------------------------------------------------------

with open(SCHEMA_PATH, encoding="utf-8") as f:
    _SCHEMA: dict = json.load(f)  # {dataset: {table: [{name, type, description}, ...]}}

_ALL_TABLE_IDS = [f"{ds}.{tbl}" for ds, tables in _SCHEMA.items() for tbl in tables]

# ---------------------------------------------------------------------------
# Search (embeddings) — lazy-loaded, first call downloads the model (~90MB)
# ---------------------------------------------------------------------------

_embedding_model = None
_embedding_model_lock = threading.Lock()
_table_embeddings = None  # {"tables": [{"id","text","embedding"}], "model": str}


def _load_embeddings():
    global _table_embeddings
    if _table_embeddings is None:
        with open(EMBEDDINGS_PATH, encoding="utf-8") as f:
            _table_embeddings = json.load(f)
    return _table_embeddings


def _get_embedding_model():
    global _embedding_model
    with _embedding_model_lock:
        if _embedding_model is None:
            from sentence_transformers import SentenceTransformer

            data = _load_embeddings()
            model_name = os.environ.get("MCP_EMBEDDING_MODEL", data["model"])
            _embedding_model = SentenceTransformer(model_name)
    return _embedding_model


def _cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ---------------------------------------------------------------------------
# Join keys — parsed once, cached
# ---------------------------------------------------------------------------

_join_keys_index = None  # {column_lower: section_text}
_join_keys_lock = threading.Lock()

_JOIN_KEY_HEADER_RE = re.compile(r"^### `([^`]+)` — (\d+ tables?)\s*$", re.MULTILINE)


def _parse_join_keys():
    global _join_keys_index
    with _join_keys_lock:
        if _join_keys_index is not None:
            return _join_keys_index
        text = JOIN_KEYS_PATH.read_text(encoding="utf-8")
        headers = list(_JOIN_KEY_HEADER_RE.finditer(text))
        index = {}
        for i, m in enumerate(headers):
            start = m.start()
            end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
            index[m.group(1).lower()] = {
                "column": m.group(1),
                "count": m.group(2),
                "section": text[start:end].strip(),
            }
        _join_keys_index = index
        return _join_keys_index


# ---------------------------------------------------------------------------
# run_sql — read-only guard + HTTP client
# ---------------------------------------------------------------------------

_DISALLOWED_KEYWORDS = (
    "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER", "ATTACH",
    "DETACH", "PRAGMA", "SET", "CALL", "INSTALL", "LOAD", "COPY", "EXPORT",
    "IMPORT", "VACUUM", "CHECKPOINT", "GRANT", "REVOKE", "TRUNCATE",
    "REPLACE", "MERGE",
)


def _strip_sql_comments(sql: str) -> str:
    sql = re.sub(r"--[^\n]*", "", sql)
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    return sql


def _check_read_only(sql: str) -> str | None:
    """Returns an error message if sql isn't a safe single read-only statement, else None."""
    stripped = _strip_sql_comments(sql).strip()
    if not stripped:
        return "Empty query."

    body = stripped[:-1].strip() if stripped.endswith(";") else stripped
    if ";" in body:
        return "Multiple statements are not allowed — read-only by design."

    first_token_match = re.match(r"[A-Za-z_]+", body)
    first_token = first_token_match.group(0).upper() if first_token_match else ""
    if first_token not in ("SELECT", "WITH"):
        return (
            f"Statement type '{first_token or '?'}' is not allowed — "
            "read-only by design. Only SELECT/WITH queries are permitted."
        )

    upper_body = body.upper()
    for kw in _DISALLOWED_KEYWORDS:
        if re.search(rf"\b{kw}\b", upper_body):
            return f"Keyword '{kw}' is not allowed — read-only by design."

    return None


def _run_sql_ssh(sql: str) -> dict:
    remote_cmd = f"{BEELINK_DUCKDB_BIN} -json {BEELINK_DUCKDB_PATH}"
    # beelink's ~/.duckdbrc sets enable_progress_bar=true, which prints a
    # progress meter to stdout for any query past the render threshold
    # (~2s) and corrupts -json output. Disable it for this session only —
    # doesn't touch the on-disk .duckdbrc.
    stdin_payload = f"SET enable_progress_bar=false;\n{sql}"
    try:
        proc = subprocess.run(
            ["ssh", BEELINK_HOST, remote_cmd],
            input=stdin_payload.encode("utf-8"),
            capture_output=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return {"error": "Query timed out after 120s (ssh beelink)."}
    except FileNotFoundError:
        return {"error": "ssh not found on PATH — cannot reach beelink."}

    if proc.returncode != 0:
        stderr = proc.stderr.decode("utf-8", errors="replace")
        stderr = re.sub(r"\x1b\[[0-9;]*m", "", stderr)  # strip ANSI color codes
        # Strip the duckdbrc-load banner line the CLI prints on every invocation.
        stderr = re.sub(r"^.*Loading resources from.*\n?", "", stderr, flags=re.MULTILINE)
        return {"error": stderr.strip() or f"ssh beelink exited with status {proc.returncode}"}

    stdout = proc.stdout.decode("utf-8", errors="replace").strip()
    if not stdout:
        return {"rows": []}

    try:
        return {"rows": json.loads(stdout)}
    except json.JSONDecodeError:
        return {"error": f"Non-JSON response from beelink: {stdout[:2000]}"}


# ---------------------------------------------------------------------------
# MCP app + tools
# ---------------------------------------------------------------------------

mcp = FastMCP("rodado")


@mcp.tool()
def list_datasets() -> dict:
    """List all datasets in the Base dos Dados catalog mirror, with their table counts.

    180 datasets, 765 tables total (RAIS, SIM, TSE, CGU, IBGE, INEP and others,
    mirrored from Base dos Dados). Use this to get oriented before drilling
    into a specific dataset with list_tables().
    """
    return {
        "count": len(_SCHEMA),
        "datasets": [
            {"dataset": ds, "table_count": len(tables)}
            for ds, tables in sorted(_SCHEMA.items())
        ],
    }


@mcp.tool()
def list_tables(dataset: str) -> dict:
    """List the tables in one dataset (e.g. 'br_tse_eleicoes').

    If the dataset name doesn't match exactly, returns close-match suggestions
    instead of an empty result.
    """
    if dataset in _SCHEMA:
        return {"dataset": dataset, "tables": sorted(_SCHEMA[dataset].keys())}

    suggestions = difflib.get_close_matches(dataset, _SCHEMA.keys(), n=5, cutoff=0.4)
    return {
        "error": f"Unknown dataset '{dataset}'.",
        "suggestions": suggestions,
    }


@mcp.tool()
def describe_table(table: str) -> dict:
    """Describe one table's columns: name, type, and description.

    `table` must be "dataset.table", e.g. "br_tse_eleicoes.candidatos".
    On a miss, returns close-match suggestions from the full table list.
    """
    if "." not in table:
        return {"error": "table must be in the form 'dataset.table'."}

    dataset, _, table_name = table.partition(".")
    tables = _SCHEMA.get(dataset)
    if tables is None or table_name not in tables:
        suggestions = difflib.get_close_matches(table, _ALL_TABLE_IDS, n=5, cutoff=0.4)
        return {"error": f"Unknown table '{table}'.", "suggestions": suggestions}

    return {"table": table, "columns": tables[table_name]}


@mcp.tool()
def search_tables(query: str, top_k: int = 10, min_similarity: float = SEARCH_THRESHOLD) -> dict:
    """Semantic search over all 765 tables by natural-language description.

    Example: search_tables("gastos de campanha eleitoral") surfaces
    despesas_candidato/receitas_candidato even without exact keyword matches.

    NOTE: the first call in a session downloads the embedding model
    (~90MB from Hugging Face) and is slow; subsequent calls are fast.
    """
    model = _get_embedding_model()
    data = _load_embeddings()
    query_embedding = model.encode(query).tolist()

    scored = [
        (_cosine_similarity(query_embedding, t["embedding"]), t)
        for t in data["tables"]
    ]
    scored.sort(key=lambda x: x[0], reverse=True)

    results = [
        {"table": t["id"], "similarity": round(score, 4), "text": t["text"]}
        for score, t in scored
        if score >= min_similarity
    ][:top_k]

    return {"query": query, "results": results}


@mcp.tool()
def get_join_keys(column: str | None = None) -> dict:
    """Look up foreign-key join columns shared across tables.

    No argument: returns a compact index of all documented join columns.
    With `column`: case-insensitive substring match returning the full
    reference section (sample tables + example JOIN) for that column, or
    an error with the available keys on a miss.
    """
    index = _parse_join_keys()

    if column is None:
        return {"columns": [{"column": v["column"], "count": v["count"]} for v in index.values()]}

    needle = column.lower()
    for key, entry in index.items():
        if needle in key:
            return {"column": entry["column"], "section": entry["section"]}

    return {
        "error": f"No join key matching '{column}'.",
        "available_keys": [v["column"] for v in index.values()],
    }


@mcp.tool()
def run_sql(sql: str, max_rows: int = 500) -> dict:
    """Run a read-only SQL query against beelink's DuckDB mirror over SSH —
    the project's official data source (fresher than the S3-backed remote
    endpoint, and where newly-scraped datasets land first). This server
    never opens its own DuckDB connection.

    Only SELECT/WITH queries are allowed; everything else is rejected before
    any SSH call. Results are truncated client-side to `max_rows`.

    Query discipline (per this project's conventions):
    - Always filter large tables on partition columns (ano, mes, sigla_uf)
      to avoid timeouts.
    - Before reporting results: state the expected order of magnitude,
      flag any row that exceeds it, and verify counts two independent ways.
    - SQL dialect is DuckDB, not BigQuery.
    - Some views in beelink's basedosdados.duckdb are stale and still point
      at s3://; if a query on a view looks wrong, check
      `SELECT sql FROM duckdb_views() WHERE view_name='...'` and fall back to
      `read_parquet('~/rodado/<dataset>/<table>/*.parquet')` directly.
    """
    error = _check_read_only(sql)
    if error:
        return {"error": error}

    result = _run_sql_ssh(sql)
    if "error" in result:
        return result

    rows = result["rows"]
    if isinstance(rows, list) and len(rows) > max_rows:
        return {
            "rows": rows[:max_rows],
            "truncated": True,
            "returned": max_rows,
            "total": len(rows),
        }
    return {"rows": rows, "truncated": False}


# ---------------------------------------------------------------------------
# Friendly per-theme tools — thin wrappers over data already on beelink or a
# single well-known live API, for callers who don't want to write SQL
# ---------------------------------------------------------------------------

_CNPJ_BASE = "~/rodado/br_me_cnpj"


def _only_digits(s: str) -> str:
    return re.sub(r"\D", "", s or "")


@mcp.tool()
def consultar_cnpj(cnpj: str) -> dict:
    """Look up a Brazilian company by CNPJ against the full registry already
    mirrored on beelink (br_me_cnpj — empresas/estabelecimentos/socios) —
    no external API call, just SQL over local data already on this server.
    Accepts a full 14-digit CNPJ or an 8-digit CNPJ básico; punctuation
    (dots/slash/dash) is stripped automatically.

    Returns company info (razão social, natureza jurídica, capital social),
    all matriz/filial establishments (up to 50), and registered sócios (up
    to 50).
    """
    digits = _only_digits(cnpj)
    if len(digits) not in (8, 14):
        return {"error": f"'{cnpj}' isn't a valid CNPJ (need 8 or 14 digits, got {len(digits)})."}
    basico = digits[:8]

    empresa = _run_sql_ssh(
        f"SELECT cnpj_basico, razao_social, natureza_juridica, "
        f"qualificacao_responsavel, capital_social "
        f"FROM read_parquet('{_CNPJ_BASE}/empresas/*.parquet') "
        f"WHERE cnpj_basico = '{basico}' LIMIT 1"
    )
    if "error" in empresa:
        return empresa
    if not empresa["rows"]:
        return {"error": f"No company found for cnpj_basico '{basico}'."}

    estabelecimentos = _run_sql_ssh(
        f"SELECT cnpj, identificador_matriz_filial, nome_fantasia, "
        f"situacao_cadastral, data_situacao_cadastral, sigla_uf, cep "
        f"FROM read_parquet('{_CNPJ_BASE}/estabelecimentos/*.parquet') "
        f"WHERE cnpj_basico = '{basico}' LIMIT 50"
    )
    socios = _run_sql_ssh(
        f"SELECT nome, documento, qualificacao, data "
        f"FROM read_parquet('{_CNPJ_BASE}/socios/*.parquet') "
        f"WHERE cnpj_basico = '{basico}' LIMIT 50"
    )

    return {
        "cnpj_basico": basico,
        "empresa": empresa["rows"][0],
        "estabelecimentos": estabelecimentos.get("rows", []),
        "socios": socios.get("rows", []),
    }


@mcp.tool()
def consultar_cep(cep: str) -> dict:
    """Look up a Brazilian address by CEP via ViaCEP.

    There's no bulk-downloadable CEP database to mirror (Correios only sells
    that commercially), so this is a genuine live external lookup — but kept
    consistent with this server's single-execution-path design: it shells
    out through `ssh beelink` (curl there) rather than making an HTTP call
    from this process directly.
    """
    digits = _only_digits(cep)
    if len(digits) != 8:
        return {"error": f"'{cep}' isn't a valid CEP (need 8 digits, got {len(digits)})."}

    cmd = f"curl -s --max-time 10 https://viacep.com.br/ws/{digits}/json/"
    try:
        proc = subprocess.run(
            ["ssh", BEELINK_HOST, cmd], capture_output=True, timeout=15
        )
    except subprocess.TimeoutExpired:
        return {"error": "Query timed out after 15s (ssh beelink -> viacep.com.br)."}

    if proc.returncode != 0:
        return {"error": proc.stderr.decode("utf-8", errors="replace").strip() or "ssh/curl failed"}

    stdout = proc.stdout.decode("utf-8", errors="replace").strip()
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        return {"error": f"Non-JSON response from ViaCEP: {stdout[:500]}"}

    if data.get("erro"):
        return {"error": f"CEP '{digits}' not found."}
    return data


if __name__ == "__main__":
    mcp.run()
