/**
 * O laço — as 9 etapas, da pergunta em pt-BR ao número conferido.
 *
 * O modelo é chamado em quatro pontos curtos (datasets, tabelas, sql, prosa).
 * Escolher tabela candidata, montar schema, validar e executar é código: são as
 * partes onde um erro é caro e o determinismo é barato.
 *
 * As rejeições do portão voltam ao modelo como próxima mensagem — é onde um
 * modelo pequeno se sai bem, porque o erro é mecânico (coluna que não existe,
 * partição faltando) e a mensagem já diz o conserto.
 */
import { montaPrefixo } from "./prefixo.ts";
import { pergunta as chama } from "./modelo.ts";
import { portao, checaExplain } from "./portao.ts";
import { runSqlSsh } from "./beelink.ts";
import { colunasDe, tabelasDe, resolveDataset, type Coluna } from "./catalogo.ts";
import { dicasDeJoin } from "./pontes.ts";
import type { Caso } from "./casos.ts";

export interface Passo { etapa: string; detalhe: string; segundos?: number }

export interface Resultado {
  sql?: string;
  linhas?: Record<string, unknown>[];
  /** o n que a consulta devolveu — a impressão digital do join */
  n?: number;
  /** avisos da etapa de sanidade: número que passou pela ordem de grandeza esperada */
  alertas?: string[];
  prosa?: string;
  /** a prosa citava tabela do espelho e teve a citação apagada à força —
   *  a reescrita pedida ao modelo não bastou. Sinal para revisão, não erro. */
  prosaSaneada?: boolean;
  erro?: string;
  tentativas: number;
  passos: Passo[];
  prefiladosMax: number;
}

const MAX_TENTATIVAS = 4;
/** Consulta multi-CTE de verdade é grande — algumas passam de 1.000 tokens.
 *  Cortada no meio ela vira erro
 *  de coluna fantasma no portão e queima uma tentativa à toa. */
const TETO_SQL = 1800;
const TETO_COLUNAS = 25;

/** Termos da pergunta, para ranquear colunas. */
function termos(s: string): Set<string> {
  return new Set(
    s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "")
      .split(/[^a-z0-9_]+/).filter((w) => w.length > 3),
  );
}

/**
 * Schema capado. `br_mjsp_sisdepen` tem 3.957 colunas numa tabela só — 124k
 * tokens, quatro vezes o contexto inteiro. Listar tudo foi a causa raiz de um
 * estouro de prompt registrado no branch ask-web; aqui as colunas são ranqueadas
 * pela pergunta e cortadas, com a contagem do que ficou de fora para o modelo
 * saber que há mais.
 */
function montaDDL(tabelas: string[], q: string): string {
  const t = termos(q);
  const linhas: string[] = [];
  for (const id of tabelas) {
    const cols = colunasDe(id);
    if (!cols) continue;
    const pontuada = cols.map((c: Coluna) => {
      const nome = c.name.toLowerCase();
      let p = 0;
      for (const w of t) if (nome.includes(w) || w.includes(nome)) p += 2;
      if (["ano", "mes", "sigla_uf", "id_municipio"].includes(nome)) p += 3; // partição/join primeiro
      return { c, p };
    }).sort((a, b) => b.p - a.p);
    const mostra = pontuada.slice(0, TETO_COLUNAS);
    const corte = cols.length - mostra.length;
    linhas.push(
      `${id}: ${mostra.map((x) => `${x.c.name}:${x.c.type}`).join(" ")}` +
      (corte > 0 ? ` … +${corte} colunas` : ""),
    );
  }
  return linhas.join("\n");
}

const soLista = (s: string) =>
  s.split(/[,\n]/).map((x) => x.trim().replace(/^[-*\d.\s]+/, "")).filter(Boolean);

/** Tira cerca de markdown que o modelo às vezes põe apesar da instrução. */
const limpaSql = (s: string) =>
  s.replace(/```(?:sql)?\s*/gi, "").replace(/```/g, "").trim();

