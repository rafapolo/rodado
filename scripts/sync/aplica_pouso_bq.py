#!/usr/bin/env python3
"""Aplica no ~/rodado as partições que o finland deixou em s3://baseldosdados/_pouso/.

Roda no beelink, pelo cron, a cada 15 minutos. Offline, o `mc` falha e nada acontece: a próxima
passada tenta de novo. Só entra no ~/rodado o que passar na conferência; o arquivo antigo vai para
~/backups/pouso_<data>/, a mesma troca de atualiza_particoes_bq.py. Partição aplicada sai do pouso.
Com _pouso/FIM.json e nada a aplicar, repara as views, soma o gasto ao contador de cota do
beelink e tira a própria linha do crontab. Ver coleta_pouso_bq.py.
"""
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

H = Path.home()
MC = str(H / "bin/mc")
POUSO = "hzS3/baseldosdados/_pouso"
RAIZ = H / "rodado"
ESTADO = H / "scrap_tmp/pouso_estado.json"
REPO = H / "scrap_tmp/repo"


def log(*a):
    print(time.strftime("%F %T"), *a, flush=True)


def corre(*cmd, timeout=7200):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def duck(sql):
    r = subprocess.run([str(H / "bin/duckdb"), "-json", "-c", "SET enable_progress_bar=false; " + sql],
                       capture_output=True, text=True, timeout=7200)
    i = r.stdout.find("[")
    return json.loads(r.stdout[i:]) if i >= 0 else None


def aplica(chave, ok, estado):
    prefixo = f"{POUSO}/{chave}"
    sys.path.insert(0, str(REPO / "scripts/sync"))
    from fonte_propria import recusa
    import retrato_novo
    ds_tb = ".".join(chave.split("/")[:2])
    retrato = retrato_novo.config(ds_tb)
    if not retrato and (m := recusa(ds_tb)):
        log("  recusada:", chave, m)
        return False
    dest = RAIZ / chave.rsplit("/", 1)[0]
    p, col, n = ok["p"], ok["col"], ok["bq"]
    # retrato novo (último retrato + *_historico): cai no diretório de trabalho, nunca em <tb>/
    novo = Path(os.path.expanduser(retrato_novo.pasta(ds_tb))) / p if retrato else dest / f".novo_{p}"
    subprocess.run(["rm", "-rf", str(novo)], check=True)
    r = corre(MC, "cp", "--recursive", "-q", prefixo + "/", str(novo) + "/")
    if r.returncode:
        log("  sem download:", chave, r.stderr[:160])
        return False
    (novo / "ok.json").unlink(missing_ok=True)
    conf = duck(f"SELECT count(*) n, count(*) FILTER (WHERE CAST({col} AS VARCHAR) = '{p}') na FROM read_parquet('{novo}/*.parquet')")
    if not conf or conf[0]["n"] != n or conf[0]["na"] != n:
        subprocess.run(["rm", "-rf", str(novo)])
        log("  conferência falhou:", chave, conf)
        return False
    if retrato:
        # --anexa confere D contra a fonte e o passado contra o histórico; ocupado => próxima passada
        r = subprocess.run(["bash", "-c", retrato_novo.comando(ds_tb, novo=shlex.quote(str(novo))).replace("flock ", "flock -n ", 1)],
                           capture_output=True, text=True, cwd=str(REPO))
        if r.returncode:
            log("  --anexa não concluiu (ocupado ou recusado), o retrato fica em", novo, (r.stdout + r.stderr)[-300:])
            return False
        estado["aplicadas"].append(chave)
        estado["bytes"] += ok.get("bytes", 0)
        ESTADO.write_text(json.dumps(estado))
        corre(MC, "rm", "--recursive", "--force", prefixo + "/")
        log(f"  {chave}: anexado ao histórico ({n:,} linhas)")
        return True
    backup = H / f"backups/pouso_{time.strftime('%Y%m%d')}/{dest.relative_to(RAIZ)}"
    antigos = " ".join(shlex.quote(a) for a in ok.get("antigos") or [])
    mover = f"mkdir -p {shlex.quote(str(backup))} && mv {antigos} {shlex.quote(str(backup))}/ && " if antigos else ""
    r = subprocess.run(["bash", "-c", f"set -e; cd {shlex.quote(str(dest))}; {mover}"
                        f"i=0; for f in $(ls .novo_{p}/*.parquet | sort); do "
                        f"while [ -e $(printf '%012d.parquet' $i) ]; do i=$((i+1)); done; "
                        f"mv $f $(printf '%012d.parquet' $i); chmod 664 $(printf '%012d.parquet' $i); done; "
                        f"rmdir .novo_{p}"], capture_output=True, text=True)
    if r.returncode:
        log("  troca falhou, ver à mão:", chave, r.stderr[:200])
        return False
    dep = duck(f"SELECT count(*) n FROM read_parquet('{dest}/*.parquet', union_by_name=true) WHERE CAST({col} AS VARCHAR) = '{p}'")
    if not dep or dep[0]["n"] != n:
        log("  contagem final diverge, ver à mão:", chave, dep)
        return False
    estado["aplicadas"].append(chave)
    estado["bytes"] += ok.get("bytes", 0)
    estado["views"] = True
    ESTADO.write_text(json.dumps(estado))
    corre(MC, "rm", "--recursive", "--force", prefixo + "/")
    log(f"  {chave}: {ok['disco']:,} -> {n:,}")
    return True


def main():
    r = corre(MC, "ls", "--recursive", POUSO + "/", timeout=300)
    if r.returncode:
        return 0  # offline, ou pouso ainda vazio: a próxima passada tenta de novo
    chaves = [ln.split()[-1] for ln in r.stdout.splitlines() if ln.split()]
    estado = json.loads(ESTADO.read_text()) if ESTADO.exists() else {"aplicadas": [], "bytes": 0, "views": False}
    falhou = 0
    for c in sorted(c[:-len("/ok.json")] for c in chaves if c.endswith("/ok.json")):
        if c in estado["aplicadas"]:
            continue
        ok = json.loads(corre(MC, "cat", f"{POUSO}/{c}/ok.json").stdout)
        if not aplica(c, ok, estado):
            falhou += 1
    if estado["views"]:
        v = subprocess.run([sys.executable, "-u", "scripts/repara_views_beelink.py", "--apply"], cwd=REPO,
                           env={**os.environ, "BEELINK_HOST": "local"}, capture_output=True, text=True)
        if v.returncode == 0 and "falhou" not in v.stdout + v.stderr:
            estado["views"] = False
            ESTADO.write_text(json.dumps(estado))
            log("views reparadas")
        else:
            log("views não reparadas agora; tenta na próxima passada")
    if "FIM.json" in chaves and not falhou and not estado["views"]:
        sys.path.insert(0, str(REPO / "scripts/sync"))
        import bq_quota
        bq_quota.reserve(estado["bytes"])
        fim = corre(MC, "cat", f"{POUSO}/FIM.json").stdout
        (H / "scrap_tmp/pouso_fim.json").write_text(fim)
        corre(MC, "rm", "--force", f"{POUSO}/FIM.json")
        cron = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
        subprocess.run(["crontab", "-"], input="".join(ln + "\n" for ln in cron.splitlines() if "aplica_pouso_bq" not in ln), text=True)
        log(f"FIM: {len(estado['aplicadas'])} partições aplicadas, {estado['bytes']/1e9:.1f} GB lidos; cron removido")
    return 1 if falhou else 0


if __name__ == "__main__":
    sys.exit(main())
