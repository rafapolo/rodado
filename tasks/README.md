# tasks/ — índice

`tasks/` é versionado (voltou ao controle de versão em 2026-09-02, depois de
ter sido tirado em `7a5fe32`). Duas áreas: arquivos ativos aqui na raiz e
`done/` (arquivado — mantido por provenance, não é lista de afazeres).

Tarefas específicas do subsistema `harness/` (o apurador local com Gemma 4 —
plano, medições, catálogo de refino, avaliação de modelo candidato) vivem em
[`harness/tasks/`](../harness/tasks/README.md), não aqui — aqui fica o que é
do projeto como um todo (datasets, raspagem, camada semântica, o espelho).

## Ativos

Ordenados por atividade recente (mtime + commits), não por tema — o que está
sendo trabalhado agora fica no topo.

| Arquivo | Descrição | Status |
|---|---|---|
| [`datasets_quase_duplicados.md`](datasets_quase_duplicados.md) | Datasets quase-duplicados no espelho (item 2 do TODO do harness) — `br_ibama_embargos` vazio é o mais urgente | 🔴 diagnosticado, ação pendente — survey de 2026-09-01, nada removido/mapeado ainda |
| [`datasets_licenciamento_ambiental.md`](datasets_licenciamento_ambiental.md) | Datasets de licenciamento e poluição ambiental (saído do relatório de Nova Friburgo) | 🟡 6 de 8 raspados 2026-09-01 (ANM, IBAMA CTF/autos/embargos, INEA, Querido Diário) — ver *Em aberto* abaixo |
| [`relatorio_saude_mental.md`](relatorio_saude_mental.md) | Mapa do que o espelho tem para um relatório de saúde mental — ainda não é o relatório | 🔵 aberto — levantamento 2026-09-01 |
| [`municipio_dashboard_datasets_pendentes.md`](municipio_dashboard_datasets_pendentes.md) | 53 datasets com coluna de município que o dashboard `dataviz/municipio` (repo `xyz`) ainda não usa | 🔵 aberto — levantamento 2026-08-28, triado em baldes |
| [`bugs_e_achados_agentes.md`](bugs_e_achados_agentes.md) | Log da rodada de 5 agentes paralelos (2026-08-27): bugs e achados cruzados | 🟡 em andamento — 1 agente caiu por rate limit, progresso mesclado |
| [`deanonimizacao_geral.md`](deanonimizacao_geral.md) | Nomear quem só aparece como CNPJ/CPF no espelho, via join com cadastros | 🟡 parcial — baldes 1 (CNPJ) e 2 (CPF) feitos, resto aberto |
| [`datasets_coverage_gaps.md`](datasets_coverage_gaps.md) | Os 111 (de 197) datasets do espelho que nenhuma pergunta em `docs/perguntas.md` nunca tocou | 🟡 em andamento — 1ª rodada: 7/10 respondidas, 3 bloqueadas |
| [`respostas_pendentes.md`](respostas_pendentes.md) | O que falta responder no golden set `douradas_perguntas.json` (continuação de `done/mcp_search_refino.md`) | 🟡 em andamento |
| [`ana_series_historicas.md`](ana_series_historicas.md) | Séries históricas da ANA (vazão/cota) — o que falta além do ETL e da página `series.html` | 🟡 parcial — ETL/análise feitos 2026-08-10, itens residuais abertos |
| [`datasets_gap_analysis.md`](datasets_gap_analysis.md) | Fontes públicas *fora* do espelho, candidatas a ETL, rankeadas por valor/esforço | 🔵 backlog — vários itens bloqueados por credencial/API |
| [`todo.md`](todo.md) | Threads abertas pós-finalização do scraping (2026-07-14) | 🟡 1 de 2 resolvida — Atlas da Violência ✅; Consumidor.gov.br bloqueado em login gov.br |
| [`datasets_to_scrap.md`](datasets_to_scrap.md) | Board de status do scraping autônomo — só o que ainda é acionável (`blocked`, `blocked → mcp-todo`) | 🟢 ativo — resolvidos vivem em `done/datasets_to_scrap_done.md` |
| [`minc_salic_import.md`](minc_salic_import.md) | Import do SALIC/Lei Rouanet (MinC), trazido do repo `../Mostre` | ✅ feito (parcial) — 2026-08-25 |
| [`douradas_perguntas.json`](douradas_perguntas.json) | Golden set dataset-level (43 temas × 5) gerado de `docs/perguntas.md`+`docs/respostas.md`, mede `search_tables` | ⚙️ gerado — regenerar via `build_douradas_perguntas.py` após resposta nova |

