# Higiene do espelho — duplicatas, dado zerado e outlier

Plano consolidado a partir de duas fontes que cobriam o mesmo problema em
níveis diferentes: a seção **"Higiene do espelho"** de `tasks/README.md`
(3 itens de ação, achados na sessão de raspagem ambiental 2026-09-01/02) e o
levantamento completo de **[`datasets_quase_duplicados.md`](datasets_quase_duplicados.md)**
(item 2 do TODO do harness, survey de 2026-09-01). Junto num plano só porque
os 3 itens acionáveis do README **são** os dois primeiros diagnósticos deste
survey mais o outlier do PNCP; sem juntar, o mesmo "remover
`br_ibama_embargos`" ficava documentado em dois lugares com risco de
divergir.

**Status em 2026-09-02: os 4 itens estão feitos** (conferido no beelink —
ver cada item abaixo). Arquivado em `done/` por isso.

`datasets_quase_duplicados.md` continua existindo como o levantamento
original (método, contagens brutas, itens 3-6 de prioridade média/baixa que
não viram ação aqui) — este arquivo é o plano de execução dos itens que
**têm** ação clara e pendente.

## Ação imediata — dado incorreto sendo servido silenciosamente

**Itens 1 e 2 já feitos** — conferido no beelink em 2026-09-02: os dois
diretórios não existem mais em `~/rodado/`, foram movidos (não apagados) para
`~/rodado/_obsoleto/` (com `LEIA-ME.md` explicando cada um) e já saíram de
`_rodado_metadata` (regen já rodou). Passos abaixo ficam como registro de
como foi feito, não como pendência.

### 1. ✅ `br_ibama_embargos` removido (substituído por `br_ibama_embargos_novo`)

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

Feito 2026-09-02: movido para `~/rodado/_obsoleto/br_ibama_embargos` (não
apagado — pode ir embora de vez depois de algumas semanas sem quebrar nada).
`~/rodado/_obsoleto/LEIA-ME.md` documenta a lição no lugar do dataset: "era
pior que inútil — consultas contra ele devolviam zero e pareciam resposta.
Foi o que aconteceu no levantamento de Nova Friburgo, que registrou '0
embargos, conferido' quando o município tem 118." `_rodado_metadata` já
conferido sem a entrada — regen já rodou.

Checado 2026-09-02: `bridges.yaml` e `docs/overview/` não citam
`br_ibama_embargos` em nenhum lugar (grep vazio) — nada a apontar para
`_novo`. `tasks/done/datasets_to_scrap_done.md` atualizado para "removido
2026-09-02".

### 2. ✅ `br_seeg` removido (duplicata redundante de `br_seeg_emissoes`)

`br_seeg.emissoes_municipais` (12.106.780 linhas, raspado da API GraphQL do
SEEG) já está marcado `status = 'redundante — remover'` em
`tasks/done/datasets_to_scrap_done.md` desde 2026-09-01 — o sinalizador já
existe, só falta a remoção física. `br_seeg_emissoes.municipio` (espelho do
Base dos Dados, 165.736.450 linhas, 1970–2024) é mais granular (bioma,
atividade econômica, produto, detalhamento, 4 conversões de gás) e tem
`dicionario` de decode; conferido idêntico onde se sobrepõe (Nova Friburgo
2024: 345.342 tCO2e nos dois).

Feito 2026-09-02: movido para `~/rodado/_obsoleto/br_seeg` (não apagado).
`_rodado_metadata` já conferido sem a entrada — regen já rodou. `LEIA-ME.md`
guarda duas armadilhas do substituto que vale saber ao usar
`br_seeg_emissoes`: precisa de `.dicionario` para decodificar valores, e
somar `emissao_ar6` sem filtrar por `gas` **dobra o resultado** (CO2e GWP e
CO2e GTP são linhas separadas contando o mesmo carbono).

`tasks/done/datasets_to_scrap_done.md` atualizado 2026-09-02 para "removido"
com a data.

### 3. ✅ Filtrar outlier de `valorGlobal` no PNCP

54 contratos (0,008% de `br_pncp.contratos`) somam **88% do valor total de
2024** — uma empresa de ônibus aparece com "R$ 481 bilhões". Mediana real:
R$ 2.800. Qualquer `SUM(valorGlobal)` sem filtro de outlier mente por um
fator de ~8x.

