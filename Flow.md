# Flow — o espelho por domínio

Os 195 datasets do espelho agrupados nos 10 domínios do `ERD.md`, e as chaves com que cada um alcança os hubs de referência.

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
    subgraph dom_referencia["Diretórios e tabelas de referência · 10"]
        direction TB
        d_br_bd_diretorios_brasil["bd_diretorios_brasil"]
        d_br_bd_diretorios_data_tempo["bd_diretorios_data_tempo"]
        d_br_bd_diretorios_mundo["bd_diretorios_mundo"]
        d_br_bd_diretorios_us["bd_diretorios_us"]
        d_br_bd_metadados["bd_metadados"]
        d_br_bd_vizinhanca["bd_vizinhanca"]
        d_br_brasilapi["brasilapi"]
        d_br_datasus_cid10["datasus_cid10"]
        d_br_ibge_amc["ibge_amc"]
        d_br_ibge_cbo_2002["ibge_cbo_2002"]
    end
    subgraph dom_saude["Saúde · 20"]
        direction TB
        d_br_ans_beneficiario["ans_beneficiario"]
        d_br_anvisa_cmed["anvisa_cmed"]
        d_br_anvisa_consultas["anvisa_consultas"]
        d_br_anvisa_medicamentos_industrializados["anvisa_medicamentos_industrializados"]
        d_br_ieps_saude["ieps_saude"]
        d_br_ms_atencao_basica["ms_atencao_basica"]
        d_br_ms_cnes["ms_cnes"]
        d_br_ms_imunizacoes["ms_imunizacoes"]
        d_br_ms_pns["ms_pns"]
        d_br_ms_populacao["ms_populacao"]
        d_br_ms_sia["ms_sia"]
        d_br_ms_sih["ms_sih"]
        d_br_ms_sim["ms_sim"]
        d_br_ms_sinan["ms_sinan"]
        d_br_ms_sinan_violencia["ms_sinan_violencia"]
        d_br_ms_sinasc["ms_sinasc"]
        d_br_ms_sisvan["ms_sisvan"]
        d_br_ms_vacinacao_covid19["ms_vacinacao_covid19"]
        d_br_saude_bps["saude_bps"]
        d_br_saude_farmaciapopular["saude_farmaciapopular"]
    end
    subgraph dom_educacao["Educação e ciência · 20"]
        direction TB
        d_br_capes_bolsas["capes_bolsas"]
        d_br_cnpq_bolsas["cnpq_bolsas"]
        d_br_inep_ana["inep_ana"]
        d_br_inep_avaliacao_alfabetizacao["inep_avaliacao_alfabetizacao"]
        d_br_inep_censo_educacao_superior["inep_censo_educacao_superior"]
        d_br_inep_censo_escolar["inep_censo_escolar"]
        d_br_inep_educacao_especial["inep_educacao_especial"]
        d_br_inep_enem["inep_enem"]
        d_br_inep_formacao_docente["inep_formacao_docente"]
        d_br_inep_ideb["inep_ideb"]
        d_br_inep_indicador_nivel_socioeconomico["inep_indicador_nivel_socioeconomico"]
        d_br_inep_indicadores_educacionais["inep_indicadores_educacionais"]
        d_br_inep_saeb["inep_saeb"]
        d_br_inep_sinopse_estatistica_educacao_basica["inep_sinopse_estatistica_educacao_basica"]
        d_br_mec_prouni["mec_prouni"]
        d_br_mec_sisu["mec_sisu"]
        d_br_simet_educacao_conectada["simet_educacao_conectada"]
        d_world_iea_pirls["world_iea_pirls"]
        d_world_iea_timss["world_iea_timss"]
        d_world_oecd_pisa["world_oecd_pisa"]
    end
    subgraph dom_economia["Trabalho, empresas e economia · 40"]
        direction TB
        d_br_anp_combustiveis["anp_combustiveis"]
        d_br_anp_precos_combustiveis["anp_precos_combustiveis"]
        d_br_bcb_estban["bcb_estban"]
        d_br_bcb_sgs["bcb_sgs"]
        d_br_bcb_sicor["bcb_sicor"]
        d_br_bndes_operacoes_contratadas["bndes_operacoes_contratadas"]
        d_br_brasilio_holdings["brasilio_holdings"]
        d_br_caixa_sinapi["caixa_sinapi"]
        d_br_caixa_sorteios["caixa_sorteios"]
        d_br_clp_ranking_competitividade["clp_ranking_competitividade"]
        d_br_cvm_administradores_carteira["cvm_administradores_carteira"]
        d_br_cvm_fundos["cvm_fundos"]
        d_br_cvm_oferta_publica_distribuicao["cvm_oferta_publica_distribuicao"]
        d_br_datahackers_state_data["datahackers_state_data"]
        d_br_fgv_igp["fgv_igp"]
        d_br_fipe_veiculos["fipe_veiculos"]
        d_br_firjan_ifgf["firjan_ifgf"]
        d_br_ibge_inpc["ibge_inpc"]
        d_br_ibge_ipca["ibge_ipca"]
        d_br_ibge_ipca15["ibge_ipca15"]
        d_br_ibge_ipp["ibge_ipp"]
        d_br_ibge_pam["ibge_pam"]
        d_br_ibge_pevs["ibge_pevs"]
        d_br_ibge_pib["ibge_pib"]
        d_br_ibge_ppm["ibge_ppm"]
        d_br_mc_indicadores["mc_indicadores"]
        d_br_me_caged["me_caged"]
        d_br_me_clima_organizacional["me_clima_organizacional"]
        d_br_me_cno["me_cno"]
        d_br_me_cnpj["me_cnpj"]
        d_br_me_comex_stat["me_comex_stat"]
        d_br_me_exportadoras_importadoras["me_exportadoras_importadoras"]
        d_br_me_rais["me_rais"]
        d_br_me_rais_identificada["me_rais_identificada"]
        d_br_me_sic["me_sic"]
        d_br_mme_consumo_energia_eletrica["mme_consumo_energia_eletrica"]
        d_br_rf_arrecadacao["rf_arrecadacao"]
        d_br_rf_cafir["rf_cafir"]
        d_br_rf_cno["rf_cno"]
        d_br_trase_supply_chain["trase_supply_chain"]
    end
    subgraph dom_governo["Governo, orçamento e compras · 31"]
        direction TB
        d_br_ba_feiradesantana_camara_leis["ba_feiradesantana_camara_leis"]
        d_br_cgu_beneficios_cidadao["cgu_beneficios_cidadao"]
        d_br_cgu_cartao_pagamento["cgu_cartao_pagamento"]
        d_br_cgu_dados_abertos["cgu_dados_abertos"]
        d_br_cgu_ebt["cgu_ebt"]
        d_br_cgu_fef["cgu_fef"]
        d_br_cgu_garantia_safra["cgu_garantia_safra"]
        d_br_cgu_licitacao_contrato["cgu_licitacao_contrato"]
        d_br_cgu_orcamento_publico["cgu_orcamento_publico"]
        d_br_cgu_pe_de_meia["cgu_pe_de_meia"]
        d_br_cgu_receitas_publicas["cgu_receitas_publicas"]
        d_br_cgu_seguro_defeso["cgu_seguro_defeso"]
        d_br_cgu_servidores_executivo_federal["cgu_servidores_executivo_federal"]
        d_br_cgu_viagens["cgu_viagens"]
        d_br_comprasgov_catmatcatser["comprasgov_catmatcatser"]
        d_br_comprasgov_sicaf["comprasgov_sicaf"]
        d_br_me_estoque_divida_publica["me_estoque_divida_publica"]
        d_br_me_siape["me_siape"]
        d_br_me_siconfi["me_siconfi"]
        d_br_me_siorg["me_siorg"]
        d_br_mp_pep["mp_pep"]
        d_br_ok_queridodiario["ok_queridodiario"]
        d_br_siop_orcamento["siop_orcamento"]
        d_br_tce_es["tce_es"]
        d_br_tce_pi["tce_pi"]
        d_br_tce_rj["tce_rj"]
        d_br_tce_sp["tce_sp"]
        d_br_tce_to["tce_to"]
        d_br_tcu_dadosabertos["tcu_dadosabertos"]
        d_br_tesouro_capag["tesouro_capag"]
        d_br_transferegov["transferegov"]
    end
    subgraph dom_politica["Política e eleições · 6"]
        direction TB
        d_br_camara_dados_abertos["camara_dados_abertos"]
        d_br_cgu_emendas_parlamentares["cgu_emendas_parlamentares"]
        d_br_poder360_pesquisas["poder360_pesquisas"]
        d_br_senado_dadosabertos["senado_dadosabertos"]
        d_br_tse_eleicoes["tse_eleicoes"]
        d_br_tse_filiacao_partidaria["tse_filiacao_partidaria"]
    end
    subgraph dom_justica["Justiça, segurança e sanções · 21"]
        direction TB
        d_br_bcb_penalidades["bcb_penalidades"]
        d_br_cnj_estatisticas_poder_judiciario["cnj_estatisticas_poder_judiciario"]
        d_br_cnj_improbidade_administrativa["cnj_improbidade_administrativa"]
        d_br_fbsp_absp["fbsp_absp"]
        d_br_ggb_relatorio_lgbtqi["ggb_relatorio_lgbtqi"]
        d_br_ipea_atlasviolencia["ipea_atlasviolencia"]
        d_br_mj_consumidorgovbr["mj_consumidorgovbr"]
        d_br_mjsp_ckan["mjsp_ckan"]
        d_br_mjsp_procurados["mjsp_procurados"]
        d_br_mjsp_sinesp["mjsp_sinesp"]
        d_br_mjsp_sisdepen["mjsp_sisdepen"]
        d_br_pgfn_dividaativa["pgfn_dividaativa"]
        d_br_rj_isp_estatisticas_seguranca["rj_isp_estatisticas_seguranca"]
        d_br_stf_corte_aberta["stf_corte_aberta"]
        d_br_stj_dadosabertos["stj_dadosabertos"]
        d_br_tcu_inidoneos["tcu_inidoneos"]
        d_eu_sanctions["eu_sanctions"]
        d_global_icij_offshoreleaks["global_icij_offshoreleaks"]
        d_global_ofac_sanctions["global_ofac_sanctions"]
        d_global_opensanctions["global_opensanctions"]
        d_un_sanctions["un_sanctions"]
    end
    subgraph dom_territorio["Território, ambiente e infraestrutura · 21"]
        direction TB
        d_br_ana_atlas_esgotos["ana_atlas_esgotos"]
        d_br_ana_reservatorios["ana_reservatorios"]
        d_br_ana_telemetria["ana_telemetria"]
        d_br_anac_dadosabertos["anac_dadosabertos"]
        d_br_anatel_banda_larga_fixa["anatel_banda_larga_fixa"]
        d_br_anatel_indice_brasileiro_conectividade["anatel_indice_brasileiro_conectividade"]
        d_br_geobr_mapas["geobr_mapas"]
        d_br_ibama_embargos["ibama_embargos"]
        d_br_inmet_bdmep["inmet_bdmep"]
        d_br_inpe_prodes["inpe_prodes"]
        d_br_inpe_queimadas["inpe_queimadas"]
        d_br_inpe_sisam["inpe_sisam"]
        d_br_ipea_acesso_oportunidades["ipea_acesso_oportunidades"]
        d_br_mapbiomas_estatisticas["mapbiomas_estatisticas"]
        d_br_mdr_snis["mdr_snis"]
        d_br_mma_extincao["mma_extincao"]
        d_br_mobilidados_indicadores["mobilidados_indicadores"]
        d_br_seeg_emissoes["seeg_emissoes"]
        d_br_sfb_sicar["sfb_sicar"]
        d_global_ibge_tabua_mares["global_ibge_tabua_mares"]
        d_world_wwf_hydrosheds["world_wwf_hydrosheds"]
    end
    subgraph dom_demografia["Demografia e indicadores sociais · 17"]
        direction TB
        d_br_abrinq_oca["abrinq_oca"]
        d_br_ce_fortaleza_sefin_iptu["ce_fortaleza_sefin_iptu"]
        d_br_ibge_censo2022_raca["ibge_censo2022_raca"]
        d_br_ibge_censo2022_religiao["ibge_censo2022_religiao"]
        d_br_ibge_censo_2022["ibge_censo_2022"]
        d_br_ibge_censo_demografico["ibge_censo_demografico"]
        d_br_ibge_estadic["ibge_estadic"]
        d_br_ibge_munic["ibge_munic"]
        d_br_ibge_nomes_brasil["ibge_nomes_brasil"]
        d_br_ibge_pnad["ibge_pnad"]
        d_br_ibge_pnad_covid["ibge_pnad_covid"]
        d_br_ibge_pnadc["ibge_pnadc"]
        d_br_ibge_pof["ibge_pof"]
        d_br_ibge_populacao["ibge_populacao"]
        d_br_ipea_avs["ipea_avs"]
        d_br_mg_belohorizonte_smfa_iptu["mg_belohorizonte_smfa_iptu"]
        d_br_sp_saopaulo_geosampa_iptu["sp_saopaulo_geosampa_iptu"]
    end
    subgraph dom_internacional["Internacional, cultura e esporte · 9"]
        direction TB
        d_mundo_transfermarkt_competicoes["mundo_transfermarkt_competicoes"]
        d_mundo_transfermarkt_competicoes_internacionais["mundo_transfermarkt_competicoes_internacionais"]
        d_us_harvard_ned["us_harvard_ned"]
        d_world_ampas_oscar["world_ampas_oscar"]
        d_world_imdb_movies["world_imdb_movies"]
        d_world_oecd_public_finance["world_oecd_public_finance"]
        d_world_olympedia_olympics["world_olympedia_olympics"]
        d_world_sofascore_competicoes_futebol["world_sofascore_competicoes_futebol"]
        d_world_wb_mides["world_wb_mides"]
    end
    d_br_bd_diretorios_brasil -->|"cbo_2002 +1"| CBO
    d_br_bd_diretorios_brasil -->|"cep"| CEP
    d_br_bd_diretorios_brasil -->|"cid_datasus"| CID10
    d_br_bd_diretorios_brasil -->|"cnae_1 +2"| CNAE
    d_br_bd_diretorios_brasil -->|"cnpj +3"| EMPRESA_CNPJ
    d_br_bd_diretorios_brasil -->|"id_escola"| ESCOLA
    d_br_bd_diretorios_brasil -->|"id_ies"| IES
    d_br_bd_diretorios_brasil -->|"id_municipio +4"| MUNICIPIO
    d_br_bd_diretorios_brasil -->|"id_setor_censitario"| SETOR_CENSITARIO
    d_br_bd_diretorios_brasil -->|"sigla_uf +1"| UF
    d_br_bd_diretorios_mundo -->|"id_ncm +3"| NCM_SH
    d_br_bd_diretorios_mundo -->|"sigla_pais_iso3 +2"| PAIS
    d_br_bd_diretorios_mundo -.->|"sigla"| UF
    d_br_bd_diretorios_us -.->|"city"| MUNICIPIO
    d_br_bd_metadados -.->|"state"| UF
    d_br_bd_vizinhanca -->|"id_municipio_1 +1"| MUNICIPIO
    d_br_bd_vizinhanca -->|"sigla_uf_1 +1"| UF
    d_br_brasilapi -.->|"city"| MUNICIPIO
    d_br_brasilapi -.->|"state"| UF
    d_br_datasus_cid10 -.->|"CAT"| CID10
    d_br_ibge_amc -->|"id_municipio"| MUNICIPIO
    d_br_ibge_cbo_2002 -->|"cbo_2002"| CBO
    d_br_ans_beneficiario -->|"cnpj"| EMPRESA_CNPJ
    d_br_ans_beneficiario -->|"id_municipio"| MUNICIPIO
    d_br_ans_beneficiario -->|"sigla_uf"| UF
    d_br_anvisa_cmed -->|"cnpj"| EMPRESA_CNPJ
    d_br_anvisa_medicamentos_industrializados -->|"id_municipio"| MUNICIPIO
    d_br_anvisa_medicamentos_industrializados -->|"sigla_uf +1"| UF
    d_br_ieps_saude -->|"id_municipio"| MUNICIPIO
    d_br_ieps_saude -->|"sigla_uf"| UF
    d_br_ms_atencao_basica -->|"id_municipio +1"| MUNICIPIO
    d_br_ms_atencao_basica -->|"sigla_uf"| UF
    d_br_ms_cnes -->|"cbo_2002 +2"| CBO
    d_br_ms_cnes -->|"cep"| CEP
    d_br_ms_cnes -->|"id_estabelecimento_cnes"| CNES
    d_br_ms_cnes -->|"cnpj_mantenedora"| EMPRESA_CNPJ
    d_br_ms_cnes -.->|"cnpj_mantenedora"| IES
    d_br_ms_cnes -->|"id_municipio +2"| MUNICIPIO
    d_br_ms_cnes -.->|"cpf_cnpj"| PESSOA_CPF
    d_br_ms_cnes -->|"sigla_uf"| UF
    d_br_ms_imunizacoes -->|"id_municipio"| MUNICIPIO
    d_br_ms_imunizacoes -->|"sigla_uf"| UF
    d_br_ms_pns -->|"sigla_uf"| UF
    d_br_ms_populacao -->|"id_municipio"| MUNICIPIO
    d_br_ms_sia -->|"cid_principal_categoria +5"| CID10
    d_br_ms_sia -->|"id_estabelecimento_cnes +1"| CNES
    d_br_ms_sia -->|"id_municipio +1"| MUNICIPIO
    d_br_ms_sia -->|"sigla_uf"| UF
    d_br_ms_sih -->|"cbo_2002_paciente +1"| CBO
    d_br_ms_sih -->|"cid_principal_categoria +27"| CID10
    d_br_ms_sih -->|"id_estabelecimento_cnes"| CNES
    d_br_ms_sih -->|"cnpj_mantenedora +1"| EMPRESA_CNPJ
    d_br_ms_sih -.->|"cnpj_mantenedora"| IES
    d_br_ms_sih -->|"id_municipio_gestor +3"| MUNICIPIO
    d_br_ms_sih -->|"cpf_gestor"| PESSOA_CPF
    d_br_ms_sih -->|"sigla_uf"| UF
    d_br_ms_sim -.->|"codigo_estabelecimento"| CNES
    d_br_ms_sim -->|"id_municipio +4"| MUNICIPIO
    d_br_ms_sim -->|"sigla_uf"| UF
    d_br_ms_sinan -->|"id_estabelecimento_cnes"| CNES
    d_br_ms_sinan -->|"id_municipio_infeccao +6"| MUNICIPIO
    d_br_ms_sinan -->|"sigla_uf +4"| UF
    d_br_ms_sinan_violencia -.->|"ID_MUNICIP"| MUNICIPIO
    d_br_ms_sinan_violencia -.->|"SG_UF"| UF
    d_br_ms_sinasc -.->|"codigo_estabelecimento"| CNES
    d_br_ms_sinasc -->|"id_municipio_mae +2"| MUNICIPIO
    d_br_ms_sinasc -->|"sigla_uf"| UF
    d_br_ms_sisvan -->|"id_municipio"| MUNICIPIO
    d_br_ms_sisvan -->|"sigla_uf"| UF
    d_br_ms_vacinacao_covid19 -.->|"id_estabelecimento"| CNES
    d_br_ms_vacinacao_covid19 -->|"id_municipio"| MUNICIPIO
    d_br_ms_vacinacao_covid19 -->|"sigla_uf"| UF
    d_br_saude_bps -->|"cnpj_do_fabricante +2"| EMPRESA_CNPJ
    d_br_saude_bps -.->|"nome_do_munica­pio_da_instituicao"| MUNICIPIO
    d_br_saude_farmaciapopular -.->|"numero_cnpj +1"| EMPRESA_CNPJ
    d_br_saude_farmaciapopular -.->|"codigo_municipio"| MUNICIPIO
    d_br_saude_farmaciapopular -.->|"codigo_uf"| UF
    d_br_capes_bolsas -->|"cpf"| PESSOA_CPF
    d_br_cnpq_bolsas -.->|"municipio_destino"| MUNICIPIO
    d_br_cnpq_bolsas -->|"sigla_uf_origem +1"| UF
    d_br_inep_ana -->|"id_escola"| ESCOLA
    d_br_inep_ana -->|"id_municipio"| MUNICIPIO
    d_br_inep_ana -->|"id_uf"| UF
    d_br_inep_avaliacao_alfabetizacao -->|"id_escola"| ESCOLA
    d_br_inep_avaliacao_alfabetizacao -->|"id_municipio"| MUNICIPIO
    d_br_inep_avaliacao_alfabetizacao -->|"sigla_uf"| UF
    d_br_inep_censo_educacao_superior -->|"cep"| CEP
    d_br_inep_censo_educacao_superior -->|"id_ies"| IES
    d_br_inep_censo_educacao_superior -->|"id_municipio"| MUNICIPIO
    d_br_inep_censo_educacao_superior -->|"sigla_uf"| UF
    d_br_inep_censo_escolar -->|"cnpj_mantenedora +1"| EMPRESA_CNPJ
    d_br_inep_censo_escolar -->|"id_escola +1"| ESCOLA
    d_br_inep_censo_escolar -.->|"cnpj_mantenedora"| IES
    d_br_inep_censo_escolar -->|"id_municipio"| MUNICIPIO
    d_br_inep_censo_escolar -->|"sigla_uf"| UF
    d_br_inep_educacao_especial -->|"id_municipio"| MUNICIPIO
    d_br_inep_educacao_especial -->|"sigla_uf"| UF
    d_br_inep_enem -->|"id_municipio_prova +2"| MUNICIPIO
    d_br_inep_enem -->|"sigla_uf_prova +3"| UF
    d_br_inep_formacao_docente -->|"sigla_uf"| UF
    d_br_inep_ideb -->|"id_escola"| ESCOLA
    d_br_inep_ideb -->|"id_municipio"| MUNICIPIO
    d_br_inep_ideb -->|"sigla_uf"| UF
    d_br_inep_indicador_nivel_socioeconomico -->|"id_escola"| ESCOLA
    d_br_inep_indicador_nivel_socioeconomico -->|"id_municipio"| MUNICIPIO
    d_br_inep_indicador_nivel_socioeconomico -->|"sigla_uf"| UF
    d_br_inep_indicadores_educacionais -->|"id_escola"| ESCOLA
    d_br_inep_indicadores_educacionais -->|"id_municipio"| MUNICIPIO
    d_br_inep_indicadores_educacionais -->|"sigla_uf"| UF
    d_br_inep_saeb -->|"id_escola"| ESCOLA
    d_br_inep_saeb -->|"id_municipio"| MUNICIPIO
    d_br_inep_saeb -->|"sigla_uf"| UF
    d_br_inep_sinopse_estatistica_educacao_basica -->|"id_municipio"| MUNICIPIO
    d_br_inep_sinopse_estatistica_educacao_basica -->|"sigla_uf"| UF
    d_br_mec_sisu -->|"id_ies"| IES
    d_br_mec_sisu -->|"id_municipio_campus +1"| MUNICIPIO
    d_br_mec_sisu -->|"cpf"| PESSOA_CPF
    d_br_mec_sisu -->|"sigla_uf_ies +2"| UF
    d_br_simet_educacao_conectada -->|"id_escola"| ESCOLA
    d_br_simet_educacao_conectada -->|"id_municipio"| MUNICIPIO
    d_br_simet_educacao_conectada -->|"sigla_uf"| UF
    d_world_oecd_pisa -.->|"wle_intercultural_communication_awareness"| MUNICIPIO
    d_br_anp_combustiveis -->|"cep"| CEP
    d_br_anp_combustiveis -->|"cnpj"| EMPRESA_CNPJ
    d_br_anp_combustiveis -.->|"municipio"| MUNICIPIO
    d_br_anp_combustiveis -.->|"estado"| UF
    d_br_anp_precos_combustiveis -->|"cnpj_revenda"| EMPRESA_CNPJ
    d_br_anp_precos_combustiveis -->|"id_municipio"| MUNICIPIO
    d_br_anp_precos_combustiveis -->|"sigla_uf"| UF
    d_br_bcb_estban -->|"cnpj_basico +1"| EMPRESA_CNPJ
    d_br_bcb_estban -->|"id_municipio"| MUNICIPIO
    d_br_bcb_estban -->|"sigla_uf"| UF
    d_br_bcb_sicor -->|"cnpj +5"| EMPRESA_CNPJ
    d_br_bcb_sicor -->|"id_programa"| FUNCAO_PROGRAMA
    d_br_bcb_sicor -->|"id_municipio"| MUNICIPIO
    d_br_bcb_sicor -->|"cpf"| PESSOA_CPF
    d_br_bcb_sicor -->|"sigla_uf"| UF
    d_br_bndes_operacoes_contratadas -->|"cnpj_cliente +1"| EMPRESA_CNPJ
    d_br_bndes_operacoes_contratadas -->|"id_municipio"| MUNICIPIO
    d_br_bndes_operacoes_contratadas -->|"sigla_uf"| UF
    d_br_brasilio_holdings -->|"cnpj +1"| EMPRESA_CNPJ
    d_br_caixa_sinapi -.->|"uf"| UF
    d_br_clp_ranking_competitividade -->|"id_municipio"| MUNICIPIO
    d_br_clp_ranking_competitividade -->|"sigla_uf"| UF
    d_br_cvm_administradores_carteira -->|"cep"| CEP
    d_br_cvm_administradores_carteira -->|"cnpj"| EMPRESA_CNPJ
    d_br_cvm_administradores_carteira -.->|"municipio"| MUNICIPIO
    d_br_cvm_administradores_carteira -->|"sigla_uf"| UF
    d_br_cvm_fundos -.->|"CNPJ_ADMIN +5"| EMPRESA_CNPJ
    d_br_cvm_fundos -.->|"CPF_CNPJ_GESTOR"| PESSOA_CPF
    d_br_cvm_oferta_publica_distribuicao -->|"cnpj_lider +2"| EMPRESA_CNPJ
    d_br_cvm_oferta_publica_distribuicao -.->|"data_comunicado +1"| MUNICIPIO
    d_br_datahackers_state_data -.->|"p1_i_1"| UF
    d_br_firjan_ifgf -->|"id_municipio"| MUNICIPIO
    d_br_firjan_ifgf -->|"sigla_uf"| UF
    d_br_ibge_inpc -.->|"categoria"| CID10
    d_br_ibge_inpc -->|"id_municipio"| MUNICIPIO
    d_br_ibge_inpc -->|"sigla_uf"| UF
    d_br_ibge_ipca -.->|"categoria"| CID10
    d_br_ibge_ipca -->|"id_municipio"| MUNICIPIO
    d_br_ibge_ipca -->|"sigla_uf"| UF
    d_br_ibge_ipca15 -.->|"categoria"| CID10
    d_br_ibge_ipca15 -->|"id_municipio"| MUNICIPIO
    d_br_ibge_ipca15 -->|"sigla_uf"| UF
    d_br_ibge_pam -->|"id_municipio"| MUNICIPIO
    d_br_ibge_pam -->|"sigla_uf"| UF
    d_br_ibge_pevs -->|"id_municipio"| MUNICIPIO
    d_br_ibge_pib -->|"id_municipio"| MUNICIPIO
    d_br_ibge_pib -->|"sigla_uf +1"| UF
    d_br_ibge_ppm -->|"id_municipio"| MUNICIPIO
    d_br_ibge_ppm -->|"sigla_uf"| UF
    d_br_mc_indicadores -->|"id_municipio"| MUNICIPIO
    d_br_me_caged -->|"cbo_2002"| CBO
    d_br_me_caged -.->|"categoria"| CID10
    d_br_me_caged -->|"cnae_2_subclasse +1"| CNAE
    d_br_me_caged -->|"id_municipio"| MUNICIPIO
    d_br_me_caged -->|"sigla_uf"| UF
    d_br_me_clima_organizacional -.->|"subclasse"| CNAE
    d_br_me_cno -->|"cnae_2"| CNAE
    d_br_me_cnpj -->|"cep"| CEP
    d_br_me_cnpj -->|"cnae_fiscal_principal +1"| CNAE
    d_br_me_cnpj -->|"cnpj +3"| EMPRESA_CNPJ
    d_br_me_cnpj -->|"id_municipio +1"| MUNICIPIO
    d_br_me_cnpj -->|"id_pais"| PAIS
    d_br_me_cnpj -->|"cpf_representante_legal"| PESSOA_CPF
    d_br_me_cnpj -->|"sigla_uf"| UF
    d_br_me_comex_stat -->|"id_municipio"| MUNICIPIO
    d_br_me_comex_stat -->|"id_ncm +1"| NCM_SH
    d_br_me_comex_stat -->|"sigla_pais_iso3 +1"| PAIS
    d_br_me_comex_stat -->|"sigla_uf +1"| UF
    d_br_me_rais -->|"cbo_2002 +1"| CBO
    d_br_me_rais -->|"cep"| CEP
    d_br_me_rais -->|"cnae_2_subclasse +2"| CNAE
    d_br_me_rais -->|"id_municipio +1"| MUNICIPIO
    d_br_me_rais -->|"sigla_uf"| UF
    d_br_me_rais_identificada -->|"cnae_fiscal_principal"| CNAE
    d_br_me_rais_identificada -->|"cnpj_basico"| EMPRESA_CNPJ
    d_br_me_rais_identificada -->|"id_municipio"| MUNICIPIO
    d_br_me_rais_identificada -->|"sigla_uf"| UF
    d_br_mme_consumo_energia_eletrica -->|"sigla_uf"| UF
    d_br_rf_arrecadacao -->|"id_municipio"| MUNICIPIO
    d_br_rf_arrecadacao -->|"sigla_uf"| UF
    d_br_rf_cafir -->|"cep"| CEP
    d_br_rf_cafir -->|"id_municipio"| MUNICIPIO
    d_br_rf_cafir -->|"sigla_uf"| UF
    d_br_rf_cno -->|"cep"| CEP
    d_br_rf_cno -.->|"categoria"| CID10
    d_br_rf_cno -->|"cnae_2_subclasse"| CNAE
    d_br_rf_cno -->|"id_municipio"| MUNICIPIO
    d_br_rf_cno -->|"id_pais"| PAIS
    d_br_rf_cno -->|"sigla_uf"| UF
    d_br_trase_supply_chain -->|"cnpj +1"| EMPRESA_CNPJ
    d_br_trase_supply_chain -.->|"municipality_id +4"| MUNICIPIO
    d_br_trase_supply_chain -.->|"cnpj_cpf"| PESSOA_CPF
    d_br_trase_supply_chain -.->|"state"| UF
    d_br_ba_feiradesantana_camara_leis -.->|"categoria"| CID10
    d_br_cgu_beneficios_cidadao -->|"id_municipio"| MUNICIPIO
    d_br_cgu_beneficios_cidadao -->|"cpf_favorecido +3"| PESSOA_CPF
    d_br_cgu_beneficios_cidadao -->|"sigla_uf"| UF
    d_br_cgu_cartao_pagamento -->|"cnpj_cpf_favorecido"| EMPRESA_CNPJ
    d_br_cgu_cartao_pagamento -->|"codigo_orgao +1"| ORGAO
    d_br_cgu_cartao_pagamento -->|"cpf_portador"| PESSOA_CPF
    d_br_cgu_cartao_pagamento -->|"codigo_unidade_gestora"| UNIDADE_GESTORA
    d_br_cgu_dados_abertos -->|"id_municipio"| MUNICIPIO
    d_br_cgu_dados_abertos -->|"sigla_uf"| UF
    d_br_cgu_ebt -->|"id_municipio"| MUNICIPIO
    d_br_cgu_ebt -->|"sigla_uf"| UF
    d_br_cgu_fef -->|"id_municipio"| MUNICIPIO
    d_br_cgu_fef -->|"sigla_uf"| UF
    d_br_cgu_garantia_safra -.->|"nome_municipio +1"| MUNICIPIO
    d_br_cgu_garantia_safra -.->|"uf"| UF
    d_br_cgu_licitacao_contrato -.->|"cpf_cnpj_vencedor +2"| EMPRESA_CNPJ
    d_br_cgu_licitacao_contrato -->|"id_municipio"| MUNICIPIO
    d_br_cgu_licitacao_contrato -->|"id_orgao +1"| ORGAO
    d_br_cgu_licitacao_contrato -.->|"cpf_cnpj_vencedor +2"| PESSOA_CPF
    d_br_cgu_licitacao_contrato -->|"sigla_uf"| UF
    d_br_cgu_licitacao_contrato -->|"id_unidade_gestora +1"| UNIDADE_GESTORA
    d_br_cgu_orcamento_publico -->|"id_funcao +3"| FUNCAO_PROGRAMA
    d_br_cgu_orcamento_publico -->|"id_orgao_superior +1"| ORGAO
    d_br_cgu_orcamento_publico -->|"id_unidade_orcamentaria"| UNIDADE_GESTORA
    d_br_cgu_pe_de_meia -.->|"nome_municipio +1"| MUNICIPIO
    d_br_cgu_pe_de_meia -->|"cpf_responsavel +1"| PESSOA_CPF
    d_br_cgu_pe_de_meia -.->|"uf"| UF
    d_br_cgu_receitas_publicas -->|"id_orgao +1"| ORGAO
    d_br_cgu_receitas_publicas -->|"codigo_unidade_gestora"| UNIDADE_GESTORA
    d_br_cgu_seguro_defeso -.->|"nome_municipio +1"| MUNICIPIO
    d_br_cgu_seguro_defeso -->|"cpf_favorecido"| PESSOA_CPF
    d_br_cgu_seguro_defeso -.->|"uf"| UF
    d_br_cgu_servidores_executivo_federal -->|"cpf +2"| PESSOA_CPF
    d_br_cgu_servidores_executivo_federal -->|"sigla_uf"| UF
    d_br_cgu_viagens -->|"codigo_orgao_solicitante"| ORGAO
    d_br_cgu_viagens -->|"cpf_viajante"| PESSOA_CPF
    d_br_cgu_viagens -.->|"origem_uf +1"| UF
    d_br_comprasgov_catmatcatser -.->|"codigo_ncm +1"| NCM_SH
    d_br_comprasgov_sicaf -.->|"codigoCnae"| CNAE
    d_br_comprasgov_sicaf -->|"cnpj"| EMPRESA_CNPJ
    d_br_comprasgov_sicaf -.->|"nomeMunicipio"| MUNICIPIO
    d_br_comprasgov_sicaf -->|"cpf"| PESSOA_CPF
    d_br_comprasgov_sicaf -.->|"ufSigla"| UF
    d_br_me_siconfi -->|"id_municipio"| MUNICIPIO
    d_br_me_siconfi -->|"sigla_uf +1"| UF
    d_br_mp_pep -->|"sigla_uf"| UF
    d_br_ok_queridodiario -.->|"territory_id +1"| MUNICIPIO
    d_br_ok_queridodiario -.->|"state_code"| UF
    d_br_siop_orcamento -.->|"MunicÃ­pio"| MUNICIPIO
    d_br_siop_orcamento -.->|"UF"| UF
    d_br_tce_es -.->|"categoria"| CID10
    d_br_tce_es -.->|"EmpresaCNPJ"| EMPRESA_CNPJ
    d_br_tce_es -.->|"Municipio"| MUNICIPIO
    d_br_tce_pi -.->|"codIBGE +1"| MUNICIPIO
    d_br_tce_pi -.->|"sigla"| UF
    d_br_tce_rj -.->|"CPFCNPJ +1"| EMPRESA_CNPJ
    d_br_tce_rj -.->|"Ente"| MUNICIPIO
    d_br_tce_rj -.->|"CPFCNPJ +1"| PESSOA_CPF
    d_br_tce_sp -.->|"municipio +1"| MUNICIPIO
    d_br_tesouro_capag -.->|"Nome_Município +1"| MUNICIPIO
    d_br_tesouro_capag -.->|"UF"| UF
    d_br_transferegov -->|"cnpj_fundo_programa +7"| EMPRESA_CNPJ
    d_br_transferegov -->|"id_programa"| FUNCAO_PROGRAMA
    d_br_transferegov -->|"id_orgao_superior_programa +1"| ORGAO
    d_br_transferegov -->|"id_unidade_gestora_programa"| UNIDADE_GESTORA
    d_br_camara_dados_abertos -->|"cnpj_cpf_fornecedor"| EMPRESA_CNPJ
    d_br_camara_dados_abertos -->|"id_municipio_nascimento"| MUNICIPIO
    d_br_camara_dados_abertos -->|"sigla_partido"| PARTIDO
    d_br_camara_dados_abertos -->|"cpf"| PESSOA_CPF
    d_br_camara_dados_abertos -->|"sigla_uf +3"| UF
    d_br_cgu_emendas_parlamentares -->|"id_funcao +3"| FUNCAO_PROGRAMA
    d_br_cgu_emendas_parlamentares -->|"id_municipio_gasto"| MUNICIPIO
    d_br_cgu_emendas_parlamentares -->|"sigla_uf_gasto"| UF
    d_br_poder360_pesquisas -.->|"nome_municipio"| MUNICIPIO
    d_br_poder360_pesquisas -->|"sigla_partido"| PARTIDO
    d_br_poder360_pesquisas -->|"sigla_uf"| UF
    d_br_senado_dadosabertos -.->|"Sigla +1"| UF
    d_br_tse_eleicoes -->|"cep"| CEP
    d_br_tse_eleicoes -->|"cnae_2_doador +5"| CNAE
    d_br_tse_eleicoes -->|"cnpj_candidato +1"| EMPRESA_CNPJ
    d_br_tse_eleicoes -->|"id_municipio +4"| MUNICIPIO
    d_br_tse_eleicoes -->|"sigla_partido"| PARTIDO
    d_br_tse_eleicoes -->|"cpf +2"| PESSOA_CPF
    d_br_tse_eleicoes -->|"sigla_uf +3"| UF
    d_br_tse_filiacao_partidaria -->|"id_municipio +1"| MUNICIPIO
    d_br_tse_filiacao_partidaria -->|"sigla_partido"| PARTIDO
    d_br_tse_filiacao_partidaria -->|"cpf"| PESSOA_CPF
    d_br_tse_filiacao_partidaria -->|"sigla_uf"| UF
    d_br_bcb_penalidades -.->|"CPF_CNPJ"| EMPRESA_CNPJ
    d_br_bcb_penalidades -.->|"CPF_CNPJ"| PESSOA_CPF
    d_br_cnj_estatisticas_poder_judiciario -->|"sigla_uf"| UF
    d_br_cnj_improbidade_administrativa -.->|"comunicado_tse"| MUNICIPIO
    d_br_cnj_improbidade_administrativa -->|"sigla_uf"| UF
    d_br_fbsp_absp -->|"id_municipio"| MUNICIPIO
    d_br_fbsp_absp -->|"sigla_uf"| UF
    d_br_mj_consumidorgovbr -.->|"UF"| UF
    d_br_mjsp_ckan -.->|"NumeroCNPJ +1"| EMPRESA_CNPJ
    d_br_mjsp_ckan -.->|"UF"| UF
    d_br_mjsp_procurados -.->|"estado"| UF
    d_br_mjsp_sinesp -.->|"cód_ibge +1"| MUNICIPIO
    d_br_mjsp_sinesp -->|"sigla_uf"| UF
    d_br_mjsp_sisdepen -->|"cep"| CEP
    d_br_mjsp_sisdepen -.->|"municipio +5"| MUNICIPIO
    d_br_mjsp_sisdepen -.->|"uf"| UF
    d_br_pgfn_dividaativa -.->|"categoria"| CID10
    d_br_pgfn_dividaativa -.->|"CPF_CNPJ"| EMPRESA_CNPJ
    d_br_pgfn_dividaativa -.->|"CPF_CNPJ"| PESSOA_CPF
    d_br_rj_isp_estatisticas_seguranca -->|"id_municipio"| MUNICIPIO
    d_br_tcu_inidoneos -.->|"CPF_CNPJ"| EMPRESA_CNPJ
    d_br_tcu_inidoneos -.->|"MUNICIPIO"| MUNICIPIO
    d_br_tcu_inidoneos -.->|"CPF +1"| PESSOA_CPF
    d_br_tcu_inidoneos -.->|"UF"| UF
    d_br_ana_atlas_esgotos -->|"id_municipio"| MUNICIPIO
    d_br_ana_atlas_esgotos -->|"sigla_uf"| UF
    d_br_ana_telemetria -.->|"nmMunicipio +1"| MUNICIPIO
    d_br_ana_telemetria -.->|"nmEstado +1"| UF
    d_br_anatel_banda_larga_fixa -->|"cnpj"| EMPRESA_CNPJ
    d_br_anatel_banda_larga_fixa -->|"id_municipio"| MUNICIPIO
    d_br_anatel_banda_larga_fixa -->|"sigla_uf"| UF
    d_br_anatel_indice_brasileiro_conectividade -->|"id_municipio"| MUNICIPIO
    d_br_anatel_indice_brasileiro_conectividade -->|"sigla_uf"| UF
    d_br_geobr_mapas -.->|"categoria"| CID10
    d_br_geobr_mapas -->|"id_escola"| ESCOLA
    d_br_geobr_mapas -->|"id_municipio"| MUNICIPIO
    d_br_geobr_mapas -->|"id_setor_censitario"| SETOR_CENSITARIO
    d_br_geobr_mapas -->|"sigla_uf +1"| UF
    d_br_ibama_embargos -.->|"seq_tad;seq_decisao_judicial;dat_decisao_embargo;tipo_decisao;des_observacao;num_pessoa_interessado;interessado;cpf_cnpj_interessado;tipo_acao;dat_inclusao_acao;sit_cancelado;ultima_atualizacao_relatorio +1"| EMPRESA_CNPJ
    d_br_ibama_embargos -.->|"seq_tad;seq_hist_tad;dt_alteracao;des_status_formulario;sit_cancelado;num_tad;ser_tad;dat_embargo;dat_impressao;forma_entrega;num_processo;des_tad;cod_municipio;municipio;uf;des_localizacao;num_longitude_tad;num_latitude_tad;deter_prodes;id_poligono;embarga_poligono;qtd_area_embargada;nome_imovel;tipo_area;wkt;unid_apresentacao;unid_controle;sit_desembargo;dat_desembargo;des_desembargo;seq_auto_infracao;seq_notificacao;seq_acao_fiscalizatoria;operacao;seq_ordem_fiscalizacao;ordem_fiscalizacao;unid_ordenadora;seq_solicitacao_recurso;solicitacao_recurso;operacao_sol_recurso;dat_ult_alteracao;tipo_alteracao;justificativa_alteracao;ultima_atualizacao_relatorio +1"| MUNICIPIO
    d_br_ibama_embargos -.->|"seq_tad;seq_decisao_judicial;dat_decisao_embargo;tipo_decisao;des_observacao;num_pessoa_interessado;interessado;cpf_cnpj_interessado;tipo_acao;dat_inclusao_acao;sit_cancelado;ultima_atualizacao_relatorio +1"| PESSOA_CPF
    d_br_inmet_bdmep -->|"id_municipio"| MUNICIPIO
    d_br_inpe_prodes -->|"id_municipio"| MUNICIPIO
    d_br_inpe_queimadas -->|"id_municipio"| MUNICIPIO
    d_br_inpe_queimadas -->|"sigla_uf"| UF
    d_br_inpe_sisam -->|"id_municipio"| MUNICIPIO
    d_br_inpe_sisam -->|"sigla_uf"| UF
    d_br_ipea_acesso_oportunidades -->|"id_municipio"| MUNICIPIO
    d_br_mapbiomas_estatisticas -->|"id_municipio"| MUNICIPIO
    d_br_mapbiomas_estatisticas -->|"sigla_uf"| UF
    d_br_mdr_snis -->|"id_municipio"| MUNICIPIO
    d_br_mdr_snis -->|"sigla_uf"| UF
    d_br_mma_extincao -.->|"categoria"| CID10
    d_br_mobilidados_indicadores -->|"id_municipio"| MUNICIPIO
    d_br_mobilidados_indicadores -->|"sigla_uf"| UF
    d_br_seeg_emissoes -.->|"categoria +1"| CID10
    d_br_seeg_emissoes -->|"id_municipio"| MUNICIPIO
    d_br_seeg_emissoes -->|"sigla_uf"| UF
    d_br_sfb_sicar -->|"id_municipio"| MUNICIPIO
    d_br_sfb_sicar -->|"sigla_uf"| UF
    d_world_wwf_hydrosheds -.->|"country"| PAIS
    d_br_abrinq_oca -->|"id_municipio"| MUNICIPIO
    d_br_ibge_censo2022_raca -->|"id_municipio"| MUNICIPIO
    d_br_ibge_censo2022_religiao -->|"id_municipio"| MUNICIPIO
    d_br_ibge_censo_2022 -->|"cep"| CEP
    d_br_ibge_censo_2022 -->|"id_municipio"| MUNICIPIO
    d_br_ibge_censo_2022 -->|"id_setor_censitario"| SETOR_CENSITARIO
    d_br_ibge_censo_2022 -->|"sigla_uf +1"| UF
    d_br_ibge_censo_demografico -->|"id_municipio"| MUNICIPIO
    d_br_ibge_censo_demografico -.->|"numero_familia"| PESSOA_CPF
    d_br_ibge_censo_demografico -->|"id_setor_censitario"| SETOR_CENSITARIO
    d_br_ibge_censo_demografico -->|"sigla_uf"| UF
    d_br_ibge_estadic -->|"sigla_uf"| UF
    d_br_ibge_munic -->|"id_municipio"| MUNICIPIO
    d_br_ibge_munic -->|"sigla_uf"| UF
    d_br_ibge_nomes_brasil -->|"id_municipio"| MUNICIPIO
    d_br_ibge_pnad -.->|"numero_familia"| PESSOA_CPF
    d_br_ibge_pnad -->|"sigla_uf +1"| UF
    d_br_ibge_pnadc -->|"id_municipio"| MUNICIPIO
    d_br_ibge_pnadc -->|"sigla_uf +1"| UF
    d_br_ibge_pof -->|"sigla_uf"| UF
    d_br_ibge_populacao -->|"id_municipio"| MUNICIPIO
    d_br_ibge_populacao -->|"sigla_uf"| UF
    d_br_ipea_avs -->|"id_municipio"| MUNICIPIO
    d_br_ipea_avs -->|"sigla_uf"| UF
    d_br_mg_belohorizonte_smfa_iptu -->|"cep"| CEP
    d_br_sp_saopaulo_geosampa_iptu -->|"cep"| CEP
    d_world_oecd_public_finance -.->|"country"| PAIS
    d_world_olympedia_olympics -.->|"city"| MUNICIPIO
    d_world_olympedia_olympics -.->|"country"| PAIS
    d_world_wb_mides -->|"cep"| CEP
    d_world_wb_mides -.->|"documento"| EMPRESA_CNPJ
    d_world_wb_mides -->|"id_municipio"| MUNICIPIO
    d_world_wb_mides -.->|"nome_orgao"| ORGAO
    d_world_wb_mides -->|"sigla_uf"| UF
    d_world_wb_mides -->|"id_unidade_gestora"| UNIDADE_GESTORA
