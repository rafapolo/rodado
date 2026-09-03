#!/usr/bin/env bun
/**
 * Servidor MCP do harness — o espelho, com o portão embutido.
 *
 * A integração com o dsh acontece aqui, e a escolha central é esta: **o portão
 * é uma ferramenta, não um passo de pipeline.** Quando `consultar` rejeita uma
 * consulta, a mensagem volta ao modelo como resultado da ferramenta, e o laço
 * agêntico do dsh a usa para tentar de novo. O reparo deixa de ser código meu e
 * passa a ser o que o harness já sabe fazer — com o log de sessão junto, que é
 * o que permite defender um número publicado depois.
 *
 * As descrições das ferramentas são curtas de propósito. As do mcp_server.py
 * somam 3.482 tokens de nuance escrita para o Claude; um 26B em q4 não aproveita
 * essa prosa e ela ainda dilui o prompt. Aqui cada uma diz o que faz e a regra
 * que faz a chamada ser rejeitada — nada mais.
 */
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { listaDatasets, tabelasDe, colunasDe, resolveDataset } from "./catalogo.ts";
import {
  portao, checaExplain, alertasDeSanidade, faixasCitadas, checaCitacaoTabela,
  juncoesSemPonte, mensagemSemPonte, assinaturaJuncao,
} from "./portao.ts";
import { dicasDeJoin } from "./pontes.ts";
import { runSqlSsh } from "./beelink.ts";
import { capRows } from "./sqlguard.ts";
import { textoFaixa } from "./anos.ts";
import { inservivel } from "./catalogo.ts";
import { metrica, listaMetricas } from "./metricas.ts";

const servidor = new Server(
  { name: "rodado-harness", version: "1.0.0" },
  { capabilities: { tools: {} } },
);

/**
 * backlog.md item 12 — o post-mortem da pergunta de 5 fontes que rodou 40 min
 * e morreu sem resposta, presa 38x na mesma junção inexistente. Duas coisas
 * que aquele caso mostrou faltar, e que só fazem sentido com estado por
 * pergunta (um processo mcp.ts = uma pergunta = um `dsh --profile headless`,
 * ver pergunte.ts — o Map nasce e morre com ela, nunca vaza entre perguntas):
 *
 *  - disjuntor de repetição: a MESMA junção (mesmo FROM/JOIN/ON, só o resto
 *    mudando) tentada `LIMIAR_REPETICAO` vezes sem achar linha escala a
 *    mensagem de zero-linhas — ela para de soar como "você errou o tipo,
 *    tenta de novo" e passa a dizer "pare de tentar isso";
 *  - orçamento de consultas: um teto bem mais apertado que os 40 min de
 *    parede do `pergunte.ts` (`HARNESS_TIMEOUT_MS`) — se a pergunta não
 *    convergiu em `ORCAMENTO_CONSULTAS` chamadas de `consultar`, é sinal de
 *    que não vai convergir sozinha, e o corte aqui é imediato (sem ida ao
 *    beelink), não silencioso 25+ minutos depois.
 */
const tentativasPorJuncao = new Map<string, number>();
const LIMIAR_REPETICAO = Number(Bun.env.HARNESS_LIMIAR_REPETICAO ?? 3);
const ORCAMENTO_CONSULTAS = Number(Bun.env.HARNESS_ORCAMENTO_CONSULTAS ?? 30);
let totalConsultas = 0;

