/**
 * Conjunto de avaliação — cruza `docs/perguntas.md` (a pergunta e os datasets
 * que ela exige) com `docs/respostas.md` (o número já conferido no beelink).
 *
 * A métrica que vale é o **n**. Ele é a impressão digital do join: juntar
 * RAIS × SIM × Censo por município com os filtros certos dá n=4.251, e
 * qualquer erro de tabela, de chave ou de filtro dá outro número. Um inteiro
 * valida a cadeia inteira — recuperação, join e partição — sem precisar
 * comparar prosa.
 *
 * Datasets marcados com `*` em perguntas.md são de apoio ("de outros temas,
 * usados para completar o cruzamento") e não contam contra o recall — mesma
 * regra de scripts/avalia_douradas_perguntas.py, para os números serem
 * comparáveis.
 */
import { readFileSync } from "node:fs";

const RAIZ = new URL("..", import.meta.url).pathname;

export interface Caso {
  /** T01-2 — o código da PERGUNTA em perguntas.md */
  id: string;
  /** o conteúdo do gabarito casa melhor com OUTRA pergunta do mesmo tema */
  suspeito: boolean;
  /** qual pergunta casaria melhor, quando suspeito */
  melhorCasamento?: string;
  tema: number;
  item: number;
  pergunta: string;
  /** datasets obrigatórios, sem o prefixo br_ */
  obrigatorios: string[];
  /** datasets de apoio (marcados com *) — não contam contra o recall */
  apoio: string[];
  /** n conferido, quando respostas.md declara um */
  n?: number;
  /** coeficiente de correlação conferido, quando há */
  r?: number;
  /** o texto da resposta conferida, para inspeção */
  gabarito: string;
}

function normaliza(ds: string): string {
  return ds.trim().replace(/^br_/, "").replace(/[*\\\s]+$/g, "").toLowerCase();
}

/** Aceita "4.251", "4251" e "1 657" — respostas.md usa ponto de milhar pt-BR. */
function numero(s: string): number {
  return Number(s.replace(/[.\s]/g, "").replace(",", "."));
}

export function carregaCasos(): Caso[] {
  const perguntas = readFileSync(`${RAIZ}docs/perguntas.md`, "utf8").split("\n");
  const respostas = readFileSync(`${RAIZ}docs/respostas.md`, "utf8");

  // 1. perguntas.md — tema vem do cabeçalho "## 01 · ...", item da numeração
  const porId = new Map<string, Omit<Caso, "gabarito" | "n" | "r" | "suspeito" | "melhorCasamento">>();
  let tema = 0;
  for (const linha of perguntas) {
    const cab = linha.match(/^##\s+(\d+)\s+·/);
    if (cab) { tema = Number(cab[1]); continue; }
    const m = linha.trim().match(/^(\d+)\.\s+(.*?)\s*\*\(n=\d+:\s*([^)]+)\)\*\s*$/);
    if (!m || !tema) continue;
    const item = Number(m[1]);
    const obrigatorios: string[] = [];
    const apoio: string[] = [];
    // As perguntas multi-dataset anotam `n=4+: ds1, ds2, chaves: id_municipio,
    // sigla_uf` — tudo depois de "chaves:" é coluna de junção, não dataset. Sem
    // cortar, `sigla_uf` e `id_municipio` entram no gabarito como se fossem
    // datasets e o modelo é acusado de não os ter escolhido; eram a 3ª e a 7ª
    // "falha" mais comum da rodada de 274.
    for (const bruto of m[3].split(/;|\bchaves?\s*:/i)[0].split(",")) {
      const n = normaliza(bruto);
      if (n.length < 3) continue;
      (/[*\\]/.test(bruto) ? apoio : obrigatorios).push(n);
    }
    const id = `T${String(tema).padStart(2, "0")}-${item}`;
    porId.set(id, { id, tema, item, pergunta: m[2].trim(), obrigatorios, apoio });
  }

  // 2. respostas.md — a numeração declarada é a verdade, e o conteúdo a audita.
  //
  //    respostas.md diz que `T<tema>-<nº>` "identifica a pergunta exata". Em
  //    parte dos casos não identifica: no tema 05 a resposta sobre o Senado é
  //    T05-3 mas a pergunta do Senado é a nº 2. As respostas parecem ter sido
  //    escritas na ordem em que foram investigadas.
  //
  //    Reatribuir por heurística de palavras seria trocar um erro conhecido por
  //    um inventado — o casador erra sozinho (dois gabaritos de educação caem na
  //    mesma pergunta, porque todos falam de IDEB e ENEM). Então: mantemos o par
  //    declarado e marcamos `suspeito` quando outra pergunta do tema casa
  //    visivelmente melhor. Só os confiáveis entram na avaliação; os suspeitos
  //    saem numa lista para revisão humana.
  const casos: Caso[] = [];
  for (const [, id, status, texto] of respostas.matchAll(
    /\*\*(T\d+-\d+)\s+(✅|◐)\*\*\s*(.*)/g,
  )) {
    const declarada = porId.get(id);
    if (!declarada) continue;

    const tema = declarada.tema;
    const pontos = [...porId.values()]
      .filter((p) => p.tema === tema)
      .map((p) => ({ id: p.id, s: sobreposicao(texto, p.pergunta) }))
      .sort((x, y) => y.s - x.s);
    const melhor = pontos[0]!;
    const daDeclarada = pontos.find((x) => x.id === id)?.s ?? 0;
    // margem de 2 termos: ruído de vocabulário não deve virar acusação
    const suspeito = melhor.id !== id && melhor.s - daDeclarada >= 2;

    const n = texto.match(/\bn\s*=\s*([\d.\s]+\d)/);
    const r = texto.match(/\br\s*=\s*([+−-]?\s*[\d,]+)/);
    casos.push({
      ...declarada,
      suspeito,
      melhorCasamento: suspeito ? melhor.id : undefined,
      gabarito: texto.trim(),
      n: n ? numero(n[1]) : undefined,
      r: r ? numero(r[1].replace(/[−-]\s*/, "-").replace(/\+\s*/, "")) : undefined,
    });
    void status;
  }
  return casos;
}

