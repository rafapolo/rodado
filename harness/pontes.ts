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

/** Chaves de join que valem por convenção quando nenhuma ponte especial existe. */
const CANONICAS = ["id_municipio", "sigla_uf", "ano", "id_uf"];

export function dicasDeJoin(tabelas: string[]): string {
  const b = bridges();
  const linhas: string[] = [];

  for (const [conceito, pontes] of Object.entries(b.bridges ?? {})) {
    for (const p of pontes ?? []) {
      if (!tabelas.includes(p.table)) continue;
      const expr = p.join_expr ?? p.expr;
      if (!expr) continue;
      linhas.push(
        `  ${p.table}.${p.column} é ${p.concept ?? conceito}: ${expr}` +
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
