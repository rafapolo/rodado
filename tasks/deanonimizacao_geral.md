# deanonimizacao_geral.md — nomear quem só aparece como CNPJ/CPF no espelho

Nasceu em 2026-08-26, depois de de-anonimizar `br_me_rais_identificada.estabelecimentos`
(36,16M linhas, 2010-2021): join por `cnpj_basico` contra `br_me_cnpj.empresas`/
`estabelecimentos` (snapshot set/2025) trouxe `cnpj_completo`, `nome_fantasia`,
`situacao_cadastral*` pra dentro da própria tabela. Taxa de match: 99,9995%.

**Baldes 1 e 2 executados em 2026-08-26.** Dez tabelas nomeadas in place. O Balde 2
mudou de fonte no meio do caminho: a fonte que o plano previa (`br_me_cnpj.socios`)
foi medida e descartada, e o trabalho foi refeito sobre os cadastros que publicam CPF
inteiro.

## Balde 1 — CNPJ sem nome — FEITO

Sete tabelas nomeadas in place, backup em `~/backups/<ds>_<tabela>__20260826/` no
beelink. Todas por igualdade exata de CNPJ contra o snapshot **2025-09** de
`br_me_cnpj` — nenhuma heurística de texto, nenhum resultado probabilístico.

| Tabela | Linhas | Colunas novas | Cobertura |
|---|---|---|---|
| `br_ms_cnes.estabelecimento` | 68,2M | `razao_social`, `nome_fantasia`, `situacao_cadastral_codigo`, `situacao_cadastral_descricao`, `razao_social_mantenedora` | **99,996%** das 45,4M linhas de PJ |
| `br_ms_sih.aihs_reduzidas` | 200,1M | `razao_social_estabelecimento`, `nome_fantasia_estabelecimento`, `razao_social_mantenedora`, `origem_nome_estabelecimento` | 84,7% com nome próprio, **98,9%** com algum nome |
| `br_bcb_sicor.operacao` | 27,2M | `razao_social_agente_investimento`, `razao_social_instituicao_financeira`, `razao_social_cadastrante` | **100,000%** |
| `br_bcb_sicor.recurso_publico_complemento_operacao` | 22,0M | `razao_social_agencia`, `nome_fantasia_agencia`, `sigla_uf_agencia`, `id_municipio_agencia` | **100,000%** |
| `br_bcb_sicor.recurso_publico_mutuario` | 17,1M | `razao_social_mutuario`, `razao_social_cnpj_basico` | **100,000%** das 37k linhas de PJ |
| `br_bcb_sicor.recurso_publico_propriedade` | 26,6M | `razao_social_cnpj_basico` | **100,000%** das 376k linhas de PJ |
| `br_bcb_sicor.recurso_publico_cooperado` | 152k | `razao_social_cnpj_basico` | **100,000%** das 1.886 linhas de PJ |
| `br_transferegov.transferencias` | 4.248 | `razao_social_favorecido`, `nome_fantasia_favorecido` | 100% — **mas ver a ressalva abaixo** |

O `lookup` compartilhado (332.009 CNPJs de 14 dígitos + 302.992 `cnpj_basico`) casou
**99,9946%** contra o snapshot; 18 CNPJs no total ficaram sem nome.

Vale registrar o que **não** foi feito e por quê: `razao_social` nunca cai pra
`razao_social_mantenedora`. Uma UBS não é a prefeitura, e um coalesce silencioso entre
os dois transformaria "quem é este estabelecimento" em "quem é o dono dele" sem avisar.
As duas colunas ficam separadas e quem analisa decide.

### As cinco armadilhas que a execução achou

Todas registradas em `docs/context/bridges.yaml` (e daí em `join_keys.md`), porque
nenhuma delas é visível no schema.

1. **`br_ms_sih.aihs_reduzidas.cnpj_estabelecimento` perde o zero à esquerda em
   37.115.348 linhas (18,5%)** — chegam com 13 dígitos. Sem `lpad(...,14,'0')` essas
   37M internações ficariam sem nome de hospital, em silêncio. É a mesma armadilha do
   `br_anp_combustiveis.precos` que o CLAUDE.md já documenta, num volume 20x maior.
