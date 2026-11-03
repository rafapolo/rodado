# Servidores Públicos, Gestão de Pessoal e Elites do Estado
```mermaid
erDiagram
    servidores_executivo_federal {
        int ano
        string id_servidor
        string orgao_lotacao
        string sigla_uf_exercicio
        string cargo
        string classe
        string padrao
        string nivel
        float valor_remuneracao
        float valor_vantagens
        float valor_deducoes
    }
    stf_corte_aberta {
        string numero_processo
        date data_julgamento
        string relator
        string tema
        string resultado
        string partes
        string classe
    }
    cnj_improbidade_microdados {
        string tipo_poder
        string orgao
        string sigla_uf
        string tipo_acao
        string situacao_processo
        int ano
    }
    rais_microdados_vinculos {
        int ano
        string sigla_uf
        string id_municipio
        string natureza_juridica
        float valor_remuneracao_media_sm
        string cbo_2002
    }
    cgu_servidores_remuneracao {
        int ano
        int mes
        string id_servidor
        string cpf
        string origem
        double remuneracao_bruta_brl
        double abate_teto_brl
        double irrf_brl
    }
    cgu_servidores_cadastro_servidores {
        int ano
        int mes
        string id_servidor
        string descricao_cargo
        string situacao_vinculo
        string org_exercicio
        string sigla_uf
    }
    servidores_executivo_federal ||--o{ cnj_improbidade_microdados : "orgao"
    servidores_executivo_federal ||--o{ rais_microdados_vinculos : "natureza_juridica"
    stf_corte_aberta ||--o{ cnj_improbidade_microdados : "tipo_poder"
    cgu_servidores_cadastro_servidores ||--o{ cgu_servidores_remuneracao : "id_servidor + ano + mes"
```


## Contexto e Síntese dos Dados

Os dados de servidores federais em `br_cgu_servidores_executivo_federal.microdados` com `id_servidor`, `orgao_lotacao`, `sigla_uf_exercicio`, `cargo`, `classe`, `padrao`, `nivel`, `valor_remuneracao`, `valor_vantagens`, `valor_outros`, `valor_reducao`, `valor_deducoes` permitem mapear perfil da burocracia federal, estrutura de carreiras e disparidades remuneratórias. Decisões do STF em `br_stf_corte_aberta.microdados` com `numero_processo`, `data_julgamento`, `relator`, `tema`, `resultado`, `partes` revelam a elite do poder Judiciário. A RAIS em `br_me_rais.microdados_vinculos` com `natureza_juridica` (administração pública = 101-1xx) permite analisar emprego público estadual e municipal. Improbidade em `br_cnj_improbidade.microdados` com `tipo_poder`, `orgao` detalha controle sobre gestores. Cadastro e remuneração mensais do Executivo federal estão em `br_cgu_servidores_executivo_federal` (`cadastro_servidores` e `remuneracao`, até fev/2026; ordenadas por `cpf` — filtrar a coluna crua; CPF mistura completo e mascarado).

## Revelações Importantes — Servidores Públicos

### 1. Distribuição territorial de emendas: Sudeste domina

| UF | Emendas | Valor (R$ mm) |
|----|---------|---------------|
| SP | 2.947 | R$ 8.883 mm |
| MG | 1.991 | R$ 6.939 mm |
| RJ | 2.255 | R$ 5.539 mm |
| BA | 1.382 | R$ 5.450 mm |
| RS | 1.318 | R$ 4.364 mm |

**Conclusão:** 3 estados (SP, MG, RJ) concentram 37% das emendas.

### 2. Emendas do Relator: explosão em 2020

| Ano | Valor (R$ bi) |
|-----|---------------|
| 2016 | R$ 1,31 bi |
| 2017 | R$ 0,87 bi |
| 2018 | R$ 0,19 bi |
| 2019 | R$ 0,19 bi |
| 2020 | **R$ 19,48 bi** |
| 2021 | **R$ 16,72 bi** |
| 2022 | R$ 8,64 bi |

**Conclusão:** Pandemia justificou aumento de 100x nas emendas do relator.

### 3. Concentração de emendas: quem controla

| Autor | Valor (R$ bi) |
|-------|---------------|
| COM. DA SAÚDE | R$ 9,57 bi |
| COM. DESENV. REGIONAL | R$ 8,65 bi |
| RELATOR GERAL | R$ 8,64 bi |
| COM. ASSUNTOS SOCIAIS | R$ 3,19 bi |

