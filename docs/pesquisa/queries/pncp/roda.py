#!/usr/bin/env python3
"""Roda cada bloco "-- arquivo: x.csv" de consultas.sql no beelink (só leitura) e grava o CSV aqui."""
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sql = (AQUI / "consultas.sql").read_text()
blocos = re.split(r"^-- arquivo: (\S+\.csv).*$", sql, flags=re.M)[1:]
so = set(sys.argv[1:])
for nome, corpo in zip(blocos[::2], blocos[1::2]):
    if so and nome not in so:
        continue
    r = subprocess.run(["ssh", "beelink", "ulimit -n 65536; ~/bin/duckdb -readonly -csv ~/rodado/basedosdados.duckdb"],
                       input="SET enable_progress_bar=false;\n.output /dev/null\nSELECT 1;\n.output\n" + corpo,
                       capture_output=True, text=True)
    linhas = [l for l in r.stdout.splitlines() if not l.startswith("\x1b") and "Loading resources" not in l]
    if r.returncode != 0 or "Error" in r.stderr:
        sys.exit(f"{nome}: {r.stderr[-500:]}")
    (AQUI / nome).write_text("\n".join(linhas) + "\n")
    print(f"{nome}: {len(linhas) - 1} linhas")
