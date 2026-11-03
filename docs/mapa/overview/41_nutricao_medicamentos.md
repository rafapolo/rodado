# Nutrição, Preço de Medicamentos e Acesso à Saúde
```mermaid
erDiagram
    br_anvisa_cmed_precos {
        string substancia
        string laboratorio
        string produto
        string classe_terapeutica
        string tarja
        string pmc_0_pct
    }
    br_ms_sisvan_microdados { int ano string id_municipio double peso double altura }
    br_saude_farmaciapopular_estabelecimentos { bigint codigo_cnes string numero_cnpj bigint codigo_uf bigint codigo_municipio string codigo_motivo_desabilitacao_estabelecimento date data_atualizacao }
    br_ibge_pof_dieta { string id_domicilio string sigla_uf }
    br_saude_farmaciapopular_estabelecimentos }o--|| br_ibge_censo_2022_municipio : "codigo_municipio = left(id_municipio,6)"
```

## Contexto e Sintese dos Dados

`br_anvisa_cmed.precos` fixa o teto de preco de 51.140 apresentacoes com `tarja`, `substancia`, `classe_terapeutica` e preco maximo por faixa de ICMS. Somado a `br_ms_sisvan` (vigilancia nutricional), `br_saude_farmaciapopular`, `br_saude_bps` e `br_ibge_pof` (orcamento e dieta domiciliar).

## Revelacoes Importantes

### 1. Preco por tarja

| Tarja | Registros | Preco mediano |
|---|---|---|
| Sem tarja | 3.644 | R$ 36,35 |
| Tarja preta | 1.426 | R$ 81,88 |
| Tarja vermelha | 26.296 | R$ 103,76 |
| Vermelha sob restricao | 10.450 | R$ 143,24 |

**Conclusao:** exigir receita quase triplica o preco mediano.

### 2. Composicao do mercado

| Tarja | % do total |
|---|---|
| Tarja vermelha | 51,4% |
| Vermelha sob restricao | 20,4% |
| Sem tarja | 7,1% |

**Conclusao:** 71,8% das apresentacoes exigem prescricao.

### 3. Controle x preco

**Conclusao:** a tarja preta (controle maximo) custa menos que a vermelha comum — o preco segue a patente, nao o risco sanitario.

### 4. Farmacia Popular — rede credenciada (cadastro ate out/2026)

| Regiao | Farmacias ativas | Por 100 mil hab. | Municipios sem nenhuma |
|---|---|---|---|
| Sul | 8.513 | 28,4 | 27,4% |
| Centro-Oeste | 2.862 | 17,6 | 21,8% |
| Sudeste | 11.864 | 14,0 | 16,1% |
| Norte | 2.004 | 11,5 | 42,7% |
| Nordeste | 5.424 | 9,9 | 37,3% |
| Brasil | 30.667 | 15,1 | 28,0% (1.557) |

`br_saude_farmaciapopular.estabelecimentos` tem 32.592 linhas (uma por CNES, sem repeticao); 1.925 com `codigo_motivo_desabilitacao_estabelecimento` preenchido ficaram fora. `codigo_municipio` tem 6 digitos (sem o verificador). A tabela de medicamentos do programa nao existe no espelho (o diagrama antigo a citava). Populacao: censo 2022 por UF sem as faixas sobrepostas 15-17 e 18-19.

## Cruzamentos Poderosos

- **Receita x Preco:** prescricao quase triplica o preco mediano.
- **Restricao x Preco:** vermelha restrita custa 3,9x o de venda livre.
- **Tarja preta x Patente:** controle maximo mais barato que prescricao comum.
- **Mercado x Prescricao:** 71,8% exigem receita.
- **Acesso x Consulta:** a primeira barreira e a receita, nao o preco.

## Hipoteses Explicativas

O gradiente mede estrutura de concorrencia: venda livre compete em gondola com demanda elastica; prescricao compete pela caneta do medico, com demanda inelastica.

## Implicacoes para Politicas Publicas

Ampliar a lista de isentos de prescricao para moleculas antigas reduziria a barreira dupla de consulta mais preco.
