/**
 * Roda perguntas abertas pelo dsh e registra o que voltou.
 *
 *     bun harness/lote.ts perguntas.txt
 *     bun harness/lote.ts --diff benchmarks/a.json benchmarks/b.json
 *
 * Cada pergunta é um processo `dsh --profile headless` novo, mas o cache de
 * prefixo vive no llama-server e sobrevive entre processos — medido: 16.397 de
 * 16.585 tokens vieram do cache já na primeira pergunta seguinte. Esse cache é
 * a diferença entre 6 min e ~40 min por caso e quebra em silêncio: a checagem
 * de prefill abaixo existe por isso.
 *
 * Todo tempo registrado carrega o `-np`/`-c` que o produziu. Rodada 8: `-np 5`
 * levou o total de 20,9 para 15,2 min (−27%, não 5x) — sem a config no arquivo,
 * a comparação seguinte lê isso como ganho do harness.
 */
import { writeFileSync } from "node:fs";
import {
  avalia, configServidor, rotuloConfig, avisaConfigDivergente,
  avisaPrefill, marcaDoLog, prefillsDesde, LIMIAR_PREFILL, confereBoot,
  type ConfigServidor,
} from "./acerto.ts";
import { sobeGuarda, resumoGuarda, type Estatistica } from "./guarda.ts";
import { garanteTunel } from "./modelo.ts";
import { comandoPi, comandoOmp } from "./pi.ts";

const RAIZ = new URL("..", import.meta.url).pathname;
const PATCH = "harness/dsh/rodado.patch.yml";
/** O laço agêntico: `dsh` (padrão), `pi` ou `omp` — tasks/pi_no_lugar_do_dsh.md. */
export type Cliente = "dsh" | "pi" | "omp";
const CLIENTE = (Bun.env.HARNESS_CLIENTE ?? "dsh") as Cliente;

export interface Saida {
  pergunta: string;
  resposta: string;
  segundos: number;
  /** o dsh terminou e produziu texto — NÃO quer dizer que o texto está certo */
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
}

/** Arquivo de saída — o tempo sem a config que o produziu não é comparável. */
export interface Rodada {
  gerado: string;
  config?: ConfigServidor;
  /** ausente = dsh, o único que existia antes */
  cliente?: Cliente;
  casos: Saida[];
}

/**
 * Um caso com resposta conhecida. Sem isto o benchmark mede a coisa errada:
 * medido em 2026-09-02, a pergunta dos suicídios devolveu "não foram encontrados
 * óbitos" (o certo é 789) e a versão anterior deste arquivo contou como sucesso,
 * porque só checava se veio texto. Resposta errada com prosa confiante é o pior
 * resultado possível, e era o que estava sendo premiado.
 */
export interface Caso { pergunta: string; esperado?: string }

/** Uma tentativa isolada — um processo `dsh` do começo ao fim. */
interface Tentativa {
  resposta: string;
  segundos: number;
  respondeu: boolean;
  prefillMax?: number;
  prefillInicial?: number;
  semLog: boolean;
  guarda: Estatistica;
}

/**
 * Quantas vezes tentar uma pergunta antes de desistir. backlog.md item 10:
 * medido 2026-09-03, 4 de 6 sessões reais terminaram com a chamada de
 * ferramenta do Gemma caindo como texto solto (formato nativo do modelo,
 * `<|tool_call>...<tool_call|>`, que o parser do llama-server às vezes não
 * reconhece) — o dsh não imprime nada nesse caso, então `respondeu` fica
 * `false` mesmo com `code === 0`. Não é erro de raciocínio: casos 1 e 5, com
 * sessões do mesmo tamanho, completaram normalmente — é probabilístico por
 * turno, então repetir a MESMA pergunta numa sessão `dsh` nova tem boa chance
 * de não bater o mesmo bug de novo. Não conserta a causa raiz (aberta,
 * bloqueando em `backlog.md`); é o workaround que torna a rodada usável
 * enquanto ela não fecha.
 */
const MAX_TENTATIVAS = Number(Bun.env.HARNESS_TENTATIVAS ?? 3);

