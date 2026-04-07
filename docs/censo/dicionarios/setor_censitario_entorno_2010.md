# Dicionário: setor_censitario_entorno_2010

**Tabela**: `br_ibge_censo_demografico.setor_censitario_entorno_2010`  
**Fonte**: IBGE - Census Demográfico 2010 (Base de Informações por Setor Censitário - Universo)  
**Extração**: `/Volumes/EXTRA/bkps/Censos/Censo_Demografico_2010/Entorno_dos_Domicilios/csv/`

---

## Estrutura Geral

A tabela de entorno contém **1056 variáveis** organizadas em **5 arquivos de entorno** (Entorno 01 a 05), cada um correspondendo a um conjunto de características do entorno urbano.

### Arquivos de Origem

| Arquivo | Descrição |
|---------|-----------|
| Entorno 01 | Identificação do logradouro, Iluminação, Pavimentação, Calçada, Meio-fio |
| Entorno 02 | Bueiro, Rampa, Arborização, Esgoto a céu aberto, Lixo |
| Entorno 03 | Abastecimento de água |
| Entorno 04 | Esgotamento sanitário |
| Entorno 05 | Destino do lixo |

---

## Características do Entorno

Cada característica pode ter valores:
- **Existe** / **Não existe** / **Sem declaração**

### Lista Completa de Características

| Código | Característica | Descrição |
|--------|----------------|-----------|
| 1 | Identificação do logradouro | Presença de nome de rua |
| 2 | Iluminação pública | Existência de postes/lâmpadas |
| 3 | Pavimentação | Calçamento/asfalto na rua |
| 4 | Calçada | Passeio para pedestres |
| 5 | Meio-fio / guia | Divisão entre calçada e rua |
| 6 | Bueiro / boca de lobo | Drenagem pluvial |
| 7 | Rampa para cadeirante | Acessibilidade |
| 8 | Arborização | Árvores na rua |
| 9 | Esgoto a céu aberto | Vala/esgoto exposto |
| 10 | Lixo acumulado | Resíduos nos logradouros |

---

## Mapeamento de Variáveis

### Variáveis de Identificação

| Variável | Descrição |
|----------|-----------|
| `cod_setor` | Código do setor censitário |
| `situacao_setor` | 1=Área urbanizada, 2=Não urbanizada, 3=Urbana isolada, 4-8=Rural |

### Bloco 1: Identificação do Logradouro (V001-V027)

| Variável | Descrição |
|----------|-----------|
| V001 | Total de domicílios |
| V002 | Próprios - Existe identificação do logradouro |
| V003 | Próprios - Não existe identificação do logradouro |
| V004 | Alugados - Existe identificação do logradouro |
| V005 | Alugados - Não existe identificação do logradouro |
| V006 | Cedidos - Existe identificação do logradouro |
| V007 | Cedidos - Não existe identificação do logradouro |

### Bloco 2: Iluminação Pública (V008-V018)

| Variável | Descrição |
|----------|-----------|
| V008 | Próprios - Existe iluminação pública |
| V009 | Próprios - Não existe iluminação pública |
| V010 | Alugados - Existe iluminação pública |
| V011 | Alugados - Não existe iluminação pública |
| V012 | Cedidos - Existe iluminação pública |
| V013 | Cedidos - Não existe iluminação pública |

### Bloco 3: Pavimentação (V014-V026)

| Variável | Descrição |
|----------|-----------|
| V014 | Próprios - Existe pavimentação |
| V015 | Próprios - Não existe pavimentação |
| V016 | Alugados - Existe pavimentação |
| V017 | Alugados - Não existe pavimentação |
| V018 | Cedidos - Existe pavimentação |
| V019 | Cedidos - Não existe pavimentação |

### Bloco 4: Calçada (V020-V026)

| Variável | Descrição |
|----------|-----------|
| V020 | Próprios - Existe calçada |
| V021 | Próprios - Não existe calçada |
| V022 | Alugados - Existe calçada |
| V023 | Alugados - Não existe calçada |
| V024 | Cedidos - Existe calçada |
| V025 | Cedidos - Não existe calçada |

### Bloco 5: Meio-fio/Guia (V027-V033)

| Variável | Descrição |
|----------|-----------|
| V027 | Próprios - Existe meio-fio/guia |
| V028 | Próprios - Não existe meio-fio/guia |
| V029 | Alugados - Existe meio-fio/guia |
| V030 | Alugados - Não existe meio-fio/guia |
| V031 | Cedidos - Existe meio-fio/guia |
| V032 | Cedidos - Não existe meio-fio/guia |

### Bloco 6: Bueiro/Boca de Lobo (V033-V039)

