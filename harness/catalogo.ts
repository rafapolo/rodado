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
  /** status do _rodado_metadata: mirrored, done, blocked, redundante... */
  status?: string;
  /** notas de procedência — carregam avisos como "está VAZIO, use o novo" */
  notas?: string;
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

/**
 * Índice de datasets aposentados — construído das notas de procedência de TODOS
 * os outros, porque um dataset quebrado raramente se denuncia.
 *
 * O caso que motivou isto: `br_ibama_embargos` tem 497 mil linhas em uma de suas
 * tabelas e `status = 'done'`. Nenhuma coluna de metadado a acusa: as linhas
 * existem, os *valores* é que são strings vazias — o CSV foi parseado errado e os
 * bytes nunca chegaram (`max(length()) = 0`). Ela não falha, responde zero, e o
 * zero passa por resposta: "não há embargos" no lugar de "não há dado". O único
 * sinal no espelho inteiro é a nota do dataset que a substituiu, dizendo
 * "Substitui `br_ibama_embargos`, que está VAZIO".
 */
let _aposentados: Map<string, string> | null = null;
function aposentados(): Map<string, string> {
  if (_aposentados) return _aposentados;
  const m = new Map<string, string>();
  for (const e of catalogo()) {
    if (!e.notas) continue;
    for (const [, alvo] of e.notas.matchAll(/Substitui\s+`([a-z0-9_.]+)`/gi)) {
      const frase = e.notas.match(new RegExp(`[^.]*${alvo}[^.]*\\.`))?.[0]?.trim();
      m.set(alvo.toLowerCase(), frase ?? `substituído por ${e.dataset}`);
    }
  }
  _aposentados = m;
  return m;
}

/**
 * Tabela que não serve para consulta, e por quê — ou null se está de pé.
 * Três sinais, do mais forte ao mais sutil: aposentada por outro dataset,
 * marcada como redundante no status, ou sem nenhuma linha.
 */
export function inservivel(id: string): string | null {
  const [ds, tb] = partir(id);
  const ap = aposentados();
  const motivo = ap.get(id.toLowerCase()) ?? ap.get(ds.toLowerCase());
  if (motivo) {
    return `${id} foi aposentada: ${motivo} Consultá-la devolve resultado que parece legítimo.`;
  }

  const e = catalogo().find((x) => x.dataset === ds && x.tabela === tb);
  if (!e) return null;
  if (/redundante|obsolet|remover/i.test(e.status ?? "")) {
    return `${id} está marcada como '${e.status}' no catálogo. Use a tabela canônica.`;
  }
  if (e.linhas === 0) return `${id} está vazia (0 linhas).`;
  return null;
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
    SELECT dataset, "table" AS tabela, rows AS linhas, status,
           substr(provenance_notes, 1, 300) AS notas
    FROM read_parquet('~/rodado/_rodado_metadata/catalog.parquet')
    WHERE source <> 'view_only'
    ORDER BY dataset, tabela`;
  const r = await runSqlSsh(sql);
  if (r.error) throw new Error(`catalog.parquet: ${r.error}`);
  const linhas = (r.rows ?? []).map((x) => ({
    dataset: String(x.dataset),
    tabela: String(x.tabela),
    linhas: Number(x.linhas ?? 0),
    status: x.status ? String(x.status) : undefined,
    notas: x.notas ? String(x.notas) : undefined,
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

/**
 * Resolve o nome que o modelo escreveu contra o catálogo real — **só grafia**.
 *
 * Medido em 2026-09-01. A tentação era mapear prefixo (`seeg` -> o dataset que
 * começa com `seeg_`), porque parecia que o modelo truncava nomes. Não truncava:
 * `br_seeg` existe, tem `emissoes_municipais` com 12,1M linhas, e
 * `br_seeg_emissoes` é um dataset **diferente**, com `municipio` a 165,7M. O
 * espelho tem quase-duplicatas, e a "falha" era o modelo escolhendo o outro
 * membro defensável do par. Mapear por prefixo trocaria uma escolha legítima
 * por outra em silêncio.
 *
 * Sobra o que é erro de grafia de fato: prefixo `br_` ausente, e underscore a
 * mais ou a menos (`ibge_censo_2022_religiao` para `br_ibge_censo2022_religiao`).
 * Nome que não resolve devolve `null`, nunca um palpite.
 */
export function resolveDataset(escrito: string): string | null {
  const alvo = escrito.trim().toLowerCase().replace(/[.*\\\s]+$/g, "");
  if (!alvo) return null;
  const todos = listaDatasets();

  // O espelho tem três famílias de prefixo, não uma. Medido em 2026-09-02: o
  // modelo respondeu `olympedia_olympics` e o dataset é `world_olympedia_olympics`
  // — só `br_` era tentado, então um acerto virava falha na contagem.
  const PREFIXOS = ["br_", "world_", "us_"];

  // 1. exato, com ou sem prefixo
  const exato = todos.find((d) => d === alvo || PREFIXOS.some((p) => d === p + alvo));
  if (exato) return exato;

  // 2. ignorando underscores, e só quando o resultado é único
  const achata = (s: string) => s.replace(/_/g, "");
  for (const cand of [alvo, ...PREFIXOS.map((p) => p + alvo)]) {
    const planos = todos.filter((d) => achata(d) === achata(cand));
    if (planos.length === 1) return planos[0]!;
  }

  return null;
}
