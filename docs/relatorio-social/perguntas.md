# Perguntas Sociológicas para Base dos Dados

Este documento apresenta 50 perguntas de pesquisa em ciências sociais que podem ser respondidas utilizando a Base dos Dados Brasil. As perguntas foram elaboradas para explorar relações complexas entre múltiplas dimensões sociais, cruzando dados de censos, saúde, educação, trabalho, política, segurança e infraestrutura.

---

## 1. Desigualdade Racial e Estratificação Social

**1. Qual é a relação entre cor/raça, nível educacional e renda no Brasil, e como essa relação mudou entre os censos de 1991, 2000 e 2010?**

- **Fontes:** `br_ibge_censo_demografico.setor_censitario_pessoa_renda_2010`, `br_ibge_censo_demografico.setor_censitario_raca_alfabetizacao_idade_genero_2010`, `br_ibge_censo_2022.populacao_grupo_idade_sexo_raca`

**2. Como a mortalidade por causas violentas (homicídios) varia por raça/cor, sexo e faixa etária nos municípios brasileiros, e qual a correlação com indicadores socioeconômicos?**

- **Fontes:** `br_ms_sim.microdados`, `br_rj_isp_estatisticas_seguranca.taxa_evolucao_mensal_municipio`, `br_ibge_pib.municipio`

**3. Qual a diferença na taxa de fecundidade adolescente entre mulheres negras e não-negras no Brasil, e como essa diferença se distribui regionalmente?**

- **Fontes:** `br_ms_sinasc.microdados`, `br_ibge_censo_2022.populacao_grupo_idade_sexo_raca`

**4. Existe segregação residencial racial nos grandes centros urbanos brasileiros? Qual a correlação entre composição racial do setor censitário e renda média?**

- **Fontes:** `br_ibge_censo_demografico.setor_censitario_basico_2010`, `br_ibge_censo_demografico.setor_censitario_responsavel_renda_2010`

---

## 2. Educação, Mobilidade Social e Desigualdade

**5. Qual a relação entre o nível socioeconômico dos estudantes (medido pelo INEP) e seu desempenho no ENEM/SAEB, e essa relação varia por região e tipo de escola (pública/privada)?**

- **Fontes:** `br_inep_enem.microdados`, `br_inep_saeb.municipio`, `br_inep_indicador_nivel_socioeconomico.escola`

**6. Qual a disparidade educacional entre populações urbanas e rurais, especialmente entre indígenas e quilombolas?**

- **Fontes:** `br_ibge_censo_2022.terra_indigena`, `br_ibge_censo_2022.territorio_quilombola`, `br_inep_censo_escolar.escola`

**7. Como a distorção idade-série no ensino fundamental varia conforme a cor/raça do estudante e a dependência administrativa da escola?**

- **Fontes:** `br_inep_educacao_especial.distorcao_idade_serie`, `br_inep_educacao_especial.sexo_raca_cor`, `br_inep_censo_escolar.escola`

**8. Qual a relação entre investimento em educação (remuneração docente) e indicadores de qualidade educacional (IDEB) nos municípios?**

- **Fontes:** `br_inep_ideb.municipio`, `br_inep_indicadores_educacionais.municipio_remuneracao_docentes`, `br_me_siconfi.municipio_despesas_funcao`

---

## 3. Saúde, Acesso a Serviços e Determinantes Sociais

**9. Qual a relação entre o número de estabelecimentos de saúde por 1000 habitantes e indicadores de mortalidade infantil nos municípios brasileiros?**

- **Fontes:** `br_ms_cnes.estabelecimento`, `br_ms_sim.microdados`, `br_ms_sinasc.microdados`, `br_ibge_populacao.municipio`

**10. Existe correlação entre a cobertura de planos de saúde privados e a utilização de serviços do SUS em diferentes faixas etárias?**

- **Fontes:** `br_ans_beneficiario.informacao_consolidada`, `br_ms_cnes.estabelecimento`, `br_ms_sia.producao_ambulatorial`

**11. Qual a distribuição espacial de profissionais de saúde (médicos, enfermeiros) nos municípios e como essa distribuição se correlaciona com indicadores de mortalidade materna e infantil?**

- **Fontes:** `br_ms_cnes.profissional`, `br_ms_cnes.equipamento`, `br_ms_sinasc.microdados`

**12. Como a prevalência de doenças crônicas (medida pela PNS) se associa a indicadores socioeconômicos e de acesso a serviços de saúde?**

- **Fontes:** `br_ms_pns.microdados_2019`, `br_ibge_pib.municipio`, `br_ibge_censo_demografico.setor_censitario_pessoa_renda_2010`

---

## 4. Mercado de Trabalho, Informalidade e Estratificação

