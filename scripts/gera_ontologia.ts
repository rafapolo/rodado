#!/usr/bin/env bun
/**
 * Ontologia do espelho: classes de entidade e as relações entre elas.
 *
 *   bun scripts/gera_ontologia.ts   # -> pages/atlas/ontologia.json + docs/mapa/ONTOLOGIA.md
 *   python3 scripts/build_atlas.py  # o atlas busca o JSON no modo "Ontologia"
 *
 * Lê docs/context/ontologia.yaml (curado à mão), bridges.yaml (os 62 conceitos)
 * e pages/atlas/schema_graph.json (tabelas → chaves → datasets, o mesmo grafo
 * do atlas). Cada chave do atlas cai numa classe por conceito exato ou pela
 * primeira regex que casa; tabela e dataset herdam as classes das suas chaves.
 *
 * Recusa o build se um conceito de bridges.yaml ficar sem classe ou cair em
 * duas, se uma classe citar conceito inexistente ou se uma relação apontar
 * para classe inexistente — os três jeitos de a ontologia mentir em silêncio.
 */
import { join } from "node:path";

const REPO = join(import.meta.dir, "..");
const ONTO = join(REPO, "docs/context/ontologia.yaml");
const BRIDGES = join(REPO, "docs/context/bridges.yaml");
const GRAPH = join(REPO, "pages/atlas/schema_graph.json");
// todas as colunas de todas as tabelas — o schema_graph só traz as chaves do
// atlas (colunas repetidas entre datasets) e corta a lista de colunas
const SCHEMAS = join(REPO, "docs/context/schemas.json");
// o datative cruza CNPJ/CPF em ~140 tabelas; se o repo irmão estiver ao lado,
// toda coluna que ele usa precisa cair numa classe
const DATATIVE = join(REPO, "../datative/src/cnpj-datasets.ts");
const OUT = join(REPO, "pages/atlas/ontologia.json");

type Classe = {
  nome: string; dominio: string; desc: string; conceitos: string[];
  chaves?: string[]; chaves_amplas?: string[]; colunas?: string[]; tabelas?: string[];
  tipo?: "fato"; desenha?: boolean;
};
type Rel = { de: string; tipo: string; para: string; via: string; ligacao?: string };

const onto = Bun.YAML.parse(await Bun.file(ONTO).text()) as {
  dominios: Record<string, { nome: string; cor: string }>;
  classes: Record<string, Classe>;
  relacoes: Rel[];
};
// bridges.yaml tem construções que o parser do Bun recusa; o PyYAML (que os
// outros geradores já usam) lê e devolve JSON.
const bridges = JSON.parse(
  await Bun.$`python3 -c ${"import sys,json,yaml;json.dump(yaml.safe_load(open(sys.argv[1])),sys.stdout,default=str)"} ${BRIDGES}`.text(),
) as {
  concepts: Record<string, { category: string; canonical_table?: string }>;
};
const g = await Bun.file(GRAPH).json();

const erros: string[] = [];

// ── conceitos: cada um em exatamente uma classe ─────────────────────────
const dono = new Map<string, string>();
for (const [id, c] of Object.entries(onto.classes)) {
  if (!onto.dominios[c.dominio]) erros.push(`classe ${id}: domínio ${c.dominio} não existe`);
  for (const k of c.conceitos ?? []) {
    if (!bridges.concepts[k]) erros.push(`classe ${id}: conceito ${k} não está em bridges.yaml`);
    if (dono.has(k)) erros.push(`conceito ${k} em duas classes: ${dono.get(k)} e ${id}`);
    dono.set(k, id);
  }
}
for (const k of Object.keys(bridges.concepts))
  if (!dono.has(k)) erros.push(`conceito ${k} de bridges.yaml sem classe em ontologia.yaml`);
for (const r of onto.relacoes)
  for (const end of [r.de, r.para])
    if (!onto.classes[end]) erros.push(`relação ${r.de} -[${r.tipo}]-> ${r.para}: classe ${end} não existe`);

if (erros.length) {
  console.error(erros.map((e) => "✗ " + e).join("\n"));
  process.exit(1);
}

// ── coluna → classe ─────────────────────────────────────────────────────
// Ordem: conceito exato → coluna nomeada (dataset.tabela.coluna) → regex da
// classe (na ordem do YAML) → regex ampla (último recurso: "tem cnpj no nome").
// Vale para TODAS as colunas do espelho, não só as chaves do atlas: o
// `cpf_cnpj_contratado` dos contratos da CGU só existe numa tabela, então nunca
// vira chave do atlas, mas identifica um fornecedor do mesmo jeito.
const regras: [string, RegExp][] = [], amplas: [string, RegExp][] = [];
const nomeadas = new Map<string, string>();
const porTabela: [string, RegExp][] = [];
for (const [id, c] of Object.entries(onto.classes)) {
  for (const re of c.tabelas ?? []) porTabela.push([id, new RegExp(re, "i")]);
  for (const re of c.chaves ?? []) regras.push([id, new RegExp(re, "i")]);
  for (const re of c.chaves_amplas ?? []) amplas.push([id, new RegExp(re, "i")]);
  for (const col of c.colunas ?? []) nomeadas.set(col, id);
}
function classifica(col: string, tabela?: string): string | null {
  if (dono.has(col)) return dono.get(col)!;
  if (tabela && nomeadas.has(`${tabela}.${col}`)) return nomeadas.get(`${tabela}.${col}`)!;
  for (const [id, re] of regras) if (re.test(col)) return id;
  for (const [id, re] of amplas) if (re.test(col)) return id;
  return null;
}
const classeDaChave: (string | null)[] = g.keys.map((k: { n: string }) => classifica(k.n));

