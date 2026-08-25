# Perguntas por tema — cada uma cruzando 3+ datasets

5 perguntas por cada um dos 43 temas de [`Temas.md`](Temas.md). Toda pergunta exige
**n ≥ 3 datasets** simultâneos (contagem entre parênteses). Datasets de referência
de outros temas, usados para completar o cruzamento, marcados com `*`. Chaves de
join: [`context/join_keys.md`](context/join_keys.md). Ao fim, 5 perguntas que
atravessam vários datasets de famílias distintas ao mesmo tempo.

---

## 01 · Desigualdade Racial e Estratificação Social

1. Nos municípios onde a lacuna de rendimento branco-negro na RAIS é maior, a taxa de óbitos por agressão no SIM por 100 mil habitantes é também maior quando normalizada pela população do Censo 2022? *(n=3: me_rais, ms_sim, ibge_censo_2022\*)*
2. Municípios de maioria negra (Censo) têm salário médio formal menor (RAIS) mesmo entre os de PIB per capita equivalente? *(n=3: ibge_censo_2022\*, me_rais, ibge_pib\*)*
3. A composição racial dos vínculos por CNAE na RAIS reflete a composição da população residente do Censo nos mesmos municípios — há setores onde a distância é maior? *(n=3: me_rais, ibge_censo_2022\*, ibge_pib\*)*
4. Entre UFs, a lacuna racial salarial da RAIS se correlaciona com a mortalidade diferencial por raça no SIM controlada pela estrutura etária do Censo? *(n=3: me_rais, ms_sim, ibge_censo_2022\*)*
5. Municípios que reduziram a lacuna racial de rendimento (RAIS 2012→2022) melhoraram também seus indicadores demográficos e de renda do Censo/PIB? *(n=3: me_rais, ibge_censo_2022\*, ibge_pib\*)*

## 02 · Educação, Mobilidade Social e Desigualdade

1. Municípios de maior IDEB nos anos finais têm candidatos ENEM com médias maiores, e essa relação sobrevive ao controle pelo nível socioeconômico das escolas (INSE)? *(n=3: inep_ideb, inep_enem, inep_indicador_nivel_socioeconomico)*
2. Escolas rurais (Censo Escolar) de municípios pobres (PIB) acumulam pior fluxo (IDEB) e pior média ENEM que as urbanas vizinhas? *(n=3: inep_censo_escolar\*, ibge_pib\*, inep_ideb, inep_enem)*
3. Quais municípios combinam IDEB baixo, alta participação no ENEM e alta renda municipal (PIB) — acesso sem aprendizado mesmo onde há recursos? *(n=3: inep_ideb, inep_enem, ibge_pib\*)*
4. O nível socioeconômico médio (INSE) das escolas explica mais a variação do IDEB ou a do ENEM dentro de cada UF? *(n=3: inep_indicador_nivel_socioeconomico, inep_ideb, inep_enem)*
5. Municípios que ganharam população jovem entre os censos (Censo 2022 vs 2010) ampliaram matrícula e mantiveram IDEB? *(n=3: ibge_censo_2022\*, inep_ideb, inep_censo_escolar\*)*

## 03 · Saúde, Acesso a Serviços e Determinantes Sociais

1. Municípios com mais beneficiários de programas sociais (CGU) têm maior proporção de cesáreas no SINASC mesmo com oferta hospitalar semelhante (CNES)? *(n=3: cgu_beneficios_cidadao, ms_sinasc, ms_cnes)*
2. A razão óbitos infantis (SIM) / nascidos vivos (SINASC) melhora conforme aumentam leitos e equipes do CNES por habitante? *(n=3: ms_sim, ms_sinasc, ms_cnes)*
3. Os municípios com excesso de mortalidade infantil (SIM×SINASC) concentram-se nas faixas mais baixas de PIB per capita e de cobertura social (CGU)? *(n=3: ms_sim, ms_sinasc, ibge_pib\*, cgu_beneficios_cidadao)*
4. Onde há muitos nascidos vivos (SINASC) mas poucos estabelecimentos com obstetra (CNES), a mortalidade materna (SIM) excede a regional? *(n=3: ms_sinasc, ms_cnes, ms_sim)*
5. Benefícios sociais (CGU) chegam aos municípios cujo perfil de nascidos vivos (SINASC) indica maior vulnerabilidade — escolaridade materna e consultas pré-natais? *(n=3: cgu_beneficios_cidadao, ms_sinasc, ibge_censo_2022\*)*

## 04 · Mercado de Trabalho, Informalidade e Estratificação

1. Setores com maior rotatividade no CAGED pagam abaixo da mediana da RAIS no mesmo município, e isso coincide com piores indicadores de saúde mental no SIM? *(n=3: me_caged, me_rais, ms_sim)*
2. Municípios que mais perderam vínculos no CAGED em 2020 recuperaram emprego formal na RAIS até 2022 proporcionalmente à sua renda (PIB)? *(n=3: me_caged, me_rais, ibge_pib\*)*
3. CBOs dominadas por admissões precárias no CAGED correspondem às ocupações de menor rendimento médio na RAIS por faixa de escolaridade? *(n=3: me_caged, me_rais, ibge_censo_2022\*)*
4. Municípios dependentes de um único CNAE dominante (CAGED/RAIS) têm pior perfil socioeconômico no Censo 2022 que diversificados com mesma população? *(n=3: me_caged, me_rais, ibge_censo_2022\*)*
5. Onde o emprego formal cresceu (CAGED) sem crescer a população (Censo), o rendimento médio local subiu na RAIS e no PIB municipal? *(n=3: me_caged, ibge_censo_2022\*, me_rais, ibge_pib\*)*

## 05 · Política, Representação e Comportamento Eleitoral

1. Deputados eleitos com maior patrimônio declarado no TSE autorizam mais proposições na Câmara, e representam municípios de maior PIB per capita? *(n=3: tse_eleicoes, camara_dados_abertos, ibge_pib\*)*
2. Senadores eleitos (TSE) autorizam no Senado proposições alinhadas ao perfil econômico dos estados que os elegeram (PIB setorial IBGE)? *(n=3: senado_dadosabertos\*, tse_eleicoes, ibge_pib\*)*
3. Candidatos empresários no TSE são eleitos mais vezes que liberais com igual gasto, e suas empresas aparecem depois em contratos públicos (CGU)? *(n=3: tse_eleicoes, me_cnpj\*, cgu_licitacao_contrato\*)*
4. A fragmentação partidária municipal no TSE acompanha a federal medida nas votações da Câmara, ou diverge por região? *(n=3: tse_eleicoes, camara_dados_abertos, ibge_censo_2022\*)*
5. Municípios onde o vencedor gastou mais por voto (TSE) recebem mais transferências voluntárias depois da eleição? *(n=3: tse_eleicoes, transferegov\*, ibge_pib\*)*

## 06 · Crime, Violência e Segurança Pública

1. Estados com maior encarceramento relativo (SISDEPEN) reduziram homicídios (SIM) entre 2015 e 2023, controlando pelo perfil socioeconômico municipal (Censo)? *(n=3: mjsp_sisdepen, ms_sim, ibge_censo_2022\*)*
2. No RJ, a queda dos crimes letais do ISP-RJ espelha a dos óbitos por agressão no SIM, município a município, ou divergem nos grandes centros? *(n=3: rj_isp_estatisticas_seguranca, ms_sim, ibge_censo_2022\*)*
3. Municípios com economia concentrada em poucos CNAE (RAIS) têm taxas de homicídio (SIM) acima dos diversificados de mesma população? *(n=3: me_rais\*, ms_sim, ibge_censo_2022\*)*
4. A taxa de mortes por intervenção policial (SIM) por UF relaciona-se ao tamanho relativo do sistema prisional (SISDEPEN) e à renda local (PIB)? *(n=3: ms_sim, mjsp_sisdepen, ibge_pib\*)*
5. Municípios de fronteira/portos identificados pelo CNAE de transporte (RAIS) concentram homicídios acima do esperado pelo Censo e pelo ISP? *(n=3: me_rais\*, ms_sim, rj_isp_estatisticas_seguranca)*

## 07 · Economia, Crédito e Desenvolvimento Regional

1. Municípios que mais captam crédito rural (SICOR) são os de maior PIB agropecuário (IBGE) e maior estoque pecuário (PPM), ou há descolamento? *(n=3: bcb_sicor, ibge_pib, ibge_ppm\*)*
2. A densidade bancária (ESTBAN) explica parte da diferença de PIB per capita entre municípios vizinhos da mesma UF após controlar pela população do Censo? *(n=3: bcb_estban, ibge_pib, ibge_censo_2022\*)*
3. Crédito rural por CPF/CNPJ tomador (SICOR) concentra-se nos imóveis gigantes do SICAR dos municípios de maior PIB agro? *(n=3: bcb_sicor, sfb_sicar\*, ibge_pib)*
4. Municípios que perderam agências (ESTBAN) tiveram crescimento de PIB municipal inferior aos que as mantiveram, mesma UF e porte populacional? *(n=3: bcb_estban, ibge_pib, ibge_censo_2022\*)*
5. A concentração do crédito agrícola (SICOR) nos maiores tomadores varia com o uso do solo (MapBiomas) e a estrutura fundiária (SICAR) de cada região? *(n=3: bcb_sicor, mapbiomas_estatisticas\*, sfb_sicar\*)*

