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
 *
 * A régua de acerto vem de `acerto.ts`, e não daqui: ela estava copiada em dois
 * arquivos comparando substring de dígitos, e `789` casava dentro de `1789`.
 */
import { roda as rodaLaco } from "./laco.ts";
import { carregaCasos } from "./casos.ts";
import { avalia, configServidor, rotuloConfig, avisaPrefill, LIMIAR_PREFILL } from "./acerto.ts";

interface Caso { pergunta: string; esperado?: string }

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

  const config = await configServidor();
  console.log(`PIPELINE FIXO (laco.ts, sem MCP) — ${casos.length} perguntas — ${rotuloConfig(config)}`);
  if (!config) console.log("AVISO: sem a config do servidor, o TEMPO desta rodada não é comparável com nenhuma outra");
  console.log(`limiar de prefill: ${LIMIAR_PREFILL} tokens\n`);
  let certos = 0, comGab = 0, tempo = 0, ecos = 0, piorPrefill = 0;
  for (const [i, c] of casos.entries()) {
    const t0 = Date.now();
    const r = await rodaLaco(c.pergunta, exemplos);
    const seg = (Date.now() - t0) / 1000;
    tempo += seg;
    const texto = `${r.prosa ?? ""} ${JSON.stringify(r.linhas ?? [])}`;
    const a = avalia(texto, c.esperado, c.pergunta);
    const ok = a.veredito === "certo" ? true : a.veredito === "errado" ? false : undefined;
    if (a.eco) ecos++;
    if (ok !== undefined) { comGab++; if (ok) certos++; }
    const marca = a.eco ? "ECO " : ok === false ? "ERRO" : ok === true ? " ok " : r.erro ? "  --" : " ?  ";
    console.log(`${marca} ${i + 1}/${casos.length}  ${seg.toFixed(0)}s  ${r.tentativas} tentativa(s)  ${c.pergunta.slice(0, 50)}`);
    if (r.erro) console.log(`      ${r.erro}`);
    else if (a.eco) console.log(`      esperado ${c.esperado} aparece na própria pergunta — caso fora do denominador`);
    else if (ok === false) console.log(`      esperava ${c.esperado} | n=${r.n} | ${(r.prosa ?? "").replace(/\s+/g, " ").slice(0, 110)}`);

    // `laco.ts` já devolve o maior `timings.prompt_n` das 4 chamadas do caso, e
    // ninguém olhava. O primeiro caso prefila o prefixo inteiro por definição.
    if (i > 0) {
      piorPrefill = Math.max(piorPrefill, r.prefiladosMax);
      const aviso = avisaPrefill([r.prefiladosMax]);
      if (aviso) console.log(`      ${aviso}`);
    }
  }
  console.log(`\n${"=".repeat(56)}`);
  if (comGab) console.log(`CORRETO: ${certos}/${comGab} = ${(100 * certos / comGab).toFixed(0)}%`);
  if (ecos) console.log(`FORA DO DENOMINADOR: ${ecos} caso(s) cujo esperado ecoa na pergunta`);
  console.log(`TEMPO MÉDIO: ${(tempo / casos.length).toFixed(0)}s por pergunta  [${rotuloConfig(config)}]`);
  if (piorPrefill) console.log(`PIOR PREFILL após o aquecimento: ${piorPrefill} tokens (limiar ${LIMIAR_PREFILL})`);
  console.log("=".repeat(56));
}