/**
 * Item 3 do backlog: a convenção de `pages/analises/results/` é citar o
 * ÓRGÃO de origem do dado, nunca a tabela nem a ferramenta —
 * `br_ibge_pib.municipio` na prosa final é exatamente o que ela proíbe, e hoje
 * nenhuma resposta gerada sai publicável sem edição à mão. A instrução sozinha
 * (no prompt da etapa 9, abaixo) é do tipo que o modelo obedece na maioria das
 * vezes; isto é a metade que transforma "maioria" em "todas".
 */
const REF_TABELA = /\bbr_[a-z_]+\.[a-z_]+\b/;

/** `undefined` = a prosa não cita tabela. Caso contrário, a mensagem de
 *  reparo — mesmo padrão das camadas do portão: diz o que consertar. */
export function checaProsa(texto: string): string | undefined {
  const m = texto.match(REF_TABELA);
  if (!m) return undefined;
  return `A prosa cita "${m[0]}" — nome de tabela do espelho, não texto para o leitor final. ` +
    `Reescreva citando o ÓRGÃO de origem do dado (ex.: "segundo o Censo do IBGE", ` +
    `"segundo a RAIS, do Ministério do Trabalho"), nunca a tabela nem a ferramenta.`;
}

/**
 * Rede de segurança para quando a reescrita (uma tentativa, como o portão de
 * SQL) ainda falha: em vez de publicar a tabela mesmo assim, apaga a citação.
 * Silêncio é o lado certo de errar aqui — perder uma frase de atribuição é
 * menos grave que vazar `br_ms_sim.microdados` num relatório.
 */
export function saneiaProsa(texto: string): { texto: string; saneada: boolean } {
  if (!REF_TABELA.test(texto)) return { texto, saneada: false };
  return { texto: texto.replace(new RegExp(REF_TABELA, "g"), "a fonte do espelho"), saneada: true };
}

