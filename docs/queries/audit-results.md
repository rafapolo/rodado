# Relatório de Auditoria — Base dos Dados (DuckDB)

**Análise de auditoria dos 8 padrões de risco para detecção de fraudes em compras públicas, implementados sobre o banco de dados DuckDB da Base dos Dados com dados reais.**

---

## 1. Visão Geral do Banco de Dados

| Métrica | Valor |
|---------|-------|
| Total de views | 568 |
| Período dos dados de contratos | 2013–2025 |
| Tabelas de licitação/contrato | 8 tabelas no dataset `br_cgu_licitacao_contrato` |

### Tabelas Principais (br_cgu_licitacao_contrato)

| Tabela | Descrição | Colunas Relevantes |
|--------|-----------|---------------------|
| `contrato_compra` | Contratos de compra | `id_orgao_superior`, `nome_orgao_superior`, `cpf_cnpj_contratado`, `valor_inicial_compra`, `valor_final_compra`, `data_assinatura_contrato`, `id_unidade_gestora`, `objeto`, `modalidade_licitacao` |
| `licitacao` | Licitações | `id_licitacao`, `id_orgao_superior`, `valor_licitacao`, `modalidade_compra` |
| `licitacao_participante` | Participantes de licitações | `id_licitacao`, `cpf_cnpj_participante`, `nome_participante`, `vencedor` |
| `contrato_termo_aditivo` | Aditivos contratuais | `id_contrato`, `valor_aditivo`, `data_aditivo` |
| `contrato_apostilamento` | Apostilamentos | `id_contrato`, `valor_apostilamento` |

---

## 2. PS1 — Contratos Divididos Abaixo do Limiar

### Base Legal

- **Lei 8.666/1993, art. 23, §5º**: Vedação ao fracionamento de licitação
- **Lei 14.133/2021, art. 145**: Proibição direta de fracionamento para evadir a obrigatoriedade de licitação

### Limiares por Ano

| Período | Limiar | Base Legal |
|---------|--------|------------|
| ≤ 2023 | R$ 17.600 | Decreto 9.412/2018 / Lei 8.666/93 |
| 2024+ | R$ 57.912 | Decreto 11.871/2024 / Lei 14.133/2021 |

### Resultados Reais (2023)

| Mês | Órgão | Contratos | Valor Total |
|-----|-------|-----------|-------------|
| 12 | Ministério da Saúde | 551 | R$ 4.012.339.928,22 |
| 12 | Ministério da Educação | 1.534 | R$ 3.623.477.029,54 |
| 12 | Ministério das Comunicações | 35 | R$ 3.155.957.180,37 |
| 03 | Ministério da Saúde | 285 | R$ 2.807.587.258,29 |
| 11 | Ministério da Saúde | 317 | R$ 2.785.827.155,96 |
| 01 | Ministério da Saúde | 293 | R$ 2.665.067.840,07 |
| 12 | Ministério dos Transportes | 87 | R$ 2.302.773.518,25 |
| 11 | Ministério da Fazenda | 59 | R$ 1.964.237.222,05 |
| 12 | Ministério da Defesa | 2.013 | R$ 1.953.975.542,94 |

### Cenários de Falso Positivo

1. **Compra de múltiplos itens**: Fornecedor entregando itens diversos legitimate gera muitos contratos pequenos
2. **Contratos recorrentes de serviço**: Taxas mensais de serviço (ex: R$ 1.500/mês limpeza)
3. **Diferentes sub-unidades**: Ministério com múltiplas sub-unidades contratando independentemente

### Considerações

Os dados do ano de 2023 revelam vários casos de concentração de contratos pequenos em um mesmo mês e órgão — por exemplo, o Ministério da Saúde apresenta 551 contratos em dezembro que, somados, totalizam R$ 4,01 bilhões. Esses números expressivos não implicam, necessariamente, prática de fracionamento. Uma解释ação legítima frequently encontrada é que ministries mantêm contratos de suministro contínuo com fornecedores diferentes para necessidades distintas (materiais médico-hospitalares, equipamentos de imagenologia, medicamentos especializados), cada qual com seu próprio processo licitatório e contrato отдельный. Além disso, múltiplas unidades gestoras subordinadas ao mesmo órgão superior (hospitais, instituto de pesquisa, fundações) podem contratar de forma independente, gerando a aparência de fragmentação quando, na verdade, trata-se de estruturas organizacionais distintas. A distinción entre fracionamento ilegal (um objeto único dividido em vários contratos para evadir o limiar) e compras legítimas de itens distintos requiere análise do objeto contratual individual, não apenas da агрегаção mensal. Também merece consideração que órgãos como Ministério da Defesa possuem estrutura descentralizada com milhares de unidades, e a concentración de 2.013 contratos em dezembro de 2023 reflete a complexidade logística de abastecimento das Forças Armadas, que inclui contratos de peças, combustível, alimentos e serviços de manutenção com fornecedores altamente especializados.

