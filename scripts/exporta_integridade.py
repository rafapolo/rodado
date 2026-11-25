#!/usr/bin/env python3
"""Traz do beelink o último hash lógico de cada tabela para docs/integridade/{hashes,particoes}.csv.

O cálculo roda no beelink (hash_logico.py, só local); aqui só se lê ~/rodado/_integridade/*.jsonl e
grava os CSVs ordenados, para o git guardar o histórico de cada hash. Especificação em
docs/integridade/README.md.
"""
import csv
import json
import subprocess
from pathlib import Path

# schemas internos (cópias locais, logs de auditoria) não vão para o repositório
PRIVADOS = ("_", "logs.")
DEST = Path(__file__).resolve().parent.parent / "docs" / "integridade"


def le(nome):
    r = subprocess.run(["ssh", "beelink", f"cat ~/rodado/_integridade/{nome}"], capture_output=True, text=True, check=True)
    return [json.loads(l) for l in r.stdout.splitlines() if l.strip()]


def main():
    ult = {}
    for r in le("hashes.jsonl"):
        if r["tabela"].startswith(PRIVADOS):
            continue
        ult[r["tabela"]] = r   # a última linha de cada tabela vale
    with open(DEST / "hashes.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["tabela", "linhas", "hash", "calculado_em"])
        for t in sorted(ult):
            r = ult[t]
            w.writerow([t, r["linhas"], r["hash"], r["calculado_em"][:10]])
    ultp = {}
    for r in le("particoes.jsonl"):
        if not r["tabela"].startswith(PRIVADOS) and ult.get(r["tabela"], {}).get("calculado_em") == r["calculado_em"]:
            ultp[(r["tabela"], str(r["ano"]))] = r
    with open(DEST / "particoes.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["tabela", "ano", "linhas", "hash"])
        for k in sorted(ultp):
            r = ultp[k]
            w.writerow([r["tabela"], r["ano"], r["linhas"], r["hash"]])
    print(f"{len(ult)} tabelas, {len(ultp)} partições -> {DEST}")


if __name__ == "__main__":
    main()