2. **A mesma coluna guarda 14 espaços em branco, não NULL, em 47.490.278 linhas
   (23,7%).** `count(cnpj_estabelecimento)` conta essas linhas como preenchidas — foi o
   que fez a cobertura aparecer como 76% numa primeira leitura. Descontando os brancos,
   **todo CNPJ real casou: 100,000%.** Essas linhas foram nomeadas por outro caminho:
   `id_estabelecimento_cnes` → `br_ms_cnes.estabelecimento` (já nomeada) → nome. Daí a
   coluna `origem_nome_estabelecimento`, que diz `cnpj_aih` ou `cnes` conforme o
   caminho; ela é NULL quando não há nome próprio, mesmo que a mantenedora tenha nome.
3. **`br_ms_cnes.estabelecimento.cpf_cnpj` mistura CPF e CNPJ e só `tipo_pessoa`
   separa.** Com `tipo_pessoa='1'` são 11 dígitos de CPF alinhados à direita num campo
   de 14 (`00087978997120` = CPF 87978997120): 22,8M linhas que um join ingênuo joga
   contra a base de CNPJ. Essas são as únicas linhas do CNES que continuam sem nome.
4. **`br_transferegov.transferencias.cnpj_favorecido_empenho` não é quem recebeu** —
   4.218 das 4.248 linhas (99,3%, R$ 1,50 bi) são do **BANCO DO BRASIL SA**, o agente
   pagador; as outras 30 são governos estaduais. O destinatário final da transferência
   não está nessa coluna. Marcada como `false_friend`: agrupar gasto por ela produz um
   ranking de bancos com cara de ranking de beneficiários. A tabela foi nomeada mesmo
   assim (é barata), mas o nome que ela traz responde outra pergunta.
5. **`00000000` é um `cnpj_basico` legítimo — é o do Banco do Brasil.** Um filtro
   `NOT SIMILAR TO '0+'` para descartar lixo derrubou em silêncio as ~4.900 agências do
   BB e fez a taxa de match cair de 99,99% para 98,52%. A diferença entre as duas
   passadas foi o que denunciou o bug.

Achado lateral, fora do escopo: **`br_ms_sih.aihs_reduzidas.sigla_uf` é BIGINT e está
100% nula** nas 200M linhas — já era assim antes desta tarefa. Filtre por
`id_municipio_estabelecimento`, nunca por `sigla_uf`.

## Balde 2 — CPF sem nome — FEITO, por outra fonte

O plano original mandava juntar contra `br_me_cnpj.socios`. Duas medições derrubaram
isso, e uma terceira abriu o caminho que acabou sendo usado.

### 1. `br_me_cnpj.socios` é imprestável como fonte de nome — medido, não estimado

A Receita mascara o CPF de pessoa física (`tipo='2'`) em `***513278**`, sobrando 6
dígitos do meio. No snapshot 2025-09:

| | |
|---|---|
| máscaras distintas | **999.751** — praticamente todas as 10⁶ combinações |
| pares máscara/nome | 17.170.230 |
| nomes por máscara | **17,17** em média, 14 na mediana, 82 no pior caso |
| máscaras com um único nome | **0,18%** |

Um join por `substr(cpf,4,6)` devolve ~17 candidatos com ~5,8% de chance de acertar.
Não é um join com ruído — é um join sem sinal. Descartado.

### 2. `br_capes_bolsas.mobilidade_internacional` é falso positivo

A coluna `beneficiario` já traz o nome completo nas 146.036 linhas, e o `cpf` vem
mascarado (`***.321.977-**`) de qualquer jeito. **Nada a fazer** — saiu do balde.

### 3. O espelho tem CPF INTEIRO, e a nota do `bridges.yaml` dizia o contrário

O `bridges.yaml` afirmava que "as fontes públicas mascaram o CPF". Medido:

| Tabela | Linhas | Mascaradas | **CPF completo (11 dígitos)** |
|---|---|---|---|
| `br_cgu_servidores_executivo_federal.cadastro_servidores` | 168,1M | 3,85M (2,3%) | **159,6M (95%)** |
| `br_tse_filiacao_partidaria.microdados` | 17,2M | **0** | 16,6M |
| `br_cgu_beneficios_cidadao.novo_bolsa_familia` (2025) | 139,2M | 8,72M | **103,2M** |

Os portais de transparência publicam CPF completo com nome completo. O join é por
igualdade de 11 dígitos — exato, o oposto do que a máscara do `socios` oferecia.
`bridges.yaml` corrigido.

### O resultado

**3.425.540 dos 5.607.513 CPFs do SICOR nomeados — 61,09%**, por 16 fontes.
Três colunas novas nas três tabelas, tudo in place com backup:

