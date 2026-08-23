import { expect, test, describe, beforeAll } from "bun:test";
import { readFileSync } from "node:fs";

// prompt.js é um módulo de navegador sem dependência de DOM na parte de Tier 1,
// então dá pra exercitá-lo aqui direto — é a lógica que mais custou na versão
// Rust e a que mais barato se protege.
let P: any;
beforeAll(async () => {
  P = await import("../static/prompt.js");
  const sem = JSON.parse(readFileSync("web/static/index/semantica.json", "utf-8"));
  globalThis.fetch = (async () => ({ json: async () => sem })) as any;
  await P.carregarSemantica();
});

describe("Tier 1 — métrica determinística", () => {
  test("resolve população com ano", () => {
    const r = P.resolverMetrica("qual a população em 2022");
    expect(r).not.toBeNull();
    expect(r.caiu).toBe(false);
    expect(r.sql).toContain("ano = 2022");
  });

  test("o match mais LONGO vence — pib per capita não é pib", () => {
    const r = P.resolverMetrica("qual o pib per capita em 2021");
    expect(r?.metrica.name).toBe("pib_per_capita");
  });

  test("cai pro modelo quando sobra termo não explicado", () => {
    // 'por municipio' não é filtro que sabemos ler: responder o agregado
    // nacional aqui seria errado e silencioso.
    const r = P.resolverMetrica("populacao por municipio em 2022");
    expect(r?.caiu).toBe(true);
    expect(r.motivo).toContain("municipio");
  });

  test("cai quando falta o filtro obrigatório", () => {
    const r = P.resolverMetrica("qual a populacao");
    expect(r?.caiu).toBe(true);
    expect(r.motivo).toContain("ano");
  });

  test("devolve null quando não é métrica nomeada", () => {
    expect(P.resolverMetrica("quais empresas doaram para candidatos em 2022")).toBeNull();
  });

  test("entende sinônimo e acento", () => {
    const r = P.resolverMetrica("quantos habitantes em 2022");
    expect(r?.metrica.name).toBe("populacao");
  });
});
