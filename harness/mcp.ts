#!/usr/bin/env bun
/**
 * Servidor MCP do harness — o espelho, com o portão embutido.
 *
 * A integração com o laço (o Pi, via pi-mcp-adapter — pi.ts) acontece aqui, e a
 * escolha central é esta: **o portão
 * é uma ferramenta, não um passo de pipeline.** Quando `consultar` rejeita uma
 * consulta, a mensagem volta ao modelo como resultado da ferramenta, e o laço
 * agêntico a usa para tentar de novo. O reparo deixa de ser código meu e
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
import { listaDatasets, tabelasDe, colunasDe, resolveDataset, COLUNAS_PARTICAO, tabelaPrincipal } from "./catalogo.ts";
import {
  portao, checaExplain, alertasDeSanidade, faixasCitadas,
  juncoesSemPonte, mensagemSemPonte, assinaturaJuncao, sugestao, semComentarios, repara, NOTA_AMOSTRA,
  perguntaDePesquisa, checaRanking, extraiN, fonteTrocada,
} from "./portao.ts";
import { dicasDeJoin } from "./pontes.ts";
import { runSqlSsh } from "./beelink.ts";
import { capRows } from "./sqlguard.ts";
import { textoFaixa } from "./anos.ts";
import { inservivel } from "./catalogo.ts";
import { metrica, listaMetricas } from "./metricas.ts";
import { descreve, tabelaTexto, dicaMunicipio, dicaColunaInexistente } from "./formato.ts";
import { faltando } from "./recortes.ts";
import { garanteValores } from "./valores.ts";
import { notaTabela, notaColuna, calculosDaTabela } from "./semantica.ts";
import { colunasDe as colunas } from "./catalogo.ts";

const tabelasDaSql = (sql: string) =>
  [...new Set([...sql.matchAll(/\b(?:FROM|JOIN)\s+([a-z_][\w]*\.[a-z_][\w]*)/gi)].map((m) => m[1]!.toLowerCase()))]
    .filter((t) => colunas(t));
const colunasCitadas = (sql: string, tabela: string) =>
  (colunas(tabela) ?? []).map((c) => c.name).filter((n) => new RegExp(`\\b${n}\\b`, "i").test(sql));

const servidor = new Server(
  { name: "rodado-harness", version: "1.0.0" },
  { capabilities: { tools: {} } },
);

/**
 * harness_tasks.md B12 — o post-mortem da pergunta de 5 fontes que rodou 40 min
 * e morreu sem resposta, presa 38x na mesma junção inexistente. Duas coisas
 * que aquele caso mostrou faltar, e que só fazem sentido com estado por
 * pergunta (um processo mcp.ts = uma pergunta = um `pi --print`,
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
/** SQL que rodou e devolveu linha — é contra ela que o recorte da pergunta é conferido. */
const executadas: string[] = [];
const PERGUNTA = Bun.env.HARNESS_PERGUNTA ?? "";
/** Relação entre variáveis em muitos municípios — cobra medida sobre todos, com n. */
const PESQUISA = perguntaDePesquisa(PERGUNTA);
/** A mesma consulta, só com outro LIMIT: medido rodando 3x seguidas sem mudar nada. */
const jaRodadas = new Set<string>();
/** Tabelas cuja nota e cálculo verificado o modelo já viu nesta pergunta. */
const semanticaVista = new Set<string>();
const semLimite = (s: string) => s.replace(/\blimit\s+\d+/gi, "").replace(/\s+/g, " ").trim().toLowerCase();

