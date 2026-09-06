#!/usr/bin/env python3
"""Enumera as combinações de famílias que NINGUÉM ainda perguntou.

Complementa a cascata F0–F7 de `tasks/hipoteses.md`, que conta quantas hipóteses
existem. Aqui a pergunta é outra: **quais** delas ainda não foram feitas, e
quais dessas valem a pena.

Três entradas, todas versionadas:
  docs/context/familias.yaml              dataset -> família + papel
  docs/context/cobertura_municipal.json   quantos municípios cada dataset cobre
  docs/context/basedosdados-schema.json   colunas, para achar a chave de join

E três saídas em tasks/:
  inedito_familias.tsv   toda combinação de 2..4 famílias, coberta ou não
  inedito_ranked.tsv     só as inéditas, ranqueadas
  inedito_cobertura.tsv  o que cada pergunta/hipótese/achado já ocupa

  python3 scripts/hipoteses/93_inedito.py [--n 3]
"""
import json, re, sys, itertools, unicodedata
from pathlib import Path
from collections import defaultdict, Counter
import yaml

REPO = Path(__file__).resolve().parent.parent.parent
CTX  = REPO / "docs" / "context"
OUT  = REPO / "tasks"

fam_cfg  = yaml.safe_load((CTX / "familias.yaml").read_text(encoding="utf-8"))
DSFAM    = {k: v["familia"] for k, v in fam_cfg["datasets"].items()}
DSPAPEL  = {k: v["papel"]   for k, v in fam_cfg["datasets"].items()}
FAMDESC  = {k: v["desc"]    for k, v in fam_cfg["familias"].items()}
schema   = json.loads((CTX / "basedosdados-schema.json").read_text(encoding="utf-8"))

cob_path = CTX / "cobertura_municipal.json"
COB = json.loads(cob_path.read_text(encoding="utf-8")) if cob_path.exists() else {}
if not COB:
    print("aviso: cobertura_municipal.json ausente — filtro de poder desligado", file=sys.stderr)

MIN_MUN = 2000          # F4
NMAX    = int(sys.argv[sys.argv.index("--n")+1]) if "--n" in sys.argv else 4

# ---------------------------------------------------------------- resolução
def norm(s): return s.replace("_", "").lower()
_BY_NORM = {}
for d in DSFAM:
    for pref in ("br_", "world_", "us_", "eu_", "un_", "global_", "mundo_", ""):
        if d.startswith(pref): _BY_NORM.setdefault(norm(d[len(pref):]), d)
def resolve(name):
    name = name.strip().strip("*\\`.,;:")
    if name in DSFAM: return name
    if f"br_{name}" in DSFAM: return f"br_{name}"
    return _BY_NORM.get(norm(name))

# ---------------------------------------------------------------- o que já existe
DS_TOKEN = re.compile(r"\b((?:br|world|us|eu|un|global|mundo)_[a-z0-9_]+)\b")
# achados_fortes.md e hipoteses.md citam a fonte em prosa ("CNEFE", "PRODES"),
# não como token — sem o léxico nenhum achado conta como cobertura
APELIDO = fam_cfg.get("apelidos", {})
_ALIAS_RE = re.compile("|".join(re.escape(k) for k in
                       sorted(APELIDO, key=len, reverse=True)))
def datasets_no_texto(linha):
    ds = {d for d in DS_TOKEN.findall(linha) if d in DSFAM}
    ds |= {APELIDO[m.group(0)] for m in _ALIAS_RE.finditer(linha)}
    return {d for d in ds if d in DSFAM}

def familias_de(names):
    fs = {DSFAM[d] for d in names if d in DSFAM}
    return frozenset(fs - {"referencia"})

coberto = defaultdict(list)   # frozenset(familias) -> [origem]

# perguntas.md — tem a lista de datasets entre parênteses, é o caso fácil
ITEM = re.compile(r"^(\d+)\.\s+.*?\*\(n=\d+[+–-]*:\s*(.+?)\)\*\s*$")
tema = None
for line in (REPO/"docs"/"hipoteses"/"perguntas.md").read_text(encoding="utf-8").splitlines():
    m = re.match(r"^## (\d+) · ", line)
    if m: tema = m.group(1); continue
    m = ITEM.match(line.strip())
    if not m: continue
    ds = {r for r in (resolve(x) for x in m.group(2).split(",")) if r}
    f = familias_de(ds)
    if len(f) >= 2: coberto[f].append(f"P{tema}-{m.group(1)}")

