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
import { carregaCasos, carregaTodasPerguntas, exemplosIndependentes, type Caso } from "./casos.ts";
import { listaDatasets, resolveDataset } from "./catalogo.ts";
import { catalogoComPistas } from "./desambigua.ts";
import { pergunta, vivo } from "./modelo.ts";

// item 1 do backlog: sem a pista contrastiva aqui, esta avaliação mede a régua
// de ANTES do conserto — o próprio erro que motivou o item, medindo o catálogo
// sem a descrição que deveria estar sendo testada.
const CATALOGO = catalogoComPistas();

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

/** Slots paralelos do llama-server. O `-np` do servidor tem que casar com isto:
 *  com `-np 1` as requisições só enfileiram e o paralelismo é ilusório. */
const PARALELO = Number(Bun.env.HARNESS_PARALELO ?? 5);

export async function avalia(casos: Caso[], exemplos: Caso[] = []) {
  const SISTEMA = montaSistema(exemplos);
  let acertos = 0, esperados = 0, perfeitos = 0, erros = 0, feitos = 0;
  const falhas: { caso: Caso; faltou: string[]; deu: string[] }[] = [];

  // A primeira chamada sozinha, para o prefixo entrar no cache antes de abrir as
  // paralelas: disparar 5 de uma vez com o cache frio faz as 5 pagarem o prefill
  // inteiro em vez de uma só.
  const aquecer = casos[0];
  if (aquecer) await pergunta(SISTEMA, aquecer.pergunta, { maxTokens: 8 }).catch(() => {});

  const fila = [...casos];
  async function trabalhador() {
    for (;;) {
      const c = fila.shift();
      if (!c) return;
      let r;
      try {
        r = await pergunta(SISTEMA, c.pergunta, { maxTokens: 80 });
      } catch (e) {
        // Um caso que estoura não pode derrubar a avaliação inteira: antes disso
        // um TimeoutError perdia as 273 restantes.
        erros++; feitos++;
        console.log(`ERR ${feitos}/${casos.length} ${c.id}  ${String(e).slice(0, 60)}`);
        continue;
      }
      const preditos = new Set(r.texto.split(/[,\n]/).map(norm).filter(Boolean));
      const req = new Set(c.obrigatorios.map(norm));
      const hit = [...req].filter((d) => preditos.has(d));

      acertos += hit.length;
      esperados += req.size;
      feitos++;
      if (hit.length === req.size) perfeitos++;
      else falhas.push({ caso: c, faltou: [...req].filter((d) => !preditos.has(d)), deu: [...preditos] });

      const marca = hit.length === req.size ? "ok " : "   ";
      console.log(
        `${marca}${String(feitos).padStart(3)}/${casos.length} ${c.id}  ` +
        `${hit.length}/${req.size}  ${r.segundos.toFixed(1)}s  prefill=${r.prefilados}`,
      );
    }
  }
  const t0 = Date.now();
  await Promise.all(Array.from({ length: PARALELO }, trabalhador));
  const mins = (Date.now() - t0) / 60000;
  console.log(`\n${feitos} casos em ${mins.toFixed(1)} min com ${PARALELO} em paralelo (${erros} erro(s))`);

  console.log("\n" + "=".repeat(62));
  console.log(`RECALL (datasets obrigatórios): ${acertos}/${esperados} = ${(100 * acertos / esperados).toFixed(1)}%`);
  console.log(`CASOS PERFEITOS (todos obrigatórios): ${perfeitos}/${casos.length} = ${(100 * perfeitos / casos.length).toFixed(1)}%`);
  console.log("=".repeat(62));

  // Taxonomia das falhas — o ponto de uma avaliação não é o número, é saber o
  // que consertar. Cada classe abaixo aponta para um conserto diferente:
  // "nao_existe" é grafia (resolveDataset), "vizinho" é o modelo escolhendo o
  // parente errado (few-shot ou desambiguação no catálogo), "nada_perto" é
  // recuperação de fato falhando.
  const classe = (faltou: string[], deu: string[]) => {
    const perdido = faltou[0] ?? "";
    if (!deu.length) return "sem_resposta";
    if (deu.some((d) => d.split("_")[0] === perdido.split("_")[0])) return "vizinho";
    if (perdido && !listaDatasets().some((d) => d.replace(/^br_/, "") === perdido)) return "nao_existe";
    return "nada_perto";
  };

  if (falhas.length) {
    const porClasse = new Map<string, typeof falhas>();
    for (const f of falhas) {
      const c = classe(f.faltou, f.deu);
      (porClasse.get(c) ?? porClasse.set(c, []).get(c)!).push(f);
    }
    console.log("\nFALHAS POR CLASSE (cada uma aponta um conserto diferente):");
    for (const [c, fs] of [...porClasse].sort((a, b) => b[1].length - a[1].length)) {
      console.log(`\n  ${c}: ${fs.length}`);
      for (const f of fs.slice(0, 6)) {
        console.log(`    ${f.caso.id} faltou ${f.faltou.join(", ")} | deu ${f.deu.slice(0, 4).join(", ")}`);
      }
      if (fs.length > 6) console.log(`    … +${fs.length - 6}`);
    }
    // o que mais some, em qualquer classe
    const cont = new Map<string, number>();
    for (const f of falhas) for (const d of f.faltou) cont.set(d, (cont.get(d) ?? 0) + 1);
    console.log("\nDATASETS QUE MAIS ESCAPAM:");
    for (const [d, n] of [...cont].sort((a, b) => b[1] - a[1]).slice(0, 10)) {
      console.log(`    ${n}x  ${d}`);
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
  // Exemplos de FONTE INDEPENDENTE (docs/relatorio-social/), não do conjunto de
  // teste. Antes eu tirava metade das perguntas para o prefixo e media na outra
  // metade — 36 viravam exemplo e sobravam 45. Vindos de fora, as 274 inteiras
  // viram teste, e não há vazamento a policiar.
  const usaFewShot = !Bun.argv.includes("--sem-fewshot");
  const exemplos = usaFewShot
    ? exemplosIndependentes().map((e) => ({ ...e, id: "ext", tema: 0, item: 0, apoio: [],
        gabarito: "", suspeito: false } as Caso))
    : [];

  const arg2 = Bun.argv.indexOf("--n");
  const lim = arg2 > -1 ? Number(Bun.argv[arg2 + 1]) : Infinity;
  const casos = carregaTodasPerguntas()
    .map((c) => ({ ...c, gabarito: "", suspeito: false } as Caso))
    .slice(0, lim);

  console.log(`catálogo de ${listaDatasets().length} datasets`);
  console.log(`${casos.length} perguntas de teste (TODAS as de perguntas.md)`);
  console.log(`  ${casos.filter((c) => c.obrigatorios.length > 1).length} exigem 2+ datasets`);
  console.log(usaFewShot
    ? `${exemplos.length} exemplos de fonte independente (docs/relatorio-social/)\n`
    : `sem few-shot (base de comparação)\n`);
  await avalia(casos, exemplos);
}
