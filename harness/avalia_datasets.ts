/**
 * Etapa 1 do harness: a pergunta em pt-BR escolhe os datasets certos?
 *
 *     bun harness/avalia_datasets.ts [--n 20]
 *
 * Mede contra os casos confiáveis de casos.ts, com a mesma régua de
 * scripts/avalia_douradas_perguntas.py: só os datasets **obrigatórios** contam;
 * os de apoio (marcados com `*`) não entram no denominador, porque nunca foram
 * reivindicados como necessários.
 *
 * O catálogo dos 212 datasets vai no system prompt e nunca muda entre casos —
 * é isso que faz o cache de prefixo do llama-server valer 44x. A coluna
 * `prefill` no relatório existe para provar que o cache está de fato ativo: se
 * ela parar de cair para ~0 depois do primeiro caso, alguma coisa passou a
 * variar no prefixo e a avaliação ficou 40x mais lenta em silêncio.
 */
import { carregaCasos, type Caso } from "./casos.ts";
import { listaDatasets, resolveDataset } from "./catalogo.ts";
import { pergunta, vivo } from "./modelo.ts";

const CATALOGO = listaDatasets().join("\n");

/**
 * Monta o system prompt. Com `exemplos`, entram casos já resolvidos —
 * `respostas.md` não é só gabarito, ele ensina qual dataset serve qual tipo de
 * pergunta, e o cache de prefixo faz isso custar **zero por pergunta** depois da
 * primeira chamada.
 *
 * Os exemplos precisam sair do MESMO prefixo para todos os casos avaliados: um
 * prefixo por caso (leave-one-out) invalidaria o cache e cada pergunta voltaria
 * a pagar o prefill inteiro. Daí a divisão fixa por tema em vez de LOO.
 */
function montaSistema(exemplos: Caso[]): string {
  let s =
    "Você escolhe quais datasets do espelho respondem à pergunta.\n" +
    "Catálogo completo (um por linha):\n" + CATALOGO;
  if (exemplos.length) {
    s += "\n\nExemplos já resolvidos e conferidos no beelink:\n";
    for (const e of exemplos) {
      s += `\nP: ${e.pergunta}\nD: ${e.obrigatorios.map((d) => `br_${d}`).join(", ")}\n`;
    }
  }
  s += "\n\nResponda SÓ com os nomes dos datasets escolhidos, separados por vírgula. Sem explicação.";
  return s;
}

/** Passa o que o modelo escreveu pelo resolvedor de grafia antes de comparar.
 *  Nome que não resolve fica como veio, para aparecer no relatório de falha. */
const norm = (s: string) => {
  const cru = s.trim().toLowerCase().replace(/[*\\\s.]+$/g, "");
  if (!cru) return "";
  return (resolveDataset(cru) ?? cru).replace(/^br_/, "");
};

export async function avalia(casos: Caso[], exemplos: Caso[] = []) {
  const SISTEMA = montaSistema(exemplos);
  let acertos = 0, esperados = 0, perfeitos = 0;
  const falhas: { caso: Caso; faltou: string[]; deu: string[] }[] = [];

  for (const [i, c] of casos.entries()) {
    const r = await pergunta(SISTEMA, c.pergunta, { maxTokens: 80 });
    const preditos = new Set(r.texto.split(/[,\n]/).map(norm).filter(Boolean));
    const req = new Set(c.obrigatorios.map(norm));
    const hit = [...req].filter((d) => preditos.has(d));

    acertos += hit.length;
    esperados += req.size;
    if (hit.length === req.size) perfeitos++;
    else falhas.push({ caso: c, faltou: [...req].filter((d) => !preditos.has(d)), deu: [...preditos] });

    const marca = hit.length === req.size ? "ok" : "  ";
    console.log(
      `${marca} ${String(i + 1).padStart(2)}/${casos.length} ${c.id}  ` +
      `${hit.length}/${req.size}  ${r.segundos.toFixed(1)}s  prefill=${r.prefilados}`,
    );
  }

  console.log("\n" + "=".repeat(62));
  console.log(`RECALL (datasets obrigatórios): ${acertos}/${esperados} = ${(100 * acertos / esperados).toFixed(1)}%`);
  console.log(`CASOS PERFEITOS (todos obrigatórios): ${perfeitos}/${casos.length} = ${(100 * perfeitos / casos.length).toFixed(1)}%`);
  console.log("=".repeat(62));

  if (falhas.length) {
    console.log("\nonde falhou:");
    for (const f of falhas.slice(0, 14)) {
      console.log(`  ${f.caso.id} faltou: ${f.faltou.join(", ")}`);
      console.log(`         deu: ${f.deu.slice(0, 6).join(", ")}`);
    }
  }
  return { acertos, esperados, perfeitos, falhas };
}

if (import.meta.main) {
  if (!await vivo()) {
    console.error("llama-server inalcançável. Abra o túnel:");
    console.error("  ssh -f -N -L 8099:127.0.0.1:8099 beelink");
    process.exit(1);
  }
  const arg = Bun.argv.indexOf("--n");
  const limite = arg > -1 ? Number(Bun.argv[arg + 1]) : Infinity;
  const confiaveis = carregaCasos().filter((c) => !c.suspeito);

  // Divisão por TEMA, não por caso: dentro de um tema as 5 perguntas são
  // variações do mesmo cruzamento (T02-1 e T02-2 citam ambas IDEB e ENEM), então
  // dividir por caso deixaria o vizinho quase-idêntico no prefixo e mediria
  // memória, não generalização.
  const usaFewShot = Bun.argv.includes("--fewshot");
  const temas = [...new Set(confiaveis.map((c) => c.tema))].sort((a, b) => a - b);
  const temasExemplo = new Set(temas.filter((_, i) => i % 2 === 0));

  const exemplos = usaFewShot ? confiaveis.filter((c) => temasExemplo.has(c.tema)) : [];
  const casos = confiaveis.filter((c) => !temasExemplo.has(c.tema)).slice(0, limite);

  console.log(`catálogo de ${listaDatasets().length} datasets`);
  console.log(`${casos.length} casos de teste (temas ímpares da lista)`);
  console.log(usaFewShot
    ? `${exemplos.length} exemplos no prefixo (temas pares — disjuntos do teste)\n`
    : `sem few-shot (base de comparação)\n`);
  await avalia(casos, exemplos);
}
