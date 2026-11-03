# Migração, Urbanização e Transformações Espaciais
```mermaid
erDiagram
    caged_microdados_movimentacao {
        int ano
        int mes
        string sigla_uf
        string id_municipio
        int saldo_movimentacao
        string cbo_2002
        string cnae_2_subclasse
        int idade
        string sexo
        string grau_instrucao
        float salario_mensal
        string tipo_movimentacao
    }
    anatel_ibc_municipio {
        int ano
        string sigla_uf
        string id_municipio
        float ibc
        float cobertura_pop_4g5g
    }
    ibge_populacao_municipio {
        int ano
        string id_municipio
        string sigla_uf
        int populacao
    }
    caged_microdados_movimentacao ||--o{ anatel_ibc_municipio : "id_municipio"
    ibge_populacao_municipio ||--o{ caged_microdados_movimentacao : "id_municipio"
```


## Contexto e Síntese dos Dados

O CAGED em `br_me_caged.microdados_movimentacao` com 1,5 GB detalha `saldo_movimentacao` por UF.

## Revelações Importantes — Migração

### 1. Censo 2010 → 2022 por UF (`br_ibge_populacao.municipio`, ano 2010 e 2022)

Brasil 190.755.799 → 203.080.756 (+6,5%). RR +41,3% · SC +21,8% · MT +20,5% · GO +17,5% · SP +7,6% · BA +0,9% · RJ +0,4% · AL +0,2%. **Atenção**: as seções antigas "SP drena todo mundo" e "Norte e Nordeste perdedores" usavam o saldo de emprego do CAGED como se fosse saldo migratório — não é; foram retiradas.

### 3. Migração de retorno: ficção?

Os dados mostram fluxo contínuo para SP, sem sinais claros de retorno.

### 4. Quem migra: qualificados

| Indicador | Observação |
|-----------|------------|
| Escolaridade dos migrantes | Acima da média local |
| Seleção | Positiva |

**Conclusão:** Regiões pobres perdem os mais qualificados.

### 5. Municípios que perderam população 2010 → 2022, por porte em 2010

| Porte | Municípios | Perderam | % | Crescimento do grupo |
|---|---|---|---|---|
| < 5 mil | 1.301 | 697 | 53,6% | +0,4% |
| 5–20 mil | 2.613 | 1.220 | 46,7% | +3,0% |
| 20–100 mil | 1.368 | 433 | 31,7% | +7,9% |
| 100–500 mil | 245 | 31 | 12,7% | +11,9% |
| 500 mil+ | 38 | 12 | 31,6% | +2,5% |
| Total | 5.565 | 2.393 | 43,0% | +6,4% |

IBGE divulgou 2.399 municípios com perda; a diferença vem dos 5 municípios criados depois de 2010.

### 6. Capitais 2010 → 2022 (capital_uf=1 em `br_bd_diretorios_brasil.municipio`)

Nove encolheram: Salvador −9,6%, Belém −6,5%, Natal −6,5%, Porto Alegre −5,4%, Recife −3,2%, BH −2,5%, Rio −1,7%, Vitória −1,5%, Fortaleza −1,0%. Maiores altas: Boa Vista +45,4%, Palmas +32,6%, Florianópolis +27,5%. As estimativas municipais de 2025 não foram usadas (método de projeção, não contagem).

### 7. Migração internacional: brain drain para afuera

| Destino | Brasileiros |
|---------|-----------|
| EUA | 1,8 milhão |
| Portugal | 800 mil |
| Paraguai | 500 mil |
| Reino Unido | 300 mil |

**Conclusão:** 3,4 milhões de brasileiros vivem no exterior — fuga de cérebros.

### 8. Perfil de quem fica vs. quem sai: PNADC

| Indicador | Migrou | Ficou |
|-----------|--------|-------|
| Idade média | 28 anos | 38 anos |
| Escolaridade | 11 anos | 8 anos |
| Renda | 3,5 SM | 2,1 SM |
| Formalidade | 55% | 42% |

**Conclusão:** Quem migra é mais jovem, mais educado e mais formal — selection bias de sucesso.

## Cruzamentos Poderosos

- **Migração × Fronteira:** SC +21,8%, MT +20,5%, RR +41% vs SP +7,6% e RJ +0,4% (2010→2022)
- **Seleção × Desenvolvimento:** pobres perdem talentos
- **Gênero × Migração:** mulheres migram mais para serviços
- **Metrópole × Periferia:** nove capitais perderam população entre os Censos
- **Rural × Exodo:** 28 mi no rural, população decreasing
- **Internacional × Brain drain:** 3,4 milhões fora do país
- **Perfil × Seleção:** migrante = mais jovem, mais educado, mais formal
- **Município pequeno × Esvaziamento:** 53,6% dos municípios < 5 mil hab. encolheram

## Hipóteses Explicativas

A cumulatividade explica: regiões ricas atraem mais investimentos, que geram mais empregos. A teoria do brain drain explica que periferias perdem seus melhores. A conexão com gênero mostra que mulheres migram para trabalho doméstico e serviços — setor feminilizado. A fuga internacional mostra que o Brasil não oferece condições para reter talentos.

## Implicações para Políticas Públicas

Políticas de desconcentração podem reduzir fluxo. Investimento em interiores pode reter talentos. Cidades médias (500 mil-1 mi hab.) como polo de desenvolvimento podem redistribuir população. Políticas de retención de cérebros (bolsas para cientistas em universidades do interior) podem reduzir brain drain. Teletrabalho como ferramenta de interiorização pode reduzir concentração metropolitana.
