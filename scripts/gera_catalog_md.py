#!/usr/bin/env python3
"""Export `_rodado_metadata/catalog.parquet` as `docs/catalog.md` — one row
per dataset (description, tables, rows, source), human-readable.

    python3 scripts/build_metadata_catalog.py  # -> catalog.parquet (+ description column)
    python3 scripts/gera_catalog_md.py         # catalog.parquet -> docs/catalog.md

Generated file — edit docs/context/dataset_descriptions.yaml instead, never
this output. See docs/housekeeping.md item 7: run this every time
catalog.parquet changes, not just when descriptions change.
"""

import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG = REPO_ROOT / "_rodado_metadata" / "catalog.parquet"
OUT = REPO_ROOT / "docs" / "catalog.md"


def fmt_int(n):
    return f"{n:,}".replace(",", ".")


def main():
    try:
        import pyarrow.parquet as pq
    except ImportError:
        sys.exit("pyarrow required: pip install pyarrow")

    if not CATALOG.exists():
        sys.exit(f"{CATALOG} not found — run build_metadata_catalog.py first")

    table = pq.read_table(CATALOG)
    rows = table.to_pylist()
    rows = [r for r in rows if r.get("source") != "view_only"]

    by_dataset = defaultdict(lambda: {"description": "", "source_name": "",
                                       "n_tables": 0, "rows": 0, "last_date": ""})
    for r in rows:
        d = by_dataset[r["dataset"]]
        d["description"] = r.get("description") or d["description"]
        d["source_name"] = r.get("source_name") or d["source_name"]
        d["n_tables"] += 1
        d["rows"] += r.get("rows") or 0
        ld = r.get("last_date") or ""
        if ld and ld > d["last_date"]:
            d["last_date"] = ld

    datasets = sorted(by_dataset.items())
    total_tables = sum(d["n_tables"] for _, d in datasets)
    total_rows = sum(d["rows"] for _, d in datasets)
    n_missing = sum(1 for _, d in datasets if not d["description"])
    n_freshness = sum(1 for _, d in datasets if d["last_date"])

    lines = [
        "# docs/catalog.md — catálogo de datasets",
        "",
        f"**Gerado por `scripts/gera_catalog_md.py`, a partir de "
        f"`_rodado_metadata/catalog.parquet` — não editar à mão.** "
        f"Descrições vêm de `docs/context/dataset_descriptions.yaml`; "
        f"a coluna Dado até vem de `docs/context/dataset_freshness.yaml` "
        f"(curado, só ~6 datasets por enquanto — vazio não significa "
        f"\"sem gap\", significa \"não conferido ainda\"). Editar os YAML "
        f"e regenerar (`build_metadata_catalog.py` → `gera_catalog_md.py`), "
        f"nunca este arquivo.",
        "",
        f"**{len(datasets)} datasets, {fmt_int(total_tables)} tabelas, "
        f"{fmt_int(total_rows)} linhas.**"
        + (f" {n_missing} dataset(s) sem descrição." if n_missing else "")
        + f" {n_freshness} com data de frescor conferida (de {len(datasets)}).",
        "",
        "| Dataset | Descrição | Tabelas | Linhas | Dado até | Fonte |",
        "|---|---|---:|---:|---|---|",
    ]
    for name, d in datasets:
        desc = d["description"] or "_(sem descrição)_"
        lines.append(
            f"| `{name}` | {desc} | {d['n_tables']} | {fmt_int(d['rows'])} | "
            f"{d['last_date'] or '—'} | {d['source_name']} |"
        )
    lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"{OUT.relative_to(REPO_ROOT)}")
    print(f"  {len(datasets)} datasets, {total_tables} tabelas, {total_rows:,} linhas")
    print(f"  {n_freshness} dataset(s) com data de frescor conferida")
    if n_missing:
        print(f"  {n_missing} dataset(s) sem descrição em "
              f"docs/context/dataset_descriptions.yaml")


if __name__ == "__main__":
    main()
