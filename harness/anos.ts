/**
 * Faixa de anos por tabela — o fato que faltava.
 *
 * Diagnosticado em 2026-09-01: o modelo escreveu uma consulta CAGED × RAIS × PIB
 * bem formada, com as chaves certas e LPAD nas duas pontas, e o join devolveu
 * n=0. A causa não estava no SQL: `br_ibge_pib.municipio` termina em **2021** e
 * ele filtrou `ano = 2022`. Não tinha como saber — nada no prompt dizia.
 *
 * Uma consulta por tabela, cacheada em disco. Regerar depois de um sync com
 * `bun harness/anos.ts --atualiza`.
 */
import { readFileSync, existsSync, writeFileSync } from "node:fs";
import { runSqlSsh } from "./beelink.ts";
import { catalogo, colunasDe } from "./catalogo.ts";

const CACHE = new URL("dados/anos.json", import.meta.url).pathname;

export interface Faixa { min: number; max: number }

let _f: Record<string, Faixa> | null = null;

function carrega(): Record<string, Faixa> {
  if (_f) return _f;
  _f = existsSync(CACHE) ? JSON.parse(readFileSync(CACHE, "utf8")) : {};
  return _f!;
}

/** Faixa de anos de `dataset.tabela`, ou null se a tabela não é particionada por ano. */
export function faixaDeAnos(id: string): Faixa | null {
  return carrega()[id] ?? null;
}

/** Texto pronto para o prompt, ou "" quando não há faixa conhecida. */
export function textoFaixa(id: string): string {
  const f = faixaDeAnos(id);
  return f ? `  anos disponíveis: ${f.min}–${f.max}` : "";
}

export async function atualiza(): Promise<number> {
  const alvos = catalogo()
    .map((e) => `${e.dataset}.${e.tabela}`)
    .filter((id) => (colunasDe(id) ?? []).some((c) => c.name.toLowerCase() === "ano"));

  const out: Record<string, Faixa> = {};
  let feitas = 0;
  // Uma consulta por lote de tabelas: min/max de `ano` é barato num parquet
  // particionado (lê só a estatística do arquivo), mas 600 idas de ssh não são.
  const LOTE = 25;
  for (let i = 0; i < alvos.length; i += LOTE) {
    const lote = alvos.slice(i, i + LOTE);
    const sql = lote
      .map((id) => `SELECT '${id}' AS t, min(ano) AS lo, max(ano) AS hi FROM ${id}`)
      .join("\nUNION ALL\n");
    const r = await runSqlSsh(sql);
    if (r.error) { console.error(`lote ${i}: ${r.error.slice(0, 120)}`); continue; }
    for (const linha of r.rows ?? []) {
      const lo = Number(linha.lo), hi = Number(linha.hi);
      if (Number.isFinite(lo) && Number.isFinite(hi)) out[String(linha.t)] = { min: lo, max: hi };
    }
    feitas += lote.length;
    console.error(`  ${feitas}/${alvos.length}`);
  }
  writeFileSync(CACHE, JSON.stringify(out));
  _f = out;
  return Object.keys(out).length;
}

if (import.meta.main) {
  if (Bun.argv.includes("--atualiza")) {
    console.log(`${await atualiza()} tabelas com faixa de anos -> harness/dados/anos.json`);
  } else {
    const f = carrega();
    console.log(`${Object.keys(f).length} tabelas com faixa conhecida`);
    for (const id of ["br_ibge_pib.municipio", "br_me_caged.microdados_movimentacao", "br_ms_sim.microdados"]) {
      console.log(`  ${id}: ${JSON.stringify(f[id] ?? null)}`);
    }
  }
}
