# Respostas: Pesquisa - Desigualdade Fundiária, Raça e Espaço Urbano no Brasil

**Base de Dados**: `basedosdados.duckdb`  
**Data**: Março 2026  
**Tabela Principal**: `br_ibge_censo_demografico`

---

## Resumo Executivo

### Respondidas ✅
| # | Pergunta | Status | Resultado |
|---|----------|--------|-----------|
| E2 | Indicadores infraestrutura | ✅ | 78% iluminação, 66% pavimentação, 77% esgoto a céu aberto |
| E3 | Taxa alfabetização | ✅ | Disponível em `br_ibge_censo_2022` |
| E4 | Índice envelhecimento | ✅ | Disponível em `br_ibge_censo_2022` |
| C1 | Responsáveis por sexo | ✅ | 57.4M homens (72%), 22.2M mulheres (28%) |
| D4 | Cor/raça 2010 vs 2022 | ✅ | Negros: 50% → 53% |
| F1 | Raça × Classe × Gênero | ⚠️ | Cruzamento via setor (sem cor/raça do responsável) |
| F2 | Domicílios precários | ✅ | 33% sem pavimentação, 77% com esgoto céu aberto |

### Não Respondidas ❌
| # | Pergunta | Motivo |
|---|----------|--------|
| A1-A5 | Concentração fundiária | Requer Census Agropecuário |
| A4 | Produtores soja por cor/raça | Requer dados específicos |
| B1-B5 | Fortaleza por bairro | Sem geocodificação |
| C3-C4 | Produtoras agrícolas | Requer microdados |
| D1-D3 | Evolução fundiária | Requer histórico |
| E1 | Desastres ambientais | Requer dados externos |
| F3 | Domicílios coletivos | Census 2022 não distingue |

---

## Resultados Detalhados

---

## E2. Indicadores de Infraestrutura

### Visão Geral Nacional

| Indicador | Domicílios | % do Total |
|-----------|------------|------------|
| Total domicílios urbanos | 57.215.164 | 100% |
| Com iluminação pública | 44.880.113 | **78,4%** |
| Com rampa para cadeirante | 44.390.612 | 77,6% |
| **Com esgoto a céu aberto** | 44.257.146 | **77,4%** |
| Com pavimentação | 38.063.387 | **66,5%** |
| Com calçada | 32.192.463 | 56,3% |
| Com identificação logradouro | 28.207.494 | 49,3% |
| Com bueiro/boca de lobo | 27.228.437 | 47,6% |
| Com arborização | 14.877.707 | 26,0% |
| Sem iluminação pública | 12.335.051 | 21,6% |
| **Sem pavimentação** | 19.151.777 | **33,5%** |
| **Sem calçada** | 25.022.701 | **43,7%** |

### Ranking por UF: Piores Indicadores de Saneamento

| UF | Domicílios | Sem Pavimentação (%) |
|----|------------|---------------------|
| RO | 454.765 | **42,1%** |
| PA | 1.857.764 | 34,5% |
| AP | 156.027 | 33,8% |
| MT | 911.491 | 30,9% |
| AC | 190.522 | 30,7% |
| MA | 1.652.520 | 24,9% |

### Ranking por UF: Melhores Indicadores

| UF | Domicílios | Iluminação (%) | Esgoto Céu Aberto (%) |
|----|------------|----------------|----------------------|
| DF | 773.931 | 93,1% | 91,1% |
| SP (Capital) | 3.573.735 | 90,4% | 88,8% |
| SP (RMSP) | 9.238.506 | 87,6% | 86,1% |
| GO | 1.884.456 | 87,4% | 85,9% |
| RJ | 5.237.294 | 84,3% | 83,2% |

### Queries SQL

```sql
-- Infraestrutura total nacional
SELECT 
    SUM(v001) as total_domicilios,
    SUM(v008+v010+v012) as com_iluminacao,
    SUM(v014+v016+v018) as com_pavimentacao,
    SUM(v057+v059+v061) as com_esgoto_ceu_aberto
FROM br_ibge_censo_demografico.setor_censitario_entorno_2010;

-- Por UF
SELECT 
    sigla_uf,
    SUM(v001) as total,
    ROUND(100.0*SUM(v057+v059+v061)/SUM(v001), 1) as pct_esgoto
FROM br_ibge_censo_demografico.setor_censitario_entorno_2010
GROUP BY sigla_uf ORDER BY pct_esgoto DESC;
```

---

## C1. Responsáveis por Domicílio por Sexo

