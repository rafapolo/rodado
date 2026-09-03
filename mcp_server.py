#!/usr/bin/env python3
"""MCP server exposing the Base dos Dados catalog (docs/context/) and the
beelink DuckDB mirror as tools for Claude Desktop/Claude Code.

Never opens its own DuckDB connection locally — all SQL execution is
delegated to the DuckDB CLI on beelink over SSH (the project's only data
source since 2026-07-09: local Parquet on beelink, no cloud storage — this
is where newly-scraped datasets land first).
"""
import difflib
import json
import os
import re
import subprocess
import threading
from pathlib import Path
from typing import Optional

import yaml
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
DOC2QUERY_INDEX_PATH = CONTEXT_DIR / "doc2query_index.json"
DOC2QUERY_VECTORS_PATH = CONTEXT_DIR / "doc2query_vectors.npy"
JOIN_KEYS_PATH = CONTEXT_DIR / "join_keys.md"
BRIDGES_PATH = CONTEXT_DIR / "bridges.yaml"
METRICS_PATH = CONTEXT_DIR / "metrics.yaml"
HIERARCHIES_PATH = CONTEXT_DIR / "hierarchies.yaml"
DICIONARIO_COVERAGE_PATH = CONTEXT_DIR / "dicionario_coverage.json"

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
# Join knowledge (docs/context/bridges.yaml)
# ---------------------------------------------------------------------------
# `get_join_keys` still reads join_keys.md, and has to: 92 of its 152 sections
# are auto-detected from schemas.json and exist only in the rendered markdown.
# The YAML carries the part that has to be *executed* rather than read — the
# normalization expressions — so resolve_join can hand back a clause instead of
# a paragraph describing one.

with open(BRIDGES_PATH, encoding="utf-8") as f:
    _BRIDGES: dict = yaml.safe_load(f)

_FALSE_FRIENDS: dict = _BRIDGES.get("false_friends", {})
_CODED_DIFFERENTLY: dict = _BRIDGES.get("coded_differently", {})
_CONCEPTS: dict = _BRIDGES.get("concepts", {})
_CONCEPT_ALIASES: dict = _BRIDGES.get("concept_aliases", {})

with open(METRICS_PATH, encoding="utf-8") as f:
    _METRICS: dict = yaml.safe_load(f).get("metrics", {})

with open(HIERARCHIES_PATH, encoding="utf-8") as f:
    _HIERARCHIES: dict = yaml.safe_load(f).get("hierarchies", {})

# IBGE census microdata (1970-2010) keeps raw IBGE codes as column names
# (`v0502`, `v6033`...) instead of the Portuguese names the rest of the
# mirror normalizes to. `{dataset}.dicionario` has the chave->valor decode;
# this map (dataset.table -> decodable column names), generated offline by
# scripts/gera_dicionario_coverage.py, is what lets describe_table point a
# caller at it instead of returning bare `v0502` with no hint it's decodable.
with open(DICIONARIO_COVERAGE_PATH, encoding="utf-8") as f:
    _DICIONARIO_COVERAGE: dict = json.load(f).get("tables", {})


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", s.lower().strip())


# Exact match after normalization, name and synonym alike — the cheap
# deterministic path that answers "quantos habitantes tem SP?" without spending
# an LLM call on it.
_METRIC_BY_NAME = {_norm(k): k for k in _METRICS}
_METRIC_BY_SYNONYM: dict = {}
for _name, _m in _METRICS.items():
    for _syn in _m.get("synonyms", []):
        _METRIC_BY_SYNONYM.setdefault(_norm(_syn), _name)


def _bridge_matches(pattern: str, table_id: str) -> bool:
    """Bridge tables are written for humans: wildcards and `a / b` alternatives."""
    for alt in pattern.split(" / "):
        alt = alt.strip()
        if "." not in alt and "." in pattern:
            alt = pattern.split(".", 1)[0] + "." + alt
        if alt.endswith("*"):
            if table_id.startswith(alt[:-1]):
                return True
        elif alt == table_id:
            return True
    return False


