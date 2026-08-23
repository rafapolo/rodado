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

describe("validarTabelas", () => {
  const T = [{ id: "br_ms_sim.microdados" }, { id: "br_rj_isp_estatisticas_seguranca.evolucao_mensal_uf" }];
  test("pega dataset escrito sem a tabela — o erro que queimava os 2 reparos", () => {
    const r = ask.validarTabelas("SELECT 1 FROM br_rj_isp_estatisticas_seguranca WHERE ano=2000", T);
    expect(r).not.toBeNull();
    expect(r[0].ref).toBe("br_rj_isp_estatisticas_seguranca");
    expect(r[0].sugestao).toContain("br_rj_isp_estatisticas_seguranca.evolucao_mensal_uf");
  });
  test("aceita dataset.tabela correto", () => {
    expect(ask.validarTabelas("SELECT 1 FROM br_ms_sim.microdados", T)).toBeNull();
  });
  test("aceita JOIN entre duas oferecidas", () => {
    expect(ask.validarTabelas(
      "SELECT 1 FROM br_ms_sim.microdados a JOIN br_rj_isp_estatisticas_seguranca.evolucao_mensal_uf b ON a.ano=b.ano", T)).toBeNull();
  });
});

describe("corrigirTabelas — conserto mecânico", () => {
  const T = [{ id: "br_rj_isp_estatisticas_seguranca.evolucao_mensal_uf" },
             { id: "br_rj_isp_estatisticas_seguranca.taxa_evolucao_anual_uf" },
             { id: "br_ms_sim.microdados" }];
  test("troca dataset solto pela tabela mais bem ranqueada dele", () => {
    const r = ask.corrigirTabelas("SELECT 1 FROM br_rj_isp_estatisticas_seguranca WHERE ano=2000", T);
    expect(r).not.toBeNull();
    expect(r.sql).toContain("FROM br_rj_isp_estatisticas_seguranca.evolucao_mensal_uf");
    expect(r.trocas[0]).toContain("→");
  });
  test("não mexe em SQL já correto", () => {
    expect(ask.corrigirTabelas("SELECT 1 FROM br_ms_sim.microdados", T)).toBeNull();
  });
  test("não confunde alias com nome de dataset", () => {
    expect(ask.corrigirTabelas("SELECT 1 FROM br_ms_sim.microdados s JOIN x ON 1=1", T)).toBeNull();
  });
});

describe("resultado vazio não vira 'zero'", () => {
  const vazio = (rows: any[]) => !rows?.length ||
    rows.every((l) => Object.values(l).every((v) => v === null || v === undefined));
  test("SUM(null) não é resposta", () => expect(vazio([{ total: null }])).toBe(true));
  test("nenhuma linha não é resposta", () => expect(vazio([])).toBe(true));
  test("zero de verdade É resposta", () => expect(vazio([{ total: 0 }])).toBe(false));
  test("linha com um nulo entre valores é resposta", () =>
    expect(vazio([{ uf: "RJ", total: null }, { uf: "SP", total: 12 }])).toBe(false));
});
