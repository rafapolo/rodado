# Datasets to Scrap

Datasets from br-acc not present in `basedosdados.duckdb`.

Legend: `auth` = none (public), `api_key` (requires registration), `token` (OAuth/specific)

## Portal da Transparência

| Source | Pipeline | Node Types | Auth | Source URL | Format |
|--------|----------|------------|------|------------|--------|
| Portal da Transparência | `transparencia` | Contract, PublicOffice, Amendment | api_key | `https://api.portaldatransparencia.gov.br/api-de-dados` | JSON |
| Portal da Transparência | `renuncias` | TaxWaiver | api_key | `https://api.portaldatransparencia.gov.br/api-de-dados/renuncias` | JSON |
| Portal da Transparência | `viagens` | GovTravel | api_key | `https://api.portaldatransparencia.gov.br/api-de-dados/viagens-por-cpf` | JSON |

## Compras Públicas

| Source | Pipeline | Node Types | Auth | Source URL | Format |
|--------|----------|------------|------|------------|--------|
| PNCP | `pncp` | Bid | none | `https://pncp.gov.br/api/consulta/v1` | JSON |
| PNCP/Comprasnet | `comprasnet` | Contract, Bid | none | `https://dadosabertos.compras.gov.br` | JSON |
| CEPIM | `cepim` | BarredNGO | api_key | `https://api.portaldatransparencia.gov.br/api-de-dados/cepim` | JSON |
| Contratos.gov.br | `contratos` | Contract | none | `https://contratos.comprasnet.gov.br/api` | JSON |

## Dívida e Execução

| Source | Pipeline | Node Types | Auth | Source URL | Format |
|--------|----------|------------|------|------------|--------|
| PGFN | `pgfn` | Finance | none | `https://www.gov.br/pgfn/pt-br/acesso-a-informacao/dados-abertos` | CSV (bulk) |
| BCB Penalties | `bcb` | BCBPenalty | none | `https://dadosabertos.bcb.gov.br` | JSON/CSV/ZIP |
| IBAMA | `ibama` | Embargo | none | `https://www.ibama.gov.br/servicos/embargos` | CSV (scrape) |

## Sanções e PEPs

| Source | Pipeline | Node Types | Auth | Source URL | Format |
|--------|----------|------------|------|------------|--------|
| OFAC | `ofac` | InternationalSanction | none | `https://home.treasury.gov/policy-issues/financial-sanctions` | CSV/JSON |
| EU Sanctions | `eu_sanctions` | InternationalSanction | none | `https://data.europa.eu/data/datasets?keywords=sanctions` | JSON/CSV |
| UN Sanctions | `un_sanctions` | InternationalSanction | none | `https://www.un.org/securitycouncil/sanctions/` | CSV/XML |
| OpenSanctions | `opensanctions` | GlobalPEP | none | `https://www.opensanctions.org/` | JSON |
| CEIS | `cejs` | Sanction | api_key | `https://api.portaldatransparencia.gov.br/api-de-dados/cejs` | JSON |
| CNEP | `cnep` | Sanction | api_key | `https://api.portaldatransparencia.gov.br/api-de-dados/cnep` | JSON |
| CEAF | `ceaf` | Sanction | api_key | `https://api.portaldatransparencia.gov.br/api-de-dados/ceaf` | JSON |
| CGU PEP | `pep_cgu` | PEPRecord | none | `https://portaldatransparencia.gov.br/peps` | CSV |

## Outros

