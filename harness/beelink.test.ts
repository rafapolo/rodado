import { expect, test, describe } from "bun:test";
import { rewriteToReadParquet, needsParquetFallback } from "./beelink.ts";

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