const FERRAMENTAS = [
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
      "Colunas, tipos e o significado dos códigos de uma tabela, mais as pontes de join já " +
      "conferidas para ela. Em tabela larga, use filtro para listar só as colunas com aquele trecho no nome.",
    inputSchema: {
      type: "object",
      properties: {
        tabela: { type: "string", description: "ex.: br_ms_sim.microdados" },
        filtro: { type: "string", description: "opcional, ex.: matricula" },
      },
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
    if (!ds) return erro(`Dataset '${arg.dataset}' não existe. Os nomes estão no CATÁLOGO do system prompt.`);
    const linhas = tabelasDe(ds).map((t) => {
      const cols = colunasDe(`${ds}.${t.tabela}`) ?? [];
      const part = cols.filter((c) => (COLUNAS_PARTICAO as readonly string[]).includes(c.name.toLowerCase()));
      return `${ds}.${t.tabela}  ${t.linhas.toLocaleString("pt-BR")} linhas` +
             (part.length ? `  particionada por: ${part.map((c) => c.name).join(", ")}` : "") +
             textoFaixa(`${ds}.${t.tabela}`) +
             (inservivel(`${ds}.${t.tabela}`) ? "  ⚠ NÃO USE — " + inservivel(`${ds}.${t.tabela}`) : "");
    });
    // A tabela principal vem descrita junto: dispensa o turno seguinte de
    // descrever_tabela, que acontecia em quase toda pergunta.
    const principal = tabelaPrincipal(ds);
    if (principal) {
      const cols = colunasDe(principal)!;
      await garanteValores(principal, cols);
      semanticaVista.add(principal);
      const dicas = dicasDeJoin([principal]);
      linhas.push("", `Tabela principal, já descrita (as outras: descrever_tabela):`,
        descreve(principal, cols, textoFaixa(principal), "", PERGUNTA) + (dicas ? `\n\n${dicas}` : ""));
    }
    return texto(linhas.join("\n"));
  }

  if (name === "descrever_tabela") {
    const cols = colunasDe(arg.tabela ?? "");
    if (!cols) return erro(`Tabela '${arg.tabela}' não existe.${sugestao(arg.tabela ?? "")} Chame listar_tabelas do dataset.`);
    await garanteValores(arg.tabela!, cols);
    semanticaVista.add(arg.tabela!.toLowerCase());
    const dicas = dicasDeJoin([arg.tabela!]);
    return texto(descreve(arg.tabela!, cols, textoFaixa(arg.tabela!), arg.filtro ?? "", PERGUNTA) + (dicas ? `\n\n${dicas}` : ""));
  }

  if (name === "definicao_de_calculo") {
    if (!arg.nome) return texto(listaMetricas());
    const m = metrica(arg.nome);
    return m ? texto(m) : erro(
      `Não há definição verificada para '${arg.nome}'. Disponíveis:\n${listaMetricas()}`);
  }

  if (name === "consultar") {
    let sql = semComentarios(arg.sql ?? "").trim();

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

    // O portão. A rejeição vira resultado de ferramenta — é assim que o laço
    // agêntico vira o mecanismo de reparo, sem código de retry meu.
    const original = sql;
    const reparo = repara(original);
    sql = reparo.sql;
    const v = portao(sql);
    if (!v.ok) return erro(`REJEITADA (${v.camada}): ${v.erro}`);
    if (PESQUISA) {
      const vr = checaRanking(sql);
      if (!vr.ok) return erro(`REJEITADA (${vr.camada}): ${vr.erro}`);
    }

    const ex = await checaExplain(sql, runSqlSsh);
    if (!ex.ok) {
      // O reparo quebrou a consulta (ex.: COUNT(*) numa projeção sem GROUP BY):
      // volta a rejeição original, que ensina o conserto certo.
      // Só o COUNT(*) inserido pode ser a causa; LIMIT e tabela principal não
      // quebram SQL válida, então ali o erro do DuckDB é o problema de verdade.
      if (reparo.notas.includes(NOTA_AMOSTRA)) {
        const semN = repara(original, { amostra: false });
        const ex2 = await checaExplain(semN.sql, runSqlSsh);
        if (ex2.ok) {
          const v0 = portao(semN.sql);
          if (!v0.ok) return erro(`REJEITADA (${v0.camada}): ${v0.erro}`);
        }
      }
      const tabs = tabelasDaSql(sql).map((ref) => ({ ref, cols: (colunas(ref) ?? []).map((c) => c.name) }));
      return erro(`REJEITADA (explain): ${ex.erro}${dicaColunaInexistente(ex.erro ?? "", tabs)}`);
    }

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
        "A consulta rodou e devolveu ZERO linhas: algum filtro (WHERE, HAVING ou JOIN) não casou " +
        "com nenhum valor real. Confira os valores com SELECT DISTINCT na coluna filtrada " +
        "(códigos são texto: '2', não 2 nem 'Rural') e o tipo das duas pontas do join." +
        (faixas ? ` Faixa de anos das tabelas citadas: ${faixas}.` : " Chame listar_tabelas para ver a faixa de anos."),
      ];
      // harness_tasks.md B12: quando a junção nem tem ponte conhecida, a mensagem
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
    executadas.push(sql);
    const alertas = alertasDeSanidade(sql, capado.rows);
    if (reparo.notas.length) alertas.unshift(`Ajustei a consulta antes de rodar: ${reparo.notas.join("; ")}.`);
    // Medido 2026-09-23: o modelo foi direto ao consultar, sem descrever_tabela,
    // e contou todos os vínculos da RAIS (186.571) em vez dos ativos em 31/12
    // (142.490) — a nota e o cálculo verificado só apareciam na descrição.
    // Na 1ª consulta a uma tabela não descrita, eles vêm junto do resultado.
    for (const ref of tabelasDaSql(sql)) {
      if (semanticaVista.has(ref)) continue;
      semanticaVista.add(ref);
      const partes = [notaTabela(ref), ...calculosDaTabela(ref).map((c) => `cálculo verificado: ${c}`),
        ...colunasCitadas(sql, ref).map((c) => { const n = notaColuna(ref, c); return n ? `${c}: ${n}` : ""; })].filter(Boolean);
      if (partes.length) alertas.push(`Sobre ${ref} (confira se a consulta respeita): ${partes.join(" · ")}`);
    }
    // O recorte da pergunta (ano, estado, bioma) que nenhuma SQL aplicou até
    // aqui: antes era checado num turno à parte (revisar_resposta, 151 chamadas
    // e nenhuma rejeição); agora vai junto do resultado que o modelo vai usar.
    if (PERGUNTA && /\b(COUNT|SUM|AVG|MIN|MAX)\s*\(|\bGROUP\s+BY\b/i.test(sql)) {
      const sem = faltando(PERGUNTA, executadas);
      if (sem.length) {
        alertas.push(`A pergunta pede ${sem.map((r) => r.rotulo).join(", ")}, e nenhuma consulta até aqui filtrou por isso. ` +
          `Se este resultado é a resposta, refaça aplicando o recorte (ex.: no WHERE); se o dado desse recorte não existe, diga isso na resposta.`);
      }
    }
    if (jaRodadas.has(semLimite(sql))) {
      alertas.push("Esta consulta já rodou nesta pergunta (só o LIMIT mudou) e o resultado é o mesmo. " +
        "Se o número parece errado, o problema está na lógica — junção que multiplica linhas, filtro, nível de agregação —, não no LIMIT.");
    }
    jaRodadas.add(semLimite(sql));
    // Agregado sobre nada: 1 linha com n=0 ou tudo NULL é o "zero linhas" disfarçado.
    const unica = capado.rows.length === 1 ? (capado.rows[0] as Record<string, unknown>) : undefined;
    const agregado = /\b(COUNT|SUM|AVG|MIN|MAX)\s*\(/i.test(sql) && !/\bGROUP\s+BY\b/i.test(sql);
    if (agregado && unica && Object.values(unica).every((v) => v === null || v === 0 || v === "0")) {
      alertas.push("A agregação não achou nenhum registro (n=0 ou tudo NULL): algum filtro não casou com valor real. " +
        "Confira os valores com SELECT DISTINCT na coluna filtrada antes de responder.");
    }
    // Medido 2026-09-24, caso 6 da rodada B2: a SQL tinha `COUNT(*) AS n` sete
    // vezes e a prosa não citou nenhuma. Numa pergunta de pesquisa o n é quanto
    // da amostra a conclusão cobre — sem ele na resposta, ninguém confere o join.
    // B14, medido 2026-09-25: com o lembrete do n, 44/50 respostas citaram o n,
    // e só 8/50 o coeficiente — a prosa dizia "correlação positiva fraca" sem o
    // número. O que não se pede não vem; o r entra no mesmo lembrete.
    const nomes = Object.keys(capado.rows[0] ?? {}).map((k) => k.toLowerCase());
    const temN = nomes.includes("n");
    const coef = Object.keys(capado.rows[0] ?? {}).filter((k) => /^(r|rho|corr\w*|correla\w*|r_\w+)$/i.test(k));
    if (PESQUISA && (temN || coef.length)) {
      const n = extraiN(capado.rows as Record<string, unknown>[]);
      const pedeN = temN
        ? "o n — quantos municípios entraram na medida" +
          (n !== undefined && capado.rows.length === 1 ? ` (aqui, n=${n})` : ", somando os grupos se houver mais de um")
        : "";
      const pedeR = coef.length
        ? `o coeficiente como número, com duas casas (${coef.map((k) => `${k}=${(capado.rows[0] as Record<string, unknown>)[k]}`).join(", ")})`
        : "";
      alertas.push(`Se este resultado sustenta a resposta, escreva nela ${[pedeR, pedeN].filter(Boolean).join(" e ")}. ` +
        `"Correlação fraca" sem o número, ou conclusão sem o tamanho da amostra, não dá para conferir.`);
    }
    // Pergunta direta que nomeia uma fonte, respondida com outra (CAGED 2019
    // pela RAIS, holdout3 2026-09-25). Pesquisa cruza fontes por desenho: fica fora.
    if (PERGUNTA && !PESQUISA) {
      const troca = fonteTrocada(PERGUNTA, sql);
      if (troca) alertas.push(troca);
    }
    const municipio = dicaMunicipio(capado.rows as Record<string, unknown>[]);
    if (municipio) alertas.push(municipio);
    const prefixo = alertas.length ? alertas.map((a) => `⚠ ${a}`).join("\n") + "\n\n" : "";
    return texto(prefixo + tabelaTexto(capado));
  }

  return erro(`Ferramenta desconhecida: ${name}`);
});

await servidor.connect(new StdioServerTransport());
