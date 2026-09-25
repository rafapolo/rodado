#!/usr/bin/env python3
"""schema_dict_status.json + uso real -> docs/context/schema_dict_prioridade.json

    python3 scripts/prioriza_schema_dict_status.py [--top 300]

Estágio 3 de tasks/generate-full-schema-dict.md: das colunas `nao_verificado`
(sem fonte de significado em lugar nenhum), quais estão no caminho de uma
pergunta real? Documentar coluna que ninguém consulta rende pouco; o estágio 4
(pesquisa manual) começa pelo topo desta lista.

Sinais, do mais forte ao mais fraco:

  sql      consultas SQL de verdade que citam a tabela E a coluna (palavra
           inteira). Três fontes, as três só locais (fora do git, toleradas
           ausentes num clone novo):
             - sessões do harness (`~/.rodado-harness/sessoes/*.jsonl`,
               chamadas `consultar` do Gemma);
             - transcrições do Claude Code neste projeto
               (`~/.claude/projects/<repo>/*.jsonl`):
               `mcp__rodado__run_sql` e comandos Bash que chamam duckdb;
             - o log do MCP (`logs/mcp_calls.jsonl`) não serve: guarda só
               nome da ferramenta e latência, sem argumento.
  docs     arquivos versionados que citam tabela e coluna: docs/pesquisa/,
           docs/context/*.yaml, scripts/hipoteses/, harness/, pages/analises/.
  desc     chamadas de describe_table/descrever_tabela na tabela (nível tabela).
  perg     vezes que o dataset aparece em docs/pesquisa/hipoteses/perguntas.md.
  linhas   tamanho da tabela (catálogo local `_rodado_metadata/catalog.parquet`).

Pontuação: 10*sql + 5*docs + 1*desc + 0,5*perg + 0,5*log10(linhas+1). O peso
é deliberadamente simples: o que importa é a ordem do topo, e o topo é
dominado por `sql`/`docs`, que são contagem de uso observado.
"""
import argparse
import json
import math
import re
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STATUS = REPO / "docs" / "context" / "schema_dict_status.json"
DST = REPO / "docs" / "context" / "schema_dict_prioridade.json"
CATALOG = REPO / "_rodado_metadata" / "catalog.parquet"
HARNESS_SESSIONS = Path.home() / ".rodado-harness" / "sessoes"
# o Claude Code guarda as transcrições em ~/.claude/projects/<caminho do repo com / trocado por ->
CLAUDE_TRANSCRIPTS = Path.home() / ".claude" / "projects" / str(REPO).replace("/", "-")
PERGUNTAS = REPO / "docs" / "pesquisa" / "hipoteses" / "perguntas.md"
DOC_GLOBS = [
    "docs/pesquisa/**/*.md", "docs/pesquisa/**/*.sql",
    "docs/context/bridges.yaml", "docs/context/metrics.yaml",
    "docs/context/hierarchies.yaml", "docs/context/moldes.yaml",
    "scripts/hipoteses/*.sql", "scripts/hipoteses/*.py",
    "harness/*.ts", "harness/dados/*.tsv", "pages/analises/**/*.md",
]


def harness_calls():
    """(sqls, described_tables) das sessões do harness."""
    sqls, desc = [], []
    if not HARNESS_SESSIONS.exists():
        return sqls, desc
    for f in HARNESS_SESSIONS.glob("*.jsonl"):
        for line in f.open(encoding="utf-8", errors="replace"):
            try:
                o = json.loads(line)
            except ValueError:
                continue
            content = (o.get("message") or {}).get("content")
            if not isinstance(content, list):
                continue
            for b in content:
                if not isinstance(b, dict) or b.get("type") != "toolCall":
                    continue
                args = b.get("arguments") or {}
                if b.get("name") == "consultar":
                    sqls.append(json.dumps(args, ensure_ascii=False))
                elif b.get("name") == "descrever_tabela":
                    desc.append(str(args.get("tabela") or args.get("table") or args))
    return sqls, desc


