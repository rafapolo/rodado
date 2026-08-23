/**
 * A máquina de estados. Espelha o `enum Phase` da TUI Rust, que já era a certa:
 * Input → Embedando → GerandoSQL → Validando → Executando → [Reparando] → Pronto
 */
import * as embed from "./embed.js";
import * as llm from "./llm.js";
import * as P from "./prompt.js";
import * as lexical from "./lexical.js";

const MAX_REPAROS = 2;
let colunas = null;

export async function carregarColunas(meta) {
  colunas = colunas ?? (await fetch("/index/colunas.json").then((r) => r.json()));
  if (meta) lexical.indexar(meta, colunas);   // índice lexical: em memória, instantâneo
  return colunas;
}

async function executar(sql) {
  const r = await fetch("/api/executar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sql }),
  });
  return r.json();
}

/**
 * Confere as colunas do SQL contra o schema, no navegador, antes de gastar um
 * round-trip. É a correção mais barata do laço e a falha mais comum de um
 * modelo pequeno.
 */
export function validarColunas(sql, tabelas) {
  const conhecidas = new Set();
  for (const t of tabelas) for (const c of colunas[t.id] ?? []) conhecidas.add(c.n.toLowerCase());
  if (!conhecidas.size) return null;

  const RESERVADAS = new Set(["select","from","where","group","order","by","limit","as","on","join",
    "left","right","inner","outer","full","and","or","not","in","is","null","count","sum","avg","min",
    "max","distinct","having","with","case","when","then","else","end","desc","asc","cast","varchar",
    "integer","double","date","union","all","offset","using","over","partition","round","coalesce","between"]);

  const suspeitas = new Set();
  for (const [, col] of sql.matchAll(/\b[A-Za-z_][\w]*\.([A-Za-z_][\w]*)\b/g)) {
    const c = col.toLowerCase();
    if (!conhecidas.has(c) && !RESERVADAS.has(c) && !/^\d/.test(c)) suspeitas.add(col);
  }
  if (!suspeitas.size) return null;

  const disponiveis = tabelas.map((t) =>
    `${t.id}: ${(colunas[t.id] ?? []).map((c) => c.n).join(", ")}`).join("\n");
  return { invalidas: [...suspeitas], disponiveis };
}

/**
 * @param pergunta texto em pt-BR
 * @param emitir   (evento, dados) => void  — mesmo papel do WorkerMsg da TUI
 */
export async function perguntar(pergunta, emitir) {
  // --- Tier 1: métrica nomeada, antes do embedding -------------------------
  const t1 = P.resolverMetrica(pergunta);
  if (t1 && !t1.caiu) {
    emitir("tier1", { metrica: t1.metrica.name, verificado: t1.metrica.verified });
    emitir("sql", { sql: t1.sql, origem: "métrica" });
    const r = await executar(t1.sql);
    if (r.erro) return emitir("erro", { mensagem: r.erro, fase: "execucao" });
    emitir("linhas", r);
    return emitir("fim", {});
  }
  if (t1?.caiu) emitir("tier1", { metrica: t1.metrica.name, caiu: t1.motivo });

  // --- seleção de tabelas ---------------------------------------------------
  emitir("fase", { nome: "embedando" });
  const tabelas = await embed.selecionarHibrido(pergunta, lexical, 5);
  if (!tabelas.length) {
    return emitir("erro", { mensagem: "Nenhuma tabela do acervo parece responder a isso.", fase: "selecao" });
  }
  emitir("tabelas", tabelas);

  if (!llm.pronto()) {
    return emitir("erro", {
      mensagem: "O modelo de linguagem ainda não está carregado — as tabelas acima são o que existe sobre o assunto.",
      fase: "llm",
    });
  }

  // --- geração + reparo -----------------------------------------------------
  let prompt = P.montarPrompt(pergunta, tabelas, colunas);
  for (let tentativa = 0; tentativa <= MAX_REPAROS; tentativa++) {
    emitir("fase", { nome: tentativa === 0 ? "gerando" : "reparando", tentativa });

    const g = await llm.gerarSQL(prompt);
    if (g.erro) return emitir("erro", { mensagem: g.erro, fase: "geracao" });

    const ruins = validarColunas(g.sql, tabelas);
    if (ruins && tentativa < MAX_REPAROS) {
      emitir("reparo", { tentativa: tentativa + 1, erro: `coluna inexistente: ${ruins.invalidas.join(", ")}`, local: true });
      prompt = `${P.SISTEMA}\n\nVocê escreveu:\n${g.sql}\n\nEssas colunas NÃO existem: ${ruins.invalidas.join(", ")}\n` +
               `As colunas que existem:\n${ruins.disponiveis}\n\nPERGUNTA: ${pergunta}\nSQL corrigido:`;
      continue;
    }

    emitir("sql", { sql: g.sql, origem: "modelo" });
    emitir("fase", { nome: "executando" });
    const r = await executar(g.sql);

    if (r.erro) {
      if (tentativa < MAX_REPAROS) {
        emitir("reparo", { tentativa: tentativa + 1, erro: r.erro });
        // Reusa a MESMA seleção de tabelas: a TUI re-embedava pergunta+erro+SQL
        // e acabava escolhendo tabelas diferentes da primeira passada.
        prompt = `${P.SISTEMA}\n\nTABELAS DISPONÍVEIS\n${P.montarDDL(tabelas, colunas, pergunta)}\n` +
                 `${P.montarJoinHints(tabelas)}\nEste SQL falhou:\n${g.sql}\n\nErro do DuckDB:\n${r.erro}\n\n` +
                 `PERGUNTA: ${pergunta}\nSQL corrigido:`;
        continue;
      }
      return emitir("erro", { mensagem: r.erro, fase: "execucao" });
    }

    emitir("linhas", r);
    if (r.rows?.length) {
      emitir("fase", { nome: "explicando" });
      try {
        const e = await llm.explicar(pergunta, g.sql, r.rows, r.colunas ?? []);
        if (e.resposta) emitir("prosa", { texto: e.resposta });
        if (e.grafico) emitir("grafico", e.grafico);
      } catch { /* prosa é bônus: resultado já está na tela */ }
    }
    return emitir("fim", {});
  }
}