| Tabela | Linhas | Com CPF | Nomeadas | % |
|---|---|---|---|---|
| `br_bcb_sicor.recurso_publico_mutuario` | 17,1M | 17.013.300 | 10.332.393 | **60,7%** |
| `br_bcb_sicor.recurso_publico_propriedade` | 26,6M | 26.174.028 | 14.365.214 | **54,9%** |
| `br_bcb_sicor.recurso_publico_cooperado` | 152k | 149.851 | 66.162 | **44,2%** |

As colunas são `nome_cpf`, `variantes_nome_cpf` e `origem_nome_cpf`.

**`origem_nome_cpf` é parte do dado, não metadado descartável.** Ela diz de qual
cadastro o nome veio — e quando o valor é `auxilio_emergencial` ou
`bolsa_familia_pagamento`, o fato de aquele produtor rural constar de uma lista de
benefício social viaja junto com o nome. 954.718 dos produtores nomeados vêm *só* do
auxílio emergencial; 675.356 aparecem nas quatro listas de benefício ao mesmo tempo.
Quem publicar análise em cima dessas colunas está publicando isso também, saiba ou não.

### Contribuição de cada fonte

| Fonte | CPFs do SICOR alcançados |
|---|---|
| `br_cgu_beneficios_cidadao.auxilio_emergencial` | 2.419.860 |
| `br_cgu_beneficios_cidadao.bolsa_familia_pagamento` | 1.292.892 |
| `br_cgu_beneficios_cidadao.novo_bolsa_familia` | 1.068.360 |
| `br_cgu_beneficios_cidadao.auxilio_brasil` | 1.059.432 |
| `br_tse_filiacao_partidaria.microdados` | 929.747 |
| `br_tse_eleicoes.candidatos` | 139.823 |
| `br_cgu_beneficios_cidadao.bpc` | 38.167 |
| `cgu_remuneracao` / `cadastro_servidores` / `observacoes` | 20.301 / 20.223 / 10.817 |
| `cadastro_aposentados` / `pensionistas` / `militares` | 7.328 / 3.141 / 1.344 |
| as três tabelas de `br_tcu_inidoneos` | 1.331 |

As seis fontes baratas sozinhas (TSE + CGU servidores + TCU) davam 17,31% em 13
segundos; as quatro tabelas de benefício levaram a 61,09% ao custo de ~2,8 bilhões de
linhas varridas, em ~1 min cada.

### Divergência entre fontes: 99,267% unânime

25.116 CPFs (0,73%) têm mais de uma grafia de nome. Inspecionadas, **são a mesma
pessoa** — acento (`JOSÉ` vs `JOSE`), ou nome de casada acrescentado (`ELENA MACIEL DA
SILVA` vs `ELENA MACIEL DA SILVA GOMES`). Nenhuma amostra mostrou pessoas diferentes
sob o mesmo CPF, o que era o risco real. O registro agrupa ignorando acento e exibe a
grafia mais completa; `variantes_nome_cpf` deixa a divergência visível em vez de
escondê-la atrás de um `mode()`.

### Duas armadilhas do Balde 2

6. **`br_cgu_beneficios_cidadao.bpc` tem UTF-8 inválido na origem** — o valor
   `"NELS(\x06~\xBDBw"` em `nome_favorecido` faz qualquer leitura da coluna abortar
   com `Invalid string encoding`. Está confinado a **2020-11**; os outros 83 meses leem
   limpo. Pior: `WHERE NOT (ano=2020 AND mes=11)` e `WHERE ano IN (...)` **não** podam
   o row group — o erro acontece na leitura, antes do filtro. Só varrer ano a ano com
   `=` funciona. Os beneficiários de 2020-11 reaparecem em 2019 e 2021, então a perda
   de cobertura é aproximadamente zero.
7. **`bpc_original` não é a cópia sã do `bpc`** — parece ser (lê sem erro de encoding),
   mas é o arquivo cru da CGU, com o CPF **mascarado** (`***.835.382-**`). O par
   `<tabela>` / `<tabela>_original` neste dataset é "tratada" vs "crua", não "boa" vs
   "quebrada". Usar a `_original` como fallback devolve zero linhas casadas — em
   silêncio, porque nenhum CPF de 11 dígitos casa com uma string mascarada.

## Como reproduzir / desfazer

