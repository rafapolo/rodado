#!/usr/bin/env python3
"""metrics.yaml -> docs/context/metrics.json, para o `ask` (Rust) ler.

    python3 scripts/gera_metrics_json.py

O `ask` já depende de serde_json e não de YAML — e serde_yaml está
descontinuado. Converter aqui evita uma dependência nova no crate e mantém o
YAML como fonte única: rode isto depois de mexer em metrics.yaml.
"""
import json
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "docs" / "context" / "metrics.yaml"
DST = REPO / "docs" / "context" / "metrics.json"


def main():
    if not SRC.exists():
        sys.exit(f"{SRC} não encontrado.")
    metrics = yaml.safe_load(SRC.read_text(encoding="utf-8")).get("metrics", {})
    out = {
        "_meta": {"source": "docs/context/metrics.yaml", "count": len(metrics)},
        "metrics": [
            {
                "name": name,
                "description": m.get("description", ""),
                "unit": m.get("unit", ""),
                "grain": m.get("grain", []),
                "source_table": m.get("source_table", ""),
                "expression": m.get("expression", ""),
                "required_filters": m.get("required_filters", []),
                "synonyms": m.get("synonyms", []),
                "caveat": m.get("caveat", ""),
                "needs_join": m.get("needs_join"),
            }
            for name, m in sorted(metrics.items())
        ],
    }
    DST.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{DST.relative_to(REPO)} — {len(metrics)} métricas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
