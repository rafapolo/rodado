import { expect, test, describe } from "bun:test";
import { carregaTodasPerguntas, exemplosIndependentes } from "./casos.ts";

// regras.md, "Tarefas — travar o que ainda é só disciplina", item 2: o few-shot
// tem que vir de fora do conjunto de teste. Já aconteceu uma vez — metade das
// perguntas ia para o prefixo e a outra metade "media" contra memória, não
// contra recuperação. `exemplosIndependentes()` lê docs/relatorio-social/, que
// não alimenta `carregaTodasPerguntas()` (docs/perguntas.md); este teste trava
// essa separação diretamente, pelo conteúdo, não pelo caminho do arquivo — assim
// pega o erro mesmo que alguém troque a fonte por engano.
describe("exemplosIndependentes — fonte tem que ser independente do teste", () => {
  test("não fica vazio (senão o few-shot da avaliação silenciosamente vira zero)", () => {
    expect(exemplosIndependentes().length).toBeGreaterThan(0);
  });

  test("nenhuma pergunta do few-shot aparece no conjunto de teste", () => {
    const teste = new Set(carregaTodasPerguntas().map((c) => c.pergunta.trim()));
    const vazando = exemplosIndependentes()
      .map((e) => e.pergunta.trim())
      .filter((p) => teste.has(p));
    expect(vazando).toEqual([]);
  });
});
