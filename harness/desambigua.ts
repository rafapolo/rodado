/**
 * Detector de **dataset irmão** — quais nomes do catálogo não se distinguem.
 *
 * Por que existe: item 1 do `tasks/backlog.md`. Na rodada de 274 perguntas,
 * **24 das 36 falhas** foram o modelo escolhendo o parente errado — pediu
 * `br_ibge_ppm` (pecuária) e deu `br_ibge_pam` (agrícola); `br_anp_combustiveis`
 * por `br_anp_precos_combustiveis`; `br_me_caged` por `br_me_rais`. Nome
 * semântico separa domínio, não separa irmão.
 *
 * A lista de pares tem que ser **reprodutível**, não um palpite: se a
 * desambiguação vier de uma lista escrita à mão, ninguém sabe depois se ela
 * cobre o catálogo ou só os quatro casos que apareceram na última rodada. Por
 * isso a detecção é código sobre `listaDatasets()` e as descrições, dado.
 *
 *     bun harness/desambigua.ts            # os pares detectados, por regra
 *     bun harness/desambigua.ts --sem-desc # só os que ainda não têm descrição
 *
 * **Limite conhecido e medido:** este detector acha ambiguidade de NOME. A
 * confusão `br_tesouro_capag` -> `br_firjan_ifgf` / `br_me_siconfi` é
 * *semântica* (três medidas de saúde fiscal municipal, siglas sem nada em
 * comum) e nenhuma regra de string a encontra. Esses grupos entram no JSON pela
 * chave `grupos_semanticos`, vindos das falhas medidas — e é por isso que o
 * arquivo de dados não é gerado por este script, só conferido contra ele.
 */
import { listaDatasets } from "./catalogo.ts";

/** Prefixos de escopo geográfico — não são o órgão, são a jurisdição. */
const ESCOPOS = new Set(["br", "world", "us", "eu", "un", "global", "mundo"]);

export interface Par {
  a: string;
  b: string;
  regra: string;
}

/** Órgão e resto de um nome de dataset. `br_ibge_ppm` -> ["ibge", "ppm"]. */
export function parte(nome: string): { orgao: string; resto: string } {
  const segs = nome.replace(/^_/, "").split("_").filter(Boolean);
  const i = ESCOPOS.has(segs[0] ?? "") ? 1 : 0;
  return { orgao: segs[i] ?? "", resto: segs.slice(i + 1).join("") };
}

function levenshtein(a: string, b: string): number {
  const m = a.length, n = b.length;
  let ant = Array.from({ length: n + 1 }, (_, j) => j);
  for (let i = 1; i <= m; i++) {
    const cur = [i];
    for (let j = 1; j <= n; j++) {
      cur[j] = Math.min(
        ant[j]! + 1,
        cur[j - 1]! + 1,
        ant[j - 1]! + (a[i - 1] === b[j - 1] ? 0 : 1),
      );
    }
    ant = cur;
  }
  return ant[n]!;
}

/**
 * Os pares de nomes que um leitor (ou um 26B em q4) pode trocar um pelo outro.
 * Ordem determinística: `listaDatasets()` já vem ordenado e o laço é sobre
 * índices crescentes — nada de Set/Map iterado sem sort, porque o catálogo entra
 * no prefixo estável e ordem variável evapora o cache de 44x em silêncio.
 */
export function paresAmbiguos(datasets = listaDatasets()): Par[] {
  const out: Par[] = [];
  for (let i = 0; i < datasets.length; i++) {
    for (let j = i + 1; j < datasets.length; j++) {
      const a = datasets[i]!, b = datasets[j]!;
      const pa = parte(a), pb = parte(b);
      const regra = classifica(pa, pb);
      if (regra) out.push({ a, b, regra });
    }
  }
  return out;
}

/** O tema do dataset: o resto, ou o próprio órgão quando não há resto
 *  (`eu_sanctions` -> "sanctions", `br_me_cno` -> "cno"). */
const tema = (p: { orgao: string; resto: string }) => p.resto || p.orgao;

function classifica(
  pa: { orgao: string; resto: string },
  pb: { orgao: string; resto: string },
): string | null {
  // 1. Mesmo tema em órgãos diferentes: `br_me_cno` e `br_rf_cno` são os dois
  //    "cadastro nacional de obras"; `eu_sanctions`/`un_sanctions`/
  //    `global_ofac_sanctions`. Aqui o órgão é justamente o que distingue, e é
  //    o pedaço do nome que o modelo tende a omitir.
  if (tema(pa) === tema(pb)) return "cauda_igual";

  if (pa.orgao !== pb.orgao) return null;

  // 2. `br_anp_combustiveis` dentro de `br_anp_precos_combustiveis`, e
  //    `br_me_rais` dentro de `br_me_rais_identificada`. Foi a forma exata de
  //    duas das quatro confusões medidas. Comparado sobre o resto achatado
  //    (sem underscore) para pegar `censo_2022` vs `censo2022_raca`.
  if (pa.resto && pb.resto && (pb.resto.includes(pa.resto) || pa.resto.includes(pb.resto))) {
    return "contido";
  }

  // 3. Sigla curta contra sigla curta do mesmo órgão: `ppm`/`pam`, `sia`/`sih`/
  //    `sim`. Uma letra de diferença em três é o caso `ibge_ppm`->`ibge_pam`,
  //    sozinho 4 das 38 perdas.
  if (pa.resto.length <= 6 && pb.resto.length <= 6) {
    const d = levenshtein(pa.resto, pb.resto);
    if (d <= Math.max(1, Math.floor(Math.min(pa.resto.length, pb.resto.length) / 3))) {
      return "sigla_proxima";
    }
  }

  // 4. Raiz comum longa no mesmo órgão: `censo_escolar` x
  //    `censo_educacao_superior`, `sipni_*`, `indicador...` x `indicadores...`.
  //    Cinco caracteres é o piso que separa família de coincidência ("cn" de
  //    `cno`/`cnpj` casaria com dois).
  const pre = prefixoComum(pa.resto, pb.resto);
  if (pre >= 5) return "raiz_comum";

  return null;
}

function prefixoComum(a: string, b: string): number {
  let i = 0;
  while (i < a.length && i < b.length && a[i] === b[i]) i++;
  return i;
}

/** Os datasets envolvidos em pelo menos um par, ordenados. */
export function datasetsAmbiguos(pares = paresAmbiguos()): string[] {
  const s = new Set<string>();
  for (const p of pares) { s.add(p.a); s.add(p.b); }
  return [...s].sort();
}

if (import.meta.main) {
  const pares = paresAmbiguos();
  const porRegra = new Map<string, Par[]>();
  for (const p of pares) (porRegra.get(p.regra) ?? porRegra.set(p.regra, []).get(p.regra)!).push(p);
  for (const regra of [...porRegra.keys()].sort()) {
    const ps = porRegra.get(regra)!;
    console.log(`\n${regra}: ${ps.length}`);
    for (const p of ps) console.log(`  ${p.a}  |  ${p.b}`);
  }
  const envolvidos = datasetsAmbiguos(pares);
  console.log(`\n${pares.length} pares, ${envolvidos.length} datasets envolvidos de ${listaDatasets().length}`);

  if (Bun.argv.includes("--sem-desc")) {
    const desc = JSON.parse(
      await Bun.file(new URL("./dados/desambiguacao.json", import.meta.url)).text(),
    ) as { descricoes: Record<string, string> };
    const faltam = envolvidos.filter((d) => !desc.descricoes[d]);
    console.log(`\nSEM DESCRIÇÃO (${faltam.length}):`);
    for (const d of faltam) console.log(`  ${d}`);
  }
}
