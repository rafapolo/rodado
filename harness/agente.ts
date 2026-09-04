/**
 * O laço agêntico — substitui o `dsh` (`@deepseek-ai/dsh`), removido.
 *
 * `dsh` era um CLI agêntico completo (system prompt, sessão, cliente MCP,
 * parser de tool-call) usado como camada entre o Gemma 4 local (beelink) e o
 * servidor MCP do projeto (`mcp.ts`) — um processo `dsh` novo por pergunta,
 * via `bunx dsh --profile headless --patch harness/dsh/rodado.patch.yml`.
 *
 * Achado ao trocar: `dsh` já usava `@earendil-works/pi-ai` por baixo, como
 * plugin de LLM (`@deepseek-ai/dsh-llm-pi-ai`). `pi-ai` é biblioteca de
 * chamada de modelo unificada — sem CLI, sem sessão, sem cliente MCP embutido
 * — então este arquivo é o laço inteiro escrito à mão sobre ela, no mesmo
 * processo Bun: monta o contexto (persona + ferramentas do MCP), chama o
 * modelo, executa a ferramenta que ele pedir via um cliente MCP próprio
 * falando com `bun harness/mcp.ts` por stdio, devolve o resultado, repete.
 *
 * O que isso ganha sobre o `dsh`: o laço só conhece as 7 ferramentas do
 * `mcp-rodado` — não existe `bash`/`fs`/`web`/`subagent` para desligar à mão
 * num patch (ver `regras.md` — o Gemma descobriu `bash` uma vez e consultou
 * o DuckDB por cima do portão inteiro). Aqui essas ferramentas simplesmente
 * não existem: o laço não tem acesso a nenhuma API além da que o cliente MCP
 * expõe.
 */
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import {
  createModels, createProvider, Type,
  type Context, type Model, type Tool,
} from "@earendil-works/pi-ai";
import { openAICompletionsApi } from "@earendil-works/pi-ai/api/openai-completions.lazy";

const RAIZ = new URL("..", import.meta.url).pathname;

/**
 * Persona — texto portado byte-a-byte de `dsh/rodado.patch.yml`
 * (`system-prompt.config.persona`, removido). Cada frase aqui corrigiu um
 * bug medido, não é estilo: "nunca pare num plano" veio de `regras.md`
 * ("o modelo às vezes para num plano pedindo aprovação"); "cite o ÓRGÃO,
 * nunca a tabela" é `backlog.md` item 3, reforçado por `revisar_resposta`
 * (`checaCitacaoTabela`, `portao.ts`) do lado da ferramenta. Não reformular
 * sem repetir a medição que motivou a frase original.
 */
export const PERSONA = `Você apura dados públicos brasileiros pelo espelho do projeto rodado,
usando as ferramentas do servidor MCP "rodado". Você opera sozinho, sem
humano disponível para aprovar passos — NUNCA pare a resposta num plano
de investigação esperando confirmação ("aguardando aprovação",
"próximo passo: executar..."). Execute as consultas direto, uma após a
outra, até ter o número final; um plano sem execução não é resposta.
Escreva a resposta final em português, citando o ÓRGÃO de origem do
dado (ex.: Ministério da Saúde/SIM, IBGE, RAIS/CAGED do Ministério do
Trabalho) — NUNCA o nome da tabela, do dataset ou o SQL usado. Antes de
responder ao usuário, chame a ferramenta revisar_resposta com o
parágrafo pronto; só entregue a resposta depois que ela aprovar.`;

/**
 * Modelo e provider — portados de `dsh/rodado.patch.yml` (`llm-pi-ai`,
 * `agent-default-model`). O `llama-server` não autentica e ignora o valor —
 * mas `api/openai-completions.js` do `pi-ai` (`getClientApiKey`) EXIGE uma
 * `apiKey` truthy antes de montar a requisição, mesmo para provider keyless;
 * o exemplo Ollama da doc (`resolve: async () => ({ auth: {} })`) não
 * sobrevive a essa checagem — testado ao vivo, `auth: {}` derruba com
 * "No API key for provider". Uma string-placebo resolve, sem a
 * chave-fantasma `HARNESS_LLM_KEY` que o plugin do `dsh` exigia só como
 * referência de env var.
 */
const BASE_URL = `${Bun.env.HARNESS_LLM ?? "http://127.0.0.1:8099"}/v1`;

export const MODELO: Model<"openai-completions"> = {
  id: "gemma-4-26B-A4B-it-qat",
  name: "Gemma 4 26B-A4B q4_0 QAT",
  api: "openai-completions",
  provider: "beelink-local",
  baseUrl: BASE_URL,
  // `false` declara um modelo NÃO-raciocinante — nenhum parâmetro de thinking
  // vai na requisição. O desligamento de verdade é do lado do SERVIDOR
  // (`llama-server --chat-template-kwargs '{"enable_thinking":false}'`, já
  // no ar no beelink): nenhuma config do lado do cliente muda o llama.cpp —
  // medido com o `dsh` (`operacao.md`, "Raciocínio: o que resolve e o que só
  // parece resolver"), e a mesma restrição vale aqui.
  reasoning: false,
  input: ["text"],
  cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
  // llama-server sobe com -c 32768; o modelo suporta 262k, mas o KV a 262k
  // não cabe junto do mirror na mesma máquina.
  contextWindow: 32768,
  maxTokens: 4096,
  // `openai-completions` autodetecta compat por baseUrl para uma lista fixa
  // de providers conhecidos (Cerebras, xAI, DeepSeek...); um `llama-server`
  // em localhost não bate em nenhum, então os defaults (pensados para a API
  // da OpenAI de verdade) não servem — mesma classe de ajuste que a doc do
  // `pi-ai` recomenda para Ollama/vLLM/SGLang. `modelo.ts` (usado por
  // `laco.ts`, chamada HTTP crua) já manda `max_tokens` e `role: "system"`
  // pro mesmo servidor — os valores abaixo replicam isso pelo lado do pi-ai.
  compat: {
    supportsDeveloperRole: false,
    supportsReasoningEffort: false,
    supportsStore: false,
    supportsStrictMode: false,
    maxTokensField: "max_tokens",
  },
};