```

## Sem ligação documentada

37 datasets não têm nenhuma chave que chegue a um hub — estão no espelho, mas nada documentado os liga a mais nada:

- `br_ana_reservatorios`
- `br_anac_dadosabertos`
- `br_anvisa_consultas`
- `br_bcb_sgs`
- `br_bd_diretorios_data_tempo`
- `br_caixa_sorteios`
- `br_ce_fortaleza_sefin_iptu`
- `br_fgv_igp`
- `br_fipe_veiculos`
- `br_ggb_relatorio_lgbtqi`
- `br_ibge_ipp`
- `br_ibge_pnad_covid`
- `br_ipea_atlasviolencia`
- `br_me_estoque_divida_publica`
- `br_me_exportadoras_importadoras`
- `br_me_siape`
- `br_me_sic`
- `br_me_siorg`
- `br_mec_prouni`
- `br_stf_corte_aberta`
- `br_stj_dadosabertos`
- `br_tce_to`
- `br_tcu_dadosabertos`
- `eu_sanctions`
- `global_ibge_tabua_mares`
- `global_icij_offshoreleaks`
- `global_ofac_sanctions`
- `global_opensanctions`
- `mundo_transfermarkt_competicoes`
- `mundo_transfermarkt_competicoes_internacionais`
- `un_sanctions`
- `us_harvard_ned`
- `world_ampas_oscar`
- `world_iea_pirls`
- `world_iea_timss`
- `world_imdb_movies`
- `world_sofascore_competicoes_futebol`
