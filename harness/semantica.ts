/**
 * O que a descrição de uma tabela precisa dizer além de nome e tipo: a nota de
 * semântica curada (`dados/notas.json`), o cálculo verificado que usa aquela
 * tabela (`metrics.yaml`) e, quando o modelo inventa uma tabela, as reais mais
 * parecidas com o nome que ele tentou.
 *
 * Tudo sem ida ao beelink. `definicao_de_calculo` continua existindo, mas o
 * modelo raramente a chama — medido 2026-09-22: montou o saldo do CAGED com um
 * CASE sobre tipo_movimentacao em vez de SUM(saldo_movimentacao), que é a
 * definição verificada. Mostrar a definição junto da tabela dispensa a chamada.
 */
import { readFileSync } from "node:fs";
import { parse } from "yaml";
import { listaDatasets, tabelasDe } from "./catalogo.ts";

const RAIZ = new URL("..", import.meta.url).pathname;

type Notas = Record<string, Record<string, string>>;
let _notas: Notas | null = null;
function notas(): Notas {
  if (!_notas) {
    const bruto = JSON.parse(readFileSync(`${RAIZ}harness/dados/notas.json`, "utf8")) as Record<string, unknown>;
    _notas = Object.fromEntries(Object.entries(bruto).filter(([k]) => !k.startsWith("_"))) as Notas;
  }
  return _notas;
}

export const notaTabela = (tabela: string) => notas()[tabela.toLowerCase()]?.["*"] ?? "";
export const notaColuna = (tabela: string, coluna: string) => notas()[tabela.toLowerCase()]?.[coluna.toLowerCase()] ?? "";

interface Metrica { source_table?: string; expression?: string; required_filters?: string[]; unit?: string }
let _metricas: Record<string, Metrica> | null = null;
function metricas(): Record<string, Metrica> {
  if (!_metricas) {
    const y = parse(readFileSync(`${RAIZ}docs/context/metrics.yaml`, "utf8")) as { metrics?: Record<string, Metrica> };
    _metricas = y.metrics ?? {};
  }
  return _metricas;
}

/** Os cálculos verificados cuja tabela-fonte é esta, prontos para colar na SQL. */
export function calculosDaTabela(tabela: string): string[] {
  return Object.entries(metricas())
    .filter(([, m]) => m.source_table === tabela.toLowerCase() && m.expression && !m.expression.startsWith("n/a"))
    .map(([nome, m]) => `${nome} = ${m.expression!.replace(/\s+/g, " ").trim()}` +
      (m.unit ? ` (${m.unit})` : ""));
}

const raiz = (t: string) => t.toLowerCase().replace(/(oes|aes|s)$/, "");
const tokens = (s: string) => new Set(s.toLowerCase().split(/[._\s]+/).filter((t) => t.length > 2 && t !== "br").map(raiz));

/** As tabelas reais mais parecidas com um nome inventado ("br_ibge.municipios"). */
export function sugereTabelas(ref: string, n = 3): string[] {
  const alvo = tokens(ref);
  if (!alvo.size) return [];
  const cand: [string, number][] = [];
  for (const linha of listaDatasets()) {
    const ds = linha.split(/\s/)[0]!;
    for (const t of tabelasDe(ds)) {
      const id = `${ds}.${t.tabela}`;
      const tkDs = tokens(ds), tkTb = tokens(t.tabela);
      let s = 0;
      for (const a of alvo) s += (tkTb.has(a) ? 2 * a.length : 0) + (tkDs.has(a) ? a.length : 0);
      // "municipios" tentado, "municipio" existe: o nome da tabela inteiro bate
      if ([...tkTb].length === 1 && alvo.has([...tkTb][0]!)) s += 10;
      if (s) cand.push([id, s + Math.min(t.linhas, 1e9) / 1e12]);
    }
  }
  return cand.sort((a, b) => b[1] - a[1]).slice(0, n).map(([id]) => id);
}

/** Onde estão os nomes: o erro mais frequente é código no lugar do nome. */
export const DIRETORIOS =
  "Nomes: município em br_bd_diretorios_brasil.municipio (id_municipio, nome, sigla_uf); " +
  "estado em br_bd_diretorios_brasil.uf (sigla, nome, regiao).";
