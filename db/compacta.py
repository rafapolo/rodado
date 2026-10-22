#!/usr/bin/env python3
"""Recomprime em zstd 19 os parquet do bucket s3://baseldosdados, no finland, sem o beelink.

O beelink grava em zstd 3 a 9 (escrever rápido importa lá, e o disco sobra). O db.rodado.xyz
paga cada byte que baixa do bucket, então a cópia do bucket (e a do SSD) vai no nível 19:
~20% menos no espelho, leitura igual (medido em 2026-10-22, ver
tasks/plans/normalizar_e_reordenar.md). O nível 22 dá o mesmo tamanho que o 19 no DuckDB.

Para cada objeto: baixa, regrava (mesma ordem de linhas), confere linhas + soma de hash de
todas as linhas + tipos das colunas, confere que o objeto não mudou no bucket enquanto isso,
e sobe no mesmo nome. Arquivo com metadado próprio (GeoParquet, pandas...) fica como está.
A cópia do SSD (docker volume rodado-db-dados) é trocada pela comprimida na hora.

O progresso fica em s3://baseldosdados/_db/compactados.json ({arquivo: {orig, z, ...}}): o
`s3_sync_check.py` do beelink o lê e trata como em dia o arquivo que tem o tamanho original
no beelink e o comprimido no bucket. Arquivo que o beelink sobe de novo (mudou lá) volta a
ter o tamanho original no bucket e é comprimido de novo na rodada seguinte.

Roda pelo cron do finland, de hora em hora, sob flock: se já está rodando, a nova sai; se
caiu (reboot, OOM), a próxima retoma do manifesto. Prioridade baixa, 3 threads.

    0 * * * * cd /root/rodado-db && flock -n compacta.lock nice -n 19 ionice -c3 python3 compacta.py >> compacta.log 2>&1

    python3 compacta.py --status     # quanto falta, sem mexer em nada
    python3 compacta.py --max 3      # só os 3 primeiros da fila (teste)
"""
import json
import os
import shutil
import subprocess
import sys
import time

import duckdb

BASE = "/root/rodado-db"
TMP = f"{BASE}/compacta_tmp"
MANIFESTO_LOCAL = f"{BASE}/compactados.json"
CHAVE = "_db/compactados.json"
SSD = "/var/lib/docker/volumes/rodado-db-dados/_data/local"
CATALOGO = "/var/lib/docker/volumes/rodado-db-dados/_data/catalogo.duckdb"
BUCKET = "s3://baseldosdados"
ENDPOINT = "https://hel1.your-objectstorage.com"
NIVEL = 19
GANHO_MINIMO = 0.97  # menos de 3% de ganho não vale a troca: fica como está, marcado "pulado"

# primeiro o que mais encolhe (medido); depois o resto, do maior arquivo para o menor
PRIORIDADE = ["br_cgu_novo_bolsa_familia/", "br_cgu_pe_de_meia/", "br_cgu_seguro_defeso/",
              "br_cgu_garantia_safra/", "br_bcb_sicor/saldo/", "br_ok_queridodiario_texto/",
              "br_pgfn_dividaativa/divida_trimestres/", "br_me_rais/microdados_vinculos/"]
# encolhem ~4% no nível 19 e custariam dias de CPU daqui
FORA = ("br_tse_eleicoes/", "br_ms_sia/", "br_ibge_pnadc/")


def log(*a):
    print(time.strftime("%Y-%m-%d %H:%M:%S"), *a, flush=True)


def ambiente():
    env = dict(os.environ)
    for linha in open(f"{BASE}/.s3"):
        if "=" in linha and not linha.lstrip().startswith("#"):
            k, v = linha.strip().split("=", 1)
            env[k] = v.strip().strip('"').strip("'")
    env.update(AWS_ACCESS_KEY_ID=env["S3_KEY"], AWS_SECRET_ACCESS_KEY=env["S3_SECRET"], AWS_DEFAULT_REGION="hel1")
    return env


