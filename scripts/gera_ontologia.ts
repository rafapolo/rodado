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
const OUT = join(REPO, "pages/atlas/ontologia.json");

type Classe = { nome: string; dominio: string; desc: string; conceitos: string[]; chaves?: string[] };
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

// ── chaves do atlas → classe ────────────────────────────────────────────
const regras: [string, RegExp][] = [];
for (const [id, c] of Object.entries(onto.classes))
  for (const re of c.chaves ?? []) regras.push([id, new RegExp(re, "i")]);

const classeDaChave: (string | null)[] = g.keys.map((k: { n: string }) => {
  if (dono.has(k.n)) return dono.get(k.n)!;
  for (const [id, re] of regras) if (re.test(k.n)) return id;
  return null;
});

// ── agregados por classe e por dataset ──────────────────────────────────
const ids = Object.keys(onto.classes);
const idx = new Map(ids.map((id, i) => [id, i]));
// chaves e datasets viajam como índices do schema_graph.json: o atlas já tem
// os nomes, a ontologia só diz a que classe cada um pertence
const porClasse = ids.map(() => ({ tabelas: 0, linhas: 0, ds: new Map<number, number>(), chaves: [] as [number, number][] }));
g.keys.forEach((k: { n: string; t: number }, i: number) => {
  const c = classeDaChave[i];
  if (c) porClasse[idx.get(c)!].chaves.push([i, k.t]);
});
const dsClasses = g.datasets.map(() => new Map<number, number>());
for (const t of g.tables) {
  const cs = new Set<number>();
  for (const ki of t.k) {
    const c = classeDaChave[ki];
    if (c) cs.add(idx.get(c)!);
  }
  for (const ci of cs) {
    const p = porClasse[ci];
    p.tabelas++;
    p.linhas += t.r || 0;
    p.ds.set(t.ds, (p.ds.get(t.ds) ?? 0) + 1);
    dsClasses[t.ds].set(ci, (dsClasses[t.ds].get(ci) ?? 0) + 1);
  }
}

const semClasse = g.keys.filter((_: unknown, i: number) => !classeDaChave[i]);
const tabelasComClasse = g.tables.filter((t: { k: number[] }) => t.k.some((ki) => classeDaChave[ki])).length;

const out = {
  meta: {
    gerado: new Date().toISOString().slice(0, 10),
    classes: ids.length,
    relacoes: onto.relacoes.length,
    conceitos: Object.keys(bridges.concepts).length,
    chaves: g.keys.length,
    chaves_classificadas: g.keys.length - semClasse.length,
    tabelas: g.tables.length,
    tabelas_com_classe: tabelasComClasse,
    datasets: g.datasets.length,
  },
  dominios: onto.dominios,
  classes: ids.map((id, i) => {
    const c = onto.classes[id];
    const p = porClasse[i];
    return {
      id,
      nome: c.nome,
      dom: c.dominio,
      desc: c.desc,
      conceitos: (c.conceitos ?? []).map((k) => [k, bridges.concepts[k].canonical_table ?? ""]),
      chaves: p.chaves.sort((a, b) => b[1] - a[1]),
      tabelas: p.tabelas,
      linhas: p.linhas,
      ds: [...p.ds].sort((a, b) => b[1] - a[1]),
    };
  }),
  relacoes: onto.relacoes.map((r) => ({
    de: idx.get(r.de),
    para: idx.get(r.para),
    tipo: r.tipo,
    via: r.via,
    conceito: r.ligacao === "conceito" ? 1 : 0,
  })),
  datasets: dsClasses.map((m) => [...m].sort((a, b) => b[1] - a[1])),
  sem_classe: g.keys.map((_: unknown, i: number) => i).filter((i: number) => !classeDaChave[i]),
};

const json = JSON.stringify(out);
await Bun.write(OUT, json + "\n");

const m = out.meta;
console.log(`classes ${m.classes} · relações ${m.relacoes} · conceitos ${m.conceitos}/${m.conceitos} com classe`);
console.log(`chaves ${m.chaves_classificadas}/${m.chaves} classificadas · tabelas ${m.tabelas_com_classe}/${m.tabelas} com alguma classe`);
for (const c of out.classes.filter((c) => !c.tabelas)) console.log(`  ⚠ classe sem tabela: ${c.id}`);
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
  `${m.classes} classes, ${m.relacoes} relações; os ${m.conceitos} conceitos de \`bridges.yaml\` cabem nelas, e ${m.tabelas_com_classe} das ${m.tabelas} tabelas tocam alguma.`,
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
  for (const id of cs) md.push(`    ${id}(("${onto.classes[id].nome}"))`);
  md.push("  end");
}
for (const r of onto.relacoes)
  md.push(`  ${r.de} ${r.ligacao === "conceito" ? "-." : "--"} ${r.tipo} ${r.ligacao === "conceito" ? ".->" : "-->"} ${r.para}`);
const pal: Record<string, string> = {
  territorio: "#d55181", empresa: "#199e70", pessoa: "#d95926", titular: "#9085e9", classificacao: "#c063c7", educacao: "#3987e5",
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
