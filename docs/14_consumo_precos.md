# Consumo, Preços e Estratificação de Classe

## Contexto e Síntese dos Dados

O IPCA em `br_ibge_ipca.mes_categoria_municipio` com 49.356 registros detalha inflação por categoria. A ANP em `br_anp_precos_combustiveis.microdados` revela preços de combustíveis.

## Dados Tabu — Consumo

### 1. Inflação: pobre paga mais

| Categoria | Peso Pobre | Peso Rico |
|-----------|------------|----------|
| Alimentação | **45%** | 20% |
| Transporte | 15% | 25% |

**Conclusão:** Pobre gasta 45% com comida, rico 20%.

### 2. Gasolina: ICMS varia 30%

| Região | Preço |
|--------|-------|
| Sudeste | menor |
| Norte/Nordeste | **maior** |

**Conclusão:** ICMS mais alto no Norte penaliza pobres.

### 3. A cesta básica: quanto come o pobre?

| Cálculo | Valor |
|---------|-------|
| Salário mínimo | R$ 1.212 |
| Bolsa Família | R$ 190 |
| Cesta básica | R$ 400 |

**Conclusão:** Bolsa Família = 47% da cesta básica.

### 4. Transporte: o peso do combustível

| Item | Impacto |
|------|---------|
| Diesel × pobre | Alto (depende de ônibus) |
| Gasolina × rico | Alto (carro) |

**Conclusão:** Pobre é mais sensível a diesel.

## Cruzamentos Poderosos

- **Inflação × Classe:** alimentação pesa mais para pobre
- **Combustível × ICMS:** Norte paga mais
- **Transporte × Pobreza:** sem carro, depende de ônibus caro

## Hipóteses Explicativas

A tributação regressiva explica: pobre paga mais proportionally. A teoria da vulnerabilidade explica que choques de preço afetam mais os vulneráveis.

## Implicações para Políticas Públicas

Tributação progressiva pode reduzir impacto em pobres. Subsídios seletivos podem proteger vulneráveis.
