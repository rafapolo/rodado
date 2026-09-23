/**
 * Como as ferramentas escrevem para o modelo. O contexto é o gargalo — cada
 * token de resultado é prefilado a ~60 t/s e fica no histórico até o fim da
 * pergunta —, então o formato é compacto, mas nunca perde o que decide a SQL:
 * o tipo da coluna (aspas ou não no literal) e o significado dos códigos.
 */
import type { CappedResult } from "./sqlguard.ts";
import { legenda, codigos } from "./dicionarios.ts";
import { COLUNAS_PARTICAO } from "./catalogo.ts";
import { notaTabela, notaColuna, calculosDaTabela } from "./semantica.ts";
import { valores } from "./valores.ts";

export interface Coluna { name: string; type: string }

const PARTICAO = new Set<string>(COLUNAS_PARTICAO);
const CURTO: Record<string, string> = {
  INTEGER: "int", INT64: "int", BIGINT: "int", STRING: "str", VARCHAR: "str",
  FLOAT: "float", FLOAT64: "float", DOUBLE: "float", NUMERIC: "num", DECIMAL: "num",
  BOOLEAN: "bool", BOOL: "bool", DATE: "date", DATETIME: "datetime", TIMESTAMP: "timestamp",
};
const curto = (t: string) => CURTO[t.toUpperCase()] ?? t.toLowerCase();

/**
 * Com mais colunas codificadas que isto, só as ligadas à pergunta mostram a
 * lista de códigos. SIM e RAIS descreviam-se em ~3.500 tokens (~70 s de
 * leitura), quase tudo códigos de colunas que a pergunta não usa.
 */
const MUITAS_CODIFICADAS = 8;

// Palavras de toda pergunta, que casariam com qualquer coluna. "rede", "estadual"
// e "municipal" NÃO entram: "rede municipal" tem que achar os códigos de `rede`.
const PARADAS = new Set(["qual", "quai", "quan", "tota", "nume", "bras", "cida", "segu",
  "entr", "dado", "anos", "pais", "medi", "houv", "fora", "tinh", "havi", "tipo", "code", "codi"]);

/** Raízes de 4 letras das palavras — "rurais" e "Rural" casam em "rura". */
function raizes(texto: string): Set<string> {
  const n = texto.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();
  return new Set(n.split(/[^a-z]+/).filter((w) => w.length >= 4).map((w) => w.slice(0, 4)).filter((r) => !PARADAS.has(r)));
}

/** A coluna codificada tem a ver com a pergunta: pelo nome ou por um rótulo. */
export function ligadaAPergunta(tabela: string, coluna: string, pergunta: string): boolean {
  const q = raizes(pergunta);
  if (!q.size) return true;
  const rotulos = codigos(tabela, coluna)?.previa.map(([, v]) => v) ?? [];
  return [...raizes([coluna.replace(/_/g, " "), ...rotulos].join(" "))].some((r) => q.has(r));
}

/** Acima disto, só as colunas que decidem a SQL ganham linha própria. */
const LARGA = 60;

/** Prefixo de grupo: as duas primeiras palavras do nome (quantidade_matricula_*). */
const prefixo = (n: string) => n.split("_").slice(0, 2).join("_");

/**
 * Tabela larga sem filtro: as colunas-chave e as codificadas por extenso, o
 * resto resumido por prefixo. As 455 colunas de `escola` eram 5.660 tokens
 * prefilados a cada pergunta que a tocava — e a pergunta quase nunca usa mais
 * de três.
 */
