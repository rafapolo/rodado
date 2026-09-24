import { describe, expect, test } from "bun:test";
import { sugereTabelas, calculosDaTabela, notaColuna, notaTabela } from "./semantica.ts";

describe("semantica", () => {
  test("o cálculo verificado aparece com a tabela-fonte", () => {
    expect(calculosDaTabela("br_me_caged.microdados_movimentacao")).toEqual([
      "saldo_caged = SUM(saldo_movimentacao) (postos de trabalho)",
    ]);
    expect(calculosDaTabela("br_ibge_pib.municipio").join()).toContain("SUM(pib) / NULLIF(SUM(populacao), 0)");
    expect(calculosDaTabela("br_x.nao_existe")).toEqual([]);
  });
  test("notas por tabela e por coluna", () => {
    expect(notaColuna("br_ms_sim.microdados", "circunstancia_obito")).toContain("SUBCONTA");
    expect(notaColuna("br_me_caged.microdados_movimentacao", "tipo_movimentacao")).toContain("'97'");
    expect(notaTabela("br_ms_cnes.estabelecimento")).toContain("COUNT(DISTINCT");
    expect(notaColuna("br_ms_sim.microdados", "nao_existe")).toBe("");
  });
  test("a cidade mais fria de 2026-09-24: estação não é município, turma repete aluno", () => {
    expect(notaTabela("br_inmet_bdmep.microdados")).toContain("br_inmet_bdmep.estacao");
    expect(notaColuna("br_inep_censo_escolar.turma", "quantidade_matriculas")).toContain("etapa_ensino");
  });
  test("tabela inventada ganha as reais parecidas", () => {
    expect(sugereTabelas("br_inep.escolas")).toContain("br_inep_censo_escolar.escola");
    expect(sugereTabelas("br_ms_sim.obitos")).toContain("br_ms_sim.microdados");
  });
});
