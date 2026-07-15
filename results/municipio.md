# Atributos por município

195+ tabelas têm `id_municipio` como chave de junção. Abaixo, as principais agrupadas por tema.

## Índice

- [Diretório Canônico](#diretório-canônico-br_bd_diretorios_brasilmunicipio)
- [Demografia & População](#demografia--população)
- [Geografia & Mapas](#geografia--mapas)
- [Economia & Finanças](#economia--finanças)
- [Educação](#educação)
- [Saúde](#saúde)
- [Segurança Pública](#segurança-pública)
- [Infraestrutura & Saneamento](#infraestrutura--saneamento)
- [Meio Ambiente & Clima](#meio-ambiente--clima)
- [Conectividade & Tecnologia](#conectividade--tecnologia)
- [Política & Eleições](#política--eleições)
- [Transparência & Governança](#transparência--governança)
- [Social & Vulnerabilidade](#social--vulnerabilidade)
- [Comércio Exterior](#comércio-exterior)
- [Trabalho & Emprego](#trabalho--emprego)
- [Agropecuária](#agropecuária)
- [Benefícios Sociais](#benefícios-sociais)
- [Vizinhança](#vizinhança)

---

## Diretório Canônico (`br_bd_diretorios_brasil.municipio`)

27 colunas — tabela mestre que mapeia o código IBGE de 7 dígitos para toda hierarquia geográfica.

| Coluna | Descrição |
|--------|-----------|
| `id_municipio` | Código IBGE 7 dígitos (chave canônica, ex: `3550308` = São Paulo) |
| `id_municipio_6` | Código IBGE 6 dígitos (formato antigo) |
| `id_municipio_tse` | Código TSE (Justiça Eleitoral) |
| `id_municipio_rf` | Código Receita Federal |
| `id_municipio_bcb` | Código Banco Central |
| `nome` | Nome do município |
| `sigla_uf` | Sigla do estado |
| `id_uf` | ID do estado |
| `nome_uf` | Nome do estado |
| `nome_regiao` | Região (Norte, Nordeste, Sudeste, Sul, Centro-Oeste) |
| `capital_uf` | É capital? (1 = sim, 0 = não) |
| `id_microrregiao` | Código microrregião IBGE |
| `nome_microrregiao` | Nome da microrregião |
| `id_mesorregiao` | Código mesorregião IBGE |
| `nome_mesorregiao` | Nome da mesorregião |
| `id_regiao_imediata` | Código região imediata IBGE |
| `nome_regiao_imediata` | Nome da região imediata |
| `id_regiao_intermediaria` | Código região intermediária IBGE |
| `nome_regiao_intermediaria` | Nome da região intermediária |
| `id_regiao_saude` | Código região de saúde |
| `nome_regiao_saude` | Nome da região de saúde |
| `id_regiao_metropolitana` | Código região metropolitana |
| `nome_regiao_metropolitana` | Nome da região metropolitana |
| `id_comarca` | Código da comarca (judiciário) |
| `ddd` | Código de área (DDD) |
| `amazonia_legal` | Está na Amazônia Legal? (1 = sim, 0 = não) |
| `centroide` | Centroide geográfico (espacial) |

---

## Demografia & População

### População (`br_ibge_populacao.municipio`)
- `ano`, `populacao` (estimativa anual)

### População por sexo/idade (`br_ms_populacao.municipio`)
- `ano`, `sexo`, `grupo_idade`, `populacao`

### Censo 2022 (`br_ibge_censo_2022.municipio`)
- `domicilios`, `populacao`, `area`, `taxa_alfabetizacao`, `idade_mediana`, `razao_sexo`, `indice_envelhecimento`, `populacao_indigena`

### Censo 2022 — desagregações (`br_ibge_censo_2022.*`)
- `alfabetizacao_grupo_idade_sexo_raca`: alfabetização por faixa etária, sexo e raça
- `caracteristica_domicilio_*`: características dos domicílios (várias tabelas)
- `domicilio_recenseado`: domicílios recenseados
- `indice_envelhecimento_raca`: índice de envelhecimento por raça
- `populacao_grupo_idade_sexo_raca`: população por faixa etária, sexo e raça
- `populacao_idade_sexo`: população por idade e sexo
- `setor_censitario`: dados por setor censitário

### Censo Demográfico — microdados históricos (`br_ibge_censo_demografico.*`)
- `microdados_domicilio_1970`, `_1980`, `_1991`, `_2000`, `_2010`
- `microdados_pessoa_1970`, `_1980`, `_1991`, `_2000`, `_2010`

---

## Geografia & Mapas

### Mapas (`br_geobr_mapas.*`)
- `municipio`: geometria do polígono municipal (GeoParquet)
- `area_minima_comparavel_2010`: áreas mínimas comparáveis entre censos
- `area_risco_desastre`: áreas de risco de desastre
- `arranjo_populacional`: arranjos populacionais IBGE
- `concentracao_urbana`: concentrações urbanas
- `estabelecimentos_saude`: estabelecimentos de saúde georreferenciados
- `limite_vizinhanca`: limites de vizinhança
- `pegada_urbana`: pegada urbana
- `regiao_metropolitana_2017`: regiões metropolitanas
- `sede_municipal`: sede do município (ponto)
- `semiarido`: delimitação do semiárido
- `setor_censitario_2010`: setores censitários 2010

---

## Economia & Finanças

### PIB (`br_ibge_pib.municipio`)
- `ano`, `pib`, `impostos_liquidos`, `va` (valor adicionado total), `va_agropecuaria`, `va_industria`, `va_servicos`, `va_adespss` (Adm. Pública)

### Finanças públicas — SICONFI (`br_me_siconfi.*`)
- `municipio_balanco_patrimonial`: balanço patrimonial (conta, valor)
- `municipio_despesas_funcao`: despesas por função (estágio, conta, valor)
- `municipio_despesas_orcamentarias`: despesas orçamentárias
- `municipio_receitas_orcamentarias`: receitas orçamentárias

### Inflação
- `br_ibge_inpc.mes_categoria_municipio`: INPC (peso mensal, variação mensal/anual/12 meses, por categoria)
- `br_ibge_ipca.mes_categoria_municipio`: IPCA (mesma estrutura)
- `br_ibge_ipca15.mes_categoria_municipio`: IPCA-15 (mesma estrutura)

### Atividade bancária (`br_bcb_estban.municipio`)
- `ano`, `mes`, `cnpj_basico`, `instituicao`, `agencias_esperadas`, `agencias_processadas`, `id_verbete`, `valor`

### Compras públicas
- `br_cgu_licitacao_contrato.licitacao`: licitações municipais
- `world_wb_mides.*`: empenho, licitação, licitação_item, licitação_participante, liquidação, órgão unidade gestora, pagamento, relacionamentos

### Impostos e cadastro rural
- `br_rf_arrecadacao.itr`: arrecadação ITR
- `br_rf_cafir.imoveis_rurais`: imóveis rurais (CAFIR)
- `br_rf_cno.microdados`: Cadastro Nacional de Obras
- `br_sfb_sicar.area_imovel`: áreas de imóveis (SICAR)

---

## Educação

### IDEB (`br_inep_ideb.municipio`)
- `ano`, `rede`, `ensino`, `anos_escolares`, `taxa_aprovacao`, `indicador_rendimento`, `nota_saeb_matematica`, `nota_saeb_lingua_portuguesa`, `nota_saeb_media_padronizada`

### SAEB (`br_inep_saeb.municipio`)
- `ano`, `rede`, `localizacao`, `disciplina`, `serie`, `media`, `nivel_0`, `nivel_1`, `nivel_2` (proporções)

### Indicadores Educacionais (`br_inep_indicadores_educacionais.municipio`)
- **215 colunas** — ATU (Atendimento Territorial Urbano) por creche, pré-escola, EF anos iniciais/finais, localização, rede

### Taxas de Transição (`br_inep_indicadores_educacionais.municipio_taxa_transicao`)
- `taxa_evasao_ef`, `taxa_evasao_ef_5_ano` (68 colunas no total)

### Alfabetização (`br_inep_avaliacao_alfabetizacao.municipio`)
- `ano`, `serie`, `rede`, `taxa_alfabetizacao`, `media_portugues`, `proporcao_aluno_nivel_0` a `nivel_3`

### Metas de Alfabetização (`br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_municipio`)
- `taxa_alfabetizacao`, `meta_alfabetizacao_2024` a `meta_alfabetizacao_2030`

### Censo Escolar (`br_inep_censo_escolar.*`)
- `escola`: escolas (com `id_municipio`)
- `turma`: turmas

### ENEM (`br_inep_enem.microdados`)
- microdados com `id_municipio` (prova, escola, participante)

### Educação Superior (`br_inep_censo_educacao_superior.*`)
- `curso`: cursos superiores
- `ies`: instituições de ensino superior (`id_municipio` na IES)

---

## Saúde

### CNES — Cadastro Nacional de Estabelecimentos de Saúde (`br_ms_cnes.*`)
- `estabelecimento`, `leito`, `profissional`, `equipamento`, `equipe`

### SINAN — Agravos de Notificação (`br_ms_sinan.*`)
- `microdados_dengue`, `microdados_influenza_srag` (SRAG/influenza)

### SINASC — Nascidos Vivos (`br_ms_sinasc.microdados`)

### SISVAN — Vigilância Alimentar (`br_ms_sisvan.microdados`)

### SIA — Produção Ambulatorial (`br_ms_sia.producao_ambulatorial`, `psicossocial`)

---

## Segurança Pública

### FBSP — Anuário Brasileiro de Segurança Pública (`br_fbsp_absp.municipio`)
- `proporcao_mortes_intenvencao_policial_x_mortes_violentas_intencionais`
- `quantidade_estupro`
- `quantidade_feminicidio`
- `quantidade_furto_veiculos`
- `quantidade_homicidio_doloso`
- `quantidade_latrocinio`
- `quantidade_lesao_corporal_dolosa_violencia_domestica`
- `quantidade_lesao_corporal_morte`
- `quantidade_morte_policiais_civis_confronto_em_servico`
- `quantidade_morte_policiais_civis_fora_de_servico`
- `quantidade_morte_policiais_militares_confronto_em_servico`
- `quantidade_morte_policiais_militares_fora_de_servico`
- `quantidade_mortes_intervencao_policial`
- `quantidade_mortes_intervencao_policial_civil_em_servico`
- `quantidade_mortes_intervencao_policial_civil_fora_de_servico`
- `quantidade_mortes_intervencao_policial_militar_em_servico`
- `quantidade_mortes_intervencao_policial_militar_fora_de_servico`
- `quantidade_mortes_policiais_confronto`
- `quantidade_mortes_violentas_intencionais`
- `quantidade_porte_ilegal_arma_de_fogo`
- `quantidade_posse_ilegal_arma_de_fogo`
- `quantidade_posse_ilegal_porte_ilegal_arma_de_fogo`
- `quantidade_posse_uso_entorpecente`
- `quantidade_roubo_furto_veiculos`
- `quantidade_roubo_veiculos`
- `quantidade_trafico_entorpecente`

### ISP-RJ — Estatísticas de Segurança do RJ (`br_rj_isp_estatisticas_seguranca.*`)
- `evolucao_mensal_municipio`: homicídio doloso, latrocínio, lesão corporal morte, crimes violentos letais intencionais, letalidade violenta, tentativa homicídio, intervenção policial + 47 outras (58 colunas)
- `taxa_evolucao_anual_municipio`: taxas por 100 mil hab (56 colunas)
- `taxa_evolucao_mensal_municipio`: taxas mensais (58 colunas)
- `evolucao_mensal_cisp`: por CISP (circunscrição policial)
- `feminicidio_mensal_cisp`
- `armas_fogo_apreendidas_mensal`
- `relacao_cisp_aisp_risp`

---

## Infraestrutura & Saneamento

### Atlas Esgotos — ANA (`br_ana_atlas_esgotos.municipio`)
- `populacao_urbana_2013`, `populacao_urbana_2035`
- `prestador_servico_esgotamento_sanitario`, `sigla_prestador`
- `indice_sem_atendimento_sem_coleta_sem_tratamento`
- `indice_atendimento_solucao_individual`
- `indice_atendimento_com_coleta_sem_tratamento`
- `indice_atendimento_com_coleta_com_tratamento`
- `vazao_sem_coleta_sem_tratamento`, `vazao_solucao_individual`, `vazao_com_coleta_sem_tratamento`, `vazao_com_coleta_com_tratamento`, `vazao_total`
- `carga_gerada_*` (várias), `carga_lancada_*` (várias)
- `indice_atendimento_etes_2035`, `indice_atendimento_solucao_individual_2035`
- `carga_gerada_total_2035`, `carga_afluente_ete_2035`, `carga_efluente_ete_2035`
- `carga_afluente_solucao_individual_2035`, `carga_efluente_solucao_individual_2035`
- `populacao_atendida_2035`
- `investimento_coleta`, `investimento_tratamento`, `investimento_coleta_tratatamento`
- `necessidade_remocao_dbo`, `tipologia_solucao`
- `atencao_fosforo`, `atencao_nitrogenio`

### SNIS — Água e Esgoto (`br_mdr_snis.municipio_agua_esgoto`)
- **133 colunas** — população atendida água/esgoto, população urbana, consumidores, economias ativas, volume consumido/produzido, extensão rede, ligações ativas, hidrômetros, despesas, arrecadação, tarifas, etc.

---

## Meio Ambiente & Clima

### Desmatamento — PRODES (`br_inpe_prodes.municipio_bioma`)
- `ano`, `bioma`, `area_total`, `desmatado`, `vegetacao_natural`, `nao_vegetacao_natural`, `hidrografia`

### Emissões — SEEG (`br_seeg_emissoes.municipio`)
- `ano`, `bioma`, `gas`, `tipo`, `recorte`, `setor`, `atividade_economica`, `categoria`, `subcategoria` + 6 indicadores de emissão

---

## Conectividade & Tecnologia

### Banda Larga Fixa (`br_anatel_banda_larga_fixa.densidade_municipio`)
- `ano`, `mes`, `densidade`

### Índice Brasileiro de Conectividade (`br_anatel_indice_brasileiro_conectividade.municipio`)
- `ibc`, `cobertura_pop_4g5g`, `fibra`, `densidade_smp`, `hhi_smp`, `densidade_scm`, `hhi_scm`, `adensamento_estacoes`

---

## Política & Eleições

### Detalhes da Votação (`br_tse_eleicoes.detalhes_votacao_municipio`)
- `ano`, `turno`, `cargo`, `aptos`, `secoes`, `votos_nominais`, `votos_legenda`, `votos_brancos`, `votos_nulos`, `votos_anulados_aptos` (25 colunas)

### Detalhes por Zona (`detalhes_votacao_municipio_zona`)
- mesmo que acima + `zona` eleitoral

### Perfil do Eleitorado (`perfil_eleitorado_municipio_zona`)
- `genero`, `estado_civil`, `grupo_idade`, `instrucao`, `situacao_biometria`, `eleitores`, `eleitores_biometria`

### Resultados por Candidato (`resultados_candidato_municipio`)
- `ano`, `cargo`, `numero_partido`, `sigla_partido`, `titulo_eleitoral_candidato`, `votos_nominais`, `qtd_votos` (16 colunas)

### Resultados por Partido (`resultados_partido_municipio`)
- `ano`, `cargo`, `numero_partido`, `sigla_partido`, `votos_nominais`, `qtd_votos` (13 colunas)

### Resultados por Zona
- versões com `_zona` de todas as tabelas acima

### Demais tabelas TSE
- `candidatos`, `despesas_candidato`, `detalhes_votacao_secao`, `partidos`, `perfil_eleitorado_local_votacao`, `perfil_eleitorado_secao`, `receitas_candidato`, `receitas_comite`, `receitas_orgao_partidario`, `resultados_candidato_secao`, `resultados_partido_secao`, `vagas`
- `br_tse_filiacao_partidaria.microdados`, `microdados_antigos`

---

## Transparência & Governança

### Escala Brasil Transparente (`br_cgu_ebt.municipio`)
- `nota`, `ranking` (transparência pública)

### Municípios Sorteados — CGU (`br_cgu_fef.municipios_sorteados`)
- `sorteio` (número do sorteio de auditoria)

### Ranking de Competitividade — CLP (`br_clp_ranking_competitividade.nota_geral_municipio`)
- `colocacao`, `nota_geral`, `pilar_dimensao`

---

## Social & Vulnerabilidade

### IVS — Índice de Vulnerabilidade Social (`br_ipea_avs.municipio`)
- `raca_cor`, `sexo`, `localizacao`
- `ivs` (geral)
- `ivs_infraestrutura_urbana`
- `ivs_capital_humano`
- `ivs_renda_trabalho`
- `udh` (Índice de Desenvolvimento Humano)
- +81 colunas adicionais

### Primeira Infância (`br_abrinq_oca.municipio_primeira_infancia`)
- `taxa_bruta_matricula_pre_escola`, `numero_absoluto_bruto_matricula_pre_escola`
- `taxa_liquida_matricula_pre_escola`, `numero_absoluto_liquido_matricula_pre_escola`

---

## Comércio Exterior

### Exportações (`br_me_comex_stat.municipio_exportacao`)
- `ano`, `mes`, `id_sh4` (produto), `id_pais`, `sigla_pais_iso3`, `peso_liquido_kg`, `valor_fob_dolar`

### Importações (`br_me_comex_stat.municipio_importacao`)
- mesma estrutura

---

## Trabalho & Emprego

### CAGED (`br_me_caged.microdados_movimentacao`)
- microdados de movimentação de trabalhadores (admissões e desligamentos)

### RAIS (`br_me_rais.*`)
- `microdados_vinculos`: vínculos empregatícios
- `microdados_estabelecimentos`: estabelecimentos

### CNPJ (`br_me_cnpj.estabelecimentos`)
- estabelecimentos com `id_municipio`

---

## Agropecuária

### PAM — Produção Agrícola Municipal (`br_ibge_pam.*`)
- `lavoura_permanente`: área plantada, área colhida, quantidade produzida, rendimento médio, valor produção (culturas permanentes)
- `lavoura_temporaria`: mesma estrutura (culturas temporárias)

### PPM — Produção Pecuária Municipal (`br_ibge_ppm.*`)
- `efetivo_rebanhos`: cabeças por tipo de rebanho
- `producao_aquicultura`: produção aquícola
- `producao_origem_animal`: produção de origem animal (leite, ovos, mel, etc.)

---

## Benefícios Sociais

### CGU — Benefícios ao Cidadão (`br_cgu_beneficios_cidadao.*`)
- `auxilio_brasil`: pagamentos do Auxílio Brasil
- `auxilio_emergencial`: Auxílio Emergencial (COVID-19)
- `bolsa_familia_pagamento`: Bolsa Família
- `bpc`: Benefício de Prestação Continuada
- `garantia_safra`: Garantia-Safra
- `novo_bolsa_familia`: Novo Bolsa Família

---

## Vizinhança

### `br_bd_vizinhanca.municipio`
- `ano`, `id_municipio_1`, `id_municipio_2` (pares de municípios vizinhos)
