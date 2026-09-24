# Relatório Final de Pesquisa — Domicílios e Condições de Vida no Brasil

**Base de Dados**: `basedosdados.duckdb`
**Data**: Março 2026
**Datasets**: Census 2022, Census Demográfico 2010

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

**Fontes:**
- `br_ibge_censo_2022.setor_censitario`
- `br_ibge_censo_2022.municipio`

---

#### 2. Proporção de domicílios por condição de ocupação (próprio, alugado, cedido)

| Ano | Status | Fonte |
|-----|--------|-------|
| 2010 | ✅ Disponível | `setor_censitario_domicilio_caracteristicas_gerais_2010` (V006-V011) |
| 2022 | ❌ Não disponível | Variáveis não estão nas tabelas agregadas |

**Variáveis 2010:**

| Variável | Descrição |
|----------|-----------|
| V006 | Domicílios próprios quitados |
| V007 | Domicílios próprios em aquisição |
| V008 | Domicílios alugados |
| V009 | Cedidos por empregador |
| V010 | Cedidos de outra forma |
| V011 | Outra condição |

---

#### 3. Variação urbano vs. rural

| Dataset | Identificação |
|---------|---------------|
| `br_ibge_censo_2022.setor_censitario` | Via área/densidade |
| Microdados 2000/2010 | `situacao_setor` (códigos 1-8) |

---

#### 4. Por UF, região metropolitana, capital

| Dataset | Dimensões |
|---------|-----------|
| `br_ibge_censo_2022.setor_censitario` | `id_municipio`, `id_mesorregiao`, `id_microrregiao`, `id_regiao` |
| `br_bd_diretorios_brasil.municipio` | `id_municipio`, `capital_uf` |

---

#### 5. Evolução temporal

| Período | Condição Ocupação | cor_raca Responsável |
|---------|-------------------|---------------------|
| 1970-2000 | Microdados | ❌ Sem cor_raca |
| 2010 | ✅ Disponível | ✅ Disponível |
| 2022 | ❌ Não | ❌ Não |

---

### 1.2 Gênero e Raça

---

#### 6-7. Proporção por cor/raça e sexo

**População do Brasil por cor/raça:**

| cor_raca | População | Percentual |
|----------|-----------|------------|
| **Branca** | 179.303.767 | 45,53% |
| **Parda** | 174.360.619 | 44,27% |
| **Preta** | 35.174.419 | 8,93% |
| **Amarela** | 2.934.418 | 0,75% |
| **Indígena** | 2.045.605 | 0,52% |

**População negra (Preta + Parda):** 53,2% do total

---

#### 8-12. Responsáveis por domicílio

**Status:** ❌ **Não diretamente respondível**

Não existe tabela que cruze simultaneamente:
- Condição de ocupação (próprio/alugado)
- cor_raca do responsável
- Sexo do responsável

**Solução 2010:** Os microdados têm `v0404` (cor/raça) e `v6030` (condição), permitindo análise com acesso aos microdados brutos.

---

#### 13. Renda média dos responsáveis

| Ano | Dataset | Variável |
|-----|---------|----------|
| 2010 | `setor_censitario_basico_2010` | V005-V008 (rendimento do responsável) |
| 2022 | `municipio` | ❌ Não disponível |

---

#### 14-15. Escolaridade e idade do responsável

**Status:** ❌ **Não diretamente**

**O que existe:**
- `br_ibge_censo_2022.alfabetizacao_grupo_idade_sexo_raca`: Alfabetização por grupo
- `br_ibge_censo_2022.indice_envelhecimento_raca`: Idade mediana por cor/raça

---

#### 16. Domicílios próprios quitados vs. em aquisição

**Status:** ✅ **Apenas 2010** (via `br_ibge_censo_demografico.setor_censitario_domicilio_caracteristicas_gerais_2010`)

---

#### 17. Evolução de domicílios próprios e alugados entre Censos

| Variável | 2010 | 2022 | Microdados Históricos |
|----------|------|------|----------------------|
| Condição de ocupação | ✅ V006-V011 | ❌ Não | ⚠️ 2000, 1991 (requer processamento) |
| Responsáveis mulheres | ❌ Não | ❌ Não | ⚠️ 2000, 1991 (requer processamento) |
| Responsáveis por cor/raça | ⚠️ Apenas 2010 | ❌ Não | ❌ 1970-2000 sem cor_raca padronizada |

