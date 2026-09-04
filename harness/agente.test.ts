import { expect, test, describe } from "bun:test";
import { PERSONA, MODELO, converteFerramentas } from "./agente.ts";

// Substitui `patch.test.ts` (deletado junto de `dsh/rodado.patch.yml`). As
// garantias mudam de forma — não há mais YAML pra travar — mas o alvo é o
// mesmo: instruções que corrigiram bugs medidos não podem regredir caladas.

describe("PERSONA — as frases que corrigiram bugs medidos", () => {
  test("instrui a nunca parar num plano esperando aprovação", () => {
    // regras.md: "o modelo às vezes para num plano pedindo aprovação, em vez
    // de executar" — achado 2x em 2026-09-03, corrigido só depois desta frase.
    expect(PERSONA).toMatch(/NUNCA pare a resposta num plano/);
  });

  test("instrui a citar o ÓRGÃO, nunca tabela/dataset/SQL", () => {
    // backlog.md item 3 — a convenção de pages/analises/results/ é citar o
    // órgão de origem, nunca a ferramenta ou a tabela.
    expect(PERSONA).toMatch(/ÓRGÃO de origem/);
    expect(PERSONA).toMatch(/NUNCA o nome da tabela, do dataset ou o SQL/);
  });

  test("exige revisar_resposta antes da resposta final", () => {
    expect(PERSONA).toMatch(/revisar_resposta/);
  });
});

describe("MODELO — os valores medidos, não um chute", () => {
  test("contexto e raciocínio batem com o llama-server real do beelink", () => {
    // -c 32768 no boot do llama-server; reasoning:false porque o desligamento
    // de verdade é o --chat-template-kwargs do lado do servidor, não algo que
    // o cliente manda (operacao.md, "Raciocínio: o que resolve...").
    expect(MODELO.contextWindow).toBe(32768);
    expect(MODELO.maxTokens).toBe(4096);
    expect(MODELO.reasoning).toBe(false);
  });
});

describe("converteFerramentas — MCP → pi-ai sem perder nem duplicar", () => {
  const entrada = [
    { name: "listar_datasets", description: "lista os datasets", inputSchema: { type: "object", properties: {} } },
    { name: "consultar", description: "roda SQL", inputSchema: { type: "object", properties: { sql: { type: "string" } }, required: ["sql"] } },
  ];

  test("preserva nome e descrição 1:1", () => {
    const saida = converteFerramentas(entrada);
    expect(saida.map((t) => t.name)).toEqual(["listar_datasets", "consultar"]);
    expect(saida.map((t) => t.description)).toEqual(["lista os datasets", "roda SQL"]);
  });

  test("não perde nem duplica nenhuma ferramenta", () => {
    const saida = converteFerramentas(entrada);
    expect(saida.length).toBe(entrada.length);
  });

  test("descrição ausente vira string vazia, não undefined", () => {
    const saida = converteFerramentas([{ name: "x", inputSchema: { type: "object", properties: {} } }]);
    expect(saida[0]?.description).toBe("");
  });
});
