/**
 * Os recortes que a pergunta nomeia — ano, estado, bioma — e se alguma SQL
 * executada os aplicou.
 *
 * Medido 2026-09-22, conjunto separado: "desmatamento no bioma Amazônia em 2021"
 * foi respondido com a diferença de estoque certa, só que de TODOS os biomas —
 * o filtro de bioma nunca entrou na SQL. Número plausível, errado por 2x, e
 * nada no portão via, porque cada consulta isolada é válida. A checagem só é
 * possível no fim, olhando a pergunta e o que foi executado juntos.
 */
export interface Recorte { rotulo: string; aceitos: string[]; ano?: number }

const UFS: [string, string][] = [
  ["AC", "Acre"], ["AL", "Alagoas"], ["AP", "Amapá"], ["AM", "Amazonas"], ["BA", "Bahia"],
  ["CE", "Ceará"], ["DF", "Distrito Federal"], ["ES", "Espírito Santo"], ["GO", "Goiás"],
  ["MA", "Maranhão"], ["MT", "Mato Grosso"], ["MS", "Mato Grosso do Sul"], ["MG", "Minas Gerais"],
  ["PA", "Pará"], ["PB", "Paraíba"], ["PR", "Paraná"], ["PE", "Pernambuco"], ["PI", "Piauí"],
  ["RJ", "Rio de Janeiro"], ["RN", "Rio Grande do Norte"], ["RS", "Rio Grande do Sul"],
  ["RO", "Rondônia"], ["RR", "Roraima"], ["SC", "Santa Catarina"], ["SP", "São Paulo"],
  ["SE", "Sergipe"], ["TO", "Tocantins"],
];
const BIOMAS = ["Amazônia", "Cerrado", "Caatinga", "Mata Atlântica", "Pampa", "Pantanal"];

const norm = (s: string) => s.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();

export function recortes(pergunta: string): Recorte[] {
  const p = norm(pergunta);
  const out: Recorte[] = [];
  for (const m of p.matchAll(/\b(19[89]\d|20[0-4]\d)\b/g)) {
    const ano = Number(m[1]);
    if (!out.some((r) => r.ano === ano)) out.push({ rotulo: String(ano), aceitos: [String(ano)], ano });
  }
  // Nome mais longo primeiro: "Mato Grosso do Sul" não pode virar "Mato Grosso".
  let resto = p;
  const cru = pergunta.toLowerCase();
  for (const [sigla, nome] of [...UFS].sort((a, b) => b[1].length - a[1].length)) {
    const n = norm(nome);
    const re = new RegExp(`\\b${n}\\b`);
    if (!re.test(resto)) continue;
    // "para" sem acento é preposição; o estado só conta escrito "Pará"
    if (n === "para" && !/(?<!\p{L})pará(?!\p{L})/u.test(cru)) continue;
    // "município/cidade de São Paulo" é a capital, não o estado
    if (new RegExp(`(municipio|cidade|capital) d[eo] ${n}`).test(resto)) { resto = resto.replace(re, " "); continue; }
    out.push({ rotulo: nome, aceitos: [`'${sigla.toLowerCase()}'`, n] });
    resto = resto.replace(re, " ");
  }
  for (const b of BIOMAS) if (p.includes(norm(b))) out.push({ rotulo: `bioma ${b}`, aceitos: [norm(b)] });
  return out;
}

/** Os recortes da pergunta que nenhuma SQL executada contém. */
export function faltando(pergunta: string, sqls: string[]): Recorte[] {
  const texto = norm(sqls.join("\n"));
  const anosSql = [...texto.matchAll(/\b(19[89]\d|20[0-4]\d)\b/g)].map((m) => Number(m[1]));
  return recortes(pergunta).filter((r) => {
    if (r.aceitos.some((a) => texto.includes(a))) return false;
    // ano coberto por faixa: BETWEEN 2019 AND 2022, ano >= 2020 ...
    if (r.ano !== undefined && anosSql.some((a) => a < r.ano!) && anosSql.some((b) => b > r.ano!)) return false;
    return true;
  });
}