export async function roda(q: string, exemplos: Caso[] = []): Promise<Resultado> {
  const sistema = montaPrefixo(exemplos);
  const passos: Passo[] = [];
  let prefiladosMax = 0;

  const perguntar = async (msg: string, maxTokens = 200) => {
    const r = await chama(sistema, msg, { maxTokens });
    prefiladosMax = Math.max(prefiladosMax, r.prefilados);
    return r;
  };

  // 1 · datasets
  let r = await perguntar(`ETAPA datasets\nPergunta: ${q}`, 80);
  const datasets = soLista(r.texto).map((d) => resolveDataset(d)).filter((d): d is string => !!d);
  passos.push({ etapa: "datasets", detalhe: datasets.join(", "), segundos: r.segundos });
  if (!datasets.length) return { erro: "nenhum dataset resolvido", tentativas: 0, passos, prefiladosMax };

  // 2 · tabelas candidatas — determinístico
  const candidatas = datasets.flatMap((d) => tabelasDe(d).map((t) => `${d}.${t.tabela}`));
  passos.push({ etapa: "candidatas", detalhe: `${candidatas.length} tabelas` });
  if (!candidatas.length) return { erro: "datasets sem tabela", tentativas: 0, passos, prefiladosMax };

  // 3 · o modelo escolhe entre as candidatas
  r = await perguntar(
    `ETAPA tabelas\nPergunta: ${q}\nTabelas disponíveis:\n${candidatas.join("\n")}\n\n` +
    `Escolha desta lista as tabelas necessárias. Responda só com os nomes dataset.tabela ` +
    `separados por vírgula, copiados exatamente da lista.`, 120);
  // Casamento tolerante: o modelo às vezes devolve só o nome da tabela, sem o
  // dataset. Aceita quando isso identifica UMA candidata; ambíguo é descartado.
  const escolhidas = [...new Set(soLista(r.texto).map((t) => {
    if (candidatas.includes(t)) return t;
    const iguais = candidatas.filter((c) => c.endsWith(`.${t}`) || c === `br_${t}`);
    return iguais.length === 1 ? iguais[0]! : null;
  }).filter((t): t is string => !!t))];
  passos.push({ etapa: "tabelas", detalhe: escolhidas.join(", "), segundos: r.segundos });
  if (!escolhidas.length) return { erro: "nenhuma tabela válida escolhida", tentativas: 0, passos, prefiladosMax };

  // 4 · schema — determinístico, capado
  const ddl = montaDDL(escolhidas, q);

  // 5-7 · SQL, portão, execução, com reparo
  //
  // Cada chamada ao modelo é INDEPENDENTE — ele não lembra nada da anterior.
  // A primeira versão mandava só "foi rejeitada: X, corrija", e o modelo
  // respondia, com razão, que não tinha recebido consulta nenhuma. O prompt de
  // reparo tem que carregar o contexto inteiro de volta: pergunta, schema,
  // pontes, a SQL rejeitada e o motivo.
  const dicas = dicasDeJoin(escolhidas);

  const promptSql = (rejeitada?: string, motivo?: string) => {
    const base =
      `ETAPA sql\nPergunta: ${q}\n\nSchema das tabelas escolhidas:\n${ddl}\n` +
      (dicas ? `\n${dicas}\n` : "") +
      `\nEscreva UMA consulta DuckDB que responda à pergunta. Agregue (COUNT, AVG, corr) ` +
      `em vez de listar linhas.\n` +
      `OBRIGATÓRIO: inclua no SELECT final uma coluna \`COUNT(*) AS n\` com o tamanho da ` +
      `amostra. Correlação ou média sem o n não é resultado reportável.`;
    if (!rejeitada) {
      return `${base}\nResponda APENAS com a consulta SQL. Comece com SELECT ou WITH. ` +
             `Não repita as etapas anteriores, não escreva "ETAPA", não use markdown.`;
    }
    return `${base}\n\nA consulta abaixo foi rejeitada:\n${rejeitada}\n\nMotivo: ${motivo}\n\n` +
           `Reescreva a consulta inteira, corrigida. Responda APENAS com a SQL, ` +
           `começando por SELECT ou WITH.`;
  };

  let msg = promptSql();
  let tentativas = 0;

  while (tentativas < MAX_TENTATIVAS) {
    tentativas++;
    r = await perguntar(msg, TETO_SQL);
    const sql = limpaSql(r.texto);
    passos.push({ etapa: `sql#${tentativas}`, detalhe: sql.slice(0, 160), segundos: r.segundos });

    // Truncamento não é erro de SQL — é orçamento. Mandar a metade de uma
    // consulta para o portão produz "coluna inexistente: id_" (o pedaço do
    // identificador cortado) e gasta uma tentativa num erro que o modelo não
    // cometeu.
    if (r.truncada) {
      passos.push({ etapa: `truncada#${tentativas}`, detalhe: `cortada em ${TETO_SQL} tokens` });
      msg = promptSql() + `\n\nA tentativa anterior foi cortada por tamanho. ` +
        `Escreva uma consulta MAIS CURTA: menos CTEs, menos colunas no SELECT.`;
      continue;
    }

    const v = portao(sql);
    if (!v.ok) {
      passos.push({ etapa: `portão#${tentativas}`, detalhe: `[${v.camada}] ${v.erro}` });
      msg = promptSql(sql, v.erro);
      continue;
    }

    const ex = await checaExplain(sql, runSqlSsh);
    if (!ex.ok) {
      passos.push({ etapa: `explain#${tentativas}`, detalhe: (ex.erro ?? "").slice(0, 140) });
      msg = promptSql(sql, ex.erro);
      continue;
    }

    const res = await runSqlSsh(sql);
    if (res.error) {
      passos.push({ etapa: `execução#${tentativas}`, detalhe: res.error.slice(0, 140) });
      msg = promptSql(sql, res.error);
      continue;
    }

    const linhas = res.rows ?? [];
    passos.push({ etapa: "execução", detalhe: `${linhas.length} linha(s)` });

    // 8 · sanidade. O n é a impressão digital do join: juntar RAIS × SIM × Censo
    // por município com os filtros certos dá um número específico, e qualquer
    // erro de tabela, chave ou partição dá outro. Vem da coluna chamada `n`,
    // exigida no prompt — pegar "o primeiro número da linha" apanhava o
    // coeficiente de correlação e comparava laranja com maçã.
    let n: number | undefined;
    const prim = linhas[0];
    if (prim) {
      const chave = Object.keys(prim).find((k) => k.toLowerCase() === "n");
      if (chave !== undefined) n = Number(prim[chave]);
    }
    if (n === undefined && linhas.length > 1) n = linhas.length;

    // n = 0, ou toda métrica nula, significa que o join não casou nada. A
    // consulta é válida e o resultado é vazio — o pior caso, porque sem esta
    // checagem a etapa 9 escreve prosa confiante sobre coisa nenhuma. Volta
    // para reparo, e o motivo mais comum vai no prompt: as duas pontas da chave
    // com tipo ou formato diferente (id_municipio é VARCHAR com zero à esquerda).
    const soNulos = prim !== undefined &&
      Object.entries(prim).every(([k, v]) => k.toLowerCase() === "n" || v === null);
    if ((n === 0 || soNulos) && tentativas < MAX_TENTATIVAS) {
      passos.push({ etapa: `vazio#${tentativas}`, detalhe: `n=${n}, join não casou` });
      msg = promptSql(sql,
        `a consulta rodou mas devolveu n=${n} — o join não casou nenhuma linha. ` +
        `Verifique: (a) as duas pontas da chave têm o mesmo tipo? id_municipio é ` +
        `VARCHAR de 7 dígitos com zero à esquerda, não número; (b) os filtros de ano ` +
        `das duas tabelas se sobrepõem?; (c) a coluna de junção existe nas duas.`);
      continue;
    }

    const alertas: string[] = [];
    if (n !== undefined && n > 5570 && /municipio/i.test(sql)) {
      alertas.push(`n=${n} passa dos 5.570 municípios do país — o join provavelmente duplicou linhas`);
    }
    for (const [k, v] of Object.entries(prim ?? {})) {
      if (/^(corr|r|correlacao)/i.test(k) && typeof v === "number" && Math.abs(v) > 0.95) {
        alertas.push(`${k}=${v} é alto demais para dado social — suspeite de auto-correlação`);
      }
    }
    if (alertas.length) passos.push({ etapa: "sanidade", detalhe: alertas.join("; ") });

    // 9 · prosa
    const amostra = JSON.stringify(linhas.slice(0, 12));
    const promptProsa =
      `ETAPA prosa\nPergunta: ${q}\nResultado da consulta: ${amostra}\n\n` +
      `Escreva um parágrafo em português respondendo à pergunta com estes números. ` +
      `Cite o órgão de origem do dado, nunca a ferramenta nem o nome da tabela.`;
    let p = await perguntar(promptProsa, 400);
    passos.push({ etapa: "prosa", detalhe: `${p.texto.length} chars`, segundos: p.segundos });

    // A checagem que transforma a instrução acima de "maioria das vezes" em
    // "sempre": uma reescrita, e se ainda falhar, a citação é apagada à força
    // (saneiaProsa) em vez de publicada — ver o comentário da função.
    let erroProsa = checaProsa(p.texto);
    if (erroProsa) {
      passos.push({ etapa: "prosa#rejeitada", detalhe: erroProsa });
      p = await perguntar(
        `${promptProsa}\n\nA resposta anterior foi:\n${p.texto}\n\n${erroProsa}`,
        400);
      passos.push({ etapa: "prosa#2", detalhe: `${p.texto.length} chars`, segundos: p.segundos });
      erroProsa = checaProsa(p.texto);
    }
    const { texto: prosaFinal, saneada } = erroProsa ? saneiaProsa(p.texto) : { texto: p.texto, saneada: false };
    if (saneada) passos.push({ etapa: "prosa#saneada", detalhe: "citação de tabela apagada à força após a reescrita ainda falhar" });

    return {
      sql, linhas, n, alertas, prosa: prosaFinal.trim(), prosaSaneada: saneada || undefined,
      tentativas, passos, prefiladosMax,
    };
  }

  return { erro: `não passou do portão em ${MAX_TENTATIVAS} tentativas`, tentativas, passos, prefiladosMax };
}
