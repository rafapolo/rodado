import { describe, expect, test } from "bun:test";
import { fontesDaPergunta } from "./fontes.ts";

describe("fontesDaPergunta", () => {
  test("sigla no nome do dataset (T07-1: SICOR nunca aberto)", () => {
    const f = fontesDaPergunta("Municípios que mais captam crédito rural (SICOR) são os de maior PIB agropecuário (IBGE)?");
    expect(f).toContain("SICOR → br_bcb_sicor");
    expect(f).not.toContain("IBGE");
  });

  test("coluna entre crases e sigla fora do nome (T81-2: hhi_smp 'não consta')", () => {
    const f = fontesDaPergunta("O sub-índice de mercado móvel do IBC (`hhi_smp`) é pior onde a cobertura do Bolsa Família é maior?");
    expect(f).toContain("IBC → br_anatel_indice_brasileiro_conectividade");
    expect(f).toContain("coluna hhi_smp → br_anatel_indice_brasileiro_conectividade.municipio");
  });

  test("segmento inteiro: SIM não casa br_simet_…", () => {
    const f = fontesDaPergunta("Óbitos por agressão no SIM");
    expect(f).toContain("SIM → br_ms_sim");
    expect(f).not.toContain("simet");
  });

  test("sigla de UF e tabela de trabalho ficam fora; ISP-RJ resolve pelo ISP", () => {
    const f = fontesDaPergunta("No RJ, a queda dos crimes letais do ISP-RJ espelha a dos óbitos (RAIS)?");
    expect(f).toContain("ISP-RJ → br_rj_isp_estatisticas_seguranca");
    expect(f).not.toMatch(/^\s+RJ →/m);
    expect(f).not.toContain("_local_");
  });

  test("pergunta sem fonte nomeada não ganha pista", () => {
    expect(fontesDaPergunta("Quantos municípios tem o Brasil?")).toBe("");
    expect(fontesDaPergunta("")).toBe("");
  });
});
