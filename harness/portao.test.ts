/**
 * Os casos deste arquivo não são hipotéticos: cada um é uma SQL que o Gemma 4
 * escreveu de verdade no beelink em 2026-09-01, ou um erro que o pipeline do
 * ask-web apanhou em produção. O portão existe por causa deles.
 */
import { expect, test, describe } from "bun:test";
import { portao } from "./portao.ts";

describe("camada read-only (sqlguard)", () => {
  test("rejeita escrita", () => {
    expect(portao("DELETE FROM br_ms_sim.microdados").ok).toBe(false);
  });
  test("rejeita statement múltiplo", () => {
    const v = portao("SELECT 1; SELECT 2");
    expect(v.ok).toBe(false);
    expect(v.camada).toBe("read-only");
  });
});

describe("camada partição — o lock de 2h", () => {
  test("REJEITA o COUNT(*) que o Gemma gerou de primeira", () => {
    const v = portao("SELECT COUNT(*) FROM br_ms_sim.microdados");
    expect(v.ok).toBe(false);
    expect(v.camada).toBe("particao");
    expect(v.erro).toContain("ano");
  });
  test("aceita a mesma consulta com filtro de partição", () => {
    const v = portao("SELECT COUNT(*) FROM br_ms_sim.microdados WHERE ano = 2020");
    expect(v.ok).toBe(true);
  });
  test("tabela pequena não exige partição", () => {
    const v = portao("SELECT COUNT(*) FROM br_bcb_sgs.serie_temporal");
    expect(v.camada).not.toBe("particao");
  });
});

describe("camada codificação — o erro de 8% que passa plausível", () => {
  test("REJEITA a faixa de CID sobre a coluna crua (726 vs 789 reais)", () => {
    const v = portao(
      "SELECT sexo, COUNT(*) FROM br_ms_sim.microdados " +
      "WHERE ano = 2020 AND sigla_uf = 'RJ' " +
      "AND causa_basica BETWEEN 'X60' AND 'X84' GROUP BY sexo",
    );
    expect(v.ok).toBe(false);
    expect(v.camada).toBe("codificacao");
    expect(v.erro).toContain("substr");
  });
  test("aceita a forma correta com substr", () => {
    const v = portao(
      "SELECT COUNT(*) FROM br_ms_sim.microdados " +
      "WHERE ano = 2020 AND sigla_uf = 'RJ' " +
      "AND substr(causa_basica,1,3) BETWEEN 'X60' AND 'X84'",
    );
    expect(v.ok).toBe(true);
  });
});

describe("camada tabela — o erro mais caro de modelo pequeno", () => {
  test("rejeita FROM dataset sem a tabela", () => {
    const v = portao("SELECT COUNT(*) FROM br_ms_sim WHERE ano = 2020");
    expect(v.ok).toBe(false);
    expect(v.camada).toBe("tabela");
  });
  test("rejeita tabela inexistente", () => {
    const v = portao("SELECT COUNT(*) FROM br_ms_sim.nao_existe WHERE ano = 2020");
    expect(v.ok).toBe(false);
    expect(v.camada).toBe("tabela");
  });
});

describe("camada coluna", () => {
  test("rejeita coluna inventada", () => {
    const v = portao(
      "SELECT m.coluna_inventada FROM br_ms_sim.microdados m WHERE m.ano = 2020 LIMIT 10",
    );
    expect(v.ok).toBe(false);
    expect(v.camada).toBe("coluna");
  });
});

describe("camada limite", () => {
  test("exige LIMIT em consulta não agregada", () => {
    const v = portao("SELECT causa_basica FROM br_ms_sim.microdados WHERE ano = 2020");
    expect(v.ok).toBe(false);
    expect(v.camada).toBe("limite");
  });
  test("agregação dispensa LIMIT", () => {
    expect(portao("SELECT COUNT(*) FROM br_ms_sim.microdados WHERE ano = 2020").ok).toBe(true);
  });
});

describe("CTE — o caso multi-dataset, que é o que importa", () => {
  const sql = `WITH caged AS (
      SELECT id_municipio, SUM(saldo_movimentacao) AS saldo
      FROM br_me_caged.microdados_movimentacao WHERE ano = 2020 GROUP BY id_municipio
    ), pib AS (
      SELECT id_municipio, pib FROM br_ibge_pib.municipio WHERE ano = 2020
    )
    SELECT COUNT(*) FROM caged JOIN pib ON caged.id_municipio = pib.id_municipio`;

  test("não confunde nome de CTE com tabela inexistente", () => {
    const v = portao(sql);
    expect(v.camada).not.toBe("tabela");
  });
  test("a consulta multi-dataset inteira passa", () => {
    expect(portao(sql).ok).toBe(true);
  });
  test("coluna criada com AS não é acusada de inexistente", () => {
    const v = portao(
      `WITH t AS (SELECT id_municipio, COUNT(*) AS total
         FROM br_ms_sim.microdados WHERE ano = 2020 GROUP BY id_municipio)
       SELECT AVG(t.total) FROM t`,
    );
    expect(v.ok).toBe(true);
  });
  test("ainda pega tabela de verdade inexistente dentro de CTE", () => {
    const v = portao(
      `WITH t AS (SELECT * FROM br_ms_sim.nao_existe WHERE ano = 2020 LIMIT 5) SELECT * FROM t LIMIT 5`,
    );
    expect(v.ok).toBe(false);
    expect(v.camada).toBe("tabela");
  });
});

describe("camada inservível — a tabela que responde zero e parece certa", () => {
  // Os dois casos que motivaram esta camada — br_ibama_embargos (497 mil linhas
  // de string vazia) e br_seeg (redundante) — foram REMOVIDOS do espelho em
  // 2026-09-02, depois que o levantamento os expôs. Hoje eles caem na camada
  // `tabela`, que é o desfecho melhor: some do catálogo em vez de precisar ser
  // desviado. A camada continua valendo para o que ainda existe e para o
  // próximo caso do gênero.
  test("REJEITA tabela vazia (0 linhas)", () => {
    const v = portao("SELECT COUNT(*) FROM br_bd_diretorios_brasil.empresa");
    expect(v.ok).toBe(false);
    expect(v.camada).toBe("inservivel");
    expect(v.erro).toContain("vazia");
  });
  test("os datasets aposentados já não estão no catálogo, e caem antes", () => {
    for (const sql of [
      "SELECT COUNT(*) FROM br_ibama_embargos.termo_embargo WHERE ano = 2020",
      "SELECT COUNT(*) FROM br_seeg.emissoes_municipais WHERE ano = 2020",
    ]) {
      const v = portao(sql);
      expect(v.ok).toBe(false);
      expect(v.camada).toBe("tabela");
    }
  });
  test("aceita as que os substituíram", () => {
    expect(portao("SELECT COUNT(*) FROM br_ibama_embargos_novo.termo_embargo").ok).toBe(true);
  });
  test("não bloqueia o diretório canônico de municípios", () => {
    const v = portao("SELECT COUNT(*) FROM br_bd_diretorios_brasil.municipio");
    expect(v.camada).not.toBe("inservivel");
  });
});
