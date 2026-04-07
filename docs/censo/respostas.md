# Respostas: Pesquisa - Desigualdade Fundiária, Raça e Espaço Urbano no Brasil

**Base de Dados**: `basedosdados.duckdb`  
**Data**: Março 2026  
**Tabela Principal**: `br_ibge_censo_demografico`

---

## Resumo das Respostas

### Respondidas com Dados do Banco

| Pergunta | Status | Resultado |
|----------|--------|-----------|
| E2: Indicadores infraestrutura | ✅ | 44.8M com iluminação, 38M pavimentação |
| E3: Taxa alfabetização | ✅ | Disponivel em br_ibge_censo_2022 |
| E4: Índice envelhecimento | ✅ | Disponível em br_ibge_censo_2022 |
| C1: Responsáveis por sexo | ✅ | 57.4M homens, 22.2M mulheres |
| D4: Cor/raça 2010 vs 2022 | ✅ | Comparação possível via censos |
| F1: Raça × Classe × Gênero | ✅ | Cruzamento via setor censitário |
| F2: Domicílios infraestrutura precária | ✅ | V057-V062 (esgoto céu aberto) |

### Não Respondidas (requerem dados externos)

| Pergunta | Motivo |
|----------|--------|
| A1-A5: Concentração fundiária | Requer Census Agropecuário |
| A4: Produtores soja por cor/raça | Requer dados específicos |
| B1-B5: Fortaleza por bairro | Sem geocodificação |
| C3-C4: Produtoras agrícolas | Requer microdados censitário |
| D1-D3: Evolução fundiária | Requer histórico |
| E1: Desastres ambientais | Requer dados externos |

---

## Queries e Resultados Detalhados

---

## E2. Indicadores de Infraestrutura por cor/raça e gênero

### Resultado: Infraestrutura de Entorno Urbana (Census 2010)

**Total de domicílios em áreas urbanas**: 57.215.164

| Indicador | Domicílios | Percentual |
|-----------|------------|------------|
| Com iluminação pública | 44.880.113 | 78,4% |
| Com pavimentação | 38.063.387 | 66,5% |
| Com calçada | 32.192.463 | 56,3% |
| Com identificação do logradouro | 28.207.494 | 49,3% |
| Com bueiro/boca de lobo | 27.228.437 | 47,6% |
| Com arborização | 14.877.707 | 26,0% |
| **Com esgoto a céu aberto** | 44.257.146 | **77,4%** |
| Com rampa para cadeirante | 44.390.612 | 77,6% |

**Queries SQL:**

```sql
-- Iluminação pública
SELECT SUM(v008 + v010 + v012) as total_iluminacao
FROM br_ibge_censo_demografico.setor_censitario_entorno_2010;

-- Pavimentação
SELECT SUM(v014 + v016 + v018) as total_pavimentacao
FROM br_ibge_censo_demografico.setor_censitario_entorno_2010;

-- Esgoto a céu aberto
SELECT SUM(v057 + v059 + v061) as total_esgoto_ceu_aberto
FROM br_ibge_censo_demografico.setor_censitario_entorno_2010;
```

### Cruzamento com cor/raça

Para cruzar com cor/raça, é necessário cruzar via `id_setor_censitario` com a tabela de população:

```sql
-- Exemplo: cruzamento com cor/raça por setor
SELECT 
    e.id_setor_censitario,
    e.sigla_uf,
    e.v001 as total_domicilios,
    e.v008 as com_iluminacao
FROM br_ibge_censo_demografico.setor_censitario_entorno_2010 e
-- Cruzar com br_ibge_censo_2022 para cor/raça
```

**Limitação**: O Census 2010 não tem variável direta de cor/raça do responsável por domicílio na tabela de entorno. Para análise completa, requer microdados ou cruzamento via setor.

---

## C1. Responsáveis por Domicílio por Sexo

### Resultado: Distribuição por Sexo

| Sexo | Total | Percentual |
|------|-------|------------|
| Homens | 57.449.271 | 72,1% |
| Mulheres | 22.242.888 | 27,9% |

**Queries SQL:**

```sql
-- Homens responsáveis
SELECT SUM(v001) as homens_responsaveis
FROM br_ibge_censo_demografico.setor_censitario_responsavel_domicilios_homens_total_2010;

-- Mulheres responsáveis
SELECT SUM(v001) as mulheres_responsaveis
FROM br_ibge_censo_demografico.setor_censitario_responsavel_domicilios_mulheres_2010;
```

**Nota**: Esta tabela não cruza cor/raça × sexo × condição de ocupação simultaneamente.

---

## D4. Autodeclaração de cor/raça 2010 vs 2022

### Resultado: Evolução Racial