# hipoteses.md e achados_fortes.md — só citam o nome do dataset no texto
for arq, tag in [("tasks/hipoteses.md","H"), ("docs/hipoteses/achados_fortes.md","A")]:
    for line in (REPO/arq).read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"): continue
        cod = re.match(r"\|\s*\*\*([A-Z]?\d+[a-z]?)\*\*", line)
        f = familias_de(datasets_no_texto(line))
        if len(f) >= 2:
            coberto[f].append(f"{tag}{cod.group(1) if cod else '?'}")

# uma combinação está coberta se ela OU qualquer superconjunto dela foi usado
def esta_coberta(f):
    for c in coberto:
        if f <= c: return coberto[c][0]
    return None

# ---------------------------------------------------------------- candidatas
# melhor dataset municipal de cada família (mais municípios, papel desfecho)
melhor = {}
for d, fam in DSFAM.items():
    if fam == "referencia": continue
    n = COB.get(d, {}).get("n_mun", 0)
    if n < MIN_MUN: continue
    cur = melhor.get(fam)
    if cur is None or n > cur[1]: melhor[fam] = (d, n)

FAMS = sorted(melhor)
print(f"{len(FAMS)} famílias com pelo menos um dataset cobrindo ≥{MIN_MUN} municípios")
print(f"{len(coberto)} combinações de família já ocupadas por pergunta/hipótese/achado")

so_controle = {f for f in FAMS
               if all(DSPAPEL.get(d) == "controle"
                      for d in DSFAM if DSFAM[d] == f and COB.get(d,{}).get("n_mun",0) >= MIN_MUN)}

linhas, ineditas = [], []
for n in range(2, NMAX+1):
    for combo in itertools.combinations(FAMS, n):
        f = frozenset(combo)
        # F6: no máximo uma perna que só serve de controle
        if len(f & so_controle) > 1: continue
        origem = esta_coberta(f)
        poder = min(melhor[x][1] for x in combo)
        linhas.append((n, "+".join(sorted(combo)), poder, origem or ""))
        if not origem: ineditas.append((n, combo, poder))

print(f"{len(linhas)} combinações de 2..{NMAX} famílias; {len(ineditas)} inéditas")

with (OUT/"inedito_familias.tsv").open("w") as fh:
    fh.write("n\tfamilias\tpoder_min_municipios\tcoberta_por\n")
    for r in sorted(linhas, key=lambda r: (r[0], -r[2])):
        fh.write("\t".join(map(str, r)) + "\n")

# ---------------------------------------------------------------- ranking
# ineditismo: quantos dos pares internos também são inéditos (0..1)
par_coberto = {frozenset(p) for c in coberto for p in itertools.combinations(c, 2)}
rank = []
for n, combo, poder in ineditas:
    pares = list(itertools.combinations(combo, 2))
    novos = sum(1 for p in pares if frozenset(p) not in par_coberto)
    rank.append({
        "n": n, "familias": combo, "poder": poder,
        "ineditismo": novos/len(pares),
        "datasets": [melhor[x][0] for x in combo],
        "score": (novos/len(pares)) * min(1.0, poder/5000),
    })
rank.sort(key=lambda r: (-r["score"], -r["poder"]))
with (OUT/"inedito_ranked.tsv").open("w") as fh:
    fh.write("score\tn\tineditismo\tpoder\tfamilias\tdatasets_sugeridos\n")
    for r in rank:
        fh.write(f"{r['score']:.3f}\t{r['n']}\t{r['ineditismo']:.2f}\t{r['poder']}\t"
                 f"{'+'.join(sorted(r['familias']))}\t{', '.join(r['datasets'])}\n")

with (OUT/"inedito_cobertura.tsv").open("w") as fh:
    fh.write("familias\tn_familias\tocorrencias\torigens\n")
    for f, o in sorted(coberto.items(), key=lambda x: -len(x[1])):
        fh.write(f"{'+'.join(sorted(f))}\t{len(f)}\t{len(o)}\t{','.join(o[:8])}\n")

print("\ntop 25 inéditas:")
for r in rank[:25]:
    print(f"  {r['score']:.3f}  n={r['n']}  poder={r['poder']:5d}  "
          f"{'+'.join(sorted(r['familias']))}")
print(f"\nescrito: tasks/inedito_ranked.tsv, inedito_familias.tsv, inedito_cobertura.tsv")