## 08 · Políticas Públicas, Transferências e Proteção Social

1. Municípios com mais beneficiários (CGU) gastam proporcionalmente mais em assistência social no SICONFI e têm maior vulnerabilidade no Censo? *(n=3: cgu_beneficios_cidadao, me_siconfi, ibge_censo_2022\*)*
2. A cobertura de benefícios (CGU) supera a pobreza estimada pelo Censo justamente nos municípios de maior repasse estadual/federal no SICONFI? *(n=3: cgu_beneficios_cidadao, ibge_censo_2022\*, me_siconfi)*
3. Municípios com arrecadação própria forte (SICONFI) dependem menos de benefícios federais per capita, mesmo com igual renda média (Censo)? *(n=3: me_siconfi, cgu_beneficios_cidadao, ibge_censo_2022\*)*
4. As despesas de saúde e educação (SICONFI) dos municípios com mais beneficiários diferem em resultado — mortalidade evitável (SIM) e analfabetismo (Censo)? *(n=3: me_siconfi, ms_sim, ibge_censo_2022\*)*
5. Onde o número de beneficiários (CGU) excede a estimativa de pobreza do Censo, o orçamento municipal (SICONFI) compensa ou duplica o repasse federal (SIOP)? *(n=3: cgu_beneficios_cidadao, ibge_censo_2022\*, siop_orcamento\*)*

## 09 · Gênero, Família e Dinâmicas Demográficas

1. Municípios com maior feminização do emprego formal (RAIS) têm menos violência doméstica notificada no SINAN, controlando pela população feminina do Censo? *(n=3: me_rais, ms_sinan\*, ibge_censo_2022\*)*
2. A proporção de cesáreas no SINASC por escolaridade materna varia com a oferta de leitos obstétricos (CNES) do município? *(n=3: ms_sinasc, ms_cnes\*, ibge_censo_2022\*)*
3. Mulheres reingressam no emprego formal (CAGED) mais devagar que homens nas ocupações de maior rendimento (RAIS), e essa diferença é maior em quais UFs? *(n=3: me_caged, me_rais, ibge_censo_2022\*)*
4. Onde a mortalidade materna e obstétrica (SIM) excede a nacional, quantos leitos e equipes de obstetrícia existem (CNES) e qual a renda municipal (PIB)? *(n=3: ms_sim, ms_cnes\*, ibge_pib\*)*
5. Municípios com mais mulheres chefes de família (Censo) têm rendimento médio formal feminino (RAIS) acima ou abaixo da masculina local? *(n=3: ibge_censo_2022\*, me_rais, ibge_pib\*)*

## 10 · Meio Ambiente, Desenvolvimento e Sustentabilidade

1. Municípios líderes de desmatamento (PRODES) têm maior PIB agropecuário (IBGE) e maior emissão agropecuária no SEEG, na mesma ordem? *(n=3: inpe_prodes, ibge_pib, seeg_emissoes)*
2. Imóveis com pendências no SICAR concentram-se nos municípios recordistas de desmatamento (PRODES) e de maior rebanho (PPM)? *(n=3: sfb_sicar, inpe_prodes, ibge_ppm\*)*
3. As emissões per capita do SEEG correlacionam com perda de vegetação (MapBiomas) e desmatamento (PRODES) nos mesmos municípios? *(n=3: seeg_emissoes, mapbiomas_estatisticas\*, inpe_prodes)*
4. Municípios com CAR validado (SICAR) desmataram menos (PRODES) que os pendentes, mesmo com produção pecuária igual (PPM)? *(n=3: sfb_sicar, inpe_prodes, ibge_ppm\*)*
5. Onde a renda agro (PIB) cresceu junto com o desmatamento (PRODES), as emissões (SEEG) cresceram na mesma proporção ou mais? *(n=3: ibge_pib, inpe_prodes, seeg_emissoes)*

## 11 · Infraestrutura, Serviços e Qualidade de Vida

1. Municípios com pior índice de conectividade Anatel têm também menor cobertura de água/esgoto (SNIS) e menor gasto público municipal em saneamento (SICONFI)? *(n=3: anatel_indice_brasileiro_conectividade, mdr_snis, me_siconfi\*)*
2. Investimento municipal em saneamento (SICONFI) converte-se em melhores indicadores SNIS de coleta de esgoto, e a defasagem é maior no Norte? *(n=3: me_siconfi\*, mdr_snis, ibge_censo_2022\*)*
3. A defasagem digital (Anatel) explica parte da diferença de IDEB entre municípios do Norte e do Sul com renda (PIB) parecida? *(n=3: anatel_indice_brasileiro_conectividade, inep_ideb\*, ibge_pib\*)*
4. Municípios universalizados em água (SNIS) mas deficientes em esgoto têm perfil econômico (PIB/CNAE RAIS) distinto dos universalizados em ambos? *(n=3: mdr_snis, ibge_pib\*, me_rais\*)*
5. Melhor conectividade (Anatel) associa-se a mais empresas formais per capita (RAIS/CNPJ) nos municípios de interior? *(n=3: anatel_indice_brasileiro_conectividade, me_rais\*, me_cnpj\*)*

## 12 · Interseccionalidade e Desigualdades Complexas

1. Entre mulheres negras (RAIS × Censo), quais CNAE concentram vínculos e o rendimento nelas compara ao de homens brancos na mesma ocupação e município? *(n=3: me_rais, ibge_censo_2022\*, ibge_pib\*)*
2. Mães pretas e pardas (SINASC) dão à luz em municípios com menos leitos obstétricos per capita (CNES) e menor renda (PIB) que mães brancas? *(n=3: ms_sinasc, ms_cnes\*, ibge_pib\*)*
3. A dupla desvantagem raça×sexo no rendimento da RAIS é maior nos setores de maior rotatividade do CAGED? *(n=3: me_rais, me_caged, ibge_censo_2022\*)*
4. Mulheres chefes de família (Censo) concentram-se nos municípios de menor rendimento formal (RAIS) e maior mortalidade feminina precoce (SIM)? *(n=3: ibge_censo_2022\*, me_rais, ms_sim)*
5. A interseção raça × sexo × setor (RAIS) produz a maior lacuna salarial em quais combinações de UF e CNAE, e esses territórios são os mais pobres (PIB)? *(n=3: me_rais, ibge_censo_2022\*, ibge_pib\*)*

## 13 · Migração, Urbanização e Transformações Espaciais

1. Municípios que importam vínculos formais (CAGED origem/destino) ganharam população entre censos (2010→2022) acima da média de sua UF? *(n=3: me_caged, ibge_censo_2022\*, ibge_munic\*)*
2. Os polos de atração de trabalhadores (CAGED) coincidem com os municípios de maior PIB per capita ou com os de boom da construção civil (CNAE)? *(n=3: me_caged, ibge_pib\*, me_rais\*)*
3. Fluxos de vínculos entre municípios (CAGED) seguem a hierarquia urbana capturada nas malhas do geobr/regiões do IBGE? *(n=3: me_caged, geobr_mapas\*, ibge_munic\*)*
4. Municípios que exportaram trabalhadores (CAGED) envelheceram mais rápido no Censo 2022 que os receptores? *(n=3: me_caged, ibge_censo_2022\*, ibge_pib\*)*
5. A migração interna de vínculos (CAGED 2019–2022) antecipou mudanças de domicílio entre os censos, município a município? *(n=3: me_caged, ibge_censo_2022\*, ibge_munic\*)*

## 14 · Consumo, Preços e Estratificação de Classe

1. A dispersão de preços da gasolina entre postos (ANP) é maior nos municípios pobres (Censo) e de menos postos concorrentes (CNPJ/RAIS)? *(n=3: anp_precos_combustiveis, ibge_censo_2022\*, me_cnpj\*)*
2. Regiões com IPCA de alimentos mais alto também têm combustível (ANP) e renda (POF) com comportamento distinto das demais regiões? *(n=3: ibge_ipca, anp_precos_combustiveis, ibge_pof\*)*
3. Itens de maior peso no orçamento das famílias pobres (POF) foram os que mais subiram no IPCA, e isso varia por região? *(n=3: ibge_pof\*, ibge_ipca, ibge_censo_2022\*)*
4. Municípios próximos de distribuidoras de combustíveis (CNAE na RAIS) praticam preços ANP menores, e a diferença escala com a renda local (PIB)? *(n=3: anp_precos_combustiveis, me_rais\*, ibge_pib\*)*
5. O consumo residencial de combustíveis por município (ANP vendas) escala com renda do Censo e frota implícita, ou há regiões fora da curva? *(n=3: anp_combustiveis, ibge_censo_2022\*, ibge_pib\*)*

## 15 · Poder, Elite e Reprodução Social