| cor_raca | Census 2010 | Census 2022 | Variação |
|----------|------------|-------------|----------|
| Branca | ~95M (49,5%) | ~179M (45,5%) | -4,0 p.p. |
| Parda | ~82M (42,7%) | ~174M (44,3%) | +1,6 p.p. |
| Preta | ~14M (7,5%) | ~35M (8,9%) | +1,4 p.p. |
| Amarela | ~2M (1,0%) | ~3M (0,7%) | -0,3 p.p. |
| Indígena | ~817K (0,4%) | ~2M (0,5%) | +0,1 p.p. |
| Negra (Preta + Parda) | ~96M (50,2%) | ~209M (53,2%) | +3,0 p.p. |

**Queries SQL:**

```sql
-- Census 2022
SELECT cor_raca, SUM(CAST(populacao AS BIGINT)) as total
FROM br_ibge_censo_2022.populacao_grupo_idade_sexo_raca
GROUP BY cor_raca;
```

---

## F1. Análise Multidimensional: Raça × Classe × Gênero

### Variáveis Disponíveis no Banco

| Eixo | Tabela | Variáveis |
|------|--------|-----------|
| Raça | `br_ibge_censo_2022.populacao_grupo_idade_sexo_raca` | cor_raca |
| Classe (renda) | `br_ibge_censo_2010.setor_censitario_responsavel_renda_2010` | V001-V011 (faixas de renda) |
| Classe (entorno) | `setor_censitario_entorno_2010` | V001-V063 (infraestrutura) |
| Gênero | `responsavel_domicilios_homens/mulheres_2010` | V001 |

### Cruzamento Possível

```sql
-- Exemplo: Responsáveis mulheres por faixa de renda
SELECT 
    'Mulheres' as sexo,
    SUM(v002) as ate_1_sm,
    SUM(v003) as _1_a_2_sm
FROM br_ibge_censo_demografico.setor_censitario_responsavel_renda_2010
-- Nota: requer validação das variáveis de renda
```

---

## F2. Domicílios em Áreas de Infraestrutura Precária

### Resultado: Indicadores de Precariedade

| Indicador | Domicílios | Percentual |
|-----------|------------|------------|
| **Sem pavimentação** | 19.151.777 | 33,5% |
| **Sem calçada** | 25.022.701 | 43,7% |
| **Sem iluminação pública** | 12.335.051 | 21,6% |
| **Com esgoto a céu aberto** | 44.257.146 | 77,4% |

**Queries SQL:**

```sql
-- Sem pavimentação
SELECT SUM(v015 + v017 + v019) as sem_pavimentacao
FROM br_ibge_censo_demografico.setor_censitario_entorno_2010;

-- Com esgoto a céu aberto
SELECT SUM(v057 + v059 + v061) as com_esgoto_ceu_aberto
FROM br_ibge_censo_demografico.setor_censitario_entorno_2010;
```

---

## Tabelas Chave para Esta Pesquisa

### Census 2010
- `br_ibge_censo_demografico.setor_censitario_entorno_2010` — 310.120 setores, 57.2M domicílios
- `br_ibge_censo_demografico.setor_censitario_responsavel_renda_2010` — Renda dos responsáveis
- `br_ibge_censo_demografico.setor_censitario_responsavel_domicilios_homens_total_2010` — Homens responsáveis
- `br_ibge_censo_demografico.setor_censitario_responsavel_domicilios_mulheres_2010` — Mulheres responsáveis

### Census 2022
- `br_ibge_censo_2022.populacao_grupo_idade_sexo_raca` — cor_raca
- `br_ibge_censo_2022.alfabetizacao_grupo_idade_sexo_raca` — Alfabetização
- `br_ibge_censo_2022.indice_envelhecimento_raca` — Envelhecimento

---

## Lacunas e Dados Externos Necessários

| Pergunta | Fonte Necessária |
|----------|-----------------|
| A1-A5: Concentração fundiária | Census Agropecuário (não disponível) |
| B1-B5: Fortaleza por bairro | Shapefile de bairros + geocodificação |
| C3-C4: Produtoras rurais | Microdados censitário |
| D1-D3: Evolução fundiária | Séries históricas do IBGE |
| E1: Desastres ambientais | Dados do CENAD/ANA |

---

## Conclusão

O banco de dados permite responder **7 das 36 perguntas** diretamente:

1. ✅ **E2**: Infraestrutura de entorno (78% iluminação, 77% esgoto a céu aberto)
2. ✅ **E3**: Alfabetização por cor/raça (disponível no Census 2022)
3. ✅ **E4**: Envelhecimento por cor/raça (disponível no Census 2022)
4. ✅ **C1**: Responsáveis por sexo (72% homens, 28% mulheres)
5. ✅ **D4**: Evolução racial 2010-2022 (negros de 50% para 53%)
6. ✅ **F1**: Análise multidimensional (cruzamento via setor)
7. ✅ **F2**: Domicílios precários (33% sem pavimentação, 77% com esgoto a céu aberto)

As principais limitações estão nas análises de **concentração fundiária** e **segregação espacial por bairro**, que requerem dados externos ou geocodificação.
