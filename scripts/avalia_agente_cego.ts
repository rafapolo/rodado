/**
 * Avaliação cega do db.rodado.xyz: um agente que nunca viu o projeto recebe só a URL e uma
 * pergunta, e tem de achar a resposta pelo HTTP (curl). Mede se o guia (/llm), o contexto
 * (/contexto), os exemplos (/exemplos) e o ensaio (/confere) levam ao número certo — e por
 * onde ele andou, para saber qual camada falhou.
 *
 * A régua são os holdouts das perguntas diretas do harness (branch harness-gemma,
 * harness/dados/diretas_holdout*.tsv): nenhuma nota nem exemplo servido pelo /exemplos foi
 * escrito a partir deles (o /exemplos só leva diretas.tsv, o conjunto de treino). Medir nas
 * de treino mediria memória.
 *
 * O agente é o `opencode run --auto` (sem o --auto ele para esperando aprovação para o curl)
 * com um modelo gratuito (não gasta a sessão do Claude). Cada
 * caso roda numa pasta vazia, com teto de tempo e uma nova tentativa; o resultado fica por
 * id num JSONL, e rodar de novo pula o que já terminou.
 *
 *   bun scripts/avalia_agente_cego.ts --rodada base --modelo opencode/minimax-m3.1-flash-free
 *   bun scripts/avalia_agente_cego.ts --rodada base --resumo     # só o placar
 *
 * Opções: --url (https://db.rodado.xyz), --paralelo 3, --limite N, --conjuntos
 * holdout,holdout2,holdout3, --teto 600 (s por caso).
 */