1. Deputados eleitos com maior patrimônio no TSE concentram autoria na Câmara em quais temas, e vêm de municípios de maior renda (Censo)? *(n=3: tse_eleicoes, camara_dados_abertos, ibge_censo_2022\*)*
2. Candidatos empresários (TSE) são eleitos mais vezes que liberais com gasto igual, e suas empresas (CNPJ) vencem mais licitações depois (CGU)? *(n=3: tse_eleicoes, me_cnpj\*, cgu_licitacao_contrato\*)*
3. Dinastias políticas (recorrência de sobrenomes no TSE) controlam municípios de maior ou de menor PIB per capita? *(n=3: tse_eleicoes, ibge_pib\*, camara_dados_abertos\*)*
4. Empresas de doadores recorrentes (TSE) recebem mais pagamentos via cartão corporativo público (CGU) que equivalentes sem doação? *(n=3: tse_eleicoes, me_cnpj\*, cgu_cartao_pagamento\*)*
5. A razão patrimônio do eleito (TSE) / renda média do eleitorado (Censo) é maior em quais UFs, e essas UFs têm mais emendas direcionadas (CGU)? *(n=3: tse_eleicoes, ibge_censo_2022\*, cgu_emendas_parlamentares\*)*

## 16 · Economia Política e Desenvolvimento

1. UFs que contribuem com arrecadação (RF) acima do peso no PIB nacional subsidiam as demais? *(n=3: rf_arrecadacao, ibge_pib, ibge_censo_2022\*)*
2. Municípios de economia dominada por um único setor (CNPJ/CNAE) têm arrecadação per capita (RF) mais volátil entre anos? *(n=3: rf_arrecadacao\*, me_cnpj, ibge_pib\*)*
3. Onde a arrecadação (RF) depende de tributos setoriais (IEF/II), a produção agro ou extrativa (PPM/PIB) domina o município? *(n=3: rf_arrecadacao\*, ibge_ppm\*, ibge_pib)*
4. Estados que mais arrecadam (RF) são os mesmos que repassam mais transferências voluntárias ou recebem mais (SIOP)? *(n=3: rf_arrecadacao\*, siop_orcamento, transferegov\*)*
5. Municípios com mais empresas de grande porte (CNPJ) têm arrecadação per capita (RF) proporcionalmente maior que a média da UF? *(n=3: me_cnpj, rf_arrecadacao\*, ibge_censo_2022\*)*

## 17 · Agropecuária, Estrutura Fundiária e Agronegócio

1. Os municípios de maior estoque bovino (PPM) concentram crédito rural (SICOR) e área cadastrada gigante (SICAR) na mesma proporção? *(n=3: ibge_ppm, bcb_sicor, sfb_sicar)*
2. Imóveis gigantes no SICAR captam quanto do crédito por tomador (SICOR), e produzem proporcionalmente mais no PPM? *(n=3: sfb_sicar, bcb_sicor, ibge_ppm)*
3. A cadeia TRASE confirma que o desmatamento municipal (PRODES) está ligado à expansão pecuária medida pelo PPM e financiada pelo SICOR? *(n=3: trase_supply_chain, inpe_prodes\*, ibge_ppm)*
4. Municípios com CAR pendente (SICAR) produzem (PPM) tanto quanto os validados, mas recebem menos crédito formal (SICOR)? *(n=3: sfb_sicar, ibge_ppm, bcb_sicor)*
5. Quem recebe crédito (SICOR) gera mais PIB agro local (IBGE) por hectare cadastrado (SICAR) — escala ou produtividade? *(n=3: bcb_sicor, ibge_pib, sfb_sicar)*

## 18 · Comércio Exterior, Integração Global e Cadeias de Valor

1. Municípios exportadores de manufaturados (COMEX) geram mais emprego industrial formal (RAIS) que exportadores de primários, mesmo com valor exportado igual? *(n=3: me_comex_stat, me_rais\*, ibge_pib\*)*
2. As exportações para a China (COMEX por país) saem exatamente dos municípios primários/agro (NCM × PIB agro) identificados pelo IBGE? *(n=3: me_comex_stat, ibge_pib\*, sfb_sicar\*)*
3. Municípios importadores de bens intermediários (COMEX) crescem mais em vínculos industriais (RAIS) nos anos seguintes que os não importadores vizinhos? *(n=3: me_comex_stat, me_rais\*, geobr_mapas\*)*
4. A concentração exportadora em poucos NCM-Sh por município acompanha a concentração fundiária medida pelo SICAR? *(n=3: me_comex_stat, sfb_sicar\*, ibge_ppm\*)*
5. O valor exportado per capita (COMEX ÷ Censo) explica quanto da diferença de PIB per capita dentro de cada UF? *(n=3: me_comex_stat, ibge_censo_2022\*, ibge_pib\*)*

## 19 · Mercado Financeiro, Fundos e Estrutura de Capital

1. Municípios com melhor conectividade Anatel atraem mais operações bancárias (ESTBAN) e bolsistas CNPq simultaneamente? *(n=3: anatel_indice_brasileiro_conectividade, bcb_estban\*, cnpq_bolsas\*)*
2. Onde o crédito rural (SICOR) cresce acima do PIB agro (IBGE), há endividamento, e isso coincide com queda de agências (ESTBAN)? *(n=3: bcb_sicor, ibge_pib, bcb_estban\*)*
3. Bolsistas CNPq concentram-se nas capitais/regiões de maior densidade financeira (ESTBAN) e renda (PIB)? *(n=3: cnpq_bolsas, bcb_estban\*, ibge_pib\*)*
4. Municípios atendidos só por cooperativas de crédito têm crédito rural (SICOR) mais barato que os servidos por grandes bancos (ESTBAN)? *(n=3: bcb_estban\*, bcb_sicor, ibge_ppm\*)*
5. A presença bancária (ESTBAN) antecede ou segue o crescimento do PIB municipal, controlado pela população do Censo? *(n=3: bcb_estban\*, ibge_pib, ibge_censo_2022\*)*

## 20 · Ciência, Tecnologia, Bolsas e Produção Acadêmica

1. Municípios formadores de bolsistas CNPq produzem candidatos ENEM com notas maiores mesmo controlando pela renda municipal (PIB)? *(n=3: cnpq_bolsas, inep_enem, ibge_pib\*)*
2. As bolsas CNPq distribuem-se proporcionalmente à população (Censo) das regiões das IES, ou reforçam a concentração do Sudeste? *(n=3: cnpq_bolsas, ibge_censo_2022\*, ibge_pib\*)*
3. Escolas de alta nota no ENEM alimentam depois mais bolsistas de iniciação científica, município a município? *(n=3: inep_enem, cnpq_bolsas, inep_ideb\*)*
4. Investimento federal em ciência (bolsas) vai para estados cuja participação no PIB é menor — correção ou reforço da desigualdade regional? *(n=3: cnpq_bolsas, ibge_pib\*, ibge_censo_2022\*)*
5. Onde não há bolsas nem IES (CNPQ), as notas ENEM locais diferem sistematicamente dos municípios vizinhos com campus, mesma renda? *(n=3: cnpq_bolsas, inep_enem, ibge_pib\*)*

## 21 · Corrupção, Improbidade e Controle Público

1. Fornecedores recorrentes via cartão corporativo (CGU) aparecem também nas licitações dispensadas e pagam menos imposto proporcional (RF)? *(n=3: cgu_cartao_pagamento, cgu_licitacao_contrato, rf_arrecadacao\*)*
2. Emendas parlamentares (CGU) executadas por certos municípios terminam contratando sempre os mesmos CNPJ — quais perfis esses fornecedores têm? *(n=3: cgu_emendas_parlamentares, cgu_licitacao_contrato, me_cnpj\*)*
3. Empresas licitantes com padrões anormais (CGU) pertencem a setores (CNAE/CNPJ) que proporcionalmente menos arrecadam na RF? *(n=3: cgu_licitacao_contrato, me_cnpj\*, rf_arrecadacao\*)*
4. Municípios que mais recebem emendas (CGU) executam o equivalente no orçamento (SICONFI/SIOP), ou há retenção em nível estadual? *(n=3: cgu_emendas_parlamentares, siop_orcamento\*, me_siconfi\*)*
5. Itens idênticos comprados via cartão (CGU) custam mais que os comprados por licitação no mesmo órgão e período? *(n=3: cgu_cartao_pagamento, cgu_licitacao_contrato, siop_orcamento\*)*

## 22 · Clima, Queimadas e Variação de Temperatura

1. Municípios recordistas de focos de calor (QUEIMADAS) perderam mais vegetação (PRODES) e emitem mais no SEEG no mesmo período? *(n=3: inpe_queimadas\*, inpe_prodes, seeg_emissoes)*
2. Estações do INMET registram tendência de temperatura mais alta nos municípios que mais desmataram (PRODES) vs conservados vizinhos? *(n=3: inmet_bdmep\*, inpe_prodes, geobr_mapas\*)*
3. Imóveis com sobreposição irregular no SICAR concentram-se nos municípios de pico de queimadas e emissões SEEG? *(n=3: sfb_sicar, inpe_queimadas\*, seeg_emissoes)*
4. A mortalidade respiratória (SIM) sobe nos meses/municípios de pico de fogo (QUEIMADAS), controlada pela população do Censo? *(n=3: inpe_queimadas\*, ms_sim\*, ibge_censo_2022\*)*
5. As emissões SEEG municipais confirmam que o fogo está associado à conversão agropecuária (PIB agro) e não a eventos naturais? *(n=3: seeg_emissoes, inpe_queimadas\*, ibge_pib)*

## 23 · Epidemiologia, Doenças Infecciosas e Vigilância

