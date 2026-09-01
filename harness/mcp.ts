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
import { portao, checaExplain } from "./portao.ts";
import { dicasDeJoin } from "./pontes.ts";
import { runSqlSsh } from "./beelink.ts";
import { capRows } from "./sqlguard.ts";
import { textoFaixa } from "./anos.ts";

const servidor = new Server(
  { name: "rodado-harness", version: "1.0.0" },
  { capabilities: { tools: {} } },
);

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
             textoFaixa(`${ds}.${t.tabela}`);
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

  if (name === "consultar") {
    const sql = (arg.sql ?? "").trim();

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
      return erro(
        "A consulta rodou e devolveu ZERO linhas — o join não casou nada, ou o filtro " +
        "de ano não tem dado. Confira a faixa de anos com listar_tabelas e o tipo das " +
        "duas pontas da chave.",
      );
    }
    return texto(JSON.stringify(capado));
  }

  return erro(`Ferramenta desconhecida: ${name}`);
});

await servidor.connect(new StdioServerTransport());
