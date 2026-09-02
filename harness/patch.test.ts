import { expect, test, describe } from "bun:test";

const RAIZ = new URL(".", import.meta.url).pathname;
const PATCH = `${RAIZ}dsh/rodado.patch.yml`;

// operacao.md, "Tarefas", item 4: travar a superfície de ferramenta. O corte de
// 14.213 → 6.849 tokens de system prompt (regras.md) veio de desligar as
// ferramentas que este harness não usa — e uma delas (`bash`) não era peso, era
// BURACO NO PORTÃO: o modelo descobriu a ferramenta e consultou o DuckDB por
// cima do `consultar`, sem nenhuma camada de validação. Nenhuma das entradas
// abaixo pode voltar a `disabled: false` (ou sumir do patch) sem que isso seja
// deliberado — este teste é o que torna a mudança visível no diff em vez de
// silenciosa.
//
// Fecha quando (do backlog): reabilitar `bash` no patch quebra este teste.
const DESLIGADAS = [
  "tool-bash", "tool-pwsh", "tool-fs", "tool-fs-search",
  "tool-str-replace-editor", "tool-web", "tool-subagent",
  "tool-subagent-fork", "tool-subagent-control", "tool-subagent-list-agents",
  "tool-subagent-report", "tool-skill", "skill-filesystem", "skill-badge",
  "tool-workflow", "tool-jobs", "tool-ralph", "tool-todo", "tool-goal",
];

interface Entrada { id?: string; disabled?: boolean; insert?: unknown }

async function carregaPatch(): Promise<Entrada[]> {
  const txt = await Bun.file(PATCH).text();
  return Bun.YAML.parse(txt) as Entrada[];
}

describe("rodado.patch.yml — a superfície de ferramenta fica travada", () => {
  test("bash, fs e as demais ferramentas de contorno seguem desligadas", async () => {
    const entradas = await carregaPatch();
    const porId = new Map(entradas.filter((e) => e.id).map((e) => [e.id, e]));
    for (const id of DESLIGADAS) {
      expect(porId.has(id)).toBe(true);
      expect(porId.get(id)?.disabled).toBe(true);
    }
  });

  test("a ferramenta MCP do próprio harness (mcp-rodado) não está nessa lista", async () => {
    // Ela é o caminho pelo portão — desligá-la por engano junto das outras
    // tiraria a única forma de o modelo consultar o espelho.
    const entradas = await carregaPatch();
    const insert = entradas.find((e) => e.insert) as { insert?: { id?: string }[] } | undefined;
    const ids = (insert?.insert ?? []).map((e) => e.id);
    expect(ids).toContain("mcp-rodado");
  });
});
