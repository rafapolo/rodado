import { describe, expect, test, afterEach } from "bun:test";
import { chamadasNativas, decide, sobeGuarda } from "./guarda.ts";

describe("chamadasNativas", () => {
  test("o caso 4 real do backlog", () => {
    const r = chamadasNativas('<|tool_call>call:mcp__rodado__descrever_tabela{tabela:<|"|>br_inep_ideb.escola<|"|>}<tool_call|>');
    expect(r).toEqual([{ nome: "mcp__rodado__descrever_tabela", argumentos: { tabela: "br_inep_ideb.escola" } }]);
  });
  test("SQL com chaves, aspas e quebra de linha dentro da string", () => {
    const sql = "\nWITH x AS (SELECT '{a}' AS s, \"b\" FROM t)\nSELECT * FROM x\n";
    const r = chamadasNativas(`bla <|tool_call>call:mcp__rodado__consultar{sql:<|"|>${sql}<|"|>}<tool_call|>`);
    expect(r[0]?.argumentos).toEqual({ sql });
  });
  test("número, booleano, nulo, lista e objeto aninhado", () => {
    const r = chamadasNativas('<|tool_call>call:f{a:1.5,b:true,c:null,d:[1,<|"|>x<|"|>],e:{f:-2}}<tool_call|>');
    expect(r[0]?.argumentos).toEqual({ a: 1.5, b: true, c: null, d: [1, "x"], e: { f: -2 } });
  });
  test("argumentos vazios", () => {
    expect(chamadasNativas("<|tool_call>call:mcp__rodado__listar_datasets{}<tool_call|>")[0]?.argumentos).toEqual({});
  });
  test("a tag de fechamento sozinha não é chamada — é o caso 2/3", () => {
    expect(chamadasNativas("<tool_call|>")).toEqual([]);
    expect(decide("<tool_call|>").acao).toBe("repete");
  });
  test("chamada cortada no meio não é resgatada", () => {
    expect(chamadasNativas('<|tool_call>call:f{sql:<|"|>SELECT 1')).toEqual([]);
  });
});

const sse = (...eventos: unknown[]) =>
  eventos.map((e) => `data: ${typeof e === "string" ? e : JSON.stringify(e)}\n\n`).join("");
const pedaco = (delta: object, finish_reason: string | null = null) =>
  ({ id: "chatcmpl-x", created: 1, model: "m", object: "chat.completion.chunk", choices: [{ index: 0, delta, finish_reason }] });

const DEGENERADO = sse(pedaco({ role: "assistant", content: null }), pedaco({ reasoning_content: "<tool_call|>" }), pedaco({}, "stop"), "[DONE]");
const SAUDAVEL = sse(pedaco({ role: "assistant", content: null }), pedaco({ content: "789 óbitos" }), pedaco({}, "stop"),
  { choices: [], usage: { prompt_tokens: 1234 } }, "[DONE]");
const ENGOLIDO = sse(pedaco({ role: "assistant", content: null }),
  pedaco({ reasoning_content: '<|tool_call>call:mcp__rodado__listar_tabelas{dataset:<|"|>br_ms_sim<|"|>}<tool_call|>' }),
  pedaco({}, "stop"), "[DONE]");

let fechar: (() => void)[] = [];
afterEach(() => { for (const f of fechar) f(); fechar = []; });

function falso(respostas: string[]) {
  let n = 0;
  const s = Bun.serve({
    hostname: "127.0.0.1", port: 0,
    fetch: () => new Response(respostas[Math.min(n++, respostas.length - 1)], { headers: { "Content-Type": "text/event-stream" } }),
  });
  fechar.push(() => s.stop(true));
  return { url: `http://127.0.0.1:${s.port}`, chamadas: () => n };
}

async function pede(url: string) {
  const r = await fetch(`${url}/chat/completions`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ stream: true, messages: [] }),
  });
  return r.text();
}

describe("sobeGuarda", () => {
  test("turno degenerado é repetido e o laço só vê o saudável", async () => {
    const up = falso([DEGENERADO, SAUDAVEL]);
    const g = sobeGuarda({ upstream: up.url });
    fechar.push(g.para);
    const txt = await pede(g.url);
    expect(up.chamadas()).toBe(2);
    expect(txt).toContain("789 óbitos");
    expect(txt).not.toContain("tool_call|");
    expect(g.stats).toMatchObject({ turnos: 1, repetidos: 1, resgatados: 0, perdidos: 0, contextoMax: 1234 });
  });

  test("chamada engolida pelo pensamento vira tool_calls", async () => {
    const up = falso([ENGOLIDO]);
    const g = sobeGuarda({ upstream: up.url });
    fechar.push(g.para);
    const txt = await pede(g.url);
    expect(up.chamadas()).toBe(1);
    expect(txt).toContain('"name":"mcp__rodado__listar_tabelas"');
    expect(txt).toContain('"arguments":"{\\"dataset\\":\\"br_ms_sim\\"}"');
    expect(txt).toContain('"finish_reason":"tool_calls"');
    expect(txt).not.toContain("reasoning_content");
    expect(txt.trimEnd().endsWith("data: [DONE]")).toBe(true);
    expect(g.stats.resgatados).toBe(1);
  });

  test("desiste depois do teto e devolve o que veio", async () => {
    const up = falso([DEGENERADO]);
    const g = sobeGuarda({ upstream: up.url, tentativas: 3 });
    fechar.push(g.para);
    const txt = await pede(g.url);
    expect(up.chamadas()).toBe(3);
    expect(txt).toContain("<tool_call|>");
    expect(g.stats).toMatchObject({ repetidos: 2, perdidos: 1 });
  });

  test("turno saudável passa direto, sem repetir", async () => {
    const up = falso([SAUDAVEL]);
    const g = sobeGuarda({ upstream: up.url });
    fechar.push(g.para);
    expect(await pede(g.url)).toBe(SAUDAVEL);
    expect(up.chamadas()).toBe(1);
  });
});

test("a repetição proíbe <|channel>; a 1ª tentativa vai intacta", async () => {
  const corpos: string[] = [];
  let n = 0;
  const s = Bun.serve({
    hostname: "127.0.0.1", port: 0,
    async fetch(req) {
      corpos.push(await req.text());
      return new Response(n++ === 0 ? DEGENERADO : SAUDAVEL, { headers: { "Content-Type": "text/event-stream" } });
    },
  });
  fechar.push(() => s.stop(true));
  const g = sobeGuarda({ upstream: `http://127.0.0.1:${s.port}` });
  fechar.push(g.para);
  await pede(g.url);
  expect(JSON.parse(corpos[0]!).logit_bias).toBeUndefined();
  expect(JSON.parse(corpos[1]!).logit_bias).toEqual({ "100": -100 });
});
