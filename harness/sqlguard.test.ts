import { expect, test, describe } from "bun:test";
import { checkReadOnly, stripSqlComments, capRows, RUN_SQL_MAX_CHARS, DESCRIBE_MAX_COLS } from "./sqlguard.ts";

// Os casos abaixo são os de tests/test_mcp_server.py, um a um. São duas
// implementações do mesmo firewall (Python no MCP, TS aqui); repetir os casos
// é o que impede as duas de derivarem.

describe("checkReadOnly aceita", () => {
  for (const sql of [
    "SELECT 1",
    "select * from br_tse_eleicoes.candidatos limit 1",
    "  WITH x AS (SELECT 1) SELECT * FROM x",
    "SELECT 1;",
    "SELECT 1 -- trailing comment",
    "/* leading comment */ SELECT 1",
  ]) test(sql, () => expect(checkReadOnly(sql)).toBeNull());
});

describe("checkReadOnly recusa", () => {
  for (const sql of [
    "", "   ",
    "DROP TABLE foo",
    "INSERT INTO foo VALUES (1)",
    "SELECT 1; SELECT 2",
    "SELECT 1; DROP TABLE foo",
    "ATTACH 'x.db'",
    "PRAGMA table_info('x')",
    "COPY (SELECT 1) TO 'out.csv'",
  ]) test(JSON.stringify(sql), () => expect(checkReadOnly(sql)).not.toBeNull());
});

test("recusa keyword escondida no segundo statement", () => {
  const err = checkReadOnly("SELECT 1; DELETE FROM foo");
  expect(err).not.toBeNull();
  expect(err!.toLowerCase()).toContain("statement");
});

test("stripSqlComments tira linha e bloco", () => {
  const s = stripSqlComments("SELECT 1 -- comment\n/* block */ FROM x");
  expect(s).not.toContain("comment");
  expect(s).not.toContain("block");
});

test("capRows deixa passar resultado pequeno", () => {
  const rows = Array.from({ length: 5 }, (_, n) => ({ n }));
  const out = capRows(rows, 500);
  expect(out.rows).toEqual(rows);
  expect(out.truncated).toBe(false);
});

test("capRows corta por número de linhas", () => {
  const out = capRows(Array.from({ length: 50 }, (_, n) => ({ n })), 10);
  expect(out.returned).toBe(10);
  expect(out.total).toBe(50);
  expect(out.truncated).toBe(true);
  // Achado em tasks/ferramentas_claude_code.md: o corte por linhas também
  // precisa ensinar — só o de tamanho tinha `note` antes deste teste.
  expect(out.note).toBeDefined();
  expect(out.note).toContain("50");
});

test("capRows corta linha larga por tamanho", () => {
  // ~4 KB por linha: largo o bastante pra 500 linhas estourarem, estreito o
  // bastante pra muitas ainda caberem — o corte cai numa fronteira real.
  const wide = Array.from({ length: 500 }, () =>
    Object.fromEntries(Array.from({ length: 40 }, (_, i) => [`col_${i}`, "x".repeat(100)])));
  const out = capRows(wide, 500);
  expect(out.truncated).toBe(true);
  expect(out.returned!).toBeLessThan(500);
  expect(JSON.stringify(out.rows).length).toBeLessThanOrEqual(RUN_SQL_MAX_CHARS);
  expect(out.note).toBeDefined();
});

test("capRows devolve nomes de coluna quando uma linha só já estoura", () => {
  const monster = [Object.fromEntries(
    Array.from({ length: 1000 }, (_, i) => [`col_${i}`, "x".repeat(500)]))];
  const out = capRows(monster, 500);
  expect(out.rows).toEqual([]);
  expect(out.columnsTotal).toBe(1000);
  expect(out.columns!.length).toBe(DESCRIBE_MAX_COLS);
  expect(JSON.stringify(out).length).toBeLessThan(RUN_SQL_MAX_CHARS);
});