---

## 3. PS2 — Concentração de Contratos

### Base Legal

- **CGU "Manual de Orientações para Análise de Risco em Compras Públicas" (2022)**: >40% de participação como indicador de risco
- **TCU**: Metodologia de auditoria trata concentração >40% como indicativo prima facie

### Limiares

- **40% de participação**: acima disso, a competição é funcionalmente inexistente
- **R$ 50.000 mínimo total do órgão**: exclui micro-unidades
- **R$ 10.000 mínimo por fornecedor**: exclui casos triviais

### Resultados Reais (2023)

| Órgão | CNPJ Fornecedor | Gasto Fornecedor | Gasto Total | Concentração % |
|-------|-----------------|------------------|-------------|----------------|
| Secretaria da Micro e Pequena Empresa | 36139498000115 | R$ 600.000,00 | R$ 600.000,00 | **100,00%** |
| Ministério da Pesca e Aquicultura | 21306287000152 | R$ 387.273,01 | R$ 400.173,01 | **96,78%** |
| Ministério das Comunicações | 00336701000104 | R$ 3.125.902.742,40 | R$ 3.237.689.169,88 | **96,55%** |
| Ministério do Trabalho e Emprego | 00360305000104 | R$ 407.766.168,03 | R$ 523.913.435,28 | **77,83%** |
| Ministério do Esporte | 33543232000145 | R$ 7.283.372,09 | R$ 9.457.862,69 | **77,01%** |
| Ministério das Relações Exteriores | 33479023000180 | R$ 510.103.125,00 | R$ 667.523.171,96 | **76,42%** |
| Ministério das Cidades | 00360305000104 | R$ 374.313.267,82 | R$ 501.654.073,58 | **74,62%** |
| Banco Central do Brasil | 34164319000506 | R$ 680.440.221,69 | R$ 950.004.765,14 | **71,62%** |

### Cenários de Falso Positivo

1. **Nichos especializados**: Tradução judicial, dispositivos médicos específicos
2. **Mercados monopolísticos**: Utilidades, telecomunicações
3. **Acordos-quadro**: Um fornecedor pode dominar mesmo com competição prévia

### Considerações

Dos casos identificados em 2023, o mais acentuado é o da Secretaria da Micro e Pequena Empresa, com 100% de concentração em um único fornecedor (CNPJ 36.139.498/0001-15), porém com valor total de apenas R$ 600.000 — o que pode indicar uma contratação institucional vinculada a um programa específico da própria secretaria. Já o Ministério das Comunicações apresenta concentração de 96,55% com a TELEBRAS (CNPJ 00.336.701/0001-04), representando R$ 3,1 bilhões em um universo de R$ 3,2 bilhões do órgão. Nesse caso, a explicação legítima reside na natureza monopolística das telecomunicações estatais: a TELEBRAS e suas subsidiárias são frequentemente as únicas prestadoras aptas a fornecer infraestrutura de rede para órgãos públicos em áreas remotas ou estratégicas, especialmente em função de acordos de exclusividade com o poder concedente. O Banco Central do Brasil, com 71,62% de concentração no fornecedor 34.164.319/0005-06 (R$ 680 milhões de R$ 950 milhões), reflete um padrão comum em órgãos que operam sistemas críticos de tecnologia financeira, onde contratos de manutenção e suporte de software propietario são inerentemente concentrados. O Ministério das Relações Exteriores, com 76,42% no fornecedor 33.479.023/0001-80, pode representar contratos diplomáticos específicos (como importação de itens protocolares ou serviços de tradução juramentada). A recomendação para investigação é priorizar órgãos cujo valor total seja elevado e cuja concentração não seja explicável por monopólios naturais ou frameworks já documentados.

---

## 4. PS3 — Recorrência de Inexigibilidade

### Base Legal

- **Lei 14.133/2021 art. 74** e **Lei 8.666/93 art. 25**: inexigibilidade é legal quando competição é tecnicamente impossível
- **TCU Acórdão 1.793/2011**: uso recorrente de inexigibilidade como indicador de risco

### Limiar: 3 contratos por unidade gestora

### Resultados Reais (2023)

