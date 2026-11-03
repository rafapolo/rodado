"""Confere a máscara de CPF da saída (rodado_sql.mascara_cpf), sem catálogo nem S3.

    python3 db/testes/mascara_cpf.py
"""

import os
import sys

import duckdb
from duckdb import sqltypes

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import rodado_sql  # noqa: E402

CPF, CPF_F = "52998224725", "529.982.247-25"

con = duckdb.connect(":memory:")
con.create_function("_mascara_cpf", rodado_sql.mascara_texto, [sqltypes.VARCHAR], sqltypes.VARCHAR,
                    side_effects=False)
con.execute("SET enable_external_access=false")
con.execute("SET lock_configuration=true")
cur = con.cursor()

casos = {
    # coluna com outro nome, CPF solto e formatado, dentro de texto (MEI)
    f"SELECT '{CPF}' AS x": [("***982247**",)],
    f"SELECT '{CPF_F}' AS documento": [("***.982.247-**",)],
    f"SELECT 'JOAO DA SILVA {CPF}' AS razao_social": [("JOAO DA SILVA ***982247**",)],
    f"SELECT '{CPF},{CPF_F}' AS dois": [("***982247**,***.982.247-**",)],
    # nomes repetidos: referência por posição
    f"SELECT '{CPF}' AS a, '{CPF}' AS a": [("***982247**", "***982247**")],
    # o que não é CPF passa intacto
    "SELECT '12.345.678/0001-90' a, '12345678000190' b, '11002050506' c, '140.12558008151' d, "
    "'-45097157000.0' e, '111.111.111-11' f, 52998224725 AS valor, '52998224725,50' g, '105794.52000' h, '529.982247-25' i":
        [("12.345.678/0001-90", "12345678000190", "11002050506", "140.12558008151",
          "-45097157000.0", "111.111.111-11", 52998224725, "52998224725,50", "105794.52000", "529.982247-25")],
    # inteiro em coluna cpf, lista, struct
    "SELECT 52998224725 AS cpf_int": [("***982247**",)],
    f"SELECT ['{CPF}', 'x'] AS l": [(["***982247**", "x"],)],
    f"SELECT {{'k': '{CPF}'}} AS s": [("{'k': ***982247**}",)],
    "SELECT NULL::VARCHAR AS n": [(None,)],
}
falhas = 0
for sql, esperado in casos.items():
    obtido = rodado_sql.mascara_cpf(cur.sql(sql)).fetchall()
    if obtido != esperado:
        falhas += 1
        print(f"FALHOU: {sql}\n  esperado {esperado}\n  obtido   {obtido}")
erro = rodado_sql.mascara_texto(f"Conversion Error: Could not convert string '{CPF}x' to INT32")
if CPF in erro:
    falhas += 1
    print("FALHOU: mensagem de erro com CPF:", erro)
print(f"{len(casos) + 1 - falhas}/{len(casos) + 1} ok")
sys.exit(1 if falhas else 0)
