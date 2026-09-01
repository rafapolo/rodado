/**
 * Catálogo do espelho — as duas fontes que o harness usa para navegar.
 *
 *  1. `~/rodado/_rodado_metadata/catalog.parquet` (beelink) — quantas linhas
 *     cada tabela tem. É o que o portão precisa para saber quando exigir filtro
 *     de partição. Cacheado em `harness/dados/catalogo.json`; regerar com
 *     `bun harness/catalogo.ts --atualiza` depois de qualquer sync.
 *
 *  2. `docs/context/basedosdados-schema.json` (local) — colunas por tabela.
 *     Lido do disco, sem ssh.
 *
 * Por que o catálogo por DATASET e não por tabela no prompt: medido em
 * 2026-09-01, os 212 nomes de dataset são 1.954 tokens e as 904 tabelas são
 * 14.570. Com o cache de prefixo do llama-server o catálogo de dataset sai de
 * graça a partir da 2ª pergunta, e a escolha de dataset acertou 88% (15/17)
 * contra os 52,9% do search_tables por embedding.
 */
import { readFileSync, existsSync, writeFileSync } from "node:fs";
import { runSqlSsh } from "./beelink.ts";

const RAIZ = new URL("..", import.meta.url).pathname;
const CACHE = `${RAIZ}harness/dados/catalogo.json`;
const SCHEMA = `${RAIZ}docs/context/basedosdados-schema.json`;

export interface EntradaCatalogo {
  dataset: string;
  tabela: string;
  linhas: number;
}

export interface Coluna {
  name: string;
  type: string;
}

/** Acima disto o portão exige filtro de partição. Uma varredura cheia numa
 *  tabela deste porte segura o lock do DuckDB por minutos ou horas. */
export const LIMIAR_PARTICAO = 10_000_000;

/** Colunas que servem de partição neste espelho. */
export const COLUNAS_PARTICAO = ["ano", "mes", "sigla_uf"] as const;

let _catalogo: EntradaCatalogo[] | null = null;
let _schema: Record<string, Record<string, Coluna[]>> | null = null;

export function catalogo(): EntradaCatalogo[] {
  if (_catalogo) return _catalogo;
  if (!existsSync(CACHE)) {
    throw new Error(
      `Cache do catálogo ausente em ${CACHE}. Rode: bun harness/catalogo.ts --atualiza`,
    );
  }
  _catalogo = JSON.parse(readFileSync(CACHE, "utf8")) as EntradaCatalogo[];
  return _catalogo;
}

function schema(): Record<string, Record<string, Coluna[]>> {
  if (_schema) return _schema;
  _schema = JSON.parse(readFileSync(SCHEMA, "utf8"));
  return _schema!;
}

/** Os 212 nomes de dataset, um por linha — o catálogo que vai no prefixo. */
export function listaDatasets(): string[] {
  return [...new Set(catalogo().map((e) => e.dataset))].sort();
}

export function tabelasDe(dataset: string): EntradaCatalogo[] {
  return catalogo().filter((e) => e.dataset === dataset);
}

/** Linhas de `dataset.tabela`, ou null se desconhecida. */
export function linhasDe(id: string): number | null {
  const [ds, tb] = partir(id);
  return catalogo().find((e) => e.dataset === ds && e.tabela === tb)?.linhas ?? null;
}

/** Colunas de `dataset.tabela` a partir do schema local. */
export function colunasDe(id: string): Coluna[] | null {
  const [ds, tb] = partir(id);
  return schema()[ds]?.[tb] ?? null;
}

/** As colunas de partição que a tabela realmente tem. */
export function particoesDe(id: string): string[] {
  const cols = colunasDe(id);
  if (!cols) return [];
  const nomes = new Set(cols.map((c) => c.name.toLowerCase()));
  return COLUNAS_PARTICAO.filter((p) => nomes.has(p));
}

/** Schema completo de um dataset, para o modelo navegar. */
export function schemaDoDataset(dataset: string): Record<string, Coluna[]> | null {
  return schema()[dataset] ?? null;
}

function partir(id: string): [string, string] {
  const i = id.indexOf(".");
  return i < 0 ? [id, ""] : [id.slice(0, i), id.slice(i + 1)];
}

/** Rebusca o catálogo no beelink e regrava o cache. */
export async function atualiza(): Promise<number> {
  const sql = `
    SELECT dataset, "table" AS tabela, rows AS linhas
    FROM read_parquet('~/rodado/_rodado_metadata/catalog.parquet')
    WHERE source <> 'view_only'
    ORDER BY dataset, tabela`;
  const r = await runSqlSsh(sql);
  if (r.error) throw new Error(`catalog.parquet: ${r.error}`);
  const linhas = (r.rows ?? []).map((x) => ({
    dataset: String(x.dataset),
    tabela: String(x.tabela),
    linhas: Number(x.linhas ?? 0),
  }));
  writeFileSync(CACHE, JSON.stringify(linhas, null, 0));
  _catalogo = linhas;
  return linhas.length;
}

if (import.meta.main) {
  if (Bun.argv.includes("--atualiza")) {
    const n = await atualiza();
    console.log(`catálogo atualizado: ${n} tabelas -> harness/dados/catalogo.json`);
  } else {
    const ds = listaDatasets();
    console.log(`${ds.length} datasets, ${catalogo().length} tabelas`);
  }
}
