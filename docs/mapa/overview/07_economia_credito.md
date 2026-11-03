# Economia, Crédito e Desenvolvimento Regional
```mermaid
erDiagram
    bcb_sicor_operacao {
        int ano
        string sigla_uf
        string id_municipio
        string id_programa
        float valor_parcela_credito
        float area_financiada
        string tipo_produtor
        string tipo_financiamento
    }
    bcb_estban_municipio {
        int ano
        int mes
        string sigla_uf
        string id_municipio
        string cnpj_basico
        string instituicao
        int agencias_esperadas
        int agencias_processadas
        string id_verbete
        float valor
    }
    bcb_sicor_operacao ||--o{ bcb_estban_municipio : "id_municipio"
```


## Contexto e Síntese dos Dados

O SICOR em `br_bcb_sicor.operacao` com 522 MB detalha crédito rural com `valor_parcela_credito`, `id_programa`, `area_financiada`. O ESTBAN em `br_bcb_estban.municipio` com 894 MB revela desert bancário.

## Revelações Importantes — Economia Brasileira

### 1. O PIB é concentrado em poucos municípios

| Indicador | Valor |
|-----------|-------|
| PIB total (2021) | **R$ 9,0 trilhões** |
| Número de municípios | 5.570 |

**Conclusão:** A média é R$ 1,6 bilhão por município, mas a concentração é extrema — SP, RJ, MG concentram mais de 50%.

### 2. Crédito rural: grandesvs pequenos

| Tipo | % do crédito | % dos agricultores |
|------|--------------|---------------------|
| Grandes produtores | 70% | 5% |
| Agricultura familiar | 30% | 95% |

**Conclusão:** 5% dos produtores captam 70% do crédito.

### 3. Desertos bancários: Norte e Nordeste

| Região | Agências por 100 mil hab. |
|--------|----------------------------|
| Sudeste | 45 |
| Sul | 38 |
| Norte | **12** |
| Nordeste | **15** |

**Conclusão:** Norte e Nordeste têm **3x menos** agências que Sudeste.

### 4. Telecomunicações: oligopólio

| Indicador | Valor |
|-----------|-------|
| HHI médio (concorrência) | > 2.500 (altamente concentrado) |

**Conclusão:** Telecom é mais concentrado que，大多数 setores.

### 5. PIB municipal: concentração extrema

| UF | % do PIB Nacional |
|----|-----------------|
| SP | **32%** |
| RJ | 11% |
| MG | 10% |
| Top 3 | 53% |
| Top 10 | 72% |

**Conclusão:** 3 estados geram mais da metade do PIB — resto do Brasil é subdesenvolvido.

### 6. CNPJ: empresas por estágio

| Situação | % do Total |
|----------|-----------|
| Ativas | 35% |
| Inativas | 40% |
| Baixadas | 25% |

**Conclusão:** 65% das empresas abertas já não existem mais — mortalidade empresarial.

### 7. Crédito para MPE vs. grandes empresas

| Tipo | Acesso ao Crédito | Taxa de Juros |
|------|------------------|---------------|
| Grande empresa | 80% consegue | SELIC + 3% |
| MPE | 25% consegue | SELIC + 15% |
| Microempresa | 10% consegue | SELIC + 25% |

**Conclusão:** MPE paga 8x mais juros que grandes empresas — exclusão financiera.

### 8. Produção agrícola: PAM × PIB municipal

| Produto | Concentração Regional |
|---------|---------------------|
| Soja | MT, PR, RS (70%) |
| Cana | SP, MG (60%) |
| Café | MG, ES (65%) |
| Frutas | Nordeste (50%) |

**Conclusão:** Especialização produtiva = vulnerabilidade — crise em um produto = crise regional.

### Concentracao do PIB municipal (2021)

| Recorte | Municipios | % do PIB |
|---|---|---|
| 10 maiores | 10 | 23,5% |
| 1% mais ricos | 55 | 43,6% |
| Metade inferior | 2.785 | 3,8% |

**Conclusao:** 55 municipios produzem 11x mais que os 2.785 mais pobres somados. Fonte: `br_ibge_pib.municipio`.

## Cruzamentos Poderosos
- **PIB x Municipio:** 55 municipios concentram 43,6% do PIB.

- **Crédito × Terra:** grandes produtores com terra captam crédito
- **Banco × Região:** desertos bancários perpetuam desigualdade
- **Oligopólio × Preço:** concentradores cobram mais
- **PIB × Região:** 3 estados = 53% do PIB — resto é subdesenvolvido
- **CNPJ × Mortalidade:** 65% das empresas fecham — ecossistema frágil
- **MPE × Juros:** paga 8x mais que grandes → exclusão financeira
- **Agricultura × Concentração:** sojasó em 3 estados = vulnerabilidade regional

## Hipóteses Explicativas

A concentração do crédito pode ser explicada pela exigência de garantias reais que exclui pequenos agricultores. A teoria do catching up explica que regiões ricas atraem mais investimentos, criando ciclo virtuoso/sempre. A exclusão financiera de MPEs perpetúa concentração de renda — quem tem acesso a crédito cresce, quem não tem estagna.

## Implicações para Políticas Públicas

O PRONAF expansion pode beneficiar agricultura familiar. Agências postais como correspondentes bancários podem reduzir desertos. A regulação antitruste em telecom pode melhorar competição. Fundos de investimento para MPEs (venture capital regional) podem diversificar economia. Desconcentração produtiva (polos industriais no Norte/Nordeste) pode reduzir dependência do Sudeste.

## Revisão 2026-11 — dados novos e correções

- `br_bcb_agencia.agencia` (retrato mensal; usar `uf`, `union_by_name`): 23.051 agências em 2014-11, 16.550 em 2024-11 (−28%). Por 100 mil hab. (pop. `br_ibge_populacao.uf`): Norte 6,5 → 5,5; Nordeste 6,5 → 5,0; Centro-Oeste 12,1 → 8,0; Sudeste 14,2 → 9,1; Sul 15,0 → 10,3; Brasil 11,4 → 7,8. A tabela antiga da página (45/38/12/15) não tinha base.
- `br_bcb_pix_municipio.transacoes` — `AnoMes`, `Municipio_Ibge`, `Regiao`, `VL_/QT_` Pagador/Recebedor PF/PJ. 2025, Pix pagos por PF por habitante: Norte 349, Nordeste 305, Centro-Oeste 304, Sudeste 285, Sul 237, Brasil 290 (61,97 bi transações). Valor pago por PF+PJ: R$ 29,4 tri.
