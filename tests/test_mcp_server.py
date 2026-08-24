"""Tests for mcp_server.py — catalog tools, SQL guard, and the beelink SSH client.

The ssh subprocess and the embedding model are mocked; the real docs/context/
catalog files are used so tests double as a schema-shape regression check.
"""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import mcp_server as m


# ---------------------------------------------------------------------------
# Config — env var defaults and overrides (module-level, so re-import fresh)
# ---------------------------------------------------------------------------

def test_config_defaults():
    assert m.BEELINK_HOST == "beelink"
    assert m.BEELINK_DUCKDB_BIN == "~/bin/duckdb"
    assert m.BEELINK_DUCKDB_PATH == "~/rodado/basedosdados.duckdb"
    assert m.SEARCH_THRESHOLD == 0.35


def test_config_env_overrides(monkeypatch):
    monkeypatch.setenv("MCP_BEELINK_HOST", "other-host")
    monkeypatch.setenv("MCP_BEELINK_DUCKDB_BIN", "/usr/bin/duckdb")
    monkeypatch.setenv("MCP_BEELINK_DUCKDB_PATH", "/data/db.duckdb")
    monkeypatch.setenv("MCP_SEARCH_THRESHOLD", "0.5")

    import importlib
    reloaded = importlib.reload(m)
    try:
        assert reloaded.BEELINK_HOST == "other-host"
        assert reloaded.BEELINK_DUCKDB_BIN == "/usr/bin/duckdb"
        assert reloaded.BEELINK_DUCKDB_PATH == "/data/db.duckdb"
        assert reloaded.SEARCH_THRESHOLD == 0.5
    finally:
        monkeypatch.undo()
        importlib.reload(m)  # restore module-level state for later tests


def test_run_sql_uses_configured_beelink_target():
    with patch("mcp_server.subprocess.run") as run:
        run.return_value = _mock_completed_process(stdout="[]")
        m.run_sql("SELECT 1")
    remote_cmd = run.call_args.args[0][2]
    assert m.BEELINK_DUCKDB_BIN in remote_cmd
    assert m.BEELINK_DUCKDB_PATH in remote_cmd


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
    # The mirrored schema carries only name/type — no column descriptions exist.
    assert all({"name", "type"} <= col.keys() for col in result["columns"])


def test_describe_table_caps_wide_tables():
    """Survey mirrors run to thousands of columns; describe_table must cap them
    so a single call can't flood an LLM's context."""
    wide = max(m._ALL_TABLE_IDS, key=lambda t: len(m._SCHEMA[t.split(".", 1)[0]][t.split(".", 1)[1]]))
    total = len(m._SCHEMA[wide.split(".", 1)[0]][wide.split(".", 1)[1]])
    assert total > m.DESCRIBE_MAX_COLS, "fixture expects at least one wide table"

    result = m.describe_table(wide)
    assert len(result["columns"]) == m.DESCRIBE_MAX_COLS
    assert result["columns_truncated"]["total"] == total
    assert result["columns_truncated"]["shown"] == m.DESCRIBE_MAX_COLS


def test_describe_table_narrow_table_is_not_truncated():
    narrow = min(m._ALL_TABLE_IDS, key=lambda t: len(m._SCHEMA[t.split(".", 1)[0]][t.split(".", 1)[1]]))
    result = m.describe_table(narrow)
    assert "columns_truncated" not in result


def test_cap_rows_passes_small_results_through():
    rows = [{"n": i} for i in range(5)]
    out = m._cap_rows(rows, max_rows=500)
    assert out["rows"] == rows
    assert out["truncated"] is False


def test_cap_rows_caps_by_row_count():
    rows = [{"n": i} for i in range(50)]
    out = m._cap_rows(rows, max_rows=10)
    assert out["returned"] == 10
    assert out["total"] == 50
    assert out["truncated"] is True


def test_cap_rows_caps_wide_rows_by_size():
    """The real hazard: a row-count cap does not bound the payload, because row
    width varies by orders of magnitude across this catalog."""
    # ~4 KB per row: wide enough that 500 rows bust the budget, narrow enough
    # that many still fit — so the cap lands on a real boundary, not on the
    # keep-at-least-one-row floor exercised by the next test.
    wide = [{f"col_{i}": "x" * 100 for i in range(40)} for _ in range(500)]
    out = m._cap_rows(wide, max_rows=500)
    assert out["truncated"] is True
    assert out["returned"] < 500
    assert len(json.dumps(out["rows"], ensure_ascii=False)) <= m.RUN_SQL_MAX_CHARS
    assert "note" in out


