import { describe, expect, test } from "bun:test";
import { semOrigem, valoresVistos, citados, textosDaConversa, apurado, pedidoDeReescrita } from "./confere.ts";

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

describe("textosDaConversa — B26, o 5.570 do T31-3 vinha do alerta do harness", () => {
  // Resultados reais da sessão do T31-3 na rodada B19 (2026-09-26).
  const alertas = (n: string, r: string) =>
    `⚠ n=${n} passa dos 5.570 municípios do país. Se cada linha deveria ser um município, o join duplicou linhas — ` +
    "uma das pontas tem mais de uma linha por município (por ano, por sexo, por CNAE). Confira com COUNT(DISTINCT " +
    "id_municipio) e agregue a ponta duplicada antes do join. Se o grão é município × ano de propósito, está certo: " +
    "diga o grão na resposta.\n" +
    `⚠ Se este resultado sustenta a resposta, escreva nela o coeficiente como número, com duas casas (r=${r}) e o n — ` +
    `quantos municípios entraram na medida (aqui, n=${n}). "Correlação fraca" sem o número, ou conclusão sem o ` +
    "tamanho da amostra, não dá para conferir.\n\n" +
    "1 linha(s) (números em pt-BR: ponto separa milhar, vírgula separa decimal — copie como estão):\n";
  const R1 = alertas("15212", "-0.04034249753977142") + "r | n\n-0,04034249753977142 | 15.212";
  const R2 = alertas("7102", "-0.04577822423494077") + "r | n\n-0,04577822423494077 | 7102";
  const RESPOSTA = "O coeficiente de correlação de Pearson obtido foi de **r = -0,05** (n = 5.570 municípios), " +
    "o que indica uma **correlação desprezível/fraca**.";
  const conversa = [
    { role: "system", content: "persona com 5.570 municípios" },
    { role: "user", content: "A vulnerabilidade social (Censo + AVS) explica quanto da variação da mortalidade infantil implícita no par SIM×SINASC por município?" },
    { role: "assistant", content: "Vou juntar os 5.570 municípios.", tool_calls: [{ id: "a", function: { name: "consultar", arguments: '{"sql":"SELECT corr(x, y) AS r, COUNT(*) AS n FROM t"}' } }] },
    { role: "tool", tool_call_id: "a", content: R1 },
    { role: "assistant", content: null, tool_calls: [{ id: "b", function: { name: "descrever_tabela", arguments: '{"tabela":"br_ipea_avs.municipio"}' } }] },
    { role: "tool", tool_call_id: "b", content: "NOTA: cobre os 5.570 municípios" },
    { role: "assistant", content: null, tool_calls: [{ id: "c", function: { name: "consultar", arguments: '{"sql":"SELECT corr(x, y) AS r, COUNT(*) AS n FROM u"}' } }] },
    { role: "tool", tool_call_id: "c", content: R2 },
  ];
  const vistosEm = (c: typeof conversa) => valoresVistos(textosDaConversa(c));

  test("o n que só o alerta, o catálogo e a prosa do modelo diziam fica sem origem; o r arredondado confere", () => {
    expect(semOrigem(RESPOSTA, vistosEm(conversa))).toEqual(["5.570"]);
  });
  test("o n que a consulta devolveu confere", () => {
    expect(semOrigem("r = -0,05 (n = 7.102 municípios)", vistosEm(conversa))).toEqual([]);
  });
  test("apurado: do cabeçalho em diante; erro e alertas saem", () => {
    expect(apurado(R2)).toStartWith("1 linha(s)");
    expect(apurado("⚠ grupo\n\n5565 linhas, mostrando 200:\nid\n1")).toStartWith("5565 linhas");
    expect(apurado("Error: Faixa de anos: 2000–2010.")).toBe("");
    expect(apurado("⏱ PRAZO: 18 min\nsaldo | 115879")).toBe("saldo | 115879");
  });
  test("o pedido de reescrita da guarda não vira origem do número que ele cita", () => {
    const c = [...conversa, { role: "assistant", content: RESPOSTA }, { role: "user", content: pedidoDeReescrita(["5.570"]) }];
    expect(semOrigem(RESPOSTA, vistosEm(c as typeof conversa))).toEqual(["5.570"]);
  });
});
