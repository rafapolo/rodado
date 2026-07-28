# Temas — que dados cada investigação usa

Os 43 temas do site e os datasets que cada um cita, 103 dos 195 do espelho.

> A origem é o markdown de `docs/overview/`: os datasets que o próprio
> texto de cada tema nomeia. Não é a lista completa do que a investigação
> tocou — é o que está registrado. Dataset sem citação não aparece.

Gerado por `scripts/gera_flow.py` a partir de `schemas.json` em 2026-07-28 — não
edite à mão, regenere.

- **nó** = dataset; **cápsula** = hub de referência;
- **seta cheia** (`-->`) = a chave está no dataset com o nome canônico, join direto;
- **seta pontilhada** (`-.->`) = a chave está com outro nome ou formato, normalize
  antes — receita em [`docs/context/join_keys.md`](docs/context/join_keys.md);
- os atributos (a lista de tabelas de cada dataset) ficaram de fora de propósito:
  é o que faz o mapa inteiro caber num diagrama só. Eles estão no [`ERD.md`](ERD.md).

```mermaid
flowchart LR
    subgraph hubs_territ_rio["Território"]
        direction TB
        MUNICIPIO(["MUNICIPIO"])
        UF(["UF"])
        SETOR_CENSITARIO(["SETOR_CENSITARIO"])
        CEP(["CEP"])
    end
    subgraph hubs_pessoas_e_empresas["Pessoas e empresas"]
        direction TB
        EMPRESA_CNPJ(["EMPRESA_CNPJ"])
        PESSOA_CPF(["PESSOA_CPF"])
        CNAE(["CNAE"])
        CBO(["CBO"])
    end
    subgraph hubs_equipamentos_p_blicos["Equipamentos públicos"]
        direction TB
        ESCOLA(["ESCOLA"])
        IES(["IES"])
        CNES(["CNES"])
        CID10(["CID10"])
    end
    subgraph hubs_estado_e_economia["Estado e economia"]
        direction TB
        ORGAO(["ORGAO"])
        UNIDADE_GESTORA(["UNIDADE_GESTORA"])
        FUNCAO_PROGRAMA(["FUNCAO_PROGRAMA"])
        PARTIDO(["PARTIDO"])
        NCM_SH(["NCM_SH"])
        PAIS(["PAIS"])
    end
    subgraph tema_01["01 · Desigualdade Racial"]
        direction TB
        t01_br_me_rais["me_rais"]
        t01_br_ms_sim["ms_sim"]
    end
    subgraph tema_02["02 · Educação"]
        direction TB
        t02_br_inep_enem["inep_enem"]
        t02_br_inep_ideb["inep_ideb"]
        t02_br_inep_indicador_nivel_socioeconomico["inep_indicador_nivel_socioeconomico"]
    end
    subgraph tema_03["03 · Saúde"]
        direction TB
        t03_br_cgu_beneficios_cidadao["cgu_beneficios_cidadao"]
        t03_br_ms_sim["ms_sim"]
        t03_br_ms_sinasc["ms_sinasc"]
    end
    subgraph tema_04["04 · Mercado de Trabalho"]
        direction TB
        t04_br_me_caged["me_caged"]
        t04_br_me_rais["me_rais"]
    end
    subgraph tema_05["05 · Política"]
        direction TB
        t05_br_camara_dados_abertos["camara_dados_abertos"]
        t05_br_senado_dadosabertos["senado_dadosabertos"]
        t05_br_tse_eleicoes["tse_eleicoes"]
    end
    subgraph tema_06["06 · Crime"]
        direction TB
        t06_br_ggb_relatorio_lgbtqi["ggb_relatorio_lgbtqi"]
        t06_br_mjsp_sisdepen["mjsp_sisdepen"]
        t06_br_ms_sim["ms_sim"]
        t06_br_rj_isp_estatisticas_seguranca["rj_isp_estatisticas_seguranca"]
    end
    subgraph tema_07["07 · Economia"]
        direction TB
        t07_br_bcb_estban["bcb_estban"]
        t07_br_bcb_sicor["bcb_sicor"]
        t07_br_ibge_pib["ibge_pib"]
    end
    subgraph tema_08["08 · Políticas Públicas"]
        direction TB
        t08_br_cgu_beneficios_cidadao["cgu_beneficios_cidadao"]
        t08_br_ibge_munic["ibge_munic"]
        t08_br_me_siconfi["me_siconfi"]
    end
    subgraph tema_09["09 · Gênero"]
        direction TB
        t09_br_me_caged["me_caged"]
        t09_br_ms_sinasc["ms_sinasc"]
    end
    subgraph tema_10["10 · Meio Ambiente"]
        direction TB
        t10_br_inpe_prodes["inpe_prodes"]
        t10_br_seeg_emissoes["seeg_emissoes"]
        t10_br_sfb_sicar["sfb_sicar"]
    end
    subgraph tema_11["11 · Infraestrutura"]
        direction TB
        t11_br_anatel_indice_brasileiro_conectividade["anatel_indice_brasileiro_conectividade"]
        t11_br_mdr_snis["mdr_snis"]
    end
    subgraph tema_12["12 · Interseccionalidade"]
        direction TB
        t12_br_me_rais["me_rais"]
        t12_br_ms_sinasc["ms_sinasc"]
    end
    subgraph tema_13["13 · Migração"]
        direction TB
        t13_br_me_caged["me_caged"]
    end
    subgraph tema_14["14 · Consumo"]
        direction TB
        t14_br_anp_combustiveis["anp_combustiveis"]
        t14_br_anp_precos_combustiveis["anp_precos_combustiveis"]
        t14_br_fgv_igp["fgv_igp"]
        t14_br_ibge_ipca["ibge_ipca"]
        t14_br_ibge_ipp["ibge_ipp"]
    end
    subgraph tema_15["15 · Poder"]
        direction TB
        t15_br_camara_dados_abertos["camara_dados_abertos"]
        t15_br_tse_eleicoes["tse_eleicoes"]
    end
    subgraph tema_16["16 · Economia Política"]
        direction TB
        t16_br_rf_arrecadacao["rf_arrecadacao"]
    end
    subgraph tema_17["17 · Agropecuária"]
        direction TB
        t17_br_bcb_sicor["bcb_sicor"]
        t17_br_ibge_ppm["ibge_ppm"]
        t17_br_sfb_sicar["sfb_sicar"]
        t17_br_trase_supply_chain["trase_supply_chain"]
    end
    subgraph tema_18["18 · Comércio Exterior"]
        direction TB
        t18_br_me_comex_stat["me_comex_stat"]
    end
    subgraph tema_19["19 · Mercado Financeiro"]
        direction TB
        t19_br_anatel_indice_brasileiro_conectividade["anatel_indice_brasileiro_conectividade"]
        t19_br_cnpq_bolsas["cnpq_bolsas"]
    end
    subgraph tema_20["20 · Ciência"]
        direction TB
        t20_br_cnpq_bolsas["cnpq_bolsas"]
        t20_br_inep_enem["inep_enem"]
    end
    subgraph tema_21["21 · Corrupção"]
        direction TB
        t21_br_cgu_cartao_pagamento["cgu_cartao_pagamento"]
        t21_br_cgu_emendas_parlamentares["cgu_emendas_parlamentares"]
        t21_br_cgu_licitacao_contrato["cgu_licitacao_contrato"]
        t21_br_rf_arrecadacao["rf_arrecadacao"]
    end
    subgraph tema_22["22 · Clima"]
        direction TB
        t22_br_inpe_prodes["inpe_prodes"]
        t22_br_seeg_emissoes["seeg_emissoes"]
        t22_br_sfb_sicar["sfb_sicar"]
    end
    subgraph tema_23["23 · Epidemiologia"]
        direction TB
        t23_br_ms_cnes["ms_cnes"]
        t23_br_ms_sim["ms_sim"]
        t23_br_ms_sinasc["ms_sinasc"]
    end
    subgraph tema_24["24 · Assistência Ambulatorial"]
        direction TB
        t24_br_ieps_saude["ieps_saude"]
        t24_br_ms_cnes["ms_cnes"]
        t24_br_ms_sia["ms_sia"]
        t24_br_ms_sih["ms_sih"]
    end
    subgraph tema_25["25 · Orçamento Federal"]
        direction TB
        t25_br_bcb_sicor["bcb_sicor"]
        t25_br_cgu_emendas_parlamentares["cgu_emendas_parlamentares"]
        t25_br_rf_arrecadacao["rf_arrecadacao"]
    end
    subgraph tema_26["26 · Servidores Públicos"]
        direction TB
        t26_br_cgu_servidores_executivo_federal["cgu_servidores_executivo_federal"]
        t26_br_me_rais["me_rais"]
        t26_br_me_siape["me_siape"]
        t26_br_stf_corte_aberta["stf_corte_aberta"]
    end
    subgraph tema_27["27 · Pesquisas de Opinião"]
        direction TB
        t27_br_ibge_pnadc["ibge_pnadc"]
        t27_br_ms_pns["ms_pns"]
        t27_br_poder360_pesquisas["poder360_pesquisas"]
        t27_br_tse_eleicoes["tse_eleicoes"]
    end
    subgraph tema_28["28 · Violência Escolar"]
        direction TB
        t28_br_fbsp_absp["fbsp_absp"]
        t28_br_inep_censo_escolar["inep_censo_escolar"]
        t28_br_inep_enem["inep_enem"]
        t28_br_inep_saeb["inep_saeb"]
        t28_br_ms_sinan["ms_sinan"]
        t28_br_rj_isp_estatisticas_seguranca["rj_isp_estatisticas_seguranca"]
    end
    subgraph tema_29["29 · Dados Eleitorais Detalhados"]
        direction TB
        t29_br_stf_corte_aberta["stf_corte_aberta"]
        t29_br_tse_eleicoes["tse_eleicoes"]
    end
    subgraph tema_30["30 · Estrutura Produtiva"]
        direction TB
        t30_br_me_cnpj["me_cnpj"]
    end
    subgraph tema_31["31 · Desenvolvimento Humano"]
        direction TB
        t31_br_cgu_beneficios_cidadao["cgu_beneficios_cidadao"]
        t31_br_ibge_censo_2022["ibge_censo_2022"]
        t31_br_ipea_avs["ipea_avs"]
    end
    subgraph tema_32["32 · Conectividade"]
        direction TB
        t32_br_anatel_banda_larga_fixa["anatel_banda_larga_fixa"]
        t32_br_anatel_indice_brasileiro_conectividade["anatel_indice_brasileiro_conectividade"]
        t32_br_inep_enem["inep_enem"]
        t32_br_simet_educacao_conectada["simet_educacao_conectada"]
    end
    subgraph tema_33["33 · Dados Internacionais Comparativos"]
        direction TB
        t33_br_fbsp_absp["fbsp_absp"]
    end
    subgraph tema_34["34 · Atlas"]
        direction TB
        t34_br_geobr_mapas["geobr_mapas"]
        t34_br_ibge_censo_2022["ibge_censo_2022"]
    end
    subgraph tema_35["35 · Transporte"]
        direction TB
        t35_br_anac_dadosabertos["anac_dadosabertos"]
        t35_br_fipe_veiculos["fipe_veiculos"]
        t35_br_ipea_atlasviolencia["ipea_atlasviolencia"]
        t35_br_mobilidados_indicadores["mobilidados_indicadores"]
    end
    subgraph tema_36["36 · Religiosidade"]
        direction TB
        t36_br_ibge_censo2022_religiao["ibge_censo2022_religiao"]
        t36_br_ibge_censo_2022["ibge_censo_2022"]
        t36_br_me_cnpj["me_cnpj"]
        t36_br_me_rais["me_rais"]
    end
    subgraph tema_37["37 · Sanções"]
        direction TB
        t37_br_pgfn_dividaativa["pgfn_dividaativa"]
        t37_br_tcu_inidoneos["tcu_inidoneos"]
        t37_global_icij_offshoreleaks["global_icij_offshoreleaks"]
        t37_global_ofac_sanctions["global_ofac_sanctions"]
        t37_global_opensanctions["global_opensanctions"]
    end
    subgraph tema_38["38 · Educação Básica"]
        direction TB
        t38_br_inep_avaliacao_alfabetizacao["inep_avaliacao_alfabetizacao"]
        t38_br_inep_educacao_especial["inep_educacao_especial"]
        t38_br_inep_formacao_docente["inep_formacao_docente"]
        t38_br_inep_sinopse_estatistica_educacao_basica["inep_sinopse_estatistica_educacao_basica"]
        t38_world_oecd_pisa["world_oecd_pisa"]
    end
    subgraph tema_39["39 · Justiça"]
        direction TB
        t39_br_cnj_estatisticas_poder_judiciario["cnj_estatisticas_poder_judiciario"]
        t39_br_cnj_improbidade_administrativa["cnj_improbidade_administrativa"]
        t39_br_stj_dadosabertos["stj_dadosabertos"]
        t39_br_tce_es["tce_es"]
        t39_br_tce_pi["tce_pi"]
        t39_br_tce_rj["tce_rj"]
        t39_br_tce_sp["tce_sp"]
        t39_br_tce_to["tce_to"]
        t39_br_tcu_dadosabertos["tcu_dadosabertos"]
    end
    subgraph tema_40["40 · Federalismo Fiscal"]
        direction TB
        t40_br_firjan_ifgf["firjan_ifgf"]
        t40_br_siop_orcamento["siop_orcamento"]
        t40_br_tesouro_capag["tesouro_capag"]
        t40_br_transferegov["transferegov"]
    end
    subgraph tema_41["41 · Nutrição"]
        direction TB
        t41_br_anvisa_cmed["anvisa_cmed"]
        t41_br_ibge_pof["ibge_pof"]
        t41_br_ms_sisvan["ms_sisvan"]
        t41_br_saude_bps["saude_bps"]
        t41_br_saude_farmaciapopular["saude_farmaciapopular"]
    end
    subgraph tema_42["42 · Água"]
        direction TB
        t42_br_ana_reservatorios["ana_reservatorios"]
        t42_br_ana_telemetria["ana_telemetria"]
        t42_br_inmet_bdmep["inmet_bdmep"]
        t42_br_inpe_queimadas["inpe_queimadas"]
        t42_br_inpe_sisam["inpe_sisam"]
        t42_br_mapbiomas_estatisticas["mapbiomas_estatisticas"]
        t42_br_mma_extincao["mma_extincao"]
        t42_world_wwf_hydrosheds["world_wwf_hydrosheds"]
    end
    subgraph tema_43["43 · Cultura"]
        direction TB
        t43_mundo_transfermarkt_competicoes["mundo_transfermarkt_competicoes"]
        t43_world_ampas_oscar["world_ampas_oscar"]
        t43_world_imdb_movies["world_imdb_movies"]
        t43_world_olympedia_olympics["world_olympedia_olympics"]
        t43_world_sofascore_competicoes_futebol["world_sofascore_competicoes_futebol"]
    end
    t01_br_me_rais -->|"cbo_2002 +1"| CBO
    t01_br_me_rais -->|"cep"| CEP
    t01_br_me_rais -->|"cnae_2_subclasse +2"| CNAE
    t01_br_me_rais -->|"id_municipio +1"| MUNICIPIO
    t01_br_me_rais -->|"sigla_uf"| UF
    t01_br_ms_sim -.->|"codigo_estabelecimento"| CNES
    t01_br_ms_sim -->|"id_municipio +4"| MUNICIPIO
    t01_br_ms_sim -->|"sigla_uf"| UF
    t02_br_inep_enem -->|"id_municipio_prova +2"| MUNICIPIO
    t02_br_inep_enem -->|"sigla_uf_prova +3"| UF
    t02_br_inep_ideb -->|"id_escola"| ESCOLA
    t02_br_inep_ideb -->|"id_municipio"| MUNICIPIO
    t02_br_inep_ideb -->|"sigla_uf"| UF
    t02_br_inep_indicador_nivel_socioeconomico -->|"id_escola"| ESCOLA
    t02_br_inep_indicador_nivel_socioeconomico -->|"id_municipio"| MUNICIPIO
    t02_br_inep_indicador_nivel_socioeconomico -->|"sigla_uf"| UF
    t03_br_cgu_beneficios_cidadao -->|"id_municipio"| MUNICIPIO
    t03_br_cgu_beneficios_cidadao -->|"cpf_favorecido +3"| PESSOA_CPF
    t03_br_cgu_beneficios_cidadao -->|"sigla_uf"| UF
    t03_br_ms_sim -.->|"codigo_estabelecimento"| CNES
    t03_br_ms_sim -->|"id_municipio +4"| MUNICIPIO
    t03_br_ms_sim -->|"sigla_uf"| UF
    t03_br_ms_sinasc -.->|"codigo_estabelecimento"| CNES
    t03_br_ms_sinasc -->|"id_municipio_mae +2"| MUNICIPIO
    t03_br_ms_sinasc -->|"sigla_uf"| UF
    t04_br_me_caged -->|"cbo_2002"| CBO
    t04_br_me_caged -.->|"categoria"| CID10
    t04_br_me_caged -->|"cnae_2_subclasse +1"| CNAE
    t04_br_me_caged -->|"id_municipio"| MUNICIPIO
    t04_br_me_caged -->|"sigla_uf"| UF
    t04_br_me_rais -->|"cbo_2002 +1"| CBO
    t04_br_me_rais -->|"cep"| CEP
    t04_br_me_rais -->|"cnae_2_subclasse +2"| CNAE
    t04_br_me_rais -->|"id_municipio +1"| MUNICIPIO
    t04_br_me_rais -->|"sigla_uf"| UF
    t05_br_camara_dados_abertos -->|"cnpj_cpf_fornecedor"| EMPRESA_CNPJ
    t05_br_camara_dados_abertos -->|"id_municipio_nascimento"| MUNICIPIO
    t05_br_camara_dados_abertos -->|"sigla_partido"| PARTIDO
    t05_br_camara_dados_abertos -->|"cpf"| PESSOA_CPF
    t05_br_camara_dados_abertos -->|"sigla_uf +3"| UF
    t05_br_senado_dadosabertos -.->|"Sigla +1"| UF
    t05_br_tse_eleicoes -->|"cep"| CEP
    t05_br_tse_eleicoes -->|"cnae_2_doador +5"| CNAE
    t05_br_tse_eleicoes -->|"cnpj_candidato +1"| EMPRESA_CNPJ
    t05_br_tse_eleicoes -->|"id_municipio +4"| MUNICIPIO
    t05_br_tse_eleicoes -->|"sigla_partido"| PARTIDO
    t05_br_tse_eleicoes -->|"cpf +2"| PESSOA_CPF
    t05_br_tse_eleicoes -->|"sigla_uf +3"| UF
    t06_br_mjsp_sisdepen -->|"cep"| CEP
    t06_br_mjsp_sisdepen -.->|"municipio +5"| MUNICIPIO
    t06_br_mjsp_sisdepen -.->|"uf"| UF
    t06_br_ms_sim -.->|"codigo_estabelecimento"| CNES
    t06_br_ms_sim -->|"id_municipio +4"| MUNICIPIO
    t06_br_ms_sim -->|"sigla_uf"| UF
    t06_br_rj_isp_estatisticas_seguranca -->|"id_municipio"| MUNICIPIO
    t07_br_bcb_estban -->|"cnpj_basico +1"| EMPRESA_CNPJ
    t07_br_bcb_estban -->|"id_municipio"| MUNICIPIO
    t07_br_bcb_estban -->|"sigla_uf"| UF
    t07_br_bcb_sicor -->|"cnpj +5"| EMPRESA_CNPJ
    t07_br_bcb_sicor -->|"id_programa"| FUNCAO_PROGRAMA
    t07_br_bcb_sicor -->|"id_municipio"| MUNICIPIO
    t07_br_bcb_sicor -->|"cpf"| PESSOA_CPF
    t07_br_bcb_sicor -->|"sigla_uf"| UF
    t07_br_ibge_pib -->|"id_municipio"| MUNICIPIO
    t07_br_ibge_pib -->|"sigla_uf +1"| UF
    t08_br_cgu_beneficios_cidadao -->|"id_municipio"| MUNICIPIO
    t08_br_cgu_beneficios_cidadao -->|"cpf_favorecido +3"| PESSOA_CPF
    t08_br_cgu_beneficios_cidadao -->|"sigla_uf"| UF
    t08_br_ibge_munic -->|"id_municipio"| MUNICIPIO
    t08_br_ibge_munic -->|"sigla_uf"| UF
    t08_br_me_siconfi -->|"id_municipio"| MUNICIPIO
    t08_br_me_siconfi -->|"sigla_uf +1"| UF
    t09_br_me_caged -->|"cbo_2002"| CBO
    t09_br_me_caged -.->|"categoria"| CID10
    t09_br_me_caged -->|"cnae_2_subclasse +1"| CNAE
    t09_br_me_caged -->|"id_municipio"| MUNICIPIO
    t09_br_me_caged -->|"sigla_uf"| UF
    t09_br_ms_sinasc -.->|"codigo_estabelecimento"| CNES
    t09_br_ms_sinasc -->|"id_municipio_mae +2"| MUNICIPIO
    t09_br_ms_sinasc -->|"sigla_uf"| UF
    t10_br_inpe_prodes -->|"id_municipio"| MUNICIPIO
    t10_br_seeg_emissoes -.->|"categoria +1"| CID10
    t10_br_seeg_emissoes -->|"id_municipio"| MUNICIPIO
    t10_br_seeg_emissoes -->|"sigla_uf"| UF
    t10_br_sfb_sicar -->|"id_municipio"| MUNICIPIO
    t10_br_sfb_sicar -->|"sigla_uf"| UF
    t11_br_anatel_indice_brasileiro_conectividade -->|"id_municipio"| MUNICIPIO
    t11_br_anatel_indice_brasileiro_conectividade -->|"sigla_uf"| UF
    t11_br_mdr_snis -->|"id_municipio"| MUNICIPIO
    t11_br_mdr_snis -->|"sigla_uf"| UF
    t12_br_me_rais -->|"cbo_2002 +1"| CBO
    t12_br_me_rais -->|"cep"| CEP
    t12_br_me_rais -->|"cnae_2_subclasse +2"| CNAE
    t12_br_me_rais -->|"id_municipio +1"| MUNICIPIO
    t12_br_me_rais -->|"sigla_uf"| UF
    t12_br_ms_sinasc -.->|"codigo_estabelecimento"| CNES
    t12_br_ms_sinasc -->|"id_municipio_mae +2"| MUNICIPIO
    t12_br_ms_sinasc -->|"sigla_uf"| UF
    t13_br_me_caged -->|"cbo_2002"| CBO
    t13_br_me_caged -.->|"categoria"| CID10
    t13_br_me_caged -->|"cnae_2_subclasse +1"| CNAE
    t13_br_me_caged -->|"id_municipio"| MUNICIPIO
    t13_br_me_caged -->|"sigla_uf"| UF
    t14_br_anp_combustiveis -->|"cep"| CEP
    t14_br_anp_combustiveis -->|"cnpj"| EMPRESA_CNPJ
    t14_br_anp_combustiveis -.->|"municipio"| MUNICIPIO
    t14_br_anp_combustiveis -.->|"estado"| UF
    t14_br_anp_precos_combustiveis -->|"cnpj_revenda"| EMPRESA_CNPJ
    t14_br_anp_precos_combustiveis -->|"id_municipio"| MUNICIPIO
    t14_br_anp_precos_combustiveis -->|"sigla_uf"| UF
    t14_br_ibge_ipca -.->|"categoria"| CID10
    t14_br_ibge_ipca -->|"id_municipio"| MUNICIPIO
    t14_br_ibge_ipca -->|"sigla_uf"| UF
    t15_br_camara_dados_abertos -->|"cnpj_cpf_fornecedor"| EMPRESA_CNPJ
    t15_br_camara_dados_abertos -->|"id_municipio_nascimento"| MUNICIPIO
    t15_br_camara_dados_abertos -->|"sigla_partido"| PARTIDO
    t15_br_camara_dados_abertos -->|"cpf"| PESSOA_CPF
    t15_br_camara_dados_abertos -->|"sigla_uf +3"| UF
    t15_br_tse_eleicoes -->|"cep"| CEP
    t15_br_tse_eleicoes -->|"cnae_2_doador +5"| CNAE
    t15_br_tse_eleicoes -->|"cnpj_candidato +1"| EMPRESA_CNPJ
    t15_br_tse_eleicoes -->|"id_municipio +4"| MUNICIPIO
    t15_br_tse_eleicoes -->|"sigla_partido"| PARTIDO
    t15_br_tse_eleicoes -->|"cpf +2"| PESSOA_CPF
    t15_br_tse_eleicoes -->|"sigla_uf +3"| UF
    t16_br_rf_arrecadacao -->|"id_municipio"| MUNICIPIO
    t16_br_rf_arrecadacao -->|"sigla_uf"| UF
    t17_br_bcb_sicor -->|"cnpj +5"| EMPRESA_CNPJ
    t17_br_bcb_sicor -->|"id_programa"| FUNCAO_PROGRAMA
    t17_br_bcb_sicor -->|"id_municipio"| MUNICIPIO
    t17_br_bcb_sicor -->|"cpf"| PESSOA_CPF
    t17_br_bcb_sicor -->|"sigla_uf"| UF
    t17_br_ibge_ppm -->|"id_municipio"| MUNICIPIO
    t17_br_ibge_ppm -->|"sigla_uf"| UF
    t17_br_sfb_sicar -->|"id_municipio"| MUNICIPIO
    t17_br_sfb_sicar -->|"sigla_uf"| UF
    t17_br_trase_supply_chain -->|"cnpj +1"| EMPRESA_CNPJ
    t17_br_trase_supply_chain -.->|"municipality_id +4"| MUNICIPIO
    t17_br_trase_supply_chain -.->|"cnpj_cpf"| PESSOA_CPF
    t17_br_trase_supply_chain -.->|"state"| UF
    t18_br_me_comex_stat -->|"id_municipio"| MUNICIPIO
    t18_br_me_comex_stat -->|"id_ncm +1"| NCM_SH
    t18_br_me_comex_stat -->|"sigla_pais_iso3 +1"| PAIS
    t18_br_me_comex_stat -->|"sigla_uf +1"| UF
    t19_br_anatel_indice_brasileiro_conectividade -->|"id_municipio"| MUNICIPIO
    t19_br_anatel_indice_brasileiro_conectividade -->|"sigla_uf"| UF
    t19_br_cnpq_bolsas -.->|"municipio_destino"| MUNICIPIO
    t19_br_cnpq_bolsas -->|"sigla_uf_origem +1"| UF
    t20_br_cnpq_bolsas -.->|"municipio_destino"| MUNICIPIO
    t20_br_cnpq_bolsas -->|"sigla_uf_origem +1"| UF
    t20_br_inep_enem -->|"id_municipio_prova +2"| MUNICIPIO
    t20_br_inep_enem -->|"sigla_uf_prova +3"| UF
    t21_br_cgu_cartao_pagamento -->|"cnpj_cpf_favorecido"| EMPRESA_CNPJ
    t21_br_cgu_cartao_pagamento -->|"codigo_orgao +1"| ORGAO
    t21_br_cgu_cartao_pagamento -->|"cpf_portador"| PESSOA_CPF
    t21_br_cgu_cartao_pagamento -->|"codigo_unidade_gestora"| UNIDADE_GESTORA
    t21_br_cgu_emendas_parlamentares -->|"id_funcao +3"| FUNCAO_PROGRAMA
    t21_br_cgu_emendas_parlamentares -->|"id_municipio_gasto"| MUNICIPIO
    t21_br_cgu_emendas_parlamentares -->|"sigla_uf_gasto"| UF
    t21_br_cgu_licitacao_contrato -.->|"cpf_cnpj_vencedor +2"| EMPRESA_CNPJ
    t21_br_cgu_licitacao_contrato -->|"id_municipio"| MUNICIPIO
    t21_br_cgu_licitacao_contrato -->|"id_orgao +1"| ORGAO
    t21_br_cgu_licitacao_contrato -.->|"cpf_cnpj_vencedor +2"| PESSOA_CPF
    t21_br_cgu_licitacao_contrato -->|"sigla_uf"| UF
    t21_br_cgu_licitacao_contrato -->|"id_unidade_gestora +1"| UNIDADE_GESTORA
    t21_br_rf_arrecadacao -->|"id_municipio"| MUNICIPIO
    t21_br_rf_arrecadacao -->|"sigla_uf"| UF
    t22_br_inpe_prodes -->|"id_municipio"| MUNICIPIO
    t22_br_seeg_emissoes -.->|"categoria +1"| CID10
    t22_br_seeg_emissoes -->|"id_municipio"| MUNICIPIO
    t22_br_seeg_emissoes -->|"sigla_uf"| UF
    t22_br_sfb_sicar -->|"id_municipio"| MUNICIPIO
    t22_br_sfb_sicar -->|"sigla_uf"| UF
    t23_br_ms_cnes -->|"cbo_2002 +2"| CBO
    t23_br_ms_cnes -->|"cep"| CEP
    t23_br_ms_cnes -->|"id_estabelecimento_cnes"| CNES
    t23_br_ms_cnes -->|"cnpj_mantenedora"| EMPRESA_CNPJ
    t23_br_ms_cnes -.->|"cnpj_mantenedora"| IES
    t23_br_ms_cnes -->|"id_municipio +2"| MUNICIPIO
    t23_br_ms_cnes -.->|"cpf_cnpj"| PESSOA_CPF
    t23_br_ms_cnes -->|"sigla_uf"| UF
    t23_br_ms_sim -.->|"codigo_estabelecimento"| CNES
    t23_br_ms_sim -->|"id_municipio +4"| MUNICIPIO
    t23_br_ms_sim -->|"sigla_uf"| UF
    t23_br_ms_sinasc -.->|"codigo_estabelecimento"| CNES
    t23_br_ms_sinasc -->|"id_municipio_mae +2"| MUNICIPIO
    t23_br_ms_sinasc -->|"sigla_uf"| UF
    t24_br_ieps_saude -->|"id_municipio"| MUNICIPIO
    t24_br_ieps_saude -->|"sigla_uf"| UF
    t24_br_ms_cnes -->|"cbo_2002 +2"| CBO
    t24_br_ms_cnes -->|"cep"| CEP
    t24_br_ms_cnes -->|"id_estabelecimento_cnes"| CNES
    t24_br_ms_cnes -->|"cnpj_mantenedora"| EMPRESA_CNPJ
    t24_br_ms_cnes -.->|"cnpj_mantenedora"| IES
    t24_br_ms_cnes -->|"id_municipio +2"| MUNICIPIO
    t24_br_ms_cnes -.->|"cpf_cnpj"| PESSOA_CPF
    t24_br_ms_cnes -->|"sigla_uf"| UF
    t24_br_ms_sia -->|"cid_principal_categoria +5"| CID10
    t24_br_ms_sia -->|"id_estabelecimento_cnes +1"| CNES
    t24_br_ms_sia -->|"id_municipio +1"| MUNICIPIO
    t24_br_ms_sia -->|"sigla_uf"| UF
    t24_br_ms_sih -->|"cbo_2002_paciente +1"| CBO
    t24_br_ms_sih -->|"cid_principal_categoria +27"| CID10
    t24_br_ms_sih -->|"id_estabelecimento_cnes"| CNES
    t24_br_ms_sih -->|"cnpj_mantenedora +1"| EMPRESA_CNPJ
    t24_br_ms_sih -.->|"cnpj_mantenedora"| IES
    t24_br_ms_sih -->|"id_municipio_gestor +3"| MUNICIPIO
    t24_br_ms_sih -->|"cpf_gestor"| PESSOA_CPF
    t24_br_ms_sih -->|"sigla_uf"| UF
    t25_br_bcb_sicor -->|"cnpj +5"| EMPRESA_CNPJ
    t25_br_bcb_sicor -->|"id_programa"| FUNCAO_PROGRAMA
    t25_br_bcb_sicor -->|"id_municipio"| MUNICIPIO
    t25_br_bcb_sicor -->|"cpf"| PESSOA_CPF
    t25_br_bcb_sicor -->|"sigla_uf"| UF
    t25_br_cgu_emendas_parlamentares -->|"id_funcao +3"| FUNCAO_PROGRAMA
    t25_br_cgu_emendas_parlamentares -->|"id_municipio_gasto"| MUNICIPIO
    t25_br_cgu_emendas_parlamentares -->|"sigla_uf_gasto"| UF
    t25_br_rf_arrecadacao -->|"id_municipio"| MUNICIPIO
    t25_br_rf_arrecadacao -->|"sigla_uf"| UF
    t26_br_cgu_servidores_executivo_federal -->|"cpf +2"| PESSOA_CPF
    t26_br_cgu_servidores_executivo_federal -->|"sigla_uf"| UF
    t26_br_me_rais -->|"cbo_2002 +1"| CBO
    t26_br_me_rais -->|"cep"| CEP
    t26_br_me_rais -->|"cnae_2_subclasse +2"| CNAE
    t26_br_me_rais -->|"id_municipio +1"| MUNICIPIO
    t26_br_me_rais -->|"sigla_uf"| UF
    t27_br_ibge_pnadc -->|"id_municipio"| MUNICIPIO
    t27_br_ibge_pnadc -->|"sigla_uf +1"| UF
    t27_br_ms_pns -->|"sigla_uf"| UF
    t27_br_poder360_pesquisas -.->|"nome_municipio"| MUNICIPIO
    t27_br_poder360_pesquisas -->|"sigla_partido"| PARTIDO
    t27_br_poder360_pesquisas -->|"sigla_uf"| UF
    t27_br_tse_eleicoes -->|"cep"| CEP
    t27_br_tse_eleicoes -->|"cnae_2_doador +5"| CNAE
    t27_br_tse_eleicoes -->|"cnpj_candidato +1"| EMPRESA_CNPJ
    t27_br_tse_eleicoes -->|"id_municipio +4"| MUNICIPIO
    t27_br_tse_eleicoes -->|"sigla_partido"| PARTIDO
    t27_br_tse_eleicoes -->|"cpf +2"| PESSOA_CPF
    t27_br_tse_eleicoes -->|"sigla_uf +3"| UF
    t28_br_fbsp_absp -->|"id_municipio"| MUNICIPIO
    t28_br_fbsp_absp -->|"sigla_uf"| UF
    t28_br_inep_censo_escolar -->|"cnpj_mantenedora +1"| EMPRESA_CNPJ
    t28_br_inep_censo_escolar -->|"id_escola +1"| ESCOLA
    t28_br_inep_censo_escolar -.->|"cnpj_mantenedora"| IES
    t28_br_inep_censo_escolar -->|"id_municipio"| MUNICIPIO
    t28_br_inep_censo_escolar -->|"sigla_uf"| UF
    t28_br_inep_enem -->|"id_municipio_prova +2"| MUNICIPIO
    t28_br_inep_enem -->|"sigla_uf_prova +3"| UF
    t28_br_inep_saeb -->|"id_escola"| ESCOLA
    t28_br_inep_saeb -->|"id_municipio"| MUNICIPIO
    t28_br_inep_saeb -->|"sigla_uf"| UF
    t28_br_ms_sinan -->|"id_estabelecimento_cnes"| CNES
    t28_br_ms_sinan -->|"id_municipio_infeccao +6"| MUNICIPIO
    t28_br_ms_sinan -->|"sigla_uf +4"| UF
    t28_br_rj_isp_estatisticas_seguranca -->|"id_municipio"| MUNICIPIO
    t29_br_tse_eleicoes -->|"cep"| CEP
    t29_br_tse_eleicoes -->|"cnae_2_doador +5"| CNAE
    t29_br_tse_eleicoes -->|"cnpj_candidato +1"| EMPRESA_CNPJ
    t29_br_tse_eleicoes -->|"id_municipio +4"| MUNICIPIO
    t29_br_tse_eleicoes -->|"sigla_partido"| PARTIDO
    t29_br_tse_eleicoes -->|"cpf +2"| PESSOA_CPF
    t29_br_tse_eleicoes -->|"sigla_uf +3"| UF
    t30_br_me_cnpj -->|"cep"| CEP
    t30_br_me_cnpj -->|"cnae_fiscal_principal +1"| CNAE
    t30_br_me_cnpj -->|"cnpj +3"| EMPRESA_CNPJ
    t30_br_me_cnpj -->|"id_municipio +1"| MUNICIPIO
    t30_br_me_cnpj -->|"id_pais"| PAIS
    t30_br_me_cnpj -->|"cpf_representante_legal"| PESSOA_CPF
    t30_br_me_cnpj -->|"sigla_uf"| UF
    t31_br_cgu_beneficios_cidadao -->|"id_municipio"| MUNICIPIO
    t31_br_cgu_beneficios_cidadao -->|"cpf_favorecido +3"| PESSOA_CPF
    t31_br_cgu_beneficios_cidadao -->|"sigla_uf"| UF
    t31_br_ibge_censo_2022 -->|"cep"| CEP
    t31_br_ibge_censo_2022 -->|"id_municipio"| MUNICIPIO
    t31_br_ibge_censo_2022 -->|"id_setor_censitario"| SETOR_CENSITARIO
    t31_br_ibge_censo_2022 -->|"sigla_uf +1"| UF
    t31_br_ipea_avs -->|"id_municipio"| MUNICIPIO
    t31_br_ipea_avs -->|"sigla_uf"| UF
    t32_br_anatel_banda_larga_fixa -->|"cnpj"| EMPRESA_CNPJ
    t32_br_anatel_banda_larga_fixa -->|"id_municipio"| MUNICIPIO
    t32_br_anatel_banda_larga_fixa -->|"sigla_uf"| UF
    t32_br_anatel_indice_brasileiro_conectividade -->|"id_municipio"| MUNICIPIO
    t32_br_anatel_indice_brasileiro_conectividade -->|"sigla_uf"| UF
    t32_br_inep_enem -->|"id_municipio_prova +2"| MUNICIPIO
    t32_br_inep_enem -->|"sigla_uf_prova +3"| UF
    t32_br_simet_educacao_conectada -->|"id_escola"| ESCOLA
    t32_br_simet_educacao_conectada -->|"id_municipio"| MUNICIPIO
    t32_br_simet_educacao_conectada -->|"sigla_uf"| UF
    t33_br_fbsp_absp -->|"id_municipio"| MUNICIPIO
    t33_br_fbsp_absp -->|"sigla_uf"| UF
    t34_br_geobr_mapas -.->|"categoria"| CID10
    t34_br_geobr_mapas -->|"id_escola"| ESCOLA
    t34_br_geobr_mapas -->|"id_municipio"| MUNICIPIO
    t34_br_geobr_mapas -->|"id_setor_censitario"| SETOR_CENSITARIO
    t34_br_geobr_mapas -->|"sigla_uf +1"| UF
    t34_br_ibge_censo_2022 -->|"cep"| CEP
    t34_br_ibge_censo_2022 -->|"id_municipio"| MUNICIPIO
    t34_br_ibge_censo_2022 -->|"id_setor_censitario"| SETOR_CENSITARIO
    t34_br_ibge_censo_2022 -->|"sigla_uf +1"| UF
    t35_br_mobilidados_indicadores -->|"id_municipio"| MUNICIPIO
    t35_br_mobilidados_indicadores -->|"sigla_uf"| UF
    t36_br_ibge_censo2022_religiao -->|"id_municipio"| MUNICIPIO
    t36_br_ibge_censo_2022 -->|"cep"| CEP
    t36_br_ibge_censo_2022 -->|"id_municipio"| MUNICIPIO
    t36_br_ibge_censo_2022 -->|"id_setor_censitario"| SETOR_CENSITARIO
    t36_br_ibge_censo_2022 -->|"sigla_uf +1"| UF
    t36_br_me_cnpj -->|"cep"| CEP
    t36_br_me_cnpj -->|"cnae_fiscal_principal +1"| CNAE
    t36_br_me_cnpj -->|"cnpj +3"| EMPRESA_CNPJ
    t36_br_me_cnpj -->|"id_municipio +1"| MUNICIPIO
    t36_br_me_cnpj -->|"id_pais"| PAIS
    t36_br_me_cnpj -->|"cpf_representante_legal"| PESSOA_CPF
    t36_br_me_cnpj -->|"sigla_uf"| UF
    t36_br_me_rais -->|"cbo_2002 +1"| CBO
    t36_br_me_rais -->|"cep"| CEP
    t36_br_me_rais -->|"cnae_2_subclasse +2"| CNAE
    t36_br_me_rais -->|"id_municipio +1"| MUNICIPIO
    t36_br_me_rais -->|"sigla_uf"| UF
    t37_br_pgfn_dividaativa -.->|"categoria"| CID10
    t37_br_pgfn_dividaativa -.->|"CPF_CNPJ"| EMPRESA_CNPJ
    t37_br_pgfn_dividaativa -.->|"CPF_CNPJ"| PESSOA_CPF
    t37_br_tcu_inidoneos -.->|"CPF_CNPJ"| EMPRESA_CNPJ
    t37_br_tcu_inidoneos -.->|"MUNICIPIO"| MUNICIPIO
    t37_br_tcu_inidoneos -.->|"CPF +1"| PESSOA_CPF
    t37_br_tcu_inidoneos -.->|"UF"| UF
    t38_br_inep_avaliacao_alfabetizacao -->|"id_escola"| ESCOLA
    t38_br_inep_avaliacao_alfabetizacao -->|"id_municipio"| MUNICIPIO
    t38_br_inep_avaliacao_alfabetizacao -->|"sigla_uf"| UF
    t38_br_inep_educacao_especial -->|"id_municipio"| MUNICIPIO
    t38_br_inep_educacao_especial -->|"sigla_uf"| UF
    t38_br_inep_formacao_docente -->|"sigla_uf"| UF
    t38_br_inep_sinopse_estatistica_educacao_basica -->|"id_municipio"| MUNICIPIO
    t38_br_inep_sinopse_estatistica_educacao_basica -->|"sigla_uf"| UF
    t38_world_oecd_pisa -.->|"wle_intercultural_communication_awareness"| MUNICIPIO
    t39_br_cnj_estatisticas_poder_judiciario -->|"sigla_uf"| UF
    t39_br_cnj_improbidade_administrativa -.->|"comunicado_tse"| MUNICIPIO
    t39_br_cnj_improbidade_administrativa -->|"sigla_uf"| UF
    t39_br_tce_es -.->|"categoria"| CID10
    t39_br_tce_es -.->|"EmpresaCNPJ"| EMPRESA_CNPJ
    t39_br_tce_es -.->|"Municipio"| MUNICIPIO
    t39_br_tce_pi -.->|"codIBGE +1"| MUNICIPIO
    t39_br_tce_pi -.->|"sigla"| UF
    t39_br_tce_rj -.->|"CPFCNPJ +1"| EMPRESA_CNPJ
    t39_br_tce_rj -.->|"Ente"| MUNICIPIO
    t39_br_tce_rj -.->|"CPFCNPJ +1"| PESSOA_CPF
    t39_br_tce_sp -.->|"municipio +1"| MUNICIPIO
    t40_br_firjan_ifgf -->|"id_municipio"| MUNICIPIO
    t40_br_firjan_ifgf -->|"sigla_uf"| UF
    t40_br_siop_orcamento -.->|"MunicÃ­pio"| MUNICIPIO
    t40_br_siop_orcamento -.->|"UF"| UF
    t40_br_tesouro_capag -.->|"Nome_Município +1"| MUNICIPIO
    t40_br_tesouro_capag -.->|"UF"| UF
    t40_br_transferegov -->|"cnpj_fundo_programa +7"| EMPRESA_CNPJ
    t40_br_transferegov -->|"id_programa"| FUNCAO_PROGRAMA
    t40_br_transferegov -->|"id_orgao_superior_programa +1"| ORGAO
    t40_br_transferegov -->|"id_unidade_gestora_programa"| UNIDADE_GESTORA
    t41_br_anvisa_cmed -->|"cnpj"| EMPRESA_CNPJ
    t41_br_ibge_pof -->|"sigla_uf"| UF
    t41_br_ms_sisvan -->|"id_municipio"| MUNICIPIO
    t41_br_ms_sisvan -->|"sigla_uf"| UF
    t41_br_saude_bps -->|"cnpj_do_fabricante +2"| EMPRESA_CNPJ
    t41_br_saude_bps -.->|"nome_do_munica­pio_da_instituicao"| MUNICIPIO
    t41_br_saude_farmaciapopular -.->|"numero_cnpj +1"| EMPRESA_CNPJ
    t41_br_saude_farmaciapopular -.->|"codigo_municipio"| MUNICIPIO
    t41_br_saude_farmaciapopular -.->|"codigo_uf"| UF
    t42_br_ana_telemetria -.->|"nmMunicipio +1"| MUNICIPIO
    t42_br_ana_telemetria -.->|"nmEstado +1"| UF
    t42_br_inmet_bdmep -->|"id_municipio"| MUNICIPIO
    t42_br_inpe_queimadas -->|"id_municipio"| MUNICIPIO
    t42_br_inpe_queimadas -->|"sigla_uf"| UF
    t42_br_inpe_sisam -->|"id_municipio"| MUNICIPIO
    t42_br_inpe_sisam -->|"sigla_uf"| UF
    t42_br_mapbiomas_estatisticas -->|"id_municipio"| MUNICIPIO
    t42_br_mapbiomas_estatisticas -->|"sigla_uf"| UF
    t42_br_mma_extincao -.->|"categoria"| CID10
    t42_world_wwf_hydrosheds -.->|"country"| PAIS
    t43_world_olympedia_olympics -.->|"city"| MUNICIPIO
    t43_world_olympedia_olympics -.->|"country"| PAIS
```
