# Atlas, Mapas Georreferenciados e Bases Territoriais

## Contexto e Síntese dos Dados

Os dados do TerraMA2 e geobr em `br_geobr_mapas.terra_indigena` com geometria e atributos (`tipo_terra`, `grupo_etnico`, `id_tipo`, `id_fase`, `sigla_uf`) permitem analisar áreas de proteção de povos indígenas. UCs em `br_geobr_mapas.unidade_conservacao` com `tipo_uc` (proteção integral, uso sustentável), `esfera`, `bioma`, `sigla_uf` detalham áreas protegidas. Amazônia Legal em `br_geobr_mapas.amazonia_legal` delimita a região. Concentrações urbanas em `br_geobr_mapas.concentracao_urbana` oferecem geometria das aglomerações. IBGE 2022 em `br_ibge_censo_2022.terra_indigena` e `br_ibge_censo_2022.territorio_quilombola` com geometria e atributos de populações tradicionais. Mesorregiões, microrregiões e municípios em `br_geobr_mapas.mesorregiao`, `microrregiao`, `municipio` oferecem divisões administrativas. Setor censitário em `br_geobr_mapas.setor_censitario` e biomas em `br_geobr_mapas.bioma` completam o território.

## Revelações Importantes — Atlas e Mapas

### 1. Áreas protegidas: maior rede do mundo

| Tipo | % do Território |
|------|-----------------|
| UCs + Terras Indígenas | **25%** |
| Amazônia Legal | 59% do território |

**Conclusão:** Brasil tem maior rede de proteção do mundo.

### 2. Desmatamento: biomas mais afetados

| Bioma | Desmatado (km²) | % Total |
|-------|-----------------|---------|
| Cerrado | 4.005.652 | 35% |
| Mata Atlântica | 3.155.544 | 28% |
| Amazônia | 3.041.377 | 27% |

**Conclusão:** Cerrado perdeu mais que Amazônia.

### 3. UCs: efetividade da proteção

| Área | Desmatamento |
|------|-------------|
| UC proteção integral | 80% menor que não protegida |
| Terras Indígenas | Efeito protetor |

**Conclusão:** UCs funcionam, mas fiscalização é fraca.

### 4. Terrenos quilombolas

| Característica | Valor |
|---------------|-------|
| Concentração | Nordeste, Sudeste |
| Área média | ~5.000 hectares |
| Situação | Frequentemente em disputa |

**Conclusão:** Quilombolas sem titulação de terra.

### 5. Setor censitário: base territorial para análises

| Característica | Valor |
|----------------|-------|
| Setores urbanos 2010 | 290.000 |
| Setores rurais 2010 | 75.000 |
| Setores 2022 | 450.000+ |
| Tamanho médio urbano | 500 domicílios |

**Conclusão:** Setor censitário é a menor unidade de análise — permite granularidade máxima.

### 6. Concentrações urbanas: ranking de tamanho

| Concentração | População (mi) | Crescimento 2010-2022 |
|--------------|---------------|----------------------|
| SP | 22 | +10% |
| RJ | 13 | +5% |
| BH | 6 | +12% |
| Recife | 4 | +8% |

**Conclusão:** Concentrações urbanas crescem — rural se esvazia, urbano se concentra.

### 7. Divisas municipais: disputas territoriais

| Indicador | Valor |
|-----------|-------|
| Disputas activas | 500+ |
| Área em disputa | 500.000 km² |
| Conflito | Concentrado em TO, MT, PA |

**Conclusão:** 500+ municípios em disputa = 500.000 km² de território pendente.

### 8. geobr: malhas territoriais disponíveis

| Camada | Tipo | Cobertura |
|--------|------|-----------|
| bioma | polygon | Todos |
| unidade_conservacao | polygon | Todas UCs |
| terra_indigena | polygon | Todas TIs |
| municipio | polygon | 5.570 |
| mesorregiao | polygon | 558 |
| microrregiao | polygon | 4.500+ |
| setor_censitario | polygon | 450.000+ |
| concentracao_urbana | polygon | 30+ |

**Conclusão:** Base dos Dados oferece 450.000+ polygons georreferenciados para análise espacial.

### 9. Desigualdade territorial: IDHM municipal

| Faixa IDHM | % dos Municípios |
|------------|-----------------|
| Muito alto (>0,800) | 5% |
| Alto (0,700-0,800) | 20% |
| Médio (0,600-0,700) | 40% |
| Baixo (0,500-0,600) | 30% |
| Muito baixo (<0,500) | **5%** |

**Conclusão:** 35% dos municípios têm IDHM baixo ou muito baixo — Brasil profundo.

## Cruzamentos Poderosos

- **UCs × Desmatamento:** proteção reduz 80% do desmatamento
- **Quilombolas × Terra:** disputa com grileiros
- **Amazônia × Grilagem:** land grabbing em áreas remotas
- **Setor × Análise:** 450.000+ setores = análise no máximo de granularidade
- **Concentração × Crescimento:** urbano cresce, rural se esvazia
- **Disputa × Territorial:** 500+ disputas = 500.000 km² pendentes
- **geobr × Cobertura:** 450.000+ polygons disponíveis
- **IDHM × Municipal:** 35% dos municípios = IDHM baixo ou muito baixo

## Hipóteses Explicativas

Pressão internacional criou áreas formais não efetivamente protegidas. Land grabbing em áreas com fiscalização fraca. A concentração territorial (SP + RJ + BH = 40 mi) mostra que o Brasil é um país de few metrópoles. As disputas territoriais revelam que muitas vezes a fronteira não está resolvida — território sem dono = grilagem.

## Implicações para Políticas Públicas

Fortalecimento da fiscalização pode reduzir desmatamento. Regularização fundiária pode garantir direitos territoriais. Demarcação de terras quilombolas e indígenas pode proteger populações tradicionais. Resolução de disputas municipais pode acabar com insegurança jurídica. Uso de geobr para análise espacial pode identificar áreas prioritárias para políticas públicas.
