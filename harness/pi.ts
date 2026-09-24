/**
 * O laço agêntico do harness: o Pi (`@earendil-works/pi-coding-agent`).
 *
 * Substituiu o dsh em 2026-09-24 (README.md, "O laço: o Pi"): nas 28 primeiras
 * diretas, 27/28 com média de 55 s, contra 28/28 e 64 s do dsh na rodada 7 — o
 * único erro foi o modelo copiar errado um número que a consulta devolveu certo.
 * Mesmo llama-server, mesma guarda, mesma persona, mesmo harness/mcp.ts; mudou
 * só o laço, e com ele sumiram o patch do dsh e o teste que o travava.
 *
 * O Pi não tem MCP nativo. As 4 ferramentas chegam por `pi-mcp-adapter` com
 * `directTools: true` (uma ferramenta Pi por ferramenta MCP) e o proxy `mcp`
 * escondido. `--no-builtin-tools` tira `bash`/`read`/`edit`/`write`: com shell
 * o Gemma consulta o DuckDB por fora do portão (tasks/operacao.md).
 *
 * O diretório de agente é montado do zero a cada pergunta, num tmp: nada do
 * ~/.pi do usuário (extensões, AGENTS.md, credenciais) entra no prompt, e a URL
 * da guarda muda a cada processo. Conferido contra um servidor falso em
 * 2026-09-24: system prompt e ferramentas saem iguais byte a byte entre
 * perguntas diferentes, então o cache de prefixo vive.
 */
import { mkdtempSync, writeFileSync, mkdirSync } from "node:fs";
import { homedir, tmpdir } from "node:os";
import { join } from "node:path";

const RAIZ = new URL("..", import.meta.url).pathname;
const PERSONA = join(RAIZ, Bun.env.HARNESS_PERSONA ?? "harness/persona.md");
/** Fixo, fora do repo: `sessao.ts` lê daqui. Um .jsonl por pergunta. */
export const SESSOES = join(homedir(), ".rodado-harness", "sessoes");

/** Modelo, ajustes e servidor MCP, na forma de configuração do Pi. */
function montaAgente(llmUrl: string): string {
  const dir = mkdtempSync(join(tmpdir(), "pi-rodado-"));
  writeFileSync(join(dir, "models.json"), JSON.stringify({
    providers: {
      "beelink-local": {
        baseUrl: llmUrl,
        api: "openai-completions",
        // o llama-server ignora; o Pi só lista modelo com credencial resolvida
        apiKey: "nao-usada",
        models: [{
          id: "gemma-4-26B-A4B-it-qat",
          name: "Gemma 4 26B-A4B q4_0 QAT",
          // thinking ligado custou 28x (2026-09-01): 1.200 tokens e 94,8 s sem SQL nenhuma
          reasoning: false,
          input: ["text"],
          // llama-server sobe com -c 32768; o modelo suporta 262k, mas o KV a
          // 262k não cabe junto do mirror na mesma máquina
          contextWindow: 32768,
          maxTokens: 4096,
          cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
        }],
      },
    },
  }, null, 2));
  writeFileSync(join(dir, "settings.json"), JSON.stringify({
    defaultProvider: "beelink-local",
    defaultModel: "gemma-4-26B-A4B-it-qat",
    defaultThinkingLevel: "off",
    quietStartup: true,
    // requisição extra no mesmo slot único (-np 1)
    cacheWarming: "off",
    // reserveTokens 16384 num contexto de 32768 compactaria na metade
    compaction: { enabled: false },
    // prefill frio de ~16k a ~50 t/s passa de 5 min sem byte nenhum
    httpIdleTimeoutMs: 0,
    enableInstallTelemetry: false,
    defaultProjectTrust: "never",
  }, null, 2));
  writeFileSync(join(dir, "mcp.json"), JSON.stringify({
    settings: {
      directTools: true,
      disableProxyTool: true,
      namespaceProxyTools: false,
      scriptMode: false,
      exposeResources: false,
      allowInstall: false,
      toolPrefix: "none",
      notifyOnStartupConnect: false,
      hostConfigDiscovery: "off",
      // a consulta pesada no beelink passa fácil do default do SDK (60 s)
      requestTimeoutMs: 1_800_000,
      // tabelaTexto já corta; a guarda do adapter cortaria de novo
      outputGuard: false,
    },
    mcpServers: {
      rodado: {
        command: "bun",
        args: ["harness/mcp.ts"],
        cwd: RAIZ,
        env: { BEELINK_HOST: Bun.env.BEELINK_HOST ?? "beelink" },
        lifecycle: "eager",
        directTools: true,
      },
    },
  }, null, 2));
  return dir;
}

/** Comando e ambiente para um `Bun.spawn` com cwd na raiz do repo. */
export function comandoPi(pergunta: string, llmUrl: string) {
  const agente = montaAgente(llmUrl);
  mkdirSync(SESSOES, { recursive: true });
  return {
    cmd: [
      join(RAIZ, "node_modules/.bin/pi"),
      "--print",
      "--offline",
      "--no-builtin-tools",
      "--no-context-files",
      "--no-skills",
      "--no-prompt-templates",
      "--no-extensions",
      "-e", join(RAIZ, "node_modules/pi-mcp-adapter"),
      "--system-prompt", PERSONA,
      "--session-dir", SESSOES,
      "--", pergunta,
    ],
    env: { ...process.env, PI_CODING_AGENT_DIR: agente, HARNESS_PERGUNTA: pergunta },
  };
}