| Source | Pipeline | Node Types | Auth | Source URL | Format |
|--------|----------|------------|------|------------|--------|
| CGU Leniência | `leniency` | LeniencyAgreement | none | `https://www.gov.br/cgu/pt-br/assuntos/transparencia-publica/acordos-de-leniencia` | CSV/XLSX |
| DOU | `dou` | DOUAct | none | `https://www.in.gov.br/palavras-busca/palavras-busca.json` | JSON |
| STF | `stf` | — | none | `https://jurisprudencia.stf.jus.br/api/search/pesquisar` | JSON |
| STJ | `stj_dados_abertos` | — | none | `https://www.stj.jus.br/sites/STP/sjson/` | JSON |
| TST | `tst` | — | none | `https://jurisprudencia-backend.tst.jus.br/rest/documentos` | JSON |
| TCU | `tcu` | — | none | `https://dadosabertos.apps.tcu.gov.br/api` | JSON |
| BNDES | `bndes` | — | none | `https://dadosabertos.bndes.gov.br/api/3/action` | JSON (CKAN) |
| CPGF | `cpgf` | — | none | `https://portaldatransparencia.gov.br/cartoes/consulta` | CSV |
| DataJud | `datajud` | — | api_key | `https://datajud.cnj.jus.br` | JSON |
| DataSUS | `datasus` | — | none | `https://datasus.saude.gov.br/` | CSV/D BF/ZIP |
| ICIJ | `icij` | — | none | `https://offshoreleaks.icij.org/` | CSV/JSON |
| INEP | `inep` | — | none | `https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos` | CSV/XLSX/ZIP |
| Querido Diário | `querido_diario` | — | none | `https://queridodiario.ok.org.br/api/docs` | JSON |
| SIOP | `siop` | — | none | `https://www.planejamento.gov.br/` | CSV/XLSX |
| SICONFI | `siconfi` | — | none | `https://siconfi.tesouro.gov.br/siconfi/index.jsf` | CSV/JSON/XLSX |
| Senado CPIs | `senado_cpis` | CPI | none | `https://legis.senado.gov.br/` | JSON/HTML |
| Câmara CPIs | `camara_inquiries` | Inquiry | none | `https://dadosabertos.camara.leg.br/` | JSON |
| Brasil.IO | `holdings` | HOLDING_DE | none | `https://brasil.io/datasets/` | CSV |
| Tesouro Emendas | `tesouro_emendas` | — | none | `https://www.tesourotransparente.gov.br/` | CSV/JSON |
| TransfereGov | `transferegov` | — | none | `https://api.transferegov.gestao.gov.br` | JSON (PostgREST) |

## mcp-brasil — Sources not in basedosdados.duckdb

Sources from https://github.com/jxnxts/mcp-brasil not in `basedosdados.duckdb`.

### Health

| Source | mcp-brasil | Auth | Source URL | Format |
|--------|------------|------|------------|--------|
| ANVISA | `anvisa` | none | `https://consultas.anvisa.gov.br/api/consulta` | JSON |
| DENASUS | `denasus` | none | `https://www.gov.br/saude/pt-br/composicao/denasus` | HTML (scrape) |
| Farmácia Popular | `farmacia_popular` | none | `https://apidadosabertos.saude.gov.br/cnes/estabelecimentos` | JSON |
| OpenDataSUS | `opendatasus` | none | `https://opendatasus.saude.gov.br/api/3/action` | JSON (CKAN) |
| Imunização/PNI | `imunizacao` | api_key | `https://imunizacao.saude.gov.br` | JSON |
| RENAME | `rename` | none | `https://www.gov.br/saude/pt-br/acesso-a-informacao/medicamentos/rename` | JSON (static) |

### Legislative & Political

| Source | mcp-brasil | Auth | Source URL | Format |
|--------|------------|------|------------|--------|
| Câmara | `camara` | none | `https://dadosabertos.camara.leg.br/api/v2` | JSON |
| Senado | `senado` | none | `https://legis.senado.leg.br/dadosabertos` | JSON |
| TSE | `tse` | none | `https://divulgacandcontas.tse.jus.br/divulga/rest/v1` | JSON |

### Justice

| Source | mcp-brasil | Auth | Source URL | Format |
|--------|------------|------|------------|--------|
| DataJud | `datajud` | api_key | `https://datajud.cnj.jus.br` | JSON |
| Jurisprudência | `jurisprudencia` | none | `https://jurisprudencia.stf.jus.br`, `https://scon.stj.jus.br`, `https://jurisprudencia-backend.tst.jus.br` | JSON |

