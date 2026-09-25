/**
 * Guarda entre o laço (Pi) e o llama-server: conserta o turno, não a sessão.
 *
 * Medido 2026-09-22 com log verboso, llama.cpp `8887a48` e `f072b10`: o turno
 * que "volta vazio" (harness_tasks.md B10) é o Gemma decodificando 3 tokens —
 * `<|channel>` `thought` `<tool_call|>` — e parando em EOS. Não há chamada a
 * resgatar; o modelo nem tentou. A saída era repetir a pergunta inteira numa
 * sessão nova (5-7 min). Aqui a mesma requisição é reenviada: o prefixo já
 * está no cache do servidor, então repetir o turno custa segundos.
 *
 * O outro formato do mesmo bug (casos 4/6: a chamada inteira, bem formada,
 * dentro do bloco de pensamento) é resgatado: a chamada é extraída do
 * `reasoning_content` e devolvida como `tool_calls`.
 *
 * Regra que decide tudo: com raciocínio desligado, um turno saudável sempre
 * produz `content` não vazio ou `tool_calls`. Enquanto nenhum dos dois
 * apareceu, os pedaços ficam retidos; nada chega ao laço até o turno se provar.
 *
 * O turno que se prova por `content` pode ser a resposta final, e esse também
 * fica retido até o fim: todo número dele tem que ter saído de um resultado
 * (`confere.ts`). Se não saiu, a guarda pede a reescrita uma vez, acrescentando
 * a resposta e o pedido ao fim da mesma requisição — o prefixo continua no
 * cache — e o laço recebe só a resposta reescrita.
 */
import {
  semOrigem, valoresVistos, textosDaConversa, pedidoDeReescrita, chaveDaSessao, consultou,
} from "./confere.ts";

export interface Chamada { nome: string; argumentos: Record<string, unknown> }

export interface Estatistica {
  turnos: number;
  repetidos: number;
  resgatados: number;
  perdidos: number;
  /** respostas finais com número sem origem, mandadas reescrever */
  corrigidos: number;
  /** maior `usage.prompt_tokens` visto — o tamanho real do contexto */
  contextoMax: number;
}

const ASPAS = '<|"|>';

/** Lê um valor na sintaxe nativa de argumentos do Gemma 4 a partir de `i`. */
function valor(s: string, i: number): [unknown, number] | undefined {
  i = pula(s, i);
  if (s.startsWith(ASPAS, i)) {
    const fim = s.indexOf(ASPAS, i + ASPAS.length);
    if (fim < 0) return undefined;
    return [s.slice(i + ASPAS.length, fim), fim + ASPAS.length];
  }
  if (s[i] === "{") {
    const obj: Record<string, unknown> = {};
    i = pula(s, i + 1);
    if (s[i] === "}") return [obj, i + 1];
    for (;;) {
      const dois = s.indexOf(":", i);
      if (dois < 0) return undefined;
      const chave = s.slice(i, dois).trim();
      if (!chave || chave.includes("}")) return undefined;
      const v = valor(s, dois + 1);
      if (!v) return undefined;
      obj[chave] = v[0];
      i = pula(s, v[1]);
      if (s[i] === ",") { i = pula(s, i + 1); continue; }
      if (s[i] === "}") return [obj, i + 1];
      return undefined;
    }
  }
  if (s[i] === "[") {
    const arr: unknown[] = [];
    i = pula(s, i + 1);
    if (s[i] === "]") return [arr, i + 1];
    for (;;) {
      const v = valor(s, i);
      if (!v) return undefined;
      arr.push(v[0]);
      i = pula(s, v[1]);
      if (s[i] === ",") { i = pula(s, i + 1); continue; }
      if (s[i] === "]") return [arr, i + 1];
      return undefined;
    }
  }
  const m = /^(true|false|null|-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?)/.exec(s.slice(i));
  if (!m) return undefined;
  const t = m[1]!;
  return [t === "true" ? true : t === "false" ? false : t === "null" ? null : Number(t), i + t.length];
}

function pula(s: string, i: number): number {
  while (i < s.length && /\s/.test(s[i]!)) i++;
  return i;
}

/** Toda chamada `<|tool_call>call:NOME{...}<tool_call|>` bem formada no texto. */
export function chamadasNativas(texto: string): Chamada[] {
  const out: Chamada[] = [];
  const abre = "<|tool_call>call:";
  let i = texto.indexOf(abre);
  while (i >= 0) {
    const ini = i + abre.length;
    const chave = texto.indexOf("{", ini);
    const nome = chave > ini ? texto.slice(ini, chave).trim() : "";
    const v = nome && /^[\w.-]+$/.test(nome) ? valor(texto, chave) : undefined;
    if (v && v[0] && typeof v[0] === "object" && !Array.isArray(v[0])
        && texto.startsWith("<tool_call|>", pula(texto, v[1]))) {
      out.push({ nome, argumentos: v[0] as Record<string, unknown> });
    }
    i = texto.indexOf(abre, ini);
  }
  return out;
}