const FERRAMENTAS = [
  {
    name: "listar_datasets",
    description:
      "Lista os 212 datasets do espelho. Use para descobrir onde está o assunto da pergunta.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "listar_tabelas",
    description:
      "Lista as tabelas de um dataset, com quantas linhas cada uma tem e a faixa de anos disponível.",
    inputSchema: {
      type: "object",
      properties: { dataset: { type: "string", description: "ex.: br_ms_sim" } },
      required: ["dataset"],
    },
  },
  {
    name: "descrever_tabela",
    description:
      "Colunas e tipos de uma tabela, mais as pontes de join já conferidas para ela.",
    inputSchema: {
      type: "object",
      properties: { tabela: { type: "string", description: "ex.: br_ms_sim.microdados" } },
      required: ["tabela"],
    },
  },
  {
    name: "definicao_de_calculo",
    description:
      "Devolve a definição VERIFICADA de um cálculo nomeado (pib per capita, população, " +
      "saldo do CAGED...) com a expressão SQL exata. CHAME ANTES de escrever à mão " +
      "qualquer taxa, média ou razão: a mesma pergunta tem mais de uma leitura aritmética " +
      "e as respostas divergem. Sem argumento, lista os cálculos disponíveis.",
    inputSchema: {
      type: "object",
      properties: { nome: { type: "string", description: "ex.: pib per capita" } },
    },
  },
  {
    name: "consultar",
    description:
      "Executa uma consulta DuckDB read-only no espelho. REGRAS: tabela grande exige filtro " +
      "de partição (ano, sigla_uf); escreva sempre dataset.tabela; consulta sem agregação " +
      "precisa de LIMIT; CID-10 é guardado sem ponto, use substr(col,1,3) para faixa. " +
      "Se a consulta for rejeitada, a resposta diz o que corrigir — reescreva e chame de novo.",
    inputSchema: {
      type: "object",
      properties: { sql: { type: "string", description: "SELECT ou WITH" } },
      required: ["sql"],
    },
  },
  {
    name: "revisar_resposta",
    description:
      "Confere o parágrafo final ANTES de entregá-lo: rejeita se citar tabela ou dataset " +
      "(ex.: br_ms_sim.microdados) em vez do órgão de origem. Chame com o parágrafo pronto " +
      "— só responda ao usuário depois que esta ferramenta aprovar.",
    inputSchema: {
      type: "object",
      properties: { texto: { type: "string", description: "o parágrafo final, em português" } },
      required: ["texto"],
    },
  },
];

servidor.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: FERRAMENTAS }));

const texto = (s: string) => ({ content: [{ type: "text" as const, text: s }] });
const erro = (s: string) => ({ content: [{ type: "text" as const, text: s }], isError: true });

