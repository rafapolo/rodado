import { expect, test, describe } from "bun:test";
const { formatar } = await import("../static/render.js" as any);

describe("formatação pt-BR", () => {
  test("ano nunca leva separador de milhar", () => {
    expect(formatar(2022, "ano")).toBe("2022");   // "2.022" é leitura errada
    expect(formatar(2022, "ano_eleicao")).toBe("2022");
  });
  test("identificador não leva separador", () => {
    expect(formatar(3550308, "id_municipio")).toBe("3550308");
    expect(formatar(12345678, "cnpj_basico")).toBe("12345678");
  });
  test("contagem leva separador", () => {
    expect(formatar(203080756, "populacao")).toBe("203.080.756");
  });
  test("coluna monetária vira BRL", () => {
    expect(formatar(1234.5, "valor_contrato")).toBe("R$ 1.234,50");
    expect(formatar(1234.5, "pib_per_capita")).toBe("R$ 1.234,50");
  });
  test("nulo vira travessão", () => expect(formatar(null, "x")).toBe("—"));
});
