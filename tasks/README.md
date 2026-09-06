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
| [`datasets_to_scrap.md`](datasets_to_scrap.md) | O que está **na fila** de coleta e por que ainda não entrou (`blocked`, `deferred-api_key`) | 🟢 ativo — rodada de 2026-09-02 fechou ANVISA agrotóxicos/alimentos, CGU sanções, SEDEC desastres, Senado dados abertos, BNDES/CGU pessoal executivo/SICONFI (gap fechado) e 3/8 tabelas novas do SICAR; resolvidos vivem em [`done/datasets_to_scrap_done.md`](done/datasets_to_scrap_done.md); resta o que é genuinamente travado — BCB câmbio/Selic (access denied confirmado na origem), `br_bcb_ifdata.relatorio` e `br_sfb_sicar.app` (acima do teto seguro de 10M linhas por pull), 4 tabelas do SICAR com coluna `GEOGRAPHY` batendo num limite de tamanho da API REST do BigQuery |
| [`fontes_novas.md`](fontes_novas.md) | O que existe de dado público **fora** do espelho, rankeado por valor/esforço | 🔵 backlog — Gás do Povo (20.817.231 linhas), Novo Bolsa Família (821.346.847, 41/41 meses) e Transferegov/SICONV (62 tabelas, 69.060.758 linhas — os 5 zips multi-membro pendentes foram recuperados como 14 tabelas novas) **têm view no `.duckdb` e `count(*)` conferido**; PNCP subiu de 1.412.466 para 1.979.024 linhas e parou sozinho ("fonte esgotada", rate limit) — job já estava rodando de novo (`multi.sh`, 8 faixas) quando esta rodada checou, não foi preciso reiniciar. **Segunda rodada** fechou mais 6 datasets (~155M linhas): CNEFE (111.102.875 endereços, ponte CEP↔setor censitário↔`id_municipio`), BCB SCR.data (43.061.984, 169 meses), INPE DETER (686.136 alertas de desmatamento via endpoint AJAX não documentado), Tesouro CAUC (5.674, 3 tabelas), BCB Desenrola (12.751), DIRPF fundos habilitados (6.471). **PNCP fechou** em 5.043.371 contratos (`br_pncp.contratos`, ver `47824d1`). **Rodada de 2026-09-04** fechou mais 3: **BCB Pix por município** (item 4, era tido como "endpoint quebrado" — era falso negativo, sintaxe OData errada; 395.447 linhas, 71 meses, 5.571 municípios), **DIRPF repasses FDCA/FDI** (item 18, achou a fonte real de valores por fundo, não só a lista de habilitados; 28.885 linhas, 2022-2023 — 2013-2021 só em PDF, não convertido), **PRODES acumulado** (item 17, 7.598.548 linhas, 7 biomas, mesma decisão de shape do DETER — centroide, não WKT). **Depois fechados também**: INEA PDFs (achado um pool de proxy BR — `br_inea_boletim.atos_pdf`, 7.052 linhas) e ANEEL (`br_aneel_dadosabertos.empreendimento_geracao_distribuida`, 4.692.466 linhas), destravados pelo mesmo pool. CadÚnico ficou parcial (portal novo achado, API de valores não decifrada). O buraco de metadados do Querido Diário (out/2025→hoje) segue **bloqueado por causa real, não geo-IP** — a própria API (`api.queridodiario.ok.org.br`) tem falha de TLS handshake nos dois lados, sinal de outage real da fonte. Revalidação inicial de todo o backlog `blocked`/`blocked → mcp-todo` de `datasets_to_scrap.md` (Tier 1a/1b/1c + ANEEL/ANTT/CadÚnico/CNJ) sem proxy real disponível: nenhum destravou nessa passada — mas um pool de proxy BR foi achado logo depois (ver linha própria acima) e já destravou INEA e ANEEL; vale reter contra o resto do backlog. Catálogo regenerado, agora **1.029 tabelas, 233 datasets, 39,25 bi linhas**. **Procedência corrigida 2026-09-02/04**: todos os datasets raspados fora do espelho oficial têm linha em `done/datasets_to_scrap_done.md` com a fonte real documentada — `source_name` reflete a fonte real, não o default `Base dos Dados`/mirror. Bloqueados com motivo confirmado, não credencial: CNJ Painel (dashboard QlikView instável, não API simples), PNS 2023 (IBGE ainda não publicou); TCEs estaduais e SPU SIAPA ficam de fora por esforço (11 portais distintos / sem endpoint público) |
| [`espelho_subutilizado.md`](espelho_subutilizado.md) | O que **já está** no espelho e nada consome — nenhuma pergunta, nenhuma seção de dashboard, nenhum relatório | 🔵 inventário — mapa de saúde mental fechado (partes I e III; parte II segue aberta, depende do repo `xyz`), tema 57 (CVM) e tema 58 (programas sociais CGU: pé-de-meia, garantia-safra, seguro-defeso, viagens) fechados; achou e documentou uma ponte SIH↔SIM (`bridges.yaml`) que não existia; reverificou `br_ibama_embargos_novo` (113.878 linhas, já não está quebrado); ~9 grupos do Balde C da Parte I seguem sem tocar |
| [`respostas_pendentes.md`](respostas_pendentes.md) | Que perguntas do golden set ainda faltam responder — e que bugs aparecem ao responder | 🟡 em andamento — golden set em 193 perguntas (era 185), recall@10 dataset-level 54,9% (161/293), estável; achou sentinela `capital_social=999999999999.0` em 124 empresas e uma coluna `modalidade` não documentada em `br_inep_formacao_docente.uf` que infla `GROUP BY` sem filtro (>600%), ambos logados no arquivo; ~58 itens ⏳ restam, maioria já com bloqueio estrutural catalogado ("Bloqueios mapeados") |

