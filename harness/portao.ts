/**
 * O portão — tudo que roda entre o modelo escrever SQL e o beelink executar.
 *
 * Existe porque `checkReadOnly` (sqlguard.ts) valida só tipo de statement e
 * palavra proibida. Isso basta enquanto quem dirige é uma pessoa: a disciplina
 * de partição e de codificação está em prosa no docstring do `run_sql`. **Prosa
 * em docstring não é enforcement para um modelo autônomo.** Medido em
 * 2026-09-01, com o Gemma 4 26B-A4B:
 *
 *  - a primeiríssima tool call dele foi `SELECT COUNT(*) FROM
 *    br_ms_sim.microdados`, sem filtro nenhum — a forma exata do lock de 2h
 *    registrado no CLAUDE.md;
 *  - pedido "suicídios X60–X84 no RJ em 2020", escreveu
 *    `causa_basica BETWEEN 'X60' AND 'X84'`. O CID é guardado sem ponto
 *    (`X840`) e `'X840' > 'X84'`, então o grupo X84 inteiro sai: **726 contra
 *    789 reais, 8% a menos, com número plausível**.
 *
 * Camadas 2 e 3 (tabela/coluna) são porte de `validarTabelas`/`validarColunas`
 * de web/static/ask.js no branch ask-web, onde apanharam desses erros primeiro.
 *
 * Toda rejeição devolve mensagem que **ensina o conserto** — ela volta ao modelo
 * como próxima tentativa, e é aí que um modelo pequeno se sai bem, porque os
 * erros são mecânicos.
 */
import { checkReadOnly } from "./sqlguard.ts";
import { colunasDe, linhasDe, particoesDe, LIMIAR_PARTICAO } from "./catalogo.ts";

export interface Veredito {
  ok: boolean;
  /** Mensagem para o modelo — diz o que consertar, não só o que está errado. */
  erro?: string;
  camada?: string;
}

const OK: Veredito = { ok: true };

/** Palavras do dialeto que parecem `alias.coluna` mas não são. */
const RESERVADAS = new Set([
  "count", "sum", "avg", "min", "max", "round", "cast", "substr", "length",
  "coalesce", "nullif", "distinct", "case", "when", "then", "else", "end",
]);

/** Colunas cujo código diverge entre datasets (coded_differently, bridges.yaml). */
const CODIFICADAS = new Set(["sexo", "raca_cor", "estado_civil"]);

/** Colunas de CID-10 — guardadas sem ponto, então comparação de faixa mente. */
const COLUNAS_CID = /\b(causa_basica|cid_principal\w*|cid_\w+|causa_\w+)\b/i;

function tabelasCitadas(sql: string): string[] {
  const out = new Set<string>();
  for (const [, ref] of sql.matchAll(
    /\b(?:FROM|JOIN)\s+([A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)?)/gi,
  )) out.add(ref);
  return [...out];
}

/** Camada 2 — o modelo escreveu `FROM dataset` sem a tabela? */
function checaTabelas(sql: string): Veredito {
  const ruins: string[] = [];
  for (const ref of tabelasCitadas(sql)) {
    if (ref.includes("(")) continue;
    if (!ref.includes(".")) {
      ruins.push(`'${ref}' não tem tabela — escreva dataset.tabela`);
      continue;
    }
    if (colunasDe(ref) === null) ruins.push(`'${ref}' não existe no espelho`);
  }
  return ruins.length
    ? { ok: false, camada: "tabela", erro: `Referência inválida: ${ruins.join("; ")}.` }
    : OK;
}

/** Camada 3 — coluna inventada. */
function checaColunas(sql: string): Veredito {
  const refs = tabelasCitadas(sql).filter((r) => r.includes("."));
  const conhecidas = new Set<string>();
  for (const r of refs) {
    for (const c of colunasDe(r) ?? []) conhecidas.add(c.name.toLowerCase());
  }
  if (!conhecidas.size) return OK;

  // `dataset.tabela` casa com o mesmo padrão de `alias.coluna` — sem tirar as
  // referências de tabela, `br_ms_sim.microdados` vira "coluna inexistente".
  const semTabelas = refs.reduce((acc, r) => acc.split(r).join(" "), sql);

  const suspeitas = new Set<string>();
  for (const [, col] of semTabelas.matchAll(/\b[A-Za-z_][\w]*\.([A-Za-z_][\w]*)\b/g)) {
    const c = col.toLowerCase();
    if (!conhecidas.has(c) && !RESERVADAS.has(c) && !/^\d/.test(c)) suspeitas.add(col);
  }
  return suspeitas.size
    ? {
        ok: false,
        camada: "coluna",
        erro: `Coluna inexistente: ${[...suspeitas].join(", ")}. Use só as colunas do schema mostrado.`,
      }
    : OK;
}