/** O que fazer com um turno que terminou sem `content` nem `tool_calls`. */
export function decide(raciocinio: string): { acao: "resgata"; chamadas: Chamada[] } | { acao: "repete" } {
  const chamadas = chamadasNativas(raciocinio);
  return chamadas.length ? { acao: "resgata", chamadas } : { acao: "repete" };
}

interface Delta { content?: string | null; reasoning_content?: string; tool_calls?: unknown[] }
interface Pedaco {
  id?: string; created?: number; model?: string; object?: string;
  choices?: { delta?: Delta; finish_reason?: string | null; index?: number }[];
  usage?: { prompt_tokens?: number };
}

/** Blocos SSE (`data: ...`) de um corpo em stream, um por evento. */
async function* eventos(corpo: ReadableStream<Uint8Array>): AsyncGenerator<string> {
  const dec = new TextDecoder();
  let resto = "";
  for await (const bytes of corpo) {
    resto += dec.decode(bytes, { stream: true });
    let k: number;
    while ((k = resto.indexOf("\n\n")) >= 0) {
      const ev = resto.slice(0, k);
      resto = resto.slice(k + 2);
      if (ev.trim()) yield ev;
    }
  }
  resto += dec.decode();
  if (resto.trim()) yield resto;
}

function dados(ev: string): string | undefined {
  const linhas = ev.split("\n").filter((l) => l.startsWith("data:"));
  return linhas.length ? linhas.map((l) => l.slice(5).trimStart()).join("\n") : undefined;
}

/**
 * Tokens de molde do Gemma que vazam para o `content` sem ser resposta. Medido
 * 2026-09-25, rodada B2: a sessão terminou com o texto literal
 * `thought<tool_call|>` como resposta final — o mesmo turno degenerado de B10,
 * só que no `content` em vez do raciocínio, e por isso "provado" e repassado.
 */
const MOLDE = /<\|?[a-z_]+\|?>|\bthought\b/gi;

export function soMolde(texto: string): boolean {
  return texto.replace(MOLDE, "").trim() === "";
}

function prova(d: Delta | undefined): boolean {
  if (!d) return false;
  return (typeof d.content === "string" && !soMolde(d.content)) || (d.tool_calls?.length ?? 0) > 0;
}

function sintetiza(base: Pedaco, chamadas: Chamada[]): string[] {
  const cab = { id: base.id, created: base.created, model: base.model, object: "chat.completion.chunk" };
  const ch = (delta: object, finish_reason: string | null) =>
    `data: ${JSON.stringify({ ...cab, choices: [{ index: 0, delta, finish_reason }] })}`;
  return [
    ch({ role: "assistant", content: null }, null),
    ch({
      tool_calls: chamadas.map((c, index) => ({
        index, id: `call_${crypto.randomUUID().replace(/-/g, "").slice(0, 24)}`, type: "function",
        function: { name: c.nome, arguments: JSON.stringify(c.argumentos) },
      })),
    }, null),
    ch({}, "tool_calls"),
  ];
}

const TETO_RACIOCINIO = Number(Bun.env.HARNESS_GUARDA_TETO ?? 12_000);

/**
 * Corpo da repetição com `<|channel>` (token 100 do Gemma 4) proibido. Todo turno
 * degenerado começa por ele, e com o raciocínio desligado o modelo nunca precisa
 * gerá-lo — o bloco vazio de pensamento, quando existe, vem no prompt. Medido
 * 2026-09-23: repetir a requisição igual degenerou 4 vezes seguidas em ~5k de
 * contexto (2 turnos perdidos numa pergunta); o caminho é quase determinístico
 * naquele estado, então repetir sem mudar nada só rola o mesmo dado.
 */
export function semCanal(texto: string): string {
  try {
    const j = JSON.parse(texto) as { logit_bias?: Record<string, number> };
    j.logit_bias = { ...(j.logit_bias ?? {}), "100": -100 };
    return JSON.stringify(j);
  } catch { return texto; }
}

