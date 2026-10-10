// Testes de UI e UX do db.rodado.xyz, com a régua da auditoria de acessibilidade
// do swissviz (commit 5a8aaa8): zero controles sem nome acessível, zero falhas de
// contraste WCAG AA, :focus-visible, navegação por teclado, regiões aria-live e
// painéis que viram bottom sheet no celular e fecham ao tocar fora.
//
//   RODADO_SENHA=... bun test            (ou ./roda.sh, que busca a senha no finland)
//
// Usa o Chrome instalado (channel "chrome"): nenhum navegador é baixado.

import { afterAll, beforeAll, beforeEach, describe, expect, test } from "bun:test";
import { chromium, devices, type Browser, type BrowserContext, type Page } from "playwright-core";

const BASE = process.env.RODADO_URL ?? "https://db.rodado.xyz";
const USUARIO = process.env.RODADO_USUARIO ?? "rodado";
const SENHA = process.env.RODADO_SENHA ?? "";
const AUTH = "Basic " + Buffer.from(`${USUARIO}:${SENHA}`).toString("base64");

if (!SENHA) throw new Error("defina RODADO_SENHA (ou rode ./roda.sh)");

let navegador: Browser;
beforeAll(async () => {
  navegador = await chromium.launch({ channel: "chrome", headless: true });
});
afterAll(async () => {
  await navegador?.close();
});

// ---------------------------------------------------------------- utilidades

async function abre(ctx: BrowserContext): Promise<Page> {
  const p = await ctx.newPage();
  await p.goto(BASE + "/", { waitUntil: "domcontentloaded" });
  await p.waitForFunction(() => document.querySelectorAll(".ds").length > 0, null, { timeout: 30_000 });
  await esperaTerminal(p, "rodado>");
  return p;
}

const contexto = (extra: Parameters<Browser["newContext"]>[0] = {}) =>
  navegador.newContext({ httpCredentials: { username: USUARIO, password: SENHA }, ...extra });

/** Texto visível + rolado do xterm dentro do iframe do ttyd. */
const textoTerminal = (p: Page) =>
  p.evaluate(() => {
    const t = (document.getElementById("terminal") as HTMLIFrameElement).contentWindow as any;
    const buf = t?.term?.buffer?.active;
    if (!buf) return "";
    const linhas: string[] = [];
    for (let i = 0; i < buf.length; i++) linhas.push(buf.getLine(i)?.translateToString(true) ?? "");
    return linhas.join("\n");
  });

async function esperaTerminal(p: Page, trecho: string | RegExp, ms = 30_000) {
  const fim = Date.now() + ms;
  let ultimo = "";
  while (Date.now() < fim) {
    ultimo = await textoTerminal(p);
    if (typeof trecho === "string" ? ultimo.includes(trecho) : trecho.test(ultimo)) return ultimo;
    await p.waitForTimeout(250);
  }
  const diag = await p.evaluate(() => {
    const w = (document.getElementById("terminal") as HTMLIFrameElement).contentWindow as any;
    const t = w?.term;
    const normal = t?.buffer?.normal;
    const ult: string[] = [];
    if (normal) for (let i = Math.max(0, normal.length - 6); i < normal.length; i++) ult.push(normal.getLine(i)?.translateToString(true) ?? "");
    return { term: !!t, tipo: t?.buffer?.active?.type, linhas: t?.buffer?.active?.length, normal: normal?.length,
      cursorY: t?.buffer?.active?.cursorY, rows: t?.rows, cols: t?.cols, ult };
  });
  throw new Error(`terminal não mostrou ${trecho} (${JSON.stringify(diag)}); últimas linhas:\n${ultimo.trim().split("\n").slice(-8).join("\n")}`);
}

/** Digita no terminal como teclado de verdade (foco no xterm do iframe). */
async function digita(p: Page, texto: string) {
  // espera o prompt livre (última linha não vazia termina em "rodado>"), como uma pessoa faria
  await esperaTerminal(p, /(rodado|\.\.\.)>\s*$/);
  const f = p.frameLocator("#terminal");
  await f.locator(".xterm-helper-textarea").focus();
  await p.keyboard.type(texto, { delay: 5 });
}

