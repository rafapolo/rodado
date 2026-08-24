/**
 * Embedding da pergunta e seleção de tabelas — tudo no navegador.
 *
 * O modelo TEM que ser o mesmo que gerou docs/context/table_embeddings.json.
 * A TUI Rust embedava com all-MiniLM-L6-v2 contra um índice multilingual: as
 * duas têm 384 dims, o cosseno roda, e o ranking é ruído. build_ask_web_assets
 * aborta se o índice mudar de modelo; aqui o nome fica travado junto.
 */
export const MODELO = "Xenova/paraphrase-multilingual-MiniLM-L12-v2";

let pipe = null, vetores = null, meta = null, dims = 384;
// índice doc2query: um vetor por PERGUNTA sintética, não por tabela
let pVetores = null, pEntradas = null;

export async function carregar(onProgresso) {
  const { pipeline, env } = await import("./vendor/transformers.js");
  env.allowLocalModels = false;

  const [_, metaJson, bin] = await Promise.all([
    pipeline("feature-extraction", MODELO, {
      dtype: "q8",
      progress_callback: (p) => {
        if (p.status === "progress" && p.total) {
          onProgresso?.({ arquivo: p.file, pct: Math.round((p.loaded / p.total) * 100) });
        }
      },
    }).then((p) => (pipe = p)),
    fetch("/index/meta.json").then((r) => r.json()),
    fetch("/index/vectors.bin").then((r) => r.arrayBuffer()),
  ]);

  meta = metaJson.tabelas;

  // O índice doc2query é opcional: se ainda não foi gerado, a busca segue só
  // com o índice por tabela. Falhar aqui deixaria o app inutilizável por causa
  // de um arquivo que é melhoria, não requisito.
  try {
    const [pj, pb] = await Promise.all([
      fetch("/index/perguntas.json").then((r) => (r.ok ? r.json() : null)),
      fetch("/index/perguntas_vetores.bin").then((r) => (r.ok ? r.arrayBuffer() : null)),
    ]);
    if (pj && pb && pj.entradas.length * 384 * 4 === pb.byteLength) {
      pEntradas = pj.entradas;
      pVetores = new Float32Array(pb);
      for (let i = 0; i < pEntradas.length; i++) {
        let n = 0;
        for (let j = 0; j < 384; j++) n += pVetores[i * 384 + j] ** 2;
        n = Math.sqrt(n) || 1;
        for (let j = 0; j < 384; j++) pVetores[i * 384 + j] /= n;
      }
    }
  } catch { /* segue sem doc2query */ }
  dims = metaJson.dims;
  vetores = new Float32Array(bin);

  // Normaliza uma vez: com todos os vetores unitários, o cosseno vira produto
  // escalar, e a busca nas 824 tabelas fica em ~1 ms.
  for (let i = 0; i < meta.length; i++) {
    let n = 0;
    for (let j = 0; j < dims; j++) n += vetores[i * dims + j] ** 2;
    n = Math.sqrt(n) || 1;
    for (let j = 0; j < dims; j++) vetores[i * dims + j] /= n;
  }
  return meta.length;
}

export const pronto = () => pipe !== null;
export const tabelas = () => meta;
export const temDoc2Query = () => pEntradas !== null;

/**
 * Score por tabela vindo do índice doc2query, com agregação por MÁXIMO.
 *
 * Máximo, nunca média: uma tabela responde a muitas perguntas diferentes, e a
 * que casa com ESTA consulta é a que importa. Tirar média faria acrescentar
 * pergunta piorar o score — foi a diluição que derrubou a tentativa anterior de
 * indexar prosa junto com nomes de coluna.
 */
function scoresDoc2Query(q) {
  const out = new Map();
  if (!pEntradas) return out;
  for (let i = 0; i < pEntradas.length; i++) {
    let dot = 0;
    for (let j = 0; j < 384; j++) dot += q[j] * pVetores[i * 384 + j];
    const id = pEntradas[i].id;
    const atual = out.get(id);
    if (atual === undefined || atual.s < dot) out.set(id, { s: dot, via: pEntradas[i].q });
  }
  return out;
}

async function vetorDaPergunta(texto) {
  const saida = await pipe(texto, { pooling: "mean", normalize: true });
  return saida.data;
}

/**
 * Top-K híbrido: lexical + embedding.
 *
 * Medido isolado nas 15 douradas: lexical 5/15, embedding 1/15. Eles erram por
 * motivos diferentes — o lexical não conhece sinônimo sem raiz comum ("quanta
 * gente mora" → população), o embedding não casa termo direto ("óbito" →
 * `data_obito`). Somados com peso, cada um cobre o buraco do outro.
 *
 * PESO_LEXICAL alto de propósito: hoje o lexical é o componente que funciona.
 * Quando o índice doc2query entrar, reequilibrar COM MEDIÇÃO, não por gosto.
 */
