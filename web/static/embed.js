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
    fetch("./index/meta.json").then((r) => r.json()),
    fetch("./index/vectors.bin").then((r) => r.arrayBuffer()),
  ]);

  meta = metaJson.tabelas;
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

export async function selecionarHibrido(pergunta, lexical, k = 5) {
  const q = await vetorDaPergunta(pergunta);
  const lex = lexical.pontuar(pergunta);

  const juntos = meta.map((m, i) => {
    let dot = 0;
    for (let j = 0; j < dims; j++) dot += q[j] * vetores[i * dims + j];
    const sem = Math.max(0, dot);                  // cosseno já em 0..1 na prática
    const lx = lex.get(m.id) ?? 0;                 // já normalizado em 0..1
    return { ...m, score: PESO_LEXICAL * lx + (1 - PESO_LEXICAL) * sem, lexical: lx, semantico: sem };
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
