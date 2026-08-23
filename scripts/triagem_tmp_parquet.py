#!/usr/bin/env python3
"""Triagem dos tmp*.parquet largados no espelho do beelink.

    python3 scripts/triagem_tmp_parquet.py            # dry-run (padrão)
    python3 scripts/triagem_tmp_parquet.py --apply    # executa o que for seguro

O `join_keys.md` descreve esses arquivos como sobra de um sync abortado, o que
sugere que apagar resolve. Isso vale para uma parte deles e **destrói dado** no
resto: em muitos diretórios o tmp é o único arquivo, e em outros ele tem mais
linhas que o export canônico. Por isso aqui é triagem, não faxina.

Quatro veredictos:

  PROMOVER    não existe arquivo canônico — o tmp É a tabela. Renomeia para o
              próximo índice livre (000000000NNN.parquet) e ajusta o modo, que
              nos tmp está 0600 e deveria ser 0664 como os vizinhos.
  APAGAR_TMP  mesmo conjunto de colunas, mesma contagem e mesmo hash de linhas
              que o canônico. É cópia de verdade; some sem perda.
  INVESTIGAR  qualquer divergência — contagem diferente, coluna a mais/a menos,
              ou hash diferente com a mesma contagem. Nunca é tocado.
  VAZIO       tmp com zero linhas.

A comparação de hash é por NOME de coluna, não por posição: os dois lados
gravam as mesmas colunas em ordens diferentes (o canônico de
br_bd_diretorios_brasil.uf é id_uf,sigla,nome,regiao e o tmp é
id_uf,nome,regiao,sigla), então um hash da linha inteira acusaria diferença em
arquivos idênticos. O DuckDB casa por nome ao ler o glob, então a leitura não
embaralha valor — o efeito real é só a duplicação.

Só os candidatos a APAGAR_TMP são hasheados: nos outros a contagem já decidiu, e
hashear tabela grande à toa custa I/O sem mudar veredicto.
"""
import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict

BEELINK = os.environ.get("BEELINK_HOST", "beelink")
ROOT = "/home/polo/rodado"
DUCKDB = "~/bin/duckdb"


def sh(cmd, timeout=600):
    out = subprocess.run(["ssh", BEELINK, cmd], capture_output=True, text=True, timeout=timeout)
    if out.returncode != 0:
        sys.exit(f"ssh falhou: {out.stderr.strip()[:300]}")
    return out.stdout


def duck(sql, timeout=1800):
    payload = "SET enable_progress_bar=false;\n" + sql + "\n.quit\n"
    proc = subprocess.run(
        ["ssh", BEELINK, f"{DUCKDB} -json"],
        input=payload, capture_output=True, text=True, timeout=timeout,
    )
    body = proc.stdout[proc.stdout.index("["):] if "[" in proc.stdout else ""
    if not body:
        sys.exit(f"DuckDB não devolveu nada: {proc.stderr.strip()[:300]}")
    return json.loads(body)


def q(path):
    return path.replace("'", "''")


def collect():
    """{dir: {"tmp": [files], "real": [files]}} para todo dir com tmp*.parquet."""
    listing = sh(f"find {ROOT} -maxdepth 3 -name 'tmp*.parquet' -printf '%h\\n' | sort -u")
    dirs = [d for d in listing.split("\n") if d.strip()]
    out = {}
    for d in dirs:
        files = sh(f"ls -1 {q(d)}").split("\n")
        tmp = [f for f in files if f.startswith("tmp") and f.endswith(".parquet")]
        real = [f for f in files if f.endswith(".parquet") and not f.startswith("tmp")]
        out[d] = {"tmp": sorted(tmp), "real": sorted(real)}
    return out