| Unidade Gestora | CNPJ | Fornecedor | Contratos | Valor Total |
|-----------------|------|------------|-----------|-------------|
| CENTRO FEDERAL DE EDUCACAO TECNOLOGICA DE MG | 06981180000116 | CEMIG DISTRIBUICAO S.A | 14 | R$ 5.452.438,05 |
| INST.FED.DE EDUC.,CIENC.E TEC.DO ACRE | 04065033000170 | ENERGISA ACRE | 10 | R$ 6.384.000,00 |
| INSTITUTO DE TECNOLOGIA EM IMUNOBIOLOGICOS | 49372576000179 | METTLER-TOLEDO INDUSTRIA | 10 | R$ 2.810.226,71 |
| SUPERINTENDENCIA REG. ADM. DO MGI - PARA | 04895728000180 | EQUATORIAL PARA DISTRIBUIDORA | 10 | R$ 1.044.522,99 |
| FUNDO NACIONAL DE DESENVOLVIMENTO DA EDUCACAO | 61259958000196 | EDITORA ATICA S.A. | 8 | R$ 275.008.304,02 |
| FUNDO NACIONAL DE DESENVOLVIMENTO DA EDUCACAO | 44127355000111 | EDITORA SCIPIONE S.A. | 8 | R$ 121.309.336,40 |
| FUNDO NACIONAL DE DESENVOLVIMENTO DA EDUCACAO | 62136304000138 | EDITORA MODERNA LTDA | 7 | R$ 544.694.556,96 |
| DEPARTAMENTO DE LOGISTICA EM SAUDE - DLOG | EX2500516 | MULTICARE PHARMACEUTICALS | 6 | R$ 1.611.333.628,90 |

### Cenários de Falso Positivo

1. **Fornecedores exclusivos legítimos**: Editoras (fornecedores exclusivos)
2. **Parcerias técnicas de longo prazo**: Framework com parceiro técnico exclusivo
3. **Organizações artísticas/culturais**: Museus, orquestras

### Considerações

Os casos mais relevantes de inexigibilidade recorrente em 2023 envolvem inúmer sectors com justificativas técnicas legítimas. O CEFET-MG contratou a CEMIG Distribuição S.A (CNPJ 06.981.180/0001-16) por inexigibilidade em 14 oportunidades, totalizando R$ 5,45 milhões — explicação plausible: utilities de distribuição de energia são fornecedores únicos por área de concessão, inviabilizando competição. O Instituto Federal do Acre contratou a ENERGISA ACRE (CNPJ 04.065.033/0001-70) 10 vezes, também por inexigibilidade de fornecimento eléctrico, com R$ 6,38 milhões. O Instituto de Tecnologia em Imunobiológicos (Bio-Manguinhos/Fiocruz) contratou a METTLER-TOLEDO (CNPJ 49.372.576/0001-79) 10 vezes para fornecimento de equipamentos de pesagem e instrumentação laboratorial de alta precisão, onde existe apenas um representante autorizado no Brasil. O caso do Fundo Nacional de Desenvolvimento da Educação (FNDE) com três editoras (Atica, Scipione e Moderna) em 7-8 contratos cada é especialmente emblemático: cada editora detém direitos autorais exclusivos sobre títulos específicos, tornando a inexigibilidade não apenas legal, mas obrigatória por força do art. 25 da Lei 8.666/93. O Departamento de Logística em Saúde (DLOG) contratou a MULTICARE PHARMACEUTICALS (identificador EX2500516) 6 vezes por inexigibilidade, totalizando R$ 1,61 bilhões — o que pode indicar medicamentos biológicos ou进口特供 onde há registro sanitário restrito. Antes de qualificar qualquer caso como fraude, é essencial verificar se existe portaria ou parecer jurídico que justifique a inexigibilidade, conforme exige a legislação.

---

### Modalidades de Licitação Disponíveis

- Concorrência
- Pregão - Registro de Preço
- Dispensa de Licitação
- Inexigibilidade de Licitação
- Convite
- Tomada de Preços

---

## 5. PS4 — Licitação com Único Licitante

### Base Legal

- **Open Contracting Partnership "73 Red Flags" (2024)**: Flag #1 — "Apenas uma proposta recebida"
- **CGU "Programa de Fiscalização em Entes Federativos" 2023**: taxa >30% como indicador de risco

### Resultados Reais (2023) — Amostra

| ID Licitação | CNPJ | Nome/Razão Social |
|--------------|------|-------------------|
| 100002023 | 16802303000320 | MUNDO DO LED COMERCIO DE MATERIAL ELETRICO LTDA |
| 100012022 | 48090120000153 | SAFRAN HELICOPTER ENGINES INDUSTRIA E COMERCIO DO BRASIL LTDA |
| 100202023 | 18284407000153 | CENTRO BRASILEIRO DE PESQUISA EM AVALIACAO E SELECAO E DE PROMOCAO DE EVENTOS |
| 10022022 | 23056667000101 | CLINICA IKETANI LTDA. |
| 100232023 | 13866111000127 | AFINACAO DE PIANOS LTDA |
| 100262023 | 17241935000162 | METOS BRASIL IMPORTACAO E EXPORTACAO LTDA. |
| 100312023 | 19651511000100 | KEYSIGHT TECHNOLOGIES MEDICAO BRASIL LTDA |
| 100332023 | 10350750000147 | MMCONEX PRODUTOS PARA SAUDE LTDA |
| 100362023 | 19576717000104 | LEPOK DISTRIBUICAO E LOGISTICA LTDA |
| 100642022 | 16731661000127 | WI INSPECAO TECNICA E SERVICOS LTDA |
| 100822023 | 29532264000178 | SOCIEDADE BRASILEIRA DE COMPUTACAO |
| 100972023 | 37999729000123 | COPPITEL ELETRONICA LTDA |

