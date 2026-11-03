#!/usr/bin/env python3
"""Compara ~/rodado com hzS3/baseldosdados por nome+tamanho.

Escreve em WORK: upload.txt (falta ou tamanho diferente, e aprovado por
valida_parquet.py), rejeitados.txt (reprovados: não sobem), orfaos.txt (só no S3,
como URL do mc) e imprime um resumo JSON. Sai 0 só se as duas listagens vieram
inteiras. REMOVE_OK no resumo diz se é seguro apagar os órfãos.
"""
import json, os, re, subprocess, sys, time

SRC = os.path.expanduser("~/rodado")
DST = "hzS3/baseldosdados"
MC = os.path.expanduser("~/bin/mc")
WORK = sys.argv[1]
START = float(os.environ.get("S3SYNC_START", time.time()))
G = 2**30
# datasets que sobem primeiro (a pedido, 2026-10-09)
PRIORIDADE = re.compile(r"(^|_)(tse|ibge)(_|$)")


def skip(rel):
    return rel.startswith(".claude/") or rel.endswith(".log")


# listagem local inteira ou nada (2026-11-03): os.walk pula em silêncio diretório que não
# consegue ler, e o que estava nele viraria órfão no S3. Erro de leitura aborta a checagem.
def _falha_walk(e):
    sys.exit(f"listagem local falhou: {e}")
if not os.path.isdir(SRC) or not os.listdir(SRC):
    sys.exit(f"{SRC} ausente ou vazio")
loc = {}
for root, _, files in os.walk(SRC, onerror=_falha_walk):
    for f in files:
        p = os.path.join(root, f)
        rel = os.path.relpath(p, SRC)
        if skip(rel):
            continue
        try:
            st = os.stat(p)
        except FileNotFoundError:
            continue
        loc[rel] = (st.st_size, st.st_mtime)

r = subprocess.run([MC, "ls", "-r", "--json", DST], capture_output=True, text=True)
if r.returncode != 0:
    sys.exit(f"mc ls falhou: {r.stderr[-300:]}")
s3 = {}
for line in r.stdout.splitlines():
    o = json.loads(line)
    if o.get("status") != "success":
        sys.exit(f"mc ls devolveu erro: {line[:300]}")
    if o.get("type") == "file":
        s3[o["key"]] = o["size"]

# arquivos que o finland recomprimiu em zstd 19 (db/compacta.py, desde 2026-10-22): no S3 têm
# outro tamanho de propósito. Estão em dia se o local ainda tem o tamanho de quando foram
# comprimidos e o S3 tem o tamanho comprimido; se o local mudou, sobem de novo (e o finland
# comprime outra vez na rodada seguinte).
MANIFESTO = "_db/compactados.json"
m = subprocess.run([MC, "cat", f"{DST}/{MANIFESTO}"], capture_output=True, text=True)
comp = json.loads(m.stdout) if m.returncode == 0 and m.stdout.strip() else {}
def em_dia(k, s):
    c = comp.get(k)
    return s3.get(k) == s or (c is not None and c["orig"] == s and c["z"] == s3.get(k))
up = [k for k, (s, _) in loc.items() if not em_dia(k, s)]
# arquivo mexido depois do início da corrida está sendo escrito por outra sessão
estavel = [k for k in up if loc[k][1] < START]
# trava de integridade (2026-10-28): o S3 recebia fielmente parquet gravado errado (cabeçalho
# colado, coluna JSON nula, texto não UTF-8). valida_parquet.py lê cada parquet que vai subir;
# reprovado não sobe (o S3 fica com a cópia que já tinha) e vai para rejeitados.txt.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from valida_parquet import valida
res = valida([os.path.join(SRC, k) for k in estavel])
rej = sorted(k for k in estavel if not res.get(os.path.join(SRC, k), {"ok": True})["ok"])
with open(os.path.join(WORK, "rejeitados.txt"), "w") as f:
    f.writelines(k + "\t" + "; ".join(res[os.path.join(SRC, k)]["motivos"]) + "\n" for k in rej)
rej_s = set(rej)
up = [k for k in up if k not in rej_s]
estavel = [k for k in estavel if k not in rej_s]
orf = [k for k in s3 if k not in loc and k != MANIFESTO and not k.startswith("_pouso/")]  # pouso do finland: ver coleta_pouso_bq.py
orf_b = sum(s3[k] for k in orf)

with open(os.path.join(WORK, "upload.txt"), "w") as f:
    f.writelines(k + "\n" for k in sorted(
        up, key=lambda k: (not PRIORIDADE.search(k.split("/")[0]), loc[k][0])))
with open(os.path.join(WORK, "orfaos.txt"), "w") as f:
    f.writelines(f"{DST}/{k}\n" for k in orf)

# travas da remoção: nada estável pendente, e o volume de órfãos dentro do que foi medido
# em 2026-10-09 (19.774 arquivos, 113 GiB). Listagem local truncada não chega aqui (o walk
# acima aborta), e disco desmontado dá ~50 mil órfãos, barrados pelo teto.
# Até 2026-11-03 havia também um piso de arquivos locais (70.000, depois 55.000); ele
# envelhecia a cada poda/ordenação (CNPJ em 10/13, SIA/ANS e TSE em 10/29–11/03 deixaram o
# local em 52.703) e a remoção parava de rodar. Uma razão local/S3 também não serve: cai
# justamente quando há muitos órfãos (0,84 em 2026-11-01). Retirado a pedido.
remove_ok = not estavel and len(orf) <= 25000 and orf_b <= 130 * G
print(json.dumps({
    "local": len(loc), "local_gib": round(sum(s for s, _ in loc.values()) / G, 1),
    "s3": len(s3), "s3_gib": round(sum(s3.values()) / G, 1),
    "a_subir": len(up), "a_subir_gib": round(sum(loc[k][0] for k in up) / G, 1),
    "a_subir_estavel": len(estavel), "rejeitados": len(rej),
    "a_subir_prioridade": sum(1 for k in up if PRIORIDADE.search(k.split("/")[0])),
    "a_subir_prioridade_gib": round(sum(loc[k][0] for k in up if PRIORIDADE.search(k.split("/")[0])) / G, 1),
    "orfaos": len(orf), "orfaos_gib": round(orf_b / G, 1),
    "compactados": sum(1 for k in comp if k in s3 and comp[k]["z"] == s3[k]),
    "REMOVE_OK": remove_ok,
}))