### Public Security

| Source | mcp-brasil | Auth | Source URL | Format |
|--------|------------|------|------------|--------|
| Atlas da Violência | `atlas_violencia` | none | `https://www.ipea.gov.br/atlasviolencia/api/v1` | JSON |
| SINESP/MJSP | `sinesp` | none | `https://dados.mj.gov.br/api/3/action` | JSON (CKAN) |
| Fórum Segurança | `forum_seguranca` | none | `https://publicacoes.forumseguranca.org.br/server/api` | JSON |

### Finance & Economy

| Source | mcp-brasil | Auth | Source URL | Format |
|--------|------------|------|------------|--------|
| BCB/BACEN | `bacen` | none | `https://api.bcb.gov.br/dados/serie/bcdata.sgs` | JSON |
| BNDES | `bndes` | none | `https://dadosabertos.bndes.gov.br/api/3/action` | JSON (CKAN) |
| BPS | `bps` | none | `https://apidadosabertos.saude.gov.br/economia-da-saude/bps` | CSV |

### Government Transparency

| Source | mcp-brasil | Auth | Source URL | Format |
|--------|------------|------|------------|--------|
| Transparência | `transparencia` | api_key | `https://api.portaldatransparencia.gov.br/api-de-dados` | JSON |
| TransfereGov | `transferegov` | none | `https://api.transferegov.gestao.gov.br` | JSON (PostgREST) |
| Diário Oficial | `diario_oficial` | none | `https://queridodiario.ok.org.br/api/docs` | JSON |

### TCEs

| Source | mcp-brasil | Auth | Source URL | Format |
|--------|------------|------|------------|--------|
| TCE-CE | `tce_ce` | none | `https://api-dados-abertos.tce.ce.gov.br` | JSON |
| TCE-ES | `tce_es` | none | `https://dados.es.gov.br/api/3/action/datastore_search` | JSON (CKAN) |
| TCE-PE | `tce_pe` | none | `https://sistemas.tce.pe.gov.br/DadosAbertos` | JSON |
| TCE-PI | `tce_pi` | none | `https://sistemas.tce.pi.gov.br/api/portaldacidadania` | JSON |
| TCE-RJ | `tce_rj` | none | `https://dados.tcerj.tc.br/api/v1` | JSON |
| TCE-RN | `tce_rn` | none | `https://apidadosabertos.tce.rn.gov.br/api` | JSON |
| TCE-RS | `tce_rs` | none | `https://dados.tce.rs.gov.br` | JSON (CKAN) |
| TCE-SC | `tce_sc` | none | `https://servicos.tcesc.tc.br/endpoints-portal-transparencia` | JSON |
| TCE-SP | `tce_sp` | none | `https://transparencia.tce.sp.gov.br/api` | JSON |
| TCE-TO | `tce_to` | none | `https://api.tceto.tc.br/econtas/api` | JSON |

### Environment & Science

| Source | mcp-brasil | Auth | Source URL | Format |
|--------|------------|------|------------|--------|
| INPE | `inpe` | none | `https://terrabrasilis.dpi.inpe.br/queimadas/bdqueimadas-data-service` | JSON |
| Tabua Mares | `tabua_mares` | none | `https://tabuademares.com/api/v2` | JSON |

## Basedosdados.org — Not in basedosdados.duckdb (232 tables)

Basedosdados.org has **765 tables** on BigQuery, but only **533** are on S3 (and thus in your duckdb). The following datasets have **zero or partial** tables in duckdb.

### Full datasets — no tables in duckdb