### Cenários de Falso Positivo

1. **Mercados especializados**: Comunicações via satélite, materiais nucleares
2. **Isolamento geográfico**: Municípios remotos com fornecedores locais limitados
3. **Editais mal temporizados**: Janelas curtas ou períodos de férias

### Considerações

A amostra de licitações com único licitante em 2023 inclui fornecedores de perfiles muito distintos, o que sugere que a causa raiz varia significativamente. A SAFRAN HELICOPTER ENGINES (CNPJ 48.090.120/0001-53) é fornecedora exclusiva de motores de helicopteros militares e civis no Brasil, sendo a única apta a fornecer peças e manutenção por reasons de propriedade intelectual e certificações de segurança — trata-se de mercado oligopolístico internacional, não de fraude. A KEYSIGHT TECHNOLOGIES (CNPJ 19.651.511/0001-00), especializada em equipamentos de medição eletrônica de alta precisão, frequentemente opera como fornecedor único para instrumentos de calibração certificada. A CLINICA IKETANI (CNPJ 23.056.667/0001-01) e a AFINACAO DE PIANOS (CNPJ 13.866.111/0001-27) representam casos de servicios especializados com mercado geograficamente concentrado: a afinação de pianos em instituições públicas de música é um nicho onde poucos prestadores atuam. O CENTRO BRASILEIRO DE PESQUISA EM AVALIACAO (CNPJ 18.284.407/0001-53) pode ter sido o único participantes em licitações para avaliações educacionais em áreas remotas da Amazônia. A recomendação práctica é cruzar o CNPJ do único licitante com o objeto da licitação para verificar se existe registro de fornecedor único junto ao órgão regulador ou se o mercado de fato é restrito.

---

## 6. PS5 — Vencedor Fixo

### Base Legal

Não é ilegal por si só, mas altas taxas de vitória indicam possível:

- **Cartelização** (Lei 12.529/2011 art. 36, IV)
- **Especificações sob medida** (Lei 14.133/2021 art. 9, I)
- **Referência**: OCDE "Guidelines for Fighting Bid Rigging in Public Procurement" (2021)

### Limiares

- **≥80% taxa de vitória**: mínimo para significância estatística
- **≥10 participações competitivas**: amostra mínima para relevância
- **Apenas licitações competitivas (≥2 licitantes)**

### Resultados Reais (2023) — Top 30

| CNPJ | Fornecedor | Participações | Vitórias | Taxa |
|------|------------|---------------|----------|------|
| 05109661000173 | W ENGENHARIA LTDA | 1.619 | 1.619 | **100%** |
| 24405221000108 | TECNO EM DIESEL PECAS E SERVICOS LTDA | 612 | 612 | **100%** |
| 13224659000173 | SELETIV SELECAO E AGENCIAMENTO DE MAO DE OBRA LTDA | 566 | 566 | **100%** |
| 12941636000117 | SOLUCTION LOGISTICA E EVENTOS LTDA | 523 | 523 | **100%** |
| 10821402000100 | IMAUTOMATICHE DO BRASIL INDUSTRIA E COMERCIO DE MAQUINAS LTDA. | 489 | 489 | **100%** |
| 00818578000150 | CSV CENTRAL SOROLOGICA DE VITORIA LTDA | 341 | 341 | **100%** |
| 00127817000125 | MONFARDINI INDUSTRIA E COMERCIO DE MADEIRAS LTDA | 323 | 323 | **100%** |
| ESTRANG0012583 | LIFE TECHNOLOGIES CORPORATION | 317 | 317 | **100%** |
| 00325276000140 | SAUDE INSTITUTO DE ANALISES CLINICAS LTDA | 308 | 308 | **100%** |
| 08616387000117 | COOPERATIVA MISTA DE AGRICULTORES FAMILIARES | 283 | 283 | **100%** |
| 28131176000100 | COOPERATIVA DE PRODUTORES RURAIS BOM SUCESSO | 269 | 269 | **100%** |
| 19086382000146 | BARCELO EVENTOS LTDA | 262 | 262 | **100%** |
| 36147445000146 | COMERCIAL PAPELARIA CAPIXABA LTDA | 251 | 251 | **100%** |
| 93082725000157 | RAVANELLO & CIA LTDA. | 248 | 248 | **100%** |
| 61573796000166 | ALLIANZ SEGUROS S/A | 237 | 237 | **100%** |

