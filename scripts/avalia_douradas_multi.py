#!/usr/bin/env python3
"""Sanity-check search_tables against tasks/douradas_multi.json.

Not a clean single-table golden set (each question expects 2-4 tables at
once, and search_tables scores one table per query) — this is a broader
signal, not a strict recall@5 target. For each question, checks what
fraction of its expected tables appear in the top-K search_tables results.

    python3 scripts/avalia_douradas_multi.py [--top-k 10]
"""
import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
import mcp_server as m  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top-k", type=int, default=10)
    args = ap.parse_args()

    data = json.loads((REPO / "tasks" / "douradas_multi.json").read_text(encoding="utf-8"))
    perguntas = data["perguntas"]

    total_tables, hit_tables = 0, 0
    any_hit, all_hit = 0, 0
    misses = []

    for p in perguntas:
        r = m.search_tables(p["q"], top_k=args.top_k, min_similarity=0.0)
        got = {x["table"] for x in r["results"]}
        expected = set(p["tabelas"])
        hits = expected & got
        total_tables += len(expected)
        hit_tables += len(hits)
        if hits:
            any_hit += 1
        if hits == expected:
            all_hit += 1
        else:
            misses.append((p["n"], p["q"][:70], sorted(expected - hits)))

    n = len(perguntas)
    print(f"{n} perguntas, top_k={args.top_k}")
    print(f"  tabelas: {hit_tables}/{total_tables} recuperadas ({hit_tables/total_tables:.1%})")
    print(f"  perguntas com >=1 tabela esperada no top-{args.top_k}: {any_hit}/{n} ({any_hit/n:.1%})")
    print(f"  perguntas com TODAS as tabelas esperadas no top-{args.top_k}: {all_hit}/{n} ({all_hit/n:.1%})")
    print(f"\n{len(misses)} pergunta(s) com pelo menos uma tabela ausente:")
    for n_, q, tables in misses[:15]:
        print(f"  #{n_} {q}... faltou: {tables}")
    if len(misses) > 15:
        print(f"  … e mais {len(misses) - 15}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
