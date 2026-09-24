/**
 * Roda perguntas abertas pelo Pi (pi.ts) e registra o que voltou.
 *
 *     bun harness/lote.ts perguntas.txt
 *     bun harness/lote.ts --diff benchmarks/a.json benchmarks/b.json
 *
 * Cada pergunta é um processo `pi --print` novo, mas o cache de
 * prefixo vive no llama-server e sobrevive entre processos — medido: 16.397 de
 * 16.585 tokens vieram do cache já na primeira pergunta seguinte. Esse cache é
 * a diferença entre 6 min e ~40 min por caso e quebra em silêncio: a checagem
 * de prefill abaixo existe por isso.
 *
 * Todo tempo registrado carrega o `-np`/`-c` que o produziu. Rodada 8: `-np 5`
 * levou o total de 20,9 para 15,2 min (−27%, não 5x) — sem a config no arquivo,
 * a comparação seguinte lê isso como ganho do harness.
 */
import { writeFileSync, readFileSync, readdirSync, statSync } from "node:fs";
import {
  avalia, configServidor, rotuloConfig, avisaConfigDivergente,
  avisaPrefill, marcaDoLog, prefillsDesde, LIMIAR_PREFILL, confereBoot, nsDaSessao, trocasDeBuild,
  type ConfigServidor,
} from "./acerto.ts";
import { sobeGuarda, resumoGuarda, type Estatistica } from "./guarda.ts";
import { garanteTunel } from "./modelo.ts";
import { comandoPi, SESSOES } from "./pi.ts";

const RAIZ = new URL("..", import.meta.url).pathname;

export interface Saida {
  pergunta: string;
  resposta: string;
  segundos: number;
  /** o laço terminou e produziu texto — NÃO quer dizer que o texto está certo */
  respondeu: boolean;
  /** o texto contém o valor conferido, quando o caso traz um.
   *  `undefined` = não medível (sem gabarito, ou o esperado ecoa na pergunta) */
  correto?: boolean;
  esperado?: string;
  /** o valor esperado também está escrito na pergunta: um papagaio passaria */
  eco?: boolean;
  /** maior prefill visto no llama-server durante o caso — inclui resultado de
   *  ferramenta grande no meio da conversa, então alto NÃO quer dizer cache quebrado */
  prefillMax?: number;
  /** prefill da 1ª requisição do caso: é ali que o prefixo é lido, e é este que
   *  diz se o cache viveu */
  prefillInicial?: number;
  /** quantas vezes o caso foi tentado — 1 é o normal; >1 é o workaround do item 10 agindo */
  tentativas: number;
  /** turnos repetidos/resgatados por guarda.ts, somados entre as tentativas */
  guarda?: Estatistica;
  /** os `n` que as consultas da sessão devolveram (`nsDaSessao`) — diagnóstico,
   *  não entra em `correto` */
  nNaSql?: number[];
  /** errou na prosa, mas o esperado estava num `n` da SQL: apurou e não escreveu */
  nSoNaSql?: boolean;
  /** commit do llama.cpp no ar logo depois do caso (`build_info` do /props) */
  build?: string;
}

/** Arquivo de saída — o tempo sem a config que o produziu não é comparável. */
export interface Rodada {
  gerado: string;
  config?: ConfigServidor;
  /** o laço que produziu a rodada; ausente = dsh, o único antes de 2026-09-24 */
  cliente?: "dsh" | "pi" | "omp";
  casos: Saida[];
  /** onde o build do llama.cpp mudou no meio da rodada — vazio/ausente = não mudou */
  trocasDeBuild?: { caso: number; de: string; para: string }[];
}

/**
 * Um caso com resposta conhecida. Sem isto o benchmark mede a coisa errada:
 * medido em 2026-09-02, a pergunta dos suicídios devolveu "não foram encontrados
 * óbitos" (o certo é 789) e a versão anterior deste arquivo contou como sucesso,
 * porque só checava se veio texto. Resposta errada com prosa confiante é o pior
 * resultado possível, e era o que estava sendo premiado.
 */
export interface Caso { pergunta: string; esperado?: string }

/** Uma tentativa isolada — um processo `pi` do começo ao fim. */
interface Tentativa {
  resposta: string;
  segundos: number;
  respondeu: boolean;
  prefillMax?: number;
  prefillInicial?: number;
  semLog: boolean;
  guarda: Estatistica;
  nNaSql?: number[];
}

