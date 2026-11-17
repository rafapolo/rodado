// Fontes originais declaradas pela Base dos Dados para cada tabela que espelhamos.
//
// Lê a API de metadados da BD (backend.basedosdados.org/graphql, campo
// rawDataSources de cada dataset, com as tabelas ligadas a cada fonte) e
// casa pelo id do BigQuery (cloudTables.gcpDatasetId/gcpTableId), que é o
// nome do dataset/tabela no espelho. Aplica as correções de
// docs/context/privado/fontes_originais_bd_correcoes.yaml (URL errada, morta ou que
// aponta para um intermediário) e grava:
//
//   docs/context/privado/fontes_originais_bd.json  — {dataset: {fontes, tabelas}} lido por build_metadata_catalog.py
//   docs/context/privado/fontes_originais_bd.md    — o mesmo, para gente
//
// Uso:
//   bun scripts/gera_fontes_bd.ts                 # baixa da API (cache em /tmp) e gera
//   bun scripts/gera_fontes_bd.ts --cache         # reusa o último download
//   bun scripts/gera_fontes_bd.ts --checa         # também testa cada URL (GET, 1 por domínio por vez) → $TMPDIR/fontes_bd_checagem.json
//
// A lista de datasets do espelho vem de _rodado_metadata/catalog.parquet.

import { $ } from "bun";

import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const RAIZ = join(import.meta.dir, "..");
const API = "https://backend.basedosdados.org/graphql";
const CACHE = join(tmpdir(), "fontes_bd_api.json");
const CATALOGO = join(RAIZ, "_rodado_metadata/catalog.parquet");
const CORRECOES = join(RAIZ, "docs/context/privado/fontes_originais_bd_correcoes.yaml");
const SAIDA_JSON = join(RAIZ, "docs/context/privado/fontes_originais_bd.json");
const SAIDA_MD = join(RAIZ, "docs/context/privado/fontes_originais_bd.md");
// fica fora do git: depende de onde roda (do exterior, gov.br e IBGE devolvem 403/timeout)
const CHECAGEM = join(tmpdir(), "fontes_bd_checagem.json");

const args = new Set(process.argv.slice(2));

type Fonte = { nome: string; url: string; tabelas: string[] | null; origem: "bd" | "correcao"; nota?: string };
type Dataset = { slug: string; nome: string; fontes: Fonte[]; tabelas: string[]; orgs: { nome: string; url: string }[] };

const QUERY = `query($after: String) {
  allDataset(first: 40, after: $after) {
    pageInfo { hasNextPage endCursor }
    edges { node {
      slug name
      organizations { edges { node { name website } } }
      tables { edges { node { cloudTables { edges { node { gcpDatasetId gcpTableId } } } } } }
      rawDataSources { edges { node {
        name url
        tables { edges { node { cloudTables { edges { node { gcpDatasetId gcpTableId } } } } } }
      } } }
    } }
  }
}`;

async function gql(variables: Record<string, unknown>) {
  for (let tentativa = 1; ; tentativa++) {
    try {
      const r = await fetch(API, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: QUERY, variables }),
        signal: AbortSignal.timeout(60_000),
      });
      const j: any = await r.json();
      if (j.errors) throw new Error(JSON.stringify(j.errors).slice(0, 300));
      return j.data;
    } catch (e) {
      if (tentativa >= 4) throw e;
      await Bun.sleep(2000 * tentativa);
    }
  }
}

async function baixaApi(): Promise<any[]> {
  if (args.has("--cache") && existsSync(CACHE)) return JSON.parse(readFileSync(CACHE, "utf8"));
  const nos: any[] = [];
  let after: string | null = null;
  do {
    const d = await gql({ after });
    nos.push(...d.allDataset.edges.map((e: any) => e.node));
    after = d.allDataset.pageInfo.hasNextPage ? d.allDataset.pageInfo.endCursor : null;
    process.stderr.write(`\r${nos.length} datasets da BD`);
  } while (after);
  process.stderr.write("\n");
  writeFileSync(CACHE, JSON.stringify(nos));
  return nos;
}

const idsBq = (tables: any) =>
  (tables?.edges ?? []).flatMap((t: any) =>
    (t.node.cloudTables?.edges ?? []).map((c: any) => [c.node.gcpDatasetId, c.node.gcpTableId] as [string, string]),
  );

async function datasetsDoEspelho(): Promise<Map<string, Set<string>>> {
  // todas as tabelas: o source_name do catálogo não serve de filtro (ele chama de
  // "Base dos Dados" tudo que não acha em tasks/done/, inclusive o que raspamos).
  // Quem decide se a tabela é da BD é a própria API, pelo id do BigQuery.
  const out = await $`duckdb -json -c ${`SELECT dataset, "table" FROM '${CATALOGO}'`}`.json();
  const m = new Map<string, Set<string>>();
  for (const r of out as { dataset: string; table: string }[]) {
    if (!m.has(r.dataset)) m.set(r.dataset, new Set());
    m.get(r.dataset)!.add(r.table);
  }
  return m;
}

