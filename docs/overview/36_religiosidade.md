# Religiosidade, Infraestrutura de Fé e Desigualdade de Renda
```mermaid
erDiagram
    br_ibge_censo_2022_cadastro_enderecos {
        string id_municipio
        double latitude
        double longitude
        string tipo_especie
        string descricao_estabelecimento
    }
    br_me_cnpj_estabelecimentos {
        string id_municipio
        string cep
        string cnae_fiscal_principal
        string situacao_cadastral
    }
    br_me_rais_microdados_vinculos {
        int ano
        string id_municipio
        double valor_remuneracao_media
        string vinculo_ativo_3112
    }
    br_ibge_censo2022_religiao_populacao_religiao {
        string nivel
        string id_localidade
        string localidade
        int ano
        string religiao
        string id_religiao_sidra
        int populacao_10_mais
    }
    br_ibge_censo2022_religiao_cor_raca {
        string id_municipio
        string municipio
        int ano
        string religiao
        string categoria_principal
        string dimensao_principal
        int valor
        string variavel
    }
    br_ibge_censo_2022_cadastro_enderecos ||--o{ br_me_cnpj_estabelecimentos : "id_municipio + cep"
    br_ibge_censo2022_religiao_populacao_religiao ||--o{ br_me_rais_microdados_vinculos : "id_localidade = id_municipio"
    br_ibge_censo2022_religiao_populacao_religiao ||--o{ br_ibge_censo2022_religiao_cor_raca : "id_municipio + religiao"
```

## Contexto e Síntese dos Dados

Duas famílias de fonte, cruzadas: **autodeclaração** (`br_ibge_censo2022_religiao.populacao_religiao`, religião declarada por localidade em `populacao_10_mais`, com `br_ibge_censo2022_religiao.cor_raca` cruzando religião × raça por município) e **presença física** (`br_ibge_censo_2022.cadastro_enderecos`, o CNEFE, com 765.591 templos geolocalizados a partir de `tipo_especie` e `descricao_estabelecimento`). A presença física é cruzada com `br_me_cnpj.estabelecimentos` (CNAE 9491-0/00, formalização jurídica) e com `br_me_rais.microdados_vinculos` (`valor_remuneracao_media`, salário formal médio por município). A série 2010 vem da tabela Sidra 137, coletada via API — o espelho parquet cobre 2022.

## Revelações Importantes

### 1. Transição religiosa 2010→2022

| Religião | 2010 | 2022 | Variação |
|---|---|---|---|
| Católica | 64,6% | 56,8% | -7,9 p.p. |
| Evangélica | 22,2% | 26,9% | +4,7 p.p. |
| Espírita | 2,0% | 1,8% | -0,2 p.p. |
| Umbanda/Candomblé | 0,3% | 1,1% | +0,7 p.p. |
| Sem religião | 8,0% | 9,3% | +1,2 p.p. |

**Conclusão:** municípios de maioria evangélica saltaram de 73 para 245 (3,4x) entre os dois Censos.

### 2. Infraestrutura física dos templos (CNEFE)

| Vertente | Templos | % |
|---|---|---|
| Evangélica de origem pentecostal | 245.669 | 32,1% |
| Não classificado | 282.505 | 36,9% |
| Católica Apostólica Romana | 99.680 | 13,0% |
| Evangélica de Missão | 60.405 | 7,9% |

**Conclusão:** 195.163 templos (25%) só entram na contagem por casamento de texto no nome anotado em campo — o Censo os classifica oficialmente como "outras finalidades".

### 3. Formalização jurídica (CNPJ)

| Situação | Templos | % |
|---|---|---|
| Com CNPJ ativo | 154.792 | 20,2% |
| Sem CNPJ confirmado | 610.799 | 79,8% |

**Conclusão:** informalidade jurídica é o padrão, não a exceção, na infraestrutura religiosa brasileira.

### 4. Religião × salário formal (RAIS)

| Religião | Quartil menor % | Quartil maior % |
|---|---|---|
| Católica | R$ 4.043 | R$ 2.556 |
| Espírita | R$ 2.559 | R$ 4.091 |
| Evangélica | R$ 3.000 | R$ 3.355 |

**Conclusão:** o gradiente espírita (+60%) é o cruzamento de renda mais forte do tema.

### 5. Religião afro-brasileira × raça (por UF)

| UF | % Umbanda/Candomblé | % População negra |
|---|---|---|
| RS | 3,19% | 21,2% |
| RJ | 2,58% | 57,7% |
| BA | 1,00% | 79,7% |

**Conclusão:** geografia de sincretismo regional pesa mais que composição racial isolada.

## Cruzamentos Poderosos

- **Religião × Renda:** municípios menos católicos pagam 58% mais em salário formal.
- **Espiritismo × Renda:** gradiente mais forte do tema — 60% entre extremos.
- **Umbanda × Raça:** RS tem 3x mais umbanda que BA com 1/3 da população negra.
- **Evangélico × Região:** PI e AC têm composição racial quase idêntica e proporções evangélicas opostas (15,6% vs. 44,4%).
- **Templo × CNPJ:** 80% dos templos operam sem registro empresarial formal.
- **Templo × Censo:** 1 em 4 templos só é identificado pelo nome, não pelo campo oficial.

## Hipóteses Explicativas

O gradiente de renda por composição religiosa reflete sobretudo urbanização e secularização andando juntas, não um efeito causal direto da fé sobre a renda — municípios grandes e ricos tendem a ter menor proporção católica e maior presença espírita, historicamente associada a público urbano escolarizado desde a chegada do kardecismo ao Brasil no século XIX. O crescimento evangélico segue lógica territorial (fronteira de colonização recente no Norte/Centro-Oeste, menor presença histórica católica), não lógica racial. A baixa formalização jurídica dos templos reflete um padrão associativo brasileiro mais amplo, não uma peculiaridade religiosa.

## Implicações para Políticas Públicas

Políticas de assistência ou parceria pública que exigem CNPJ como porta de entrada excluem 80% da infraestrutura religiosa real do país. A concentração territorial de vertentes específicas exige desenho regionalizado de políticas de liberdade religiosa e combate à intolerância. O forte gradiente de renda por composição religiosa é um lembrete de que a distribuição religiosa carrega sinal socioeconômico substancial — não é uma variável neutra em pesquisas sobre desigualdade.