function criaModelos() {
  const models = createModels();
  models.setProvider(createProvider({
    id: "beelink-local",
    name: "Gemma 4 26B-A4B (beelink)",
    baseUrl: BASE_URL,
    auth: { apiKey: { name: "llama.cpp", resolve: async () => ({ auth: { apiKey: "unused" } }) } },
    models: [MODELO],
    api: openAICompletionsApi(),
  }));
  return models;
}

/** MCP `Tool.inputSchema` (JSON Schema cru) → `Tool` do pi-ai (TypeBox). */
export function converteFerramentas(
  mcpTools: { name: string; description?: string; inputSchema: unknown }[],
): Tool[] {
  return mcpTools.map((t) => ({
    name: t.name,
    description: t.description ?? "",
    parameters: Type.Unsafe(t.inputSchema as object),
  }));
}

export interface ResultadoAgente {
  resposta: string;
  turnos: number;
  /** true quando o laço parou por esgotar turnos ou tempo, não por resposta final */
  interrompido?: boolean;
}

/**
 * Uma pergunta, do início ao fim: sobe um cliente MCP falando com
 * `bun harness/mcp.ts` (um processo novo, ciclo de vida = uma pergunta —
 * mesma invariante que `mcp.ts:41-58` já documenta para seus Maps de
 * estado), monta o contexto e roda o laço até ter resposta final ou até
 * bater um dos dois limites de segurança abaixo.
 *
 * `dsh` dava esses dois limites de graça, como framework de agente
 * genérico; aqui, escrevendo o laço à mão, precisam existir explicitamente:
 * `HARNESS_MAX_TURNOS` (turnos de modelo) e `HARNESS_TIMEOUT_MS` (relógio de
 * parede da sessão inteira — mesmo nome de env var que `pergunte.ts` já lia
 * para o timeout do processo `dsh`).
 */
export async function roda(
  pergunta: string,
  opts: { log?: (s: string) => void } = {},
): Promise<ResultadoAgente> {
  const log = opts.log ?? (() => {});
  const maxTurnos = Number(Bun.env.HARNESS_MAX_TURNOS ?? 40);
  const timeoutMs = Number(Bun.env.HARNESS_TIMEOUT_MS ?? 2_400_000);
  const t0 = Date.now();

  const models = criaModelos();
  const client = new Client({ name: "harness-agente", version: "1.0.0" });
  // `StdioClientTransport` por padrão só herda uma lista curta de env vars
  // "seguras" (`getDefaultEnvironment()`) — sem PATH/HOME o `ssh` que
  // `beelink.ts` dispara dentro de `mcp.ts` não roda. Env completo, mais
  // `BEELINK_HOST` explícito (mesmo valor que `dsh/rodado.patch.yml` fixava).
  const transport = new StdioClientTransport({
    command: "bun",
    args: ["harness/mcp.ts"],
    cwd: RAIZ,
    env: { ...process.env, BEELINK_HOST: Bun.env.BEELINK_HOST ?? "beelink" } as Record<string, string>,
  });

  await client.connect(transport);
  try {
    const { tools: mcpTools } = await client.listTools();
    const tools = converteFerramentas(mcpTools);

    const context: Context = {
      systemPrompt: PERSONA,
      messages: [{ role: "user", content: pergunta, timestamp: Date.now() }],
      tools,
    };

    for (let turno = 0; turno < maxTurnos; turno++) {
      if (Date.now() - t0 > timeoutMs) {
        return { resposta: "", turnos: turno, interrompido: true };
      }

      const s = models.stream(MODELO, context, {
        signal: AbortSignal.timeout(Math.max(1000, timeoutMs - (Date.now() - t0))),
      });
      for await (const ev of s) {
        if (ev.type === "text_delta") log(ev.delta);
      }
      const msg = await s.result();
      context.messages.push(msg);

      const chamadas = msg.content.filter((b) => b.type === "toolCall");
      if (!chamadas.length) {
        const resposta = msg.content
          .filter((b) => b.type === "text")
          .map((b) => b.text)
          .join("");
        return { resposta, turnos: turno + 1 };
      }

      for (const chamada of chamadas) {
        log(`\n[ferramenta] ${chamada.name}(${JSON.stringify(chamada.arguments)})\n`);
        const r = await client.callTool({ name: chamada.name, arguments: chamada.arguments });
        const conteudo = Array.isArray(r.content) ? r.content : [];
        const texto = conteudo
          .filter((c): c is { type: "text"; text: string } => c.type === "text")
          .map((c) => c.text)
          .join("\n");
        context.messages.push({
          role: "toolResult",
          toolCallId: chamada.id,
          toolName: chamada.name,
          content: [{ type: "text", text: texto }],
          isError: !!r.isError,
          timestamp: Date.now(),
        });
      }
    }
    return { resposta: "", turnos: maxTurnos, interrompido: true };
  } finally {
    await client.close();
  }
}