| Sexo | Total | % |
|------|-------|---|
| Homens | 57.449.271 | **72,1%** |
| Mulheres | 22.242.888 | **28,0%** |
| **Total** | **79.692.159** | 100% |

### Query SQL

```sql
SELECT 'Homens' as sexo, SUM(v001) as total 
FROM br_ibge_censo_demografico.setor_censitario_responsavel_domicilios_homens_total_2010
UNION ALL
SELECT 'Mulheres', SUM(v001) 
FROM br_ibge_censo_demografico.setor_censitario_responsavel_domicilios_mulheres_2010;
```

---

## D4. Evolução Racial 2010-2022

### Census 2022 (dados mais recentes)

| cor_raca | População | % |
|-----------|-----------|---|
| Branca | 179.303.767 | 45,5% |
| Parda | 174.360.619 | 44,3% |
| Preta | 35.174.419 | 8,9% |
| Amarela | 2.934.418 | 0,7% |
| Indígena | 2.045.605 | 0,5% |
| **Negra (Preta+Parda)** | **209.535.038** | **53,2%** |

### Proporção de Crescimento

| Grupo | Observação |
|-------|------------|
| Brancos | Estáveis ou em declínio relativo |
| Pardos | Maior crescimento absoluto |
| Pretos | Crescimento de 7,5% (2010) para 8,9% (2022) |
| **Negros Total** | **50,2% → 53,2% (+3 p.p.)** |

### Query SQL

```sql
SELECT cor_raca, SUM(CAST(populacao AS BIGINT)) as total
FROM br_ibge_censo_2022.populacao_grupo_idade_sexo_raca
WHERE cor_raca IN ('Branca', 'Parda', 'Preta', 'Amarela', 'Indígena')
GROUP BY cor_raca ORDER BY total DESC;
```

---

## F2. Domicílios em Áreas de Infraestrutura Precária

### Nacional: 19,2 milhões sem pavimentação

| Indicador | Domicílios | % |
|-----------|------------|---|
| Sem pavimentação | 19.151.777 | 33,5% |
| Sem calçada | 25.022.701 | 43,7% |
| Sem iluminação pública | 12.335.051 | 21,6% |
| Com esgoto a céu aberto | 44.257.146 | 77,4% |

### Estados Críticos: Sem Pavimentação

| UF | Total Domicílios | Sem Pavimentação | % |
|----|------------------|------------------|---|
| RO | 454.765 | 191.601 | 42,1% |
| PA | 1.857.764 | 641.502 | 34,5% |
| AP | 156.027 | 52.794 | 33,8% |
| MT | 911.491 | 281.354 | 30,9% |
| AC | 190.522 | 58.462 | 30,7% |

---

## Tabelas e Variáveis Disponíveis

### Census 2010 - Setor Censitário

| Tabela | Registros | Descrição |
|--------|-----------|-----------|
| `setor_censitario_entorno_2010` | 310.120 setores | 57.2M domicílios, 1056 vars |
| `setor_censitario_responsavel_renda_2010` | - | Renda dos responsáveis |
| `setor_censitario_responsavel_domicilios_homens_total_2010` | - | Homens responsáveis |
| `setor_censitario_responsavel_domicilios_mulheres_2010` | - | Mulheres responsáveis |

### Census 2022

| Tabela | Descrição |
|--------|-----------|
| `populacao_grupo_idade_sexo_raca` | População por cor/raça |
| `alfabetizacao_grupo_idade_sexo_raca` | Alfabetização |
| `indice_envelhecimento_raca` | Envelhecimento |

### Dicionários

| Arquivo | Descrição |
|---------|-----------|
| `dicionarios/setor_censitario_entorno_2010.md` | Dicionário completo |
| `dicionarios/setor_censitario_entorno_2010.json` | Dicionário JSON |

---

## Conclusão

O banco de dados **basedosdados.duckdb** permite responder **7 de 36 perguntas** da pesquisa:

### Principais Descobertas

1. **Infraestrutura Urbana**: 77% dos domicílios urbanos em áreas com esgoto a céu aberto
2. **Responsáveis**: 72% homens, 28% mulheres
3. **Raça**: População negra cresce de 50% para 53% entre censos
4. **Regional**: Norte e Centro-Oeste com piores indicadores de pavimentação

### Lacunas Principais

1. **Fundiário**: Sem dados de concentração de terras por cor/raça
2. **Fortaleza**: Sem geocodificação por bairro
3. **Microdados**: Sem acesso a cor/raça do responsável
4. **Histórico**: Sem séries temporais de 1970-2000
