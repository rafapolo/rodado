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
from typing import Optional

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
# Survey mirrors (SISDEPEN: 3.957 cols) would flood an LLM's context if
# describe_table returned every column, so wide tables are capped.
DESCRIBE_MAX_COLS = int(os.environ.get("MCP_DESCRIBE_MAX_COLS", "150"))
# A row-count cap alone does not bound what run_sql sends back: row width
# varies by three orders of magnitude across this catalog, so the same
# `max_rows=500` is 15 tokens on a COUNT(*) and ~2,7M tokens on
# `SELECT *` over br_inep_censo_escolar.escola (455 columns). Budget the
# serialized payload too — this is the cap that actually binds.
RUN_SQL_MAX_CHARS = int(os.environ.get("MCP_RUN_SQL_MAX_CHARS", "60000"))

SCHEMA_PATH = CONTEXT_DIR / "basedosdados-schema.json"
EMBEDDINGS_PATH = CONTEXT_DIR / "table_embeddings.json"
JOIN_KEYS_PATH = CONTEXT_DIR / "join_keys.md"

# ---------------------------------------------------------------------------
# Catalog loaders (loaded once at startup — small enough to hold in memory)
# ---------------------------------------------------------------------------

with open(SCHEMA_PATH, encoding="utf-8") as f:
    _SCHEMA: dict = json.load(f)  # {dataset: {table: [{name, type, description}, ...]}}

_ALL_TABLE_IDS = [f"{ds}.{tbl}" for ds, tables in _SCHEMA.items() for tbl in tables]

# Not every catalog table has a view/schema inside beelink's basedosdados.duckdb
# (independently-scraped datasets land on disk first) — but every one of them
# has parquet under ~/rodado/<dataset>/<table>/. This map lets run_sql fall
# back transparently when the DuckDB catalog misses.
_PARQUET_GLOBS = {tid: f"~/rodado/{tid.replace('.', '/', 1)}/*.parquet" for tid in _ALL_TABLE_IDS}

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


# SQL keywords that can legally follow a table reference — anything else after
# `FROM dataset.table` is a user alias we must preserve when rewriting.
_POST_TABLE_KEYWORDS = frozenset(
    "WHERE GROUP ORDER LIMIT OFFSET JOIN LEFT RIGHT INNER FULL CROSS NATURAL "
    "ON USING UNION INTERSECT EXCEPT HAVING QUALIFY WINDOW SEMI ANTI "
    "POSITIONAL ASOF TABLESAMPLE USE AS".split()
)


def _cap_rows(rows: list, max_rows: int) -> dict:
    """Bound a result set by row count *and* serialized size.

    Returns the response dict run_sql hands back. When even a single row busts
    the budget, no row is returned: one 1000-column row serializes to ~128k
    tokens, so handing it back would be the very context blowout this guards
    against. The caller gets the column names instead — which is what they need
    to rewrite the query with an explicit projection.
    """
    if not isinstance(rows, list):
        return {"rows": rows, "truncated": False}

    total = len(rows)
    kept = rows[:max_rows]

    def size(rs: list) -> int:
        return len(json.dumps(rs, ensure_ascii=False, default=str))

    capped_by = "rows" if total > max_rows else None
    if kept and size(kept[:1]) > RUN_SQL_MAX_CHARS:
        names = list(kept[0].keys()) if isinstance(kept[0], dict) else []
        shown = names[:DESCRIBE_MAX_COLS]
        return {
            "rows": [],
            "truncated": True,
            "returned": 0,
            "total": total,
            "columns": shown,
            "columns_total": len(names),
            "note": (
                f"A single row exceeds {RUN_SQL_MAX_CHARS} characters, so no row is "
                f"returned — it would flood the context. The row has {len(names)} "
                f"column(s)"
                + (f" (first {len(shown)} listed)" if len(names) > len(shown) else "")
                + ". Re-run selecting only the columns you need, or aggregate in SQL."
            ),
        }
    if kept and size(kept) > RUN_SQL_MAX_CHARS:
        lo, hi = 1, len(kept)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if size(kept[:mid]) <= RUN_SQL_MAX_CHARS:
                lo = mid
            else:
                hi = mid - 1
        kept = kept[:lo]
        capped_by = "size"

    if capped_by is None:
        return {"rows": kept, "truncated": False}

    out = {
        "rows": kept,
        "truncated": True,
        "returned": len(kept),
        "total": total,
    }
    if capped_by == "size":
        out["note"] = (
            f"Truncated to {len(kept)} of {total} row(s) to stay under "
            f"{RUN_SQL_MAX_CHARS} characters — the rows are wide. Select the "
            f"columns you need instead of *, or aggregate in SQL."
        )
    return out


