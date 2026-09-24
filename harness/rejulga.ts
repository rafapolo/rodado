#!/usr/bin/env bun
/**
 * Rejulga uma rodada de pesquisa pelo `r` publicado, não só pelo `n`.
 *
 *     bun harness/rejulga.ts harness/benchmarks/lote_2026-09-24*.json
 *
 * Por que existe. Lido em 2026-09-24, par a par, os 87 casos com `n`: o `n`
 * publicado quase sempre carrega um recorte que a pergunta não diz — "≥30 mil
 * hab" (T06-2), "≥5 mil admissões" (T04-3), "≥30 casos" (T23-2), UF no lugar de
 * município (T05-5) — e só ~25 dos 87 são alcançáveis a partir do texto da
 * pergunta. Na reconferência dos 8 primeiros (15:05–19:30), 6/8 passaram a medir
 * sobre os municípios com `n` na SQL e todos seguiram 0/8 pelo placar. O `n`
 * exato deixou de separar resposta boa de ruim.
 *
 * O que se mede aqui, por caso:
 *  - `n`: o de sempre (o esperado aparece na resposta);
 *  - `sinal`: a resposta cita algum r/correlação com o MESMO sinal do publicado;
 *  - `perto`: e algum deles a no máximo 0,15 do publicado.
 * Uma relação nula publicada (|r| < 0,10) aceita qualquer r citado com |r| < 0,15
 * como `sinal` — "não há relação" é o achado, e o sinal de um zero é ruído.
 *
 * Diagnóstico ao lado do placar, não substituto: o r casar por acaso com um
 * recorte diferente acontece; ler a resposta continua sendo a triagem.
 */
import { readFileSync } from "node:fs";
import { carregaCasos } from "./casos.ts";

/** Coeficientes citados na prosa: "r = −0,27", "r_parcial +0,09", "correlação de 0,41". */
export function coeficientes(texto: string): number[] {
  const out: number[] = [];
  // A prosa do Gemma rotula antes do número: "**Correlação com o PIB (2021):** -0,08".
  // O ano entre parênteses sai antes, senão o "2021" para a busca pelo número.
  const limpo = texto.replace(/\(\s*\d{4}(?:\s*[–-]\s*\d{2,4})?\s*\)/g, "");
  const re = /(?:\br(?:_?parcial|_?bruto)?\s*[=≈:]|\br_?parcial\b|\bcorrela[çc][ãa]o\b|\bcoeficiente\b|\brho\b)[^\n\d+−-]{0,60}([+−-]?\s*[01]?[,.]\d+)/gi;
  for (const m of limpo.matchAll(re)) {
    const v = Number(m[1]!.replace(/\s+/g, "").replace("−", "-").replace(",", "."));
    if (Number.isFinite(v) && Math.abs(v) <= 1) out.push(v);
  }
  return out;
}

export interface Julgamento { sinal: boolean; perto: boolean }

export function julgaR(publicado: number, citados: number[]): Julgamento {
  if (!citados.length) return { sinal: false, perto: false };
  const nulo = Math.abs(publicado) < 0.1;
  const sinal = citados.some((r) => nulo ? Math.abs(r) < 0.15 : Math.sign(r) === Math.sign(publicado));
  const perto = citados.some((r) => Math.abs(r - publicado) <= 0.15);
  return { sinal, perto };
}

const norm = (s: string) => s.replace(/\s+/g, " ").trim();

if (import.meta.main) {
  const arquivos = Bun.argv.slice(2);
  if (!arquivos.length) { console.error("uso: bun harness/rejulga.ts <lote.json>..."); process.exit(1); }
  const porPergunta = new Map(carregaCasos().map((c) => [norm(c.pergunta), c]));
  let total = 0, comR = 0, n = 0, sinal = 0, perto = 0, citou = 0;
  for (const arq of arquivos) {
    const rodada = JSON.parse(readFileSync(arq, "utf8")) as { casos: { pergunta: string; resposta: string; correto?: boolean }[] };
    for (const s of rodada.casos) {
      const c = porPergunta.get(norm(s.pergunta));
      if (!c) continue;
      total++;
      if (s.correto) n++;
      const citados = coeficientes(s.resposta);
      if (citados.length) citou++;
      const linha = [`${c.id.padEnd(6)} n:${s.correto ? "ok" : "--"}`];
      if (c.r !== undefined) {
        comR++;
        const j = julgaR(c.r, citados);
        if (j.sinal) sinal++;
        if (j.perto) perto++;
        linha.push(`r pub ${c.r.toFixed(2).padStart(5)} | citou ${citados.length ? citados.map((r) => r.toFixed(2)).join(",") : "nenhum"}`,
          j.perto ? "PERTO" : j.sinal ? "sinal" : "--");
      } else linha.push("sem r publicado");
      console.log(linha.join("  "));
    }
  }
  console.log(`\n${total} casos · n exato ${n} · citou algum r ${citou} · ` +
    `com r publicado ${comR}: mesmo sinal ${sinal}, a ≤0,15 ${perto}`);
}
