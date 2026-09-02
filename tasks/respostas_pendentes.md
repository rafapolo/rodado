# respostas.md — o que ainda falta responder

Continuação de `tasks/mcp_search_refino.md` (item 1 fechado — índice doc2query do
`search_tables` já trocado e no ar). Este arquivo rastreia o trabalho *derivado*
de perguntar "isso ajuda o MCP?": `docs/perguntas.md` + `docs/respostas.md` viraram
`tasks/douradas_perguntas.json`, um segundo conjunto-dourado (dataset-level) medindo
`search_tables` — ver `CLAUDE.md` seção "Conjuntos-dourados". Responder mais
perguntas não muda o comportamento do `search_tables` por si só (recall ficou
~51% estável nas três rodadas já feitas); o valor real de continuar é o que
aparece *ao responder*: bugs reais de join, tabelas quebradas, campos ausentes.

## Estado em 2026-08-25

- 114 perguntas mantidas no golden set (`tasks/douradas_perguntas.json`, status
  ok/partial + ≥2 datasets resolvidos) — era 106 em 2026-08-24; +1 de T40-3, +7
  dos temas 44/45 novos (abaixo). `search_tables` recall estável: 52,9% dos
  datasets esperados no top-10 (era ~51-52% nas 4 rodadas anteriores) — confirma
  de novo que responder mais pergunta não move essa métrica sozinho (perguntas
  são n≥3 datasets, fora do que uma chamada de `search_tables` resolve).
