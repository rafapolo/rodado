#!/usr/bin/env bun
/**
 * Roda o doc2query nos 33 lotes via `opencode run`, valida cada saída e retoma
 * de onde parou.
 *
 *   bun run scripts/doc2query_roda.ts                   # todos os lotes pendentes
 *   bun run scripts/doc2query_roda.ts --lote 00_amostra # só um
 *   bun run scripts/doc2query_roda.ts --modelo anthropic/claude-sonnet-4-5
 *   bun run scripts/doc2query_roda.ts --revalidar       # só confere o que já existe
 *
 * É retomável de propósito: são 33 chamadas de LLM, e uma queda no lote 20 não
 * pode custar os 19 anteriores. Lote com saída válida é pulado.
 */
import { readFileSync, writeFileSync, existsSync, readdirSync, unlinkSync } from "node:fs";

const DIR = "tasks/doc2query";
const PROMPT = "scripts/prompts/doc2query.md";
const arg = (n: string) => { const i = Bun.argv.indexOf(n); return i > 0 ? Bun.argv[i + 1] : undefined; };
const MODELO = arg("--modelo");
const SO_LOTE = arg("--lote");
const REVALIDAR = Bun.argv.includes("--revalidar");
const PERGUNTAS_ESPERADAS = 8;

interface Saida { id: string; perguntas: string[]; incerta?: boolean }

/**
 * Valida a saída de um lote. Rejeitar cedo importa: uma saída ruim não dá erro,
 * ela envenena a busca em silêncio — que é exatamente o problema que estamos
 * consertando.
 */
function validar(loteFile: string, saidaFile: string): { ok: boolean; erros: string[]; n: number } {
  const erros: string[] = [];
  if (!existsSync(saidaFile)) return { ok: false, erros: ["saída não existe"], n: 0 };

  const entrada: any[] = readFileSync(loteFile, "utf-8").trim().split("\n").map((l) => JSON.parse(l));
  const esperados = new Map<string, string[]>(
    entrada.map((e: any) => [e.id as string, (e.colunas as string[]).map((c) => c.toLowerCase())]));

  let saidas: Saida[];
  try {
    saidas = readFileSync(saidaFile, "utf-8").trim().split("\n")
      .filter((l) => l.trim() && !l.trim().startsWith("```"))
      .map((l) => JSON.parse(l));
  } catch (e) {
    return { ok: false, erros: [`JSON inválido: ${e}`], n: 0 };
  }

  const vistos = new Set<string>();
  let total = 0;
  for (const s of saidas) {
    if (!esperados.has(s.id)) { erros.push(`id fora do lote: ${s.id}`); continue; }
    if (vistos.has(s.id)) erros.push(`id repetido: ${s.id}`);
    vistos.add(s.id);

    if (!Array.isArray(s.perguntas) || s.perguntas.length === 0) { erros.push(`${s.id}: sem perguntas`); continue; }
    if (!s.incerta && s.perguntas.length !== PERGUNTAS_ESPERADAS) {
      erros.push(`${s.id}: ${s.perguntas.length} perguntas, esperado ${PERGUNTAS_ESPERADAS}`);
    }
    total += s.perguntas.length;

    const cols = esperados.get(s.id)!;
    for (const q of s.perguntas) {
      if (typeof q !== "string" || q.length < 8) { erros.push(`${s.id}: pergunta curta demais: "${q}"`); continue; }
      if (q.split(/\s+/).length > 20) erros.push(`${s.id}: pergunta longa demais: "${q.slice(0, 50)}…"`);
      // A regra 1 do prompt, verificada: ecoar nome de coluna anula o exercício,
      // porque o índice já tem os nomes e é justamente isso que não funciona.
      const eco = cols.find((c) => c.includes("_") && q.toLowerCase().includes(c));
      if (eco) erros.push(`${s.id}: ecoa nome de coluna "${eco}" em "${q.slice(0, 46)}…"`);
    }
  }

  for (const id of esperados.keys()) if (!vistos.has(id)) erros.push(`faltou: ${id}`);
  return { ok: erros.length === 0, erros, n: total };
}

async function rodarLote(nome: string): Promise<boolean> {
  const lote = `${DIR}/lote_${nome}.jsonl`;
  const saida = `${DIR}/saida_${nome}.jsonl`;

  const msg =
    `Leia ${PROMPT} e siga-o à risca para todas as tabelas de ${lote}. ` +
    `Escreva o resultado em ${saida}: um JSON por linha, na mesma ordem da entrada, ` +
    `sem cercas de markdown e sem nenhum texto fora do JSONL. ` +
    `Não rode nenhum comando além de ler a entrada e escrever a saída.`;

  const args = ["run", "--auto", ...(MODELO ? ["--model", MODELO] : []), msg];
  const proc = Bun.spawn(["opencode", ...args], { stdout: "pipe", stderr: "pipe" });
  const [out, err, code] = await Promise.all([
    new Response(proc.stdout).text(), new Response(proc.stderr).text(), proc.exited,
  ]);
  if (code !== 0) { console.log(`  opencode saiu com ${code}: ${err.trim().slice(0, 300)}`); return false; }
  if (!existsSync(saida)) {
    // O agente rodou mas nao gravou. Acontece com modelo que "responde" em vez
    // de usar a ferramenta de escrita — guarda o log pra isso nao ser mudo.
    writeFileSync(`${DIR}/erro_${nome}.log`, out.slice(-4000));
    console.log(`  o agente nao gravou ${saida} — log em ${DIR}/erro_${nome}.log`);
    return false;
  }

  const v = validar(lote, saida);
  if (!v.ok) {
    console.log(`  INVÁLIDO (${v.erros.length} problema(s)):`);
    for (const e of v.erros.slice(0, 6)) console.log(`    ${e}`);
    if (v.erros.length > 6) console.log(`    … e mais ${v.erros.length - 6}`);
    // apaga: saída meio-boa é pior que ausente, porque parece pronta
    if (existsSync(saida)) unlinkSync(saida);
    return false;
  }
  console.log(`  ok — ${v.n} perguntas`);
  return true;
}

const lotes = SO_LOTE ? [SO_LOTE]
  : readdirSync(DIR).filter((f) => f.startsWith("lote_")).sort()
      .map((f) => f.replace("lote_", "").replace(".jsonl", ""));

if (REVALIDAR) {
  let bons = 0, total = 0;
  for (const n of lotes) {
    const v = validar(`${DIR}/lote_${n}.jsonl`, `${DIR}/saida_${n}.jsonl`);
    if (v.ok) { bons++; total += v.n; }
    else if (existsSync(`${DIR}/saida_${n}.jsonl`)) console.log(`lote ${n}: ${v.erros[0]}`);
  }
  console.log(`\n${bons}/${lotes.length} lotes válidos, ${total} perguntas`);
  process.exit(0);
}

let feitos = 0, falhos = 0;
for (const n of lotes) {
  if (validar(`${DIR}/lote_${n}.jsonl`, `${DIR}/saida_${n}.jsonl`).ok) { feitos++; continue; }
  console.log(`lote ${n} …`);
  if (await rodarLote(n)) feitos++; else falhos++;
}
console.log(`\n${feitos}/${lotes.length} lotes prontos` + (falhos ? `, ${falhos} falharam — rode de novo, ele retoma` : ""));
