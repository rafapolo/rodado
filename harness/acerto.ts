/**
 * A régua do harness: o que conta como acerto, e sob que condições o tempo
 * medido significa alguma coisa.
 *
 * Três coisas moram aqui porque as três já falsearam um resultado sem dar erro:
 *
 *  1. **Acerto por fronteira de número.** A versão anterior comparava por
 *     substring de dígitos (`resposta.replace(/[.\s]/g,"").includes(esperado)`),
 *     copiada em `lote.ts` e `compara.ts`. Ela conta `789` como achado dentro de
 *     `1789`, e um esperado `2022` casa com o ano escrito na própria pergunta.
 *     Falso positivo silencioso — a mesma classe que já premiou "não foram
 *     encontrados óbitos" como acerto por rodadas seguidas. Estar em dois
 *     arquivos era metade do problema: consertar um e esquecer o outro é o
 *     desfecho provável. Agora é uma implementação só.
 *  2. **Config do servidor junto do tempo.** Rodada 8: `-np 5` levou o total de
 *     20,9 para 15,2 min (−27%, não 5x). Dois arquivos de saída comparados sem o
 *     `-np` de cada um viram "ganho do harness" o que é só config diferente.
 *  3. **Prefill por caso.** Com o cache de prefixo quebrado a rodada continua
 *     *correta* e fica ~7x mais lenta — passa por "o beelink hoje está pesado".
 *     `timings.prompt_n` (e a linha `prompt eval time` do log) é o único sinal.
 *
 * Está tudo num módulo só de propósito: é o mínimo que quem for confiar num
 * número medido precisa importar.
 */

// ---------------------------------------------------------------- 1. o acerto

/**
 * Números em notação pt-BR, na ordem em que aparecem.
 *
 * Duas alternativas, nesta ordem — a primeira exige grupo de milhar completo
 * (`1.234`, `1 657`), a segunda é o número simples com decimal por vírgula:
 *
 *     "1789"        -> [1789]        e NUNCA [789]: a varredura é da esquerda
 *                                    para a direita e consome o token inteiro
 *     "**789**"     -> [789]
 *     "789 óbitos"  -> [789]
 *     "R$ 1.234,56" -> [1234.56]
 *     "789,5"       -> [789.5]       e por isso não casa com 789
 *     "em 2022, 789"-> [2022, 789]
 *
 * Limite conhecido e aceito: `5 123` como dois números distintos separados por
 * espaço vira 5123. O separador de milhar por espaço aparece em respostas.md
 * ("1 657") e vale mais que essa ambiguidade — e o erro que ele causa é falso
 * NEGATIVO (deixa de achar), que é barulhento, não silencioso.
 */
const NUMERO = /\d{1,3}(?:[.\u00a0 ]\d{3})+(?:,\d+)?|\d+(?:,\d+)?/g;

export function numeros(texto: string): number[] {
  const out: number[] = [];
  for (const m of texto.matchAll(NUMERO)) {
    const v = normalizaNumero(m[0]);
    if (v !== undefined) out.push(v);
  }
  return out;
}

/** "1.234,56" -> 1234.56; "1 657" -> 1657; "789" -> 789. */
export function normalizaNumero(s: string): number | undefined {
  const limpo = s.replace(/[.\s\u00a0]/g, "").replace(",", ".");
  if (!limpo || !/^\d/.test(limpo)) return undefined;
  const v = Number(limpo);
  return Number.isFinite(v) ? v : undefined;
}

export type Veredito =
  /** o valor esperado está na resposta, como número inteiro delimitado */
  | "certo"
  /** há gabarito e o valor não está lá */
  | "errado"
  /** o caso não traz valor esperado — só dá para dizer se respondeu */
  | "sem_gabarito"
  /** o valor esperado também está escrito na pergunta: o caso não mede nada */
  | "eco";

export interface Acerto {
  veredito: Veredito;
  /** só `veredito === "certo"` */
  certo: boolean;
  /** o valor esperado aparece também na pergunta */
  eco: boolean;
  /** o valor esperado, normalizado */
  alvo?: number;
  /** os números achados na resposta, para inspecionar um "errado" */
  achados: number[];
}

