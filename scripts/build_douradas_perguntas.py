#!/usr/bin/env python3
"""docs/perguntas.md + docs/respostas.md -> tasks/douradas_perguntas.json

    python3 scripts/build_douradas_perguntas.py

docs/perguntas.md is dataset-level (43 themes x 5 questions, each citing
`n=3+` datasets, `*` marking a supporting/reference dataset rather than a
required one) — a separate, larger source than docs/relatorio-social/
perguntas.md (already used by build_douradas_multi.py for
tasks/douradas_multi.json). This script does NOT touch that file or its
output; it adds a second, independent golden set alongside it.

The key move: docs/respostas.md marks every `T<tema>-<item>` code with a
status — [OK] respondida (query actually run on beelink), [PARTIAL] parcial,
or [PENDING] pendente (not yet run, and often the entry itself says WHY the
originally-cited dataset doesn't actually work — corrupted columns, missing
fields, no shared key). Keeping [PENDING] items would poison the golden set
with dataset citations that were never verified to work. Only [OK]/[PARTIAL]
items go in, matching this project's own "verified is not decoration"
principle (see CLAUDE.md, docs/context/bridges.yaml).

Cited dataset names are resolved against the current schema by trying a
`br_` prefix first (world_/us_ names already carry their own prefix), then a
normalized (underscore-insensitive) match; anything left unresolved is
reported, not guessed.
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PERGUNTAS = REPO / "docs" / "perguntas.md"
RESPOSTAS = REPO / "docs" / "respostas.md"
SCHEMA_PATH = REPO / "docs" / "context" / "basedosdados-schema.json"
OUT = REPO / "tasks" / "douradas_perguntas.json"

STATUS_MAP = {"✅": "ok", "◐": "partial", "⏳": "pending", "❌": "no_answer"}
KEEP_STATUS = {"ok", "partial"}

THEME_RE = re.compile(r"^## (\d+) · ")
ITEM_RE = re.compile(r"^(\d+)\.\s+(.+?)\s+\*\(n=\d+\+?:\s*(.+?)\)\*\s*$")
MULTI_ITEM_RE = re.compile(r"^(\d+)\.\s+\*\*(.+?)\*\*:\s+(.+?)\s+\*\(n=\d+[+–-]*:\s*(.+?)\)\*\s*$")


def parse_perguntas():
    """(tema:int|'M', item:int) -> {"q": str, "datasets": [(name, is_ref)]}"""
    out = {}
    tema = None
    in_multi = False
    for line in PERGUNTAS.read_text(encoding="utf-8").splitlines():
        if line.startswith("# Perguntas multi-dataset"):
            in_multi = True
            tema = "M"
            continue
        m = THEME_RE.match(line)
        if m:
            tema = int(m.group(1))
            continue
        if tema is None:
            continue
        if in_multi:
            m = MULTI_ITEM_RE.match(line)
            if not m:
                continue
            item, _label, texto, citacao = m.groups()
        else:
            m = ITEM_RE.match(line)
            if not m:
                continue
            item, texto, citacao = m.groups()
        # citacao like: "me_rais, ms_sim, ibge_censo_2022\*" or "... ; chaves: ..."
        citacao = citacao.split(";")[0]
        datasets = []
        for tok in citacao.split(","):
            tok = tok.strip()
            is_ref = tok.endswith("\\*") or tok.endswith("*")
            name = tok.rstrip("*").rstrip("\\").strip()
            if name:
                datasets.append((name, is_ref))
        out[(tema, int(item))] = {"q": texto.strip(), "datasets": datasets}
    return out


CODE_RE = re.compile(r"T(\d+)-(\w+)|M(\d+)")


def expand_codes(span: str):
    """One bold span's worth of codes -> [(tema, item), ...], numeric items only."""
    codes = []
    for part in span.split("/"):
        part = part.strip()
        rng = re.match(r"T(\d+)-(\d+)\s*…\s*T(\d+)-(\d+)$", part)
        if rng:
            t1, i1, t2, i2 = map(int, rng.groups())
            if t1 == t2:
                codes.extend((t1, i) for i in range(i1, i2 + 1))
            continue
        # comma list sharing a trailing status, e.g. "T07-1, T07-3, T07-4, T07-5"
        for m in re.finditer(r"T(\d+)-(\w+)|M(\d+)", part):
            if m.group(3):
                codes.append(("M", int(m.group(3))))
                continue
            tema, item = int(m.group(1)), m.group(2)
            if item.isdigit():
                codes.append((tema, int(item)))
    return codes


BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


def parse_respostas():
    """(tema, item) -> status ('ok'/'partial'/'pending'), last one wins."""
    status = {}
    for bold in BOLD_RE.findall(RESPOSTAS.read_text(encoding="utf-8")):
        if not re.search(r"[✅◐⏳❌]", bold):
            continue
        if "T" not in bold and "M" not in bold:
            continue
        # split on status glyphs, keep each glyph paired with the codes before it
        pieces = re.split(r"([✅◐⏳❌])", bold)
        buf = ""
        for piece in pieces:
            if piece in STATUS_MAP:
                for code in expand_codes(buf):
                    status[code] = STATUS_MAP[piece]
                buf = ""
            else:
                buf += piece
    return status


def resolve(name: str, datasets: set):
    if name in datasets:
        return name
    cand = f"br_{name}"
    if cand in datasets:
        return cand
    norm = lambda s: s.replace("_", "")
    n_target = norm(name)
    for pref in ("br_", "world_", "us_", ""):
        for ds in datasets:
            if ds.startswith(pref) and norm(ds[len(pref):]) == n_target:
                return ds
    return None


def main():
    if not PERGUNTAS.exists() or not RESPOSTAS.exists():
        sys.exit(f"{PERGUNTAS} / {RESPOSTAS} não encontrados.")

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    known_datasets = set(schema.keys())

    perguntas = parse_perguntas()
    status = parse_respostas()

    entries = []
    unresolved = set()
    skipped_no_status = 0
    skipped_too_few = 0

    for (tema, item), info in perguntas.items():
        st = status.get((tema, item))
        if st is None:
            skipped_no_status += 1
            continue
        if st not in KEEP_STATUS:
            continue
        required, supporting = [], []
        for name, is_ref in info["datasets"]:
            ds = resolve(name, known_datasets)
            if ds is None:
                unresolved.add(name)
                continue
            (supporting if is_ref else required).append(ds)
        if len(required) + len(supporting) < 2:
            skipped_too_few += 1
            continue
        entries.append({
            "code": f"T{tema:02d}-{item}" if tema != "M" else f"M{item}",
            "q": info["q"],
            "status": st,
            "required_datasets": required,
            "supporting_datasets": supporting,
        })

    entries.sort(key=lambda e: e["code"])
    OUT.write_text(json.dumps({
        "_meta": {
            "origem": ["docs/perguntas.md", "docs/respostas.md"],
            "sobre": ("Conjunto dourado DATASET-level (nao table-level), restrito a perguntas "
                      "com status verificado (ok/partial) em respostas.md — perguntas pendentes "
                      "sao descartadas porque varias delas documentam explicitamente que o "
                      "dataset citado nao funciona no espelho atual."),
            "criterios": ["search_tables no top-K deve trazer >=1 tabela de cada required_dataset",
                          "supporting_datasets (marcados com * em perguntas.md) sao bonus, nao obrigatorios"],
            "n": len(entries),
        },
        "perguntas": entries,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print(f"{len(entries)} perguntas mantidas (status ok/partial, >=2 datasets resolvidos)")
    print(f"  {skipped_no_status} sem status em respostas.md (codigo nao encontrado/nao numerico)")
    print(f"  {skipped_too_few} descartadas por sobrar <2 datasets apos resolucao")
    if unresolved:
        print(f"  {len(unresolved)} nome(s) de dataset nao resolvido(s):")
        for u in sorted(unresolved):
            print(f"    {u}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
