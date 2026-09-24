/**
 * O Pi como laço agêntico do harness — tasks/pi_no_lugar_do_dsh.md.
 *
 * Mesmo llama-server, mesma guarda, mesma persona, mesmo harness/mcp.ts que o
 * dsh usava. Muda só o laço.
 *
 * O Pi não tem MCP nativo. As 4 ferramentas chegam por `pi-mcp-adapter` com
 * `directTools: true` (uma ferramenta Pi por ferramenta MCP) e o proxy `mcp`
 * escondido. `--no-builtin-tools` tira `bash`/`read`/`edit`/`write`: com shell
 * o Gemma consulta o DuckDB por fora do portão (operacao.md).
 *
 * O diretório de agente é montado do zero a cada pergunta, num tmp: nada do
 * ~/.pi do usuário (extensões, AGENTS.md, credenciais) entra no prompt. Conferido
 * contra um servidor falso em 2026-09-24: system prompt e ferramentas saem
 * iguais byte a byte entre perguntas diferentes, então o cache de prefixo vive.
 */
import { mkdtempSync, writeFileSync, mkdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const RAIZ = new URL("..", import.meta.url).pathname;
const PERSONA = join(RAIZ, Bun.env.HARNESS_PERSONA ?? "harness/dsh/persona.md");

/** O que o rodado.patch.yml fazia no dsh, na forma de configuração do Pi. */
function montaAgente(llmUrl: string): string {
  const dir = mkdtempSync(join(tmpdir(), "pi-rodado-"));
  mkdirSync(join(dir, "sessions"));
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
    // requisição extra no mesmo slot único
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
        env: { BEELINK_HOST: "beelink" },
        lifecycle: "eager",
        directTools: true,
      },
    },
  }, null, 2));
  return dir;
}

/** Comando, ambiente e onde a sessão fica, para um `Bun.spawn` com cwd na raiz. */
export function comandoPi(pergunta: string, llmUrl: string) {
  const agente = montaAgente(llmUrl);
  const sessoes = join(agente, "sessions");
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
      "--session-dir", sessoes,
      "--", pergunta,
    ],
    env: { ...process.env, PI_CODING_AGENT_DIR: agente, HARNESS_PERGUNTA: pergunta },
    sessoes,
  };
}

/**
 * O omp (oh-my-pi, fork do Pi, CLI do Homebrew) — o terceiro lado da comparação.
 *
 * Diferente do Pi, tem MCP nativo: as ferramentas chegam como
 * `mcp__rodado_<nome>`. Três cuidados, conferidos contra um servidor falso em
 * 2026-09-24:
 *  - perfil isolado (`--profile`): o `~/.omp` do usuário não entra;
 *  - cwd neutro (`--cwd`): na raiz do repo o omp injeta o CLAUDE.md inteiro
 *    (+28 mil caracteres, o mesmo desperdício que o dsh tinha) e lê MCP de
 *    `.claude/`; o `mcp.ts` tem cwd próprio no mcp.json, então não depende disso;
 *  - `--no-tools`: tira as embutidas (bash etc.) e deixa as MCP.
 * O que sobra além da persona é um bloco fixo de ~600 caracteres (máquina +
 * três regras "critical" do omp), igual entre perguntas.
 */
const PERFIL_OMP = "rodado-harness";
const CWD_OMP = join(tmpdir(), "omp-rodado");

export function comandoOmp(pergunta: string, llmUrl: string) {
  const agente = join(process.env.HOME!, ".omp", "profiles", PERFIL_OMP, "agent");
  mkdirSync(agente, { recursive: true });
  mkdirSync(CWD_OMP, { recursive: true });
  const sessoes = mkdtempSync(join(tmpdir(), "omp-sessoes-"));
  // YAML à mão: estrutura fixa, sem valor que precise de escape além da URL
  writeFileSync(join(agente, "models.yml"), [
    "providers:",
    "  beelink-local:",
    `    baseUrl: ${llmUrl}`,
    "    api: openai-completions",
    "    auth: none",
    "    models:",
    "      - id: gemma-4-26B-A4B-it-qat",
    "        name: Gemma 4 26B-A4B q4_0 QAT",
    "        contextWindow: 32768",
    "        maxTokens: 4096",
    "        reasoning: false",
    "",
  ].join("\n"));
  writeFileSync(join(agente, "config.yml"), [
    "modelRoles:",
    "  default: beelink-local/gemma-4-26B-A4B-it-qat",
    "compaction:",
    "  enabled: false",
    "advisor:",
    "  enabled: false",
    "",
  ].join("\n"));
  writeFileSync(join(agente, "mcp.json"), JSON.stringify({
    mcpServers: {
      rodado: { command: "bun", args: ["harness/mcp.ts"], cwd: RAIZ, env: { BEELINK_HOST: "beelink" } },
    },
  }, null, 2));
  return {
    cmd: [
      "omp", "--profile", PERFIL_OMP, "--cwd", CWD_OMP, "-p",
      "--no-tools", "--no-lsp", "--no-title", "--no-skills", "--no-rules", "--no-extensions",
      "--thinking", "off",
      "--system-prompt", PERSONA,
      "--session-dir", sessoes,
      pergunta,
    ],
    env: { ...process.env, HARNESS_PERGUNTA: pergunta, OMP_MCP_TIMEOUT_MS: "1800000" },
    sessoes,
  };
}
