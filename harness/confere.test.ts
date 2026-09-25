import { describe, expect, test } from "bun:test";
import { semOrigem, valoresVistos, citados } from "./confere.ts";

const vistos = (...t: string[]) => valoresVistos(t);

describe("semOrigem", () => {
  test("o caso 22/43: dígitos girados não conferem", () => {
    expect(semOrigem("O saldo foi de 115.798 postos.", vistos("saldo_total\n115.879"))).toEqual(["115.798"]);
    expect(semOrigem("O saldo foi de 115.798 postos.", vistos("saldo_total | 115879"))).toEqual(["115.798"]);
  });
  test("o mesmo número, em qualquer notação, confere", () => {
    for (const r of ["115.879", "115879", "115 879"]) expect(semOrigem(`saldo de ${r}`, vistos("115.879"))).toEqual([]);
  });
  test("arredondar com escala confere, girar não", () => {
    expect(semOrigem("R$ 328,3 milhões", vistos("328.267.000"))).toEqual([]);
    expect(semOrigem("cerca de 115,9 mil", vistos("115879"))).toEqual([]);
    expect(semOrigem("cerca de 115,8 mil", vistos("115879"))).toEqual(["115,8"]);
  });
  test("coeficiente e porcentagem arredondados, com sinal", () => {
    expect(semOrigem("r = −0,27 (n = 5.570)", vistos("r | n\n-0,2734 | 5.570"))).toEqual([]);
    expect(semOrigem("12,3% dos óbitos", vistos("0.1234"))).toEqual([]);
  });
  test("ano, ranking e potência de 10 ficam de fora", () => {
    expect(semOrigem("Em 2022, os 10 maiores, por 100 mil habitantes", vistos())).toEqual([]);
  });
  test("número da pergunta ou da SQL tem origem", () => {
    expect(semOrigem("acima de 250 leitos", vistos('{"sql":"... WHERE leitos > 250"}'))).toEqual([]);
  });
});

describe("citados", () => {
  test("guarda a precisão escrita", () => {
    expect(citados("R$ 1.234,56 e 2,5 milhões")).toMatchObject([
      { texto: "1.234,56", mantissa: 1234.56, casas: 2, escala: 1 },
      { texto: "2,5", mantissa: 2.5, casas: 1, escala: 1e6 },
    ]);
  });
});
