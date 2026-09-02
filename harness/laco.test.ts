/**
 * Item 3 do backlog: a metade que falta virar teste — a checagem que rejeita
 * (e, se a reescrita ainda falhar, apaga) citação de tabela na prosa final.
 * A instrução no prompt (etapa 9 de `roda()`) já existia; sem isto ela só
 * funcionava "na maioria das vezes".
 */
import { expect, test, describe } from "bun:test";
import { checaProsa, saneiaProsa } from "./laco.ts";

describe("checaProsa", () => {
  test("acusa nome de tabela do espelho na prosa", () => {
    const erro = checaProsa("Segundo br_ibge_pib.municipio, o PIB per capita foi de R$ 34.521.");
    expect(erro).toBeDefined();
    expect(erro).toContain("br_ibge_pib.municipio");
    expect(erro).toContain("ÓRGÃO");
  });

  test("prosa citando o órgão, não a tabela, passa", () => {
    expect(checaProsa("Segundo o IBGE, o PIB per capita de São Paulo foi de R$ 34.521 em 2022.")).toBeUndefined();
  });

  test("não confunde CID ou outra sigla com nome de tabela", () => {
    // nada com "br_" seguido de ponto — X60/X84, siglas soltas não acusam
    expect(checaProsa("A causa foi X60-X84, conforme o SIM do Ministério da Saúde.")).toBeUndefined();
  });

  test("pega qualquer tabela do espelho, não só ibge", () => {
    expect(checaProsa("O dado vem de br_ms_sim.microdados.")).toContain("br_ms_sim.microdados");
  });
});

describe("saneiaProsa — rede de segurança depois da reescrita falhar", () => {
  test("texto limpo não é tocado", () => {
    const r = saneiaProsa("Segundo o IBGE, foram 4.251 municípios.");
    expect(r.saneada).toBe(false);
    expect(r.texto).toBe("Segundo o IBGE, foram 4.251 municípios.");
  });

  test("apaga a citação em vez de publicar a tabela", () => {
    const r = saneiaProsa("Segundo br_ibge_pib.municipio, o PIB foi X.");
    expect(r.saneada).toBe(true);
    expect(r.texto).not.toContain("br_ibge_pib");
    expect(r.texto).toContain("a fonte do espelho");
  });

  test("apaga TODAS as ocorrências, não só a primeira", () => {
    const r = saneiaProsa("br_ms_sim.microdados e br_ms_sinasc.microdados foram cruzados.");
    expect(r.texto).not.toContain("br_ms_sim");
    expect(r.texto).not.toContain("br_ms_sinasc");
  });
});