/** Termos que não distinguem uma pergunta da outra dentro de um tema. */
const VAZIAS = new Set([
  "que", "com", "por", "para", "mais", "menos", "dos", "das", "nos", "nas",
  "uma", "seu", "sua", "entre", "cada", "quanto", "onde", "quais", "sao",
  "tem", "the", "essa", "esse", "mesmo", "seus", "suas", "seja", "ainda",
]);

function termos(s: string): Set<string> {
  return new Set(
    s.toLowerCase()
      .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
      .split(/[^a-z0-9_]+/)
      .filter((w) => w.length > 2 && !VAZIAS.has(w)),
  );
}

function sobreposicao(a: string, b: string): number {
  const ta = termos(a), tb = termos(b);
  let n = 0;
  for (const w of tb) if (ta.has(w)) n++;
  return n;
}

/**
 * A ponte que faltava entre este arquivo e `lote.ts`: os casos confiáveis com
 * `n` conferido, no TSV `pergunta <TAB> esperado` que `lote.ts` já lê.
 *
 *     bun harness/casos.ts --tsv > /tmp/casos.tsv
 *     bun harness/lote.ts /tmp/casos.tsv
 *
 * Só `!suspeito`: um caso cuja numeração não bate com o conteúdo leva um `n` de
 * outra pergunta, e a rodada mediria o modelo contra o gabarito errado.
 * A pergunta vai com o espaço em branco colapsado — TAB dentro dela partiria a
 * linha em três campos e o `esperado` viraria pedaço de frase.
 */
export function tsvComN(): string {
  return carregaCasos()
    .filter((c) => !c.suspeito && c.n !== undefined)
    .map((c) => `${c.pergunta.replace(/\s+/g, " ").trim()}\t${c.n}`)
    .join("\n");
}

if (import.meta.main) {
  if (Bun.argv.includes("--tsv")) { console.log(tsvComN()); process.exit(0); }
  const c = carregaCasos();
  const comN = c.filter((x) => x.n !== undefined);
  const comR = c.filter((x) => x.r !== undefined);
  console.log(`${c.length} casos casados entre perguntas.md e respostas.md`);
  console.log(`  ${comN.length} com n conferido`);
  console.log(`  ${comR.length} com r conferido`);
  console.log(`  ${c.filter((x) => x.obrigatorios.length > 1).length} exigem 2+ datasets obrigatórios`);
  const susp = c.filter((x) => x.suspeito);
  const bons = c.filter((x) => !x.suspeito);
  console.log(`\n  CONFIÁVEIS (numeração e conteúdo concordam): ${bons.length}`);
  console.log(`    com n: ${bons.filter((x) => x.n !== undefined).length}`);
  console.log(`  SUSPEITOS (fora da avaliação, para revisão): ${susp.length}`);
  for (const x of susp) console.log(`    ${x.id} casa melhor com ${x.melhorCasamento}`);
  console.log("\nexemplos:");
  for (const x of comN.slice(0, 4)) {
    console.log(`  ${x.id}  n=${x.n}${x.r !== undefined ? ` r=${x.r}` : ""}  [${x.obrigatorios.join(", ")}]`);
    console.log(`      ${x.pergunta.slice(0, 88)}`);
  }
}


