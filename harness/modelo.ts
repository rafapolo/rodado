/**
 * Cliente do Gemma 4 servido pelo llama-server no beelink.
 *
 * Duas decisões medidas em 2026-09-01 estão embutidas e não devem ser
 * parametrizadas por engano:
 *
 *  - `reasoning: "off"`. Gemma 4 é modelo de thinking; ligado gastou 1.200
 *    tokens e 94,8 s numa pergunta sem produzir SQL nenhuma. Desligado: 3,4 s.
 *  - o system prompt precisa ser **byte-idêntico** entre chamadas. O
 *    llama-server reaproveita o KV do prefixo comum: 1.165 tokens caem de
 *    19,5 s para 0,44 s da 2ª chamada em diante. Qualquer coisa variável no
 *    prefixo (timestamp, ordem não determinística) evapora o ganho em silêncio
 *    — `Resposta.prefilados` existe para flagrar isso.
 */
// O llama-server escuta em 127.0.0.1 no beelink — de propósito, para não
// expor um endpoint de inferência na rede. Do mac, abra o túnel antes:
//
//     ssh -f -N -L 8099:127.0.0.1:8099 beelink
//
const BASE = Bun.env.HARNESS_LLM ?? "http://127.0.0.1:8099";

export interface Resposta {
  texto: string;
  /** tokens do prompt realmente prefilados; ~0 significa cache de prefixo ativo */
  prefilados: number;
  segundos: number;
  /** true quando a resposta bateu no teto de tokens e foi cortada no meio */
  truncada: boolean;
}

export async function pergunta(
  sistema: string,
  usuario: string,
  opcoes: { maxTokens?: number; temperatura?: number } = {},
): Promise<Resposta> {
  const r = await fetch(`${BASE}/v1/chat/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      messages: [
        { role: "system", content: sistema },
        { role: "user", content: usuario },
      ],
      temperature: opcoes.temperatura ?? 0,
      max_tokens: opcoes.maxTokens ?? 200,
      reasoning: "off",
      chat_template_kwargs: { enable_thinking: false },
    }),
    signal: AbortSignal.timeout(Number(Bun.env.HARNESS_TIMEOUT_MS ?? 600_000)),
  });
  if (!r.ok) throw new Error(`llama-server ${r.status}: ${await r.text()}`);
  const d = await r.json() as {
    choices: { message: { content?: string }; finish_reason?: string }[];
    timings?: { prompt_n?: number; predicted_ms?: number };
  };
  return {
    texto: d.choices[0]?.message?.content ?? "",
    prefilados: d.timings?.prompt_n ?? -1,
    segundos: (d.timings?.predicted_ms ?? 0) / 1000,
    truncada: d.choices[0]?.finish_reason === "length",
  };
}

export async function vivo(): Promise<boolean> {
  try {
    const r = await fetch(`${BASE}/health`, { signal: AbortSignal.timeout(5000) });
    return r.ok;
  } catch { return false; }
}
