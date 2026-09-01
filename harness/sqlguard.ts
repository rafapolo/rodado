/**
 * SQL firewall — porte fiel de `_check_read_only` e `_cap_rows` do mcp_server.py.
 *
 * O navegador monta o SQL, mas quem executa é o servidor, então o servidor não
 * confia nele: a mesma checagem que o MCP faz roda aqui antes de qualquer ssh.
 *
 * Esta é a segunda cópia da regra (a primeira é Python, em mcp_server.py:220).
 * A duplicação é deliberada — as duas superfícies são independentes — e o que
 * impede a deriva é sqlguard.test.ts, que repete os casos de
 * tests/test_mcp_server.py um a um.
 */

/** Teto de caracteres do resultado serializado. Espelha MCP_RUN_SQL_MAX_CHARS. */
export const RUN_SQL_MAX_CHARS = Number(Bun.env.ASK_WEB_MAX_CHARS ?? 60_000);
/** Quantas colunas listar quando nem uma linha cabe. Espelha MCP_DESCRIBE_MAX_COLS. */
export const DESCRIBE_MAX_COLS = Number(Bun.env.ASK_WEB_MAX_COLS ?? 150);

const DISALLOWED_KEYWORDS = [
  "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER", "ATTACH",
  "DETACH", "PRAGMA", "SET", "CALL", "INSTALL", "LOAD", "COPY", "EXPORT",
  "IMPORT", "VACUUM", "CHECKPOINT", "GRANT", "REVOKE", "TRUNCATE",
  "REPLACE", "MERGE",
] as const;

export function stripSqlComments(sql: string): string {
  return sql.replace(/--[^\n]*/g, "").replace(/\/\*[\s\S]*?\*\//g, "");
}

/** Devolve a mensagem de erro se o SQL não for um SELECT/WITH único, ou null. */
export function checkReadOnly(sql: string): string | null {
  const stripped = stripSqlComments(sql).trim();
  if (!stripped) return "Consulta vazia.";

  const body = (stripped.endsWith(";") ? stripped.slice(0, -1) : stripped).trim();
  if (body.includes(";")) {
    return "Múltiplos statements não são permitidos — read-only por desenho.";
  }

  const firstToken = (body.match(/^[A-Za-z_]+/)?.[0] ?? "").toUpperCase();
  if (firstToken !== "SELECT" && firstToken !== "WITH") {
    return `Statement do tipo '${firstToken || "?"}' não é permitido — read-only por ` +
           `desenho. Só SELECT/WITH são aceitos.`;
  }

  const upper = body.toUpperCase();
  for (const kw of DISALLOWED_KEYWORDS) {
    if (new RegExp(`\\b${kw}\\b`).test(upper)) {
      return `A palavra-chave '${kw}' não é permitida — read-only por desenho.`;
    }
  }
  return null;
}

export type Row = Record<string, unknown>;

export interface CappedResult {
  rows: Row[];
  truncated: boolean;
  returned?: number;
  total?: number;
  columns?: string[];
  columnsTotal?: number;
  note?: string;
}

/**
 * Limita o resultado por número de linhas **e** por bytes serializados.
 *
 * O cap de linhas sozinho não limita o payload: a largura de linha varia em
 * ordens de grandeza neste catálogo — `SELECT *` em
 * br_inep_censo_escolar.escola são 455 colunas. Quando nem UMA linha cabe no
 * orçamento, nenhuma volta: devolvemos os nomes das colunas, que é o que o
 * chamador precisa para reescrever a consulta com projeção explícita.
 */
export function capRows(rows: Row[], maxRows: number): CappedResult {
  if (!Array.isArray(rows)) return { rows, truncated: false };

  const total = rows.length;
  let kept = rows.slice(0, maxRows);
  // JSON.stringify não põe espaço depois dos separadores (json.dumps põe), então
  // esta medida é alguns por cento menor que a do Python. O orçamento é uma
  // barreira de segurança, não um contrato entre as duas — a diferença é irrelevante.
  const size = (rs: Row[]) => JSON.stringify(rs).length;

  let cappedBy: "rows" | "size" | null = total > maxRows ? "rows" : null;

  const first = kept[0];
  if (first !== undefined && size([first]) > RUN_SQL_MAX_CHARS) {
    const names = Object.keys(first);
    const shown = names.slice(0, DESCRIBE_MAX_COLS);
    return {
      rows: [],
      truncated: true,
      returned: 0,
      total,
      columns: shown,
      columnsTotal: names.length,
      note:
        `Uma única linha passa de ${RUN_SQL_MAX_CHARS} caracteres, então nenhuma ` +
        `é devolvida — inundaria a resposta. A linha tem ${names.length} coluna(s)` +
        (names.length > shown.length ? ` (as ${shown.length} primeiras listadas)` : "") +
        ". Refaça a consulta escolhendo só as colunas que precisa, ou agregue no SQL.",
    };
  }

  if (kept.length > 0 && size(kept) > RUN_SQL_MAX_CHARS) {
    let lo = 1, hi = kept.length;
    while (lo < hi) {
      const mid = Math.floor((lo + hi + 1) / 2);
      if (size(kept.slice(0, mid)) <= RUN_SQL_MAX_CHARS) lo = mid;
      else hi = mid - 1;
    }
    kept = kept.slice(0, lo);
    cappedBy = "size";
  }

  if (cappedBy === null) return { rows: kept, truncated: false };

  const out: CappedResult = { rows: kept, truncated: true, returned: kept.length, total };
  if (cappedBy === "size") {
    out.note =
      `Truncado em ${kept.length} de ${total} linha(s) para caber em ` +
      `${RUN_SQL_MAX_CHARS} caracteres — as linhas são largas. Escolha as colunas ` +
      `em vez de *, ou agregue no SQL.`;
  }
  return out;
}