def _bridges_for(table_id: str) -> list:
    """Every documented bridge whose table pattern covers `table_id`."""
    out = []
    # Todo grupo declarado no YAML, não uma lista fixa: um grupo novo (o `pais`
    # foi o primeiro) passa a resolver sem tocar aqui.
    for kind in _BRIDGES["bridges"]:
        for b in _BRIDGES["bridges"].get(kind, []):
            if not _bridge_matches(b["table"], table_id):
                continue
            out.append({
                "kind": kind,
                "concept": b.get("concept"),
                "column": b["column"],
                "join_expr": b.get("join_expr"),
                "note": b.get("format") or b.get("description"),
                "verified": b.get("verified"),
            })
    return out


_duplicated_tables = None
_duplicated_lock = threading.Lock()


def _duplicated() -> set:
    """The tables that return every row twice, read off the generated markdown.

    gera_join_keys.py probes beelink for leftover tmp*.parquet and renders the
    list into join_keys.md. Parsing it back is cheap and keeps this server free
    of its own beelink round-trip at import time.
    """
    global _duplicated_tables
    with _duplicated_lock:
        if _duplicated_tables is not None:
            return _duplicated_tables
        text = JOIN_KEYS_PATH.read_text(encoding="utf-8")
        m = re.search(r"<details><summary>All \d+ affected tables</summary>(.*?)</details>",
                      text, re.DOTALL)
        _duplicated_tables = set(re.findall(r"`([\w.]+)`", m.group(1))) if m else set()
        return _duplicated_tables


# ---------------------------------------------------------------------------
# Search (doc2query) — lazy-loaded, first call downloads the model (~470MB)
# ---------------------------------------------------------------------------
# search_tables used to hold one embedding per table, over text built from its
# column names — measured nearly orthogonal to a real question (cosine 0.08 vs
# 0.39 for equivalent prose; recall@5 1/15 on the single-table golden set).
# This index instead holds one embedding per SYNTHETIC QUESTION the table
# answers (~8/table, scripts/doc2query_lotes.py + doc2query_roda.py against
# scripts/prompts/doc2query.md), so query and index live in the same space.
# See tasks/done/mcp_search_refino.md item 1.

_embedding_model = None
_embedding_model_lock = threading.Lock()
_doc2query_index = None  # {"rows": [{"id","table","text"}], "model": str, "vectors": np.ndarray, "table_rows": {table: [row_idx,...]}}


def _load_doc2query_index():
    global _doc2query_index
    if _doc2query_index is None:
        import numpy as np

        with open(DOC2QUERY_INDEX_PATH, encoding="utf-8") as f:
            meta = json.load(f)
        vectors = np.load(DOC2QUERY_VECTORS_PATH)
        table_rows: dict[str, list[int]] = {}
        for i, row in enumerate(meta["rows"]):
            table_rows.setdefault(row["table"], []).append(i)
        _doc2query_index = {
            "rows": meta["rows"],
            "model": meta["_meta"]["model"],
            "vectors": vectors,
            "table_rows": table_rows,
        }
    return _doc2query_index