/**
 * Decide o acerto de um caso.
 *
 * **Sobre o eco:** quando o valor esperado está escrito na própria pergunta
 * (quase sempre o ano — `esperado 2022`, pergunta "…em 2022"), o caso é
 * devolvido como `eco` e **não conta nem como acerto nem como erro**. A
 * alternativa era detectar quais ocorrências dentro da resposta são repetição da
 * pergunta, o que exige segmentar a resposta — chute. O eco, ao contrário, é
 * propriedade do CASO, decidível antes de rodar qualquer coisa: um caso que um
 * papagaio passa não mede o modelo, então mantê-lo no denominador é inflar o
 * placar com zero informação. Sai do denominador e é reportado à parte, porque
 * o conserto é escolher outro valor esperado, não culpar o modelo.
 *
 * `pergunta` é opcional só para não travar quem não a tem à mão — sem ela o eco
 * nunca é detectado, e é exatamente o buraco que deixou `n=2022` passar.
 */
export function avalia(
  resposta: string,
  esperado?: string,
  pergunta?: string,
): Acerto {
  const alvo = esperado ? normalizaNumero(esperado.trim()) : undefined;
  if (alvo === undefined) {
    return { veredito: "sem_gabarito", certo: false, eco: false, achados: [] };
  }
  const eco = pergunta ? numeros(pergunta).includes(alvo) : false;
  const achados = numeros(resposta);
  if (eco) return { veredito: "eco", certo: false, eco: true, alvo, achados };
  const certo = achados.includes(alvo);
  return { veredito: certo ? "certo" : "errado", certo, eco: false, alvo, achados };
}

/** O caso é passável por papagaio? Dá para auditar um TSV inteiro sem rodar nada. */
export function casoEcoa(pergunta: string, esperado?: string): boolean {
  const alvo = esperado ? normalizaNumero(esperado.trim()) : undefined;
  return alvo !== undefined && numeros(pergunta).includes(alvo);
}

/**
 * Forma antiga (`bate(texto, esperado)`), agora com fronteira de número.
 * `undefined` quer dizer "não mede" — sem gabarito, ou eco da pergunta.
 */
export function bate(
  texto: string,
  esperado?: string,
  pergunta?: string,
): boolean | undefined {
  const a = avalia(texto, esperado, pergunta);
  return a.veredito === "certo" ? true : a.veredito === "errado" ? false : undefined;
}

// ------------------------------------------------- 2. a config que produziu o tempo

const BASE = Bun.env.HARNESS_LLM ?? "http://127.0.0.1:8099";

export interface ConfigServidor {
  /** `-np` — slots do llama-server. `total_slots` no /props */
  np: number;
  /** `-c` — contexto POR SLOT. `-c 65536 -np 4` aloca 4x o KV */
  ctx: number;
  modelo: string;
}

/**
 * Lê `-np`/`-c` do servidor no ar. `/props` responde mesmo com
 * `endpoint_props: false` (medido 2026-09-02), e não custa nada — é a diferença
 * entre um tempo registrado e um tempo comparável.
 */
export async function configServidor(base = BASE): Promise<ConfigServidor | undefined> {
  try {
    const r = await fetch(`${base}/props`, { signal: AbortSignal.timeout(5000) });
    if (!r.ok) return undefined;
    const d = await r.json() as {
      total_slots?: number;
      model_alias?: string;
      default_generation_settings?: { n_ctx?: number };
    };
    return {
      np: d.total_slots ?? -1,
      ctx: d.default_generation_settings?.n_ctx ?? -1,
      modelo: (d.model_alias ?? "?").split("/").pop() ?? "?",
    };
  } catch { return undefined; }
}

export function rotuloConfig(c?: ConfigServidor): string {
  return c ? `-np ${c.np} -c ${c.ctx} (${c.modelo})` : "-np ? -c ? (servidor não respondeu)";
}

/**
 * Aviso ao comparar duas rodadas. Sem isto, 20,9 min contra 15,2 min lê-se como
 * ganho do harness quando é só `-np` diferente — a leitura errada que a Rodada 8
 * quase produziu.
 */
export function avisaConfigDivergente(
  a?: ConfigServidor,
  b?: ConfigServidor,
  rotuloA = "A",
  rotuloB = "B",
): string | undefined {
  if (!a || !b) return `AVISO: falta a config de ${!a ? rotuloA : rotuloB} — os tempos NÃO são comparáveis`;
  const d: string[] = [];
  if (a.np !== b.np) d.push(`-np ${a.np} vs ${b.np}`);
  if (a.ctx !== b.ctx) d.push(`-c ${a.ctx} vs ${b.ctx}`);
  if (a.modelo !== b.modelo) d.push(`modelo ${a.modelo} vs ${b.modelo}`);
  if (!d.length) return undefined;
  return `AVISO: ${rotuloA} e ${rotuloB} rodaram com config diferente (${d.join("; ")}) — comparar TEMPO entre elas é comparar coisas distintas`;
}

// ------------------------------------------------------------- 3. o prefill

