import { describe, expect, test } from "bun:test";
import { avisoDoAmbiente, avisoDoTeto, criaPrazo } from "./prazo.ts";

describe("criaPrazo — B27, teto de 25 min chegava antes do orçamento de consultas", () => {
  const relogio = () => {
    let t = 1_000_000;
    return { agora: () => t, anda: (ms: number) => { t += ms; } };
  };

  test("calado antes do limiar, avisa depois — e continua avisando", () => {
    const r = relogio();
    const p = criaPrazo(18 * 60_000, r.agora);
    r.anda(17 * 60_000 + 59_000);
    expect(p.aviso()).toBeUndefined();
    r.anda(1_000);
    expect(p.aviso()).toContain("18 min");
    expect(p.aviso()).toContain("PARE de consultar");
    r.anda(3 * 60_000);
    expect(p.aviso()).toContain("21 min");
  });

  test("a mensagem admite 'não foi possível'", () => {
    const r = relogio();
    const p = criaPrazo(1, r.agora);
    r.anda(5);
    expect(p.aviso()).toContain("não foi possível");
  });

  test("limiar 0 ou inválido desliga", () => {
    const r = relogio();
    for (const ms of [0, -1, NaN]) {
      const p = criaPrazo(ms, r.agora);
      r.anda(60 * 60_000);
      expect(p.aviso()).toBeUndefined();
    }
  });

  test("limiar derivado do teto: 18 dos 25 min, e segue HARNESS_TETO_MIN", () => {
    expect(avisoDoTeto(25 * 60_000)).toBe(18 * 60_000);
    expect(avisoDoAmbiente({})).toBe(18 * 60_000);
    expect(avisoDoAmbiente({ HARNESS_TETO_MIN: "40" })).toBe(avisoDoTeto(40 * 60_000));
    expect(avisoDoAmbiente({ HARNESS_TETO_MIN: "40", HARNESS_AVISO_PRAZO_MS: "60000" })).toBe(60_000);
  });
});
