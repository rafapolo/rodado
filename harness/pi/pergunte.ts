#!/usr/bin/env bun
/**
 * Uma pergunta pelo Pi no lugar do dsh — tasks/pi_no_lugar_do_dsh.md, passo 1.
 *
 *     bun harness/pi/pergunte.ts "Quantos óbitos por suicídio houve no RJ em 2020?"
 *
 * Gêmeo de harness/pergunte.ts: mesmo llama-server, mesma guarda, mesma persona,
 * mesmo harness/mcp.ts. Muda só o laço agêntico.
 *
 * O Pi não tem MCP nativo. As 4 ferramentas chegam por `pi-mcp-adapter` com
 * `directTools: true` (uma ferramenta Pi por ferramenta MCP, como no dsh) e o
 * proxy `mcp` escondido. `--no-builtin-tools` tira `bash`/`read`/`edit`/`write`:
 * com shell o Gemma consulta o DuckDB por fora do portão (operacao.md).
 *
 * O diretório de agente é montado do zero a cada pergunta, num tmp: nada do
 * ~/.pi do usuário (extensões, AGENTS.md, credenciais) entra no prompt.
 */
import { mkdtempSync, writeFileSync, mkdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { garanteTunel } from "../modelo.ts";
import { sobeGuarda, resumoGuarda } from "../guarda.ts";

const RAIZ = new URL("../..", import.meta.url).pathname;
const PERSONA = join(RAIZ, Bun.env.HARNESS_PERSONA ?? "harness/dsh/persona.md");

const pergunta = Bun.argv.slice(2).join(" ").trim();
if (!pergunta) {
  console.error("uso: bun harness/pi/pergunte.ts \"<pergunta em pt-BR>\"");
  process.exit(1);
}
if (!await garanteTunel()) {
  console.error("llama-server inalcançável em 127.0.0.1:8099 — ver harness/pergunte.ts");
  process.exit(1);
}

const guarda = sobeGuarda();

/** O que o rodado.patch.yml faz no dsh, na forma de configuração do Pi. */
function montaAgente(): string {
  const dir = mkdtempSync(join(tmpdir(), "pi-rodado-"));
  mkdirSync(join(dir, "sessions"));
  writeFileSync(join(dir, "models.json"), JSON.stringify({
    providers: {
      "beelink-local": {
        baseUrl: guarda.url,
        api: "openai-completions",
        // o llama-server ignora; o Pi só lista modelo com credencial resolvida
        apiKey: "nao-usada",
        models: [{
          id: "gemma-4-26B-A4B-it-qat",
          name: "Gemma 4 26B-A4B q4_0 QAT",
          // mesmo motivo do patch do dsh: thinking ligado custou 28x
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
    // requisição extra ao mesmo slot único; o dsh não faz
    cacheWarming: "off",
    // reserveTokens 16384 num contexto de 32768 compactaria na metade — o dsh não compacta
    compaction: { enabled: false },
    // prefill de ~16k a ~50 t/s passa de 5 min sem byte nenhum
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
      // tabelaTexto já corta; a guarda do adapter cortaria de novo, diferente do dsh
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

const agente = montaAgente();
const t0 = Date.now();
const proc = Bun.spawn([
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
  "--session-dir", join(agente, "sessions"),
  "--", pergunta,
], {
  cwd: RAIZ,
  env: { ...process.env, PI_CODING_AGENT_DIR: agente, HARNESS_PERGUNTA: pergunta },
  stdout: "inherit",
  stderr: "inherit",
  timeout: Number(Bun.env.HARNESS_TIMEOUT_MS ?? 2_400_000),
  killSignal: "SIGKILL",
});
const code = await proc.exited;
console.error(`\n[${((Date.now() - t0) / 60000).toFixed(1)} min] ${resumoGuarda(guarda.stats)}`);
console.error(`sessão: ${join(agente, "sessions")}`);
guarda.para();
process.exit(code);