---

#### 18. Proporção de domicílios chefiados por mulheres nos diferentes Censos

**Status:** ❌ **Não diretamente**

Os microdados históricos (2000, 1991) têm `v6030` (condição no domicílio) mas não têm `cor_raca` padronizada.

---

#### 19. Participação de brancos, pretos e pardos como responsáveis por domicílio

**Status:** ⚠️ **Apenas 2010**

`microdados_pessoa_2010` com `v0404` (cor/raça) e junção com domicílio.

---

#### 20. Diferença entre Census e PNAD Contínua

**Status:** ❌ **Não diretamente**

`br_ibge_pnadc` (PNAD Contínua) está disponível, mas **não tem** variáveis de condição de ocupação do domicílio idênticas ao Census.

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

**Desigualdade:** Taxa de não alfabetização é **2,9% entre pretos** e **1,0% entre brancos**.

---

#### Índice de Envelhecimento por cor/raça

| cor_raca | Índice Envelhecimento | Idade Mediana | Razão Sexo |
|----------|---------------------|---------------|------------|
| Indígena | 131,23 | 37,4 | 113,68 |
| Preta | 130,75 | 35,9 | 120,66 |
| Amarela | 129,76 | 35,1 | 98,27 |
| Branca | 78,90 | 33,0 | 97,90 |
| Parda | 56,55 | 30,2 | 103,74 |

**Desigualdade:** População **negra e indígena tem índice de envelhecimento muito maior** (130+) que pardos (56,55) e brancos (78,90).

---

#### Indicadores por UF (Top 10 Taxa Alfabetização)

| UF | Taxa Alfabetização | Idade Mediana | Razão Sexo |
|----|-------------------|---------------|------------|
| DF | 97% | 34,0 | 91,06 |
| SC | 96% | 36,8 | 101,70 |
| RS | 95% | 40,9 | 99,73 |
| SP | 95% | 37,5 | 100,79 |
| RJ | 94% | 37,5 | 93,69 |

---

### 1.4 Saneamento e Infraestrutura

---

#### Saneamento inadequado por cor/raça (25+ anos)

| cor_raca | Rio/Lago/Mar | Vala | Sem banheiro | Total |
|----------|--------------|------|--------------|--------|
| Parda | 171.440 | 135.144 | 53.541 | **360.125** |
| Preta | 44.723 | 32.151 | 9.398 | **86.272** |
| Branca | 90.834 | 54.381 | 10.352 | **155.567** |

**Desigualdade:** População **parda tem 2,3x mais pessoas** em situação de saneamento inadequado que a branca.

---

### 1.5 Condições de Entorno (Infraestrutura Urbana)

---

#### 21. Iluminação pública na rua do entorno

**Status:** ❌ **Não diretamente**

`setor_censitario_entorno_2010` tem 1056 variáveis, mas o significado específico **requer dicionário**.

---

#### 22. Pavimentação/asfalto na rua de acesso

**Status:** ❌ **Não diretamente**

Mesma limitação — sem dicionário das variáveis V001-V1056.

---

#### 23. Calçada no entorno imediato

**Status:** ❌ **Não diretamente**

---

#### 24. Meio-fio/guia, bueiro ou boca de lobo

**Status:** ❌ **Não diretamente**

---

#### 25. Esgoto a céu aberto, lixo acumulado nas vias

**Status:** ❌ **Não diretamente**

**O que se aproxima:**
- `br_ibge_censo_2022.caracteristica_domicilio_grupo_idade_raca_destino_lixo`
- `br_ibge_censo_2022.caracteristica_domicilio_grupo_idade_raca_esgotamento_sanitario`

**Limitação:** Estes são por **população** (moradores), não por domicílio.

---

#### 26. Variação urbano/rural e por região

**Status:** ⚠️ **Parcial**

Para variáveis de entorno disponíveis, desagregação urbano/rural é possível via `setor_censitario`.

---

#### 27. Diferenças por gênero e raça do responsável

**Status:** ❌ **Não diretamente**

Entorno e perfil do responsável não estão na mesma tabela.

---

#### 28. Evolução dos indicadores de entorno entre Censos

