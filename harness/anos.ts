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

  const antes = carrega();
  const out: Record<string, Faixa> = {};
  let feitas = 0;
  const guarda = (linhas: Record<string, unknown>[] | undefined) => {
    for (const linha of linhas ?? []) {
      const lo = Number(linha.lo), hi = Number(linha.hi);
      if (Number.isFinite(lo) && Number.isFinite(hi)) out[String(linha.t)] = { min: lo, max: hi };
    }
  };
  const sqlDe = (id: string) => `SELECT '${id}' AS t, min(ano) AS lo, max(ano) AS hi FROM ${id}`;
  // Uma consulta por lote de tabelas: min/max de `ano` é barato num parquet
  // particionado (lê só a estatística do arquivo), mas 600 idas de ssh não são.
  const LOTE = 25;
  for (let i = 0; i < alvos.length; i += LOTE) {
    const lote = alvos.slice(i, i + LOTE);
    const r = await runSqlSsh(lote.map(sqlDe).join("\nUNION ALL\n"));
    if (!r.error) guarda(r.rows);
    else {
      // Uma tabela lenta derruba o lote inteiro (2026-09-27: as views SIPNI,
      // que leem do R2 remoto, estouravam 120 s e levavam 23 tabelas junto).
      // Refaz uma a uma; a que falhar sozinha mantém a faixa que já tinha.
      console.error(`lote ${i}: ${r.error.slice(0, 120)} — refazendo tabela a tabela`);
      for (const id of lote) {
        const u = await runSqlSsh(sqlDe(id));
        if (!u.error) guarda(u.rows);
        else if (antes[id]) { out[id] = antes[id]; console.error(`  ${id}: falhou, mantida a faixa anterior`); }
        else console.error(`  ${id}: ${u.error.slice(0, 80)}`);
      }
    }
    feitas += lote.length;
    console.error(`  ${feitas}/${alvos.length}`);
  }
  // As tabelas sem coluna `ano` vêm de `--outras` (ano_mes, ano_competencia…):
  // refazer o cache do zero apagava as 19 (Bolsa Família, arrecadação, ISP).
  // Mantém as que seguem no catálogo.
  const noCatalogo = new Set(catalogo().map((e) => `${e.dataset}.${e.tabela}`));
  for (const [id, f] of Object.entries(antes)) {
    if (!out[id] && !alvos.includes(id) && noCatalogo.has(id)) out[id] = f;
  }
  writeFileSync(CACHE, JSON.stringify(out));
  _f = out;
  return Object.keys(out).length;
}

/**
 * Tabelas sem coluna `ano` que ainda assim têm o ano em outra coluna. Sem a
 * faixa, `listar_tabelas` não mostrava que br_mc_indicadores termina em 2020 e
 * o Novo Bolsa Família começa em 2023 — e o modelo não tinha como trocar de
 * fonte. Acrescenta ao cache existente, sem refazer as ~400 de `ano`.
 */
const OUTRAS: [string, (c: string) => string][] = [
  ["ano_referencia", (c) => c], ["ano_competencia", (c) => c], ["ano_emissao", (c) => c],
  ["ano_mes", (c) => `CAST(substr(CAST(${c} AS VARCHAR), 1, 4) AS INTEGER)`],
];

export async function atualizaOutras(): Promise<number> {
  const f = carrega();
  let n = 0;
  for (const e of catalogo()) {
    const id = `${e.dataset}.${e.tabela}`;
    if (f[id]) continue;
    const nomes = new Set((colunasDe(id) ?? []).map((c) => c.name.toLowerCase()));
    const achada = OUTRAS.find(([c]) => nomes.has(c));
    if (!achada) continue;
    const expr = achada[1](achada[0]);
    const r = await runSqlSsh(`SELECT min(${expr}) AS lo, max(${expr}) AS hi FROM ${id}`);
    const lo = Number(r.rows?.[0]?.lo), hi = Number(r.rows?.[0]?.hi);
    if (r.error || !Number.isFinite(lo) || !Number.isFinite(hi)) { console.error(`${id}: ${r.error?.slice(0, 100) ?? "sem faixa"}`); continue; }
    f[id] = { min: lo, max: hi };
    n++;
    console.error(`  ${id}: ${lo}–${hi}`);
  }
  writeFileSync(CACHE, JSON.stringify(f));
  return n;
}

if (import.meta.main) {
  if (Bun.argv.includes("--outras")) {
    console.log(`${await atualizaOutras()} tabelas acrescentadas -> harness/dados/anos.json`);
  } else if (Bun.argv.includes("--atualiza")) {
    console.log(`${await atualiza()} tabelas com faixa de anos -> harness/dados/anos.json`);
  } else {
    const f = carrega();
    console.log(`${Object.keys(f).length} tabelas com faixa conhecida`);
    for (const id of ["br_ibge_pib.municipio", "br_me_caged.microdados_movimentacao", "br_ms_sim.microdados"]) {
      console.log(`  ${id}: ${JSON.stringify(f[id] ?? null)}`);
    }
  }
}
