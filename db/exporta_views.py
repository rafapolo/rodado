#!/usr/bin/env python3
"""Exporta o SQL das views e macros do beelink para o catálogo S3 do db.rodado.xyz.

Roda no beelink, no começo de ~/scripts/s3_sync_rodado.sh: grava
~/rodado/_db/views.json, que a própria sincronização leva para
s3://baseldosdados/_db/views.json junto com os parquet que as views citam. O
catalogo.py do container no finland lê esse arquivo e monta o catálogo com os
caminhos trocados para o bucket. `_db` começa com `_`: gera_schemas.py e
build_metadata_catalog.py tratam como diretório de trabalho, não como dataset.

    python3 ~/rodado_db/exporta_views.py
"""
import json
import os

import duckdb

HOME = os.path.expanduser("~")
BANCO = f"{HOME}/rodado/basedosdados.duckdb"
SAIDA = f"{HOME}/rodado/_db/views.json"


def main():
    con = duckdb.connect(BANCO, read_only=True)
    try:
        views = [{"dataset": d, "tabela": t, "sql": s} for d, t, s in con.execute(
            "SELECT schema_name, view_name, sql FROM duckdb_views() WHERE NOT internal ORDER BY ALL").fetchall()]
        # as macros do banco (fx, sitio...) entram antes das views; duckdb_functions() guarda
        # o corpo, não o CREATE, então ele é refeito aqui
        macros = [f"CREATE MACRO {nome}({', '.join(params)}) AS {'TABLE ' if tipo == 'table_macro' else ''}{corpo}"
                  for nome, tipo, params, corpo in con.execute(
                      "SELECT function_name, function_type, parameters, macro_definition FROM duckdb_functions() "
                      "WHERE NOT internal AND function_type IN ('macro', 'table_macro') ORDER BY ALL").fetchall()]
    finally:
        con.close()
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    tmp = SAIDA + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"views": views, "macros": macros}, f, ensure_ascii=False)
    os.replace(tmp, SAIDA)
    print(f"{len(views)} views e {len(macros)} macros -> {SAIDA}")


if __name__ == "__main__":
    main()
