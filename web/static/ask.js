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
 * Confere as TABELAS citadas no SQL contra as que foram oferecidas.
 *
 * O erro mais caro de um modelo pequeno aqui não é coluna inventada, é escrever
 * `FROM br_rj_isp_estatisticas_seguranca` — o nome do DATASET sem a tabela.
 * Isso vira "Catalog Error" no beelink, queima as duas tentativas de reparo e a
 * pergunta termina sem resposta. Pegar no cliente custa zero e o erro devolvido
 * já diz o nome completo certo.
 */
export function validarTabelas(sql, tabelas) {
  const ok = new Set(tabelas.map((t) => t.id));
  const datasets = new Map();
  for (const t of tabelas) {
    const ds = t.id.split(".")[0];
    (datasets.get(ds) ?? datasets.set(ds, []).get(ds)).push(t.id);
  }

  const citadas = new Set();
  for (const [, ref] of sql.matchAll(/\b(?:FROM|JOIN)\s+([A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)?)/gi)) {
    citadas.add(ref);
  }

  const ruins = [];
  for (const ref of citadas) {
    if (ok.has(ref)) continue;
    if (ref.includes("(") || /^read_parquet$/i.test(ref)) continue;
    const sugestao = datasets.get(ref);              // dataset solto, sem tabela
    ruins.push({ ref, sugestao: sugestao ?? [...ok] });
  }
  return ruins.length ? ruins : null;
}

/**
 * Conserta `FROM dataset` (sem a tabela) trocando pela tabela mais bem
 * ranqueada daquele dataset entre as oferecidas.
 *
 * Medido: pedir ao 1,5B que corrija não funciona — ele repete o mesmo erro nas
 * duas tentativas e a pergunta morre sem resposta. A troca é mecânica e
 * inequívoca (o dataset está no top-K, e as tabelas vêm ordenadas por score),
 * então fazer é melhor que pedir.
 */
export function corrigirTabelas(sql, tabelas) {
  const melhorDoDataset = new Map();          // tabelas já vêm ordenadas por score
  for (const t of tabelas) {
    const ds = t.id.split(".")[0];
    if (!melhorDoDataset.has(ds)) melhorDoDataset.set(ds, t.id);
  }
  const trocas = [];
  const novo = sql.replace(/\b(FROM|JOIN)\s+([A-Za-z_][\w]*)(?![\w.])/gi, (m, kw, ref) => {
    const alvo = melhorDoDataset.get(ref);
    if (!alvo) return m;
    trocas.push(`${ref} → ${alvo}`);
    return `${kw} ${alvo}`;
  });
  return trocas.length ? { sql: novo, trocas } : null;
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

  // `dataset.tabela` casa com o mesmo padrão de `alias.coluna` — sem tirar as
  // referências de tabela, `br_ms_sim.microdados` vira "coluna microdados
  // inexistente" e dispara um reparo que não tinha o que reparar.
  const semTabelas = tabelas.reduce((acc, t) => acc.split(t.id).join(" "), sql);

  const suspeitas = new Set();
  for (const [, col] of semTabelas.matchAll(/\b[A-Za-z_][\w]*\.([A-Za-z_][\w]*)\b/g)) {
    const c = col.toLowerCase();
    if (!conhecidas.has(c) && !RESERVADAS.has(c) && !/^\d/.test(c)) suspeitas.add(col);
  }
  if (!suspeitas.size) return null;
  return { invalidas: [...suspeitas] };
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

    // O WebLLM REJEITA a promise (não devolve {erro}) quando o prompt passa do
    // teto de contexto do wasm — sem este try/catch essa falha é uma exceção
    // não tratada que mata a pergunta inteira, sem chance de reparo nem
    // mensagem legível na UI.
    let g;
    try {
      g = await llm.gerarSQL(prompt);
    } catch (e) {
      g = { erro: `falha ao gerar SQL: ${e.message}` };
    }
    if (g.erro) return emitir("erro", { mensagem: g.erro, fase: "geracao" });

    // `FROM dataset` sem a tabela: conserta em vez de pedir ao modelo, que
    // repete o erro. Não gasta tentativa de reparo.
    const conserto = corrigirTabelas(g.sql, tabelas);
    if (conserto) {
      emitir("conserto", { trocas: conserto.trocas });
      g.sql = conserto.sql;
    }

    const ruins = validarColunas(g.sql, tabelas);
    if (ruins && tentativa < MAX_REPAROS) {
      emitir("reparo", { tentativa: tentativa + 1, erro: `coluna inexistente: ${ruins.invalidas.join(", ")}`, local: true });
      // Reusa montarDDL (já ranqueado e capado a 25 col/tabela) em vez de
      // listar TODAS as colunas — tabela com 300+ colunas nessa lista sem
      // corte já estourou 11.991 tokens contra o teto de 4096 do wasm.
      prompt = `${P.SISTEMA}\n\nVocê escreveu:\n${g.sql}\n\nEssas colunas NÃO existem: ${ruins.invalidas.join(", ")}\n` +
               `As colunas que existem:\n${P.montarDDL(tabelas, colunas, pergunta)}\n\nPERGUNTA: ${pergunta}\nSQL corrigido:`;
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

    // Resultado vazio ou só nulos NÃO é resposta "zero". Deixar o modelo
    // redigir em cima disso produz "não houve mortes por arma no RJ" a partir
    // de um SUM(null) — uma afirmação falsa sobre dado público, que é a pior
    // saída possível deste sistema. Pior que não responder.
    const vazio = !r.rows?.length ||
      r.rows.every((l) => Object.values(l).every((v) => v === null || v === undefined));
    if (vazio) {
      emitir("semdado", {
        sql: g.sql,
        motivo: !r.rows?.length ? "a consulta não devolveu linha nenhuma"
                                : "a consulta devolveu apenas valores nulos",
      });
      return emitir("fim", {});
    }

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
