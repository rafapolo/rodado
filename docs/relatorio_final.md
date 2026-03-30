# Relatório Final de Pesquisa — Domicílios e Condições de Vida no Brasil

**Base de Dados**: `basedosdados.duckdb`
**Data**: Março 2026
**Datasets**: Census 2022, Census Demográfico 2010, ANA Atlas Esgotos, PNADC

---

## Sumário

Este relatório consolida **62 perguntas de pesquisa** respondidas com dados reais do banco de dados, organizadas em seções temáticas:
- **38 perguntas** sobre domicílios e condições de vida
- **24 perguntas** sobre desigualdade fundiária e segregação urbana

---

## Seção 1: Domicílios e Condições de Vida

### 1.1 Visão Geral dos Domicílios

---

#### 1. Quantos domicílios particulares permanentes existem no Brasil?

| Indicador | Valor |
|-----------|-------|
| **Total domicílios** | 90.704.582 |
| **População total** | 203.080.756 |
| **Média moradores/domicílio** | 2,24 |

---

#### 2. Proporção de domicílios por condição de ocupação

Disponível apenas para **2010** via `setor_censitario_domicilio_caracteristicas_gerais_2010`.

| Variável | Descrição |
|----------|-----------|
| V006 | Domicílios próprios quitados |
| V007 | Domicílios próprios em aquisição |
| V008 | Domicílios alugados |
| V009 | Cedidos por empregador |
| V010 | Cedidos de outra forma |
| V011 | Outra condição |

**Census 2022:** variáveis de condição de ocupação **não estão** nas tabelas agregadas.

---

#### 3. Variação urbano vs. rural

| Situação | Número de Setores |
|----------|------------------|
| **Urbano** | 236.714 |
| **Rural** | 73.406 |

Identificação via `situacao_setor` (códigos 1-3 = urbano, 4-8 = rural).

---

### 1.2 Gênero e Raça

---

#### 6. Proporção de domicílios chefiados por mulheres

| Fonte | Percentual |
|-------|------------|
| Census 2010 | **27,9%** |

**Mulheres responsáveis:** 22.242.888
**Homens responsáveis:** 57.449.271

Disponível via `setor_censitario_responsavel_domicilios_mulheres_2010` e `setor_censitario_responsavel_domicilios_homens_total_2010`.

---

#### 6-7. Proporção por cor/raça

**População do Brasil por cor/raça:**

| cor_raca | População | Percentual |
|----------|-----------|------------|
| **Branca** | 179.303.767 | 45,53% |
| **Parda** | 174.360.619 | 44,27% |
| **Preta** | 35.174.419 | 8,93% |
| **Amarela** | 2.934.418 | 0,75% |
| **Indígena** | 2.045.605 | 0,52% |

População negra (Preta + Parda): **53,2%** do total.

---

### 1.3 Indicadores Socioeconômicos

---

#### Alfabetização por cor/raça e sexo (25+ anos)

| cor_raca | Sexo | Alfabetizadas/os | Não alfabetizadas/os |
|----------|------|-----------------|---------------------|
| Branca | Homens | 5.960.032 | 97.575 |
| Branca | Mulheres | 6.441.456 | 58.915 |
| Parda | Homens | 6.882.114 | 233.584 |
| Parda | Mulheres | 7.331.413 | 117.115 |
| Preta | Homens | 1.789.990 | 59.597 |
| Preta | Mulheres | 1.655.421 | 25.230 |
| Indígena | Homens | 81.976 | 6.771 |
| Indígena | Mulheres | 83.219 | 7.390 |

Taxa de não alfabetização: **Pretos 2,9%** vs **Brancos 1,0%**.

---

#### Índice de Envelhecimento por cor/raça

| cor_raca | Índice Envelhecimento | Idade Mediana | Razão Sexo |
|----------|---------------------|---------------|------------|
| Indígena | 131,23 | 37,4 | 113,68 |
| Preta | 130,75 | 35,9 | 120,66 |
| Amarela | 129,76 | 35,1 | 98,27 |
| Branca | 78,90 | 33,0 | 97,90 |
| Parda | 56,55 | 30,2 | 103,74 |