async function rodaUmaVez(q: string): Promise<Tentativa> {
  if (!await garanteTunel()) console.log("      (llama-server inalcançável mesmo reabrindo o túnel)");
  // O prefill não volta pelo stdout do dsh — cada pergunta é outro processo.
  // A marca no log do llama-server é o que sobra para saber se o cache viveu.
  const marca = await marcaDoLog();
  const guarda = sobeGuarda();
  const t0 = Date.now();
  const { cmd, env } = CLIENTE === "pi" ? comandoPi(q, guarda.url)
    : CLIENTE === "omp" ? comandoOmp(q, guarda.url)
    : {
      cmd: ["bunx", "dsh", "--profile", "headless", "--patch", PATCH, q],
      env: { ...process.env, HARNESS_LLM_KEY: "x", HARNESS_LLM_URL: guarda.url, HARNESS_PERGUNTA: q },
    };
  const p = Bun.spawn(cmd, {
    cwd: RAIZ, env,
    // o omp em -p espera stdin fechado; com um pipe aberto trava em readPipedInput
    stdin: "ignore",
    stdout: "pipe", stderr: "pipe",
    timeout: 2_400_000, killSignal: "SIGKILL",
  });
  const texto = await new Response(p.stdout).text();
  const err = await new Response(p.stderr).text();
  const code = await p.exited;
  guarda.para();
  const seg = (Date.now() - t0) / 1000;
  const resposta = (texto.trim() || err.trim()).slice(0, 4000);
  const respondeu = code === 0 && texto.trim().length > 40;

  const prefills = await prefillsDesde(marca);
  const prefillMax = prefills?.length ? Math.max(...prefills) : undefined;
  const prefillInicial = prefills?.[0];
  return { resposta, segundos: seg, respondeu, prefillMax, prefillInicial, semLog: prefills === undefined, guarda: guarda.stats };
}

export async function roda(casos: Caso[], aoCaso?: (feitos: Saida[]) => void): Promise<Saida[]> {
  const out: Saida[] = [];
  let semLog = false;
  for (const [i, caso] of casos.entries()) {
    const q = caso.pergunta;
    let tentativa = await rodaUmaVez(q);
    let tentativas = 1;
    let segundos = tentativa.segundos;
    let prefillMax = tentativa.prefillMax;
    const prefillInicial = tentativa.prefillInicial;
    const guarda: Estatistica = { ...tentativa.guarda };
    // Retentativa: só quando o dsh terminou sem produzir NADA (item 10) — uma
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

    out.push({ pergunta: q, resposta, segundos, respondeu, correto, esperado: caso.esperado, eco: a.eco || undefined, prefillMax, prefillInicial, tentativas, guarda });
    const marcaLinha = a.eco ? "ECO " : correto === false ? "ERRO" : correto === true ? " ok " : respondeu ? " ?  " : "  -- ";
    const sufixoTentativas = tentativas > 1 ? ` (${tentativas} tentativas)` : "";
    console.log(`${marcaLinha} ${i + 1}/${casos.length}  ${segundos.toFixed(0)}s${sufixoTentativas}  ${q.slice(0, 58)}`);
    if (a.eco) console.log(`      esperado ${caso.esperado} aparece na própria pergunta — caso fora do denominador`);
    else if (correto === false) console.log(`      esperava ${caso.esperado} | veio: ${resposta.replace(/\s+/g, " ").slice(0, 130)}`);
    else if (!respondeu) console.log(`      (vazio após ${tentativas} tentativas)`);
    console.log(`      ${resumoGuarda(guarda)}`);
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

  // operacao.md tarefa 2: confere raciocínio desligado e cache de prefixo
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
  console.log(`${casos.length} perguntas pelo ${CLIENTE} — ${rotuloConfig(config)}`);
  if (!config) console.log("AVISO: sem a config do servidor, o TEMPO desta rodada não é comparável com nenhuma outra");
  console.log(`limiar de prefill: ${LIMIAR_PREFILL} tokens\n`);
  // Gravado a cada caso, não só no fim: as rodadas de 2026-09-03 dos casos com
  // `n` foram interrompidas no meio e perderam o que já tinham rodado.
  const saida = `${RAIZ}harness/benchmarks/lote_${new Date().toISOString().slice(0, 16).replace(/[:T]/g, "")}.json`;
  const grava = (casosFeitos: Saida[]) =>
    writeFileSync(saida, JSON.stringify({ gerado: new Date().toISOString(), config, cliente: CLIENTE, casos: casosFeitos } satisfies Rodada, null, 1));
  const r = await roda(casos, grava);
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
  console.log("=".repeat(56));
  grava(r);
  console.log(`\ndetalhe em ${saida}`);
}
