import { expect, test, describe } from "bun:test";
import { resolverJuncao, semColunaComum, conceitoDaColuna } from "./pontes.ts";
import { colunasDe } from "./catalogo.ts";

// Casos reais do catálogo, não sintéticos — resolverJuncao lê bridges.yaml de
// verdade, e o que importa validar é que ele acha o MESMO par que
// mcp_server.py.resolve_join acharia para as mesmas duas tabelas.

describe("resolverJuncao", () => {
  test("ponte curada substitui a igualdade ingênua", () => {
    const a = "br_tesouro_capag.municipios";
    const b = "br_bd_diretorios_brasil.municipio";
    const colsA = colunasDe(a)!.map((c) => c.name);
    const colsB = colunasDe(b)!.map((c) => c.name);
    const r = resolverJuncao(a, colsA, b, colsB);
    expect(r.joins.length).toBeGreaterThan(0);
    const ponte = r.joins.find((j) => j.kind === "bridge");
    expect(ponte).toBeDefined();
    expect(ponte!.on).toContain("Código Município Completo");
    expect(ponte!.on).toContain("b.id_municipio");
    expect(ponte!.verified).toBeDefined();
  });

  test("chave canônica direta quando não há ponte curada", () => {
    const a = "br_me_caged.microdados_movimentacao";
    const b = "br_me_rais.microdados_vinculos";
    const colsA = colunasDe(a)!.map((c) => c.name);
    const colsB = colunasDe(b)!.map((c) => c.name);
    const r = resolverJuncao(a, colsA, b, colsB);
    const direta = r.joins.find((j) => j.concept === "id_municipio" && j.kind === "direct");
    expect(direta).toBeDefined();
    expect(direta!.on).toBe("a.id_municipio = b.id_municipio");
  });

  test("sem junção documentada avisa em vez de inventar", () => {
    const r = resolverJuncao("x.a", ["nome", "endereco"], "y.b", ["nome", "telefone"]);
    expect(r.joins.length).toBe(0);
    expect(r.avisos.length).toBeGreaterThan(0);
  });

  test("false_friend rejeita em vez de casar por nome igual", () => {
    // cnpj_favorecido_empenho é false_friend documentado em bridges.yaml —
    // duas tabelas sintéticas com essa coluna em comum não devem juntar por ela.
    const r = resolverJuncao("x.a", ["cnpj_favorecido_empenho"], "y.b", ["cnpj_favorecido_empenho"]);
    expect(r.joins.find((j) => j.concept === "cnpj_favorecido_empenho")).toBeUndefined();
    expect(r.rejeitados.length).toBe(1);
    expect(r.rejeitados[0]!.motivo.length).toBeGreaterThan(0);
  });

  test("consistente com conceitoDaColuna / semColunaComum já testados", () => {
    // As duas funções leem a mesma bridges.yaml — não podem discordar sobre se
    // duas tabelas têm ou não conceito em comum.
    const a = "br_me_caged.microdados_movimentacao", b = "br_me_rais.microdados_vinculos";
    const colsA = colunasDe(a)!.map((c) => c.name), colsB = colunasDe(b)!.map((c) => c.name);
    const semComum = semColunaComum(a, colsA, b, colsB);
    const r = resolverJuncao(a, colsA, b, colsB);
    expect(semComum).toBe(false);
    expect(r.joins.length).toBeGreaterThan(0);
    void conceitoDaColuna;
  });
});
