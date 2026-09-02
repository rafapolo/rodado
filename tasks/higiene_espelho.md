# Higiene do espelho — duplicatas, dado zerado e outlier

Plano consolidado a partir de duas fontes que cobriam o mesmo problema em
níveis diferentes: a seção **"Higiene do espelho"** de `tasks/README.md`
(3 itens de ação, achados na sessão de raspagem ambiental 2026-09-01/02) e o
levantamento completo de **[`datasets_quase_duplicados.md`](datasets_quase_duplicados.md)**
(item 2 do TODO do harness, survey de 2026-09-01 — nada removido/mapeado
ainda). Junto num plano só porque os 3 itens acionáveis do README **são** os
dois primeiros diagnósticos deste survey mais o outlier do PNCP; sem juntar,
o mesmo "remover `br_ibama_embargos`" ficava documentado em dois lugares com
risco de divergir.

`datasets_quase_duplicados.md` continua existindo como o levantamento
original (método, contagens brutas, itens 3-6 de prioridade média/baixa que
não viram ação aqui) — este arquivo é o plano de execução dos itens que
**têm** ação clara e pendente.

## Ação imediata — dado incorreto sendo servido silenciosamente

### 1. Remover `br_ibama_embargos` (substituído por `br_ibama_embargos_novo`)

**Por quê é o mais urgente dos três**: não é uma duplicata redundante, é uma
tabela **vazia que não parece vazia**. `br_ibama_embargos` tem
113.878 linhas em `termo_embargo` (e as outras 7 subtabelas do dataset) com
`max(length(qualquer_coluna)) = 0` — bug de parsing no scraping original que
zerou os bytes. Uma pergunta contra ela roda sem erro e devolve zero linhas,
que parece "não há embargo" quando na verdade há — só que na tabela errada.
Já documentado no próprio `provenance_notes` de `br_ibama_embargos_novo`, mas
`br_ibama_embargos` continua com `status='done'` em `_rodado_metadata`, não
`blocked`/removido.

**Canônico**: `br_ibama_embargos_novo` (892.279 linhas, 2001–2026, 8
subtabelas — mesma forma, contagens iguais ou maiores em cada par: ver
tabela completa em `datasets_quase_duplicados.md` item 1).

Passos:
1. Confirmar no beelink que `br_ibama_embargos_novo` cobre o que
   `br_ibama_embargos` cobria (já conferido no survey — contagens iguais/
   maiores em todas as 8 subtabelas).
2. `ssh beelink 'rm -rf ~/rodado/br_ibama_embargos'` (ver o diretório antes de
   apagar — regra de confirmação tripla para `rm`).
3. `python3 scripts/build_metadata_catalog.py` — recria `_rodado_metadata`/
   `_rodado_datasets` sem a entrada.
4. `python3 scripts/gera_schemas.py && python3 scripts/sync_mcp_schema.py` —
   tira as 8 tabelas do schema que `describe_table`/`search_tables` leem.
5. Checar se `bridges.yaml` ou `docs/overview/` citam `br_ibama_embargos`
   pelo nome antigo; se sim, apontar para `_novo`.
6. Registrar a remoção em `tasks/done/datasets_to_scrap_done.md` (padrão já
   usado para o SEEG, ver item 2).

### 2. Remover `br_seeg` (duplicata redundante de `br_seeg_emissoes`)

`br_seeg.emissoes_municipais` (12.106.780 linhas, raspado da API GraphQL do
SEEG) já está marcado `status = 'redundante — remover'` em
`tasks/done/datasets_to_scrap_done.md` desde 2026-09-01 — o sinalizador já
existe, só falta a remoção física. `br_seeg_emissoes.municipio` (espelho do
Base dos Dados, 165.736.450 linhas, 1970–2024) é mais granular (bioma,
atividade econômica, produto, detalhamento, 4 conversões de gás) e tem
`dicionario` de decode; conferido idêntico onde se sobrepõe (Nova Friburgo
2024: 345.342 tCO2e nos dois).

