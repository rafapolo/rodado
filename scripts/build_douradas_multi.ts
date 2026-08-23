#!/usr/bin/env bun
/**
 * Converte docs/relatorio-social/perguntas.md no conjunto dourado MULTI-TABELA.
 *
 *   bun run scripts/build_douradas_multi.ts   # -> tasks/douradas_multi.json
 *
 * Aquele documento já é o que uma bancada precisa: 50 perguntas de pesquisa
 * reais, cada uma com as tabelas-fonte anotadas à mão. Todas as 50 são
 * multi-tabela (2 a 4 fontes), que é exatamente o caso que o app ainda não
 * resolve.
 *
 * Tabela citada que não existe no catálogo é DESCARTADA da expectativa, não
 * silenciosamente aceita: cobrar do sistema uma tabela inexistente mede o nada.
 */
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";

const md = readFileSync("docs/relatorio-social/perguntas.md", "utf-8");
const catalogo = new Set<string>(
  JSON.parse(readFileSync("web/static/index/meta.json", "utf-8")).tabelas.map((t: any) => t.id));

const re = /\*\*(\d+)\.\s*(.+?)\*\*\s*\n\s*\n?\s*-\s*\*\*Fontes:\*\*\s*(.+?)(?:\n\n|\n#)/gs;
const perguntas: any[] = [];
const fantasmas = new Set<string>();

for (const m of md.matchAll(re)) {
  const [, n, textoBruto, fontes] = m;
  const citadas = [...fontes!.matchAll(/`([\w.]+)`/g)].map((x) => x[1]!);
  const validas = citadas.filter((t) => catalogo.has(t));
  citadas.filter((t) => !catalogo.has(t)).forEach((t) => fantasmas.add(t));
  if (validas.length < 2) continue;                  // deixou de ser multi-tabela

  perguntas.push({
    n: Number(n),
    q: textoBruto!.replace(/\s+/g, " ").trim(),
    tabelas: validas,
    descartadas: citadas.length - validas.length || undefined,
    datasets: [...new Set(validas.map((t) => t.split(".")[0]))],
  });
}

mkdirSync("tasks", { recursive: true });
writeFileSync("tasks/douradas_multi.json", JSON.stringify({
  _meta: {
    origem: "docs/relatorio-social/perguntas.md",
    sobre: "Conjunto dourado MULTI-TABELA. Mede se a recuperação traz TODAS as " +
           "pontas de uma pergunta de pesquisa, e se o modelo escreve o JOIN. " +
           "As 15 de tasks/ask_web_douradas.json medem o caso de uma tabela só.",
    criterios: ["recall@k das tabelas esperadas", "SQL cita 2+ tabelas",
                "SQL tem JOIN", "executa sem erro", "resultado não é vazio/nulo"],
  },
  perguntas,
}, null, 1));

const porN = perguntas.reduce((a: any, p) => (a[p.tabelas.length] = (a[p.tabelas.length] ?? 0) + 1, a), {});
console.log(`${perguntas.length} perguntas multi-tabela`);
console.log(`  por nº de tabelas: ${Object.entries(porN).map(([k, v]) => `${k}→${v}`).join("  ")}`);
console.log(`  datasets distintos: ${new Set(perguntas.flatMap((p) => p.datasets)).size}`);
if (fantasmas.size) {
  console.log(`\n  ${fantasmas.size} tabela(s) citada(s) que não existem, descartadas:`);
  for (const f of fantasmas) console.log(`    ${f}`);
}
