import { chromium } from "playwright";
const b = await chromium.launch({ channel: "chrome" });
const p = await b.newPage();
p.on("console", m => { const t = m.text(); if (/error|fail/i.test(t)) console.log("[console]", t.slice(0,200)); });
await p.goto("http://127.0.0.1:8090/_diag.html");
await p.waitForFunction("window.__done === true", null, { timeout: 300000 });
console.log(await p.textContent("#out"));
await b.close();