def metadata(dirs):
    """Contagem de linhas e conjunto de colunas, por lado, para cada diretório.

    Os globs vão explícitos, um por diretório: varrer o espelho inteiro devolve
    ~2 milhões de linhas de schema (200 MB de JSON) para decidir sobre 80 pastas.
    """
    globs = "[" + ", ".join(f"'{q(d)}/*.parquet'" for d in dirs) + "]"
    rows = duck(f"""
WITH f AS (
  SELECT regexp_replace(file_name, '/[^/]+$', '') AS dir,
         regexp_extract(file_name, '([^/]+)$', 1) AS fname,
         num_rows
  FROM parquet_file_metadata({globs})
)
SELECT dir,
       COALESCE(SUM(num_rows) FILTER (WHERE fname LIKE 'tmp%'), 0)     AS tmp_rows,
       SUM(num_rows) FILTER (WHERE fname NOT LIKE 'tmp%')              AS real_rows
FROM f GROUP BY dir;""")
    meta = {r["dir"]: r for r in rows}

    cols = duck(f"""
SELECT regexp_replace(file_name, '/[^/]+$', '') AS dir,
       CASE WHEN regexp_extract(file_name, '([^/]+)$', 1) LIKE 'tmp%'
            THEN 'tmp' ELSE 'real' END AS side,
       name
FROM parquet_schema({globs})
WHERE num_children IS NULL OR num_children = 0;""")
    colmap = defaultdict(lambda: {"tmp": set(), "real": set()})
    for c in cols:
        colmap[c["dir"]][c["side"]].add(c["name"])

    for d in dirs:
        m = meta.get(d, {})
        dirs[d]["tmp_rows"] = int(m.get("tmp_rows") or 0)
        dirs[d]["real_rows"] = None if m.get("real_rows") is None else int(m["real_rows"])
        dirs[d]["tmp_cols"] = colmap[d]["tmp"]
        dirs[d]["real_cols"] = colmap[d]["real"]
    return dirs


def hash_side(directory, files, columns):
    """Hash das linhas, somado (independe de ordem), com as colunas por nome.

    Recebe a lista de arquivos, não um glob: os nomes canônicos não seguem um
    padrão que dê para casar com segurança, e um glob que não casa nada vira
    erro em vez de veredicto.
    """
    expr = ", ".join(f'"{c}"' for c in sorted(columns))
    paths = "[" + ", ".join(f"'{q(directory)}/{q(f)}'" for f in files) + "]"
    res = duck(
        f"SELECT COALESCE(sum(hash({expr})::HUGEINT), 0) AS h "
        f"FROM read_parquet({paths});"
    )
    return str(res[0]["h"])


def classify(dirs):
    plan = []
    for d, info in sorted(dirs.items()):
        table = d.replace(ROOT + "/", "").replace("/", ".", 1)
        tmp_rows, real_rows = info["tmp_rows"], info["real_rows"]

        if tmp_rows == 0:
            verdict, why = "VAZIO", "tmp sem linhas"
        elif real_rows is None:
            verdict, why = "PROMOVER", f"não há arquivo canônico; o tmp tem {tmp_rows:,} linhas"
        elif info["tmp_cols"] != info["real_cols"]:
            only_t = sorted(info["tmp_cols"] - info["real_cols"])
            only_r = sorted(info["real_cols"] - info["tmp_cols"])
            verdict = "INVESTIGAR"
            why = f"colunas diferem — só no tmp: {only_t or '—'}; só no canônico: {only_r or '—'}"
        elif tmp_rows != real_rows:
            delta = tmp_rows - real_rows
            verdict = "INVESTIGAR"
            why = (f"tmp {tmp_rows:,} x canônico {real_rows:,} "
                   f"({delta:+,} — apagar o tmp {'truncaria' if delta > 0 else 'não perde'})")
        else:
            verdict, why = "?", ""
        plan.append({"dir": d, "table": table, "verdict": verdict, "why": why, **info})
    return plan


