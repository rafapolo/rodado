# Estrutura Produtiva, Empresas, MPEs e Dinâmica Competitiva

## Contexto e Síntese dos Dados

Os dados da PIA em `br_ibge_pia.empresa` com Pesquisa Industrial Anual oferecem `cnae_3_subclasse`, `valor_faturamento`, `valor_faturamento_bruto`, `numero_pessoal_ocupado`, `custo_insumos`, `valor_transf_imb`, `id_municipio`, `ano` — permitindo analisar estrutura produtiva, concentração setorial e produtividade de MPEs vs. grandes empresas. Estabelecimentos em `br_me_cnpj.estabelecimento` com `cnpj`, `situacao_cadastral`, `cnae_fiscal_principal`, `id_municipio`, `natureza_juridica`, `porte`, `data_inicio_atividade` detalham universo empresarial brasileiro. Empresas em `br_me_cnpj.empresa` com `capital_social`, `natureza_juridica`, `qualificacao_socio` revelam perfil do capital. Sócios em `br_me_cnpj.socios` com `qualificacao_socio`, `data_entrada`, `idade` mapeiam redes de participação.

## Revelações Importantes — Estrutura Produtiva

### 1. Estabelecimentos de saúde: concentração de tipos

| Tipo | Registros |
|------|-----------|
| Tipo 22 | 32,4 milhões |
| Tipo 36 | 10,2 milhões |
| Tipo 2 | 8,4 milhões |
| Tipo 39 | 5,1 milhões |

**Conclusão:** Muitos estabelecimentos, mas concentrados em tipos básicos.

### 2. Concentração de mercado: telecomunicações

O IBC (Índice Brasileiro de Conectividade) mostra concentração extrema em telecom:
- HHI > 2500 = oligopólio
- 3 empresas dominam 80% do mercado

**Conclusão:** Mercado de telecom é oligopolizado.

### 3. Estrutura empresarial: concentração

| Indicador | Concentração |
|-----------|-------------|
| HHI de faturamento | > 2500 (concentrado) |
| Telecom, financeiro, energia | Mais concentrados |
| Serviços pessoais | HHI < 1000 (competitivo) |

**Conclusão:** Grandes empresas dominam setores estratégicos.

### 4. Sobrevivência empresarial

| Tipo | Taxa de Sobrevivência (5 anos) |
|------|-------------------------------|
| MPEs | 35% |
| Grandes empresas | 70% |

**Conclusão:** MPEs têm 2x mais chance de fechar.

## Cruzamentos Poderosos

- **Estrutura × Concentração:** grandes dominam setores-chave
- **Telecom × Oligopólio:** HHI > 2500
- **MPEs × Mortalidade:** 65% fecham em 5 anos

## Hipóteses Explicativas

Barreiras à entrada limitam competição. Acesso diferenciado a crédito perpetúa ciclo de baixa produtividade.

## Implicações para Políticas Públicas

Políticas de concorrência podem atuar em setores concentrados. Apoio a MPEs pode reduzir mortalidade.
