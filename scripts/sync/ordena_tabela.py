#!/usr/bin/env python3
"""Regrava uma tabela do espelho em ordem da chave de busca, sem mudar os nomes de arquivo.

Roda NO beelink (o ressincroniza_bq.py o chama por ssh depois da troca):

    python3 ordena_tabela.py ~/rodado/<dataset>/<tabela> <chave> [desempate] [--mb 100]

Ordem global, e cada arquivo recebe uma faixa contígua da chave: a busca por um valor cai
num arquivo só, e dentro dele o min/max dos row groups pula o resto. Sem --mb, os nomes ficam
os mesmos (a view do beelink segue válida, nenhum órfão no COLD). Com --mb N, junta em
arquivos numerados de ~N MB, numa pasta nova trocada inteira — aí rode
repara_views_beelink.py --apply.
Lido do S3 pelo db.rodado.xyz, cada arquivo custa um rodapé na busca fria: a
licitacao_participante (2026-10-26) levava 36 s desordenada, 16-23 s ordenada em 408
arquivos e 2,3 s em 8 (0,3-0,5 s com cache).

Só troca depois de conferir contagem, colunas e soma de hash de todas as linhas.
"""
import glob
import math
import os
import shutil
import sys

import duckdb


def ordena(diretorio, chave, desempate=None, mb=None):
    diretorio = os.path.expanduser(diretorio.rstrip("/"))
    orig = sorted(glob.glob(f"{diretorio}/*.parquet"))
    if not orig:
        sys.exit(f"nenhum parquet em {diretorio}")
    # fora de ~/rodado: o rsync do COLD (a cada 6 h, sem --delete) levaria as partes para lá e
    # elas ficariam órfãs para sempre. Mesmo disco, então o os.replace segue atômico
    tmp = os.path.expanduser(f"~/duckdb_tmp/ordenando_{os.path.basename(diretorio)}_{os.getpid()}")
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
    saida = orig
    if mb:   # arquivos de ~mb MB, numerados: AC.parquet com NIS do país inteiro seria um nome mentiroso
        k = max(1, math.ceil(sum(map(os.path.getsize, orig)) / (mb * 1e6)))
        saida = [f"{diretorio}/{i:012d}.parquet" for i in range(k)]
    faixa = max(1, math.ceil(n / len(saida)))
    shutil.rmtree(tmp, ignore_errors=True)
    con.execute(f"""COPY (SELECT * EXCLUDE (__r), __r // {faixa} AS __parte FROM (
                      SELECT *, row_number() OVER (ORDER BY {ordem}) - 1 AS __r FROM {fonte}))
                    TO '{tmp}' (FORMAT parquet, PARTITION_BY (__parte), COMPRESSION zstd, ROW_GROUP_SIZE 122880)""")
    # o PARTITION_BY acerta o conteúdo de cada faixa, mas não a ordem dentro dela, e grava mais
    # de um arquivo quando ela é grande (491 para 408 na licitacao_participante): cada faixa é
    # regravada num arquivo só, ordenado, para os row groups não se sobreporem
    partes = []
    for d in sorted(glob.glob(f"{tmp}/__parte=*"), key=lambda d: int(d.rsplit("=", 1)[1])):
        arqs = sorted(glob.glob(f"{d}/*.parquet"))
        junto = f"{d}.parquet"
        con.execute(f"""COPY (SELECT * FROM read_parquet({[*arqs]}, hive_partitioning=false) ORDER BY {ordem})
                        TO '{junto}' (FORMAT parquet, COMPRESSION zstd, ROW_GROUP_SIZE 122880)""")
        partes.append(junto)
    nlista = "[" + ",".join(f"'{p}'" for p in partes) + "]"
    # hive_partitioning=false: o caminho __parte=N/ faria o DuckDB acrescentar a coluna __parte
    # às linhas, e a soma de hash não bateria nunca
    marca = "SELECT count(*), sum(hash(t)::HUGEINT) FROM read_parquet({}, union_by_name=true, hive_partitioning=false) t"
    m0, m1 = con.execute(marca.format(lista)).fetchone(), con.execute(marca.format(nlista)).fetchone()
    c1 = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet({nlista}, union_by_name=true, hive_partitioning=false)").fetchall()]
    if m0 != m1 or c1 != colunas or len(partes) > len(saida):
        shutil.rmtree(tmp, ignore_errors=True)
        sys.exit(f"conferência falhou, nada trocado: {m0} x {m1}, {len(partes)} partes para {len(saida)} arquivos")
    if mb:
        # pasta nova montada ao lado e trocada inteira: os nomes mudam, e nenhum leitor vê metade
        nova, velha = f"{tmp}_final", f"{tmp}_velha"
        os.makedirs(nova)
        for i, p in enumerate(partes):
            os.replace(p, f"{nova}/{i:012d}.parquet")
        os.chmod(nova, os.stat(diretorio).st_mode & 0o7777)
        for f in glob.glob(f"{nova}/*.parquet"):
            os.chmod(f, 0o664)
        os.rename(diretorio, velha)
        os.rename(nova, diretorio)
        shutil.rmtree(velha)
        saida = partes
    else:
        # arquivos que sobrarem (tabela com menos linhas que arquivos) ficam com zero linhas e o mesmo schema
        for i, destino in enumerate(saida):
            if i < len(partes):
                os.replace(partes[i], destino)
            else:
                con.execute(f"COPY (SELECT * FROM read_parquet('{destino}') LIMIT 0) TO '{destino}.vazio' (FORMAT parquet)")
                os.replace(f"{destino}.vazio", destino)
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.rmtree(despejo, ignore_errors=True)
    print(f"ordenada por {ordem}: {n} linhas em {len(saida)} arquivos de até {faixa}"
          + (f" (eram {len(orig)}, nomes novos: rode repara_views_beelink.py --apply)" if mb else ""))


if __name__ == "__main__":
    args = sys.argv[1:]
    mb = None
    if "--mb" in args:
        i = args.index("--mb"); mb = float(args[i + 1]); del args[i:i + 2]
    if len(args) < 2:
        sys.exit(__doc__)
    ordena(args[0], args[1], args[2] if len(args) > 2 else None, mb)