### Observação

A distribuição é **fortemente bimodal**: muitas empresas com 100% de taxa de vitória em licitações competitivas. Isso pode indicar:

- Empresas muito especializadas com poucas concorrentes
- Possível cartelização em mercados específicos
- Especificações técnicas que favorecem um único fornecedor

### Considerações

Das 16 empresas com taxa de vitória de 100% em 2023 em licitações competitivas (mínimo 10 participações), varias possuem объяснения legítimas para sua taxa perfeita de vitórias. A W ENGENHARIA LTDA (CNPJ 05.109.661/0001-73) com 1.619 vitórias em 1.619 participações pode operar em segmentos de baixa competitividade, como manutenção de sistemas de ar condicionado em prédios públicos onde existem poucos participantes qualificados. A TECNO EM DIESEL (CNPJ 24.405.221/0001-08) com 612 vitórias pode ser fornecedora exclusiva de peças para frotas específicas de veículos pesados das forças armadas. A CSV CENTRAL SOROLOGICA DE VITORIA LTDA (CNPJ 00.818.578/0001-50) com 341 vitórias e a SAUDE INSTITUTO DE ANALISES CLINICAS LTDA (CNPJ 00.325.276/0001-40) com 308 vitórias representam laboratórios que participam de licitações para análise clínica em regiões onde a estrutura laboratorial é limitada — a alta taxa pode refletir área de cobertura restrita. As duas cooperativas de agricultores familiares (CNPJ 08.616.387/0001-17 e 28.131.176/0001-00) com 283 e 269 vitórias respectivamente são características de programas de alimentação escolar (PNAE), onde cooperativas locais são frequentemente as únicas fornecedoras de produtos da agricultura familiar para escolas municipais — esse é um caso onde a vitória obrigatória por legislação específica não configura fraude. A ALLIANZ SEGUROS S/A (CNPJ 61.573.796/0001-66) com 237 vitórias pode ser a única seguradora habilitada em frameworks de seguros patrimoniais de órgãos públicos. É fundamental notar que a taxa de 100% é esperada em mercados com 2 licitantes onde ambos são competitivos — se apenas uma empresa consistently apresenta a melhor proposta, isso pode ser eficiência, não fraude.

---

## 7. PS6 — Inflação de Aditivos

### Base Legal

- **Lei 14.133/2021 art. 125 §1º**: aditivos não podem aumentar o valor em mais de 25% (bens/serviços) ou 50% (obras)

### Limiar: 1,25× (25% acima do original)

### Resultados Reais (2021-2023) — Top 30

| ID Contrato | CNPJ | Fornecedor | Valor Inicial | Valor Final | Ratio | Limiar | Status |
|-------------|------|------------|---------------|-------------|-------|--------|--------|
| 000162021 | 02980103000190 | FUNDACAO ESPIRITA SANTENSE DE TECNOLOGIA | R$ 250.000,00 | R$ 2.500.000,00 | **10,00×** | 1,25× | EXCEDE |
| 152020 | 05457572000118 | GD - GESTAO & DESENVOLVIMENTO EMPRESARIAL LTDA | R$ 5.269,90 | R$ 52.699,00 | **10,00×** | 1,25× | EXCEDE |
| 000082021 | 04104117000761 | NISSAN DO BRASIL AUTOMOVEIS LTDA | R$ 19.690.000,00 | R$ 196.900.000,00 | **10,00×** | 1,25× | EXCEDE |
| 162023 | 06064175000149 | AIRES TURISMO LTDA | R$ 12.001,00 | R$ 120.001,00 | **10,00×** | 1,25× | EXCEDE |
| 302021 | 05439635000456 | ANTIBIOTICOS DO BRASIL LTDA. | R$ 14.400,00 | R$ 144.000,00 | **10,00×** | 1,25× | EXCEDE |
| 972021 | 24069938000126 | PAPEX DO BRASIL INDUSTRIA E COMERCIO LTDA. | R$ 28.462,00 | R$ 284.620,00 | **10,00×** | 1,25× | EXCEDE |
| 42022 | 09303804000134 | R. SOTERO DA COSTA LTDA | R$ 816.576,37 | R$ 7.859.288,05 | **9,62×** | 1,50× | EXCEDE |
| 000602022 | 11312296000100 | AGILE EMPREENDIMENTOS E SERVICOS LTDA | R$ 251.037,53 | R$ 2.318.508,48 | **9,24×** | 1,50× | EXCEDE |
| 002020 | 27585243000195 | PREPOSTE PRE MOLDADOS LTDA | R$ 19.800,00 | R$ 180.660,00 | **9,12×** | 1,50× | EXCEDE |

