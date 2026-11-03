#!/usr/bin/env bun
/**
 * Confere, no ar, se rodado.xyz e ミ.xyz estão achaveis e compartilháveis:
 *
 *  1. robots.txt e sitemap.xml respondem nos dois hosts;
 *  2. toda URL do sitemap responde 200 e tem og:title, og:image e
 *     twitter:card, e a og:image responde 200;
 *  3. toda análise e plataforma dos manifests (pages/analises/results/
 *     manifest.json, pages/plataformas/plataformas.json) hospedada num dos
 *     dois hosts está no sitemap do seu host.
 *
 * Uso: bun scripts/checa_seo.ts   (sai 1 se algo falhar)
 * Rotina que o chama: tasks/routine/seo_sitemaps.md
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";

const HOSTS = ["https://rodado.xyz", "https://xn--2dk.xyz"];
const PAGES = join(import.meta.dir, "..", "pages");
const UA = { "user-agent": "rodado-checa-seo/1.0" };

const falhas: string[] = [];
const falha = (s: string) => falhas.push(s);

async function get(url: string): Promise<{ status: number; body: string }> {
  for (let tentativa = 0; tentativa < 3; tentativa++) {
    try {
      const r = await fetch(url, { headers: UA, redirect: "follow", signal: AbortSignal.timeout(30_000) });
      return { status: r.status, body: await r.text() };
    } catch {
      await Bun.sleep(2000);
    }
  }
  return { status: 0, body: "" };
}

// rodado.xyz e ミ.xyz são GitHub Pages: 8 em paralelo é educado o bastante
async function emLotes<T>(itens: T[], n: number, f: (x: T) => Promise<void>) {
  for (let i = 0; i < itens.length; i += n) await Promise.all(itens.slice(i, i + n).map(f));
}

const meta = (html: string, prop: string) =>
  html.match(new RegExp(`<meta[^>]+(?:property|name)=["']${prop}["'][^>]*content=["']([^"']*)["']`, "i"))?.[1] ??
  html.match(new RegExp(`<meta[^>]+content=["']([^"']*)["'][^>]*(?:property|name)=["']${prop}["']`, "i"))?.[1];

const norm = (u: string) => u.split(/[?#]/)[0].replace(/index\.html$/, "");
const noSitemap = new Map<string, Set<string>>();
const imagensVistas = new Map<string, number>();

for (const host of HOSTS) {
  const robots = await get(`${host}/robots.txt`);
  if (robots.status !== 200) falha(`${host}/robots.txt: HTTP ${robots.status}`);
  else if (!robots.body.includes(`${host}/sitemap.xml`)) falha(`${host}/robots.txt não aponta o sitemap`);

  const sm = await get(`${host}/sitemap.xml`);
  if (sm.status !== 200) {
    falha(`${host}/sitemap.xml: HTTP ${sm.status}`);
    continue;
  }
  const urls = [...sm.body.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1].replace(/&amp;/g, "&"));
  noSitemap.set(host, new Set(urls.map(norm)));
  console.log(`${host}: ${urls.length} URLs no sitemap`);

  await emLotes(urls, 8, async (url) => {
    const r = await get(url);
    if (r.status !== 200) return falha(`${url}: HTTP ${r.status}`);
    const faltam = ["og:title", "og:image", "twitter:card"].filter((p) => !meta(r.body, p));
    if (faltam.length) return falha(`${url}: sem ${faltam.join(", ")}`);
    const img = meta(r.body, "og:image")!;
    if (!imagensVistas.has(img)) {
      imagensVistas.set(img, -1);
      const ri = await fetch(img, { method: "GET", headers: UA, signal: AbortSignal.timeout(30_000) })
        .then((x) => x.status).catch(() => 0);
      imagensVistas.set(img, ri);
    }
  });
}

for (const [img, st] of imagensVistas) if (st !== 200) falha(`og:image ${img}: HTTP ${st}`);

// tudo o que os manifests publicam num dos dois hosts tem de estar no sitemap
const manifests: [string, { slug: string; url?: string }[]][] = [
  ["analises", JSON.parse(readFileSync(join(PAGES, "analises/results/manifest.json"), "utf8"))],
  ["plataformas", JSON.parse(readFileSync(join(PAGES, "plataformas/plataformas.json"), "utf8"))],
];
const foraDosHosts: [string, string][] = [];
for (const [secao, itens] of manifests) {
  for (const it of itens) {
    const url = norm(it.url ?? `https://rodado.xyz/${secao}/${it.slug}/`);
    const host = HOSTS.find((h) => url.startsWith(h + "/"));
    if (!host) {
      // github.io e afins: fora do nosso sitemap, mas o cartão ao compartilhar vale igual
      foraDosHosts.push([`${secao}/${it.slug}`, url]);
      continue;
    }
    // no ar o host do dataviz pode vir escrito em unicode (ミ.xyz)
    if (!noSitemap.get(host)?.has(url)) falha(`${secao}/${it.slug}: ${url} fora do sitemap de ${host}`);
  }
}

// plataformas hospedadas fora (rafapolo.github.io/viso etc.): só o cartão og
await emLotes(foraDosHosts, 8, async ([nome, url]) => {
  const r = await get(url);
  if (r.status !== 200) return falha(`${nome}: ${url} HTTP ${r.status}`);
  const faltam = ["og:title", "og:image", "twitter:card"].filter((p) => !meta(r.body, p));
  if (faltam.length) return falha(`${nome}: ${url} sem ${faltam.join(", ")}`);
  const img = meta(r.body, "og:image")!;
  const ri = await fetch(img, { method: "GET", headers: UA, signal: AbortSignal.timeout(30_000) })
    .then((x) => x.status).catch(() => 0);
  imagensVistas.set(img, ri);
  if (ri !== 200) falha(`og:image ${img}: HTTP ${ri}`);
});
console.log(`${foraDosHosts.length} plataformas fora dos dois hosts conferidas`);

console.log(`${imagensVistas.size} imagens og conferidas`);
if (falhas.length) {
  console.log(`\n${falhas.length} falhas:`);
  for (const f of falhas.sort()) console.log(`  ✗ ${f}`);
  process.exit(1);
}
console.log("ok: tudo achável e com cartão");
