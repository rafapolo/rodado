/**
 * Cálculos nomeados — a definição única de cada número.
 *
 * Existe porque a mesma pergunta tem mais de uma leitura aritmética e as duas
 * parecem certas. Medido em 2026-09-02: perguntado "PIB per capita médio dos
 * municípios de MG em 2020", o harness respondeu **R$ 23.704,50** — a média das
 * razões municipais. A definição do projeto é `SUM(pib)/SUM(populacao)`, que dá
 * **R$ 32.066,73**. Diferença de 35%, e nenhuma das duas dá erro.
 *
 * `metrics.yaml` foi escrito exatamente para isso, e o harness não o consultava:
 * eu tinha cortado a ferramenta ao enxugar a superfície para quatro.
 */
import { readFileSync } from "node:fs";
import { parse } from "yaml";

const RAIZ = new URL("..", import.meta.url).pathname;

interface Metrica {
  description?: string;
  unit?: string;
  grain?: string[];
  source_table?: string;
  expression?: string;
  required_filters?: string[];
  synonyms?: string[];
  verified?: string;
  needs_join?: { table?: string; on?: string };
}

let _m: Record<string, Metrica> | null = null;
function todas(): Record<string, Metrica> {
  if (!_m) {
    const y = parse(readFileSync(`${RAIZ}docs/context/metrics.yaml`, "utf8")) as
      { metrics?: Record<string, Metrica> } | Record<string, Metrica>;
    _m = ("metrics" in y ? y.metrics : y) as Record<string, Metrica>;
  }
  return _m!;
}

const norm = (s: string) =>
  s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[_\s]+/g, " ").trim();

/**
 * Busca por nome ou sinônimo, exato depois de normalizar — **nunca por
 * similaridade**. "população de SP" e "população carcerária" ficam perto no
 * espaço vetorial e querem tabelas diferentes.
 */
export function metrica(nome: string): string | null {
  const alvo = norm(nome);
  for (const [k, v] of Object.entries(todas())) {
    const chaves = [norm(k), ...(v.synonyms ?? []).map(norm)];
    if (!chaves.includes(alvo)) continue;
    const l = [
      `${k} — ${v.description ?? ""}`,
      `unidade: ${v.unit ?? "?"}`,
      `grão: ${(v.grain ?? []).join(", ")}`,
      `tabela: ${v.source_table ?? "?"}`,
      `EXPRESSÃO (use exatamente esta): ${v.expression ?? "?"}`,
    ];
    if (v.needs_join?.table) l.push(`exige join com ${v.needs_join.table} ON ${v.needs_join.on}`);
    if (v.required_filters?.length) l.push(`filtros obrigatórios: ${v.required_filters.join(", ")}`);
    if (v.verified) l.push(`conferido: ${v.verified}`);
    return l.join("\n");
  }
  return null;
}

export function listaMetricas(): string {
  return Object.entries(todas())
    .map(([k, v]) => `  ${k}: ${v.description ?? ""}`)
    .join("\n");
}
