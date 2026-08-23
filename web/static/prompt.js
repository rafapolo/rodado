/**
 * Orçamento de prompt e Tier 1 determinístico.
 *
 * É aqui que o desenho vive ou morre: um modelo local roda com contexto curto,
 * e br_inep_censo_escolar.escola sozinha tem 455 colunas.
 */

let sem = null;
export async function carregarSemantica() {
  sem = sem ?? (await fetch("./index/semantica.json").then((r) => r.json()));
  return sem;
}

const semAcento = (s) =>
  s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim();

/**
 * Tier 1 — métrica por nome ou sinônimo EXATO, nunca por similaridade:
 * "população de SP" e "população carcerária" ficam perto no espaço vetorial e
 * querem tabelas diferentes.
 *
 * Três detalhes que custaram trabalho na versão Rust e não devem ser
 * redescobertos:
 *  1. o match mais LONGO vence — senão "pib per capita" resolve como "pib";
 *  2. isto roda ANTES do embedding (~18s → 0ms quando casa);
 *  3. sobrando QUALQUER termo não explicado, cai para o modelo — responder o
 *     agregado nacional a uma pergunta sobre municípios é errado e silencioso.
 */
export function resolverMetrica(pergunta) {
  if (!sem?.metricas) return null;
  const p = semAcento(pergunta);

  let achada = null, termo = "";
  for (const m of sem.metricas) {
    for (const nome of [m.name, ...(m.synonyms ?? [])]) {
      const n = semAcento(nome);
      if (n.length > termo.length && new RegExp(`(^|\\s)${n}(\\s|$)`).test(p)) {
        achada = m; termo = n;
      }
    }
  }
  if (!achada) return null;

  // O que sobra depois de tirar a métrica, os filtros que sabemos ler e as
  // palavras de ligação. Sobrou algo? cai pro modelo.
  const filtros = {};
  let resto = p.replace(new RegExp(`(^|\\s)${termo}(\\s|$)`), " ");

  const ano = resto.match(/\b(19|20)\d{2}\b/);
  if (ano) { filtros.ano = Number(ano[0]); resto = resto.replace(ano[0], " "); }

  const uf = resto.match(/\b(ac|al|ap|am|ba|ce|df|es|go|ma|mt|ms|mg|pa|pb|pr|pe|pi|rj|rn|rs|ro|rr|sc|sp|se|to)\b/);
  if (uf) { filtros.sigla_uf = uf[0].toUpperCase(); resto = resto.replace(uf[0], " "); }

  const RUIDO = new Set(["qual","quais","quantos","quantas","quanto","foi","foram","e","de","do","da",
    "dos","das","em","no","na","nos","nas","o","a","os","as","por","para","total","numero","o total"]);
  const sobra = resto.split(/\s+/).filter((w) => w && !RUIDO.has(w));
  if (sobra.length > 0) return { caiu: true, motivo: `termos não explicados: ${sobra.join(", ")}`, metrica: achada };

  for (const f of achada.required_filters ?? []) {
    if (!(f in filtros)) return { caiu: true, motivo: `falta o filtro obrigatório '${f}'`, metrica: achada };
  }

  const where = Object.entries(filtros)
    .map(([k, v]) => (typeof v === "number" ? `${k} = ${v}` : `${k} = '${v}'`)).join(" AND ");
  const cols = Object.keys(filtros);
  return {
    caiu: false,
    metrica: achada,
    sql: `SELECT ${cols.length ? cols.join(", ") + ", " : ""}${achada.expression} AS ${achada.name}\n` +
         `FROM ${achada.source_table}\n` + (where ? `WHERE ${where}\n` : "") +
         (cols.length ? `GROUP BY ${cols.map((_, i) => i + 1).join(", ")}` : ""),
  };
}

const PARTICOES = new Set(["ano", "mes", "sigla_uf", "id_municipio"]);

