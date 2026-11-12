"""O terminal (terminal.py) conta o que exibe num balde comum a todas as abas.

    python3 db/testes/terminal_cota.py

Sem catálogo nem rede: um DuckDB em memória no lugar do catálogo. Confere o teto do `.linhas`,
o balde e que uma entrada com muitos comandos (`SELECT …; SELECT …; …`) para quando ele zera —
a checagem é por comando, não por entrada.
"""

import contextlib
import io
import os
import sys
import tempfile

os.environ.update({"RODADO_LIMITES_DB": os.path.join(tempfile.mkdtemp(), "l.sqlite"),
                   "RODADO_COTA_TERMINAL_DIA": "500", "RODADO_POR_MINUTO": "0"})
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import duckdb  # noqa: E402
from duckdb import sqltypes  # noqa: E402

import rodado_sql  # noqa: E402

base = duckdb.connect()
base.create_function("_mascara_cpf", rodado_sql.mascara_texto, [sqltypes.VARCHAR], sqltypes.VARCHAR,
                     side_effects=False)
base.execute("CREATE SCHEMA br_t; CREATE TABLE br_t.g AS SELECT range AS a FROM range(100000)")
rodado_sql.conecta = lambda *a, **k: base.cursor()

import limites  # noqa: E402
import terminal  # noqa: E402


def main():
    # 50 comandos de 100 linhas numa entrada só: ~5.000 linhas, o balde é de 500
    entrada = " ".join(f"SELECT a FROM br_t.g WHERE a >= {i * 100} LIMIT 100;" for i in range(50))
    tela = io.StringIO()
    with contextlib.redirect_stdout(tela):
        terminal._roda(entrada, 100)
    usado = terminal.LIMITES.usado(limites.BALDE_TERMINAL)[0]
    assert "esgotada" in tela.getvalue(), tela.getvalue()[-500:]
    assert 500 <= usado < 700, usado          # para no comando seguinte ao que zerou o balde
    with contextlib.redirect_stdout(io.StringIO()) as t2:
        terminal._roda("SELECT 1;", 40)
    assert "esgotada" in t2.getvalue()
    print("2/2 ok")


if __name__ == "__main__":
    main()