const PESO_LEXICAL = 0.6;
// Com doc2query o peso muda de figura: aquele índice vive no mesmo espaço da
// consulta (medido: tabela certa em 0,58-0,97, contra 0,0755 do índice por
// coluna), então ele lidera e o lexical vira desempate.
const PESO_D2Q = 0.6, PESO_LEX_COM_D2Q = 0.3;

export async function selecionarHibrido(pergunta, lexical, k = 5) {
  const q = await vetorDaPergunta(pergunta);
  const lex = lexical.pontuar(pergunta);
  const d2q = scoresDoc2Query(q);

  const juntos = meta.map((m, i) => {
    let dot = 0;
    for (let j = 0; j < dims; j++) dot += q[j] * vetores[i * dims + j];
    const sem = Math.max(0, dot);                  // cosseno já em 0..1 na prática
    const lx = lex.get(m.id) ?? 0;                 // já normalizado em 0..1
    const dq = d2q.get(m.id);
    const score = dq
      ? PESO_D2Q * Math.max(0, dq.s) + PESO_LEX_COM_D2Q * lx + (1 - PESO_D2Q - PESO_LEX_COM_D2Q) * sem
      : PESO_LEXICAL * lx + (1 - PESO_LEXICAL) * sem;
    return { ...m, score, lexical: lx, semantico: sem, ...(dq ? { via: dq.via } : {}) };
  });
  return juntos.sort((a, b) => b.score - a.score).slice(0, k);
}

/** Top-K só por similaridade de cosseno (sem lexical). */
export async function selecionar(pergunta, k = 5, limiar = 0.2) {
  const q = await vetorDaPergunta(pergunta);
  const scores = new Array(meta.length);
  for (let i = 0; i < meta.length; i++) {
    let dot = 0;
    for (let j = 0; j < dims; j++) dot += q[j] * vetores[i * dims + j];
    scores[i] = dot;
  }
  return meta
    .map((m, i) => ({ ...m, score: scores[i] }))
    .filter((t) => t.score >= limiar)
    .sort((a, b) => b.score - a.score)
    .slice(0, k);
}

// ---------------------------------------------------------------------------
// Expansão pelo grafo de join
//
// Uma pergunta de pesquisa é CONJUNÇÃO de aspectos ("mortalidade" E "PIB
// municipal") e cada aspecto mora numa tabela diferente. A similaridade acha no
// máximo o centro de massa; o que liga as pontas é ESTRUTURA, não semântica:
// tabelas que compartilham chave de join (`id_municipio`, `sigla_uf`, `cnpj`).
// Recuperada a âncora, os vizinhos por chave compartilhada entram no ranking.
//
// Chave ubíqua não distingue: `ano` aparece em 385 das 824 tabelas, ligaria
// qualquer coisa a qualquer coisa. O peso da chave é a especificidade
// log(T/n), zerada abaixo de 2 tabelas ou acima de 40% do acervo.
// ---------------------------------------------------------------------------

let grafoColTab = null, grafoTabCol = null, nAcervo = 0;

export function indexarGrafo(colunas) {
  grafoColTab = new Map(), grafoTabCol = new Map();
  nAcervo = meta.length;
  for (const [id, cs] of Object.entries(colunas)) {
    grafoTabCol.set(id, cs.map((c) => c.n));
    for (const c of cs) {
      const a = grafoColTab.get(c.n);
      if (a) a.push(id); else grafoColTab.set(c.n, [id]);
    }
  }
}

function pesoChave(col) {
  const n = grafoColTab.get(col)?.length ?? 0;
  if (n < 2 || n > nAcervo * 0.6) return 0;
  // 1 - fração do acervo que carrega a chave: `id_municipio` (260 tabelas)
  // ainda vale ~0,68 porque LIGAR municípios é o que a pergunta pede; `ano`
  // (385+) afunda. Escala comparável ao score híbrido — ganho de expansão
  // precisa competir por assento, não ser desempate.
  return 1 - n / nAcervo;
}

// Âncoras: quantos do topo puxam vizinhos. Vizinho: quanto do score da âncora a
// estrutura vale, e quanto do lexical da pergunta pesa no desempate entre os
// centenas de vizinhos que uma âncora boa tem.
const MAX_ANCORAS = 3, LIMIAR_ANCORA = 0.5, PESO_ESTRUTURA = 1.0, PESO_LEX_VIZINHO = 0.25;

