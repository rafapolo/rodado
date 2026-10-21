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

test("SIAFI do Novo Bolsa Família aponta a junção por nome + UF e a tabela com id_municipio (caso 4 da rodada B2)", () => {
  expect(notaColuna("br_cgu_novo_bolsa_familia.novo_bolsa_familia", "codigo_municipio_siafi")).toContain("strip_accents(nome_municipio)");
  expect(notaTabela("br_cgu_novo_bolsa_familia.novo_bolsa_familia")).toContain("br_cgu_beneficios_cidadao.novo_bolsa_familia");
});

test("HARNESS_ABLA desliga nota, gotcha e alerta sem tocar no resto", async () => {
  const { alertasDeSanidade } = await import("./portao.ts");
  const sql = "SELECT count(*) AS n FROM br_ms_sim.microdados WHERE circunstancia_obito = '2'";
  const antes = Bun.env.HARNESS_ABLA;
  try {
    Bun.env.HARNESS_ABLA = "";
    expect(notaTabela("br_ms_sim.microdados")).toContain("ARMADILHA: Para causa de morte");
    expect(alertasDeSanidade(sql, [{ n: 749 }]).join()).toContain("SUB-PREENCHIDO");
    Bun.env.HARNESS_ABLA = "gotchas:br_ms_sim, nota:br_ms_sim.microdados.circunstancia_obito, alerta:circunstancia_obito";
    expect(notaTabela("br_ms_sim.microdados")).not.toContain("ARMADILHA");
    expect(notaTabela("br_ms_sim.microdados")).toContain("uma linha por óbito");
    expect(notaColuna("br_ms_sim.microdados", "circunstancia_obito")).toBe("");
    expect(notaColuna("br_ms_sim.microdados", "causa_basica")).toContain("X60");
    expect(alertasDeSanidade(sql, [{ n: 749 }]).join()).not.toContain("SUB-PREENCHIDO");
    Bun.env.HARNESS_ABLA = "gotchas";
    expect(notaTabela("br_ms_sim.microdados")).not.toContain("ARMADILHA");
  } finally {
    Bun.env.HARNESS_ABLA = antes;
  }
});
