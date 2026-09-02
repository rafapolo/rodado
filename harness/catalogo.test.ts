import { expect, test, describe } from "bun:test";
import { resolveDataset, listaDatasets } from "./catalogo.ts";

describe("resolveDataset — os erros de grafia medidos", () => {
  test("nome exato passa", () => {
    expect(resolveDataset("br_ms_sim")).toBe("br_ms_sim");
  });
  test("sem o prefixo br_", () => {
    expect(resolveDataset("ms_sim")).toBe("br_ms_sim");
  });
  test("prefixo world_ também resolve, não só br_", () => {
    // Medido em 2026-09-02: o modelo respondeu `olympedia_olympics` e o dataset
    // é `world_olympedia_olympics`. Só `br_` era tentado, então um acerto virava
    // falha na contagem.
    expect(resolveDataset("olympedia_olympics")).toBe("world_olympedia_olympics");
  });
  test("br_seeg foi removido do espelho — não inventa substituto", () => {
    // Enquanto existia, `seeg` resolvia para ele. Removido em 2026-09-02, o
    // certo é devolver null: mapear para br_seeg_emissoes seria adivinhar.
    expect(resolveDataset("seeg")).toBeNull();
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