/**
 * Top-K com expansão: híbrido primeiro, depois vizinhos por chave compartilhada
 * com as âncoras. Re-ranqueia e devolve K — o orçamento de prompt não cresce,
 * só a composição do que entra nele.
 */
export async function selecionarComGrafo(pergunta, lexical, k = 8) {
  const top = await selecionarHibrido(pergunta, lexical, k);
  if (!grafoColTab || !top.length) return top;

  const lex = lexical.pontuar(pergunta);
  const dentro = new Set(top.map((t) => t.id));
  const ancoras = top.filter((t) => t.score >= LIMIAR_ANCORA * top[0].score).slice(0, MAX_ANCORAS);
  const ganhos = new Map();   // id -> { score, via }

  for (const a of ancoras) {
    for (const col of grafoTabCol.get(a.id) ?? []) {
      const w = pesoChave(col);
      if (!w) continue;
      for (const idViz of grafoColTab.get(col)) {
        if (dentro.has(idViz) || idViz === a.id) continue;
        const g = PESO_ESTRUTURA * a.score * w + PESO_LEX_VIZINHO * (lex.get(idViz) ?? 0);
        const atual = ganhos.get(idViz);
        if (!atual || g > atual.score) ganhos.set(idViz, { score: g, via: `↔ ${col}` });
      }
    }
  }

// Vizinho forte DESLOCA membro fraco do topo — o orçamento de K é fixo e a
// composição é o que muda. Sem isso a expansão nunca entraria: o híbrido já
// devolve exatamente K.
  return [...top,
    ...[...ganhos.entries()].map(([id, g]) => ({ ...meta.find((m) => m.id === id), ...g }))]
    .sort((x, y) => y.score - x.score)
    .slice(0, k);
}

/**
 * Seleção DATASET-FIRST.
 *
 * Medido no diagnóstico das 50 douradas: o conjunto esperado de cada pergunta
 * quase sempre vive em 2-4 datasets, e dentro de um dataset as irmãs ficam
 * espalhadas no ranking porque nomes como `microdados`/`municipio` não
 * distinguem nada. Ranquear DATASETS (pelo melhor score de tabela) e repartir
 * o orçamento de K entre eles cobre as pontas que a busca por tabela deixa
 * para trás no posto 9+.
 */
export async function selecionarPorDataset(pergunta, lexical, k = 8, porDataset = 2) {
  const todos = await selecionarHibrido(pergunta, lexical, meta.length);
  const porDs = new Map();
  for (const t of todos) {
    const ds = t.id.split(".")[0];
    const a = porDs.get(ds);
    if (a) a.tabs.push(t); else porDs.set(ds, { ds, melhor: t.score, tabs: [t] });
  }
  const ranking = [...porDs.values()]
    .map((a) => ({ ...a, tabs: a.tabs.sort((x, y) => y.score - x.score).slice(0, porDataset) }))
    .sort((a, b) => b.melhor - a.melhor);

  const saida = [];
  for (let rodada = 0; rodada < porDataset && saida.length < k; rodada++) {
    for (const a of ranking) {
      if (saida.length >= k) break;
      if (a.tabs[rodada]) saida.push(a.tabs[rodada]);
    }
  }
  return saida;
}

/**
 * Afinidade de dataset (MMR-like): âncoras do topo promovem as IRMÃS do próprio
 * dataset que já estavam no pelotão de trás.
 *
 * Medido nas 50 douradas: o padrão dominante de falha é a segunda tabela do
 * MESMO dataset ficar no posto 9-30 ("receitas_candidato" a h24 quando
 * "despesas_candidato" é h1). O round-robin dataset-first falhou porque
 * desperdiça assento em dataset ruído; aqui o boost só alcança quem já provou
 * relevância própria — multiplicador sobre score existente, não assento novo.
 */
const JANELA_AFINIDADE = 40, BOOST_AFINIDADE = 1.25;

export async function selecionarComAfinidade(pergunta, lexical, k = 8) {
  const todos = await selecionarHibrido(pergunta, lexical, JANELA_AFINIDADE);
  if (todos.length <= k) return todos;
  const ancoras = new Set(todos.slice(0, 3).map((t) => t.id.split(".")[0]));
  return todos
    .map((t) => ancoras.has(t.id.split(".")[0]) ? { ...t, score: t.score * BOOST_AFINIDADE } : t)
    .sort((a, b) => b.score - a.score)
    .slice(0, k);
}
