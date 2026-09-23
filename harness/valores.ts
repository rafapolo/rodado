/**
 * Os valores reais das colunas de texto de baixa cardinalidade que não têm
 * dicionário: `rede` ('estadual', 'municipal'...), `cargo` ('prefeito'),
 * `produto` ('Gasolina').
 *
 * Medido 2026-09-22: o modelo filtrou `ensino = 'Ensino Médio' AND rede =
 * 'Estadual'` e voltou vazio — o valor guardado é 'medio'/'estadual'. Custou
 * duas consultas descobrir; o mesmo aconteceu com cargo = 'Prefeito'. Mostrar
 * os valores junto da coluna tira essa volta.
 *
 * Calculado na primeira vez que a tabela é descrita e guardado em
 * `dados/valores.json`. Tabela de até 5M linhas é lida inteira; até 50M, pelas
 * primeiras 200 mil linhas (o que aparece é marcado como amostra); acima disso
 * não se calcula — o custo não compensa e as colunas codificadas dessas tabelas
 * já têm dicionário.
 */
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { runSqlSsh } from "./beelink.ts";
import { linhasDe } from "./catalogo.ts";
import { codigos } from "./dicionarios.ts";

const CACHE = new URL("dados/valores.json", import.meta.url).pathname;
const MAX_VALORES = 12;
const INTEIRA = 5_000_000;
const AMOSTRAVEL = 50_000_000;

/** tabela -> { amostra, colunas: coluna -> valores } ; coluna ausente = alta cardinalidade */
type Cache = Record<string, { amostra: boolean; colunas: Record<string, string[]> }>;
let _c: Cache | null = null;
const cache = (): Cache => (_c ??= existsSync(CACHE) ? JSON.parse(readFileSync(CACHE, "utf8")) : {});

const FORA = /^(id_|cpf|cnpj|nis|sequencial|titulo|numero|codigo|cep|email|telefone|data|url)|nome|endereco|bairro|descricao|texto|complemento|logradouro|razao|objeto|justificativa|observ/;

export function candidatas(tabela: string, cols: { name: string; type: string }[]): string[] {
  return cols
    .filter((c) => /^(STRING|VARCHAR)$/i.test(c.type) && !FORA.test(c.name) && !codigos(tabela, c.name))
    .map((c) => c.name)
    .slice(0, 20);
}

export function valores(tabela: string, coluna: string): { lista: string[]; amostra: boolean } | undefined {
  const t = cache()[tabela.toLowerCase()];
  const lista = t?.colunas[coluna.toLowerCase()];
  return lista ? { lista, amostra: t!.amostra } : undefined;
}

const q = (c: string) => `"${c.replace(/"/g, "")}"`;

/** Garante o cache da tabela; falha em silêncio (a descrição sai sem valores). */
export async function garanteValores(tabela: string, cols: { name: string; type: string }[]): Promise<void> {
  const id = tabela.toLowerCase();
  if (cache()[id]) return;
  const linhas = linhasDe(id) ?? 0;
  const alvo = candidatas(id, cols);
  if (!alvo.length || linhas > AMOSTRAVEL) { cache()[id] = { amostra: false, colunas: {} }; return salva(); }
  const amostra = linhas > INTEIRA;
  const fonte = amostra ? `(SELECT ${alvo.map(q).join(", ")} FROM ${id} LIMIT 200000)` : id;
  const r1 = await runSqlSsh(`SELECT ${alvo.map((c) => `approx_count_distinct(${q(c)}) AS ${q(c)}`).join(", ")} FROM ${fonte}`);
  if (r1.error || !r1.rows?.[0]) return;
  const baixas = alvo.filter((c) => { const n = Number(r1.rows![0]![c]); return n > 0 && n <= MAX_VALORES + 2; });
  const colunas: Record<string, string[]> = {};
  if (baixas.length) {
    const r2 = await runSqlSsh(`SELECT ${baixas.map((c) => `list(DISTINCT ${q(c)} ORDER BY ${q(c)}) AS ${q(c)}`).join(", ")} FROM ${fonte}`);
    if (r2.error || !r2.rows?.[0]) return;
    for (const c of baixas) {
      const l = (r2.rows[0]![c] as unknown[] | null ?? []).filter((v) => v !== null).map(String);
      if (l.length && l.length <= MAX_VALORES) colunas[c.toLowerCase()] = l;
    }
  }
  cache()[id] = { amostra, colunas };
  salva();
}

function salva() { writeFileSync(CACHE, JSON.stringify(cache())); }
