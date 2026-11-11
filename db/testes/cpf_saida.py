"""Coluna de CPF só sai pura (mascarada) ou contada (rodado_sql._confere_cpf).

    python3 db/testes/cpf_saida.py

Sem catálogo nem S3: um DuckDB em memória com uma tabela de CPF. Cada vazamento achado em
2026-11-11 (e as variações de renomear para depois transformar) tem de ser recusado; o uso
legítimo — filtrar, juntar, agrupar, contar, devolver puro — tem de passar e sair mascarado.
"""

import os
import sys

import duckdb
from duckdb import sqltypes

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import rodado_sql  # noqa: E402

CPF = "52998224725"
con = duckdb.connect(":memory:")
con.create_function("_mascara_cpf", rodado_sql.mascara_texto, [sqltypes.VARCHAR], sqltypes.VARCHAR,
                    side_effects=False)
con.execute(f"""
    CREATE SCHEMA br_t;
    CREATE TABLE br_t.p AS SELECT '{CPF}' AS cpf, '{CPF}' AS cpf_cnpj, 'ANA' AS nome, 2020 AS ano;
    CREATE TABLE br_t.q AS SELECT '{CPF}' AS cpf_favorecido, 10.5 AS valor;
""")

VAZA = [
    "SELECT CAST(cpf AS BIGINT) AS n FROM br_t.p",
    "SELECT cpf::BIGINT + 1 AS x FROM br_t.p",
    "SELECT split(cpf, '') AS s FROM br_t.p",
    "SELECT substr(cpf, 1, 6) a, substr(cpf, 7) b FROM br_t.p",
    "SELECT substr(cpf_cnpj, 1, 8) FROM br_t.p",
    "SELECT reverse(cpf) FROM br_t.p",
    "SELECT list(cpf) FROM br_t.p",
    "SELECT to_json(p) FROM br_t.p",
    "SELECT p::VARCHAR FROM br_t.p",
    "SELECT lag(cpf) OVER () FROM br_t.p",
    "SELECT COLUMNS('c.*')::BIGINT FROM br_t.p",
    "SELECT * REPLACE (cpf::BIGINT AS cpf) FROM br_t.p",
    "SELECT * RENAME (cpf AS x) FROM br_t.p",
    "SELECT cpf AS x FROM br_t.p",
    "SELECT coalesce(cpf, '') AS x FROM br_t.p",
    "SELECT x::BIGINT FROM (SELECT cpf AS x FROM br_t.p)",
    "WITH w(x) AS (SELECT cpf FROM br_t.p) SELECT x::BIGINT FROM w",
    "SELECT x FROM (SELECT cpf FROM br_t.p) z(x)",
    "SELECT n FROM br_t.p AS z(n)",
    "SELECT nome FROM br_t.p UNION ALL SELECT cpf FROM br_t.p",
    "SELECT v FROM (UNPIVOT br_t.p ON cpf INTO NAME k VALUE v)",
    "SELECT (SELECT cpf::BIGINT FROM br_t.p) AS y",
    "SELECT struct_pack(c := cpf) FROM br_t.p",
    "SELECT CASE WHEN length(cpf_cnpj) = 14 THEN substr(cpf_cnpj, 1, 8) END FROM br_t.p",       # formatado tem 14
    "SELECT CASE WHEN length(regexp_replace(cpf_cnpj || '000', '[^0-9]', '', 'g')) = 14 "
    "THEN substr(cpf_cnpj, 1, 8) END FROM br_t.p",
    "SELECT CASE WHEN length(regexp_replace(cpf, '[^0-9]', '', 'g')) = 14 THEN substr(cpf, 1, 8) END FROM br_t.p",
]

PASSA = {
    "SELECT cpf FROM br_t.p": [("***982247**",)],
    "SELECT p.cpf, nome FROM br_t.p AS p WHERE cpf = '52998224725'": [("***982247**", "ANA")],
    "SELECT count(DISTINCT cpf) AS n FROM br_t.p": [(1,)],
    "SELECT approx_count_distinct(cpf_cnpj) AS n FROM br_t.p": [(1,)],
    "SELECT ano, count(*) FROM br_t.p WHERE substr(cpf, 1, 3) = '529' GROUP BY ano": [(2020, 1)],
    "SELECT nome, sum(valor) FROM br_t.p JOIN br_t.q ON cpf = cpf_favorecido GROUP BY nome": [("ANA", 10.5)],
    "SELECT cpf IS NULL AS vazio, cpf IN ('1') AS um FROM br_t.p": [(False, False)],
    "SELECT CASE WHEN length(cpf) = 11 THEN 'pf' ELSE 'pj' END AS tipo FROM br_t.p": [("pf",)],
    "SELECT count(*) FILTER (WHERE cpf_cnpj LIKE '5%') FROM br_t.p": [(1,)],
    "SELECT row_number() OVER (PARTITION BY cpf ORDER BY cpf_cnpj) AS r FROM br_t.p": [(1,)],
    "SELECT max(cpf) AS cpf_max FROM br_t.p": [("***982247**",)],
    "SELECT * FROM br_t.p": [("***982247**", "***982247**", "ANA", 2020)],
    "SELECT * EXCLUDE (cpf_cnpj) FROM br_t.p": [("***982247**", "ANA", 2020)],
    "SELECT cpf AS cpf_titular FROM br_t.p": [("***982247**",)],
    "WITH w AS (SELECT cpf, nome FROM br_t.p) SELECT * FROM w": [("***982247**", "ANA")],
    "SELECT nome FROM br_t.p WHERE cpf IN (SELECT cpf_favorecido FROM br_t.q)": [("ANA",)],
    "SELECT cpf FROM br_t.p UNION ALL SELECT cpf_favorecido FROM br_t.q": [("***982247**",), ("***982247**",)],
    "SELECT nome, ano FROM br_t.p": [("ANA", 2020)],
    # raiz do CNPJ numa coluna mista: só no ramo que garante 14 dígitos (o CPF dá NULL)
    "SELECT CASE WHEN length(regexp_replace(cpf_cnpj, '[^0-9]', '', 'g')) = 14 "
    "THEN substr(regexp_replace(cpf_cnpj, '[^0-9]', '', 'g'), 1, 8) END AS raiz FROM br_t.p": [(None,)],
    # coluna com o nome de uma CTE não é a linha inteira de tabela nenhuma
    "WITH ano AS (SELECT 1 AS x) SELECT ano + 1 AS seguinte FROM br_t.p, ano": [(2021,)],
}


def main():
    falhas = 0
    for sql in VAZA:
        try:
            rodado_sql.separa(con, sql)
            falhas += 1
            print(f"FALHOU (passou e vaza): {sql}")
        except rodado_sql.ConsultaRecusada:
            pass
    for sql, esperado in PASSA.items():
        try:
            (c,) = rodado_sql.separa(con, sql)
            obtido = rodado_sql.mascara_cpf(con.sql(c.query)).fetchall()
            if obtido != esperado:
                falhas += 1
                print(f"FALHOU (resultado {obtido}): {sql}")
        except rodado_sql.ConsultaRecusada as e:
            falhas += 1
            print(f"FALHOU (recusou: {e}): {sql}")
    total = len(VAZA) + len(PASSA)
    print(f"{total - falhas}/{total} ok")
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
