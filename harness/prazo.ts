/**
 * Aviso de prazo: perto do teto de tempo, manda responder com o que tem (B27).
 *
 * Medido na B19 (2026-09-26): com turnos de 50–90 s, o orçamento de 30
 * consultas (`mcp.ts`) nunca dispara antes do teto de 25 min do `lote.ts` —
 * o máximo visto foi 18 consultas. No teto o `pi` leva SIGKILL e a resposta
 * inteira some (T03-1, T07-1, T16-4, T23-2: última fala com 0–10 caracteres).
 * O aviso chega junto do próximo resultado de ferramenta, dentro do laço, e
 * deixa alguns turnos para escrever.
 *
 * O relógio começa quando o processo do MCP sobe, que é o começo da tentativa
 * (`lifecycle: "eager"` em `pi.ts`; cada tentativa é um processo novo).
 */

/** Fração do teto em que o aviso começa: 18 dos 25 min. */
export const FRACAO_AVISO = 0.72;

/** Milissegundos até o aviso, a partir do teto da tentativa. */
export const avisoDoTeto = (tetoMs: number) => Math.round(tetoMs * FRACAO_AVISO);

export function mensagemDePrazo(minutos: number): string {
  return `⏱ PRAZO: ${minutos} min gastos nesta pergunta, e o tempo acaba em poucos turnos — ` +
    "quando acaba, a resposta inteira se perde. PARE de consultar e escreva AGORA a resposta final " +
    "com o que já foi apurado, citando os números que os resultados devolveram. Se o que foi apurado " +
    "não basta para responder, diga que não foi possível e por quê.";
}

/**
 * `aviso()` devolve a mensagem de prazo quando já passou `avisoMs` desde o
 * início, e `undefined` antes disso. Vale em todo resultado depois do limiar:
 * o modelo que ignorou o primeiro aviso e consultou de novo vê de novo.
 * `avisoMs <= 0` desliga.
 */
export function criaPrazo(avisoMs: number, agora: () => number = Date.now) {
  const inicio = agora();
  return {
    aviso(): string | undefined {
      if (!(avisoMs > 0)) return undefined;
      const gasto = agora() - inicio;
      return gasto >= avisoMs ? mensagemDePrazo(Math.floor(gasto / 60_000)) : undefined;
    },
  };
}

/** O limiar do ambiente: `HARNESS_AVISO_PRAZO_MS`, senão derivado de `HARNESS_TETO_MIN` (25). */
export function avisoDoAmbiente(env: Record<string, string | undefined>): number {
  if (env.HARNESS_AVISO_PRAZO_MS !== undefined) return Number(env.HARNESS_AVISO_PRAZO_MS);
  return avisoDoTeto(Number(env.HARNESS_TETO_MIN ?? 25) * 60_000);
}