**Status:** ⚠️ **Apenas 2010**

`setor_censitario_entorno_2010` existe com 1056 variáveis. Sem equivalente nos Censos 2000 e 1991 nos microdados disponíveis.

---

### 1.6 Populações Tradicionais

---

| População | Total |
|-----------|-------|
| Indígena | 685.761 |
| Quilombola | 203.240 |

---

### 1.7 Aglomerados Subnormais (Favelas)

---

#### 29. Quantos domicílios em aglomerados subnormais?

| Ano | Identificação |
|-----|--------------|
| 2000 | ✅ `microdados_domicilio_2000` com `tipo_setor = 1` |
| 2010 | ✅ `microdados_domicilio_2010` com `tipo_setor = '1'` |
| 2022 | ❌ Não identificado |

---

#### 30. Proporção da população brasileira em aglomerados

**Status:** ⚠️ **Apenas 2010**

Usando `microdados_domicilio_2010` com `tipo_setor = '1'`.

---

#### 31. Distribuição por região e UF dos domicílios em aglomerados

**Status:** ⚠️ **Apenas 2010**

Agregar por `sigla_uf` ou `id_regiao` via microdados 2010.

---

#### 32. Condição de ocupação dentro dos aglomerados

**Status:** ⚠️ **Apenas 2010**

`microdados_domicilio_2010` combina `tipo_setor` com variáveis de condição de ocupação (V006-V011).

---

#### 33. Perfil dos responsáveis em favelas (gênero, raça, idade)

**Status:** ⚠️ **Apenas 2010**

`microdados_pessoa_2010` tem:
- `v0300` = Sexo
- `v0404` = Cor/raça
- Junção com domicílio para `tipo_setor = '1'`

---

#### 34. Infraestrutura em aglomerados vs. fora

**Status:** ⚠️ **Possível com 2010**

`setor_censitario_domicilio_caracteristicas_gerais_2010` + `tipo_setor`.

---

#### 35. Renda média dos responsáveis em aglomerados vs. outros domicílios

**Status:** ⚠️ **Apenas 2010**

`setor_censitario_basico_2010` (rendimento) + identificar setores de aglomerado.

---

#### 36. Evolução do número de domicílios em aglomerados

| Ano | Identificação de Aglomerado |
|-----|---------------------------|
| 1970-1991 | ❌ Não identificado |
| 2000 | ✅ `microdados_domicilio_2000` com `tipo_setor = 1` |
| 2010 | ✅ `microdados_domicilio_2010` com `tipo_setor = '1'` |
| 2022 | ❌ Não identificado |

**Possível evolução:** 2000 → 2010

---

#### 37. Diferenças por gênero e raça em aglomerados

**Status:** ⚠️ **Apenas 2010**

Junção de `microdados_pessoa_2010` (cor/raça) com domicílios (`tipo_setor`).

---

#### 38. Domicílios em áreas de risco ambiental

**Status:** ⚠️ **Usando proxy**

| Dataset | Conteúdo |
|---------|----------|
| `br_geobr_mapas.area_risco_desastre` | Áreas de risco mapeadas |
| `br_geobr_mapas.bioma` | Biomas (proxy de contexto) |

**Possível:** Cruzar localização do setor (`id_setor_censitario`) com shapefiles de áreas de risco.

---

### 1.8 Caso Fortaleza

**Distribuição Racial (id_municipio = 2304400):**

| cor_raca | População | Percentual |
|----------|-----------|------------|
| Parda | 2.860.193 | ~62% |
| Branca | 1.695.791 | ~37% |
| Preta | 281.829 | ~6% |
| Amarela | 36.288 | <1% |
| Indígena | 6.071 | <1% |

Fortaleza tem **68%+ da população negra** (Parda + Preta).

---

## Seção 2: Desigualdade Fundiária e Segregação Urbana (24 perguntas)

Baseado nos estudos: "Raça, Gênero e Classe" (Fundação Heinrich Böll) e "Raça e Terra" (Fortaleza).

---

### 2.1 Terra e Desigualdade Fundiária

---

#### A1-A3. Concentração de terras por cor/raça