import { $ } from "bun";
import { appendFileSync, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { parseArgs } from "node:util";

const RAIZ = new URL("..", import.meta.url).pathname;
const { values: op } = parseArgs({
  options: {
    rodada: { type: "string", default: "base" },
    modelo: { type: "string", default: "opencode/minimax-m3.1-flash-free" },
    url: { type: "string", default: "https://db.rodado.xyz" },
    paralelo: { type: "string", default: "3" },
    limite: { type: "string" },
    conjuntos: { type: "string", default: "holdout,holdout2,holdout3" },
    teto: { type: "string", default: "600" },
    resumo: { type: "boolean", default: false },
  },
});
const SAIDA_DIR = join(RAIZ, "tasks", "avaliacao_agente");
mkdirSync(SAIDA_DIR, { recursive: true });
const SAIDA = join(SAIDA_DIR, `${op.rodada}.jsonl`);

// ------------------------------------------------------------------ casos

interface Caso { id: string; pergunta: string; esperado: string }

async function carregaCasos(): Promise<Caso[]> {
  const casos: Caso[] = [];
  for (const c of op.conjuntos!.split(",")) {
    const tsv = await $`git -C ${RAIZ} show harness-gemma:harness/dados/diretas_${c}.tsv`.text();
    let i = 0;
    for (const linha of tsv.split("\n")) {
      if (!linha.trim() || linha.startsWith("#")) continue;
      const [pergunta, esperado] = linha.split("\t");
      if (pergunta && esperado) casos.push({ id: `${c}-${String(++i).padStart(2, "0")}`, pergunta, esperado: esperado.trim() });
    }
  }
  return op.limite ? casos.slice(0, Number(op.limite)) : casos;
}

// ------------------------------------------------------------------ régua (de harness/acerto.ts)

const NUMERO = /\d{1,3}(?:[.  ]\d{3})+(?:,\d+)?|\d+(?:,\d+)?/g;
const semAcento = (s: string) => s.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();

function normalizaNumero(s: string): number | undefined {
  const limpo = s.replace(/[.\s ]/g, "").replace(",", ".");
  if (!limpo || !/^\d/.test(limpo)) return undefined;
  const v = Number(limpo);
  return Number.isFinite(v) ? v : undefined;
}

const ESCALA: [RegExp, number][] = [
  [/^\s*mil\b/i, 1e3],
  [/^\s*(milh(ão|ões|ao|oes)|mi)\b/i, 1e6],
  [/^\s*(bilh(ão|ões|ao|oes)|bi)\b/i, 1e9],
];

function candidatos(texto: string): number[] {
  const out = new Set<number>();
  for (const m of texto.matchAll(NUMERO)) {
    const v = normalizaNumero(m[0]);
    if (v === undefined) continue;
    out.add(v);
    const depois = texto.slice(m.index! + m[0].length, m.index! + m[0].length + 12);
    for (const [re, f] of ESCALA) if (re.test(depois)) out.add(v * f);
  }
  for (const m of texto.matchAll(/(?<![\d.,])\d+\.\d{1,2}(?![\d.,])/g)) out.add(Number(m[0]));
  return [...out];
}

const DIZ_SEM_DADO = new RegExp([
  "nao ha (dados?|registros?|informac)", "nao (existem?|constam?|possui|tem|temos|encontrei|encontramos) (os )?(dados?|registros?|informac)",
  "nao (esta|estao) disponive", "indisponive", "sem dados?", "nao cobre", "nao abrange", "fora da cobertura",
  "(vai|cobre|chega|vao|cobrem|chegam) (apenas |somente |so )?ate", "disponive(l|is) (apenas |somente |so )?ate",
  "ainda nao (foi|foram) (publicad|divulgad|disponibilizad)", "nao (foi|foram) (publicad|divulgad)",
  "(contem|tem|possui|traz) (dados|registros|informac\\w*)? ?(apenas |somente |so )?ate",
  "nao e possivel (informar|responder|calcular|obter|determinar|saber|apurar)",
  "(so|apenas|somente) (contem|tem|possui|cobre|traz) (dados |registros )?(a partir de|desde)",
].join("|"));

function certo(resposta: string, esperado: string): boolean {
  const texto = semAcento(resposta);
  const exatos = [...resposta.matchAll(NUMERO)].map((m) => normalizaNumero(m[0])).filter((v) => v !== undefined);
  const cands = candidatos(resposta);
  return esperado.split("|").map((x) => x.trim()).filter(Boolean).some((x) => {
    if (x === "SEM_DADO") return DIZ_SEM_DADO.test(texto);
    const [base, tol] = x.split("~").map((y) => y.trim());
    const v = /^-?[\d.,\s]+$/.test(base!) ? normalizaNumero(base!) : undefined;
    if (v === undefined) return texto.includes(semAcento(x));
    if (!tol) return exatos.includes(v);
    const t = Number(tol.replace("%", "").replace(",", "."));
    const margem = tol.endsWith("%") ? (t / 100) * Math.abs(v) : t;
    return cands.some((c) => Math.abs(c - v) <= margem + 1e-9);
  });
}

/** O valor do gabarito já está escrito no que o serviço entrega (/exemplos, /contexto)? Então
 *  o caso mede leitura, não consulta: o placar sai com e sem ele (como o `eco` do acerto.ts). */
const SERVIDO = existsSync(join(RAIZ, "db", "contexto.json")) ? readFileSync(join(RAIZ, "db", "contexto.json"), "utf8") : "";
function vaza(esperado: string): boolean {
  return esperado.split("|").some((x) => {
    const base = x.split("~")[0]!.trim();
    if (base === "SEM_DADO" || base.replace(/\D/g, "").length < 3) return false;
    return new RegExp(`(?<![\\d.,])${base.replace(/[.,]/g, "[.,]")}(?![\\d])`).test(SERVIDO);
  });
}

// ------------------------------------------------------------------ agente

const PROMPT = (pergunta: string) => `Você é um agente de dados e não conhece este projeto.
A única fonte de dados é o serviço HTTP ${op.url}; a credencial está na variável de ambiente
RODADO_TOKEN (nunca a escreva na resposta). Descubra sozinho
como usá-lo, a partir dessa URL, usando só curl pelo shell. Não crie nem edite arquivos. Não use
outra fonte (nem a web, nem o que você lembra): se o serviço não tiver o dado, diga isso.

Pergunta: ${pergunta}

Termine com uma linha exatamente no formato:
RESPOSTA: <valor ou "sem dado no serviço">`;

const ROTAS = ["/llm", "/tabelas", "/colunas", "/contexto", "/exemplos", "/confere", "/query"];

// stdout do opencode: banner, chamadas de ferramenta e texto; tira o colorido do terminal
const limpa = (s: string) => s.replace(/\x1b\[[0-9;]*m/g, "");

async function roda(caso: Caso) {
  const pasta = mkdtempSync(join(tmpdir(), "avalia-"));
  const teto = Number(op.teto) * 1000;
  try {
    for (let tentativa = 1; tentativa <= 2; tentativa++) {
      const inicio = Date.now();
      const proc = Bun.spawn(["opencode", "run", "--auto", "-m", op.modelo!, PROMPT(caso.pergunta)],
        { cwd: pasta, stdout: "pipe", stderr: "pipe" });
      const timer = setTimeout(() => proc.kill(), teto);
      const saida = limpa(await new Response(proc.stdout).text());
      await proc.exited;
      clearTimeout(timer);
      const segundos = Math.round((Date.now() - inicio) / 1000);
      const final = [...saida.matchAll(/RESPOSTA:\s*(.+)/g)].at(-1)?.[1]?.trim();
      if (!final && tentativa === 1) continue;  // estourou ou parou no meio: mais uma
      const rotas = Object.fromEntries(ROTAS.map((r) => [r, saida.split(r).length - 1]));
      return {
        id: caso.id, pergunta: caso.pergunta, esperado: caso.esperado, resposta: final ?? null, vaza: vaza(caso.esperado),
        // o agente viu os avisos do /query? no cabeçalho só com curl -i / -D; no corpo, desde
        // 2026-10-20, sempre que pede sem `formato` (o campo "avisos" com algo dentro)
        viu_avisos: saida.split("X-Avisos").length - 1 + (saida.match(/"avisos":\s*\[\s*"/g)?.length ?? 0),
        certo: final ? certo(final, caso.esperado) : false, segundos, tentativa, rotas,
        cauda: saida.slice(-1500),
      };
    }
  } finally {
    rmSync(pasta, { recursive: true, force: true });
  }
}

// ------------------------------------------------------------------ placar

function placar() {
  if (!existsSync(SAIDA)) return console.log("sem resultados ainda");
  const rs = readFileSync(SAIDA, "utf8").trim().split("\n").map((l) => JSON.parse(l));
  const certos = rs.filter((r) => r.certo).length;
  console.log(`${op.rodada}: ${certos}/${rs.length} certos (${Math.round((100 * certos) / rs.length)}%), ` +
    `${rs.filter((r) => !r.resposta).length} sem resposta, mediana ${rs.map((r) => r.segundos).sort((a, b) => a - b)[rs.length >> 1]} s`);
  const limpos = rs.filter((r) => !r.vaza);
  console.log(`  sem os ${rs.length - limpos.length} casos cujo gabarito o serviço já escreve: ` +
    `${limpos.filter((r) => r.certo).length}/${limpos.length}; X-Avisos visto em ${rs.filter((r) => r.viu_avisos > 0).length} casos`);
  for (const r of ROTAS) {
    const usou = rs.filter((x) => x.rotas[r] > 0);
    const c = usou.filter((x) => x.certo).length;
    console.log(`  ${r.padEnd(10)} usada em ${String(usou.length).padStart(3)} casos · ${usou.length ? Math.round((100 * c) / usou.length) : 0}% certos entre eles`);
  }
  for (const conj of new Set(rs.map((r) => r.id.split("-")[0]))) {
    const g = rs.filter((r) => r.id.startsWith(conj + "-"));
    console.log(`  ${conj}: ${g.filter((r) => r.certo).length}/${g.length}`);
  }
}

if (op.resumo) {
  placar();
} else {
  const feitos = new Set(existsSync(SAIDA)
    ? readFileSync(SAIDA, "utf8").trim().split("\n").filter(Boolean).map((l) => JSON.parse(l).id) : []);
  const fila = (await carregaCasos()).filter((c) => !feitos.has(c.id));
  console.log(`${fila.length} casos a rodar em ${op.rodada} (${feitos.size} já feitos), modelo ${op.modelo}`);
  const trabalhador = async () => {
    for (let caso = fila.shift(); caso; caso = fila.shift()) {
      const r = await roda(caso);
      if (!r) continue;
      appendFileSync(SAIDA, JSON.stringify(r) + "\n");
      console.log(`${r.certo ? "✓" : "✗"} ${r.id} ${r.segundos}s → ${r.resposta ?? "(sem resposta)"} [esperado ${r.esperado}]`);
    }
  };
  await Promise.all(Array.from({ length: Number(op.paralelo) }, trabalhador));
  placar();
}
