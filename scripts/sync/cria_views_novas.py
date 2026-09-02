#!/usr/bin/env python3
"""Cria views em ~/rodado/basedosdados.duckdb (beelink) para tabelas novas que
ainda não têm view no catálogo -- o passo que falta depois de
gcp_to_beelink_sync.py ou de qualquer scraper novo largar parquet direto no
disco sem passar por um `CREATE VIEW`.

`repara_views_beelink.py` só CONSERTA views que já existem e ficaram fora de
sincronia com o disco; não cria view nova do zero. Este script faz a parte
que falta: para cada `dataset/table` na lista de entrada, confere se já existe
uma view (pula se sim, idempotente) e, se não, lista os parquet no diretório e
roda `CREATE SCHEMA IF NOT EXISTS` + `CREATE OR REPLACE VIEW` no mesmo formato
usado por `repara_views_beelink.py` (arquivos enumerados um a um dentro de
`read_parquet(list_value(...))`, não glob -- mesma convenção do resto do
catálogo).

Uso:
    python3 scripts/sync/cria_views_novas.py <lista.txt>   # uma linha por dataset/table
"""
import json
import os
import subprocess
import sys

BEELINK = os.environ.get("BEELINK_HOST", "beelink")
DB = "~/rodado/basedosdados.duckdb"
DUCKDB = "~/bin/duckdb"


def duck(sql, readonly=True, timeout=120):
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


def sh(cmd, timeout=60):
    return subprocess.run(["ssh", BEELINK, cmd], capture_output=True,
                          text=True, timeout=timeout).stdout


def main():
    if len(sys.argv) != 2:
        sys.exit("uso: cria_views_novas.py <lista.txt>")

    with open(sys.argv[1]) as f:
        pairs = [line.strip().split("/", 1) for line in f if line.strip()]

    existing_views = {
        (v["schema_name"], v["view_name"])
        for v in duck("SELECT schema_name, view_name FROM duckdb_views() WHERE NOT internal;")
    }

    stmts = []
    skipped_no_files = []
    already = []
    for dataset, table in pairs:
        if (dataset, table) in existing_views:
            already.append(f"{dataset}.{table}")
            continue
        remote_dir = f"~/rodado/{dataset}/{table}"
        files_raw = sh(
            f"find {remote_dir} -maxdepth 1 -name '*.parquet' 2>/dev/null"
        ).strip()
        files = sorted(f for f in files_raw.split("\n") if f)
        # find with ~ over ssh needs expansion -- resolve to absolute /home/... paths
        # (same shape repara_views_beelink.py expects) via a second hop if needed.
        if not files:
            skipped_no_files.append(f"{dataset}.{table}")
            continue
        lst = ", ".join(f"'{p}'" for p in files)
        stmts.append(f'CREATE SCHEMA IF NOT EXISTS "{dataset}";')
        stmts.append(
            f'CREATE OR REPLACE VIEW "{dataset}"."{table}" AS SELECT * FROM '
            f"read_parquet(list_value({lst}), hive_partitioning=true, union_by_name=true);"
        )

    if already:
        print(f"Já tinham view ({len(already)}): {', '.join(already)}")
    if skipped_no_files:
        print(f"Sem parquet no diretório, pulados ({len(skipped_no_files)}): {', '.join(skipped_no_files)}")
    if not stmts:
        print("Nada para criar.")
        return 0

    print(f"Criando {len(stmts)//2} views novas...")
    duck("\n".join(stmts), readonly=False)
    print("OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
