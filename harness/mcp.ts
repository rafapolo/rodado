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
  juncoesSemPonte, mensagemSemPonte, assinaturaJuncao, checaExecutouConsulta,
  checaDescritaAntes,
} from "./portao.ts";
import { dicasDeJoin, semColunaComum, avisoSemColunaComum, resolverJuncao } from "./pontes.ts";
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

/**
 * Achado ao vivo 2026-09-04 (testando THINKING=1): o modelo pulou `consultar`
 * inteiro e aprovou em `revisar_resposta` um número inventado (467, contra os
 * 789 reais) — pior que SQL errado, porque nem chega a tocar o beelink.
 * `checaExecutouConsulta` (portao.ts) usa este contador pra recusar qualquer
 * resposta final que não veio de dado de verdade.
 */
let consultasComResultado = 0;

/**
 * backlog.md item 12, ponto 2 — `dicasDeJoin` foi desenhada pra comparar DUAS
 * tabelas (`pontes.ts`: o aviso "JOIN — estas tabelas..." só liga com
 * `tabelas.length > 1`), mas `descrever_tabela` sempre chamava com um array de
 * um elemento só — a dica nunca disparava na prática, porque o modelo descreve
 * uma tabela por chamada. O disjuntor de repetição (abaixo) cobre o sintoma
 * DEPOIS de queimar `LIMIAR_REPETICAO` tentativas; isto cobre a causa, ANTES da
 * primeira SQL: lembra as tabelas já descritas nesta pergunta (mesmo Map de
 * módulo, mesmo ciclo de vida — nasce e morre com o processo) e passa a lista
 * inteira, não só a mais recente. Janela limitada a 6 pra não inflar o prompt
 * numa pergunta que navega muitos datasets sem relação com o join em questão.
 */
const tabelasDescritas: string[] = [];
const JANELA_TABELAS_DESCRITAS = 6;

/**
 * Curto-circuito idempotente — `tasks/ferramentas_claude_code.md`, proposta 5.
 *
 * A classe de desperdício mais cara medida no head-to-head de 2026-09-04: 5 das
 * 21 chamadas da sessão `53ac1869` re-obtiveram schema que o modelo já tinha
 * (`SELECT * … LIMIT 1` e `PRAGMA table_info` de tabelas descritas nos passos 3
 * e 8), sendo TRÊS byte-idênticas entre si. Ele não estava confuso: nada no
 * diálogo lembrava que a informação já estava em mãos.
 *
 * É o análogo do `Read` do Claude Code dizer "do NOT re-read a file you just
 * edited" — instrução que só é honesta porque o lado do servidor de fato sabe.
 * Aqui o servidor sabe, então nem precisa pedir: devolve o mesmo resultado, diz
 * que é repetição, e **não gasta a ida ao beelink**.
 *
 * Chave é a SQL normalizada só em espaço em branco — não em semântica. Duas
 * consultas diferentes que fazem a mesma coisa continuam ambas executando; o
 * alvo é a repetição literal, que é a que foi medida e a única com risco zero.
 */
const consultasFeitas = new Map<string, string>();
const normalizaSql = (s: string) => s.trim().replace(/\s+/g, " ").toLowerCase();

/** Proposta 1 do mesmo documento — ver o comentário no ponto de uso, em
 *  `consultar`. Desligada por padrão por falta de caso observado. */
const EXIGE_DESCRICAO = Bun.env.HARNESS_EXIGE_DESCRICAO === "1";

/**
 * Proposta 3 (`tasks/ferramentas_claude_code.md`) — estado que hoje só é
 * descoberto tarde: o orçamento de consultas só aparece quando estoura, e a
 * repetição de junção só falava na LIMIAR_REPETICAO-ésima vez. O que falta não
 * é mais checagem — é o mesmo estado, que já existe em memória, GRUDADO no
 * resultado desde a 1ª chamada. Não toca no prefixo (viaja no retorno, que já
 * ia voltar) e não custa turno (o modelo lê, não precisa perguntar).
 */
