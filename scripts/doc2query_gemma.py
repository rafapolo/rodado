#!/usr/bin/env python3
"""doc2query pelo Gemma 4 local no beelink, no lugar do `opencode`.

Motivo: em 2026-09-02 o `opencode/hy3-free` que o `doc2query_roda.py` usa passou
a devolver `UnknownError: Unexpected server error` em toda chamada, o que trava
a geração do corpus. O beelink já roda um `llama-server` com Gemma 4 26B na
porta 8099 (ver tasks/harness_gemma_dsh.md), e ele serve para esta tarefa --
gerar perguntas em português é bem mais tolerante que gerar SQL, onde o Gemma
erra codificação em silêncio.

Uma tabela por chamada (não o lote inteiro): o contexto fica pequeno, o JSON sai
mais confiável e uma falha custa uma tabela, não vinte e cinco.

    python3 scripts/doc2query_gemma.py --lote 19
    python3 scripts/doc2query_gemma.py --faltantes   # só o que o corpus não cobre
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DIR = REPO / "tasks" / "doc2query"
PROMPT = (REPO / "scripts" / "prompts" / "doc2query.md").read_text(encoding="utf-8")
URL = "http://127.0.0.1:8099/v1/chat/completions"

def gemma(msg: str, max_tokens=900) -> str:
    payload = json.dumps({"messages": [{"role": "user", "content": msg}],
                          "max_tokens": max_tokens, "temperature": 0.7})
    r = subprocess.run(
        ["ssh", "beelink", f"curl -s --max-time 300 {URL} -H 'Content-Type: application/json' "
         f"--data-binary @-"],
        input=payload, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[:200])
    return json.loads(r.stdout)["choices"][0]["message"]["content"]

def perguntas_de(tab: dict) -> list:
    cols = ", ".join(tab["colunas"][:40])
    msg = (f"{PROMPT}\n\n---\n\nTabela: `{tab['id']}`\n"
           f"Linhas: {tab.get('linhas','?')}\nColunas: {cols}\n\n"
           "Responda APENAS com um objeto JSON, sem cerca de código e sem texto antes ou "
           'depois, exatamente nesta forma:\n'
           '{"id": "' + tab["id"] + '", "perguntas": ["pergunta 1", "pergunta 2", ...]}\n'
           "Exatamente 8 perguntas.")
    txt = gemma(msg)
    m = re.search(r"\{.*\}", txt, re.S)
    if not m:
        raise ValueError("sem JSON na resposta")
    d = json.loads(m.group(0))
    qs = [q.strip() for q in d.get("perguntas", []) if isinstance(q, str) and q.strip()]
    if len(qs) < 4:
        raise ValueError(f"só {len(qs)} perguntas")
    return qs[:8]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lote")
    ap.add_argument("--faltantes", action="store_true")
    a = ap.parse_args()

    alvo = []
    if a.faltantes:
        corpus = {r["table"] for r in json.loads(
            (REPO / "docs/context/doc2query_index.json").read_text(encoding="utf-8"))["rows"]}
        for f in sorted(DIR.glob("lote_*.jsonl")):
            for l in f.read_text(encoding="utf-8").splitlines():
                if l.strip():
                    t = json.loads(l)
                    if t["id"] not in corpus:
                        alvo.append((f.stem.replace("lote_", ""), t))
    elif a.lote:
        f = DIR / f"lote_{a.lote}.jsonl"
        alvo = [(a.lote, json.loads(l)) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
    else:
        sys.exit("use --lote NN ou --faltantes")

    print(f"{len(alvo)} tabelas a gerar", flush=True)
    por_lote = {}
    ok = falhou = 0
    for i, (lote, tab) in enumerate(alvo, 1):
        try:
            qs = perguntas_de(tab)
            por_lote.setdefault(lote, []).append({"id": tab["id"], "perguntas": qs})
            ok += 1
            print(f"  [{i}/{len(alvo)}] ok  {tab['id']} — {len(qs)}q · {qs[0][:50]}", flush=True)
        except Exception as e:
            falhou += 1
            print(f"  [{i}/{len(alvo)}] ERR {tab['id']}: {str(e)[:70]}", flush=True)
        if i % 5 == 0 or i == len(alvo):
            for lt, rows in por_lote.items():
                out = DIR / f"saida_{lt}.jsonl"
                antigos = []
                if out.exists():
                    antigos = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines() if l.strip()]
                ids = {r["id"] for r in rows}
                juntos = [r for r in antigos if r["id"] not in ids] + rows
                out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in juntos) + "\n",
                               encoding="utf-8")
    print(f"FIM ok={ok} falhou={falhou}", flush=True)

if __name__ == "__main__":
    main()
