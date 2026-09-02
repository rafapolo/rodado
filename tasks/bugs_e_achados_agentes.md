# Bugs e achados da rodada de 5 agentes paralelos — 2026-08-27

> **Atualização 2026-08-27, ~14h30**: com o Agente A bloqueado por rate limit
> (reset 18:10 Zurique) e portanto sem risco de conflito de edição, a sessão
> orquestradora mesclou tudo que já estava pronto: tema 56 completo em
> `docs/perguntas.md`/`docs/respostas.md`, e as 4 entradas de `bridges.yaml`
> (NU_ANO vazio em 2020, CS_RACA subcontagem, ILIKE de resultado eleitoral,
> censo 2010+2022 na mesma coluna `ano`). Rodada a cadeia de regen
> (`gera_join_keys.py`, `gera_metrics_json.py`, `valida_metrics.py` — 0 erros)
> e o golden set (`build_douradas_perguntas.py` → 172 perguntas mantidas;
> `avalia_douradas_perguntas.py` → 69,8% com ≥1 dataset esperado no top-10,
> 45,3% com todos). **Achado durante a mesclagem**: PyYAML rejeita `": "`
> (dois-pontos+espaço) dentro de scalar plano multi-linha — quebrou o parse
> ao colar o texto do agente A ("duas safras: 393,8M..."); corrigido trocando
> por travessão. Vale lembrar quando colar texto de agente livre em YAML.
> As seções abaixo ficam como estavam no momento em que cada agente reportou —
> não voltei a editá-las, só este aviso no topo.

Em 2026-08-27, 5 agentes rodaram em paralelo sobre o backlog de `tasks/`:
`respostas_pendentes.md` (A), `ana_series_historicas.md` (B), `todo.md` (C),
`datasets_coverage_gaps.md` (D) e `datasets_gap_analysis.md` +
`deanonimizacao_geral.md` (E). Só o agente A tinha permissão de editar os
arquivos compartilhados (`docs/perguntas.md`, `docs/respostas.md`,
`docs/context/bridges.yaml`, `docs/context/metrics.yaml`) direto, pra evitar
conflito de edição concorrente — os outros quatro reportaram achados em modo
read-only. Este arquivo consolida esses achados numa lista acionável: bugs a
corrigir e conteúdo pronto pra mesclar/expandir.

**Status de cada agente nesta rodada** (atualizar conforme completam):

| Agente | Tarefa | Status em 2026-08-27 |
|---|---|---|
| A | `respostas_pendentes.md` — resolver ⏳/◐ | **caiu por rate limit da conta** (reset 18:10 Zurique) — progresso real salvo, ver §2.8 |
| B | `ana_series_historicas.md` — corrigir sort + reprocessar | item 0 **resolvido e verificado independente**; item 4 (gap COTA) em andamento no beelink, ~95min restantes — ver §2.9 |
| C | `todo.md` — IPEA Atlas + pesquisa consumidor.gov.br | **concluído** — IPEA 152/152, pesquisa consumidor.gov.br achou o dataset e o bloqueio real, ver §2.4 |
| D | `datasets_coverage_gaps.md` — tema novo | **concluído** — tema 56 pronto, ver abaixo |
| E | `datasets_gap_analysis.md` + `deanonimizacao_geral.md` | **concluído** — ver §2.6 e §2.7 |

---

## 1. Bugs confirmados (achados pelo Agente D, tema 56)

### 1.1 `br_ms_sinan_violencia.microdados_violencia.NU_ANO` vazio pra 100% do lote 2020
- **Sintoma**: `NU_ANO` vem como string vazia (`''`) em 326.563 de ~4,94M linhas,
  concentradas quase inteiramente (326.503 de 326.563) no lote com
  `ano_sinan=2020`. Qualquer `GROUP BY NU_ANO` pula 2020 inteiro em silêncio —
  a série salta de 2019 direto pra 2021, sem erro nem linha vazia visível.
- **Fix**: usar `ano_sinan` (inteira, sem branco, cobre 2009-2025 contínuo)
  como partição de ano nesta tabela — nunca `NU_ANO`.