def confirm_duplicates(plan):
    """Só os empatados em contagem: hash dos dois lados para provar igualdade."""
    for item in plan:
        if item["verdict"] != "?":
            continue
        try:
            h_tmp = hash_side(item["dir"], item["tmp"], item["tmp_cols"])
            h_real = hash_side(item["dir"], item["real"], item["real_cols"])
        except Exception as exc:                                   # noqa: BLE001
            item["verdict"] = "INVESTIGAR"
            item["why"] = f"hash falhou ({exc})"
            continue
        if h_tmp == h_real:
            item["verdict"] = "APAGAR_TMP"
            item["why"] = f"cópia idêntica ({item['tmp_rows']:,} linhas, hash confere)"
        else:
            item["verdict"] = "INVESTIGAR"
            item["why"] = (f"mesma contagem ({item['tmp_rows']:,}) mas conteúdo "
                           f"diferente — hash não confere")
    return plan


def next_index(directory, existing):
    used = set()
    for f in existing:
        stem = f.split(".")[0]
        if stem.isdigit():
            used.add(int(stem))
    i = 0
    while i in used:
        i += 1
    return f"{i:012d}.parquet"


def apply(plan):
    done = {"PROMOVER": 0, "APAGAR_TMP": 0}
    for item in plan:
        if item["verdict"] == "PROMOVER":
            existing = list(item["real"])
            for tmp in item["tmp"]:
                target = next_index(item["dir"], existing)
                existing.append(target)
                sh(f"mv -n {q(item['dir'])}/{tmp} {q(item['dir'])}/{target} && "
                   f"chmod 664 {q(item['dir'])}/{target}")
                print(f"  promovido  {item['table']}: {tmp} -> {target}")
                done["PROMOVER"] += 1
        elif item["verdict"] == "APAGAR_TMP":
            for tmp in item["tmp"]:
                sh(f"rm -f {q(item['dir'])}/{tmp}")
                print(f"  apagado    {item['table']}: {tmp}")
                done["APAGAR_TMP"] += 1
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="executa PROMOVER e APAGAR_TMP (INVESTIGAR nunca é tocado)")
    args = ap.parse_args()

    print("Levantando os tmp*.parquet no beelink…")
    achados = collect()
    if not achados:
        # Sem isso o glob vazio vira parquet_file_metadata([]) e o DuckDB aborta
        # com "needs at least one file to read". Nenhuma sobra é o estado bom.
        print("  nenhum tmp*.parquet no espelho — nada a triar.")
        return 0
    dirs = metadata(achados)
    print(f"  {len(dirs)} diretórios com tmp\n")

    plan = classify(dirs)
    pend = sum(1 for i in plan if i["verdict"] == "?")
    if pend:
        print(f"Conferindo hash de {pend} candidatos a duplicata…\n")
        plan = confirm_duplicates(plan)

    order = ["PROMOVER", "APAGAR_TMP", "VAZIO", "INVESTIGAR"]
    for verdict in order:
        items = [i for i in plan if i["verdict"] == verdict]
        if not items:
            continue
        print(f"\n=== {verdict} ({len(items)})")
        for i in items:
            print(f"  {i['table']:58} {i['why']}")

    counts = {v: sum(1 for i in plan if i["verdict"] == v) for v in order}
    rows_at_risk = sum(i["tmp_rows"] for i in plan if i["verdict"] == "PROMOVER")
    print(f"\n{'-' * 78}")
    print(f"PROMOVER {counts['PROMOVER']}  ({rows_at_risk:,} linhas que só existem no tmp)")
    print(f"APAGAR_TMP {counts['APAGAR_TMP']}   VAZIO {counts['VAZIO']}   "
          f"INVESTIGAR {counts['INVESTIGAR']}")

    if not args.apply:
        print("\nDry-run. Nada foi alterado. Rode com --apply para executar "
              "PROMOVER e APAGAR_TMP.")
        return 0

    print("\nAplicando…")
    done = apply(plan)
    print(f"\n{done['PROMOVER']} promovidos, {done['APAGAR_TMP']} apagados.")
    print("Agora rode, nesta ordem:")
    print("  python3 scripts/gera_schemas.py")
    print("  python3 scripts/build_metadata_catalog.py")
    print("  python3 scripts/gera_join_keys.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
