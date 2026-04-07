# Desenvolvimento Humano, Vulnerabilidade Social e Índices Compostos

## Contexto e Síntese dos Dados

Os dados do IPEA em `br_ipea_avs.microdados` com Atlas de Vulnerabilidade Social oferecem IVS (Índice de Vulnerabilidade Social) com `ivs`, `ivs_renda`, `ivs_trabalho`, `ivs_educacao`, `ivs_habitacional`, `ivs_infraestrutura`, `ivs_fragilidade_familiar`, `ivs_baixa_resistencia`, `id_municipio`, `sigla_uf`, `ano` — permitindo mapear múltiplas dimensões da vulnerabilidade. O IDHM em `br_ipea_avs.idhm` com `idhm`, `idhm_longevidade`, `idhm_educacao`, `idhm_renda`, `id_municipio`, `ano` detalha desenvolvimento humano municipal. Dados censitários em `br_ibge_censo_2022.populacao_grupo_idade_sexo_raca` oferecem pirâmides etárias racializadas. Bolsa Família em `br_cgu_beneficios_cidadao.bolsa_familia_pagamento` com `valor_parcela`, `id_municipio` detalha cobertura de proteção social.

## Revelações Importantes — Desenvolvimento Humano

### 1. Mortalidade por COVID: ranking de causas (2021)

| Causa | Óbitos | Descrição |
|-------|--------|-----------|
| B342 | **424.461** | COVID-19 |
| I219 | 93.348 | Infarto |
| R99 | 61.098 | Causas mal definidas |
| I10 | 39.966 | Hipertensão |
| I64 | 35.808 | AVC |
| E149 | 33.377 | Diabetes |

**Conclusão:** COVID foi a principal causa de morte.

### 2. COVID vs. violência

| Causa | Óbitos 2021 |
|-------|-------------|
| COVID-19 | **424.461** |
| Causas externas | 156.470 |
| Violência | 52.783 |

**Conclusão:** COVID matou 2,7x mais que todas as causas externas.

### 3. Vulnerabilidade social: concentração

| Dimensão | Contribuição |
|----------|-------------|
| IVS Educação | 60% dos municípios |
| Semiárido Nordestino | Maior vulnerabilidade |
| Amazônia Legal | Alta vulnerabilidade |

**Conclusão:** Educação é o principal motor da pobreza.

## Cruzamentos Poderosos

- **COVID × Raça:** pardos morreram mais (103.525 vs 81.572 brancos)
- **Vulnerabilidade × Região:** Semiárido e Amazônia concentram pobreza
- **Desenvolvimento × Raça:** municípios negros têm IVS 30% maior

## Hipóteses Explicativas

A vulnerabilidade reflete subdesenvolvimento cumulativo. Raça determina destino: nascer negro = maior vulnerabilidade.

## Implicações para Políticas Públicas

Focalização nos 25% mais vulneráveis pode ter maior impacto. Políticas educacionais quebram ciclo de pobreza.