def _get_embedding_model():
    global _embedding_model
    with _embedding_model_lock:
        if _embedding_model is None:
            from sentence_transformers import SentenceTransformer

            index = _load_doc2query_index()
            model_name = os.environ.get("MCP_EMBEDDING_MODEL", index["model"])
            _embedding_model = SentenceTransformer(model_name)
    return _embedding_model


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
    # -readonly: this server never writes (enforced above by _check_read_only
    # regardless), but the DuckDB CLI still takes an EXCLUSIVE file lock by
    # default even for a bare SELECT — one read-write connection anywhere
    # blocks every other connection, read-only or not, on the same .duckdb
    # file (https://duckdb.org/docs/stable/connect/concurrency). Multiple
    # concurrent sessions querying the same beelink mirror (this server runs
    # from more than one machine/session at once) hit that lock constantly.
    # Opening read-only lets any number of readers coexist; it only still
    # blocks if some OTHER process opens the file read-write.
    # timeout -k 5 115: the remote command kills itself before the local
    # subprocess.run timeout (120s) fires. Without this, a killed local ssh
    # client does NOT propagate to the remote process — the query keeps
    # running on beelink indefinitely, orphaned, eventually holding a lock
    # nothing can ever release (see tasks/todo.md, confirmed live 2026-08-24).
    # -k 5 sends SIGKILL 5s after the initial SIGTERM if duckdb doesn't exit
    # on its own.
    remote_cmd = (
        f"timeout -k 5 115 {BEELINK_DUCKDB_BIN} -readonly -json {BEELINK_DUCKDB_PATH}"
    )
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

    Three things surface here that the bare column list would hide:
      * `warning` — this table returns every row twice (leftover tmp*.parquet
        next to the real export); same check `resolve_join` runs, but here it
        fires even when you're not joining anything.
      * `dicionario_coverage` — many datasets keep raw numeric/letter codes
        (`v0502`, or `sexo`/`raca_cor` as bare integers) with a chave->valor
        decode sitting in a sibling `dicionario` table; this lists which of
        this table's columns have one.
      * `coded_value_warning` — a stronger version of the above: this table
        has a column (e.g. `sexo`, `raca_cor`) whose code is known to differ
        from the SAME-NAMED column in other datasets, and sometimes even
        across years of this same table. Reusing a code value learned from
        another table's data silently returns wrong or empty results, not an
        error — call explain_column() or check this table's own dicionario
        before filtering on it.
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
    if table in _duplicated():
        result["warning"] = (
            f"`{table}` returns every row twice — a leftover tmp*.parquet sits "
            "next to the real export. Filter with SELECT DISTINCT, and treat "
            "any count()/sum() on it as doubled."
        )
    decodable = _DICIONARIO_COVERAGE.get(table)
    if decodable:
        result["dicionario_coverage"] = {
            "decodable_columns": decodable,
            "how": (
                f"These columns are raw codes. Query "
                f"{dataset}.dicionario WHERE id_tabela = '{table_name}' AND "
                "nome_coluna = '<column>' for the code->label mapping."
            ),
        }
    column_names = {c["name"].lower() for c in columns}
    coded_conflicts = sorted(column_names & set(_CODED_DIFFERENTLY))
    if coded_conflicts:
        result["coded_value_warning"] = [
            {
                "column": col,
                "reason": _CODED_DIFFERENTLY[col]["reason"],
                "how": f"Query {dataset}.dicionario WHERE id_tabela = '{table_name}' "
                       f"AND nome_coluna = '{col}' for THIS table's own mapping — "
                       "do not assume it matches another table's.",
            }
            for col in coded_conflicts
        ]
    return result


