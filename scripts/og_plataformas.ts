#!/usr/bin/env bun
/**
 * Põe o cartão de compartilhamento (Open Graph + Twitter) nas plataformas que
 * chegam sem ele.
 *
 * As plataformas em /plataformas/<pasta>/ não vivem neste repositório: o
 * .github/workflows/pages.yml as monta no deploy a partir de outros repos
 * (shutafut, rios-do-brasil, pet16704, datative...). Algumas não trazem
 * metatag nenhuma, e o link compartilhado ia sem título nem imagem. Este
 * script roda no workflow depois da montagem e antes do upload.
 *
 * Fonte: pages/plataformas/plataformas.json (título, dek, slug). A imagem é
 * pages/plataformas/img/og-<slug>.png, a mesma do índice de plataformas.
 * Página que já tem og:title fica intocada: quem a mantém decidiu o cartão.
 *
 * Uso: bun scripts/og_plataformas.ts [--checa]
 *   --checa  só lista o que faltaria, sem escrever (sai 1 se faltar algo)
 */
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const BASE = "https://rodado.xyz";
const PAGES = join(import.meta.dir, "..", "pages");
const PLAT = join(PAGES, "plataformas");
const checa = process.argv.includes("--checa");

type Item = { slug: string; title: string; url: string; dek?: string; caption?: string };
const manifest: Item[] = JSON.parse(readFileSync(join(PLAT, "plataformas.json"), "utf8"));

const esc = (s: string) =>
  s.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

let faltando = 0;
let feitas = 0;
for (const item of manifest) {
  const url = item.url.split(/[?#]/)[0];
  const m = url.match(/^https:\/\/rodado\.xyz\/plataformas\/([^/]+)\/$/);
  if (!m) continue; // hospedada fora (xn--2dk.xyz, github.io)
  const pasta = m[1];
  const arquivo = join(PLAT, pasta, "index.html");
  if (!existsSync(arquivo)) {
    console.log(`  - ${pasta}: não montada neste build, ignorada`);
    continue;
  }
  const html = readFileSync(arquivo, "utf8");
  if (/property=["']og:title["']/i.test(html)) continue;

  faltando++;
  if (checa) {
    console.log(`  ! ${pasta}: sem og:title`);
    continue;
  }
  const img = existsSync(join(PLAT, "img", `og-${item.slug}.png`))
    ? `${BASE}/plataformas/img/og-${item.slug}.png`
    : `${BASE}/assets/og.png`;
  const desc = (item.dek || item.caption || "").trim();
  const titulo = item.title.trim();
  const tags = [
    "<!-- og:start (gerado por scripts/og_plataformas.ts no deploy) -->",
    /rel=["']canonical["']/i.test(html) ? "" : `<link rel="canonical" href="${esc(url)}">`,
    /name=["']description["']/i.test(html) ? "" : `<meta name="description" content="${esc(desc)}">`,
    '<meta property="og:type" content="website">',
    '<meta property="og:site_name" content="rodado">',
    '<meta property="og:locale" content="pt_BR">',
    `<meta property="og:url" content="${esc(url)}">`,
    `<meta property="og:title" content="${esc(titulo)}">`,
    `<meta property="og:description" content="${esc(desc)}">`,
    `<meta property="og:image" content="${esc(img)}">`,
    '<meta property="og:image:width" content="1200">',
    '<meta property="og:image:height" content="630">',
    `<meta property="og:image:alt" content="${esc(`${titulo} — rodado`)}">`,
    '<meta name="twitter:card" content="summary_large_image">',
    `<meta name="twitter:title" content="${esc(titulo)}">`,
    `<meta name="twitter:description" content="${esc(desc)}">`,
    `<meta name="twitter:image" content="${esc(img)}">`,
    "<!-- og:end -->",
  ].filter(Boolean).join("\n");

  const novo = /<\/head>/i.test(html)
    ? html.replace(/<\/head>/i, `${tags}\n</head>`)
    : /<head(\s[^>]*)?>/i.test(html)
      ? html.replace(/<head(\s[^>]*)?>/i, (h) => `${h}\n${tags}`)
      : // HTML5 sem <head> explícito (rios-do-brasil): as metatags valem
        // em qualquer ponto antes do <body> implícito, logo após o <title>
        /<\/title>/i.test(html)
        ? html.replace(/<\/title>/i, (t) => `${t}\n${tags}`)
        : null;
  if (novo === null) {
    console.log(`  ! ${pasta}: sem <head>, não deu para injetar`);
    continue;
  }
  writeFileSync(arquivo, novo);
  feitas++;
  console.log(`  + ${pasta}: cartão "${titulo}" (${img.split("/").pop()})`);
}

if (checa) {
  console.log(`${faltando} plataformas sem cartão`);
  process.exit(faltando ? 1 : 0);
}
console.log(`${feitas} plataformas receberam cartão`);