1. Municípios com muitas notificações de dengue no SINAN têm internações correspondentes no SIH, ou subnotificam casos graves dado sua oferta hospitalar (CNES)? *(n=3: ms_sinan\*, ms_sih\*, ms_cnes)*
2. A letalidade das doenças infecciosas notificadas (SINAN×SIM) é menor onde há mais estabelecimentos do CNES per capita? *(n=3: ms_sinan\*, ms_sim, ms_cnes)*
3. Condições socioeconômicas (Censo) explicam quanto do gradiente geográfico das notificações (SINAN) e óbitos (SIM) por doença infecciosa? *(n=3: ms_sinan\*, ibge_censo_2022\*, ms_sim)*
4. Municípios de baixa cobertura vacinal (SIPNI) registraram depois excesso de óbitos infecciosos no SIM, controlando pela estrutura de saúde (CNES)? *(n=3: ms_sipni_microdados\*, ms_sim, ms_cnes\*)*
5. Nascidos vivos de mães sem pré-natal adequado (SINASC) concentram-se nos municípios de pior vigilância (menos notificações SINAN per capita e menos CNES)? *(n=3: ms_sinasc, ms_sinan\*, ms_cnes)*

## 24 · Assistência Ambulatorial, Hospitalar e Procedimentos do SUS

1. Quais municípios exportam pacientes pelo SIH para hospitais de outros municípios, e isso correlaciona com a falta de leitos locais no CNES e com a renda municipal? *(n=3: ms_sih, ms_cnes, ibge_pib\*)*
2. Procedimentos ambulatoriais da SIA concentram-se onde o CNES registra mais equipamentos especializados, e o IEPS confirma a desigualdade de acesso? *(n=3: ms_sia, ms_cnes, ieps_saude)*
3. Internações evitáveis no SIH caem onde há mais atenção básica no CNES, mesmo entre municípios de igual vulnerabilidade (Censo)? *(n=3: ms_sih, ms_cnes, ibge_censo_2022\*)*
4. O valor pago por AIH (SIH) varia entre hospitais do mesmo porte (CNES) pelos mesmos procedimentos, por região? *(n=3: ms_sih, ms_cnes, ibge_pib\*)*
5. Municípios com alta mortalidade evitável no SIM são os mesmos que mais dependem de atendimento fora do município (SIH) e têm menos CNES? *(n=3: ms_sim, ms_sih, ms_cnes)*

## 25 · Orçamento Federal, Emendas e Execução Orçamentária

1. As emendas parlamentares (CGU) chegam aos municípios declarados via Transferegov, ou ficam retidas em nível estadual/federal conforme o SIOP? *(n=3: cgu_emendas_parlamentares, transferegov\*, siop_orcamento\*)*
2. Crédito rural subsidiado (SICOR) custa quanto ao orçamento (SIOP) comparado aos programas sociais, e quem captura os dois simultaneamente? *(n=3: bcb_sicor, siop_orcamento\*, cgu_beneficios_cidadao\*)*
3. Emendas individuais vs de bancada (CGU) diferem em velocidade de execução e taxa de bloqueio registrada no SIOP/Transferegov? *(n=3: cgu_emendas_parlamentares, siop_orcamento\*, transferegov\*)*
4. Municípios que mais receberam emendas (CGU) mudaram o voto (TSE) em direção aos partidos proponentes na eleição seguinte? *(n=3: cgu_emendas_parlamentares, tse_eleicoes\*, ibge_censo_2022\*)*
5. A arrecadação crescente (RF) virou mais emendas parlamentares (CGU) ou mais juros no orçamento (SIOP) ao longo dos anos? *(n=3: rf_arrecadacao\*, siop_orcamento, cgu_emendas_parlamentares)*

## 26 · Servidores Públicos, Gestão de Pessoal e Elites do Estado

1. Servidores comissionados (CGU) residem proporcionalmente nos municípios-sede ou espalham-se conforme a renda local (PIB/Censo)? *(n=3: cgu_servidores_executivo_federal, ibge_censo_2022\*, ibge_pib\*)*
2. A remuneração média do servidor federal por cargo (CGU) compara à média RAIS das ocupações equivalentes na mesma UF? *(n=3: cgu_servidores_executivo_federal, me_rais, ibge_pib\*)*
3. Municípios-sede de órgãos federais elevam o rendimento médio local (RAIS) acima dos vizinhos sem presença federal, controlada pela população (Censo)? *(n=3: cgu_servidores_executivo_federal\*, me_rais, ibge_censo_2022\*)*
4. O envelhecimento dos quadros (CGU) projeta quantas aposentadorias por órgão/UF e quanto isso pesa no orçamento (SIOP) até 2035? *(n=3: cgu_servidores_executivo_federal, siop_orcamento\*, ibge_censo_2022\*)*
5. Onde servidores per capita (CGU ÷ Censo) excedem muito o padrão nacional, a economia local depende do setor público (RAIS/CNAE público)? *(n=3: cgu_servidores_executivo_federal, ibge_censo_2022\*, me_rais)*

## 27 · Pesquisas de Opinião, Percepção Pública e Comportamento Político

1. As intenções de voto do Poder360 acertaram o resultado TSE município a município, e o erro foi maior nas regiões de perfil PNADC mais informal? *(n=3: poder360_pesquisas, tse_eleicoes, ibge_pnadc\*)*
2. Estados com pior autodeclaração de saúde (PNS) votam diferente dos mais saudáveis, controlando pela renda municipal (PIB)? *(n=3: ms_pns, tse_eleicoes, ibge_pib\*)*
3. O perfil socioeconômico regional da PNADC prediz o vencedor TSE melhor que as pesquisas nacionais agregadas? *(n=3: ibge_pnadc, tse_eleicoes, ibge_censo_2022\*)*
4. Regiões de maior informalidade (PNADC) tiveram maior oscilação de voto entre eleições (TSE), punindo o incumbente? *(n=3: ibge_pnadc, tse_eleicoes, ibge_censo_2022\*)*
5. Onde a percepção de saúde (PNS) divergiu mais das condições objetivas (SIM/SISVAN), o voto divergiu também da média nacional? *(n=3: ms_pns, ms_sim\*, tse_eleicoes)*

## 28 · Violência Escolar, Segurança Educacional e Ambiente de Aprendizagem

1. Notificações de violência contra adolescentes no SINAN se concentram nos municípios cujas escolas (Censo Escolar) têm pior infraestrutura e menor INSE? *(n=3: ms_sinan, inep_censo_escolar, inep_indicador_nivel_socioeconomico\*)*
2. Escolas de menor nível socioeconômico (INSE) ficam nos municípios de maior letalidade juvenil (SIM), dentro da mesma região? *(n=3: inep_indicador_nivel_socioeconomico\*, ms_sim\*, ibge_censo_2022\*)*
3. A queda de participação entre SAEB e ENEM é maior nos municípios de maior letalidade juvenil (SIM) e criminalidade (ISP-RJ)? *(n=3: inep_saeb, inep_enem, ms_sim\*)*
4. Casos de violência escolar notificados no SINAN coincidem geograficamente com registros policiais (ISP-RJ) e com escolas de maior vulnerabilidade (Censo Escolar)? *(n=3: ms_sinan, rj_isp_estatisticas_seguranca, inep_censo_escolar)*
5. Municípios com pior SAEB têm mais automutilação notificada no SINAN entre jovens, controlada pela população adolescente do Censo? *(n=3: inep_saeb, ms_sinan, ibge_censo_2022\*)*

## 29 · Dados Eleitorais Detalhados, Judicialização e STF

1. Candidatos reeleitos (TSE 2018→2022) repetiram o mapa municipal de votos, e esses mapas seguem a divisão de renda (Censo/PIB)? *(n=3: tse_eleicoes, ibge_censo_2022\*, ibge_pib\*)*
2. O patrimônio médio dos eleitos (TSE) cresceu entre eleições, e os maiores saltos vieram de partidos com mais bancada na Câmara? *(n=3: tse_eleicoes, camara_dados_abertos\*, senado_dadosabertos\*)*
3. Municípios com eleição mais disputada (TSE margem estreita) receberam mais emendas parlamentares (CGU) depois? *(n=3: tse_eleicoes, cgu_emendas_parlamentares\*, ibge_censo_2022\*)*
4. A fragmentação partidária municipal (TSE) acompanha a federal (votações Câmara) ou segue lógica própria por região? *(n=3: tse_eleicoes, camara_dados_abertos\*, geobr_mapas\*)*
5. A participação eleitoral (TSE ÷ população Censo) caiu mais nos municípios jovens, pobres e do interior? *(n=3: tse_eleicoes, ibge_censo_2022\*, ibge_pib\*)*

## 30 · Estrutura Produtiva, Empresas, MPEs e Dinâmica Competitiva

1. Os setores dominados por poucas gigantes (capital social no CNPJ) pagam salários maiores na RAIS mas empregam menos proporcionalmente à população (Censo)? *(n=3: me_cnpj, me_rais\*, ibge_censo_2022\*)*
2. Municípios com mais microempresas per capita (CNPJ) crescem mais em vínculos formais (RAIS) que os de estrutura concentrada? *(n=3: me_cnpj, me_rais\*, ibge_pib\*)*
3. A taxa de abertura vs fechamento de empresas (CNPJ) antecipa ciclos visíveis no PIB municipal um ano depois? *(n=3: me_cnpj, ibge_pib\*, me_comex_stat\*)*
4. Empresas com sócios estrangeiros (CNPJ) instalam-se em quais municípios/CNAE e geram quantos empregos formais (RAIS) comparados às nacionais do mesmo setor? *(n=3: me_cnpj, me_rais\*, me_comex_stat\*)*
5. Setores de alta concentração (CNPJ) arrecadam proporcionalmente mais imposto (RF) por trabalhador formal (RAIS) que os competitivos? *(n=3: me_cnpj, rf_arrecadacao\*, me_rais\*)*

