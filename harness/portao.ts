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
 *    registrado no AGENTS.md;
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
import { colunasDe, camposPontuados, linhasDe, particoesDe, inservivel, LIMIAR_PARTICAO, tabelaPrincipal, resolveDataset } from "./catalogo.ts";
import { sugereTabelas, sugereDatasets, tabelasDoDataset, DIRETORIOS } from "./semantica.ts";
import { codigos } from "./dicionarios.ts";
import { valores } from "./valores.ts";
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

/**
 * SUM(populacao) no mesmo escopo que microdados, com JOIN: a população entra uma
 * vez por LINHA do microdado. Medido 2026-09-22: taxa de homicídio por UF saiu
 * 0,9 por 100 mil (o certo é ~42 em SE) — SIM × população municipal juntados
 * óbito a óbito e a população somada por óbito.
 */
const DENOMINADOR = /\bSUM\s*\(\s*(?:\w+\.)?(populacao|pop|pib|area|area_total|domicilios|habitantes)\s*\)/i;
function fanOut(sql: string): string | undefined {
  const ctes = ctesDefinidos(sql);
  for (const seg of segmentos(sql)) {
    if (!DENOMINADOR.test(seg) || !/\bJOIN\b/i.test(seg)) continue;
    const grande = refsDoEscopo(seg, ctes).find((r) => (linhasDe(r.ref) ?? 0) > 1_000_000);
    if (grande) {
      return `SUM(${DENOMINADOR.exec(seg)![1]}) numa junção com ${grande.ref} (${((linhasDe(grande.ref) ?? 0) / 1e6).toFixed(0)}M linhas): ` +
        `o denominador é somado uma vez por LINHA do microdado e a taxa sai errada. Agregue cada lado numa CTE ` +
        `no mesmo nível (ex.: óbitos por sigla_uf; população por sigla_uf e ano) e só depois junte e divida.`;
    }
  }
  return undefined;
}

/** Tabelas `brasil`/`uf`/`regiao` do mesmo dataset de uma tabela de unidade menor citada. */
function tabelasAgregadas(sql: string): string[] {
  const out = new Set<string>();
  for (const ref of tabelasCitadas(sql)) {
    const [ds, tb] = ref.toLowerCase().split(".");
    // Os diretórios têm uf/regiao, mas são cadastro de nomes, não índice agregado:
    // 2026-09-23 o alerta disparou num AVG de temperatura por município.
    if (!ds || !tb || tb === "brasil" || ds.startsWith("br_bd_diretorios")) continue;
    // A média das 27 UFs também não é o Brasil (2026-09-23: IDEB médio estadual
    // saiu 3,8 pela média de br_inep_ideb.uf; o oficial, em .brasil, é 3,9).
    const niveis = tb === "uf" || tb === "regiao" ? ["brasil"] : ["brasil", "uf", "regiao"];
    for (const nivel of niveis) {
      if (colunasDe(`${ds}.${nivel}`)) out.add(`${ds}.${nivel}`);
    }
  }
  return [...out];
}

/**
 * "Parecidas: ..." para um nome inventado, e onde estão os nomes de lugar.
 *
 * Dataset certo com tabela errada (ou sem tabela) lista as tabelas DAQUELE
 * dataset: 'br_ibge_populacao' e 'br_ibge_pib' sem tabela foram os dois erros
 * de tabela mais frequentes das rodadas de 2026-09-25 a 27 (8 e 7 sessões), e a
 * busca por parecença devolvia tabelas do Censo, porque 'populacao' casava o
 * nome da tabela deles e não o `municipio` de br_ibge_populacao. Dataset
 * inexistente sugere datasets pelo termo distintivo (`br_me_sicor` → br_bcb_sicor).
 */
export function sugestao(ref: string): string {
  const semTabela = !ref.includes(".");
  const ds = resolveDataset(ref.split(".")[0]!);
  if (ds) {
    const tabs = tabelasDoDataset(ds);
    const lugar = /municip|cidade|estado|\buf\b|diretori|nome/i.test(ref.split(".")[1] ?? "") ? ` ${DIRETORIOS}` : "";
    return ` (${semTabela ? `'${ref}' é o dataset; ` : ""}tabelas de ${ds}: ${tabs.join(", ")})` + lugar.replace(/\.$/, "");
  }
  const dss = sugereDatasets(ref);
  if (dss.length) return ` (datasets com esse nome: ${dss.join(", ")} — confira o nome exato no CATÁLOGO)`;
  const s = sugereTabelas(ref);
  const lugar = /municip|cidade|estado|\buf\b|diretori|nome/i.test(ref) ? ` ${DIRETORIOS}` : "";
  return (s.length ? ` (parecidas que existem: ${s.join(", ")})` : "") + lugar.replace(/\.$/, "");
}

/** O CTE definido a até 2 edições de `ref` (erro de grafia), ou undefined. */
function cteParecida(ref: string, ctes: Set<string>): string | undefined {
  const a = ref.toLowerCase();
  for (const c of ctes) if (c !== a && distancia(a, c) <= 2 && Math.min(a.length, c.length) >= 5) return c;
  return undefined;
}

/** Distância de edição (Levenshtein), para nomes curtos. */
function distancia(a: string, b: string): number {
  let ant = Array.from({ length: b.length + 1 }, (_, j) => j);
  for (let i = 1; i <= a.length; i++) {
    const cur = [i];
    for (let j = 1; j <= b.length; j++) {
      cur[j] = Math.min(ant[j]! + 1, cur[j - 1]! + 1, ant[j - 1]! + (a[i - 1] === b[j - 1] ? 0 : 1));
    }
    ant = cur;
  }
  return ant[b.length]!;
}

