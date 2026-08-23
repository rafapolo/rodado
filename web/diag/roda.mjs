/**
 * Roda uma página de diagnóstico num perfil PERSISTENTE do Chrome.
 *
 * Perfil efêmero não serve: a cota de storage é pequena e estoura antes de
 * cachear 1,1 GB de modelo ("Quota exceeded"), e cada execução refaz o
 * download. Com perfil fixo, o modelo é baixado uma vez só — que é também o
 * comportamento real de um usuário.
 */
import { chromium } from "playwright";
const pagina = process.argv[2] ?? "diag/gera.html";
const timeout = Number(process.argv[3] ?? 900000);
const ctx = await chromium.launchPersistentContext("/tmp/askweb-profile", { channel: "chrome" });
const p = ctx.pages()[0] ?? await ctx.newPage();
p.on("pageerror", e => console.error("PAGEERROR:", e.message.slice(0,180)));
await p.goto(`http://127.0.0.1:8090/${pagina}`);
await p.waitForFunction("window.__done===true", null, { timeout });
console.log(await p.textContent("#out"));
await ctx.close();
