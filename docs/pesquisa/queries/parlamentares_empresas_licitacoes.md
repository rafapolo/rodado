# Parlamentares Eleitos com Empresas Vencedoras de Licitações Federais

Cruzamento entre:
- **TSE** (`br_tse_eleicoes.candidatos` + `resultados_candidato`) — parlamentares eleitos com CPF
- **CNPJ/ME** (`br_me_cnpj.socios`) — quadro societário das empresas vencedoras
- **CGU** (`br_cgu_licitacao_contrato.licitacao_item`) — itens de licitação > R$10k

**Join**: nome exato (case-insensitive) + 6 dígitos centrais do CPF mascarado (`***XXXXXX**`).  
**Filtro**: `valor_item` entre R$10.001 e R$500M; CNPJ vencedor válido (14 dígitos numéricos); empresas públicas federais conhecidas excluídas manualmente.

---

## Resultados (ordenados por valor total)

| Parlamentar | Cargo | Partido | UF | Último mandato | Empresa | CNPJ | Primeiro contrato | Último contrato | Itens | Valor Total (R$) |
|---|---|---|---|---|---|---|---|---|---|---|
| VITTORIO MEDIOLI | Dep. Federal / Prefeito | PSDB → PSD | MG | 2020 | DEVA VEICULOS LTDA | 23762552000302 | 2017 | 2023 | 270 | 1.872.266.982 |
| MANOEL SALVIANO SOBRINHO | Dep. Federal | PSDB | CE | 2010 | FARMACE – IND. QUIM.-FARM. CEARENSE LTDA | 06628333000146 | 2013 | 2023 | 8.283 | 1.108.154.974 |
| WALDOMIRO LUIZ SOSTER | Dep. Estadual | PSDB | AC | 1998 | M. S. M. INDUSTRIAL LTDA | 05394853000179 | 2015 | 2023 | 74 | 791.602.773 |
| STELLA ALVES BRANCO ROMANOS | Prefeita / Vice-prefeita | PDT / PHS | RJ | 2004 | INSTITUTO VITAL BRAZIL S/A¹ | 30064034000100 | 2014 | 2022 | 50 | 754.366.936 |
| CARLOS RONALDO VIEIRA FERNANDES | Vereador | PT | RS | 2000 | CEEE-D (COMPANHIA ESTADUAL DE DIST. ENERGIA)¹ | 08467115000100 | 2013 | 2023 | 451 | 753.170.033 |
| MARIA HELENA TEIXEIRA LIMA | Dep. Federal | MDB | RR | 2022 | VOARE TAXI AEREO LTDA | 00581615000159 | 2013 | 2023 | 57 | 301.817.731 |
| RUBEM MEDINA | Dep. Federal | PFL | RJ | 1998 | ARTPLAN COMUNICACAO S/A | 33673286000478 | 2013 | 2017 | 4 | 398.000.000² |
| REGINA VERA NOGUEIRA LEMOS | Vereadora | PTN | SP | 2004 | POWERTECH ENGENHARIA SERV. E LOCACOES | 12302292000104 | 2016 | 2017 | 4 | 278.077.027 |
| CARLOS AVALONE JUNIOR | Dep. Estadual | PSDB | MT | 2022 | FRATELLO ENGENHARIA LTDA | 22451088000109 | 2016 | 2019 | 13 | 240.612.157 |
| ANTONIO ELIAS DE OLIVEIRA | Prefeito | PMDB | PA | 2008 | CONSTRUTORA JUMBO LTDA | 07630228000104 | 2023 | 2023 | 4 | 196.475.734 |
| EDMILSON PEDRO PELIZARI | Prefeito / Vice-prefeito | PP | RS | 2016 | ASSOC RIOGR EMPR ASSIST TEC E EXT. RURAL | 89161475000173 | 2013 | 2018 | 192 | 185.532.591 |
| FRANCISCO BELLO GALINDO FILHO | Dep. Estadual | PTB | MT | 2006 | UNIDAS CONSTRUTORA LTDA | 01865426000170 | 2013 | 2018 | 11 | 170.824.189 |
| MARCOS LEITE FRANCO SOBRINHO | Dep. Estadual | PMDB | SE | 2002 | SERGIPE IND. TEXTIL LTDA (em rec. judicial) | 13006218000286 | 2013 | 2020 | 64 | 134.846.234 |
| TARCIZO MESSIAS DOS SANTOS | Prefeito | PSDB | PR | 2000 | FRANGOS PIONEIRO IND. ALIMENTOS LTDA | 00974731000642 | 2013 | 2023 | 102 | 113.637.682 |
| FRANCISCO LIMA LEITE | Vereador | PR | PE | 2012 | S N SINALIZADORA NACIONAL E SERVICOS LTDA | 08439201000100 | 2018 | 2022 | 19 | 103.573.686 |
| JOAQUIM FRANCISCO DE PAULA | Prefeito / Vereador | PSDC | SP | 2004 | HOSPIMETAL IND. METAL. EQUIP. HOSP. LTDA | 54178983000180 | 2013 | 2021 | 98 | 88.256.950 |
| MARCUS ANTONIO D ARRIGO | Vereador | PSDB | RS | 2004 | INTRAL SA IND. MATERIAIS ELETRICOS | 88611264000122 | 2014 | 2023 | 57 | 87.609.908 |
| ANSELMO GUEDES DE CASTILHO | Vereador | PT | PB | 2000 | FUNDACAO FUNETEC PB | 02168943000153 | 2013 | 2023 | 43 | 145.263.270 |
| MARCIO GAMBIN | Vereador | PT | RS | 2000 | LICITARE PRODUTOS, MAT. E SERVICOS LTDA | 18641075000117 | 2013 | 2023 | 2.812 | 111.541.070 |

