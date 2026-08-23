/**
 * ask-web — servidor local.
 *
 * É só um executor de SQL e um servidor de estáticos: não fala com modelo
 * nenhum, não guarda estado, não tem chave de API. O embedding e o LLM rodam
 * no navegador. Bind em 127.0.0.1 — não é para sair da máquina.
 */
import { checkReadOnly, capRows } from "./src/sqlguard.ts";
import { runSqlSsh, rewriteToReadParquet, needsParquetFallback } from "./src/beelink.ts";

const PORT = Number(Bun.env.ASK_WEB_PORT ?? 8090);
const MAX_ROWS = Number(Bun.env.ASK_WEB_MAX_ROWS ?? 500);
const STATIC = new URL("./static/", import.meta.url).pathname;

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8" },
  });

async function executar(req: Request): Promise<Response> {
  let sql: string;
  try {
    const body = (await req.json()) as { sql?: unknown };
    if (typeof body.sql !== "string") return json({ erro: "Campo 'sql' ausente ou não-string." }, 400);
    sql = body.sql;
  } catch {
    return json({ erro: "Corpo inválido — esperado JSON {sql}." }, 400);
  }

  // O navegador monta o SQL, mas não é confiável: o firewall roda aqui, antes
  // de qualquer ssh.
  const recusa = checkReadOnly(sql);
  if (recusa) return json({ erro: recusa }, 400);

  const t0 = performance.now();
  let result = await runSqlSsh(sql);
  let rewrittenTables: string[] | undefined;

  // Muitas views do catálogo ainda apontam pro S3, que não existe mais. Quando
  // é esse o erro, reescreve pra read_parquet no caminho local e tenta uma vez.
  if (result.error && needsParquetFallback(result.error)) {
    const { sql: fallback, rewritten } = rewriteToReadParquet(sql);
    if (rewritten.length > 0) {
      const retry = await runSqlSsh(fallback);
      if (!retry.error) {
        result = retry;
        rewrittenTables = [...new Set(rewritten)];
      }
    }
  }

  const ms = Math.round(performance.now() - t0);
  if (result.error) return json({ erro: result.error, ms });

  const capped = capRows(result.rows ?? [], MAX_ROWS);
  const colunas = capped.columns ?? Object.keys(capped.rows[0] ?? {});
  return json({ ...capped, colunas, ms, ...(rewrittenTables ? { rewrittenTables } : {}) });
}

const server = Bun.serve({
  port: PORT,
  hostname: "127.0.0.1",
  async fetch(req) {
    const url = new URL(req.url);

    if (url.pathname === "/api/executar") {
      if (req.method !== "POST") return json({ erro: "Use POST." }, 405);
      return executar(req);
    }

    // estáticos — Bun.file resolve Content-Type e range sozinho
    const rel = url.pathname === "/" ? "index.html" : url.pathname.slice(1);
    if (rel.includes("..")) return new Response("Não.", { status: 400 });
    const file = Bun.file(STATIC + rel);
    if (await file.exists()) return new Response(file);
    return new Response("Não encontrado", { status: 404 });
  },
});

console.log(`ask-web em http://127.0.0.1:${server.port} — dado via ssh ${Bun.env.BEELINK_HOST ?? "beelink"}`);