## Em aberto — deixado pela sessão de 2026-09-01/02

O que ficou pela metade quando a sessão de raspagem ambiental terminou. Cada
item é acionável sozinho; nenhum depende dos outros.

### Coleta

| O quê | Estado | O que falta |
|---|---|---|
| **PNCP: endpoint escondido `/api/search`** | Descoberto 2026-09-02 no bundle Angular do portal (`pncp.gov.br/app/main.*.js`, chave `searchURL`). Responde em **1,4s** com **57 campos** por contrato (a API pública leva 30–120s e dá 41 campos), e traz `municipio_id`, `esfera_nome`, `poder_nome` que a pública não tem. Exige header `Referer: https://pncp.gov.br/app/contratos` e `status` obrigatório (`todos`). **Não serve para ETL**: teto duro de 10.000 resultados (`pagina × tam_pagina ≤ 10000`, o limite do Elasticsearch — o próprio portal assume em `qtdDocumentsToShow: 9990`), e os únicos filtros que fatiam são `anos` e `ufs`, insuficientes (RJ/2025 sozinho tem 61.241). **Ótimo para consulta pontual**, péssimo para colheita. Atenção: em teste, `anos=2024` e `anos=2025` devolveram o mesmo total — o filtro parece ser ignorado às vezes, então não confiar no `total` sem conferir contra a API oficial |
| **PNCP mai/2025 → hoje** | 1.412.466 contratos em `br_pncp.contratos` (2021–2026); faltam ~85 janelas de 5 dias | O `HTTP 500` da API é **rate limit por IP** — confirmado por um `429` explícito. Paralelizar do mesmo IP não adianta (todos dividem a cota); o proxy BR tem cota própria e devolve 200 onde o direto dá 500. `_staging/pncp/duplo.sh` roda as duas rotas, ~20h. Retomar: `nohup bash ~/rodado/_staging/pncp/duplo.sh &` — ele pula por `stat` o que já existe |
| **INEA anterior a 2019** | Índice do Boletim de Serviço começa em 28/01/2019 | Acervo velho está em `portalproderj.inea.rj.gov.br`, que não respondeu nem pelo proxy BR. Pode estar desativado |
| **PDFs dos 1.081 boletins do INEA** | Só o índice foi colhido | É neles que estão **validade e condicionantes** da licença — dois campos que o relatório de Nova Friburgo pedia e o índice não traz |
| **Qualidade do ar (item 8, 2ª metade)** | SEEG fechou a parte de emissão estimada | Rede de monitoramento do INEA não raspada; segue sem confirmar se Nova Friburgo tem estação |
| **8 páginas do PNCP irrecuperáveis** | Servidor não entrega nem após 5 tentativas | Registrar como buraco conhecido, não insistir |

### Higiene do espelho

| O quê | Por que urge |
|---|---|
| **Remover `br_ibama_embargos`** | 113.878 linhas com **zero** não-vazias — o CSV foi parseado errado e os bytes nunca foram gravados. Quem consulta recebe zero e acha que é resposta. Substituto pronto: `br_ibama_embargos_novo` (892.279 linhas, 2001–2026). Ver [`datasets_quase_duplicados.md`](datasets_quase_duplicados.md) |
| **Remover `br_seeg`** | Raspei 12,1M linhas da API GraphQL **antes de conferir** que `br_seeg_emissoes.municipio` já existia com 165,7M linhas e mais granular. Conferido idêntico onde se sobrepõem (Nova Friburgo 2024: 345.342 tCO2e nos dois) |
| **`valorGlobal` do PNCP tem outlier absurdo** | 54 contratos (0,008%) somam **88% do total de 2024**: uma empresa de ônibus com "R$ 481 bilhões". Sem filtro, qualquer soma mente por fator de 8. Mediana real: R$ 2.800 |

