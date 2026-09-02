# tasks/ — índice

`tasks/` é versionado (voltou ao controle de versão em 2026-09-02, depois de
ter sido tirado em `7a5fe32`). Duas áreas: arquivos ativos aqui na raiz e
`done/` (arquivado — mantido por provenance, não é lista de afazeres).

Tarefas específicas do subsistema `harness/` (o apurador local com Gemma 4 —
plano, medições, catálogo de refino, avaliação de modelo candidato) vivem em
[`harness/tasks/`](../harness/tasks/README.md), não aqui — aqui fica o que é
do projeto como um todo (datasets, raspagem, camada semântica, o espelho).

> **Reorganizado em 2026-09-02.** Eram 15 arquivos ativos, hoje são 6. Cinco
> foram fundidos em dois arquivos de grupo (`fontes_novas.md`,
> `espelho_subutilizado.md`) e quatro foram para `done/` com os fios ainda
> vivos roteados para quem é dono deles. O mapa da mudança está no fim.

## Ativos

Quatro arquivos, cada um com uma pergunta própria. A regra que separa os três
primeiros: **onde o dado está**.

| Arquivo | A pergunta que ele responde | Status |
|---|---|---|
| [`datasets_to_scrap.md`](datasets_to_scrap.md) | O que está **na fila** de coleta e por que ainda não entrou (`blocked`, `deferred-api_key`) | 🟢 ativo — resolvidos vivem em [`done/datasets_to_scrap_done.md`](done/datasets_to_scrap_done.md) |
| [`fontes_novas.md`](fontes_novas.md) | O que existe de dado público **fora** do espelho, rankeado por valor/esforço | 🔵 backlog — varredura geral (2026-08-23) + mergulho em licenciamento ambiental (2026-09-01); vários itens presos em credencial/API |
| [`espelho_subutilizado.md`](espelho_subutilizado.md) | O que **já está** no espelho e nada consome — nenhuma pergunta, nenhuma seção de dashboard, nenhum relatório | 🔵 inventário — 111 datasets sem pergunta, 53 sem uso no dashboard, + o mapa de saúde mental |
| [`respostas_pendentes.md`](respostas_pendentes.md) | Que perguntas do golden set ainda faltam responder — e que bugs aparecem ao responder | 🟡 em andamento — inclui o backlog herdado do Agente A |

Não são tarefas, são insumos:

| Arquivo | O que é |
|---|---|
| [`douradas_perguntas.json`](douradas_perguntas.json) | Golden set dataset-level (43 temas × 5) — ⚙️ **gerado**, regenerar com `build_douradas_perguntas.py` depois de cada resposta nova em `docs/respostas.md` |
| [`doc2query/`](doc2query/) | Os 39 lotes brutos da geração doc2query (`lote_*.jsonl`, `saida_*.jsonl`) — insumo de `gera_doc2query_corpus.py` |

## Em aberto — sem arquivo próprio

Fios que sobraram da sessão de raspagem ambiental de 2026-09-01/02 e não
pertencem a nenhum dos seis acima. Cada item é acionável sozinho.

### Coleta