def test_cap_rows_returns_column_names_when_one_row_busts_the_budget():
    """Handing back a single 1000-column row would be the blowout this guards
    against (~128k tokens), so return the column names to rewrite the query."""
    monster = [{f"col_{i}": "x" * 500 for i in range(1000)}]
    out = m._cap_rows(monster, max_rows=500)
    assert out["rows"] == []
    assert out["columns_total"] == 1000
    assert len(out["columns"]) == m.DESCRIBE_MAX_COLS
    assert len(json.dumps(out, ensure_ascii=False)) < m.RUN_SQL_MAX_CHARS


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
# run_sql — SSH-to-beelink client behavior (mocked, no real network calls)
# ---------------------------------------------------------------------------

_BANNER = "\x1b[90m-- Loading resources from /home/polo/.duckdbrc\n\x1b[00m"


def _mock_completed_process(returncode=0, stdout="", stderr=_BANNER):
    proc = MagicMock()
    proc.returncode = returncode
    proc.stdout = stdout.encode("utf-8")
    proc.stderr = stderr.encode("utf-8")
    return proc


def test_run_sql_rejects_before_any_ssh_call():
    with patch("mcp_server.subprocess.run") as run:
        result = m.run_sql("DROP TABLE foo")
    assert "error" in result
    run.assert_not_called()


def test_run_sql_success():
    with patch("mcp_server.subprocess.run") as run:
        run.return_value = _mock_completed_process(stdout='[{"n":42}]')
        result = m.run_sql("SELECT 42 AS n")
    assert result == {"rows": [{"n": 42}], "truncated": False}
    args = run.call_args.args[0]
    assert args[0] == "ssh"
    assert args[1] == m.BEELINK_HOST
    assert run.call_args.kwargs["input"] == b"SET enable_progress_bar=false;\nSELECT 42 AS n"


def test_run_sql_empty_result():
    with patch("mcp_server.subprocess.run") as run:
        run.return_value = _mock_completed_process(stdout="")
        result = m.run_sql("SELECT 1 WHERE FALSE")
    assert result == {"rows": [], "truncated": False}


def test_run_sql_surfaces_sql_error_and_strips_banner():
    stderr = _BANNER + "Catalog Error: Table with name foo does not exist!"
    with patch("mcp_server.subprocess.run") as run:
        run.return_value = _mock_completed_process(returncode=1, stderr=stderr)
        result = m.run_sql("SELECT nope FROM foo")
    assert result == {"error": "Catalog Error: Table with name foo does not exist!"}


def test_run_sql_surfaces_timeout():
    with patch("mcp_server.subprocess.run", side_effect=m.subprocess.TimeoutExpired("ssh", 120)):
        result = m.run_sql("SELECT 1")
    assert "error" in result
    assert "timed out" in result["error"].lower()


def test_run_sql_truncates_rows():
    rows = [{"n": i} for i in range(10)]
    with patch("mcp_server.subprocess.run") as run:
        run.return_value = _mock_completed_process(stdout=json.dumps(rows))
        result = m.run_sql("SELECT n FROM x", max_rows=3)
    assert result["truncated"] is True
    assert result["returned"] == 3
    assert result["total"] == 10
    assert len(result["rows"]) == 3


# ---------------------------------------------------------------------------
# search_tables — doc2query index, embedding model mocked, no download/network
# ---------------------------------------------------------------------------

def _fake_doc2query_index():
    import numpy as np

    rows = [
        {"id": "ds.a.q1", "table": "ds.a", "text": "quem foram os candidatos eleitorais"},
        {"id": "ds.a.q2", "table": "ds.a", "text": "pergunta completamente irrelevante"},
        {"id": "ds.b.q1", "table": "ds.b", "text": "óbitos por município"},
    ]
    # ds.a's best question is a perfect match (sim 1.0); its other question is
    # a perfect mismatch (sim -1.0). ds.b's only question is a close-but-not-
    # perfect match (sim ~0.994). Mean-pooling ds.a would give it (1.0-1.0)/2
    # = 0.0, losing to ds.b — so a top result of ds.a proves MAX aggregation,
    # not mean, is what's running.
    vectors = np.array([[1.0, 0.0], [-1.0, 0.0], [0.9, 0.1]], dtype="float32")
    table_rows = {"ds.a": [0, 1], "ds.b": [2]}
    return {"rows": rows, "model": "fake-model", "vectors": vectors, "table_rows": table_rows}


