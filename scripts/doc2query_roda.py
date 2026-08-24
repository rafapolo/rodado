#!/usr/bin/env python3
"""Resumable doc2query batch runner — Python port of ask-web's doc2query_roda.ts,
adapted to call `opencode run --model opencode/hy3-free` (OpenCode Zen free tier;
`opencode-go/*` is out of balance, `opencode/hy3-free` is not).

    python3 doc2query_roda.py              # all pending lotes
    python3 doc2query_roda.py --lote 05    # just one

Retomable de propósito: uma queda no lote 20 nao pode custar os 19 anteriores.
Lote com saida ja valida e pulado.
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

DIR = Path("tasks/doc2query")
PROMPT = Path("scripts/prompts/doc2query.md")
MODEL = "opencode/hy3-free"
OPENCODE_BIN = "opencode"
PERGUNTAS_ESPERADAS = 8
ESTRUTURAIS = {"nome_coluna", "id_tabela", "cobertura_temporal"}


def validar(lote_file: Path, saida_file: Path):
    entrada = [json.loads(l) for l in lote_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    esperados = {e["id"]: [c.lower() for c in e["colunas"]] for e in entrada}
    erros = []
    if not saida_file.exists():
        return {"ok": False, "erros": ["saida nao existe"], "n": 0}
    try:
        linhas = [l for l in saida_file.read_text(encoding="utf-8").strip().split("\n")
                  if l.strip() and not l.strip().startswith("```")]
        saidas = [json.loads(l) for l in linhas]
    except Exception as e:
        return {"ok": False, "erros": [f"JSON invalido: {e}"], "n": 0}

    vistos = set()
    total = 0
    for s in saidas:
        if s["id"] not in esperados:
            erros.append(f"id fora do lote: {s['id']}")
            continue
        if s["id"] in vistos:
            erros.append(f"id repetido: {s['id']}")
        vistos.add(s["id"])
        cols = esperados[s["id"]]
        perguntas = s.get("perguntas", [])
        if not perguntas:
            erros.append(f"{s['id']}: sem perguntas")
            continue
        if not s.get("incerta") and len(perguntas) != PERGUNTAS_ESPERADAS:
            erros.append(f"{s['id']}: {len(perguntas)} perguntas, esperado {PERGUNTAS_ESPERADAS}")
        eh_dicionario = s["id"].endswith(".dicionario")
        for q in perguntas:
            if not isinstance(q, str) or len(q) < 8:
                erros.append(f"{s['id']}: pergunta curta demais: {q!r}")
                continue
            if len(q.split()) > 20:
                erros.append(f"{s['id']}: pergunta longa demais: {q[:50]!r}")
            ql = q.lower()
            for c in cols:
                if "_" in c and c in ql and not (eh_dicionario and c in ESTRUTURAIS):
                    erros.append(f"{s['id']}: ecoa coluna '{c}' em {q[:46]!r}")
                    break
        total += len(perguntas)
    for id_ in esperados:
        if id_ not in vistos:
            erros.append(f"faltou: {id_}")
    return {"ok": len(erros) == 0, "erros": erros, "n": total}


def rodar_lote(nome: str) -> bool:
    lote = DIR / f"lote_{nome}.jsonl"
    saida = DIR / f"saida_{nome}.jsonl"

    msg = (
        f"Leia {PROMPT} e siga-o à risca para todas as tabelas de {lote}. "
        f"Escreva o resultado em {saida}: um JSON por linha, na mesma ordem da entrada, "
        f"sem cercas de markdown e sem nenhum texto fora do JSONL. "
        f"Não rode nenhum comando além de ler a entrada e escrever a saída."
    )
    cmd = [OPENCODE_BIN, "run", "--auto", "--model", MODEL, msg]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        print("  timeout apos 600s")
        return False

    if proc.returncode != 0:
        print(f"  opencode saiu com {proc.returncode}: {proc.stderr.strip()[:300]}")
        return False
    if not saida.exists():
        errlog = DIR / f"erro_{nome}.log"
        errlog.write_text(proc.stdout[-4000:], encoding="utf-8")
        print(f"  o agente nao gravou {saida} — log em {errlog}")
        return False

    v = validar(lote, saida)
    if not v["ok"]:
        print(f"  INVALIDO ({len(v['erros'])} problema(s)):")
        for e in v["erros"][:6]:
            print(f"    {e}")
        if len(v["erros"]) > 6:
            print(f"    ... e mais {len(v['erros']) - 6}")
        saida.unlink(missing_ok=True)
        return False
    print(f"  ok — {v['n']} perguntas")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lote")
    ap.add_argument("--max-retries", type=int, default=2)
    args = ap.parse_args()

    if args.lote:
        lotes = [args.lote]
    else:
        lotes = sorted(
            f.stem.replace("lote_", "") for f in DIR.glob("lote_*.jsonl")
        )

    feitos, falhos = 0, 0
    for n in lotes:
        lote_file, saida_file = DIR / f"lote_{n}.jsonl", DIR / f"saida_{n}.jsonl"
        if validar(lote_file, saida_file)["ok"]:
            feitos += 1
            print(f"lote {n} — ja pronto, pulando")
            continue
        print(f"lote {n} ...", flush=True)
        ok = False
        for attempt in range(args.max_retries):
            if rodar_lote(n):
                ok = True
                break
            print(f"  retry {attempt + 1}/{args.max_retries}")
            time.sleep(5)
        if ok:
            feitos += 1
        else:
            falhos += 1
        sys.stdout.flush()

    print(f"\n{feitos}/{len(lotes)} lotes prontos" +
          (f", {falhos} falharam apos retries" if falhos else ""))


if __name__ == "__main__":
    main()
