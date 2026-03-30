# br_ibge_censo — População Carcerária e Domicílios Coletivos

## Visão Geral

Conjunto de datasets do IBGE sobre censos demográficos. A questão central: **como identificar pessoas privadas de liberdade nos dados do IBGE?**

**Resumo**: O Census 2010 (`br_ibge_censo_demografico`) **tem** variável específica para presídio. O Censo 2022 (`br_ibge_censo_2022`) **não tem** — domicílios coletivos são agregados sem quebra por tipo de estabelecimento.

---

## Como o IBGE classifica domicílios coletivos vs. presídios

O IBGE usa o conceito estatístico de "domicílio" onde **prisões são classificadas como domicílios coletivos**. Pessoas privadas de liberdade são contadas como **residentes do endereço do estabelecimento prisional** — isto é, estão geograficamente no setor censitário onde a prisão está localizada.

### Tipos de espécie de domicílio (IBGE)

| Código | Espécie |
|--------|---------|
| 1 | Particular permanente |
| 2 | Particular permanente não ocupado (vago) |
| 3 | Particular permanente não ocupado (uso ocasional) |
| 4 | Particular improvisado |
| 5 | Coletivo - com morador |
| 6 | Coletivo - sem morador |

---

## br_ibge_censo_demografico (2010)

### microdados_domicilio_2010 — ✅ Tem presídio

**Tabela**: `br_ibge_censo_demografico.microdados_domicilio_2010`

A variável **`v4002`** identifica o **tipo de domicílio** com categoria específica para presídio:

| Código v4002 | Descrição | Count (~2010) |
|---|---|---|
| 11 | Casa | 5.608.489 |
| 12 | Casa de vila ou em condomínio | 72.657 |
| 13 | Apartamento | 408.530 |
| 14 | Habitação em casa de cômodos, cortiço ou cabeça de porco | 21.809 |
| 15 | Oca ou maloca | 2.402 |
| 51 | Tenda ou barraca | 5.014 |
| 52 | Wagon, trailer, gruta, etc. | 7.180 |
| 53 | Alojamento de trabalhadores com morador | 1.825 |
| 61 | Hotel, pensão e similares com morador | 18.186 |
| 62 | **Asilo, orfanato e similares com morador** | 4.752 |
| **63** | **Penitenciária, presídio e casa de detenção com morador** | **5.449** |
| 64 | Outro com morador | 32.517 |
| 65 | Dentro do estabelecimento | 3.522 |

**Código 63 = penitenciária/presídio/casa de detenção**, com **5.449 domicílios coletivos** classificados como prisão.

**Como usar para encontrar população carcerária**:

1. `microdados_domicilio_2010` — filtra `v4002 = '63'`
2. Join com `microdados_pessoa_2010` via `id_domicilio`
3. Agregar por setor censitário

### setor_censitario_idade_*_2010 — Residentes em domicílios coletivos

As tabelas de idade por setor incluem a variável **`v021`** para "indivíduos em domicílio coletivo":

- `setor_censitario_idade_homens_2010` → `v021 = "Individuais em domicílio coletivo, do sexo masculino"`
- `setor_censitario_idade_mulheres_2010` → `v021 = "Individuais em domicílio coletivo do sexo feminino"`
- `setor_censitario_idade_total_2010` → `v021 = "Individuais em domicílio coletivo"`

**Limitações**: não distingue presídio de asilo/hotel/outro coletivo.

---

## br_ibge_censo_2022

### domicilio_recenseado — ❌ Não distingue presídio

**Tabela**: `br_ibge_censo_2022.domicilio_recenseado`

A coluna `especie` tem categorias genéricas:

```
- Coletivo
- Coletivo - com morador
- Coletivo - sem morador
- Particular
- Particular improvisado
- Particular permanente
- Particular permanente não ocupado
- Particular permanente não ocupado - uso ocasional
- Particular permanente não ocupado - vago
- Particular permanente ocupado
- Particular permanente ocupado - com entrevista
- Particular permanente ocupado - sem entrevista
```

**Não há quebra por tipo de domicílio coletivo** — presídios estão agregados junto com hotéis, asilos, orfanatos, etc.

### cadastro_enderecos — ❌ Não distingue presídio

**Tabela**: `br_ibge_censo_2022.cadastro_enderecos`

| Campo | Descrição |
|---|---|
| `tipo_especie` | "Domicílio coletivo" (código 3 ou 8), "Domicílio particular" (código 1), etc. |
| `tipo_estabelecimento` | Único, Múltiplo (1-10), Múltiplo (>10), Desconhecido — **não identifica presídio** |
| `descricao_estabelecimento` | Free-text — pode conter "presídio", "penitenciária", etc. mas **não é confiável** |
| `tipo_edificacao_domicilio` | Casa, Apartamento, Casa de vila, Outros — não se aplica a coletivos |

**Não existe variável que identifique presídio especificamente.**

### setor_censitario — ❌ Sem granularidade

**Tabela**: `br_ibge_censo_2022.setor_censitario`

Coluna `domicilios_coletivos` = `DCCM + DCSM` (soma de todos domicílios coletivos, sem quebra por tipo).

As **1.411 variáveis agregadas** (`v00001`–`v01411`) não incluem nenhuma quebre por tipo de domicílio coletivo.

---

## br_ibge_pnad

**Tabela**: `br_ibge_pnad.microdados_compatibilizados_domicilio`

A coluna `especie_domicilio` tem apenas 3 categorias:

```
1 = particular permanente
3 = particular improvisado
5 = coletivo
```

**Não identifica presídio.**

---

## br_fbsp_absp — Fonte Alternativa

**Tabela**: `br_fbsp_absp.uf`

| Coluna | Descrição |
|---|---|
| `quantidade_populacao_sistema_penitenciario` | População total do sistema prisional por UF/ano |

- **Granularidade**: UF
- **Período**: séries anuais (Anuário Brasileiro de Segurança Pública)
- **Não tem**: setor censitário, município

---

## Conclusão

| Fonte | Granularidade presídio? | Via |
|---|---|---|
| `br_ibge_censo_demografico.microdados_domicilio_2010` | ✅ `v4002 = '63'` | join pessoa → setor |
| `br_ibge_censo_demografico.setor_censitario_*_2010` | ⚠️ domicílio coletivo genérico | v021 (sem presídio específico) |
| `br_ibge_censo_2022.setor_censitario` | ❌ não | agregado sem quebra |
| `br_ibge_censo_2022.cadilio_recenseado` | ❌ não | só genérico |
| `br_ibge_censo_2022.cadastro_enderecos` | ❌ não | free-text não confiável |
| `br_ibge_pnad.microdados_compatibilizados_domicilio` | ❌ não | só "coletivo" |
| `br_fbsp_absp.uf` | ⚠️ total UF | `quantidade_populacao_sistema_penitenciario` |

**O Censo 2022 perdeu a granularidade de presídio** que existia no 2010 via `v4002`.

### Recomendações

1. **Análise por setor censitário**: usar `br_ibge_censo_demografico.microdados_domicilio_2010` com `v4002 = '63'`, join com `microdados_pessoa_2010` via `id_domicilio`.
2. **Dados mais recentes por UF**: `br_fbsp_absp.uf.quantidade_populacao_sistema_penitenciario`.
3. **Para 2022**: não é possível identificar pop. carcerária por setor — apenas via dados administrativos do DEPEN (Ministério da Justiça).
