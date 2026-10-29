#!/usr/bin/env python3
"""Regrava uma tabela do espelho em ordem da chave de busca, sem mudar os nomes de arquivo.

Roda NO beelink (o ressincroniza_bq.py o chama por ssh depois da troca):

    python3 ordena_tabela.py ~/rodado/<dataset>/<tabela> <chave> [desempate] [--mb 100] [--por ano] [--mem 12GB] [--threads 14]

Ordem global, e cada arquivo recebe uma faixa contígua da chave: a busca por um valor cai
num arquivo só, e dentro dele o min/max dos row groups pula o resto. Sem --mb, os nomes ficam
os mesmos (a view do beelink segue válida, nenhum órfão no COLD). Com --mb N, junta em
arquivos numerados de ~N MB, numa pasta nova trocada inteira — aí rode
repara_views_beelink.py --apply.
Lido do S3 pelo db.rodado.xyz, cada arquivo custa um rodapé na busca fria: a
licitacao_participante (2026-10-26) levava 36 s desordenada, 16-23 s ordenada em 408
arquivos e 2,3 s em 8 (0,3-0,5 s com cache).

Com --por <coluna> (exige --mb), a ordem é coluna e depois chave: cada valor da coluna (o ano)
ganha os seus arquivos, e dentro deles faixas contíguas da chave. Serve às tabelas consultadas
por ano (SIA, SIH, ANS): ordem global só pela chave mataria o salto do filtro por ano. Cada faixa
sai direto da fonte (WHERE ano = Y AND faixa da chave), relendo o ano uma vez por faixa: o sort do
ano inteiro num temporário, que evitava a releitura, perde a faixa inteira quando erra. E erra: com
o beelink sob pressão de swap (2026-10-27, 13 GB em zram + swap.img), faixas de ~100 MB saíram com
linha trocada (4 em ~25) e uma com o parquet corrompido no disco, no 1.5.5 e no 1.4.5 (segfault);
sem pressão, as mesmas partes releem estáveis. Cada faixa é conferida e regravada.

Só troca depois de conferir contagem, colunas e soma de hash de todas as linhas.

Retomável: o beelink derruba o processo com segfault depois de ~10-20 min de carga a ~92 °C
(SIA, 2026-10-29, duas rodadas; nenhum try pega isso). Os limites das faixas (amostra aleatória)
ficam em limites.json na pasta de trabalho e cada faixa conferida deixa um .ok com o hash; outra
execução com a mesma origem e os mesmos argumentos pula o que já está conferido. Rodar em laço:
    until python3 ordena_tabela.py ...; do sleep 30; done
"""
import glob
import json
import math
import os
import shutil
import sys

import duckdb