- **Onde documentar**: acréscimo na entrada existente da ponte `id_municipio_6`
  em `docs/context/bridges.yaml` (`notes:`, perto dos bullets de
  `br_ms_sinan_violencia`):
  ```yaml
      - 'br_ms_sinan_violencia.microdados_violencia.NU_ANO vem vazio (string vazia)
        pra 100% do lote tageado ano_sinan=2020 (326.503 de 326.563 linhas em
        branco) — usar ano_sinan como partição de ano nesta tabela, nunca NU_ANO,
        ou a série pula 2020 inteiro em silêncio. Achado tema 56, 2026-08-27.'
  ```
- **Status**: não mesclado ainda (aguardando agente A liberar `bridges.yaml`).

### 1.2 `CS_RACA='2'` sozinho subconta vítimas negras em ~5x
- **Sintoma**: `br_ipea_atlasviolencia` pré-agrega "negro" como preto+pardo
  dentro do próprio nome da série (`Homicídios Negros`, id 41), enquanto
  `br_ms_sinan_violencia.microdados_violencia` mantém preto (`CS_RACA='2'`) e
  pardo (`CS_RACA='4'`) separados, sem coluna pré-agregada. Filtrar só
  `CS_RACA='2'` pensando "vítimas negras" captura ~9% das notificações; o
  valor correto (`CS_RACA IN ('2','4')`) é 46-58% ao longo de 2011-2022 —
  número plausível e silenciosamente errado.
- **Fix**: sempre `CS_RACA IN ('2','4')` pra "negro" nesta tabela, nunca só `'2'`.
- **Onde documentar**: nova entrada em `coded_differently:` no `bridges.yaml`:
  ```yaml
    raca_cor_negro_agregado (br_ms_sinan_violencia vs br_ipea_atlasviolencia):
      reason: mesmo rótulo "negro" significa coisas diferentes entre as duas fontes —
        br_ipea_atlasviolencia já vem com "negro" pré-agregado (preto+pardo, convenção
        IBGE) dentro do próprio nome da série (`Homicídios Negros`, id 41), enquanto
        br_ms_sinan_violencia.microdados_violencia mantém preto e pardo em códigos
        CS_RACA separados (2=preta, 4=parda) sem nenhuma coluna pré-agregada.
        Filtrar CS_RACA='2' pensando "vítimas negras" captura só ~9% das notificações
        quando o valor correto (preto+pardo, CS_RACA IN ('2','4')) é 46-58% ao longo
        de 2011-2022 — subestima em ~5x, número plausível e silenciosamente errado.
        Achado respondendo tema 56, 2026-08-27.
      seen_in: 2 datasets (br_ms_sinan_violencia, br_ipea_atlasviolencia) — padrão
        (agregado "negro" pré-computado em uma fonte, cru em outra) provável de
        recorrer em qualquer cruzamento entre série pronta do IPEA e microdado
        bruto de raça/cor.
  ```
- **Status**: não mesclado ainda.

### 1.3 `br_ipea_atlasviolencia` é só nacional, sem UF/município
- **Sintoma**: apesar do Atlas da Violência ser conhecido por granularidade
  municipal, o espelho hoje só tem `valores_nacional` — nenhuma tabela de
  UF ou município. Limitação real de escopo do mirror, não bug de query.
- **Ação**: nenhum fix de código; é um gap de cobertura a registrar em
  `datasets_coverage_gaps.md` ou `datasets_gap_analysis.md` (o scrape do
  Agente C, se completar 152/152 séries, pode revelar se a granularidade
  sub-nacional existe na fonte e não foi capturada — checar depois).

### 1.4 `resultado ILIKE '%eleito%'` casa também "não eleito" (Agente A, T29-1)
- **Sintoma**: em `br_tse_eleicoes`, filtrar reeleitos com `resultado ILIKE
  '%eleito%'` casa a substring "eleito" dentro de "**não** eleito" também —
  inflou a contagem de deputados reeleitos de 282 pra 472 (67% a mais).
- **Fix**: usar `resultado IN ('eleito por media','eleito por qp')` — valores
  exatos, nunca `ILIKE '%eleito%'` nesta coluna.
- **Status**: achado documentado direto na entrada T29-1 de `docs/respostas.md`
  (já mesclado pelo próprio agente A, que tinha permissão de escrita). Vale
  levar pro `bridges.yaml`/`false_friends` se o padrão se repetir em outra
  coluna de resultado eleitoral.

