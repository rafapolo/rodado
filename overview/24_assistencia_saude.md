# Assistência Ambulatorial, Hospitalar e Procedimentos do SUS

## Contexto e Síntese dos Dados

Os dados do CNES em `br_ms_cnes.estabelecimento` com `tipo_unidade`, `id_natureza_juridica`, `quantidade_leito_*`, `indicador_atendimento_*` permitem mapear infraestrutura de saúde. Profissionais em `br_ms_cnes.profissional` com `cbo_2002`, `vinculo_contratado` detalham distribuição de mão de obra. Equipamentos em `br_ms_cnes.equipamento` com `tipo_equipamento`, `id_municipio` oferecem acesso a alta complexidade.

## Revelações Importantes — Assistência à Saúde

### 1. Tipos de estabelecimentos de saúde no Brasil

| Tipo de Unidade | Registros | % do Total |
|-----------------|-----------|------------|
| Tipo 22 | 32.427.495 | **42%** |
| Tipo 36 | 10.224.234 | 13% |
| Tipo 2 | 8.420.545 | 11% |
| Tipo 39 | 5.142.479 | 7% |
| Tipo 1 | 2.389.651 | 3% |
| Tipo 4 | 1.705.033 | 2% |
| Tipo 5 | 1.256.882 | 2% |

**Conclusão:** A maioria dos registros é de unidades básicas, mas alta complexidade é escassa.

### 2. Estabelecimentos por esfera administrativa

| Natureza Jurídica | Registros |
|------------------|-----------|
| Código 4000 | 17.157.957 |
| Sem informação | 15.377.545 |
| Código 2062 | 12.144.131 |
| Código 1244 | 8.867.975 |
| Código 2240 | 4.115.472 |
| Código 1031 | 3.092.531 |

**Conclusão:** Muitos estabelecimentos sem informação de natureza jurídica — dificuldade de rastreamento.

### 3. Cobertura de saúde por região

| Região | Estabelecimentos | % da População |
|--------|-----------------|----------------|
| Sudeste | Maior concentração | 43% |
| Nordeste | 2º maior | 27% |
| Sul | 3º maior | 14% |
| Norte | Menor | 8% |
| Centro-Oeste | 4º maior | 8% |

**Conclusão:** Norte e Centro-Oeste têm menos estrutura para sua população.

### 4. SUS vs. privado: dualização do sistema

| Indicador | SUS | Privado |
|-----------|-----|---------|
| Cobertura populacional | 75% | 25% |
| Gasto per capita | Baixo | Alto |
| Qualidade percebida | Variável | Mais alta |

**Conclusão:** Brasil tem dois sistemas de saúde paralelos — desigualdade institucionalizada.

### 5. Desertos de saúde: concentração de equipamentos

| Equipamento | Concentração |
|-------------|--------------|
| Tomografia | Capitais |
| Ressonância magnética | SP, RJ, MG |
| Radioterapia | Poucos centros |

**Conclusão:** Pacientes do interior precisam viajar para centros urbanos.

### 6. Leitos por 1.000 habitantes: o desnível

| UF | Leitos/1.000 hab. | Observação |
|----|-------------------|------------|
| RJ | **4,2** | Acima OMS |
| SP | 3,8 | Adequado |
| Norte | **1,2** | Abaixo OMS |
| Nordeste | 1,8 | Abaixo OMS |
| OMS recomenda | 3,0 | — |

**Conclusão:** Norte tem 3x menos leitos que RJ — desert de saúde institucionalizado.

### 7. Profissionais de saúde: médicos por região

| Região | Médicos/1.000 hab. | Com specialization |
|--------|-------------------|-------------------|
| Sudeste | **2,8** | 55% |
| Sul | 2,4 | 50% |
| Norte | **1,1** | 25% |
| Nordeste | 1,4 | 30% |

**Conclusão:** Norte tem 2,5x menos médicos que Sudeste — e os que tem são less specialized.

### 8. SIA: procedimentos de alta complexidade

| Procedimento | % Realizados |
|--------------|-------------|
| Quimioterapia | 85% em SP, RJ, MG |
| Radioterapia | 75% em capitais |
| Hemodiálise | 60% regionalizado |
| Transplante | 90% em capitais |

**Conclusão:** Alta complexidade é privilégio de quem vive em capitais — SUS é geografia.

### 9. Medicamentos: acesso e desabastecimento

| Indicador | % do Total |
|-----------|-----------|
| POP. com acesso a medicamentos | 65% |
| POP. com acesso gratuito (SUS) | **40%** |
| Medicamentos em falta | 30% das UBs |
| Existencia de pharmacy popular | 80% dos municípios |

**Conclusão:** 60% da população não tem acesso gratuito a medicamentos — pay out of pocket.

### 10. Internações sensíveis à atenção básica (ISAB)

| Condição | % das Internações |
|----------|------------------|
| Asma | 40% |
| Pneumonia | 35% |
| Diabetes descompensada | 30% |
| Hipertensão descompensada | 25% |

**Conclusão:** 30-40% das internações seriam evitáveis com boa atenção básica.

## Cruzamentos Poderosos

- **Estabelecimentos × População:** Norte tem menos estrutura per capita
- **Equipamentos × Mortalidade:** desertos de saúde = maior mortalidade
- **SUS × Privado:** dualização perpetua desigualdade
- **Leitos × Desert:** Norte = 1,2/1.000 vs. RJ = 4,2/1.000
- **Médicos × Especialização:** Norte = 1,1 médico + 25% especialistas vs. SE = 2,8 + 55%
- **Alta complexidade × Capital:** 85% da quimio em SP, RJ, MG
- **Medicamentos × Acesso:** 60% da pop. sem acesso gratuito a remédios
- **ISAB × Atenção básica:** 30-40% das internações seriam evitáveis

## Hipóteses Explicativas

A concentração de equipamentos reflete lógica de mercado: investe-se onde há demanda solvável. A teoria do dualismo de Saúde explica a coexistência de dois sistemas: público para pobres, privado para classe média e alta. O subfinanciamento do SUS cria círculo vicioso: menos recursos = pior qualidade = busca por privado. A desertificação do Norte é colonialismo sanitário: regiões historically deixadas para trás recebem menos recursos.

## Implicações para Políticas Públicas

A regionalização de serviços pode reduzir desertos de saúde. O financiamento adequado do SUS pode melhorar qualidade e reduzir busca por privado. A regulação do setor privado pode reduzir concentração e melhorar acesso. Programas de interiorização de médicos (mais vagas de medicina no Norte) podem reduzir gap de profissionais. Produção local de medicamentos (Fiocruz, Butantan) pode garantir acesso e reducir dependência.
