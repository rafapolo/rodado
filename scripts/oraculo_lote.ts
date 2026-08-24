#!/usr/bin/env bun
/**
 * Oráculo em lote: para cada pergunta convertível, um professor forte escreve
 * SQL, executa no beelink e sanciona o resultado. O que sobreviver vira
 * `esperado` — o alvo do corpus de destilação.
 *
 *   nohup bun run scripts/oraculo_lote.ts > /tmp/opencode/oraculo.log 2>&1 &
 *
 * Retomável: pula código já ok em /tmp/opencode/oraculo_lote_resultados.json. Salva a cada
 * questão — o lote leva horas e não pode morrer com tudo na memória.
 */
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { stripSqlComments } from "../web/src/sqlguard.ts";

const RODADO = "../rodado/docs";
const META = JSON.parse(readFileSync("web/static/index/meta.json", "utf-8"));
const COLUNAS = JSON.parse(readFileSync("web/static/index/colunas.json", "utf-8"));
const EXEMPLOS = JSON.parse(readFileSync("web/static/index/exemplos.json", "utf-8")).exemplos;
const VIAB = JSON.parse(readFileSync("tasks/pendentes_viabilidade.json", "utf-8"));
const SAIDA = Bun.env.ORACULO_SAIDA ?? "tasks/oraculo_resultados.json";
const ENDPOINT = Bun.env.ORACULO_ENDPOINT ?? "http://127.0.0.1:11434";
const [MOD_N, MOD_I] = (Bun.env.ORACULO_MOD ?? "").split(":").map(Number);