/** Ranqueia colunas: chave de join > partição > casa com a pergunta > resto. */
function ranquear(cols, pergunta, teto) {
  const p = semAcento(pergunta);
  const ff = new Set(Object.keys(sem?.false_friends ?? {}));
  const peso = (c) => {
    const n = semAcento(c.n);
    let s = 0;
    if (PARTICOES.has(c.n)) s += 100;
    if (/^(id_|cod|cnpj|cpf|sigla)/.test(c.n) && !ff.has(c.n)) s += 50;
    if (p.includes(n) && n.length > 3) s += 30;
    return s;
  };
  const ord = [...cols].sort((a, b) => peso(b) - peso(a));
  return { mostradas: ord.slice(0, teto), cortadas: Math.max(0, cols.length - teto) };
}

/** DDL enxuto das tabelas escolhidas, dentro do orçamento. */
export function montarDDL(tabelas, colunasPorTabela, pergunta, tetoColunas = 25) {
  const linhas = [];
  for (const t of tabelas) {
    const cols = colunasPorTabela[t.id] ?? [];
    const { mostradas, cortadas } = ranquear(cols, pergunta, tetoColunas);
    let l = `${t.id}: ` + mostradas.map((c) => `${c.n}:${c.t}`).join(" ");
    if (cortadas) l += ` … +${cortadas} colunas`;
    if (t.duplicada) l += `\n  -- ATENÇÃO: esta tabela devolve toda linha DUAS VEZES. Use SELECT DISTINCT.`;
    linhas.push(l);
  }
  return linhas.join("\n");
}

/** JOIN HINTS a partir das pontes — a expressão já testada no beelink. */
export function montarJoinHints(tabelas) {
  if (!sem?.pontes) return "";
  const ids = new Set(tabelas.map((t) => t.id));
  const hints = [];
  for (const [conceito, pontes] of Object.entries(sem.pontes)) {
    for (const b of pontes) {
      if (ids.has(b.table) && b.join_expr) {
        hints.push(`  ${b.table}.${b.column} → ${conceito}: ${b.join_expr}` +
                   (b.verified ? `  (conferido: ${b.verified})` : ""));
      }
    }
  }
  if (!hints.length) return "";
  return `\nJOIN HINTS — use estas expressões, não a igualdade ingênua:\n${hints.join("\n")}\n`;
}

/** false_friends que aparecem nas tabelas escolhidas. */
export function montarFalseFriends(tabelas, colunasPorTabela) {
  if (!sem?.false_friends) return "";
  const vistas = new Set();
  for (const t of tabelas) for (const c of colunasPorTabela[t.id] ?? []) {
    if (sem.false_friends[c.n]) vistas.add(c.n);
  }
  if (!vistas.size) return "";
  const l = [...vistas].map((c) => `  ${c}: ${sem.false_friends[c].reason}`);
  return `\nNUNCA use estas colunas como chave de join:\n${l.join("\n")}\n`;
}

export const SISTEMA = `Você escreve SQL DuckDB sobre o acervo rodado (dados públicos brasileiros).

REGRAS
- Responda APENAS com o SQL. Sem explicação, sem markdown, sem \`\`\`.
- Sempre qualifique a tabela: dataset.tabela. Nome solto falha.
- Filtre por ano/mes/sigla_uf/id_municipio sempre que a coluna existir — são
  colunas de partição e cortam a leitura drasticamente.
- Valores de texto estão em MINÚSCULA: cargo = 'deputado federal'.
- Use SOMENTE as colunas listadas no DDL. Não invente coluna.
- br_bd_diretorios_brasil.municipio e .uf são as tabelas canônicas de geografia;
  junte com elas para mostrar NOME em vez de código.
- Se não der para responder com as tabelas dadas, responda exatamente:
  {"error": "o motivo"}`;

export function montarPrompt(pergunta, tabelas, colunas) {
  return `${SISTEMA}\n\nTABELAS DISPONÍVEIS\n${montarDDL(tabelas, colunas, pergunta)}\n` +
         `${montarJoinHints(tabelas)}${montarFalseFriends(tabelas, colunas)}\nPERGUNTA: ${pergunta}\nSQL:`;
}