| O quê | Estado | O que falta |
|---|---|---|
| **PNCP mai/2025 → hoje** | 1.412.466 contratos em `br_pncp.contratos` (2021–2026); faltam ~85 janelas de 5 dias | O `HTTP 500` da API é **rate limit por IP** — confirmado por um `429` explícito. Paralelizar do mesmo IP não adianta (todos dividem a cota); o proxy BR tem cota própria e devolve 200 onde o direto dá 500. `_staging/pncp/duplo.sh` roda as duas rotas, ~20h. Retomar: `nohup bash ~/rodado/_staging/pncp/duplo.sh &` — ele pula por `stat` o que já existe |
| **PNCP: endpoint escondido `/api/search`** | Descoberto 2026-09-02 no bundle Angular do portal (`pncp.gov.br/app/main.*.js`, chave `searchURL`). Responde em **1,4s** com **57 campos** por contrato (a API pública leva 30–120s e dá 41), e traz `municipio_id`, `esfera_nome`, `poder_nome` que a pública não tem. Exige header `Referer: https://pncp.gov.br/app/contratos` e `status=todos` | **Não serve para ETL**: teto duro de 10.000 resultados (`pagina × tam_pagina ≤ 10000`, limite do Elasticsearch — o próprio portal assume em `qtdDocumentsToShow: 9990`), e os únicos filtros que fatiam são `anos` e `ufs`, insuficientes (RJ/2025 sozinho tem 61.241). **Ótimo para consulta pontual, péssimo para colheita.** Atenção: em teste, `anos=2024` e `anos=2025` devolveram o mesmo total — o filtro parece ser ignorado às vezes, não confiar no `total` sem conferir contra a API oficial |
| **8 páginas do PNCP irrecuperáveis** | Servidor não entrega nem após 5 tentativas | Registrar como buraco conhecido, não insistir |
| **PDFs dos 1.081 boletins do INEA** | Só o índice foi colhido | É neles que estão **validade e condicionantes** da licença — dois campos que o relatório de Nova Friburgo pedia e o índice não traz |
| **INEA anterior a 2019** | Índice do Boletim de Serviço começa em 28/01/2019 | Acervo velho está em `portalproderj.inea.rj.gov.br`, que não respondeu nem pelo proxy BR. Pode estar desativado |
| **Qualidade do ar (2ª metade)** | SEEG fechou a parte de emissão estimada | Rede de monitoramento do INEA não raspada; segue sem confirmar se Nova Friburgo tem estação |

### Descoberta e documentação

| O quê | Estado |
|---|---|
| **Índice doc2query** | ⏸️ **parado a pedido em 2026-09-02** com 23 de 63 tabelas geradas (`doc2query/saida_0{1,2}.jsonl`, resumível com `--faltantes`). Nada foi aplicado ao índice: as 63 tabelas novas seguem **invisíveis para `search_tables`**, embora apareçam em `list_tables`/`describe_table` — quem procurar "licenciamento ambiental" não acha o INEA. Gerador: **Gemma 4 local** (`scripts/doc2query_gemma.py`, `llama-server` na porta 8099 do beelink) — o `opencode/hy3-free` que o `doc2query_roda.py` usa passou a devolver `UnknownError` em toda chamada. Uma tabela por chamada (contexto menor, JSON mais confiável, falha custa uma tabela e não 25). Depois: `gera_doc2query_corpus.py` → `gera_doc2query_index.py`. O corpus cobre 832 tabelas; o espelho tem 909 |
| **`douradas_multi.json` não existe** | `CLAUDE.md` cita o golden set table-level (`scripts/build_douradas_multi.py`, gerado de `docs/relatorio-social/perguntas.md`), mas o arquivo não está em `tasks/` — rodar o gerador ou remover a referência do `CLAUDE.md` |

## `done/` — arquivado (provenance, não é to-do)

