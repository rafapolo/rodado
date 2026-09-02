# Datasets com dado de município que o dashboard `dataviz/municipio` ainda não usa

Levantamento de 2026-08-28: dos 111 datasets do espelho que têm pelo menos uma
tabela com coluna de município (`docs/context/basedosdados-schema.json`, busca
por `municip` no nome da coluna), `dataviz/municipio/extract_municipio.py`
(repo `xn--2dk.xyz` / `xyz`, não este) usa 62. Os 53 abaixo não entraram —
triados em três baldes pra decidir depois quais valem uma seção nova. Nenhum
destes foi verificado com query real no beelink; são hipóteses de escopo a
partir do nome das tabelas e colunas, pra guiar a próxima rodada de decisão,
não pra implementar direto.

## Balde A — gap real, provável de valer a pena

- `br_ms_sia` (`producao_ambulatorial`, `psicossocial`) — produção ambulatorial do SUS; complemento natural do SIH (internação) que já está no dashboard.
- `br_ms_atencao_basica` (`municipio`) — cobertura de atenção básica/ESF; hoje o dashboard só tem CNES (estrutura) e agravos pontuais, nada sobre cobertura de saúde da família.
- `br_transferegov` (`transferencias`, `programas`, `planos_acao`) — repasses federais a convênios/planos de ação, além das emendas parlamentares já cobertas.
- `br_tcu_inidoneos` (`empresas`, `inabilitados_funcao_publica`, ...) — empresas e pessoas inabilitadas para contratar com o poder público; complementa a seção de transparência com um ângulo de integridade.
- `br_tse_filiacao_partidaria` (`microdados`) — filiação partidária por município; complementa a seção de política, que hoje só tem eleitorado e resultado.
- `br_comprasgov_sicaf` (`fornecedores`) — fornecedores cadastrados no SICAF sediados no município; complementa CNPJ/licitação.
- `br_bndes_operacoes_contratadas` (`operacoes_nao_automaticas`) — financiamentos do BNDES contratados no município.
- `br_cgu_pe_de_meia` (`pe_de_meia`) — programa de transferência a estudantes do ensino médio (2024+); mesma família de `bolsa_familia`/`bpc` já cobertos em `beneficios`.
- `br_cgu_seguro_defeso` (`seguro_defeso`) — seguro-defeso a pescadores artesanais; mesma família de benefícios sociais.
- `br_ibge_ipca` / `br_ibge_ipca15` (`mes_categoria_municipio`) — inflação por categoria **no município**, não só o INPC nacional que já está em `economia`. Cobertura limitada às ~16 cidades onde o IBGE coleta preços (capitais + poucas outras) — checar se Nova Friburgo tem dado antes de prometer a seção.

## Balde B — relevante, mas com escopo geográfico estreito (não aparece pra toda cidade)

- `br_tce_es`, `br_tce_pi`, `br_tce_sp` — dados de tribunais de contas estaduais; só existem para município do ES/PI/SP respectivamente, então uma seção "genérica" mostraria vazio pra ~89% dos municípios do país.
- `br_trase_supply_chain` (`soy_beans*`, `beef*`) — rastreabilidade de cadeia de soja/boi; só tem dado real pra município de fronteira agrícola.
- `br_ibama_embargos` — embargos ambientais; concentrado em município de desmatamento/Amazônia Legal. Nota: `datasets_coverage_gaps.md` já registrou que as 8 tabelas deste dataset têm 100% das colunas vazias em pelo menos um teste (2026-08-25) — checar se ainda está quebrado antes de investir tempo aqui.
- `br_ana_outorgas` (`captacoes`, `lancamentos`) — outorgas de uso de água; só relevante pra município com corpo d'água outorgado. O projeto já tem conhecimento verificado sobre este dataset (ver memória `reference_outorgas_snirh` / `bridges.yaml`), então o custo de adicionar é baixo mesmo sendo de cobertura parcial.
- `br_ana_telemetria` (`estacoes`, `series_chuva_*`, `series_cota_*`) — séries de chuva/nível de rio por estação telemétrica; só município com estação ANA por perto.
- `br_cnpq_bolsas` (`microdados`) — bolsas CNPq por município de destino; concentrado em município com instituição de pesquisa.
- `br_sfb_sicar` (`area_imovel`) — Cadastro Ambiental Rural; mais relevante pra município rural/agropecuário.
- `br_ibge_pevs` (`producao_extracao_vegetal`, `producao_silvicultura`) — produção de extrativismo vegetal e silvicultura; só município com essa atividade.
- `world_wb_mides` (`licitacao`, `empenho`, `liquidacao`) — execução orçamentária por município apesar do prefixo `world_`; parece ligado a um programa financiado pelo Banco Mundial, cobertura provavelmente restrita aos municípios participantes desse programa — checar antes de assumir.

## Balde C — baixa prioridade, niche ou registro administrativo sem grão cívico