Passos:
1. `ssh beelink 'rm -rf ~/rodado/br_seeg'`.
2. Mesma sequência de regen do item 1 (`build_metadata_catalog.py` →
   `gera_schemas.py` → `sync_mcp_schema.py`).
3. `tasks/done/datasets_to_scrap_done.md` já tem a nota de lição aprendida
   ("conferir o espelho antes de raspar", ver `[[feedback_conferir_espelho_antes_de_raspar]]`)
   — só atualizar o status de "redundante — remover" para "removido" com
   data.
4. Preservar o mapa da API GraphQL do SEEG que já está documentado ali (útil
   se o Base dos Dados parar de atualizar), mesmo depois de apagar o parquet.

### 3. Filtrar outlier de `valorGlobal` no PNCP

54 contratos (0,008% de `br_pncp.contratos`) somam **88% do valor total de
2024** — uma empresa de ônibus aparece com "R$ 481 bilhões". Mediana real:
R$ 2.800. Qualquer `SUM(valorGlobal)` sem filtro de outlier mente por um
fator de ~8x.

Passos:
1. No beelink, achar o corte real (ex. os 54 contratos por percentil ou por
   um teto de sanidade tipo "maior contrato público conhecido do Brasil").
2. Decidir: excluir na consulta (documentar o filtro em `metrics.yaml` se
   virar uma métrica nomeada, ex. `pncp_valor_total_contratos`) ou marcar as
   linhas com uma flag em vez de apagar — apagar dado de origem pública é
   mais arriscado que uma métrica que já filtra.
3. Se virar métrica: `get_metric()`/`list_metrics()` evita que cada consulta
   futura reintroduza o mesmo erro de 8x (mesmo padrão do
   `[[feedback_check_metrics_before_hand_rolling]]`: `pib_per_capita` existe
   verificado por isso).

## Prioridade média — documentar, não fundir

### 4. `br_anp_combustiveis.precos` × `br_anp_precos_combustiveis.microdados`

Não são duplicata — cobrem janelas diferentes (raspagem própria: 2024-03 a
2026-07, ~7 meses de atraso a menos, mas `cnpj` sem padding e local em texto
livre; espelho BD: 2004 a 2026-02, 22 anos de histórico, `id_municipio`/
`sigla_uf` padronizados). Um modelo escolhendo a tabela errada dá resposta
plausível mas de fonte/período errado, silenciosamente. Ação: nota em
`bridges.yaml` (ou `docs/overview/`) dizendo qual usar para "preço atual" vs
"preço histórico" — mesmo padrão que `false_friends` já documenta. Nenhuma
tabela é removida.

## Prioridade baixa / não verificado — sem ação, só registro

Ficam como estão em `datasets_quase_duplicados.md` (itens 4-6): os 5 pares
`_original` de `br_cgu_beneficios_cidadao` (provavelmente convenção do
próprio Base dos Dados, risco baixo por serem tabelas do mesmo dataset), os
pares `_antigo` de `br_ibge_pib` (hipótese de série metodológica diferente,
não duplicata), e `br_me_rais_identificada` × `br_me_rais` (escopo diferente
por nome). Nenhum tem ação clara — não repetir aqui, só linkar.

## Ordem de execução recomendada

1. Item 1 (`br_ibama_embargos`) — maior risco (zero silencioso), menor
   esforço (remoção já diagnosticada, substituto já rodando).
2. Item 2 (`br_seeg`) — sinalizador já existe, só falta apertar o gatilho.
3. Item 3 (outlier PNCP) — não é remoção de dataset, é filtro de consulta/
   métrica; pode rodar em paralelo aos outros dois.
4. Item 4 — só documentação, sem pressa de dado incorreto em jogo.

Depois de 1 e 2: rodar a cadeia completa de regen do `CLAUDE.md` (`gera_schemas.py`
→ `sync_mcp_schema.py` → `build_metadata_catalog.py` → `gera_join_keys.py` →
`gera_metrics_json.py` → `valida_metrics.py` → `gera_schema_graph.py` →
`build_atlas.py`) — a lista completa já está na seção "Camada semântica" do
`CLAUDE.md`, não repetida aqui.