/** Camada 4 — filtro de partição em tabela grande. O que evita o lock de horas. */
function checaParticao(sql: string): Veredito {
  const upper = sql.toUpperCase();
  for (const ref of tabelasCitadas(sql)) {
    if (!ref.includes(".")) continue;
    const linhas = linhasDe(ref);
    if (linhas === null || linhas < LIMIAR_PARTICAO) continue;
    const parts = particoesDe(ref);
    if (!parts.length) continue;
    const temFiltro = parts.some((p) =>
      new RegExp(`\\b${p.toUpperCase()}\\s*(=|IN|BETWEEN|>|<|>=|<=)`).test(upper),
    );
    if (!temFiltro) {
      return {
        ok: false,
        camada: "particao",
        erro:
          `${ref} tem ${(linhas / 1e6).toFixed(1)}M linhas e exige filtro de partição. ` +
          `Adicione um predicado em: ${parts.join(", ")}. ` +
          `Ex.: WHERE ano = 2020${parts.includes("sigla_uf") ? " AND sigla_uf = 'RJ'" : ""}.`,
      };
    }
  }
  return OK;
}

/** Camada 5 — LIMIT em consulta não agregada. */
function checaLimite(sql: string): Veredito {
  const upper = sql.toUpperCase();
  const agrega = /\b(COUNT|SUM|AVG|MIN|MAX|GROUP\s+BY)\b/.test(upper);
  if (agrega || /\bLIMIT\s+\d+/.test(upper)) return OK;
  return {
    ok: false,
    camada: "limite",
    erro: "Consulta sem agregação precisa de LIMIT. Adicione LIMIT 100, ou agregue no SQL.",
  };
}

/** Camada 6 — as armadilhas de codificação do espelho. */
function checaCodificacao(sql: string): Veredito {
  // CID sem ponto: BETWEEN sobre a coluna crua perde a última categoria inteira.
  const faixaCrua = new RegExp(
    `${COLUNAS_CID.source}\\s+BETWEEN`, "i",
  );
  if (faixaCrua.test(sql)) {
    return {
      ok: false,
      camada: "codificacao",
      erro:
        "Faixa de CID sobre a coluna crua está errada: o código é guardado sem ponto " +
        "('X840'), e 'X840' > 'X84', então a última categoria some inteira. " +
        "Use substr(coluna,1,3) BETWEEN 'X60' AND 'X84'.",
    };
  }
  // Código que diverge entre datasets: exige decode pelo dicionario do dataset.
  for (const col of CODIFICADAS) {
    const usaComparacao = new RegExp(`\\b${col}\\s*(=|IN)\\s*['"\\d(]`, "i").test(sql);
    const temDecode = new RegExp(`dicionario`, "i").test(sql);
    if (usaComparacao && !temDecode) {
      return {
        ok: false,
        camada: "codificacao",
        erro:
          `'${col}' tem código que diverge entre datasets — comparar contra literal ` +
          `dá resultado errado e plausível. Junte com {dataset}.dicionario para ` +
          `decodificar, ou agrupe pelo código cru sem interpretá-lo.`,
      };
    }
  }
  return OK;
}

/**
 * Roda as camadas em ordem de custo: as baratas e locais primeiro, para que o
 * modelo gaste as tentativas de reparo em erro real e não em ida ao beelink.
 * O EXPLAIN (que fala com o beelink) é `checaExplain`, chamado à parte.
 */
export function portao(sql: string): Veredito {
  const leitura = checkReadOnly(sql);
  if (leitura) return { ok: false, camada: "read-only", erro: leitura };

  for (const camada of [checaTabelas, checaColunas, checaParticao, checaLimite, checaCodificacao]) {
    const v = camada(sql);
    if (!v.ok) return v;
  }
  return OK;
}

/**
 * Camada 7 — EXPLAIN no beelink. Valida tabela e coluna contra o catálogo real
 * sem ler uma linha de dado; erro de nome volta em milissegundos em vez de
 * depois de uma varredura. Separado de `portao()` porque custa uma ida à rede.
 */
export async function checaExplain(
  sql: string,
  roda: (s: string) => Promise<{ error?: string }>,
): Promise<Veredito> {
  const r = await roda(`EXPLAIN ${sql}`);
  return r.error
    ? { ok: false, camada: "explain", erro: `DuckDB rejeitou: ${r.error}` }
    : OK;
}