**13. Qual a relação entre escolaridade, cor/raça e posição na ocupação no mercado de trabalho brasileiro contemporâneo?**

- **Fontes:** `br_me_rais.microdados_vinculos`, `br_ibge_pnadc.microdados`, `br_bd_diretorios_brasil.cbo_2002`

**14. Como a informalidade laboral varia entre regiões metropolitanas e interiores, e qual a correlação com indicadores de pobreza e acesso a serviços públicos?**

- **Fontes:** `br_me_rais.microdados_vinculos`, `br_me_caged.microdados_movimentacao`, `br_ibge_pnadc.microdados`

**15. Qual a disparidade salarial entre homens e mulheres com mesmo nível educacional e ocupação, controlando por setor econômico?**

- **Fontes:** `br_me_rais.microdados_vinculos`, `br_ibge_pnadc.microdados`, `br_bd_diretorios_brasil.cbo_2002`

**16. Qual a relação entre o porte das empresas (micro, pequena, média, grande) e os salários médios oferecidos, considerando a distribuição regional?**

- **Fontes:** `br_me_rais.microdados_estabelecimentos`, `br_me_rais.microdados_vinculos`, `br_bd_diretorios_brasil.empresa`

---

## 5. Política, Representação e Comportamento Eleitoral

**17. Qual a relação entre o perfil socioeconômico dos municípios e o comportamento eleitoral (voto em candidatos de esquerda vs. direita)?**

- **Fontes:** `br_tse_eleicoes.resultados_candidato_municipio`, `br_ibge_pib.municipio`, `br_ibge_censo_demografico.setor_censitario_pessoa_renda_2010`

**18. Existe sub-representação de mulheres e pessoas negras entre candidatos e eleitos nas eleições municipais, estaduais e federais?**

- **Fontes:** `br_tse_eleicoes.candidatos`, `br_tse_eleicoes.resultados_candidato`, `br_ibge_censo_2022.populacao_grupo_idade_sexo_raca`

**19. Qual a relação entre despesas de campanha, tempo de rádio/TV e resultado electoral, e existem diferenças por partido e região?**

- **Fontes:** `br_tse_eleicoes.despesas_candidato`, `br_tse_eleicoes.receitas_candidato`, `br_tse_eleicoes.resultados_candidato`

**20. Qual o perfil dos parlamentares brasileiros (idade, sexo, raça, profissão, origem regional) e como esse perfil mudou ao longo das legislaturas?**

- **Fontes:** `br_camara_dados_abertos.deputado`, `br_camara_dados_abertos.deputado_profissao`, `br_camara_dados_abertos.legislatura`

---

## 6. Crime, Violência e Segurança Pública

**21. Qual a relação entre desigualdade de renda (coeficiente de Gini), concentração fundiária e taxas de homicídio nos municípios brasileiros?**

- **Fontes:** `br_ibge_pib.gini`, `br_rj_isp_estatisticas_seguranca.taxa_evolucao_mensal_municipio`, `br_ms_sim.microdados`

**22. Como a presença de unidades de polícia pacificadora (UPPs) no Rio de Janeiro se correlaciona com indicadores de criminalidade e condições socioeconômicas das áreas afetadas?**

- **Fontes:** `br_rj_isp_estatisticas_seguranca.evolucao_mensal_upp`, `br_rj_isp_estatisticas_seguranca.taxa_letalidade`, `br_ibge_censo_demografico.setor_censitario_basico_2010`

**23. Qual a correlação entre armas apreendidas, efetivo policial e taxas de letalidade violenta nos estados brasileiros?**

- **Fontes:** `br_rj_isp_estatisticas_seguranca.armas_apreendidas_mensal`, `br_rj_isp_estatisticas_seguranca.evolucao_policial_morto_servico_mensal`, `br_rj_isp_estatisticas_seguranca.taxa_evolucao_anual_uf`

---

## 7. Economia, Crédito e Desenvolvimento Regional

**24. Como o crédito agrícola do SICOR se distribui entre pequenos, médios e grandes produtores, e existe concentração regional e por tipo de cultivo?**

- **Fontes:** `br_bcb_sicor.operacao`, `br_bcb_sicor.recurso_publico_mutuario`, `br_bcb_sicor.recurso_publico_propriedade`

**25. Qual a relação entre acesso a instituições bancárias (número de agências) e indicadores de desenvolvimento socioeconômico nos municípios?**

- **Fontes:** `br_bcb_estban.agencia`, `br_bcb_estban.municipio`, `br_ibge_pib.municipio`

**26. Existe correlação entre a diversificação econômica dos municípios (variedade de CNAEs) e seus indicadores de emprego e renda?**

- **Fontes:** `br_me_cnpj.estabelecimentos`, `br_bd_diretorios_brasil.cnae_2`, `br_me_rais.microdados_vinculos`