### 1.5 Censo 2022 e 2010 na mesma tabela, mesma coluna `ano`, dobra o total sem filtro (Agente A, T38-5)
- **Sintoma**: `br_ibge_censo_2022.populacao_grupo_idade_sexo_raca` e
  `.indice_envelhecimento_raca` guardam os censos **2010 E 2022 na mesma
  tabela**, distinguidos só pela coluna `ano` — apesar do nome do dataset
  ser só "censo_2022". Um `SUM(populacao)` sem `WHERE ano=2022` soma as duas
  safras: 393,8M em vez dos 203,1M reais.
- **Fix**: sempre `WHERE ano=2022` (ou `2010`) nessas duas tabelas
  especificamente. As outras do dataset (`populacao_grupo_idade_uf`,
  `populacao_idade_sexo`, `alfabetizacao_grupo_idade_sexo_raca`, as
  `caracteristica_domicilio_*`) **não** têm esse problema.
- **Onde documentar**: candidato a `docs/context/bridges.yaml` (`notes:` na
  entrada do hub `id_municipio`/censo, ou nova entrada em
  `false_friends`/`coded_differently` — mais parecido com `coded_differently`
  no sentido de "mesma coluna, dois anos misturados").
- **Status**: achado documentado na entrada T38-5 de `docs/respostas.md`; não
  mesclado em `bridges.yaml` ainda (o agente A caiu antes de chegar nisso —
  ver §2.8).

---

## 2. Achados/enhancements prontos pra mesclar (Agente D — tema 56)

Tema completo, 5 perguntas respondidas com número real, todas ✅. Bloco
íntegro pronto pra colar em `docs/perguntas.md` e `docs/respostas.md`:

### 2.1 Bloco pra `docs/perguntas.md`

```markdown
## 56 · Violência Notificada, Vulnerabilidade Infantil e Autolesão

1. A tendência nacional de notificações de autolesão/tentativa de suicídio no SINAN acompanha a tendência da taxa de suicídio consolidada pelo Atlas da Violência (IPEA), ou os dois indicadores divergem? *(n=2: ms_sinan_violencia, ipea_atlasviolencia)*
2. Municípios com maior taxa de notificação de violência sexual contra crianças (SINAN, vítima menor de 18 anos) por 100 mil habitantes têm menor cobertura líquida de matrícula na pré-escola (Observatório da Criança e do Adolescente/Abrinq)? *(n=3: ms_sinan_violencia, abrinq_oca, ibge_populacao*)*
3. A composição racial das vítimas notificadas no SINAN (qualquer tipo de violência) reflete a composição racial das vítimas de homicídio consolidada pelo Atlas da Violência (IPEA), ou pessoas negras estão sobrerrepresentadas nos desfechos letais em relação à violência notificada em geral? *(n=2: ms_sinan_violencia, ipea_atlasviolencia)*
4. A participação de parceiro/ex-parceiro íntimo entre os agressores de vítimas mulheres notificadas no SINAN cresceu entre 2011 e 2024, e esse movimento acompanha — ou diverge de — a tendência nacional de homicídios de mulheres do Atlas da Violência? *(n=2: ms_sinan_violencia, ipea_atlasviolencia)*
5. A cobertura temporal das notificações do SINAN Violência é confiável usando a coluna documentada de ano da notificação (NU_ANO), ou existe alguma lacuna de rotulagem que exige outra coluna de ano pra reconstituir a série 2009-2025 corretamente? *(n=1: ms_sinan_violencia)*
```

### 2.2 Bloco pra `docs/respostas.md`

