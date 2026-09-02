/**
 * Roda perguntas abertas pelo dsh e registra o que voltou.
 *
 *     bun harness/lote.ts perguntas.txt
 *
 * Cada pergunta é um processo `dsh --profile headless` novo, mas o cache de
 * prefixo vive no llama-server e sobrevive entre processos — medido: 16.397 de
 * 16.585 tokens vieram do cache já na primeira pergunta seguinte.
 */
import { writeFileSync } from "node:fs";

const PATCH = "harness/dsh/rodado.patch.yml";

export interface Saida {
  pergunta: string;
  resposta: string;
  segundos: number;
  /** o dsh terminou e produziu texto — NÃO quer dizer que o texto está certo */
  respondeu: boolean;
  /** o texto contém o valor conferido, quando o caso traz um */
  correto?: boolean;
  esperado?: string;
}

/**
 * Um caso com resposta conhecida. Sem isto o benchmark mede a coisa errada:
 * medido em 2026-09-02, a pergunta dos suicídios devolveu "não foram encontrados
 * óbitos" (o certo é 789) e a versão anterior deste arquivo contou como sucesso,
 * porque só checava se veio texto. Resposta errada com prosa confiante é o pior
 * resultado possível, e era o que estava sendo premiado.
 */
export interface Caso { pergunta: string; esperado?: string }

export async function roda(casos: Caso[]): Promise<Saida[]> {
  const out: Saida[] = [];
  for (const [i, caso] of casos.entries()) {
    const q = caso.pergunta;
    const t0 = Date.now();
    const p = Bun.spawn(
      ["bunx", "dsh", "--profile", "headless", "--patch", PATCH, q],
      {
        env: { ...process.env, HARNESS_LLM_KEY: "x" },
        stdout: "pipe", stderr: "pipe",
        timeout: 2_400_000, killSignal: "SIGKILL",
      },
    );
    const texto = await new Response(p.stdout).text();
    const err = await new Response(p.stderr).text();
    const code = await p.exited;
    const seg = (Date.now() - t0) / 1000;
    const resposta = (texto.trim() || err.trim()).slice(0, 4000);
    const respondeu = code === 0 && texto.trim().length > 40;
    // compara só os dígitos: 789 casa com "789", "**789**" e "789 óbitos"
    const correto = caso.esperado
      ? respondeu && resposta.replace(/[.\s]/g, "").includes(caso.esperado.replace(/[.\s]/g, ""))
      : undefined;
    out.push({ pergunta: q, resposta, segundos: seg, respondeu, correto, esperado: caso.esperado });
    const marca = correto === false ? "ERRO" : correto === true ? " ok " : respondeu ? " ?  " : "  -- ";
    console.log(`${marca} ${i + 1}/${casos.length}  ${seg.toFixed(0)}s  ${q.slice(0, 58)}`);
    if (correto === false) console.log(`      esperava ${caso.esperado} | veio: ${resposta.replace(/\s+/g, " ").slice(0, 130)}`);
    else if (!respondeu) console.log(`      (vazio)`);
  }
  return out;
}

if (import.meta.main) {
  const arquivo = Bun.argv[2];
  if (!arquivo) { console.error("uso: bun harness/lote.ts <arquivo-de-perguntas>"); process.exit(1); }
  // formato: pergunta [TAB] valor esperado (opcional)
  const casos: Caso[] = (await Bun.file(arquivo).text()).split("\n")
    .map((l) => l.trim()).filter(Boolean)
    .map((l) => { const [p, e] = l.split("\t"); return { pergunta: p!.trim(), esperado: e?.trim() }; });
  console.log(`${casos.length} perguntas pelo dsh\n`);
  const r = await roda(casos);
  const bons = r.filter((x) => x.respondeu).length;
  const medio = r.reduce((a, b) => a + b.segundos, 0) / r.length;
  console.log(`\n${"=".repeat(56)}`);
  const comGabarito = r.filter((x) => x.correto !== undefined);
  const certos = comGabarito.filter((x) => x.correto).length;
  console.log(`RESPONDEU (produziu texto): ${bons}/${r.length} = ${(100 * bons / r.length).toFixed(0)}%`);
  if (comGabarito.length) {
    console.log(`CORRETO (número confere):   ${certos}/${comGabarito.length} = ${(100 * certos / comGabarito.length).toFixed(0)}%`);
  }
  console.log(`TEMPO MÉDIO: ${medio.toFixed(0)}s por pergunta`);
  console.log("=".repeat(56));
  const saida = `benchmarks/lote_${new Date().toISOString().slice(0, 16).replace(/[:T]/g, "")}.json`;
  writeFileSync(saida, JSON.stringify(r, null, 1));
  console.log(`\ndetalhe em ${saida}`);
}
