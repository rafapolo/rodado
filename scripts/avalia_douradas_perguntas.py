#!/usr/bin/env python3
"""Sanity-check search_tables against tasks/douradas_perguntas.json.

Dataset-level, not table-level (see build_douradas_perguntas.py): a "hit" is
search_tables returning ANY table from a required dataset in the top-K, not
one specific table. supporting_datasets (the `*`-marked ones in
docs/perguntas.md) are reported separately and don't count against recall —
they were never claimed as required.

    python3 scripts/avalia_douradas_perguntas.py [--top-k 10]
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

    data = json.loads((REPO / "tasks" / "douradas_perguntas.json").read_text(encoding="utf-8"))
    perguntas = data["perguntas"]

    total_required, hit_required = 0, 0
    any_hit, all_hit = 0, 0
    misses = []

    for p in perguntas:
        r = m.search_tables(p["q"], top_k=args.top_k, min_similarity=0.0)
        got_datasets = {x["table"].split(".", 1)[0] for x in r["results"]}
        required = set(p["required_datasets"])
        hits = required & got_datasets
        total_required += len(required)
        hit_required += len(hits)
        if hits:
            any_hit += 1
        if hits == required:
            all_hit += 1
        else:
            misses.append((p["code"], p["q"][:70], sorted(required - hits)))

    n = len(perguntas)
    print(f"{n} perguntas (status ok/partial), top_k={args.top_k}")
    print(f"  datasets: {hit_required}/{total_required} recuperados ({hit_required/total_required:.1%})")
    print(f"  perguntas com >=1 dataset esperado no top-{args.top_k}: {any_hit}/{n} ({any_hit/n:.1%})")
    print(f"  perguntas com TODOS os datasets esperados no top-{args.top_k}: {all_hit}/{n} ({all_hit/n:.1%})")
    print(f"\n{len(misses)} pergunta(s) com pelo menos um dataset ausente:")
    for code, q, datasets in misses[:15]:
        print(f"  {code} {q}... faltou: {datasets}")
    if len(misses) > 15:
        print(f"  … e mais {len(misses) - 15}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
