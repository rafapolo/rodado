#!/usr/bin/env python3
"""docs/relatorio-social/perguntas.md -> tasks/douradas_multi.json

Python port of origin/ask-web's scripts/build_douradas_multi.ts (same source
doc, same filtering rule: a cited table not in the current catalog is
DISCARDED from the expectation, not silently kept, and a question left with
fewer than 2 valid tables stops being multi-table and is dropped).

    python3 scripts/build_douradas_multi.py
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "docs" / "relatorio-social" / "perguntas.md"
SCHEMA_PATH = REPO / "docs" / "context" / "basedosdados-schema.json"
OUT = REPO / "tasks" / "douradas_multi.json"

PATTERN = re.compile(r"\*\*(\d+)\.\s*(.+?)\*\*\s*\n\s*\n?\s*-\s*\*\*Fontes:\*\*\s*(.+?)(?:\n\n|\n#)", re.DOTALL)


def main():
    md = SRC.read_text(encoding="utf-8")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    catalogo = {f"{ds}.{tbl}" for ds, tables in schema.items() for tbl in tables}

    perguntas = []
    fantasmas = set()
    for m in PATTERN.finditer(md):
        n, texto, fontes = m.group(1), m.group(2), m.group(3)
        citadas = re.findall(r"`([\w.]+)`", fontes)
        validas = [t for t in citadas if t in catalogo]
        fantasmas.update(t for t in citadas if t not in catalogo)
        if len(validas) < 2:
            continue
        perguntas.append({
            "n": int(n),
            "q": re.sub(r"\s+", " ", texto).strip(),
            "tabelas": validas,
            "descartadas": (len(citadas) - len(validas)) or None,
            "datasets": sorted({t.split(".")[0] for t in validas}),
        })

    OUT.write_text(json.dumps({
        "_meta": {
            "origem": "docs/relatorio-social/perguntas.md",
            "sobre": ("Conjunto dourado MULTI-TABELA. Mede se a recuperação traz TODAS as "
                      "pontas de uma pergunta de pesquisa, e se o modelo escreve o JOIN."),
            "criterios": ["recall@k das tabelas esperadas", "SQL cita 2+ tabelas",
                          "SQL tem JOIN", "executa sem erro", "resultado não é vazio/nulo"],
        },
        "perguntas": perguntas,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print(f"{len(perguntas)} perguntas multi-tabela")
    if fantasmas:
        print(f"  {len(fantasmas)} tabela(s) citada(s) que não existem, descartadas:")
        for f in sorted(fantasmas):
            print(f"    {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