// ---- perguntas.md: código -> texto ------------------------------------------
const pergTexto = new Map<string, string>();
{
  let temaNum: string | null = null;
  for (const linha of readFileSync(`${RODADO}/perguntas.md`, "utf-8").split("\n")) {
    const mTema = linha.match(/^## (\d+) · /);
    if (mTema) { temaNum = mTema[1]!.padStart(2, "0"); continue; }
    const mItem = linha.match(/^(\d+)\.\s+(.+?)\s+\*\(n=/);
    if (mItem && temaNum) pergTexto.set(`T${temaNum}-${mItem[1]}`, mItem[2]!.replace(/\s+/g, " ").trim());
  }
}

// ---- seleção de tabelas por dataset: lexical da pergunta primeiro ----------
// O gargalo medido: professor bom com tabela errada falha 7/7. Ranquear por
// tamanho escolhia br_ibge_censo_2022.municipio genérica em vez da tabela de
// raça que a pergunta pede. Mesma raiz de palavra do lexical.js do app.
const RUIDO = new Set(("qual quais quantos quantas quanto foi foram e de do da dos das em no na " +
  "nos nas o a os as por para com que mais maior menor tem existe existem segundo acima " +
  "ano anos entre sobre um uma como onde quando").split(" "));
const semAcento = (s: string) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
const raiz = (w: string) => w.replace(/(oes|aes|ais|eis|is|ns|s)$/, "");

function scoreLexical(pergunta: string, id: string) {
  const termos = new Set<string>();
  for (const w of semAcento(id).split(/[_.\s]+/)) if (w.length > 2) termos.add(raiz(w));
  for (const c of COLUNAS[id] ?? []) for (const w of semAcento(c.n).split(/[_\s]+/)) if (w.length > 2) termos.add(raiz(w));
  let s = 0;
  for (const w of semAcento(pergunta).split(/\W+/)) {
    if (w.length <= 2 || RUIDO.has(w) || /^\d+$/.test(w)) continue;
    const r = raiz(w);
    for (const t of termos) if (t === r || t.startsWith(r) || r.startsWith(t)) { s++; break; }
  }
  return s;
}

function tabelasDe(datasets: string[], pergunta: string) {
  const escolhidas: string[] = [];
  for (const ds of datasets) {
    const tabs = (META.tabelas as any[])
      .filter((t) => t.id.startsWith(`${ds}.`) && !/dicionario/.test(t.id))
      .map((t) => ({ ...t,
        lex: scoreLexical(pergunta, t.id),
        agregada: /municipio|_uf$|^uf$/.test(t.tabela) ? 1 : 0 }))
      .sort((a, b) => (b.lex * 10 + b.agregada) - (a.lex * 10 + a.agregada) || Number(b.linhas ?? 0) - Number(a.linhas ?? 0));
    for (const t of tabs.slice(0, 2)) if (!escolhidas.includes(t.id)) escolhidas.push(t.id);
  }
  return escolhidas.slice(0, 6);
}

function montarDDL(ids: string[]) {
  return ids.map((id) => {
    const cols = (COLUNAS[id] ?? []).slice(0, 20).map((c: any) => `${c.n}:${c.t}`).join(" ");
    return `${id}: ${cols}`;
  }).join("\n");
}

function exemplosPara(pergunta: string, datasets: string[]) {
  const p = pergunta.toLowerCase();
  return EXEMPLOS.filter((e: any) =>
      (e.gatilhos ?? []).some((g: string) => p.includes(g.toLowerCase())) &&
      (e.datasets ?? []).some((d: string) => datasets.includes(d)))
    .slice(0, 2)
    .map((e: any) => `EXEMPLO VERIFICADO:\n${e.sql}`)
    .join("\n\n");
}

const SISTEMA = `Você escreve SQL DuckDB sobre o acervo rodado (dados públicos brasileiros).

REGRAS
- Responda APENAS com o SQL. Sem explicação, sem markdown, sem \`\`\`.
- Sempre qualifique a tabela: dataset.tabela. "dataset." nunca é prefixo de coluna.
- Agregue: SUM/COUNT com GROUP BY, corr() para correlação entre dois fenômenos.
  Correlação de pesquisa: CTEs que agregam cada fonte por id_municipio+ano,
  join, corr(a.x, b.y) e count(*) como n.
- Filtre ano/mes/sigla_uf/id_municipio sempre que existirem (partições).
- Valores de texto em minúscula; datasets codificados resolvem pelo .dicionario.
- Use SOMENTE colunas do DDL dado. Não invente.
- Mostre NOME juntando com br_bd_diretorios_brasil.municipio (id_municipio, nome)
  ou .uf — ATENÇÃO: .uf usa coluna SIGLA, não sigla_uf. Ex.: u.sigla = o.sigla_uf.
- Impossível com estas tabelas? Responda exatamente {"error": "motivo"}.`;

const PROFESSORES = ["qwen2.5-coder:14b", "qwen2.5-coder:7b"];
const TENTATIVAS_POR_PROFESSOR = [4, 2];

async function gerar(modelo: string, prompt: string) {
  const r = await fetch(`${ENDPOINT}/api/generate`, {
    method: "POST",
    body: JSON.stringify({ model: modelo, prompt, stream: false, keep_alive: "30m", think: false,
      options: { temperature: 0.2, num_predict: 800, num_ctx: 12288 } }),
    signal: AbortSignal.timeout(420_000),
  });
  const j = await r.json();
  return (j.response ?? "").trim();
}

function limparSQL(t: string) {
  let s = t.replace(/<think>[\s\S]*?<\/think>/gi, "").trim();
  const m = s.match(/```(?:sql)?\s*([\s\S]*?)```/i);
  s = (m ? m[1] : s).trim();
  if (/^\s*\{/.test(s)) {
    const err = s.match(/"error"\s*:\s*"([^"]+)"/i);
    throw new Error(err?.[1] ?? "modelo recusou");
  }
  if (!/^\s*(SELECT|WITH)\b/i.test(stripSqlComments(s))) throw new Error(`não é SQL`);
  return s.replace(/;\s*$/, "");
}

async function executar(sql: string): Promise<any> {
  const tmp = `/tmp/opencode/o_${Math.random().toString(36).slice(2)}.sql`;
  await Bun.write(tmp, `SET enable_progress_bar=false; SET threads=4;\n${sql};`);
  const p = Bun.$`timeout 150 ssh -o ConnectTimeout=10 beelink '~/bin/duckdb -json ~/rodado/basedosdados.duckdb' < ${tmp}`.nothrow().quiet();
  const res = await p;
  try {
    const rows = JSON.parse(res.stdout.toString());
    return { rows };
  } catch {
    throw new Error((res.stderr.toString().replace(/-- Loading resources.*\n/g, "") || `exit ${res.exitCode}`).slice(0, 400));
  }
}

function sancionar(rows: any[]): string | null {
  if (!rows.length) return "resultado vazio";
  const flat = rows[0];
  for (const [k, v] of Object.entries(flat)) {
    if (typeof v === "number" && k.match(/\br\b/i) && (v < -1 || v > 1)) return `r fora de [-1,1]: ${k}=${v}`;
  }
  const nVal = flat["n"] ?? flat["N"];
  if (typeof nVal === "number" && nVal < 10) return `n muito pequeno: ${nVal}`;
  return null;
}

// ---- laço principal -----------------------------------------------------------
type Reg = any;
const anteriores: Record<string, Reg> = existsSync(SAIDA)
  ? JSON.parse(readFileSync(SAIDA, "utf-8")) : {};
const salvar = () => writeFileSync(SAIDA, JSON.stringify(anteriores, null, 1));

const fila = VIAB.itens.filter((i: any) => i.classe === "convertivel" && anteriores[i.codigo]?.status !== "ok");
const filaFiltrada = Number.isFinite(MOD_N) ? fila.filter((_, i) => i % MOD_N! === MOD_I!) : fila;
console.error(`fila: ${filaFiltrada.length} questões`);

for (const item of filaFiltrada) {
  const q = pergTexto.get(item.codigo);
  if (!q) { anteriores[item.codigo] = { status: "sem_pergunta" }; salvar(); continue; }

  // datasets citados: do viab.presentes (resolvidos contra o catálogo)
  const ids = tabelasDe(item.presentes ?? [], q);
  if (!ids.length) { anteriores[item.codigo] = { status: "sem_tabelas" }; salvar(); continue; }

  const ddl = montarDDL(ids);
  const base = `${SISTEMA}\n\nTABELAS DISPONÍVEIS\n${ddl}\n${exemplosPara(q, item.presentes ?? [])}\nPERGUNTA: ${q}\nSQL:`;

  const reg: Reg = { codigo: item.codigo, q, tabelas: ids, tentativas: [] };
  let prompt = base;

  // candidatos de coluna que o próprio DuckDB sugere no Binder Error — o
  // vocabulário certo, de graça, na mensagem que já tínhamos
  const candidatosDoErro = (msg: string) => {
    const m = msg.match(/Candidate bindings?: "([^"]+)"(.*)/s);
    return m ? (m[1] + (m[2]?.match(/"([w]+)"/g)?.slice(0, 8).join(" ").replaceAll("\"","") ?? "")).slice(0, 300) : null;
  };

  const falhas: string[] = [];
  externo:
  for (let pi = 0; pi < PROFESSORES.length; pi++) {
    const professor = PROFESSORES[pi]!;
    for (let tent = 1; tent <= TENTATIVAS_POR_PROFESSOR[pi]!; tent++) {
      const t0 = Date.now();
      try {
        const bruto = await gerar(professor, prompt);
        let sql;
        try { sql = limparSQL(bruto); } catch (e: any) {
          reg.tentativas.push({ ms: Date.now() - t0, professor, erro: String(e.message ?? e).slice(0, 250), sql_bruto: bruto.slice(0, 500) });
          throw e;
        }
        const exec = await executar(sql);
        const problema = sancionar(exec.rows);
        reg.tentativas.push({ ms: Date.now() - t0, professor, sql });
        if (problema === "resultado vazio" && tent === 1) {
          // diagnóstico: quais anos existem de fato nas tabelas citadas?
          const diags: string[] = [];
          for (const id of ids.slice(0, 4)) {
            try {
              const d = await executar(`SELECT min(ano) AS mn, max(ano) AS mx FROM ${id}`);
              diags.push(`${id}: ano ${d.rows[0]?.mn}–${d.rows[0]?.mx}`);
            } catch { /* tabela sem ano */ }
          }
          if (diags.length) falhas.push("vazio; anos disponíveis: " + diags.join("; "));
        }
        reg.status = problema ? `sancao:${problema}` : "ok";
        reg.sql = sql;
        reg.resultado = exec.rows.slice(0, 12);
        break externo;
      } catch (e: any) {
        const msg = String(e.message ?? e).slice(0, 250);
        reg.tentativas.push({ ms: Date.now() - t0, professor, erro: msg });
        falhas.push(msg);
        if (/timeout/i.test(msg) && tent >= 2) break;   // professor lento demais, troca
        const cand = candidatosDoErro(msg);
        const diag = falhas.filter((f) => f.startsWith("vazio")).slice(-1)[0];
        prompt = `${base}\n\nA tentativa anterior (${professor}) falhou assim: ${msg}` +
          (cand ? `\nColunas candidatas que EXISTEM: ${cand}` : "") +
          (diag ? `\n${diag}` : `\nSe o resultado veio VAZIO, confira os valores dos filtros.`) +
          `\nCorrija e responda só o SQL.`;
      }
    }
  }
  if (reg.status === undefined) reg.status = "falhou";
  reg.falhas = falhas;
  anteriores[item.codigo] = reg;
  salvar();
  console.error(`${item.codigo}: ${reg.status} (${reg.tentativas.length} tent.)`);
}

const oks = Object.values(anteriores).filter((r) => r.status === "ok").length;
console.error(`fim: ${oks}/${Object.keys(anteriores).length} ok`);