def _rewrite_to_read_parquet(sql: str) -> tuple[str, list[str]]:
    """Replace catalog `dataset.table` references with read_parquet() globs.

    Keeps an existing user alias when one follows the reference; otherwise
    aliases the relation to the bare table name so `table.column` qualifiers
    keep resolving. Returns (rewritten_sql, list of rewritten table ids).
    """
    rewritten: list[str] = []
    ids_pattern = "|".join(re.escape(tid) for tid in sorted(_PARQUET_GLOBS, key=len, reverse=True))
    pattern = re.compile(rf"(?<![\w.\"])({ids_pattern})(?![\w.])")

    def _sub(m: re.Match) -> str:
        tid = m.group(1)
        rewritten.append(tid)
        replacement = f"read_parquet('{_PARQUET_GLOBS[tid]}')"
        rest = sql[m.end():].lstrip()
        next_token = re.match(r"[A-Za-z_][A-Za-z_0-9]*", rest)
        has_alias = bool(next_token) and next_token.group(0).upper() not in _POST_TABLE_KEYWORDS
        if next_token and next_token.group(0).upper() == "AS":
            has_alias = True
        if not has_alias:
            replacement += f' AS "{tid.partition(".")[2]}"'
        return replacement

    return pattern.sub(_sub, sql), rewritten


# ---------------------------------------------------------------------------
# MCP app + tools
# ---------------------------------------------------------------------------

mcp = FastMCP("rodado")