| Arquivo | Descrição | Concluído em |
|---|---|---|
| [`deanonimizacao_geral.md`](done/deanonimizacao_geral.md) | Quem no espelho só aparece como CNPJ/CPF e dá pra nomear — baldes 1 (CNPJ) e 2 (CPF) feitos e reconferidos ao vivo no beelink. **Arquivado com 1 decisão de privacidade ainda em aberto** (CNES `tipo_pessoa='1'`, ver o topo do arquivo para as opções a/b/c) — arquivar não a resolveu, só tirou o arquivo da lista ativa a pedido | 2026-09-02 |
| [`ana_series_historicas_pendencias.md`](done/ana_series_historicas_pendencias.md) | O item que ficava aberto em `ana_series_historicas.md` — gap da COTA fechado: `series_cota_mensal_completa` criada no beelink (1.807.220 linhas, 7.197 estações, 1900-01 a 2026-05). Causa raiz não era falta de coleta — o script de merge no beelink estava desatualizado e nunca recebeu a flag `--tipo` | 2026-09-02 |
| [`threads_pos_scraping_2026-07.md`](done/threads_pos_scraping_2026-07.md) | Era `todo.md` — as 3 threads pós-scraping: `_run_sql_ssh` órfão, Atlas da Violência (152/152), pesquisa completa do bloqueio do Consumidor.gov.br | 2026-09-02 |
| [`bugs_e_achados_agentes.md`](done/bugs_e_achados_agentes.md) | Log da rodada de 5 agentes paralelos: 5 bugs confirmados (já em `bridges.yaml`) + o que cada agente entregou | 2026-09-02 |
| [`higiene_espelho.md`](done/higiene_espelho.md) | Duplicatas/dado zerado no espelho (`br_ibama_embargos`, `br_seeg`) + outlier do PNCP + nota ANP — 4 de 4 | 2026-09-02 |
| [`datasets_quase_duplicados.md`](done/datasets_quase_duplicados.md) | O survey que originou o `higiene_espelho.md` — método e contagens brutas | 2026-09-02 |
| [`minc_salic_import.md`](done/minc_salic_import.md) | Import do SALIC/Lei Rouanet (MinC), trazido do repo `../Mostre` | 2026-08-25 |
| [`datasets_to_scrap_done.md`](done/datasets_to_scrap_done.md) | Linhas resolvidas/fechadas splitadas de `datasets_to_scrap.md` (provenance) | 2026-08-24 (split) |
| [`mcp_search_refino.md`](done/mcp_search_refino.md) | Achados da investigação ask-web aplicados ao `mcp_server.py` (índice doc2query, `dicionario_coverage`) | 2026-08-24 |
| [`ask_web.md`](done/ask_web.md) | App web local de pergunta em pt-BR — retirado de circulação, preservado em `origin/ask-web` | 2026-08-24 |
| [`ana_series_etl.md`](done/ana_series_etl.md) | ETL do zip da ANA + análise de tendência ("rios morrendo") | 2026-08-09 |
| [`ana_series_historicas.md`](done/ana_series_historicas.md) | Download/extração do zip único da série histórica ANA | (insumo do item acima) |
| [`sync_censo.md`](done/sync_censo.md) | Mirror completo do FTP do IBGE para beelink | ✅ (resumível, concluído) |
| [`sync_cpf.md`](done/sync_cpf.md) | Completar CPFs mascarados em 15 tabelas via `pessoas.parquet` | ✅ |
| [`semantica.plan`](done/semantica.plan) | Camada semântica: `bridges.yaml` + `metrics.yaml` + `hierarchies.yaml` | ✅ executado — 2026-08-22 |
| [`normalization.plan`](done/normalization.plan) | Consolidar 52.281 parquets do IBGE FTP (1/UF) em datasets com `_uf` | ✅ v4 em produção — 2026-07-27 |
| [`ducklake.plan`](done/ducklake.plan) | Avaliação de migração para DuckLake | ❌ arquivado, não adotado |

## O que mudou em 2026-09-02

**Fusões** — cinco arquivos viraram dois, sem perda de conteúdo:

| Novo | Absorveu | Por que é uma coisa só |
|---|---|---|
| `fontes_novas.md` | `datasets_gap_analysis.md` + `datasets_licenciamento_ambiental.md` | Os dois rankeiam fonte pública **fora** do espelho como candidata a ETL; licenciamento era o mergulho temático da mesma pergunta |
| `espelho_subutilizado.md` | `datasets_coverage_gaps.md` + `municipio_dashboard_datasets_pendentes.md` + `relatorio_saude_mental.md` | Os três inventariam dado **já espelhado** que nada consome — muda só quem é o consumidor ausente (pergunta, dashboard, relatório) |

**Arquivamentos** — com os fios vivos roteados antes de mover, não descartados:

| Saiu | Fio que ainda respirava | Foi para |
|---|---|---|
| `todo.md` | Consumidor.gov.br travado em login gov.br | `datasets_to_scrap.md`, seção *Deferred* (é credencial pessoal, não infra quebrada) |
| `bugs_e_achados_agentes.md` | Backlog do Agente A (T37-2/3/4 + temas não tocados) | `respostas_pendentes.md` |
| `bugs_e_achados_agentes.md` | Decisão de privacidade do CNES `tipo_pessoa='1'` | `deanonimizacao_geral.md` |
| `datasets_quase_duplicados.md` | — (itens 1-4 executados em `higiene_espelho.md`; 5-6 sem ação por decisão) | nada pendente |
| `minc_salic_import.md` | — (feito em 2026-08-25) | nada pendente |
