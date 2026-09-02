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
import { colunasDe, linhasDe, particoesDe, inservivel, LIMIAR_PARTICAO } from "./catalogo.ts";

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

/**
 * Nomes definidos por `WITH x AS (...)`. Um CTE é referenciado igual a uma
 * tabela e não existe no catálogo — sem reconhecê-los, o portão rejeita toda
 * consulta multi-dataset, que é justamente a que importa aqui: CTE é como se
 * escreve o join entre dois datasets sem repetir subconsulta.
 */
function ctesDefinidos(sql: string): Set<string> {
  const out = new Set<string>();
  // WITH a AS (...), b AS (...)  — pega tanto o primeiro quanto os seguintes
  for (const [, nome] of sql.matchAll(/(?:\bWITH\s+|,\s*)([A-Za-z_][\w]*)\s+AS\s*\(/gi)) {
    out.add(nome.toLowerCase());
  }
  return out;
}

function tabelasCitadas(sql: string): string[] {
  const ctes = ctesDefinidos(sql);
  const out = new Set<string>();
  for (const [, ref] of sql.matchAll(
    /\b(?:FROM|JOIN)\s+([A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)?)/gi,
  )) {
    if (!ctes.has(ref.toLowerCase())) out.add(ref);
  }
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

/**
 * Camada 2b — a tabela existe, tem linhas, e ainda assim não serve.
 *
 * `br_ibama_embargos` tem 497 mil linhas e status 'done', mas os valores são
 * strings vazias: o CSV foi parseado errado na raspagem e os bytes nunca
 * chegaram. Uma consulta contra ela devolve zero e o zero passa por resposta —
 * "não há embargos" no lugar de "não há dado". É a falha mais cara que existe
 * aqui, porque não deixa rastro nenhum.
 */
function checaInservivel(sql: string): Veredito {
  for (const ref of tabelasCitadas(sql)) {
    if (!ref.includes(".")) continue;
    const motivo = inservivel(ref);
    if (motivo) return { ok: false, camada: "inservivel", erro: motivo };
  }
  return OK;
}

/** Camada 3 — coluna inventada. */
function checaColunas(sql: string): Veredito {
  const refs = tabelasCitadas(sql).filter((r) => r.includes("."));
  const conhecidas = new Set<string>();
  for (const r of refs) {
    for (const c of colunasDe(r) ?? []) conhecidas.add(c.name.toLowerCase());
  }
  if (!conhecidas.size) return OK;

  // Colunas que a própria consulta cria com AS viram referência válida adiante
  // (`SUM(x) AS saldo_2020` e depois `c.saldo_2020`). Sem isso o portão acusa
  // de inexistente exatamente a coluna que a consulta acabou de definir.
  for (const [, apelido] of sql.matchAll(/\bAS\s+([A-Za-z_][\w]*)/gi)) {
    conhecidas.add(apelido.toLowerCase());
  }

  // `dataset.tabela` casa com o mesmo padrão de `alias.coluna` — sem tirar as
  // referências de tabela, `br_ms_sim.microdados` vira "coluna inexistente".
  const semTabelas = refs.reduce((acc, r) => acc.split(r).join(" "), sql);

  const suspeitas = new Set<string>();
  for (const [, col] of semTabelas.matchAll(/\b[A-Za-z_][\w]*\.([A-Za-z_][\w]*)\b/g)) {
    const c = col.toLowerCase();
    if (!conhecidas.has(c) && !RESERVADAS.has(c) && !/^\d/.test(c)) suspeitas.add(col);
  }
  if (!suspeitas.size) return OK;

  // A rejeição precisa ENSINAR, não só acusar. Medido em 2026-09-02: o modelo
  // gastou 991 s e 31 consultas caçando o nome da coluna de causa de morte
  // (`causa_materia`, `causa_materna`, `cid_causa_morte`) e nunca achou
  // `causa_basica`, apesar de `descrever_tabela` devolvê-la na quinta linha —
  // ele só não chamou a ferramenta. Uma mensagem que diz "não existe" e para aí
  // devolve o modelo ao mesmo palpite. Listar as colunas parecidas custa zero e
  // corta o laço.
  const inventadas = [...suspeitas];
  const dicas = refs.map((r) => {
    const cols = (colunasDe(r) ?? []).map((c) => c.name);
    const parecidas = cols.filter((c) =>
      inventadas.some((i) => {
        const a = i.toLowerCase(), b = c.toLowerCase();
        return b.includes(a.slice(0, 4)) || a.includes(b.slice(0, 4));
      }),
    );
    const mostrar = (parecidas.length ? parecidas : cols).slice(0, 20);
    return `  ${r} tem: ${mostrar.join(", ")}` +
      (cols.length > mostrar.length ? ` … +${cols.length - mostrar.length} (use descrever_tabela)` : "");
  });

  return {
    ok: false,
    camada: "coluna",
    erro: `Coluna inexistente: ${inventadas.join(", ")}.\n${dicas.join("\n")}`,
  };
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

  for (const camada of [checaTabelas, checaInservivel, checaColunas, checaParticao, checaLimite, checaCodificacao]) {
    const v = camada(sql);
    if (!v.ok) return v;
  }
  return OK;
}

/** Assinaturas de erro real do DuckDB. Qualquer outra saída de um EXPLAIN
 *  significa que ele montou o plano — ou seja, tabela e coluna existem. */
const ERROS_DUCKDB = [
  "Catalog Error", "Binder Error", "Parser Error", "Conversion Error",
  "Syntax Error", "Type Error", "Not implemented Error", "Invalid Input Error",
];

/**
 * Camada 7 — EXPLAIN no beelink. Valida tabela e coluna contra o catálogo real
 * sem ler uma linha de dado; erro de nome volta em milissegundos em vez de
 * depois de uma varredura. Separado de `portao()` porque custa uma ida à rede.
 *
 * `EXPLAIN` devolve o plano físico em arte-ASCII, não JSON — então o executor,
 * que espera JSON, reporta "resposta não-JSON". Isso é **sucesso**: o plano só
 * existe porque a consulta ligou. Falha é só a assinatura de erro do próprio
 * DuckDB. Sem esta distinção o portão rejeitava toda consulta válida.
 */
export async function checaExplain(
  sql: string,
  roda: (s: string) => Promise<{ error?: string }>,
): Promise<Veredito> {
  const r = await roda(`EXPLAIN ${sql}`);
  if (!r.error) return OK;
  const real = ERROS_DUCKDB.find((e) => r.error!.includes(e));
  return real
    ? { ok: false, camada: "explain", erro: `DuckDB rejeitou (${real}): ${r.error.slice(0, 300)}` }
    : OK; // plano em ASCII — a consulta liga
}