ENV = ambiente()


def aws(*args, check=True, capture=True):
    return subprocess.run(["aws", *args, "--endpoint-url", ENDPOINT], env=ENV, check=check,
                          capture_output=capture, text=True)


def listagem():
    """{chave: tamanho} de todos os .parquet do bucket."""
    out = aws("s3", "ls", "--recursive", f"{BUCKET}/").stdout
    objs = {}
    for linha in out.splitlines():
        partes = linha.split(None, 3)
        if len(partes) == 4 and partes[3].endswith(".parquet"):
            objs[partes[3]] = int(partes[2])
    return objs


def tamanho_no_bucket(chave):
    r = aws("s3api", "head-object", "--bucket", "baseldosdados", "--key", chave, check=False)
    return json.loads(r.stdout)["ContentLength"] if r.returncode == 0 else None


def le_manifesto():
    r = aws("s3", "cp", f"{BUCKET}/{CHAVE}", "-", check=False)
    if r.returncode == 0 and r.stdout.strip():
        return json.loads(r.stdout)
    return json.load(open(MANIFESTO_LOCAL)) if os.path.exists(MANIFESTO_LOCAL) else {}


def grava_manifesto(m):
    with open(MANIFESTO_LOCAL + ".tmp", "w") as f:
        json.dump(m, f, separators=(",", ":"))
    os.replace(MANIFESTO_LOCAL + ".tmp", MANIFESTO_LOCAL)
    aws("s3", "cp", "--only-show-errors", MANIFESTO_LOCAL, f"{BUCKET}/{CHAVE}")


def feito(m, chave, tamanho):
    c = m.get(chave)
    return c is not None and c["z"] == tamanho


def fila(objs, m):
    falta = [k for k, s in objs.items() if not k.startswith("_") and not k.startswith(FORA) and not feito(m, k, s)]
    def ordem(k):
        p = next((i for i, pre in enumerate(PRIORIDADE) if k.startswith(pre)), len(PRIORIDADE))
        return (p, -objs[k])
    return sorted(falta, key=ordem)


def impressao(con, arq):
    lit = "'" + arq.replace("'", "''") + "'"
    tipos = con.execute(f"SELECT column_name, column_type FROM (DESCRIBE SELECT * FROM read_parquet({lit}, hive_partitioning=false))").fetchall()
    n, h = con.execute(f"SELECT count(*), sum(hash(t))::HUGEINT FROM read_parquet({lit}, hive_partitioning=false) t").fetchone()
    return tipos, n, h


def comprime(con, chave, tamanho):
    """Devolve a entrada do manifesto para `chave`, ou None se não deu para decidir agora."""
    orig, novo = f"{TMP}/orig.parquet", f"{TMP}/z.parquet"
    for f in (orig, novo):
        if os.path.exists(f):
            os.remove(f)
    aws("s3", "cp", "--only-show-errors", f"{BUCKET}/{chave}", orig)
    if os.path.getsize(orig) != tamanho:
        log(f"  ! {chave}: baixou {os.path.getsize(orig)} bytes, o bucket diz {tamanho}; fica para a próxima")
        return None
    lit = "'" + orig + "'"
    meta = con.execute(f"SELECT count(*) FROM parquet_kv_metadata({lit}) WHERE key::VARCHAR NOT IN ('ARROW:schema')").fetchone()[0]
    if meta:
        return {"orig": tamanho, "z": tamanho, "pulado": "metadado próprio"}
    con.execute(f"COPY (SELECT * FROM read_parquet({lit}, hive_partitioning=false)) TO '{novo}' "
                f"(FORMAT parquet, COMPRESSION zstd, COMPRESSION_LEVEL {NIVEL}, ROW_GROUP_SIZE 122880)")
    a, b = impressao(con, orig), impressao(con, novo)
    if a != b:
        log(f"  ! {chave}: regravado NÃO bate (linhas {a[1]} -> {b[1]}, tipos iguais {a[0] == b[0]}); fica como está")
        return {"orig": tamanho, "z": tamanho, "pulado": "não bateu"}
    z = os.path.getsize(novo)
    if z >= GANHO_MINIMO * tamanho:
        return {"orig": tamanho, "z": tamanho, "pulado": f"ganho {100 - 100 * z / tamanho:.1f}%"}
    if tamanho_no_bucket(chave) != tamanho:  # o beelink subiu outra versão enquanto isso
        log(f"  ! {chave}: mudou no bucket durante a compressão; fica para a próxima")
        return None
    aws("s3", "cp", "--only-show-errors", novo, f"{BUCKET}/{chave}")
    if tamanho_no_bucket(chave) != z:
        log(f"  ! {chave}: subida não conferiu; fica para a próxima")
        return None
    local = f"{SSD}/{chave}"
    if os.path.exists(local) and os.path.getsize(local) == tamanho:
        shutil.copyfile(novo, local + ".parcial")
        os.chown(local + ".parcial", 1000, 1000)
        os.replace(local + ".parcial", local)
    return {"orig": tamanho, "z": z, "linhas": a[1], "quando": time.strftime("%Y-%m-%d")}