## 31 · Desenvolvimento Humano, Vulnerabilidade Social e Índices Compostos

1. Municípios de maior vulnerabilidade social no Censo 2022 recebem benefícios (CGU) proporcionais à necessidade medida também pelo IPEA-AVS? *(n=3: ibge_censo_2022\*, cgu_beneficios_cidadao, ipea_avs)*
2. Áreas de risco ambiental do IPEA-AVS sobrepõem-se aos setores censitários mais vulneráveis do Censo nos grandes municípios? *(n=3: ipea_avs, ibge_censo_2022\*, geobr_mapas\*)*
3. Onde beneficiários (CGU) são muitos mas a vulnerabilidade (Censo/AVS) é baixa — sobreposição de programas ou erro cadastral? *(n=3: cgu_beneficios_cidadao, ibge_censo_2022\*, ipea_avs)*
4. A vulnerabilidade social (Censo + AVS) explica quanto da variação da mortalidade infantil implícita no par SIM×SINASC por município? *(n=3: ibge_censo_2022\*, ms_sim, ms_sinasc)*
5. Municípios com pior indicador composto (AVS/IPEA) melhoraram entre ondas, e o ganho acompanhou crescimento do PIB ou dos repasses sociais (CGU)? *(n=3: ipea_avs, ibge_pib\*, cgu_beneficios_cidadao\*)*

## 32 · Conectividade, Educação Digital e Telecomunicações

1. Municípios com pior índice Anatel têm escolas com pior ENEM mesmo dentro da mesma UF e faixa de renda (PIB)? *(n=3: anatel_indice_brasileiro_conectividade, inep_enem, ibge_pib\*)*
2. As velocidades medidas pelo SIMET nas escolas confirmam o índice agregado da Anatel por município, ou há divergências sistemáticas por região? *(n=3: simet_educacao_conectada, anatel_indice_brasileiro_conectividade, inep_censo_escolar\*)*
3. Provedores regionais pequenos (banda larga Anatel) cobrem os municípios abandonados pelas grandes operadoras — e qual o perfil econômico desses? *(n=3: anatel_banda_larga_fixa, anatel_indice_brasileiro_conectividade, ibge_pib\*)*
4. Escolas rurais (Censo Escolar) têm conectividade medida (SIMET) sistematicamente inferior às urbanas no mesmo município? *(n=3: simet_educacao_conectada, inep_censo_escolar\*, ibge_censo_2022\*)*
5. Melhorias no índice Anatel precedem ganhos no IDEB municipal, ou apenas coincidem com ciclos econômicos (PIB)? *(n=3: anatel_indice_brasileiro_conectividade, inep_ideb\*, ibge_pib\*)*

## 33 · Dados Internacionais Comparativos e Rankings Globais

1. Se cada UF fosse um país, onde ranquearia em homicídios (FBSP) considerando sua população equivalente (Censo)? *(n=3: fbsp_absp, ibge_censo_2022\*, geobr_mapas\*)*
2. A desigualdade intra-brasileira por UF (PIB municipal IBGE) supera a desigualdade entre países vizinhos nos comparativos da FBSP? *(n=3: fbsp_absp, ibge_pib\*, ibge_censo_2022\*)*
3. Municípios brasileiros teriam posição internacional melhor avaliados isoladamente (PIB + FBSP) que o Brasil agregado — quais superariam a média da OCDE? *(n=3: fbsp_absp, ibge_pib\*, world_oecd_pisa\*)*
4. Quais UFs combinam ranking internacional bom de segurança (FBSP) com indicadores sociais ruins (Censo) — e vice-versa? *(n=3: fbsp_absp, ibge_censo_2022\*, ipea_avs\*)*
5. Estados brasileiros como "países" (população Censo × violência FBSP × PIB): quais seriam de renda média-alta e quais zonas de conflito segundo os benchmarks internacionais? *(n=3: fbsp_absp, ibge_censo_2022\*, ibge_pib\*)*

## 34 · Atlas, Mapas Georreferenciados e Bases Territoriais

1. Quantos municípios mudaram código/nome desde as malhas históricas do geobr, e o Censo 2022 captou todos os novos? *(n=3: geobr_mapas, ibge_censo_2022\*, ibge_munic\*)*
2. A soma das malhas setoriais do Censo 2022 cobre exatamente o polígono municipal do geobr nos grandes municípios, ou há buracos/sobreposições? *(n=3: geobr_mapas, ibge_censo_2022\*, ibge_munic\*)*
3. A área calculada via malha do geobr diverge da oficial do Censo em quais municípios, e a divergência segue padrão regional/bioma? *(n=3: geobr_mapas, ibge_censo_2022\*, mapbiomas_estatisticas\*)*
4. Municípios criados após 2000 (geobr histórico) têm perfil demográfico distinto dos antigos no Censo 2022? *(n=3: geobr_mapas, ibge_censo_2022\*, ibge_pib\*)*
5. É possível reconstruir densidade populacional por setor censitário juntando Censo 2022 + malhas geobr sem lacunas, validando contra os totais municipais oficiais? *(n=3: ibge_censo_2022\*, geobr_mapas, ibge_munic\*)*

## 35 · Transporte e Mobilidade Urbana

1. Municípios-dormitório (Mobilidados) exportam quantos trabalhadores por dia (CAGED), e isso explica o tempo médio de deslocamento acima dos pares de mesma população (Censo)? *(n=3: mobilidados_indicadores, me_caged\*, ibge_censo_2022\*)*
2. As regiões metropolitanas de pior mobilidade (Mobilidados) são as de maior PIB per capita ou as de crescimento mais recente (PIB/Censo)? *(n=3: mobilidados_indicadores, ibge_pib\*, ibge_censo_2022\*)*
3. Onde o tempo de deslocamento cresceu mais entre medições (Mobilidados), coincide com expansão urbana visível no Censo e no geobr? *(n=3: mobilidados_indicadores, ibge_censo_2022\*, geobr_mapas\*)*
4. Capitais com melhor infraestrutura de transporte (Mobilidados) registram menos mortes no trânsito (SIM) per capita que as demais? *(n=3: mobilidados_indicadores\*, ms_sim\*, ibge_censo_2022\*)*
5. O tempo de deslocamento (Mobilidados) penaliza mais a renda efetiva do trabalhador (RAIS ÷ tempo) em quais metrópoles? *(n=3: mobilidados_indicadores\*, me_rais\*, ibge_censo_2022\*)*

## 36 · Religiosidade, Infraestrutura de Fé e Desigualdade de Renda

1. Municípios com mais templos evangélicos per capita (CNPJ, CNAE religioso) têm renda média menor no Censo e vínculos religiosos pagando menos na RAIS? *(n=3: me_cnpj, ibge_censo_2022\*, me_rais)*
2. A proporção de fiéis por religião (Censo 2022) acompanha a densidade de templos por denominação registrados como empresas no CNPJ? *(n=3: ibge_censo2022_religiao, me_cnpj, ibge_censo_2022\*)*
3. Vínculos em organizações religiosas (RAIS/CNAE) cresceram mais onde o Censo mostra maior conversão ao evangelicalismo entre 2010 e 2022? *(n=3: me_rais, ibge_censo2022_religiao, ibge_censo_2022\*)*
4. Onde há pouca igreja católica por fiel mas muitos templos evangélicos (CNPJ × Censo), qual o perfil socioeconômico local (renda/educação do Censo)? *(n=3: me_cnpj, ibge_censo2022_religiao, ibge_censo_2022\*)*
5. A renda média dos vínculos em organizações religiosas (RAIS) fica acima ou abaixo da média municipal, e essa diferença varia com a renda local (PIB)? *(n=3: me_rais, ibge_censo_2022\*, ibge_pib\*)*

## 37 · Sanções, Offshore e Arquitetura da Impunidade Empresarial

1. CNPJ sancionados pelo TCU (inidôneos) permanecem ativos no cadastro do CNPJ, em quais CNAE e municípios, e continuam vencendo licitações? *(n=3: tcu_inidoneos\*, me_cnpj\*, cgu_licitacao_contrato\*)*
2. Empresas com dívida ativa federal (PGFN) recebem pagamentos públicos (cartão CGU/licitações) apesar do débito? *(n=3: pgfn_dividaativa\*, cgu_licitacao_contrato\*, cgu_cartao_pagamento\*)*
3. CPFs de sócios de empresas inidôneas (TCU) reaparecem como sócios de novas empresas ativas — recriação de personalidade jurídica? *(n=3: tcu_inidoneos\*, me_cnpj\*, rf_arrecadacao\*)*
4. Empresas sancionadas (TCU) ou endividadas (PGFN) mantêm quadro de funcionários formais (RAIS) e sede em quais municípios? *(n=3: tcu_inidoneos\*, me_rais\*, me_cnpj\*)*
5. Os maiores devedores da PGFN concentram-se em poucos grupos econômicos (mesmo CNPJ raiz), e esses aparecem também nas sanções do TCU? *(n=3: pgfn_dividaativa\*, tcu_inidoneos\*, cgu_licitacao_contrato\*)*