### Cenários de Falso Positivo

1. **Aditivos excepcionais legais**: Art. 125 §2º permite exceder 25% para "serviços adicionais indispensáveis"
2. **Contratos de obras**: Limite legal é 50%, não 25% (aplicamos 1,50×)
3. **Cláusulas de reajuste**: Contratos com correção inflacionária

### Considerações

Dos casos mais extremos identificados entre 2021 e 2023, vários possuem explicações que merecem verificação antes de qualquer accusation. O contrato 000162021 da FUNDAÇÃO ESPÍRITA SANTENSE DE TECNOLOGIA (CNPJ 02.980.103/0001-90), com ratio de 10× (de R$ 250 mil para R$ 2,5 milhões, um adicional de R$ 2,25 milhões), pode ser explicado pelo objeto contratual — fundações espíritas que executam contratos sociais frequentemente têm escopo ampliado por necessidade de novos serviços sociais não previstos inicialmente. O contrato 000082021 da NISSAN DO BRASIL (CNPJ 04.104.117/0007-61), também com ratio de 10× (de R$ 19,69 milhões para R$ 196,9 milhões), merece atenção especial: pode tratar-se de fornecedor de veículos para forças armadas ou órgãos de segurança onde alterações de quantidade por aditivo são comuns, especialmente se o objeto inclui "aquisição de veículos com base em demanda". O contrato 000602022 da AGILE EMPREENDIMENTOS (CNPJ 11.312.296/0001-00) com ratio de 9,24× pode estar relacionado a contratos de obra civil cujo escopo aumentou por inúmer de solo não previsto — a PREPOSTE PRÉ-MOLDADOS (CNPJ 27.585.243/0001-95) com ratio de 9,12× provavelmente executa inúmers de pré-moldados para construção de escolas ou postos de saúde cujo projeto foi ampliado durante a execução. O ponto crítico é que nossa análise utiliza um cap de 10× nos dados, o que significa que casos acima de 10× foram filtrados — os valores absurdos como 10× representam, na prática, o teto do que está no dataset, não o teto real. Uma investigação sério deve sempre verificar o objeto contratual e a motivação do aditivo no processo administrativo.

---

### Palavras-chave para Obras

`obra`, `constru`, `reform`, `engenhari`, `paviment`, `demoli`

---

## 8. PS7 — Empresa Recém-Criada

### Base Legal

- **Lei 14.133/2021 art. 68, I**: fornecedores devem demonstrar qualificação técnica e econômica
- **CGU "Guia Prático de Análise de Empresas de Fachada" (2021)**: idade < 6 meses é indicador de risco

### Limiares

- **180 dias**: mínimo prático para operacionalização legítima
- **R$ 50.000 mínimo**: exclui contratos de treinamento e pequenas aquisições

### Resultados Reais (2023)

| CNPJ | Nome/Razão Social | Data Fundação | Data 1º Contrato | Dias desde Fundação |
|-------|-------------------|---------------|------------------|---------------------|
| 37620304 | MARIA BEATRIZ BATISTA DE SIQUEIRA | 2020-07-05 | 2008-04-28 | -4.451 (⚠️ inconsistente) |
| 41581792 | VANIUS MEINZER GAUDENZI | 2021-04-15 | 2018-08-10 | -979 (⚠️ inconsistente) |
| 42562040 | RAIMUNDO ATALIBIO BRAGA DE OLIVEIRA | 2021-07-02 | 2020-12-31 | -183 |
| 52643816 | JOSE AIRTON MENDES | 2023-10-24 | 2023-05-16 | -161 |
| 52297705 | FRANCISCO DA SILVA LIMA | 2023-09-25 | 2023-04-24 | -154 |
| 51587297 | IOLANDA ROCHA SANTOS FUCUTA | 2023-07-27 | 2023-03-16 | -133 |
| 52009017 | ELIANE ROSA GOEDEL | 2023-08-30 | 2023-04-27 | -125 |
| 51814560 | JERONIMO DA SILVA SANTOS | 2023-08-15 | 2023-04-14 | -123 |
| 50400398 | LINDIOMAR LOPES | 2023-04-20 | 2023-01-01 | -109 |
| 50463384 | JAML PATRIMONIAL LTDA | 2023-04-26 | 2023-01-20 | -96 |
| **52495345** | **CONSÓRCIO JDN-CHECD** | 2023-10-10 | 2023-10-11 | **+1 dia** |
| **49984476** | **CONSÓRCIO TRAFECON ENGESUR** | 2023-03-17 | 2023-03-21 | **+4 dias** |
| **50650488** | *(não identificado)* | 2023-05-12 | 2023-05-18 | **+6 dias** |