// contraste WCAG 2.x
const auditaContraste = (p: Page, seletor: string) =>
  p.evaluate((sel) => {
    const rgb = (c: string) => (c.match(/[\d.]+/g) ?? []).map(Number);
    const lum = ([r, g, b]: number[]) => {
      const f = (v: number) => ((v /= 255) <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
      return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
    };
    const fundo = (el: Element | null): number[] => {
      for (; el; el = el.parentElement) {
        const c = rgb(getComputedStyle(el).backgroundColor);
        if (c.length >= 3 && (c[3] ?? 1) > 0.5) return c.slice(0, 3);
      }
      return [30, 30, 46];
    };
    const falhas: string[] = [];
    let total = 0;
    const els = [...document.querySelectorAll(sel)].filter((e) => {
      const r = (e as HTMLElement).getBoundingClientRect();
      return r.width > 0 && r.height > 0 && [...e.childNodes].some((n) => n.nodeType === 3 && n.textContent!.trim());
    });
    for (const el of els) {
      const cs = getComputedStyle(el);
      if (cs.visibility === "hidden" || cs.opacity === "0") continue;
      total++;
      const a = lum(rgb(cs.color)), b = lum(fundo(el));
      const razao = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
      const grande = parseFloat(cs.fontSize) >= 24 || (parseFloat(cs.fontSize) >= 18.66 && +cs.fontWeight >= 700);
      if (razao < (grande ? 3 : 4.5)) falhas.push(`${el.tagName.toLowerCase()}.${el.className} "${el.textContent!.trim().slice(0, 20)}" ${razao.toFixed(2)}`);
    }
    return { total, falhas: [...new Set(falhas)] };
  }, seletor);

// ---------------------------------------------------------------- API (curl)

describe("API /query", () => {
  const q = (sql: string, params = "", auth = AUTH) =>
    fetch(`${BASE}/query${params}`, { method: "POST", body: sql, headers: auth ? { Authorization: auth } : {} });

  test("sem senha devolve 401, inclusive na página e no terminal", async () => {
    for (const caminho of ["/query", "/", "/tty/", "/catalogo.json"]) {
      const r = await fetch(BASE + caminho);
      expect(r.status, caminho).toBe(401);
    }
  });

  test("senha errada devolve 401", async () => {
    const r = await q("SELECT 1", "", "Basic " + Buffer.from("rodado:errada").toString("base64"));
    expect(r.status).toBe(401);
  });

  test("/health responde sem senha (usado pelo haloy)", async () => {
    expect((await fetch(BASE + "/health")).status).toBe(200);
  });

  test("JSON com cabeçalhos de linhas, corte e tempo", async () => {
    const r = await q("SELECT sigla FROM br_bd_diretorios_brasil.uf ORDER BY 1");
    expect(r.status).toBe(200);
    const d = (await r.json()) as { sigla: string }[];
    expect(d.length).toBe(27);
    expect(d[0].sigla).toBe("AC");
    expect(r.headers.get("x-linhas")).toBe("27");
    expect(r.headers.get("x-truncado")).toBe("0");
    expect(Number(r.headers.get("x-segundos"))).toBeGreaterThanOrEqual(0);
  });

  test("CSV, TSV e limite", async () => {
    const csv = await (await q("SELECT sigla, nome FROM br_bd_diretorios_brasil.uf ORDER BY 1", "?formato=csv")).text();
    expect(csv.split("\n")[0]).toBe("sigla,nome");
    const r = await q("FROM br_bd_diretorios_brasil.uf", "?formato=tsv&limite=3");
    expect(r.headers.get("x-truncado")).toBe("1");
    expect((await r.text()).trim().split("\n").length).toBe(4);
  });

  test("parquet tipado (lido pelo próprio cabeçalho mágico)", async () => {
    const r = await q("SELECT 42::INTEGER AS x", "?formato=parquet");
    const b = new Uint8Array(await r.arrayBuffer());
    expect(new TextDecoder().decode(b.slice(0, 4))).toBe("PAR1");
  });

  test("GET com q= funciona (curl -G)", async () => {
    const r = await fetch(`${BASE}/query?q=${encodeURIComponent("SELECT 42 AS ok")}`, { headers: { Authorization: AUTH } });
    expect(await r.json()).toEqual([{ ok: 42 }]);
  });

  test("só leitura: COPY, SET, ATTACH, INSTALL e vários comandos são recusados", async () => {
    for (const sql of [
      "COPY (SELECT 1) TO '/home/polo/rodado/x.csv'",
      "SET threads = 1",
      "ATTACH 'x.duckdb'",
      "INSTALL httpfs",
      "CREATE TABLE t AS SELECT 1",
      "SELECT 1; SELECT 2",
    ]) {
      const r = await q(sql);
      expect(r.status, sql).toBe(400);
      expect(((await r.json()) as any).erro, sql).toBeTruthy();
    }
  });

  test("arquivos fora de ~/rodado não são lidos", async () => {
    const r = await q("SELECT * FROM read_text('/home/polo/.ssh/rodado_tunel')");
    expect(r.status).toBe(400);
    expect(((await r.json()) as any).erro).toContain("disabled by configuration");
  });

  test("dado conhecido bate: 156,45 mi de eleitores em 2022", async () => {
    const d = (await (await q("SELECT sum(eleitores_secao)::BIGINT AS n FROM br_rodado_eleicoes.secao_setor WHERE ano = 2022")).json()) as any[];
    expect(d[0].n).toBe(156454011);
  });
});

// ---------------------------------------------------------------- desktop

describe("desktop", () => {
  let ctx: BrowserContext;
  let p: Page;
  beforeAll(async () => {
    ctx = await contexto({ viewport: { width: 1440, height: 900 } });
    p = await abre(ctx);
  });
  afterAll(async () => ctx?.close());

  test("carrega catálogo inteiro e o terminal conectado", async () => {
    expect(await p.title()).toBe("rodado SQL");
    const ds = await p.locator(".ds").count();
    expect(ds).toBeGreaterThan(200);
    expect(await p.locator("#resumo").textContent()).toMatch(/\d+ ds · \d+ tab · [\d,]+ (bi|mi)/);
    expect(await textoTerminal(p)).toContain("rodado>");
  });

  test("JetBrains Mono no terminal e na árvore", async () => {
    const fonteTerm = await p.evaluate(() => ((document.getElementById("terminal") as any).contentWindow.term.options.fontFamily as string));
    expect(fonteTerm).toContain("JetBrains Mono");
    expect(await p.evaluate(() => document.fonts.check('12px "JetBrains Mono"'))).toBe(true);
    expect(await p.evaluate(() => getComputedStyle(document.body).fontFamily)).toContain("JetBrains Mono");
  });

  test("a11y: nenhum controle interativo sem nome acessível", async () => {
    const semNome = await p.evaluate(() =>
      [...document.querySelectorAll("button, input, select, textarea, iframe, [role=button], [role=separator], [tabindex]")]
        .filter((e) => !(e as HTMLElement).closest("[aria-hidden=true]"))
        .filter((e) => {
          const nome = e.getAttribute("aria-label") || e.getAttribute("aria-labelledby") || e.getAttribute("title")
            || (e.tagName !== "INPUT" && e.textContent?.trim());
          return !nome;
        })
        .map((e) => e.outerHTML.slice(0, 80)));
    expect(semNome).toEqual([]);
  });

  test("a11y: contraste WCAG AA em todo texto da árvore e do cabeçalho", async () => {
    const primeiro = p.locator(".ds > summary").first();
    await primeiro.click();
    await p.locator(".ds[open] .tb > summary").first().click();
    await p.waitForSelector(".tb[open] .coluna");
    const r = await auditaContraste(p, "aside *");
    expect(r.total).toBeGreaterThan(20);
    expect(r.falhas).toEqual([]);
    await primeiro.click();
  });

  test("a11y: regras :focus-visible existem e aparecem ao navegar por Tab", async () => {
    const regras = await p.evaluate(() =>
      [...document.styleSheets].flatMap((s) => { try { return [...s.cssRules]; } catch { return []; } })
        .filter((r) => (r as CSSStyleRule).selectorText?.includes(":focus-visible")).length);
    expect(regras).toBeGreaterThanOrEqual(2);
    await p.locator("#busca").focus();
    await p.keyboard.press("Tab");
    const contorno = await p.evaluate(() => {
      const e = document.activeElement as HTMLElement;
      const cs = getComputedStyle(e);
      return { tag: e.tagName, outline: cs.outlineStyle !== "none" && parseFloat(cs.outlineWidth) > 0, sombra: cs.boxShadow !== "none" };
    });
    expect(contorno.outline || contorno.sombra).toBe(true);
  });

  test("a11y: regiões aria-live anunciam o resultado da busca", async () => {
    expect(await p.locator("[aria-live]").count()).toBeGreaterThanOrEqual(1);
    await p.locator("#busca").fill("secao_setor");
    await p.waitForTimeout(400);
    expect(await p.locator("#status").textContent()).toMatch(/1 tabela/);
    await p.locator("#busca").fill("");
    await p.waitForTimeout(300);
  });

  test("busca filtra por tabela e mostra estado vazio", async () => {
    await p.locator("#busca").fill("secao_setor");
    await p.waitForTimeout(400);
    expect(await p.locator(".ds").count()).toBe(1);
    expect(await p.locator(".ds summary").first().textContent()).toContain("br_rodado_eleicoes");
    await p.locator("#busca").fill("zzzz_nao_existe");
    await p.waitForTimeout(400);
    expect(await p.locator("#arvore").textContent()).toContain("nada encontrado");
    await p.locator("#busca").fill("");
    await p.waitForTimeout(300);
  });

  test("teclado: ↓ da busca entra na árvore, ↑/↓ navegam, → abre, ← fecha", async () => {
    await p.locator("#busca").fill("br_rodado_eleicoes");
    await p.waitForTimeout(400);
    await p.locator("#busca").focus();
    await p.keyboard.press("ArrowDown");
    expect(await p.evaluate(() => document.activeElement?.closest(".ds") !== null)).toBe(true);
    await p.keyboard.press("ArrowDown");
    expect(await p.evaluate(() => (document.activeElement?.closest(".tb") as HTMLElement)?.dataset.t)).toMatch(/^br_rodado_eleicoes\./);
    await p.keyboard.press("ArrowRight");
    await p.waitForFunction(() => document.querySelector(".tb[open] .coluna") !== null);
    await p.keyboard.press("ArrowLeft");
    expect(await p.locator(".tb[open]").count()).toBe(0);
    await p.keyboard.press("ArrowUp");
    expect(await p.evaluate(() => document.activeElement?.parentElement?.classList.contains("ds"))).toBe(true);
    await p.keyboard.press("Escape");
    expect(await p.evaluate(() => document.activeElement?.id)).toBe("busca");
    await p.locator("#busca").fill("");
    await p.waitForTimeout(300);
  });

  test("abrir uma tabela lista colunas com tipo, descrição e fonte", async () => {
    await p.locator("#busca").fill("secao_setor");
    await p.waitForTimeout(400);
    await p.locator(".tb summary").first().click();
    await p.waitForSelector(".tb[open] .coluna");
    expect(await p.locator(".tb[open] .coluna").count()).toBe(18);
    expect(await p.locator(".tb[open] .coluna .tipo").first().textContent()).toBe("INTEGER");
  });

  test("▶ cola a consulta no terminal e Enter executa", async () => {
    await p.locator(".tb[open] summary .usar").click();
    await esperaTerminal(p, "FROM br_rodado_eleicoes.secao_setor LIMIT 10;");
    await p.frameLocator("#terminal").locator(".xterm-helper-textarea").press("Enter");
    await esperaTerminal(p, /10 rows/);
    await p.locator("#busca").fill("");
    await p.waitForTimeout(300);
  });

  test("terminal: consulta em várias linhas, cores e tempo", async () => {
    await digita(p, "SELECT sigla_uf, count(*) AS n");
    await p.keyboard.press("Enter");
    await digita(p, "FROM br_rodado_eleicoes.secao_setor WHERE ano = 2026 GROUP BY 1 ORDER BY 2 DESC LIMIT 2;");
    await p.keyboard.press("Enter");
    const t = await esperaTerminal(p, /SP\s+│\s+103904/);
    expect(t).toMatch(/\(\d+\.\d\d s\)/);
    // a palavra-chave SELECT foi pintada (cor diferente do texto comum)
    const cores = await p.evaluate(() => {
      const term = (document.getElementById("terminal") as any).contentWindow.term;
      const buf = term.buffer.active;
      for (let i = buf.length - 1; i >= 0; i--) {
        const l = buf.getLine(i);
        if (l?.translateToString(true).includes("SELECT sigla_uf")) {
          const x = l.translateToString(true).indexOf("SELECT");
          return [l.getCell(x).getFgColor(), l.getCell(x + 7).getFgColor()];
        }
      }
      return null;
    });
    expect(cores).not.toBeNull();
    expect(cores![0]).not.toBe(cores![1]);
  });

  test("terminal: autocompletar com Tab", async () => {
    await digita(p, "DESCRIBE br_rodado_eleicoes.setor_l");
    await p.keyboard.press("Tab");
    await p.waitForTimeout(300);
    await p.keyboard.type(";");
    await p.keyboard.press("Enter");
    await esperaTerminal(p, "distancia_centroide_m");
  });

  test("terminal: escrita é recusada com mensagem clara", async () => {
    await digita(p, "COPY (SELECT 1) TO 'x.csv';");
    await p.keyboard.press("Enter");
    await esperaTerminal(p, "recusado: COPY não é permitido");
  });

  test("divisor: arrastar muda a largura, refaz o terminal, lembra e duplo clique restaura", async () => {
    const sep = p.locator("#arrasta");
    expect(await sep.getAttribute("role")).toBe("separator");
    const colsAntes = await p.evaluate(() => (document.getElementById("terminal") as any).contentWindow.term.cols);
    const box = (await sep.boundingBox())!;
    await p.mouse.move(box.x + 1, box.y + box.height / 2);
    await p.mouse.down();
    await p.mouse.move(box.x - 200, box.y + box.height / 2, { steps: 8 });
    await p.mouse.up();
    const largura = await p.evaluate(() => document.querySelector("aside")!.getBoundingClientRect().width);
    expect(largura).toBeGreaterThan(540);
    await p.waitForTimeout(300);
    expect(await p.evaluate(() => (document.getElementById("terminal") as any).contentWindow.term.cols)).toBeLessThan(colsAntes);
    await p.reload();
    await p.waitForFunction(() => document.querySelectorAll(".ds").length > 0);
    expect(Math.round(await p.evaluate(() => document.querySelector("aside")!.getBoundingClientRect().width))).toBe(Math.round(largura));
    await p.locator("#arrasta").dblclick();
    expect(await p.evaluate(() => document.querySelector("aside")!.getBoundingClientRect().width)).toBe(360);
    await esperaTerminal(p, "rodado>");
  });

  test("divisor também responde ao teclado (← →)", async () => {
    await p.locator("#arrasta").focus();
    await p.keyboard.press("ArrowLeft");
    await p.keyboard.press("ArrowLeft");
    expect(await p.evaluate(() => document.querySelector("aside")!.getBoundingClientRect().width)).toBe(400);
    await p.locator("#arrasta").dblclick();
  });

  test("sem rolagem horizontal na página", async () => {
    expect(await p.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  });

  test("moldura de 2 px rgb(144, 157, 235) na página inteira, sem bloquear clique", async () => {
    const m = await p.evaluate(() => {
      const cs = getComputedStyle(document.documentElement, "::after");
      return { borda: cs.borderTopWidth, cor: cs.borderTopColor, pos: cs.position, eventos: cs.pointerEvents, inset: cs.inset };
    });
    expect(m).toEqual({ borda: "2px", cor: "rgb(144, 157, 235)", pos: "fixed", eventos: "none", inset: "0px" });
  });
});

// ---------------------------------------------------------------- celular

describe("celular (iPhone 14)", () => {
  let ctx: BrowserContext;
  let p: Page;
  beforeAll(async () => {
    const { defaultBrowserType: _, ...iphone } = devices["iPhone 14"];
    ctx = await contexto(iphone);
    p = await abre(ctx);
  });
  afterAll(async () => ctx?.close());
  // cada teste começa com o painel fechado: um teste que falha não derruba os seguintes
  beforeEach(async () => {
    await p.evaluate(() => {
      document.body.classList.remove("arvore-aberta");
      const b = document.getElementById("busca") as HTMLInputElement;
      b.value = "";
      b.dispatchEvent(new Event("input"));
    });
    await p.waitForTimeout(300);
  });

  test("terminal ocupa a tela, árvore escondida, barra de teclas visível", async () => {
    const m = await p.evaluate(() => {
      const r = (s: string) => document.querySelector(s)!.getBoundingClientRect();
      return { term: r("#terminal"), teclas: r("#teclas"), aside: r("aside"), w: innerWidth, h: innerHeight };
    });
    expect(m.term.width).toBe(m.w);
    expect(m.term.height).toBeGreaterThan(m.h * 0.75);
    expect(m.teclas.bottom).toBeLessThanOrEqual(m.h + 1);
    expect(m.aside.top).toBeGreaterThanOrEqual(m.h - 1); // fora da tela
    expect(await textoTerminal(p)).toContain("rodado>");
  });

  test("toque: alvos de pelo menos 36 px (WCAG 2.5.8 pede 24)", async () => {
    const pequenos = await p.evaluate(() =>
      [...document.querySelectorAll("#teclas button, #fecha")]
        .map((b) => ({ t: b.textContent, r: b.getBoundingClientRect() }))
        .filter(({ r }) => r.height < 36 || r.width < 36).map((x) => x.t));
    expect(pequenos).toEqual([]);
  });

  test("busca com 16 px (o iOS não dá zoom no foco)", async () => {
    expect(await p.evaluate(() => parseFloat(getComputedStyle(document.getElementById("busca")!).fontSize))).toBeGreaterThanOrEqual(16);
  });

  test("☰ abre o painel como bottom sheet; tocar fora e ✕ fecham", async () => {
    const aberto = () => p.evaluate(() => document.body.classList.contains("arvore-aberta"));
    await p.locator("[data-acao=arvore]").tap();
    expect(await aberto()).toBe(true);
    expect(await p.locator("[data-acao=arvore]").getAttribute("aria-expanded")).toBe("true");
    await p.waitForTimeout(300);
    const topo = await p.evaluate(() => document.querySelector("aside")!.getBoundingClientRect().top);
    expect(topo).toBeLessThan(await p.evaluate(() => innerHeight * 0.5));
    await p.mouse.click(100, 40); // no fundo escurecido
    expect(await aberto()).toBe(false);
    await p.locator("[data-acao=arvore]").tap();
    await p.locator("#fecha").tap();
    expect(await aberto()).toBe(false);
    await p.locator("[data-acao=arvore]").tap();
    await p.keyboard.press("Escape");
    expect(await aberto()).toBe(false);
  });

  test("▶ visível sem hover; tocar cola no terminal e fecha o painel", async () => {
    await p.locator("[data-acao=arvore]").tap();
    await p.locator("#busca").fill("diretorios_brasil.uf");
    await p.waitForTimeout(400);
    const usar = p.locator('.tb[data-t="br_bd_diretorios_brasil.uf"] .usar');
    expect(await usar.evaluate((e) => getComputedStyle(e).visibility)).toBe("visible");
    await usar.tap();
    expect(await p.evaluate(() => document.body.classList.contains("arvore-aberta"))).toBe(false);
    await esperaTerminal(p, "FROM br_bd_diretorios_brasil.uf LIMIT 10;");
    await p.locator("[data-k=enter]").tap();
    await esperaTerminal(p, "Santa Catarina");
  });

  test("barra de teclas manda ; e ⏎ ao terminal", async () => {
    await p.evaluate(() => (document.getElementById("terminal") as any).contentWindow.term.paste("SELECT 6 * 7 AS resposta"));
    await p.locator('#teclas [data-t=";"]').tap();
    await p.locator("[data-k=enter]").tap();
    await esperaTerminal(p, /│\s+42\s+│/);
  });

  test("Ctrl-C limpa a linha em edição", async () => {
    await p.evaluate(() => (document.getElementById("terminal") as any).contentWindow.term.paste("SELECT 'nao_deve_rodar'"));
    await p.locator("[data-k=ctrlc]").tap();
    await p.locator("[data-k=enter]").tap();
    await p.waitForTimeout(800);
    expect(await textoTerminal(p)).not.toMatch(/│\s+nao_deve_rodar\s+│/);
  });

  test("sem rolagem horizontal", async () => {
    expect(await p.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  });

  test("contraste AA também no painel do celular", async () => {
    await p.locator("[data-acao=arvore]").tap();
    await p.waitForTimeout(300);
    const r = await auditaContraste(p, "aside *, #teclas *");
    expect(r.falhas).toEqual([]);
    await p.keyboard.press("Escape");
  });
});