## 38 · Educação Básica, Alfabetização e Comparação Internacional

1. A proporção de alfabetizados na avaliação nacional (INEP) equivale ao que o PISA indicaria para o Brasil nos mesmos anos, por faixa socioeconômica? *(n=3: inep_avaliacao_alfabetizacao, world_oecd_pisa, inep_indicador_nivel_socioeconomico\*)*
2. Escolas com mais alunos público-alvo da educação especial (INEP) têm desempenho SAEB comparável às demais dentro do mesmo município e rede? *(n=3: inep_educacao_especial, inep_saeb\*, inep_censo_escolar\*)*
3. Municípios cujos docentes têm maior formação superior (formação docente INEP) melhoram mais na alfabetização medida pelo INEP, controlada pela renda (PIB)? *(n=3: inep_formacao_docente, inep_avaliacao_alfabetizacao, ibge_pib\*)*
4. O gap entre o quartil rico brasileiro e a média OCDE no PISA aparece já na alfabetização dos anos iniciais (INEP) nas escolas privadas? *(n=3: world_oecd_pisa, inep_avaliacao_alfabetizacao, inep_censo_escolar\*)*
5. A matrícula na educação básica (Sinopse INEP) caiu proporcionalmente à perda de população jovem entre censos (2010→2022) em cada município? *(n=3: inep_sinopse_estatistica_educacao_basica, ibge_censo_2022\*, ibge_munic\*)*

## 39 · Justiça, Tribunais de Contas e Custo do Judiciário

1. Estados com maior despesa de pessoal do Judiciário (CNJ) julgam mais processos per capita, controlando pela população e renda (Censo/PIB)? *(n=3: cnj_estatisticas_poder_judiciario, ibge_censo_2022\*, ibge_pib\*)*
2. Ações de improbidade ajuizadas (CNJ) se concentram nos estados cujos TCEs mais aplicaram multa (TCE-ES/PI/RJ/SP)? *(n=3: cnj_improbidade_administrativa, tce_sp, tce_rj)*
3. As penalidades dos TCEs estaduais recaem sobre gestores de quais perfis de município (porte/população do Censo), e há reincidência por gestão seguinte? *(n=3: tce_es, tce_pi, ibge_censo_2022\*)*
4. Municípios punidos por um TCE voltam a ser alvo de novas irregularidades nos anos seguintes (mesma base TCE, série temporal)? *(n=3: tce_rj, tce_sp, tce_pi)*
5. O custo médio por processo (CNJ) varia entre tribunais do mesmo estado, e a variação acompanha a despesa de pessoal total (SICONFI)? *(n=3: cnj_estatisticas_poder_judiciario, me_siconfi\*, tce_rj\*)*

## 40 · Federalismo Fiscal e Capacidade Financeira dos Municípios

1. Municípios com melhor CAPAG (Tesouro) recebem mais ou menos transferências voluntárias (Transferegov) que os de pior nota, controlado pelo porte (Censo)? *(n=3: tesouro_capag, transferegov, ibge_censo_2022\*)*
2. O índice FIRjan IFGF confirma a classificação da CAPAG município a município, e onde divergem há diferença de gasto obrigatório no SIOP? *(n=3: firjan_ifgf, tesouro_capag, siop_orcamento)*
3. Emendas e transferências federais (Transferegov/CGU) vão proporcionalmente aos municípios de pior capacidade fiscal ou aos politicamente fortes? *(n=3: transferegov, cgu_emendas_parlamentares\*, tesouro_capag)*
4. Despesas obrigatórias autorizadas no SIOP pesam quanto do orçamento dos municípios de menor IFGF vs os de melhor nota? *(n=3: siop_orcamento, firjan_ifgf, ibge_pib\*)*
5. Municípios que melhoraram a CAPAG entre anos receberam mais investimentos via Transferegov ou cortaram despesa própria medida no SICONFI? *(n=3: tesouro_capag, transferegov, me_siconfi\*)*

## 41 · Nutrição, Preço de Medicamentos e Acesso à Saúde

1. O preço máximo permitido pela CMED (ANVISA) difere do praticado no Farmácia Popular para os mesmos princípios ativos, e a diferença varia por região? *(n=3: anvisa_cmed, saude_farmaciapopular, geobr_mapas\*)*
2. Municípios com pior estado nutricional no SISVAN são os que mais consomem medicamentos contínuos (BPS/Farmácia Popular) per capita? *(n=3: ms_sisvan, saude_bps\*, saude_farmaciapopular\*)*
3. O orçamento familiar com alimentação (POF) explica quanto da variação regional do sobrepeso/obesidade no SISVAN, controlada pela renda municipal? *(n=3: ibge_pof, ms_sisvan, ibge_censo_2022\*)*
4. Medicamentos com demanda regulada (CMED) ficaram mais baratos depois de entrarem no Farmácia Popular, na série temporal? *(n=3: anvisa_cmed, saude_farmaciapopular, saude_bps\*)*
5. Onde o SISVAN mostra déficit nutricional infantil acima da média, o gasto alimentar per capita (POF ÷ Censo) é menor e o acesso a medicamentos contínuos (BPS) também? *(n=3: ms_sisvan, ibge_pof\*, saude_bps\*)*

## 42 · Água, Clima e Biodiversidade Ameaçada

1. Bacias monitoradas pela ANA com vazão crítica coincidem com os municípios de maior foco de queimadas (INPE) e perda de vegetação (MapBiomas) nos mesmos períodos? *(n=3: ana_telemetria, inpe_queimadas\*, mapbiomas_estatisticas\*)*
2. Estações do INMET confirmam secas prolongadas exatamente onde o MapBiomas registra perda de cobertura nativa e o SISAM modelou anomalia climática? *(n=3: inmet_bdmep, mapbiomas_estatisticas\*, inpe_sisam)*
3. Espécies ameaçadas de extinção (MMA) concentram-se nos biomas/municípios que mais perderam vegetação (MapBiomas) e mais queimaram (INPE)? *(n=3: mma_extincao, mapbiomas_estatisticas\*, inpe_queimadas\*)*
4. Os dados hidrológicos do HydroSHEDS (WWF) validam as bacias críticas apontadas pela telemetria da ANA nos mesmos períodos de seca? *(n=3: world_wwf_hydrosheds, ana_telemetria, inmet_bdmep\*)*
5. A mortalidade respiratória (SIM) sobe nos municípios de pico de fogo (INPE) dentro das bacias de vazão crítica (ANA), no mesmo trimestre? *(n=3: inpe_queimadas\*, ms_sim\*, ana_telemetria)*

## 43 · Cultura, Esporte e Desempenho Internacional

1. Atletas olímpicos brasileiros nascidos em municípios grandes (Censo) superam proporcionalmente os de cidades pequenas, ou há polos regionais específicos (malhas geobr)? *(n=3: world_olympedia_olympics, ibge_censo_2022\*, geobr_mapas\*)*
2. Medalhas olímpicas por município de nascimento (Olympedia) correlacionam-se com PIB per capita municipal e renda média do Censo? *(n=3: world_olympedia_olympics, ibge_pib\*, ibge_censo_2022\*)*
3. Quais esportes concentram as medalhas do Brasil (Olympedia) e de quais regiões vêm seus atletas (geobr × Censo)? *(n=3: world_olympedia_olympics, geobr_mapas\*, ibge_censo_2022\*)*
4. A evolução histórica das medalhas brasileiras acompanhou o crescimento do PIB nacional ou seguiu ciclos de política esportiva próprios? *(n=3: world_olympedia_olympics, ibge_pib\*, ibge_munic\*)*
5. Municípios-sede de atletas olímpicos (Olympedia × Censo) têm mais empresas formais do setor esportivo (CNPJ/CNAE) que a média dos vizinhos? *(n=3: world_olympedia_olympics, me_cnpj\*, geobr_mapas\*)*

## 44 · Saneamento, Produção Rural e Desmatamento

1. Municípios com pior índice de esgotamento sanitário (ANA Atlas Esgotos) têm maior mortalidade infantil (SIM/SINASC), controlado pela renda (Censo)? *(n=3: ana_atlas_esgotos, ms_sim\*, ibge_censo_2022\*)*
2. A produção agropecuária municipal (PAM lavouras, PEVS extração vegetal/silvicultura) cresce mais nos municípios que mais desmataram (PRODES) — silvicultura plantada substituindo extração nativa onde a vegetação já caiu? *(n=3: ibge_pam, ibge_pevs, inpe_prodes\*)*
3. Imóveis rurais cadastrados no CAFIR (Receita Federal) concentram-se nos municípios recordistas de desmatamento (PRODES), na mesma medida que o crédito rural do SICOR? *(n=2: rf_cafir, inpe_prodes\*)*
4. Dos imóveis embargados pelo IBAMA por desmatamento, quantos seguem com produção agropecuária ativa declarada (PAM) no mesmo município? *(n=2: ibama_embargos, ibge_pam\*)*
5. Municípios com mais outorgas de captação de água (ANA Outorgas) por habitante são os de maior produção agropecuária irrigada (PAM), ou os de maior industrialização (CNPJ/CNAE)? *(n=3: ana_outorgas, ibge_pam\*, me_cnpj\*)*

