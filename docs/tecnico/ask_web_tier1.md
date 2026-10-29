# ask-web: resolução de métrica por frase (Tier 1)

A TUI Rust `ask`, que resolvia métrica por frase ("Tier 1"), foi removida
(`ask/` apagado em `58ab7c7`, 2026-08-23). A mesma lógica sobrevive
reimplementada em JS — `resolverMetrica()` em `web/static/prompt.js` —, parte
do app web `ask-web` que vive só no branch local `ask-web` (sem cópia no
remoto, não mesclado em `main`, sem worktree). Ela resolve métrica **antes**
da seleção por embedding, por match exato de nome ou sinônimo — nunca por
similaridade, porque "população de SP" e "população carcerária" ficam perto
no espaço vetorial e querem tabelas diferentes.

**Isto não é `mcp_server.py`**: o `get_metric()` do MCP é um lookup direto sem
parser de frase (confirmado em `mcp/MCP.md`) — não faz longest-match sobre uma
pergunta em texto livre, não tem Tier 2/3.

Três detalhes do Tier 1 que custaram trabalho na versão Rust e não devem ser
redescobertos:

1. O match é por nome **ou sinônimo**, exato, depois de normalizar acento e
   caixa, e **o mais longo vence** — sem isso "pib per capita" resolve como
   "pib".
2. O Tier 1 roda **antes** do embedding. Depois dele economiza a chamada ao
   modelo mas ainda paga o embedding inteiro (~18s → 0,00s).
3. Cai para o modelo quando sobra **qualquer** termo não explicado na
   pergunta. "população por município em 2022" tem que cair: responder o
   agregado nacional a uma pergunta sobre municípios é errado e silencioso.
