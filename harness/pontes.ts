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
      if (p.table === ref && p.column.toLowerCase() === col) return p.concept ?? conceito;
    }
  }
  return CANONICAS.includes(col) ? col : undefined;
}

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

/**
 * A metade que `dicasDeJoin` sozinha não cobre: ela lista o que EXISTE, mas
 * fica calada quando NADA existe — a ausência ficava implícita, dependendo do
 * modelo notar que só um lado tem ponte listada. `juncoesSemPonte` (portao.ts)
 * já detecta esse caso, mas só depois que o modelo ESCREVEU um `ON` e a
 * consulta voltou vazia. Aqui não há `ON` ainda — o sinal disponível é mais
 * grosso (a tabela toda, não um par de colunas): entre as colunas de A e as de
 * B, existe ALGUMA que bata em conceito (ponte curada ou chave canônica)? Se
 * não, é o mesmo caso do par emendas/licitacao_item do backlog.md item 12 —
 * confirmado ao vivo: nenhuma coluna real em comum, sem depender de zero
 * linhas pra descobrir.
 */
export function semColunaComum(
  tabelaA: string, colsA: string[],
  tabelaB: string, colsB: string[],
): boolean {
  const conceitosA = new Set(colsA.map((c) => conceitoDaColuna(tabelaA, c)).filter((c): c is string => !!c));
  if (!conceitosA.size) return true;
  return !colsB.some((c) => {
    const k = conceitoDaColuna(tabelaB, c);
    return k !== undefined && conceitosA.has(k);
  });
}

export function avisoSemColunaComum(tabelaA: string, tabelaB: string): string {
  return (
    `⚠ Nenhuma coluna em comum encontrada entre ${tabelaA} e ${tabelaB} ` +
    `(nem ponte curada em bridges.yaml, nem chave canônica com o mesmo nome) — ` +
    `pode não existir junção direta entre estas duas tabelas neste espelho. ` +
    `Antes de tentar um JOIN entre elas, procure uma coluna que aponte de uma ` +
    `pra outra (CNPJ, id_orgao, id_municipio); se não achar, responda só com a ` +
    `parte que tem dado e diga que este cruzamento não é possível com as ` +
    `tabelas disponíveis — não repita a mesma junção esperando resultado diferente.`
  );
}
