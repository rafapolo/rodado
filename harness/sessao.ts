#!/usr/bin/env bun
/**
 * Lê uma sessão do dsh como transcrição: cada chamada de ferramenta com os
 * argumentos (a SQL inteira), o começo do resultado e a resposta final.
 *
 *     bun harness/sessao.ts            # a mais recente
 *     bun harness/sessao.ts <id|dir>   # uma específica
 *     bun harness/sessao.ts --n 3      # as 3 mais recentes
 */
import { readdirSync, statSync, readFileSync } from "node:fs";
import { homedir } from "node:os";

const RAIZ = new URL("..", import.meta.url).pathname;
const DIR = `${homedir()}/.dsh/sessions/-${RAIZ.replace(/\//g, "-")}-`;

export function sessoes(): string[] {
  return readdirSync(DIR).filter((d) => d.startsWith("session-"))
    .map((d) => `${DIR}/${d}`)
    .sort((a, b) => statSync(b).mtimeMs - statSync(a).mtimeMs);
}

export function eventos(dir: string): Record<string, any>[] {
  const arq = `${dir}/session.jsonl.zstd`;
  const bruto = Bun.zstdDecompressSync(readFileSync(arq));
  return new TextDecoder().decode(bruto).split("\n").filter(Boolean).flatMap((l) => {
    try { return [JSON.parse(l)]; } catch { return []; }
  });
}

export interface Passo { ferramenta: string; argumentos: string; resultado: string; erro: boolean }

export function transcricao(dir: string): { pergunta: string; passos: Passo[]; final: string } {
  const evs = eventos(dir);
  const passos: Passo[] = [];
  const porId = new Map<string, Passo>();
  let pergunta = "";
  let final = "";
  for (const e of evs) {
    if (e.type === "user/message" && !pergunta && e.data?.source?.kind === "user") {
      pergunta = e.data.content?.map((c: any) => c.text).join("") ?? "";
    }
    if (e.type === "tool/call") {
      const p = { ferramenta: e.data.name, argumentos: e.data.arguments, resultado: "", erro: false };
      passos.push(p);
      porId.set(e.data.callId, p);
    }
    if (e.type === "tool/result") {
      const r = e.data.message?.content?.[0];
      const p = porId.get(r?.toolCallId ?? e.data.message?.source?.callId);
      if (p) {
        p.resultado = (r?.content ?? []).map((c: any) => c.text ?? "").join("");
        p.erro = Boolean(r?.isError);
      }
    }
    if (e.type === "assistant/message") {
      const txt = (e.data.message?.content ?? []).filter((c: any) => c.type === "text").map((c: any) => c.text).join("");
      if (txt.trim()) final = txt;
    }
  }
  return { pergunta, passos, final };
}

if (import.meta.main) {
  const args = Bun.argv.slice(2);
  const n = args[0] === "--n" ? Number(args[1]) : 1;
  const alvo = args[0] && args[0] !== "--n" ? args[0] : undefined;
  const dirs = alvo ? [alvo.includes("/") ? alvo : sessoes().find((d) => d.includes(alvo))!] : sessoes().slice(0, n);
  const corte = Number(Bun.env.SESSAO_CORTE ?? 600);
  for (const d of dirs) {
    const t = transcricao(d);
    console.log(`=== ${d.split("/").pop()}\nPERGUNTA: ${t.pergunta}\n`);
    for (const [i, p] of t.passos.entries()) {
      let a = p.argumentos;
      try { const j = JSON.parse(a); a = j.sql ?? j.texto ?? JSON.stringify(j); } catch { /* cru */ }
      console.log(`[${i + 1}] ${p.ferramenta.replace("mcp__rodado__", "")}${p.erro ? " ✗" : ""}: ${a}`);
      console.log(`    → ${p.resultado.slice(0, corte).replace(/\n/g, "\n      ")}${p.resultado.length > corte ? " …" : ""}\n`);
    }
    console.log(`FINAL: ${t.final}\n`);
  }
}