/**
 * Quantas vezes tentar uma pergunta antes de desistir. harness_tasks.md B10:
 * medido 2026-09-03, 4 de 6 sessões reais terminaram com a chamada de
 * ferramenta do Gemma caindo como texto solto (formato nativo do modelo,
 * `<|tool_call>...<tool_call|>`, que o parser do llama-server às vezes não
 * reconhece) — o laço não imprime nada nesse caso, então `respondeu` fica
 * `false` mesmo com `code === 0`. Não é erro de raciocínio: casos 1 e 5, com
 * sessões do mesmo tamanho, completaram normalmente — é probabilístico por
 * turno, então repetir a MESMA pergunta num processo novo tem boa chance
 * de não bater o mesmo bug de novo. Não conserta a causa raiz (aberta,
 * bloqueando em `harness_tasks.md`); é o workaround que torna a rodada usável
 * enquanto ela não fecha.
 */
const MAX_TENTATIVAS = Number(Bun.env.HARNESS_TENTATIVAS ?? 3);

async function rodaUmaVez(q: string): Promise<Tentativa> {
  if (!await garanteTunel()) console.log("      (llama-server inalcançável mesmo reabrindo o túnel)");
  // O prefill não volta pelo stdout do Pi — cada pergunta é outro processo.
  // A marca no log do llama-server é o que sobra para saber se o cache viveu.
  const marca = await marcaDoLog();
  const guarda = sobeGuarda();
  const t0 = Date.now();
  const { cmd, env } = comandoPi(q, guarda.url);
  const p = Bun.spawn(cmd, {
    cwd: RAIZ, env,
    stdin: "ignore",
    stdout: "pipe", stderr: "pipe",
    timeout: 2_400_000, killSignal: "SIGKILL",
  });
  const texto = await new Response(p.stdout).text();
  const err = await new Response(p.stderr).text();
  const code = await p.exited;
  const nNaSql = nsDaUltimaSessao(t0);
  guarda.para();
  const seg = (Date.now() - t0) / 1000;
  const resposta = (texto.trim() || err.trim()).slice(0, 4000);
  const respondeu = code === 0 && texto.trim().length > 40;

  const prefills = await prefillsDesde(marca);
  const prefillMax = prefills?.length ? Math.max(...prefills) : undefined;
  const prefillInicial = prefills?.[0];
  return { resposta, segundos: seg, respondeu, prefillMax, prefillInicial, semLog: prefills === undefined, guarda: guarda.stats, nNaSql };
}

/** A sessão que o Pi gravou para este caso: o .jsonl mais novo desde `t0`. */
function nsDaUltimaSessao(t0: number): number[] | undefined {
  try {
    const arq = readdirSync(SESSOES).filter((a) => a.endsWith(".jsonl"))
      .map((a) => ({ a: `${SESSOES}/${a}`, m: statSync(`${SESSOES}/${a}`).mtimeMs }))
      .filter((x) => x.m >= t0).sort((x, y) => y.m - x.m)[0];
    return arq ? nsDaSessao(readFileSync(arq.a, "utf8")) : undefined;
  } catch { return undefined; }
}