```markdown
## 56 · Violência Notificada, Vulnerabilidade Infantil e Autolesão

- **T56-1 ✅ (2026-08-27)** Volume anual de notificações de autolesão/tentativa
  de suicídio no SINAN (`LES_AUTOP='1'`, partição `ano_sinan`) × taxa nacional
  de suicídio do Atlas da Violência IPEA (série 323, `valores_nacional`):
  **r = 0,75 (n=12 anos, 2011-2022)** — ambos sobem no período, mas em ritmos
  muito diferentes: autolesão notificada saltou de 14.940 (2011) pra 116.269
  (2021, +678%), enquanto a taxa de suicídio subiu de 5,02 pra 7,38 por 100
  mil (+47%). A correlação alta reflete duas séries crescentes no mesmo
  período mais do que uma relação direta — o crescimento da notificação é
  muito mais rápido que o crescimento real de suicídios, consistente com
  expansão da cobertura/cultura de notificação do SINAN ao longo da década,
  não com uma epidemia de autolesão 7x maior que o aumento real de mortes.
  2022 tem queda no SINAN (61.676) que é artefato de subnotificação daquele
  ano (mesmo padrão do dip visto na contagem geral da tabela), não real.
- **T56-2 ✅ (2026-08-27)** Taxa de notificação de violência sexual contra
  crianças/adolescentes (SINAN, `VIOL_SEXU='1'` e idade < 18 extraída de
  `NU_IDADE_N`, 197.256 notificações com município de residência preenchido,
  2010-2019) por 100 mil habitantes × cobertura líquida de pré-escola
  (`br_abrinq_oca.municipio_primeira_infancia`, 5.570 municípios): **r =
  0,025 (n=22.270 pares município-ano)** — correlação nula. Cobertura
  pré-escolar municipal não explica taxa de notificação de violência sexual
  infantil; mais provável é que a notificação capture capacidade/vontade de
  notificar (rede de saúde, Conselho Tutelar) tanto quanto incidência real,
  ruído que domina qualquer sinal de vulnerabilidade educacional.
- **T56-3 ✅ (2026-08-27)** Composição racial das vítimas notificadas no SINAN
  (preto+pardo, `CS_RACA IN ('2','4')` sobre raça conhecida) × proporção de
  vítimas negras entre homicídios do Atlas da Violência IPEA (série 41 ÷
  série 328, mesmo conceito "negro" = preto+pardo no IPEA): **SINAN sobe de
  46,5% (2011) pra 57,7% (2022); Atlas IPEA sobe de 67,4% pra 76,6%** no
  mesmo intervalo — pessoas negras são sempre 15-21 pontos percentuais mais
  representadas entre os homicídios (desfecho letal) do que entre as
  notificações de violência em geral (todos os tipos, incluindo
  não-letais). **Achado de gotcha de codificação**: `CS_RACA='2'` sozinho
  (só "preta") captura apenas ~9% das notificações — usar só o código
  "preta" em vez de "preta+parda" subestima em 5x a proporção real de
  vítimas negras; ver `coded_differently` em `bridges.yaml` (§1.2 acima).
- **T56-4 ✅ (2026-08-27)** Participação de parceiro/ex-parceiro/namorado/
  ex-namorado (`REL_CONJ`/`REL_EXCON`/`REL_NAMO`/`REL_EXNAM`='1') entre
  agressores de vítimas mulheres no SINAN: oscila entre 22,9% e 33,3% do
  total de notificações femininas, **sem tendência de alta** — cai de 31,9%
  (2011) pra 26,3% (2024) em termos relativos, mas em número absoluto cresce
  de 23.925 pra 115.362 (quase 5x), porque o total de notificações femininas
  do SINAN também explodiu (75.033 → 437.828, ~5,8x). No mesmo período, os
  homicídios de mulheres do Atlas da Violência IPEA **caíram** de 4.522
  (2011) pra 3.806 (2022, -16%). As duas séries divergem: violência não-letal
  contra a mulher notificada cresce fortemente em volume absoluto (mais
  expansão de cobertura do sistema de notificação do que necessariamente
  mais violência) enquanto o desfecho letal (homicídio) recua no mesmo
  intervalo.
- **T56-5 ✅ (2026-08-27) — bug de partição confirmado** ver §1.1 acima
  (`NU_ANO` vazio pra 100% do lote 2020, usar `ano_sinan`).
```

### 2.3 Resumo (contexto pra quem for mesclar)

`br_ipea_atlasviolencia` é só nacional (sem UF/município) — limitação real de
escopo. O bug de destaque é `NU_ANO` vazio pro lote inteiro de 2020 (326,5k
linhas), sumindo com 2020 em silêncio de qualquer query particionada por ano.
O gotcha de destaque é o descompasso de codificação racial (§1.2). Vítimas
negras são consistentemente 15-21pp mais representadas em desfechos letais
(homicídios IPEA) do que na violência notificada em geral (SINAN). Violência
não-letal por parceiro íntimo contra mulher cresceu ~5x em volume absoluto
notificado enquanto homicídios femininos caíram 16% no mesmo período —
sugere expansão de vigilância mais do que aumento de violência letal.
Cobertura municipal de pré-escola: correlação essencialmente nula com taxa de
notificação de violência sexual infantil (r=0,025, n=22.270).

