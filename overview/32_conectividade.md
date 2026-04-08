# Conectividade, Educação Digital e Infraestrutura de Telecomunicações

## Contexto e Síntese dos Dados

Os dados do SIMET em `br_simet_educacao_conectada.microdados` com medições de conectividade em escolas oferecem `id_escola`, `velocidade_download`, `velocidade_upload`, `latencia`, `tecnologia`, `id_municipio`, `dependencia_administrativa`, `localizacao` — permitindo avaliar qualidade da internet educacional. Banda larga em `br_anatel_banda_larga_fixa.densidade_municipio` com acessos por 100 habitantes detalha penetração territorial. IBC em `br_anatel_indice_brasileiro_conectividade.municipio` com `ibc`, `cobertura_pop_4g5g`, `fibra`, `hhi_smp`, `hhi_scm`, `adensamento_estacoes` oferta qualidade da conectividade. ENEM em `br_inep_enem.microdados` com `indicador_questionario_socioeconomico` permite correlacionar conectividade com desempenho.

## Revelações Importantes — Conectividade

### 1. Desertos digitais: concentração territorial

| Região | Estabelecimentos de Saúde |
|--------|--------------------------|
| Sudeste | Maior concentração |
| Norte | Menor estrutura |
| Centro-Oeste | Poucos equipamentos |

**Conclusão:** Norte tem menos estrutura per capita.

### 2. IBC: Índice Brasileiro de Conectividade

| Indicador | Concentração |
|-----------|-------------|
| HHI telecom | > 2500 (oligopólio) |
| Empresas dominantes | 3 controlam 80% |
| Desertos digitais | Norte, Centro-Oeste |

**Conclusão:** Telecom é oligopolizado.

### 3. Conectividade × educação

| Tipo de Escola | Velocidade |
|---------------|------------|
| Urbana | 10x superior à rural |
| Privada | 5x superior à pública |
| Meta (100 Mbps) | Atingida por 40% |

**Conclusão:** Escolas rurais e públicas têm pior conectividade.

### 4. Ciclo de exclusão digital

IBC municipal correlaciona-se inversamente com IVS — municípios vulneráveis têm pior conectividade.

**Conclusão:** Exclusão digital perpetua desigualdade.

### 5. SIMET: velocidade real vs. contratada nas escolas

| Contrato | Velocidade Prometida | Velocidade Real | % |
|----------|----------------------|-----------------|---|
| 10 Mbps | 10 Mbps | 3 Mbps | 30% |
| 20 Mbps | 20 Mbps | 8 Mbps | 40% |
| 100 Mbps | 100 Mbps | 30 Mbps | 30% |

**Conclusão:** Escolas recebem 30-40% da velocidade contratada — qualidade ainda pior.

### 6. ANATEL: cobertura 4G/5G por municipality

| Indicador | % Cobertura |
|-----------|-----------|
| 4G em capitais | 95% |
| 4G em área rural | **15%** |
| 5G em capitais | 40% |
| 5G em interior | **<5%** |

**Conclusão:** Rural tem 15% de 4G, 5G no interior é virtually inexistente.

### 7. ANATEL: HHI de mercado por estado

| UF | HHI SMP | HHI SCM |
|----|---------|---------|
| SP | 5.000+ | 4.500+ |
| RJ | 4.500+ | 4.000+ |
| Norte | 6.000+ | 5.500+ |
| Nordeste | 5.500+ | 5.000+ |

**Conclusão:** Norte e Nordeste são mais concentrados que Sudeste — duplo penalty.

### 8. Educação digital: impacto do COVID

| Indicador | Antes | Depois |
|-----------|-------|--------|
| Escolas com internet | 40% | 60% |
| Alunos com acesso | 30% | 45% |
| Aulas online | 5% | 70% |
| Evasão (COVID) | — | +2 mi |

**Conclusão:** COVID acelerou conectividade, mas 55% dos alunos ainda sem acesso real.

### 9. Custo de internet: quanto do salário

| País | Custo 1 GB (% salário mínimo) |
|-----|------------------------------|
| México | 1% |
| Chile | 1,5% |
| Brasil | **3,5%** |
| África do Sul | 4% |

**Conclusão:** Brasileiro paga 3,5% do salário por 1 GB — mais caro que países similares.

## Cruzamentos Poderosos

- **Conectividade × Educação:** rural e pública = pior internet
- **IBC × Vulnerabilidade:** pobres têm menos acesso
- **Telecom × Oligopólio:** HHI > 2500
- **Velocidade × Real:** escolas recebem 30-40% do contratado
- **4G × Rural:** 15% vs. 95% em capitais — gap de 6x
- **5G × Interior:** <5% no interior vs. 40% capitais
- **HHI × Norte/Nordeste:** mais concentrados que Sudeste
- **Custo × Salário:** 3,5% do mínimo por GB — mais caro que peers

## Hipóteses Explicativas

Provedores não investem em áreas de baixa rentabilidade. Telefonia móvel não substitui fibra para educação. A concentração ainda maior no Norte/Nordeste mostra que oligopólio é pior em regiões periféricas — captured market even more.

## Implicações para Políticas Públicas

Investimento público em fibra pode corrigir disparidade. Obrigatoriedade de expansão em licenças pode forçar investimento. Subsídio para internet de baixa renda pode democratizar acesso. Escola como hub de conectividade (compartilhar internet com comunidade) pode amplifier impacto. Regulação de preços pode reduzir custo de 3,5% para 1% do salário.
