import { expect, test, describe } from "bun:test";
import { readFileSync } from "node:fs";

const cols = JSON.parse(readFileSync("web/static/index/colunas.json", "utf-8"));
const ask = await import("../static/ask.js" as any);
globalThis.fetch = (async () => ({ json: async () => cols })) as any;
await ask.carregarColunas();

const T = [{ id: "br_ms_sim.microdados" }, { id: "br_bd_diretorios_brasil.municipio" }];

describe("validarColunas", () => {
  test("não confunde dataset.tabela com alias.coluna", () => {
    // o bug real: `br_ms_sim.microdados` era lido como coluna "microdados"
    expect(ask.validarColunas(
      "SELECT count(*) FROM br_ms_sim.microdados WHERE sigla_uf = 'PE'", T)).toBeNull();
  });
  test("aceita SQL correto com alias", () => {
    expect(ask.validarColunas(
      "SELECT s.ano, s.sigla_uf FROM br_ms_sim.microdados s WHERE s.ano = 2020", T)).toBeNull();
  });
  test("pega coluna inventada de verdade", () => {
    const r = ask.validarColunas("SELECT s.coluna_fantasma FROM br_ms_sim.microdados s", T);
    expect(r).not.toBeNull();
    expect(r.invalidas).toContain("coluna_fantasma");
  });
  test("não acusa palavra reservada", () => {
    expect(ask.validarColunas(
      "SELECT count(*) FROM br_ms_sim.microdados s GROUP BY s.ano", T)).toBeNull();
  });
});