**Status**: `tasks/datasets_coverage_gaps.md` já foi atualizado pelo próprio
agente D (moveu os 3 datasets — `br_ipea_atlasviolencia`, `br_ms_sinan_violencia`,
`br_abrinq_oca` — de "untouched" pro registro de tocados). Falta só mesclar
os blocos acima em `docs/perguntas.md`/`docs/respostas.md` e as duas entradas
de `bridges.yaml` do §1.

---

## 2.4 Agente C — IPEA Atlas da Violência: fechado 152/152

Duas rodadas encadeadas de `IPEA_DEADLINE_SECONDS=700`:

- Run 1: 151/152 (série 158 bateu no `curl rc=28` intermitente já conhecido) — 2.831 linhas anuais.
- Run 2: pegou a série pendente → **152/152 séries cobertas** — 2.854 linhas anuais.

Verificado no beelink: `br_ipea_atlasviolencia.series` = 152 linhas (1 por
série); `br_ipea_atlasviolencia.valores_nacional` = 2.854 linhas, **136**
`serie_id` distintos, 1979-2024.

**Achado, não bug**: 16 das 152 séries retornam array vazio de `dados-api`
(checkpointado como `[]`, contam como "cobertas" mas sem linha de valor) —
aparentemente não publicam série nacional anual por esse endpoint. Não
investigado a fundo, fora do escopo desta rodada. Bate com o §1.3 acima
(o dataset é só nacional, sem UF/município) — juntos, os dois achados dizem
que a cobertura de `br_ipea_atlasviolencia` tem limite real de granularidade
e de série, não é falha de scrape.

`tasks/todo.md` já foi atualizado pelo próprio agente, seção marcada ✅
RESOLVIDO.

## 2.5 Agente C — Consumidor.gov.br: fonte localizada, bloqueio muda de natureza

Não rodou scrape (instruído a só pesquisar); `PACKAGE_API` não foi tocado.

- `dados.mj.gov.br` reconfirmado `NXDOMAIN` — aposentado, não fora do ar.
  Existe snapshot no Wayback Machine, mas todo link de download nele ainda
  aponta pro host morto — sem CDN alternativo.
- **Dataset localizado** no portal unificado: slug
  `reclamacoes-do-consumidor-gov-br1`, página
  `https://dados.gov.br/dados/conjuntos-dados/reclamacoes-do-consumidor-gov-br1`
  (carrega, 200, mas é SPA Vue cujas chamadas de dado dão 401).
- Toda a superfície de API do `dados.gov.br` (CKAN velho e REST novo) é
  travada por um header obrigatório `chave-api-dados-abertos` (401,
  `www-authenticate: Bearer`) — mesmo em rotas nomeadas "publico". Testado
  com headers de navegador também, ainda 401: é gate de backend de verdade,
  não fingerprint de cliente.
- **Como conseguir a chave** (pela própria spec OpenAPI + docs do pacote
  `dados-gov-sdk` no PyPI): logar em `dados.gov.br` com conta gov.br/CPF e
  gerar token em "Minha Conta" — sem etapa de aprovação separada descrita.
  **O agente não criou conta**, conforme instruído.
- **Conclusão**: a fonte não está mais perdida, mas destravar o scrape agora
  precisa de um humano logar e gerar o token — não é mais "achar onde
  mudou", é "alguém logar". Estado do scrape sem mudança: 10.167.141 linhas /
  70 de 86 arquivos.

**Decisão pendente pro usuário**: logar com CPF pessoal em `dados.gov.br` pra
gerar a chave não é uma chamada que o agente (nem eu) deveria tomar sozinho —
é uso de credencial pessoal. Ver §5.

## 2.6 Agente E — quick-wins executados e bloqueios reais