| Dataset | Tables missing | Notes |
|---------|----------------|-------|
| `br_abrinq_oca` | municipio_primeira_infancia | |
| `br_ana_atlas_esgotos` | municipio | |
| `br_ana_reservatorios` | sin | |
| `br_anvisa_medicamentos_industrializados` | microdados | |
| `br_ba_feiradesantana_camara_leis` | microdados | |
| `br_bd_diretorios_data_tempo` | tempo, data, ano, mes, dia, hora, bimestre, trimestre, semestre, minuto, segundo | Directory of time dimensions |
| `br_bd_metadados` | external_links, information_requests, organizations, prefect_flows, resources, tables | BD metadata catalog |
| `br_bd_vizinhanca` | municipio, uf | |
| `br_caixa_sorteios` | megasena | |
| `br_camara_dados_abertos` | sigla_partido | |
| `br_capes_bolsas` | mobilidade_internacional | |
| `br_cgu_ebt` | municipio, uf | |
| `br_cgu_fef` | microdados, municipios_sorteados, sorteio | |
| `br_cgu_pessoal_executivo_federal` | terceirizados | |
| `br_clp_ranking_competitividade` | nota_geral_municipio, nota_geral_uf | |
| `br_cnj_estatisticas_poder_judiciario` | recursos_financeiros | |
| `br_fbsp_absp` | municipio | |
| `br_firjan_ifgf` | ranking | |
| `br_ggb_relatorio_lgbtqi` | brasil, causa_obito, grupo_lgbtqia, local, raca_cor | |
| `br_ibge_amc` | municipio_de_para | |
| `br_ibge_cbo_2002` | perfil_ocupacional, sinonimo | |
| `br_ibge_estadic` | comunicacao_informatica, educacao, governanca, indicadores_perfil_gestor, indicadores_quantidade_vinculo, politica_mulher, recursos_humanos | |
| `br_ibge_ipp` | mes_categoria_economica, mes_grupo_industrial, mes_industria_atividade, mes_industria_extrativa, mes_industria_geral, mes_industria_transformacao | |
| `br_ibge_munic` | indicadores_perfil_gestor, indicadores_quantidade_vinculo | |
| `br_ibge_nomes_brasil` | quantidade_municipio_nome_2010 | |
| `br_ieps_saude` | brasil, macrorregiao, municipio, regiao_saude, uf | |
| `br_imprensa_nacional_dou` | secao_1, secao_2, secao_3 | Official gazette sections |
| `br_ipea_acesso_oportunidades` | estatisticas_2019, indicadores_2019 | |
| `br_mapbiomas_estatisticas` | classe, cobertura_municipio_classe, cobertura_uf_classe, transicao_municipio_de_para_anual/decenal/quinquenal, transicao_uf_de_para_anual/decenal/quinquenal | |
| `br_mc_indicadores` | transferencias_municipio | |
| `br_me_clima_organizacional` | microdados | |
| `br_me_estoque_divida_publica` | microdados | |
| `br_me_exportadoras_importadoras` | dicionario, estabelecimentos | |
| `br_me_pensionistas` | microdados | |
| `br_me_siape` | servidores_executivo_federal | |
| `br_me_siorg` | remuneracao | |
| `br_mma_extincao` | fauna_ameacada, flora_ameacada | |
| `br_mobilidados_indicadores` | 11 tables (comprometimento_renda_tarifa_transp_publico, proporcao_*, taxa_motorizacao, etc.) | |
| `br_ms_atencao_basica` | municipio | |
| `br_ms_imunizacoes` | municipio | |
| `br_ons_energia_armazenada` | subsistemas | |
| `br_rj_rio_de_janeiro_ipp_ips` | dimensoes_componentes, indicadores | |
| `br_rj_tce_iegm` | indicadores | |
| `br_senado_cpipandemia` | discursos | |
| `br_sgp_informacao` | despesas_cartao_corporativo | |
| `br_sp_alesp` | assessores_lideranca, assessores_parlamentares, deputados, despesas_gabinete, despesas_gabinete_atual | |
| `br_sp_gov_orcamento` | despesa, receita_arrecadada, receita_prevista | |
| `br_sp_gov_ssp` | ocorrencias_registradas, produtividade_policial | |
| `br_sp_saopaulo_dieese_icv` | ano | |
| `br_sp_seduc_fluxo_escolar` | escola, municipio | |
| `br_sp_seduc_idesp` | diretoria, escola, uf | |
| `br_sp_seduc_inse` | escola | |
| `br_tpe_classificacao_saeb` | categoria | |
| `eu_fra_lgbt` | consciencia_direitos, cotidiano, discriminacao, especifico_transgenero, violencia_abuso | |
| `mundo_bm_learning_poverty` | pais | |
| `mundo_kaggle_olimpiadas` | microdados | |
| `mundo_onu_adh` | brasil, municipio, uf | |
| `mundo_transrespect_transphobia` | causa_obito, local, pais | |
| `nl_ug_pwt` | microdados | |
| `world_fao_production` | country_group, crop_livestock, dictionary, element, item, item_group, production_indices, value_agricultural_production | |
| `world_fifa_women_world_cup` | matches | |
| `world_fifa_worldcup` | award_winners, matches, players, teams, tournaments | |
| `world_gsps_consortium_gsps` | global_indicators | |
| `world_slave_voyages_consortium_slave_trade` | transatlantic | |
| `world_spi_spi` | global_indicators | |
| `world_ti_corruption_perception` | country | |
| `world_wb_wwbi` | country_finance, country_indicators | |

