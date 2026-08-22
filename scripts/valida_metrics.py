#!/usr/bin/env python3
"""Valida docs/context/metrics.yaml e docs/context/hierarchies.yaml.

    python3 scripts/valida_metrics.py

A separação hard/soft é deliberada, e é a mesma do SQL firewall que já existe:
`mcp_server._check_read_only` revalida toda query antes de executar, então criar
uma métrica pode ser permissivo sem perder segurança. Bloquear aqui o que o
serve-time já barra só rejeitaria expressão válida-porém-incomum.

  HARD (exit 1)  DML/DDL na expressão; source_table ausente do schema quando o
                 schema foi lido com sucesso (ausência provável, não presumida)
  SOFT (aviso)   coluna que não aparece no schema; falta de `verified`;
                 sinônimo repetido entre métricas

Sem schema legível, a checagem de tabela falha fechado: não dá para provar
ausência, então nada é rejeitado por ela.
"""
import json
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
CONTEXT = REPO / "docs" / "context"
SCHEMA = CONTEXT / "basedosdados-schema.json"

DML = ("INSERT", "UPDATE", "DELETE", "DROP", "TRUNCATE", "GRANT", "REVOKE",
       "CREATE", "ALTER", "ATTACH", "COPY", "CALL", "INSTALL", "LOAD",
       "REPLACE", "MERGE", "EXPORT", "IMPORT", "VACUUM", "PRAGMA")


def load_schema():
    if not SCHEMA.exists():
        return None
    with SCHEMA.open(encoding="utf-8") as fh:
        return json.load(fh)


def columns_of(schema, table_id):
    ds, _, tbl = table_id.partition(".")
    cols = schema.get(ds, {}).get(tbl)
    return None if cols is None else {c["name"].lower() for c in cols}


def check_metrics(doc, schema):
    hard, soft = [], []
    seen_syn = {}
    for name, m in doc.get("metrics", {}).items():
        expr = m.get("expression", "")

        upper = expr.upper()
        for kw in DML:
            if re.search(rf"\b{kw}\b", upper):
                hard.append(f"{name}: expressão contém `{kw}` — métrica é leitura, sempre")

        table = m.get("source_table", "")
        if schema is not None and table:
            cols = columns_of(schema, table)
            if cols is None:
                hard.append(f"{name}: source_table `{table}` não existe no schema")
            else:
                referenced = set(re.findall(r"\b[a-z_][a-z0-9_]*\b", expr.lower()))
                sqlish = {"sum", "count", "avg", "min", "max", "filter", "where",
                          "nullif", "cast", "as", "distinct", "and", "or", "not", "null"}
                for col in referenced - sqlish - cols:
                    if col.isdigit() or len(col) < 3:
                        continue
                    soft.append(f"{name}: coluna `{col}` não está em {table} "
                                f"(pode vir do needs_join)")

        for field in ("description", "unit", "grain", "required_filters", "synonyms"):
            if not m.get(field):
                soft.append(f"{name}: sem `{field}`")
        if not m.get("verified"):
            soft.append(f"{name}: sem `verified` — a métrica é aspiracional até "
                        f"alguém conferir o número no beelink")

        for syn in m.get("synonyms", []):
            key = syn.lower().strip()
            if key in seen_syn:
                soft.append(f"{name}: sinônimo '{syn}' já é de {seen_syn[key]} — "
                            f"match exato fica ambíguo")
            seen_syn[key] = name
    return hard, soft


def check_hierarchies(doc, schema):
    hard, soft = [], []
    for name, h in doc.get("hierarchies", {}).items():
        table = h.get("table", "")
        cols = columns_of(schema, table) if schema and table else None
        if schema is not None and table and cols is None:
            hard.append(f"{name}: table `{table}` não existe no schema")
            continue
        for level in h.get("levels", []):
            if cols is not None and level.lower() not in cols:
                soft.append(f"{name}: nível `{level}` não é coluna de {table}")
        for edge, p in h.get("parents", {}).items():
            if not p.get("verified"):
                soft.append(f"{name}: `{edge}` sem `verified`")
    return hard, soft


def main():
    schema = load_schema()
    if schema is None:
        print("! schema não encontrado — checagem de tabela/coluna desativada",
              file=sys.stderr)

    hard, soft = [], []
    for path, checker in ((CONTEXT / "metrics.yaml", check_metrics),
                          (CONTEXT / "hierarchies.yaml", check_hierarchies)):
        if not path.exists():
            hard.append(f"{path.name} não existe")
            continue
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        h, s = checker(doc, schema)
        hard += h
        soft += s

    for msg in soft:
        print(f"  aviso  {msg}")
    for msg in hard:
        print(f"  ERRO   {msg}", file=sys.stderr)

    print(f"\n{len(hard)} erro(s), {len(soft)} aviso(s)")
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