**Executado e no beelink**: refresh de `br_bcb_sgs.series` (18 séries
curadas, `scripts/scrap/bcb_sgs.py`, API pública do BCB, overwrite
idempotente). Confirmado: séries 1 (`dolar_comercial_venda`) e 11
(`taxa_selic_diaria`) foram de 6.660 linhas/stale em 2025-12-31 pra **6.694
linhas, atual até 2026-08-26**. É o substituto mais próximo disponível pro
`br_bcb_taxa_cambio`/`taxa_selic` original — ver por quê abaixo.

**Bloqueios confirmados, não "não tentado"**:

- `br_bcb_taxa_cambio`/`taxa_selic` — os dois datasets são **ACL-restritos no
  próprio projeto BigQuery do Base dos Dados** (`Readers: projectReaders`,
  falta o `allUsers` que todo dataset funcional tem). `bq query` dá `Access
  Denied` mesmo com `bq show` funcionando (por isso pareciam simples de
  puxar). Não é corrigível do nosso lado — a fonte real virou `br_bcb_sgs`.
- MUNIC/ESTADIC 2023-24 — o beelink já bate exatamente com o mirror do Base
  dos Dados no BigQuery (conferido tabela por tabela); não há drift a
  fechar via `bq`. O mirror do BD em si está stale pra maioria das tabelas.
  Confirmado via `curl` que o FTP do IBGE tem os XLSX consolidados 2023/2024
  reais (`ftp.ibge.gov.br/Perfil_Municipios/2024/...xlsx`, 25,5MB, HTTP 200,
  sem auth) — mas construir o scraper significa mapear ~300 colunas de um
  XLSX grande pras 7 tabelas normalizadas do BD por pesquisa, o que exige o
  codebook do IBGE e é projeto de ETL real, não refresh de 20 minutos.
- Querido Diário — gap hoje é **~10,7 meses** (2025-10-05 → hoje), maior que
  os "~9 meses" que o doc antigo registrava. API confirmada viva (`curl` ao
  vivo retorna dado atual). Não rodou porque o script só suporta
  `--years N` (repuxa N anos inteiros), o que duplicaria ~2 anos já
  cobertos num segundo parquet sobreposto — precisa de flag `--since`/
  `--until` nova, ou apagar o arquivo velho manualmente primeiro. Decisão
  de escopo deixada pro usuário.

## 2.7 Agente E — CNES `tipo_pessoa='1'`: números reais em vez de estimativa

Rodou só `COUNT`/`JOIN` read-only contra `~/staging/b2_registro.parquet` —
**nada escrito**:

- Dos 180.573 CPFs distintos de estabelecimento de saúde, só **2.636 (1,46%)**
  teriam nome via o registro Balde 2 existente — não 22,8M como a estimativa
  original sugeria (esse era o total de *linhas*, não de CPFs distintos
  nomeáveis).
- Desses 2.636: **93,9% (2.474)** viriam de fontes "baratas" — filiação/
  candidatura TSE, cadastro de servidor/aposentado CGU, TCU — registros
  profissionais/políticos já públicos.
- **6,1% (162)** só seriam nomeados porque o CPF também aparece numa lista de
  benefício social (auxílio emergencial, bolsa família, BPC etc.) — este é
  o trade-off de privacidade específico que o doc original sinalizou: nomear
  profissional de saúde individual cruzando com cadastro de benefício
  social. Números reais pra quem for decidir: **162 de 2.636**, não "todos
  os 22,8M".

**SICOR 38,91% sem nome**: reconfirmado exato — 5.607.513 CPFs distintos,
2.181.973 sem nome. Informativo, sem fix disponível no espelho.

**Inventário de extensão do Balde 2**: varreu as 199 datasets/832 tabelas do
`basedosdados-schema.json` procurando coluna de CPF sem coluna de nome ao
lado. Das 70 tabelas com alguma coluna `*cpf*`, só 3 não tinham nome óbvio
por palavra-chave — e as 3 eram falso-positivo na inspeção manual
(`br_cvm_fundos.fundos` já tem `GESTOR`; `br_trase_supply_chain.soy_beans_storage_facilities`
já tem `company`; `br_ibama_embargos.decisao` nem existe como tabela viva no
beelink, bloqueio de infra já conhecido). **Resultado: zero alvos novos** de
extensão pra Balde 2 além do SICOR.

## 2.8 Agente A — caiu por rate limit da conta, progresso real preservado