- `br_anp_precos_combustiveis` (`microdados`) — parece duplicar `br_anp_combustiveis.precos`, que já está no dashboard; checar se são o mesmo dado antes de somar.
- `br_anvisa_medicamentos_industrializados` — fabricantes de medicamento registrados por município; só relevante pra município com planta farmacêutica.
- `br_bcb_sicor` (`operacao`, `empreendimento`, ...) — operações de crédito rural por instituição financeira; nicho, mais dado de mercado financeiro que perfil municipal.
- `br_cvm_administradores_carteira` — administradores de carteira registrados na CVM; registro profissional, não indicador do município.
- `br_rf_cafir` (`imoveis_rurais`) — Cadastro de Imóveis Rurais da Receita; `datasets_coverage_gaps.md` já registrou 61-64% das linhas sem id em todo snapshot (achado de 2026-08-25) — dado corrompido conhecido, não vale investir sem re-checar a fonte.
- `br_rf_cno` (`microdados`, `vinculos`, `areas`, `cnaes`) — Cadastro Nacional de Obras; nicho, mais dado de fiscalização trabalhista em obra que perfil municipal.
- `br_rf_arrecadacao` (`ir_ipi`, `itr`, ...) — arrecadação federal, mas tabelas parecem ser por UF/CNAE, não por município — checar grão antes de assumir que serve.
- `br_ibge_amc` (`municipio_de_para`) — crosswalk de códigos de município ao longo do tempo (municípios que se desmembraram); é metadado de correspondência, não dado sobre o município em si.
- `br_ibge_nomes_brasil` (`quantidade_municipio_nome_2010`) — nomes de bebês por município, censo 2010; curiosidade demográfica, não indicador.
- `br_ibge_censo2022_raca` (`fecundidade_idade`, `instrucao`) — parece sobreposto ao que `censo_extra`/`demografia` já cobrem do censo 2022; checar antes de duplicar.
- `br_ibge_censo_demografico` (`microdados_domicilio_1970` … `2010`) — censos históricos pré-2022; dado rico mas trabalho pesado (33 tabelas, microdados de domicílio) pra uma seção "perfil atual" — mais adequado a uma seção de série histórica futura, se um dia o dashboard ganhar visão temporal longa.
- `br_ibge_pnadc` (`ano_municipio_raca_cor`, `ano_municipio_grupo_idade`) — PNAD Contínua parece ter uma agregação por município (`id_municipio`, `populacao`, `raca_cor`/`grupo_idade`), o que contraria a suposição inicial de que PNAD é só amostral sem grão municipal — vale conferir o que exatamente essa agregação representa antes de descartar.
- `br_inep_ana`, `br_inep_avaliacao_alfabetizacao`, `br_inep_censo_educacao_superior`, `br_inep_educacao_especial`, `br_inep_indicador_nivel_socioeconomico`, `br_inep_sinopse_estatistica_educacao_basica` — tabelas INEP adicionais (alfabetização, educação especial, nível socioeconômico, ensino superior); o núcleo forte (IDEB/SAEB/ENEM/censo_escolar/SISU) já está coberto, estas são complementares, não um buraco óbvio.
- `br_inmet_bdmep` (`estacao`, `microdados`) — dados meteorológicos por estação INMET; só município com estação por perto, e é clima, não indicador socioeconômico.
- `br_ipea_acesso_oportunidades` (`estatisticas_2019`) — índice de acesso a oportunidades urbanas (empregos, serviços por transporte); dado único de 2019, sem série.
- `br_mobilidados_indicadores` — indicadores de mobilidade urbana; provavelmente só grandes cidades têm cobertura real.
- `br_ms_populacao` (`municipio`) — provavelmente duplica `br_ibge_populacao`, que já está no dashboard; checar se é a mesma série antes de somar.
- `br_ms_vacinacao_covid19` (`microdados_estabelecimento`) — vacinação covid por estabelecimento; dado histórico de um evento específico, não indicador contínuo.
- `br_mjsp_sisdepen` (`populacao_carceraria`) — população carcerária; o projeto já tem conhecimento verificado deste dataset (`bridges.yaml`, correção de formato feita nesta mesma sessão), custo de adicionar é baixo.
- `br_poder360_pesquisas` (`microdados`) — pesquisas eleitorais; dado de opinião, não indicador do município.
- `br_simet_educacao_conectada` (`escola`) — conectividade de escola; sobrepõe parcialmente `conectividade`/`educacao` já existentes.
- `br_cgu_dados_abertos` (`conjunto`, `organizacao`, `recurso`) — metadado do portal de dados abertos, não dado sobre o município.
- `br_cgu_fef` (`microdados`, `municipios_sorteados`, `sorteio`) — Fundo de Fiscalização de sorteio da CGU; nicho, cobertura por sorteio, não sistemática.
- `br_cgu_garantia_safra` — já tem bridge documentado e é da mesma família de benefícios, mas não é usado ainda; baixa prioridade só porque `bolsa_familia`/`bpc` já cobrem o essencial de `beneficios`.
- `world_oecd_public_finance` (`country`) — grão é país, não município; entrou na varredura por falso positivo (não tem coluna de município real) — descartar da lista de pendências.

## Como decidir depois

Pra promover um item do Balde A/B pra uma seção real: `mcp__rodado__describe_table`
+ uma query real no beelink pra confirmar que Nova Friburgo (`id_municipio`
`3303401`) tem dado não-nulo, antes de prometer a seção no dashboard — vários
destes datasets têm bugs conhecidos e catalogados (`br_rf_cafir`,
`br_ibama_embargos`) que só apareceram ao tentar de fato.
