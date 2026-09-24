import { expect, test } from "bun:test";
import { metrica } from "./metricas.ts";

test("o caveat chega ao modelo (tipo_obito_ocorrencia zera os óbitos infantis)", () => {
  const m = metrica("mortalidade infantil")!;
  expect(m).toContain("CUIDADO:");
  expect(m).toContain("tipo_obito_ocorrencia");
});