**27. Qual a concentração de mercado (HHI) no setor de telecomunicações (banda larga fixa) e como ela varia entre estados e municípios?**

- **Fontes:** `br_anatel_banda_larga_fixa.microdados`, `br_anatel_indice_brasileiro_conectividade.municipio`

---

## 8. Políticas Públicas, Transferências e Proteção Social

**28. Qual a relação entre a cobertura de programas sociais (Bolsa Família, BPC, Auxílio Brasil) e indicadores de pobreza e desigualdade nos municípios?**

- **Fontes:** `br_cgu_beneficios_cidadao.bolsa_familia_pagamento`, `br_cgu_beneficios_cidadao.bpc`, `br_cgu_beneficios_cidadao.novo_bolsa_familia`, `br_ibge_pib.gini`

**29. Como a execução orçamentária dos municípios (despesas por função) se correlaciona com indicadores de desenvolvimento humano e perfil socioeconômico?**

- **Fontes:** `br_me_siconfi.municipio_despesas_funcao`, `br_me_siconfi.municipio_receitas_orcamentarias`, `br_ibge_pib.municipio`

**30. Qual o impacto do Programa Universidade para Todos (PROUNI) na mobilidade social de egressos de escolas públicas?**

- **Fontes:** `br_mec_prouni.dicionario`, `br_inep_enem.microdados`, `br_inep_censo_educacao_superior.ies`

---

## 9. Gênero, Família e Dinâmicas Demográficas

**31. Como a taxa de mortalidade materna varia conforme escolaridade, cor/raça e acesso a serviços de saúde pré-natal nos municípios?**

- **Fontes:** `br_ms_sinasc.microdados`, `br_ms_sim.microdados`, `br_ms_cnes.estabelecimento`

**32. Qual a relação entre participação feminina no mercado de trabalho e indicadores de fecundidade, e como essa relação varia por classe social e região?**

- **Fontes:** `br_me_rais.microdados_vinculos`, `br_ms_sinasc.microdados`, `br_ibge_pnadc.microdados`

**33. Como a proporção de mulheres chefes de família (sem cônjuge) se relaciona com indicadores de pobreza e vulnerabilidade nos setores censitários?**

- **Fontes:** `br_ibge_censo_demografico.setor_censitario_responsavel_domicilios_mulheres_2010`, `br_ibge_censo_demografico.setor_censitario_responsavel_renda_2010`

---

## 10. Meio Ambiente, Desenvolvimento e Sustentabilidade

**34. Qual a relação entre a expansão da fronteira agrícola (soja, gado) e o desmatamento em áreas de biomas brasileiros (Amazônia, Cerrado, Pantanal)?**

- **Fontes:** `br_trase_supply_chain.soy_beans`, `br_trase_supply_chain.beef`, `br_inpe_prodes.municipio_bioma`, `br_seeg_emissoes.municipio`

**35. Como as emissões de gases de efeito estufa se correlacionam com o perfil produtivo (agrícola, industrial, serviços) dos municípios?**

- **Fontes:** `br_seeg_emissoes.municipio`, `br_ibge_pam.lavoura_temporaria`, `br_ibge_ppm.efetivo_rebanhos`, `br_me_rais.microdados_vinculos`

**36. Qual a relação entre a presença de unidades de conservação e indicadores socioeconômicos das populações vizinhas?**

- **Fontes:** `br_geobr_mapas.unidade_conservacao`, `br_ibge_censo_demografico.setor_censitario_basico_2010`, `br_ibge_pib.municipio`

---

## 11. Infraestrutura, Serviços e Qualidade de Vida

**37. Qual a relação entre acesso a saneamento básico (água, esgoto, coleta de lixo) e indicadores de saúde (mortalidade, internações) nos municípios?**

- **Fontes:** `br_mdr_snis.municipio_agua_esgoto`, `br_ms_sih.servicos_profissionais`, `br_ms_sim.microdados`

**38. Como a densidade de banda larga fixa e a cobertura de celular (4G/5G) se correlacionam com indicadores de desenvolvimento e acesso a serviços públicos nos municípios?**

- **Fontes:** `br_anatel_banda_larga_fixa.densidade_municipio`, `br_anatel_indice_brasileiro_conectividade.municipio`, `br_ibge_pib.municipio`

**39. Qual a relação entre infraestrutura escolar (laboratórios, bibliotecas, quadra esportiva) e desempenho dos estudantes em avaliações nacionais?**

- **Fontes:** `br_ms_cnes.estabelecimento_ensino`, `br_inep_saeb.municipio`, `br_inep_ideb.escola`

---

## 12. Interseccionalidade e Desigualdades Complexas

**40. Como a interseção entre classe social, cor/raça e gênero afeta as chances de ascensão social (mudança de classe entre gerações) no Brasil?**

