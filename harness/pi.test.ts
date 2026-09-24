import { describe, expect, test } from "bun:test";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { comandoPi } from "./pi.ts";

/**
 * Trava a superfície do laço (harness_tasks.md O4, antes em patch.test.ts para
 * o dsh). Com shell, o Gemma consultou o DuckDB por fora do portão em
 * 2026-09-02; com o CLAUDE.md injetado, 89% do prompt era instrução para outro
 * agente. Nenhuma das duas falhas dá erro — por isso o teste.
 */
describe("pi.ts — superfície do laço", () => {
  const { cmd, env } = comandoPi("pergunta de teste", "http://127.0.0.1:1/v1");
  const agente = env.PI_CODING_AGENT_DIR!;
  const le = (arq: string) => JSON.parse(readFileSync(join(agente, arq), "utf8"));

  test("sem ferramenta embutida, sem arquivo de contexto, sem extensão descoberta", () => {
    for (const f of ["--no-builtin-tools", "--no-context-files", "--no-skills", "--no-extensions", "--offline", "--print"]) {
      expect(cmd).toContain(f);
    }
    // a única extensão é o adapter MCP, carregada explicitamente
    expect(cmd[cmd.indexOf("-e") + 1]).toEndWith("node_modules/pi-mcp-adapter");
  });

  test("o único caminho até o dado é o mcp.ts, com as ferramentas diretas e sem proxy", () => {
    const mcp = le("mcp.json");
    expect(Object.keys(mcp.mcpServers)).toEqual(["rodado"]);
    expect(mcp.mcpServers.rodado.args).toEqual(["harness/mcp.ts"]);
    expect(mcp.settings.directTools).toBe(true);
    expect(mcp.settings.disableProxyTool).toBe(true);
    expect(mcp.settings.allowInstall).toBe(false);
    expect(mcp.settings.hostConfigDiscovery).toBe("off");
  });

  test("modelo não-raciocinante pela guarda, sem compactar nem aquecer cache no slot único", () => {
    const provider = le("models.json").providers["beelink-local"];
    expect(provider.baseUrl).toBe("http://127.0.0.1:1/v1");
    expect(provider.models[0].reasoning).toBe(false);
    const settings = le("settings.json");
    expect(settings.compaction.enabled).toBe(false);
    expect(settings.cacheWarming).toBe("off");
  });

  test("a persona é o system prompt", () => {
    expect(cmd[cmd.indexOf("--system-prompt") + 1]).toEndWith("harness/persona.md");
  });
});
