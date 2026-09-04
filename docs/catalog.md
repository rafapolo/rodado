# docs/catalog.md — catálogo de datasets

**Gerado por `scripts/gera_catalog_md.py`, a partir de `_rodado_metadata/catalog.parquet` — não editar à mão.** Descrições vêm de `docs/context/dataset_descriptions.yaml`; editar lá e regenerar (`build_metadata_catalog.py` → `gera_catalog_md.py`), nunca este arquivo.

**233 datasets, 1.029 tabelas, 39.245.598.931 linhas.**

| Dataset | Descrição | Tabelas | Linhas | Fonte |
|---|---|---:|---:|---|
| `_local_rais_cnpj` | RAIS de estabelecimentos cruzada com CNPJ, 2010-2021 | 1 | 40.626.223 | Base dos Dados |
| `br_abrinq_oca` | Observatório da Criança e do Adolescente (Fundação Abrinq) — indicadores de primeira infância por município | 1 | 55.700 | Base dos Dados |
| `br_ana_atlas_esgotos` | Atlas Esgotos da ANA — diagnóstico de coleta e tratamento de esgoto por município | 1 | 5.570 | Base dos Dados |
| `br_ana_bho` | Base Hidrográfica Ottocodificada da ANA — topologia de trechos de rio | 1 | 462.539 | ANA Base Hidrográfica Ottocodificada (topologia) |
| `br_ana_outorgas` | Outorgas de uso da água (captação e lançamento) da ANA | 2 | 192.772 | ANA outorgas de uso da água |
| `br_ana_reservatorios` | Reservatórios do Sistema Integrado Nacional monitorados pela ANA | 1 | 1.157.621 | Base dos Dados |
| `br_ana_telemetria` | Telemetria da ANA — séries de vazão, cota e chuva de estações de monitoramento de rios | 13 | 165.625.437 | ANA telemetria (rios/chuva) |
| `br_anac_dadosabertos` | ANAC — registro de aeronaves, voos e pontualidade | 3 | 129.666 | ANAC |
| `br_anatel_banda_larga_fixa` | Densidade de acessos de banda larga fixa por município/UF (Anatel) | 4 | 58.902.377 | Base dos Dados |
| `br_anatel_indice_brasileiro_conectividade` | Índice Brasileiro de Conectividade por município (Anatel) | 1 | 22.280 | Base dos Dados |
| `br_aneel_dadosabertos` | ANEEL — empreendimentos de geração distribuída (mini/microgeração solar, eólica etc.) | 1 | 4.692.466 | ANEEL — geração distribuída (empreendimentos) |
| `br_anm` | ANM/SIGMINE — processos minerários, CFEM (royalties de mineração) e licenciamento | 22 | 8.324.108 | ANM / SIGMINE — títulos minerários e CFEM |
| `br_anp_combustiveis` | ANP — preços de combustíveis por posto/revenda | 1 | 2.006.614 | ANP combustíveis (preços revenda/distribuição) |
| `br_anp_precos_combustiveis` | ANP — preços de combustíveis pesquisados (via Base dos Dados) | 1 | 16.409.523 | Base dos Dados |
| `br_ans_beneficiario` | ANS — beneficiários de planos de saúde suplementar | 1 | 2.307.338.481 | Base dos Dados |
| `br_anvisa_cmed` | CMED/ANVISA — preços regulados de medicamentos | 1 | 51.140 | CMED (preços de medicamentos, ANVISA) |
| `br_anvisa_consultas` | ANVISA — registros de agrotóxicos, alimentos e produtos regulados | 3 | 101.938 | ANVISA (consulta completa) |
| `br_anvisa_medicamentos_industrializados` | ANVISA — medicamentos industrializados registrados | 1 | 10.000.000 | Base dos Dados |
| `br_ba_feiradesantana_camara_leis` | Câmara Municipal de Feira de Santana — leis municipais | 1 | 6.033 | Base dos Dados |
| `br_bcb_desenrola` | BCB — programa Desenrola Brasil (renegociação de dívidas de pessoa física) | 1 | 12.751 | BCB Desenrola Brasil |
| `br_bcb_estban` | BCB ESTBAN — estatísticas bancárias por agência/município | 3 | 699.984.822 | Base dos Dados |
| `br_bcb_ifdata` | BCB IF.data — indicadores financeiros de instituições financeiras | 3 | 488.982 | Base dos Dados |
| `br_bcb_penalidades` | BCB — penalidades aplicadas a instituições financeiras | 1 | 16.822 | BCB Penalties |
| `br_bcb_pix_municipio` | BCB — volume de transações Pix por município, separado por perfil pagador/recebedor PF/PJ | 1 | 395.447 | BCB — Estatísticas do Pix por município |
| `br_bcb_scrdata` | BCB SCR.data — carteira de crédito do Sistema de Informações de Crédito | 1 | 43.061.984 | BCB SCR.data |
| `br_bcb_sgs` | BCB SGS — séries temporais macroeconômicas (câmbio, Selic, inflação etc.) | 1 | 25.066 | BACEN/BCB SGS séries |
| `br_bcb_sicor` | BCB SICOR — operações de crédito rural | 11 | 759.657.502 | Base dos Dados |
| `br_bd_diretorios_brasil` | Base dos Dados — diretórios de referência (CEP, CNAE, CID, município etc.) | 23 | 1.951.703 | Base dos Dados |
| `br_bd_diretorios_data_tempo` | Base dos Dados — diretório de calendário/tempo | 11 | 1.922.812 | Base dos Dados |
| `br_bd_diretorios_mundo` | Base dos Dados — diretórios internacionais (país, NCM, sistema harmonizado) | 4 | 20.648 | Base dos Dados |
| `br_bd_diretorios_us` | Base dos Dados — diretórios de referência dos EUA | 11 | 267.721 | Base dos Dados |
| `br_bd_metadados` | Base dos Dados — metadados do próprio catálogo original (tabelas, organizações) | 7 | 123.379 | Base dos Dados |
| `br_bd_vizinhanca` | Base dos Dados — vizinhança geográfica de municípios e UFs | 2 | 523.926 | Base dos Dados |
| `br_bndes_operacoes_contratadas` | BNDES — operações de crédito contratadas | 3 | 2.405.142 | Base dos Dados |
| `br_brasilapi` | BrasilAPI — bancos, DDDs, feriados nacionais, taxas de referência | 4 | 6.149 | BrasilAPI |
| `br_brasilio_holdings` | Brasil.IO — estrutura societária de holdings empresariais | 1 | 515.191 | Brasil.IO holdings |
| `br_caixa_sinapi` | SINAPI/Caixa — custos e insumos de construção civil | 1 | 1.962.674 | SINAPI (custos/insumos de construção civil) |
| `br_caixa_sorteios` | Caixa Econômica — resultados da Mega-Sena | 1 | 15.294 | Base dos Dados |
| `br_camara_dados_abertos` | Câmara dos Deputados — deputados, votações, despesas, licitações internas | 30 | 14.361.616 | Base dos Dados |
| `br_capes_bolsas` | CAPES — bolsas de mobilidade acadêmica internacional | 1 | 146.036 | Base dos Dados |
| `br_ce_fortaleza_sefin_iptu` | Prefeitura de Fortaleza — cadastro de IPTU por face de quadra | 1 | 68.932 | Base dos Dados |
| `br_cgu_beneficios_cidadao` | CGU — benefícios sociais federais (Bolsa Família, Auxílio Emergencial, BPC etc.) | 11 | 6.609.906.509 | Base dos Dados |
| `br_cgu_cartao_pagamento` | CGU — gastos com cartão de pagamento do governo federal | 4 | 3.075.035 | Base dos Dados |
| `br_cgu_dados_abertos` | CGU — catálogo de dados abertos do governo federal | 3 | 89.771 | Base dos Dados |
| `br_cgu_ebt` | CGU — Escala Brasil Transparente (municípios e UFs) | 2 | 1.384 | Base dos Dados |
| `br_cgu_emendas_parlamentares` | CGU — emendas parlamentares ao orçamento federal | 1 | 88.991 | Base dos Dados |
| `br_cgu_fef` | CGU — Fundo de Erradicação da Pobreza e sorteios de fiscalização | 3 | 84.945 | Base dos Dados |
| `br_cgu_garantia_safra` | Garantia-Safra — pagamentos aos agricultores familiares do semiárido | 1 | 33.522.915 | Portal - Garantia-Safra |
| `br_cgu_gas_do_povo` | Gás do Povo — pagamentos do benefício de gás de cozinha | 1 | 20.817.231 | Gás do Povo (CGU) |
| `br_cgu_licitacao_contrato` | CGU — licitações e contratos do governo federal | 8 | 100.105.069 | Base dos Dados |
| `br_cgu_novo_bolsa_familia` | Novo Bolsa Família — pagamentos mensais por beneficiário | 1 | 821.346.847 | Novo Bolsa Família (CGU) |
| `br_cgu_orcamento_publico` | CGU — execução do orçamento público federal | 1 | 289.426 | Base dos Dados |
| `br_cgu_pe_de_meia` | Pé-de-Meia — pagamentos do programa de incentivo à permanência escolar | 1 | 64.047.519 | Portal - Pe-de-Meia |
| `br_cgu_pessoal_executivo_federal` | CGU — terceirizados do Poder Executivo federal | 1 | 732.269 | Base dos Dados |
| `br_cgu_receitas_publicas` | CGU — receitas públicas federais | 1 | 1.529.345 | Base dos Dados |
| `br_cgu_sancoes` | CGU — sanções administrativas (CEIS, CNEP, CEPIM, acordos de leniência) | 6 | 24.551 | Base dos Dados |
| `br_cgu_seguro_defeso` | Seguro-Defeso — pagamentos aos pescadores artesanais durante o defeso | 1 | 42.088.721 | Portal - Seguro-Defeso |
| `br_cgu_servidores_executivo_federal` | CGU — cadastro e remuneração de servidores do Poder Executivo federal | 14 | 852.909.944 | Base dos Dados |
| `br_cgu_viagens` | CGU — viagens a serviço de servidores federais | 4 | 52.617.461 | Portal - Viagens |
| `br_clp_ranking_competitividade` | CLP — ranking de competitividade dos estados | 2 | 9.431 | Base dos Dados |
| `br_cnj_estatisticas_poder_judiciario` | CNJ — recursos financeiros do Poder Judiciário | 1 | 1.189 | Base dos Dados |
| `br_cnj_improbidade_administrativa` | CNJ — condenações por improbidade administrativa | 1 | 53.342 | Base dos Dados |
| `br_cnpq_bolsas` | CNPq — bolsas de pesquisa concedidas | 2 | 2.839.807 | Base dos Dados |
| `br_comprasgov_catmatcatser` | ComprasGov — catálogo de materiais e serviços padronizados (CATMAT/CATSER) | 2 | 250.875 | CATMAT/CATSER (catálogo de materiais/serviços) |
| `br_comprasgov_sicaf` | SICAF — cadastro de fornecedores habilitados a contratar com o governo | 1 | 957.885 | SICAF fornecedores |
| `br_cvm_administradores_carteira` | CVM — administradores de carteira de valores mobiliários | 3 | 16.126 | Base dos Dados |
| `br_cvm_fundos` | CVM — cadastro de fundos de investimento | 1 | 46.809 | CVM Fundos |
| `br_cvm_oferta_publica_distribuicao` | CVM — ofertas públicas de distribuição de valores mobiliários | 1 | 27.486 | Base dos Dados |
| `br_datahackers_state_data` | Data Hackers — pesquisa State of Data sobre o mercado de dados no Brasil | 1 | 4.271 | Base dos Dados |
| `br_datasus_cid10` | DATASUS — tabela de códigos CID-10 e CID-O | 6 | 15.672 | CID-10 (tabela de códigos, DATASUS) |
| `br_fbsp_absp` | Fórum Brasileiro de Segurança Pública — violência nas escolas | 3 | 2.484 | Base dos Dados |
| `br_fgv_igp` | FGV — índices de preços (IGP-M, IGP-DI e variantes) | 7 | 2.536 | Base dos Dados |
| `br_fipe_veiculos` | FIPE — tabela de preços de referência de veículos | 1 | 11.289 | FIPE veículos |
| `br_firjan_ifgf` | FIRJAN — Índice de Gestão Fiscal municipal | 1 | 55.680 | Base dos Dados |
| `br_geobr_mapas` | geobr — malhas geográficas oficiais do IBGE (municípios, UFs, biomas, terras indígenas etc.) | 25 | 984.345 | Base dos Dados |
| `br_ggb_relatorio_lgbtqi` | Grupo Gay da Bahia — relatório de mortes de pessoas LGBTQI+ | 5 | 145 | Base dos Dados |
| `br_ibama_autos` | IBAMA — autos de infração ambiental | 8 | 3.021.141 | IBAMA — autos de infração |
| `br_ibama_ctf` | IBAMA — Cadastro Técnico Federal de atividades potencialmente poluidoras | 2 | 1.473.755 | IBAMA — CTF/APP (atividades potencialmente poluidoras) |
| `br_ibama_embargos_novo` | IBAMA — termos de embargo ambiental | 8 | 892.279 | IBAMA — termos de embargo (re-raspagem) |
| `br_ibge_amc` | IBGE — correspondência de áreas mínimas comparáveis entre municípios ao longo do tempo | 1 | 434.070 | Base dos Dados |
| `br_ibge_cbo_2002` | IBGE — Classificação Brasileira de Ocupações 2002 | 2 | 177.556 | Base dos Dados |
| `br_ibge_censo2022_raca` | IBGE Censo 2022 — cor/raça cruzada com instrução e fecundidade, por município | 2 | 1.415.034 | Censo 2022 — Cor ou raça × instrução/fecundidade |
| `br_ibge_censo2022_religiao` | IBGE Censo 2022 — religião e recortes demográficos associados | 15 | 6.451.488 | Censo 2022 — Religião (pacote completo) |
| `br_ibge_censo_2022` | IBGE — Censo Demográfico 2022, agregados por setor censitário e município | 16 | 138.805.409 | Base dos Dados |
| `br_ibge_censo_demografico` | IBGE — microdados dos Censos Demográficos 1970 a 2010 | 33 | 145.684.505 | Base dos Dados |
| `br_ibge_cnefe` | IBGE — Cadastro Nacional de Endereços para Fins Estatísticos, Censo 2022 (endereço a endereço) | 1 | 111.102.875 | CNEFE Censo 2022 (microdado completo) |
| `br_ibge_estadic` | IBGE — Pesquisa de Informações Básicas Estaduais (ESTADIC) | 8 | 3.044 | Base dos Dados |
| `br_ibge_inpc` | IBGE — Índice Nacional de Preços ao Consumidor | 4 | 608.478 | Base dos Dados |
| `br_ibge_ipca` | IBGE — Índice de Preços ao Consumidor Amplo | 4 | 622.069 | Base dos Dados |
| `br_ibge_ipca15` | IBGE — IPCA-15, prévia mensal do IPCA | 4 | 359.690 | Base dos Dados |
| `br_ibge_ipp` | IBGE — Índice de Preços ao Produtor | 6 | 5.118 | Base dos Dados |
| `br_ibge_munic` | IBGE — Pesquisa de Informações Básicas Municipais (MUNIC) | 7 | 852.056 | Base dos Dados |
| `br_ibge_nomes_brasil` | IBGE — frequência de nomes de pessoas por município, Censo 2010 | 1 | 1.959.116 | Base dos Dados |
| `br_ibge_pam` | IBGE — Produção Agrícola Municipal, lavouras permanentes e temporárias | 2 | 20.097.187 | Base dos Dados |
| `br_ibge_pevs` | IBGE — Produção da Extração Vegetal e da Silvicultura | 2 | 558.451 | Base dos Dados |
| `br_ibge_pib` | IBGE — PIB municipal e estadual | 7 | 190.805 | Base dos Dados |
| `br_ibge_pnad` | IBGE — PNAD, microdados compatibilizados históricos | 3 | 9.587.801 | Base dos Dados |
| `br_ibge_pnad_covid` | IBGE — PNAD-COVID19, dicionário de variáveis | 1 | 554 | Base dos Dados |
| `br_ibge_pnadc` | IBGE — PNAD Contínua, mercado de trabalho e rendimento | 14 | 31.529.302 | Base dos Dados |
| `br_ibge_pof` | IBGE — Pesquisa de Orçamentos Familiares | 14 | 2.238.882 | Base dos Dados |
| `br_ibge_populacao` | IBGE — estimativas populacionais por município, UF e Brasil | 3 | 192.080 | Base dos Dados |
| `br_ibge_ppm` | IBGE — Pesquisa Pecuária Municipal (rebanhos, aquicultura, produção animal) | 4 | 2.455.095 | Base dos Dados |
| `br_ieps_saude` | IEPS — indicadores de saúde por município e região de saúde | 5 | 73.980 | Base dos Dados |
| `br_inea_boletim` | INEA-RJ — boletins de serviço de licenciamento ambiental, atos e texto extraído dos PDFs | 5 | 24.743 | INEA — boletins de serviço, texto dos PDFs (validade/condicionantes) |
| `br_inep_ana` | INEP — Avaliação Nacional da Alfabetização | 3 | 98.778 | Base dos Dados |
| `br_inep_avaliacao_alfabetizacao` | INEP — avaliação da alfabetização e metas por município/UF | 7 | 3.902.954 | Base dos Dados |
| `br_inep_censo_educacao_superior` | INEP — Censo da Educação Superior | 3 | 3.891.339 | Base dos Dados |
| `br_inep_censo_escolar` | INEP — Censo Escolar, escolas e turmas | 3 | 43.155.409 | Base dos Dados |
| `br_inep_educacao_especial` | INEP — indicadores de educação especial/inclusiva | 15 | 12.213.008 | Base dos Dados |
| `br_inep_enem` | INEP — microdados do ENEM | 28 | 216.277.169 | Base dos Dados |
| `br_inep_formacao_docente` | INEP — formação de docentes da educação básica | 4 | 164.105 | Base dos Dados |
| `br_inep_ideb` | INEP — Índice de Desenvolvimento da Educação Básica | 5 | 1.492.158 | Base dos Dados |
| `br_inep_indicador_nivel_socioeconomico` | INEP — indicador de nível socioeconômico das escolas | 5 | 528.410 | Base dos Dados |
| `br_inep_indicadores_educacionais` | INEP — indicadores educacionais (transição de etapa, remuneração docente) | 12 | 5.135.062 | Base dos Dados |
| `br_inep_saeb` | INEP — SAEB, proficiência de alunos por etapa/disciplina | 11 | 200.886.659 | Base dos Dados |
| `br_inep_sinopse_estatistica_educacao_basica` | INEP — sinopse estatística da educação básica | 18 | 114.748.803 | Base dos Dados |
| `br_inmet_bdmep` | INMET — Banco de Dados Meteorológicos, séries por estação | 2 | 84.515.289 | Base dos Dados |
| `br_inpe_deter` | INPE DETER — alertas quase em tempo real de desmatamento | 1 | 686.136 | INPE DETER (avisos de desmatamento) |
| `br_inpe_prodes` | INPE PRODES — desmatamento anual agregado por município e bioma | 1 | 156.864 | Base dos Dados |
| `br_inpe_prodes_acumulado` | INPE PRODES — polígonos de desmatamento acumulado por bioma, geometria em centroide | 1 | 7.598.548 | INPE PRODES acumulado (desmatamento por bioma) |
| `br_inpe_queimadas` | INPE — focos de queimada detectados por satélite | 1 | 17.812.710 | Base dos Dados |
| `br_inpe_sisam` | INPE SISAM — qualidade do ar | 1 | 158.705.816 | Base dos Dados |
| `br_ipea_acesso_oportunidades` | IPEA — acesso a oportunidades urbanas (empregos, serviços) por tempo de deslocamento | 1 | 336.427 | Base dos Dados |
| `br_ipea_atlasviolencia` | IPEA — Atlas da Violência, indicadores de homicídio e letalidade | 2 | 3.006 | Atlas da Violência (IPEA) |
| `br_ipea_avs` | IPEA — Atlas da Vulnerabilidade Social | 1 | 319.681 | Base dos Dados |
| `br_mapbiomas_estatisticas` | MapBiomas — estatísticas de cobertura e transição de uso do solo | 6 | 1.219.409 | Base dos Dados |
| `br_mc_indicadores` | Ministério das Cidades — transferências a municípios | 1 | 1.118.855 | Base dos Dados |
| `br_mdr_snis` | SNIS/MDR — indicadores de água e esgoto por município e prestador de serviço | 2 | 245.101 | Base dos Dados |
| `br_me_caged` | Ministério do Trabalho — CAGED, movimentação de empregos formais (admissões/demissões) | 4 | 240.703.713 | Base dos Dados |
| `br_me_clima_organizacional` | Ministério da Economia — pesquisa de clima organizacional no serviço público | 1 | 16.436 | Base dos Dados |
| `br_me_cno` | Cadastro Nacional de Obras (CNO) — obras e vínculos de trabalhadores da construção | 3 | 1.020.894 | Base dos Dados |
| `br_me_cnpj` | Receita Federal — cadastro completo de empresas, estabelecimentos, sócios e Simples Nacional | 5 | 6.039.639.816 | Base dos Dados |
| `br_me_comex_stat` | Comex Stat — exportação e importação por município e NCM | 5 | 129.489.938 | Base dos Dados |
| `br_me_estoque_divida_publica` | Tesouro Nacional — estoque da dívida pública federal | 1 | 124.419 | Base dos Dados |
| `br_me_exportadoras_importadoras` | dicionário de empresas exportadoras e importadoras | 1 | 3 | Base dos Dados |
| `br_me_rais` | RAIS — microdados de vínculos empregatícios e estabelecimentos | 3 | 2.317.177.294 | Base dos Dados |
| `br_me_rais_identificada` | RAIS — estabelecimentos com identificação não anonimizada | 1 | 36.161.488 | RAIS Estabelecimentos (identificada) |
| `br_me_siape` | SIAPE — servidores do Poder Executivo federal | 1 | 358.869 | Base dos Dados |
| `br_me_sic` | SIC — Serviço de Informação ao Cidadão, pedidos de acesso à informação | 2 | 30.001 | Base dos Dados |
| `br_me_siconfi` | SICONFI — contas públicas de municípios, estados e União | 19 | 106.528.781 | Base dos Dados |
| `br_me_siorg` | SIORG — remuneração de cargos em comissão da administração federal | 1 | 258 | Base dos Dados |
| `br_mec_prouni` | MEC ProUni — dicionário de variáveis do programa | 1 | 20 | Base dos Dados |
| `br_mec_sisu` | MEC SISU — microdados de inscrição no Sistema de Seleção Unificada | 1 | 34.700.256 | Base dos Dados |
| `br_mg_belohorizonte_smfa_iptu` | Prefeitura de Belo Horizonte — cadastro de IPTU | 2 | 21.463.825 | Base dos Dados |
| `br_minc_salic` | MinC — SALIC/Lei Rouanet, projetos culturais incentivados | 8 | 839.316 | SALIC/Lei Rouanet (MinC) |
| `br_mj_consumidorgovbr` | Consumidor.gov.br — reclamações de consumidores contra empresas | 1 | 10.167.141 | Consumidor.gov.br |
| `br_mjsp_ckan` | MJSP — Procon (reclamações Sindec) e Infopen (censo penitenciário legado) | 2 | 13.803 | MJSP CKAN (broader) |
| `br_mjsp_procurados` | MJSP — lista de procurados do projeto Captura Nacional | 1 | 195 | Procurados (MJSP/Interpol) |
| `br_mjsp_sinesp` | SINESP — ocorrências registradas de segurança pública | 2 | 23.843 | SINESP/MJSP |
| `br_mjsp_sisdepen` | SISDEPEN — população carcerária por unidade prisional | 1 | 38.364 | MJSP SISDEPEN (população carcerária) |
| `br_mma_extincao` | MMA — listas oficiais de fauna e flora ameaçadas de extinção | 2 | 7.676 | Base dos Dados |
| `br_mme_consumo_energia_eletrica` | MME — consumo de energia elétrica por UF | 1 | 38.880 | Base dos Dados |
| `br_mobilidados_indicadores` | MobiliDados — indicadores de mobilidade urbana (transporte, ciclovia, acidentes) | 10 | 671.362 | Base dos Dados |
| `br_mp_pep` | Ministério do Planejamento — cargos e funções do Poder Executivo federal | 1 | 1.799.733 | Base dos Dados |
| `br_ms_atencao_basica` | Ministério da Saúde — indicadores de atenção básica por município | 1 | 901.944 | Base dos Dados |
| `br_ms_cnes` | CNES — Cadastro Nacional de Estabelecimentos de Saúde | 14 | 1.272.716.224 | Base dos Dados |
| `br_ms_imunizacoes` | Ministério da Saúde — cobertura vacinal por município | 1 | 149.124 | Base dos Dados |
| `br_ms_pns` | Ministério da Saúde — Pesquisa Nacional de Saúde | 3 | 521.059 | Base dos Dados |
| `br_ms_populacao` | Ministério da Saúde — estimativas populacionais por município | 1 | 4.919.222 | Base dos Dados |
| `br_ms_sia` | SIA/SUS — produção ambulatorial e psicossocial | 3 | 6.298.035.211 | Base dos Dados |
| `br_ms_sih` | SIH/SUS — Autorizações de Internação Hospitalar (AIH) | 3 | 2.619.388.412 | Base dos Dados |
| `br_ms_sim` | SIM — Sistema de Informações sobre Mortalidade | 3 | 31.376.032 | Base dos Dados |
| `br_ms_sinan` | SINAN — notificação compulsória de dengue e influenza/SRAG | 3 | 38.468.299 | Base dos Dados |
| `br_ms_sinan_chikungunya` | SINAN — notificação compulsória de chikungunya | 1 | 2.498.459 | Base dos Dados |
| `br_ms_sinan_esquistossomose` | SINAN — notificação compulsória de esquistossomose | 1 | 169.721 | SINAN Esquistossomose |
| `br_ms_sinan_febre_amarela` | SINAN — notificação compulsória de febre amarela | 1 | 39.517 | Base dos Dados |
| `br_ms_sinan_malaria` | SINAN — notificação compulsória de malária fora da Amazônia Legal | 1 | 68.320 | SINAN Malária (notificação fora da Amazônia Legal) |
| `br_ms_sinan_violencia` | SINAN — notificação compulsória de violência doméstica, sexual e outras | 1 | 4.939.266 | SINAN Violência (violência doméstica, sexual e/ou outras) |
| `br_ms_sinan_zika` | SINAN — notificação compulsória de zika | 1 | 605.045 | Base dos Dados |
| `br_ms_sinasc` | SINASC — Sistema de Informações sobre Nascidos Vivos | 2 | 85.559.448 | Base dos Dados |
| `br_ms_sipni_dicionarios` | SI-PNI — dicionários de cobertura vacinal | 4 | 224 | Base dos Dados |
| `br_ms_sipni_doses_historicas` | SI-PNI — doses de vacina aplicadas, série histórica agregada | 1 | 93.785.056 | Base dos Dados |
| `br_ms_sipni_microdados` | SI-PNI — microdados de vacinação individual (2020) | 1 | 102.423.524 | Base dos Dados |
| `br_ms_sisvan` | SISVAN — Sistema de Vigilância Alimentar e Nutricional | 2 | 406.253.847 | Base dos Dados |
| `br_ms_vacinacao_covid19` | Ministério da Saúde — vacinação contra covid-19 | 2 | 805.917 | Base dos Dados |
| `br_ok_queridodiario` | Querido Diário — metadados de diários oficiais municipais | 1 | 231.899 | Querido Diário |
| `br_ok_queridodiario_texto` | Querido Diário — texto integral das edições de diários oficiais municipais | 1 | 231.897 | Querido Diário — texto integral das edições |
| `br_pgfn_dividaativa` | PGFN — dívida ativa da União (tributária, FGTS, previdenciária) | 1 | 46.607.085 | PGFN |
| `br_pncp` | PNCP — Portal Nacional de Contratações Públicas, licitações e contratos de todos os entes | 1 | 5.043.371 | PNCP — Portal Nacional de Contratações Públicas |
| `br_poder360_pesquisas` | Poder360 — pesquisas eleitorais | 1 | 162.075 | Base dos Dados |
| `br_rf_arrecadacao` | Receita Federal — arrecadação tributária federal | 5 | 535.465 | Base dos Dados |
| `br_rf_cafir` | Receita Federal — Cadastro de Imóveis Rurais (CAFIR) | 2 | 169.935.565 | Base dos Dados |
| `br_rf_cno` | Receita Federal — Cadastro Nacional de Obras | 5 | 1.856.072.409 | Base dos Dados |
| `br_rf_dirpf` | Receita Federal — fundos habilitados e repasses via destinação de IRPF (FDCA/FDI) | 2 | 35.356 | Receita Federal — DIRPF repasses FDCA/FDI (valores) |
| `br_rj_isp_estatisticas_seguranca` | ISP-RJ — estatísticas de segurança pública do estado do Rio de Janeiro | 14 | 164.367 | Base dos Dados |
| `br_saude_bps` | Boletim de Pessoal da Saúde — dados de profissionais de saúde | 1 | 342.716 | BPS |
| `br_saude_farmaciapopular` | Farmácia Popular — estabelecimentos credenciados | 1 | 31.029 | Farmácia Popular |
| `br_sedec_desastres` | SEDEC/Defesa Civil — reconhecimentos vigentes de situação de emergência ou calamidade | 1 | 1.237 | Base dos Dados |
| `br_seeg_emissoes` | SEEG — emissões estimadas de gases de efeito estufa por município e setor | 3 | 183.668.150 | Base dos Dados |
| `br_senado_ceaps` | Senado Federal — Cota para Exercício da Atividade Parlamentar (CEAPS) | 1 | 393.521 | Senado CEAPS (cota parlamentar) |
| `br_senado_dados_abertos` | Senado Federal — senadores, votações, discursos, comissões | 18 | 619.782 | Base dos Dados |
| `br_senado_dados_abertos_administrativos` | Senado Federal — dados administrativos (CEAPS, remuneração de servidores) | 12 | 309.684 | Base dos Dados |
| `br_senado_dadosabertos` | Senado Federal — comissões, matérias, senadores e votações (fonte alternativa) | 4 | 166.049 | Senado (geral) |
| `br_sfb_sicar` | SICAR/SFB — Cadastro Ambiental Rural | 5 | 81.893.549 | Base dos Dados |
| `br_simet_educacao_conectada` | Programa Educação Conectada — conectividade de internet em escolas | 1 | 137.914 | Base dos Dados |
| `br_siop_orcamento` | SIOP — Sistema Integrado de Planejamento e Orçamento federal | 4 | 36.922 | SIOP |
| `br_sp_saopaulo_geosampa_iptu` | Prefeitura de São Paulo — cadastro de IPTU (GeoSampa) | 1 | 93.430.758 | Base dos Dados |
| `br_stf_corte_aberta` | STF — decisões do projeto Corte Aberta | 2 | 2.708.896 | Base dos Dados |
| `br_stj_dadosabertos` | STJ — documentos e decisões | 1 | 549.243 | STJ dados abertos |
| `br_tce_es` | TCE-ES — fiscalização de contas de municípios e do estado | 5 | 12.422 | TCE-ES |
| `br_tce_pi` | TCE-PI — despesas, licitações e receitas de municípios | 5 | 406 | TCE-PI |
| `br_tce_rj` | TCE-RJ — contratos, licitações, convênios e gastos com pessoal | 6 | 179.409 | TCE-RJ |
| `br_tce_sp` | TCE-SP — municípios fiscalizados | 1 | 644 | TCE-SP |
| `br_tce_to` | TCE-TO — pautas de julgamento | 1 | 50 | TCE-TO |
| `br_tcu_dadosabertos` | TCU — dados abertos gerais | 1 | 36.499 | TCU |
| `br_tcu_inidoneos` | TCU — empresas e responsáveis inidôneos ou inabilitados | 4 | 45.404 | TCU inidôneos e suspensos |
| `br_tesouro_capag` | Tesouro Nacional — Capacidade de Pagamento (CAPAG) de estados e municípios | 2 | 5.815 | CAPAG (capacidade de pagamento, entes SICONFI) |
| `br_tesouro_cauc` | Tesouro Transparente — CAUC, regularidade fiscal de estados e municípios | 3 | 5.674 | Tesouro Transparente — CAUC |
| `br_transferegov` | TransfereGov — planos de ação, programas e transferências (API normalizada) | 3 | 30.346 | TransfereGov |
| `br_transferegov_siconv` | TransfereGov/SICONV — convênios, contratos de repasse e execução física/financeira completa | 62 | 69.060.758 | Transferegov/SICONV completo |
| `br_trase_supply_chain` | Trase — cadeia de suprimentos de soja e carne bovina, do frigorífico/esmagadora à origem | 7 | 1.824.843 | Base dos Dados |
| `br_tse_eleicoes` | TSE — eleições 2026 (candidatos, votação, resultados, bens, receitas) | 23 | 1.514.381.653 | TSE ciclo de 2026 (em aberto) |
| `br_tse_filiacao_partidaria` | TSE — filiação partidária | 2 | 41.840.389 | Base dos Dados |
| `eu_sanctions` | União Europeia — lista de sanções | 1 | 42.347 | EU Sanctions |
| `global_ibge_tabua_mares` | IBGE — tábua de marés | 2 | 1.261.446 | Tábua de Marés |
| `global_icij_offshoreleaks` | ICIJ Offshore Leaks — empresas offshore, intermediários e beneficiários | 6 | 5.355.790 | ICIJ Offshore Leaks |
| `global_ofac_sanctions` | OFAC (EUA) — lista de sanções | 1 | 19.129 | OFAC |
| `global_opensanctions` | OpenSanctions — consolidado mundial de listas de sanções e PEP | 1 | 1.316.073 | OpenSanctions |
| `mundo_transfermarkt_competicoes` | Transfermarkt — Campeonato Brasileiro Série A e Copa do Brasil | 2 | 9.054 | Base dos Dados |
| `mundo_transfermarkt_competicoes_internacionais` | Transfermarkt — Champions League | 1 | 2.572 | Base dos Dados |
| `politicos` | Base dos Dados — contatos de políticos | 1 | 7.664 | Base dos Dados |
| `un_sanctions` | ONU — lista de sanções | 1 | 1.002 | UN Sanctions |
| `us_harvard_ned` | Harvard NED — eleições parlamentares e presidenciais internacionais | 2 | 6.309 | Base dos Dados |
| `world_ampas_oscar` | Oscar (AMPAS) — demografia de vencedores | 1 | 415 | Base dos Dados |
| `world_iea_pirls` | IEA PIRLS — avaliação internacional de leitura | 8 | 1.941.828 | Base dos Dados |
| `world_iea_timss` | IEA TIMSS — avaliação internacional de matemática e ciências | 11 | 1.929.595 | Base dos Dados |
| `world_imdb_movies` | IMDB — filmes mais bem avaliados por ano | 1 | 33.600 | Base dos Dados |
| `world_oecd_pisa` | OCDE PISA — avaliação internacional de estudantes | 1 | 1.745.082 | Base dos Dados |
| `world_oecd_public_finance` | OCDE — finanças públicas por país | 1 | 2.646 | Base dos Dados |
| `world_olympedia_olympics` | Olympedia — atletas e resultados olímpicos históricos | 6 | 482.195 | Base dos Dados |
| `world_sofascore_competicoes_futebol` | Sofascore — Campeonato Brasileiro Série A e Champions League | 2 | 11.324 | Base dos Dados |
| `world_wb_mides` | World Bank/MIDES — licitações e execução orçamentária (dataset internacional de referência) | 9 | 1.132.307.276 | Base dos Dados |
| `world_wwf_hydrosheds` | WWF HydroSHEDS — bacias, lagos e rios do mundo, dataset hidrográfico de referência | 3 | 15.119.487 | Base dos Dados |