def ordena(diretorio, chave, desempate=None, mb=None, por=None, mem="12GB", threads=14):
    diretorio = os.path.expanduser(diretorio.rstrip("/"))
    orig = sorted(glob.glob(f"{diretorio}/*.parquet"))
    if not orig:
        sys.exit(f"nenhum parquet em {diretorio}")
    # fora de ~/rodado: o rsync do COLD (a cada 6 h, sem --delete) levaria as partes para lá e
    # elas ficariam órfãs para sempre. Mesmo disco, então o os.replace segue atômico
    # sem o pid no nome: a execução seguinte acha o trabalho da que morreu
    tmp = os.path.expanduser(f"~/duckdb_tmp/ordenando_{os.path.basename(diretorio)}")
    # temp_directory próprio: dois processos no mesmo ~/duckdb_tmp colidiram nos arquivos de
    # despejo e os dois morreram com "Could not read enough bytes" (2026-10-25)
    despejo = os.path.expanduser(f"~/duckdb_tmp/ordena_{os.getpid()}")
    con = duckdb.connect(config={"memory_limit": mem, "threads": threads, "temp_directory": despejo})
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
    if por and not mb:
        sys.exit("--por exige --mb")
    if por and por not in colunas:
        sys.exit(f"{por} não é coluna de {diretorio}")
    assinatura = [len(orig), sum(map(os.path.getsize, orig)), chave, desempate, mb, por]
    manifesto = f"{tmp}/limites.json"
    estado = {}
    if os.path.exists(manifesto):
        estado = json.load(open(manifesto))
        if estado.get("assinatura") != assinatura:   # origem ou argumentos mudaram: recomeça
            estado = {}
    if not estado:
        shutil.rmtree(tmp, ignore_errors=True)
        os.makedirs(tmp)
        estado = {"assinatura": assinatura, "limites": {}}
    else:
        print(f"retomando {tmp}: {len(glob.glob(f'{tmp}/*.ok'))} faixas já conferidas", flush=True)
    c = f'"{chave}"'
    lit = lambda v: repr(v) if isinstance(v, (int, float)) else "'" + str(v).replace("'", "''") + "'"
    partes = []
    hash_de = lambda origem: con.execute(f"SELECT count(*), sum(hash(t)::HUGEINT) FROM {origem} t").fetchone()

    def temperatura():
        for h in glob.glob("/sys/class/hwmon/hwmon*"):
            try:
                if open(f"{h}/name").read().strip() == "k10temp":
                    return f"{int(open(f'{h}/temp1_input').read()) // 1000}C"
            except OSError:
                pass
        return "?"

    def grava(origem, onde, destino):
        """COPY ordenado conferido contra a origem: o beelink errou conta de vez em quando mesmo
        depois do memtest (2026-10-26: uma linha de hash trocado em ~30 min de carga, ora na
        gravação, ora no próprio hash). Diverge: recalcula os dois lados; segue divergindo: regrava."""
        if os.path.exists(f"{destino}.ok") and os.path.exists(destino):
            return
        for tentativa in range(4):
            # o erro também aparece lendo a origem íntegra ("Payload value bigger than allowed",
            # SIA 2011, 2026-10-29; duas releituras do ano bateram): conta como divergência
            try:
                con.execute(f"""COPY (SELECT * FROM {origem} WHERE {onde} ORDER BY {ordem})
                                TO '{destino}' (FORMAT parquet, COMPRESSION zstd, ROW_GROUP_SIZE 122880)""")
            except duckdb.Error as e:
                a, b = "COPY", str(e)[:80]
                print(f"  {os.path.basename(destino)} divergiu ({a} x {b}), regravando {temperatura()}", flush=True)
                continue
            b = None
            for _ in range(2):
                try:
                    a = hash_de(f"(SELECT * FROM {origem} WHERE {onde})")
                except duckdb.Error as e:
                    a = str(e)[:80]
                    continue
                try:
                    b = hash_de(f"read_parquet('{destino}')")
                except duckdb.Error as e:   # "dictionary offset out of range": gravou corrompido, regravar
                    b = str(e)[:80]
                    break
                if a == b:
                    with open(f"{destino}.ok", "w") as f:
                        f.write(f"{a[0]} {a[1]}\n")
                    return
            print(f"  {os.path.basename(destino)} divergiu ({a} x {b}), regravando {temperatura()}", flush=True)
        # tmp fica: as faixas já conferidas valem para a próxima execução
        sys.exit(f"{destino} divergiu da origem em 4 gravações, nada trocado")

    def faixas(origem, k, filtro="true", aproximado=False):
        """k arquivos com faixas contíguas da chave, lidos de `origem` onde `filtro`."""
        # limites pelos quantis da chave; cada faixa é um COPY com WHERE ... ORDER BY.
        # Nada de PARTITION_BY: no DuckDB 1.5 ele gravou arquivos corrompidos em tabelas grandes
        # ("dictionary offset out of range", soma de hash errada, segfault — 2026-10-26)
        q = ", ".join(str(i / k) for i in range(1, k))
        # amostra basta quando a faixa só equilibra tamanho (approx_quantile não aceita VARCHAR)
        # USING SAMPLE vale antes do WHERE da mesma consulta: amostra fora do filtro, senão sobram
        # só as linhas do ano dentro de 1 milhão tiradas da tabela inteira
        amostra = " USING SAMPLE 1000000 ROWS" if aproximado else ""
        if filtro in estado["limites"]:   # a amostra muda a cada execução: retomar exige os mesmos limites
            limites = estado["limites"][filtro]
        else:
            limites = con.execute(f'SELECT quantile_disc({c}, [{q}]) FROM (SELECT {c} FROM {origem} WHERE ({filtro}) '
                                  f'AND {c} IS NOT NULL){amostra}').fetchone()[0] if k > 1 else []
            limites = sorted(set(v for v in (limites or []) if v is not None))   # chave repetida demais junta faixas
            estado["limites"][filtro] = limites
            with open(f"{manifesto}.novo", "w") as f:
                json.dump(estado, f, default=str)
            os.replace(f"{manifesto}.novo", manifesto)
        for i in range(len(limites) + 1):
            conds = []
            if i > 0:
                conds.append(f"{c} >= {lit(limites[i - 1])}")
            if i < len(limites):
                conds.append(f"{c} < {lit(limites[i])}")
            onde = " AND ".join(conds) or "true"
            if i == len(limites):
                onde = f"({onde}) OR {c} IS NULL"
            destino = f"{tmp}/{len(partes):012d}.parquet"
            grava(origem, f"({filtro}) AND ({onde})", destino)
            partes.append(destino)

    if por:
        p = f'"{por}"'
        tamanho = sum(map(os.path.getsize, orig))
        grupos = con.execute(f"SELECT {p}, count(*) FROM {fonte} GROUP BY 1 ORDER BY 1 NULLS LAST").fetchall()
        for valor, linhas in grupos:
            filtro = f"{p} IS NULL" if valor is None else f"{p} = {lit(valor)}"
            k = max(1, math.ceil(tamanho * linhas / n / (mb * 1e6)))
            faixas(fonte, k, filtro, aproximado=True)
            print(f"{por}={valor}: {linhas} linhas em {k} arquivos {temperatura()}", flush=True)
        saida = [f"{diretorio}/{i:012d}.parquet" for i in range(len(partes))]
    else:
        faixas(fonte, len(saida))
    faixa = math.ceil(n / len(partes))
    nlista = "[" + ",".join(f"'{p}'" for p in partes) + "]"
    marca = "SELECT count(*), sum(hash(t)::HUGEINT) FROM read_parquet({}, union_by_name=true, hive_partitioning=false) t"
    m0, m1 = con.execute(marca.format(lista)).fetchone(), con.execute(marca.format(nlista)).fetchone()
    if m0 != m1:   # uma segunda conta antes de desistir: o erro pode estar no hash, não nos arquivos
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
    mb = por = None
    mem = "12GB"
    if "--mb" in args:
        i = args.index("--mb"); mb = float(args[i + 1]); del args[i:i + 2]
    if "--por" in args:
        i = args.index("--por"); por = args[i + 1]; del args[i:i + 2]
    if "--mem" in args:   # menos que o padrão quando outra coisa pesada divide o beelink
        i = args.index("--mem"); mem = args[i + 1]; del args[i:i + 2]
    threads = 14
    if "--threads" in args:   # menos threads, menos calor (o beelink erra quente)
        i = args.index("--threads"); threads = int(args[i + 1]); del args[i:i + 2]
    if len(args) < 2:
        sys.exit(__doc__)
    ordena(args[0], args[1], args[2] if len(args) > 2 else None, mb, por, mem, threads)
