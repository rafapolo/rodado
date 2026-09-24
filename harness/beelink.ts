/**
 * Executor de SQL — porte de `_run_sql_ssh` e `_rewrite_to_read_parquet`
 * (mcp_server.py:246 e :378).
 *
 * beelink é a ÚNICA fonte de dado do projeto: nunca S3, nunca BigQuery, nunca
 * o endpoint db.xn--2dk.xyz. O caminho canônico é ~/rodado.
 */
import { readFileSync } from "node:fs";

const HOST = Bun.env.BEELINK_HOST ?? "beelink";
const DUCKDB_BIN = Bun.env.ASK_WEB_DUCKDB_BIN ?? "~/bin/duckdb";
const DUCKDB_PATH = Bun.env.ASK_WEB_DUCKDB_PATH ?? "~/rodado/basedosdados.duckdb";
const MEMORIA = Bun.env.HARNESS_DUCKDB_MEM ?? "3GB";
const THREADS = Number(Bun.env.HARNESS_DUCKDB_THREADS ?? 4);
const TIMEOUT_MS = Number(Bun.env.ASK_WEB_TIMEOUT_MS ?? 120_000);

export interface SqlResult {
  rows?: Record<string, unknown>[];
  error?: string;
}

/** Limpa o que a CLI do DuckDB escreve no stderr em toda invocação. */
function cleanStderr(raw: string): string {
  return raw
    .replace(/\x1b\[[0-9;]*m/g, "")                       // códigos ANSI de cor
    .replace(/^.*Loading resources from.*\n?/gm, "")      // banner do ~/.duckdbrc
    .trim();
}

/**
 * O "Corrupt database file: computed checksum … does not match" que o DuckDB
 * devolve às vezes. Visto 2x em 2026-09-24 (blocos 18198 e 18230, os de
 * metadados no fim do arquivo) e nunca reproduzido: o arquivo não muda desde
 * 13/09, o sha256 lido direto do SSD (dd iflag=direct) bate em toda leitura, a
 * cópia lê inteira sem erro e ~80 consultas repetidas, 4 em paralelo e com a
 * config do harness, passaram todas. Nas duas vezes a MESMA consulta passou na
 * tentativa seguinte. É transitório (a máquina roda com ~2 GB livres ao lado do
 * llama-server); repetir resolve, e o modelo não gasta um turno lendo um erro
 * de infraestrutura como se fosse da SQL dele — foi o que tirou o filtro certo
 * da consulta de matrículas na 1ª pergunta do Pi com a lição.
 */
export function ehChecksumTransitorio(erro: string | undefined): boolean {
  return !!erro && /Corrupt database file|checksum \d+ does not match/i.test(erro);
}

const TENTATIVAS_CHECKSUM = 3;

export async function runSqlSsh(sql: string): Promise<SqlResult> {
  let r = await rodaUmaVez(sql);
  for (let i = 1; i < TENTATIVAS_CHECKSUM && ehChecksumTransitorio(r.error); i++) r = await rodaUmaVez(sql);
  return r;
}

async function rodaUmaVez(sql: string): Promise<SqlResult> {
  // O ~/.duckdbrc do beelink liga enable_progress_bar, e a barra vai pro stdout
  // em qualquer consulta que passe de ~2s — corrompendo o -json. Desligar por
  // sessão não toca no arquivo em disco.
  //
  // Teto de memória: o llama-server divide a máquina (23 de 27 GB) e o padrão
  // do DuckDB é 80% da RAM. Um GROUP BY grande sem teto põe o OOM killer para
  // escolher, e ele escolhe o maior processo — o modelo, no meio da pergunta.
  const stdin =
    `SET enable_progress_bar=false;\n` +
    `SET memory_limit='${MEMORIA}';\nSET threads=${THREADS};\nSET temp_directory='/tmp/duckdb_harness';\n${sql}`;

  let proc;
  try {
    // -readonly é obrigatório: a CLI do DuckDB pega lock EXCLUSIVO do arquivo
    // mesmo num SELECT puro, e uma conexão read-write bloqueia toda outra sessão
    // no mesmo .duckdb — inclusive as read-only. Várias sessões consultam este
    // mirror ao mesmo tempo. (O porte original em web/src/beelink.ts perdeu esta
    // flag que mcp_server.py:310 tem; ver feedback_duckdb_readonly_no_kill.)
    proc = Bun.spawn(["ssh", HOST, `${DUCKDB_BIN} -readonly -json ${DUCKDB_PATH}`], {
      stdin: new TextEncoder().encode(stdin),
      stdout: "pipe",
      stderr: "pipe",
      timeout: TIMEOUT_MS,
      killSignal: "SIGKILL",
    });
  } catch (e) {
    const msg = String(e);
    if (msg.includes("ENOENT")) return { error: "ssh não encontrado no PATH — beelink inalcançável." };
    return { error: `Falha ao invocar ssh: ${msg}` };
  }

  const [stdout, stderr, code] = await Promise.all([
    new Response(proc.stdout).text(),
    new Response(proc.stderr).text(),
    proc.exited,
  ]);

  // `proc.killed` é true em QUALQUER saída não-zero, inclusive erro de SQL —
  // não serve pra detectar timeout. `signalCode` só vem preenchido quando o Bun
  // mata o processo pelo timeout. Confundir os dois mascararia todo erro de
  // Binder como "excedeu 120s", e o laço de reparo depende do erro real.
  if (proc.signalCode) {
    return { error: `Consulta excedeu ${Math.round(TIMEOUT_MS / 1000)}s (ssh beelink).` };
  }
  if (code !== 0) {
    return { error: cleanStderr(stderr) || `ssh beelink saiu com status ${code}` };
  }

  const out = stdout.trim();
  if (!out) return { rows: [] };
  try {
    return { rows: JSON.parse(out) };
  } catch {
    // O -json do DuckDB escreve NaN e Infinity crus (corr() num grupo constante),
    // que não são JSON. Medido 2026-09-22: a consulta inteira virou "Falhou" e o
    // modelo respondeu lendo o texto do erro.
    try {
      return { rows: JSON.parse(semNaoNumeros(out)) };
    } catch {
      return { error: `Resposta não-JSON do beelink: ${out.slice(0, 2000)}` };
    }
  }
}

/** NaN/Infinity fora de string viram null. */
export function semNaoNumeros(json: string): string {
  let out = "";
  for (let i = 0; i < json.length; i++) {
    const c = json[i]!;
    if (c === '"') {
      let j = i + 1;
      while (j < json.length && json[j] !== '"') j += json[j] === "\\" ? 2 : 1;
      out += json.slice(i, j + 1);
      i = j;
      continue;
    }
    const m = /^(-?Infinity|NaN)\b/.exec(json.slice(i, i + 9));
    if (m) { out += "null"; i += m[1]!.length - 1; continue; }
    out += c;
  }
  return out;
}

// Palavras que podem seguir legitimamente uma referência de tabela — qualquer
// outra coisa depois de `FROM dataset.table` é alias do usuário, e tem que ser
// preservada na reescrita.
const POST_TABLE_KEYWORDS = new Set(
  ("WHERE GROUP ORDER LIMIT OFFSET JOIN LEFT RIGHT INNER FULL CROSS NATURAL " +
   "ON USING UNION INTERSECT EXCEPT HAVING QUALIFY WINDOW SEMI ANTI " +
   "POSITIONAL ASOF TABLESAMPLE USE AS").split(" "));

let _globs: Map<string, string> | null = null;

/** `dataset.table` -> `~/rodado/dataset/table/*.parquet`, lido do schemas.json. */
export function parquetGlobs(schemaPath = "docs/context/schemas.json"): Map<string, string> {
  if (_globs) return _globs;
  const schema = JSON.parse(readFileSync(schemaPath, "utf-8")) as Record<string, Record<string, unknown>>;
  _globs = new Map();
  for (const [ds, tables] of Object.entries(schema)) {
    for (const tbl of Object.keys(tables)) {
      _globs.set(`${ds}.${tbl}`, `~/rodado/${ds}/${tbl}/*.parquet`);
    }
  }
  return _globs;
}

const escapeRe = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

/**
 * Troca referências `dataset.table` por `read_parquet()`.
 *
 * Mantém o alias do usuário quando existe; senão apelida a relação com o nome
 * simples da tabela, para que qualificadores `tabela.coluna` sigam resolvendo.
 */
export function rewriteToReadParquet(
  sql: string,
  globs = parquetGlobs(),
): { sql: string; rewritten: string[] } {
  const rewritten: string[] = [];
  const ids = [...globs.keys()].sort((a, b) => b.length - a.length).map(escapeRe);
  if (ids.length === 0) return { sql, rewritten };
  const pattern = new RegExp(`(?<![\\w."])(${ids.join("|")})(?![\\w.])`, "g");

  const out = sql.replace(pattern, (match, tid: string, offset: number) => {
    rewritten.push(tid);
    let replacement = `read_parquet('${globs.get(tid)}')`;
    const rest = sql.slice(offset + match.length).trimStart();
    const nextToken = rest.match(/^[A-Za-z_][A-Za-z_0-9]*/)?.[0];
    const upper = nextToken?.toUpperCase();
    const hasAlias = nextToken !== undefined && (upper === "AS" || !POST_TABLE_KEYWORDS.has(upper!));
    if (!hasAlias) replacement += ` AS "${tid.slice(tid.indexOf(".") + 1)}"`;
    return replacement;
  });

  return { sql: out, rewritten };
}

/** O erro pede o fallback de parquet? (view apontando pro S3 que já não existe) */
export function needsParquetFallback(error: string): boolean {
  return error.includes("Catalog Error") || error.includes("NoSuchBucket") || error.includes("s3://");
}