Feito 2026-09-02: conferido no beelink que o corte de **R$ 1 bi** reproduz
exatamente o diagnóstico original — 54 contratos em 2024 (88,15% do bruto,
fator ~8,4x). Acima de R$ 50 bi (15 contratos, 2021-2026 inteiro) o erro é
inequívoco por incompatibilidade com o objeto do contrato: um "serviço de
nefrologia" a R$ 1,96 trilhão (maior que o PIB do Brasil) e um valor
sentinela óbvio (R$ 999.999.999.999,999999, fornecedor "P R C DUARTE",
2026). Escolhida a opção de **métrica documentada, não apagar/flag em
linha**: `pncp_valor_total_contratos` em `docs/context/metrics.yaml`
(`SUM(valorGlobal) FILTER (WHERE valorGlobal < 1e9)`), com `verified` e
`caveat` cobrindo o trade-off (alguns contratos legítimos perto de R$ 1 bi,
como pavimentação asfáltica e a Fundação Butantan em 2024, saem do filtro
junto — teto de sanidade, não fronteira exata). `gera_metrics_json.py` e
`valida_metrics.py` já rodaram (0 erros). `get_metric("pncp_valor_total_contratos")`
evita que cada consulta futura reintroduza o erro de 8x (mesmo padrão do
`[[feedback_check_metrics_before_hand_rolling]]`).

## Prioridade média — documentar, não fundir

### 4. ✅ `br_anp_combustiveis.precos` × `br_anp_precos_combustiveis.microdados`

Não são duplicata — cobrem janelas diferentes (raspagem própria: 2024-03 a
2026-07, ~7 meses de atraso a menos, mas `cnpj` sem padding e local em texto
livre; espelho BD: 2004 a 2026-02, 22 anos de histórico, `id_municipio`/
`sigla_uf` padronizados). Um modelo escolhendo a tabela errada dá resposta
plausível mas de fonte/período errado, silenciosamente.

Feito 2026-09-02: nota adicionada em `docs/overview/14_consumo_precos.md`
(não `bridges.yaml` — as únicas seções que `mcp_server.py` lê de lá são
`false_friends`/`coded_differently`/`concept_aliases`, todas chave-de-coluna,
não chave-de-tabela; uma seção nova ali não seria lida por nenhuma
ferramenta MCP, só documentação inerte). A nota traz a tabela comparativa
(origem, período, formato de `cnpj`/local, contagem de linhas) e a regra:
`br_anp_combustiveis.precos` para preço atual/semanal por posto,
`br_anp_precos_combustiveis.microdados` para série histórica ou join por
`id_municipio`/`sigla_uf`. Nenhuma tabela foi removida.

## Prioridade baixa / não verificado — sem ação, só registro

Ficam como estão em `datasets_quase_duplicados.md` (itens 4-6): os 5 pares
`_original` de `br_cgu_beneficios_cidadao` (provavelmente convenção do
próprio Base dos Dados, risco baixo por serem tabelas do mesmo dataset), os
pares `_antigo` de `br_ibge_pib` (hipótese de série metodológica diferente,
não duplicata), e `br_me_rais_identificada` × `br_me_rais` (escopo diferente
por nome). Nenhum tem ação clara — não repetir aqui, só linkar.

## Ordem de execução recomendada

1. ~~Item 1 (`br_ibama_embargos`)~~ ✅ feito 2026-09-02.
2. ~~Item 2 (`br_seeg`)~~ ✅ feito 2026-09-02.
3. ~~Item 3 (outlier PNCP)~~ ✅ feito 2026-09-02 — métrica
   `pncp_valor_total_contratos` em `metrics.yaml`.
4. ~~Item 4 (nota ANP)~~ ✅ feito 2026-09-02 — nota em
   `docs/overview/14_consumo_precos.md`.

Confirmado no beelink 2026-09-02: `_rodado_metadata` já não tem entrada para
`br_ibama_embargos`/`br_seeg`, então a cadeia de regen do `CLAUDE.md`
(`gera_schemas.py` → `sync_mcp_schema.py` → `build_metadata_catalog.py` →
`gera_join_keys.py` → `gera_metrics_json.py` → `valida_metrics.py` →
`gera_schema_graph.py` → `build_atlas.py`) já rodou depois da remoção — não
precisa rerodar por causa dos itens 1-2. O item 3 só mudou `metrics.yaml`:
`gera_metrics_json.py` e `valida_metrics.py` já rodaram (0 erros, 13
métricas). O item 4 não tocou nenhum YAML gerado (nota em markdown solto),
então não dispara regen nenhum. Nada pendente na cadeia.