- **Fontes:** `br_me_rais.microdados_vinculos`, `br_ibge_pnadc.microdados`, `br_ibge_censo_2022.populacao_grupo_idade_sexo_raca`

**41. Qual a relação entre trabalho doméstico remunerado (empregadoras vs. trabalhadoras) e indicadores de desigualdade de classe e raça?**

- **Fontes:** `br_me_rais.microdados_vinculos`, `br_bd_diretorios_brasil.cbo_2002`, `br_ibge_pnadc.microdados`

**42. Como a violência doméstica (feminicídio) se relaciona com indicadores de desigualdade de gênero, participação política feminina e acesso a serviços de proteção?**

- **Fontes:** `br_rj_isp_estatisticas_seguranca.feminicidio_mensal_cisp`, `br_tse_eleicoes.candidatos`, `br_ms_cnes.estabelecimento`

---

## 13. Migrração, Urbanização e Transformações Espaciais

**43. Qual a relação entre fluxos migratórios municipais (saldos de emprego formal) e indicadores de crescimento econômico e demanda por serviços públicos?**

- **Fontes:** `br_me_caged.microdados_movimentacao`, `br_ibge_populacao.municipio`, `br_ibge_pib.municipio`

**44. Como a distribuição espacial de populações em territórios quilombolas e terras indígenas se correlaciona com indicadores de acesso a serviços básicos (saúde, educação, saneamento)?**

- **Fontes:** `br_ibge_censo_2022.terra_indigena`, `br_ibge_censo_2022.territorio_quilombola`, `br_ms_cnes.estabelecimento`, `br_inep_censo_escolar.escola`

---

## 14. Consumo, Preços e Estratificação de Classe

**45. Como a variação nos preços de combustíveis se transmite para os índices de preços ao consumidor (IPCA/INPC) em diferentes estratos de renda?**

- **Fontes:** `br_anp_precos_combustiveis.microdados`, `br_ibge_ipca.mes_categoria_municipio`, `br_ibge_inpc.mes_categoria_municipio`

**46. Qual a relação entre estrutura de consumo das famílias (Pesquisa de Orçamentos Familiares) e indicadores de insegurança alimentar nos municípios?**

- **Fontes:** `br_ibge_pof.dicionario`, `br_ms_sisvan.microdados`, `br_ibge_censo_demografico.setor_censitario_pessoa_renda_2010`

---

## 15. Poder, Elite e Reprodução Social

**47. Qual o perfil das elites econômicas e políticas brasileiras? Existe sobreposição entre elites econômicas, políticas e familiares nos cargos de poder?**

- **Fontes:** `br_tse_eleicoes.candidatos`, `br_camara_dados_abertos.deputado_profissao`, `br_me_rais.microdados_estabelecimentos`, `br_me_cnpj.socios`

**48. Qual a relação entre origem social dos parlamentares (renda, escolaridade, ocupação prévia) e suas proposições legislativas e votações?**

- **Fontes:** `br_camara_dados_abertos.deputado`, `br_camara_dados_abertos.deputado_profissao`, `br_camara_dados_abertos.proposicao_tema`, `br_camara_dados_abertos.votacao_parlamentar`

**49. Como a filiação partidária e a origem regional dos candidatos se relacionam com suas chances de eleição e acesso a recursos públicos?**

- **Fontes:** `br_tse_filiacao_partidaria.microdados`, `br_tse_eleicoes.candidatos`, `br_tse_eleicoes.resultados_candidato`, `br_cgu_emendas_parlamentares.microdados`

---

## 16. Economia Política e Desenvolvimento

**50. Qual a relação entre a estrutura tributária municipal (arrecadação por tipo de imposto) e os níveis de desigualdade e investimento em serviços públicos?**

- **Fontes:** `br_rf_arrecadacao.uf`, `br_me_siconfi.municipio_receitas_orcamentarias`, `br_me_siconfi.municipio_despesas_funcao`, `br_ibge_pib.gini`

---

## Notas Metodológicas

1. **Cruzamento de bases:** A maioria das perguntas requer join entre múltiplas tabelas usando identificadores geográficos (`id_municipio`, `sigla_uf`) ou temporais (`ano`, `mes`).

2. **Unidades de análise:** As perguntas contemplam análises em múltiplos níveis: indivíduo (microdados de censos, PNAD, RAIS), domicílio, setor censitário, município, mesorregião, estado e região.

3. **Variáveis de controle sugeridas:** Para análises multivariadas, recomenda-se controlar por: PIB per capita, índice de Gini, taxa de urbanização, proporção de população rural, indicadores de infraestrutura.

4. **Temporalidade:** Os dados variam de 1970 a 2023, permitindo análises longitudinais e comparativas entre períodos.
