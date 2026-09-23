/**
 * O significado dos códigos, ao lado da coluna.
 *
 * `descrever_tabela` dava nome e tipo — `tipo_localizacao: STRING` — e o modelo
 * tinha que descobrir sozinho que existe `br_inep_censo_escolar.dicionario` e
 * que ali '2' quer dizer Rural. Quando não descobre, chuta o código ou filtra
 * pelo texto ('Rural') numa coluna que só tem dígitos e volta zero linhas.
 *
 * Fonte: toda coluna listada em `docs/context/dicionario_coverage.json`,
 * decodificada pela tabela `{dataset}.dicionario` do próprio espelho. Cache em
 * `harness/dados/dicionarios.json`; `bun harness/dicionarios.ts --atualiza`
 * rebusca no beelink depois de um sync.
 */
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { runSqlSsh } from "./beelink.ts";

const RAIZ = new URL("..", import.meta.url).pathname;
const COBERTURA = `${RAIZ}docs/context/dicionario_coverage.json`;
const CACHE = `${RAIZ}harness/dados/dicionarios.json`;

/** `dataset.tabela` -> coluna -> [chave, valor][]. Listas longas guardam só a
 *  prévia e o total — nunca vão inteiras para o prompt mesmo. */
type Cache = Record<string, Record<string, [string, string][] | { total: number; previa: [string, string][] }>>;

let _cache: Cache | null = null;

function cache(): Cache {
  if (_cache) return _cache;
  _cache = existsSync(CACHE) ? JSON.parse(readFileSync(CACHE, "utf8")) : {};
  return _cache!;
}

/** Os códigos de uma coluna, ou undefined se ela não é decodificável. */
export function codigos(tabela: string, coluna: string): { total: number; previa: [string, string][] } | undefined {
  const c = cache()[tabela.toLowerCase()]?.[coluna.toLowerCase()];
  if (!c) return undefined;
  return Array.isArray(c) ? { total: c.length, previa: c } : c;
}

const MAX_INLINE = Number(Bun.env.HARNESS_DICIONARIO_INLINE ?? 15);

/** Sufixo para a linha da coluna em `descrever_tabela`, ou "" se não há código. */
export function legenda(tabela: string, coluna: string): string {
  const cs = codigos(tabela, coluna);
  if (!cs?.total) return "";
  const curto = (v: string) => (v.length > 45 ? `${v.slice(0, 42).trimEnd()}…` : v);
  if (cs.total <= MAX_INLINE) return ` — códigos: ${cs.previa.map(([k, v]) => `'${k}'=${curto(v)}`).join(", ")}`;
  const [ds, tb] = tabela.split(".");
  return ` — ${cs.total} códigos: ${cs.previa.slice(0, 4).map(([k, v]) => `'${k}'=${curto(v)}`).join(", ")}… ` +
    `(todos em ${ds}.dicionario WHERE id_tabela='${tb}' AND nome_coluna='${coluna}')`;
}

async function atualiza() {
  const cob = JSON.parse(readFileSync(COBERTURA, "utf8")) as { tables: Record<string, string[]> };
  const porDataset = new Map<string, Map<string, string[]>>();
  for (const [tabela, cols] of Object.entries(cob.tables)) {
    const [ds, tb] = tabela.split(".");
    if (!porDataset.has(ds!)) porDataset.set(ds!, new Map());
    porDataset.get(ds!)!.set(tb!, cols);
  }
  const out: Cache = {};
  let n = 0;
  for (const [ds, tabelas] of porDataset) {
    const r = await runSqlSsh(
      `SELECT id_tabela, nome_coluna, chave, valor FROM ${ds}.dicionario ORDER BY id_tabela, nome_coluna, chave`);
    if (r.error) { console.error(`${ds}: ${r.error.split("\n")[0]}`); continue; }
    for (const row of r.rows ?? []) {
      // A fonte tem nome com espaço no fim ('tipo_situacao_funcionamento ').
      const tb = String(row.id_tabela ?? "").trim();
      const col = String(row.nome_coluna ?? "").trim();
      if (!tabelas.get(tb)?.includes(col)) continue;
      const chave = String(row.chave ?? "");
      const valor = String(row.valor ?? "").replace(/\s+/g, " ").trim();
      const alvo = ((out[`${ds}.${tb}`] ??= {})[col] ??= []);
      // O mesmo código pode mudar de texto entre períodos (cobertura_temporal):
      // junta as versões numa entrada só em vez de repetir a chave.
      const ja = alvo.find(([k]) => k === chave);
      if (!ja) alvo.push([chave, valor]);
      else if (!ja[1].split(" / ").includes(valor)) ja[1] += ` / ${valor}`;
      n++;
    }
  }
  for (const cols of Object.values(out)) {
    for (const [col, lista] of Object.entries(cols)) {
      if (Array.isArray(lista) && lista.length > MAX_INLINE) cols[col] = { total: lista.length, previa: lista.slice(0, 4) };
    }
  }
  writeFileSync(CACHE, JSON.stringify(out));
  console.log(`${Object.keys(out).length} tabelas, ${n} códigos -> ${CACHE}`);
}

if (import.meta.main) {
  if (Bun.argv.includes("--atualiza")) await atualiza();
  else {
    const [tabela, coluna] = Bun.argv.slice(2);
    if (!tabela || !coluna) { console.error("uso: bun harness/dicionarios.ts [--atualiza | <dataset.tabela> <coluna>]"); process.exit(1); }
    console.log(`${coluna}${legenda(tabela, coluna) || " — sem códigos"}`);
  }
}
