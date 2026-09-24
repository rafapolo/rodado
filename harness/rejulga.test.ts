import { expect, test } from "bun:test";
import { coeficientes, julgaR } from "./rejulga.ts";

test("coeficientes lê os formatos que a prosa usa", () => {
  expect(coeficientes("**r = −0,27** e controlando r_parcial +0,09; correlação de 0,41")).toEqual([-0.27, 0.09, 0.41]);
  expect(coeficientes("n = 5.570 municípios, R$ 1.036,72")).toEqual([]);
});

test("julgaR: sinal, proximidade e relação nula", () => {
  expect(julgaR(-0.6, [-0.52])).toEqual({ sinal: true, perto: true });
  expect(julgaR(-0.6, [-0.2])).toEqual({ sinal: true, perto: false });
  expect(julgaR(0.33, [-0.1])).toEqual({ sinal: false, perto: false });
  expect(julgaR(0.02, [-0.08])).toEqual({ sinal: true, perto: true });
  expect(julgaR(0.5, [])).toEqual({ sinal: false, perto: false });
});
