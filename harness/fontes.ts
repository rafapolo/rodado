/**
 * Fontes que a pergunta nomeia → datasets do espelho.
 *
 * Medido 2026-09-27, remedição 2 dos 27: T07-1 pede "crédito rural (SICOR)" e
 * o modelo nunca abriu `br_bcb_sicor` — procurou em `br_anm` (CFEM) e concluiu
 * que o SICOR não existe; T81-2 pede "o sub-índice de mercado móvel do IBC
 * (`hhi_smp`)" e respondeu que `hhi_smp` "não consta no catálogo" (está em
 * `br_anatel_indice_brasileiro_conectividade.municipio`). O CATÁLOGO do system
 * prompt só tem nomes; a sigla que a pergunta usa nem sempre está neles (IBC,
 * IVS), e quando está o modelo ainda erra. Isto é conhecimento, não regra: diz
 * onde a fonte nomeada mora, não o que calcular.
 *
 * Vai junto da primeira resposta de catálogo da sessão (listar_tabelas ou
 * descrever_tabela), não no system prompt — que tem de ficar byte-idêntico para
 * o cache de prefixo valer.
 */
import { catalogo, colunasDe } from "./catalogo.ts";

/** Siglas que não aparecem no nome do dataset. Medidas no schema, não chutadas. */
const APELIDOS: Record<string, string[]> = {
  IBC: ["br_anatel_indice_brasileiro_conectividade"],
  IVS: ["br_ipea_avs"],
  ISP: ["br_rj_isp_estatisticas_seguranca"],
};

/** Siglas genéricas demais para apontar dataset (órgão com dezenas de bases, palavra comum). */
const IGNORA = new Set([
  "IBGE", "CGU", "INEP", "RF", "PIB", "CNAE", "CBO", "UF", "SUS", "II",
  // sigla de UF: 'RJ' casava br_rj_isp_… e br_tce_rj numa pergunta sobre o estado
  "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR",
  "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
]);

const MAX_DATASETS = 4;

/** Siglas em maiúsculas (2+ letras) e identificadores entre crases na pergunta. */
function termos(pergunta: string): { siglas: string[]; colunas: string[] } {
  const colunas = [...pergunta.matchAll(/`([A-Za-z_][A-Za-z0-9_]*)`/g)].map((m) => m[1]!);
  const semCrase = pergunta.replace(/`[^`]*`/g, " ");
  const siglas = [...new Set([...semCrase.matchAll(/\b([A-Z][A-Z0-9]{1,}(?:-[A-Z]{2})?)\b/g)].map((m) => m[1]!))];
  return { siglas, colunas: [...new Set(colunas)] };
}

/** Datasets cujo nome tem a sigla como segmento inteiro (`sicor` em `br_bcb_sicor`, não `sim` em `br_simet_…`). */
function datasetsDaSigla(sigla: string, datasets: string[]): string[] {
  if (APELIDOS[sigla]) return APELIDOS[sigla]!.filter((d) => datasets.includes(d));
  const s = sigla.toLowerCase().replace(/-/g, "_");
  return datasets.filter((d) => {
    const seg = d.split("_");
    return seg.includes(s) || d.endsWith(`_${s}`) || d.includes(`_${s}_`);
  });
}

/** Texto da pista, ou "" quando a pergunta não nomeia nada que o catálogo resolva. */
export function fontesDaPergunta(pergunta: string): string {
  if (!pergunta) return "";
  const cat = catalogo();
  // `_local_*` são tabelas de trabalho do projeto, não fonte.
  const datasets = [...new Set(cat.map((e) => e.dataset))].filter((d) => !d.startsWith("_"));
  const { siglas, colunas } = termos(pergunta);
  const linhas: string[] = [];
  for (const s of siglas) {
    if (IGNORA.has(s)) continue;
    // 'ISP-RJ': a sigla com sufixo de UF resolve pela parte antes do hífen
    let ds = datasetsDaSigla(s, datasets);
    if (!ds.length && s.includes("-")) ds = datasetsDaSigla(s.split("-")[0]!, datasets);
    if (!ds.length || ds.length > MAX_DATASETS) continue;
    linhas.push(`${s} → ${ds.join(", ")}`);
  }
  for (const c of colunas) {
    const alvo = c.toLowerCase();
    const tabelas = cat
      .filter((e) => !e.dataset.startsWith("_"))
      .map((e) => `${e.dataset}.${e.tabela}`)
      .filter((id) => (colunasDe(id) ?? []).some((col) => col.name.toLowerCase() === alvo));
    if (tabelas.length && tabelas.length <= MAX_DATASETS) linhas.push(`coluna ${c} → ${tabelas.join(", ")}`);
  }
  if (!linhas.length) return "";
  return `FONTES NOMEADAS NA PERGUNTA (onde moram no espelho):\n` + linhas.map((l) => `  ${l}`).join("\n");
}