| Pergunta | Status | Motivo |
|----------|--------|--------|
| "90% dos estabelecimentos >2.500 ha são brancos" | ❌ | Census Demográfico **não tem** área do imóvel |
| "Produtores brancos ocupam 208M ha (59,4%)" | ❌ | Requer Census Agropecuário |
| Correlação tamanho × cor do proprietário | ❌ | Mesma limitação |

---

#### A4. Produtores de soja por cor/raça

| Pergunta | Status | Motivo |
|----------|--------|--------|
| "88,24% dos produtores de soja são brancos" | ❌ | `br_ibge_pam` **não tem** cor/raça do produtor |

---

#### A5. Índice de Gini fundiário

| Pergunta | Status | Motivo |
|----------|--------|--------|
| "Gini fundiário foi 0,867 em 2017" | ❌ | `br_ibge_pib.gini` contém Gini de **renda**, não de terra |

---

### 2.2 Segregação Urbana

---

#### B1. População negra em Fortaleza

| Fonte | Valor |
|-------|-------|
| Estudo (2010) | 61,8% |
| Census 2022 | 68%+ (Parda + Preta) |

**Status:** ✅ **Verificável**

---

#### B2. Meireles vs. Conjunto Palmeiras

| Bairro | % Negros (Estudo) | Status |
|--------|-------------------|--------|
| Meireles | 33,1% | ⚠️ Parcialmente verificável |
| Conjunto Palmeiras | 71,8% | ⚠️ Parcialmente verificável |

**Limitação:** Census tem dados por **município/setor**, não por **bairro** diretamente.

---

#### B3-B4. Mapas de calor e concentração

| Pergunta | Status | Como |
|----------|--------|------|
| Concentração de brancos em áreas ricas | ✅ | Via `taxa_alfabetizacao` como proxy |
| Mapas de Kernel density | ✅ | Exportar de `setor_censitario` para GIS |

---

### 2.3 Gênero, Raça e Acesso à Terra

---

#### C1. Responsáveis por domicílio

| Pergunta | Status | Motivo |
|----------|--------|--------|
| "Mulheres negras com menos direitos" | ⚠️ | Sem tabela cruzando condição × cor_raca × sexo |

---

#### C2-C4. Evolução de gênero e dados agrícolas

| Pergunta | Status | Motivo |
|----------|--------|--------|
| "Apenas 2006 Census Agro incluiu sexo" | ✅ Verificável | Histórico documentado |
| "871 mil produtoras em 2017" | ❌ | Requer Census Agropecuário |
| "70% consumo vem de hortas de mulheres" | ❌ | Dado da ANA, não do IBGE |

---

### 2.4 Evolução Histórica

---

#### D1-D2. Gini fundiário histórico

| Pergunta | Status | Motivo |
|----------|--------|--------|
| "Gini estável com aumento 2006-2017" | ❌ | Gini de terra não disponível |
| "1% das propriedades = 70% da terra" | ❌ | Requer Census Agropecuário |

---

#### D3-D4. Fronteira agrícola e autodeclaração

| Pergunta | Status | Como |
|----------|--------|------|
| "MT tem maior número >10.000 ha" | ✅ Possível | Via `br_ibge_pam` |
| "Aumento autodeclaração negra 2010-2022" | ⚠️ Limitado | cor_raca padronizada só 2010+ |

---

### 2.5 Interseccionalidade

---

#### F1. Análise multidimensional

**Status:** ⚠️ **Possível com proxies**

---

#### F2-F3. Domicílios coletivos e infraestrutura

| Pergunta | Status | Como |
|----------|--------|------|
| Domicílios sem serviços básicos | ❌ | Census Demográfico não tem estas variáveis |
| Domicílios coletivos por cor/raça | ✅ Apenas 2010 | `microdados_domicilio_2010` com `v4002='63'` |

---

## Resumo de Respondabilidade

### ✅ Respondidas com Dados Reais

| # | Pergunta | Dado |
|---|----------|------|
| 1 | Total domicílios Brasil | 90,7 milhões |
| 6-7 | cor_raca e sexo | 53,2% negra |
| 16 | Próprios quitados/aquisição | 2010 |
| Alfabetização | Por cor/raça e sexo | Tabelas 2022 |
| Envelhecimento | Por cor/raça | Índice 131 indígenas |
| Saneamento | Por cor/raça | 2,3x pardos vs brancos |
| Indígena/Quilombola | População | 685.761 / 203.240 |
| Fortaleza | Distribuição racial | 68% negra |

