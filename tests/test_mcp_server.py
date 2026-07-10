"""Tests for mcp_server.py — catalog tools, SQL guard, and HTTP client.

Network calls and the embedding model are mocked; the real docs/context/
catalog files are used so tests double as a schema-shape regression check.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import mcp_server as m


# ---------------------------------------------------------------------------
# Catalog tools (list_datasets, list_tables, describe_table)
# ---------------------------------------------------------------------------

def test_list_datasets_matches_schema():
    result = m.list_datasets()
    assert result["count"] == len(m._SCHEMA)
    assert result["count"] > 0
    assert len(result["datasets"]) == result["count"]
    assert all("dataset" in d and "table_count" in d for d in result["datasets"])


def test_list_tables_known_dataset():
    dataset = next(iter(m._SCHEMA))
    result = m.list_tables(dataset)
    assert result["dataset"] == dataset
    assert result["tables"] == sorted(m._SCHEMA[dataset].keys())


def test_list_tables_unknown_dataset_returns_suggestions():
    result = m.list_tables("br_tse_eleicoesXYZ")
    assert "error" in result
    assert "suggestions" in result


def test_describe_table_known_table():
    table_id = m._ALL_TABLE_IDS[0]
    result = m.describe_table(table_id)
    assert result["table"] == table_id
    assert isinstance(result["columns"], list)
    assert all({"name", "type", "description"} <= col.keys() for col in result["columns"])


def test_describe_table_missing_dot():
    result = m.describe_table("no_dot_here")
    assert "error" in result


def test_describe_table_unknown_returns_suggestions():
    result = m.describe_table("br_tse_eleicoes.nao_existe_tabela")
    assert "error" in result
    assert "suggestions" in result


# ---------------------------------------------------------------------------
# get_join_keys
# ---------------------------------------------------------------------------

def test_get_join_keys_no_arg_lists_all():
    result = m.get_join_keys()
    assert "columns" in result
    assert len(result["columns"]) > 0


def test_get_join_keys_known_column():
    column = next(iter(m._parse_join_keys().values()))["column"]
    result = m.get_join_keys(column)
    assert result["column"] == column
    assert "section" in result


def test_get_join_keys_unknown_column():
    result = m.get_join_keys("coluna_que_nao_existe_zzz")
    assert "error" in result
    assert "available_keys" in result


# ---------------------------------------------------------------------------
# SQL read-only guard
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("sql", [
    "SELECT 1",
    "select * from br_tse_eleicoes.candidatos limit 1",
    "  WITH x AS (SELECT 1) SELECT * FROM x",
    "SELECT 1;",
    "SELECT 1 -- trailing comment",
    "/* leading comment */ SELECT 1",
])
def test_check_read_only_allows_select_with(sql):
    assert m._check_read_only(sql) is None


@pytest.mark.parametrize("sql", [
    "",
    "   ",
    "DROP TABLE foo",
    "INSERT INTO foo VALUES (1)",
    "SELECT 1; SELECT 2",
    "SELECT 1; DROP TABLE foo",
    "ATTACH 'x.db'",
    "PRAGMA table_info('x')",
    "COPY (SELECT 1) TO 'out.csv'",
])
def test_check_read_only_rejects(sql):
    assert m._check_read_only(sql) is not None


def test_check_read_only_rejects_keyword_in_second_statement_via_semicolon():
    error = m._check_read_only("SELECT 1; DELETE FROM foo")
    assert error is not None
    assert "statement" in error.lower()


def test_strip_sql_comments():
    sql = "SELECT 1 -- comment\n/* block */ FROM x"
    stripped = m._strip_sql_comments(sql)
    assert "comment" not in stripped
    assert "block" not in stripped


# ---------------------------------------------------------------------------
# run_sql — HTTP client behavior (mocked, no real network calls)
# ---------------------------------------------------------------------------

def _mock_response(status_code=200, json_data=None, text=""):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    if json_data is not None:
        resp.json.return_value = json_data
    else:
        resp.json.side_effect = ValueError("no json")
    return resp


def test_run_sql_rejects_before_any_network_call():
    with patch("mcp_server.requests.get") as get, patch("mcp_server.requests.post") as post:
        result = m.run_sql("DROP TABLE foo")
    assert "error" in result
    get.assert_not_called()
    post.assert_not_called()


def test_run_sql_requires_password(monkeypatch):
    monkeypatch.delenv("BASIC_AUTH_PASSWORD", raising=False)
    result = m.run_sql("SELECT 1")
    assert "error" in result
    assert "BASIC_AUTH_PASSWORD" in result["error"]


def test_run_sql_success(monkeypatch):
    monkeypatch.setenv("BASIC_AUTH_PASSWORD", "secret")
    with patch("mcp_server.requests.post") as post:
        post.return_value = _mock_response(200, [{"n": 42}])
        result = m.run_sql("SELECT 42 AS n", method="post")
    assert result == {"rows": [{"n": 42}], "truncated": False}
    assert post.call_args.kwargs["headers"]["X-Password"] == "secret"


def test_run_sql_uses_get_method(monkeypatch):
    monkeypatch.setenv("BASIC_AUTH_PASSWORD", "secret")
    with patch("mcp_server.requests.get") as get:
        get.return_value = _mock_response(200, [{"n": 1}])
        result = m.run_sql("SELECT 1 AS n", method="get")
    assert result == {"rows": [{"n": 1}], "truncated": False}
    get.assert_called_once()


def test_run_sql_surfaces_sql_error_despite_http_200(monkeypatch):
    """auth.py returns HTTP 200 even on SQL errors — must check the body."""
    monkeypatch.setenv("BASIC_AUTH_PASSWORD", "secret")
    with patch("mcp_server.requests.post") as post:
        post.return_value = _mock_response(200, {"error": "Binder Error: no such column"})
        result = m.run_sql("SELECT nope FROM foo")
    assert result == {"error": "Binder Error: no such column"}


def test_run_sql_surfaces_http_error(monkeypatch):
    monkeypatch.setenv("BASIC_AUTH_PASSWORD", "secret")
    with patch("mcp_server.requests.post") as post:
        post.return_value = _mock_response(401, text="Unauthorized")
        result = m.run_sql("SELECT 1")
    assert "error" in result
    assert "401" in result["error"]


def test_run_sql_truncates_rows(monkeypatch):
    monkeypatch.setenv("BASIC_AUTH_PASSWORD", "secret")
    rows = [{"n": i} for i in range(10)]
    with patch("mcp_server.requests.post") as post:
        post.return_value = _mock_response(200, rows)
        result = m.run_sql("SELECT n FROM x", max_rows=3)
    assert result["truncated"] is True
    assert result["returned"] == 3
    assert result["total"] == 10
    assert len(result["rows"]) == 3


# ---------------------------------------------------------------------------
# search_tables — embedding model mocked, no download/network
# ---------------------------------------------------------------------------

def test_search_tables_ranks_by_cosine_similarity(monkeypatch):
    fake_data = {
        "model": "all-MiniLM-L6-v2",
        "tables": [
            {"id": "ds.a", "text": "candidatos eleitorais", "embedding": [1.0, 0.0]},
            {"id": "ds.b", "text": "óbitos por município", "embedding": [0.0, 1.0]},
        ],
    }
    monkeypatch.setattr(m, "_table_embeddings", fake_data)

    fake_model = MagicMock()
    fake_model.encode.return_value = MagicMock(tolist=lambda: [1.0, 0.0])
    monkeypatch.setattr(m, "_embedding_model", fake_model)

    result = m.search_tables("candidatos", top_k=5, min_similarity=0.0)
    assert result["results"][0]["table"] == "ds.a"
    assert result["results"][0]["similarity"] == 1.0


def test_cosine_similarity_orthogonal_and_identical():
    assert m._cosine_similarity([1, 0], [0, 1]) == 0.0
    assert m._cosine_similarity([1, 0], [1, 0]) == 1.0
    assert m._cosine_similarity([0, 0], [1, 0]) == 0.0