export async function roda(casos: Caso[], aoCaso?: (feitos: Saida[]) => void, buildInicial?: string): Promise<Saida[]> {
  const out: Saida[] = [];
  let buildAnterior = buildInicial;
  let semLog = false;
  for (const [i, caso] of casos.entries()) {
    const q = caso.pergunta;
    let tentativa = await rodaUmaVez(q);
    let tentativas = 1;
    let segundos = tentativa.segundos;
    let prefillMax = tentativa.prefillMax;
    const prefillInicial = tentativa.prefillInicial;
    const guarda: Estatistica = { ...tentativa.guarda };
    // Retentativa: só quando o laço terminou sem produzir NADA (item 10) — uma
    // resposta que veio, mesmo errada, não se repete: é erro de raciocínio,
    // não do bug de parsing, e repetir esconderia o número real de acerto.
    while (!tentativa.respondeu && tentativas < MAX_TENTATIVAS) {
      tentativas++;
      console.log(`      (vazio — tentativa ${tentativas}/${MAX_TENTATIVAS}, workaround do item 10)`);
      tentativa = await rodaUmaVez(q);
      segundos += tentativa.segundos;
      prefillMax = Math.max(prefillMax ?? 0, tentativa.prefillMax ?? 0) || undefined;
      for (const k of ["turnos", "repetidos", "resgatados", "perdidos"] as const) guarda[k] += tentativa.guarda[k];
      guarda.contextoMax = Math.max(guarda.contextoMax, tentativa.guarda.contextoMax);
    }
    if (tentativa.semLog && !semLog) {
      semLog = true;
      console.log("      (sem leitura do log do llama-server — o cache de prefixo NÃO está sendo conferido)");
    }
    const { resposta, respondeu } = tentativa;
    // fronteira de número, não substring: `789` não pode casar dentro de `1789`
    const a = avalia(resposta, caso.esperado, q);
    const correto = a.veredito === "sem_gabarito" || a.veredito === "eco"
      ? undefined
      : respondeu && a.certo;

    const nNaSql = tentativa.nNaSql?.length ? [...new Set(tentativa.nNaSql)] : undefined;
    const alvo = Number(caso.esperado);
    const nSoNaSql = correto === false && Number.isFinite(alvo) && nNaSql?.includes(alvo) ? true : undefined;
    // Medido 2026-09-24: 6b790a9 no lugar de f072b10 no meio da rodada B2, e
    // nada no JSON registrou — o build é relido a cada caso, não só no começo.
    const build = (await configServidor())?.build;
    out.push({ pergunta: q, resposta, segundos, respondeu, correto, esperado: caso.esperado, eco: a.eco || undefined, prefillMax, prefillInicial, tentativas, guarda, nNaSql, nSoNaSql, build });
    const marcaLinha = a.eco ? "ECO " : correto === false ? "ERRO" : correto === true ? " ok " : respondeu ? " ?  " : "  -- ";
    const sufixoTentativas = tentativas > 1 ? ` (${tentativas} tentativas)` : "";
    console.log(`${marcaLinha} ${i + 1}/${casos.length}  ${segundos.toFixed(0)}s${sufixoTentativas}  ${q.slice(0, 58)}`);
    if (a.eco) console.log(`      esperado ${caso.esperado} aparece na própria pergunta — caso fora do denominador`);
    else if (correto === false) console.log(`      esperava ${caso.esperado} | veio: ${resposta.replace(/\s+/g, " ").slice(0, 130)}`);
    if (correto === false) console.log(nSoNaSql
      ? `      o n ${caso.esperado} estava na SQL e não na resposta`
      : `      n na SQL: ${nNaSql?.slice(0, 8).join(", ") ?? "nenhum"}`);
    else if (!respondeu) console.log(`      (vazio após ${tentativas} tentativas)`);
    console.log(`      ${resumoGuarda(guarda)}`);
    if (build && buildAnterior && build !== buildAnterior) {
      console.log(`      AVISO: o llama.cpp trocou de build no meio da rodada (${buildAnterior} → ${build}) — ` +
        `os casos daqui em diante NÃO são comparáveis com os anteriores`);
    }
    if (build) buildAnterior = build;
    aoCaso?.(out);

    // O primeiro caso fica de fora: `confereBoot()` acabou de mandar a conversa
    // de teste de `servidor.sh aquece`, e com `-np 1` ela tira o prefixo do laço
    // do slot — o 1º caso paga o prefixo inteiro sempre (~4.500 tokens, medido
    // 2026-09-24). Do segundo em diante, prefixo inteiro prefilado é cache
    // quebrado: a rodada continua CERTA e fica ~7x mais lenta.
    // Olha a 1ª requisição do caso, onde o prefixo é lido — não o maior prefill:
    // numa pergunta de pesquisa um resultado de ferramenta grande no meio da
    // conversa passa do limiar sem cache nenhum quebrado (6.830 tokens medidos
    // em 2026-09-24).
    if (i > 0 && prefillInicial) {
      const aviso = avisaPrefill([prefillInicial]);
      if (aviso) console.log(`      ${aviso}`);
    }
  }
  return out;
}

/** Compara dois arquivos de rodada. O aviso de config é o ponto. */
function diff(arqA: string, arqB: string, a: Rodada, b: Rodada) {
  const conta = (r: Rodada) => {
    const casos = r.casos;
    const gab = casos.filter((x) => x.correto !== undefined);
    return {
      n: casos.length,
      certos: gab.filter((x) => x.correto).length,
      comGab: gab.length,
      minutos: casos.reduce((s, x) => s + x.segundos, 0) / 60,
    };
  };
  const ca = conta(a), cb = conta(b);
  for (const [arq, r, c] of [[arqA, a, ca], [arqB, b, cb]] as const) {
    console.log(`${arq}`);
    console.log(`  ${r.cliente ?? "dsh"} · ${rotuloConfig(r.config)}`);
    console.log(`  ${c.certos}/${c.comGab} certos em ${c.n} casos · ${c.minutos.toFixed(1)} min`);
  }
  const aviso = avisaConfigDivergente(a.config, b.config, arqA, arqB);
  console.log(aviso ? `\n${aviso}` : `\nconfig idêntica — os tempos são comparáveis`);
}

