#!/usr/bin/env bun
/**
 * Converte docs/perguntas.md (do repo irmão rodado) no segundo conjunto dourado.
 *
 *   bun run scripts/build_douradas_temas.ts --md ../rodado/docs/perguntas.md \
 *     # -> tasks/douradas_temas.json + web/static/_douradas_temas.json
 *
 * Aquele documento anota por pergunta os DATASETS esperados em nome curto
 * (`n=3: me_rais, ms_sim, ibge_censo_2022*`), não tabelas. A expectativa é de
 * dataset — mede se a recuperação traz UMA tabela de cada família citada,
 * porque é essa a granularidade da anotação humana.
 *
 * Nome curto -> id do catálogo: `ms_sim` -> `br_ms_sim`; nomes que já trazem o
 * prefixo mundial (`world_oecd_pisa`) passam como estão. Dataset sem match no
 * catálogo vai para a lista `sem_match` — visível, nunca silencioso.
 */
import { readFileSync, writeFileSync } from "node:fs";

const argi = Bun.argv.indexOf("--md") + 1;
const MD = argi > 0 ? Bun.argv[argi] : "../rodado/docs/perguntas.md";

const md = readFileSync(MD, "utf-8");
const meta = JSON.parse(readFileSync("web/static/index/meta.json", "utf-8"));
const datasetsCatalogo = new Set<string>(meta.tabelas.map((t: any) => t.id.split(".")[0]));

// tabelas por dataset ordenadas por linhas desc — candidatas concretas de referência
const porDataset = new Map<string, any[]>();
for (const t of meta.tabelas as any[]) {
  const ds = t.id.split(".")[0];
  if (!porDataset.has(ds)) porDataset.set(ds, []);
  porDataset.get(ds)!.push(t);
}
for (const l of porDataset.values()) l.sort((a, b) => b.linhas - a.linhas);

function resolver(curto: string): string | null {
  const limpo = curto.trim().replace(/\\?\*/g, "").replace(/^\d+\s*[+–-]?\d*\s*:\s*/, "").trim();
  const candidatos = [`br_${limpo}`, limpo];
  for (const c of candidatos) if (datasetsCatalogo.has(c)) return c;
  return null;
}

const reTema = /^## (\d+) · (.+)$/gm;
const reItem = /^(\d+)\.\s+(.+?)\s+\*\(n=([0-9+–-]+):\s*(.+?)\)\*\s*$/gm;
const perguntas: any[] = [];
const semMatch = new Map<string, number>();
let temaAtual: string | null = null;

const linhas = md.split("\n");
let textoAcumulado: string[] = [];

for (const linha of linhas) {
  const mTema = linha.match(/^## (\d+) · (.+)$/);
  if (mTema) { temaAtual = `${mTema[1].padStart(2, "0")} · ${mTema[2]!.trim()}`; continue; }
  if (linha.startsWith("#")) { temaAtual = temaAtual && !linha.startsWith("## ") ? "multi-família" : null; continue; }

  // formato dos 5 finais: `1. **título**: pergunta (n=…; chaves: …)` — 4 grupos;
  // formato dos temas: `1. pergunta (n=3: ds1, ds2*)` — 3 grupos
  const mFinal = linha.match(/^(\d+)\.\s+\*\*(.+?)\*\*:?\s*(.+?)\s+\*\(n=(.+?)\)\*\s*$/);
  const mSimples = linha.match(/^(\d+)\.\s+(.+?)\s+\*\(n=(.+?)\)\*\s*$/);
  let q: string, espec: string;
  if (mFinal && !mSimples) { q = `${mFinal[2]}: ${mFinal[3]}`; espec = mFinal[4]!; }
  else if (mSimples) { q = mSimples[2]!; espec = mSimples[3]!; }
  else continue;
  if (!temaAtual) continue;

  // separa datasets de eventuais chaves anotadas: "...; chaves: id_municipio, sigla_uf"
  const [parteDs] = espec!.split(/;\s*(?:chaves|Chaves):/);
  const curtos = parteDs!.split(",").map((s) => s.trim()).filter(Boolean);

  const resolvidos: string[] = [];
  let naoAchou = false;
  for (const c of curtos) {
    const ds = resolver(c);
    if (ds) { if (!resolvidos.includes(ds)) resolvidos.push(ds); }
    else {
      const chave = c.replace(/\\?\*/g, "").replace(/^\d+\s*[+–-]?\d*\s*:\s*/, "").trim();
      naoAchou = true; semMatch.set(chave, (semMatch.get(chave) ?? 0) + 1);
    }
  }
  if (resolvidos.length < 2) continue;   // deixou de ser multi-dataset

  const tabelasRef = Object.fromEntries(resolvidos.map((ds) =>
    [ds, (porDataset.get(ds) ?? []).slice(0, 3).map((t: any) => t.id)]));

  perguntas.push({
    tema: temaAtual,
    n: perguntas.length + 1,
    q: q.replace(/\s+/g, " ").trim(),
    datasets: resolvidos,
    tabelas_ref: tabelasRef,
    sem_match: naoAchou || undefined,
  });
}

const conteudo = JSON.stringify({
  _meta: {
    origem: MD,
    sobre: "Conjunto dourado TEMAS (43 temas x 5 + 5 multi-familia). Expectativa é de " +
           "DATASET: recuperacao boa = >=1 tabela de cada dataset citado. tabelas_ref sao " +
           "as 3 maiores tabelas de cada dataset, so para referencia humana.",
    criterios: ["recall@k por dataset (>=1 tabela de cada)", "SQL cita tabelas de 2+ datasets",
                "executa sem erro", "resultado não é vazio/nulo"],
  },
  perguntas,
}, null, 1);

writeFileSync("tasks/douradas_temas.json", conteudo);
writeFileSync("web/static/_douradas_temas.json", conteudo);

const porTema = new Map<string, number>();
for (const p of perguntas) porTema.set(p.tema!, (porTema.get(p.tema!) ?? 0) + 1);
console.log(`${perguntas.length} perguntas de ${porTema.size} temas`);
console.log(`datasets distintos: ${new Set(perguntas.flatMap((p) => p.datasets)).size}`);
if (semMatch.size) {
  console.log(`\n${semMatch.size} nome(s) curto(s) SEM match no catálogo:`);
  for (const [nome, vezes] of [...semMatch].sort((a, b) => b[1] - a[1])) console.log(`  ${nome} (${vezes}x)`);
}
