#!/usr/bin/env bun
/**
 * Empacota, para o navegador, tudo que o ask-web precisa ter na mão:
 *
 *   web/static/index/vectors.bin   Float32 824×384, ordem igual a meta.json
 *   web/static/index/meta.json     id, dataset, tabela, linhas, duplicada
 *   web/static/index/colunas.json  colunas por tabela (orçamento + validação)
 *   web/static/index/semantica.json  métricas, false_friends, pontes
 *
 * Rodar depois de `scripts/update_embeddings.py`, e depois de qualquer sync
 * que mude tabelas.
 *
 *   bun run scripts/build_ask_web_assets.ts
 */
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { parse as parseYaml } from "yaml";
import { runSqlSsh } from "../web/src/beelink.ts";

const CTX = "docs/context";
const OUT = "web/static/index";
const MODELO_ESPERADO = "paraphrase-multilingual-MiniLM-L12-v2";

interface TableEmbedding { id: string; text: string; embedding: number[] }

async function main() {
  mkdirSync(OUT, { recursive: true });

  // ---- índice de embeddings ------------------------------------------------
  const idx = JSON.parse(readFileSync(`${CTX}/table_embeddings.json`, "utf-8")) as
    { tables: TableEmbedding[]; model: string };

  // Falhar alto: a TUI Rust ranqueava com o modelo errado (all-MiniLM-L6-v2
  // contra um índice multilingual) e ninguém percebeu por meses, porque as duas
  // têm 384 dims e o cosseno "roda". Se o modelo mudar, o navegador tem que
  // parar aqui, não gerar um índice que ele vai consultar no espaço errado.
  if (idx.model !== MODELO_ESPERADO) {
    throw new Error(
      `table_embeddings.json diz model="${idx.model}", esperado "${MODELO_ESPERADO}".\n` +
      `O navegador embeda com o modelo esperado; espaços vetoriais diferentes ` +
      `produzem ranking que parece plausível e é ruído. Abortando.`);
  }

  const dims = idx.tables[0]!.embedding.length;
  if (dims !== 384) throw new Error(`Esperava 384 dims, veio ${dims}.`);
  for (const t of idx.tables) {
    if (t.embedding.length !== dims) throw new Error(`${t.id} tem ${t.embedding.length} dims, esperado ${dims}.`);
  }

  // ---- catálogo: linhas e o que é view órfã --------------------------------
  // Filtra source <> 'view_only' (NUNCA source = 'disk'): as tabelas
  // duckdb_native leem tabelas nativas dentro do .duckdb e valem 250M linhas
  // que o parquet_metadata contava como zero.
  const cat = await runSqlSsh(
    `SELECT dataset, "table" AS tabela, rows, source FROM _rodado_metadata WHERE source <> 'view_only'`);
  if (cat.error) throw new Error(`Catálogo indisponível no beelink: ${cat.error}`);
  const linhas = new Map<string, number>();
  const fonte = new Map<string, string>();
  for (const r of cat.rows as { dataset: string; tabela: string; rows: number; source: string }[]) {
    linhas.set(`${r.dataset}.${r.tabela}`, Number(r.rows));
    fonte.set(`${r.dataset}.${r.tabela}`, r.source);
  }

  // ---- as tabelas que devolvem toda linha duas vezes -----------------------
  const jk = readFileSync(`${CTX}/join_keys.md`, "utf-8");
  const bloco = jk.match(/<details><summary>All (\d+) affected tables<\/summary>([\s\S]*?)<\/details>/);
  const duplicadas = new Set(bloco ? [...bloco[2]!.matchAll(/`([\w.]+)`/g)].map(m => m[1]!) : []);

  // ---- vetores + meta, só do que existe no catálogo ------------------------
  const mantidas = idx.tables.filter(t => linhas.has(t.id));
  const buf = new Float32Array(mantidas.length * dims);
  const meta = mantidas.map((t, i) => {
    buf.set(t.embedding, i * dims);
    const [dataset, ...resto] = t.id.split(".");
    return {
      id: t.id,
      dataset,
      tabela: resto.join("."),
      linhas: linhas.get(t.id) ?? 0,
      fonte: fonte.get(t.id),
      duplicada: duplicadas.has(t.id) || undefined,
    };
  });
  writeFileSync(`${OUT}/vectors.bin`, Buffer.from(buf.buffer));
  writeFileSync(`${OUT}/meta.json`, JSON.stringify({ dims, tabelas: meta }));

  // ---- colunas: o orçamento de prompt e a validação local ------------------
  // basedosdados-schema.json, não schemas.json: aquele tem as 824 tabelas
  // (casando 1:1 com o índice de embeddings) e tipos lógicos (INTEGER, STRING),
  // enquanto schemas.json tem 778 e tipos físicos do parquet (INT64, BYTE_ARRAY).
  // Nenhum dos dois carrega descrição de coluna — são 0 de 38.095 — então o
  // orçamento de prompt ranqueia por nome, chave e partição, sem prosa.
  const schema = JSON.parse(readFileSync(`${CTX}/basedosdados-schema.json`, "utf-8")) as
    Record<string, Record<string, { name: string; type: string }[]>>;
  const colunas: Record<string, { n: string; t: string }[]> = {};
  for (const m of meta) {
    const cols = schema[m.dataset!]?.[m.tabela];
    if (cols) colunas[m.id] = cols.map(c => ({ n: c.name, t: c.type }));
  }
  writeFileSync(`${OUT}/colunas.json`, JSON.stringify(colunas));

  // ---- camada semântica: métricas, false_friends, pontes -------------------
  const br = parseYaml(readFileSync(`${CTX}/bridges.yaml`, "utf-8"));
  const mt = JSON.parse(readFileSync(`${CTX}/metrics.json`, "utf-8"));
  writeFileSync(`${OUT}/semantica.json`, JSON.stringify({
    metricas: mt.metrics,
    false_friends: br.false_friends,
    pontes: br.bridges,
    conceitos: Object.fromEntries(Object.entries(br.concepts as Record<string, any>)
      .map(([k, v]) => [k, { categoria: v.category, canonica: v.canonical_table }])),
  }));

  // ---- exemplares few-shot: receita verificada entra no prompt -------------
  // Falhar alto sem carimbo verified datado — mesma regra de metrics.yaml:
  // exemplar aspiracional ensina o modelo a escrever SQL que não roda.
  const ex = parseYaml(readFileSync(`${CTX}/exemplos_sql.yaml`, "utf-8"));
  const exemplares = Object.entries(ex.exemplos as Record<string, any>).map(([id, e]) => ({
    id,
    quando: e.quando,
    gatilhos: e.gatilhos,
    datasets: e.datasets,
    sql: e.sql,
    verified: e.verified,
  }));
  if (!exemplares.length) throw new Error(`exemplos_sql.yaml não gerou nenhum exemplar.`);
  for (const e of exemplares) {
    if (!/\(\d{4}-\d{2}-\d{2}\)/.test(e.verified ?? "")) {
      throw new Error(`exemplar ${e.id} sem carimbo verified datado.`);
    }
  }
  writeFileSync(`${OUT}/exemplos.json`, JSON.stringify({ exemplos: exemplares }));

  const kb = (p: string) => (Bun.file(p).size / 1024).toFixed(0) + " KB";
  console.log(`${meta.length} tabelas × ${dims} dims`);
  console.log(`  vectors.bin    ${kb(`${OUT}/vectors.bin`)}`);
  console.log(`  meta.json      ${kb(`${OUT}/meta.json`)}`);
  console.log(`  colunas.json   ${kb(`${OUT}/colunas.json`)}`);
  console.log(`  semantica.json ${kb(`${OUT}/semantica.json`)}  (${mt.metrics.length} métricas, ${Object.keys(br.false_friends).length} false_friends)`);
  console.log(`  exemplos.json  ${kb(`${OUT}/exemplos.json`)}  (${exemplares.length} exemplares verificados)`);
  console.log(`  ${duplicadas.size} tabelas duplicadas marcadas`);
  const semSchema = meta.length - Object.keys(colunas).length;
  if (semSchema > 0) console.log(`  aviso: ${semSchema} tabela(s) sem colunas no schemas.json`);
}

main();
