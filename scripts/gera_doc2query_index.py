#!/usr/bin/env python3
"""docs/context/doc2query_corpus.jsonl -> docs/context/doc2query_index.json + .npy

    python3 scripts/gera_doc2query_index.py

Embeds every doc2query question (one row = one table's one synthetic
question) with MODEL_NAME below — override with MCP_EMBEDDING_MODEL to match
mcp_server.py's own override env var if you re-embed with a different model.
`search_tables` scores a table by the MAX cosine similarity across its
questions, so one vector per question (not one per table) is the point.

Two files, not one, because the vectors are the expensive/bulky part:
  * doc2query_index.json — id/table/text per row, in the .npy's row order
  * doc2query_vectors.npy — float32 (n_questions, dim) array, same order

The LLM-generation step (tasks/doc2query/*.jsonl via scripts/doc2query_lotes.py
+ scripts/doc2query_roda.py, combined into the corpus by
scripts/gera_doc2query_corpus.py) is the expensive, one-time part — a bank of
opencode calls, not something to rerun casually. Its raw batches live under
tasks/, which is gitignored — the corpus itself lives in docs/context/
instead precisely so it doesn't get lost the way the ask-web project's
version of it did (see tasks/done/mcp_search_refino.md item 1). This script is
the cheap, freely-rerunnable half: change embedding model or re-embed after
editing the corpus by hand, and just run this again.
"""
import json
import os
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
CORPUS_PATH = REPO / "docs" / "context" / "doc2query_corpus.jsonl"
OUT_META = REPO / "docs" / "context" / "doc2query_index.json"
OUT_VECTORS = REPO / "docs" / "context" / "doc2query_vectors.npy"
MODEL_NAME = os.environ.get("MCP_EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")


def main():
    if not CORPUS_PATH.exists():
        sys.exit(f"{CORPUS_PATH} não encontrado — rode scripts/gera_doc2query_corpus.py primeiro.")

    rows = [json.loads(l) for l in CORPUS_PATH.read_text(encoding="utf-8").strip().split("\n")]
    model_name = MODEL_NAME
    print(f"{len(rows)} perguntas, modelo {model_name}")

    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    texts = [r["text"] for r in rows]
    vectors = model.encode(texts, show_progress_bar=True, convert_to_numpy=True).astype("float32")

    tables = sorted({r["table"] for r in rows})
    OUT_VECTORS.parent.mkdir(parents=True, exist_ok=True)
    np.save(OUT_VECTORS, vectors)

    meta = {
        "_meta": {
            "source": "docs/context/doc2query_corpus.jsonl",
            "generated_by": "scripts/gera_doc2query_index.py",
            "model": model_name,
            "n_questions": len(rows),
            "n_tables": len(tables),
            "vectors_file": OUT_VECTORS.name,
            "note": (
                "rows[i] describes doc2query_vectors.npy row i. search_tables "
                "scores a table by the MAX cosine similarity across its rows, "
                "not the mean — mean-pooling was tried and measured worse."
            ),
        },
        "rows": [{"id": r["id"], "table": r["table"], "text": r["text"]} for r in rows],
    }
    OUT_META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"{OUT_META.relative_to(REPO)} — {len(tables)} tabelas, {len(rows)} perguntas")
    print(f"{OUT_VECTORS.relative_to(REPO)} — shape {vectors.shape}, "
          f"{OUT_VECTORS.stat().st_size / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