def claude_calls():
    """(sqls, described_tables) das transcrições do Claude Code no projeto."""
    sqls, desc = [], []
    if not CLAUDE_TRANSCRIPTS.exists():
        return sqls, desc
    for f in CLAUDE_TRANSCRIPTS.glob("*.jsonl"):
        for line in f.open(encoding="utf-8", errors="replace"):
            if '"tool_use"' not in line:
                continue
            try:
                o = json.loads(line)
            except ValueError:
                continue
            content = (o.get("message") or {}).get("content")
            if not isinstance(content, list):
                continue
            for b in content:
                if not isinstance(b, dict) or b.get("type") != "tool_use":
                    continue
                name, inp = b.get("name", ""), b.get("input") or {}
                if name.endswith("run_sql"):
                    sqls.append(str(inp.get("sql", "")))
                elif name.endswith("describe_table"):
                    desc.append(str(inp.get("table", "")))
                elif name == "Bash" and "duckdb" in str(inp.get("command", "")):
                    sqls.append(str(inp.get("command", "")))
    return sqls, desc


def table_refs(tid: str) -> list[str]:
    ds, tb = tid.split(".", 1)
    return [f"{ds}.{tb}".lower(), f"{ds}/{tb}".lower()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=300)
    args = ap.parse_args()

    columns = json.loads(STATUS.read_text())["columns"]
    by_table = defaultdict(list)
    for key, info in columns.items():
        if info.get("label") == "nao_verificado":
            tid, _, col = key.rpartition(".")
            by_table[tid].append(col)

    h_sql, h_desc = harness_calls()
    c_sql, c_desc = claude_calls()
    sqls = [s.lower() for s in h_sql + c_sql]
    descs = [d.lower() for d in h_desc + c_desc]

    docs = []
    for g in DOC_GLOBS:
        for p in REPO.glob(g):
            if p.is_file():
                docs.append(p.read_text(encoding="utf-8", errors="replace").lower())

    perg_text = PERGUNTAS.read_text().lower() if PERGUNTAS.exists() else ""

    rows = {}
    if CATALOG.exists():
        import polars as pl
        for r in pl.read_parquet(CATALOG).select(["dataset", "table", "rows"]).iter_rows():
            rows[f"{r[0]}.{r[1]}"] = r[2] or 0

    ranked = []
    for tid, cols in by_table.items():
        refs = table_refs(tid)
        t_sqls = [s for s in sqls if any(r in s for r in refs)]
        t_docs = [d for d in docs if any(r in d for r in refs)]
        n_desc = sum(1 for d in descs if tid.lower() in d)
        ds = tid.split(".")[0]
        n_perg = perg_text.count(ds.lower())
        n_rows = rows.get(tid, 0)
        for col in cols:
            pat = re.compile(r"(?<![a-z0-9_])" + re.escape(col.lower()) + r"(?![a-z0-9_])")
            n_sql = sum(1 for s in t_sqls if pat.search(s))
            n_docs = sum(1 for d in t_docs if pat.search(d))
            score = 10 * n_sql + 5 * n_docs + n_desc + 0.5 * n_perg + 0.5 * math.log10(n_rows + 1)
            ranked.append({
                "coluna": f"{tid}.{col}", "score": round(score, 2),
                "sql": n_sql, "docs": n_docs, "desc": n_desc,
                "perg": n_perg, "linhas": n_rows,
                "reason": columns[f"{tid}.{col}"].get("reason", ""),
            })

    ranked.sort(key=lambda r: (-r["score"], r["coluna"]))
    used = [r for r in ranked if r["sql"] or r["docs"]]
    out = {
        "_meta": {
            "generated_by": "scripts/prioriza_schema_dict_status.py",
            "fonte": "docs/context/schema_dict_status.json (label nao_verificado)",
            "sinais": {
                "consultas_sql_lidas": len(sqls),
                "harness_consultar": len(h_sql),
                "claude_run_sql_ou_bash_duckdb": len(c_sql),
                "describe_table_lidos": len(descs),
                "docs_versionados_lidos": len(docs),
            },
            "nao_verificado_total": len(ranked),
            "com_uso_observado_sql_ou_docs": len(used),
            "com_uso_em_sql": sum(1 for r in ranked if r["sql"]),
            "formula": "10*sql + 5*docs + 1*desc + 0.5*perg + 0.5*log10(linhas+1)",
            "top": args.top,
        },
        "ranking": ranked[: args.top],
    }
    DST.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(out["_meta"], ensure_ascii=False, indent=1))
    for r in ranked[:60]:
        print(f'{r["score"]:7.2f} sql={r["sql"]:3d} docs={r["docs"]:2d} desc={r["desc"]:3d} {r["coluna"]}')


if __name__ == "__main__":
    main()