function estadoFooter(): string {
  const partes = [`consultas: ${totalConsultas}/${ORCAMENTO_CONSULTAS}`];
  if (tabelasDescritas.length) partes.push(`tabelas descritas: ${tabelasDescritas.join(", ")}`);
  return `[estado] ${partes.join(" · ")}`;
}

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
      "Colunas e tipos de uma tabela, mais as pontes de join já conferidas para ela. Para " +
      "montar um JOIN, descreva as duas de uma vez com 'tabelas' — a dica de junção sai na " +
      "mesma resposta. O resultado não muda dentro desta pergunta — não chame duas vezes " +
      "para a mesma tabela.",
    inputSchema: {
      type: "object",
      properties: {
        tabela: { type: "string", description: "ex.: br_ms_sim.microdados — uma só" },
        tabelas: {
          type: "array",
          items: { type: "string" },
          description: "duas ou mais — use quando o objetivo é montar JOIN entre elas",
        },
      },
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
    name: "resolver_juncao",
    description:
      "Devolve a cláusula ON pronta entre duas tabelas — chame ANTES de escrever o JOIN à " +
      "mão, sem gastar consulta. Se não houver junção documentada, diz isso claramente em " +
      "vez de deixar você descobrir por tentativa e erro.",
    inputSchema: {
      type: "object",
      properties: {
        tabela_a: { type: "string", description: "ex.: br_me_caged.microdados_movimentacao" },
        tabela_b: { type: "string", description: "ex.: br_me_rais.microdados_vinculos" },
      },
      required: ["tabela_a", "tabela_b"],
    },
  },
  {
    name: "consultar",
    description:
      "Executa uma consulta DuckDB read-only no espelho. REGRAS: tabela grande exige filtro " +
      "de partição (ano, sigla_uf); escreva sempre dataset.tabela; consulta sem agregação " +
      "precisa de LIMIT; CID-10 é guardado sem ponto, use substr(col,1,3) para faixa. " +
      "Se a consulta for rejeitada, a resposta diz o que corrigir — reescreva e chame de novo. " +
      "Não reenvie a mesma junção variando só SELECT, WHERE ou LIMIT — se voltou zero linhas, " +
      "o que precisa mudar é o ON.",
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

/**
 * Proposta 6 (`tasks/ferramentas_claude_code.md`) — argumento não declarado é
 * erro, não silêncio.
 *
 * Medido: a chamada 6 da sessão `53ac1869` foi
 * `listar_datasets({"dataset":"br_transferegov"})`. O schema não tem `dataset`,
 * o argumento foi ignorado calado e voltaram os 212 datasets — resposta grande,
 * plausível e inútil, que não corrige o modelo e ainda enche o contexto. Ele
 * queria `listar_tabelas`.
 *
 * A dica sai do próprio inventário: se outra ferramenta declara a chave que
 * veio sobrando, é quase certo que era essa a intenção.
 */
function checaArgumentos(nome: string, arg: Record<string, unknown>): string | null {
  const def = FERRAMENTAS.find((f) => f.name === nome);
  if (!def) return null;
  const aceitas = new Set(Object.keys(def.inputSchema.properties ?? {}));
  const sobrando = Object.keys(arg).filter((k) => !aceitas.has(k));
  if (!sobrando.length) return null;
  const dicas = sobrando.map((k) => {
    const outra = FERRAMENTAS.find(
      (f) => f.name !== nome && Object.keys(f.inputSchema.properties ?? {}).includes(k),
    );
    return outra ? `'${k}' (é argumento de ${outra.name} — era essa que você queria?)` : `'${k}'`;
  });
  return (
    `${nome} não aceita ${dicas.join(", ")}. ` +
    (aceitas.size ? `Aceita: ${[...aceitas].join(", ")}.` : "Não aceita argumento nenhum.")
  );
}

servidor.setRequestHandler(CallToolRequestSchema, async (req) => {
  const { name, arguments: a } = req.params;
  const arg = (a ?? {}) as Record<string, string>;

  const argRuim = checaArgumentos(name, arg);
  if (argRuim) return erro(argRuim);

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
    // Proposta 2 (tasks/ferramentas_claude_code.md): a forma plural existe pra
    // que o par que vai virar JOIN chegue descrito na MESMA chamada — dicasDeJoin
    // foi desenhada pra comparar duas tabelas, mas o modelo sempre descrevia uma
    // por vez, e a dica nunca disparava (backlog.md item 12, ponto 2). A forma
    // singular abaixo continua idêntica, como rede de segurança pra quando o
    // modelo ainda descrever uma de cada vez.
    const tabelasArg = (arg as unknown as { tabelas?: unknown }).tabelas;
    if (Array.isArray(tabelasArg) && tabelasArg.length) {
      const lista = tabelasArg.map(String);
      const blocos = lista.map((t) => {
        const cols = colunasDe(t);
        if (!cols) return `${t}: não existe. Chame listar_tabelas do dataset.`;
        const repetida = tabelasDescritas.includes(t);
        if (!repetida) {
          tabelasDescritas.push(t);
          if (tabelasDescritas.length > JANELA_TABELAS_DESCRITAS) tabelasDescritas.shift();
        }
        return (
          (repetida
            ? `(você já descreveu ${t} nesta pergunta — o schema não muda; abaixo é a ` +
              `mesma resposta.)\n\n`
            : "") +
          `${t} — ${cols.length} colunas${textoFaixa(t)}\n` +
          cols.map((c) => `  ${c.name}: ${c.type}`).join("\n")
        );
      });
      const dicas = dicasDeJoin(tabelasDescritas);
      const avisos: string[] = [];
      for (let i = 0; i < lista.length - 1; i++) {
        const a = lista[i]!, b = lista[i + 1]!;
        const colsA = colunasDe(a), colsB = colunasDe(b);
        if (!colsA || !colsB) continue;
        if (semColunaComum(a, colsA.map((c) => c.name), b, colsB.map((c) => c.name))) {
          avisos.push(avisoSemColunaComum(a, b));
        }
      }
      return texto(
        blocos.join("\n\n") +
        (dicas ? `\n\n${dicas}` : "") +
        (avisos.length ? `\n\n${avisos.join("\n")}` : ""),
      );
    }

    const cols = colunasDe(arg.tabela ?? "");
    if (!cols) return erro(`Tabela '${arg.tabela}' não existe. Chame listar_tabelas do dataset.`);
    // Proposta 5: repetir descrever_tabela é grátis em rede mas não em turno —
    // o aviso é o que impede a próxima repetição, já que o conteúdo é idêntico.
    const repetida = tabelasDescritas.includes(arg.tabela!);
    // A tabela anterior na sessão, ANTES de empurrar a atual — é o par mais
    // provável de ser o join que o modelo está investigando (descreve A,
    // depois descreve B pra montar o ON entre as duas).
    const anterior = tabelasDescritas[tabelasDescritas.length - 1];
    if (!tabelasDescritas.includes(arg.tabela!)) {
      tabelasDescritas.push(arg.tabela!);
      if (tabelasDescritas.length > JANELA_TABELAS_DESCRITAS) tabelasDescritas.shift();
    }
    const dicas = dicasDeJoin(tabelasDescritas);
    // backlog.md item 12 — a checagem que hoje só roda DEPOIS de uma SQL com
    // ON escrito voltar zero linhas (juncoesSemPonte, portao.ts), aqui roda
    // ANTES de qualquer SQL: se a tabela recém-descrita e a anterior não têm
    // nenhuma coluna com o mesmo conceito, avisa já.
    const colsAnterior = anterior && anterior !== arg.tabela ? colunasDe(anterior) : null;
    const avisoJuncao = colsAnterior && semColunaComum(
      anterior!, colsAnterior.map((c) => c.name),
      arg.tabela!, cols.map((c) => c.name),
    ) ? avisoSemColunaComum(anterior!, arg.tabela!) : "";
    return texto(
      (repetida
        ? `(você já descreveu ${arg.tabela} nesta pergunta — o schema não muda; ` +
          `abaixo é a mesma resposta. Se o que falta é ver VALOR de exemplo, ` +
          `consulte projetando as colunas que interessam.)\n\n`
        : "") +
      `${arg.tabela} — ${cols.length} colunas${textoFaixa(arg.tabela!)}\n` +
      cols.map((c) => `  ${c.name}: ${c.type}`).join("\n") +
      (dicas ? `\n\n${dicas}` : "") +
      (avisoJuncao ? `\n\n${avisoJuncao}` : ""),
    );
  }

  if (name === "definicao_de_calculo") {
    if (!arg.nome) return texto(listaMetricas());
    const m = metrica(arg.nome);
    return m ? texto(m) : erro(
      `Não há definição verificada para '${arg.nome}'. Disponíveis:\n${listaMetricas()}`);
  }

  if (name === "resolver_juncao") {
    const a = arg.tabela_a ?? "", bb = arg.tabela_b ?? "";
    const colsA = colunasDe(a), colsB = colunasDe(bb);
    if (!colsA) return erro(`Tabela '${a}' não existe. Chame listar_tabelas do dataset.`);
    if (!colsB) return erro(`Tabela '${bb}' não existe. Chame listar_tabelas do dataset.`);
    const r = resolverJuncao(a, colsA.map((c) => c.name), bb, colsB.map((c) => c.name));
    const linhas = r.joins.map((j) =>
      `  ${j.kind === "bridge" ? "[ponte]" : "[canônica]"} ${j.on}` +
      (j.verified ? `  (conferido: ${j.verified})` : ""));
    const rej = r.rejeitados.map((x) => `  ${x.coluna}: ${x.motivo}`);
    return texto(
      `${a} × ${bb}\n` +
      (linhas.length ? linhas.join("\n") : "(nenhuma junção documentada)") +
      (rej.length ? `\n\nColunas com nome igual mas significado diferente (NÃO junte por elas):\n${rej.join("\n")}` : "") +
      (r.avisos.length ? `\n\n${r.avisos.join("\n")}` : ""),
    );
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

    // Proposta 1 — DESLIGADA por padrão, de propósito. A justificativa original
    // (economizar as idas ao beelink dos chutes de nome) não sobreviveu à
    // releitura dos resultados no log: tabela inexistente já é rejeitada de
    // graça pela camada `tabela`. Sobra o caso de tabela que existe e nunca foi
    // olhada — real, mas SEM falha observada atrás, e a regra da casa é que
    // camada especulativa não entra: uma camada errada rejeita trabalho legítimo
    // tão calada quanto o bug que ela queria pegar. Implementada e testada
    // (`checaDescritaAntes`, 5 casos), esperando seu próprio caso medido.
    if (EXIGE_DESCRICAO) {
      const d = checaDescritaAntes(sql, tabelasDescritas);
      if (!d.ok) return erro(`REJEITADA (${d.camada}): ${d.erro}`);
    }

    // Proposta 5 — repetição literal não vai ao beelink. Devolve o que já
    // devolveu, dizendo que é o mesmo, pra romper o ciclo em vez de alimentá-lo.
    const chave = normalizaSql(sql);
    const anterior = consultasFeitas.get(chave);
    if (anterior !== undefined) {
      return texto(
        `(consulta IDÊNTICA a uma que você já rodou nesta pergunta — não foi ` +
        `executada de novo, o resultado é o mesmo. Se ele não respondeu o que ` +
        `você precisa, mude a consulta: outra coluna, outro recorte, outra ` +
        `tabela — repetir não muda o resultado.)\n\n${anterior}\n\n${estadoFooter()}`,
      );
    }

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
      // Proposta 3: o placar da MESMA junção aparece desde a 2ª tentativa, não
      // só na LIMIAR_REPETICAO-ésima — "×2" já é sinal de reincidência, esperar
      // a 3ª pra falar é deixar o modelo repetir de olhos fechados.
      if (repeticoes > 1) {
        partes.push(
          `Esta MESMA junção (mesmo FROM/JOIN/ON — só o resto da consulta mudou) já ` +
          `devolveu zero linhas ${repeticoes}x nesta pergunta.`,
        );
      }
      // E quando é a MESMA junção repetindo demais, nem a mensagem mais clara
      // ajuda — o que falta é parar, não explicar melhor.
      if (repeticoes >= LIMIAR_REPETICAO) {
        partes.push(
          `⚠ Pare de tentar variações desta junção: troque a tabela ou a coluna de junção ` +
          `por algo estruturalmente diferente, ou conclua que esta pergunta não tem resposta ` +
          `direta com os dados disponíveis e diga isso — repetir não vai fazer a linha aparecer.`,
        );
      }
      partes.push(estadoFooter());
      return erro(partes.join("\n\n"));
    }
    // Chegou aqui com linha de verdade — a resposta final poderá se apoiar em
    // dado real. checaExecutouConsulta (revisar_resposta) só aprova depois disto.
    consultasComResultado++;
    // Alertas de sanidade (grupo reportado como total, join que duplicou linha,
    // correlação suspeita) grudados ANTES dos dados, no mesmo texto — nenhum
    // rejeita, mas o modelo só corrige o que vê.
    const alertas = alertasDeSanidade(sql, capado.rows);
    const prefixo = alertas.length ? alertas.map((a) => `⚠ ${a}`).join("\n") + "\n\n" : "";
    const saida = prefixo + JSON.stringify(capado);
    consultasFeitas.set(chave, saida);
    return texto(`${saida}\n\n${estadoFooter()}`);
  }

  if (name === "revisar_resposta") {
    // backlog.md item 12/13: achado ao vivo — o modelo aprovou um número
    // inventado (467 contra 789 reais) sem nunca ter chamado `consultar`.
    // Grounding vem ANTES da checagem de citação: sem dado real, a forma da
    // prosa não importa.
    const g = checaExecutouConsulta(consultasComResultado);
    if (!g.ok) return erro(`REJEITADA (${g.camada}): ${g.erro}`);

    const v = checaCitacaoTabela(arg.texto ?? "");
    return v.ok
      ? texto("Aprovado — pode responder ao usuário com este texto.")
      : erro(`REJEITADA (${v.camada}): ${v.erro}`);
  }

  return erro(`Ferramenta desconhecida: ${name}`);
});

await servidor.connect(new StdioServerTransport());