function normalizaUrl(u: string): string {
  let s = (u ?? "").trim().replace(/[`'".,;\\]+$/g, "").replace(/\\n$/, "");
  s = s.replace(/^(https?:\/\/)+(https?:\/\/)/i, "$2");
  if (s && !/^https?:\/\//i.test(s) && /^[\w-]+(\.[\w-]+)+/.test(s)) s = "https://" + s;
  return s;
}

type Correcao = { url?: string; nome?: string; nota: string; remove?: boolean; tabelas?: string[] };
// chave: "<dataset>" + lista de correções por URL errada; ou "<dataset>.adiciona"
type Correcoes = Record<string, { troca?: Record<string, Correcao>; adiciona?: Correcao[] }>;

function carregaCorrecoes(): Correcoes {
  if (!existsSync(CORRECOES)) return {};
  return (Bun.YAML.parse(readFileSync(CORRECOES, "utf8")) as Correcoes) ?? {};
}

async function checaUrls(urls: string[]) {
  // GET pausado por domínio: os portais gov.br têm WAF (ver reference_cgu_cdn_waf)
  const porHost = new Map<string, string[]>();
  for (const u of urls) {
    let h = "?";
    try { h = new URL(u).host; } catch {}
    if (!porHost.has(h)) porHost.set(h, []);
    porHost.get(h)!.push(u);
  }
  const res: Record<string, { status: number | string; final?: string }> = {};
  const fila = [...porHost.values()];
  let feitos = 0;
  async function trabalhador() {
    for (let grupo = fila.shift(); grupo; grupo = fila.shift()) {
      for (const u of grupo) {
        try {
          const r = await fetch(u, {
            redirect: "follow",
            headers: { "User-Agent": "Mozilla/5.0 (Macintosh) fontes-check" },
            signal: AbortSignal.timeout(20_000),
          });
          res[u] = { status: r.status, final: r.url !== u ? r.url : undefined };
          await r.body?.cancel();
        } catch (e: any) {
          res[u] = { status: String(e?.name ?? e).slice(0, 60) };
        }
        process.stderr.write(`\rchecadas ${++feitos}/${urls.length}`);
        await Bun.sleep(1500);
      }
    }
  }
  await Promise.all(Array.from({ length: 8 }, trabalhador));
  process.stderr.write("\n");
  return res;
}

async function main() {
  const nos = await baixaApi();
  const espelho = await datasetsDoEspelho();
  const correcoes = carregaCorrecoes();

  // dataset do BigQuery -> fontes; um slug da BD pode cobrir mais de um dataset do BQ
  const porDs = new Map<string, Dataset>();
  for (const n of nos) {
    const dsDoSlug = new Set(idsBq(n.tables).map(([d]) => d));
    for (const ds of dsDoSlug) {
      if (!espelho.has(ds)) continue;
      const daBd = new Set(idsBq(n.tables).filter(([d]) => d === ds).map(([, t]) => t));
      const nossas = [...espelho.get(ds)!].filter((t) => daBd.has(t));
      if (!nossas.length) continue;
      const orgs = (n.organizations?.edges ?? [])
        .map((o: any) => ({ nome: o.node.name?.trim() ?? "", url: normalizaUrl(o.node.website ?? "") }))
        .filter((o: { url: string }) => o.url);
      const alvo = porDs.get(ds) ?? { slug: n.slug, nome: n.name, fontes: [], tabelas: [], orgs };
      alvo.tabelas = [...new Set([...alvo.tabelas, ...nossas])].sort();
      for (const f of n.rawDataSources?.edges ?? []) {
        const url = normalizaUrl(f.node.url);
        const tabs = idsBq(f.node.tables).filter(([d, t]) => d === ds && espelho.get(ds)!.has(t)).map(([, t]) => t);
        // fonte ligada só a tabelas de outro dataset do BQ não vale para este
        // (ou só a tabelas da BD que não espelhamos)
        if (idsBq(f.node.tables).length && !tabs.length) continue;
        const dup = alvo.fontes.find((x) => x.url === url && x.nome === f.node.name);
        if (dup) {
          if (dup.tabelas && tabs.length) dup.tabelas = [...new Set([...dup.tabelas, ...tabs])].sort();
          continue;
        }
        alvo.fontes.push({ nome: f.node.name?.trim() ?? "", url, tabelas: tabs.length ? tabs.sort() : null, origem: "bd" });
      }
      porDs.set(ds, alvo);
    }
  }

  // correções
  const naoUsadas: string[] = [];
  for (const [ds, c] of Object.entries(correcoes)) {
    const alvo = porDs.get(ds);
    if (!alvo) { naoUsadas.push(ds); continue; }
    for (const [urlErrada, cor] of Object.entries(c.troca ?? {})) {
      const achadas = alvo.fontes.filter((f) => f.url === urlErrada && f.origem === "bd");
      if (!achadas.length) { naoUsadas.push(`${ds}: ${urlErrada}`); continue; }
      for (const f of achadas) {
        if (cor.remove) { alvo.fontes.splice(alvo.fontes.indexOf(f), 1); continue; }
        if (cor.url) f.url = cor.url;
        if (cor.nome) f.nome = cor.nome;
        f.origem = "correcao";
        f.nota = cor.nota;
      }
    }
    for (const a of c.adiciona ?? [])
      alvo.fontes.push({ nome: a.nome ?? "", url: a.url!, tabelas: a.tabelas ?? null, origem: "correcao", nota: a.nota });
  }
  if (naoUsadas.length) console.error("correções que não casaram com nada (a BD pode ter corrigido):\n  " + naoUsadas.join("\n  "));

  // sem fonte declarada nem corrigida: vale o site do órgão que a BD cadastra como dono do dado
  for (const d of porDs.values())
    if (!d.fontes.length)
      d.fontes = d.orgs.map((o) => ({ nome: o.nome, url: o.url, tabelas: null, origem: "bd" as const, nota: "site do órgão: a BD não declara fonte original" }));

  // de-duplica URL repetida com nome repetido depois das correções
  for (const d of porDs.values()) {
    const vistos = new Set<string>();
    d.fontes = d.fontes.filter((f) => {
      const k = f.url + "|" + (f.tabelas ?? []).join(",");
      if (vistos.has(k)) return false;
      vistos.add(k);
      return true;
    });
  }

  if (args.has("--checa")) {
    const urls = [...new Set([...porDs.values()].flatMap((d) => d.fontes.map((f) => f.url)).filter(Boolean))];
    writeFileSync(CHECAGEM, JSON.stringify(await checaUrls(urls), null, 1) + "\n");
  }

  const ordenados = [...porDs.entries()].sort(([a], [b]) => a.localeCompare(b));
  const json: Record<string, { slug_bd: string; nome: string; tabelas: string[]; fontes: Fonte[] }> = {};
  for (const [ds, d] of ordenados) json[ds] = { slug_bd: d.slug, nome: d.nome, tabelas: d.tabelas, fontes: d.fontes };
  writeFileSync(SAIDA_JSON, JSON.stringify(json, null, 1) + "\n");

  const n = ordenados.length;
  const semFonte = ordenados.filter(([, d]) => !d.fontes.length).map(([ds]) => ds);
  const nCorr = ordenados.reduce((s, [, d]) => s + d.fontes.filter((f) => f.origem === "correcao").length, 0);
  const hoje = new Date().toISOString().slice(0, 10);
  const esc = (s: string) => s.replace(/\|/g, "\\|").replace(/\s+/g, " ");
  const linhas = [
    "# Fontes originais das tabelas espelhadas do Base dos Dados",
    "",
    `> Gerado por \`scripts/gera_fontes_bd.ts\` em ${hoje}. Não editar à mão: corrigir em`,
    "> `docs/context/privado/fontes_originais_bd_correcoes.yaml` e rodar o script de novo.",
    "",
    `Para cada um dos ${n} datasets do espelho que existem no Base dos Dados (BD), a fonte original que a`,
    "BD declara nos seus metadados (`rawDataSources` da API `backend.basedosdados.org/graphql`), casada",
    "pelo id do BigQuery. É o que a BD declara, com as correções que fizemos quando a URL estava",
    `errada, morta ou apontava para um intermediário (${nCorr} correções, marcadas com ✎). A URL costuma ser a página do`,
    "conjunto de dados, não o arquivo baixado.",
    "",
    "Quando a fonte vale só para parte das tabelas, elas aparecem entre colchetes. *(órgão)* marca",
    "dataset para o qual a BD não declara fonte e só cadastra o órgão dono do dado: vai o site do órgão.",
    semFonte.length ? `\nSem fonte declarada na BD (${semFonte.length}): ${semFonte.map((d) => "`" + d + "`").join(", ")}.` : "",
    "",
    "A coluna *tabelas* conta só as tabelas do espelho que também existem na BD.",
    "",
    "| dataset | tabelas | fonte original |",
    "|---|---:|---|",
  ];
  for (const [ds, d] of ordenados) {
    const fontes = d.fontes.length
      ? d.fontes
          .map((f) => {
            const tabs = f.tabelas ? ` [${f.tabelas.join(", ")}]` : "";
            const marca = (f.origem === "correcao" ? " ✎" : "") + (f.nota?.startsWith("site do órgão") ? " (órgão)" : "");
            return `[${esc(f.nome || f.url)}](${f.url})${tabs}${marca}`;
          })
          .join("<br>")
      : "—";
    linhas.push(`| \`${ds}\` | ${d.tabelas.length} | ${fontes} |`);
  }
  writeFileSync(SAIDA_MD, linhas.filter((l, i) => !(l === "" && linhas[i - 1] === "")).join("\n") + "\n");
  console.log(`${n} datasets, ${n - semFonte.length} com fonte, ${nCorr} correções → ${SAIDA_MD}`);
}

await main();
