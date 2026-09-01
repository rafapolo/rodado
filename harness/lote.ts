/**
 * Roda perguntas abertas pelo dsh e registra o que voltou.
 *
 *     bun harness/lote.ts perguntas.txt
 *
 * Cada pergunta é um processo `dsh --profile headless` novo, mas o cache de
 * prefixo vive no llama-server e sobrevive entre processos — medido: 16.397 de
 * 16.585 tokens vieram do cache já na primeira pergunta seguinte.
 */
import { writeFileSync } from "node:fs";

const PATCH = "harness/dsh/rodado.patch.yml";

export interface Saida {
  pergunta: string;
  resposta: string;
  segundos: number;
  ok: boolean;
}

export async function roda(perguntas: string[]): Promise<Saida[]> {
  const out: Saida[] = [];
  for (const [i, q] of perguntas.entries()) {
    const t0 = Date.now();
    const p = Bun.spawn(
      ["bunx", "dsh", "--profile", "headless", "--patch", PATCH, q],
      {
        env: { ...process.env, HARNESS_LLM_KEY: "x" },
        stdout: "pipe", stderr: "pipe",
        timeout: 2_400_000, killSignal: "SIGKILL",
      },
    );
    const texto = await new Response(p.stdout).text();
    const err = await new Response(p.stderr).text();
    const code = await p.exited;
    const seg = (Date.now() - t0) / 1000;
    const resposta = (texto.trim() || err.trim()).slice(0, 4000);
    const ok = code === 0 && texto.trim().length > 40;
    out.push({ pergunta: q, resposta, segundos: seg, ok });
    console.log(`${ok ? "ok" : "--"} ${i + 1}/${perguntas.length}  ${seg.toFixed(0)}s  ${q.slice(0, 62)}`);
    if (!ok) console.log(`     ${resposta.replace(/\s+/g, " ").slice(0, 180)}`);
  }
  return out;
}

if (import.meta.main) {
  const arquivo = Bun.argv[2];
  if (!arquivo) { console.error("uso: bun harness/lote.ts <arquivo-de-perguntas>"); process.exit(1); }
  const perguntas = (await Bun.file(arquivo).text()).split("\n").map((l) => l.trim()).filter(Boolean);
  console.log(`${perguntas.length} perguntas pelo dsh\n`);
  const r = await roda(perguntas);
  const bons = r.filter((x) => x.ok).length;
  const medio = r.reduce((a, b) => a + b.segundos, 0) / r.length;
  console.log(`\n${"=".repeat(56)}`);
  console.log(`RESPONDEU: ${bons}/${r.length} = ${(100 * bons / r.length).toFixed(0)}%`);
  console.log(`TEMPO MÉDIO: ${medio.toFixed(0)}s por pergunta`);
  console.log("=".repeat(56));
  const saida = `benchmarks/lote_${new Date().toISOString().slice(0, 16).replace(/[:T]/g, "")}.json`;
  writeFileSync(saida, JSON.stringify(r, null, 1));
  console.log(`\ndetalhe em ${saida}`);
}