/** Camada 2 — o modelo escreveu `FROM dataset` sem a tabela? */
function checaTabelas(sql: string): Veredito {
  const ruins: string[] = [];
  for (const ref of tabelasCitadas(sql)) {
    if (ref.includes("(")) continue;
    if (!ref.includes(".")) {
      // CTE com erro de grafia: `estban_agencies` para a `estban_agencias`
      // definida. A mensagem antiga ("escreva dataset.tabela") mandou o modelo
      // procurar tabela e ele reenviou a mesma SQL 4x (T07-2, 2026-09-27).
      const cte = cteParecida(ref, ctesDefinidos(sql));
      if (cte) ruins.push(`'${ref}' não é tabela nem CTE — você definiu a CTE '${cte}'; confira a grafia`);
      else ruins.push(`'${ref}' não tem tabela — escreva dataset.tabela${sugestao(ref)}`);
      continue;
    }
    if (colunasDe(ref) === null) ruins.push(`'${ref}' não existe no espelho${sugestao(ref)}`);
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
  // Campo de struct só vale depois do pai (`unidadeOrgao.codigoIbge`), nunca
  // solto (`c.codigoIbge`) — B37.
  const campos = new Set<string>();
  for (const r of refs) {
    const cols = colunasDe(r) ?? [];
    for (const c of cols) conhecidas.add(c.name.toLowerCase());
    for (const p of camposPontuados(cols)) campos.add(p.toLowerCase());
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
  // Literal de texto sai também: `'br_ibge_pib.municipio' AS fonte` não é
  // alias.coluna (B25, T81-2 da B19: "Coluna inexistente: municipio").
  const semTabelas = refs.reduce((acc, r) => acc.split(r).join(" "), sql.replace(/'(?:[^']|'')*'/g, "''"));

  const suspeitas = new Set<string>();
  // A coluna aceita letra com acento (\p{L}): o DuckDB aceita `d.Função` sem
  // aspas, e com \w ASCII o portão lia `Fun` e rejeitava coluna real — B24,
  // T16-4 da B19, 10 rejeições seguidas de "Coluna inexistente: Fun, Subfun, A".
  for (const [, pai, col] of semTabelas.matchAll(/\b([A-Za-z_][\w]*)\.([\p{L}_][\p{L}\p{N}_]*)/gu)) {
    const c = col.toLowerCase();
    if (campos.has(`${pai!.toLowerCase()}.${c}`)) continue;
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
    const todas = colunasDe(r) ?? [];
    const cols = [...todas.map((c) => c.name), ...camposPontuados(todas)];
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

/** Coluna de tempo ou de código: somar não dá total de nada (B36). */
export function naoSomavel(col: string): boolean {
  return /^(ano|mes|dia|trimestre|semestre|semana)(_|$)|^(id|cod|codigo|sigla)(_|$)/i.test(col);
}

/** Camada 4 — filtro de partição em tabela grande. O que evita o lock de horas. */
/**
 * Código de município do TSE igualado a código IBGE. Rodadas de 2026-09-25 a 27:
 * 4 sessões (T05-1 nas três rodadas, T05-5) juntaram `id_municipio_tse` com o
 * `id_municipio` do PIB/população ou do transferegov, e todas voltaram zero
 * linha ou r NULL. As duas numerações não se encontram (35 é Porto Velho no TSE),
 * e as tabelas de br_tse_eleicoes já trazem `id_municipio` (IBGE) ao lado.
 */
const COD_TSE = /\b(?:\w+\.)?id_municipio_tse\w*\b/i;
export function checaCodigoTse(sql: string): Veredito {
  const limpo = semComentarios(sql).replace(/'(?:[^']|'')*'/g, "''");
  const ident = String.raw`(?:CAST\s*\(\s*)?(?:\w+\.)?\w+`;
  const re = new RegExp(String.raw`(${ident})\s*=\s*(${ident})`, "gi");
  for (const [, a, b] of limpo.matchAll(re)) {
    const [tse, outro] = COD_TSE.test(a!) ? [a!, b!] : COD_TSE.test(b!) ? [b!, a!] : [];
    if (!tse || /_tse/i.test(outro!) || !/municip|ibge/i.test(outro!)) continue;
    return {
      ok: false, camada: "codigo-tse",
      erro: `${tse.trim()} = ${outro!.trim()}: id_municipio_tse é o código do TSE (numeração própria, que ` +
        `repete entre UFs), não o IBGE de 7 dígitos — igualar os dois dá zero linha. As tabelas de ` +
        `br_tse_eleicoes também têm id_municipio (IBGE): junte por ele. Sem ele, passe por ` +
        `br_bd_diretorios_brasil.municipio (id_municipio_tse + sigla_uf → id_municipio).`,
    };
  }
  return OK;
}

function checaParticao(sql: string): Veredito {
  const upper = sql.toUpperCase();
  for (const ref of tabelasCitadas(sql)) {
    if (!ref.includes(".")) continue;
    const linhas = linhasDe(ref);
    if (linhas === null || linhas < LIMIAR_PARTICAO) continue;
    const parts = particoesDe(ref);
    if (!parts.length) continue;
    // B34, T22-2 da B19: a CTE lia br_ms_sim.microdados inteira e só um
    // `WHERE o.ano = 2021` de fora satisfazia a busca na SQL toda. O filtro tem
    // que estar no escopo (CTE/subconsulta) que lê a tabela — como checaAno faz.
    const filtra = (txt: string) => parts.some((p) =>
      new RegExp(`\\b${p.toUpperCase()}\\s*(=|IN|BETWEEN|>|<|>=|<=)`).test(txt.toUpperCase()),
    );
    const ctes = ctesDefinidos(sql);
    const escopos = segmentos(sql).filter((s) =>
      refsDoEscopo(s, ctes).some((r) => r.ref.toLowerCase() === ref.toLowerCase()));
    const temFiltro = escopos.length ? escopos.every(filtra) : filtra(upper);
    if (!temFiltro && !scanBarato(sql, ref, linhas)) {
      return {
        ok: false,
        camada: "particao",
        erro:
          `${ref} tem ${(linhas / 1e6).toFixed(1)}M linhas e exige filtro de partição. ` +
          `Adicione um predicado em: ${parts.join(", ")}. ` +
          `Ex.: WHERE ${exemploParticao(parts)}.` +
          // B28, T15-3: o exemplo 'RJ' levou o modelo a medir filiação só em SP
          // numa pergunta sobre o país. Abaixo do teto, o caminho nacional existe.
          (linhas < LIMIAR_SEM_FILTRO
            ? ` Se a pergunta é sobre o país, não recorte um estado (o recorte muda a pergunta): ` +
              `agregue ${ref} sozinha numa CTE, sem JOIN (ex.: SELECT id_municipio, COUNT(*) ... GROUP BY 1), ` +
              `e junte o resultado depois — assim o filtro não é exigido.`
            : ""),
      };
    }
  }
  return OK;
}

/**
 * Até aqui um scan inteiro custa segundos no DuckDB (siconfi 19–27M, sicar 79M,
 * filiação 17M). O que travou o beelink por horas foi join sem filtro contra as
 * tabelas de bilhões do CNPJ, que continuam acima do teto.
 */
const LIMIAR_SEM_FILTRO = 100_000_000;
const AGREGA = /\b(GROUP\s+BY|DISTINCT|COUNT|SUM|AVG|MIN|MAX)\b/i;

/**
 * Leitura sem filtro de partição que não custa o que o filtro evita, nem mistura
 * anos (B25: das 27 rejeições de partição da B19, 12 eram assim):
 *  - espiada: `SELECT ... FROM t LIMIT n`, uma tabela, sem agregar nem ordenar —
 *    o DuckDB para de ler no n-ésimo registro;
 *  - `SELECT DISTINCT col ... LIMIT n` de uma tabela abaixo de LIMIAR_SEM_FILTRO:
 *    listar os códigos de `conta_bd` não depende de ano;
 *  - agregação de tabela cuja partição é só de lugar, abaixo do teto e lida
 *    sozinha no seu escopo (CTE ou subconsulta sem JOIN): o país inteiro por
 *    município (B28, T15-3). Com partição de tempo, somar sem filtro soma todos
 *    os anos — aí o filtro é a pergunta, não custo, e segue exigido.
 */
function scanBarato(sql: string, ref: string, linhas: number): boolean {
  const limite = /\bLIMIT\s+(\d+)\s*$/i.exec(sql);
  if (
    limite && Number(limite[1]) <= 1000 && tabelasCitadas(sql).length === 1 &&
    !/\b(GROUP\s+BY|COUNT|SUM|AVG|MIN|MAX|ORDER\s+BY|JOIN|OVER|WITH)\b/i.test(sql)
  ) {
    const distinct = /\bDISTINCT\b/i.test(sql);
    if (linhas < LIMIAR_SEM_FILTRO ? true : !distinct && !/\bWHERE\b/i.test(sql)) return true;
  }
  if (linhas >= LIMIAR_SEM_FILTRO) return false;
  if (!particoesDe(ref).every((p) => ["sigla_uf", "uf"].includes(p))) return false;
  const ctes = ctesDefinidos(sql);
  const alvo = ref.toLowerCase();
  const escopos = segmentos(sql).filter((s) => refsDoEscopo(s, ctes).some((r) => r.ref.toLowerCase() === alvo));
  return escopos.length > 0 && escopos.every((s) => AGREGA.test(s) && !/\bJOIN\b/i.test(s));
}

const EXEMPLO: Record<string, string> = {
  ano: "ano = 2020", mes: "mes = 3", sigla_uf: "sigla_uf = 'RJ'", uf: "uf = 'RJ'",
  ano_mes: "ano_mes = '202403'", ano_emissao: "ano_emissao = 2020", mes_emissao: "mes_emissao = 3",
};
function exemploParticao(parts: string[]): string {
  const tempo = parts.find((p) => !["sigla_uf", "uf"].includes(p));
  const lugar = parts.find((p) => ["sigla_uf", "uf"].includes(p));
  return [tempo, lugar].filter(Boolean).map((p) => EXEMPLO[p!] ?? `${p} = ...`).join(" AND ");
}

/** Camada 5 — LIMIT em consulta não agregada. */
function checaLimite(sql: string): Veredito {
  const upper = sql.toUpperCase();
  const agrega = /\b(COUNT|SUM|AVG|MIN|MAX|GROUP\s+BY|DISTINCT)\b/.test(upper);
  if (agrega || /\bLIMIT\s+\d+/.test(upper)) return OK;
  // Tabela pequena (o diretório de UFs, 27 linhas) já vem capada em 200 linhas
  // por capRows; exigir LIMIT ali só custava um turno — medido duas vezes numa
  // pergunta só em 2026-09-22.
  const refs = tabelasCitadas(sql).filter((r) => r.includes("."));
  if (refs.every((r) => (linhasDe(r) ?? Infinity) <= 100_000)) return OK;
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
    // 2026-09-22: `sexo = '2'` na RAIS (2 = Feminino, certo) era recusado, e o
    // modelo não tinha saída — descrever_tabela já mostra os códigos da tabela.
    // Com dicionário conhecido, o literal passa se for chave válida; se não for,
    // a recusa lista as válidas.
    const conferido = usaComparacao && !temDecode ? literalConferido(sql, col) : undefined;
    if (conferido === true) continue;
    if (typeof conferido === "string") return { ok: false, camada: "codificacao", erro: conferido };
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
 * Camada `valor` — literal de texto que a coluna não tem, em qualquer coluna.
 *
 * A conferência de literal existia só para `CODIFICADAS` (sexo, raca_cor...).
 * Medido 2026-09-25, triagem de 58 casos da rodada B2: 10 desistiram depois de
 * junções que voltaram vazias, e 68 consultas de zero linha tinham
 * `id_municipio = id_municipio` — a junção estava certa; o vazio vinha do
 * filtro, como `cor_raca IN ('Preto', 'Pardo')` no Censo 2022, que guarda
 * 'Preta'/'Parda' (e `valores.json` já sabia). Só recusa quando cada tabela com
 * a coluna tem a lista COMPLETA (dicionário inteiro, ou `valores` sem amostra).
 */
function checaValores(sql: string): Veredito {
  const cols = new Set<string>();
  for (const m of sql.matchAll(/\b(?:\w+\.)?([a-z_]\w*)\s*(?:=\s*'|IN\s*\(\s*')/gi)) cols.add(m[1]!.toLowerCase());
  for (const col of cols) {
    if (CODIFICADAS.has(col)) continue; // a camada de codificação cuida
    const r = literalConferido(sql, col);
    if (typeof r === "string") return { ok: false, camada: "valor", erro: r.replace("não tem o código", "não tem o valor").replace("Códigos válidos", "Valores guardados") };
  }
  return OK;
}

/** true: todo literal comparado com `col` é chave do dicionário de cada tabela
 *  citada que tem a coluna; string: a mensagem de recusa; undefined: sem dicionário. */
function literalConferido(sql: string, col: string): true | string | undefined {
  const tabelas = tabelasCitadas(sql).filter((t) => t.includes(".") && (colunasDe(t) ?? []).some((c) => c.name.toLowerCase() === col));
  if (!tabelas.length) return undefined;
  // Chaves conhecidas por tabela: o dicionário inteiro, ou os valores vistos
  // (valores.ts) quando a coluna é texto sem dicionário ('Mulheres' no Censo).
  const dics = tabelas.map((t) => {
    const d = codigos(t, col);
    if (d && d.total <= d.previa.length) return [t, d.previa] as const;
    const v = valores(t, col);
    return [t, v && !v.amostra ? v.lista.map((x) => [x, x] as [string, string]) : undefined] as const;
  });
  if (dics.every(([, d]) => !d)) return undefined;
  const literais: string[] = [];
  for (const m of sql.matchAll(new RegExp(`\\b${col}\\s*(?:=\\s*('[^']*'|\\d+)|IN\\s*\\(([^)]*)\\))`, "gi"))) {
    const lista = m[1] ? [m[1]] : (m[2] ?? "").split(",");
    for (const x of lista) literais.push(x.trim().replace(/^'|'$/g, ""));
  }
  const conhecidas = new Set(dics.flatMap(([, d]) => (d ?? []).map(([k]) => k)));
  const ruins = literais.filter((l) => !conhecidas.has(l));
  if (!ruins.length) return true;
  if (dics.some(([, d]) => !d)) return undefined;
  return `'${col}' não tem o código ${ruins.map((r) => `'${r}'`).join(", ")} em ${tabelas.join(", ")}. ` +
    `Códigos válidos: ${dics.map(([t, d]) => `${t}: ${d!.map(([k, v]) => (k === v ? `'${k}'` : `'${k}'=${v}`)).join(", ")}`).join("; ")}.`;
}

/** SQL sem comentários: o modelo comenta em português ("junte com a tabela"), e
 *  `FROM`/`JOIN` dentro do comentário virava tabela inexistente ('com'). */
export function semComentarios(sql: string): string {
  let out = "";
  for (let i = 0; i < sql.length; i++) {
    const c = sql[i]!;
    if (c === "'" || c === '"') {
      const fim = sql.indexOf(c, i + 1);
      const j = fim < 0 ? sql.length : fim + 1;
      out += sql.slice(i, j);
      i = j - 1;
    } else if (c === "-" && sql[i + 1] === "-") {
      const fim = sql.indexOf("\n", i);
      i = (fim < 0 ? sql.length : fim) - 1;
    } else if (c === "/" && sql[i + 1] === "*") {
      const fim = sql.indexOf("*/", i + 2);
      i = (fim < 0 ? sql.length : fim + 2) - 1;
    } else out += c;
  }
  return out;
}

/**
 * Conserta sozinho as rejeições que são só forma, em vez de gastar um turno do
 * modelo (~15 s) para ele reescrever. Medido 2026-09-23: numa pergunta de 17
 * turnos, 3 foram LIMIT, `COUNT(*) AS n` e dataset sem tabela. Só o que tem uma
 * correção única e segura; o resto continua rejeitado com a mensagem de sempre.
 */
export const NOTA_AMOSTRA = "acrescentei COUNT(*) AS n ao SELECT final";

/**
 * B29, T15-3: `SELECT DISTINCT ano FROM br_ibge_pib.municipio LIMIT 5` devolveu
 * 5 anos quaisquer, e o modelo tomou 2016 pelo mais recente (a tabela vai a
 * 2021). O DISTINCT final só de colunas de tempo, sem ORDER BY, ganha
 * `ORDER BY <cols> DESC` — o topo passa a ser o mais recente.
 */
const COLUNA_TEMPO = /^(?:\w+\.)?(ano|mes|data|dia|semana|trimestre)(_\w+)?$/i;
function ordenaTempo(sql: string): { sql: string; chaves: string } | undefined {
  const m = /\bSELECT\s+DISTINCT\s+([\w.\s,]+?)\s+FROM\s+[\w.]+(?:\s+(?:AS\s+)?\w+)?(?:\s+WHERE\s+[^()]*?)?(\s+LIMIT\s+\d+)?$/i.exec(sql);
  // Depois de UNION o ORDER BY valeria para a união toda, não para este SELECT.
  if (!m || /\bUNION\b/i.test(sql)) return undefined;
  const cols = m[1]!.split(",").map((c) => c.trim());
  if (!cols.length || !cols.every((c) => COLUNA_TEMPO.test(c))) return undefined;
  const chaves = cols.map((c) => `${c} DESC`).join(", ");
  const corte = m[2] ? sql.length - m[2].length : sql.length;
  return { sql: `${sql.slice(0, corte)}\nORDER BY ${chaves}${m[2] ?? ""}`, chaves };
}

export function repara(sql: string, opcoes: { amostra?: boolean } = {}): { sql: string; notas: string[] } {
  const notas: string[] = [];
  let atual = sql.trim().replace(/;\s*$/, "");
  const tempo = ordenaTempo(atual);
  if (tempo) {
    atual = tempo.sql;
    notas.push(`acrescentei ORDER BY ${tempo.chaves} (sem ordem, os primeiros anos do DISTINCT não são os mais recentes)`);
  }
  for (let i = 0; i < 4; i++) {
    const v = portao(atual);
    if (v.ok) break;
    let novo: string | undefined;
    if (v.camada === "limite") {
      novo = `${atual}\nLIMIT 100`;
      notas.push("acrescentei LIMIT 100");
    } else if (v.camada === "amostra" && opcoes.amostra !== false) {
      // No FIM da lista de colunas: no começo deslocaria `GROUP BY 1`.
      const p = selectExterno(atual);
      const f = p === undefined ? undefined : fromExterno(atual, p);
      if (p !== undefined && f !== undefined && !/^\s*DISTINCT\b/i.test(atual.slice(p + 6)) && !temUniao(atual)) {
        novo = `${atual.slice(0, f).trimEnd()}, COUNT(*) AS n\n${atual.slice(f)}`;
        notas.push(NOTA_AMOSTRA);
      }
    } else if (v.camada === "tabela") {
      const nus = tabelasCitadas(atual).filter((r) => !r.includes(".") && !r.includes("("));
      const trocas = nus.map((ds) => [ds, tabelaPrincipal(ds.toLowerCase())] as const);
      if (nus.length && trocas.every(([, t]) => t)) {
        novo = atual;
        for (const [ds, t] of trocas) novo = novo.replace(new RegExp(`\\b${ds}\\b(?!\\.)`, "g"), t!);
        notas.push(`troquei ${trocas.map(([ds, t]) => `${ds} por ${t}`).join(", ")} (a tabela principal do dataset)`);
      }
    }
    if (!novo || novo === atual) break;
    atual = novo;
  }
  return { sql: atual, notas };
}

/** Posição do SELECT da consulta externa (fora de parênteses e literais). */
function selectExterno(sql: string): number | undefined {
  let nivel = 0, ultimo: number | undefined;
  for (let i = 0; i < sql.length; i++) {
    const c = sql[i]!;
    if (c === "'" || c === '"') { const f = sql.indexOf(c, i + 1); i = f < 0 ? sql.length : f; continue; }
    if (c === "(") nivel++;
    else if (c === ")") nivel--;
    else if (nivel === 0 && /^SELECT\b/i.test(sql.slice(i, i + 7)) && !/\w/.test(sql[i - 1] ?? " ")) ultimo = i;
  }
  return ultimo;
}

/** Posição do FROM da consulta externa, depois do SELECT externo. */
function fromExterno(sql: string, inicio: number): number | undefined {
  let nivel = 0;
  for (let i = inicio; i < sql.length; i++) {
    const c = sql[i]!;
    if (c === "'" || c === '"') { const f = sql.indexOf(c, i + 1); i = f < 0 ? sql.length : f; continue; }
    if (c === "(") nivel++;
    else if (c === ")") nivel--;
    else if (nivel === 0 && /^FROM\b/i.test(sql.slice(i, i + 5)) && /\s/.test(sql[i - 1] ?? " ")) return i;
  }
  return undefined;
}

/** UNION no nível de fora. Tira os parênteses de dentro para fora até não
 *  sobrar nenhum: uma passada só deixava o UNION de uma subconsulta dentro de
 *  CTE à mostra (B24, T03-1 da B19), e o COUNT(*) AS n não era acrescentado. */
const temUniao = (sql: string) => {
  let s = sql, antes;
  do { antes = s; s = s.replace(/\([^()]*\)/g, " "); } while (s !== antes);
  return /\b(UNION|INTERSECT|EXCEPT)\b/i.test(s);
};

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
 *  Junção sem ponte — harness_tasks.md B12.
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
/**
 * Apelido de subconsulta ou nome de CTE → a tabela real de dentro, quando ela é
 * uma só. Medido 2026-09-24, caso 4 da rodada B2: `JOIN (SELECT
 * codigo_municipio_siafi … FROM br_cgu_novo_bolsa_familia…) bcf ON
 * s.id_municipio_nascimento = bcf.codigo_municipio_siafi` voltou zero linhas
 * três vezes, e a mensagem de sem-ponte nunca disparou — no escopo de fora a
 * subconsulta vira espaço e `bcf` não tinha tabela por trás.
 */
function tabelasDerivadas(sql: string, ctes: Set<string>): Map<string, string> {
  const out = new Map<string, string>();
  const dentro = (corpo: string) => {
    const refs = new Set(refsDoEscopo(recorta(corpo, []), ctes).map((r) => r.ref));
    return refs.size === 1 ? [...refs][0]! : undefined;
  };
  for (let i = sql.indexOf("("); i >= 0; i = sql.indexOf("(", i + 1)) {
    const fim = fechaParen(sql, i);
    const corpo = sql.slice(i + 1, fim);
    if (!/^\s*SELECT\b/i.test(corpo)) continue;
    const antes = /\b([A-Za-z_]\w*)\s+AS\s*$/i.exec(sql.slice(0, i));
    const depois = /^\s*(?:AS\s+)?([A-Za-z_]\w*)/i.exec(sql.slice(fim + 1));
    const nome = antes && ctes.has(antes[1]!.toLowerCase()) ? antes[1]! : depois?.[1];
    const ref = dentro(corpo);
    if (nome && ref && !NAO_APELIDO.has(nome.toLowerCase())) out.set(nome.toLowerCase(), ref);
  }
  return out;
}

export function juncoesSemPonte(sql: string): JuncaoSemPonte[] {
  const ctes = ctesDefinidos(sql);
  const derivadas = tabelasDerivadas(sql, ctes);
  const acha = (refs: RefEscopo[], a: string): string | undefined =>
    refs.find((r) => r.apelidos.has(a.toLowerCase()))?.ref ?? derivadas.get(a.toLowerCase());
  const achados: JuncaoSemPonte[] = [];
  for (const seg of segmentos(sql)) {
    const refs = refsDoEscopo(seg, ctes);
    for (const m of seg.matchAll(
      /\bJOIN\s+[A-Za-z_][\w.]*(?:\s+(?:AS\s+)?[A-Za-z_]\w*)?\s+ON\s+([\s\S]*?)(?=\bJOIN\b|\bWHERE\b|\bGROUP\b|\bORDER\b|\bLIMIT\b|\bQUALIFY\b|$)/gi,
    )) {
      for (const [a1, c1, a2, c2] of paresIgualdade(m[1]!)) {
        const r1 = acha(refs, a1);
        const r2 = acha(refs, a2);
        if (!r1 || !r2 || r1 === r2) continue;
        if (r1.split(".")[0] === r2.split(".")[0]) continue; // mesmo dataset, sem risco
        const k1 = conceitoDaColuna(r1, c1);
        const k2 = conceitoDaColuna(r2, c2);
        if (k1 && k1 === k2) continue; // ponte confirmada, curada ou canônica
        achados.push({ refA: r1, colA: c1, refB: r2, colB: c2 });
      }
    }
  }
  return achados;
}

/**
 * A MESMA SQL mandada de novo depois de rejeitada. B24, medido na B19: T03-1
 * reenviou a consulta idêntica 10 vezes e T16-4 8 vezes, cada vez um turno de
 * ~90 s, até o teto de 1.500 s — `jaRodadas` só vê SQL que rodou, e o
 * orçamento de 30 consultas não chega antes do teto a esse ritmo. Da 2ª vez
 * em diante a rejeição diz que é repetição e manda mudar a consulta ou parar.
 */
export function avisoRejeicaoRepetida(vezes: number): string | undefined {
  if (vezes < 2) return undefined;
  return `⚠ Esta é a ${vezes}ª vez que ESTA MESMA consulta é mandada e rejeitada pelo mesmo motivo. ` +
    `Reenviar sem mudar nada devolve a mesma rejeição. Mude a parte que a mensagem acima aponta, ` +
    `ou reescreva a consulta de outro jeito (outra tabela, CTE mais simples); se não houver como, ` +
    `pare e responda com o que já apurou, dizendo o que não deu para calcular.`;
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

/**
 * Pergunta de pesquisa — relação entre variáveis em muitos municípios, não um
 * número só. As diretas começam por interrogativo ("Qual", "Quantos", "Em que");
 * as de pesquisa afirmam uma relação e perguntam se ela vale ("Municípios com
 * mais X têm Y?"). Medido 2026-09-24: 87/87 dos casos de pesquisa e 0/42 das
 * diretas (os três `dados/diretas*.tsv`). O único que começa por "Quais" cai
 * pelo verbo de relação.
 */
export function perguntaDePesquisa(pergunta: string): boolean {
  const q = pergunta.trim();
  if (!q) return false;
  if (/\b(correlaciona\w*|correla[çc][ãa]o|associa\w*|explica|prev[êe])\b/i.test(q)) return true;
  return /\?\s*$/.test(q) && !/^(qual|quais|quant[oa]s?|em (que|qual|quant[oa]s?)|quem|como|por que)\b/i.test(q);
}

/**
 * Ranking cruzando fontes, numa pergunta de pesquisa — rejeitado.
 *
 * Medido 2026-09-24, os 8 primeiros casos da rodada B2, todos errados: a
 * pergunta era "municípios com mais X têm mais Y?" e 7 das 8 sessões fecharam
 * num `ORDER BY … LIMIT 10` com quatro fontes juntadas, sem `corr()` nem
 * `COUNT(*) AS n`. A resposta vira uma lista de exemplos (Tufilândia, Extrema,
 * Abadia de Goiás) e uma conclusão hesitante — nenhuma medida sobre os
 * municípios todos, e nenhum `n` para conferir o join.
 *
 * Só quando a SQL junta **duas ou mais fontes** (os diretórios não contam): a
 * exploração de uma tabela só com `LIMIT` — ver valores, conferir código —
 * segue livre. E só no SELECT externo, sem estatística derivada nem `n`: uma
 * comparação de faixas com `COUNT(*) AS n` e `ORDER BY` passa.
 *
 * Fica fora de `portao()` porque depende da pergunta, que só `mcp.ts` conhece.
 */
/**
 * Faixas por quartil, inteiras e copiáveis. B15, medido 2026-09-25: a versão
 * em prosa desta instrução ("ntile numa CTE, e no SELECT final GROUP BY
 * faixa") precedeu 4 dos 8 `GROUP BY clause cannot contain window functions!`
 * da rodada B2 — o modelo punha o `ntile` direto no GROUP BY.
 */
export const MOLDE_FAIXAS =
  "o ntile numa CTE e o GROUP BY fora dela, assim: " +
  "WITH base AS (SELECT id_municipio, x, y, ntile(4) OVER (ORDER BY x) AS faixa FROM ...) " +
  "SELECT faixa, AVG(y) AS media_y, COUNT(*) AS n FROM base GROUP BY faixa ORDER BY faixa.";

/**
 * Janela ou agregado dentro do GROUP BY — o DuckDB rejeita, e o erro dele só
 * diz que não pode. Medido 2026-09-25, 75 sessões da rodada B2: 10x janela e
 * 6x agregado no GROUP BY, cada um um turno inteiro do modelo. Aqui a
 * rejeição chega antes do EXPLAIN e com o molde que funciona.
 */
function checaGroupBy(sql: string): Veredito {
  for (const seg of segmentos(sql)) {
    // Um segmento pode ter vários ramos de UNION, cada um com o seu GROUP BY.
    // B24 (T03-1 da B19): sem parar no UNION, o GROUP BY do 1º ramo engolia o
    // `SELECT id, COUNT(*)` do 2º e a SQL válida era rejeitada 12 vezes.
    for (const m of seg.matchAll(/\bGROUP\s+BY\b([\s\S]*?)(?=\bHAVING\b|\bORDER\s+BY\b|\bLIMIT\b|\bQUALIFY\b|\bWINDOW\b|\bUNION\b|\bINTERSECT\b|\bEXCEPT\b|$)/gi)) {
    const g = m[1]!;
    if (/\bOVER\b/i.test(g) || /\b(ntile|row_number|rank|dense_rank|percent_rank|cume_dist|lag|lead)\s*\(/i.test(g)) {
      return { ok: false, camada: "group-by",
        erro: `Função de janela dentro do GROUP BY — o DuckDB não aceita. Calcule a faixa antes e agrupe depois: ${MOLDE_FAIXAS}` };
    }
    if (/\b(SUM|COUNT|AVG|MIN|MAX|MEDIAN|CORR|STDDEV\w*)\s*\(/i.test(g)) {
      return { ok: false, camada: "group-by",
        erro: "Agregado dentro do GROUP BY — o DuckDB não aceita. Agrupe pelas colunas de grupo (ou pela faixa) e " +
          `deixe SUM/COUNT/AVG só no SELECT. Para faixas de um valor agregado, agregue numa CTE primeiro: ${MOLDE_FAIXAS}` };
    }
    }
  }
  return OK;
}

export function checaRanking(sql: string): Veredito {
  const externo = segmentos(sql).at(-1) ?? sql;
  if (!/\bORDER\s+BY\b[\s\S]*\bLIMIT\s+\d+/i.test(externo)) return OK;
  if (DERIVADAS.test(externo) || /\bAS\s+"?n"?\b/i.test(externo)) return OK;
  // B25: ordenar primeiro por tempo é olhar a série, não ranking (T06-2, T22-2
  // da B19: `ORDER BY i.ano, ... LIMIT 5`); e no grão de UF as 27 cabem na tela,
  // e "quais UFs" é a própria pergunta (T15-5: 3 rejeições seguidas).
  const chave = /\bORDER\s+BY\s+(?:\w+\.)?(\w+)/i.exec(externo.slice(externo.search(/\bORDER\s+BY\b[^()]*$/i)))?.[1];
  if (chave && /^(ano|mes|data|dia|semana|trimestre)(_\w+)?$/i.test(chave)) return OK;
  if (/\b(sigla_uf|uf)\b/i.test(externo) && !/\bid_municipio\w*\b/i.test(externo)) return OK;
  const fontes = new Set(
    tabelasCitadas(sql)
      .filter((r) => r.includes(".") && !/^br_bd_diretorios/i.test(r))
      .map((r) => r.split(".")[0]!.toLowerCase()),
  );
  if (fontes.size < 2) return OK;
  return {
    ok: false,
    camada: "ranking",
    erro:
      `A pergunta é sobre uma relação entre variáveis nos municípios, e esta consulta ` +
      `junta ${fontes.size} fontes (${[...fontes].join(", ")}) para devolver só os ` +
      `primeiros de um ORDER BY … LIMIT. Uma lista dos 10 maiores é exemplo, não ` +
      `resposta: não diz se a relação vale para os municípios todos. Meça sobre TODOS ` +
      `os municípios com dado, sem LIMIT no SELECT final, e com o tamanho da amostra: ` +
      `SELECT corr(x, y) AS r, COUNT(*) AS n FROM ... ; ou compare faixas com ` +
      MOLDE_FAIXAS + ` Exemplos com nome podem vir depois, numa consulta à parte.`,
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

/**
 * Fonte que a pergunta nomeia → prefixo dos datasets dela. Medido 2026-09-25,
 * holdout3: "saldo do CAGED em 2019" (o CAGED do espelho começa em 2020) foi
 * respondido duas vezes com a RAIS — a segunda depois de uma nota dizendo "não
 * troque pela RAIS", com o modelo afirmando que a nota mandava. Regra escrita
 * não segurou; o aviso vai junto do resultado que ele está prestes a usar.
 */
const FONTES: [RegExp, string, string][] = [
  [/\bCAGED\b/i, "br_me_caged", "CAGED"], [/\bRAIS\b/i, "br_me_rais", "RAIS"],
  [/\bSINASC\b/i, "br_ms_sinasc", "SINASC"], [/\bSIM\b/, "br_ms_sim", "SIM"],
  [/\bCNES\b/i, "br_ms_cnes", "CNES"], [/\bSIH\b/, "br_ms_sih", "SIH"],
  [/\bSINAN\b/i, "br_ms_sinan", "SINAN"], [/\bENEM\b/i, "br_inep_enem", "ENEM"],
  [/\bIDEB\b/i, "br_inep_ideb", "IDEB"], [/\bPNAD\b/i, "br_ibge_pnad", "PNAD"],
  [/\bPRODES\b/i, "br_inpe_prodes", "PRODES"], [/\bANP\b/, "br_anp_", "ANP"],
];

/**
 * A fonte nomeada na pergunta que a consulta não tocou — para pergunta direta.
 * Só com agregado (consulta com cara de resposta); exploração e DISTINCT passam.
 */
export function fonteTrocada(pergunta: string, sql: string): string | undefined {
  if (!/\b(COUNT|SUM|AVG)\s*\(/i.test(sql)) return undefined;
  const usadas = tabelasCitadas(sql).map((t) => t.toLowerCase());
  for (const [re, prefixo, nome] of FONTES) {
    if (!re.test(pergunta) || usadas.some((t) => t.startsWith(prefixo))) continue;
    const outras = [...new Set(usadas.filter((t) => t.includes(".") && !t.startsWith("br_bd_diretorios")).map((t) => t.split(".")[0]))];
    if (!outras.length) continue;
    return `A pergunta pede o ${nome}, e esta consulta não usa ${prefixo}* — usa ${outras.join(", ")}. ` +
      `Se o ${nome} não tem o dado pedido (ano ou recorte fora da cobertura), a resposta certa é dizer isso; ` +
      `um número de outra fonte, mesmo parecido, responde outra pergunta. Se usar outra fonte, diga qual e ` +
      `que ela NÃO é o ${nome}.`;
  }
  return undefined;
}

/** Código IBGE da UF → sigla. */
export const UF_IBGE: Record<string, string> = {
  "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
  "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL", "28": "SE", "29": "BA",
  "31": "MG", "32": "ES", "33": "RJ", "35": "SP", "41": "PR", "42": "SC", "43": "RS",
  "50": "MS", "51": "MT", "52": "GO", "53": "DF",
};

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

/** Coluna de coeficiente pelo nome: `r`, `rho`, `corr_*`, `correlacao*`, `r_*`. */
export const COLUNA_COEFICIENTE = /^(r|rho|corr\w*|correla\w*|r_\w+)$/i;

/**
 * B22, medido na B19 (2026-09-26): dos 35 casos com `r` publicado que não
 * citaram coeficiente nenhum, **12 tinham rodado `corr()` com sucesso — e ele
 * voltou NULL** (37 de 38 resultados de `corr()` nesses casos). Omissão de um
 * `r` de verdade quase não existe: quando o coeficiente veio numérico, 27 de
 * 28 respostas o citaram. Em 14 desses NULL o `n` era grande (3.602, 5.570):
 * `COUNT(*)` conta linhas, não pares — um LEFT JOIN que não casou deixa uma
 * das pontas toda NULL, e `corr()` ignora o par. O lembrete ainda pedia
 * "escreva o coeficiente (r=null) e o n (aqui, n=3602)".
 *
 * Devolve o alerta quando algum coeficiente da 1ª linha é NULL/NaN, ou
 * degenerado (|r| ≥ 0,99999 — exato, não "alto": população × eleitorado dá 0,998 de verdade; uma ponta é função da outra, ou só 2 pontos).
 */
export function coeficienteVazio(linhas: Linha[]): string | undefined {
  const prim = linhas[0];
  if (!prim) return undefined;
  const coef = Object.keys(prim).filter((k) => COLUNA_COEFICIENTE.test(k));
  if (!coef.length) return undefined;
  const nulos = coef.filter((k) => prim[k] === null || prim[k] === undefined || prim[k] === "" || !Number.isFinite(Number(prim[k])));
  const degenerados = coef.filter((k) => !nulos.includes(k) && Math.abs(Number(prim[k])) >= 0.99999);
  if (!nulos.length && !degenerados.length) return undefined;
  const n = extraiN(linhas);
  const partes: string[] = [];
  if (nulos.length) {
    partes.push(`${nulos.join(", ")} voltou NULL${n ? ` embora n=${n}` : ""}: nenhum município teve as duas pontas preenchidas (ou uma delas é constante). ` +
      `COUNT(*) conta linhas, não pares — conte os pares com regr_count(y, x) e cada ponta com COUNT(x), COUNT(y) para achar a vazia. ` +
      `A causa comum é um LEFT JOIN que não casou (código de município em outro formato ou com outro nome de coluna, ano sem dado numa das tabelas).`);
  }
  if (degenerados.length) {
    partes.push(`${degenerados.join(", ")} deu ±1: uma ponta é função da outra (mesma coluna dos dois lados, razão sobre o mesmo denominador) ou sobraram 2 pontos.`);
  }
  return `${partes.join(" ")} Não escreva esse coeficiente na resposta: conserte a consulta, ou diga que a medida não foi possível e por quê.`;
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
export function alertasDeSanidade(sql: string, linhas: Linha[], pergunta = ""): string[] {
  const alertas: string[] = [];

  // harness_tasks.md B9, medido em 2026-09-03 ao vivo (não procurado — apareceu
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

  // Medido 2026-09-22 (duas vezes, mesmo com a regra no prompt): "IDEB do Brasil"
  // respondido como AVG(ideb) das escolas — 4,15 contra o 3,9 oficial. Média de
  // índices de unidades menores não é o índice do agregado, e o dataset já traz
  // a tabela no nível pedido.
  const fan = fanOut(sql);
  if (fan) alertas.push(fan);

  const agregadas = tabelasAgregadas(sql);
  if (agregadas.length && /\bAVG\s*\(/i.test(sql)) {
    alertas.push(
      `Média (AVG) sobre tabela de unidade menor, e o dataset tem tabela já agregada: ${agregadas.join(", ")}. ` +
      `Se a pergunta é sobre o Brasil, um estado ou uma região, leia o valor pronto dessa tabela — ` +
      `a média dos índices de escolas, municípios ou estados NÃO é o índice do agregado.`);
  }

  // Medido 2026-09-25, holdout3: "MG ou BA?" filtrado com id_uf_mae IN ('41',
  // '26') — Paraná e Pernambuco. A consulta roda, devolve dois números
  // plausíveis, e o modelo respondeu 148.581 para MG (são 247.192). O código
  // IBGE da UF não é adivinhável; dizer quais estados foram filtrados basta.
  const ufs = new Set<string>();
  for (const m of sql.matchAll(/\bid_uf\w*\s*(?:=\s*'?(\d{2})'?|IN\s*\(([^)]*)\))/gi)) {
    const lista = m[1] ? [m[1]] : (m[2] ?? "").match(/\d{2}/g) ?? [];
    for (const c of lista) if (UF_IBGE[c]) ufs.add(c);
  }
  if (ufs.size) {
    alertas.push(`Os códigos de UF filtrados são ${[...ufs].map((c) => `${c} = ${UF_IBGE[c]}`).join(", ")}. ` +
      `Confira se são os estados da pergunta — o código IBGE não segue a ordem alfabética (MG = 31, BA = 29, SP = 35, RJ = 33).`);
  }

  const prim = linhas[0];
  if (!prim) return alertas;

  // Medido 2026-09-24, caso 6 da rodada B2: taxa de mortalidade infantil 0,0 em
  // todos os grupos, e o modelo explicou o zero como achado. A causa era
  // `tipo_obito_ocorrencia != '8'` — NULL em 1.494.553 dos 1.556.824 óbitos do
  // SIM 2020, e `NULL != '8'` não é verdadeiro: o filtro jogou fora os 28.864
  // óbitos infantis. Só avisa quando as duas coisas aparecem juntas.
  const diferentes = [...sql.matchAll(/\b([A-Za-z_]\w*)\s*(?:!=|<>)\s*'[^']*'/g)].map((m) => m[1]!);
  const zeradas = colunasNumericas(linhas).filter((k) => k.toLowerCase() !== "n" &&
    linhas.every((l) => Number(l[k]) === 0));
  if (diferentes.length && zeradas.length) {
    const cols = [...new Set(diferentes)];
    alertas.push(
      `${zeradas.join(", ")} deu 0 em todas as linhas, e a consulta filtra com != / <> ` +
      `(${cols.join(", ")}). Em SQL, NULL != 'x' não é verdadeiro: a linha com a coluna ` +
      `vazia sai do resultado junto com a que vale 'x'. Medido aqui: ` +
      `tipo_obito_ocorrencia != '8' descartou os 28.864 óbitos infantis do SIM 2020, ` +
      `porque a coluna é NULL em 96% das linhas. Use (${cols[0]} IS NULL OR ${cols[0]} != '...'), ` +
      `ou tire o filtro — um zero assim é o filtro, não um achado.`,
    );
  }

  // Medido em 2026-09-01: o pipeline fixo respondeu 573 onde o total era 789 —
  // agrupou por sexo e reportou UM grupo como se fosse o total. É o erro que o
  // laço agêntico não pode repetir na prosa, e ele não custa nada de avisar.
  // Ranking explícito (ORDER BY ... LIMIT) já declara que quer grupos: o aviso
  // ali só gastava tokens — disparou 9x numa pergunta de "qual município".
  if (linhas.length > 1 && /\bGROUP\s+BY\b/i.test(sql) && !/\bORDER\s+BY\b[\s\S]*\bLIMIT\s+\d+/i.test(sql)) {
    // B36: ano/mês e códigos não são quantidade — "Somando a coluna 'ano' … 10049".
    const num = colunasNumericas(linhas).filter((k) => !naoSomavel(k));
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
  // Só para o total de uma linha (a junção que duplicou). Com várias linhas, o n
  // de cada grupo é o que a camada 8 obriga a contar — 8.784 leituras horárias
  // por estação disparavam o alerta à toa (2026-09-23, duas vezes seguidas).
  if (n !== undefined && n > MUNICIPIOS_BR && linhas.length === 1 && /municipio/i.test(sql)) {
    alertas.push(
      `n=${n} passa dos ${MUNICIPIOS_BR.toLocaleString("pt-BR")} municípios do país. ` +
      `Se cada linha deveria ser um município, o join duplicou linhas — uma das pontas ` +
      `tem mais de uma linha por município (por ano, por sexo, por CNAE). Confira com ` +
      `COUNT(DISTINCT id_municipio) e agregue a ponta duplicada antes do join. ` +
      `Se o grão é município × ano de propósito, está certo: diga o grão na resposta.`,
    );
  }

  const extensivas = correlacaoExtensiva(sql);
  if (extensivas.length) alertas.push(mensagemExtensiva(extensivas));
  const totais = totaisSobPedidoDeTaxa(sql, pergunta);
  if (totais.length) alertas.push(mensagemTotais(totais));
  const parteTodo = correlacaoParteTodo(sql);
  if (parteTodo.length) alertas.push(mensagemParteTodo(parteTodo));

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

/** Argumentos de nível zero de uma chamada, a partir do índice logo depois do `(`. */
function argumentosDe(sql: string, inicio: number): string[] {
  const args: string[] = [];
  let prof = 0, atual = "";
  for (let i = inicio; i < sql.length; i++) {
    const ch = sql[i]!;
    if (ch === "(") prof++;
    else if (ch === ")") { if (prof === 0) { args.push(atual.trim()); return args; } prof--; }
    else if (ch === "," && prof === 0) { args.push(atual.trim()); atual = ""; continue; }
    atual += ch;
  }
  return args;
}

/** A expressão de um item de SELECT que projeta `alias` (`<expr> AS alias`), ou undefined. */
function definicaoDe(sql: string, alias: string): string | undefined {
  const re = new RegExp(`\\bAS\\s+${alias}\\b`, "gi");
  let m: RegExpExecArray | null;
  while ((m = re.exec(sql))) {
    // Anda para trás até a vírgula ou o SELECT de nível zero que abre o item.
    let prof = 0, i = m.index - 1;
    for (; i >= 0; i--) {
      const ch = sql[i]!;
      if (ch === ")") prof++;
      else if (ch === "(") { if (prof === 0) break; prof--; }
      else if (ch === "," && prof === 0) break;
      else if (prof === 0 && /\bSELECT\s*$/i.test(sql.slice(Math.max(0, i - 6), i + 1))) break;
    }
    const expr = sql.slice(i + 1, m.index).replace(/^\s*(DISTINCT\s+)?/i, "").trim();
    // `FROM br_inep_ideb.municipio AS ideb` é apelido de tabela, não de coluna:
    // o recuo atravessaria o FROM e leria o item anterior (T81-3, falso positivo).
    if (expr && !/\b(FROM|JOIN)\b/i.test(expr)) return expr;
  }
  return undefined;
}

/** A expressão é uma contagem/soma crua: COUNT/SUM sem nenhuma divisão. */
function ehExtensiva(sql: string, expr: string, visto = new Set<string>()): boolean {
  if (expr.includes("/")) return false;
  if (/^\s*(COUNT|SUM)\s*\(/i.test(expr)) return true;
  // Um nível de embrulho: `COALESCE(total, 0)`, `b.total`, `total` → segue o alias.
  const m = /^\s*(?:COALESCE\s*\(\s*)?(?:\w+\.)?(\w+)\s*(?:,\s*0\s*\))?\s*$/i.exec(expr);
  if (!m || visto.has(m[1]!.toLowerCase())) return false;
  visto.add(m[1]!.toLowerCase());
  const def = definicaoDe(sql, m[1]!);
  return def !== undefined && ehExtensiva(sql, def, visto);
}

/**
 * harness_tasks.md B23, rodada B19 (2026-09-26). Três dos cinco casos de sinal
 * trocado correlacionaram uma contagem ou soma crua por município — beneficiários,
 * sobrenomes repetidos, emendas em R$ — contra outra variável. Contagem crua mede
 * o porte do município antes de medir o fenômeno. T29-3, remedido no beelink: a
 * SQL do modelo dá r=+0,22 (n=1.808); a mesma SQL com emenda per capita e margem
 * em % dá +0,013, o publicado é +0,018. O alerta cita a coluna e manda normalizar;
 * não rejeita, porque correlacionar totais pode ser a pergunta.
 */
export function correlacaoExtensiva(sql: string): string[] {
  const limpo = semComentarios(sql);
  const achadas = new Set<string>();
  const re = /\bcorr\s*\(/gi;
  let m: RegExpExecArray | null;
  while ((m = re.exec(limpo))) {
    // Só o par misto (um total contra uma taxa). Total contra total é às vezes a
    // pergunta — focos × km² desmatados (T22-1), emendas × despesa (T21-4) — e o
    // publicado mediu assim; o alerta ali mandaria o modelo para longe dele.
    const args = argumentosDe(limpo, m.index + m[0].length);
    const ext = args.filter((a) => ehExtensiva(limpo, a));
    if (args.length === 2 && ext.length === 1) achadas.add(ext[0]!.replace(/\s+/g, " "));
  }
  return [...achadas];
}

/**
 * `corr(x / y, x)`: uma ponta é razão que contém a outra (numerador ou
 * denominador), e o r sai da aritmética, não do dado. T35-4, rerun de
 * 2026-09-27: corr(renda_media / tempo, renda_media) deu 0,68 e a resposta
 * leu como "tempo × renda" — o publicado é −0,40.
 */
export function correlacaoParteTodo(sql: string): string[][] {
  const limpo = semComentarios(sql);
  const pares: string[][] = [];
  const re = /\bcorr\s*\(/gi;
  let m: RegExpExecArray | null;
  const nome = (s: string) => /^\s*(?:\w+\.)?(\w+)\s*$/.exec(s)?.[1]?.toLowerCase();
  while ((m = re.exec(limpo))) {
    const args = argumentosDe(limpo, m.index + m[0].length);
    if (args.length !== 2) continue;
    for (const [a, b] of [[args[0]!, args[1]!], [args[1]!, args[0]!]]) {
      const alvo = nome(b);
      if (!alvo || !a.includes("/")) continue;
      const termos = a.toLowerCase().split(/[^\w.]+/).map((t) => t.split(".").pop());
      if (termos.includes(alvo)) { pares.push([a.replace(/\s+/g, " "), b.trim()]); break; }
    }
  }
  return pares;
}

/**
 * A pergunta pede taxa, proporção ou controle por população — e a SQL
 * correlaciona dois totais crus. Total contra total fica calado quando a
 * pergunta é sobre volume (B23: focos × km² desmatados em T22-1, emendas ×
 * receita em T21-4 foram publicados assim). Medido nas sessões de 2026-09-25 a
 * 27: dos casos com corr() de dois totais, a pista na pergunta separa os dois
 * grupos sem erro — dispara em T08-1, T28-5, T03-1, T22-2, T59-4 (publicado
 * normalizado; o modelo deu 0,85 e 0,92 onde o publicado é −0,08 e per capita)
 * e fica calado em T22-1, T21-4, T06-2, T59-1, T07-1 (publicado em totais).
 */
export const PEDE_TAXA = /controlad|per capita|proporç|proporcion|\btaxa|por habitante|razão|relativ/i;
export function totaisSobPedidoDeTaxa(sql: string, pergunta: string): string[][] {
  // "PIB per capita" nomeia uma variável que já é taxa, não pede normalizar as
  // outras (T05-1: patrimônio × proposições, no grão do deputado).
  const pista = pergunta.replace(/pib\s+per\s+capita/gi, "");
  return PEDE_TAXA.test(pista) ? correlacaoDeTotais(sql) : [];
}

export function mensagemTotais(pares: string[][]): string {
  return (
    `corr() entre dois totais crus (${pares.map((p) => p.join(" × ")).join("; ")}), e a pergunta pede ` +
    `taxa, proporção ou controle por população. Dois totais por município crescem juntos com o porte: ` +
    `o r sai alto e positivo e mede o tamanho do município, não o fenômeno (medido aqui: beneficiários × ` +
    `gasto social deu 0,85; o publicado, per capita, é −0,08). Divida cada lado pela população ` +
    `(ou pela base que a pergunta nomeia) e correlacione as taxas.`
  );
}

export function mensagemParteTodo(pares: string[][]): string {
  return (
    `corr() de uma razão com um dos próprios termos (${pares.map((p) => p.join(" × ")).join("; ")}): ` +
    `o r sai da aritmética — x/y cresce com x por construção —, não do dado. Para a relação entre as ` +
    `duas variáveis, correlacione uma com a outra (ex.: corr(tempo, renda)).`
  );
}

/** Algum alerta de escala (total cru, dois totais sob pedido de taxa, razão com o próprio termo)? */
export function alertaDeEscala(sql: string, pergunta = ""): boolean {
  return correlacaoExtensiva(sql).length > 0 || totaisSobPedidoDeTaxa(sql, pergunta).length > 0 ||
    correlacaoParteTodo(sql).length > 0;
}

/** Os pares de `corr()` em que as DUAS pontas são contagem/soma crua. */
export function correlacaoDeTotais(sql: string): string[][] {
  const limpo = semComentarios(sql);
  const pares: string[][] = [];
  const re = /\bcorr\s*\(/gi;
  let m: RegExpExecArray | null;
  while ((m = re.exec(limpo))) {
    const args = argumentosDe(limpo, m.index + m[0].length);
    if (args.length === 2 && args.every((a) => ehExtensiva(limpo, a))) pares.push(args.map((a) => a.replace(/\s+/g, " ")));
  }
  return pares;
}

export function mensagemExtensiva(args: string[]): string {
  return (
    `corr() sobre contagem ou soma crua (${args.join(", ")}): um total por município ` +
    `cresce com a população, e o r mede o porte antes do fenômeno. Medido aqui: margem ` +
    `de votos × emendas em R$ deu r=+0,22; com margem em % e emenda per capita, +0,01. ` +
    `Divida pela população (ou pelo total do mesmo município) antes de correlacionar, ` +
    `a menos que a pergunta seja mesmo sobre totais.`
  );
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

  // Aposentada antes de inexistente: a mensagem diz para onde o dado foi.
  for (const camada of [checaInservivel, checaTabelas, checaColunas, checaCodigoTse, checaParticao, checaLimite, checaCodificacao, checaAno, checaValores, checaGroupBy, checaAmostra]) {
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
