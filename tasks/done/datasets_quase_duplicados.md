# Datasets quase-duplicados no espelho

Levantamento (item 2 do TODO do harness Gemma) — **só survey, nenhum dataset
foi removido, renomeado ou mapeado**. `resolveDataset` e afins não foram tocados.

Método: `_rodado_metadata` por padrão de nome (`%antigo%`, `%novo%`, `%original%`,
`%backup%`, `%_v1/_v2%`) + inspeção manual de datasets com prefixo compartilhado
(`br_anp_combustiveis` / `br_anp_precos_combustiveis`, `br_seeg` / `br_seeg_emissoes`,
`br_ibama_embargos` / `br_ibama_embargos_novo`). Todas as contagens abaixo vieram
de `_rodado_metadata` ou `read_parquet(...)` direto no beelink, 2026-09-01.

## Prioridade alta — já diagnosticados, ação pendente

### 1. `br_ibama_embargos` × `br_ibama_embargos_novo`
**`br_ibama_embargos` está VAZIO** — bug de parsing no scraping original zerou os
bytes de toda subtabela (`max(length())=0`). Já documentado no próprio
`provenance_notes` de `br_ibama_embargos_novo`: *"Substitui `br_ibama_embargos`,
que está VAZIO... Consultas contra o antigo devolvem zero e parecem resposta
legítima. O dataset antigo deve ser removido ou marcado obsoleto."* — diagnosticado,
mas `br_ibama_embargos` continua com `status='done'`, não `blocked`/removido. Isso é
pior que uma duplicata redundante: uma pergunta contra o antigo roda, não dá erro, e
devolve zero linhas — parece "não há dado" quando na verdade há, só que na tabela
errada. **Canônico: `br_ibama_embargos_novo`.**

Tabelas (8 cada, quase idênticas): `coordenadas` (64.562), `decisao` (439),
`enquadramento` (137.997), `itens` (48.776), `termo_embargo` (113.878),
`termo_embargo_historico` (497.054) — mesma contagem nos dois; `enquadramento_complementar`
13.530→13.721 e `anexo`→`termo_de_embargo_anexo` 15.751→15.852 no novo (rescrape mais recente).

### 2. `br_seeg` × `br_seeg_emissoes`
Já conhecido (caso que motivou este levantamento). `br_seeg.emissoes_municipais`
(12.106.780 linhas) já está marcado `status = '**redundante — remover**'` em
`_rodado_metadata` — alguém já sinalizou, ainda não removido. **Canônico:
`br_seeg_emissoes.municipio`** (165.736.450 linhas, + `uf` agregado + `dicionario`
de decode) — mais granular e é o que tem dicionário de código.

## Prioridade média — dois datasets legítimos, mas confundíveis

### 3. `br_anp_combustiveis.precos` × `br_anp_precos_combustiveis.microdados`
Não são duplicata no sentido acima — cobrem janelas diferentes e um modelo
escolhendo errado dá resposta plausível mas de fonte/período errado, silenciosamente:

| | `br_anp_combustiveis.precos` | `br_anp_precos_combustiveis.microdados` |
|---|---|---|
| Linhas | 2.006.614 | 16.409.523 |
| Período | 2024-03-11 → 2026-07-24 | 2004 → 2026-02-06 |
| Origem | raspagem própria do projeto | espelho Base dos Dados |
| Localização | `municipio`/`estado` texto livre, `cnpj` **sem padding** (ver `bridges.yaml`/CLAUDE.md) | `id_municipio` (código IBGE), `sigla_uf` |
| Preço | só `preco_revenda` | `preco_compra` **e** `preco_venda` |

Ou seja: o espelho da BD tem histórico longo (22 anos) mas atrasa ~7 meses; a
raspagem própria é mais atual (~5 meses de defasagem a menos) mas cobre só 2 anos
e usa esquema de local não padronizado. Nenhum é redundante — mas nada em
`bridges.yaml`/`docs/context` diz qual usar para "preço atual" vs "preço histórico".
Sugestão: não fundir, só documentar a distinção (nota em `bridges.yaml` ou
`docs/overview/`), do jeito que `false_friends` já documenta outras ambiguidades.

## Prioridade baixa — provavelmente não são o problema

### 4. `br_cgu_beneficios_cidadao`: 5 pares tabela-base × `_original`
`auxilio_brasil`/`_original`, `auxilio_emergencial`/`_original`,
`bolsa_familia_pagamento`/`_original`, `bpc`/`_original`, `novo_bolsa_familia`/`_original`
— **mesma contagem de linha em cada par**, colunas quase idênticas (só ordem
diferente, ex. `cpf_favorecido`/`nis_favorecido` trocados). `source_type='mirror'`
nos dois lados — isso vem de cima, da própria Base dos Dados, não é raspagem
nossa. Provavelmente convenção do BD (uma versão "trabalhada", outra "como
capturada"), não um erro deste projeto. Não investiguei o porquê a fundo — mas como
é dentro do MESMO dataset (o modelo escolhe *tabela*, não *dataset*), o risco de
confusão de gabarito é menor que os casos acima. Fica registrado, sem prioridade.

### 5. `br_ibge_pib`: `municipio` (111.400) × `municipio_antigo` (77.910)
Contagens diferentes — parece série antiga por metodologia de cálculo do PIB
municipal revisada pelo IBGE, não um duplicado do mesmo dado. Mesmo padrão em
`brasil`/`brasil_antigo`, `regiao_antigo`, `uf`/`uf_antigo`. Não tratar como
redundante sem checar se cobre um período que o `municipio` atual não cobre —
fica como hipótese em aberto, não conclusão.

### 6. `br_me_rais_identificada.estabelecimentos` × `br_me_rais.microdados_estabelecimentos`
Escopo diferente por nome (identificada = com CNPJ/CPF reidentificado vs
microdados desidentificados padrão) — não parece duplicata, não aprofundei.

## Não verificado — fora do escopo deste levantamento
Não fiz uma varredura sistemática de todos os 207 datasets por sobreposição
semântica (só nome compartilhado + `_antigo`/`_novo`/`_original`). Pode haver
outros pares que não compartilham prefixo de nome e por isso não apareceram
nesta busca.

---

## ✅ Arquivado em 2026-09-02

Survey encerrado. Os itens **1 a 4** viraram ação e estão todos executados —
o plano e o registro de execução estão em
[`higiene_espelho.md`](higiene_espelho.md) (`br_ibama_embargos` e `br_seeg`
movidos para `~/rodado/_obsoleto/`; outlier do PNCP virou a métrica
`pncp_valor_total_contratos`; distinção ANP documentada em
`docs/overview/14_consumo_precos.md`).

Os itens **5 e 6** (pares `_antigo` de `br_ibge_pib`,
`br_me_rais_identificada` × `br_me_rais`) seguem sem ação **por decisão** —
são hipóteses de escopo diferente, não duplicatas. Nada pendente aqui; o
arquivo fica pelo método e pelas contagens brutas.
