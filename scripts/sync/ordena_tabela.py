#!/usr/bin/env python3
"""Regrava uma tabela do espelho em ordem da chave de busca, sem mudar os nomes de arquivo.

Roda NO beelink (o ressincroniza_bq.py o chama por ssh depois da troca):

    python3 ordena_tabela.py ~/rodado/<dataset>/<tabela> <chave> [desempate]

Ordem global, e cada arquivo existente recebe uma faixa contígua da chave: a busca por um
valor cai num arquivo só, e dentro dele o min/max dos row groups pula o resto. Medido em
2026-10-25 na licitacao_participante lida do S3 pelo db.rodado.xyz: 12-21 s -> 0,4 s.
Os nomes ficam os mesmos, então a view do beelink segue válida e não sobra órfão no COLD.

Só troca depois de conferir contagem, colunas e soma de hash de todas as linhas.
"""
import glob
import math
import os
import shutil
import sys

import duckdb


def ordena(diretorio, chave, desempate=None):
    diretorio = os.path.expanduser(diretorio.rstrip("/"))
    orig = sorted(glob.glob(f"{diretorio}/*.parquet"))
    if not orig:
        sys.exit(f"nenhum parquet em {diretorio}")
    tmp = f"{diretorio}.ordenando"
    # temp_directory próprio: dois processos no mesmo ~/duckdb_tmp colidiram nos arquivos de
    # despejo e os dois morreram com "Could not read enough bytes" (2026-10-25)
    despejo = os.path.expanduser(f"~/duckdb_tmp/ordena_{os.getpid()}")
    con = duckdb.connect(config={"memory_limit": "12GB", "threads": 14, "temp_directory": despejo})
    lista = "[" + ",".join("'" + f.replace("'", "''") + "'" for f in orig) + "]"
    fonte = f"read_parquet({lista}, union_by_name=true, hive_partitioning=false)"
    colunas = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM {fonte}").fetchall()]
    ordem = ", ".join(f'"{c}" NULLS LAST' for c in (chave, desempate) if c and c in colunas)
    if chave not in colunas:
        sys.exit(f"{chave} não é coluna de {diretorio}")
    n = con.execute(f"SELECT count(*) FROM {fonte}").fetchone()[0]
    faixa = max(1, math.ceil(n / len(orig)))
    shutil.rmtree(tmp, ignore_errors=True)
    con.execute(f"""COPY (SELECT * EXCLUDE (__r), __r // {faixa} AS __parte FROM (
                      SELECT *, row_number() OVER (ORDER BY {ordem}) - 1 AS __r FROM {fonte}))
                    TO '{tmp}' (FORMAT parquet, PARTITION_BY (__parte), COMPRESSION zstd, ROW_GROUP_SIZE 122880)""")
    partes = sorted(glob.glob(f"{tmp}/__parte=*/*.parquet"),
                    key=lambda p: int(p.split("__parte=")[1].split("/")[0]))
    nlista = "[" + ",".join(f"'{p}'" for p in partes) + "]"
    # hive_partitioning=false: o caminho __parte=N/ faria o DuckDB acrescentar a coluna __parte
    # às linhas, e a soma de hash não bateria nunca
    marca = "SELECT count(*), sum(hash(t)::HUGEINT) FROM read_parquet({}, union_by_name=true, hive_partitioning=false) t"
    m0, m1 = con.execute(marca.format(lista)).fetchone(), con.execute(marca.format(nlista)).fetchone()
    c1 = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet({nlista}, union_by_name=true, hive_partitioning=false)").fetchall()]
    if m0 != m1 or c1 != colunas or len(partes) > len(orig):
        shutil.rmtree(tmp, ignore_errors=True)
        sys.exit(f"conferência falhou, nada trocado: {m0} x {m1}, {len(partes)} partes para {len(orig)} arquivos")
    # arquivos que sobrarem (tabela com menos linhas que arquivos) ficam com zero linhas e o mesmo schema
    for i, destino in enumerate(orig):
        if i < len(partes):
            os.replace(partes[i], destino)
        else:
            con.execute(f"COPY (SELECT * FROM read_parquet('{destino}') LIMIT 0) TO '{destino}.vazio' (FORMAT parquet)")
            os.replace(f"{destino}.vazio", destino)
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.rmtree(despejo, ignore_errors=True)
    print(f"ordenada por {ordem}: {n} linhas em {len(orig)} arquivos de até {faixa}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    ordena(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