def test_search_tables_scores_by_max_not_mean(monkeypatch):
    import numpy as np

    monkeypatch.setattr(m, "_doc2query_index", _fake_doc2query_index())

    fake_model = MagicMock()
    fake_model.encode.return_value = np.array([1.0, 0.0], dtype="float32")
    monkeypatch.setattr(m, "_embedding_model", fake_model)

    result = m.search_tables("candidatos", top_k=5, min_similarity=-1.0)
    assert result["results"][0]["table"] == "ds.a"
    assert result["results"][0]["similarity"] == 1.0
    assert result["results"][0]["text"] == "quem foram os candidatos eleitorais"
    assert result["results"][1]["table"] == "ds.b"


def test_search_tables_respects_min_similarity(monkeypatch):
    import numpy as np

    monkeypatch.setattr(m, "_doc2query_index", _fake_doc2query_index())

    fake_model = MagicMock()
    fake_model.encode.return_value = np.array([1.0, 0.0], dtype="float32")
    monkeypatch.setattr(m, "_embedding_model", fake_model)

    result = m.search_tables("candidatos", top_k=5, min_similarity=0.995)
    assert [r["table"] for r in result["results"]] == ["ds.a"]


# ---------------------------------------------------------------------------
# consultar_cnpj / consultar_cep — friendly per-theme tools
# ---------------------------------------------------------------------------

def test_only_digits():
    assert m._only_digits("09.944.413/0001-00") == "09944413000100"
    assert m._only_digits("") == ""
    assert m._only_digits(None) == ""


def test_consultar_cnpj_invalid_length():
    result = m.consultar_cnpj("123")
    assert "error" in result
    assert "8 or 14 digits" in result["error"]


def test_consultar_cnpj_not_found():
    with patch("mcp_server.subprocess.run") as run:
        run.return_value = _mock_completed_process(stdout="[]")
        result = m.consultar_cnpj("09944413")
    assert result == {"error": "No company found for cnpj_basico '09944413'."}


def test_consultar_cnpj_success():
    responses = [
        '[{"cnpj_basico":"09944413","razao_social":"ARSENAL DE GUERRA DO RIO"}]',
        '[{"cnpj":"09944413000100","identificador_matriz_filial":"1"}]',
        '[{"nome":"FULANO DE TAL","documento":"***123456**"}]',
    ]
    with patch("mcp_server.subprocess.run") as run:
        run.side_effect = [_mock_completed_process(stdout=r) for r in responses]
        result = m.consultar_cnpj("09.944.413/0001-00")
    assert result["cnpj_basico"] == "09944413"
    assert result["empresa"]["razao_social"] == "ARSENAL DE GUERRA DO RIO"
    assert len(result["estabelecimentos"]) == 1
    assert len(result["socios"]) == 1
    assert run.call_count == 3


def test_consultar_cep_invalid_length():
    result = m.consultar_cep("123")
    assert "error" in result
    assert "8 digits" in result["error"]


def test_consultar_cep_success():
    payload = json.dumps({"cep": "01310-100", "logradouro": "Avenida Paulista", "uf": "SP"})
    with patch("mcp_server.subprocess.run") as run:
        run.return_value = _mock_completed_process(stdout=payload)
        result = m.consultar_cep("01310-100")
    assert result["logradouro"] == "Avenida Paulista"
    args = run.call_args.args[0]
    assert args[0] == "ssh"
    assert args[1] == m.BEELINK_HOST
    assert "viacep.com.br/ws/01310100/json" in args[2]


def test_consultar_cep_not_found():
    with patch("mcp_server.subprocess.run") as run:
        run.return_value = _mock_completed_process(stdout='{"erro": true}')
        result = m.consultar_cep("00000000")
    assert result == {"error": "CEP '00000000' not found."}


# ---------------------------------------------------------------------------
# bridges.yaml — resolve_join / explain_column
# ---------------------------------------------------------------------------

def test_bridges_yaml_shapes_match_what_the_loader_expects():
    assert set(m._BRIDGES) >= {"categories", "concepts", "bridges", "false_friends"}
    for kind in ("municipio", "uf", "identity"):
        for b in m._BRIDGES["bridges"][kind]:
            assert "table" in b and "column" in b
            if b.get("join_expr"):
                assert "{s}" in b["join_expr"] and "{d}" in b["join_expr"]
                assert b.get("concept"), f"{b['table']} has join_expr but no concept"


def test_resolve_join_prefers_the_bridge_over_the_naive_equality():
    r = m.resolve_join("br_anp_combustiveis.precos", "br_me_cnpj.estabelecimentos")
    cnpj = [j for j in r["joins"] if j["concept"] == "cnpj"]
    assert len(cnpj) == 1
    assert cnpj[0]["kind"] == "bridge"
    # the whole point: ANP stores cnpj unpadded, so a.cnpj = b.cnpj is wrong
    assert "lpad" in cnpj[0]["on"]
    assert "a.cnpj = b.cnpj" not in [j["on"] for j in r["joins"]]


