import { describe, expect, test } from "bun:test";
import { casaTabela, tabelasDaPonte, dicasDeJoin, conceitoDaColuna } from "./pontes.ts";

describe("B33 — ponte com várias tabelas no campo `table` chega ao modelo", () => {
  test("ds.a / b: b herda o dataset", () => {
    expect(tabelasDaPonte("br_transferegov.programas / planos_acao"))
      .toEqual(["br_transferegov.programas", "br_transferegov.planos_acao"]);
    expect(casaTabela("br_ms_sinan.microdados_influenza_srag / dengue", "br_ms_sinan.dengue")).toBe(true);
  });
  test("sufixo `_x` troca o último pedaço do nome anterior", () => {
    expect(tabelasDaPonte("br_bcb_sicor.recurso_publico_mutuario / _cooperado / _propriedade")).toEqual([
      "br_bcb_sicor.recurso_publico_mutuario", "br_bcb_sicor.recurso_publico_cooperado", "br_bcb_sicor.recurso_publico_propriedade",
    ]);
  });
  test("curingas: ds.* e ds.contratos_*", () => {
    expect(casaTabela("br_tcu_inidoneos.*", "br_tcu_inidoneos.empresas")).toBe(true);
    expect(casaTabela("br_tce_rj.contratos_*", "br_tce_rj.contratos_municipio")).toBe(true);
    expect(casaTabela("br_tce_rj.contratos_*", "br_tce_rj.licitacoes")).toBe(false);
    expect(casaTabela("br_ibge_censo2022_raca.* / br_ibge_censo2022_religiao.*", "br_ibge_censo2022_religiao.religiao")).toBe(true);
  });
  test("datasets inteiros sem ponto: o 2º herda o prefixo br_cgu_", () => {
    expect(casaTabela("br_cgu_garantia_safra / pe_de_meia / seguro_defeso", "br_cgu_pe_de_meia.microdados")).toBe(true);
    expect(casaTabela("br_cgu_garantia_safra / pe_de_meia / seguro_defeso", "br_cgu_sancoes.ceis")).toBe(false);
  });
  test("nome exato continua casando só a si mesmo", () => {
    expect(casaTabela("br_anp_combustiveis.precos", "br_anp_combustiveis.precos")).toBe(true);
    expect(casaTabela("br_anp_combustiveis.precos", "br_anp_combustiveis.precos_x")).toBe(false);
  });
  test("dicasDeJoin e conceitoDaColuna enxergam a ponte multi-tabela", () => {
    expect(dicasDeJoin(["br_cgu_pe_de_meia.microdados"])).toContain("br_cgu_pe_de_meia.microdados.uf é sigla_uf");
    expect(conceitoDaColuna("br_cgu_seguro_defeso.microdados", "uf")).toBe("sigla_uf");
  });
});