servidor.setRequestHandler(CallToolRequestSchema, async (req) => {
  const { name, arguments: a } = req.params;
  const arg = (a ?? {}) as Record<string, string>;

  if (name === "listar_datasets") return texto(listaDatasets().join("\n"));

  if (name === "listar_tabelas") {
    const ds = resolveDataset(arg.dataset ?? "");
    if (!ds) return erro(`Dataset '${arg.dataset}' não existe. Chame listar_datasets.`);
    const linhas = tabelasDe(ds).map((t) => {
      const cols = colunasDe(`${ds}.${t.tabela}`) ?? [];
      const part = cols.filter((c) => ["ano", "mes", "sigla_uf"].includes(c.name.toLowerCase()));
      return `${ds}.${t.tabela}  ${t.linhas.toLocaleString("pt-BR")} linhas` +
             (part.length ? `  particionada por: ${part.map((c) => c.name).join(", ")}` : "") +
             textoFaixa(`${ds}.${t.tabela}`) +
             (inservivel(`${ds}.${t.tabela}`) ? "  ⚠ NÃO USE — " + inservivel(`${ds}.${t.tabela}`) : "");
    });
    return texto(linhas.join("\n"));
  }

  if (name === "descrever_tabela") {
    const cols = colunasDe(arg.tabela ?? "");
    if (!cols) return erro(`Tabela '${arg.tabela}' não existe. Chame listar_tabelas do dataset.`);
    const dicas = dicasDeJoin([arg.tabela!]);
    return texto(
      `${arg.tabela} — ${cols.length} colunas${textoFaixa(arg.tabela!)}\n` +
      cols.map((c) => `  ${c.name}: ${c.type}`).join("\n") +
      (dicas ? `\n\n${dicas}` : ""),
    );
  }

  if (name === "definicao_de_calculo") {
    if (!arg.nome) return texto(listaMetricas());
    const m = metrica(arg.nome);
    return m ? texto(m) : erro(
      `Não há definição verificada para '${arg.nome}'. Disponíveis:\n${listaMetricas()}`);
  }

  if (name === "consultar") {
    const sql = (arg.sql ?? "").trim();

    totalConsultas++;
    if (totalConsultas > ORCAMENTO_CONSULTAS) {
      return erro(
        `Orçamento de ${ORCAMENTO_CONSULTAS} consultas nesta pergunta esgotado (esta seria a ` +
        `${totalConsultas}ª). ${totalConsultas - 1} tentativas sem chegar numa resposta é sinal ` +
        `de que a estratégia atual não vai convergir sozinha, não de que falta mais uma tentativa. ` +
        `Pare de consultar agora: responda com o que já apurou, ou diga explicitamente que não ` +
        `conseguiu responder e por quê — não invente número pra fechar a pergunta.`,
      );
    }

    // O portão. A rejeição vira resultado de ferramenta — é assim que o laço do
    // dsh vira o mecanismo de reparo, sem código de retry meu.
    const v = portao(sql);
    if (!v.ok) return erro(`REJEITADA (${v.camada}): ${v.erro}`);

    const ex = await checaExplain(sql, runSqlSsh);
    if (!ex.ok) return erro(`REJEITADA (explain): ${ex.erro}`);

    const r = await runSqlSsh(sql);
    if (r.error) return erro(`Falhou: ${r.error}`);

    const capado = capRows(r.rows ?? [], 200);
    if (!capado.rows.length) {
      const faixas = faixasCitadas(sql);
      const semPonte = juncoesSemPonte(sql);

      const assinatura = assinaturaJuncao(sql);
      const repeticoes = (tentativasPorJuncao.get(assinatura) ?? 0) + 1;
      tentativasPorJuncao.set(assinatura, repeticoes);

      const partes = [
        "A consulta rodou e devolveu ZERO linhas — o join não casou nada, ou o filtro " +
        "de ano não tem dado. Confira o tipo das duas pontas da chave." +
        (faixas ? ` Faixa de anos das tabelas citadas: ${faixas}.` : " Chame listar_tabelas para ver a faixa de anos."),
      ];
      // backlog.md item 12: quando a junção nem tem ponte conhecida, a mensagem
      // acima soa como "você errou o tipo" e não é isso — é que a chave pode
      // nem existir. Diz isso explicitamente em vez de convidar a tentar de novo.
      if (semPonte.length) partes.push(mensagemSemPonte(semPonte));
      // E quando é a MESMA junção repetindo, nem a mensagem mais clara ajuda —
      // o que falta é parar, não explicar melhor.
      if (repeticoes >= LIMIAR_REPETICAO) {
        partes.push(
          `⚠ Esta MESMA junção (mesmo FROM/JOIN/ON — só o resto da consulta mudou) já ` +
          `devolveu zero linhas ${repeticoes} vezes nesta pergunta. Pare de tentar variações ` +
          `dela: troque a tabela ou a coluna de junção por algo estruturalmente diferente, ` +
          `ou conclua que esta pergunta não tem resposta direta com os dados disponíveis e ` +
          `diga isso — repetir não vai fazer a linha aparecer.`,
        );
      }
      return erro(partes.join("\n\n"));
    }
    // Alertas de sanidade (grupo reportado como total, join que duplicou linha,
    // correlação suspeita) grudados ANTES dos dados, no mesmo texto — nenhum
    // rejeita, mas o modelo só corrige o que vê.
    const alertas = alertasDeSanidade(sql, capado.rows);
    const prefixo = alertas.length ? alertas.map((a) => `⚠ ${a}`).join("\n") + "\n\n" : "";
    return texto(prefixo + JSON.stringify(capado));
  }

  if (name === "revisar_resposta") {
    const v = checaCitacaoTabela(arg.texto ?? "");
    return v.ok
      ? texto("Aprovado — pode responder ao usuário com este texto.")
      : erro(`REJEITADA (${v.camada}): ${v.erro}`);
  }

  return erro(`Ferramenta desconhecida: ${name}`);
});

await servidor.connect(new StdioServerTransport());