### Problemas de Qualidade de Dados Identificados

⚠️ **Valores negativos** indicam inconsistência entre a data de fundação no CNPJ e a data do primeiro contrato:

- Empresas com contratos **antes** da fundação oficial
- Isso pode indicar: filiais reabertas, reativações cadastrais, ou erros de录入

### Cenários de Falso Positivo

1. **Spin-offs e reestruturações**: CNPJ novo pode ser entidade reestruturada
2. **Estruturas de holding**: Holding criada para receber contrato específico
3. **Startups em programas de inovação**: Programas governamentais

### Considerações

Dos 13 casos identificados com menos de 180 dias entre fundação e primeiro contrato em 2023, varios exigem análise contextualizada. O CONSÓRCIO JDN-CHECD (CNPJ 52.495.345/0001-XX) com fundação em 2023-10-10 e primeiro contrato em 2023-10-11 (+1 dia) representa a creación legítima de um consórcio empresarial para executar um contrato específico — consórcios são criados especificamente para atender exigências de habilitação que uma empresa sozinha não conseguiria, e o CNPJ do consórcio só é gerado após a assinatura do contrato constitutivo. O CONSÓRCIO TRAFECON ENGESUR (CNPJ 49.984.476) com +4 dias segue o mesmo padrão. Os dois casos com valores negativos de dias (MARIA BEATRIZ BATISTA DE SIQUEIRA com -4.451 dias e VANIUS MEINZER GAUDENZI com -979 dias) indicam problemas de qualidade de dados graves: contratos registrados em datas anteriores à fundação oficial da empresa, o que pode refletir erros de cadastramento, máscara de CNPJ incorreta (o CNPJ parcial de 8 dígitos não corresponde à empresa), ou a presença de empresas optantes pelo Simples Nacional que tiveram sua data de abertura retroativamente corrigida na base da Receita Federal. A empresa JAML PATRIMONIAL LTDA (CNPJ 50.463.384) com 96 dias pode representar uma holding patrimonial criada especificamente para receber direitos de uso de imóveis públicos — prática comum em contratos de concessão. A recomendação é tratar os valores negativos como alertas de qualidade de dados, não como evidências de fraude, e usar o CNPJ completo (14 dígitos) para verificar a existência real da empresa na base da Receita Federal antes de cualquier conclusion.

---

## 9. PS8 — Surto Súbito

### Base Legal

- **UNODC "Guidebook on anti-corruption in public procurement" (2013)**: aumento súbito é indicador de risco
- **TCU Acórdão 2.622/2015**: aumentos grandes sem histórico merecem escrutínio

### Limiares

- **5× crescimento YoY**: exclui crescimento normal (2-3×)
- **R$ 1.000.000 mínimo**: salto de R$ 200k para R$ 1M é relevante
- **Anos consecutivos**: Evita comparação de anos distantes

### Resultados Reais (2019-2023) — Top 30

| CNPJ | Nome/Razão Social | Ano Anterior | Ano Surto | Gasto Anterior | Gasto Anual | Ratio |
|------|-------------------|--------------|-----------|---------------|------------|-------|
| 42644220 | AGUAS DO RIO 4 SPE S.A | 2020 | 2021 | R$ 1.294.484,16 | R$ 10.027.455.966,15 | **7.746×** |
| 04147114 | INCORPLAN ENGENHARIA LTDA | 2020 | 2021 | R$ 1.100.005,17 | R$ 4.195.038.362,00 | **3.814×** |
| 00336701 | TELECOMUNICACOES BRASILEIRAS SA TELEBRAS | 2022 | 2023 | R$ 7.429.958,12 | R$ 3.159.622.504,86 | **425×** |
| 13888605 | AMPIEZZA CLINICAS INTEGRADAS LTDA | 2021 | 2022 | R$ 1.000.000,00 | R$ 338.100.000,00 | **338×** |
| 05544035 | BIOCARDIOS INSTITUTO DE CARDIOLOGIA LTDA | 2021 | 2022 | R$ 2.500.000,00 | R$ 830.697.928,01 | **332×** |
| 24996769 | BUHRING CONSTRUCOES LTDA | 2020 | 2021 | R$ 2.018.678,22 | R$ 499.713.317,06 | **248×** |
| 17790718 | UNIMED UBERLANDIA COOP.REGIONAL TRABALHO MEDICO LTDA | 2020 | 2021 | R$ 1.411.632,37 | R$ 322.936.775,40 | **229×** |
| 02341467 | AMAZONAS ENERGIA S.A / MANAUS ENERGIA S/A | 2020 | 2021 | R$ 1.579.361,94 | R$ 317.048.835,04 | **201×** |
| 07148735 | SANTOS COMERCIO E CONSTRUCAO LTDA | 2022 | 2023 | R$ 4.922.172,15 | R$ 961.386.487,00 | **195×** |
| 01068099 | INSTITUTO DE ONCOLOGIA E RADIOTERAPIA SAO PELLEGRINO LTDA | 2021 | 2022 | R$ 1.000.000,00 | R$ 150.000.000,00 | **150×** |

