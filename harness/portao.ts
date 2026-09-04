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
import { faixaDeAnos, type Faixa } from "./anos.ts";
import { conceitoDaColuna } from "./pontes.ts";

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

export function tabelasCitadas(sql: string): string[] {
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

/* ------------------------------------------------------------------ *
 *  Escopos — a máquina que as camadas 7 e 8 compartilham.
 *
 *  Um predicado de ano só pode ser cobrado da tabela a que ele pertence, e
 *  `WHERE ano = 2022` dentro de um CTE não fala das tabelas dos outros CTEs.
 *  Sem separar escopo, a camada de ano acusaria a tabela errada — e falso
 *  positivo aqui é o pior desfecho possível: rejeita trabalho legítimo com a
 *  mesma calma com que a falha silenciosa reporta número errado.
 * ------------------------------------------------------------------ */

/** Acha o `)` que fecha o `(` em `i`, pulando literais. */
function fechaParen(s: string, i: number): number {
  let nivel = 0;
  for (let k = i; k < s.length; k++) {
    const c = s[k]!;
    if (c === "'" || c === '"') {
      const fim = s.indexOf(c, k + 1);
      k = fim < 0 ? s.length : fim;
      continue;
    }
    if (c === "(") nivel++;
    else if (c === ")" && --nivel === 0) return k;
  }
  return s.length - 1;
}

/**
 * Divide a SQL em escopos independentes: todo parêntese que contém um SELECT
 * (corpo de CTE ou subconsulta) vira um segmento próprio e some do pai. O
 * último elemento é sempre a consulta externa — a projeção que de fato sai
 * para quem perguntou, que é o que a camada 8 precisa olhar.
 */
function segmentos(sql: string): string[] {
  const dentro: string[] = [];
  const raiz = recorta(sql, dentro);
  return [...dentro, raiz];
}

function recorta(s: string, saida: string[]): string {
  let out = "";
  let i = 0;
  while (i < s.length) {
    const c = s[i]!;
    if (c === "'" || c === '"') {
      const fim = s.indexOf(c, i + 1);
      const j = fim < 0 ? s.length : fim + 1;
      out += s.slice(i, j);
      i = j;
      continue;
    }
    if (c === "(") {
      const fim = fechaParen(s, i);
      const conteudo = s.slice(i + 1, fim);
      if (/\bSELECT\b/i.test(conteudo)) {
        saida.push(recorta(conteudo, saida));
        out += " "; // o escopo sai do pai: o WHERE de fora não é o WHERE de dentro
        i = fim + 1;
        continue;
      }
    }
    out += c;
    i++;
  }
  return out;
}

/** Palavras que vêm depois do nome da tabela e NÃO são apelido. */
const NAO_APELIDO = new Set([
  "on", "where", "group", "order", "join", "left", "right", "inner", "full",
  "cross", "using", "limit", "having", "union", "and", "or", "as", "natural",
  "qualify", "window", "except", "intersect", "offset", "lateral", "anti",
  "semi", "asof", "positional", "tablesample",
]);

interface RefEscopo {
  /** `dataset.tabela` como escrito */
  ref: string;
  /** todo nome pelo qual uma coluna dela pode ser qualificada */
  apelidos: Set<string>;
}

/** As tabelas reais citadas num escopo, com os apelidos por que respondem. */
function refsDoEscopo(seg: string, ctes: Set<string>): RefEscopo[] {
  const out: RefEscopo[] = [];
  for (const m of seg.matchAll(
    /\b(?:FROM|JOIN)\s+([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?)(?:\s+(?:AS\s+)?([A-Za-z_]\w*))?/gi,
  )) {
    const ref = m[1]!;
    if (!ref.includes(".") || ctes.has(ref.toLowerCase())) continue;
    const apelidos = new Set([ref.toLowerCase(), ref.split(".").pop()!.toLowerCase()]);
    const a = m[2]?.toLowerCase();
    if (a && !NAO_APELIDO.has(a)) apelidos.add(a);
    out.push({ ref, apelidos });
  }
  return out;
}

/** Um filtro de ano encontrado no SQL, já reduzido a "isto intersecta a faixa?". */
interface PredAno {
  /** qualificador escrito (`p` em `p.ano`), ou undefined se veio cru */
  qual?: string;
  texto: string;
  intersecta: (f: Faixa) => boolean;
}

function predicadosDeAno(seg: string): PredAno[] {
  const out: PredAno[] = [];
  const q = (m: RegExpMatchArray) => m[1]?.toLowerCase();

  for (const m of seg.matchAll(/(?:\b([A-Za-z_]\w*)\.)?\bano\s*=\s*(\d{4})\b/gi)) {
    const a = Number(m[2]);
    out.push({ qual: q(m), texto: `ano = ${a}`, intersecta: (f) => a >= f.min && a <= f.max });
  }
  for (const m of seg.matchAll(/(?:\b([A-Za-z_]\w*)\.)?\bano\s+IN\s*\(([^)]*)\)/gi)) {
    const anos = [...m[2]!.matchAll(/\d{4}/g)].map((x) => Number(x[0]));
    if (!anos.length) continue;
    out.push({
      qual: q(m),
      texto: `ano IN (${anos.join(", ")})`,
      intersecta: (f) => anos.some((a) => a >= f.min && a <= f.max),
    });
  }
  for (const m of seg.matchAll(
    /(?:\b([A-Za-z_]\w*)\.)?\bano\s+BETWEEN\s+(\d{4})\s+AND\s+(\d{4})/gi,
  )) {
    const lo = Number(m[2]), hi = Number(m[3]);
    out.push({
      qual: q(m),
      texto: `ano BETWEEN ${lo} AND ${hi}`,
      intersecta: (f) => lo <= f.max && hi >= f.min,
    });
  }
  for (const m of seg.matchAll(/(?:\b([A-Za-z_]\w*)\.)?\bano\s*(>=|<=|>|<)\s*(\d{4})/gi)) {
    const op = m[2]!, a = Number(m[3]);
    const intersecta = (f: Faixa) =>
      op === ">=" ? f.max >= a : op === ">" ? f.max > a : op === "<=" ? f.min <= a : f.min < a;
    out.push({ qual: q(m), texto: `ano ${op} ${a}`, intersecta });
  }
  return out;
}

const temColunaAno = (ref: string) =>
  (colunasDe(ref) ?? []).some((c) => c.name.toLowerCase() === "ano");

/**
 * Camada 7 — o filtro de ano cai fora da faixa que a tabela tem.
 *
 * O caso medido em 2026-09-01: o modelo montou CAGED × RAIS × PIB com as chaves
 * certas e LPAD nas duas pontas, e filtrou `ano = 2022`. `br_ibge_pib.municipio`
 * termina em **2021**. O join deu zero e o harness reportou zero como se fosse
 * resposta — a falha cara, a que não dá exceção. `anos.ts` já sabia a faixa das
 * 377 tabelas e não bloqueava nada: só serviu para explicar o n=0 depois do fato.
 *
 * Quando esta camada se CALA de propósito, porque falso positivo aqui rejeita
 * trabalho legítimo em silêncio:
 *
 *  - tabela sem faixa conhecida (`faixaDeAnos` devolve null) nunca acusa;
 *  - predicado qualificado (`p.ano = 2022`) cujo apelido não bate com nenhuma
 *    tabela real do escopo — é CTE ou subconsulta, e o ano de lá já foi checado
 *    no escopo dele;
 *  - predicado cru (`ano = 2022`) num escopo onde MAIS DE UMA tabela tem coluna
 *    `ano`: não dá para dizer de quem é o filtro sem resolver o binder do DuckDB,
 *    e chutar acusaria a tabela errada. Nesse caso o portão deixa passar e o
 *    n=0, se vier, volta pela mensagem de `mcp.ts`, que lista as faixas reais.
 */
function checaAno(sql: string): Veredito {
  const ctes = ctesDefinidos(sql);
  for (const seg of segmentos(sql)) {
    const refs = refsDoEscopo(seg, ctes);
    if (!refs.length) continue;
    const comAno = refs.filter((r) => temColunaAno(r.ref));

    for (const p of predicadosDeAno(seg)) {
      const alvo = p.qual
        ? refs.find((r) => r.apelidos.has(p.qual!))
        : comAno.length === 1 ? comAno[0] : undefined;
      if (!alvo) continue;
      const f = faixaDeAnos(alvo.ref);
      if (!f || p.intersecta(f)) continue;
      return {
        ok: false,
        camada: "ano",
        erro:
          `${alvo.ref} só tem dados de ${f.min} a ${f.max}, e o filtro pede ${p.texto}. ` +
          `Fora da faixa a consulta NÃO dá erro: devolve zero linha, e zero passa por ` +
          `resposta. Conserte de um destes jeitos: (a) use um ano dentro de ` +
          `${f.min}–${f.max} — o mais recente é ${f.max}; (b) se as tabelas do ` +
          `cruzamento têm faixas diferentes, filtre cada uma pela sua e junte pelo ano ` +
          `comum; (c) se este ano é indispensável, tire ${alvo.ref} do cruzamento e diga ` +
          `na resposta que o dado não existe para ${p.texto}. ` +
          `listar_tabelas mostra a faixa de todas as tabelas do dataset.`,
      };
    }
  }
  return OK;
}

/* ------------------------------------------------------------------ *
 *  Junção sem ponte — backlog.md item 12.
 *
 *  Medido ao vivo 2026-09-03: a pergunta de 5 fontes de perguntas.md (emenda →
 *  contrato → CNPJ → TCU → PGFN) rodou 40 min, 55 SQLs, e morreu sem resposta —
 *  38 delas (69%) tentando a MESMA junção, `id_emenda = id_licitacao`, que
 *  nunca existiu: as duas tabelas não compartilham coluna nenhuma, e
 *  bridges.yaml não documenta relação entre elas. A mensagem de "zero linhas"
 *  de mcp.ts dizia "confira o tipo das duas pontas da chave" — como se fosse
 *  consertável — e o modelo tentou 38 variações cosméticas em volta da mesma
 *  chave errada.
 *
 *  NÃO é uma camada de `portao()`: rodar ANTES da execução arriscaria bloquear
 *  uma junção legítima que só ainda não está documentada em bridges.yaml — o
 *  mesmo risco de falso positivo que a camada `ano` evita calando-se de
 *  propósito (ver o comentário dela). Em vez disso, `mcp.ts` chama isto só
 *  quando a consulta JÁ rodou e voltou zero linhas — nesse ponto já se sabe
 *  empiricamente que a junção não achou nada, e a pergunta é só "por quê", não
 *  "devo deixar rodar".
 */

/** Pares `alias.coluna = alias.coluna` dentro de um texto de ON. */
function paresIgualdade(texto: string): Array<[string, string, string, string]> {
  const out: Array<[string, string, string, string]> = [];
  for (const m of texto.matchAll(
    /\b([A-Za-z_]\w*)\.([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)\.([A-Za-z_]\w*)/g,
  )) {
    out.push([m[1]!, m[2]!, m[3]!, m[4]!]);
  }
  return out;
}

export interface JuncaoSemPonte {
  refA: string; colA: string; refB: string; colB: string;
}

/**
 * As junções entre tabelas de datasets DIFERENTES cuja coluna usada não é uma
 * ponte curada (bridges.yaml) nem uma chave canônica com o mesmo nome dos dois
 * lados (`id_municipio`, `sigla_uf`, `ano`, `id_uf`). Uma lista vazia não prova
 * que a junção está certa — só que ela não caiu num buraco CONHECIDO.
 */
export function juncoesSemPonte(sql: string): JuncaoSemPonte[] {
  const ctes = ctesDefinidos(sql);
  const achados: JuncaoSemPonte[] = [];
  for (const seg of segmentos(sql)) {
    const refs = refsDoEscopo(seg, ctes);
    if (refs.length < 2) continue;
    for (const m of seg.matchAll(
      /\bJOIN\s+[A-Za-z_][\w.]*(?:\s+(?:AS\s+)?[A-Za-z_]\w*)?\s+ON\s+([\s\S]*?)(?=\bJOIN\b|\bWHERE\b|\bGROUP\b|\bORDER\b|\bLIMIT\b|\bQUALIFY\b|$)/gi,
    )) {
      for (const [a1, c1, a2, c2] of paresIgualdade(m[1]!)) {
        const r1 = refs.find((r) => r.apelidos.has(a1.toLowerCase()));
        const r2 = refs.find((r) => r.apelidos.has(a2.toLowerCase()));
        if (!r1 || !r2 || r1.ref === r2.ref) continue;
        if (r1.ref.split(".")[0] === r2.ref.split(".")[0]) continue; // mesmo dataset, sem risco
        const k1 = conceitoDaColuna(r1.ref, c1);
        const k2 = conceitoDaColuna(r2.ref, c2);
        if (k1 && k1 === k2) continue; // ponte confirmada, curada ou canônica
        achados.push({ refA: r1.ref, colA: c1, refB: r2.ref, colB: c2 });
      }
    }
  }
  return achados;
}

/** Mensagem que ensina o próximo passo, não só aponta o buraco. */
export function mensagemSemPonte(achados: JuncaoSemPonte[]): string {
  return achados.map((a) =>
    `Nenhuma ponte conhecida entre ${a.refA}.${a.colA} e ${a.refB}.${a.colB} — ` +
    `bridges.yaml não documenta essa relação, e o nome da coluna não bate por ` +
    `convenção. Pode não existir junção direta entre estas duas tabelas neste ` +
    `espelho. Antes de tentar outra variação desta MESMA junção: chame ` +
    `descrever_tabela nas duas e procure uma coluna que aponte de uma pra outra ` +
    `(CNPJ, id_orgao, id_municipio); se não achar nenhuma, responda só com a ` +
    `parte que tem dado e diga que este cruzamento não é possível com as ` +
    `tabelas disponíveis.`
  ).join("\n");
}

/**
 * Assinatura estrutural de FROM/JOIN/ON, sem literal nem espaço — pra detectar
 * quando o modelo tenta a MESMA junção de novo com cosmético diferente em
 * volta (WHERE, LIMIT, colunas do SELECT). Medido: 38 das 55 tentativas do
 * caso acima variavam só o que fica FORA desta assinatura.
 */
export function assinaturaJuncao(sql: string): string {
  const semLiterais = sql
    .replace(/'[^']*'/g, "?")
    .replace(/\b\d+\b/g, "?")
    .toLowerCase();
  const m = /\bfrom\b[\s\S]*?(?=\bwhere\b|\bgroup\s+by\b|\border\s+by\b|\blimit\b|$)/.exec(semLiterais);
  return (m ? m[0] : semLiterais).replace(/\s+/g, " ").trim();
}

/**
 * Estatísticas cujo número **não carrega o tamanho da amostra**: uma média de 3
 * municípios e uma de 5.570 saem idênticas na tela.
 */
const DERIVADAS =
  /\b(AVG|MEDIAN|QUANTILE\w*|STDDEV\w*|STDEV\w*|VAR_POP|VAR_SAMP|VARIANCE|CORR|COVAR\w*|REGR_\w+|MODE)\s*\(/i;

/** Razão escrita à mão entre dois agregados — `SUM(pib) / NULLIF(SUM(pop),0)`. */
const RAZAO =
  /\b(?:SUM|COUNT)\s*\([\s\S]{0,120}?\)\s*(?:::\s*\w+\s*)?\/\s*(?:NULLIF\s*\(\s*)?(?:SUM|COUNT|AVG)\s*\(/i;

/**
 * Camada 8 — estatística derivada sem `COUNT(*) AS n`.
 *
 * A regra existia só no `laco.ts` (prompt da etapa 5), que é o caminho
 * aposentado; no laço agêntico o número volta da **prosa do modelo**, e foi
 * assim que "573 em vez de 789" entrou na Rodada 6 — um grupo do `GROUP BY`
 * lido como total. O `n` é a impressão digital do join: RAIS × SIM × Censo por
 * município com os filtros certos dá um número específico, e qualquer erro de
 * chave ou de partição dá outro.
 *
 * **O recorte, e por que não é "toda consulta agregada":** exigir `n` de todo
 * `SUM`/`COUNT` rejeitaria trabalho legítimo — um `SUM(pib)` puro e um
 * `GROUP BY` de ranking já carregam a própria ordem de grandeza, e a rejeição
 * seria só atrito. A camada cobra `n` **apenas quando o resultado é uma
 * estatística derivada** — média, mediana, desvio, correlação, regressão ou
 * razão entre agregados —, que é exatamente a família em que o número sozinho é
 * indefensável: sem o n não dá para separar um coeficiente de 0,97 sobre 5.000
 * pares de um sobre 4.
 *
 * Olha só o escopo EXTERNO (a projeção final, com as subconsultas apagadas):
 * um `AVG` intermediário dentro de um CTE não é o que se reporta. Isso deixa um
 * buraco conhecido — `WITH m AS (SELECT AVG(x) AS media …) SELECT * FROM m` não
 * é cobrado —, e é o lado certo de errar: silêncio em vez de falso positivo.
 *
 * O nome tem que ser literalmente `n`: quem lê o resultado procura a coluna
 * chamada `n`, e "o primeiro número da linha" apanhava o coeficiente de
 * correlação no lugar do tamanho da amostra.
 */
function checaAmostra(sql: string): Veredito {
  const externo = segmentos(sql).at(-1) ?? sql;
  const derivada = DERIVADAS.exec(externo)?.[1];
  const razao = !derivada && RAZAO.test(externo);
  if (!derivada && !razao) return OK;
  if (/\bAS\s+"?n"?\b/i.test(externo)) return OK;

  const oQue = derivada ? `${derivada.toUpperCase()}(...)` : "uma razão entre agregados";
  return {
    ok: false,
    camada: "amostra",
    erro:
      `O SELECT final devolve ${oQue} sem o tamanho da amostra. Uma média ou ` +
      `correlação sobre 4 linhas e sobre 5.000 saem idênticas na tela, e é assim que ` +
      `um número errado passa por certo. Acrescente ao SELECT final a coluna ` +
      `\`COUNT(*) AS n\` — o nome tem que ser exatamente \`n\`, é por ele que o ` +
      `tamanho da amostra é lido. Ex.: ` +
      `SELECT corr(a, b) AS corr, COUNT(*) AS n FROM ... . ` +
      `Contagem e soma puras não precisam disso; só média, mediana, desvio, ` +
      `correlação, regressão e razão.`,
  };
}

/* ------------------------------------------------------------------ *
 *  Sanidade — depois da execução, sobre as linhas que voltaram.
 *
 *  Ver `alertasDeSanidade`: aqui NADA vira rejeição dura. A rejeição dura
 *  desta família é a camada 8, que age ANTES de executar, sobre a forma da
 *  consulta — a única leitura que não tem exceção legítima.
 * ------------------------------------------------------------------ */

export type Linha = Record<string, unknown>;

/** Os 5.570 municípios do país — o teto natural de um resultado por município. */
export const MUNICIPIOS_BR = 5570;

/**
 * O `n` do resultado: a coluna literalmente chamada `n`, nunca "o primeiro
 * número da linha" — isso apanhava o coeficiente de correlação e comparava
 * laranja com maçã.
 */
export function extraiN(linhas: Linha[]): number | undefined {
  const prim = linhas[0];
  if (!prim) return undefined;
  const chave = Object.keys(prim).find((k) => k.toLowerCase() === "n");
  if (chave === undefined) return linhas.length > 1 ? linhas.length : undefined;
  const v = Number(prim[chave]);
  return Number.isFinite(v) ? v : undefined;
}

/** Colunas cujo valor é numérico em toda linha — candidatas a somar. */
function colunasNumericas(linhas: Linha[]): string[] {
  const prim = linhas[0];
  if (!prim) return [];
  return Object.keys(prim).filter((k) =>
    linhas.every((l) => l[k] !== null && l[k] !== "" && Number.isFinite(Number(l[k]))),
  );
}

/**
 * Alertas de sanidade sobre o resultado — portados da etapa 8 do `laco.ts`, o
 * pipeline aposentado, onde eles só apareciam num `passos[]` que ninguém lê.
 *
 * **Por que nenhum destes rejeita.** Todos têm leitura legítima:
 *
 *  - `n > 5.570` é o esperado quando o grão não é um município por linha —
 *    município × ano, ou contagem de pessoas/vínculos. Rejeitar mataria toda
 *    consulta de painel multianual, que é a maioria das que importam aqui.
 *  - `corr > 0,95` acontece de verdade entre população e eleitorado.
 *  - várias linhas num `GROUP BY` é o resultado correto de um ranking.
 *  - `circunstancia_obito` sozinho é uma leitura válida quando a pergunta é
 *    sobre a circunstância registrada, não sobre a causa médica — o alerta
 *    é só para o caso comum de classificar causa de óbito por ele.
 *
 * O que faz o alerta valer é o modelo **ver** — por isso ele volta grudado no
 * resultado da ferramenta `consultar`, no mesmo texto e antes dos dados, e não
 * num log. A única desta família que rejeita é a camada 8 (`n` ausente), porque
 * lá não há leitura legítima: é forma da consulta, não julgamento do número.
 */
export function alertasDeSanidade(sql: string, linhas: Linha[]): string[] {
  const alertas: string[] = [];

  // backlog.md item 9, medido em 2026-09-03 ao vivo (não procurado — apareceu
  // testando outra coisa). br_ms_sim.circunstancia_obito é decodificado via
  // dicionario e mais fácil de achar que causa_basica (CID), mas está
  // sub-preenchido: RJ 2020, substr(causa_basica,1,3) BETWEEN 'X60' AND 'X84'
  // dá 789 óbitos por suicídio; circunstancia_obito = '2' (Suicídio) dá só
  // 749 — 40 óbitos que o CID classifica como suicídio não têm o campo
  // preenchido. O modelo achou o número errado, plausível, sem o portão
  // acusar nada: é a mesma classe da camada 6 (codificação), só que num
  // campo que ela não cobre.
  if (/\bcircunstancia_obito\b/i.test(sql) && !/\bcausa_basica\b/i.test(sql)) {
    alertas.push(
      "circunstancia_obito classifica causa de óbito, mas está SUB-PREENCHIDO: " +
      "medido em RJ 2020, circunstancia_obito='2' (Suicídio) deu 749 contra 789 " +
      "de causa_basica/CID (substr(causa_basica,1,3) BETWEEN 'X60' AND 'X84') — " +
      "40 óbitos que o CID classifica como suicídio não têm o campo preenchido. " +
      "Se a pergunta é sobre causa médica de óbito, prefira causa_basica (CID-10); " +
      "circunstancia_obito só é a leitura certa se a pergunta for sobre a " +
      "circunstância registrada, não sobre a causa.",
    );
  }

  const prim = linhas[0];
  if (!prim) return alertas;

  // Medido em 2026-09-01: o pipeline fixo respondeu 573 onde o total era 789 —
  // agrupou por sexo e reportou UM grupo como se fosse o total. É o erro que o
  // laço agêntico não pode repetir na prosa, e ele não custa nada de avisar.
  if (linhas.length > 1 && /\bGROUP\s+BY\b/i.test(sql)) {
    const num = colunasNumericas(linhas);
    const alvo = num.find((k) => k.toLowerCase() === "n") ?? (num.length === 1 ? num[0] : undefined);
    const soma = alvo
      ? ` Somando a coluna '${alvo}' nas ${linhas.length} linhas: ` +
        `${linhas.reduce((s, l) => s + Number(l[alvo]), 0)}.`
      : "";
    alertas.push(
      `São ${linhas.length} linhas e cada uma é um GRUPO do GROUP BY, não o total.` +
      soma +
      ` Se a pergunta pede um número só, some os grupos ou tire o GROUP BY — ` +
      `reportar um grupo como total já aconteceu aqui (573 no lugar de 789).`,
    );
  }

  const n = extraiN(linhas);
  if (n !== undefined && n > MUNICIPIOS_BR && /municipio/i.test(sql)) {
    alertas.push(
      `n=${n} passa dos ${MUNICIPIOS_BR.toLocaleString("pt-BR")} municípios do país. ` +
      `Se cada linha deveria ser um município, o join duplicou linhas — uma das pontas ` +
      `tem mais de uma linha por município (por ano, por sexo, por CNAE). Confira com ` +
      `COUNT(DISTINCT id_municipio) e agregue a ponta duplicada antes do join. ` +
      `Se o grão é município × ano de propósito, está certo: diga o grão na resposta.`,
    );
  }

  for (const [k, v] of Object.entries(prim)) {
    const x = Number(v);
    if (/^(corr|correlacao|r|r2|rho)$/i.test(k) && Number.isFinite(x) && Math.abs(x) > 0.95) {
      alertas.push(
        `${k}=${x} é alto demais para dado social. Quase sempre é auto-correlação: as ` +
        `duas colunas medem a mesma coisa (população dos dois lados, ou um total contra ` +
        `uma parte dele). Confira se as variáveis são independentes; se forem, ` +
        `normalize por população antes de correlacionar. Reporte sempre com o n.`,
      );
    }
  }
  return alertas;
}

/**
 * Faixa de anos das tabelas citadas, em uma linha — para a mensagem de n=0.
 * Devolve "" quando nenhuma tabela citada tem faixa conhecida.
 */
export function faixasCitadas(sql: string): string {
  const partes: string[] = [];
  for (const ref of tabelasCitadas(sql)) {
    if (!ref.includes(".")) continue;
    const f = faixaDeAnos(ref);
    if (f) partes.push(`${ref}: ${f.min}–${f.max}`);
  }
  return partes.join("; ");
}

/**
 * Roda as camadas em ordem de custo: as baratas e locais primeiro, para que o
 * modelo gaste as tentativas de reparo em erro real e não em ida ao beelink.
 * O EXPLAIN (que fala com o beelink) é `checaExplain`, chamado à parte.
 */
export function portao(sql: string): Veredito {
  const leitura = checkReadOnly(sql);
  if (leitura) return { ok: false, camada: "read-only", erro: leitura };

  for (const camada of [checaTabelas, checaInservivel, checaColunas, checaParticao, checaLimite, checaCodificacao, checaAno, checaAmostra]) {
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
/**
 * Camada de grounding — a resposta final não pode existir sem consulta real.
 *
 * Achado ao vivo 2026-09-04, testando `THINKING=1` (não era o que se estava
 * procurando): na pergunta canônica do suicídio RJ 2020, o modelo explorou o
 * schema (`listar_tabelas`, `descrever_tabela` ×2) e foi direto pra
 * `revisar_resposta` com **467 óbitos (355 M / 112 F)** — número inventado,
 * SEM NUNCA CHAMAR `consultar`. `revisar_resposta` aprovou, porque
 * `checaCitacaoTabela` só olha se a prosa cita tabela/dataset — nunca se ela
 * veio de dado real. É pior que SQL errado: SQL errado pelo menos executa
 * contra o beelink e pode ser pego por partição/coluna/zero-linhas; isto
 * pula a execução inteira e ainda assim tem aparência de resposta apurada.
 *
 * A regra é deliberadamente cega ao CONTEÚDO da prosa — não tenta adivinhar
 * "isto parece uma estatística inventada" por regex (frágil: teria que
 * distinguir um número fabricado de um ano citado da própria pergunta, e
 * errar pra qualquer lado é ruim). Em vez disso, é incondicional: a persona
 * deste harness instrui SEMPRE chamar `revisar_resposta` antes de responder
 * (`dsh/rodado.patch.yml`), então nenhuma resposta final legítima deveria
 * existir sem pelo menos uma consulta que voltou linha — o próprio trabalho
 * deste harness é apurar contra o mirror, não redigir de memória.
 */
/**
 * "Olhou antes de tocar" — o análogo do `Edit` do Claude Code exigir um `Read`
 * antes: a pré-condição é do SERVIDOR, não um conselho na descrição.
 *
 * Medido no head-to-head de 2026-09-04 (`tasks/ferramentas_claude_code.md`):
 * das 21 chamadas da sessão `53ac1869`, três (15, 16, 17) inventaram
 * `_rodado_metadata` — tabela que existe no `mcp_server.py` e NÃO no contrato
 * de 6 ferramentas do harness. Cada uma custou uma ida ao beelink para
 * devolver erro. Uma tabela que o modelo nunca descreveu é uma tabela sobre a
 * qual ele está chutando.
 *
 * Roda DEPOIS de `portao()` de propósito: assim uma tabela que não existe no
 * catálogo recebe a mensagem certa da camada 2 ("não existe, chame
 * listar_tabelas") em vez desta, que fala de descrever. As duas são locais, a
 * ordem só escolhe qual ensina melhor.
 */
export function checaDescritaAntes(sql: string, descritas: Iterable<string>): Veredito {
  const vistas = new Set([...descritas].map((t) => t.toLowerCase()));
  const faltando = tabelasCitadas(sql)
    .filter((r) => r.includes("."))
    .filter((r) => !vistas.has(r.toLowerCase()));
  if (!faltando.length) return { ok: true };
  return {
    ok: false,
    camada: "nao-descrita",
    erro:
      `Você ainda não chamou descrever_tabela para: ${faltando.join(", ")}. ` +
      `Descreva antes de consultar — é local, não custa ida ao banco, e devolve as ` +
      `colunas reais (mais as pontes de junção conferidas). Consultar sem isso é ` +
      `chutar nome de coluna, e o erro só volta depois de gastar a consulta.`,
  };
}

export function checaExecutouConsulta(consultasComResultado: number): Veredito {
  if (consultasComResultado > 0) return OK;
  return {
    ok: false,
    camada: "sem-consulta",
    erro:
      "Nenhuma consulta SQL foi executada com sucesso nesta pergunta ainda — a resposta " +
      "final não pode ser aprovada sem vir de dado real apurado no beelink, mesmo que o " +
      "texto pareça correto. Chame consultar com a SQL que apura o número, confira que " +
      "ela devolveu linhas, e só depois chame revisar_resposta de novo.",
  };
}

/* ------------------------------------------------------------------ *
 *  Citação — não é camada de SQL, é checagem da PROSA final.
 * ------------------------------------------------------------------ */

/** `br_`/`world_`/`us_` seguido de `.tabela` — os três prefixos do espelho. */
const CITA_TABELA = /\b(?:br|world|us)_[a-z0-9_]+\.[a-z0-9_]+\b/gi;

/**
 * A prosa final cita a ferramenta, não o órgão. backlog.md item 3: a convenção
 * de `pages/analises/results/` é citar o ÓRGÃO de origem do dado (ex.: "Ministério
 * da Saúde/SIM", "IBGE") — nunca a tabela, nunca o SQL. Hoje nenhuma resposta
 * gerada sai publicável sem edição à mão.
 *
 * Não é uma camada de `portao()` — roda sobre texto em português, não SQL, e é
 * chamada pela ferramenta `revisar_resposta` do MCP, não por `consultar`. A
 * instrução sozinha no system prompt é do tipo que o modelo obedece na maioria
 * das vezes; esta checagem, chamada como ferramenta ANTES do modelo poder
 * encerrar, transforma "maioria" em "todas" — mesmo mecanismo que faz o portão
 * de SQL funcionar: a rejeição volta como resultado de ferramenta, e o laço
 * agêntico do dsh reescreve.
 */
export function checaCitacaoTabela(texto: string): Veredito {
  const achados = [...new Set([...texto.matchAll(CITA_TABELA)].map((m) => m[0]))];
  if (!achados.length) return OK;
  return {
    ok: false,
    camada: "citacao",
    erro:
      `A resposta cita a tabela/dataset diretamente: ${achados.join(", ")}. Troque pelo ` +
      "ÓRGÃO de origem do dado (ex.: Ministério da Saúde/SIM, IBGE, RAIS/CAGED do " +
      "Ministério do Trabalho) — nunca o nome da tabela, do dataset nem SQL na resposta final.",
  };
}

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
