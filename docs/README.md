# docs/ — índice

| Pasta | O que tem | Quem lê |
|---|---|---|
| [`context/`](context/README.md) | A camada semântica e os schemas: `bridges.yaml`, `metrics.yaml`, `hierarchies.yaml`, `schemas.json`, `rodado-schema.json`. Quase tudo é gerado; o README diz a fonte de cada arquivo | `mcp_server.py`, `harness/`, os scripts de regen — **não mover arquivos daqui sem mudar o código** |
| [`mapa/`](mapa/) | Mapas **gerados** do espelho: [`ERD.md`](mapa/ERD.md) / [`ERD_EN.md`](mapa/ERD_EN.md) (`gera_erd.py`), [`Flow.md`](mapa/Flow.md) e [`Temas.md`](mapa/Temas.md) (`gera_flow.py`), [`catalog.md`](mapa/catalog.md) (`gera_catalog_md.py`), e [`overview/`](mapa/overview/), os resumos por tema que alimentam o `Temas.md` | Pessoas; regenerar, nunca editar à mão |
| [`tecnico/`](tecnico/) | Engenharia: [`TECHNICAL.md`](tecnico/TECHNICAL.md) (ambiente, setup do MCP, ordem do regen), [`housekeeping.md`](tecnico/housekeeping.md), [`gemma_stats.md`](tecnico/gemma_stats.md) (benchmark do modelo local). As ferramentas do MCP estão em [`mcp/MCP.md`](../mcp/MCP.md), junto do servidor | Pessoas |
| [`pesquisa/`](pesquisa/) | Perguntas e resultados: [`hipoteses/`](pesquisa/hipoteses/) (o banco de perguntas e respostas que vira os casos do harness), [`relatorio-social/`](pesquisa/relatorio-social/), [`censo/`](pesquisa/censo/), [`queries/`](pesquisa/queries/) (SQL de exemplo e auditoria de CNAE), [`viz-uf/`](pesquisa/viz-uf/), [`nova-friburgo/`](pesquisa/nova-friburgo/) (os dois levantamentos que estavam soltos na raiz como `relatorio*.md`), [`notas/`](pesquisa/notas/) e [`deanonimizacao.md`](pesquisa/deanonimizacao.md) | Pessoas; `hipoteses/` e `relatorio-social/` também por `harness/casos.ts` |

Reorganizado em 2026-09-24: o que estava solto em `docs/` e na raiz do repo foi
agrupado nestas quatro pastas. Os caminhos antigos seguem no histórico
(`git log --follow -- docs/mapa/ERD.md`).
