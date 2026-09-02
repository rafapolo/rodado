/**
 * dsh+MCP contra pipeline fixo, nas MESMAS perguntas.
 *
 *     bun harness/compara.ts <arquivo-de-perguntas>
 *
 * A pergunta que isto responde: o laço agêntico paga por si? Os dois caminhos
 * usam o mesmo modelo, o mesmo portão e o mesmo beelink. O que muda é quem
 * decide a sequência — o modelo (dsh) ou o código (laco.ts).
 *
 * Roda um de cada vez: os dois disputam o mesmo llama-server e medir em paralelo
 * falsearia o tempo dos dois.
 */
import { roda as rodaLaco } from "./laco.ts";
import { carregaCasos } from "./casos.ts";

interface Caso { pergunta: string; esperado?: string }

const bate = (texto: string, esperado?: string) =>
  esperado ? texto.replace(/[.\s]/g, "").includes(esperado.replace(/[.\s]/g, "")) : undefined;

if (import.meta.main) {
  const arquivo = Bun.argv[2];
  if (!arquivo) { console.error("uso: bun harness/compara.ts <arquivo>"); process.exit(1); }
  const casos: Caso[] = (await Bun.file(arquivo).text()).split("\n")
    .map((l) => l.trim()).filter(Boolean)
    .map((l) => { const [p, e] = l.split("\t"); return { pergunta: p!.trim(), esperado: e?.trim() }; });

  // mesmos exemplos few-shot que a avaliação de datasets usa
  const todos = carregaCasos().filter((c) => !c.suspeito);
  const temas = [...new Set(todos.map((c) => c.tema))].sort((a, b) => a - b);
  const pares = new Set(temas.filter((_, i) => i % 2 === 0));
  const exemplos = todos.filter((c) => pares.has(c.tema));

  console.log(`PIPELINE FIXO (laco.ts, sem MCP) — ${casos.length} perguntas\n`);
  let certos = 0, comGab = 0, tempo = 0;
  for (const [i, c] of casos.entries()) {
    const t0 = Date.now();
    const r = await rodaLaco(c.pergunta, exemplos);
    const seg = (Date.now() - t0) / 1000;
    tempo += seg;
    const texto = `${r.prosa ?? ""} ${JSON.stringify(r.linhas ?? [])}`;
    const ok = bate(texto, c.esperado);
    if (ok !== undefined) { comGab++; if (ok) certos++; }
    const marca = ok === false ? "ERRO" : ok === true ? " ok " : r.erro ? "  --" : " ?  ";
    console.log(`${marca} ${i + 1}/${casos.length}  ${seg.toFixed(0)}s  ${r.tentativas} tentativa(s)  ${c.pergunta.slice(0, 50)}`);
    if (r.erro) console.log(`      ${r.erro}`);
    else if (ok === false) console.log(`      esperava ${c.esperado} | n=${r.n} | ${(r.prosa ?? "").replace(/\s+/g, " ").slice(0, 110)}`);
  }
  console.log(`\n${"=".repeat(56)}`);
  if (comGab) console.log(`CORRETO: ${certos}/${comGab} = ${(100 * certos / comGab).toFixed(0)}%`);
  console.log(`TEMPO MÉDIO: ${(tempo / casos.length).toFixed(0)}s por pergunta`);
  console.log("=".repeat(56));
}