@mcp.tool()
def search_tables(query: str, top_k: int = 10, min_similarity: float = SEARCH_THRESHOLD) -> dict:
    """Semantic search over all 832 tables by natural-language question.

    Example: search_tables("gastos de campanha eleitoral") surfaces
    despesas_candidato/receitas_candidato even without exact keyword matches.

    Backed by a doc2query index: ~8 synthetic questions per table, each
    embedded on its own. A table's score is the MAX cosine similarity across
    its own questions, not their average — a table answers many different
    questions, and it's whichever one matches yours that should decide the
    score (averaging was tried and measured worse: it dilutes a table's best
    match with its unrelated ones). `text` is the specific question that
    matched, not a table description — there's no single description in this
    index — so read a hit as "this table can answer: <text>"; call
    describe_table() for the actual columns.

    NOTE: the first call in a session downloads the embedding model
    (~470MB from Hugging Face) and is slow; subsequent calls are fast.
    """
    import numpy as np

    model = _get_embedding_model()
    index = _load_doc2query_index()
    query_vec = np.asarray(model.encode(query), dtype="float32")

    vectors = index["vectors"]
    query_norm = float(np.linalg.norm(query_vec))
    if query_norm == 0:
        sims = np.zeros(len(vectors), dtype="float32")
    else:
        norms = np.linalg.norm(vectors, axis=1)
        sims = (vectors @ query_vec) / (norms * query_norm + 1e-12)

    best_per_table = {}
    for table, row_idxs in index["table_rows"].items():
        table_sims = sims[row_idxs]
        best_local = int(np.argmax(table_sims))
        best_per_table[table] = (float(table_sims[best_local]), row_idxs[best_local])

    ranked = sorted(best_per_table.items(), key=lambda kv: kv[1][0], reverse=True)

    results = [
        {
            "table": table,
            "similarity": round(score, 4),
            "text": index["rows"][row_idx]["text"],
        }
        for table, (score, row_idx) in ranked
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
def resolve_join(table_a: str, table_b: str) -> dict:
    """Return the ON clause that actually joins two tables, ready to paste.

    Both arguments are "dataset.table". This is the executable half of
    get_join_keys: instead of the reference section describing how `codIBGE`
    relates to `id_municipio`, you get
    `lpad(CAST(a.codIBGE AS VARCHAR), 7, '0') = b.id_municipio`.

    Three things come back that a plain column-name match would miss:
      * bridges — the two tables name the same key differently, and the
        expression that converts one to the other has been run on beelink
        (`verified` says what it matched)
      * rejected — columns the two share whose name matches but whose meaning
        does not, so joining on them yields a large, plausible, wrong result
      * warnings — either table returning every row twice from a leftover
        tmp*.parquet, which silently doubles counts and sums
    """
    for tid in (table_a, table_b):
        if "." not in tid:
            return {"error": f"'{tid}' must be in the form 'dataset.table'."}
        ds, _, tbl = tid.partition(".")
        if ds not in _SCHEMA or tbl not in _SCHEMA[ds]:
            return {"error": f"Unknown table '{tid}'.",
                    "suggestions": difflib.get_close_matches(tid, _ALL_TABLE_IDS, n=5, cutoff=0.4)}

    def cols(tid):
        ds, _, tbl = tid.partition(".")
        return {c["name"].lower(): c for c in _SCHEMA[ds][tbl]}

    ca, cb = cols(table_a), cols(table_b)
    joins, rejected = [], []

    # Bridges first: when one exists for a shared column, the naive
    # `a.col = b.col` is the wrong answer, not a second opinion.
    bridged_concepts = set()
    for src, dst, s_alias, d_alias in ((table_a, table_b, "a", "b"),
                                       (table_b, table_a, "b", "a")):
        dst_cols = cols(dst)
        for br in _bridges_for(src):
            concept, expr = br["concept"], br["join_expr"]
            if not concept:
                continue
            # The directory names some keys differently (its UF column is
            # `sigla`), so the concept may live under a local alias.
            local = concept
            if concept not in dst_cols:
                local = next((c for c, k in _CONCEPT_ALIASES.get(dst, {}).items()
                              if k == concept and c in dst_cols), None)
                if local is None:
                    continue
            if not expr:
                rejected.append({
                    "column": br["column"],
                    "reason": f"documented but not resolvable to an expression — {br['note']}",
                })
                continue
            bridged_concepts.add(concept)
            bridged_concepts.add(br["column"].strip('"').lower())
            joins.append({
                "concept": concept,
                "kind": "bridge",
                "on": expr.format(s=s_alias, d=d_alias).replace(
                    f"{d_alias}.{concept}", f"{d_alias}.{local}"),
                "note": br["note"],
                "verified": br["verified"],
            })

    known_keys = set(_CONCEPTS) | set(_parse_join_keys())
    for name in sorted(set(ca) & set(cb)):
        if name in _FALSE_FRIENDS:
            rejected.append({"column": name, "reason": _FALSE_FRIENDS[name]["reason"]})
            continue
        if name in bridged_concepts:
            continue
        if name not in known_keys:
            # Shared name, never documented as a key anywhere in the mirror:
            # `nome`, `bairro`, `complemento`. Listing these as joins is how a
            # model ends up joining two tables on a street address.
            continue
        ta, tb = ca[name].get("type"), cb[name].get("type")
        entry = {
            "concept": name,
            "kind": "direct",
            "on": f"a.{name} = b.{name}",
        }
        if ta and tb and ta != tb:
            entry["on"] = f"CAST(a.{name} AS VARCHAR) = CAST(b.{name} AS VARCHAR)"
            entry["note"] = f"type differs ({ta} vs {tb}) — cast both sides"
        if name in _CONCEPTS:
            entry["canonical_table"] = _CONCEPTS[name].get("canonical_table")
        joins.append(entry)

    warnings = []
    dup = _duplicated()
    for tid, alias in ((table_a, "a"), (table_b, "b")):
        if tid in dup:
            warnings.append(
                f"`{tid}` (alias {alias}) returns every row twice — a leftover "
                "tmp*.parquet sits next to the real export. Join against "
                "SELECT DISTINCT, and treat any count()/sum() on it as doubled."
            )
    if not joins:
        warnings.append(
            "No documented join between these two. Check get_join_keys() for a "
            "third table that bridges them (usually br_bd_diretorios_brasil.municipio)."
        )

    return {
        "table_a": table_a, "table_b": table_b,
        "aliases": {"a": table_a, "b": table_b},
        "joins": joins,
        "rejected": rejected,
        "warnings": warnings,
    }


@mcp.tool()
def explain_column(column: str) -> dict:
    """Say whether a column is a join key, and if not, why not.

    Columns like `valor`, `id` and `numero` appear across dozens of datasets
    under the same name with a different meaning in each. They are deliberately
    absent from get_join_keys(), which used to make them look merely
    undocumented — this tool gives the reason instead of silence.

    A second, more dangerous case (`coded_differently` instead of
    `is_join_key`): the column names the SAME real-world concept everywhere
    (sexo, raca_cor, estado_civil...) but the numeric CODE behind it is not
    shared — RAIS's sexo=1 is masculino, CAGED's sexo=1 is also masculino but
    its sexo=3 is feminino where RAIS uses sexo=2. Never carry a code value
    from one table's filter into another table's query (or even the same
    table in a different year) without checking that table's own
    `{dataset}.dicionario` first — silently returns 0 rows or a wrong
    subset, not an error.
    """
    name = column.lower().strip().strip("`\"")
    if name in _FALSE_FRIENDS:
        e = _FALSE_FRIENDS[name]
        return {"column": name, "is_join_key": False,
                "reason": e["reason"], "seen_in": e["seen_in"]}
    if name in _CODED_DIFFERENTLY:
        e = _CODED_DIFFERENTLY[name]
        return {"column": name, "is_join_key": False, "coded_differently": True,
                "reason": e["reason"], "seen_in": e["seen_in"],
                "how": f"Query `{{dataset}}.dicionario WHERE nome_coluna = '{name}'` "
                       "for the table you're actually using before filtering on it."}
    if name in _CONCEPTS:
        c = _CONCEPTS[name]
        return {"column": name, "is_join_key": True,
                "category": c.get("category"),
                "canonical_table": c.get("canonical_table"),
                "description": c.get("description"),
                "note": "call get_join_keys(column) for the full section and example SQL"}
    index = _parse_join_keys()
    if name in index:
        return {"column": name, "is_join_key": True,
                "note": "auto-detected (shared by 2+ datasets); "
                        "call get_join_keys(column) for the section"}
    return {"column": name, "is_join_key": None,
            "note": "not documented as a join key and not a known false friend — "
                    "it may simply be local to one table."}


@mcp.tool()
def get_metric(name: str) -> dict:
    """Look up a named calculation — its SQL, its grain, and the filters it needs.

    Matching is exact after normalization, against both the metric name and its
    pt-BR synonyms ("populacao", "habitantes", "pop" are one metric). On a miss
    you get the available names rather than a guess.

    `required_filters` are not advisory: those are partition columns, and a
    query that omits them scans the whole table.
    """
    key = _norm(name)
    metric = _METRIC_BY_NAME.get(key) or _METRIC_BY_SYNONYM.get(key)
    if metric is None:
        matches = [n for n in _METRICS if key and key in _norm(n)]
        return {
            "error": f"No metric matching '{name}'.",
            "did_you_mean": matches,
            "available": sorted(_METRICS),
        }
    m = dict(_METRICS[metric])
    m["metric"] = metric
    return m


@mcp.tool()
def list_metrics() -> dict:
    """Every named calculation, with what it measures and its unit."""
    return {
        "count": len(_METRICS),
        "metrics": [
            {"metric": n, "description": m.get("description"),
             "unit": m.get("unit"), "source_table": m.get("source_table")}
            for n, m in sorted(_METRICS.items())
        ],
    }


@mcp.tool()
def rollup(code_column: str, to_level: str) -> dict:
    """How to climb one classification code to a level above it.

    CNAE and CID-10 are prefix codes, so the parent is a substr() of the child
    and needs no join at all — `rollup("subclasse", "divisao")` returns
    `substr(subclasse, 1, 2)`. Levels that are not positional (a CNAE seção is a
    letter, a CID capítulo depends on letter ranges) say so instead of returning
    an expression that would quietly produce wrong groupings.
    """
    src, dst = code_column.lower().strip(), to_level.lower().strip()
    for name, h in _HIERARCHIES.items():
        parents = h.get("parents", {})
        edge = f"{src} -> {dst}"
        if edge in parents:
            p = parents[edge]
            if not p.get("expr"):
                return {"hierarchy": name, "from": src, "to": dst,
                        "expr": None, "table": h.get("table"),
                        "note": p.get("verified"), "caveat": h.get("caveat")}
            return {"hierarchy": name, "from": src, "to": dst,
                    "expr": p["expr"], "kind": h.get("kind"),
                    "verified": p.get("verified"), "caveat": h.get("caveat")}
    edges = [e for h in _HIERARCHIES.values() for e in h.get("parents", {})]
    return {"error": f"No documented rollup from '{src}' to '{dst}'.",
            "available": edges}




@mcp.tool()
def run_sql(sql: str, max_rows: int = 500) -> dict:
    """Run a read-only SQL query against beelink's DuckDB mirror over SSH —
    local Parquet on beelink is the project's only data source (no cloud
    storage), and where newly-scraped datasets land first. This server
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
    - Before hand-writing a per-capita/rate/ratio, call list_metrics() /
      get_metric() first — a wrong unit assumption is easy to make and hard
      to notice. `pib_per_capita` exists exactly because `pib` itself is
      stored in whole BRL, not thousands as its own metrics.yaml comment
      warns is the easy mistake; a query that multiplies by 1,000 "to be
      safe" silently inflates every result 1,000x and still looks plausible
      until checked against a known reference value.
    - Classifying `br_me_cnpj.estabelecimentos` rows by name (e.g. keyword
      matching a business type) does not require joining to `.empresas` —
      `nome_fantasia` already lives on `estabelecimentos`. Joining the full
      `.empresas` table (tens of millions of rows) for this is both
      unnecessary and the single most expensive mistake to make here.
    - Before reporting results: state the expected order of magnitude,
      flag any row that exceeds it, and verify counts two independent ways.
    - SQL dialect is DuckDB, not BigQuery.
    - A handful of views in beelink's basedosdados.duckdb are stale leftovers
      from before the local-parquet migration and still point at a bucket
      that no longer exists; if a query on a view looks wrong, check
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
    # catalog (scraped datasets), or the view is a stale leftover pointing at
    # a bucket that no longer exists. Both are fixed by querying the local
    # parquet directly. The "s3://" marker matches DuckDB's own error text
    # for that dead bucket, not anything this project still depends on.
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


@mcp.tool()
def consultar_painelprecos(
    codigo_item: int,
    tipo_item: str = "material",
    tipo_codigo: str = "codigoItemCatalogo",
    estado: Optional[str] = None,
    max_rows: int = 20,
) -> dict:
    """Look up recent public-purchase prices for one CATMAT/CATSER item via
    ComprasGov's Painel de Preços — a genuine live external lookup (no local
    mirror possible: the API is per-item, `codigo_item` is required, there's
    no "all items" call — ~250k catalog items would mean ~250k calls to
    mirror it).

    `codigo_item` is a CATMAT (material) or CATSER (serviço) catalog code —
    look one up first with `run_sql` against `br_comprasgov_catmatcatser.
    {materiais,servicos}` (columns `codigoItem`/`descricaoItem` or
    `codigoServico`/`nomeServico`).

    Args:
        codigo_item: the catalog code to price-check.
        tipo_item: 'material' or 'servico' — which catalog `codigo_item` is from.
        tipo_codigo: for `tipo_item='material'` only — 'codigoItemCatalogo'
            (specific item) or 'codigoPdm' (padrão descritivo de material,
            broader family of items). Ignored for `tipo_item='servico'`.
        estado: optional 2-letter UF to filter purchases (e.g. "SP").

    Returns each purchase's unit price, quantity, buying entity (UASG),
    município/estado, fornecedor and date, most recent first.
    """
    try:
        codigo = int(codigo_item)
    except (TypeError, ValueError):
        return {"error": f"'{codigo_item}' isn't a valid integer catalog code."}

    if tipo_item not in ("material", "servico"):
        return {"error": f"tipo_item must be 'material' or 'servico', got '{tipo_item}'."}
    if tipo_codigo not in ("codigoItemCatalogo", "codigoPdm"):
        return {"error": f"tipo_codigo must be 'codigoItemCatalogo' or 'codigoPdm', got '{tipo_codigo}'."}

    uf = None
    if estado:
        if not re.fullmatch(r"[A-Za-z]{2}", estado):
            return {"error": f"'{estado}' isn't a valid 2-letter UF."}
        uf = estado.upper()

    tamanho_pagina = max(10, min(max_rows, 500))
    if tipo_item == "material":
        url = (
            "https://dadosabertos.compras.gov.br/modulo-pesquisa-preco/1_consultarMaterial"
            f"?tipo={tipo_codigo}&codigo={codigo}&pagina=1&tamanhoPagina={tamanho_pagina}"
        )
    else:
        url = (
            "https://dadosabertos.compras.gov.br/modulo-pesquisa-preco/3_consultarServico"
            f"?codigoItemCatalogo={codigo}&pagina=1&tamanhoPagina={tamanho_pagina}"
        )
    if uf:
        url += f"&estado={uf}"

    cmd = f"curl -s --max-time 15 '{url}'"
    try:
        proc = subprocess.run(
            ["ssh", BEELINK_HOST, cmd], capture_output=True, timeout=20
        )
    except subprocess.TimeoutExpired:
        return {"error": "Query timed out after 20s (ssh beelink -> compras.gov.br)."}

    if proc.returncode != 0:
        return {"error": proc.stderr.decode("utf-8", errors="replace").strip() or "ssh/curl failed"}

    stdout = proc.stdout.decode("utf-8", errors="replace").strip()
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        return {"error": f"Non-JSON response from Painel de Preços: {stdout[:500]}"}

    if "resultado" not in data:
        return {"error": data.get("message") or f"Unexpected response shape: {stdout[:500]}"}

    rows = data["resultado"]
    return {
        "codigo_item": codigo,
        "tipo_item": tipo_item,
        "compras": rows[:max_rows],
        "truncated": len(rows) > max_rows,
        "total_registros": data.get("totalRegistros"),
    }


if __name__ == "__main__":
    mcp.run()
