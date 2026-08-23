import { chromium } from "playwright";
import { writeFileSync } from "node:fs";
const b = await chromium.launch({ channel: "chrome" });
const p = await b.newPage();
await p.goto("http://127.0.0.1:8090/diag/embeda.html");
await p.waitForFunction("window.__done === true", null, { timeout: 1_800_000 });
const erro = await p.evaluate("window.__erro");
if (erro) { console.error("ERRO:", erro); process.exit(1); }
const b64 = await p.evaluate("window.__b64");
const n = await p.evaluate("window.__n");
writeFileSync("web/static/index/perguntas_vetores.bin", Buffer.from(b64, "base64"));
console.log(`${n} vetores gravados em web/static/index/perguntas_vetores.bin`);
await b.close();
