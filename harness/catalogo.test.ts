import { expect, test, describe } from "bun:test";
import { resolveDataset, listaDatasets } from "./catalogo.ts";

describe("resolveDataset — os erros de grafia medidos", () => {
  test("nome exato passa", () => {
    expect(resolveDataset("br_ms_sim")).toBe("br_ms_sim");
  });
  test("sem o prefixo br_", () => {
    expect(resolveDataset("ms_sim")).toBe("br_ms_sim");
  });
  test("seeg resolve para br_seeg, que EXISTE — não para br_seeg_emissoes", () => {
    // As duas são reais e ambas têm emissão municipal. Mapear prefixo aqui
    // trocaria uma escolha defensável do modelo por outra, calado.
    expect(resolveDataset("seeg")).toBe("br_seeg");
  });
  test("underscore a mais no censo (1 falha medida)", () => {
    expect(resolveDataset("ibge_censo_2022_religiao")).toBe("br_ibge_censo2022_religiao");
  });
  test("nome inventado devolve null, não um palpite", () => {
    expect(resolveDataset("br_nao_existe_mesmo")).toBeNull();
  });
  test("prefixo solto não vira palpite", () => {
    expect(resolveDataset("ibge")).toBeNull();
    expect(resolveDataset("ms")).toBeNull();
  });
  test("todo dataset do catálogo resolve para si mesmo", () => {
    for (const d of listaDatasets()) expect(resolveDataset(d)).toBe(d);
  });
});
