/**
 * Item 1 do backlog: a descrição contrastiva de `desambiguacao.json` fica só
 * onde há dataset irmão, e o arquivo de dados não vira glossário do catálogo
 * inteiro por engano. `persona.ts` a gruda no catálogo do system prompt.
 */
import { expect, test, describe } from "bun:test";
import { readFileSync } from "node:fs";
import { datasetsAmbiguos } from "./desambigua.ts";
import { listaDatasets } from "./catalogo.ts";

interface Desambiguacao {
  grupos_semanticos: Record<string, { datasets: string[] }>;
  descricoes: Record<string, string>;
}

const dados = JSON.parse(
  readFileSync(new URL("./dados/desambiguacao.json", import.meta.url), "utf8"),
) as Desambiguacao;

describe("regra de entrada do desambiguacao.json", () => {
  const doDetector = new Set(datasetsAmbiguos());
  const doGrupo = new Set(
    Object.values(dados.grupos_semanticos).flatMap((g) => g.datasets),
  );

  test("todo dataset em descricoes está num par detectado ou num grupo semântico", () => {
    const orfaos = Object.keys(dados.descricoes).filter(
      (d) => !doDetector.has(d) && !doGrupo.has(d),
    );
    expect(orfaos).toEqual([]);
  });

  test("todo dataset citado ainda existe no catálogo — o arquivo não fica para trás do espelho", () => {
    const atual = new Set(listaDatasets());
    const citados = new Set([
      ...Object.keys(dados.descricoes),
      ...Object.values(dados.grupos_semanticos).flatMap((g) => g.datasets),
    ]);
    const sumidos = [...citados].filter((d) => !atual.has(d));
    expect(sumidos).toEqual([]);
  });
});
