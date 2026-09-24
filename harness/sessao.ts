#!/usr/bin/env bun
/**
 * Lê uma sessão do Pi como transcrição: cada chamada de ferramenta com os
 * argumentos (a SQL inteira), o começo do resultado e a resposta final.
 *
 *     bun harness/sessao.ts            # a mais recente
 *     bun harness/sessao.ts <id|arq>   # uma específica (parte do nome basta)
 *     bun harness/sessao.ts --n 3      # as 3 mais recentes
 *
 * As sessões ficam em `SESSOES` (pi.ts), um .jsonl por pergunta, fora do repo.
 */
import { readdirSync, statSync, readFileSync, existsSync } from "node:fs";
import { SESSOES } from "./pi.ts";

export function sessoes(): string[] {
  if (!existsSync(SESSOES)) return [];
  return readdirSync(SESSOES).filter((a) => a.endsWith(".jsonl"))
    .map((a) => `${SESSOES}/${a}`)
    .sort((a, b) => statSync(b).mtimeMs - statSync(a).mtimeMs);
}

export function eventos(arq: string): Record<string, any>[] {
  return readFileSync(arq, "utf8").split("\n").filter(Boolean).flatMap((l) => {
    try { return [JSON.parse(l)]; } catch { return []; }
  });
}

export interface Passo { ferramenta: string; argumentos: string; resultado: string; erro: boolean }

const texto = (conteudo: any): string =>
  typeof conteudo === "string" ? conteudo
    : (conteudo ?? []).filter((c: any) => c.type === "text").map((c: any) => c.text).join("");

export function transcricao(arq: string): { pergunta: string; passos: Passo[]; final: string } {
  const passos: Passo[] = [];
  const porId = new Map<string, Passo>();
  let pergunta = "";
  let final = "";
  for (const e of eventos(arq)) {
    const m = e.type === "message" ? e.message : undefined;
    if (!m) continue;
    if (m.role === "user" && !pergunta) pergunta = texto(m.content);
    if (m.role === "assistant") {
      for (const c of m.content ?? []) {
        if (c.type !== "toolCall") continue;
        const p = { ferramenta: c.name, argumentos: JSON.stringify(c.arguments), resultado: "", erro: false };
        passos.push(p);
        porId.set(c.id, p);
      }
      const t = texto(m.content);
      if (t.trim()) final = t;
    }
    if (m.role === "toolResult") {
      const p = porId.get(m.toolCallId);
      if (p) { p.resultado = texto(m.content); p.erro = Boolean(m.isError); }
    }
  }
  return { pergunta, passos, final };
}

if (import.meta.main) {
  const args = Bun.argv.slice(2);
  const n = args[0] === "--n" ? Number(args[1]) : 1;
  const alvo = args[0] && args[0] !== "--n" ? args[0] : undefined;
  const arqs = alvo ? [alvo.includes("/") ? alvo : sessoes().find((a) => a.includes(alvo))!] : sessoes().slice(0, n);
  if (!arqs.length || !arqs[0]) { console.error(`nenhuma sessão em ${SESSOES}`); process.exit(1); }
  const corte = Number(Bun.env.SESSAO_CORTE ?? 600);
  for (const a of arqs) {
    const t = transcricao(a);
    console.log(`=== ${a.split("/").pop()}\nPERGUNTA: ${t.pergunta}\n`);
    for (const [i, p] of t.passos.entries()) {
      let arg = p.argumentos;
      try { const j = JSON.parse(arg); arg = j.sql ?? j.texto ?? JSON.stringify(j); } catch { /* cru */ }
      console.log(`[${i + 1}] ${p.ferramenta}${p.erro ? " ✗" : ""}: ${arg}`);
      console.log(`    → ${p.resultado.slice(0, corte).replace(/\n/g, "\n      ")}${p.resultado.length > corte ? " …" : ""}\n`);
    }
    console.log(`FINAL: ${t.final}\n`);
  }
}