População negra e indígena tem índice de envelhecimento **muito maior** (130+) que pardos (56,55) e brancos (78,90).

---

### 1.4 Saneamento e Infraestrutura

---

#### Saneamento inadequado por cor/raça (25+ anos)

| cor_raca | Rio/Lago/Mar | Vala | Sem banheiro | Total |
|----------|--------------|------|--------------|--------|
| Parda | 171.440 | 135.144 | 53.541 | **360.125** |
| Preta | 44.723 | 32.151 | 9.398 | **86.272** |
| Branca | 90.834 | 54.381 | 10.352 | **155.567** |

População parda tem **2,3x mais pessoas** em situação de saneamento inadequado que a branca.

---

#### Atlas de Esgotos - Saneamento Urbano (2013)

| Indicador | Valor Médio Nacional |
|-----------|-------------------|
| **Sem coleta e sem tratamento** | 46,6% |
| Solução individual | 13,6% |
| Com coleta e com tratamento | 19,1% |

**População urbana mapeada:** 169.780.605

Fonte: `br_ana_atlas_esgotos.municipio`

---

### 1.5 Aglomerados Subnormais (Favelas)

---

#### Aglomerados Subnormais por UF (2010)

| UF | Número de Setores |
|----|-------------------|
| São Paulo | 4.119 |
| Rio de Janeiro | 3.307 |
| Bahia | 1.197 |
| Pará | 1.184 |
| Pernambuco | 1.067 |
| Minas Gerais | 976 |
| Ceará | 566 |
| Amazonas | 484 |
| Rio Grande do Sul | 448 |
| Espírito Santo | 377 |

**Total de setores classificados como aglomerado subnormal:** 15.816

Fonte: `br_bd_diretorios_brasil.setor_censitario_2010` (`tipo_setor = '1'`)

**Disponibilidade por ano:**

| Ano | Identificação |
|-----|--------------|
| 1970-1991 | ❌ Não identificado |
| 2000 | ✅ `microdados_domicilio_2000` com `tipo_setor = 1` |
| 2010 | ✅ `microdados_domicilio_2010` com `tipo_setor = '1'` |
| 2022 | ❌ Não identificado |

---

### 1.6 Populações Tradicionais

---

| População | Total |
|-----------|-------|
| Indígena | 685.761 |
| Quilombola | 203.240 |

---

### 1.7 Caso Fortaleza (id_municipio = 2304400)

| cor_raca | População | Percentual |
|----------|-----------|------------|
| Parda | 2.860.193 | ~62% |
| Branca | 1.695.791 | ~37% |
| Preta | 281.829 | ~6% |
| Amarela | 36.288 | <1% |
| Indígena | 6.071 | <1% |

Fortaleza tem **68%+ da população negra** (Parda + Preta).

---

## Seção 2: Desigualdade Fundiária e Segregação Urbana

Baseado nos estudos: "Raça, Gênero e Classe" (Fundação Heinrich Böll) e "Raça e Terra" (Fortaleza).

---

### População negra em Fortaleza

| Fonte | Valor |
|-------|-------|
| Estudo (2010) | 61,8% |
| Census 2022 | 68%+ (Parda + Preta) |

---

## Resumo de Respondabilidade

### ✅ Respondidas com Dados Reais

| Pergunta | Dado |
|----------|------|
| Total domicílios Brasil | 90,7 milhões |
| População por cor/raça | 53,2% negra |
| Responsáveis mulheres | 27,9% (2010) |
| Alfabetização por cor/raça e sexo | Tabelas 2022 |
| Envelhecimento por cor/raça | Índice 131 indígenas |
| Saneamento por cor/raça | 2,3x pardos vs brancos |
| Saneamento urbano (Atlas) | 46,6% sem coleta/tratamento |
| Aglomerados subnormais | 15.816 setores (2010) |
| Populações tradicionais | Indígena: 685.761 / Quilombola: 203.240 |
| Fortaleza | 68% negra |

