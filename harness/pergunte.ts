#!/usr/bin/env bun
/**
 * Uma pergunta, uma resposta.
 *
 *     bun harness/pergunte.ts "Quantos óbitos por suicídio houve no RJ em 2020?"
 *
 * Passa pelo caminho agêntico (Pi + as ferramentas de harness/mcp.ts), que é o
 * que acerta: medido em 2026-09-02, agêntico 3/3 correto contra 0/3 do pipeline
 * fixo nas mesmas perguntas. O fixo é 14x mais rápido e erra — reporta um grupo
 * do GROUP BY como se fosse o total, devolve código de município em vez do nome,
 * e desiste depois de algumas rejeições em vez de iterar.
 *
 * Espere ~1 min numa pergunta direta e ~5 a 10 numa que cruza fontes. O tempo
 * está no laço, não na consulta: cada turno de modelo gera a ~9 t/s.
 *
 * O turno degenerado do item 10 de `tasks/backlog.md` é repetido por
 * `guarda.ts`, que fica entre o Pi e o llama-server. Repetir a pergunta
 * inteira num processo novo sobra só como última linha, para quando a guarda
 * esgota as tentativas dela.
 *
 * A transcrição (cada SQL e o começo de cada resultado): `bun harness/sessao.ts`.
 */
import { garanteTunel } from "./modelo.ts";
import { sobeGuarda, resumoGuarda } from "./guarda.ts";
import { comandoPi } from "./pi.ts";

const RAIZ = new URL("..", import.meta.url).pathname;
const MAX_TENTATIVAS = Number(Bun.env.HARNESS_TENTATIVAS ?? 3);

const pergunta = Bun.argv.slice(2).join(" ").trim();
if (!pergunta) {
  console.error("uso: bun harness/pergunte.ts \"<pergunta em pt-BR>\"");
  console.error("ex.:  bun harness/pergunte.ts \"Quantos CAPS existem por estado?\"");
  process.exit(1);
}

if (!await garanteTunel()) {
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

async function tenta(): Promise<{ code: number; texto: string }> {
  const { cmd, env } = comandoPi(pergunta, guarda.url);
  const proc = Bun.spawn(cmd, {
    cwd: RAIZ,
    env,
    stdin: "ignore",
    stdout: "pipe",
    stderr: "inherit",
    timeout: Number(Bun.env.HARNESS_TIMEOUT_MS ?? 2_400_000),
    killSignal: "SIGKILL",
  });
  // "pipe" em vez de "inherit" só para poder medir se saiu algo — o texto
  // ainda vai pro terminal em tempo real, igual antes.
  const decoder = new TextDecoder();
  const pedacos: string[] = [];
  for await (const pedaco of proc.stdout) {
    const s = decoder.decode(pedaco, { stream: true });
    process.stdout.write(s);
    pedacos.push(s);
  }
  const code = await proc.exited;
  return { code, texto: pedacos.join("") };
}

const guarda = sobeGuarda();
const t0 = Date.now();
let resultado = await tenta();
let tentativas = 1;
while (resultado.texto.trim().length <= 40 && tentativas < MAX_TENTATIVAS) {
  tentativas++;
  console.error(`\n(vazio — tentativa ${tentativas}/${MAX_TENTATIVAS}, workaround do item 10)\n`);
  resultado = await tenta();
}
console.error(`\n[${((Date.now() - t0) / 60000).toFixed(1)} min] ${resumoGuarda(guarda.stats)}`);
guarda.para();
process.exit(resultado.code);
