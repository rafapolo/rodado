# br_ibge_pnadc.microdados

**Fonte**: `rodado-schema.json` + [dicionário oficial do IBGE](https://ftp.ibge.gov.br/Trabalho_e_Rendimento/Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Trimestral/Microdados/Documentacao/Dicionario_e_input_20221031.zip) (`dicionario_PNADC_microdados_trimestral.xls`, versão de 2022-10-31). Os códigos de categoria de cada coluna estão em `br_ibge_pnadc.dicionario`.

PNAD Contínua trimestral, de 2012-T1 a 2025-T3: uma linha por pessoa entrevistada, 28,4 milhões de linhas e 424 colunas, das quais 200 são réplicas do peso. A amostra é desenhada para representar Brasil, região, UF, capital e região metropolitana. **Não há `id_municipio`**: a geografia mais fina é `id_uf` com `capital` e `rm_ride`.

Cada pessoa responde a quatro partes do questionário:

| Parte | O que se registra | Colunas |
|---|---|---|
| Identificação e amostra | ano, trimestre, UF, capital/RM, domicílio, painel e visita, urbano/rural, peso | 22 + 200 réplicas |
| Moradores | sexo, data de nascimento, idade, cor ou raça, posição no domicílio, nº de moradores | 9 |
| Educação (5 anos ou mais) | alfabetização, escola atual (rede, curso, série), escolaridade anterior e conclusão | 22 |
| Trabalho (14 anos ou mais) | se trabalhou, afastamento, nº de trabalhos, ocupação (COD) e atividade (CNAE domiciliar), posição (empregado, conta própria, empregador…), carteira, servidor, CNPJ do negócio, tamanho da empresa, local de trabalho, previdência, rendimento habitual e efetivo, horas, subocupação, procura de trabalho, tempo de procura, motivo de não procurar | 135 |
| Derivadas do IBGE (`VD*`) | condição na força de trabalho, ocupação/desocupação, desalento, posição e categoria, grupamentos de atividade e ocupação, rendimentos, horas, nível de instrução e anos de estudo | 35 |

As derivadas `VD*` já aplicam a definição oficial do IBGE: para taxa de desocupação, informalidade e rendimento, use-as, não as perguntas `V4*` de origem. As armadilhas medidas estão em [`gotchas/br_ibge_pnadc.yml`](../gotchas/br_ibge_pnadc.yml).

## Números conferidos contra o IBGE (medidos 2026-10-19)

Todos com `sum(V1028)`:

| Medida | Valor no espelho | Divulgado |
|---|---|---|
| Taxa de desocupação 2021-T1 = `VD4002='2'` ÷ `VD4001='1'` | 14,9% | 14,9% |
| Taxa de desocupação 2025-T2 / 2025-T3 | 5,8% / 5,6% | 5,8% / 5,6% |
| Ocupados 2025-T3 (`VD4002='1'`) | 102,4 mi | 102,4 mi |
| Rendimento médio habitual de todos os trabalhos 2025-T3 (`VD4019`, ocupados) | R$ 3.507 | R$ 3.507 |

No mesmo 2025-T3, o rendimento habitual médio foi de R$ 3.844 para homens e R$ 3.061 para mulheres (79,6%), e de R$ 4.522 para brancos contra cerca de R$ 2.690 para pretos e pardos somados (59%).

## Colunas

Descrições copiadas do dicionário do IBGE; as colunas sem período são acréscimos da Base dos Dados. As variáveis com período encerrado (ex.: `1º tri/2012 - 3º tri/2015`) foram substituídas pela versão com sufixo `A` e vêm NULL fora do período.

### Identificação, amostra e peso (22)

| Coluna | Tipo | Descrição (dicionário do IBGE) | Período |
|---|---|---|---|
| `ano` | INTEGER | Ano de referência | 1º tri/2012 - atual |
| `trimestre` | INTEGER | Trimestre de referência | 1º tri/2012 - atual |
| `id_uf` | STRING | Código da UF (2 dígitos) |  |
| `sigla_uf` | STRING | Sigla da UF |  |
| `capital` | STRING | Município da Capital | 1º tri/2012 - atual |
| `rm_ride` | STRING | Região Metropolitana e Região Administrativa Integrada de Desenvolvimento | 1º tri/2012 - atual |
| `id_upa` | STRING | Unidade primária de amostragem (UPA) |  |
| `id_estrato` | STRING | Estrato da amostra |  |
| `id_domicilio` | STRING | Identificador do domicílio (acrescentado pela Base dos Dados) |  |
| `id_pessoa` | STRING | Identificador da pessoa (acrescentado pela Base dos Dados) |  |
| `V1008` | STRING | Número de seleção do domicílio | 1º tri/2012 - atual |
| `V1014` | STRING | Painel | 1º tri/2012 - atual |
| `V1016` | INTEGER | Número da entrevista no domicílio | 1º tri/2012 - atual |
| `V1022` | STRING | Situação do domicílio | 1º tri/2012 - atual |
| `V1023` | STRING | Tipo de área | 1º tri/2012 - atual |
| `V1027` | FLOAT | Peso do domicílio e das pessoas, **sem** calibração pela projeção de população — não usar para estimar | 1º tri/2012 - atual |
| `V1028` | FLOAT | Peso do domicílio e das pessoas, **com** calibração — o peso a usar: `sum(V1028)` estima a população | 1º tri/2012 - atual |
| `V1028001`…`V1028200` | FLOAT | 200 réplicas do peso V1028 (bootstrap), para estimar variância e intervalo de confiança | 1º tri/2012 - atual |
| `V1029` | INTEGER | Projeção da população por níveis geográficos | 1º tri/2012 - atual |
| `V1033` | INTEGER | Projeção da população por sexo e idade | 1º tri/2012 - atual |
| `posest` | STRING | Domínios de projeção geográficos | 1º tri/2012 - atual |
| `posest_sxi` | STRING | Domínios de projeção por sexo e idade | 1º tri/2012 - atual |

### Características gerais dos moradores (9)

| Coluna | Tipo | Descrição (dicionário do IBGE) | Período |
|---|---|---|---|
| `V2001` | INTEGER | Número de pessoas no domicílio | 1º tri/2012 - atual |
| `V2003` | INTEGER | Número de ordem | 1º tri/2012 - atual |
| `V2005` | STRING | Condição no domicílio | 1º tri/2012 - atual |
| `V2007` | STRING | Sexo | 1º tri/2012 - atual |
| `V2008` | INTEGER | Dia de nascimento | 1º tri/2012 - atual |
| `V20081` | INTEGER | Mês de nascimento | 1º tri/2012 - atual |
| `V20082` | INTEGER | Ano de nascimento | 1º tri/2012 - atual |
| `V2009` | INTEGER | Idade do morador na data de referência | 1º tri/2012 - atual |
| `V2010` | STRING | Cor ou raça | 1º tri/2012 - atual |

### Educação (5 anos ou mais) (22)

| Coluna | Tipo | Descrição (dicionário do IBGE) | Período |
|---|---|---|---|
| `V3001` | STRING | ... sabe ler e escrever? | 1º tri/2012 - atual |
| `V3002` | STRING | ... frequenta escola? | 1º tri/2012 - atual |
| `V3002A` | STRING | A escola que ... frequenta é de | 4º tri/2015 - atual |
| `V3003` | STRING | Qual é o curso que ... frequenta? | 1º tri/2012 - 3º tri/2015 |
| `V3003A` | STRING | Qual é o curso que ... frequenta? | 4º tri/2015 - atual |
| `V3004` | STRING | A duração deste curso que ... frequenta é de: | 1º tri/2012 - 4º tri/2017 |
| `V3005` | STRING | Este curso que ... frequenta é seriado? | 1º tri/2012 - 3º tri/2015 |
| `V3005A` | STRING | Esse curso que .... frequenta é organizado em: | 4º tri/2015 - atual |
| `V3006` | STRING | Qual é o ano/série/semestre que ... frequenta? | 1º tri/2012 - atual |
| `V3006A` | STRING | Qual é a etapa do ensino fundamental que ... frequenta? | 1º tri/2018 - atual |
| `V3007` | STRING | ... já concluiu algum outro curso de graduação? | 1º tri/2012 - atual |
| `V3008` | STRING | Anteriormente ... frequentou escola? | 1º tri/2012 - atual |
| `V3009` | STRING | Qual foi o curso mais elevado que ... frequentou anteriormente? | 1º tri/2012 - 3º tri/2015 |
| `V3009A` | STRING | Qual foi o curso mais elevado que ... frequentou anteriormente? | 4º tri/2015 - atual |
| `V3010` | STRING | A duração deste curso que ... frequentou anteriormente era de: | 1º tri/2012 - atual |
| `V3011` | STRING | Este curso que ... frequentou anteriormente era seriado? | 1º tri/2012 - 3º tri/2015 |
| `V3011A` | STRING | Esse curso que .... frequentou era organizado em: | 4º tri/2015 - atual |
| `V3012` | STRING | ... concluiu com aprovação, pelo menos a primeira série deste curso que frequentou anteriormente? | 1º tri/2012 - atual |
| `V3013` | STRING | Qual foi o último ano/série/semestre que ... concluiu com aprovação, neste curso que frequentou anteriormente | 1º tri/2012 - atual |
| `V3013A` | STRING | Qual foi a etapa de ensino fundamental que ... frequentou? | 1º tri/2018 - atual |
| `V3013B` | STRING | ... Concluiu os anos iniciais deste curso que frequentou anteriormente? | 1º tri/2018 - atual |
| `V3014` | STRING | ... concluiu este curso que frequentou anteriormente | 1º tri/2012 - atual |

### Trabalho (14 anos ou mais) (135)

| Coluna | Tipo | Descrição (dicionário do IBGE) | Período |
|---|---|---|---|
| `V4001` | STRING | Na semana de ... a ... (semana de referência), ... trabalhou ou estagiou, durante pelo menos 1 hora, em alguma atividade remunerada em dinheiro? | 1º tri/2012 - atual |
| `V4002` | STRING | Na semana de ... a ... (semana de referência), ... trabalhou ou estagiou, durante pelo menos 1 hora, em alguma atividade remunerada em produtos, mercadorias, moradia, alimentação, etc.? | 1º tri/2012 - atual |
| `V4003` | STRING | Na semana de ... a ... (semana de referência), ... fez algum bico ou trabalhou em alguma atividade ocasional remunerada durante pelo menos 1 hora? | 1º tri/2012 - atual |
| `V4004` | STRING | Na semana de ... a ... (semana de referência), ... ajudou durante pelo menos 1 hora, sem receber pagamento, no trabalho remunerado de algum morador do domicílio ou de parente? | 1º tri/2012 - atual |
| `V4005` | STRING | Na semana de ... a ... (semana de referência), ... tinha algum trabalho remunerado do qual estava temporariamente afastado? | 1º tri/2012 - atual |
| `V4006` | STRING | Na semana de ... a .... (semana de referência), por que motivo ... estava afastado desse trabalho? | 1º tri/2012 - 3º tri/2015 |
| `V4006A` | STRING | Na semana de ... a .... (semana de referência), por que motivo ... estava afastado desse trabalho? | 4º tri/2015 - atual |
| `V4007` | STRING | Durante o tempo de afastamento, ... continuou a receber ao menos uma parte do pagamento? | 1º tri/2012 - 3º tri/2015 |
| `V4008` | STRING | Em .../.../...(último dia da semana de referência), fazia quanto tempo que ... estava afastado desse trabalho? | 1º tri/2012 - atual |
| `V40081` | INTEGER | Tempo que estava afastado (De 1 mês a menos de 1 ano) | 1º tri/2012 - atual |
| `V40082` | INTEGER | Tempo que estava afastado (De 1 ano a menos de 2 anos) | 1º tri/2012 - atual |
| `V40083` | INTEGER | Tempo que estava afastado (de 02 anos a 98 anos) | 1º tri/2012 - atual |
| `V4009` | STRING | Quantos trabalhos ... tinha na semana de ... a ... (semana de referência ? | 1º tri/2012 - atual |
| `V4010` | STRING | Código da ocupação (cargo ou função) | 1º tri/2012 - atual |
| `V4012` | STRING | Nesse trabalho, ... era: | 1º tri/2012 - atual |
| `V40121` | STRING | Trabalhador não remunerado | 1º tri/2012 - atual |
| `V4013` | STRING | Código da principal atividade desse negócio/empresa | 1º tri/2012 - atual |
| `V40132` | STRING | Qual a seção da atividade? | 1º tri/2012 - 3º tri/2015 |
| `V40132A` | STRING | Qual a seção da atividade? | 4º tri/2015 - atual |
| `V4014` | STRING | Esse trabalho era na área: | 1º tri/2012 - atual |
| `V4015` | STRING | Na semana de ... a ... (semana de referência), ... teve ajuda, nesse trabalho, de pelo menos um trabalhador não remunerado que era membro do domicílio ou parente? | 1º tri/2012 - 3º tri/2015 e 3º tri/2016 - atual |
| `V40151` | STRING | Quantos trabalhadores não remunerados ? | 1º tri/2012 - 3º tri/2015 e 3º tri/2016 - atual |
| `V401511` | INTEGER | 1 a 5 trabalhadores não remunerados | 1º tri/2012 - 3º tri/2015 e 3º tri/2016 - atual |
| `V401512` | INTEGER | 6 a 10 trabalhadores não remunerados | 1º tri/2012 - 3º tri/2015 e 3º tri/2016 - atual |
| `V4016` | STRING | Na semana de ... a ... (semana de referência), quantos empregados trabalhavam nesse negócio/empresa que ... tinha ? | 1º tri/2012 - 3º tri/2015 e 3º tri/2016 - atual |
| `V40161` | INTEGER | 1 a 5 empregados | 1º tri/2012 - 3º tri/2015 e 3º tri/2016 - atual |
| `V40162` | INTEGER | 6 a 10 empregados | 1º tri/2012 - 3º tri/2015 e 3º tri/2016 - atual |
| `V40163` | INTEGER | 11 a 50 empregados | 1º tri/2012 - 3º tri/2015 e 3º tri/2016 - atual |
| `V4017` | STRING | Na semana de ... a ... (semana de referência), ... tinha pelo menos um sócio que trabalhava nesse negócio/empresa ? | 1º tri/2012 - 3º tri/2015 e 3º tri/2016 - atual |
| `V40171` | STRING | Quantos? | 1º tri/2012 - 3º tri/2015 e 3º tri/2016 - atual |
| `V401711` | INTEGER | 1 a 5 sócios | 1º tri/2012 - 3º tri/2015 e 3º tri/2016 - atual |
| `V4018` | STRING | Na semana de ... a ... (semana de referência), contando com ... , quantas pessoas trabalhavam nesse negócio/empresa ? | 1º tri/2012 - 3º tri/2015 e 3º tri/2016 - atual |
| `V40181` | INTEGER | 1 a 5 pessoas | 1º tri/2012 - 3º tri/2015 e 3º tri/2016 - atual |
| `V40182` | INTEGER | 6 a 10 pessoas | 1º tri/2012 - 3º tri/2015 e 3º tri/2016 - atual |
| `V40183` | INTEGER | 11 a 50 pessoas | 1º tri/2012 - 3º tri/2015 e 3º tri/2016 - atual |
| `V4019` | STRING | Esse negócio/empresa era registrado no Cadastro Nacional da Pessoa Jurídica - CNPJ? | 4º tri/2015 - atual |
| `V4020` | STRING | Em que tipo de local funcionava esse negócio/empresa ? | 1º tri/2018 - atual |
| `V4021` | STRING | ... exercia normalmente o trabalho em estabelecimento desse negócio/empresa ? | 1º tri/2018 - atual |
| `V4022` | STRING | Então onde ... exercia normalmente esse trabalho ? | 1º tri/2018 - atual |
| `V4024` | STRING | No período de ... a ... (período de referência de 30 dias) ... prestava serviço doméstico em mais de um domicílio ? | 1º tri/2012 - atual |
| `V4025` | STRING | Nesse trabalho, ... era contratado(a) como empregado temporário ? | 1º tri/2012 - atual |
| `V4026` | STRING | Na semana de ... a ... (semana de referência), ... era contratado(a) somente por pessoa responsável pelo negócio/empresa em que trabalhava ? | 1º tri/2017 - atual |
| `V4027` | STRING | Na semana de ... a ... (semana de referência) era contratado(a) somente por intermediário (empresa empreiteira, empreiteiro, "gato", etc.) ? | 1º tri/2017 - atual |
| `V4028` | STRING | Nesse trabalho, ... era servidor público estatutário (federal, estadual ou municipal) ? | 1º tri/2012 - atual |
| `V4029` | STRING | Nesse trabalho, ... tinha carteira de trabalho assinada ? | 1º tri/2012 - atual |
| `V4032` | STRING | Era contribuinte de instituto de previdência por esse trabalho ? | 1º tri/2012 - atual |
| `V4033` | STRING | Qual era o rendimento bruto mensal que ... recebia/fazia normalmente nesse trabalho? (variável auxiliar) | 1º tri/2012 - atual |
| `V40331` | STRING | Recebia/fazia normalmente nesse trabalho rendimento/retirada em dinheiro? | 1º tri/2012 - atual |
| `V403311` | STRING | Número da faixa do rendimento/retirada em dinheiro | 1º tri/2012 - atual |
| `V403312` | FLOAT | Qual era o rendimento bruto/retirada mensal que ... recebia/fazia normalmente nesse trabalho ? (valor em dinheiro) | 1º tri/2012 - atual |
| `V40332` | STRING | Recebia/fazia normalmente nesse trabalho rendimento/retirada em produtos e mercadorias ? | 1º tri/2012 - atual |
| `V403321` | STRING | Número da faixa do rendimento/retirada em produtos e mercadorias | 1º tri/2012 - atual |
| `V403322` | FLOAT | Qual era o rendimento bruto/retirada mensal que ... recebia/fazia normalmente nesse trabalho ? (valor estimado dos produtos ou mercadorias) | 1º tri/2012 - atual |
| `V40333` | STRING | Recebia/fazia normalmente nesse trabalho rendimento/retirada somente em benefícios ? | 1º tri/2012 - atual |
| `V403331` | STRING | Tipo de rendimento/retirada em benefícios que recebia/fazia nesse trabalho | 2º tri/2016 - atual |
| `V4034` | STRING | Qual foi o rendimento bruto que ... recebeu/fez nesse trabalho, no mês de referência? (variável auxiliar) | 1º tri/2012 - atual |
| `V40341` | STRING | Recebeu/fez nesse trabalho rendimento/retirada em dinheiro no mês de referência | 1º tri/2012 - atual |
| `V403411` | STRING | Número da faixa do rendimento/retirada em dinheiro | 1º tri/2012 - atual |
| `V403412` | FLOAT | Qual foi o rendimento bruto/retirada que ... recebeu/fez nesse trabalho, no mês de referência ? (valor em dinheiro) | 1º tri/2012 - atual |
| `V40342` | STRING | Recebeu/fez nesse trabalho no mês de referencia, rendimento/retirada em produtos e mercadorias | 1º tri/2012 - atual |
| `V403421` | STRING | Número da faixa do rendimento/retirada em produtos e mercadorias | 1º tri/2012 - atual |
| `V403422` | FLOAT | Qual foi o rendimento bruto/retirada que ... recebeu/fez nesse trabalho, no mês de referência ? (valor estimado dos produtos ou mercadorias) | 1º tri/2012 - atual |
| `V4039` | INTEGER | Quantas horas ... trabalhava normalmente, por semana, nesse trabalho principal? | 1º tri/2012 - atual |
| `V4039C` | INTEGER | Quantas horas ... trabalhou efetivamente na semana de referência nesse trabalho principal? | 4º tri/2015 - atual |
| `V4040` | STRING | Até o dia ... (último dia da semana de referência) fazia quanto tempo que ... estava nesse trabalho ? | 1º tri/2012 - atual |
| `V40401` | STRING | Fazia quanto tempo que estava nesse trabalho (de 1 mês a menos de 1 ano) | 1º tri/2012 - atual |
| `V40402` | STRING | Fazia quanto tempo que estava nesse trabalho (de 1 ano a menos de 2 anos) | 1º tri/2012 - atual |
| `V40403` | STRING | Fazia quanto tempo estava nesse trabalho (2 anos ou mais) | 1º tri/2012 - atual |
| `V4041` | STRING | Código da ocupação (cargo ou função) | 1º tri/2012 - atual |
| `V4043` | STRING | Nesse trabalho secundário, ... era | 1º tri/2012 - atual |
| `V40431` | STRING | Trabalhador familiar não remunerado | 1º tri/2012 - atual |
| `V4044` | STRING | Código da principal atividade desse negócio/empresa | 1º tri/2012 - atual |
| `V4045` | STRING | Esse trabalho era na área | 1º tri/2012 - atual |
| `V4046` | STRING | Esse negócio/empresa era registrado no Cadastro Nacional da Pessoa Jurídica - CNPJ? | 4º tri/2015 - atual |
| `V4047` | STRING | Nesse trabalho secundário era funcionário público estatutário (federal, estadual ou municipal)? | 1º tri/2012 - atual |
| `V4048` | STRING | Nesse trabalho secundário tinha carteira de trabalho assinada? | 1º tri/2012 - atual |
| `V4049` | STRING | Era contribuinte de instituto de previdência por esse trabalho secundário? | 1º tri/2012 - atual |
| `V4050` | STRING | Qual era o rendimento bruto mensal que ... recebia/fazia normalmente nesse trabalho secundário? (variável auxiliar) | 1º tri/2012 - atual |
| `V40501` | STRING | Recebia/fazia normalmente nesse trabalho secundário rendimento/retirada em dinheiro | 1º tri/2012 - atual |
| `V405011` | STRING | Número da faixa do rendimento/retirada em dinheiro | 1º tri/2012 - atual |
| `V405012` | FLOAT | Valor em dinheiro do rendimento mensal que recebia normalmente nesse trabalho secundário | 1º tri/2012 - atual |
| `V40502` | STRING | Recebia/fazia normalmente nesse trabalho secundário rendimento/retirada em produtos e mercadorias | 1º tri/2012 - atual |
| `V405021` | STRING | Número da faixa do rendimento/retirada em produtos e mercadorias | 1º tri/2012 - atual |
| `V405022` | FLOAT | Valor estimado dos produtos e mercadorias que recebia normalmente nesse trabalho secundário | 1º tri/2012 - atual |
| `V40503` | STRING | Recebia/fazia normalmente nesse trabalho secundário rendimento/retirada somente em benefícios | 1º tri/2012 - atual |
| `V405031` | STRING | Tipo de rendimento/retirada em benefícios que recebia/fazia nesse trabalho secundário | 2º tri/2016 - atual |
| `V4051` | STRING | Qual foi o rendimento bruto que ... recebeu/fez nesse trabalho secundário, no mês de referência? (variável auxiliar) | 1º tri/2012 - atual |
| `V40511` | STRING | Recebeu/fez nesse trabalho secundário rendimento/retirada em dinheiro no mês de referência | 1º tri/2012 - atual |
| `V405111` | STRING | Número da faixa do rendimento/retirada em dinheiro | 1º tri/2012 - atual |
| `V405112` | FLOAT | Valor em dinheiro do rendimento mensal que recebeu nesse trabalho secundário no mês de referência | 1º tri/2012 - atual |
| `V40512` | STRING | Recebeu/fez nesse trabalho secundário no mês de referencia, rendimento/retirada em produtos e mercadorias | 1º tri/2012 - atual |
| `V405121` | STRING | Número da faixa do rendimento/retirada em produtos e mercadorias | 1º tri/2012 - atual |
| `V405122` | FLOAT | Valor estimado dos produtos e mercadorias que recebia recebeu nesse trabalho secundário no mês de referência | 1º tri/2012 - atual |
| `V4056` | INTEGER | Quantas horas ... trabalhava normalmente, por semana, nesse trabalho secundário? | 1º tri/2012 - atual |
| `V4056C` | INTEGER | Quantas horas ... trabalhou efetivamente na semana de referência nesse trabalho secundário? | 4º tri/2015 - atual |
| `V4057` | STRING | Era contribuinte de instituto de previdência por esse(s) outro(s) trabalho(s)? | 1º tri/2012 - atual |
| `V4058` | STRING | Qual era o rendimento bruto mensal que ... recebia/fazia normalmente nesse(s) outro(s) trabalho(s)? (variável auxiliar) | 1º tri/2012 - atual |
| `V40581` | STRING | Recebia/fazia normalmente nesse(s) outro(s) trabalho(s) rendimento/retirada em dinheiro | 1º tri/2012 - atual |
| `V405811` | STRING | Número da faixa do rendimento/retirada em dinheiro | 1º tri/2012 - atual |
| `V405812` | FLOAT | Valor em dinheiro do rendimento mensal que recebia normalmente nesse(s) outro(s) trabalho(s) | 1º tri/2012 - atual |
| `V40582` | STRING | Recebia/fazia normalmente nesse(s) outro(s) trabalho(s) rendimento/retirada em produtos e mercadorias | 1º tri/2012 - atual |
| `V405821` | STRING | Número da faixa do rendimento/retirada em produtos e mercadorias | 1º tri/2012 - atual |
| `V405822` | FLOAT | Valor estimado do produtos e mercadorias que recebia normalmente nesse(s) outro(s) trabalho(s) | 1º tri/2012 - atual |
| `V40583` | STRING | Recebia/fazia normalmente nesse(s) outro(s) trabalho(s) rendimento/retirada somente em benefícios | 1º tri/2012 - atual |
| `V405831` | STRING | Tipo de rendimento/retirada em benefícios que recebia/fazia nesse(s) outro(s) trabalho(s) | 2º tri/2016 - atual |
| `V40584` | STRING | Não remunerado nesse(s) outro(s) trabalho(s) | 1º tri/2012 - atual |
| `V4059` | STRING | Qual foi o rendimento bruto que ... recebeu/fez nesse(s) outro(s) trabalho(s), no mês de referência? (variável auxiliar) | 1º tri/2012 - atual |
| `V40591` | STRING | Recebeu/fez nesse(s) outro(s) trabalho(s) rendimento/retirada em dinheiro no mês de referência | 1º tri/2012 - atual |
| `V405911` | STRING | Número da faixa do rendimento/retirada em dinheiro | 1º tri/2012 - atual |
| `V405912` | FLOAT | Valor em dinheiro do rendimento mensal que recebeu nesse(s) outro(s) trabalho(s) no mês de referência | 1º tri/2012 - atual |
| `V40592` | STRING | Recebeu/fez nesse(s) outro(s) trabalhos no mês de referencia, rendimento/retirada em produtos e mercadorias | 1º tri/2012 - atual |
| `V405921` | STRING | Número da faixa do rendimento/retirada em produtos e mercadorias | 1º tri/2012 - atual |
| `V405922` | FLOAT | Valor estimado do produtos e mercadorias que recebia normalmente nesse(s) outro(s) trabalho(s) no mês de referência | 1º tri/2012 - atual |
| `V4062` | INTEGER | Quantas horas ... trabalhava normalmente, por semana, nesse(s) outro(s) trabalho(s)? | 1º tri/2012 - atual |
| `V4062C` | INTEGER | Quantas horas ... trabalhou efetivamente na semana de referência nesses outros trabalhos? | 4º tri/2015 - atual |
| `V4063` | STRING | ... gostaria de trabalhar mais horas do que as ... (soma das horas declaradas nas variáveis VD4031, VD4032, VD4033) horas que efetivamente trabalhou no(s) trabalho(s) que tinha na semana de referência? | 1º tri/2012 - 3º tri/2015 |
| `V4063A` | STRING | ... gostaria de trabalhar mais horas do que as ... (soma das horas declaradas nos quesitos 39, 56 e 62) horas que normalmente trabalhava no(s) trabalho(s) que tinha na semana de referência? | 4º tri/2015 - atual |
| `V4064` | STRING | No mês de referência, ... estaria disponível para trabalhar mais do que as (soma das horas declaradas nas variáveis VD4031, VD4032, VD4033) horas que efetivamente trabalhou no(s) trabalho(s) que tinha na semana de referência? | 1º tri/2012 - 3º tri/2015 |
| `V4064A` | STRING | No mês de referência, ... estaria disponível para trabalhar mais do que as (soma das horas declaradas nos quesitos 39, 56 e 62) horas que normalmente trabalhava no(s) trabalho(s) que tinha na semana de referência? | 4º tri/2015 - atual |
| `V4071` | STRING | No período de ... a ... (período de referência de 30 dias), ... Tomou alguma providência para conseguir trabalho, seja um emprego ou um negócio próprio? | 1º tri/2012 - atual |
| `V4072` | STRING | No período de ... a ... (período de referência de 30 dias), qual foi a principal providência que ... tomou para conseguir trabalho? | 1º tri/2012 - 3º tri/2015 |
| `V4072A` | STRING | No período de ... a ... (período de referência de 30 dias), qual foi a principal providência que ... tomou para conseguir trabalho? | 4º tri/2015 - atual |
| `V4073` | STRING | Embora não tenha tomado providência para conseguir trabalho, gostaria de ter trabalhado na semana de ... a ... (semana de referência) ? | 1º tri/2012 - atual |
| `V4074` | STRING | Qual foi o principal motivo de ... não ter tomado providência para conseguir trabalho no período de ... a ... (período de referência de 30 dias)? | 1º tri/2012 - 3º tri/2015 |
| `V4074A` | STRING | Qual foi o principal motivo de ... não ter tomado providência para conseguir trabalho no período de ... a ... (período de referência de 30 dias)? | 4º tri/2015 - atual |
| `V4075A` | STRING | Quanto tempo depois de ... (último dia da semana de referência) irá começar esse trabalho que conseguiu? | 2º tri/2016 - atual |
| `V4075A1` | INTEGER | Número de meses para começar o trabalho que conseguiu | 2º tri/2016 - atual |
| `V4076` | STRING | Até o dia ... (último dia da semana de referência), fazia quanto tempo que ... estava sem qualquer trabalho e tentando conseguir trabalho? | 1º tri/2012 - atual |
| `V40761` | INTEGER | fazia quanto tempo que vinha procurando trabalho (de 1 mês a menos de 1 ano) | 1º tri/2012 - atual |
| `V40762` | INTEGER | fazia quanto tempo que vinha procurando trabalho (de 1 ano a menos de 2 anos) | 1º tri/2012 - atual |
| `V40763` | INTEGER | fazia quanto tempo vinha procurando trabalho (2 anos ou mais) | 1º tri/2012 - atual |
| `V4077` | STRING | Se tivesse conseguido um trabalho, ... poderia ter começado a trabalhar na semana de ... a ... (semana de referência)? | 1º tri/2012 - atual |
| `V4078` | STRING | Qual foi o principal motivo para ... não querer(poder começar a) trabalhar na semana de ... a ... (semana de referência)? | 1º tri/2012 - 3º tri/2015 |
| `V4078A` | STRING | Qual foi o principal motivo para ... não querer(poder começar a) trabalhar na semana de ... a ... (semana de referência)? | 4º tri/2015 - atual |
| `V4082` | STRING | No período de captação de 358 dias, ... trabalhou por pelo menos 1 hora? | 4º tri/2016 - atual |

### Variáveis derivadas — domicílio e educação (6)

| Coluna | Tipo | Descrição (dicionário do IBGE) | Período |
|---|---|---|---|
| `VD2002` | STRING | Condição no domicílio | 1º tri/2012 - atual |
| `VD2003` | INTEGER | Número de componentes do domicílio (exclusive as pessoas cuja condição no domicílio era pensionista, empregado doméstico ou parente do empregado doméstico) | 1º tri/2012 - atual |
| `VD2004` | STRING | Espécie da unidade doméstica | 1º tri/2012 - atual |
| `VD3004` | STRING | Nível de instrução mais elevado alcançado (pessoas de 5 anos ou mais de idade) padronizado para o Ensino fundamental - SISTEMA DE 9 ANOS | 1º tri/2012 - atual |
| `VD3005` | INTEGER | Anos de estudo (pessoas de 5 anos ou mais de idade) padronizado para o Ensino fundamental - SISTEMA DE 9 ANOS | 1º tri/2012 - atual |
| `VD3006` | STRING | Grupos de anos de estudo (pessoas de 5 anos ou mais de idade) padronizado para o Ensino fundamental - SISTEMA DE 9 ANOS | 1º tri/2012 - atual |

### Variáveis derivadas — trabalho e rendimento (29)

| Coluna | Tipo | Descrição (dicionário do IBGE) | Período |
|---|---|---|---|
| `VD4001` | STRING | Condição em relação à força de trabalho na semana de referência para pessoas de 14 anos ou mais de idade | 1º tri/2012 - atual |
| `VD4002` | STRING | Condição de ocupação na semana de referência para pessoas de 14 anos ou mais de idade | 1º tri/2012 - atual |
| `VD4003` | STRING | Força de trabalho potencial para pessoas de 14 anos ou mais de idade | 1º tri/2012 - atual |
| `VD4004` | STRING | Subocupação por insuficiência de horas efetivamente trabalhadas em todos os trabalhos | 1º tri/2012 - 3º tri/2015 |
| `VD4004A` | STRING | Subocupação por insuficiência de horas habitualmente trabalhadas em todos os trabalhos | 4º tri/2015 - atual |
| `VD4005` | STRING | Pessoas desalentadas na semana de referência | 1º tri/2012 - atual |
| `VD4007` | STRING | Posição na ocupação no trabalho principal da semana de referência para pessoas de 14 anos ou mais de idade | 1º tri/2012 - atual |
| `VD4008` | STRING | Posição na ocupação no trabalho principal da semana de referência para pessoas de 14 anos ou mais de idade (com subcategorias de empregados) | 1º tri/2012 - atual |
| `VD4009` | STRING | Posição na ocupação e categoria do emprego do trabalho principal da semana de referência para pessoas de 14 anos ou mais de idade | 1º tri/2012 - atual |
| `VD4010` | STRING | Grupamentos de atividade principal do empreendimento do trabalho principal da semana de referência para pessoas de 14 anos ou mais de idade | 1º tri/2012 - atual |
| `VD4011` | STRING | Grupamentos ocupacionais do trabalho principal da semana de referência para pessoas de 14 anos ou mais de idade | 1º tri/2012 - atual |
| `VD4012` | STRING | Contribuição para instituto de previdência em qualquer trabalho da semana de referência para pessoas de 14 anos ou mais de idade | 1º tri/2012 - atual |
| `VD4013` | STRING | Faixa das horas habitualmente trabalhadas por semana em todos os trabalhos para pessoas de 14 anos ou mais de idade | 1º tri/2012 - atual |
| `VD4014` | STRING | Faixa das horas efetivamente trabalhadas na semana de referência em todos os trabalhos para pessoas de 14 anos ou mais de idade | 1º tri/2012 - atual |
| `VD4015` | STRING | Tipo de remuneração habitualmente recebida no trabalho principal para pessoas de 14 anos ou mais de idade | 1º tri/2012 - atual |
| `VD4016` | FLOAT | Rendimento mensal habitual do trabalho principal para pessoas de 14 anos ou mais de idade (apenas para pessoas que receberam em dinheiro, produtos ou mercadorias no trabalho principal) | 1º tri/2012 - atual |
| `VD4017` | FLOAT | Rendimento mensal efetivo do trabalho principal para pessoas de 14 anos ou mais de idade (apenas para pessoas que receberam em dinheiro, produtos ou mercadorias no trabalho principal) | 1º tri/2012 - atual |
| `VD4018` | STRING | Tipo de remuneração habitualmente recebida em todos os trabalhos para pessoas de 14 anos ou mais de idade | 1º tri/2012 - atual |
| `VD4019` | FLOAT | Rendimento mensal habitual de todos os trabalhos para pessoas de 14 anos ou mais de idade (apenas para pessoas que receberam em dinheiro, produtos ou mercadorias em qualquer trabalho) | 1º tri/2012 - atual |
| `VD4020` | FLOAT | Rendimento mensal efetivo de todos os trabalhos para pessoas de 14 anos ou mais de idade (apenas para pessoas que receberam em dinheiro, produtos ou mercadorias em qualquer trabalho) | 1º tri/2012 - atual |
| `VD4023` | STRING | Motivo pelo qual não procurou trabalho ou não gostaria de ter trabalhado ou não estava disponível para iniciar um trabalho | 1º tri/2012 - 3º tri/2015 |
| `VD4030` | STRING | Motivo pelo qual não procurou trabalho ou não gostaria de ter trabalhado ou não estava disponível para iniciar um trabalho | 4º tri/2015 - atual |
| `VD4031` | INTEGER | Horas habitualmente trabalhadas por semana em todos os trabalhos para pessoas de 14 anos ou mais de idade | 1º tri/2012 - atual |
| `VD4032` | INTEGER | Horas efetivamente trabalhadas na semana de referência no trabalho principal para pessoas de 14 anos ou mais de idade | 1º tri/2012 - 3º tri/2015 |
| `VD4033` | INTEGER | Horas efetivamente trabalhadas na semana de referência no trabalho secundário para pessoas de 14 anos ou mais de idade | 1º tri/2012 - 3º tri/2015 |
| `VD4034` | INTEGER | Horas efetivamente trabalhadas na semana de referência nos outros trabalhos para pessoas de 14 anos ou mais de idade | 1º tri/2012 - 3º tri/2015 |
| `VD4035` | INTEGER | Horas efetivamente trabalhadas na semana de referência em todos os trabalhos para pessoas de 14 anos ou mais de idade | 1º tri/2012 - atual |
| `VD4036` | STRING | Faixa das horas habitualmente trabalhadas por semana no trabalho principal para pessoas de 14 anos ou mais de idade | 1º tri/2012 - atual |
| `VD4037` | STRING | Faixa das horas efetivamente trabalhadas na semana de referência no trabalho principal para pessoas de 14 anos ou mais de idade | 1º tri/2012 - atual |

### Deflatores (2)

| Coluna | Tipo | Descrição (dicionário do IBGE) | Período |
|---|---|---|---|
| `habitual` | FLOAT | Deflator do rendimento habitual (acrescentado pela Base dos Dados) — NULL de 2021-T4 em diante |  |
| `efetivo` | FLOAT | Deflator do rendimento efetivo (acrescentado pela Base dos Dados) — NULL de 2021-T4 em diante |  |