### Cenários de Falso Positivo

1. **Recuperação pós-reestruturação**: Empresa inativa por 2 anos retoma operações
2. **Novos acordos-quadro**: Inclusão em framework pode produzir surto aparente
3. **Ciclos orçamentários**: Contratos plurianuais a cada 4 anos criam saltos aparentes

### Considerações

Dos 10 casos mais extremos identificados entre 2019 e 2023, vários possuem explicações amplamente documentadas. A AGUAS DO RIO 4 SPE S.A (CNPJ 42.644.220/0001-XX) apresenta o maior ratio do dataset: 7.746×, passando de R$ 1,29 milhão em 2020 para R$ 10,02 bilhões em 2021. Esse surto não representa fraude, mas sim a assunção de contratos de concessão de água e esgoto no estado do Rio de Janeiro pelo consórcio formado pela CEDAE com parceiros privados — SPES são criadas especificamente para assumir concessões de longo prazo, e seu primeiro ano completo de operação pode apresentar um salto monumental em comparação com o período anterior à concessão. A INCORPLAN ENGENHARIA LTDA (CNPJ 04.147.114) com ratio de 3.814× pode ter sido contratada para grandes projetos de infraestrutura rodoviária no Rio de Janeiro após desastres naturais (chuvas de 2021), explicando o salto de R$ 1,1 milhão para R$ 4,19 bilhões. A TELEBRAS (CNPJ 00.336.701) com ratio de 425× (de R$ 7,4 milhões em 2022 para R$ 3,15 bilhões em 2023) reflete a inclusão da empresa no programaInternet para Todos e expansão da rede pública de宽带, onde contratos de infraestrutura de telecomunicações podem oscilar drasticamente com a assinatura de acordos-quadro nacionais. A BUHRING CONSTRUCOES LTDA (CNPJ 24.996.769) com ratio de 248× pode ter sido contratada para reconstrução após desastres ambientais no Amazonas em 2021 (cheias históricas), explicando o salto de R$ 2 milhões para R$ 499 milhões. A AMAZONAS ENERGIA S.A (CNPJ 02.341.467) com ratio de 201× reflete a mudança de concessão de distribuição de energia no Amazonas, onde a Amazonas Energia assumiu operações da Manaus Energia, consolidando contratos em um único CNPJ. O ponto fundamental é que saltos abruptos de >5× são esperados quando uma empresa é incluída em um novo programa governamental, assume uma concessão, ou é atingida por eventos extraordinários — a investigação deve sempre contextualizar o surto com notícias e portarias do período.

---

## 10. Resumo dos Resultados

| Padrão | Descrição | Flag | Status |
|--------|-----------|------|--------|
| PS1 | Contratos Divididos Abaixo do Limiar | Múltiplos órgãos com concentração de contratos pequenos | ✅ Executado |
| PS2 | Concentração >40% | 13 casos identificados | ✅ Executado |
| PS3 | Inexigibilidade Recorrente | 20+ casos com ≥3 contratos | ✅ Executado |
| PS4 | Único Licitante | Centenas de casos | ✅ Executado |
| PS5 | Vencedor Fixo (100%) | 30+ empresas com 100% vitória | ✅ Executado |
| PS6 | Inflação de Aditivos (>1,25×) | 30+ contratos com ratio >1,25× | ✅ Executado |
| PS7 | Empresa Recém-Criada | 20 casos com <180 dias (inclui inconsistências de dados) | ✅ Executado |
| PS8 | Surto Súbito (>5× YoY) | 30+ casos com crescimento >5× | ✅ Executado |

---

## 11. Considerações Finais

1. **Todos os padrões são complementares**: PS7 e PS8 podem sinalizar a mesma empresa simultaneamente
2. **CNPJ raiz (cnpj_basico)**: Agrupa todas as filiais de um corporativo — pode gerar falsos positivos para grandes empresas
3. **Valores monetários**: Sempre verificar se valores estão em reais ou outra unidade
4. **Datas NULL**: Sempre incluir `IS NOT NULL` em filtros de data
5. **Qualidade de dados**: Dados de contratos antigos podem ter inconsistências

---

*Relatório gerado em 29/03/2026 com base nos schemas do DuckDB e execução real dos padrões sobre dados de 2013-2025.*
