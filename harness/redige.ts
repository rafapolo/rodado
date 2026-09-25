#!/usr/bin/env bun
/**
 * B8 — o Gemma redige o relatório, ou só apura o número?
 *
 *     bun harness/redige.ts pages/analises/results/o-salario-nao-explica.md
 *
 * O experimento isola a REDAÇÃO da apuração: os fatos já estão apurados (cada
 * frase com número da análise publicada vira uma linha de ficha), e o modelo
 * só precisa escrever. Se nem assim ele chega ao padrão das análises — 3–4 mil
 * palavras, contra-argumento forte respondido, órgão citado, nenhum número que
 * não veio da ficha —, a Fase 5 não é dele.
 *
 * Mede, sem julgamento de gosto:
 *  - palavras e se a saída foi cortada pelo teto de tokens;
 *  - números inventados: números da prosa que não estão na ficha (anos incluídos);
 *  - cobertura: quantos números da ficha a prosa usa;
 *  - se existe um contra-argumento (seção ou marcador explícito).
 * A saída inteira fica em ~/.rodado-harness/redige/ para leitura.
 */
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { homedir } from "node:os";
import { basename, join } from "node:path";
import { pergunta } from "./modelo.ts";

/** Números como aparecem em pt-BR ("1.234,5", "0,27", "12%", "2022"), normalizados. */
export function numerosDe(texto: string): Set<string> {
  const out = new Set<string>();
  for (const m of texto.matchAll(/(?<![\w.,])[−-]?\d{1,3}(?:\.\d{3})+(?:,\d+)?|[−-]?\d+(?:,\d+)?/g)) {
    const n = m[0].replace(/[−-]/, "").replace(/\./g, "").replace(",", ".");
    const v = Number(n);
    if (!Number.isFinite(v)) continue;
    if (Number.isInteger(v) && v < 10) continue; // "3 grupos", "2 tabelas": ruído
    out.add(String(v));
  }
  return out;
}

/** A ficha: toda frase da análise que carrega número, sem títulos nem tabelas de markdown. */
export function ficha(md: string): string[] {
  const corpo = md.replace(/^---[\s\S]*?---\n/, "").replace(/^\|.*\|$/gm, "").replace(/^#+ .*$/gm, "");
  const frases = corpo.split(/(?<=[.!?])\s+|\n+/).map((f) => f.replace(/[*_`>]/g, "").trim());
  return [...new Set(frases.filter((f) => /\d/.test(f) && f.length > 25))];
}

const SISTEMA = `Você redige análises de dados públicos brasileiros para leitores leigos e exigentes.
Regras que não têm exceção:
- Escreva em português do Brasil, entre 3.000 e 4.000 palavras, em seções com título.
- Use SOMENTE os números da ficha que o usuário manda. Não calcule número novo, não arredonde de outro jeito, não traga número de memória.
- Cite o órgão de origem de cada dado (IBGE, Ministério do Trabalho/RAIS, Ministério da Saúde...). Nunca cite tabela, SQL nem ferramenta.
- Tenha uma seção de contra-argumento: a objeção mais forte que um leitor cético faria, apresentada na sua melhor forma, e depois respondida com os dados da ficha.
- Termine dizendo o que os dados NÃO permitem concluir.`;

if (import.meta.main) {
  const arq = Bun.argv[2];
  if (!arq) { console.error("uso: bun harness/redige.ts <analise.md>"); process.exit(1); }
  const md = readFileSync(arq, "utf8");
  const titulo = (/^title:\s*(.+)$/m.exec(md)?.[1] ?? /^# (.+)$/m.exec(md)?.[1] ?? basename(arq)).replace(/^["']|["']$/g, "");
  const fatos = ficha(md);
  const usuario = `Tema: ${titulo}\n\nFicha de fatos já apurados (um por linha):\n${fatos.map((f) => `- ${f}`).join("\n")}\n\nEscreva a análise.`;

  console.log(`${basename(arq)}: ${fatos.length} fatos na ficha, publicada com ${md.split(/\s+/).length} palavras`);
  const t0 = Date.now();
  const r = await pergunta(SISTEMA, usuario, { maxTokens: 9000, temperatura: 0.3 });
  const texto = r.texto;

  const daFicha = numerosDe(fatos.join("\n"));
  const daProsa = numerosDe(texto);
  const inventados = [...daProsa].filter((n) => !daFicha.has(n));
  const usados = [...daFicha].filter((n) => daProsa.has(n));
  const contra = /contra-?argumento|obje[çc][ãa]o|advogado do diabo|um c[ée]tico|poderia[- ]se argumentar|alguém poderia/i.test(texto);
  const palavras = texto.split(/\s+/).filter(Boolean).length;

  const dir = join(homedir(), ".rodado-harness", "redige");
  mkdirSync(dir, { recursive: true });
  const saida = join(dir, basename(arq));
  writeFileSync(saida, texto);

  console.log(`  ${palavras} palavras em ${((Date.now() - t0) / 1000).toFixed(0)} s${r.truncada ? " — CORTADA no teto de tokens" : ""}`);
  console.log(`  números da ficha usados: ${usados.length}/${daFicha.size}`);
  console.log(`  números fora da ficha: ${inventados.length}${inventados.length ? ` — ${inventados.slice(0, 15).join(", ")}` : ""}`);
  console.log(`  contra-argumento: ${contra ? "sim" : "NÃO"}`);
  console.log(`  texto em ${saida}`);
}