- **Temas novos 44 e 45 criados e respondidos nesta rodada**, propositalmente
  desenhados pra tocar datasets nunca citados em `perguntas.md` (111 dos 197 do
  espelho nunca apareciam em nenhuma das 215 perguntas anteriores) e testar
  joins nunca exercitados de verdade. 7 de 10 perguntas novas respondidas com
  número real; 3 bloqueadas por corrupção de dado genuína, não por falta de
  tentativa (ver `docs/respostas.md`):
  - **T44-3**: `br_rf_cafir.imoveis_rurais` tem 61-64% de TODAS as linhas com
    `id_imovel_receita_federal = NULL`, em todo snapshot mensal (169,9M linhas,
    só 3,89M ids distintos) — achado novo, não catalogado antes.
  - **T44-4**: as 8 tabelas de `br_ibama_embargos` (113k+48k+439 linhas
    amostradas) têm 100% das colunas vazias — o header do CSV virou o nome da
    própria coluna. Diferente do bloqueio já conhecido em `todo.md` ("infra
    impede *atualizar*"): este é sobre o que já está no beelink não servir pra
    nada, achado novo.
  - **T45-5**: OpenSanctions tem `identifiers` praticamente vazio pra
    `LegalEntity` tagueado Brasil (11 fragmentos em 131.626 registros).
  - **Achado lateral, virou métrica**: `br_ibge_pam.valor_producao` está em mil
    reais, não reais — sem aviso no schema, confirmado batendo a safra de soja
    2022. Agora é `valor_producao_agropecuaria` em `metrics.yaml`.
  - **2 bridges novos + 6 verificados pela primeira vez** em `bridges.yaml`:
    `br_cgu_emendas_parlamentares` (id_municipio, direto) e `br_ana_outorgas`
    (sem id_municipio nenhum — só nome+UF, 99,4% de match) no hub `municipio`;
    o hub `identity` (cnpj) já tinha SICAF/BCB-penalidades/PGFN/TCU-inidôneos/
    holdings/CVM documentados mas nenhum com `verified:` — todos ganharam
    contagem real rodando T45-1..4.
- Bloqueios estruturais catalogados (seção "Bloqueios mapeados" ao fim de
  `docs/respostas.md`) — dado corrompido/ausente/sem chave, não falta de query.
  +5 grupos nesta rodada: os 3 de 44/45 acima, mais nenhum dos 4 espelhos de
  TCE (ES/PI/RJ/SP) ter multa por município — bloqueia T39-2/3/4;
  `br_cnj_estatisticas_poder_judiciario` sem volume processual — bloqueia
  T39-5; `br_siop_orcamento` é orçamento da União, não municipal — T40-4 cruza
  a fonte errada.
- Temas **39 (Justiça) e 40 (Federalismo Fiscal) totalmente verificados**
  tabela por tabela: T39-1 e T40-1/T40-2 já estavam feitos; T40-3 respondido
  nesta rodada (CAPAG × emendas per capita, r=−0,08, n=1.509 — mesmo padrão de
  T40-1, capacidade fiscal não explica quem recebe); T39-2/3/4/5 e T40-4
  confirmados como bloqueio estrutural real (não falta de tentativa); T40-5
  seguia já corretamente documentado (CAPAG sem série temporal no espelho).
- 2 achados de join reais confirmados nas passadas 2 e 3 (ver
  `docs/context/bridges.yaml` — `br_ms_sih` e `br_ms_sinan_violencia` usam
  código de município do SUS de 6 dígitos em MAIS colunas do que a única já
  bridged (`ID_MUNICIP`); `ID_MN_RESI`/`ID_MN_OCOR` do SINAN e as 3 colunas do
  SIH não tinham bridge nenhuma antes dessa sessão).

## Ainda não tocado (~85 perguntas dos temas 1-43, temas inteiros ou parciais)

Temas: 29 (Dados Eleitorais, restam 1/3/4/5), 30 (itens 2-5), 31 (itens 1-3 e 5),
32 (itens 2 e 4), 34 (Atlas — geoespacial, geobr, pulado de propósito), 35 (itens
1-4), 37 (itens 2-4), 38 (itens 1/2/5), 41 (itens 1-4), 42 (todo — hidro/clima),
43 (itens 1/2/4/5), M1-M5 (cadeias multi-dataset).

A maioria já vem autodescrita no próprio `perguntas.md`/`respostas.md` como
precisando de pipeline dedicado (SIH/SIA bilhões de linhas, resolução de entidade
CPF/CNPJ, funções espaciais do geobr) — mas isso não foi verificado tabela por
tabela pra esses temas, ao contrário dos que já foram tentados (incluindo 39, 40,
44 e 45 agora).

**Cobertura de datasets ainda não tocados por nenhuma pergunta**: dos 111
datasets nunca citados (levantamento 2026-08-25), os temas 44/45 tocaram ~20
(ANA outorgas/atlas_esgotos, IBAMA embargos, PAM, PEVS, CAFIR, SICAF, CVM
fundos/administradores, BCB penalidades, Brasil.IO holdings, OpenSanctions).
Ficam **~90 datasets ainda nunca exercitados por uma pergunta** — candidatos
óbvios para um próximo tema: `br_ibge_censo_demografico` (série histórica
1970-2010, nunca cruzada com o Censo 2022), `br_ibge_estadic` (survey estadual
de gestão pública, nunca usado nos temas de fiscal/judiciário), `br_ans_beneficiario`
(saúde suplementar, nunca cruzado com SUS/SIM), `br_capes_bolsas`/`br_mec_prouni`/
`br_mec_sisu` (educação superior, nunca cruzados com INEP), sanções internacionais
(`eu_sanctions`/`un_sanctions`/`global_ofac_sanctions`/`global_icij_offshoreleaks`)
ainda sem tentativa própria além do OpenSanctions bloqueado acima.

## Pra continuar

```bash
# depois de responder mais perguntas em docs/respostas.md:
python3 scripts/build_douradas_perguntas.py    # -> tasks/douradas_perguntas.json
python3 scripts/avalia_douradas_perguntas.py   # mede search_tables contra ele
```

Mesma disciplina das rodadas já feitas: só escrever `✅`/`◐` com query real
rodada no beelink (partição filtrada, ordem de grandeza checada); um número
que parece verificado mas não é é pior que deixar `⏳`. Se um item pendente na
verdade está bloqueado por dado ruim/ausente, documentar em "Bloqueios
mapeados", não forçar resposta.

---

# O prompt pra rodar isto

> **Não executar automaticamente.** Esta seção é o prompt a ser colado numa
> sessão (ou usado com `/loop`) quando alguém decidir de fato atacar as
> pendências. Veio de `docs/prompt_resolver_pendentes.md`, escrito em
> 2026-08-24 e fundido aqui em 2026-08-27 — os dois arquivos eram o mesmo
> trabalho visto de dois ângulos: este arquivo é o *estado*, o prompt é o
> *procedimento*.

Estado real hoje (contado em `docs/respostas.md`, não estimado): **62 `⏳` e
25 `◐`** dos 223 itens, espalhados pelos 45 temas mais a seção
multi-referência (M1–M5). O prompt original falava em 180 pendências — era o
número de 24/08, antes das rodadas que fecharam os temas 39, 40, 44 e 45.

## Regras não-negociáveis (vêm do CLAUDE.md do projeto)

1. **Nunca BigQuery, GCP, `bq`, S3 ou o endpoint `db.xn--2dk.xyz`.** Toda query
   roda via `ssh beelink '~/bin/duckdb -readonly -json ~/rodado/basedosdados.duckdb'`,
   com `SET enable_progress_bar=false;` antes. O `-readonly` não é opcional: o
   DuckDB toma lock exclusivo mesmo pra um `SELECT` sem ele, e há outras
   sessões no mesmo arquivo.
2. **Filtre por partição** (`ano`, `mes`, `sigla_uf`) em qualquer tabela
   grande — SIH, SIA, SINAN, CAGED, CGU servidores/cartão, PGFN, etc. têm
   centenas de milhões a bilhões de linhas.
3. **Nunca junte por `false_friends`.** Antes de escrever um `ON` à mão,
   consulte `docs/context/bridges.yaml` (ou as ferramentas MCP
   `resolve_join`/`explain_column`/`get_join_keys`) — `cnpj`, `valor`,
   `id_municipio` têm armadilhas documentadas ali.
4. **Cheque `list_metrics()`/`get_metric()` antes de calcular taxa ou
   per capita na mão.** `metrics.yaml` existe porque suposição de unidade é
   fácil de errar e o número errado continua plausível.
5. **Valide cada resultado três vezes** antes de reportar: (1) diga a ordem de
   grandeza esperada, (2) sinalize qualquer linha fora dela, (3) confira a
   contagem por dois caminhos independentes. Só entra em `respostas.md` o que
   passa nas três.
6. Correlações são Pearson sobre agregados municipais (5.570 municípios) ou
   estaduais (27 UFs) — mantenha esse padrão para comparabilidade com A1–A16.
7. Preserve o formato exato já usado em `respostas.md`: código `T<tema>-<nº>`,
   selo `✅`/`◐`/`⏳`, métrica em negrito, `n`, referência cruzada `*(AN)*`
   quando a correlação também entra na tabela "Resultados transversais".

## Ordem sugerida de ataque

Vá tema por tema, na ordem de `docs/perguntas.md`, mas dentro de cada tema
resolva primeiro os itens que dependem só de tabelas **já usadas** em A1–A16
(RAIS, SIM, SINASC, CAGED, TSE, PIB, Censo, PRODES, SEEG, PPM, Anatel IBC,
CNPJ) — são join barato, painel pronto. Deixe para o fim os que dependem de
tabelas nunca tocadas no painel atual (SICOR, SICAR, SNIS, SIOP, Transferegov,
CGU cartão/servidores, SINAN, SIH, SIA, CNJ, TCEs, ANP, IPCA, POF, CNPq,
COMEX, TRASE, geobr, ipea_avs, QUEIMADAS, INMET, ANA, MMA, Olympedia,
Poder360, PNS, PNADC, world_oecd_pisa) — cada uma exige achar a tabela certa
com `search_tables`/`describe_table` antes de escrever a query.

Para cada pergunta pendente:

1. Releia o enunciado exato em `perguntas.md` (código `T<tema>-<nº>`) e a nota
   `(n=...)` que lista os datasets exigidos.
2. Confirme que as tabelas existem no beelink (`describe_table`, ou
   `docs/context/all_tables.txt`, que hoje é gerado do catálogo).
3. Resolva os joins com `bridges.yaml`/`resolve_join` em vez de chutar coluna
   por nome igual.
4. Escreva a query com filtro de partição, rode via `ssh beelink`.
5. Se a pergunta pede correlação, calcule Pearson (`corr(x, y)`) sobre o nível
   certo (município ou UF) e registre `n`.
6. Se a tabela não existir no espelho hoje ou exigir pipeline dedicado
   (>1 bi linhas sem partição viável, ou normalização que não existe),
   mantenha `⏳` mas adicione uma frase objetiva do motivo — não invente dado,
   e registre em "Bloqueios mapeados" ao fim de `respostas.md`.
7. Atualize a linha correspondente em `docs/respostas.md`: troque `⏳` por
   `✅` (ou `◐` se só parte do cruzamento saiu), com métrica, `n` e uma leitura
   de uma frase. Se o achado for forte (|r| ≥ 0,4) e transversal, adicione uma
   linha nova na tabela "Resultados transversais" com o próximo código livre
   (`A17`, `A18`, ...) e referencie com `*(AN)*` no fim da entrada de tema.
8. Não toque em itens já `✅`. Não invente número — se a query não confirmar
   com folga o esperado, marque `◐` e explique a limitação em vez de forçar
   um `✅`.

Depois de responder qualquer coisa, regenerar o conjunto-dourado:

```bash
python3 scripts/build_douradas_perguntas.py    # respostas.md -> tasks/douradas_perguntas.json
python3 scripts/avalia_douradas_perguntas.py   # mede search_tables contra ele
```

## Casos que exigem cuidado extra (não são query simples)

- **T13 (Migração), T21 (Corrupção), T26 (Servidores)**: exigem agregação
  dedicada em tabelas de centenas de milhões de linhas (CAGED 232M, CGU
  servidores 852M). Não tente `SELECT *`; agregue direto no DuckDB com
  `GROUP BY` e filtro de ano antes de trazer qualquer linha pro cliente.
- **T23–T24 (Epidemiologia/SUS)**: SIH/SIA são bilhões de linhas — comece pela
  partição mais estreita possível (um `ano` + uma `sigla_uf`) pra validar a
  query antes de rodar full-panel.
- **T34 (Atlas/geobr)**: exige funções espaciais (`ST_*`) — confirme que a
  extensão `spatial` do DuckDB está carregada no beelink antes de tentar.
- **T05/T15/T29 (Câmara/Senado dados abertos)**: essas fontes normalmente não
  têm `id_municipio` direto — o join com TSE/Censo passa por normalização de
  nome do candidato/partido; documente a taxa de match.
- **T42 (hidro/clima)**: as 7 séries do `br_ana_telemetria` são particionadas
  por `bacia` e só ficaram visíveis no `schemas.json` em 27/08. O
  `inventario` (37.782 estações) é quem liga série a território, por `codigo`
  — e o `municipiocodigo` dele **não** é IBGE: 0 de 4.770 casam. Ver as
  pontes no hub `municipio`.
- **Multi-referência M1–M5**: são cadeias de 3+ joins em cascata. Resolva
  primeiro os componentes isolados (já parcialmente em A1/A2/T37-1/T37-5) e só
  monte a cadeia completa depois que cada elo estiver validado.

## Time-boxing — encerrar bem antes de estourar o orçamento

Esta tarefa é grande demais pra uma sessão só. Não tente terminar tudo de uma
vez — monitore o orçamento e pare limpo bem antes de ficar sem tokens:

1. **Cheque o orçamento periodicamente**, não só no fim: a cada tema concluído
   (ou a cada ~15–20 min), olhe o contador `<total_tokens>N tokens left` que
   aparece nos `system-reminder`, e rode `/usage` como referência complementar.
2. **Defina uma reserva de segurança**: pare de puxar *itens novos* quando
   restar menos de ~20% do orçamento inicial — folga o bastante pra escrever o
   resumo e editar `respostas.md` sem cortar no meio.
3. **Feche o item em andamento antes de parar** — nunca deixe uma query rodada
   sem registrar o resultado, nem uma edição pela metade. Melhor um tema a
   menos do que uma entrada quebrada.
4. **Ao bater a reserva**, escreva o estado: `grep -o '⏳' docs/respostas.md |
   wc -l` pras pendências restantes; quantos viraram `✅`, quantos `◐`, e por
   que os que continuam `⏳`; qual foi o **último tema totalmente processado** e
   qual seria o **próximo item a retomar**.
5. Se rodar via `/loop` (self-paced), use esse mesmo checkpoint como critério
   de `noop`/parada.
6. **Não faça commit automático** — pare pra revisão do usuário antes de
   `git add`/`git commit`, mesmo ao encerrar por orçamento.

---

## Herdado de `bugs_e_achados_agentes.md` (arquivado 2026-09-02)

A rodada de 5 agentes de 2026-08-27 deixou um fio aberto que é deste arquivo,
não daquele: o **Agente A caiu por rate limit** no meio do backlog de
perguntas e nunca retomou. O que ficou por responder:

- **T37-2/3/4 em diante**, mais os temas listados acima como "ainda não tocado".
  **Retomado em 2026-09-02**: T37-2/3/4 já estavam completos e staged quando
  a sessão de retomada assumiu (confirmados, não refeitos) — commit
  `5e4341e`. Tema 37 está fechado (T37-1 a T37-5 todos ✅/◐). Além disso
  nesta mesma janela outra(s) sessão(ões) concorrente(s) fecharam T31
  (commit `4795752`), T35-2/4 (`2c96122`) e mexeram em T42 (`377c2ed`) — não
  refazer, ver `docs/respostas.md`. T43-4 fechado nesta sessão (`ff0fd91`).
- Os dois achados que o agente produziu **já foram mesclados** em
  `bridges.yaml` (ILIKE de resultado eleitoral casando "não eleito"; censo
  2010+2022 na mesma coluna `ano` dobrando o total sem filtro) — não refazer.

O log completo da rodada, com os 5 bugs confirmados e o que cada agente
entregou, está em `done/bugs_e_achados_agentes.md`.

## Bugs encontrados nesta sessão (2026-09-02)

- **`br_me_cnpj.empresas.capital_social` tem valor-sentinela**: 124 linhas
  (snapshot 2025-09) têm `capital_social = 999999999999.0` (R$ 1 trilhão
  exatos, quase o PIB nacional inteiro de 2021) — claramente um
  placeholder/erro de preenchimento, não capital real. Qualquer soma ou HHI
  sobre essa coluna sem excluir esse valor-sentinela fica distorcido para o
  CNAE/UF onde ele cai. Usado para fechar T30-1 (HHI de concentração por
  divisão CNAE) — refazer excluindo essas 124 linhas não mudou o resultado
  neste caso (r's idênticos), mas o próximo uso da coluna deveria filtrar
  `capital_social < 999999999999` ou tratar como nulo. Não catalogado em
  `bridges.yaml` (não é join, é qualidade de valor) — considerar registrar
  em `dicionario_coverage.json` ou como nota na tabela se o padrão se
  repetir em outro dataset do CNPJ.
