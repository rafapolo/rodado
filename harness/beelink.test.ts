import { expect, test, describe } from "bun:test";
import { rewriteToReadParquet, needsParquetFallback, ehChecksumTransitorio, preambuloSessao } from "./beelink.ts";

const globs = new Map([
  ["br_ms_sim.microdados", "~/rodado/br_ms_sim/microdados/*.parquet"],
  ["br_bd_diretorios_brasil.municipio", "~/rodado/br_bd_diretorios_brasil/municipio/*.parquet"],
]);

describe("rewriteToReadParquet", () => {
  test("apelida com o nome simples quando nao ha alias", () => {
    const { sql, rewritten } = rewriteToReadParquet("SELECT * FROM br_ms_sim.microdados WHERE ano = 2020", globs);
    expect(sql).toContain(`read_parquet('~/rodado/br_ms_sim/microdados/*.parquet') AS "microdados"`);
    expect(rewritten).toEqual(["br_ms_sim.microdados"]);
  });

  test("preserva o alias do usuario", () => {
    const { sql } = rewriteToReadParquet("SELECT s.ano FROM br_ms_sim.microdados s", globs);
    expect(sql).toContain(`read_parquet('~/rodado/br_ms_sim/microdados/*.parquet') s`);
    expect(sql).not.toContain(`AS "microdados"`);
  });

  test("preserva alias com AS explicito", () => {
    const { sql } = rewriteToReadParquet("SELECT * FROM br_ms_sim.microdados AS m", globs);
    expect(sql).toContain(`read_parquet('~/rodado/br_ms_sim/microdados/*.parquet') AS m`);
  });

  test("nao confunde palavra-chave seguinte com alias", () => {
    const { sql } = rewriteToReadParquet("SELECT * FROM br_ms_sim.microdados WHERE x=1", globs);
    expect(sql).toContain(`AS "microdados" WHERE`);
  });

  test("reescreve as duas pontas de um join", () => {
    const { rewritten } = rewriteToReadParquet(
      "SELECT * FROM br_ms_sim.microdados s JOIN br_bd_diretorios_brasil.municipio m ON s.id_municipio = m.id_municipio",
      globs);
    expect(rewritten.sort()).toEqual(["br_bd_diretorios_brasil.municipio", "br_ms_sim.microdados"]);
  });

  test("nao toca em tabela fora do catalogo", () => {
    const { sql, rewritten } = rewriteToReadParquet("SELECT * FROM outra.coisa", globs);
    expect(sql).toBe("SELECT * FROM outra.coisa");
    expect(rewritten).toEqual([]);
  });
});

test("needsParquetFallback reconhece so os erros de catalogo/S3", () => {
  expect(needsParquetFallback("Catalog Error: Table not found")).toBe(true);
  expect(needsParquetFallback("IO Error: NoSuchBucket")).toBe(true);
  expect(needsParquetFallback("... s3://baseldosdados/x ...")).toBe(true);
  expect(needsParquetFallback("Binder Error: coluna inexistente")).toBe(false);
});

import { semNaoNumeros } from "./beelink.ts";
test("NaN e Infinity do -json do DuckDB viram null, sem tocar em string", () => {
  const cru = '[{"uf":"AC","corr":NaN,"x":-Infinity,"y":Infinity,"t":"NaN no texto","z":0.4}]';
  expect(JSON.parse(semNaoNumeros(cru))).toEqual([{ uf: "AC", corr: null, x: null, y: null, t: "NaN no texto", z: 0.4 }]);
});

describe("ehChecksumTransitorio", () => {
  test("reconhece o erro visto em 2026-09-24 e nada mais", () => {
    expect(ehChecksumTransitorio("Falhou: IO Error: Corrupt database file: computed checksum 3937549283549580682 does not match stored checksum 3154664207457498862 in block at location 4770508800")).toBe(true);
    expect(ehChecksumTransitorio("Binder Error: Referenced column \"x\" not found")).toBe(false);
    expect(ehChecksumTransitorio(undefined)).toBe(false);
  });
});

test("a SQL do modelo roda com acesso a arquivo travado em ~/rodado e no despejo", () => {
  const p = preambuloSessao();
  expect(p).toContain("SET allowed_directories=['/home/polo/rodado/', '/home/polo/duckdb_tmp/'];");
  // a ordem importa: travar antes de desligar o acesso impediria o próprio SET
  expect(p.indexOf("enable_external_access=false")).toBeLessThan(p.indexOf("lock_configuration=true"));
  expect(p).not.toContain("/tmp/");
  expect(p.trimEnd().endsWith("SET lock_configuration=true;")).toBe(true);
});