/**
 * TODAS as perguntas com datasets anotados — 280, contra as 84 que têm resposta
 * conferida.
 *
 * A restrição a "casos com resposta" era minha, não da fonte: para medir
 * **escolha de dataset** basta a pergunta e os datasets que ela cita, e as 280
 * têm isso. Só a medição de número ponta a ponta precisa do gabarito de
 * `respostas.md`. Estava desprezando 178 casos à toa.
 */
export function carregaTodasPerguntas(): Omit<Caso, "gabarito" | "suspeito">[] {
  const linhas = readFileSync(`${RAIZ}docs/perguntas.md`, "utf8").split("\n");
  const out: Omit<Caso, "gabarito" | "suspeito">[] = [];
  let tema = 0;
  for (const linha of linhas) {
    const cab = linha.match(/^##\s+(\d+)\s+·/);
    if (cab) { tema = Number(cab[1]); continue; }
    const m = linha.trim().match(/^(\d+)\.\s+(.*?)\s*\*\(n=\d+\+?:\s*([^)]+)\)\*\s*$/);
    if (!m || !tema) continue;
    const obrigatorios: string[] = [];
    const apoio: string[] = [];
    // A seção multi-dataset anota `n=4: ds1, ds2; chaves: id_municipio, sigla_uf`
    // — tudo depois do `;` (ou de "chaves:") é coluna de junção, não dataset.
    // Sem cortar, `sigla_uf` e `id_municipio` entram no gabarito como datasets e
    // o modelo é acusado de não os ter escolhido: eram a 3ª e a 7ª "falha" mais
    // comum da rodada de 274.
    for (const bruto of m[3]!.split(/;|\bchaves?\s*:/i)[0]!.split(",")) {
      const n = normaliza(bruto);
      if (n.length < 3) continue;
      (/[*\\]/.test(bruto) ? apoio : obrigatorios).push(n);
    }
    if (!obrigatorios.length) continue;
    out.push({
      id: `T${String(tema).padStart(2, "0")}-${m[1]}`,
      tema, item: Number(m[1]), pergunta: m[2]!.trim(), obrigatorios, apoio,
    });
  }
  return out;
}

/**
 * Exemplos few-shot de uma fonte **independente** — `docs/relatorio-social/`,
 * que cita tabelas em `**Fontes:**` e não alimenta nenhuma avaliação daqui.
 *
 * Antes eu tirava os exemplos do próprio conjunto de teste, o que custava metade
 * dele: 36 perguntas iam para o prefixo e sobravam 45 para medir. Vindos de fora,
 * as 280 inteiras viram teste.
 */
export function exemplosIndependentes(): { pergunta: string; obrigatorios: string[] }[] {
  const txt = readFileSync(`${RAIZ}docs/relatorio-social/perguntas.md`, "utf8");
  const out: { pergunta: string; obrigatorios: string[] }[] = [];
  const linhas = txt.split("\n");
  for (let i = 0; i < linhas.length; i++) {
    const f = linhas[i]!.match(/^\s*-\s*\*\*Fontes:\*\*\s*(.+)$/);
    if (!f) continue;
    // a pergunta vem logo acima, no formato `**N. texto?**`
    let q = "";
    for (let j = i - 1; j >= 0 && j > i - 5; j--) {
      const m = linhas[j]!.trim().match(/^\*\*\d+\.\s+(.+?)\*\*$/);
      if (m) { q = m[1]!.trim(); break; }
    }
    if (!q) continue;
    const ds = [...new Set(
      [...f[1]!.matchAll(/`([a-z0-9_]+)\.[a-z0-9_]+`/g)].map((m) => normaliza(m[1]!)),
    )];
    if (ds.length) out.push({ pergunta: q, obrigatorios: ds });
  }
  return out;
}
