# Água, Clima e Biodiversidade Ameaçada
```mermaid
erDiagram
    br_mma_extincao_fauna_ameacada {
        string especie_ou_subespecie
        string grupo
        string familia
        string ordem
        string categoria
    }
    br_mma_extincao_flora_ameacada { string especie_ou_subespecie string categoria }
    br_ana_reservatorios_sin { date data string id_reservatorio string nome_reservatorio double cota double afluencia double defluencia double proporcao_volume_util }
    br_inmet_bdmep_microdados { date data double temperatura double precipitacao }
    br_inpe_queimadas_focos { date data string bioma }
    br_mma_extincao_fauna_ameacada ||--o{ br_inpe_queimadas_focos : "bioma"
```

## Contexto e Sintese dos Dados

`br_mma_extincao` reune a lista oficial de especies ameacadas com `grupo`, `familia` e `categoria` de risco (VU, EN, CR, EX). Somado a `br_ana_reservatorios` e `br_ana_telemetria` (agua), `br_inmet_bdmep` (meteorologia), `br_inpe_queimadas` e `br_inpe_sisam` (fogo e qualidade do ar), `world_wwf_hydrosheds` (bacias) e `br_mapbiomas_estatisticas` (uso do solo).

## Revelacoes Importantes

### 1. Flora x fauna

| Reino | Especies | % |
|---|---|---|
| Flora | 6.418 | 83,6% |
| Fauna | 1.258 | 16,4% |

**Conclusao:** cinco plantas ameacadas para cada animal.

### 2. Fauna por grupo

| Grupo | Especies |
|---|---|
| Peixes | 388 |
| Invertebrados terrestres | 275 |
| Aves | 263 |
| Mamiferos | 103 |

**Conclusao:** peixes e invertebrados sao 60% da fauna ameacada.

### 3. Categoria de risco

| Categoria | Especies |
|---|---|
| Vulneravel | 465 |
| Em perigo | 425 |
| Em perigo critico | 322 |
| Extinta / possivelmente extinta | 46 |

**Conclusao:** 46 especies ja perdidas ou possivelmente perdidas.

### Reservatorios do SIN (ANA, 2000-2021)

Painel fixo de 37 reservatorios com >= 300 dias validos em todos os 22 anos; `proporcao_volume_util` filtrada em [-50, 105] (gotcha).

| Ano | Volume util medio | Abaixo de 10% em algum dia |
|---|---|---|
| 2000 | 49,6% | 11 |
| 2001 | 52,0% | 9 |
| 2011 | 77,3% | 0 |
| 2014 | 45,3% | 12 |
| 2015 | 47,1% | 12 |
| 2020 | 50,0% | 15 |
| 2021 | 43,8% | 8 |

**Conclusao:** 2021 tem a menor media da serie (pela mediana, 2014 e o pior: 40,3% contra 45,8%). Sem o painel fixo (44 a 71 reservatorios por ano) a ordem muda — 2020 aparece com 33 reservatorios abaixo de 10%. Tabela vai so ate 2022-01-12; a serie nao tem subsistema.

## Cruzamentos Poderosos

- **Flora x Fauna:** 84% das ameacadas sao plantas.
- **Peixe x Mamifero:** 388 contra 103 especies.
- **Visibilidade x Risco:** os grupos mais ameacados tem menor cobertura.
- **Critico x Extinto:** 322 em perigo critico, 46 perdidas.
- **Taxonomia x Subestimacao:** nao se declara ameacada a especie nao descrita.

## Hipoteses Explicativas

Plantas nao migram diante da supressao de habitat: qualquer conversao de area elimina populacoes inteiras. Peixes sofrem com barramento, assoreamento e poluicao de bacias.

## Implicacoes para Politicas Publicas

Priorizar areas por endemismo botanico protege melhor o grosso da biodiversidade em risco que unidades centradas em fauna carismatica.