## 45 · Integridade do Sistema Financeiro e Fornecedores Públicos

1. Fornecedores habilitados a licitar no SICAF (Comprasgov) que também constam como inidôneos no TCU continuam com CNPJ ativo e habilitação vigente? *(n=3: comprasgov_sicaf, tcu_inidoneos, me_cnpj\*)*
2. Fundos de investimento registrados na CVM sob CNPJ com dívida ativa federal (PGFN) — quantos e qual o valor devido? *(n=2: cvm_fundos, pgfn_dividaativa)*
3. Instituições ou pessoas penalizadas pelo Banco Central (penalidades BCB) reaparecem como administradores de carteira registrados na CVM? *(n=2: bcb_penalidades, cvm_administradores_carteira)*
4. Sócios de empresas com CNPJ inidôneo no TCU recriam personalidade jurídica via cadeias de holding (Brasil.IO) com a mesma pessoa como sócia em nova empresa? *(n=2: tcu_inidoneos, brasilio_holdings)*
5. Entidades sancionadas internacionalmente (OpenSanctions/OFAC/EU/UN) têm nome compatível com alguma empresa ativa no cadastro CNPJ brasileiro? *(n=2: global_opensanctions\*, me_cnpj\*)*

## 46 · Educação Superior e Acesso

1. Municípios com maior proporção de vagas de graduação financiadas pelo PROUNI (Censo da Educação Superior) têm PIB per capita sistematicamente menor — o programa cumpre seu papel redistributivo, ou se distribui igual entre municípios ricos e pobres? *(n=2: inep_censo_educacao_superior, ibge_pib\*)*
2. A proporção de docentes com doutorado nas IES de um município (Censo da Educação Superior) se relaciona com a taxa de abandono no ensino médio local (Indicadores Educacionais)? *(n=2: inep_censo_educacao_superior, inep_indicadores_educacionais)*
3. Os bolsistas de mobilidade internacional da CAPES se concentram nos mesmos estados de maior PIB per capita e maior corpo docente com doutorado (Censo da Educação Superior), ou o programa também alcança estados menos providos de pesquisa? *(n=3: capes_bolsas, ibge_pib\*, inep_censo_educacao_superior)*
4. Municípios onde o SISU é mais concorrido (candidatos aprovados por vaga) formam proporcionalmente mais concluintes em relação às matrículas ativas (Censo da Educação Superior) no mesmo ano? *(n=2: mec_sisu, inep_censo_educacao_superior)*
5. Municípios sem nenhuma instituição de ensino superior (Censo da Educação Superior) têm nível socioeconômico médio mais baixo nas escolas de ensino fundamental avaliadas pela ANA do que os que têm ao menos uma IES? *(n=2: inep_censo_educacao_superior, inep_ana)*

## 47 · Servidor Público e Integridade

1. A concentração per capita de cargos comissionados federais por UF (Painel Estatístico de Pessoal) acompanha o PIB per capita, ou é só um artefato de Brasília sediar a maioria dos órgãos? *(n=2: mp_pep, ibge_pib\*)*
2. A composição racial dos cargos comissionados federais (Painel Estatístico de Pessoal) reflete a composição racial da população brasileira do Censo 2022? *(n=2: mp_pep, ibge_censo_2022\*)*
3. A composição racial do funcionalismo federal como um todo (SIAPE) difere da composição racial de quem ocupa cargo comissionado (Painel Estatístico de Pessoal) — o topo da carreira é mais branco que a base? *(n=2: me_siape, mp_pep)*
4. Responsáveis por obras cadastradas no CNO (Receita Federal) que constam como inidôneos no TCU seguem registrando obras ativas? *(n=2: rf_cno, tcu_inidoneos)*
5. Municípios com mais obras ativas cadastradas no CNO per capita têm maior participação industrial no PIB local? *(n=2: rf_cno, ibge_pib\*)*

## 48 · Sanções Internacionais e Verificação de Identificador

1. As listas de sanções internacionais (UE, ONU, OFAC) contêm alguma entrada ligada ao Brasil com identificador estruturado (CNPJ/CPF) utilizável para cruzamento, ou o vínculo — quando existe — só aparece em texto livre? *(n=3: eu_sanctions, un_sanctions, global_ofac_sanctions)*
2. Das entidades offshore do ICIJ Offshore Leaks (Panama/Paradise/Pandora Papers) marcadas com país Brasil, quantas casam por nome exato com uma razão social no cadastro CNPJ, e sob qual natureza jurídica? *(n=2: global_icij_offshoreleaks, me_cnpj\*)*
3. O nome das pessoas físicas ("officers") do ICIJ ligadas ao Brasil, cruzado por nome exato contra sócios do CNPJ, produz identificação confiável de beneficiário final ou colide em nomes comuns demais para servir como chave? *(n=2: global_icij_offshoreleaks, me_cnpj\*)*
4. As entidades offshore do ICIJ casadas ao CNPJ aparecem como sócias de empresas brasileiras no grafo de holdings do Brasil.IO, e alguma coincide com os CNPJ inidôneos do TCU? *(n=3: global_icij_offshoreleaks, brasilio_holdings\*, tcu_inidoneos\*)*
5. Entre as entidades offshore do ICIJ casadas ao CNPJ brasileiro, qual vazamento de origem (Panama/Paradise/Pandora Papers) domina, e a situação cadastral (ativa/suspensa/baixada) se distribui de forma diferente por jurisdição de incorporação? *(n=2: global_icij_offshoreleaks, me_cnpj\*)*

## 49 · Saúde Suplementar e Atenção Básica

1. Cobertura de plano de saúde privado (ANS) por município reduz a mortalidade infantil (SIM×SINASC), mesmo controlando a renda (PIB per capita)? *(n=4: br_ans_beneficiario, ms_sim\*, ms_sinasc\*, ibge_pib\*)*
2. Onde a cobertura de plano de saúde privado (ANS) é maior, a cobertura da Estratégia Saúde da Família (Atenção Básica) é menor — substituição do público pelo privado, independente da renda municipal (PIB)? *(n=3: br_ans_beneficiario, br_ms_atencao_basica, ibge_pib\*)*
3. A cobertura vacinal infantil (Imunizações, vacina pentavalente) explica a mortalidade infantil (SIM×SINASC) melhor ou pior que a cobertura de Atenção Básica (equipes de Saúde da Família) no mesmo município? *(n=4: br_ms_imunizacoes, ms_sim\*, ms_sinasc\*, br_ms_atencao_basica)*
4. A cobertura vacinal contra Covid-19 por município (Vacinação Covid-19) foi maior onde a Atenção Básica já era mais forte (equipes de Saúde da Família), ou a campanha emergencial chegou igual a todos? *(n=2: br_ms_vacinacao_covid19, br_ms_atencao_basica)*
5. Beneficiários de plano de saúde privado (ANS) são proporcionalmente mais idosos que a população geral do município (Censo 2022), e isso muda com a renda (PIB per capita)? *(n=3: br_ans_beneficiario, ibge_censo_2022\*, ibge_pib\*)*

## 50 · Justiça Complementar e Filiação Partidária

1. Nos partidos, a proporção de mulheres entre os filiados (TSE filiação partidária) se traduz em proporção equivalente entre os eleitos em 2022, e essa lacuna de conversão varia com a riqueza do estado (PIB per capita)? *(n=3: tse_filiacao_partidaria, tse_eleicoes\*, ibge_pib\*)*
2. A densidade de filiados por partido e UF (TSE filiação) explica a votação obtida para deputado federal em 2022 (TSE eleições), e essa conversão de filiado em voto é mais eficiente nos estados mais ricos (PIB)? *(n=3: tse_filiacao_partidaria, tse_eleicoes\*, ibge_pib\*)*
3. A taxa de homicídio doloso por UF em 2022 (SINESP), normalizada pela população do Censo, acompanha o resultado presidencial do primeiro turno (TSE eleições) — estados mais violentos votaram menos em Bolsonaro/PL? *(n=3: mjsp_sinesp, ibge_censo_2022\*, tse_eleicoes\*)*
4. O volume de decisões eleitorais do STF (Corte Aberta) acompanha o salto de candidaturas registradas no TSE entre eleição municipal e geral, e o gasto do Judiciário eleitoral (CNJ) confirma esse padrão? *(n=3: stf_corte_aberta, tse_eleicoes\*, cnj_estatisticas_poder_judiciario\*)*
5. As reclamações registradas nos PROCONs (MJSP/CKAN) por UF, normalizadas pela população do Censo, indicam maior conflito de consumo per capita ou cobertura desigual da fonte — e as empresas mais reclamadas seguem ativas no CNPJ? *(n=3: mjsp_ckan, ibge_censo_2022\*, me_cnpj\*)*

## 54 · Censo Histórico e Consistência Populacional

