#!/usr/bin/env bun
/**
 * Renderiza o .md de cada análise em HTML, com o MESMO marked que o navegador
 * carrega (12.0.2, fixado em package.json e no <script> das páginas), para o
 * gera_analises.py gravar o corpo pronto dentro de #doc: o leitor vê o texto
 * sem esperar o JS, e crawler/prévia de link (que não rodam JS) também.
 *
 * Uso: bun scripts/renderiza_analises.ts <slug>...   → JSON {slug: html} no stdout
 * As páginas geradas não carregam mais o marked; ele segue só em
 * pages/analises/index.html, para o ?doc=<slug> antigo. Ao mudar a versão,
 * mudar nos dois lugares, ou o texto daqui e o do ?doc= passam a divergir.
 */
import { marked } from "marked";
import { readFileSync } from "node:fs";
import { join, resolve } from "node:path";

const RESULTS = resolve(import.meta.dir, "..", "pages", "analises", "results");

const saida: Record<string, string> = {};
for (const slug of process.argv.slice(2)) {
  const md = readFileSync(join(RESULTS, `${slug}.md`), "utf8");
  let i = 0;
  // como o viewer.js fazia depois de montar: a 1ª figura carrega já, as outras
  // só perto da tela. No HTML estático isso precisa estar no atributo, senão o
  // navegador baixa todas antes do JS rodar
  saida[slug] = (marked.parse(md, { async: false }) as string).replace(/<img /g, () =>
    i++ === 0 ? '<img decoding="async" ' : '<img decoding="async" loading="lazy" ');
}
process.stdout.write(JSON.stringify(saida));
