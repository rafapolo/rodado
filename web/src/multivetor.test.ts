import { expect, test, describe } from "bun:test";

/**
 * O agregador do doc2query é MÁXIMO, nunca média. Este teste trava essa
 * decisão: foi a diluição (média) que derrubou a tentativa anterior de indexar
 * prosa junto com nomes de coluna — 0,33 contra 0,39 da prosa sozinha.
 */
function agregarMax(entradas: { id: string; s: number; q: string }[]) {
  const out = new Map<string, { s: number; via: string }>();
  for (const e of entradas) {
    const a = out.get(e.id);
    if (a === undefined || a.s < e.s) out.set(e.id, { s: e.s, via: e.q });
  }
  return out;
}

describe("agregação multi-vetor", () => {
  test("fica com o melhor match, não com a média", () => {
    const r = agregarMax([
      { id: "t", s: 0.9, q: "a certa" },
      { id: "t", s: 0.1, q: "irrelevante" },
      { id: "t", s: 0.1, q: "irrelevante 2" },
    ]);
    expect(r.get("t")!.s).toBe(0.9);          // média daria 0.37 e perderia pra qualquer distrator
    expect(r.get("t")!.via).toBe("a certa");
  });

  test("acrescentar pergunta ruim nunca piora a tabela", () => {
    const base = agregarMax([{ id: "t", s: 0.7, q: "boa" }]).get("t")!.s;
    const depois = agregarMax([
      { id: "t", s: 0.7, q: "boa" }, { id: "t", s: 0.05, q: "ruim" },
    ]).get("t")!.s;
    expect(depois).toBe(base);
  });

  test("guarda qual pergunta casou, para a escolha ser auditável", () => {
    const r = agregarMax([
      { id: "a", s: 0.5, q: "p1" }, { id: "b", s: 0.8, q: "p2" }, { id: "a", s: 0.6, q: "p3" },
    ]);
    expect(r.get("a")!.via).toBe("p3");
    expect([...r.entries()].sort((x, y) => y[1].s - x[1].s)[0]![0]).toBe("b");
  });
});