const schemas = (await Bun.file(SCHEMAS).json()).tables as Record<string, { columns: { name: string }[] }>;
const colunasDe = (t: { ds: number; n: string; c: [string, string][] }) => {
  const nome = `${g.datasets[t.ds].n}.${t.n}`;
  return { nome, cols: schemas[nome]?.columns.map((c) => c.name) ?? t.c.map((c) => c[0]) };
};

// ── agregados por classe e por dataset ──────────────────────────────────
const ids = Object.keys(onto.classes);
const idx = new Map(ids.map((id, i) => [id, i]));
const keyIdx = new Map<string, number>(g.keys.map((k: { n: string }, i: number) => [k.n, i]));
const porClasse = ids.map(() => ({ tabelas: 0, linhas: 0, ds: new Map<number, number>(), cols: new Map<string, number>() }));
const dsClasses = g.datasets.map(() => new Map<number, number>());
const classesDaTabela: Set<number>[] = [];
for (const t of g.tables) {
  const { nome, cols } = colunasDe(t);
  const cs = new Set<number>();
  // a tabela inteira registra um fato (o SIM é registro de óbitos)
  for (const [id, re] of porTabela) if (re.test(nome)) cs.add(idx.get(id)!);
  for (const col of cols) {
    const c = classifica(col, nome);
    if (!c) continue;
    const ci = idx.get(c)!;
    cs.add(ci);
    const m = porClasse[ci].cols;
    m.set(col, (m.get(col) ?? 0) + 1);
  }
  classesDaTabela.push(cs);
  for (const ci of cs) {
    const p = porClasse[ci];
    p.tabelas++;
    p.linhas += t.r || 0;
    p.ds.set(t.ds, (p.ds.get(t.ds) ?? 0) + 1);
    dsClasses[t.ds].set(ci, (dsClasses[t.ds].get(ci) ?? 0) + 1);
  }
}

const semClasse = g.keys.filter((_: unknown, i: number) => !classeDaChave[i]);
// conta só as classes desenhadas: uma tabela que só tem `ano` não toca o grafo
const desenhada = (ci: number) => onto.classes[ids[ci]].desenha !== false;
const tabelasComClasse = classesDaTabela.filter((cs) => [...cs].some(desenhada)).length;

// classes com `desenha: false` (o Período) ficam classificadas mas fora do grafo;
// os índices de saída são renumerados sem elas
const vis = ids.filter((id) => onto.classes[id].desenha !== false);
const novo = new Map(vis.map((id, i) => [idx.get(id)!, i]));
for (const r of onto.relacoes)
  if (!novo.has(idx.get(r.de)!) || !novo.has(idx.get(r.para)!))
    throw new Error(`relação ${r.de} -[${r.tipo}]-> ${r.para} toca classe que não é desenhada`);
const domsVis = new Set(vis.map((id) => onto.classes[id].dominio));

const out = {
  meta: {
    gerado: new Date().toISOString().slice(0, 10),
    classes: vis.length,
    relacoes: onto.relacoes.length,
    conceitos: Object.keys(bridges.concepts).length,
    chaves: g.keys.length,
    chaves_classificadas: g.keys.length - semClasse.length,
    tabelas: g.tables.length,
    tabelas_com_classe: tabelasComClasse,
    datasets: g.datasets.length,
  },
  dominios: Object.fromEntries(Object.entries(onto.dominios).filter(([d]) => domsVis.has(d))),
  classes: vis.map((id) => {
    const c = onto.classes[id];
    const p = porClasse[idx.get(id)!];
    return {
      id,
      nome: c.nome,
      dom: c.dominio,
      fato: c.tipo === "fato" ? 1 : 0,
      desc: c.desc,
      conceitos: (c.conceitos ?? []).map((k) => [k, bridges.concepts[k].canonical_table ?? ""]),
      // [coluna, nº de tabelas, índice da chave no atlas ou -1]
      chaves: [...p.cols].sort((a, b) => b[1] - a[1]).map(([col, n]) => [col, n, keyIdx.get(col) ?? -1]),
      tabelas: p.tabelas,
      linhas: p.linhas,
      ds: [...p.ds].sort((a, b) => b[1] - a[1]),
    };
  }),
  relacoes: onto.relacoes.map((r) => ({
    de: novo.get(idx.get(r.de)!),
    para: novo.get(idx.get(r.para)!),
    tipo: r.tipo,
    via: r.via,
    conceito: r.ligacao === "conceito" ? 1 : 0,
  })),
  datasets: dsClasses.map((m) => [...m].filter(([ci]) => novo.has(ci)).map(([ci, n]) => [novo.get(ci)!, n]).sort((a, b) => b[1] - a[1])),
  sem_classe: g.keys.map((_: unknown, i: number) => i).filter((i: number) => !classeDaChave[i]),
};

