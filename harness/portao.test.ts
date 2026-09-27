/**
 * Os casos deste arquivo não são hipotéticos: cada um é uma SQL que o Gemma 4
 * escreveu de verdade no beelink em 2026-09-01, ou um erro que o pipeline do
 * ask-web apanhou em produção. O portão existe por causa deles.
 */
import { expect, test, describe } from "bun:test";
import {
  portao, alertasDeSanidade,
  juncoesSemPonte, mensagemSemPonte, assinaturaJuncao,
  perguntaDePesquisa, checaRanking, fonteTrocada, coeficienteVazio, correlacaoExtensiva, naoSomavel,
  checaCodigoTse, correlacaoParteTodo, totaisSobPedidoDeTaxa, alertaDeEscala, sugestao,
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
  // B24, T03-1 da B19: o UNION ALL dentro de uma subconsulta dentro da CTE
  // (parênteses aninhados, com COUNT(*) dentro) parecia UNION no nível de fora,
  // e o COUNT(*) AS n não era acrescentado.
  test("UNION aninhado numa CTE não impede o COUNT(*) AS n no SELECT final", () => {
    const sql = `WITH b AS (SELECT id_municipio, SUM(cnt) AS total FROM (
        SELECT id_municipio, COUNT(*) AS cnt FROM br_ibge_pib.municipio WHERE ano = 2020 GROUP BY 1
        UNION ALL
        SELECT id_municipio, COUNT(*) FROM br_ibge_populacao.municipio WHERE ano = 2020 GROUP BY 1
      ) GROUP BY 1)
      SELECT CORR(total, total) AS r FROM b`;
    const r = repara(sql);
    expect(r.sql).toContain("AS r, COUNT(*) AS n\nFROM b");
  });
  test("UNION no nível de fora continua sem COUNT(*) enfiado", () => {
    const r = repara(`SELECT AVG(pib) AS m FROM br_ibge_pib.municipio WHERE ano = 2020
      UNION ALL SELECT AVG(pib) AS m FROM br_ibge_pib.municipio WHERE ano = 2021`);
    expect(r.notas).toEqual([]);
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

describe("B15 — janela e agregado no GROUP BY (rodada B2, 2026-09-25)", () => {
  test("ntile no GROUP BY é rejeitado com o molde", () => {
    const v = portao("SELECT ntile(4) OVER (ORDER BY pib) AS faixa, COUNT(*) AS n FROM br_ibge_pib.municipio WHERE ano = 2020 GROUP BY ntile(4) OVER (ORDER BY pib)");
    expect(v.ok).toBe(false);
    expect(v.camada).toBe("group-by");
    expect(v.erro).toContain("WITH base AS");
  });
  test("agregado no GROUP BY é rejeitado", () => {
    const v = portao("SELECT sigla_uf, COUNT(*) AS n FROM br_ibge_pib.municipio WHERE ano = 2020 GROUP BY sigla_uf, SUM(pib)");
    expect(v.camada).toBe("group-by");
  });
  test("o molde de faixas passa", () => {
    const v = portao("WITH base AS (SELECT id_municipio, pib, ntile(4) OVER (ORDER BY pib) AS faixa FROM br_ibge_pib.municipio WHERE ano = 2020) SELECT faixa, AVG(pib) AS media_y, COUNT(*) AS n FROM base GROUP BY faixa ORDER BY faixa");
    expect(v.camada).not.toBe("group-by");
  });
  test("GROUP BY posicional e por coluna passam", () => {
    expect(portao("SELECT sigla_uf, SUM(pib) AS s FROM br_ibge_pib.municipio WHERE ano = 2020 GROUP BY 1").camada).not.toBe("group-by");
  });
  // B24, T03-1 da B19: o GROUP BY do 1º ramo de um UNION ALL engolia o SELECT
  // do 2º ramo (`GROUP BY 1 UNION ALL SELECT id, COUNT(*)`), e a SQL válida
  // foi rejeitada 12 vezes seguidas até o teto de 1.500 s.
  test("GROUP BY antes de UNION ALL não lê o agregado do ramo seguinte", () => {
    const sql = `SELECT id_municipio, SUM(cnt) AS total FROM (
      SELECT id_municipio, COUNT(*) AS cnt FROM br_ibge_pib.municipio WHERE ano = 2020 GROUP BY 1
      UNION ALL
      SELECT id_municipio, COUNT(*) FROM br_ibge_populacao.municipio WHERE ano = 2020 GROUP BY 1
    ) GROUP BY 1`;
    expect(portao(sql).camada).not.toBe("group-by");
  });
  test("agregado no GROUP BY de um ramo de UNION continua rejeitado", () => {
    const sql = `SELECT sigla_uf, COUNT(*) AS n FROM br_ibge_pib.municipio WHERE ano = 2020 GROUP BY 1
      UNION ALL SELECT sigla_uf, COUNT(*) AS n FROM br_ibge_pib.municipio WHERE ano = 2021 GROUP BY sigla_uf, SUM(pib)`;
    expect(portao(sql).camada).toBe("group-by");
  });
});

describe("B24 — a mesma SQL rejeitada de novo (T03-1 10x, T16-4 8x na B19)", () => {
  const { avisoRejeicaoRepetida } = require("./portao.ts");
  test("1ª rejeição não ganha aviso", () => {
    expect(avisoRejeicaoRepetida(1)).toBeUndefined();
  });
  test("da 2ª em diante diz que é repetição e manda mudar ou parar", () => {
    const a = avisoRejeicaoRepetida(3);
    expect(a).toContain("3ª vez");
    expect(a).toContain("pare e responda");
  });
});

describe("B24 — coluna com acento sem aspas (T16-4 da B19)", () => {
  // `d.Função` virava a coluna inexistente `Fun`: o \w do JS é só ASCII. A SQL
  // foi rejeitada 10 vezes com "Coluna inexistente: Fun, Subfun, A".
  test("coluna real com acento passa", () => {
    const v = portao("SELECT d.Função, d.Subfunção, d.Ação, COUNT(*) AS n FROM br_siop_orcamento.dados d GROUP BY 1, 2, 3");
    expect(v.camada).not.toBe("coluna");
  });
  test("coluna inventada com acento continua rejeitada, com o nome inteiro", () => {
    const v = portao("SELECT d.Funçãozinha, COUNT(*) AS n FROM br_siop_orcamento.dados d GROUP BY 1");
    expect(v.camada).toBe("coluna");
    expect(v.erro).toContain("Funçãozinha");
  });
});

describe("camada valor — literal que a coluna não tem (triagem B2, 2026-09-25)", () => {
  test("'Preto'/'Pardo' no Censo 2022, que guarda 'Preta'/'Parda'", () => {
    const v = portao("SELECT id_municipio, SUM(populacao) AS p FROM br_ibge_censo_2022.populacao_grupo_idade_sexo_raca WHERE cor_raca IN ('Preto','Pardo') GROUP BY 1");
    expect(v.camada).toBe("valor");
    expect(v.erro).toContain("'Preta'");
  });
  test("o valor certo passa", () => {
    expect(portao("SELECT id_municipio, SUM(populacao) AS p FROM br_ibge_censo_2022.populacao_grupo_idade_sexo_raca WHERE cor_raca IN ('Preta','Parda') GROUP BY 1").ok).toBe(true);
  });
  test("valor de outra coluna ('finais (6-9)' é anos_escolares, não ensino)", () => {
    const v = portao("SELECT id_municipio, ideb FROM br_inep_ideb.municipio WHERE ano = 2019 AND ensino = 'finais (6-9)' LIMIT 10");
    expect(v.camada).toBe("valor");
  });
});

test("código de UF filtrado vira sigla no alerta (holdout3: '41','26' era PR e PE, não MG e BA)", () => {
  const a = alertasDeSanidade("SELECT id_uf_mae, COUNT(*) AS n FROM br_ms_sinasc.microdados WHERE ano = 2020 AND id_uf_mae IN ('41', '26') GROUP BY id_uf_mae",
    [{ id_uf_mae: "41", n: 148581 }, { id_uf_mae: "26", n: 142122 }]).join(" ");
  expect(a).toContain("41 = PR");
  expect(a).toContain("26 = PE");
});

describe("fonte trocada — pergunta direta nomeia uma fonte e a SQL usa outra (holdout3, 2026-09-25)", () => {
  const q = "Qual foi o saldo de empregos formais do CAGED no Brasil em 2019?";
  test("CAGED pedido, RAIS consultada: avisa", () => {
    const a = fonteTrocada(q, "SELECT COUNT(*) AS n FROM br_me_rais.microdados_vinculos WHERE ano = 2019 AND vinculo_ativo_3112 = '1'");
    expect(a).toContain("não usa br_me_caged");
    expect(a).toContain("br_me_rais");
  });
  test("CAGED pedido e consultado: calado", () => {
    expect(fonteTrocada(q, "SELECT SUM(saldo_movimentacao) FROM br_me_caged.microdados_movimentacao WHERE ano = 2021")).toBeUndefined();
  });
  test("exploração sem agregado: calado", () => {
    expect(fonteTrocada(q, "SELECT DISTINCT ano FROM br_me_rais.microdados_vinculos")).toBeUndefined();
  });
  test("SIM não casa 'sim' minúsculo da prosa", () => {
    expect(fonteTrocada("Houve mais óbitos, sim ou não, em 2020 no RAIS?", "SELECT COUNT(*) FROM br_me_rais.microdados_vinculos WHERE ano=2020")).toBeUndefined();
  });
});

describe("coeficienteVazio — corr() NULL não é resultado a escrever (B22, B19 2026-09-26)", () => {
  test("T03-2: r NULL com n=3602 — aponta pares, não linhas", () => {
    const a = coeficienteVazio([{ r_leitos: null, r_equipes: null, n: 3602 }]);
    expect(a).toContain("r_leitos, r_equipes voltou NULL embora n=3602");
    expect(a).toContain("regr_count");
    expect(a).toContain("Não escreva esse coeficiente");
  });
  test("T09-1: r NULL com n=0", () => {
    expect(coeficienteVazio([{ r: null, n: 0 }])).toContain("r voltou NULL");
  });
  test("T38-2: r = 1,0000000000000009 é degenerado", () => {
    expect(coeficienteVazio([{ r: 1.0000000000000009, n: 27 }])).toContain("deu ±1");
  });
  test("coeficiente de verdade, mesmo alto (população × eleitorado 0,998): calado", () => {
    expect(coeficienteVazio([{ r: 0.998, n: 5570 }])).toBeUndefined();
    expect(coeficienteVazio([{ r: -0.27, n: 5460 }])).toBeUndefined();
  });
  test("sem coluna de coeficiente: calado", () => {
    expect(coeficienteVazio([{ total: null, n: 0 }])).toBeUndefined();
  });
  test("NaN do -json também conta como vazio", () => {
    expect(coeficienteVazio([{ corr_pib: "NaN", n: 10 }])).toContain("corr_pib voltou NULL");
  });
});

describe("B23 — corr() sobre contagem crua (rodada B19, sinal trocado, 2026-09-26)", () => {
  // SQLs do Gemma na B19, encurtadas só no que não muda o que o detector lê.
  test("T29-3: emendas somadas por COALESCE de um SUM, dois níveis de alias", () => {
    const sql = `WITH e AS (SELECT id_municipio_gasto AS id_municipio, ano_emenda, SUM(valor_liquidado) as total_emendas
      FROM br_cgu_emendas_parlamentares.microdados WHERE ano_emenda BETWEEN 2014 AND 2024 GROUP BY 1, 2),
    d AS (SELECT m.id_municipio, m.margem_votos, COALESCE(e.total_emendas, 0) as valor_emendas FROM m LEFT JOIN e ON m.id_municipio = e.id_municipio)
    SELECT corr(margem_votos, valor_emendas) as r, COUNT(*) as n FROM d WHERE valor_emendas > 0`;
    expect(correlacaoExtensiva(sql)).toEqual(["valor_emendas"]);
    expect(alertasDeSanidade(sql, [{ r: 0.2154, n: 1808 }]).some((a) => a.includes("contagem ou soma crua"))).toBe(true);
  });
  test("T08-1: COUNT(DISTINCT nis) contra gasto per capita — só a contagem é apontada", () => {
    const sql = `WITH beneficiarios AS (SELECT id_municipio, COUNT(DISTINCT nis_favorecido) AS n_beneficiarios
      FROM br_cgu_beneficios_cidadao.novo_bolsa_familia WHERE ano_referencia = 2023 GROUP BY id_municipio)
    SELECT corr(b.n_beneficiarios, (g.total_social_empenhado / NULLIF(p.total_pop, 0)) * 100) AS r_gasto,
      corr(b.n_beneficiarios, v.pct_baixa_instrucao) AS r_vuln, COUNT(DISTINCT b.id_municipio) AS n
    FROM beneficiarios b JOIN g ON TRUE`;
    expect(correlacaoExtensiva(sql)).toEqual(["b.n_beneficiarios"]);
  });
  test("T15-3: COUNT(CASE ...) de sobrenomes repetidos", () => {
    const sql = `WITH s AS (SELECT id_municipio, COUNT(CASE WHEN freq >= 2 THEN 1 END) as qtd_sobrenomes_recorrentes FROM f GROUP BY 1)
    SELECT CORR(s.qtd_sobrenomes_recorrentes, p.pib_pc) AS r, COUNT(*) AS n FROM s JOIN p ON s.id_municipio = p.id_municipio`;
    expect(correlacaoExtensiva(sql)).toEqual(["s.qtd_sobrenomes_recorrentes"]);
  });
  test("taxas e per capita não disparam (T08-3, T31-3, pib per capita)", () => {
    expect(correlacaoExtensiva(`SELECT corr(r.receita_propria_total / NULLIF(p.total_pop, 0), f.receita_federal_total / NULLIF(p.total_pop, 0)) AS r, COUNT(*) AS n FROM r`)).toEqual([]);
    expect(correlacaoExtensiva(`WITH m AS (SELECT id, 1000.0 * COUNT(*) FILTER (WHERE idade < 1) / NULLIF(MAX(nasc), 0) AS tmi FROM x GROUP BY 1)
      SELECT corr(m.tmi, v.ivs) AS r, COUNT(*) AS n FROM m JOIN v ON TRUE`)).toEqual([]);
    expect(correlacaoExtensiva(`WITH p AS (SELECT id_municipio, SUM(pib) / NULLIF(SUM(populacao), 0) AS pib_pc FROM t GROUP BY 1)
      SELECT corr(pib_pc, AVG_x) AS r, COUNT(*) AS n FROM p`)).toEqual([]);
  });
  test("T81-3: apelido de tabela igual ao nome da coluna não é definição", () => {
    expect(correlacaoExtensiva(`SELECT corr(esf.proporcao_cobertura, ideb.ideb) AS r, COUNT(*) AS n
      FROM br_ms_atencao_basica.municipio AS esf JOIN br_inep_ideb.municipio AS ideb ON esf.id_municipio = ideb.id_municipio`)).toEqual([]);
  });
  test("total contra total não dispara: às vezes é a pergunta (T22-1 focos × km² desmatados)", () => {
    expect(correlacaoExtensiva(`WITH f AS (SELECT id_municipio, COUNT(*) AS total_focos FROM q GROUP BY 1),
      d AS (SELECT id_municipio, SUM(area) AS desmatamento FROM p GROUP BY 1)
      SELECT corr(total_focos, desmatamento) AS r, COUNT(*) AS n FROM f JOIN d USING (id_municipio)`)).toEqual([]);
  });
  test("limite conhecido: coluna crua de tabela, sem alias, não é seguida", () => {
    expect(correlacaoExtensiva("SELECT corr(populacao, pib) AS r, COUNT(*) AS n FROM br_ibge_pib.municipio WHERE ano = 2021")).toEqual([]);
  });
});

// B25: toda SQL rejeitada da B19 reaplicada offline no portão. Cada falso
// positivo vem com a SQL real e um par que prova que o erro de verdade segue
// rejeitado.
describe("B25 — falsos positivos da B19", () => {
  test("coluna: nome pontuado dentro de literal não é alias.coluna (T81-2)", () => {
    const v = portao(
      "SELECT 'br_ibge_pib.municipio' as fonte_pib, 'br_mc_indicadores.transferencias_municipio' as fonte_pbf " +
      "FROM br_bd_diretorios_brasil.municipio LIMIT 1",
    );
    expect(v.ok).toBe(true);
  });
  test("par: a mesma coluna fora do literal segue inexistente", () => {
    const v = portao("SELECT m.transferencias_municipio FROM br_bd_diretorios_brasil.municipio m LIMIT 1");
    expect(v.camada).toBe("coluna");
  });

  test("partição: espiada SELECT * LIMIT 5 passa (T30-2, T35-4)", () => {
    expect(portao("SELECT * FROM br_me_cnpj.estabelecimentos LIMIT 5").ok).toBe(true);
    expect(portao("SELECT * FROM br_me_rais_identificada.estabelecimentos LIMIT 5").ok).toBe(true);
  });
  test("par: DISTINCT sobre os 2,5 bi do CNPJ lê tudo e segue exigindo filtro (T36-2)", () => {
    const v = portao("SELECT DISTINCT cnae_fiscal_principal FROM br_me_cnpj.estabelecimentos LIMIT 100");
    expect(v.camada).toBe("particao");
  });
  test("partição: DISTINCT de código em tabela abaixo de 100M passa (T21-4, T77-5)", () => {
    expect(portao("SELECT DISTINCT conta_bd FROM br_me_siconfi.municipio_receitas_orcamentarias LIMIT 20").ok).toBe(true);
    expect(portao(
      "SELECT DISTINCT conta_bd FROM br_me_siconfi.municipio_receitas_orcamentarias WHERE conta_bd LIKE '%CFEM%' LIMIT 20",
    ).ok).toBe(true);
  });
  test("par: somar sem ano em tabela com partição de tempo soma todos os anos (T11-2)", () => {
    const v = portao(
      "WITH investimento_municipio AS (SELECT id_municipio, sigla_uf, SUM(valor) AS investimento_saneamento_empenhado " +
      "FROM br_me_siconfi.municipio_despesas_funcao WHERE estagio = 'Despesas Empenhadas' GROUP BY 1, 2) " +
      "SELECT corr(i.investimento_saneamento_empenhado, i.investimento_saneamento_empenhado) AS r, COUNT(*) AS n FROM investimento_municipio i",
    );
    expect(v.camada).toBe("particao");
  });

  test("ranking: ordenar por ano é olhar a série, não ranking (T22-2)", () => {
    const sql =
      "WITH o AS (SELECT ano, mes, id_municipio, COUNT(*) AS total_obitos FROM br_ms_sim.microdados WHERE ano = 2021 GROUP BY 1, 2, 3), " +
      "f AS (SELECT ano, mes, id_municipio, COUNT(*) AS total_focos FROM br_inpe_queimadas.microdados WHERE ano = 2021 GROUP BY 1, 2, 3) " +
      "SELECT o.ano, o.mes, o.total_obitos, f.total_focos FROM o JOIN f ON o.id_municipio = f.id_municipio " +
      "ORDER BY o.ano, o.mes LIMIT 10";
    expect(checaRanking(sql).ok).toBe(true);
  });
  test("ranking: 'quais UFs' no grão de UF não é amostra de municípios (T15-5)", () => {
    const sql =
      "WITH p AS (SELECT sigla_uf, AVG(valor_item) AS pat FROM br_tse_eleicoes.bens_candidato WHERE ano = 2024 GROUP BY 1), " +
      "e AS (SELECT sigla_uf_gasto, SUM(valor_empenhado) AS total_emendas FROM br_cgu_emendas_parlamentares.microdados WHERE ano_emenda = 2023 GROUP BY 1) " +
      "SELECT p.sigla_uf, p.pat, e.total_emendas FROM p JOIN e ON p.sigla_uf = e.sigla_uf_gasto ORDER BY p.pat DESC LIMIT 10";
    expect(checaRanking(sql).ok).toBe(true);
  });
  test("par: top 10 de municípios juntando duas fontes segue rejeitado (T13-2)", () => {
    const sql =
      "WITH p AS (SELECT id_municipio, SUM(pib) AS pib FROM br_ibge_pib.municipio WHERE ano = 2021 GROUP BY 1), " +
      "c AS (SELECT id_municipio, SUM(saldo_movimentacao) AS saldo FROM br_me_caged.microdados_movimentacao WHERE ano = 2023 GROUP BY 1) " +
      "SELECT p.id_municipio, p.pib, c.saldo FROM p JOIN c ON p.id_municipio = c.id_municipio ORDER BY p.pib DESC LIMIT 10";
    expect(checaRanking(sql).camada).toBe("ranking");
  });
});

describe("B28 — filiação nacional sem recorte de UF (T15-3)", () => {
  test("agregar a filiação do país sozinha numa CTE passa", () => {
    const v = portao(
      "WITH filiados AS (SELECT id_municipio, COUNT(*) AS total_filiados, COUNT(DISTINCT regexp_extract(nome, ' ([^ ]+)$')) AS sobrenomes " +
      "FROM br_tse_filiacao_partidaria.microdados WHERE situacao_registro = 'Regular' GROUP BY 1), " +
      "pib AS (SELECT id_municipio, SUM(pib) AS pib FROM br_ibge_pib.municipio WHERE ano = 2021 GROUP BY 1) " +
      "SELECT corr(f.sobrenomes, p.pib) AS r, COUNT(*) AS n FROM filiados f JOIN pib p ON f.id_municipio = p.id_municipio",
    );
    expect(v.ok).toBe(true);
  });
  test("par: filiação crua num JOIN sem UF segue rejeitada, e a mensagem ensina o caminho nacional", () => {
    const v = portao(
      "SELECT f.id_municipio, COUNT(*) AS n FROM br_tse_filiacao_partidaria.microdados f " +
      "JOIN br_ibge_pib.municipio p ON f.id_municipio = p.id_municipio WHERE p.ano = 2021 GROUP BY 1",
    );
    expect(v.camada).toBe("particao");
    expect(v.erro).toContain("não recorte um estado");
  });
  test("par: acima de 100M a mensagem não oferece o caminho sem filtro", () => {
    const v = portao("SELECT COUNT(*) FROM br_ms_sih.aihs_reduzidas");
    expect(v.camada).toBe("particao");
    expect(v.erro).not.toContain("não recorte um estado");
  });
});

describe("B29 — DISTINCT ano sem ORDER BY (T15-3)", () => {
  const { repara } = require("./portao.ts");
  test("o DISTINCT final de ano ganha ORDER BY ano DESC antes do LIMIT", () => {
    const r = repara(
      "WITH pib_pop AS (SELECT DISTINCT ano FROM br_ibge_pib.municipio LIMIT 5)\nSELECT DISTINCT ano FROM br_ibge_pib.municipio LIMIT 5;",
    );
    expect(r.sql).toEndWith("SELECT DISTINCT ano FROM br_ibge_pib.municipio\nORDER BY ano DESC LIMIT 5");
    expect(r.notas.join(" ")).toContain("ORDER BY ano DESC");
  });
  test("várias colunas de tempo, com WHERE (T07-2)", () => {
    const r = repara("SELECT DISTINCT ano, mes FROM br_bcb_estban.municipio WHERE sigla_uf = 'SP' LIMIT 10");
    expect(r.sql).toContain("ORDER BY ano DESC, mes DESC LIMIT 10");
  });
  test("par: com ORDER BY, ou coluna que não é tempo, não mexe", () => {
    expect(repara("SELECT DISTINCT ano FROM br_ibge_pib.municipio ORDER BY ano LIMIT 5").notas).toEqual([]);
    const r = repara("SELECT DISTINCT ano, raca_cor FROM br_ipea_avs.municipio LIMIT 20");
    expect(r.sql).not.toContain("ORDER BY");
  });
});

describe("B34 — filtro de partição no escopo que lê a tabela (T22-2)", () => {
  test("T22-2: a CTE lê o SIM inteiro e só o WHERE de fora filtra ano — rejeita", () => {
    const v = portao(
      "WITH o AS (SELECT ano, mes, id_municipio_residencia AS id_municipio, COUNT(*) AS total_obitos FROM br_ms_sim.microdados GROUP BY 1, 2, 3) " +
      "SELECT o.id_municipio, SUM(o.total_obitos) AS obitos, COUNT(*) AS n FROM o WHERE o.ano = 2021 GROUP BY 1",
    );
    expect(v.camada).toBe("particao");
  });
  test("par: o mesmo com o filtro dentro da CTE passa", () => {
    const v = portao(
      "WITH o AS (SELECT ano, mes, id_municipio_residencia AS id_municipio, COUNT(*) AS total_obitos FROM br_ms_sim.microdados WHERE ano = 2021 GROUP BY 1, 2, 3) " +
      "SELECT o.id_municipio, SUM(o.total_obitos) AS obitos, COUNT(*) AS n FROM o GROUP BY 1",
    );
    expect(v.ok).toBe(true);
  });
  test("filtro por apelido no mesmo escopo do JOIN passa", () => {
    const v = portao(
      "SELECT s.id_municipio_residencia, COUNT(*) AS n FROM br_ms_sim.microdados s JOIN br_ibge_pib.municipio p " +
      "ON s.id_municipio_residencia = p.id_municipio AND p.ano = 2021 WHERE s.ano = 2021 GROUP BY 1",
    );
    expect(v.ok).toBe(true);
  });
  test("subconsulta com filtro próprio passa", () => {
    const v = portao(
      "SELECT id_municipio, nome FROM br_bd_diretorios_brasil.municipio WHERE id_municipio IN " +
      "(SELECT id_municipio_residencia FROM br_ms_sim.microdados WHERE ano = 2020 GROUP BY 1)",
    );
    expect(v.ok).toBe(true);
  });
  test("tabela lida em dois escopos, um sem filtro: rejeita", () => {
    const v = portao(
      "WITH a AS (SELECT id_municipio_residencia AS id_municipio, COUNT(*) AS x FROM br_ms_sim.microdados WHERE ano = 2021 GROUP BY 1), " +
      "b AS (SELECT id_municipio_residencia AS id_municipio, COUNT(*) AS y FROM br_ms_sim.microdados GROUP BY 1) " +
      "SELECT corr(a.x, b.y) AS r, COUNT(*) AS n FROM a JOIN b ON a.id_municipio = b.id_municipio",
    );
    expect(v.camada).toBe("particao");
  });
  test("as exceções da B25 seguem valendo: espiada e agregação nacional de tabela só por UF", () => {
    expect(portao("SELECT * FROM br_me_cnpj.estabelecimentos LIMIT 5").ok).toBe(true);
    expect(portao(
      "WITH filiados AS (SELECT id_municipio, COUNT(*) AS total_filiados FROM br_tse_filiacao_partidaria.microdados GROUP BY 1), " +
      "pib AS (SELECT id_municipio, SUM(pib) AS pib FROM br_ibge_pib.municipio WHERE ano = 2021 GROUP BY 1) " +
      "SELECT corr(f.total_filiados / p.pib, p.pib) AS r, COUNT(*) AS n FROM filiados f JOIN pib p ON f.id_municipio = p.id_municipio",
    ).camada).not.toBe("particao");
  });
});

describe("B36 — a anotação de GROUP BY não soma ano nem código", () => {
  test("naoSomavel: tempo e código fora; quantidade dentro", () => {
    for (const c of ["ano", "mes", "ano_emenda", "id_municipio", "cod_ibge", "codigo_ibge", "sigla_uf", "id"]) expect(naoSomavel(c)).toBe(true);
    for (const c of ["n", "total", "valor", "anos_estudo", "populacao", "idade"]) expect(naoSomavel(c)).toBe(false);
  });
  test("GROUP BY ano sem outra coluna numérica: não diz 'Somando a coluna ano'", () => {
    const a = alertasDeSanidade("SELECT ano FROM br_ms_sim.microdados WHERE ano >= 2020 GROUP BY ano",
      [{ ano: 2020 }, { ano: 2021 }, { ano: 2022 }, { ano: 2023 }, { ano: 2024 }]);
    expect(a.join(" ")).not.toContain("Somando a coluna 'ano'");
  });
  test("par: com ano e uma quantidade, soma a quantidade", () => {
    const a = alertasDeSanidade("SELECT ano, SUM(x) AS total FROM br_ms_sim.microdados WHERE ano >= 2020 GROUP BY ano",
      [{ ano: 2020, total: 10 }, { ano: 2021, total: 5 }]);
    expect(a.join(" ")).toContain("Somando a coluna 'total' nas 2 linhas: 15");
  });
});

describe("rerun de 2026-09-27 — sinal trocado e r ausente (TRACE)", () => {
  test("T05-5: código TSE igualado a código IBGE é recusado, com o id_municipio da própria tabela", () => {
    const v = checaCodigoTse(`WITH g AS (SELECT r.id_municipio_tse FROM br_tse_eleicoes.resultados_candidato_municipio r WHERE r.ano = 2020),
      t AS (SELECT CAST(p.codigo_ibge_municipio_ente_recebedor_plano_acao AS VARCHAR) as id_municipio_str FROM br_transferegov.planos_acao p)
      SELECT CORR(g.x, t.y) AS r, COUNT(*) AS n FROM g JOIN t ON g.id_municipio_tse = t.id_municipio_str`);
    expect(v.ok).toBe(false);
    expect(v.erro).toContain("id_municipio (IBGE)");
  });
  test("T05-1: db.id_municipio_tse = m.id_municipio (PIB) é recusado", () => {
    expect(checaCodigoTse("SELECT 1 FROM d db LEFT JOIN m ON db.id_municipio_tse = m.id_municipio").ok).toBe(false);
  });
  test("TSE com TSE, e TSE com literal, passam", () => {
    expect(checaCodigoTse(`SELECT m.nome FROM br_tse_eleicoes.detalhes_votacao_municipio v JOIN mun m
      ON v.id_municipio_tse = m.id_municipio_tse AND v.sigla_uf = m.sigla_uf`).ok).toBe(true);
    expect(checaCodigoTse("SELECT * FROM br_tse_eleicoes.candidatos WHERE id_municipio_tse = '71072'").ok).toBe(true);
    expect(checaCodigoTse("SELECT * FROM a JOIN b ON a.id_municipio = b.id_municipio").ok).toBe(true);
  });

  test("T35-4: corr(renda/tempo, renda) é razão contra o próprio termo", () => {
    const sql = `WITH base AS (SELECT r.id_municipio, AVG(r.valor_remuneracao_media) AS renda_media, t.tempo_medio_deslocamento AS tempo
      FROM br_me_rais.microdados_vinculos r JOIN br_mobilidados_indicadores.tempo_deslocamento_casa_trabalho t ON r.id_municipio = t.id_municipio
      WHERE r.ano = 2022 AND t.ano = 2010 GROUP BY r.id_municipio, t.tempo_medio_deslocamento)
      SELECT corr(renda_media / tempo, renda_media) AS r, COUNT(*) AS n FROM base`;
    expect(correlacaoParteTodo(sql)).toEqual([["renda_media / tempo", "renda_media"]]);
    expect(alertasDeSanidade(sql, [{ r: 0.6797, n: 227 }]).some((a) => a.includes("próprios termos"))).toBe(true);
  });
  test("razões independentes e variável contra variável não disparam", () => {
    expect(correlacaoParteTodo("SELECT corr(renda_media, tempo) AS r, COUNT(*) AS n FROM b")).toEqual([]);
    expect(correlacaoParteTodo("SELECT corr(obitos / pop, focos / area) AS r, COUNT(*) AS n FROM b")).toEqual([]);
  });

  // T22-2 (pergunta pede controle por população) × T22-1 (publicado em totais).
  const totXtot = `WITH o AS (SELECT id_municipio, COUNT(*) AS obitos_resp FROM x GROUP BY 1),
    f AS (SELECT id_municipio, COUNT(*) AS num_focos FROM y GROUP BY 1)
    SELECT corr(o.obitos_resp, f.num_focos) AS r, COUNT(*) AS n FROM o JOIN f USING (id_municipio)`;
  test("T22-2: dois totais sob pergunta que pede controle por população disparam", () => {
    const p = "A mortalidade respiratória (SIM) sobe nos meses/municípios de pico de fogo (QUEIMADAS), controlada pela população do Censo?";
    expect(totaisSobPedidoDeTaxa(totXtot, p)).toEqual([["o.obitos_resp", "f.num_focos"]]);
    expect(alertasDeSanidade(totXtot, [{ r: 0.5, n: 5000 }], p).some((a) => a.includes("dois totais crus"))).toBe(true);
    expect(alertaDeEscala(totXtot, p)).toBe(true);
  });
  test("T22-1 (totais publicados) e T05-1 ('PIB per capita' nomeia variável) ficam calados", () => {
    expect(totaisSobPedidoDeTaxa(totXtot, "Municípios recordistas de focos de calor (QUEIMADAS) perderam mais vegetação (PRODES)?")).toEqual([]);
    expect(totaisSobPedidoDeTaxa(totXtot, "Deputados com maior patrimônio autorizam mais proposições e representam municípios de maior PIB per capita?")).toEqual([]);
    expect(alertaDeEscala(totXtot, "")).toBe(false);
  });
  test("T15-3: total cru contra taxa conta como alerta de escala (o lembrete deixa de pedir o r)", () => {
    const sql = `WITH d AS (SELECT id_municipio, COUNT(DISTINCT sobrenome) as qtd FROM s GROUP BY 1),
      p AS (SELECT id_municipio, SUM(pib) / NULLIF(SUM(populacao), 0) as pib_per_capita FROM t GROUP BY 1)
      SELECT corr(d.qtd, p.pib_per_capita) as r, COUNT(*) as n FROM d JOIN p ON d.id_municipio = p.id_municipio`;
    expect(alertaDeEscala(sql)).toBe(true);
  });

  test("dataset sem tabela lista as tabelas dele (br_ibge_populacao: 8 sessões)", () => {
    expect(sugestao("br_ibge_populacao")).toContain("br_ibge_populacao.municipio");
    const v = portao("SELECT id_municipio, populacao FROM br_ibge_populacao WHERE ano = 2021");
    expect(v.ok).toBe(false);
    expect(v.erro).toContain("br_ibge_populacao.municipio");
  });
  test("tabela errada de dataset certo lista as do dataset, não as do Censo", () => {
    expect(sugestao("br_ibge_populacao.municipios")).toContain("br_ibge_populacao.municipio");
  });
  test("T07-1: dataset com órgão errado sugere o certo (br_me_sicor → br_bcb_sicor)", () => {
    expect(sugestao("br_me_sicor.microdados")).toContain("br_bcb_sicor");
  });
  test("T07-2: CTE com erro de grafia aponta a CTE definida", () => {
    const v = portao(`WITH estban_agencias AS (SELECT id_municipio, SUM(agencias_processadas) AS total FROM br_bcb_estban.municipio WHERE ano = 2020 AND mes = 12 GROUP BY 1)
      SELECT e.total, COUNT(*) AS n FROM estban_agencies e GROUP BY 1`);
    expect(v.ok).toBe(false);
    expect(v.erro).toContain("você definiu a CTE 'estban_agencias'");
  });
  test("nome sem tabela e sem CTE parecida continua pedindo dataset.tabela", () => {
    const v = portao("WITH base AS (SELECT 1 AS x) SELECT x, COUNT(*) AS n FROM tabela_que_nao_existe GROUP BY 1");
    expect(v.ok).toBe(false);
    expect(v.erro).toContain("escreva dataset.tabela");
    expect(v.erro).not.toContain("você definiu a CTE");
  });
});