### Partial datasets — some tables in duckdb, some missing

| Dataset | Missing tables | In duckdb |
|---------|----------------|-----------|
| `br_anatel_banda_larga_fixa` | backhaul, pble | densidade_*, microdados |
| `br_bcb_sicor` | microdados_liberacao, microdados_operacao, microdados_saldo | dicionario, liberacao, operacao, saldo, recurso_publico_* |
| `br_bcb_taxa_cambio` | taxa_cambio | — (ACCESS_DENIED) |
| `br_bcb_taxa_selic` | taxa_selic | — (ACCESS_DENIED) |
| `br_ibge_pib` | brasil_antigo, municipio_antigo, regiao_antigo, uf, uf_antigo | gini, municipio |
| `br_ibge_pnad_covid` | microdados | dicionario |
| `br_ibge_pnadc` | ano_brasil_grupo_idade, ano_brasil_raca_cor, ano_municipio_*, ano_regiao_*, ano_uf_* (cross-tabs) | dicionario, educacao, microdados, rendimentos_outras_fontes |
| `br_ibge_pof` | all 17 tables (morador, domicilio, despesa_*, consumo_*, etc.) | none |
| `br_inep_ana` | aluno, escola, prova | dicionario |
| `br_inep_censo_escolar` | docente, matricula | dicionario, escola, turma |
| `br_inep_formacao_docente` | brasil, escola, municipio, regiao, uf | dicionario |
| `br_inep_indicador_nivel_socioeconomico` | brasil, municipio, uf | dicionario, escola |
| `br_inep_indicadores_educacionais` | escola_nivel_socioeconomico, fluxo_educacao_superior | all others |
| `br_inmet_bdmep` | estacao | microdados |
| `br_me_caged` | microdados_antigos, microdados_antigos_ajustes | dicionario, microdados_movimentacao* |
| `br_me_cno` | microdados, microdados_cnae, microdados_vinculo | dicionario, microdados |
| `br_me_rais` | all tables | dicionario, microdados_estabelecimentos, microdados_vinculos |
| `br_mec_prouni` | microdados | dicionario |
| `br_ms_sim` | municipio, municipio_causa, municipio_causa_idade, municipio_causa_idade_sexo_raca | dicionario, microdados |
| `br_ms_sinan` | microdados_violencia | dicionario, microdados_dengue, microdados_influenza_srag |
| `br_ms_vacinacao_covid19` | microdados, microdados_estabelecimento, microdados_paciente, microdados_vacinacao | dicionario |
| `br_seeg_emissoes` | brasil | dicionario, municipio, uf |
| `br_tse_eleicoes` | local_secao | all others |
| `world_oecd_pisa` | dictionary, school_summary, student_summary | student |