## `plan/` — planos abertos, ainda não executados

| Arquivo | O quê |
|---|---|
| [`plan/generate-full-schema-dict.md`](plan/generate-full-schema-dict.md) | Varredura em estágios pra achar colunas-código sem significado documentado em lugar nenhum (hoje só ~45 de ~230 datasets têm decode, via `dicionario_coverage.json`) — motivado pelo achado de `circunstancia_obito` (item 9 de `harness/tasks/backlog.md`), que subcontava suicídio sem nenhum alerta existir. 🟡 estágios 1+2 rodados 2026-09-03, mais uma passada de leitura humana/LLM (não regex) — `docs/context/schema_dict_status.json` etiqueta 28.263 colunas, **8.690 `nao_verificado`** (era 17.164 antes da leitura); `describe_table` já expõe o aviso. Estágios 3 (priorizar por uso real) e 4 (pesquisa manual, o que sobrou — PIRLS/TIMSS/PNS/censo 2022) seguem abertos |
| [`plan/automatizar_atualizacao_fontes.md`](plan/automatizar_atualizacao_fontes.md) | Usar `source_url` (já existe no catálogo) + `dataset_freshness.yaml` (novo, 6 entradas) pra automatizar a checagem de gap contra a fonte viva — não a correção. 🔴 nada executado ainda; plano explicitamente recomenda Fase 1 (só checar e reportar em `tasks/`) antes de cogitar re-scrape automático, dados os bugs reais achados na sessão que motivou isto (proxy caindo, CRLF corrompendo URL silenciosamente, um `max()` de string vs. data que deu resultado errado) |
| [`plan/gotchas_por_dataset.md`](plan/gotchas_por_dataset.md) | Um `.yml` de armadilhas por dataset (233 possíveis, escritos só onde há medição), entregue como quinto bloco do `describe_table` — sem ferramenta nova. Motivado por medição desta sessão: o Gemma 4 chamou `describe_table` 5/5 e ainda assim contou suicídio por `circunstancia_obito` (749 contra 789), porque a coluna que **motivou** o `nao_verificado_warning` hoje aparece em `dicionario_coverage` — sinal positivo. As 4 classes de aviso existentes são estruturais; esta armadilha é semântica. 🔴 nada implementado — Fase 0 é o teste que decide (tirar o hardcode do prompt e ver se o mecanismo sustenta o 789); Fase 2 exige grupo de controle em datasets sem gotcha, única coisa que separa mecanismo de memorização |