Backups completos, um por tabela, em `~/backups/<dataset>_<tabela>__20260826/` no
beelink — estado **original**, antes de qualquer coluna nova. As três tabelas do SICOR
tocadas pelos dois baldes têm um segundo backup `__20260826_balde1`, com o estado
intermediário (só as colunas de CNPJ). Para desfazer: apagar o diretório em `~/rodado/<ds>/<tbl>/`, copiar o backup de
volta e recriar a view com o `read_parquet` apontando pros arquivos restaurados.

Os `lookup` intermediários ficaram em `~/staging/` no beelink
(`lookup_cnpj14.parquet`, `lookup_cnpj8b.parquet`, `lookup_cnes.parquet` para o Balde
1; `b2_alvo.parquet` e `b2_registro.parquet` para o Balde 2) — dá pra refazer qualquer
join sem varrer de novo os 2,4 bi de linhas de `br_me_cnpj.empresas` nem os 2,8 bi das
tabelas de benefício. `b2_registro.parquet` é o registro CPF→nome consolidado das 16
fontes: 3,4M linhas, e o insumo de qualquer extensão do Balde 2 a outras tabelas.

Toda a escrita rodou com `duckdb -readonly`: `COPY ... TO` grava parquet fora do banco
sem pegar o lock exclusivo. Só o `CREATE OR REPLACE VIEW` final precisa de conexão de
escrita, e leva segundos — foi o que manteve as outras sessões trabalhando durante a
reescrita inteira.

Depois desta tarefa foi rodado: `gera_schemas.py` → `sync_mcp_schema.py` →
`build_metadata_catalog.py` → `gera_join_keys.py` → `gera_metrics_json.py` →
`valida_metrics.py` → `gera_schema_graph.py` → `build_atlas.py` →
`gera_dicionario_coverage.py`. O espelho segue em **38.118.026.146 linhas** — nenhuma
linha ganha ou perdida em nenhuma das dez tabelas.

`sync_mcp_schema.py` não estava na lista do CLAUDE.md e **foi acrescentado**: sem ele o
`mcp_server.py` continua lendo o schema antigo e não enxerga nenhuma coluna nova —
`describe_table` mente calado.

## O que sobrou

- **`br_ms_cnes.estabelecimento`, `tipo_pessoa='1'`** — 22,8M linhas de estabelecimento
  de saúde registrado no CPF de uma pessoa física, hoje sem nome. O `b2_registro.parquet`
  já existe e o join seria de minutos; a decisão de nomear consultório individual por
  cadastro de benefício social não foi tomada nem levantada.
- **Os 38,91% do SICOR que ficaram sem nome** — são CPFs que não constam de nenhuma das
  16 fontes. Não há fonte no espelho que os alcance; só um cadastro que o espelho não
  tem resolveria.
- **Estender o Balde 2 a outras tabelas com CPF cru.** Nenhuma foi inventariada além das
  do SICOR: o inventário original só procurou tabelas com CPF **sem** coluna de nome, e a
  varredura que achou as 16 fontes (tabelas com CPF **e** nome) nunca foi virada do
  avesso para procurar alvos novos.

## Investigação 2026-08-27 — os três itens acima, sem escrever nada

### 1. CNES `tipo_pessoa='1'` — quantos casariam, SÓ contagem, nada escrito

