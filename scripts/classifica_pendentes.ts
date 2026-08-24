#!/usr/bin/env bun
/**
 * Classifica as perguntas pendentes do ../rodado/docs/respostas.md por
 * viabilidade contra o catálogo do espelho.
 *
 *   bun run scripts/classifica_pendentes.ts
 *   # -> tasks/pendentes_viabilidade.json
 *
 * Uma pergunta ⏳ é CONVERTÍVEL quando TODOS os datasets que ela cita existem
 * no catálogo (meta.json) — falta só rodar e verificar. Bloqueada tem pelo
 * menos um dataset fora do espelho; listar quais é o insumo para priorizar
 * o sync, não silenciar o furo.
 *
 * O código T<tema>-<item> vem do respostas.md; os nomes curtos de dataset
 * vêm do perguntas.md do repo irmão (mesma fonte do build_douradas_temas).
 */
import { readFileSync, writeFileSync } from "node:fs";

const RODADO = "../rodado/docs";
const mdP = readFileSync(`${RODADO}/perguntas.md`, "utf-8");
const mdR = readFileSync(`${RODADO}/respostas.md`, "utf-8");
const meta = JSON.parse(readFileSync("web/static/index/meta.json", "utf-8"));
const catalogo = new Set<string>(meta.tabelas.map((t: any) => t.id.split(".")[0]));

function resolver(curto: string): string | null {
  const limpo = curto.trim().replace(/\\?\*/g, "").trim();
  for (const c of [`br_${limpo}`, limpo]) if (catalogo.has(c)) return c;
  return null;
}

// --- perguntas.md: código -> nomes curtos citados ---------------------------
// Tema numerado: `## 07 · Economia...`; itens: `1. pergunta (n=3: ds1, ds2*)`.
// A seção final multi-família usa outro formato; entra como tema "M".
interface Perg { tema: string; item: string; curtos: string[] }
const perguntas = new Map<string, Perg>();
let temaNum: string | null = null;
for (const linha of mdP.split("\n")) {
  const mTema = linha.match(/^## (\d+) · /);
  if (mTema) { temaNum = mTema[1]!.padStart(2, "0"); continue; }
  if (linha.startsWith("# ")) { temaNum = "M"; continue; }   // título da seção final
  const mItem = linha.match(/^(\d+)\.\s+.+\*\(n=[^)]*\)\s*\*?\s*$/);
  if (!mItem || !temaNum) continue;
  // nomes curtos: tudo entre "n=X:" e ")" no parêntese final
  const mDs = linha.match(/\*\(n=[^:)]+:\s*([^)]*)\)\s*\*?\s*$/);
  const curtos = (mDs?.[1] ?? "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
  perguntas.set(`T${temaNum}-${mItem[1]}`, { tema: temaNum, item: mItem[1]!, curtos });
}

// --- respostas.md: status por código ----------------------------------------
// Um bullet pode agrupar vários códigos: "- **T07-1, T07-3 ⏳** Pendentes — ..."
interface LinhaResp { codigos: string[]; status: string; nota: string }
const resps: LinhaResp[] = [];
for (const linha of mdR.split("\n")) {
  const m = linha.match(/^- \*\*(.+?)\s+([✅◐⏳])(?:\s*\([^)]*\))?\*\*(.*)$/);
  if (!m) continue;
  const codigos = [...m[1]!.matchAll(/T\d{2}-[\w-]+/g)].map((x) => x[0]);
  if (!codigos.length) continue;
  resps.push({ codigos, status: m[2]!, nota: m[3]!.trim().replace(/\s+/g, " ") });
}

// --- classificação -----------------------------------------------------------
type Classe = "respondida" | "parcial" | "convertivel" | "bloqueada" | "sem_pergunta";
interface Item {
  codigo: string; classe: Classe; nota?: string;
  presentes?: string[]; ausentes?: string[];
}
const itens: Item[] = [];

for (const r of resps) {
  for (const codigo of r.codigos) {
    if (r.status === "✅") { itens.push({ codigo, classe: "respondida", nota: r.nota }); continue; }
    if (r.status === "◐") { itens.push({ codigo, classe: "parcial", nota: r.nota }); continue; }
    const p = perguntas.get(codigo);
    if (!p) { itens.push({ codigo, classe: "sem_pergunta", nota: r.nota }); continue; }
    const presentes: string[] = [], ausentes: string[] = [];
    for (const c of p.curtos) {
      const ds = resolver(c);
      if (ds) presentes.push(ds); else ausentes.push(c.replace(/\\?\*/g, ""));
    }
    itens.push({
      codigo,
      classe: ausentes.length ? "bloqueada" : "convertivel",
      nota: r.nota,
      ...(presentes.length ? { presentes: [...new Set(presentes)] } : {}),
      ...(ausentes.length ? { ausentes: [...new Set(ausentes)] } : {}),
    });
  }
}

const contagem = itens.reduce<Record<string, number>>((a, i) => ((a[i.classe] = (a[i.classe] ?? 0) + 1), a), {});
const bloqueioFreq = new Map<string, number>();
for (const i of itens) for (const a of i.ausentes ?? []) bloqueioFreq.set(a, (bloqueioFreq.get(a) ?? 0) + 1);

writeFileSync("tasks/pendentes_viabilidade.json", JSON.stringify({
  _meta: {
    origem: [`${RODADO}/perguntas.md`, `${RODADO}/respostas.md`],
    sobre: "Viabilidade das perguntas pendentes contra o catálogo do espelho. " +
           "convertivel = todos os datasets citados existem; falta rodar e verificar. " +
           "bloqueada lista o que falta sincronizar.",
    gerado_em: new Date().toISOString().slice(0, 10),
  },
  contagem,
  itens,
}, null, 1));

console.log(`\n${itens.length} códigos classificados:`);
for (const [k, v] of Object.entries(contagem).sort()) console.log(`  ${k}: ${v}`);

console.log(`\nTop bloqueios (dataset ausente — candidato ao sync):`);
for (const [ds, n] of [...bloqueioFreq].sort((a, b) => b[1] - a[1])) console.log(`  ${ds}: ${n}x`);

console.log(`\nConvertíveis (todos os datasets no espelho):`);
for (const i of itens.filter((x) => x.classe === "convertivel")) console.log(`  ${i.codigo} — ${i.nota?.slice(0, 90) ?? ""}`);
