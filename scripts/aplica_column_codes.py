#!/usr/bin/env python3
"""docs/context/column_codes.yaml -> docs/context/schema_dict_status.json

    python3 scripts/aplica_column_codes.py

Estágio 4 de tasks/done/generate-full-schema-dict.md. `column_codes.yaml` é escrito à
mão (pesquisa com fonte oficial + medição no beelink); este script só propaga
o `status` de cada coluna para a etiqueta de `schema_dict_status.json`, que é o
que `describe_table` usa para montar o `nao_verificado_warning`:

    documentado     -> documentado_em_outro_lugar
    padrao_externo  -> padrao_externo
    nao_e_codigo    -> nao_e_codigo
    pendente        -> fica nao_verificado, com a nota anexada ao reason

Roda DEPOIS de gera_schema_dict_status.py e llm_triage_schema_dict_status.py —
os dois reescrevem o arquivo e apagariam esta passada. Idempotente.
Coluna do YAML ausente do status (tipo fora do escopo do estágio 1, nome
errado) é listada no fim e não interrompe: o YAML vale para describe_table
mesmo assim.
"""
import json
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "docs" / "context" / "column_codes.yaml"
DST = REPO / "docs" / "context" / "schema_dict_status.json"

LABEL = {
    "documentado": "documentado_em_outro_lugar",
    "padrao_externo": "padrao_externo",
    "nao_e_codigo": "nao_e_codigo",
    "pendente": "nao_verificado",
}


def main():
    spec = yaml.safe_load(SRC.read_text())
    fontes = spec.get("fontes", {})
    status = json.loads(DST.read_text())
    columns = status["columns"]

    changed, missing = 0, []
    for e in spec["entradas"]:
        st = e["status"]
        if st not in LABEL:
            raise SystemExit(f"status desconhecido {st!r} em {e['tabela']}")
        fonte = fontes.get(e.get("fonte", ""), {})
        for col in e["colunas"]:
            key = f"{e['tabela']}.{col}"
            if key not in columns:
                missing.append(key)
                continue
            if st == "pendente":
                reason = f"column_codes.yaml (pendente): {e.get('nota', '')}"
            else:
                what = e.get("significado") or e.get("verificado", "")
                src = f" — fonte: {fonte['url']}" if fonte.get("url") else ""
                reason = f"column_codes.yaml ({st}): {what}{src}"
            new = {"label": LABEL[st], "reason": reason, "column_codes": True}
            if columns[key] != new:
                columns[key] = new
                changed += 1

    counts: dict = {}
    for info in columns.values():
        counts[info["label"]] = counts.get(info["label"], 0) + 1
    meta = status.setdefault("_meta", {})
    meta["counts_by_label"] = dict(sorted(counts.items()))
    meta["column_codes"] = {
        "applied_by": "scripts/aplica_column_codes.py",
        "source": "docs/context/column_codes.yaml",
        "columns": sum(len(e["colunas"]) for e in spec["entradas"]) - len(missing),
    }
    DST.write_text(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{changed} colunas mudaram; contagem: {meta['counts_by_label']}")
    if missing:
        print(f"{len(missing)} colunas do YAML fora de schema_dict_status.json:")
        for k in missing:
            print("  ", k)


if __name__ == "__main__":
    main()