`b2_registro.parquet` tem `cpf` (11 dígitos), `nome_cpf`, `variantes_nome_cpf`,
`origem_nome_cpf`. Extraí o CPF de `cpf_cnpj` com `substr(cpf_cnpj, 4, 11)` (confirma o
padrão descrito no achado #3 do Balde 1 — campo de 14, CPF alinhado à direita) e fiz um
`JOIN` só de leitura, sem `CREATE`/`COPY` nenhum:

| | |
|---|---|
| Linhas totais `tipo_pessoa='1'` | 22.832.840 (bate com o número já registrado) |
| Estabelecimentos distintos (`id_estabelecimento_cnes`) — a tabela é snapshot ano/mês, então as 22,8M linhas são muito menos estabelecimentos únicos | **180.573** |
| Estabelecimentos com match em `b2_registro` | **2.636 (1,46%)** |
| Linhas (ano/mês) que ganhariam nome | 405.795 de 22.832.840 (1,78%) |

Taxa de match **muito mais baixa** que os 61,09% do SICOR — esperado: profissionais de
saúde individuais não se sobrepõem tanto com as 16 fontes (que são majoritariamente
eleitoral/servidor público/benefício social) quanto mutuários rurais do SICOR.

**O detalhe que importa pra decisão**: dos 2.636 estabelecimentos que casariam, a origem
do nome se divide assim:

| Origem do nome | Estabelecimentos | % |
|---|---|---|
| **Só fontes "baratas"** (TSE filiação/candidatura, CGU servidores/aposentados/pensionistas/militares/observações, TCU) | 2.474 | **93,9%** |
| **Envolve alguma fonte de benefício social** (auxílio emergencial, bolsa família, auxílio Brasil, novo bolsa família, BPC) | 162 | **6,1%** |

Ou seja: a maior parte do match viria de registros já públicos por natureza (filiação
partidária, cargo público, candidatura) — não do cadastro de benefício social que motivou
a cautela original. Mas os 162 casos que **envolvem** benefício social são exatamente o
cenário que o arquivo aponta como sensível: um profissional/estabelecimento de saúde
individual cujo nome só se revela porque ele (ou alguém com o mesmo CPF) também consta de
uma lista de auxílio emergencial/bolsa família/BPC — o fato de estar nessa lista viaja
junto com o nome, do jeito que `origem_nome_cpf` já deixa explícito no Balde 2.

**Nada foi escrito.** Só o `COUNT`/`JOIN` de leitura acima rodou, via `duckdb -readonly`.
A decisão de fazer o join de verdade (e se faz com as 2.636 inteiras ou só as 2.474 "fontes
baratas", excluindo as 162 que arrastam o dado de benefício social) fica com quem for
decidir — não é chamada deste agente.

### 2. SICOR 38,91% sem nome — confirmado, ainda verdade

Recontei com a mesma lógica (CPF distinto across as 3 tabelas com CPF —
`recurso_publico_mutuario`, `recurso_publico_propriedade`, `recurso_publico_cooperado`):
**5.607.513 CPFs distintos, 2.181.973 sem nome, 38,91%** — exatamente o número já
registrado. Sem fonte nova no espelho que os alcance; item informativo, nenhuma ação
necessária.

### 3. Inventário de novos alvos pro Balde 2 (fora do SICOR)

Varri `docs/context/basedosdados-schema.json` (199 datasets, cobre todos os diretórios
reais do beelink — os 11 nomes que sobram no diff são `.claude`/`scripts`/`docs`/`logs`
etc., não datasets) procurando tabelas com **alguma coluna cujo nome contém `cpf`** e
**nenhuma coluna que pareça nome** (`nome`, `razao_social`, `denominacao`,
`beneficiario`, `favorecido`, `titular`, `responsavel`, `proprietario`, `socio`,
`servidor`, `fornecedor`, `contratado`, `mutuario`, `cooperado`, e ~30 outras raízes de
papel/função). 70 tabelas no total têm alguma coluna `*cpf*`; só 3 passaram pelo filtro
de "sem nome ao lado":

| Tabela | Coluna CPF | Por que não é um alvo real |
|---|---|---|
| `br_cvm_fundos.fundos` | `CPF_CNPJ_GESTOR` | **Falso positivo** — a tabela já tem `GESTOR` (nome do gestor da carteira) na coluna ao lado; meu filtro de palavras-chave não pegou "GESTOR". Já nomeada, só não parecia pelo nome da coluna. |
| `br_trase_supply_chain.soy_beans_storage_facilities` (+ `_original`) | `cnpj_cpf` | **Falso positivo** — coluna `company` já traz o nome, inclusive de pessoa física: conferido numa amostra, `cnpj_cpf="06128262015"` (11 dígitos, CPF) casa com `company="THEODORUS GERARDUS CORNELIS SANDERS"` na mesma linha. Já nomeada. |
| `br_ibama_embargos.decisao` | (schema malformado — colunas viraram uma string única separada por `;`, sinal de parse quebrado) | **Não é candidato de verdade**: `DESCRIBE br_ibama_embargos.decisao` no beelink dá `Catalog Error: schema "br_ibama_embargos" does not exist` — é o mesmo bloqueio de infra do IBAMA já documentado em `tasks/todo.md` ("IBAMA embargos reconfirmed infra-blocked"), não uma tabela viva. |

**Resultado do inventário: zero alvos novos.** As 70 tabelas com coluna `*cpf*` ou já têm
nome (a esmagadora maioria, incluindo os 2 falsos positivos acima) ou não existem de
verdade no beelink. O Balde 2 não tem pra onde se estender além do que já foi feito no
SICOR — pelo menos não por essa via (coluna literalmente chamada `cpf`); uma coluna de CPF
sem "cpf" no nome (ex. um campo genérico "documento") não entrou nesta varredura porque
o escopo pedido foi explicitamente esse.