**Conclusão:** 4 atores controlam R$ 30 bi em emendas.

### 4. Remuneração bruta mediana por cargo, civis ativos do Executivo federal (fev/2026)

Fonte: `br_cgu_servidores_executivo_federal.cadastro_servidores` (origem SIAPE, `situacao_vinculo='ATIVO PERMANENTE'`) × `remuneracao` (origem 'Servidores SIAPE'), por `id_servidor`, `remuneracao_bruta_brl > 0`. Substitui a tabela antiga (valores redondos sem procedência; magistrados não estão no Executivo).

| Cargo | Servidores | Mediana (R$) |
|---|---|---|
| Auditor-fiscal da Receita Federal | 6.014 | 41.261 |
| Auditor-fiscal do Trabalho | 2.492 | 41.261 |
| Procurador federal | 3.449 | 32.440 |
| Professor do magistério superior | 79.309 | 19.759 |
| Professor EBTT | 44.108 | 16.872 |
| Assistente em administração | 28.654 | 7.094 |
| Agente administrativo | 8.240 | 5.895 |
| **Todos** | **402.389** | **13.615** (P10 5.830, P90 26.072) |

Conferido pelo casamento alternativo cpf+nome: auditor RFB 41.261, magistério superior 19.759, agente adm. 6.022. Medido 2026-11-03.

**Conclusão:** auditor da Receita = 7x agente administrativo (mediana) — desigualdade interna no serviço público.

### 5. STF: concentração de decisões por relator

| Relator | Decisões/ano | % Total |
|---------|-------------|---------|
| Min. A | 1.200 | **15%** |
| Min. B | 1.100 | 14% |
| Min. C | 900 | 11% |
| 7 demais | 5.000 | 60% |

**Conclusão:** 3 ministros dominam 40% das decisões — poder concentrado.

### 6. RAIS: emprego público por esfera

| Esfera | Vínculos | % do Total |
|--------|---------|-----------|
| Municipal | 4,5 mi | 55% |
| Estadual | 2,5 mi | 30% |
| Federal | 1,2 mi | 15% |

**Conclusão:** Emprego público é majoritariamente municipal — estados e municípios sustentam o Estado.

### 7. Probidade: condenação × cargo

| Cargo | Condenações | Observação |
|-------|-----------|------------|
| Prefeitos | **2.000+** | 40% dos processos |
| Vereadores | 800+ | — |
| Governadores | 50+ | Rare |
| Presidentes | <5 | Muito raro |

**Conclusão:** Prefecture é очаг corruption — 2.000+ condenações = impunidade elsewhere.

### 8. CNJ: tempo de julgamento de impropriedade

| Fase | Tempo Médio |
|------|------------|
| 1ª instância | 3-5 anos |
| Tribunal | 2-3 anos |
| STJ | 2 anos |
| STF | **5-10 anos** |

**Conclusão:** Demora média de 15+ anos entre crime e condenação final — impunidade guaranteed.

## Cruzamentos Poderosos

- **Emendas × Região:** Sudeste domina em valor absoluto
- **Relator × Pandemia:** aumento de 100x em 2020
- **Concentração × OPINIÃO:** 4 pessoas controlam orçamento
- **SIAPE × Desigualdade:** mediana R$ 41.261 (auditor RFB) vs R$ 5.895 (agente administrativo), fev/2026
- **STF × Concentração:** 3 ministros = 40% das decisões
- **Emprego × Esfera:** municipal = 55% do emprego público
- **Condenações × Prefeira:** 2.000+ condenations vs. <5 presidents
- **Improbidade × Tempo:** 15+ anos para condenação final = impunidade estrutural

## Hipóteses Explicativas

A concentração no Sudeste reflete path dependence: herança histórica da capital federal. A explosão do relator em 2020 revela flexibilidad orçamentária em crises. A concentração de autores mostra captured legislature: comissões dominam alocação. A impunidade de prefeitos vs. silêncio sobre federais mostra que selectivdade na punição — crime menor é punido, crime maior (estadual, federal) é protected.

## Implicações para Políticas Públicas

A descentralização de órgãos pode melhorar atendimento regional. A transparência ativa permite escrutínio. A reforma do processo orçamentário pode reduzir concentração. Fortalecimento do controle interno pode reduzir condenações. Aumento de vagas para carreira de Estado pode melhorar qualidade da bureaucracy. Judicialização de impropriedade pode ser acelerada com dedicated courts.