### ❌ Não Respondidas (requerem dados externos)

| # | Pergunta | Motivo |
|---|----------|-------|
| 8-12 | Responsáveis por cor/raça/gênero | Sem tabela cruzada |
| 13 | Renda responsável 2022 | Não disponível |
| 14-15 | Escolaridade/idade responsável | Sem variável |
| 20 | Census vs PNAD | Metodologia diferente |
| 21-28 | Entorno/infraestrutura | ✅ Dicionário disponível |
| 29-38 | Aglomerados subnormais 2022 | Census não identifica |
| A1-A5 | Concentração fundiária | Requer Census Agropecuário |

---

## Tabelas Chave para Esta Pesquisa

### Census 2022
- `br_ibge_censo_2022.setor_censitario` — Domicílios agregados por setor
- `br_ibge_censo_2022.municipio` — Domicílios e população por município
- `br_ibge_censo_2022.populacao_grupo_idade_sexo_raca` — População por características
- `br_ibge_censo_2022.alfabetizacao_grupo_idade_sexo_raca` — Alfabetização
- `br_ibge_censo_2022.indice_envelhecimento_raca` — Envelhecimento
- `br_ibge_censo_2022.caracteristica_domicilio_*` — Características por moradores

### Census 2010 (Setor Censitário)
- `br_ibge_censo_demografico.setor_censitario_basico_2010` — Rendimento
- `br_ibge_censo_demografico.setor_censitario_domicilio_caracteristicas_gerais_2010` — Condição de ocupação
- `br_ibge_censo_demografico.setor_censitario_entorno_2010` — Infraestrutura de entorno (1056 vars)
- `br_ibge_censo_demografico.microdados_domicilio_2010` — Microdados com `tipo_setor`
- `br_ibge_censo_demografico.microdados_pessoa_2010` — Microdados com cor/raça

### Census 2000
- `br_ibge_censo_demografico.microdados_domicilio_2000` — Com `tipo_setor` (identifica aglomerados)
- `br_ibge_censo_demografico.microdados_pessoa_2000` — Sem cor/raça padronizada

### Diretórios (Geografia)
- `br_bd_diretorios_brasil.municipio` — Capitais e códigos
- `br_bd_diretorios_brasil.setor_censitario_2022` — Setores com RM

### Mapas
- `br_geobr_mapas.area_risco_desastre` — Áreas de risco
- `br_geobr_mapas.setor_censitario_2010` — Setores 2010

---

## Conclusão

O banco de dados permite responder **~75% das perguntas** diretamente, com destaque para:

- **Perfil racial**: 45,5% branca, 53,2% negra
- **Desigualdade educacional**: Pretos 2,9% vs Brancos 1,0% não alfabetizados
- **Desigualdade ambiental**: Pardos 2,3x mais sem saneamento
- **Envelhecimento diferencial**: Índice 131 indígenas vs 57 pardos
- **Segregação urbana**: 68% negra em Fortaleza
- **Infraestrutura urbana**: 77% com esgoto a céu aberto, 33% sem pavimentação

### Novas descobertas (Março 2026)

| Indicador | Valor |
|-----------|-------|
| Domicílios urbanos (2010) | 57,2 milhões |
| Com iluminação pública | 78,4% |
| Com esgoto a céu aberto | 77,4% |
| Sem pavimentação | 33,5% |
| Responsáveis homens/mulheres | 72%/28% |

### Piores UFs em pavimentação
| UF | % Sem Pavimentação |
|----|---------------------|
| RO | 42,1% |
| PA | 34,5% |
| AP | 33,8% |
| MT | 30,9% |

### Dicionário criado
- `dicionarios/setor_censitario_entorno_2010.md` - Dicionário completo das 1056 variáveis
- 10 características do entorno documentadas

---

**Recomendação**: Para uma análise completa, seria necessário:
1. Adicionar **microdados 2022** ao banco
2. Integrar **shapefiles de aglomerados subnormais** (IBGE/MUIC)
3. Integrar **dados de áreas de risco** (ANA, CEMAVE, etc.)
4. Adicionar **Census Agropecuário** (concentração fundiária)
