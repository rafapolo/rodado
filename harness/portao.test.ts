/**
 * Os casos deste arquivo não são hipotéticos: cada um é uma SQL que o Gemma 4
 * escreveu de verdade no beelink em 2026-09-01, ou um erro que o pipeline do
 * ask-web apanhou em produção. O portão existe por causa deles.
 */
import { expect, test, describe } from "bun:test";
import {
  portao, alertasDeSanidade,
  juncoesSemPonte, mensagemSemPonte, assinaturaJuncao,
  perguntaDePesquisa, checaRanking,
} from "./portao.ts";

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
    // AVG exige `n` (camada 8) — junto para não testar duas coisas com o
    // mesmo SQL e cair na rejeição errada.
    const v = portao(
      `WITH t AS (SELECT id_municipio, COUNT(*) AS total
         FROM br_ms_sim.microdados WHERE ano = 2020 GROUP BY id_municipio)
       SELECT AVG(t.total) AS media, COUNT(*) AS n FROM t`,
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

describe("camada ano — o filtro cai fora da faixa real da tabela", () => {
  // O caso medido em 2026-09-01: CAGED × RAIS × PIB com chave e LPAD certos,
  // filtrado ano = 2022. br_ibge_pib.municipio termina em 2021, o join deu
  // zero e o zero passou por resposta. harness_tasks.md B6.
  test("ano = 2022 rejeita br_ibge_pib.municipio, que termina em 2021", () => {
    const v = portao(
      "SELECT sigla_uf, SUM(pib) AS n FROM br_ibge_pib.municipio WHERE ano = 2022 GROUP BY sigla_uf",
    );
    expect(v.ok).toBe(false);
    expect(v.camada).toBe("ano");
    expect(v.erro).toContain("2021");
  });
  test("ano dentro da faixa passa", () => {
    const v = portao(
      "SELECT sigla_uf, SUM(pib) AS n FROM br_ibge_pib.municipio WHERE ano = 2020 GROUP BY sigla_uf",
    );
    expect(v.camada).not.toBe("ano");
  });
  test("predicado cru com mais de uma tabela candidata não chuta — se cala de propósito", () => {
    const v = portao(
      `SELECT c.sigla_uf, SUM(c.saldo) AS n
       FROM br_me_caged.microdados_movimentacao c
       JOIN br_ibge_pib.municipio p ON c.id_municipio = p.id_municipio
       WHERE ano = 2022 GROUP BY c.sigla_uf`,
    );
    expect(v.camada).not.toBe("ano");
  });
});

describe("camada amostra — estatística derivada sem COUNT(*) AS n", () => {
  // harness_tasks.md R1: a regra existia só no laco.ts (pipeline aposentado).
  // No laço agêntico o número vem da prosa do modelo, e foi assim que "573 em
  // vez de 789" (um grupo do GROUP BY lido como total) entrou na Rodada 6.
  test("AVG sem n é rejeitado", () => {
    const v = portao(
      "SELECT AVG(pib) AS media FROM br_ibge_pib.municipio WHERE ano = 2020",
    );
    expect(v.ok).toBe(false);
    expect(v.camada).toBe("amostra");
    expect(v.erro).toContain("COUNT(*) AS n");
  });
  test("AVG com COUNT(*) AS n passa", () => {
    const v = portao(
      "SELECT AVG(pib) AS media, COUNT(*) AS n FROM br_ibge_pib.municipio WHERE ano = 2020",
    );
    expect(v.camada).not.toBe("amostra");
  });
  test("CORR sem n é rejeitado — o caso de corr=0,97 sobre poucos pares", () => {
    // LIMIT 1 satisfaz a camada 5 (limite) antes de chegar na 8 — CORR não é
    // reconhecida como agregação por aquela camada, e não é o que este teste mede.
    const v = portao(
      "SELECT corr(a, b) AS corr FROM br_ibge_pib.municipio WHERE ano = 2020 LIMIT 1",
    );
    expect(v.camada).toBe("amostra");
  });
  test("SUM/COUNT puros não exigem n — não são estatística derivada", () => {
    const v = portao(
      "SELECT sigla_uf, SUM(pib) AS total FROM br_ibge_pib.municipio WHERE ano = 2020 GROUP BY sigla_uf",
    );
    expect(v.camada).not.toBe("amostra");
  });
});

describe("alertasDeSanidade — circunstancia_obito subconta suicídio (backlog item 9)", () => {
  // Medido ao vivo em 2026-09-03: circunstancia_obito='2' deu 749 contra 789
  // de causa_basica/CID no mesmo recorte (RJ, 2020) — achado testando o item 3.
  test("avisa quando circunstancia_obito classifica causa sem causa_basica junto", () => {
    const alertas = alertasDeSanidade(
      "SELECT COUNT(*) AS n FROM br_ms_sim.microdados WHERE sigla_uf='RJ' AND ano=2020 AND circunstancia_obito='2'",
      [{ n: 749 }],
    );
    expect(alertas.some((a) => a.includes("circunstancia_obito"))).toBe(true);
    expect(alertas.some((a) => a.includes("749"))).toBe(true);
  });
  test("não avisa quando causa_basica também está na consulta", () => {
    const alertas = alertasDeSanidade(
      "SELECT COUNT(*) AS n FROM br_ms_sim.microdados " +
      "WHERE sigla_uf='RJ' AND ano=2020 AND (circunstancia_obito='2' OR substr(causa_basica,1,3) BETWEEN 'X60' AND 'X84')",
      [{ n: 789 }],
    );
    expect(alertas.some((a) => a.includes("circunstancia_obito"))).toBe(false);
  });
  test("não avisa quando a consulta não toca circunstancia_obito", () => {
    const alertas = alertasDeSanidade(
      "SELECT COUNT(*) AS n FROM br_ms_sim.microdados WHERE sigla_uf='RJ' AND ano=2020",
      [{ n: 12345 }],
    );
    expect(alertas).toEqual([]);
  });
});

describe("juncoesSemPonte — harness_tasks.md B12, a pergunta de 5 fontes que morreu presa", () => {
  // O caso real: 38 das 55 SQLs de uma sessão de 40 min tentaram
  // `id_emenda = id_licitacao` entre estas duas tabelas. Elas não compartilham
  // coluna nenhuma (conferido no beelink) e bridges.yaml não documenta a
  // relação — não existia ponte pra achar, e o portão não tinha como avisar.
  const semChaveNenhuma =
    "SELECT l.id_emenda, p.cpf_cnpj_vencedor FROM br_cgu_emendas_parlamentares.microdados l " +
    "JOIN br_cgu_licitacao_contrato.licitacao_item p ON l.id_emenda = p.id_licitacao " +
    "WHERE p.ano = 2022 LIMIT 5";

  test("acusa a junção sem ponte nem chave canônica em comum", () => {
    const achados = juncoesSemPonte(semChaveNenhuma);
    expect(achados.length).toBe(1);
    expect(achados[0]!.refA).toBe("br_cgu_emendas_parlamentares.microdados");
    expect(achados[0]!.refB).toBe("br_cgu_licitacao_contrato.licitacao_item");
  });

  test("a mensagem nomeia as duas colunas e diz que a ponte não é conhecida", () => {
    const msg = mensagemSemPonte(juncoesSemPonte(semChaveNenhuma));
    expect(msg).toContain("id_emenda");
    expect(msg).toContain("id_licitacao");
    expect(msg).toContain("Nenhuma ponte conhecida");
  });

  test("não acusa junção por chave canônica (id_municipio dos dois lados)", () => {
    const sql =
      "SELECT c.sigla_uf, SUM(c.saldo_movimentacao) AS n " +
      "FROM br_me_caged.microdados_movimentacao c " +
      "JOIN br_ibge_pib.municipio p ON c.id_municipio = p.id_municipio " +
      "WHERE c.ano = 2020 AND p.ano = 2020 GROUP BY c.sigla_uf";
    expect(juncoesSemPonte(sql)).toEqual([]);
  });

  test("não acusa junção dentro do mesmo dataset (sem risco de par sem lastro)", () => {
    const sql =
      "SELECT l.objeto, i.valor_item FROM br_cgu_licitacao_contrato.licitacao l " +
      "JOIN br_cgu_licitacao_contrato.licitacao_item i ON l.id_licitacao = i.id_licitacao " +
      "WHERE l.ano = 2023 LIMIT 5";
    expect(juncoesSemPonte(sql)).toEqual([]);
  });

  test("reconhece a ponte curada de emendas → município (id_municipio_gasto)", () => {
    // bridges.yaml documenta id_municipio_gasto como concept id_municipio —
    // mesmo com nomes diferentes dos dois lados, isto TEM ponte.
    const sql =
      "SELECT e.id_municipio_gasto, m.nome FROM br_cgu_emendas_parlamentares.microdados e " +
      "JOIN br_bd_diretorios_brasil.municipio m ON e.id_municipio_gasto = m.id_municipio LIMIT 5";
    expect(juncoesSemPonte(sql)).toEqual([]);
  });
});

describe("assinaturaJuncao — detecta a mesma junção repetida com cosmético diferente", () => {
  test("duas consultas com WHERE/LIMIT diferentes, mesmo FROM/JOIN/ON, têm a mesma assinatura", () => {
    const a =
      "SELECT l.id_emenda, p.cpf_cnpj_vencedor FROM br_cgu_emendas_parlamentares.microdados l " +
      "JOIN br_cgu_licitacao_contrato.licitacao_item p ON l.id_emenda = p.id_licitacao " +
      "WHERE p.ano = 2022 LIMIT 5";
    const b =
      "SELECT l.id_emenda, l.valor_liquidado, p.nome_vencedor FROM br_cgu_emendas_parlamentares.microdados l " +
      "JOIN br_cgu_licitacao_contrato.licitacao_item p ON l.id_emenda = p.id_licitacao " +
      "WHERE l.id_emenda = '201535780008' LIMIT 100";
    expect(assinaturaJuncao(a)).toBe(assinaturaJuncao(b));
  });

  test("uma junção genuinamente diferente tem assinatura diferente", () => {
    const a = "SELECT COUNT(*) AS n FROM br_ms_sim.microdados WHERE ano = 2020";
    const b = "SELECT COUNT(*) AS n FROM br_ms_sinasc.microdados WHERE ano = 2020";
    expect(assinaturaJuncao(a)).not.toBe(assinaturaJuncao(b));
  });
});

describe("camada inservível — a tabela que responde zero e parece certa", () => {
  // Os dois casos que motivaram esta camada — br_ibama_embargos (497 mil linhas
  // de string vazia) e br_seeg (redundante) — foram REMOVIDOS do espelho em
  // 2026-09-02, depois que o levantamento os expôs. `aposentados()` (catalogo.ts)
  // varre TODAS as `provenance_notes` por `Substitui \`X\`` e intercepta X pelo
  // NOME, mesmo já fora do catálogo — desfecho melhor que "tabela não existe"
  // (camada `tabela`): a mensagem explica O QUE substituiu e por quê, em vez de
  // just "não achei". Mesmo mecanismo da varredura de harness_tasks.md O5.
  test("REJEITA tabela vazia (0 linhas)", () => {
    const v = portao("SELECT COUNT(*) FROM br_bd_diretorios_brasil.empresa");
    expect(v.ok).toBe(false);
    expect(v.camada).toBe("inservivel");
    expect(v.erro).toContain("vazia");
  });
  test("br_ibama_embargos é interceptado pelo nome, com o motivo", () => {
    // aposentados() acha isto porque br_ibama_embargos_novo tem
    // "Substitui `br_ibama_embargos`" em provenance_notes — a nota existe.
    const v = portao("SELECT COUNT(*) FROM br_ibama_embargos.termo_embargo WHERE ano = 2020");
    expect(v.ok).toBe(false);
    expect(v.camada).toBe("inservivel");
    expect(v.erro).toContain("aposentada");
  });
  // br_seeg NÃO tem teste equivalente aqui, de propósito, e é um achado, não
  // um esquecimento: nenhuma provenance_notes no espelho diz "Substitui
  // `br_seeg`" (confirmado 2026-09-03, varredura de harness_tasks.md O5), então
  // aposentados() não tem como saber que ele foi removido. Pior: colunasDe()
  // lê de docs/context/rodado-schema.json (gerado por scripts/gera_schemas.py,
  // fora do escopo do harness), que não foi regenerado desde a remoção — então
  // br_seeg.emissoes_municipais ainda PASSA o portão (camadas tabela/coluna
  // acham a referência válida), mesmo com harness/dados/catalogo.json (fonte
  // viva, via `catalogo.ts --atualiza`) confirmando que o dataset não existe
  // mais. Não é um bug do portão — é uma dependência de arquivo desatualizado
  // fora do escopo deste subsistema. Fecha só regenerando rodado-schema.json.
  test("aceita as que os substituíram", () => {
    expect(portao("SELECT COUNT(*) FROM br_ibama_embargos_novo.termo_embargo").ok).toBe(true);
  });
  test("não bloqueia o diretório canônico de municípios", () => {
    const v = portao("SELECT COUNT(*) FROM br_bd_diretorios_brasil.municipio");
    expect(v.camada).not.toBe("inservivel");
  });
});

describe("média sobre unidade menor com tabela agregada no dataset", () => {
  test("AVG em ideb.escola aponta ideb.brasil e .uf", () => {
    const a = alertasDeSanidade("SELECT AVG(ideb) AS m, COUNT(*) AS n FROM br_inep_ideb.escola WHERE ano = 2019", [{ m: 4.15, n: 18728 }]);
    expect(a.join()).toContain("br_inep_ideb.brasil");
  });
  test("ler a tabela agregada não alerta", () => {
    const a = alertasDeSanidade("SELECT ideb FROM br_inep_ideb.brasil WHERE ano = 2019 LIMIT 5", [{ ideb: 3.9 }]);
    expect(a.join()).not.toContain("tabela já agregada");
  });
  test("sem AVG não alerta", () => {
    const a = alertasDeSanidade("SELECT COUNT(*) AS n FROM br_inep_ideb.escola WHERE ano = 2019", [{ n: 10 }]);
    expect(a.join()).not.toContain("tabela já agregada");
  });
});

describe("fan-out: denominador somado por linha de microdado", () => {
  test("o caso medido: SIM × população municipal com SUM(p.populacao)", () => {
    const sql = `SELECT u.sigla_uf, COUNT(m.causa_basica) * 100000.0 / SUM(p.populacao) AS taxa
      FROM br_ms_sim.microdados m
      JOIN br_ibge_populacao.municipio p ON m.id_municipio_residencia = p.id_municipio AND m.ano = p.ano
      WHERE m.ano = 2019 GROUP BY u.sigla_uf ORDER BY taxa DESC LIMIT 5`;
    expect(alertasDeSanidade(sql, [{ sigla_uf: "TO", taxa: 0.94 }]).join()).toContain("uma vez por LINHA");
  });
  test("agregado antes em CTE não alerta", () => {
    const sql = `WITH h AS (SELECT sigla_uf, COUNT(*) AS n FROM br_ms_sim.microdados WHERE ano = 2019 GROUP BY 1),
      p AS (SELECT sigla_uf, SUM(populacao) AS pop FROM br_ibge_populacao.municipio WHERE ano = 2019 GROUP BY 1)
      SELECT h.sigla_uf, 100000.0 * h.n / p.pop AS taxa FROM h JOIN p ON h.sigla_uf = p.sigla_uf ORDER BY taxa DESC LIMIT 3`;
    expect(alertasDeSanidade(sql, [{ sigla_uf: "SE", taxa: 42.1 }]).join()).not.toContain("uma vez por LINHA");
  });
});

describe("LIMIT dispensado em tabela pequena", () => {
  test("diretório de UFs sem LIMIT passa", () => {
    expect(portao("SELECT sigla, nome FROM br_bd_diretorios_brasil.uf WHERE sigla = 'SE'").camada).not.toBe("limite");
  });
  test("microdados sem LIMIT continua rejeitado", () => {
    expect(portao("SELECT causa_basica FROM br_ms_sim.microdados WHERE ano = 2020").camada).toBe("limite");
  });
});

describe("comentário e código conferido pelo dicionário", () => {
  test("FROM/JOIN dentro de comentário não vira tabela", () => {
    const { semComentarios } = require("./portao.ts");
    const sql = semComentarios("SELECT COUNT(*) AS n -- junte com a outra depois\nFROM br_ms_sim.microdados /* join com x */ WHERE ano = 2020");
    expect(portao(sql).ok).toBe(true);
    expect(sql).not.toContain("junte");
  });
  test("sexo = '2' na RAIS passa: é chave do dicionário (Feminino)", () => {
    const v = portao("SELECT COUNT(*) FILTER (WHERE sexo = '2') AS f FROM br_me_rais.microdados_vinculos WHERE ano = 2021 AND sigla_uf = 'AC'");
    expect(v.camada).not.toBe("codificacao");
  });
  test("código que não existe no dicionário é recusado com os válidos", () => {
    const v = portao("SELECT COUNT(*) AS n FROM br_me_rais.microdados_vinculos WHERE ano = 2021 AND sigla_uf = 'AC' AND sexo = 'F'");
    expect(v.camada).toBe("codificacao");
    expect(v.erro).toContain("'2'=Feminino");
  });
});

test("SELECT DISTINCT dispensa LIMIT: já reduz as linhas, e a saída é capada", () => {
  expect(portao("SELECT DISTINCT tipo_localizacao FROM br_inep_censo_escolar.escola WHERE ano = 2023").camada).not.toBe("limite");
});

describe("alertas que dispararam à toa em 2026-09-23", () => {
  test("AVG com junção ao diretório de municípios não sugere br_bd_diretorios_brasil.uf", () => {
    const sql = `SELECT m.nome, AVG(md.temperatura_min) AS media, COUNT(*) AS n FROM br_inmet_bdmep.microdados md
      JOIN br_inmet_bdmep.estacao e ON md.id_estacao = e.id_estacao
      JOIN br_bd_diretorios_brasil.municipio m ON e.id_municipio = m.id_municipio
      WHERE md.ano = 2020 GROUP BY 1 ORDER BY 2 LIMIT 10`;
    expect(alertasDeSanidade(sql, [{ nome: "Urubici", media: 10.7, n: 8784 }, { nome: "X", media: 11, n: 8000 }]).join())
      .not.toContain("tabela já agregada");
  });
  test("n de cada grupo acima de 5.570 não é junção duplicada", () => {
    const sql = "SELECT id_municipio, COUNT(*) AS n FROM br_inmet_bdmep.microdados WHERE ano = 2020 GROUP BY 1 ORDER BY 2 LIMIT 10";
    expect(alertasDeSanidade(sql, [{ id_municipio: "4218905", n: 8784 }, { id_municipio: "1", n: 8000 }]).join())
      .not.toContain("passa dos");
  });
  test("o total de uma linha acima de 5.570 continua alertado", () => {
    const sql = "SELECT COUNT(*) AS n FROM br_ibge_pib.municipio p JOIN br_ibge_populacao.municipio q ON p.id_municipio = q.id_municipio";
    expect(alertasDeSanidade(sql, [{ n: 111400 }]).join()).toContain("passa dos");
  });
});

describe("repara — o portão conserta a forma em vez de gastar um turno", () => {
  const { repara } = require("./portao.ts");
  test("LIMIT que faltava", () => {
    const r = repara("SELECT causa_basica FROM br_ms_sim.microdados WHERE ano = 2020;");
    expect(r.sql).toEndWith("LIMIT 100");
    expect(portao(r.sql).ok).toBe(true);
    expect(r.notas).toEqual(["acrescentei LIMIT 100"]);
  });
  test("COUNT(*) AS n no SELECT final, fora da CTE", () => {
    const sql = `WITH t AS (SELECT id_municipio, COUNT(*) AS total FROM br_ms_sim.microdados WHERE ano = 2020 GROUP BY 1)
      SELECT AVG(t.total) AS media FROM t`;
    const r = repara(sql);
    expect(r.sql).toContain("SELECT AVG(t.total) AS media, COUNT(*) AS n\nFROM t");
    expect(r.sql).toContain("SELECT id_municipio, COUNT(*) AS total");
    expect(portao(r.sql).ok).toBe(true);
  });
  test("o caso medido: AVG de IDEB sem n", () => {
    const r = repara("SELECT AVG(ideb) as ideb_medio FROM br_inep_ideb.escola WHERE ano = 2019 AND ensino = 'medio' AND rede = 'estadual'");
    expect(portao(r.sql).ok).toBe(true);
  });
  test("dataset sem tabela vira a tabela principal quando ela é única", () => {
    const r = repara("SELECT COUNT(*) FROM br_ms_sim WHERE ano = 2020");
    expect(r.sql).toBe("SELECT COUNT(*) FROM br_ms_sim.microdados WHERE ano = 2020");
  });
  test("dataset sem tabela principal óbvia continua rejeitado", () => {
    const r = repara("SELECT SUM(pib) FROM br_ibge_pib WHERE ano = 2020");
    expect(r.notas).toEqual([]);
    expect(portao(r.sql).camada).toBe("tabela");
  });
  test("SELECT DISTINCT não ganha COUNT(*) enfiado no meio", () => {
    const r = repara("SELECT DISTINCT AVG(pib) AS m FROM br_ibge_pib.municipio WHERE ano = 2020");
    expect(r.notas).toEqual([]);
  });
  test("GROUP BY posicional continua apontando para a mesma coluna", () => {
    const r = repara("SELECT sigla_uf, AVG(peso) AS peso_medio FROM br_ms_sinasc.microdados WHERE ano = 2019 GROUP BY 1");
    expect(r.sql).toStartWith("SELECT sigla_uf, AVG(peso) AS peso_medio, COUNT(*) AS n\nFROM");
  });
  test("consulta que já passa não muda", () => {
    const sql = "SELECT COUNT(*) FROM br_ms_sim.microdados WHERE ano = 2020";
    expect(repara(sql)).toEqual({ sql, notas: [] });
  });
});

test("AVG sobre a tabela de UFs aponta a tabela Brasil (IDEB 3,8 contra 3,9)", () => {
  const a = alertasDeSanidade("SELECT AVG(ideb) AS m, COUNT(*) AS n FROM br_inep_ideb.uf WHERE ano = 2019 AND rede = 'estadual' AND ensino = 'medio'", [{ m: 3.8, n: 27 }]);
  expect(a.join()).toContain("br_inep_ideb.brasil");
  expect(a.join()).not.toContain("br_inep_ideb.regiao");
});

describe("rodada B2, 2026-09-24 — os 8 primeiros casos, todos sem n", () => {
  test("pergunta de pesquisa contra pergunta direta", () => {
    expect(perguntaDePesquisa("Municípios que mais perderam vínculos no CAGED em 2020 recuperaram emprego formal na RAIS até 2022 proporcionalmente à sua renda (PIB)?")).toBe(true);
    expect(perguntaDePesquisa("A razão óbitos infantis (SIM) / nascidos vivos (SINASC) melhora conforme aumentam leitos e equipes do CNES por habitante?")).toBe(true);
    expect(perguntaDePesquisa("Quais municípios exportam pacientes pelo SIH para hospitais de outros municípios, e isso correlaciona com a falta de leitos locais no CNES e com a renda municipal?")).toBe(true);
    expect(perguntaDePesquisa("Qual município do Pará teve mais focos de queimada em 2020?")).toBe(false);
    expect(perguntaDePesquisa("Em quantos municípios o saldo de empregos formais do CAGED foi negativo em 2023?")).toBe(false);
    expect(perguntaDePesquisa("")).toBe(false);
  });

  // A SQL final do caso 8, encurtada: CAGED × RAIS × PIB, top 10 por um score.
  const TOP10 = `WITH p AS (SELECT id_municipio, SUM(saldo_movimentacao) AS s FROM br_me_caged.microdados_movimentacao WHERE ano = 2020 GROUP BY 1),
r AS (SELECT id_municipio, COUNT(*) AS v FROM br_me_rais.microdados_vinculos WHERE ano = 2022 GROUP BY 1),
i AS (SELECT id_municipio, pib FROM br_ibge_pib.municipio WHERE ano = 2020)
SELECT d.nome, r.v / ABS(p.s) / i.pib AS score FROM p
JOIN br_bd_diretorios_brasil.municipio d ON p.id_municipio = d.id_municipio
LEFT JOIN r ON p.id_municipio = r.id_municipio LEFT JOIN i ON p.id_municipio = i.id_municipio
ORDER BY score DESC LIMIT 10`;

  test("ranking de várias fontes é rejeitado", () => {
    const v = checaRanking(TOP10);
    expect(v.ok).toBe(false);
    expect(v.camada).toBe("ranking");
    expect(v.erro).toContain("COUNT(*) AS n");
  });
  test("a mesma junção medida com corr e n passa", () => {
    expect(checaRanking(TOP10.replace(/SELECT d\.nome[\s\S]*$/, "SELECT corr(r.v, i.pib) AS corr, COUNT(*) AS n FROM p JOIN r USING (id_municipio) JOIN i USING (id_municipio)")).ok).toBe(true);
  });
  test("faixas com n e ORDER BY passam", () => {
    expect(checaRanking("WITH f AS (SELECT a.id_municipio, ntile(4) OVER (ORDER BY a.pib) AS faixa, b.x FROM br_ibge_pib.municipio a JOIN br_ms_sim.microdados b USING (id_municipio)) SELECT faixa, AVG(x) AS y, COUNT(*) AS n FROM f GROUP BY faixa ORDER BY faixa LIMIT 100").ok).toBe(true);
  });
  test("exploração de uma fonte com LIMIT segue livre", () => {
    expect(checaRanking("SELECT nome, pib FROM br_ibge_pib.municipio p JOIN br_bd_diretorios_brasil.municipio d USING (id_municipio) WHERE ano = 2020 ORDER BY pib DESC LIMIT 10").ok).toBe(true);
  });

  test("zero em todo grupo com filtro != avisa do NULL (caso 6)", () => {
    const sql = "SELECT grupo, AVG(t) AS avg_mortalidade, COUNT(*) AS n FROM m WHERE tipo_obito_ocorrencia != '8' GROUP BY grupo";
    const a = alertasDeSanidade(sql, [{ grupo: "a", avg_mortalidade: 0, n: 1200 }, { grupo: "b", avg_mortalidade: 0, n: 2025 }]).join();
    expect(a).toContain("NULL != 'x'");
    expect(a).toContain("tipo_obito_ocorrencia");
  });
  test("zero sem filtro != não avisa", () => {
    const a = alertasDeSanidade("SELECT grupo, SUM(x) AS s, COUNT(*) AS n FROM m GROUP BY grupo", [{ grupo: "a", s: 0, n: 3 }, { grupo: "b", s: 0, n: 4 }]).join();
    expect(a).not.toContain("NULL != 'x'");
  });
});

describe("sem-ponte através de subconsulta e CTE (caso 4 da rodada B2)", () => {
  const SUB = `SELECT sinasc.id_municipio_nascimento, bcf.beneficiarios
FROM (SELECT id_municipio_nascimento, COUNT(*) AS nasc FROM br_ms_sinasc.microdados WHERE ano = 2022 GROUP BY 1) sinasc
JOIN (SELECT codigo_municipio_siafi, COUNT(*) AS beneficiarios FROM br_cgu_novo_bolsa_familia.novo_bolsa_familia WHERE ano_mes = '202306' GROUP BY codigo_municipio_siafi) bcf
  ON sinasc.id_municipio_nascimento = bcf.codigo_municipio_siafi`;
  test("apelido de subconsulta resolve para a tabela de dentro", () => {
    const a = juncoesSemPonte(SUB);
    expect(a.length).toBe(1);
    expect(a[0]!.refB).toBe("br_cgu_novo_bolsa_familia.novo_bolsa_familia");
    expect(a[0]!.colB).toBe("codigo_municipio_siafi");
  });
  test("o mesmo via CTE", () => {
    const cte = `WITH b AS (SELECT codigo_municipio_siafi, COUNT(*) AS q FROM br_cgu_novo_bolsa_familia.novo_bolsa_familia GROUP BY 1)
SELECT * FROM br_ms_sinasc.microdados s JOIN b ON s.id_municipio_nascimento = b.codigo_municipio_siafi WHERE s.ano = 2022`;
    expect(juncoesSemPonte(cte).map((j) => j.colB)).toContain("codigo_municipio_siafi");
  });
  test("id_municipio dos dois lados, via subconsulta, segue sem alerta", () => {
    const ok = `SELECT * FROM (SELECT id_municipio, SUM(pib) AS pib FROM br_ibge_pib.municipio WHERE ano = 2020 GROUP BY 1) p
JOIN (SELECT id_municipio, SUM(populacao) AS pop FROM br_ibge_populacao.municipio WHERE ano = 2020 GROUP BY 1) q ON p.id_municipio = q.id_municipio`;
    expect(juncoesSemPonte(ok)).toEqual([]);
  });
});
