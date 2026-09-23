import { describe, expect, test } from "bun:test";
import { recortes, faltando } from "./recortes.ts";

describe("recortes", () => {
  test("o caso medido: bioma esquecido na SQL", () => {
    const q = "Quantos km² de desmatamento o PRODES registrou no bioma Amazônia no ano de 2021?";
    const sql = "SELECT sum(desmatado) FROM br_inpe_prodes.municipio_bioma WHERE ano IN (2020, 2021)";
    expect(faltando(q, [sql]).map((r) => r.rotulo)).toEqual(["bioma Amazônia"]);
    expect(faltando(q, [sql + " AND bioma = 'Amazônia'"])).toEqual([]);
  });
  test("estado por sigla ou nome; o mais longo primeiro", () => {
    expect(recortes("saldo do Mato Grosso do Sul em 2022").map((r) => r.rotulo)).toEqual(["2022", "Mato Grosso do Sul"]);
    expect(faltando("escolas no Ceará em 2022", ["... WHERE ano = 2022 AND sigla_uf = 'CE'"])).toEqual([]);
    expect(faltando("escolas no Ceará em 2022", ["... WHERE ano = 2022"]).map((r) => r.rotulo)).toEqual(["Ceará"]);
  });
  test("'para' preposição não é o Pará; o Pará acentuado é", () => {
    expect(recortes("Qual o valor para o Brasil em 2020?").map((r) => r.rotulo)).toEqual(["2020"]);
    expect(recortes("Quantos focos no Pará em 2020?").map((r) => r.rotulo)).toContain("Pará");
  });
  test("município de São Paulo não exige o estado", () => {
    expect(recortes("Quantos óbitos de residentes do município de São Paulo em 2019?").map((r) => r.rotulo)).toEqual(["2019"]);
  });
  test("ano coberto por faixa na SQL", () => {
    expect(faltando("quantos em 2021?", ["WHERE ano BETWEEN 2019 AND 2022"])).toEqual([]);
  });
});