Não são tarefas, são insumos:

| Arquivo | O que é |
|---|---|
| [`douradas_perguntas.json`](douradas_perguntas.json) | Golden set dataset-level (63 temas × ~5) — ⚙️ **gerado**, regenerar com `build_douradas_perguntas.py` depois de cada resposta nova em `docs/hipoteses/respostas.md` |
| [`hipoteses.md`](hipoteses.md) | Banco de hipóteses: quanto do espaço de cruzamento é válido (2.002 trincas de família, 4,6% cobertas), a fila H01–H19 e como rodar `scripts/hipoteses_overnight.sh` offline. **H01–H19 rodaram em 2026-09-06: 6 ✅ · 6 ❌ · 3 ◐ · 4 ⏳** — resultado em `docs/hipoteses/respostas.md`, sobreviventes como F1–F7 em `docs/hipoteses/achados_fortes.md`; a corrida derrubou o D1 e o E1. **Bloco I (H41–H45, renumerado de H20–H24 por colisão de nome)** fechou em 2026-09-06: **5 ✅ · 0 ◐ · 0 ⏳** — H44c e H45 entraram em `docs/hipoteses/achados_fortes.md` como I1/I2 (renomeado de H1/H2 — colidia com os nomes das hipóteses H01–H03); provenance do fechamento em [`done/bloco_i_pendencias.md`](done/bloco_i_pendencias.md). **§5 (2026-09-06)**: fila H20–H40 gerada por subtração explícita (`familias.yaml` + `moldes.yaml` + `cobertura_municipal.json`, via `scripts/hipoteses/93_inedito.py`, sessão `dataset-coverage-discovery`); **H20–H36 rodadas** (5 ✅ · 4 ❌ · 3 ◐ · 1 ⏳ → achados G1–G7, incl. o SNIS auto-declarado a +0,63 e os 3 IPTUs intraurbanos); fila H41–H62 aberta; **H46–H62 rodadas** (todas as 17: 5 ✅ · 9 ❌ · 3 ◐ → achados J1–J5, incl. gado/ha × desmatamento +0,49, que supera o F3, e a medida direta do viés de notificação); 1.383 de 1.771 combinações ainda inéditas |
| [`doc2query/`](doc2query/) | Os 39 lotes brutos da geração doc2query (`lote_*.jsonl`, `saida_*.jsonl`) — insumo de `gera_doc2query_corpus.py` |

## Em aberto — sem arquivo próprio

Fios que sobraram da sessão de raspagem ambiental de 2026-09-01/02 e não
pertencem a nenhum dos seis acima. Cada item é acionável sozinho.

### Coleta