> ¹ Possível falso positivo: empresa com controle público estadual (Vital Brazil = empresa pública do RJ; CEEE-D = empresa pública do RS).  
> ² Rubem Medina aparece com dois CNPJs da Artplan: R$298M (CNPJ ...000478) + R$100M (CNPJ ...000125) = R$398M total.

---

## Órgãos contratantes mais recorrentes

- **DNIT** — infraestrutura rodoviária (Waldomiro Soster/M.S.M., Carlos Avalone/Fratello, Francisco Bello/Unidas)
- **CODEVASF** — irrigação e desenvolvimento regional (Vittorio Medioli/Deva Veículos)
- **EBSERH** — hospitais universitários federais (Manoel Salviano/Farmace)
- **Ministério da Saúde** — compras de saúde (Maria Helena/Voare)
- **Presidência da República** — comunicação (Rubem Medina/Artplan)

---

## Metodologia e Limitações

- **Tabelas**: `br_tse_eleicoes.candidatos`, `br_tse_eleicoes.resultados_candidato`, `br_me_cnpj.socios`, `br_cgu_licitacao_contrato.licitacao_item`
- **Chave de join sócio→parlamentar**: `SUBSTR(cpf_mascarado, 4, 6) = SUBSTR(cpf_tse, 4, 6) AND UPPER(nome_socio) = UPPER(nome_candidato)`
- **Limitações**:
  1. CPF mascarado na Receita Federal — apenas 6 de 11 dígitos visíveis; o nome mitiga mas não elimina falsos positivos
  2. Quadro societário é histórico — o sócio pode ter entrado/saído antes ou depois dos contratos
  3. Não cruzamos data do mandato com data do contrato — alguns contratos podem ser posteriores ao último mandato listado
  4. Valor filtrado entre R$10.001 e R$500M por item (58 registros com valores > R$500M foram removidos por erro na fonte)
  5. Empresas públicas federais óbvias foram excluídas (SERPRO, Caixa, BNDES, Correios, Petrobras), mas algumas mistas podem permanecer
