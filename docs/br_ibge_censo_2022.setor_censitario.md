# br_ibge_censo_2022.setor_censitario

## Overview

The `setor_censitario` table contains aggregated census data at the **census tract (setor censitário)** level from Brazil's 2022 Demographic Census (Censo Demográfico 2022), published by IBGE.

The table has **1,411 raw `v*` columns** (`v00001` through `v01411`) plus 7 named alias columns. None of the `v*` columns have descriptions in the `basedosdados-schema.json` context file.

## Named Columns (aliases for V0001–V0007)

These are human-readable aliases pointing to the basic dictionary:

| Schema Column | IBGE Code | Description |
|---|---|---|
| `pessoas` | V0001 | Total de pessoas |
| `domicilios` | V0002 | Total de Domicílios (DPPO + DPPV + DPPUO + DPIO + DCCM + DCSM) |
| `domicilios_particulares` | V0003 | Total de Domicílios Particulares (DPPO + DPPV + DPPUO + DPIO) |
| `domicilios_coletivos` | V0004 | Total de Domicílios Coletivos (DCCM + DCSM) |
| `media_moradores_domicilios` | V0005 | Média de moradores em Domicílios Particulares Ocupados |
| `porcentagem_domicilios_imputados` | V0006 | Percentual de Domicílios Particulares Ocupados Imputados |
| `domicilios_particulares_ocupados` | V0007 | Total de Domicílios Particulares Ocupados (DPPO + DPIO) |

DPPO = Domicílios Particulares Permanentes Ocupados  
DPPV = Domicílios Particulares Permanentes Vagos  
DPPUO = Domicílios Particulares de Uso Ocasional  
DPIO = Domicílios Particulares Improvisados Ocupados  
DCCM = Domicílios Coletivos com Morador  
DCSM = Domicílios Coletivos sem Morador

## Raw `v*` Columns (V00001–V01411)

These are the **1,411 detailed aggregated census variables**. They cover 8 major themes:

| Range | Theme | Count |
|---|---|---|
| V00001–V00089 | Características do Domicílio – Parte 1 | 89 |
| V00090–V00495 | Características do Domicílio – Parte 2 (crosstabs) | 406 |
| V00496–V00643 | Características do Domicílio – Parte 3 | 148 |
| V00644–V01005 | Alfabetização | 362 |
| V01006–V01041 | Demografia | 36 |
| V01042–V01223 | Parentesco | 182 |
| V01224–V01316 | Óbitos (2019-2022) | 93 |
| V01317–V01411 | Cor ou Raça | 95 |

### Theme Details

**V00001–V00089: Características do Domicílio – Parte 1**
Type of dwelling, number of residents, rooms, bathrooms, sanitation, water supply, electricity, waste collection, appliances, etc.

**V00090–V00495: Características do Domicílio – Parte 2**
Detailed dwelling characteristics cross-tabulated by type of dwelling and race/color of the responsible person.

**V00496–V00643: Características do Domicílio – Parte 3**
More detailed dwelling characteristics.

**V00644–V01005: Alfabetização**
Literacy rates by age group, sex, race/color, and other demographics.

**V01006–V01041: Demografia**
Population demographics (age, sex distribution).

**V01042–V01223: Parentesco**
Kinship/relationship structures within households.

**V01224–V01316: Óbitos**
Deaths in the household (reference period 2019-2022).

**V01317–V01411: Cor ou Raça**
Race/ethnicity breakdown of the population.

## Special Populations (Separate Variable Ranges)

In addition to the 1,411 base variables, IBGE publishes separate dictionaries for:

- **PCT – Indígenas** (V01500–V02xxx): 1,029 variables for Indigenous populations
- **PCT – Quilombolas** (V03000–V03xxx): 951 variables for Quilombola populations

These are stored in separate sheets in the IBGE dictionary file.

## Where to Find Full Variable Descriptions

### Official IBGE Dictionary

Download the official dictionary Excel file:

```
https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/dicionario_de_dados_agregados_por_setores_censitarios_20250417.xlsx
```

It contains 5 sheets:
- **Dicionario Basico** (V0001–V0007): Core counters — these map to the named schema columns
- **Siglas Basico**: Abbreviations for the basic variables
- **Dicionario nao PCT** (V00001–V01411): The main detailed variable dictionary
- **Dicionario PCT - Indigenas** (V01500–V02xxx): Indigenous population variables
- **Dicionario PCT - Quilombolas** (V03000–V03xxx): Quilombola population variables

### Other Sources

- **basedosdados website**: https://basedosdados.org/dataset/br-ibge-censo-2022
- **IBGE SIDRA**: https://sidra.ibge.gov.br (search "Agregados por Setores Censitários")
- **IBGE Census 2022 page**: https://www.ibge.gov.br/estatisticas/sociais/populacao/28740-censo-demografico-2022.html

## Notes

- The `basedosdados-schema.json` context file lists these columns as `{"name":"v00001","type":"INTEGER"}` with **no description field** — this is a known documentation gap.
- The `br_ibge_censo_2022.dicionario` table in the DuckDB only contains 30 entries for `cadastro_enderecos` — the 1,411 sector-level variable descriptions are **missing** from it.
- For the 2010 census (`br_ibge_censo_demografico`), descriptions **are** included in the schema for most tables.
