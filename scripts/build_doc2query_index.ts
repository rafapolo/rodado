#!/usr/bin/env bun
/**
 * Junta as saídas do doc2query num índice MULTI-VETOR para o navegador.
 *
 *   bun run scripts/build_doc2query_index.ts          # -> perguntas.json
 *   bun run scripts/build_doc2query_index.ts --int8   # vetores em int8
 *
 * Multi-vetor: cada pergunta sintética vira um vetor próprio e o score da
 * tabela é o MÁXIMO, nunca a média. Foi a diluição que derrubou a tentativa de
 * prosa+colunas (0,33 contra 0,39 da prosa sozinha); com máximo, acrescentar
 * pergunta nunca dilui.
 *
 * Este script só monta a lista de textos. Os vetores são gerados no navegador
 * por web/diag/embeda_perguntas.html — o mesmo modelo que atende a consulta em
 * runtime, o que elimina qualquer descasamento entre quem indexa e quem busca.
 */
import { readFileSync, writeFileSync, readdirSync, existsSync } from "node:fs";

const DIR = "tasks/doc2query";
const OUT = "web/static/index";

const arquivos = readdirSync(DIR).filter((f) => f.startsWith("saida_") && f.endsWith(".jsonl")).sort();
if (!arquivos.length) throw new Error(`Nenhuma saída em ${DIR}/ — rode scripts/doc2query_roda.ts antes.`);

const meta = JSON.parse(readFileSync(`${OUT}/meta.json`, "utf-8"));
const conhecidas = new Set<string>(meta.tabelas.map((t: any) => t.id));

const porTabela = new Map<string, string[]>();
let ignoradas = 0, incertas = 0;

for (const f of arquivos) {
  for (const linha of readFileSync(`${DIR}/${f}`, "utf-8").trim().split("\n")) {
    if (!linha.trim() || linha.trim().startsWith("```")) continue;
    let d: any;
    try { d = JSON.parse(linha); } catch { continue; }
    if (!conhecidas.has(d.id)) { ignoradas++; continue; }   // tabela saiu do catálogo
    if (d.incerta) incertas++;
    const atual = porTabela.get(d.id) ?? [];
    for (const q of d.perguntas ?? []) if (typeof q === "string" && q.length > 7) atual.push(q);
    porTabela.set(d.id, [...new Set(atual)]);               // dedup: lote repetido não infla o índice
  }
}

const entradas: { id: string; q: string }[] = [];
for (const [id, qs] of porTabela) for (const q of qs) entradas.push({ id, q });

const semPerguntas = [...conhecidas].filter((id) => !porTabela.has(id));

writeFileSync(`${OUT}/perguntas.json`, JSON.stringify({
  entradas,
  cobertura: { tabelas: porTabela.size, de: conhecidas.size, vetores: entradas.length },
}));

console.log(`${entradas.length} perguntas de ${porTabela.size}/${conhecidas.size} tabelas`);
console.log(`  media: ${(entradas.length / porTabela.size).toFixed(1)} por tabela`);
if (incertas) console.log(`  ${incertas} tabela(s) marcadas "incerta" pelo gerador`);
if (ignoradas) console.log(`  ${ignoradas} linha(s) de tabela fora do catálogo, descartadas`);
if (semPerguntas.length) {
  // Falar alto: tabela sem pergunta fica invisivel para a busca semantica, e
  // isso tem que ser um numero na tela, nao uma descoberta em producao.
  console.log(`\n  ${semPerguntas.length} TABELA(S) SEM NENHUMA PERGUNTA — invisíveis para a busca:`);
  for (const id of semPerguntas.slice(0, 10)) console.log(`    ${id}`);
  if (semPerguntas.length > 10) console.log(`    … e mais ${semPerguntas.length - 10}`);
}
console.log(`\nvetores a gerar: ${entradas.length} × 384  →  ` +
  `${(entradas.length * 384 * 4 / 1048576).toFixed(1)} MB f32 / ${(entradas.length * 384 / 1048576).toFixed(1)} MB int8`);