def main():
    os.makedirs(TMP, exist_ok=True)
    objs, m = listagem(), le_manifesto()
    falta = fila(objs, m)
    feitos = [k for k in objs if feito(m, k, objs[k]) and "pulado" not in m[k]]
    antes, depois = sum(m[k]["orig"] for k in feitos), sum(m[k]["z"] for k in feitos)
    log(f"{len(feitos)} comprimidos ({antes / 2**30:.1f} -> {depois / 2**30:.1f} GiB), "
        f"{sum(1 for k in objs if feito(m, k, objs[k]) and 'pulado' in m[k])} pulados, "
        f"{len(falta)} na fila ({sum(objs[k] for k in falta) / 2**30:.1f} GiB)")
    if "--status" in sys.argv:
        return
    con = duckdb.connect()
    con.execute(f"SET threads=3; SET memory_limit='2GB'; SET temp_directory='{TMP}/spill'; SET preserve_insertion_order=true")
    ultimo_salvo = ultimo_toque = time.monotonic()
    mudou = 0
    if "--max" in sys.argv:
        falta = falta[:int(sys.argv[sys.argv.index("--max") + 1])]
    for i, chave in enumerate(falta):
        t = time.monotonic()
        try:
            e = comprime(con, chave, objs[chave])
        except Exception as ex:  # um arquivo ruim não para a fila: tenta de novo na próxima rodada
            log(f"  ! {chave}: {type(ex).__name__}: {str(ex).splitlines()[0][:200]}")
            continue
        if e is None:
            continue
        m[chave] = e
        mudou += 1
        if "pulado" in e:
            log(f"{chave}: fica ({e['pulado']})")
        else:
            log(f"{chave}: {e['orig'] / 2**20:.1f} -> {e['z'] / 2**20:.1f} MiB ({100 * e['z'] / e['orig']:.0f}%) "
                f"em {time.monotonic() - t:.0f} s [{i + 1}/{len(falta)}]")
            # a instância do db.rodado.xyz guarda o tamanho dos arquivos (cache de metadado HTTP);
            # tocar o catálogo a faz abrir uma instância nova na próxima consulta
            if time.monotonic() - ultimo_toque > 30:
                os.utime(CATALOGO)
                ultimo_toque = time.monotonic()
        if time.monotonic() - ultimo_salvo > 300:
            grava_manifesto(m)
            ultimo_salvo, mudou = time.monotonic(), 0
    if mudou:
        grava_manifesto(m)
    os.utime(CATALOGO)
    shutil.rmtree(TMP, ignore_errors=True)
    log("fila vazia")


if __name__ == "__main__":
    main()
