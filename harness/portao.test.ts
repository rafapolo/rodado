/**
 * Os casos deste arquivo não são hipotéticos: cada um é uma SQL que o Gemma 4
 * escreveu de verdade no beelink em 2026-09-01, ou um erro que o pipeline do
 * ask-web apanhou em produção. O portão existe por causa deles.
 */
import { expect, test, describe } from "bun:test";
import {
  portao, checaCitacaoTabela, alertasDeSanidade,
  juncoesSemPonte, mensagemSemPonte, assinaturaJuncao, checaExecutouConsulta,
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
  // zero e o zero passou por resposta. backlog.md item 6.
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
  // regras.md, tarefa 1: a regra existia só no laco.ts (pipeline aposentado).
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

describe("checaCitacaoTabela — a prosa cita o órgão, não a ferramenta", () => {
  // backlog.md item 3: a convenção de pages/analises/results/ é citar o
  // órgão de origem, nunca a tabela — checaCitacaoTabela é a metade que a
  // ferramenta revisar_resposta (mcp.ts) usa para transformar a instrução do
  // system prompt em rejeição de verdade.
  test("rejeita quando a prosa cita dataset.tabela", () => {
    const v = checaCitacaoTabela(
      "Segundo br_ms_sim.microdados, houve 789 óbitos por suicídio no RJ em 2020.",
    );
    expect(v.ok).toBe(false);
    expect(v.camada).toBe("citacao");
    expect(v.erro).toContain("br_ms_sim.microdados");
  });
  test("pega mais de um prefixo do espelho (world_/us_, não só br_)", () => {
    const v = checaCitacaoTabela("Fonte: world_olympedia_olympics.resultados.");
    expect(v.ok).toBe(false);
  });
  test("prosa citando o órgão, sem nome de tabela, passa", () => {
    const v = checaCitacaoTabela(
      "Segundo o Ministério da Saúde (Sistema de Informação sobre Mortalidade), " +
      "houve 789 óbitos por suicídio no RJ em 2020.",
    );
    expect(v.ok).toBe(true);
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

describe("juncoesSemPonte — backlog.md item 12, a pergunta de 5 fontes que morreu presa", () => {
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

describe("checaExecutouConsulta — a resposta sem SQL nenhuma (467 vs 789)", () => {
  // Achado ao vivo 2026-09-04, testando THINKING=1: o modelo explorou schema,
  // nunca chamou `consultar`, e `revisar_resposta` aprovou 467 óbitos
  // inventados (o real, já verificado várias vezes neste projeto, é 789).
  test("rejeita quando nenhuma consulta com resultado rodou ainda", () => {
    const v = checaExecutouConsulta(0);
    expect(v.ok).toBe(false);
    expect(v.camada).toBe("sem-consulta");
    expect(v.erro).toContain("consultar");
  });
  test("aprova depois de pelo menos uma consulta com linha real", () => {
    expect(checaExecutouConsulta(1).ok).toBe(true);
    expect(checaExecutouConsulta(5).ok).toBe(true);
  });
});

describe("camada inservível — a tabela que responde zero e parece certa", () => {
  // Os dois casos que motivaram esta camada — br_ibama_embargos (497 mil linhas
  // de string vazia) e br_seeg (redundante) — foram REMOVIDOS do espelho em
  // 2026-09-02, depois que o levantamento os expôs. `aposentados()` (catalogo.ts)
  // varre TODAS as `provenance_notes` por `Substitui \`X\`` e intercepta X pelo
  // NOME, mesmo já fora do catálogo — desfecho melhor que "tabela não existe"
  // (camada `tabela`): a mensagem explica O QUE substituiu e por quê, em vez de
  // just "não achei". Mesmo mecanismo da varredura de operacao.md tarefa 5.
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
  // `br_seeg`" (confirmado 2026-09-03, varredura de operacao.md tarefa 5), então
  // aposentados() não tem como saber que ele foi removido. Pior: colunasDe()
  // lê de docs/context/basedosdados-schema.json (gerado por scripts/gera_schemas.py,
  // fora do escopo do harness), que não foi regenerado desde a remoção — então
  // br_seeg.emissoes_municipais ainda PASSA o portão (camadas tabela/coluna
  // acham a referência válida), mesmo com harness/dados/catalogo.json (fonte
  // viva, via `catalogo.ts --atualiza`) confirmando que o dataset não existe
  // mais. Não é um bug do portão — é uma dependência de arquivo desatualizado
  // fora do escopo deste subsistema. Fecha só regenerando basedosdados-schema.json.
  test("aceita as que os substituíram", () => {
    expect(portao("SELECT COUNT(*) FROM br_ibama_embargos_novo.termo_embargo").ok).toBe(true);
  });
  test("não bloqueia o diretório canônico de municípios", () => {
    const v = portao("SELECT COUNT(*) FROM br_bd_diretorios_brasil.municipio");
    expect(v.camada).not.toBe("inservivel");
  });
});
