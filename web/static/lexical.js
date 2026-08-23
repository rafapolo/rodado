/**
 * Busca lexical sobre nome de dataset, tabela e coluna.
 *
 * Medida sozinha, entrega 6/15 nas perguntas douradas — seis vezes o que o
 * índice de embeddings entrega (1/15), com zero byte de modelo. Ela cobre o que
 * o embedding erra: casamento direto de termo ("óbito" → coluna `data_obito`).
 * O embedding cobre o que ela erra: sinônimo sem raiz comum ("quanta gente
 * mora" → população).
 */
const RUIDO = new Set(("qual quais quantos quantas quanto foi foram e de do da dos das em no na " +
  "nos nas o a os as por para com que mais maior menor tem existe existem segundo acima " +
  "ano anos entre sobre qual e um uma como onde quando").split(" "));

const semAcento = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
// plural pt-BR grosseiro: obitos->obito, municipios->municipio, capitais->capital
const raiz = (w) => w.replace(/(oes|aes|ais|eis|is|ns|s)$/, "");

let docs = null, idf = null;

export function indexar(meta, colunas) {
  docs = meta.map((m) => {
    const termos = new Set();
    for (const w of semAcento(`${m.dataset} ${m.tabela}`).split(/[_.\s]+/)) if (w.length > 2) termos.add(raiz(w));
    for (const c of colunas[m.id] ?? []) for (const w of semAcento(c.n).split(/[_\s]+/)) if (w.length > 2) termos.add(raiz(w));
    return { id: m.id, termos };
  });
  // idf: termo que aparece em meia base não distingue nada
  const df = new Map();
  for (const d of docs) for (const t of d.termos) df.set(t, (df.get(t) ?? 0) + 1);
  idf = new Map([...df].map(([t, n]) => [t, Math.log(docs.length / (n + 1))]));
  return docs.length;
}

/** Score lexical por tabela, normalizado em 0..1. */
export function pontuar(pergunta) {
  const palavras = semAcento(pergunta).split(/\W+/)
    .filter((w) => w.length > 2 && !RUIDO.has(w) && !/^\d+$/.test(w))  // ano é filtro, não assunto
    .map(raiz);
  const scores = new Map();
  if (!palavras.length) return scores;

  let max = 0;
  for (const d of docs) {
    let s = 0;
    for (const w of palavras) {
      for (const t of d.termos) {
        if (t === w || t.startsWith(w) || w.startsWith(t)) { s += idf.get(t) ?? 0; break; }
      }
    }
    if (s > 0) { scores.set(d.id, s); if (s > max) max = s; }
  }
  if (max > 0) for (const [k, v] of scores) scores.set(k, v / max);
  return scores;
}