| Variável | Descrição |
|----------|-----------|
| V033 | Próprios - Existe bueiro/boca de lobo |
| V034 | Próprios - Não existe bueiro/boca de lobo |
| V035 | Alugados - Existe bueiro/boca de lobo |
| V036 | Alugados - Não existe bueiro/boca de lobo |
| V037 | Cedidos - Existe bueiro/boca de lobo |
| V038 | Cedidos - Não existe bueiro/boca de lobo |

### Bloco 7: Rampa para Cadeirante (V039-V045)

| Variável | Descrição |
|----------|-----------|
| V039 | Próprios - Existe rampa para cadeirante |
| V040 | Próprios - Não existe rampa para cadeirante |
| V041 | Alugados - Existe rampa para cadeirante |
| V042 | Alugados - Não existe rampa para cadeirante |
| V043 | Cedidos - Existe rampa para cadeirante |
| V044 | Cedidos - Não existe rampa para cadeirante |

### Bloco 8: Arborização (V045-V051)

| Variável | Descrição |
|----------|-----------|
| V045 | Próprios - Existe arborização |
| V046 | Próprios - Não existe arborização |
| V047 | Alugados - Existe arborização |
| V048 | Alugados - Não existe arborização |
| V049 | Cedidos - Existe arborização |
| V050 | Cedidos - Não existe arborização |

### Bloco 9: Esgoto a Céu Aberto (V051-V057)

| Variável | Descrição |
|----------|-----------|
| V051 | Próprios - Existe esgoto a céu aberto |
| V052 | Próprios - Não existe esgoto a céu aberto |
| V053 | Alugados - Existe esgoto a céu aberto |
| V054 | Alugados - Não existe esgoto a céu aberto |
| V055 | Cedidos - Existe esgoto a céu aberto |
| V056 | Cedidos - Não existe esgoto a céu aberto |

### Bloco 10: Lixo Acumulado (V057-V063)

| Variável | Descrição |
|----------|-----------|
| V057 | Próprios - Existe lixo acumulado |
| V058 | Próprios - Não existe lixo acumulado |
| V059 | Alugados - Existe lixo acumulado |
| V060 | Alugados - Não existe lixo acumulado |
| V061 | Cedidos - Existe lixo acumulado |
| V062 | Cedidos - Não existe lixo acumulado |

---

## Padrão de Repetição

As variáveis seguem um **padrão de 9 vezes** (para cada característica do entorno), com 3 valores (próprio, alugado, cedido) × 2 situações (existe/não existe).

**Fórmula simplificada:**
```
V(n) = Característica × 9 + Condição de ocupação × 3 + Situação × 1 + offset
```

---

## Tabelas Temáticas (CSV do Volume)

| Tabela | Tema |
|--------|------|
| tab1_1 | Condição de ocupação do domicílio |
| tab1_2 | Abastecimento de água |
| tab1_3 | Esgotamento sanitário |
| tab1_4 | Destino do lixo |
| tab1_5 | Adequação da moradia |
| tab1_6 | Rendimento domiciliar |
| tab1_7 | Responsabilidade pelo domicílio |
| tab1_8 | Grupos de idade |
| tab1_9 | Cor ou raça |

---

## Como Usar

### Exemplo: Domicílios em áreas COM pavimentação

```sql
-- Selecionar domicílios próprios em ruas pavimentadas
SELECT 
    COUNT(*) as total_domicilios
FROM br_ibge_censo_demografico.setor_censitario_entorno_2010
WHERE situacao_setor IN (1, 2, 3)  -- Apenas urbanos
AND cod_setor IS NOT NULL;
```

### Cruzar com Dados de Domicílios

```sql
SELECT 
    e.cod_setor,
    e.V001 as total_entorno,
    d.V001 as total_domicilios
FROM br_ibge_censo_demografico.setor_censitario_entorno_2010 e
JOIN br_ibge_censo_demografico.setor_censitario_domicilio_caracteristicas_gerais_2010 d
    ON e.cod_setor = d.cod_setor;
```

---

## Notas

1. **Dados apenas urbanos**: Entorno coletado apenas para setores urbanos (situacao_setor 1, 2, 3)

2. **Setores sem coleta**: Alguns setores urbanos podem não ter informação de entorno

3. **Unidade**: Quadra/face do logradouro

4. **Dicionário completo**: Disponível em PDF no arquivo de documentação do IBGE

---

## Referências

- IBGE. Base de Informações do Censo Demográfico 2010 - Universo. Rio de Janeiro: IBGE, 2012.
- FTP: `https://ftp.ibge.gov.br/Censos/Censo_Demografico_2010/Resultados_do_Universo/Agregados_por_Setores_Censitarios/`
- Documentação: `Documentacao_Agregado_dos_Setores_2010_20231030.zip`