def test_resolve_join_rejects_false_friends_with_a_reason():
    r = m.resolve_join("br_anp_combustiveis.precos", "br_me_cnpj.estabelecimentos")
    rejected = {x["column"]: x["reason"] for x in r["rejected"]}
    assert "numero" in rejected
    assert rejected["numero"]
    assert "numero" not in [j["concept"] for j in r["joins"]]


def test_resolve_join_skips_shared_columns_that_are_not_documented_keys():
    r = m.resolve_join("br_anp_combustiveis.precos", "br_me_cnpj.estabelecimentos")
    concepts = [j["concept"] for j in r["joins"]]
    for noise in ("bairro", "complemento", "nome"):
        assert noise not in concepts


def test_resolve_join_rewrites_the_concept_to_its_local_alias():
    # the UF directory calls the key `sigla`, not `sigla_uf`
    r = m.resolve_join("br_mjsp_sisdepen.populacao_carceraria", "br_bd_diretorios_brasil.uf")
    on = [j["on"] for j in r["joins"] if j["concept"] == "sigla_uf"]
    assert on and on[0].endswith("b.sigla")
    assert "b.sigla_uf" not in on[0]


def test_resolve_join_no_longer_warns_about_duplicated_tables():
    """`br_tce_pi.prefeituras` era duplicada por sobra de sync e o join vinha com
    aviso de "returns every row twice". As 80 sobras de `tmp*.parquet` do sync
    abortado de 2026-07-05 foram triadas e removidas em 2026-08-23, então o aviso
    deve ter sumido — se voltar, alguma coisa reintroduziu shard duplicado."""
    r = m.resolve_join("br_tce_pi.prefeituras", "br_bd_diretorios_brasil.municipio")
    assert not any("twice" in w for w in r["warnings"]), r["warnings"]


def test_resolve_join_unknown_table_returns_suggestions():
    r = m.resolve_join("br_tce_pi.prefeitura", "br_bd_diretorios_brasil.municipio")
    assert "error" in r and "suggestions" in r


def test_explain_column_gives_the_reason_a_false_friend_is_not_a_key():
    r = m.explain_column("valor")
    assert r["is_join_key"] is False
    assert r["reason"] and r["seen_in"]


def test_explain_column_recognises_a_curated_key():
    r = m.explain_column("id_municipio")
    assert r["is_join_key"] is True
    assert r["canonical_table"] == "br_bd_diretorios_brasil.municipio"


# ---------------------------------------------------------------------------
# metrics.yaml / hierarchies.yaml
# ---------------------------------------------------------------------------

def test_every_metric_carries_what_a_query_needs():
    assert m._METRICS
    for name, metric in m._METRICS.items():
        for field in ("description", "unit", "grain", "source_table",
                      "expression", "required_filters", "synonyms", "verified"):
            assert metric.get(field), f"{name} is missing {field}"


def test_metric_source_tables_exist_in_the_catalog():
    for name, metric in m._METRICS.items():
        ds, _, tbl = metric["source_table"].partition(".")
        assert tbl in m._SCHEMA.get(ds, {}), f"{name} points at a table that is gone"


def test_get_metric_matches_on_a_synonym():
    a, b = m.get_metric("habitantes"), m.get_metric("populacao")
    assert a["metric"] == b["metric"] == "populacao"
    assert a["expression"] == "SUM(populacao)"


def test_get_metric_requires_the_partition_filter():
    assert m.get_metric("saldo caged")["required_filters"] == ["ano"]


def test_get_metric_miss_lists_what_exists():
    r = m.get_metric("faturamento")
    assert "error" in r and r["available"]


def test_synonyms_are_unique_across_metrics():
    seen = {}
    for name, metric in m._METRICS.items():
        for syn in metric["synonyms"]:
            key = m._norm(syn)
            assert key not in seen, f"'{syn}' is claimed by {seen.get(key)} and {name}"
            seen[key] = name


def test_rollup_returns_a_positional_parent():
    r = m.rollup("subclasse", "divisao")
    assert r["expr"] == "substr(subclasse, 1, 2)"
    assert r["kind"] == "positional"


def test_rollup_refuses_to_invent_a_non_positional_parent():
    # a CID chapter depends on letter ranges — substr would group wrongly
    r = m.rollup("categoria", "capitulo")
    assert r["expr"] is None
    assert r["note"]


def test_rollup_unknown_edge_lists_the_documented_ones():
    r = m.rollup("subclasse", "planeta")
    assert "error" in r and r["available"]
