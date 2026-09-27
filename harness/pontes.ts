/**
 * Dicas de join — a expressão que já foi conferida no beelink, para as tabelas
 * que o modelo escolheu.
 *
 * O espelho não tem foreign key. O que liga duas tabelas é uma coluna que
 * significa a mesma coisa sob outro nome, às vezes com formato diferente:
 * `br_anp_combustiveis.precos` guarda `cnpj` sem padding, então `a.cnpj = b.cnpj`
 * está errado e é exatamente o que um casamento por nome devolveria. Esse
 * conhecimento está em `bridges.yaml` e é a razão de ele existir.
 *
 * Só as pontes das tabelas escolhidas entram no prompt. O `bridges` inteiro são
 * 15.758 tokens; as pontes de duas ou três tabelas são dezenas.
 */
import { readFileSync } from "node:fs";
import { parse } from "yaml";

const RAIZ = new URL("..", import.meta.url).pathname;

interface Ponte {
  table: string;
  column: string;
  join_expr?: string;
  expr?: string;
  verified?: string;
  concept?: string;
  format?: string;
}

interface Conceito { description?: string; canonical_table?: string }

let _b: { bridges?: Record<string, Ponte[]>; concepts?: Record<string, Conceito> } | null = null;
function bridges() {
  if (!_b) _b = parse(readFileSync(`${RAIZ}docs/context/bridges.yaml`, "utf8"));
  return _b!;
}

/**
 * O campo `table` de uma ponte, aberto nas tabelas que ele cobre, como globs.
 * `bridges.yaml` abrevia (B33): "ds.a / b" (b herda o dataset), "ds.x_mutuario /
 * _cooperado" (sufixo troca o último pedaço), "ds.*" e "ds.contratos_*", e
 * "br_cgu_garantia_safra / pe_de_meia" (datasets inteiros; o 2º herda "br_cgu_").
 * Antes o casamento era `p.table === ref`, e essas 17 pontes nunca chegavam.
 */
export function tabelasDaPonte(campo: string): string[] {
  const partes = campo.split("/").map((x) => x.trim()).filter(Boolean);
  if (!partes.length) return [];
  const out: string[] = [];
  const primeira = partes[0]!;
  if (!primeira.includes(".")) {
    // datasets inteiros
    const prefixo = primeira.split("_").slice(0, 2).join("_") + "_";
    for (const p of partes) {
      const ds = p.includes(".") ? p.split(".")[0]! : (p.startsWith(prefixo) ? p : prefixo + p);
      out.push(p.includes(".") ? p : `${ds}.*`);
    }
    return out;
  }
  let ds = primeira.split(".")[0]!;
  let anterior = primeira.split(".").slice(1).join(".");
  out.push(primeira);
  for (const p of partes.slice(1)) {
    if (p.includes(".")) { ds = p.split(".")[0]!; anterior = p.split(".").slice(1).join("."); out.push(p); continue; }
    const tabela = p.startsWith("_") ? anterior.replace(/_[^_]+$/, "") + p : p;
    out.push(`${ds}.${tabela}`);
    anterior = tabela;
  }
  return out;
}

/** `ref` (dataset.tabela) está coberta pelo campo `table` da ponte. */
export function casaTabela(campo: string, ref: string): boolean {
  const r = ref.toLowerCase();
  return tabelasDaPonte(campo.toLowerCase()).some((g) => {
    if (!g.includes("*")) return g === r;
    const re = new RegExp("^" + g.replace(/[.+?^${}()|[\]\\]/g, "\\$&").replace(/\*/g, "[^.]*") + "$");
    return re.test(r);
  });
}

/** Chaves de join que valem por convenção quando nenhuma ponte especial existe. */
const CANONICAS = ["id_municipio", "sigla_uf", "ano", "id_uf"];

/**
 * O "significado" de uma coluna pra fins de join: o `concept` da ponte curada
 * (bridges.yaml) que documenta `tabela.coluna`, ou a própria coluna quando ela
 * é uma chave canônica (não precisa de ponte pra ser reconhecida). `undefined`
 * quando nem uma coisa nem outra — é o sinal que `juncoesSemPonte` (portao.ts)
 * usa pra saber que a junção não tem lastro nenhum.
 */
export function conceitoDaColuna(ref: string, coluna: string): string | undefined {
  const col = coluna.toLowerCase();
  const b = bridges();
  for (const [conceito, pontes] of Object.entries(b.bridges ?? {})) {
    for (const p of pontes ?? []) {
      if (casaTabela(p.table, ref) && p.column.toLowerCase() === col) return p.concept ?? conceito;
    }
  }
  return CANONICAS.includes(col) ? col : undefined;
}

export function dicasDeJoin(tabelas: string[]): string {
  const b = bridges();
  const linhas: string[] = [];

  for (const [conceito, pontes] of Object.entries(b.bridges ?? {})) {
    for (const p of pontes ?? []) {
      const alvo = tabelas.find((t) => casaTabela(p.table, t));
      if (!alvo) continue;
      const expr = p.join_expr ?? p.expr;
      if (!expr) continue;
      linhas.push(
        `  ${alvo}.${p.column} é ${p.concept ?? conceito}: ${expr}` +
        (p.verified ? `  [conferido: ${p.verified}]` : ""),
      );
    }
  }

  const cab = tabelas.length > 1
    ? `JOIN — estas tabelas vêm de datasets diferentes e não têm foreign key.\n` +
      `Junte pela chave canônica quando as duas tiverem: ${CANONICAS.join(", ")}.\n` +
      `id_municipio é VARCHAR de 7 dígitos com zero à esquerda — nunca compare com número.`
    : "";

  if (!linhas.length) return cab;
  return `${cab}\nPontes específicas destas tabelas (a expressão já foi conferida):\n${linhas.join("\n")}`;
}
