#!/usr/bin/env python3
"""Recria as views do beelink que estao fora de sincronia com os parquet no disco.

    python3 scripts/repara_views_beelink.py            # dry-run
    python3 scripts/repara_views_beelink.py --apply

As views em `~/rodado/basedosdados.duckdb` não usam glob: enumeram os arquivos
um a um dentro de `read_parquet(list_value(...))`. Então qualquer coisa que
renomeie ou remova um parquet — a triagem dos `tmp*.parquet`, por exemplo —
quebra a view, e a quebra só aparece na hora de consultar:

    IO Error: No files found that match the pattern ".../tmp315dr7qq.parquet"

Aqui a detecção é pelo sintoma, não pela lista do que foi mexido: lê o SQL de
toda view, compara com o conteúdo atual do diretório, e recria as que estiverem
fora de sincronia — com a mesma forma (`hive_partitioning`, `union_by_name`).

São DOIS sintomas, e o segundo é pior que o primeiro:

  arquivo morto     a view cita um parquet que não existe mais. Barulhento: a
                    consulta falha com IO Error e alguém percebe.
  arquivo ignorado  o parquet está no diretório e a view não o cita. Silencioso:
                    a consulta responde, só que a menos. É o que acontece quando
                    um re-export gera mais shards que o anterior — todos os nomes
                    antigos continuam existindo, então nada parece quebrado.
                    `densidade_municipio` leu 1.000.000 de 1.072.350 linhas assim.
"""
import argparse
import json
import os
import re
import subprocess
import sys

BEELINK = os.environ.get("BEELINK_HOST", "beelink")
DB = "~/rodado/basedosdados.duckdb"
DUCKDB = "~/bin/duckdb"
PATH_RE = re.compile(r"'(/home/[^']*\.parquet)'")


def duck(sql, readonly=True, timeout=900):
    flag = "-readonly " if readonly else ""
    proc = subprocess.run(
        ["ssh", BEELINK, f"{DUCKDB} {flag}-json {DB}"],
        input="SET enable_progress_bar=false;\n" + sql + "\n.quit\n",
        capture_output=True, text=True, timeout=timeout,
    )
    if "[" not in proc.stdout:
        if proc.returncode != 0 or "Error" in proc.stderr:
            sys.exit(f"DuckDB falhou: {(proc.stderr or proc.stdout).strip()[:400]}")
        return []
    return json.loads(proc.stdout[proc.stdout.index("["):])


def sh(cmd, timeout=300):
    return subprocess.run(["ssh", BEELINK, cmd], capture_output=True,
                          text=True, timeout=timeout).stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    views = duck("SELECT schema_name, view_name, sql FROM duckdb_views() "
                 "WHERE NOT internal;")
    print(f"{len(views)} views no catálogo")

    existing = set(sh("find ~/rodado -maxdepth 4 -name '*.parquet'").split("\n"))
    existing.discard("")

    broken = []
    for v in views:
        refs = PATH_RE.findall(v["sql"] or "")
        if not refs:
            continue
        missing = [r for r in refs if r not in existing]
        # O outro lado do mesmo problema, e o mais traiçoeiro: arquivo que existe no
        # diretório e a view NÃO cita. Nada quebra — a consulta responde, só que a
        # menos. Um re-export que gere mais shards que o anterior cai exatamente
        # aqui, porque todos os nomes antigos continuam existindo.
        table_dir = os.path.dirname(refs[0])
        atuais = {f for f in existing if os.path.dirname(f) == table_dir}
        ignorados = sorted(atuais - set(refs))
        if missing or ignorados:
            broken.append({**v, "refs": refs, "missing": missing,
                           "ignorados": ignorados})

    if not broken:
        print("Nenhuma view inconsistente.")
        return 0

    print(f"\n{len(broken)} views fora de sincronia com o disco:\n")
    stmts = []
    for b in broken:
        table_dir = os.path.dirname(b["refs"][0])
        files = sorted(f for f in existing if os.path.dirname(f) == table_dir)
        name = f'"{b["schema_name"]}"."{b["view_name"]}"'
        sintoma = []
        if b["missing"]:
            sintoma.append(f"-{len(b['missing'])} morto(s)")
        if b["ignorados"]:
            sintoma.append(f"+{len(b['ignorados'])} ignorado(s) — LIA A MENOS")
        print(f"  {b['schema_name']}.{b['view_name']:<42} "
              f"{', '.join(sintoma)} -> {len(files)} atual(is)")
        if not files:
            print("      ! diretório vazio — view deixada como está")
            continue
        lst = ", ".join(f"'{f}'" for f in files)
        stmts.append(
            f"CREATE OR REPLACE VIEW {name} AS SELECT * FROM read_parquet("
            f"list_value({lst}), hive_partitioning=true, union_by_name=true);"
        )

    if not args.apply:
        print(f"\nDry-run. {len(stmts)} views seriam recriadas. Use --apply.")
        return 0

    duck("\n".join(stmts), readonly=False)
    print(f"\n{len(stmts)} views recriadas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
