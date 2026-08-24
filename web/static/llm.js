/**
 * WebLLM — geração de SQL e da resposta em prosa, na aba.
 *
 * Os Qwen2.5-Coder vêm pré-compilados para MLC (0.5B/1.5B/3B/7B), então não há
 * nada a compilar à mão.
 */
export const MODELOS = {
  "1.5b": { id: "Qwen2.5-Coder-1.5B-Instruct-q4f16_1-MLC", rotulo: "1,5 B — rápido, erra mais", gb: 1.1 },
  "3b":   { id: "Qwen2.5-Coder-3B-Instruct-q4f16_1-MLC",   rotulo: "3 B — equilíbrio",          gb: 2.0 },
  "7b":   { id: "Qwen2.5-Coder-7B-Instruct-q4f16_1-MLC",   rotulo: "7 B — melhor, pesado",      gb: 4.5 },
};

let engine = null, carregado = null;

/**
 * Teto por chamada. Um modelo grande em máquina lenta pode levar minutos, e sem
 * teto a página fica presa em "escrevendo o SQL…" sem nunca dizer o que houve.
 * Melhor falhar com mensagem do que esperar para sempre.
 */
const tetoMs = () => {
  try { return Number(new URLSearchParams(location.search).get("teto")) || 180_000; }
  catch { return 180_000; }   // fora do navegador (bun test) não há `location`
};

function comTeto(promessa, oque) {
  const ms = tetoMs();
  return Promise.race([
    promessa,
    new Promise((_, rej) => setTimeout(
      () => rej(new Error(`${oque} passou de ${Math.round(ms / 1000)}s. ` +
        `Um modelo menor costuma resolver — ou recarregue a página.`)), ms)),
  ]);
}

export const temWebGPU = () => typeof navigator !== "undefined" && "gpu" in navigator;
export const pronto = () => engine !== null;
export const modeloAtual = () => carregado;

export async function carregar(chave = "3b", onProgresso) {
  if (!temWebGPU()) throw new Error("Este navegador não tem WebGPU. Use Chrome ou Edge.");
  const alvo = MODELOS[chave];
  if (carregado === alvo.id && engine) return engine;

  const webllm = await import("./vendor/webllm.js");
  engine = await webllm.CreateMLCEngine(alvo.id, {
    initProgressCallback: (r) => onProgresso?.({ texto: r.text, pct: Math.round((r.progress ?? 0) * 100) }),
    // NÃO subir: o wasm pré-compilado é `..._cs1k-webgpu.wasm` e o config do
    // WebLLM traz `overrides: {context_window_size: 4096}`. Pedir 8192 é acima
    // do que a lib compilada suporta. 4k é o teto real, e é o orçamento que o
    // prompt.js tem que respeitar.
    context_window_size: 4096,
  });
  carregado = alvo.id;
  return engine;
}

const tirarCercas = (t) => {
  const s = t.trim();
  const m = s.match(/```(?:sql)?\s*([\s\S]*?)```/i);
  return (m ? m[1] : s).replace(/<think>[\s\S]*?<\/think>/gi, "").trim();
};

/**
 * Completar genérico — para tarefas que não são SQL nem prosa de resposta
 * (ex.: decompor a pergunta em aspectos antes da busca).
 */
export async function completar(prompt, { maxTokens = 300, temperature = 0 } = {}) {
  const r = await comTeto(engine.chat.completions.create({
    messages: [{ role: "user", content: prompt }],
    temperature,
    max_tokens: maxTokens,
  }), "A tarefa auxiliar do modelo");
  return (r.choices[0].message.content ?? "").trim();
}

export async function gerarSQL(prompt) {  const r = await comTeto(engine.chat.completions.create({
    messages: [{ role: "user", content: prompt }],
    temperature: 0,        // SQL não quer criatividade
    max_tokens: 700,
  }), "A geração do SQL");
  const bruto = r.choices[0].message.content ?? "";
  const limpo = tirarCercas(bruto);

  // O prompt manda o modelo responder {"error": "..."} quando não dá. A TUI Rust
  // embrulhava isso como SELECT '{error...}' AS resposta — uma linha falsa. Aqui
  // vira erro de verdade.
  const err = limpo.match(/\{\s*"?error"?\s*:\s*"([^"]+)"/i);
  if (err) return { erro: err[1] };
  if (!/^\s*(SELECT|WITH)\b/i.test(limpo)) return { erro: `O modelo não devolveu SQL: ${limpo.slice(0, 200)}` };
  return { sql: limpo.replace(/;\s*$/, "") };
}

/**
 * Segunda chamada: a prosa e a escolha do gráfico.
 *
 * SEM `response_format: {type:"json_object"}`. Medido: com ele o WebLLM trava
 * indefinidamente neste modelo — precisa compilar uma gramática para o JSON
 * forçado, e isso não termina (>10 min contra 4,5s da geração normal). Pedimos
 * JSON no texto do prompt e extraímos com regex, que é o que o `strip` já fazia
 * para o SQL.
 */
export async function explicar(pergunta, sql, linhas, colunas) {
  const amostra = JSON.stringify(linhas.slice(0, 50));
  const r = await comTeto(engine.chat.completions.create({
    messages: [{
      role: "user",
      content:
`Pergunta: ${pergunta}

SQL executado:
${sql}

Resultado (colunas: ${colunas.join(", ")}):
${amostra.slice(0, 6000)}

Responda em JSON, exatamente neste formato:
{"resposta": "um parágrafo em português do Brasil respondendo à pergunta e citando os números",
 "grafico": {"tipo": "barras|linha|dispersao", "x": "coluna", "y": "coluna", "titulo": "..."}}

Use "grafico": null quando o resultado for um número só ou uma tabela larga demais para um gráfico.`,
    }],
    temperature: 0.2,
    max_tokens: 600,
  }), "A redação da resposta");
  const bruto = (r.choices[0].message.content ?? "").trim();
  // o modelo às vezes embrulha em cerca de markdown ou escreve antes do JSON
  const m = bruto.match(/\{[\s\S]*\}/);
  if (m) {
    try {
      const j = JSON.parse(m[0]);
      return { resposta: j.resposta ?? bruto, grafico: j.grafico ?? null };
    } catch { /* cai pro texto puro */ }
  }
  return { resposta: bruto.replace(/```/g, "").trim(), grafico: null };
}
