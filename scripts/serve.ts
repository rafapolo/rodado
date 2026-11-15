#!/usr/bin/env bun
// Prévia local de pages/ com as regras do GitHub Pages:
//   /x -> x.html, /pasta/ -> pasta/index.html, 404 -> pages/404.html (se existir).
// Uso: bun scripts/serve.ts [--port 8765]
import { join, normalize, resolve } from "node:path";

const RAIZ = resolve(import.meta.dir, "..", "pages");
const i = process.argv.indexOf("--port");
const porta = i > -1 ? Number(process.argv[i + 1]) : 8765;
if (!Number.isInteger(porta) || porta < 0 || porta > 65535) {
  console.error("uso: bun scripts/serve.ts [--port 8765]");
  process.exit(1);
}

const arquivo = async (c: string) => {
  const f = Bun.file(c);
  return (await f.exists()) ? f : null;
};

async function acha(caminho: string) {
  const base = normalize(join(RAIZ, caminho));
  if (base !== RAIZ && !base.startsWith(RAIZ + "/")) return null;
  if (caminho.endsWith("/")) return arquivo(join(base, "index.html"));
  return (await arquivo(base + ".html")) ?? (await arquivo(base));
}

const server = Bun.serve({
  port: porta,
  async fetch(req) {
    const url = new URL(req.url);
    let caminho: string;
    try {
      caminho = decodeURIComponent(url.pathname);
    } catch {
      return new Response("requisição inválida", { status: 400 });
    }
    // pasta sem barra final: o Pages redireciona para /pasta/
    if (!caminho.endsWith("/") && !(await acha(caminho))) {
      const base = normalize(join(RAIZ, caminho));
      if (base.startsWith(RAIZ + "/") && (await arquivo(join(base, "index.html")))) {
        return Response.redirect(url.pathname + "/" + url.search, 301);
      }
    }
    const f = await acha(caminho);
    if (f) return new Response(f);
    const nf = await arquivo(join(RAIZ, "404.html"));
    if (nf) return new Response(nf, { status: 404 });
    return new Response("404 não encontrado", { status: 404 });
  },
});
console.log(`rodado em http://localhost:${server.port}/  (Ctrl+C para sair)`);
