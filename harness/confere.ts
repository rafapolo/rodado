/**
 * Conferência de números: todo número da resposta final tem que ter saído de
 * algum resultado que o modelo viu (ou da pergunta, ou da própria SQL).
 *
 * Medido 2026-09-24 (Pi, caso 22/43, CAGED do PR 2022): a consulta devolveu
 * `115879` e a resposta saiu `115.798`. O portão só vê a SQL, e sem gabarito
 * o número errado sai plausível. Esta conferência não precisa de gabarito: ela
 * pergunta só "este número está em algum lugar do que foi apurado?".
 *
 * Arredondar vale — "328,3 milhões" confere com 328.267.000, "12,3%" com
 * 0,1234 —, girar dígito não: sem casa decimal, o inteiro tem que ser o mesmo.
 * Fica de fora o que não é apuração: inteiro abaixo de 100 (posição de ranking,
 * "os 10 maiores"), ano solto e potência de 10 ("por 100 mil habitantes").
 */

const NUMERO = /\d{1,3}(?:[.  ]\d{3})+(?:,\d+)?|\d+(?:,\d+)?/g;

const ESCALA: [RegExp, number][] = [
  [/^\s*mil\b/i, 1e3],
  [/^\s*(milh(ão|ões|ao|oes)|mi)\b/i, 1e6],
  [/^\s*(bilh(ão|ões|ao|oes)|bi)\b/i, 1e9],
  [/^\s*(trilh(ão|ões|ao|oes)|tri)\b/i, 1e12],
];

export interface Citado {
  /** como aparece na resposta */
  texto: string;
  /** o valor antes da escala: "328,3 milhões" -> 328.3 */
  mantissa: number;
  casas: number;
  escala: number;
  porcento: boolean;
}

/** Os números da resposta, com a precisão com que foram escritos. */
export function citados(resposta: string): Citado[] {
  const out: Citado[] = [];
  for (const m of resposta.matchAll(NUMERO)) {
    const bruto = m[0];
    const [int, dec] = bruto.replace(/[.\s ]/g, "").split(",");
    const mantissa = Number(`${int}${dec ? `.${dec}` : ""}`);
    if (!Number.isFinite(mantissa)) continue;
    const fim = m.index! + bruto.length;
    const depois = resposta.slice(fim, fim + 14);
    const escala = ESCALA.find(([re]) => re.test(depois))?.[1] ?? 1;
    out.push({ texto: bruto, mantissa, casas: dec?.length ?? 0, escala, porcento: /^\s*%/.test(depois) });
  }
  return out;
}

function isento(c: Citado): boolean {
  const v = c.mantissa * c.escala;
  if (c.casas === 0 && c.escala === 1 && v < 100) return true;
  if (c.casas === 0 && c.escala === 1 && /^\d{4}$/.test(c.texto) && v >= 1900 && v <= 2100) return true;
  return c.casas === 0 && v >= 100 && Number.isInteger(Math.log10(v));
}

/**
 * Todo valor que um texto de ferramenta, pergunta ou SQL pode querer dizer.
 * Mistura de propósito as duas notações: o resultado de hoje vem em pt-BR
 * (`115.879`), a SQL e as sessões antigas em notação crua (`0.4312`).
 */
export function valoresVistos(textos: string[]): number[] {
  const out = new Set<number>();
  for (const t of textos) {
    for (const m of t.matchAll(NUMERO)) {
      const v = Number(m[0].replace(/[.\s ]/g, "").replace(",", "."));
      if (Number.isFinite(v)) out.add(v);
    }
    for (const m of t.matchAll(/\d+(?:\.\d+)?(?:e[-+]?\d+)?/gi)) {
      const v = Number(m[0]);
      if (Number.isFinite(v)) out.add(v);
    }
  }
  return [...out];
}

function confere(c: Citado, vistos: number[]): boolean {
  const alvo = c.mantissa;
  const tol = 0.5 * 10 ** -c.casas + 1e-9;
  for (const r of vistos) {
    for (const x of c.porcento ? [r, r * 100] : [r]) {
      if (Math.abs(Math.abs(x) / c.escala - alvo) <= tol) return true;
    }
  }
  return false;
}

/** Os números da resposta que não aparecem em nada do que foi apurado. */
export function semOrigem(resposta: string, vistos: number[]): string[] {
  return [...new Set(citados(resposta).filter((c) => !isento(c) && !confere(c, vistos)).map((c) => c.texto))];
}

export const MARCA = "[conferência de números]";

export function pedidoDeReescrita(faltam: string[]): string {
  return `${MARCA} Na sua resposta, ${faltam.map((f) => `"${f}"`).join(", ")} não ` +
    `${faltam.length > 1 ? "aparecem" : "aparece"} em nenhum resultado das consultas. Releia os resultados acima e ` +
    "reescreva a resposta final copiando cada número exatamente como está no resultado (já vem em pt-BR). " +
    "Se o número foi calculado de cabeça, calcule-o numa consulta.";
}

type Parte = string | { type?: string; text?: string }[] | null | undefined;
interface Mensagem {
  role?: string;
  content?: Parte;
  tool_calls?: { function?: { arguments?: string } }[];
}

const textoDe = (p: Parte) =>
  typeof p === "string" ? p : Array.isArray(p) ? p.map((x) => x.text ?? "").join("\n") : "";

/**
 * O que a requisição mostrou ao modelo, fora o system prompt: pergunta,
 * resultados de ferramenta e os argumentos que ele mesmo mandou (a SQL tem
 * os códigos e limiares que a resposta pode repetir).
 */
export function textosDaConversa(mensagens: Mensagem[]): string[] {
  const out: string[] = [];
  for (const m of mensagens) {
    if (m.role === "system") continue;
    out.push(textoDe(m.content));
    for (const t of m.tool_calls ?? []) out.push(t.function?.arguments ?? "");
  }
  return out;
}

/** A pergunta que identifica a sessão: a primeira mensagem do usuário. */
export const chaveDaSessao = (mensagens: Mensagem[]) => textoDe(mensagens.find((m) => m.role === "user")?.content);

/** A sessão já consultou alguma coisa? Sem resultado de ferramenta, não há o que conferir. */
export const consultou = (mensagens: Mensagem[]) => mensagens.some((m) => m.role === "tool");
