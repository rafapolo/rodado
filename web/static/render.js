/** Tabela, SQL e prosa. */
const el = (t, cls, txt) => { const e = document.createElement(t); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };

const MONETARIA = /(valor|preco|preço|montante|receita|despesa|gasto|pib|renda|salario|salário|remuneracao|remuneração|patrimonio|patrimônio|bem|divida|dívida|custo|orcamento|orçamento)/i;

/**
 * Formatação BRL em JS, não no SQL. O system prompt original mandava o modelo
 * escrever um REGEXP_REPLACE de três linhas (DuckDB usa RE2, sem lookahead) —
 * caro em tokens e frágil num modelo pequeno. Aqui o tipo e o nome da coluna
 * bastam.
 */
export function formatar(valor, coluna) {
  if (valor === null || valor === undefined) return "—";
  if (typeof valor === "number") {
    if (MONETARIA.test(coluna)) {
      return "R$ " + valor.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
    return Number.isInteger(valor) ? valor.toLocaleString("pt-BR")
      : valor.toLocaleString("pt-BR", { maximumFractionDigits: 4 });
  }
  return String(valor);
}

export function tabela(destino, colunas, linhas) {
  destino.innerHTML = "";
  if (!linhas?.length) { destino.append(el("p", "vazio", "A consulta não devolveu nenhuma linha.")); return; }
  const cols = colunas?.length ? colunas : Object.keys(linhas[0]);
  const wrap = el("div", "rolagem-h");
  const t = el("table");
  const thead = el("thead"), tr = el("tr");
  for (const c of cols) tr.append(el("th", null, c));
  thead.append(tr); t.append(thead);
  const tb = el("tbody");
  for (const r of linhas) {
    const l = el("tr");
    for (const c of cols) {
      const v = r[c];
      const td = el("td", typeof v === "number" ? "num" : null, formatar(v, c));
      l.append(td);
    }
    tb.append(l);
  }
  t.append(tb); wrap.append(t); destino.append(wrap);
}

const PALAVRAS = /\b(SELECT|FROM|WHERE|GROUP BY|ORDER BY|LIMIT|JOIN|LEFT|RIGHT|INNER|ON|AS|WITH|AND|OR|NOT|IN|DISTINCT|COUNT|SUM|AVG|MIN|MAX|CASE|WHEN|THEN|ELSE|END|DESC|ASC|HAVING|OFFSET|UNION|ALL)\b/g;

export function sql(destino, texto, origem) {
  destino.innerHTML = "";
  const pre = el("pre", "sql");
  pre.innerHTML = texto
    .replace(/[&<>]/g, (m) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[m]))
    .replace(PALAVRAS, '<b>$1</b>')
    .replace(/'([^']*)'/g, "<i>'$1'</i>");
  destino.append(pre);
  if (origem) destino.append(el("p", "origem", origem === "métrica"
    ? "SQL de uma métrica definida no acervo — não passou pelo modelo."
    : "SQL escrito pelo modelo. Confira antes de citar o número."));
}
