#!/usr/bin/env bun
/**
 * Uma pergunta, uma resposta.
 *
 *     bun harness/pergunte.ts "Quantos óbitos por suicídio houve no RJ em 2020?"
 *
 * Passa pelo caminho agêntico (dsh + as ferramentas de harness/mcp.ts), que é o
 * que acerta: medido em 2026-09-02, agêntico 3/3 correto contra 0/3 do pipeline
 * fixo nas mesmas perguntas. O fixo é 14x mais rápido e erra — reporta um grupo
 * do GROUP BY como se fosse o total, devolve código de município em vez do nome,
 * e desiste depois de algumas rejeições em vez de iterar.
 *
 * Espere ~5 a 10 min por pergunta. O tempo está no laço, não em uma consulta
 * lenta: são 8 e poucos turnos de modelo a ~9 t/s de geração.
 */
import { vivo } from "./modelo.ts";

const RAIZ = new URL("..", import.meta.url).pathname;
const PATCH = "harness/dsh/rodado.patch.yml";

const pergunta = Bun.argv.slice(2).join(" ").trim();
if (!pergunta) {
  console.error("uso: bun harness/pergunte.ts \"<pergunta em pt-BR>\"");
  console.error("ex.:  bun harness/pergunte.ts \"Quantos CAPS existem por estado?\"");
  process.exit(1);
}

if (!await vivo()) {
  console.error("llama-server inalcançável em 127.0.0.1:8099.\n");
  console.error("No beelink:");
  console.error("  cd ~/llama.cpp/build/bin && setsid ./llama-server \\");
  console.error("    -m ~/llm/gemma-4-26B_q4_0-it.gguf -t 8 -c 32768 -np 1 \\");
  console.error("    --chat-template-kwargs '{\"enable_thinking\":false}' \\");
  console.error("    --host 127.0.0.1 --port 8099 &\n");
  console.error("Do mac (o servidor escuta só em loopback, de propósito):");
  console.error("  ssh -f -N -L 8099:127.0.0.1:8099 beelink");
  process.exit(1);
}

const t0 = Date.now();
const proc = Bun.spawn(["bunx", "dsh", "--profile", "headless", "--patch", PATCH, pergunta], {
  cwd: RAIZ,
  // O llama-server ignora o valor, mas o pi-ai exige a referência: sem ela o
  // boot morre com "No API key for provider".
  env: { ...process.env, HARNESS_LLM_KEY: process.env.HARNESS_LLM_KEY ?? "nao-usada" },
  stdout: "inherit",
  stderr: "inherit",
  timeout: Number(Bun.env.HARNESS_TIMEOUT_MS ?? 2_400_000),
  killSignal: "SIGKILL",
});
const code = await proc.exited;
console.error(`\n[${((Date.now() - t0) / 60000).toFixed(1)} min]`);
process.exit(code);