export function sobeGuarda(opcoes: { upstream?: string; tentativas?: number; porta?: number } = {}) {
  const upstream = (opcoes.upstream ?? Bun.env.HARNESS_LLM ?? "http://127.0.0.1:8099").replace(/\/$/, "");
  const maxTentativas = opcoes.tentativas ?? Number(Bun.env.HARNESS_GUARDA_TENTATIVAS ?? 4);
  const stats: Estatistica = { turnos: 0, repetidos: 0, resgatados: 0, perdidos: 0, corrigidos: 0, contextoMax: 0 };
  /** reescritas já pedidas, por pergunta: uma só, para nunca girar em círculo */
  const reescritas = new Map<string, number>();
  type Msgs = Parameters<typeof textosDaConversa>[0];

  /** Pode conferir esta requisição? Só depois de alguma consulta, e só uma reescrita por pergunta. */
  const confereTurno = (msgs: Msgs) => consultou(msgs) && (reescritas.get(chaveDaSessao(msgs)) ?? 0) < 1;

  /** A requisição de reescrita, ou `undefined` se todo número da resposta tem origem. */
  function reescrita(corpo: object, msgs: Msgs, resposta: string): string | undefined {
    const faltam = semOrigem(resposta, valoresVistos(textosDaConversa(msgs)));
    if (!faltam.length) return undefined;
    stats.corrigidos++;
    const chave = chaveDaSessao(msgs);
    reescritas.set(chave, (reescritas.get(chave) ?? 0) + 1);
    console.error(`guarda: ${faltam.join(", ")} sem origem nos resultados — pedindo reescrita`);
    return JSON.stringify({
      ...corpo,
      messages: [...msgs, { role: "assistant", content: resposta }, { role: "user", content: pedidoDeReescrita(faltam) }],
    });
  }

  const repassa = (req: Request, url: URL, corpo?: string) =>
    fetch(`${upstream}${url.pathname}${url.search}`, {
      method: req.method,
      headers: { "Content-Type": req.headers.get("content-type") ?? "application/json" },
      body: corpo ?? (req.method === "GET" || req.method === "HEAD" ? undefined : req.body),
    });

  const servidor = Bun.serve({
    hostname: "127.0.0.1",
    port: opcoes.porta ?? 0,
    idleTimeout: 0,
    async fetch(req) {
      const url = new URL(req.url);
      if (req.method !== "POST" || !url.pathname.endsWith("/chat/completions")) return repassa(req, url);
      const texto = await req.text();
      let corpo: { stream?: boolean; messages?: Msgs };
      try { corpo = JSON.parse(texto); } catch { return repassa(req, url, texto); }
      stats.turnos++;
      const msgs = corpo.messages ?? [];
      const confere = confereTurno(msgs);
      if (!corpo.stream) return turnoInteiro(req, url, texto, corpo, confere);

      const enc = new TextEncoder();
      const stream = new ReadableStream<Uint8Array>({
        async start(ctl) {
          const escreve = (ev: string) => ctl.enqueue(enc.encode(`${ev}\n\n`));
          let retidos: string[] = [];
          for (let tentativa = 1; tentativa <= maxTentativas; tentativa++) {
            const aborta = new AbortController();
            let res: Response;
            try {
              res = await fetch(`${upstream}${url.pathname}`, {
                method: "POST", headers: { "Content-Type": "application/json" },
                body: tentativa === 1 ? texto : semCanal(texto), signal: aborta.signal,
              });
            } catch (e) {
              if (tentativa < maxTentativas) { stats.repetidos++; continue; }
              ctl.error(e); return;
            }
            if (!res.ok || !res.body) {
              const erro = await res.text();
              if (res.status >= 500 && tentativa < maxTentativas) { stats.repetidos++; continue; }
              escreve(`data: ${JSON.stringify({ error: { code: res.status, message: erro } })}`);
              ctl.close(); return;
            }
            retidos = [];
            let provado = false;
            let segura = false;
            let resposta = "";
            let raciocinio = "";
            let base: Pedaco = {};
            for await (const ev of eventos(res.body)) {
              const d = dados(ev);
              let p: Pedaco | undefined;
              if (d && d !== "[DONE]") { try { p = JSON.parse(d); } catch { /* repassa cru */ } }
              if (p?.usage?.prompt_tokens) stats.contextoMax = Math.max(stats.contextoMax, p.usage.prompt_tokens);
              const delta = p?.choices?.[0]?.delta;
              if (provado && segura) {
                retidos.push(ev);
                resposta += delta?.content ?? "";
                if (delta?.tool_calls?.length) {
                  segura = false;
                  for (const r of retidos) escreve(r);
                }
                continue;
              }
              if (provado) { escreve(ev); continue; }
              if (p?.id && !base.id) base = p;
              if (prova(delta)) {
                provado = true;
                segura = confere && !delta?.tool_calls?.length;
                if (segura) {
                  retidos.push(ev);
                  resposta = delta?.content ?? "";
                  continue;
                }
                for (const r of retidos) escreve(r);
                escreve(ev);
                continue;
              }
              retidos.push(ev);
              raciocinio += delta?.reasoning_content ?? "";
              if (raciocinio.length > TETO_RACIOCINIO && !raciocinio.includes("<|tool_call>")) {
                aborta.abort();
                break;
              }
            }
            if (provado) {
              const nova = segura ? reescrita(corpo, msgs, resposta) : undefined;
              const res2 = nova ? await fetch(`${propria}/chat/completions`, {
                method: "POST", headers: { "Content-Type": "application/json" }, body: nova,
              }).catch(() => undefined) : undefined;
              if (res2?.ok && res2.body) for await (const b of res2.body) ctl.enqueue(b);
              else if (segura) for (const r of retidos) escreve(r);
              ctl.close(); return;
            }

            const d = decide(raciocinio);
            if (d.acao === "resgata") {
              stats.resgatados++;
              for (const ev of sintetiza(base, d.chamadas)) escreve(ev);
              for (const ev of retidos) {
                const x = dados(ev);
                if (x === "[DONE]") continue;
                try { if ((JSON.parse(x ?? "{}") as Pedaco).choices?.length === 0) escreve(ev); } catch { /* descarta */ }
              }
              escreve("data: [DONE]");
              ctl.close(); return;
            }
            if (tentativa < maxTentativas) stats.repetidos++;
          }
          stats.perdidos++;
          for (const r of retidos) escreve(r);
          ctl.close();
        },
      });
      return new Response(stream, {
        headers: { "Content-Type": "text/event-stream", "Cache-Control": "no-cache", Connection: "keep-alive" },
      });
    },
  });

  // a reescrita volta pela própria guarda: o turno dela também é conferido
  // contra B10 (vazio, chamada dentro do raciocínio), só não é reconferido
  const propria = `http://127.0.0.1:${servidor.port}/v1`;

  async function turnoInteiro(
    req: Request, url: URL, texto: string, corpo: { messages?: Msgs }, confere: boolean,
  ): Promise<Response> {
    let ultimo: Response | undefined;
    for (let tentativa = 1; tentativa <= maxTentativas; tentativa++) {
      const res = await repassa(req, url, tentativa === 1 ? texto : semCanal(texto));
      if (!res.ok) { if (res.status >= 500 && tentativa < maxTentativas) { stats.repetidos++; continue; } return res; }
      const j = await res.json() as {
        choices?: { message?: { content?: string | null; reasoning_content?: string; tool_calls?: unknown[] }; finish_reason?: string }[];
        usage?: { prompt_tokens?: number };
      };
      if (j.usage?.prompt_tokens) stats.contextoMax = Math.max(stats.contextoMax, j.usage.prompt_tokens);
      const m = j.choices?.[0]?.message;
      if (!m || prova({ content: m.content, tool_calls: m.tool_calls })) {
        const nova = confere && m?.content && !m.tool_calls?.length
          ? reescrita(corpo, corpo.messages ?? [], m.content) : undefined;
        if (nova) {
          const res2 = await fetch(`${propria}/chat/completions`, {
            method: "POST", headers: { "Content-Type": "application/json" }, body: nova,
          }).catch(() => undefined);
          if (res2?.ok) return res2;
        }
        return Response.json(j);
      }
      const d = decide(m.reasoning_content ?? "");
      if (d.acao === "resgata") {
        stats.resgatados++;
        m.content = null;
        m.reasoning_content = undefined;
        m.tool_calls = d.chamadas.map((c) => ({
          id: `call_${crypto.randomUUID().replace(/-/g, "").slice(0, 24)}`, type: "function",
          function: { name: c.nome, arguments: JSON.stringify(c.argumentos) },
        }));
        j.choices![0]!.finish_reason = "tool_calls";
        return Response.json(j);
      }
      ultimo = Response.json(j);
      if (tentativa < maxTentativas) stats.repetidos++;
    }
    stats.perdidos++;
    return ultimo!;
  }

  return {
    url: propria,
    stats,
    para: () => servidor.stop(true),
  };
}

export function resumoGuarda(s: Estatistica): string {
  return `guarda: ${s.turnos} turnos · ${s.repetidos} repetidos · ${s.resgatados} resgatados · ${s.perdidos} perdidos · ${s.corrigidos} corrigidos · contexto máx ${s.contextoMax} tokens`;
}
