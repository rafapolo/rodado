#!/usr/bin/env python3
"""Combine tasks/doc2query/saida_*.jsonl (the doc2query LLM output batches)
into one corpus, re-validated, for embedding.

    python3 scripts/gera_doc2query_corpus.py   # -> docs/context/doc2query_corpus.jsonl

Re-validates every batch independently of whatever runner produced it
(generation for this run was split across beelink and a local laptop run,
so this is the single trust boundary before anything gets embedded).

The raw lote_*/saida_* batches stay under tasks/ (gitignored — they're bulky
intermediate files); the combined corpus is written to docs/context/ instead,
which is NOT gitignored, so it survives the way the ask-web project's
equivalent artifact didn't (see tasks/mcp_search_refino.md item 1).
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DIR = REPO / "tasks" / "doc2query"
OUT = REPO / "docs" / "context" / "doc2query_corpus.jsonl"

ESTRUTURAIS = {"nome_coluna", "id_tabela", "cobertura_temporal"}
PERGUNTAS_ESPERADAS = 8


def validar(lote_path: Path, saida_path: Path):
    erros = []
    entrada = [json.loads(l) for l in lote_path.read_text(encoding="utf-8").strip().split("\n")]
    esperados = {e["id"]: [c.lower() for c in e["colunas"]] for e in entrada}

    lines = [l for l in saida_path.read_text(encoding="utf-8").strip().split("\n")
             if l.strip() and not l.strip().startswith("```")]
    saidas = [json.loads(l) for l in lines]

    vistos = set()
    corpus_rows = []
    for s in saidas:
        sid = s.get("id")
        if sid not in esperados:
            erros.append(f"id fora do lote: {sid}")
            continue
        if sid in vistos:
            erros.append(f"id repetido: {sid}")
        vistos.add(sid)

        cols = esperados[sid]
        perguntas = s.get("perguntas")
        if not isinstance(perguntas, list) or len(perguntas) == 0:
            erros.append(f"{sid}: sem perguntas")
            continue
        if not s.get("incerta") and len(perguntas) != PERGUNTAS_ESPERADAS:
            erros.append(f"{sid}: {len(perguntas)} perguntas, esperado {PERGUNTAS_ESPERADAS}")

        eh_dicionario = sid.endswith(".dicionario")
        for i, q in enumerate(perguntas):
            if not isinstance(q, str) or len(q) < 8:
                erros.append(f"{sid}: pergunta curta demais: {q!r}")
                continue
            if len(q.split()) > 20:
                erros.append(f"{sid}: pergunta longa demais: {q[:50]!r}…")
            ql = q.lower()
            eco = next((c for c in cols if "_" in c and c in ql
                        and not (eh_dicionario and c in ESTRUTURAIS)), None)
            if eco:
                erros.append(f"{sid}: ecoa nome de coluna {eco!r} em {q[:46]!r}…")
            corpus_rows.append({"id": f"{sid}.q{i+1}", "table": sid, "text": q})

    for eid in esperados:
        if eid not in vistos:
            erros.append(f"faltou: {eid}")

    return erros, corpus_rows


def main():
    lote_files = sorted(p for p in DIR.glob("lote_*.jsonl") if "amostra" not in p.stem)
    all_rows = []
    all_errors = []
    tables_seen = set()

    for lote_path in lote_files:
        n = lote_path.stem.replace("lote_", "")
        saida_path = DIR / f"saida_{n}.jsonl"
        if not saida_path.exists():
            all_errors.append(f"lote {n}: saída ausente")
            continue
        erros, rows = validar(lote_path, saida_path)
        if erros:
            all_errors.append(f"lote {n}: {len(erros)} erro(s) — {erros[0]}")
            continue
        all_rows.extend(rows)
        tables_seen.update(r["table"] for r in rows)

    if all_errors:
        print(f"{len(all_errors)} lote(s) com problema:")
        for e in all_errors:
            print(f"  {e}")
        sys.exit(1)

    OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in all_rows) + "\n", encoding="utf-8")
    print(f"{OUT.relative_to(REPO)} — {len(tables_seen)} tabelas, {len(all_rows)} perguntas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