// ── conferência com o datative ──────────────────────────────────────────
if (await Bun.file(DATATIVE).exists()) {
  const src = await Bun.file(DATATIVE).text();
  const faltam: string[] = [];
  let n = 0;
  for (const bloco of src.split(/\n  \{\n/)) {
    const tb = bloco.match(/table: "([^"]+)"/);
    if (!tb) continue;
    const tabela = tb[1].split(".").slice(-2).join(".");
    for (const [, col] of bloco.matchAll(/\{ name: "([^"]+)", type: "[^"]+"/g)) {
      n++;
      if (!classifica(col, tabela)) faltam.push(`${tabela}.${col}`);
    }
  }
  console.log(`datative  ${n - faltam.length}/${n} colunas de CNPJ/CPF com classe`);
  for (const f of faltam) console.log(`  ⚠ sem classe: ${f}`);
}

const json = JSON.stringify(out);
await Bun.write(OUT, json + "\n");

const m = out.meta;
console.log(`classes ${m.classes} · relações ${m.relacoes} · conceitos ${m.conceitos}/${m.conceitos} com classe`);
console.log(`chaves ${m.chaves_classificadas}/${m.chaves} classificadas · tabelas ${m.tabelas_com_classe}/${m.tabelas} com alguma classe`);
for (const c of out.classes.filter((c) => !c.tabelas)) console.log(`  ⚠ classe sem tabela: ${c.id}`);
console.log(`fatos    ${out.classes.filter((c) => c.fato).map((c) => `${c.id} ${c.tabelas}`).join(" · ")}`);
console.log(`json     ${OUT.replace(REPO + "/", "")} (${(json.length / 1024).toFixed(0)} KB)`);
// ── mermaid: flowchart por domínio, layout ELK ──────────────────────────
// Um subgraph por domínio; tracejado = ligação que o espelho não faz.
// Período fica fora: não tem aresta, só poluiria o desenho.
const md: string[] = [
  "# Ontologia do espelho",
  "",
  "Gerado por `scripts/gera_ontologia.ts` a partir de `docs/context/ontologia.yaml` — não edite.",
  `Versão navegável: o modo Ontologia do atlas, [rodado.xyz/atlas/?mode=ontologia](https://rodado.xyz/atlas/?mode=ontologia).`,
  "",
  `${m.classes} classes (${out.classes.filter((c) => c.fato).length} delas fatos, em círculo duplo), ${m.relacoes} relações; os ${m.conceitos} conceitos de \`bridges.yaml\` cabem nelas, e ${m.tabelas_com_classe} das ${m.tabelas} tabelas tocam alguma.`,
  "Linha tracejada: a ligação existe no mundo, mas o espelho não consegue fazê-la (CPF mascarado, microdado desidentificado, texto livre).",
  "",
  "```mermaid",
  '%%{init: {"layout": "elk", "elk": {"nodePlacementStrategy": "NETWORK_SIMPLEX"}, "flowchart": {"curve": "basis"}}}%%',
  "flowchart LR",
];
const usados = new Set(onto.relacoes.flatMap((r) => [r.de, r.para]));
for (const [d, dom] of Object.entries(onto.dominios)) {
  const cs = ids.filter((id) => onto.classes[id].dominio === d && usados.has(id));
  if (!cs.length) continue;
  md.push(`  subgraph dom_${d}["${dom.nome}"]`);
  // entidade = círculo; fato = círculo duplo
  for (const id of cs) md.push(onto.classes[id].tipo === "fato"
    ? `    ${id}((("${onto.classes[id].nome}")))` : `    ${id}(("${onto.classes[id].nome}"))`);
  md.push("  end");
}
for (const r of onto.relacoes)
  md.push(`  ${r.de} ${r.ligacao === "conceito" ? "-." : "--"} ${r.tipo} ${r.ligacao === "conceito" ? ".->" : "-->"} ${r.para}`);
const pal: Record<string, string> = {
  territorio: "#d55181", empresa: "#199e70", pessoa: "#d95926", titular: "#5d6675", classificacao: "#c063c7", educacao: "#3987e5",
  seguranca: "#9085e9", meio_ambiente: "#96b83a",
  saude: "#e66767", estado: "#c98500", politica: "#008300", infraestrutura: "#7086dd", tempo: "#6b7484",
};
for (const [d, cor] of Object.entries(pal)) {
  const cs = ids.filter((id) => onto.classes[id].dominio === d && usados.has(id));
  if (cs.length) md.push(`  classDef c_${d} fill:${cor},stroke:${cor},color:#fff`, `  class ${cs.join(",")} c_${d}`);
}
md.push("```", "");
const MD = join(REPO, "docs/mapa/ONTOLOGIA.md");
await Bun.write(MD, md.join("\n"));
console.log(`mermaid  ${MD.replace(REPO + "/", "")}`);
