# done/ask_web.md — app web local de pergunta em pt-BR: retirado

Concluído (retirado de circulação) em 2026-08-24. Branch `ask-web`, 20 commits,
preservada em `origin/ask-web` — worktree e branch local removidos, histórico
completo recuperável com `git fetch && git worktree add ../rodado-ask-web
origin/ask-web`.

## O que era

Substituto da TUI Rust: app local (`localhost:8090`) onde o navegador faz
embedding (transformers.js) **e** geração de SQL (WebLLM/WebGPU) — sem chave de
API, sem servidor de LLM. O servidor Bun só executava SQL via `ssh beelink`,
com o mesmo firewall read-only do `mcp_server.py` (`web/src/sqlguard.ts`).

## Por que foi retirado

Não por ter falhado — por ficar **redundante**. A mesma pergunta que o
pipeline levava minutos e 2 tentativas de reparo pra tentar responder (às
vezes errando), o MCP (`mcp__rodado__*`, ou seja, este `mcp_server.py`
conversando com qualquer assistente que já fale MCP) resolve em segundos,
porque pode **iterar**: buscar, olhar o resultado, perceber que a fonte não
serve, buscar de novo, verificar com SQL de verdade. O ask-web fazia UMA busca
por embedding e UMA geração (2 reparos cegos, sem poder reconsiderar a
escolha de tabela).

Testado ao vivo em 2026-08-24 contra as duas perguntas que tinham falhado a
noite inteira no ask-web (3B **e** 7B): as duas resolvidas de primeira via MCP,
com causa raiz encontrada em cada uma (não só contornada):
- "preço médio da gasolina por estado 2024" — o `SISTEMA` do ask-web tinha uma
  regra fixa ("valores em minúscula") que é **falsa** pro ANP: os valores são
  maiúsculos (`'GASOLINA COMUM'`). Achado com uma `SELECT DISTINCT`, não
  adivinhado.
- "5 estados com mais homicídios, Atlas da Violência" — `br_ipea_atlasviolencia`
  só tem 2 tabelas no espelho (`series`, `valores_nacional`), NENHUMA por UF.
  Não é o modelo errando, é a pergunta pedindo um corte que a fonte não tem
  aqui. Os dois modelos locais alucinaram um join pra uma tabela errada
  (`br_fbsp_absp.uf`) tentando forçar resposta; `resolve_join` mostrou na hora
  que não há ponte documentada porque não precisa de join nenhum.

Pra quem já tem acesso a um assistente que fala MCP, ask-web nunca vai competir
com isso. O caso de uso que sobra — alguém SEM esse acesso, um link que
funciona sem conta em lugar nenhum — não era o uso real que o projeto estava
dando a ele.

## O que vale preservar (não morreu com a branch)

A camada semântica (`docs/context/bridges.yaml`, `metrics.yaml`,
`hierarchies.yaml`) não era do ask-web — já alimentava (e continua
alimentando) `resolve_join`, `get_metric`, `rollup` do próprio
`mcp_server.py`. Nada se perde aí.

Os três conjuntos dourados continuam no `origin/ask-web` em `tasks/`
(`ask_web_douradas.json` — 15 perguntas de 1 tabela; `douradas_multi.json` —
50 de pesquisa, 2+ tabelas; `douradas_temas.json` — 220 por tema) e são
material de teste reaproveitável pra qualquer coisa que precise de perguntas
douradas contra o acervo, MCP incluído.

## O achado que sobrevive e importa de verdade

**`mcp_server.py:search_tables` usa `docs/context/table_embeddings.json`
diretamente** — o MESMO índice que a investigação de 2026-08-23 mediu quebrado
(recall@5 de 1/15; texto indexado é sopa de nome de coluna com tipo, cosseno
0,0755 contra 0,3905 de prosa curta). O fix que resolveu isso pro ask-web
(índice doc2query — 6.562 perguntas sintéticas, um vetor por pergunta,
agregação por MÁXIMO — subiu recall pra 11/15) **nunca foi portado pro MCP**
que é a ferramenta usada de verdade.

Confirmado ao vivo em 2026-08-24 com perguntas complexas reais (não
hipotéticas — as mesmas do conjunto `douradas_multi`):
- `search_tables("IDEB indicadores de qualidade educacional por município")`
  não acha `br_inep_ideb.municipio` no top-5 — nem o acrônimo "IDEB" bate.
- `search_tables("remuneração de professores, despesas municipais com
  educação")` devolve **zero** resultados (limiar 0,35) e, afrouxando pra 0,1,
  o melhor achado é uma tabela do TCE-PI errada — `br_me_siconfi.
  municipio_despesas_funcao` (a certa) não aparece em lugar nenhum do ranking.
- `search_tables("taxa de fecundidade adolescente por raça, nascidos vivos")`
  não acha `br_ms_sinasc.microdados` — SINASC = **Sistema de Informações
  sobre Nascidos Vivos**, o termo literal está na pergunta e no nome do
  sistema, e mesmo assim não bate.

**Próximo passo real, registrado aqui pra não se perder**: portar
`search_tables` pra usar o índice doc2query (`web/static/index/perguntas.json`
no `origin/ask-web`, ou regenerar via `scripts/doc2query_*.ts` — 824/824
tabelas cobertas) no lugar de `table_embeddings.json`, com a mesma agregação
por máximo que `embed.js:scoresDoc2Query` já usa. Maior alavanca única
encontrada nesta investigação inteira, porque atinge a ferramenta em uso
diário, não um protótipo.
