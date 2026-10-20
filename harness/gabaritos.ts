/**
 * Gabaritos gerados — perguntas novas com o número conferido no beelink.
 *
 * Os quatro TSVs escritos à mão (diretas + 3 holdouts) somam 55 perguntas e
 * concentram-se em SIM, SINASC, RAIS, Censo, PIB e CAGED. Refinar o harness só
 * com eles mede as fontes grandes e deixa o resto do espelho sem régua. Aqui as
 * perguntas vêm de três fontes, em `dados/gabaritos/*.yaml`:
 *
 *  - `armadilhas.yaml` — uma pergunta por gotcha de `docs/context/gotchas/`,
 *    cuja resposta ingênua dá um número plausível e errado (`armadilha`).
 *  - `cobertura.yaml` — uma ou duas perguntas por dataset que nenhum TSV cobria.
 *  - `sem_dado.yaml` — o ano pedido está fora da faixa da tabela.
 *
 * O número nunca vem de quem escreveu a pergunta: `sql` roda no beelink agora.
 * Duas vias, como pede o AGENTS.md: `sql2` (outra consulta, outro caminho até o
 * mesmo número) e/ou `doc` (o número medido antes e registrado no gotcha). Caso
 * em que as vias discordam, a consulta falha ou o número aparece na própria
 * pergunta sai da rodada e é listado.
 *
 *     bun harness/gabaritos.ts            # roda o que mudou, escreve dados/gabaritos.tsv
 *     bun harness/gabaritos.ts --refaz    # ignora o cache de medições
 *     bun harness/gabaritos.ts --so <id>  # um caso só, para depurar a SQL
 *
 * O cache (`dados/gabaritos/medido.json`) guarda a medição por id e hash da SQL:
 * reescrever um caso remede só ele.
 */
import { existsSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { runSqlSsh } from "./beelink.ts";
import { numeros } from "./acerto.ts";

const DIR = `${import.meta.dir}/dados/gabaritos`;
const CACHE = `${DIR}/medido.json`;
const SAIDA = `${import.meta.dir}/dados/gabaritos.tsv`;
const PARALELO = 3;
const CATALOGO = `${import.meta.dir}/dados/catalogo.json`;

export interface Candidato {
  id: string;
  origem: string;
  pergunta: string;
  /** devolve uma linha com a coluna `v` — ou, em `sem_dado`, `max(ano)` como `v` */
  sql: string;
  sql2?: string;
  /** número medido antes (gotcha), conferido contra `sql` */
  doc?: number;
  /** tolerância do gabarito no formato de acerto.ts: "0,5%" ou "0,1" */
  tol?: string;
  /** a resposta de quem cai na armadilha, quando ela é um número */
  armadilha?: number;
  /** casas decimais do gabarito (padrão: inteiro quando v é inteiro, senão 2) */
  casas?: number;
  /** sem_dado: o ano pedido; o caso vale se ano > v (o máximo medido) */
  sem_dado_ano?: number;
  /** sem_dado: o ano pedido está ANTES da série; o caso vale se ano < v (o mínimo medido) */
  antes?: boolean;
  /** sem_dado: `sql` conta o que existiria (coluna preenchida, país presente); o caso vale se v = 0 */
  vazio?: boolean;
}

interface Medida { hash: string; v?: number; v2?: number; erro?: string; em: string }

function hash(c: Candidato): string {
  return String(Bun.hash(`${c.sql}\n--\n${c.sql2 ?? ""}`));
}

function carrega(): (Candidato & { arquivo: string })[] {
  const out: (Candidato & { arquivo: string })[] = [];
  for (const f of readdirSync(DIR).filter((f) => f.endsWith(".yaml")).sort()) {
    const lista = Bun.YAML.parse(readFileSync(`${DIR}/${f}`, "utf8")) as Candidato[];
    for (const c of lista ?? []) out.push({ ...c, arquivo: f });
  }
  const vistos = new Set<string>();
  for (const c of out) {
    if (vistos.has(c.id)) throw new Error(`id repetido: ${c.id}`);
    vistos.add(c.id);
  }
  return out;
}

async function valor(sql: string): Promise<{ v?: number; erro?: string }> {
  const r = await runSqlSsh(sql);
  if (r.error) return { erro: r.error.slice(0, 300) };
  const linha = r.rows?.[0];
  if (!linha || r.rows!.length !== 1) return { erro: `esperava 1 linha, veio ${r.rows?.length ?? 0}` };
  const v = Number(linha.v ?? Object.values(linha)[0]);
  return Number.isFinite(v) ? { v } : { erro: `v não numérico: ${JSON.stringify(linha)}` };
}

/** As duas vias concordam? Tolerância relativa de 0,5% ou a do caso, o que for maior. */
function batem(a: number, b: number, tol?: string): boolean {
  if (a === b) return true;
  let rel = 0.005, abs = 0;
  if (tol) {
    const n = Number(tol.replace("%", "").replace(",", "."));
    if (tol.endsWith("%")) rel = Math.max(rel, n / 100); else abs = n;
  }
  return Math.abs(a - b) <= Math.max(abs, rel * Math.max(Math.abs(a), Math.abs(b)));
}

/**
 * A tolerância do gabarito cobre todas as vias que bateram: se `sql2` ou `doc`
 * passou dentro de 0,5% sem ser idêntico, quem responder pelo outro caminho (ou
 * repetir o número do gotcha) não pode ser marcado errado. Mantém a forma da
 * tolerância do caso (absoluta ou %) e só a alarga.
 */
function toleraVias(v: number, outras: (number | undefined)[], tol?: string): string | undefined {
  const dif = Math.max(0, ...outras.filter((x): x is number => x !== undefined).map((x) => Math.abs(v - x)));
  const virgula = (n: number) => n.toString().replace(".", ",");
  if (tol && !tol.endsWith("%")) {
    const abs = Number(tol.replace(",", "."));
    return `~${virgula(dif > abs ? Math.ceil(dif * 100) / 100 : abs)}`;
  }
  const rel = tol ? Number(tol.replace("%", "").replace(",", ".")) : 0;
  const precisa = dif ? Math.ceil((dif / Math.abs(v)) * 1000) / 10 : 0;
  const final = Math.max(rel, precisa);
  return final ? `~${virgula(final)}%` : undefined;
}

function fmt(v: number, casas?: number): string {
  const c = casas ?? (Number.isInteger(v) ? 0 : 2);
  return v.toFixed(c).replace(".", ",");
}

async function main() {
  const refaz = Bun.argv.includes("--refaz");
  const so = Bun.argv.includes("--so") ? Bun.argv[Bun.argv.indexOf("--so") + 1] : undefined;
  const cache: Record<string, Medida> = existsSync(CACHE) ? JSON.parse(readFileSync(CACHE, "utf8")) : {};
  const todos = carrega();
  const fila = todos.filter((c) => (!so || c.id === so) && (refaz || so || cache[c.id]?.hash !== hash(c)));
  console.error(`${todos.length} candidatos, ${fila.length} a medir`);

  let i = 0;
  async function trabalhador() {
    while (i < fila.length) {
      const c = fila[i++]!;
      const t0 = Date.now();
      const a = await valor(c.sql);
      const b = c.sql2 && !a.erro ? await valor(c.sql2) : {};
      cache[c.id] = { hash: hash(c), v: a.v, v2: b.v, erro: a.erro ?? b.erro, em: new Date().toISOString().slice(0, 10) };
      console.error(`${c.id}: ${a.erro ?? b.erro ?? `${a.v}${c.sql2 ? ` / ${b.v}` : ""}`} (${((Date.now() - t0) / 1000).toFixed(0)} s)`);
      writeFileSync(CACHE, JSON.stringify(cache, null, 1));
    }
  }
  await Promise.all(Array.from({ length: PARALELO }, trabalhador));
  if (so) return;

  // dataset que o catálogo do harness (cache de catalogo.ts) ainda não lista: o caso mede o
  // cache velho, não o harness — marca no comentário até `catalogo.ts --atualiza` + persona
  const noCatalogo = new Set((JSON.parse(readFileSync(CATALOGO, "utf8")) as { dataset: string }[]).map((t) => t.dataset));
  const semCatalogo = (c: Candidato) => noCatalogo.has(c.origem.split(/[/ ]/)[0]!) ? "" : " [fora do catálogo do harness]";
  const aceitos: string[] = [];
  const recusados: string[] = [];
  for (const c of todos) {
    const m = cache[c.id];
    const recusa = (motivo: string) => recusados.push(`${c.id} (${c.arquivo}): ${motivo}`);
    if (!m || m.hash !== hash(c)) { recusa("não medido"); continue; }
    if (m.erro || m.v === undefined) { recusa(m.erro ?? "sem valor"); continue; }
    if (c.vazio) {
      if (m.v !== 0) { recusa(`devia estar vazio, veio ${m.v}`); continue; }
      aceitos.push(`# ${c.id} [${c.origem}]${semCatalogo(c)} vazio: ${m.v} linhas (${m.em})\n${c.pergunta}\tSEM_DADO`);
      continue;
    }
    if (c.sem_dado_ano !== undefined) {
      const fora = c.antes ? c.sem_dado_ano < m.v : c.sem_dado_ano > m.v;
      if (!fora) { recusa(`ano ${c.sem_dado_ano} está dentro da série (${c.antes ? "mín" : "máx"} ${m.v})`); continue; }
      aceitos.push(`# ${c.id} [${c.origem}]${semCatalogo(c)} ${c.antes ? "mín" : "máx"}(ano) = ${m.v} (${m.em})\n${c.pergunta}\tSEM_DADO`);
      continue;
    }
    if (c.sql2 && (m.v2 === undefined || !batem(m.v, m.v2, c.tol))) { recusa(`vias discordam: ${m.v} × ${m.v2}`); continue; }
    if (c.doc !== undefined && !batem(m.v, c.doc, c.tol)) { recusa(`difere do medido antes: ${m.v} × doc ${c.doc}`); continue; }
    if (!c.sql2 && c.doc === undefined) { recusa("uma via só (falta sql2 ou doc)"); continue; }
    if (m.v === 0) { recusa("v = 0: filtro que não casa nada parece resposta"); continue; }
    if (c.armadilha !== undefined && batem(m.v, c.armadilha)) { recusa(`a armadilha dá o mesmo número (${c.armadilha})`); continue; }
    const base = fmt(m.v, c.casas);
    const esperado = base + (toleraVias(Number(base.replace(",", ".")), [m.v, m.v2, c.doc], c.tol) ?? "");
    if (numeros(c.pergunta).some((n) => batem(n, m.v!))) { recusa(`eco: ${m.v} está na pergunta`); continue; }
    const vias = [c.sql2 ? `sql2 ${m.v2}` : "", c.doc !== undefined ? `doc ${c.doc}` : "", c.armadilha !== undefined ? `armadilha ${c.armadilha}` : ""].filter(Boolean).join("; ");
    aceitos.push(`# ${c.id} [${c.origem}]${semCatalogo(c)} v = ${m.v} (${vias}) — ${m.em}\n${c.pergunta}\t${esperado}`);
  }

  const cab = [
    "# Gabaritos gerados por harness/gabaritos.ts a partir de dados/gabaritos/*.yaml — NÃO editar à mão.",
    "# Cada número foi medido no beelink (DuckDB -readonly) e conferido por uma segunda via: outra",
    "# consulta (sql2) e/ou o número registrado antes no gotcha (doc). `armadilha` é o que dá a",
    "# leitura ingênua. As perguntas de armadilhas.yaml testam se o harness USA o gotcha que já recebe;",
    "# as de cobertura.yaml e sem_dado.yaml são holdout: nenhuma nota foi escrita a partir delas.",
  ];
  writeFileSync(SAIDA, cab.join("\n") + "\n" + aceitos.join("\n") + "\n");
  console.log(`${aceitos.length} aceitos -> ${SAIDA}`);
  if (recusados.length) console.log(`${recusados.length} recusados:\n  ` + recusados.join("\n  "));
}

if (import.meta.main) await main();