/**
 * Acima disto o prefill é do tamanho do PREFIXO, não da pergunta.
 *
 * Medido no log do llama-server em 2026-09-02, dentro do laço agêntico com o
 * cache vivo: 97, 177, 197 e 248 tokens por turno, com o slot em ~11k. O prefixo
 * do dsh está em 6.849. 2.000 fica entre as duas ordens de grandeza — larga o
 * bastante para não acusar um turno com muito resultado de ferramenta colado.
 */
export const LIMIAR_PREFILL = Number(Bun.env.HARNESS_LIMIAR_PREFILL ?? 2000);

/**
 * Reprova um prefill de tamanho de prefixo. **Só vale depois do aquecimento** —
 * o primeiro caso prefila o prefixo inteiro por definição, e acusá-lo seria
 * ruído garantido em toda rodada.
 */
export function avisaPrefill(
  tokens: number[],
  limiar = LIMIAR_PREFILL,
): string | undefined {
  const pior = Math.max(0, ...tokens);
  if (pior <= limiar) return undefined;
  return `AVISO: prefill de ${pior} tokens (limiar ${limiar}) — cache de prefixo quebrado. A resposta continua certa e a rodada fica ~7x mais lenta; procure o que entrou variável no prefixo (timestamp, ordem não determinística)`;
}

// -- o prefill quando não volta pelo stdout: o log do llama-server no beelink --
//
// Em `lote.ts` cada pergunta é um processo `dsh` separado e o `timings.prompt_n`
// morre lá dentro. O que sobra é o log do servidor, que imprime uma linha
// `prompt eval time = ... ms /  N tokens` por requisição. `/slots` não serve:
// medido 2026-09-02, com o slot ocioso `n_prompt_tokens_processed` e
// `n_prompt_tokens_cache` voltam 0 — o dado só existe enquanto a requisição corre.

const HOST = Bun.env.BEELINK_HOST ?? "beelink";
const LOG = Bun.env.HARNESS_SRV_LOG ?? "/tmp/srv.log";

async function ssh(cmd: string): Promise<string | undefined> {
  try {
    const p = Bun.spawn(["ssh", HOST, cmd], { stdout: "pipe", stderr: "ignore" });
    const t = await new Response(p.stdout).text();
    return (await p.exited) === 0 ? t : undefined;
  } catch { return undefined; }
}

/** Offset em bytes do log agora — a marca de onde começar a ler depois do caso. */
export async function marcaDoLog(): Promise<number | undefined> {
  const t = await ssh(`wc -c < ${LOG} 2>/dev/null`);
  const n = Number((t ?? "").trim());
  return Number.isFinite(n) && n > 0 ? n : undefined;
}

/**
 * Tokens prefilados em cada requisição desde a marca.
 *
 * Devolve `undefined` (não `[]`) quando não dá para saber — servidor reiniciado
 * (o log encolheu, `servidor.sh` reabre com `>`), log noutro caminho, ssh fora.
 * A distinção importa: `[]` viraria "prefill zero, tudo ótimo", que é
 * exatamente o tipo de silêncio que esta checagem existe para acabar.
 */
export async function prefillsDesde(marca?: number): Promise<number[] | undefined> {
  if (marca === undefined) return undefined;
  const agora = await marcaDoLog();
  if (agora === undefined || agora < marca) return undefined;
  const t = await ssh(`tail -c +${marca + 1} ${LOG} 2>/dev/null | grep -oE 'prompt eval time =[^/]*/ *[0-9]+ tokens'`);
  if (t === undefined) return undefined;
  return extraiPrefills(t);
}

/** Separado do ssh para ser testável sem servidor. */
export function extraiPrefills(logo: string): number[] {
  return [...logo.matchAll(/prompt eval time =[^/]*\/\s*(\d+) tokens/g)]
    .map((m) => Number(m[1]));
}

// ------------------------------------------------------------- 4. o boot

/**
 * `servidor.sh aquece` antes de qualquer rodada — operacao.md tarefa 2: "nada
 * chama isso automaticamente". Uma rodada de horas com o raciocínio ligado
 * (20,9 s por turno em vez de 4,7 s) ou o cache de prefixo quebrado é o
 * desperdício mais caro disponível aqui, e os dois passam sem exceção — só o
 * detector de `servidor.sh` pega. Não reinicia nada: só confere.
 */
export async function confereBoot(): Promise<boolean> {
  const p = Bun.spawn(["./harness/servidor.sh", "aquece"], {
    stdout: "inherit", stderr: "inherit",
  });
  return (await p.exited) === 0;
}