1. As duas fontes de população municipal do espelho — a série do IBGE e a do Ministério da Saúde — concordam? Quando exatamente divergem, e a divergência é sistemática ou ruído de arredondamento? *(n=2: ibge_populacao, ms_populacao)*
2. Quantos dos 5.570 municípios brasileiros atuais simplesmente não existiam como código próprio no Censo Demográfico de 1970 e no de 1980 — e o quanto isso invalida uma série histórica de população construída por join direto em `id_municipio`? *(n=1: ibge_censo_demografico)*
3. A população municipal de 2010 reconstruída a partir do peso amostral dos microdados do Censo Demográfico bate com a série oficial do IBGE — e essa reconstrução é possível para os outros anos do censo histórico (1970-2000)? *(n=2: ibge_censo_demografico, ibge_populacao\*)*
4. A taxa de alfabetização (5 anos ou mais) medida nos microdados do Censo Demográfico cresceu entre 1991 e 2000, e quantos municípios de 2000 não têm par em 1991 para essa comparação? *(n=1: ibge_censo_demografico)*
5. Estados com maior participação de cargos comissionados na administração direta (ESTADIC) têm PIB per capita menor — o comissionamento é um substituto de carreira profissionalizada nos estados mais pobres? *(n=2: ibge_estadic, ibge_pib\*)*

## 51 · Energia, Comércio Exterior e Infraestrutura

1. O consumo de energia elétrica por UF (MME) explica a renda per capita local mesmo depois de neutralizar o efeito do tamanho populacional — a correlação bruta cai de quanto para quanto quando ambas variáveis são normalizadas pela população do Censo? *(n=3: mme_consumo_energia_eletrica, ibge_pib\*, ibge_censo_2022\*)*
2. Estados com mais tráfego aéreo (ANAC) são os de maior PIB e maior consumo de energia elétrica (MME) — mas a pontualidade dos voos acompanha a riqueza do estado de destino, ou é independente dela? *(n=3: anac_dadosabertos, ibge_pib\*, mme_consumo_energia_eletrica)*
3. O preço de um insumo específico de construção (cimento, SINAPI) é mais caro nos estados mais pobres/remotos, mas essa "sobretaxa da distância" se sustenta quando se olha a cesta inteira de materiais, ou desaparece? *(n=3: caixa_sinapi, ibge_pib\*, ibge_censo_2022\*)*
4. O piso de mão de obra de referência do SINAPI acompanha o salário médio real pago na construção civil formal (RAIS, CNAE 41-43) por UF, e ambos acompanham a renda per capita local? *(n=3: caixa_sinapi, me_rais\*, ibge_pib\*)*
5. O consumo de energia elétrica da classe "Comercial" (MME) por UF é um proxy fiel do tamanho do setor de comércio formal (RAIS, CNAE 45-47), mesmo depois de tirar o efeito do tamanho populacional? *(n=3: mme_consumo_energia_eletrica, me_rais\*, ibge_censo_2022\*)*

## 52 · Séries Financeiras, Dívida Pública e Crédito

1. Municípios que mais captaram crédito direto do BNDES (operações não automáticas, 2002–2026) são os de maior PIB per capita, ou o crédito de fomento vai desproporcionalmente para municípios mais pobres? *(n=2: bndes_operacoes_contratadas, ibge_pib\*)*
2. Alguma empresa que tomou empréstimo direto do BNDES apareceu depois na lista de inidôneos do TCU — o banco público de fomento já financiou quem viria a ser formalmente declarado inapto a contratar com a União? *(n=2: bndes_operacoes_contratadas, tcu_inidoneos\*)*
3. O estoque da dívida pública federal (Tesouro Nacional) como proporção do PIB nacional (IBGE) cresceu de forma monotônica entre 2017 e 2021, ou o choque foi concentrado no ano da pandemia? *(n=2: me_estoque_divida_publica, ibge_pib\*)*
4. O IGP-M (FGV, índice geral de preços "do atacado") descolou do IPCA nos anos de choque cambial/commodities (2020–2021), e por quanto? *(n=2: fgv_igp, bcb_sgs)*
5. Os ciclos de aperto da Selic (BCB SGS) historicamente coincidem com desaceleração da contratação de crédito do BNDES, ou o crédito de fomento é imune ao ciclo de juros básico por rodar em taxas próprias (TJLP/TLP)? *(n=2: bcb_sgs, bndes_operacoes_contratadas)*

## 53 · Índices de Competitividade e Comparativos Internacionais

1. Os três índices de saúde fiscal estadual — o pilar "Solidez Fiscal" do ranking CLP, a CAPAG do Tesouro e o IFGF da FIRJAN — concordam entre si sobre quais estados têm melhor gestão fiscal? *(n=3: br_clp_ranking_competitividade, tesouro_capag\*, firjan_ifgf\*)*
2. O ranking geral de competitividade estadual do CLP é explicado pela riqueza dos estados (PIB per capita), ou existe competitividade "além da renda"? *(n=3: br_clp_ranking_competitividade, ibge_pib\*, ibge_populacao\*)*
3. A carga tributária dos estados brasileiros (impostos líquidos ÷ PIB, IBGE) cai dentro da faixa observada entre os países da OCDE (world_oecd_public_finance), ou o Brasil tributa fora da curva? *(n=3: world_oecd_public_finance, ibge_pib\*, ibge_populacao\*)*
4. O pilar "Segurança Pública" do ranking CLP acompanha o pilar "Sustentabilidade Social" e a riqueza (PIB per capita) dos mesmos estados — segurança e coesão social andam juntas? *(n=3: br_clp_ranking_competitividade, ibge_pib\*, ibge_populacao\*)*
5. Os indicadores fiscais da OCDE (world_oecd_public_finance) permitem posicionar o gasto público obrigatório dos estados brasileiros (capacidade fiscal, Tesouro CAPAG) no comparativo internacional de gasto saúde/educação como % do PIB? *(n=3: world_oecd_public_finance, ibge_pib\*, tesouro_capag\*)*

## 55 · Vulnerabilidade Social, Medicamentos e Consumo

1. A tendência anual de homicídios de pessoas LGBTQI+ (relatório do Grupo Gay da Bahia) acompanha a tendência nacional de óbitos por agressão do SIM entre 2000 e 2019, ou diverge? *(n=2: ggb_relatorio_lgbtqi, ms_sim\*)*
2. Entre os princípios ativos controlados mais vendidos no país (SNGPC/ANVISA), o preço máximo regulado pela CMED explica o volume vendido — remédio mais caro vende menos? *(n=2: anvisa_medicamentos_industrializados, anvisa_cmed\*)*
3. Os princípios ativos controlados mais vendidos no SNGPC têm base de fabricantes com registro ativo suficiente na ANVISA, ou a oferta está concentrada em pouquíssimos registros vigentes? *(n=2: anvisa_medicamentos_industrializados, anvisa_consultas)*
4. O preço FIPE por modelo/ano funciona como proxy municipal de renda quando cruzado com alguma fonte territorial do espelho? *(n=2: fipe_veiculos, ibge_censo_2022\*)*
5. A composição racial das vítimas de homicídio LGBTQI+ (GGB) segue o mesmo padrão racial das vítimas de homicídio em geral no SIM, no mesmo ano? *(n=2: ggb_relatorio_lgbtqi, ms_sim\*)*

---

# Perguntas multi-dataset simultâneos

Estas atravessam três ou mais famílias distintas de dados (trabalho + saúde +
eleições + território + dinheiro público), exigindo joins em cascata por
múltiplas chaves ao mesmo tempo.

1. **Trajetória raça → mercado → morte**: rendimento por raça (RAIS) → rotatividade/informalidade setorial (CAGED) → mortalidade por causas evitáveis (SIM), tudo por município e UF — em quais territórios as três desvantagens se acumulam simultaneamente? *(n=3+: me_rais, me_caged, ms_sim; chaves: id_municipio, sigla_uf, cbo_2002)*
2. **Escola → conectividade → eleição**: desempenho escolar (ENEM/SAEB) × conectividade municipal (Anatel) × resultado eleitoral (TSE) × perfil demográfico (Censo): municípios que investiram em conectividade escolar mudaram a nota, o voto, ou ambos? *(n=4: inep_enem, anatel_indice_brasileiro_conectividade, tse_eleicoes, ibge_censo_2022; chaves: id_municipio, sigla_uf)*
3. **Emenda → contrato → empresa → sanção**: seguir o dinheiro das emendas parlamentares (CGU) até os contratos firmados (CGU licitações/cartão), identificar os fornecedores no cadastro CNPJ e verificar quantos estão sancionados (TCU) ou endividados (PGFN). *(n=4–5: cgu_emendas_parlamentares, cgu_licitacao_contrato, me_cnpj, tcu_inidoneos, pgfn_dividaativa; chaves: cnpj, id_municipio)*
4. **Desmatamento → crédito → produção → sanção fundiária**: cruzar desmatamento (PRODES), crédito rural por tomador (SICOR), área cadastrada e pendências (SICAR) e produção pecuária (PPM) por município: quem financia e quem produz nos municípios recordistas de desmate? *(n=4: inpe_prodes, bcb_sicor, sfb_sicar, ibge_ppm; chaves: id_municipio, cpf/cnpj do financiamento)*
5. **Nascimento → escola → trabalho → óbito juvenil**: retrato de coorte territorial juntando nascidos vivos (SINASC), matrículas (Sinopse INEP), vínculos formais jovens (RAIS) e óbitos juvenis (SIM) por município — onde o ciclo se rompe mais cedo? *(n=4: ms_sinasc, inep_sinopse_estatistica_educacao_basica, me_rais, ms_sim; chaves: id_municipio, sigla_uf)*
