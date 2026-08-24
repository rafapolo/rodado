#!/usr/bin/env bun
/**
 * Compara geração via binário nativo (Ollama, schema_compact.txt INTEIRO no
 * prompt, sem retrieval nenhum) contra o baseline WebLLM medido em
 * veredito.html (3B: 40% resolvida, 7B: 67%, nas mesmas 15 douradas).
 *
 * Não precisa de Chrome/WebGPU — roda puro em Bun. Reusa o firewall e o
 * executor SQL do server.ts (mesma verificação, mesmo caminho ssh beelink).
 *
 *   bun run web/diag/nativo_compara.ts --modelo qwen2.5-coder:14b --n 15
 *   bun run web/diag/nativo_compara.ts --modelo devstral-small-2:24b --n 5
 */
import { readFileSync } from "node:fs";
import { checkReadOnly, capRows } from "../src/sqlguard.ts";
import { runSqlSsh, rewriteToReadParquet, needsParquetFallback } from "../src/beelink.ts";
import { SISTEMA } from "../static/prompt.js";

const args = new Map<string, string>();
for (let i = 0; i < process.argv.length - 1; i++) {
  if (process.argv[i].startsWith("--")) args.set(process.argv[i].slice(2), process.argv[i + 1]);
}
const MODELO = args.get("modelo") ?? "qwen2.5-coder:14b";
const N = Number(args.get("n") ?? 15);
const NUM_CTX = Number(args.get("ctx") ?? 32768);
const OLLAMA = args.get("ollama") ?? "http://127.0.0.1:11434";

const SCHEMA = readFileSync("docs/context/schema_compact.txt", "utf-8");
const { perguntas } = JSON.parse(readFileSync("tasks/ask_web_douradas.json", "utf-8"));

console.log(`modelo: ${MODELO}  num_ctx: ${NUM_CTX}  schema: ${SCHEMA.length} chars (~${Math.round(SCHEMA.length / 3.5)} tokens)  n: ${N}`);

// mesma extração de SQL que llm.js:tirarCercas — o modelo às vezes embrulha
// em cerca de markdown ou pensa em voz alta antes.
function extrairSQL(bruto: string): { sql?: string; erro?: string } {
  const s = bruto.trim();
  const cerca = s.match(/```(?:sql)?\s*([\s\S]*?)```/i);
  const limpo = (cerca ? cerca[1] : s).replace(/<think>[\s\S]*?<\/think>/gi, "").trim();
  const err = limpo.match(/\{\s*"?error"?\s*:\s*"([^"]+)"/i);
  if (err) return { erro: err[1] };
  if (!/^\s*(SELECT|WITH)\b/i.test(limpo)) return { erro: `não devolveu SQL: ${limpo.slice(0, 150)}` };
  return { sql: limpo.replace(/;\s*$/, "") };
}

async function gerarSQL(pergunta: string): Promise<{ sql?: string; erro?: string; ms: number }> {
  const prompt = `${SISTEMA}\n\nTABELAS DISPONÍVEIS (schema completo — sem recuperação, ${Math.round(SCHEMA.length / 3.5)} tokens)\n${SCHEMA}\n\nPERGUNTA: ${pergunta}\nSQL:`;
  const t0 = Date.now();
  const r = await fetch(`${OLLAMA}/api/chat`, {
    method: "POST",
    body: JSON.stringify({
      model: MODELO,
      messages: [{ role: "user", content: prompt }],
      stream: false,
      options: { num_ctx: NUM_CTX, temperature: 0 },
    }),
  }).then((r) => r.json()) as any;
  const ms = Date.now() - t0;
  if (r.error) return { erro: `ollama: ${r.error}`, ms };
  return { ...extrairSQL(r.message?.content ?? ""), ms };
}

async function executar(sql: string) {
  const recusa = checkReadOnly(sql);
  if (recusa) return { erro: recusa };
  let result = await runSqlSsh(sql);
  if (result.error && needsParquetFallback(result.error)) {
    const { sql: fallback, rewritten } = rewriteToReadParquet(sql);
    if (rewritten.length > 0) {
      const retry = await runSqlSsh(fallback);
      if (!retry.error) result = retry;
    }
  }
  return result;
}

let executou = 0, vazio = 0, erro = 0;
const linhas: string[] = [];

for (const p of perguntas.slice(0, N)) {
  const g = await gerarSQL(p.q);
  let marca: string;
  if (g.erro) {
    erro++;
    marca = `ERRO-GERACAO ${g.erro.slice(0, 60)}`;
  } else {
    const r = await executar(g.sql!);
    if (r.error) { erro++; marca = `ERRO-EXEC ${r.error.slice(0, 60)}`; }
    else {
      const semDado = !r.rows?.length || r.rows.every((l: any) => Object.values(l).every((v) => v === null || v === undefined));
      if (semDado) { vazio++; marca = "vazio"; }
      else { executou++; marca = `OK (${r.rows!.length} linhas)`; }
    }
  }
  linhas.push(`${(g.ms / 1000).toFixed(1)}s  ${marca}  ${p.q.slice(0, 55)}`);
  console.log(linhas[linhas.length - 1]);
}

const n = Math.min(N, perguntas.length);
console.log(`\n${"=".repeat(60)}`);
console.log(`modelo: ${MODELO}  schema completo (${Math.round(SCHEMA.length / 3.5)} tokens), sem retrieval`);
console.log(`resolvida (executou com dado): ${executou}/${n} (${Math.round(100 * executou / n)}%)`);
console.log(`vazio: ${vazio}/${n}   erro: ${erro}/${n}`);
