/**
 * A régua sendo medida. Os dois primeiros testes são os literais do item 0 do
 * backlog — são eles que decidem se o conserto fechou.
 */
import { expect, test, describe } from "bun:test";
import {
  avalia, bate, numeros, normalizaNumero, casoEcoa,
  avisaConfigDivergente, avisaPrefill, extraiPrefills, LIMIAR_PREFILL,
} from "./acerto.ts";

describe("fronteira de número", () => {
  test("789 NÃO casa dentro de 1789 — o caso que fecha o item 0", () => {
    const a = avalia("Foram 1789 registros no período.", "789", "quantos registros?");
    expect(a.certo).toBe(false);
    expect(a.veredito).toBe("errado");
    expect(a.achados).toEqual([1789]);
    // e pela porta antiga, que compara.ts usava
    expect(bate("Foram 1789 registros no período.", "789")).toBe(false);
  });

  test("esperado 2022 com o ano na pergunta não conta como acerto", () => {
    const a = avalia(
      "Em 2022 não foram encontrados óbitos com esse perfil.",
      "2022",
      "Quantos óbitos por suicídio em 2022?",
    );
    expect(a.eco).toBe(true);
    expect(a.certo).toBe(false);
    expect(a.veredito).toBe("eco");
    // "não mede", não "errou": bate() devolve undefined e o caso sai do denominador
    expect(bate("Em 2022 não foram encontrados óbitos.", "2022", "…em 2022?")).toBeUndefined();
  });

  test("as formas que a resposta usa de verdade casam", () => {
    for (const r of ["**789**", "789 óbitos", "foram 789.", "total: 789\n", "(789)"]) {
      expect(avalia(r, "789", "quantos óbitos?").certo).toBe(true);
    }
  });

  test("decimal não é o inteiro", () => {
    expect(avalia("a taxa foi 789,5 por mil", "789").certo).toBe(false);
    expect(avalia("a taxa foi 789,5 por mil", "789,5").certo).toBe(true);
  });

  test("separador de milhar pt-BR, ponto e espaço", () => {
    expect(avalia("foram 4.251 municípios", "4251").certo).toBe(true);
    expect(avalia("foram 4251 municípios", "4.251").certo).toBe(true);
    expect(avalia("foram 1 657 escolas", "1657").certo).toBe(true);
    expect(avalia("R$ 1.234,56 por habitante", "1.234,56").certo).toBe(true);
  });

  test("substring de dígitos não sobrevive à concatenação", () => {
    // a régua velha achava 4251 dentro de "42.510" (ambos viram "42510")
    expect(avalia("foram 42.510 registros", "4251").certo).toBe(false);
    expect(avalia("R$ 1.234,56", "234").certo).toBe(false);
  });

  test("sem gabarito não vira acerto nem erro", () => {
    expect(bate("qualquer coisa", undefined)).toBeUndefined();
    expect(avalia("qualquer coisa", undefined).veredito).toBe("sem_gabarito");
  });

  test("numeros() lê da esquerda para a direita, sem colar números vizinhos", () => {
    expect(numeros("em 2022, 789 óbitos")).toEqual([2022, 789]);
    expect(numeros("1789")).toEqual([1789]);
    expect(numeros("sem número")).toEqual([]);
  });

  test("normalizaNumero", () => {
    expect(normalizaNumero("4.251")).toBe(4251);
    expect(normalizaNumero("1 657")).toBe(1657);
    expect(normalizaNumero("0,97")).toBe(0.97);
    expect(normalizaNumero("abc")).toBeUndefined();
  });

  test("casoEcoa audita o TSV antes de gastar 6 min por pergunta", () => {
    expect(casoEcoa("Quantos óbitos em 2022?", "2022")).toBe(true);
    expect(casoEcoa("Quantos óbitos em 2022?", "789")).toBe(false);
  });
});

describe("config junto do tempo", () => {
  const a = { np: 1, ctx: 32768, modelo: "gemma-4-26B_q4_0-it.gguf" };

  test("-np diferente vira aviso", () => {
    const m = avisaConfigDivergente(a, { ...a, np: 5 }, "rodada7", "rodada8");
    expect(m).toContain("-np 1 vs 5");
    expect(m).toContain("rodada7");
  });

  test("config igual não polui a saída", () => {
    expect(avisaConfigDivergente(a, { ...a })).toBeUndefined();
  });

  test("config ausente também é aviso — 'não sei' não é 'igual'", () => {
    expect(avisaConfigDivergente(a, undefined)).toContain("NÃO são comparáveis");
  });
});

describe("prefill", () => {
  test("prefill do tamanho da pergunta passa calado", () => {
    expect(avisaPrefill([97, 177, 248])).toBeUndefined();
  });

  test("prefill do tamanho do prefixo acusa", () => {
    expect(avisaPrefill([97, 6849])).toContain("6849");
    expect(LIMIAR_PREFILL).toBeGreaterThan(248);
    expect(LIMIAR_PREFILL).toBeLessThan(6849);
  });

  test("extraiPrefills lê a linha real do llama-server", () => {
    const log = [
      "5.12.444.471 I slot print_timing: id  0 | task 517 | prompt eval time =    3524.46 ms /   101 tokens (   34.90 ms per token,    28.66 tokens per second)",
      "5.12.444.478 I slot print_timing: id  0 | task 517 |        eval time =   13847.71 ms /   116 tokens (  120.41 ms per token,     8.30 tokens per second)",
      "5.40.934.117 I slot print_timing: id  0 | task 635 | prompt eval time =    5498.58 ms /   177 tokens (   31.07 ms per token,    32.19 tokens per second)",
    ].join("\n");
    // o `eval time` do meio é geração, não prefill — não pode entrar
    expect(extraiPrefills(log)).toEqual([101, 177]);
  });
});