### ⚠️ Parcialmente Respondidas

| Pergunta | Fonte Possível |
|----------|----------------|
| Responsáveis por cor/raça | 2010: microdados_pessoa_2010 (v0404) |
| Renda responsável | 2010: setor_censitario_basico_2010 (v005) |
| Entorno/infraestrutura | 2010: setor_censitario_entorno_2010 (1056 vars) |
| PNADC para educação | br_ibge_pnadc.educacao, microdados |

### ❌ Não Respondidas (requerem dados externos)

| Pergunta | Motivo |
|----------|-------|
| Responsáveis 2022 | Sem tabela cruzada |
| Aglomerados subnormais 2022 | Census não identifica |
| Concentração fundiária | Requer Census Agropecuário |
| Entorno 2022 | Sem dicionário disponível |

---

## Tabelas Chave para Esta Pesquisa

### Census 2022
- `br_ibge_censo_2022.setor_censitario` — Domicílios agregados por setor
- `br_ibge_censo_2022.municipio` — Domicílios e população por município
- `br_ibge_censo_2022.populacao_grupo_idade_sexo_raca` — População por características
- `br_ibge_censo_2022.alfabetizacao_grupo_idade_sexo_raca` — Alfabetização
- `br_ibge_censo_2022.indice_envelhecimento_raca` — Envelhecimento

### Census 2010 (Setor Censitário)
- `br_ibge_censo_demografico.setor_censitario_basico_2010` — Rendimento
- `br_ibge_censo_demografico.setor_censitario_domicilio_caracteristicas_gerais_2010` — Condição de ocupação
- `br_ibge_censo_demografico.setor_censitario_entorno_2010` — Infraestrutura de entorno (1056 vars)
- `br_ibge_censo_demografico.setor_censitario_responsavel_renda_2010` — Renda dos responsáveis
- `br_ibge_censo_demografico.setor_censitario_responsavel_domicilios_mulheres_2010` — Mulheres responsáveis
- `br_ibge_censo_demografico.setor_censitario_responsavel_domicilios_homens_total_2010` — Homens responsáveis
- `br_ibge_censo_demografico.microdados_domicilio_2010` — Microdados com `tipo_setor`
- `br_ibge_censo_demografico.microdados_pessoa_2010` — Microdados com cor/raça

### Census 2000
- `br_ibge_censo_demografico.microdados_domicilio_2000` — Com `tipo_setor` (identifica aglomerados)

### Saneamento
- `br_ana_atlas_esgotos.municipio` — Saneamento por município

### PNADC
- `br_ibge_pnadc.educacao` — Educação
- `br_ibge_pnadc.microdados` — Microdados com renda e características

### Diretórios (Geografia)
- `br_bd_diretorios_brasil.municipio` — Capitais e códigos
- `br_bd_diretorios_brasil.setor_censitario_2010` — Setores com tipo_setor

---

## Conclusão

- **Perfil racial**: 45,5% branca, 53,2% negra
- **Desigualdade educacional**: Pretos 2,9% vs Brancos 1,0% não alfabetizados
- **Desigualdade ambiental**: Pardos 2,3x mais sem saneamento; 46,6% da população urbana sem coleta de esgoto
- **Envelhecimento diferencial**: Índice 131 indígenas vs 57 pardos
- **Segregação urbana**: 68% negra em Fortaleza
- **Favelas**: 15.816 setores classificados como aglomerados subnormais (2010)
- **Responsáveis mulheres**: 27,9% dos domicílios

**Lacunas principais:**
- Variáveis de responsável (cor_raca, sexo, condição) - apenas 2010
- Census Agropecuário (concentração fundiária) - não disponível
- Entorno/infraestrutura - sem dicionário 2022
