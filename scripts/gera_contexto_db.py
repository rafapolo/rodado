#!/usr/bin/env python3
"""Empacota a camada semântica de docs/context/ para o db.rodado.xyz: db/contexto.json.

O container do db.rodado.xyz só leva o que está em db/ (ver db/Dockerfile), e os YAML
inteiros estouram o contexto de um agente (join_keys.md tem 319 KB). Este script lê só o
que é público e escrito à mão — gotchas/*.yml, column_codes.yaml, bridges.yaml,
metrics.yaml, hierarchies.yaml —, as notas de coluna do harness (harness/dados/notas.json, lido
do branch harness-gemma quando ele existe), as respostas conferidas e as perguntas diretas de
treino (os holdouts ficam de fora: são a régua de scripts/avalia_agente_cego.py), mais o tema de
cada dataset do atlas, e grava já fatiado
por dataset: consulta.py serve /contexto?dataset=X com a fatia, nunca o arquivo todo.
docs/context/privado/ e tasks/ nunca entram.

Rodar depois de editar qualquer um desses arquivos ou de regerar o atlas:

    python3 scripts/gera_contexto_db.py
"""
import datetime
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
CTX = RAIZ / "docs" / "context"
SAIDA = RAIZ / "db" / "contexto.json"


def _texto(v):
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.isoformat()
    raise TypeError(type(v).__name__)


def _datasets_do_padrao(padrao):
    """bridges.yaml escreve a tabela para humanos: `ds.a / b`, `ds.prefixo*`."""
    return {padrao.split(".", 1)[0].strip()} if "." in padrao else set()


def _do_branch(caminho, branch="harness-gemma"):
    try:
        return subprocess.run(["git", "-C", str(RAIZ), "show", f"{branch}:{caminho}"],
                              capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _exemplos():
    """Uma entrada por resultado conferido: as linhas `- **Txx-n ✅ ...**` de respostas.md, com
    o tema do cabeçalho, e as perguntas diretas de treino com o gabarito. Pendentes e sem
    resposta ficam de fora: não ensinam caminho nenhum."""
    saida, tema = [], ""
    for linha in (RAIZ / "docs/pesquisa/hipoteses/respostas.md").read_text().splitlines():
        if linha.startswith("## "):
            tema = linha[3:].strip()
            continue
        m = re.match(r"^- \*\*(T\d+-\d+)\s+([✅◐])[^*]*\*\*\s*(.+)$", linha)
        if m:
            saida.append({"id": m.group(1), "tema": tema, "status": m.group(2), "texto": m.group(3)})
    diretas = _do_branch("harness/dados/diretas.tsv") or ""
    for i, linha in enumerate(l for l in diretas.splitlines() if l.strip() and not l.startswith("#")):
        pergunta, _, esperado = linha.partition("\t")
        saida.append({"id": f"D{i + 1:02d}", "tema": "pergunta direta", "status": "✅",
                      "texto": f"{pergunta} → {esperado.replace('|', ' ou ')}"})
    return saida


def main():
    grafo = json.loads((RAIZ / "pages" / "atlas" / "schema_graph.json").read_text())
    temas = grafo["domains"]
    dataset_tema = {d["n"]: d["dom"] for d in grafo["datasets"]}

    por_ds = defaultdict(lambda: {"gotchas": [], "codigos": [], "pontes": [], "metricas": [], "codificacao": []})

    for arq in sorted((CTX / "gotchas").glob("*.yml")):
        doc = yaml.safe_load(arq.read_text())
        por_ds[doc["dataset"]]["gotchas"] = [
            {k: g[k] for k in ("resumo", "detalhe", "tabelas", "colunas", "severidade", "verificado") if g.get(k)}
            for g in doc.get("gotchas", [])]

    codigos = yaml.safe_load((CTX / "column_codes.yaml").read_text())
    for e in codigos["entradas"]:
        ds = e["tabela"].split(".", 1)[0]
        por_ds[ds]["codigos"].append(
            {k: e[k] for k in ("tabela", "colunas", "status", "significado", "valores", "verificado", "nota")
             if e.get(k) not in (None, "", [], {})})

    pontes = yaml.safe_load((CTX / "bridges.yaml").read_text())
    conceitos = pontes["concepts"]
    for grupo, lista in pontes["bridges"].items():
        for b in lista:
            conceito = b.get("concept") or grupo
            item = {"tabela": b["table"], "coluna": b["column"], "conceito": conceito,
                    "referencia": (conceitos.get(conceito) or {}).get("canonical_table"),
                    "join": b.get("join_expr") or b.get("expr"),
                    "nota": b.get("format") or b.get("description"), "verificado": b.get("verified")}
            for ds in _datasets_do_padrao(b["table"]):
                por_ds[ds]["pontes"].append({k: v for k, v in item.items() if v})

    # coded_differently cita os datasets na própria prosa: quem é citado recebe o aviso
    for coluna, v in pontes["coded_differently"].items():
        for ds in dataset_tema:
            if ds in v["reason"]:
                por_ds[ds]["codificacao"].append(coluna)

    metricas = yaml.safe_load((CTX / "metrics.yaml").read_text())["metrics"]
    for nome, m in metricas.items():
        por_ds[m["source_table"].split(".", 1)[0]]["metricas"].append(nome)

    notas = json.loads(_do_branch("harness/dados/notas.json") or "{}")
    for tabela, cols in notas.items():
        if "." in tabela:
            por_ds[tabela.split(".", 1)[0]].setdefault("notas", {})[tabela] = cols

    pacote = {
        "gerado": datetime.date.today().isoformat(),
        "temas": temas,
        "dataset_tema": dataset_tema,
        "datasets": {ds: {k: v for k, v in d.items() if v} for ds, d in sorted(por_ds.items())},
        "falsos_amigos": {k: v["reason"] for k, v in pontes["false_friends"].items()},
        "codificacao_diferente": {k: v["reason"] for k, v in pontes["coded_differently"].items()},
        "metricas": {nome: {k: m[k] for k in ("description", "unit", "grain", "source_table", "expression",
                                              "required_filters", "synonyms", "verified", "caveat") if m.get(k)}
                     for nome, m in metricas.items()},
        "hierarquias": yaml.safe_load((CTX / "hierarchies.yaml").read_text())["hierarchies"],
        "exemplos": _exemplos(),
    }
    tmp = SAIDA.with_suffix(".tmp")
    tmp.write_text(json.dumps(pacote, ensure_ascii=False, default=_texto, separators=(",", ":")))
    tmp.replace(SAIDA)
    print(f"{len(pacote['datasets'])} datasets com contexto, {len(dataset_tema)} com tema, "
          f"{len(pacote['exemplos'])} exemplos, {len(notas)} tabelas com nota, "
          f"{SAIDA.stat().st_size / 1e3:.0f} KB -> {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
