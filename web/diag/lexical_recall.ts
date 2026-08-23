// Mede lexical, e o que o hibrido ganharia, sem depender do navegador.
import { readFileSync } from "node:fs";
const meta = JSON.parse(readFileSync("web/static/index/meta.json","utf-8")).tabelas;
const colunas = JSON.parse(readFileSync("web/static/index/colunas.json","utf-8"));
const { perguntas } = JSON.parse(readFileSync("tasks/ask_web_douradas.json","utf-8"));
const L = await import("/Users/polux/Projetos/rodado-ask-web/web/static/lexical.js" as any);
console.log(L.indexar(meta, colunas), "tabelas indexadas");
let ok=0, parc=0, top1=0;
for (const p of perguntas) {
  const sc=[...L.pontuar(p.q)].sort((a,b)=>b[1]-a[1]);
  const ids=sc.slice(0,5).map(x=>x[0]);
  const achou=(p.tabelas as string[]).filter(t=>ids.includes(t));
  if (achou.length===p.tabelas.length) ok++; else if (achou.length) parc++;
  if (ids[0]===p.tabelas[0]) top1++;
}
console.log(`lexical: recall@5 ${ok}/${perguntas.length} completo, ${parc} parcial | top-1 ${top1}/${perguntas.length}`);