export function descreve(tabela: string, cols: Coluna[], sufixo = "", filtro = "", pergunta = ""): string {
  const part = cols.filter((c) => PARTICAO.has(c.name.toLowerCase()));
  const nota = notaTabela(tabela);
  const calc = calculosDaTabela(tabela);
  const cab = `${tabela} — ${cols.length} colunas${sufixo}` +
    (part.length ? ` · filtre por partição: ${part.map((c) => c.name).join(", ")}` : "") +
    (nota ? `\n  NOTA: ${nota}` : "") +
    (calc.length ? `\n  CÁLCULOS VERIFICADOS (use estas expressões): ${calc.join("; ")}` : "");
  const termos = filtro.toLowerCase().split(/[,\s]+/).filter(Boolean);
  const codificadas = cols.filter((c) => legenda(tabela, c.name));
  const compacta = Boolean(pergunta) && codificadas.length > MUITAS_CODIFICADAS;
  const completa = (c: Coluna) => !compacta || (codigos(tabela, c.name)?.total ?? 0) <= 5 ||
    termos.some((t) => c.name.toLowerCase().includes(t)) ||
    Boolean(notaColuna(tabela, c.name)) || ligadaAPergunta(tabela, c.name, pergunta);
  const linha = (c: Coluna) => {
    const n = notaColuna(tabela, c.name);
    const leg = legenda(tabela, c.name);
    const cod = leg && !completa(c) ? ` (${codigos(tabela, c.name)?.total ?? "?"} códigos)` : leg;
    const v = leg ? undefined : valores(tabela, c.name);
    const vs = v ? ` — valores${v.amostra ? " (amostra)" : ""}: ${v.lista.map((x) => `'${x}'`).join(", ")}` : "";
    return `  ${c.name}: ${curto(c.type)}${cod}${vs}${n ? ` — NOTA: ${n}` : ""}`;
  };
  const avisoCodigos = compacta && codificadas.some((c) => !completa(c))
    ? [`  (colunas marcadas "(N códigos)": os códigos saem com descrever_tabela e filtro=<nome da coluna>)`] : [];

  const destaque = cols.filter((c) =>
    PARTICAO.has(c.name.toLowerCase()) || /^id_|^sigla|^nome/.test(c.name) || legenda(tabela, c.name) || notaColuna(tabela, c.name) || valores(tabela, c.name));

  // O filtro SOMA as colunas achadas às colunas-chave, nunca as esconde. Medido
  // 2026-09-23: a 1ª chamada já veio com filtro="escola" (um chute), a
  // descrição omitiu tipo_localizacao — a coluna com '2'=Rural — e o modelo
  // concluiu que "o Censo Escolar não classifica escola rural". Pergunta que
  // acertava em 81 s errou em 577 s.
  if (termos.length) {
    const achadas = cols.filter((c) => !destaque.includes(c) && termos.some((t) => c.name.toLowerCase().includes(t)));
    return [cab, ...avisoCodigos, ...destaque.map(linha), `  (+${achadas.length} com '${termos.join("', '")}')`, ...achadas.map(linha)].join("\n");
  }
  if (cols.length <= LARGA) return [cab, ...avisoCodigos, ...cols.map(linha)].join("\n");
  const resto = cols.filter((c) => !destaque.includes(c));
  const agrupa = (cs: Coluna[], chave: (n: string) => string) => {
    const m = new Map<string, Coluna[]>();
    for (const c of cs) m.set(chave(c.name), [...(m.get(chave(c.name)) ?? []), c]);
    return m;
  };
  // Duas palavras separam quantidade_matricula_* de quantidade_docente_*; o que
  // sobra em família pequena (agua_filtrada, agua_potavel) reagrupa por uma.
  const grupos = new Map([...agrupa(resto, prefixo)].filter(([, g]) => g.length >= 3));
  const pequenas = resto.filter((c) => !grupos.has(prefixo(c.name)));
  for (const [p, g] of agrupa(pequenas, (n) => n.split("_")[0]!)) grupos.set(p, g);
  const soltas = [...grupos.values()].filter((g) => g.length < 3).flat();
  const resumo = [...grupos].filter(([, g]) => g.length >= 3)
    .map(([p, g]) => `${p}_* (${g.length}, ex.: ${g[0]!.name}:${curto(g[0]!.type)})`);
  return [
    cab,
    ...avisoCodigos,
    ...destaque.map(linha),
    ...(soltas.length ? [`  outras: ${soltas.map((c) => `${c.name}:${curto(c.type)}`).join(", ")}`] : []),
    ...(resumo.length ? [
      `  grupos: ${resumo.join("; ")}`,
      `  Para ver os nomes de um grupo, chame descrever_tabela de novo com filtro (ex.: filtro="${[...grupos].find(([, g]) => g.length >= 3)?.[0]}").`,
    ] : []),
  ].join("\n");
}

const celula = (v: unknown) =>
  v === null || v === undefined ? "NULL" : typeof v === "object" ? JSON.stringify(v) : String(v).replace(/\s*\n\s*/g, " ");

/** Linhas como tabela de texto: cabeçalho uma vez, em vez da chave repetida em cada objeto JSON. */
export function tabelaTexto(r: CappedResult): string {
  const rows = r.rows as Record<string, unknown>[];
  const partes: string[] = [];
  if (rows.length) {
    const cols = Object.keys(rows[0]!);
    const total = r.total ?? rows.length;
    partes.push(total > rows.length ? `${total} linhas, mostrando ${rows.length}:` : `${rows.length} linha(s):`);
    partes.push(cols.join(" | "));
    for (const row of rows) partes.push(cols.map((c) => celula(row[c])).join(" | "));
  }
  if (r.note) partes.push(r.note);
  else if (!rows.length && r.columns) partes.push(`colunas: ${r.columns.join(", ")}`);
  return partes.join("\n");
}

/**
 * O resultado tem código de município e nenhum nome — o laço já respondeu
 * "3550308" em vez de "São Paulo" (README, pipeline fixo contra agêntico).
 */
export function dicaMunicipio(rows: Record<string, unknown>[]): string {
  const cols = rows.length ? Object.keys(rows[0]!) : [];
  if (!cols.some((c) => /^id_municipio/.test(c))) return "";
  if (cols.some((c) => /nome|municipio_nome/.test(c))) return "";
  return "id_municipio é o código IBGE de 7 dígitos, não o nome. Para responder com o nome do município, " +
    "junte com br_bd_diretorios_brasil.municipio (colunas id_municipio, nome, sigla_uf).";
}
