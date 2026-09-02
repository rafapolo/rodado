/**
 * Item 1 do backlog, a parte que falta trancar: o CATÁLOGO do prefixo carrega
 * a descrição contrastiva só onde há dataset irmão, e o arquivo de dados não
 * vira glossário do catálogo inteiro por engano.
 */
import { expect, test, describe } from "bun:test";
import { readFileSync } from "node:fs";
import { montaPrefixo } from "./prefixo.ts";
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

describe("montaPrefixo carrega a descrição no CATÁLOGO", () => {
  test("um par conhecido (ppm/pam) aparece com a pista, não só o nome", () => {
    const p = montaPrefixo([]);
    expect(p).toContain("br_ibge_ppm — pecuária");
    expect(p).toContain("br_ibge_pam — lavoura");
  });

  test("dataset sem ambiguidade continua sem descrição grudada", () => {
    const semPar = listaDatasets().find((d) => !dados.descricoes[d]);
    expect(semPar).toBeDefined();
    const p = montaPrefixo([]);
    expect(p).toContain(`\n${semPar}\n`);
  });

  test("o catálogo continua com um dataset por linha (nada de linha extra por descrição)", () => {
    const p = montaPrefixo([]);
    const bloco = p.split("CATÁLOGO")[1]!.split("\n\n")[0]!;
    const linhas = bloco.split("\n").filter(Boolean);
    // a primeira linha do bloco é o cabeçalho "— os N datasets...", o resto é 1/dataset
    expect(linhas.length - 1).toBe(listaDatasets().length);
  });
});