@mcp.tool()
def list_datasets() -> dict:
    """List all datasets in the unified catalog, with their table counts.

    190 datasets, 782 tables total: the Base dos Dados mirror (RAIS, SIM, TSE,
    CGU, IBGE, INEP and others) plus independently-scraped sources filling
    gaps Base dos Dados doesn't cover (SICAF, SINAN Violência, EU/UN
    Sanctions, Consumidor.gov.br and more — see tasks/datasets_to_scrap.md
    for provenance). Use this to get oriented before drilling into a
    specific dataset with list_tables().
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
        return {
            "dataset": dataset,
            "tables": sorted(_SCHEMA[dataset].keys()),
            "parquet_path": f"~/rodado/{dataset}/<table>/*.parquet",
        }

    suggestions = difflib.get_close_matches(dataset, _SCHEMA.keys(), n=5, cutoff=0.4)
    return {
        "error": f"Unknown dataset '{dataset}'.",
        "suggestions": suggestions,
    }


@mcp.tool()
def describe_table(table: str) -> dict:
    """Describe one table's columns: name and type.

    `table` must be "dataset.table", e.g. "br_tse_eleicoes.candidatos".
    On a miss, returns close-match suggestions from the full table list.

    Column descriptions are not available: the mirrored schema carries only
    name and type. Use `search_tables` for semantic lookup and `docs/overview/`
    for what a dataset actually means.

    Very wide tables are truncated to the first 150 columns (survey mirrors
    reach 3.957) — the leading columns are the identifying ones. When that
    happens the reply carries a `columns_truncated` block with the real total;
    query `parquet_path` with DESCRIBE via `run_sql` to see the rest.
    """
    if "." not in table:
        return {"error": "table must be in the form 'dataset.table'."}

    dataset, _, table_name = table.partition(".")
    tables = _SCHEMA.get(dataset)
    if tables is None or table_name not in tables:
        suggestions = difflib.get_close_matches(table, _ALL_TABLE_IDS, n=5, cutoff=0.4)
        return {"error": f"Unknown table '{table}'.", "suggestions": suggestions}

    columns = tables[table_name]
    result = {
        "table": table,
        "columns": columns[:DESCRIBE_MAX_COLS],
        "parquet_path": _PARQUET_GLOBS[table],
    }
    if len(columns) > DESCRIBE_MAX_COLS:
        result["columns_truncated"] = {
            "shown": DESCRIBE_MAX_COLS,
            "total": len(columns),
            "note": (
                f"Showing the first {DESCRIBE_MAX_COLS} of {len(columns)} columns. "
                f"Run DESCRIBE SELECT * FROM read_parquet('{_PARQUET_GLOBS[table]}') "
                f"via run_sql for the full list."
            ),
        }
    return result


@mcp.tool()
def search_tables(query: str, top_k: int = 10, min_similarity: float = SEARCH_THRESHOLD) -> dict:
    """Semantic search over all 782 tables by natural-language description.

    Example: search_tables("gastos de campanha eleitoral") surfaces
    despesas_candidato/receitas_candidato even without exact keyword matches.

    Each result's `text` is truncated to keep responses token-cheap — call
    describe_table() on a hit for the full column list.

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

    max_text = 280
    results = [
        {
            "table": t["id"],
            "similarity": round(score, 4),
            "text": t["text"][:max_text] + ("…" if len(t["text"]) > max_text else ""),
        }
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
    any SSH call.

    Results are truncated client-side to `max_rows` AND to a serialized-size
    budget, whichever binds first. The size budget is the one that matters:
    `SELECT *` on a wide table (455 columns) at the default row cap would
    otherwise return millions of tokens. When it trips, the reply carries
    `truncated`, `returned`/`total` and a `note` — project the columns you
    need or aggregate in SQL rather than raising `max_rows`.

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

    Not every catalog table has a view inside basedosdados.duckdb (scraped
    datasets land on disk first). When DuckDB reports a Catalog Error, the
    query is automatically retried with each known `dataset.table` reference
    rewritten to its read_parquet() glob, so plain catalog names work either
    way; the response carries `rewritten_tables` when that happened.
    """
    error = _check_read_only(sql)
    if error:
        return {"error": error}

    result = _run_sql_ssh(sql)
    # Two recoverable failure modes: the table has no view in the DuckDB
    # catalog (scraped datasets), or the view exists but still points at the
    # decommissioned s3:// bucket. Both are fixed by querying the local
    # parquet directly.
    _recoverable = ("Catalog Error", "NoSuchBucket", "s3://")
    if "error" in result and any(marker in result["error"] for marker in _recoverable):
        fallback_sql, rewritten = _rewrite_to_read_parquet(sql)
        if rewritten:
            retry = _run_sql_ssh(fallback_sql)
            if "error" not in retry:
                out = _cap_rows(retry["rows"], max_rows)
                out["rewritten_tables"] = rewritten
                return out
    if "error" in result:
        return result

    return _cap_rows(result["rows"], max_rows)


# ---------------------------------------------------------------------------
# Friendly per-theme tools — thin wrappers over data already on beelink or a
# single well-known live API, for callers who don't want to write SQL
# ---------------------------------------------------------------------------

_CNPJ_BASE = "~/rodado/br_me_cnpj"


def _only_digits(s: str) -> str:
    return re.sub(r"\D", "", s or "")


@mcp.tool()
def consultar_cnpj(cnpj: str, max_rows: int = 20) -> dict:
    """Look up a Brazilian company by CNPJ against the full registry already
    mirrored on beelink (br_me_cnpj — empresas/estabelecimentos/socios) —
    no external API call, just SQL over local data already on this server.
    Accepts a full 14-digit CNPJ or an 8-digit CNPJ básico; punctuation
    (dots/slash/dash) is stripped automatically.

    Returns company info (razão social, natureza jurídica, capital social),
    matriz/filial establishments and registered sócios — each list truncated
    to `max_rows` (default 20, to keep responses token-cheap; raise it when
    the full picture is needed). `*_truncated: true` flags a cut list.
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

    # LIMIT n+1 so a full page signals truncation without a COUNT round-trip.
    estabelecimentos = _run_sql_ssh(
        f"SELECT cnpj, identificador_matriz_filial, nome_fantasia, "
        f"situacao_cadastral, data_situacao_cadastral, sigla_uf, cep "
        f"FROM read_parquet('{_CNPJ_BASE}/estabelecimentos/*.parquet') "
        f"WHERE cnpj_basico = '{basico}' LIMIT {max_rows + 1}"
    )
    socios = _run_sql_ssh(
        f"SELECT nome, documento, qualificacao, data "
        f"FROM read_parquet('{_CNPJ_BASE}/socios/*.parquet') "
        f"WHERE cnpj_basico = '{basico}' LIMIT {max_rows + 1}"
    )

    estab_rows = estabelecimentos.get("rows", [])
    socio_rows = socios.get("rows", [])
    return {
        "cnpj_basico": basico,
        "empresa": empresa["rows"][0],
        "estabelecimentos": estab_rows[:max_rows],
        "estabelecimentos_truncated": len(estab_rows) > max_rows,
        "socios": socio_rows[:max_rows],
        "socios_truncated": len(socio_rows) > max_rows,
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


@mcp.tool()
def consultar_divida_ativa(
    cpf_cnpj: str,
    categoria: Optional[str] = None,
    max_rows: int = 20,
) -> dict:
    """Consult PGFN (Procuradoria-Geral da Fazenda Nacional) active debt
    registry — 46.6M inscriptions of federal tax debts (FGTS, INSS/previdenciário,
    non-previdenciário taxes like IRPJ/COFINS/CPMF) against companies and individuals.

    Looks up by CPF or CNPJ (punctuation stripped automatically). Optionally
    filter by `categoria` ('fgts', 'previdenciario', 'nao_previdenciario').

    Returns debtor info: nome, CPF/CNPJ, valor consolidado (string, formatted
    like '23337387019.50'), situação (ajuizado/em cobrança/parcelado), categoria.
    """
    digits = _only_digits(cpf_cnpj)
    if len(digits) not in (8, 11, 14):
        return {"error": f"'{cpf_cnpj}' — need 8/14 digits for CNPJ or 11 for CPF."}

    where_cpfcnpj = f"CPF_CNPJ LIKE '%{digits}%'"
    cat_filter = f" AND categoria = '{categoria}'" if categoria else ""

    result = _run_sql_ssh(
        f"SELECT CPF_CNPJ, NOME_DEVEDOR, TIPO_PESSOA, TIPO_DEVEDOR, "
        f"UF_DEVEDOR, VALOR_CONSOLIDADO, SITUACAO_INSCRICAO, "
        f"RECEITA_PRINCIPAL, DATA_INSCRICAO, INDICADOR_AJUIZADO, categoria "
        f"FROM read_parquet('~/rodado/br_pgfn_dividaativa/divida/*.parquet') "
        f"WHERE {where_cpfcnpj}{cat_filter} "
        f"ORDER BY CAST(regexp_replace(regexp_replace(VALOR_CONSOLIDADO, '\\.', ''), ',', '.') AS double) DESC "
        f"LIMIT {max_rows + 1}"
    )
    if "error" in result:
        return result

    rows = result.get("rows", [])
    return {
        "cpf_cnpj": cpf_cnpj,
        "inscricoes": rows[:max_rows],
        "inscricoes_truncated": len(rows) > max_rows,
        "total_encontradas": len(rows),
    }


@mcp.tool()
def consultar_precos_combustivel(
    municipio: Optional[str] = None,
    produto: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    max_rows: int = 50,
) -> dict:
    """Query ANP weekly fuel resale price survey — 2M+ rows (2022–2026),
    one row per gas station per fuel product per week, Brazil-wide.

    Filters: municipio (partial match), produto ('GASOLINA', 'ETANOL',
    'DIESEL', 'GLP', etc), data range (YYYY-MM-DD).

    Returns station info (CNPJ, razão social, bandeira), product, price,
    collection date. Prices are per-liter in BRL (preco_revenda).
    """
    and_clauses = []
    if municipio:
        and_clauses.append(f"municipio ILIKE '%{municipio}%'")
    if produto:
        and_clauses.append(f"produto ILIKE '%{produto}%'")
    if data_inicio:
        and_clauses.append(f"data_coleta >= '{data_inicio}'")
    if data_fim:
        and_clauses.append(f"data_coleta <= '{data_fim}'")

    where = " WHERE " + " AND ".join(and_clauses) if and_clauses else ""

    result = _run_sql_ssh(
        f"SELECT cnpj, razao, municipio, estado, bandeira, produto, "
        f"preco_revenda, data_coleta "
        f"FROM read_parquet('~/rodado/br_anp_combustiveis/precos/*.parquet'){where} "
        f"ORDER BY data_coleta DESC LIMIT {max_rows + 1}"
    )
    if "error" in result:
        return result

    rows = result.get("rows", [])
    # Summarize available products if no filter
    if not produto and rows:
        products = list(dict.fromkeys(r["produto"] for r in rows if r.get("produto")))
        return {
            "precos": rows[:max_rows],
            "truncated": len(rows) > max_rows,
            "produtos_disponiveis": products[:20],
        }
    return {
        "precos": rows[:max_rows],
        "truncated": len(rows) > max_rows,
    }


@mcp.tool()
def consultar_jurisprudencia_stj(
    processo: Optional[str] = None,
    ministro: Optional[str] = None,
    assunto: Optional[str] = None,
    data_inicio: Optional[str] = None,
    max_rows: int = 20,
) -> dict:
    """Search STJ (Superior Tribunal de Justiça) document metadata —
    549K decisions/acórdãos from 2021-01-04 onwards, with relator, type,
    case number, subject, and full text summary.

    Filters by: processo (case number), ministro (relator name, partial match),
    assunto (subject/law topic), data_inicio (earliest publication date).

    Returns SeqDocumento, dataPublicacao, tipoDocumento, processo,
    NM_MINISTRO, assuntos, teor (headnote summary).
    """
    and_clauses = []
    if processo:
        and_clauses.append(f"processo ILIKE '%{processo}%'")
    if ministro:
        and_clauses.append(f"NM_MINISTRO ILIKE '%{ministro}%'")
    if assunto:
        and_clauses.append(f"assuntos ILIKE '%{assunto}%'")
    if data_inicio:
        and_clauses.append(f"dataPublicacao >= '{data_inicio}'")

    where = " WHERE " + " AND ".join(and_clauses) if and_clauses else ""

    result = _run_sql_ssh(
        f"SELECT SeqDocumento, dataPublicacao, tipoDocumento, processo, "
        f"NM_MINISTRO, assunto, teor "
        f"FROM read_parquet('~/rodado/br_stj_dadosabertos/documentos/*.parquet'){where} "
        f"ORDER BY dataPublicacao DESC LIMIT {max_rows + 1}"
    )
    if "error" in result:
        return result

    rows = result.get("rows", [])
    return {
        "documentos": rows[:max_rows],
        "truncated": len(rows) > max_rows,
    }


@mcp.tool()
def consultar_populacao_carceraria(
    uf: Optional[str] = None,
    ciclo: Optional[str] = None,
    serie_historica: bool = False,
    max_rows: int = 40,
) -> dict:
    """Query the SISDEPEN prison census — 38K establishment-level records
    covering 22 semiannual cycles from 2014 to 2025 (successor to INFOPEN).

    Default: one row per UF for the most recent cycle, with prison population,
    capacity, occupancy rate (>100% = overcrowded) and share held without
    conviction (presos provisórios).

    Args:
        uf: filter to one state (e.g. "SP"). Omit for all states.
        ciclo: cycle id, e.g. "ciclo_13_2022_h2". Defaults to the latest
            ("ciclo_19_2025_h2"). Cycles run ciclo_01_2016_h2 .. ciclo_19_2025_h2,
            plus legacy "infopen_2014" / "infopen_2015" (different survey format,
            population field not filled).
        serie_historica: if True, return the time series by cycle instead of
            the per-UF cross-section (national, or for `uf` if given).

    Note: figures are self-reported by each establishment. The `presos` series
    is comparable across cycles; `vagas` (capacity) is NOT — it jumps from
    261,601 to 450,411 between 2022_h2 and 2023_h1 on a questionnaire change,
    not construction. Use occupancy only within a single cycle.
    """
    src = "read_parquet('~/rodado/br_mjsp_sisdepen/populacao_carceraria/*.parquet')"
    pop = 'TRY_CAST("4_1_populacao_prisional_total" AS BIGINT)'
    cap = ('TRY_CAST("1_3_capacidade_do_estabelecimento_masculino_total" AS BIGINT)'
           ' + TRY_CAST("1_3_capacidade_do_estabelecimento_feminino_total" AS BIGINT)')
    prov = ('TRY_CAST("4_1_populacao_prisional_presos_provisorios_sem_condenacao_total"'
            ' AS BIGINT)')

    if serie_historica:
        where = " WHERE ciclo_arquivo LIKE 'ciclo%'"
        if uf:
            where += f" AND uf = '{uf.strip().upper()}'"
        result = _run_sql_ssh(
            f"SELECT ciclo_arquivo AS ciclo, SUM({pop}) AS presos, SUM({cap}) AS vagas, "
            f"SUM({prov}) AS provisorios FROM {src}{where} "
            f"GROUP BY 1 ORDER BY 1 LIMIT {max_rows + 1}"
        )
        if "error" in result:
            return result
        rows = result.get("rows", [])
        return {
            "escopo": uf.strip().upper() if uf else "Brasil",
            "serie": rows[:max_rows],
            "truncated": len(rows) > max_rows,
        }

    where = f" WHERE ciclo_arquivo = '{(ciclo or 'ciclo_19_2025_h2').strip()}' AND uf IS NOT NULL"
    if uf:
        where += f" AND uf = '{uf.strip().upper()}'"
    result = _run_sql_ssh(
        f"SELECT uf, SUM({pop}) AS presos, SUM({cap}) AS vagas, SUM({prov}) AS provisorios, "
        f"ROUND(SUM({pop}) * 100.0 / NULLIF(SUM({cap}), 0), 1) AS ocupacao_pct, "
        f"ROUND(SUM({prov}) * 100.0 / NULLIF(SUM({pop}), 0), 1) AS provisorios_pct, "
        f"COUNT(*) AS estabelecimentos "
        f"FROM {src}{where} GROUP BY uf ORDER BY presos DESC LIMIT {max_rows + 1}"
    )
    if "error" in result:
        return result

    rows = result.get("rows", [])
    return {
        "ciclo": (ciclo or "ciclo_19_2025_h2").strip(),
        "estados": rows[:max_rows],
        "truncated": len(rows) > max_rows,
    }


if __name__ == "__main__":
    mcp.run()