### Descoberta e documentação

| O quê | Estado |
|---|---|
| **Índice doc2query** | 🔄 em geração 2026-09-02 pelo **Gemma 4 local** (`scripts/doc2query_gemma.py`, `llama-server` na porta 8099 do beelink) — o `opencode/hy3-free` que o `doc2query_roda.py` usa passou a devolver `UnknownError: Unexpected server error` em toda chamada. 63 tabelas a gerar, uma por chamada (contexto menor, JSON mais confiável, falha custa uma tabela e não 25). Depois: `gera_doc2query_corpus.py` → `gera_doc2query_index.py`. Cobria 832 tabelas; o espelho tem 909. As **45 tabelas novas não são encontráveis por `search_tables`** — quem procurar "licenciamento ambiental" não acha o INEA. Regenerar o embedding é barato (`scripts/gera_doc2query_index.py`), mas o corpus precisa da passada LLM, que é cara |
| **`tasks/` é gitignored** | As 7 entradas de procedência que escrevi em `done/datasets_to_scrap_done.md` vivem só nesta máquina. Se o beelink for reinstalado, `build_metadata_catalog.py` perde a procedência das fontes novas |
| **`harness/prefixo.ts` sem versionar** | Apareceu depois do commit `070d69b`, não incluído por não saber se está pronto |

## `done/` — arquivado (provenance, não é to-do)

| Arquivo | Descrição | Concluído em |
|---|---|---|
| [`ana_series_etl.md`](done/ana_series_etl.md) | ETL do zip da ANA + análise de tendência ("rios morrendo") | 2026-08-09 |
| [`ana_series_historicas.md`](done/ana_series_historicas.md) | Download/extração do zip único da série histórica ANA | (insumo do item acima) |
| [`ask_web.md`](done/ask_web.md) | App web local de pergunta em pt-BR — retirado de circulação, preservado em `origin/ask-web` | 2026-08-24 |
| [`datasets_to_scrap_done.md`](done/datasets_to_scrap_done.md) | Linhas resolvidas/fechadas splitadas de `tasks/datasets_to_scrap.md` (provenance) | 2026-08-24 (split) |
| [`mcp_search_refino.md`](done/mcp_search_refino.md) | Achados da investigação ask-web aplicados ao `mcp_server.py` (índice doc2query, `dicionario_coverage`) | 2026-08-24 |
| [`sync_censo.md`](done/sync_censo.md) | Mirror completo do FTP do IBGE para beelink | ✅ (resumível, concluído) |
| [`sync_cpf.md`](done/sync_cpf.md) | Completar CPFs mascarados em 15 tabelas via `pessoas.parquet` | ✅ |
| [`ducklake.plan`](done/ducklake.plan) | Avaliação de migração para DuckLake | ❌ arquivado, não adotado |
| [`normalization.plan`](done/normalization.plan) | Consolidar 52.281 parquets do IBGE FTP (1/UF) em datasets com `_uf` | ✅ v4 em produção — 2026-07-27 |
| [`semantica.plan`](done/semantica.plan) | Camada semântica: `bridges.yaml` + `metrics.yaml` + `hierarchies.yaml` | ✅ executado — 2026-08-22 |

## Nota

`CLAUDE.md` cita `tasks/douradas_multi.json` (golden set table-level, gerado por
`scripts/build_douradas_multi.py` a partir de `docs/relatorio-social/perguntas.md`) —
o arquivo não existe hoje em `tasks/`; rodar o script gerador ou remover a referência.