**Causa**: `rate_limit`/HTTP 429 — "You've hit your session limit · resets
6:10pm (Europe/Zurich)" (~14:13 CEST quando caiu, reset em ~4h). É limite de
conta/sessão, não erro do trabalho — e pode atingir o Agente B também, que
roda na mesma conta em paralelo.

**Nada corrompeu**: o agente editava `docs/respostas.md` incrementalmente
(tema por tema), e a última coisa que tentou (T37-2) nunca chegou a ser
escrita — ficou limpo como `⏳` junto de T37-3/T37-4. YAML de `bridges.yaml`/
`metrics.yaml` seguem válidos (`yaml.safe_load` OK) e sem diff — o agente não
chegou a adicionar bridge/metric novo antes de cair.

**Progresso real, salvo em disco** — 11 itens resolvidos (`git diff
docs/respostas.md`: +18/-7 linhas):

| Item | Selo | Achado |
|---|---|---|
| T07-4 | ✅ | Perder agência ESTBAN não prediz PIB municipal menor (r≈−0,024, controlado por população) |
| T24-4 | ✅ | Valor por AIH de parto normal sobe com porte hospitalar em todas as 5 regiões |
| T29-1 | ✅ | Reeleição 2018→2022: r=0,87 no mapa de votos por município — **+ bug do §1.4** |
| T29-3 | ✅ | Margem de vitória presidencial × emenda per capita: r≈0 |
| T29-5 | ✅ | Queda de comparecimento 2018→2022 não explicada por juventude nem PIB per capita |
| T29-4 | ⏳ | Sem operacionalização direta no espelho (fragmentação partidária) |
| T30-2 | ✅ | Microempresa per capita × crescimento RAIS: r=−0,10 |
| T30-3 | ✅ | Abertura líquida de empresa × crescimento do PIB: r fraco, defasado > contemporâneo |
| T30-4 | ✅ | Empresa com sócio estrangeiro tem ~7x menos chance de ser empregadora direta |
| T30-5 | ◐ | HHI de concentração de emprego × arrecadação por trabalhador: r=−0,25 (n=15, amostra pequena) |
| T38-5 | ✅ | Queda de matrícula × queda de população jovem: r=0,71 — **+ bug do §1.5** |
| T38-2 | ◐ | AEE só tem grão UF×rede, não município — respondido com ressalva |
| T41-2, T41-5 | ⏳ | `br_saude_bps.dados` é compra institucional, não consumo per capita — só 2,8% dos municípios têm instituição compradora, resultado descartado por não medir o que a pergunta pede |
| T43-1/2/4/5 | ⏳ | Confirmado: `world_olympedia_olympics` não tem naturalidade do atleta, nenhuma coluna de cidade/município |

**Próximo item na fila quando parou**: T37-2 (devedores PGFN recebendo
pagamento público via contrato CGU apesar da dívida) — T37-2/3/4 seguem
`⏳`, pendentes de retomada.

**Retomar**: depois de 18:10 (horário de Zurique), relançar o mesmo agente
(ou um novo com o mesmo prompt) apontando pra continuar de T37-2 em diante —
os temas já resolvidos nesta rodada não precisam ser refeitos.

---

## 2.9 Agente B — fix do sort ANA: verificado independente no beelink

**Fix aplicado** em `scripts/scrap/ana_mensal_unifica.py:104` — confirmado no
código: `todo.sort([...], descending=[False, False, True])`, mantendo o
`nivel_consistencia` mais alto (consistido) no `keep="first"`, não o mais
baixo (bruto). É o único lugar do script com esse padrão. Rastreado no git
(`scripts/` não é gitignored, ao contrário de `tasks/`) — 3 arquivos
modificados: `ana_mensal_unifica.py`, `ana_soap_worker.py`,
`ana_series_unifica_gap.py`.

**Reconferido eu mesmo, direto no beelink** (mesma comparação plural×singular
que o task doc original descreve, não confiando só no número do agente):

| | Meses comparados | Divergência de nível | Divergência de valor |
|---|---|---|---|
| Vazão | 1.331.690 | **0** (era 28.037/273 estações) | **0** |
| Cota | 1.729.199 | **0** | **54** (não reportado pelo agente) |