/** Aceita o formato novo ({config, casos}) e os arquivos antigos, que eram só o array. */
function leRodada(bruto: unknown): Rodada {
  if (Array.isArray(bruto)) return { gerado: "?", casos: bruto as Saida[] };
  return bruto as Rodada;
}

if (import.meta.main) {
  if (Bun.argv[2] === "--diff") {
    const [, , , a, b] = Bun.argv;
    if (!a || !b) { console.error("uso: bun harness/lote.ts --diff <a.json> <b.json>"); process.exit(1); }
    diff(a, b, leRodada(await Bun.file(a).json()), leRodada(await Bun.file(b).json()));
    process.exit(0);
  }

  const arquivo = Bun.argv[2];
  if (!arquivo) { console.error("uso: bun harness/lote.ts <arquivo-de-perguntas>"); process.exit(1); }

  // harness_tasks.md O2: confere raciocínio desligado e cache de prefixo
  // vivo ANTES de gastar horas rodando com um servidor mal configurado.
  console.log("conferindo o boot do servidor…");
  if (!await confereBoot()) {
    console.error("\nboot reprovado — ver mensagem acima. Rodando mesmo assim seria o desperdício mais caro disponível aqui.");
    process.exit(1);
  }
  console.log();

  // formato: pergunta [TAB] valor esperado (opcional) — o que `casos.ts --tsv` emite
  const casos: Caso[] = (await Bun.file(arquivo).text()).split("\n")
    .map((l) => l.trim()).filter((l) => l && !l.startsWith("#"))
    .map((l) => { const [p, e] = l.split("\t"); return { pergunta: p!.trim(), esperado: e?.trim() }; });
  const config = await configServidor();
  console.log(`${casos.length} perguntas pelo Pi — ${rotuloConfig(config)}`);
  if (!config) console.log("AVISO: sem a config do servidor, o TEMPO desta rodada não é comparável com nenhuma outra");
  console.log(`limiar de prefill: ${LIMIAR_PREFILL} tokens\n`);
  // Gravado a cada caso, não só no fim: as rodadas de 2026-09-03 dos casos com
  // `n` foram interrompidas no meio e perderam o que já tinham rodado.
  const saida = `${RAIZ}harness/benchmarks/lote_${new Date().toISOString().slice(0, 16).replace(/[:T]/g, "")}.json`;
  const grava = (casosFeitos: Saida[]) =>
    writeFileSync(saida, JSON.stringify({
      gerado: new Date().toISOString(), config, cliente: "pi", casos: casosFeitos,
      trocasDeBuild: trocasDeBuild(casosFeitos.map((c) => c.build), config?.build),
    } satisfies Rodada, null, 1));
  const r = await roda(casos, grava, config?.build);
  const bons = r.filter((x) => x.respondeu).length;
  const medio = r.reduce((a, b) => a + b.segundos, 0) / r.length;
  console.log(`\n${"=".repeat(56)}`);
  const comGabarito = r.filter((x) => x.correto !== undefined);
  const certos = comGabarito.filter((x) => x.correto).length;
  const ecos = r.filter((x) => x.eco).length;
  console.log(`RESPONDEU (produziu texto): ${bons}/${r.length} = ${(100 * bons / r.length).toFixed(0)}%`);
  if (comGabarito.length) {
    console.log(`CORRETO (número confere):   ${certos}/${comGabarito.length} = ${(100 * certos / comGabarito.length).toFixed(0)}%`);
  }
  if (ecos) console.log(`FORA DO DENOMINADOR: ${ecos} caso(s) cujo esperado ecoa na pergunta — troque o valor esperado, não o modelo`);
  console.log(`TEMPO MÉDIO: ${medio.toFixed(0)}s por pergunta  [${rotuloConfig(config)}]`);
  const piorPrefill = Math.max(0, ...r.slice(1).map((x) => x.prefillInicial ?? 0));
  if (piorPrefill) console.log(`PIOR PREFILL INICIAL após o 1º caso: ${piorPrefill} tokens (limiar ${LIMIAR_PREFILL})`);
  for (const t of trocasDeBuild(r.map((c) => c.build), config?.build)) {
    console.log(`BUILD TROCOU no caso ${t.caso}: llama.cpp ${t.de} → ${t.para}`);
  }
  console.log("=".repeat(56));
  grava(r);
  console.log(`\ndetalhe em ${saida}`);
}
