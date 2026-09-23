import { describe, expect, test } from "bun:test";
import { descreve, tabelaTexto, dicaMunicipio } from "./formato.ts";
import { colunasDe } from "./catalogo.ts";

describe("descreve", () => {
  test("código decodificado ao lado da coluna", () => {
    const t = descreve("br_inep_censo_escolar.escola", colunasDe("br_inep_censo_escolar.escola")!);
    expect(t).toContain("tipo_localizacao: str — códigos: '1'=Urbana, '2'=Rural");
    expect(t).toContain("tipo_situacao_funcionamento: str — códigos: '1'=Em atividade");
    expect(t).toContain("filtre por partição: ano, sigla_uf");
  });
  test("tabela estreita fica uma coluna por linha", () => {
    const t = descreve("x.y", [{ name: "ano", type: "INTEGER" }, { name: "valor", type: "FLOAT" }]);
    expect(t).toBe("x.y — 2 colunas · filtre por partição: ano\n  ano: int\n  valor: float");
  });
});

describe("tabelaTexto", () => {
  test("cabeçalho uma vez", () => {
    expect(tabelaTexto({ rows: [{ uf: "RJ", n: 789 }, { uf: "SP", n: null }], truncated: false }))
      .toBe("2 linha(s):\nuf | n\nRJ | 789\nSP | NULL");
  });
  test("avisa quando cortou", () => {
    expect(tabelaTexto({ rows: [{ a: 1 }], truncated: true, total: 500 })).toStartWith("500 linhas, mostrando 1:");
  });
});

describe("dicaMunicipio", () => {
  test("código sem nome ganha a dica", () => {
    expect(dicaMunicipio([{ id_municipio: "3550308", saldo: 136109 }])).toContain("br_bd_diretorios_brasil.municipio");
  });
  test("com nome, cala", () => {
    expect(dicaMunicipio([{ id_municipio: "3550308", nome: "São Paulo" }])).toBe("");
  });
});

describe("descreve com filtro e grupos", () => {
  const t = "br_inep_censo_escolar.escola";
  test("tabela larga resume por prefixo e ensina o filtro", () => {
    const d = descreve(t, colunasDe(t)!);
    expect(d).toContain("quantidade_matricula_* (");
    expect(d).toContain('filtro="');
    expect(d.length).toBeLessThan(6000);
  });
  test("filtro lista o grupo inteiro", () => {
    const cols = colunasDe(t)!;
    const d = descreve(t, cols, "", "matricula_fundamental");
    for (const c of cols.filter((c) => c.name.includes("matricula_fundamental"))) expect(d).toContain(`  ${c.name}:`);
    // o filtro soma, não esconde: a coluna codificada continua visível
    expect(d).toContain("tipo_localizacao: str — códigos: '1'=Urbana, '2'=Rural");
  });
});

describe("códigos só das colunas ligadas à pergunta", () => {
  const sim = "br_ms_sim.microdados";
  test("tabela com muitas codificadas encolhe e mantém a coluna da pergunta", () => {
    const d = descreve(sim, colunasDe(sim)!, "", "", "Quantos óbitos por suicídio houve no RJ em 2020?");
    expect(d.length).toBeLessThan(descreve(sim, colunasDe(sim)!).length * 0.7);
    expect(d).toContain("causa_basica: str — NOTA");
    expect(d).toContain("(N códigos)");
  });
  test("rótulo casa com a pergunta: 'rurais' abre tipo_localizacao", () => {
    const t = "br_inep_censo_escolar.escola";
    expect(descreve(t, colunasDe(t)!, "", "", "Quantas escolas rurais havia na Bahia?")).toContain("'2'=Rural");
  });
  test("lista curta (até 5 códigos) fica sempre inteira", () => {
    const t = "br_inep_censo_escolar.escola";
    expect(descreve(t, colunasDe(t)!, "", "", "Quantas escolas havia no Ceará em 2022?")).toContain("rede: str — códigos:");
  });
  test("sem pergunta, nada muda", () => {
    expect(descreve(sim, colunasDe(sim)!)).not.toContain("(N códigos)");
  });
});
