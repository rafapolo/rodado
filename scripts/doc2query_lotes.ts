#!/usr/bin/env bun
/**
 * Divide as 824 tabelas em lotes prontos para o prompt scripts/prompts/doc2query.md.
 *
 *   bun run scripts/doc2query_lotes.ts            # lotes de 25 -> tasks/doc2query/
 *   bun run scripts/doc2query_lotes.ts --lote 40
 *
 * Depois, no Claude Code, para cada lote:
 *   "Siga scripts/prompts/doc2query.md para tasks/doc2query/lote_01.jsonl,
 *    grave em tasks/doc2query/saida_01.jsonl"
 *
 * As colunas vão cortadas em 40: o prompt precisa saber do que a tabela trata,
 * não da lista inteira — br_inep_censo_escolar.escola tem 455.
 */
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";

const N = Number(process.argv[Bun.argv.indexOf("--lote") + 1]) || 25;
const DIR = "tasks/doc2query";

const meta = JSON.parse(readFileSync("web/static/index/meta.json", "utf-8"));
const colunas = JSON.parse(readFileSync("web/static/index/colunas.json", "utf-8"));
mkdirSync(DIR, { recursive: true });

const linhas = meta.tabelas.map((t: any) => JSON.stringify({
  id: t.id, dataset: t.dataset, tabela: t.tabela, linhas: t.linhas,
  colunas: (colunas[t.id] ?? []).slice(0, 40).map((c: any) => c.n),
}));

let n = 0;
for (let i = 0; i < linhas.length; i += N) {
  n++;
  const nome = `${DIR}/lote_${String(n).padStart(2, "0")}.jsonl`;
  writeFileSync(nome, linhas.slice(i, i + N).join("\n") + "\n");
}

// Um lote de amostra pra conferir a qualidade antes de gastar os 33 restantes.
const amostra = ["br_ms_sim.microdados", "br_ms_sinasc.microdados", "br_tse_eleicoes.candidatos",
  "br_bd_diretorios_brasil.municipio", "br_inep_enem.microdados", "br_me_caged.microdados_movimentacao",
  "br_anp_combustiveis.precos", "br_pgfn_dividaativa.divida"];
const sel = linhas.filter((l: string) => amostra.includes(JSON.parse(l).id));
writeFileSync(`${DIR}/lote_00_amostra.jsonl`, sel.join("\n") + "\n");

console.log(`${meta.tabelas.length} tabelas -> ${n} lotes de ${N} em ${DIR}/`);
console.log(`Comece por lote_00_amostra.jsonl (${sel.length} tabelas conhecidas) e confira a saída.`);
console.log(`\nNo Claude Code, por lote:`);
console.log(`  Siga scripts/prompts/doc2query.md para ${DIR}/lote_01.jsonl, grave em ${DIR}/saida_01.jsonl`);