Vazão bate exatamente com o que o agente reportou. Na cota achei **54
divergências de valor residuais que o agente não mencionou** (relatou "0"
pros dois). Inspecionei as maiores: todas têm `nivel_consistencia` igual
nos dois lados (2 = consistido em ambos) mas o valor médio mensal difere —
ex. código 64717000, 1992-01, 267,39 vs 378,97. **Não é o bug do dedup** (o
nível já bate) — é uma divergência residual pré-existente entre os dois
pipelines na agregação diário→mensal, de escopo menor (54 de 1,73M = 0,003%)
e fora do que a tarefa pedia corrigir. Registrando pra não ficar encoberta,
não como bloqueio — o fix do item 0 continua correto e resolvido.

**Processo em background confirmado rodando de verdade**: PID 953485 no
beelink, ativo desde 14:03, gravando arquivos batch a cada ~2 min
(`~/soap_gap_cota/batch_*.parquet`) — não é alegação vazia, tem saída real
crescendo.

**Achados extra do agente, não pedidos mas úteis**:
- A suposição de que "SOAP não serve diário pós-2023" estava **errada** —
  o mesmo endpoint de vazão mensal já devolve `Vazao01..31`/`Status`
  embutido por registro; só não foi extraído ainda (fora do escopo pedido).
- Outorgas × série por bacia: bacias em queda mais acentuada (São Francisco
  -36,2%, Atlântico Leste -32,4%) têm razão captação/vazão histórica de
  0,7-2,7%; Amazonas (+2,0%) e Uruguai (+20,7%) têm 0,04-0,30% — ordem de
  grandeza menor. Limitações reais documentadas (join por município não por
  bacia geográfica real, sem os filtros de anomalia do
  `reference_outorgas_snirh`).

**Pendente**: item 4 (gap da COTA) ainda rodando — o agente vai reportar de
novo quando o fetch (~95min restantes a partir de 14:33) terminar, fizer o
merge, validar e rodar o regen de novo (essa parte SIM cria tabela nova,
diferente do fix do item 0 que só reprocessou linha existente).

---

## 3. Pendente (aguardando o rate limit liberar / Agente B terminar)

Preencher aqui conforme cada notificação de conclusão chegar:

- [ ] **Agente A** (retomar após 18:10 Zurique): T37-2/3/4 em diante, mais os
  temas listados em `tasks/respostas_pendentes.md` como "ainda não tocado".
  Ao retomar, levar pro `bridges.yaml` os 2 achados dos §1.4/1.5 (ILIKE de
  resultado eleitoral, censo 2010+2022 na mesma coluna `ano`).
- [ ] **Agente B** (`ana_series_historicas.md`): resultado do fix de sort no
  `ana_mensal_unifica.py` (antes/depois da divergência de 28.037 meses),
  status dos 4 itens restantes (gap COTA, diária, procedência, cruzar
  outorgas). Também pode ter caído no mesmo rate limit — checar antes de
  supor que ainda está rodando.

## 4. Próximos passos, depois que os 5 terminarem

1. Mesclar os blocos do §2 em `docs/perguntas.md`/`docs/respostas.md`/`bridges.yaml`
   — só depois que o agente A (único com permissão de escrita nesses arquivos)
   sinalizar que terminou, pra não conflitar.
2. Rodar a cadeia de regen: `gera_join_keys.py`, `gera_metrics_json.py`,
   `valida_metrics.py`.
3. Regenerar o golden set: `build_douradas_perguntas.py` +
   `avalia_douradas_perguntas.py`.
4. Revisar o diff inteiro (`git status`/`git diff`) antes de qualquer commit —
   nenhum agente fez `git add`/commit, é revisão do usuário.

## 5. Decisões que ficam com o usuário (nenhum agente/orquestrador decide sozinho)

- **Consumidor.gov.br (§2.5)**: destravar o scrape exige logar em
  `dados.gov.br` com conta gov.br/CPF pessoal e gerar um token — uso de
  credencial pessoal, não é chamada de agente.
- **CNES `tipo_pessoa='1'` (deanonimização, ver seção do Agente E quando
  terminar)**: nomear 22,8M linhas de estabelecimento de saúde individual
  cruzando com cadastro de benefício social é decisão de privacidade sensível,
  explicitamente não tomada nem levantada antes — fica pro usuário decidir se
  quer isso feito, não é escolha automática.