| O quê | Estado | O que falta |
|---|---|---|
| **8 páginas do PNCP irrecuperáveis** | Servidor não entrega nem após 5 tentativas | Registrar como buraco conhecido, não insistir |
| **INEA anterior a 2019** | Índice do Boletim de Serviço começa em 28/01/2019. Acervo velho está em `portalproderj.inea.rj.gov.br` | Retestar com o proxy BR achado (linha abaixo) — não tentado ainda, escopo original era só 2019+ |
| **Proxy BR encontrado — destrava toda a classe de fontes geo-bloqueadas** | ✅ **2026-09-04**: pool de 5 proxies SOCKS4 residenciais gratuitos, de `raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/countries/BR/data.txt` (melhor hit-rate que proxyscrape/geonode nesta tentativa): `177.68.149.141:1080`, `45.70.188.10:4153`, `177.66.43.189:4145`, `187.87.35.148:4153`, `131.0.245.82:60606`. Instáveis individualmente (caem e voltam), mas com rotação/failover sustentaram ~1,2GB de download (1.079 PDFs do INEA + 106MB do ANEEL) sem intervenção manual. **Também destravou ANEEL** (`br_aneel_dadosabertos.empreendimento_geracao_distribuida`, 4.692.466 linhas — o CKAN estava vivo, só o TCP não completava de fora do BR) | Retestar contra o resto do backlog `blocked`/`blocked → mcp-todo` de `datasets_to_scrap.md` que era geo-IP e não WAF de aplicação: CadÚnico (achou o portal novo, `aplicacoes.cidadania.gov.br/vis/data3`, mas a API de valores reais não foi mapeada — SPA em duas chamadas, a segunda não decifrada), TCE-CE/PE/RN/RS (timeout total, nunca testado com IP BR real), possivelmente STF/TST/DOU (WAF pode ou não ser geo). Lista de proxy é efêmera — se todos os 5 caírem, buscar de novo na mesma fonte |
| **Buraco de metadados do Querido Diário (out/2025→hoje)** | **Bloqueado, confirmado 2026-09-04** — não é geo-bloqueio: `api.queridodiario.ok.org.br` falha com TLS handshake em toda requisição, testado do laptop **e** do beelink (IP BR), site principal (sem `api.`) responde normal. Parece outage/má-configuração real do lado da fonte, diferente de quando o scraper foi escrito (2026-07-10). O texto completo já indexado (`br_ok_queridodiario_texto/diarios`, 231.897 edições, 524 municípios, 14GB) **já estava 100% feito** por outra sessão, achado ao revisitar o item | Reteste mais tarde — se a API voltar, `scripts/scrap/querido_diario.py --since 2025-10-01 --until hoje` fecha o buraco |
| **Qualidade do ar (2ª metade)** | SEEG fechou a parte de emissão estimada | Rede de monitoramento do INEA não raspada; segue sem confirmar se Nova Friburgo tem estação |

### Descoberta e documentação

| O quê | Estado |
|---|---|
| **Índice doc2query** | ⏸️ **parado a pedido em 2026-09-02** com 23 de 63 tabelas geradas (`doc2query/saida_0{1,2}.jsonl`, resumível com `--faltantes`). Nada foi aplicado ao índice: as 63 tabelas novas seguem **invisíveis para `search_tables`**, embora apareçam em `list_tables`/`describe_table` — quem procurar "licenciamento ambiental" não acha o INEA. Gerador: **Gemma 4 local** (`scripts/doc2query_gemma.py`, `llama-server` na porta 8099 do beelink) — o `opencode/hy3-free` que o `doc2query_roda.py` usa passou a devolver `UnknownError` em toda chamada. Uma tabela por chamada (contexto menor, JSON mais confiável, falha custa uma tabela e não 25). Depois: `gera_doc2query_corpus.py` → `gera_doc2query_index.py`. O corpus cobre 832 tabelas; o espelho tem 1.029 |
| **`douradas_multi.json` não existe** | `CLAUDE.md` cita o golden set table-level (`scripts/build_douradas_multi.py`, gerado de `docs/relatorio-social/perguntas.md`), mas o arquivo não está em `tasks/` — rodar o gerador ou remover a referência do `CLAUDE.md` |

## `done/` — arquivado (provenance, não é to-do)

| Arquivo | Descrição | Concluído em |
|---|---|---|
| [`bloco_i_pendencias.md`](done/bloco_i_pendencias.md) | As 4 pendências do Bloco I (`tasks/hipoteses.md`, H41–H45): interação por quintil de HHI (H41), variável nova em `INTENSIVAS` (H42b), teste de grupo em numpy puro (H43), checagem de magnitude (H44c/H45) — fechou 5 de 5 ✅, sem SQL nova | 2026-09-06 |
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
