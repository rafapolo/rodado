# Relatório Final — Perguntas Sociológicas Respondidas pela Base dos Dados

**Repositório:** `basedosdados`
**Data:** Abril 2026
**Escopo:** 50 perguntas de pesquisa em ciências sociais, organizadas em 16 temas

---

## Sumário Executivo

Este relatório apresenta 50 perguntas de pesquisa em ciências sociais que podem ser respondidas utilizando a Base dos Dados Brasil. Para cada tema, identificamos as tabelas, colunas e relações entre bases que permitem investigar questões sociológicas complexas sobre desigualdade, educação, saúde, trabalho, política, meio ambiente e desenvolvimento.

---

## Tabela de Temas e Fontes

| # | Tema | Tabelas Principais | Tamanho Total |
|---|------|-------------------|---------------|
| 01 | Desigualdade Racial e Estratificação | `br_ibge_censo_2022.populacao_grupo_idade_sexo_raca`, `br_ms_sim.microdados`, `br_me_rais.microdados_vinculos` | 5,4 MB + 1,4 GB + 51,1 GB |
| 02 | Educação, Mobilidade Social | `br_inep_enem.microdados`, `br_inep_ideb.*`, `br_inep_indicador_nivel_socioeconomico.escola` | 6,3 GB |
| 03 | Saúde e Determinantes Sociais | `br_ms_sinasc.microdados`, `br_ms_sim.microdados`, `br_ans_beneficiario.informacao_consolidada` | 1,4 GB + 8,3 GB |
| 04 | Mercado de Trabalho | `br_me_rais.microdados_vinculos`, `br_me_caged.microdados_movimentacao`, `br_ibge_pnadc.microdados` | 51,1 GB + 1,5 GB |
| 05 | Política e Representação | `br_tse_eleicoes.candidatos`, `br_camara_dados_abertos.deputado`, `br_tse_eleicoes.despesas_candidato` | 149 MB + 125 MB |
| 06 | Crime e Violência | `br_rj_isp_estatisticas_seguranca.taxa_evolucao_mensal_municipio`, `br_ms_sim.microdados` | 852 KB + 1,4 GB |
| 07 | Economia e Crédito | `br_bcb_sicor.operacao`, `br_bcb_estban.agencia`, `br_anatel_indice_brasileiro_conectividade.municipio` | 522 MB + 1,4 GB |
| 08 | Políticas Públicas | `br_cgu_beneficios_cidadao.bolsa_familia_pagamento`, `br_me_siconfi.*` | 25,8 GB |
| 09 | Gênero e Família | `br_ms_sinasc.microdados`, `br_me_caged.microdados_movimentacao`, `br_ibge_pnadc.microdados` | 1,4 GB + 1,5 GB |
| 10 | Meio Ambiente | `br_inpe_prodes.municipio_bioma`, `br_seeg_emissoes.*`, `br_trase_supply_chain.*` | 862 KB |
| 11 | Infraestrutura | `br_mdr_snis.municipio_agua_esgoto`, `br_anatel_banda_larga_fixa.densidade_municipio` | 31,3 MB |
| 12 | Interseccionalidade | `br_me_rais.microdados_vinculos`, `br_me_caged.microdados_movimentacao`, `br_rj_isp_estatisticas_seguranca.*` | 51,1 GB |
| 13 | Migração e Urbanização | `br_me_caged.microdados_movimentacao`, `br_ibge_populacao.municipio`, `br_ibge_censo_2022.*` | 1,5 GB |
| 14 | Consumo e Preços | `br_anp_precos_combustiveis.microdados`, `br_ibge_ipca.*`, `br_ibge_inpc.*` | 79 MB |
| 15 | Poder e Elites | `br_camara_dados_abertos.deputado`, `br_tse_eleicoes.candidatos`, `br_camara_dados_abertos.despesa` | 278 KB + 125 MB |
| 16 | Economia Política | `br_rf_arrecadacao.uf`, `br_me_siconfi.*`, `br_ibge_pib.municipio` | 1,7 MB |

---

## 01 — Desigualdade Racial e Estratificação Social

### Tabelas e Colunas

| Tabela | Colunas Chave | Tamanho |
|--------|---------------|---------|
| `br_ibge_censo_2022.populacao_grupo_idade_sexo_raca` | `populacao`, `grupo_idade`, `sexo`, `cor_raca` | 5,4 MB |
| `br_ms_sim.microdados` | `causa_basica`, `causa_violencia`, `idade`, `sexo`, `raca_cor` | 1,4 GB |
| `br_me_rais.microdados_vinculos` | `raca_cor`, `valor_remuneracao_media_sm`, `cbo_2002`, `cnae_2_subclasse` | 51,1 GB |
| `br_bd_diretorios_brasil.cid_10` | `subcategoria`, `descricao_subcategoria`, `causa_violencia` | 261 KB |
| `br_ibge_censo_demografico.setor_censitario_raca_idade_genero_2010` | cruzamento raça × idade × gênero no setor | — |
| `br_ibge_pib.gini` | `gini_pib`, `sigla_uf`, `ano` | 25 KB |

### Perguntas Respondíveis

- **Q1:** Cruzando `populacao` × `cor_raca` × `grupo_idade` no Census 2022 com `valor_remuneracao_media_sm` × `raca_cor` na RAIS, é possível medir a evolução da desigualdade racial entre censos.
- **Q2:** Unindo `br_ms_sim.microdados` (com `causa_violencia` do CID-10) a `br_ibge_pib.gini` por `sigla_uf` e `ano`, pode-se correlacionar Gini municipal com mortalidade por causas externas por `raca_cor` e `sexo`.
- **Q3:** O SINASC (ver tema 09) permite calcular fecundidade adolescente por `raca_cor_mae` e `escolaridade_mae` por município.
- **Q4:** Cruzando `br_ibge_censo_demografico.setor_censitario_basico_2010` com `setor_censitario_responsavel_renda_2010` no mesmo `id_setor_censitario`, pode-se analisar segregação racial por setor.

---

## 02 — Educação, Mobilidade Social e Desigualdade

### Tabelas e Colunas

| Tabela | Colunas Chave | Tamanho |
|--------|---------------|---------|
| `br_inep_enem.microdados` | `nota_matematica`, `nota_redacao`, `cor_raca`, `tipo_escola`, `dependencia_administrativa_escola`, `localizacao_escola`, `faixa_etaria`, `indicador_treineiro`, `indicador_questionario_socioeconomico` | 6,3 GB |
| `br_inep_indicador_nivel_socioeconomico.escola` | `id_escola`, `inse` (indicador NSE) | — |
| `br_inep_ideb.*` | `ideb`, `taxa_aprovacao`, `nota_proficiencia` (brasil, uf, municipio, escola) | — |
| `br_inep_educacao_especial.distorcao_idade_serie` | `taxa_distorcao`, `localizacao`, `sexo_raca_cor` | — |
| `br_inep_indicadores_educacionais.*remuneracao_docentes` | `remuneracao_media`, `sigla_uf` / `id_municipio` | — |
| `br_me_siconfi.municipio_despesas_funcao` | `funcao = "Educação"`, `valor_empenhado` | — |
| `br_ibge_pib.municipio` | `pib_per_capita`, `id_municipio` | — |
| `br_mec_sisu.microdados` | `id_ies`, `id_curso`, `nota_corte`, `sexo_candidato` | — |

### Perguntas Respondíveis

- **Q5:** Cruzando `nota_matematica` × `indicador_questionario_socioeconomico` no ENEM por `sigla_uf_residencia` e `dependencia_administrativa_escola`, é possível quantificar a correlação entre NSE e desempenho.
- **Q6:** Unindo `br_inep_censo_escolar.escola` (com `localizacao`, `dependencia_administrativa`) a `br_ibge_censo_2022.terra_indigena` / `territorio_quilombola` por `id_municipio`, pode-se avaliar disparidades rurais/indígenas.
- **Q7:** A tabela `distorcao_idade_serie` já cruza `taxa_distorcao` × `sexo_raca_cor` × `localizacao` diretamente.
- **Q8:** Cruzando `br_inep_indicadores_educacionais.municipio_remuneracao_docentes` com `br_inep_ideb.municipio` e `br_ibge_pib.municipio` por `id_municipio`, pode-se testar a relação investimento-resultado.

---

## 03 — Saúde, Acesso a Serviços e Determinantes Sociais

### Tabelas e Colunas

| Tabela | Colunas Chave | Tamanho |
|--------|---------------|---------|
| `br_ms_cnes.estabelecimento` | `id_municipio`, `natureza_juridica`, `esfera_administrativa`, `tipo_gestao` | — |
| `br_ms_cnes.equipamento` | `id_municipio`, `descricao_equipamento` (tomógrafo, ressonância, etc.) | — |
| `br_ms_cnes.leito` | `id_municipio`, `tipo_leito`, `quantidade_leito`, `especialidade` | — |
| `br_ms_cnes.profissional` | `cbo_2002`, `sigla_uf`, `id_municipio`, `vinculo_contratado`, `quantidade_vinculos` | — |
| `br_ms_sinasc.microdados` | `peso`, `raca_cor_mae`, `escolaridade_mae`, `inicio_pre_natal`, `pre_natal`, `semana_gestacao`, `tipo_parto`, `local_nascimento`, `id_municipio_nascimento` | 1,4 GB |
| `br_ms_sim.microdados` | `causa_basica`, `causa_violencia`, `data_obito`, `idade`, `sexo`, `raca_cor`, `id_municipio_ocorrencia`, `local_ocorrencia` | 1,4 GB |
| `br_ms_pns.microdados_2019` | variáveis de morbidade, acesso a serviços, condições socioeconômicas | — |
| `br_ans_beneficiario.informacao_consolidada` | `quantidade_beneficiario_ativo`, `sexo`, `faixa_etaria`, `modalidade_operadora`, `segmentacao_beneficiario`, `sigla_uf` | 8,3 GB |
| `br_bd_diretorios_brasil.cid_10` | `subcategoria`, `causa_violencia` | 261 KB |

### Perguntas Respondíveis

- **Q9:** Cruzando `br_ms_cnes.estabelecimento` (contagem por `id_municipio`) com `br_ibge_populacao.municipio` (população) e `br_ms_sim.microdados` (mortalidade infantil por `causa_basica`) por `id_municipio_ocorrencia`, pode-se correlacionar oferta de serviços e mortalidade.
- **Q10:** Unindo `br_ans_beneficiario.informacao_consolidada` (cobertura de planos por `sigla_uf`, `faixa_etaria`) com `br_ms_cnes.estabelecimento` (SUS) e `br_ms_sia.producao_ambulatorial` (utilização SUS) por `id_municipio`, pode-se analisar segmentação.
- **Q11:** A tabela `br_ms_cnes.profissional` com `cbo_2002` (médicos = códigos 2251xx) permite mapear deserts de profissionais por `id_municipio` e correlacionar com `br_ms_sinasc.microdados` (mortalidade materna).
- **Q12:** Cruzando `br_ms_pns.microdados_2019` com `br_ibge_pib.municipio` por `id_municipio`, pode-se analisar determinantes socioeconômicos de doenças crônicas.

---

## 04 — Mercado de Trabalho, Informalidade e Estratificação

### Tabelas e Colunas

| Tabela | Colunas Chave | Tamanho |
|--------|---------------|---------|
| `br_me_rais.microdados_vinculos` | `tipo_vinculo`, `vinculo_ativo_3112`, `faixa_remuneracao_media_sm`, `valor_remuneracao_media`, `faixa_etaria`, `sexo`, `raca_cor`, `grau_instrucao_apos_2005`, `cbo_2002`, `cnae_2_subclasse`, `tamanho_estabelecimento`, `natureza_juridica`, `indicador_portador_deficiencia`, `indicador_trabalho_parcial`, `indicador_simples` | 51,1 GB |
| `br_me_caged.microdados_movimentacao` | `saldo_movimentacao`, `tipo_movimentacao`, `salario_mensal`, `raca_cor`, `sexo`, `grau_instrucao`, `idade`, `cnae_2_secao`, `id_municipio` | 1,5 GB |
| `br_ibge_pnadc.microdados` | `condicao_ocupacao`, `renda`, `sexo`, `cor_raca`, `grau_instrucao`, `posicao_ocupacional` | — |
| `br_bd_diretorios_brasil.cbo_2002` | `cbo_2002`, `descricao`, `familia`, `subgrupo` (2.225 ocupações) | 74 KB |
| `br_bd_diretorios_brasil.cnae_2` | `subclasse`, `descricao_subclasse`, `divisao`, `descricao_divisao`, `secao` | 58 KB |

### Perguntas Respondíveis

- **Q13:** Cruzando `raca_cor` × `valor_remuneracao_media_sm` × `cbo_2002` × `cnae_2_subclasse` na RAIS, pode-se medir penalidade racial controlando por ocupação e setor.
- **Q14:** Unindo `br_me_caged.microdados_movimentacao` (saldos por `id_municipio`, `cnae_2_secao`) com `br_ibge_pib.gini` por `sigla_uf`, pode-se correlacionar informalidade e desigualdade.
- **Q15:** Analisando `faixa_remuneracao_media_sm` × `sexo` na RAIS para mesmo `cbo_2002` e `grau_instrucao_apos_2005`, pode-se medir disparidade salarial de gênero.
- **Q16:** Cruzando `valor_remuneracao_media` × `tamanho_estabelecimento` × `sigla_uf` na RAIS, pode-se avaliar a relação porte-empresa × salário.

---

## 05 — Política, Representação e Comportamento Eleitoral

### Tabelas e Colunas

| Tabela | Colunas Chave | Tamanho |
|--------|---------------|---------|
| `br_tse_eleicoes.candidatos` | `ano`, `tipo_eleicao`, `sigla_uf`, `id_municipio`, `cargo`, `genero`, `raca`, `instrucao`, `ocupacao`, `idade`, `sigla_partido`, `situacao` | 149 MB |
| `br_tse_eleicoes.resultados_candidato_municipio` | `id_municipio`, `sigla_partido`, `votos`, `proporcional` | — |
| `br_tse_eleicoes.resultados_partido_municipio` | `id_municipio`, `sigla_partido`, `votos`, `quociente_eleitoral` | — |
| `br_tse_eleicoes.despesas_candidato` | `id_candidato`, `valor_despesa`, `categoria_despesa`, `fornecedor` | — |
| `br_tse_eleicoes.receitas_candidato` | `id_candidato`, `valor_receita`, `tipo_receita`, `origem_receita` | — |
| `br_tse_filiacao_partidaria.microdados` | `id_partido`, `data_filiacao`, `situacao_filiacao`, `sigla_uf` | — |
| `br_camara_dados_abertos.deputado` | `id_deputado`, `sexo`, `data_nascimento`, `id_municipio_nascimento`, `sigla_uf_nascimento` | 278 KB |
| `br_camara_dados_abertos.deputado_profissao` | `id_deputado`, `entidade`, `titulo`, `ano_inicio`, `ano_fim` | — |
| `br_camara_dados_abertos.despesa` | `id_deputado`, `sigla_partido`, `categoria_despesa`, `valor_documento`, `fornecedor`, `cnpj_cpf_fornecedor` | 125 MB |

### Perguntas Respondíveis

- **Q17:** Cruzando `br_tse_eleicoes.resultados_partido_municipio` com `br_ibge_pib.municipio` (perfil socioeconômico) por `id_municipio`, pode-se analisar correlação entre desenvolvimento e voto.
- **Q18:** Analisando `genero` × `raca` × `instrucao` na tabela de candidatos permite medir sub-representação de mulheres e negros.
- **Q19:** Cruzando `valor_despesa` × `valor_receita` × `tipo_receita` (pessoa física vs. jurídica) na tabela de despesas/receitas permite avaliar o papel do dinheiro.
- **Q20:** Unindo `br_camara_dados_abertos.deputado` × `deputado_profissao` × `despesa` por `id_deputado`, pode-se mapear o perfil socioprofissional dos federais.

---

## 06 — Crime, Violência e Segurança Pública

### Tabelas e Colunas

| Tabela | Colunas Chave | Tamanho |
|--------|---------------|---------|
| `br_rj_isp_estatisticas_seguranca.taxa_evolucao_mensal_municipio` | 54 indicadores de crime: `taxa_homicidio_doloso`, `taxa_crimes_violentos_letais_intencionais`, `taxa_letalidade_violenta`, `taxa_homicidio_intervencao_policial`, `taxa_tentativa_homicidio`, `taxa_estupro`, `taxa_roubo_transeunte`, `taxa_roubo_veiculo`, `taxa_furto_celular`, `taxa_registro_trafico_drogas`, `taxa_apreensao_drogas`, `taxa_pessoas_desaparecidas`, `taxa_policial_morto_servico`, `ano`, `mes`, `id_municipio`, `regiao` | 853 KB |
| `br_rj_isp_estatisticas_seguranca.armas_fogo_apreendidas_mensal` | `quantidade_armas`, `id_municipio`, `regiao` | — |
| `br_rj_isp_estatisticas_seguranca.taxa_letalidade` | `taxa_letalidade`, `id_municipio`, `regiao` | — |
| `br_ms_sim.microdados` | `causa_basica`, `causa_violencia` (=1 para homicide), `idade`, `sexo`, `raca_cor`, `id_municipio_ocorrencia`, `data_obito` | 1,4 GB |
| `br_ibge_pib.gini` | `gini_pib`, `sigla_uf`, `ano` | 25 KB |
| `br_ibge_censo_demografico.setor_censitario_basico_2010` | indicadores de vulnerabilidade por setor | — |

### Perguntas Respondíveis

- **Q21:** Cruzando `br_ibge_pib.gini` (Gini por UF/ano) com `br_ms_sim.microdados` (mortalidade por `causa_violencia` = 1) por `id_municipio`, pode-se correlacionar desigualdade e homicídios.
- **Q22:** Usando `taxa_homicidio_intervencao_policial` × `taxa_letalidade_violenta` × `regiao` no ISP do RJ, pode-se avaliar impacto de UPPs.
- **Q23:** Cruzando `taxa_apreensao_drogas` × `taxa_registro_trafico_drogas` × `taxa_roubo_veiculo` × `taxa_roubo_carga` permite testar conexão tráfico-crimes patrimoniais.

---

## 07 — Economia, Crédito e Desenvolvimento Regional

### Tabelas e Colunas

| Tabela | Colunas Chave | Tamanho |
|--------|---------------|---------|
| `br_bcb_sicor.operacao` | `ano_emissao`, `sigla_uf`, `id_categoria_emitente`, `id_programa` (PRONAF/outros), `area_financiada`, `valor_parcela_credito`, `taxa_juro`, `id_tipo_cultivo`, `id_fonte_recurso` | 522 MB |
| `br_bcb_sicor.recurso_publico_mutuario` | `cpf`, `cnpj`, `tipo_beneficiario`, `sexo`, `primeiro_mutuario`, `id_dap` | 297 KB |
| `br_bcb_sicor.recurso_publico_propriedade` | `id_sncr`, `id_car`, `id_nirf`, `cpf`, `cnpj` | 491 KB |
| `br_bcb_estban.agencia` | `id_municipio`, `sigla_uf`, `instituicao`, `agencias_esperadas`, `agencias_processadas`, `valor` por `id_verbete` | 1,4 GB |
| `br_bcb_estban.municipio` | `id_municipio`, `instituicao`, `quantidade_agencias` | 894 MB |
| `br_anatel_indice_brasileiro_conectividade.municipio` | `ibc`, `cobertura_pop_4g5g`, `fibra`, `hhi_smp`, `hhi_scm`, `densidade_smp`, `adensamento_estacoes` | 443 KB |
| `br_ibge_pib.municipio` | `pib`, `pib_per_capita`, `va_agro`, `va_industria`, `va_servicos` | — |

### Perguntas Respondíveis

- **Q24:** Cruzando `valor_parcela_credito` × `id_programa` × `id_categoria_emitente` × `sigla_uf` no SICOR permite medir concentração do crédito agrícola.
- **Q25:** Unindo `br_bcb_estban.municipio` (quantidade agências por 100k hab.) com `br_ibge_pib.municipio` por `id_municipio`, pode-se correlacionar acesso bancário e desenvolvimento.
- **Q26:** Cruzando `br_me_cnpj.estabelecimentos` com `br_bd_diretorios_brasil.cnae_2` e `br_ibge_pib.municipio` permite medir diversificação econômica municipal.
- **Q27:** Usando `hhi_smp` e `hhi_scm` na tabela de conectividade permite medir concentração de mercado em telecomunicações.

---

## 08 — Políticas Públicas, Transferências e Proteção Social

### Tabelas e Colunas

| Tabela | Colunas Chave | Tamanho |
|--------|---------------|---------|
| `br_cgu_beneficios_cidadao.bolsa_familia_pagamento` | `ano_competencia`, `mes_competencia`, `id_municipio`, `sigla_uf`, `cpf_favorecido`, `valor_parcela` | 25,8 GB |
| `br_cgu_beneficios_cidadao.bpc` | `id_municipio`, `sigla_uf`, `cpf`, `valor_parcela`, `tipo_beneficio` (idade/atividade) | — |
| `br_cgu_beneficios_cidadao.auxilio_brasil` | `id_municipio`, `cpf`, `valor_parcela` | — |
| `br_cgu_beneficios_cidadao.novo_bolsa_familia` | `id_municipio`, `cpf`, `valor_parcela`, `quantidade_membros_familia` | — |
| `br_me_siconfi.municipio_despesas_funcao` | `id_municipio`, `sigla_uf`, `ano`, `funcao` (Saúde, Educação, Assistência Social, Segurança), `valor_empenhado`, `valor_liquidado`, `valor_pago` | — |
| `br_me_siconfi.municipio_receitas_orcamentarias` | `id_municipio`, `origem_receita` (impostos, transferências, patrimonial), `valor_arrecadado` | — |
| `br_mec_prouni.dicionario` | variáveis de oferta e demanda do PROUNI | — |
| `br_mec_sisu.microdados` | `id_ies`, `id_curso`, `nota_corte`, `tipo_cota`, `sexo_candidato` | — |
| `br_ibge_pib.gini` | `gini_pib`, `sigla_uf`, `ano` | 25 KB |

### Perguntas Respondíveis

- **Q28:** Cruzando `valor_parcela` total do Bolsa Família por `id_municipio` com `br_ibge_pib.gini` e `br_ibge_pib.municipio` permite avaliar se transferências reduzem desigualdade.
- **Q29:** Usando `br_me_siconfi.municipio_despesas_funcao` × `funcao` × `valor_liquidado` × `sigla_uf` pode-se analisar priorização do gasto público.
- **Q30:** Cruzando `br_mec_prouni.dicionario` × `br_inep_enem.microdados` (tipo_escola = pública) × `br_ibge_pib.municipio` permite avaliar impacto do PROUNI.

---

## 09 — Gênero, Família e Dinâmicas Demográficas

### Tabelas e Colunas

| Tabela | Colunas Chave | Tamanho |
|--------|---------------|---------|
| `br_ms_sinasc.microdados` | `data_nascimento`, `sexo`, `peso`, `raca_cor` (recém-nascido), `raca_cor_mae`, `escolaridade_mae`, `estado_civil_mae`, `idade_mae`, `ocupacao_mae`, `gestacoes_ant`, `quantidade_parto_normal`, `quantidade_parto_cesareo`, `inicio_pre_natal`, `pre_natal`, `semana_gestacao`, `tipo_gravidez`, `tipo_parto`, `local_nascimento`, `data_nascimento_mae`, `id_municipio_nascimento` | 1,4 GB |
| `br_ms_sim.microdados` | `causa_basica`, `causa_violencia` (para mortalidade materna) | 1,4 GB |
| `br_ibge_pnadc.microdados` | `condicao_ocupacao`, `renda`, `sexo`, `cor_raca`, `grau_instrucao`, composição familiar | — |
| `br_me_caged.microdados_movimentacao` | `saldo_movimentacao`, `sexo`, `grau_instrucao`, `cnae_2_secao` | 1,5 GB |
| `br_ms_cnes.estabelecimento` | `local_nascimento` (hospital/domicilio) | — |

### Perguntas Respondíveis

- **Q31:** Cruzando `raca_cor_mae` × `escolaridade_mae` × `inicio_pre_natal` × `tipo_parto` × `peso` no SINASC por `id_municipio_nascimento` permite analisar determinantes de mortalidade materna e infantil.
- **Q32:** Unindo `br_ms_sinasc.microdados` (fecundidade por `escolaridade_mae`) com `br_me_caged.microdados_movimentacao` (`saldo_movimentacao` × `sexo` × `sigla_uf`) pode-se testar relação trabalho-fecundidade.
- **Q33:** Cruzando `br_ibge_censo_demografico.setor_censitario_responsavel_domicilios_mulheres_2010` com `setor_censitario_responsavel_renda_2010` no mesmo setor permite analisar vulnerabilidade econômica de famílias chefiadas por mulheres.

---

## 10 — Meio Ambiente, Desenvolvimento e Sustentabilidade

### Tabelas e Colunas

| Tabela | Colunas Chave | Tamanho |
|--------|---------------|---------|
| `br_inpe_prodes.municipio_bioma` | `ano`, `id_municipio`, `bioma` (Amazônia, Cerrado, etc.), `area_total`, `desmatado`, `vegetacao_natural`, `nao_vegetacao_natural`, `hidrografia` | 862 KB |
| `br_seeg_emissoes.municipio` | `ano`, `id_municipio`, `sigla_uf`, `emissao_gwp`, `setor_emissor` (agricultura, energia, industrial, resíduos) | — |
| `br_seeg_emissoes.uf` | `ano`, `sigla_uf`, `emissao_gwp`, `setor_emissor` | — |
| `br_trase_supply_chain.soy_beans` | `id_municipio`, `id_frigorifico`, `volume_soja`, `destino_exportacao` | — |
| `br_trase_supply_chain.beef` | `id_municipio`, `id_matadouro`, `volume_boi`, `destino_exportacao` | — |
| `br_geobr_mapas.terra_indigena` | geometria, `id_municipio` | — |
| `br_geobr_mapas.unidade_conservacao` | geometria, tipo UC, `id_municipio` | — |
| `br_geobr_mapas.amazonia_legal` | geometria da Amazônia Legal | — |
| `br_sfb_sicar.area_imovel` | `id_municipio`, `area_imovel`, `area_vegetacao_nativa`, `area_reserva_legal`, `area_degradacao` | — |

### Perguntas Respondíveis

- **Q34:** Cruzando `br_inpe_prodes.municipio_bioma` (desmatamento por `id_municipio`, `bioma`) com `br_trase_supply_chain.soy_beans` / `beef` (volume produzido) permite testar correlação expansão-produção.
- **Q35:** Usando `br_seeg_emissoes.municipio` × `setor_emissor` × `sigla_uf` pode-se calcular pegada de carbono por município e correlacionar com `br_ibge_pib.municipio` (perfil produtivo).
- **Q36:** Cruzando `br_geobr_mapas.unidade_conservacao` (área protegida) com `br_inpe_prodes` (desmatamento) por `id_municipio` permite testar efeito protetor de UCs.

---

## 11 — Infraestrutura, Serviços e Qualidade de Vida

### Tabelas e Colunas

| Tabela | Colunas Chave | Tamanho |
|--------|---------------|---------|
| `br_mdr_snis.municipio_agua_esgoto` | `id_municipio`, `sigla_uf`, `ano`, `populacao_atendida_agua`, `populacao_atentida_esgoto`, `indice_atendimento_urbano_agua`, `indice_coleta_esgoto`, `indice_tratamento_esgoto`, `indice_perda_faturamento`, `extensao_rede_agua`, `extensao_rede_esgoto`, `volume_agua_produzido`, `volume_esgoto_coletado`, `investimento_total_prestador`, `receita_operacional_direta`, `despesa_pessoal` (156 colunas) | 31,3 MB |
| `br_anatel_banda_larga_fixa.densidade_municipio` | `ano`, `mes`, `sigla_uf`, `id_municipio`, `densidade` (acessos/100 hab.) | 10,3 MB |
| `br_anatel_indice_brasileiro_conectividade.municipio` | `id_municipio`, `ibc`, `cobertura_pop_4g5g`, `fibra`, `densidade_smp`, `adensamento_estacoes`, `hhi_smp`, `hhi_scm` | 443 KB |
| `br_ms_cnes.estabelecimento` | `id_municipio`, `natureza_juridica`, `esfera_administrativa` (SUS/privado) | — |
| `br_inep_censo_escolar.escola` | `id_municipio`, `localizacao`, `dependencia_administrativa`, equipamentos (laboratório, biblioteca, quadra) | — |

### Perguntas Respondíveis

- **Q37:** Usando `indice_atendimento_urbano_agua` × `indice_coleta_esgoto` × `indice_tratamento_esgoto` no SNIS por `id_municipio` correlacionado com `br_ms_sim.microdados` (mortalidade por doenças diarreicas, CODINGS A00-B99 no CID-10) permite medir impacto do saneamento na saúde.
- **Q38:** Cruzando `br_anatel_banda_larga_fixa.densidade_municipio` × `br_anatel_indice_brasileiro_conectividade.municipio` (ibc, `cobertura_pop_4g5g`, `fibra`) com `br_ibge_pib.municipio` por `id_municipio` permite correlacionar conectividade e desenvolvimento.
- **Q39:** Unindo `br_inep_censo_escolar.escola` (infraestrutura) com `br_inep_saeb.municipio` (proficiência) por `id_municipio` permite avaliar relação equipamentos-desempenho.

---

## 12 — Interseccionalidade e Desigualdades Complexas

### Tabelas e Colunas

| Tabela | Colunas Chave | Tamanho |
|--------|---------------|---------|
| `br_me_rais.microdados_vinculos` | `sexo` × `raca_cor` × `faixa_etaria` × `grau_instrucao_apos_2005` × `faixa_remuneracao_media_sm` × `cbo_2002` × `indicador_portador_deficiencia` | 51,1 GB |
| `br_me_caged.microdados_movimentacao` | `sexo` × `raca_cor` × `idade` × `salario_mensal` × `grau_instrucao` | 1,5 GB |
| `br_ms_sinasc.microdados` | `raca_cor_mae` × `escolaridade_mae` × `estado_civil_mae` × `inicio_pre_natal` × `tipo_parto` | 1,4 GB |
| `br_rj_isp_estatisticas_seguranca.feminicidio_mensal_cisp` | `taxa_feminicidio`, `regiao`, `id_municipio`, `ano`, `mes` | — |
| `br_rj_isp_estatisticas_seguranca.taxa_estupro` | `taxa_estupro`, `id_municipio`, `regiao`, `ano`, `mes` | — |
| `br_bd_diretorios_brasil.cbo_2002` | `cbo_2002`, `descricao` (ocupações de empregados domésticos = códigos 5121xx) | 74 KB |

### Perguntas Respondíveis

- **Q40:** Cruzando `sexo` × `raca_cor` × `faixa_remuneracao_media_sm` na RAIS (51,1 GB) permite operacionalizar e medir a penalidade interseccional de gênero e raça.
- **Q41:** Usando CBO 5121xx (empregado doméstico) × `sexo` × `raca_cor` na RAIS permite analisar a racialização do trabalho de cuidado.
- **Q42:** Cruzando `br_rj_isp_estatisticas_seguranca.feminicidio_mensal_cisp` × `taxa_estupro` × `regiao` com dados de acesso a serviços (`br_ms_cnes.estabelecimento`) permite analisar determinantes da violência de gênero.

---

## 13 — Migração, Urbanização e Transformações Espaciais

### Tabelas e Colunas

| Tabela | Colunas Chave | Tamanho |
|--------|---------------|---------|
| `br_me_caged.microdados_movimentacao` | `saldo_movimentacao` (proxy de migração líquida) × `id_municipio` × `sigla_uf` × `ano` × `mes` × `sexo` × `raca_cor` × `grau_instrucao` × `idade` × `cnae_2_secao` | 1,5 GB |
| `br_ibge_populacao.municipio` | `id_municipio`, `populacao`, `ano` | — |
| `br_ibge_censo_2022.terra_indigena` | geometria, `id_municipio` | — |
| `br_ibge_censo_2022.territorio_quilombola` | geometria, `id_municipio` | — |
| `br_geobr_mapas.concentracao_urbana` | geometria, `nome_concentracao_urbana`, `id_municipio` | — |
| `br_ibge_censo_demografico.setor_censitario_responsavel_renda_2010` | distribuição de renda por setor | — |

### Perguntas Respondíveis

- **Q43:** Analisando `saldo_movimentacao` × `id_municipio` × `sigla_uf` no CAGED por `ano` permite mapear fluxos migratórios intramunicipais e sua correlação com `br_ibge_pib.municipio`.
- **Q44:** Cruzando `br_ibge_censo_2022.terra_indigena` / `territorio_quilombola` com `br_ms_cnes.estabelecimento` / `br_inep_censo_escolar.escola` por `id_municipio` permite avaliar acesso a serviços de populações tradicionais.

---

## 14 — Consumo, Preços e Estratificação de Classe

### Tabelas e Colunas

| Tabela | Colunas Chave | Tamanho |
|--------|---------------|---------|
| `br_anp_precos_combustiveis.microdados` | `ano`, `sigla_uf`, `id_municipio`, `bandeira_revenda`, `data_coleta`, `produto` (gasolina, etanol, diesel, GNV), `preco_compra`, `preco_venda` | 79 MB |
| `br_ibge_ipca.mes_categoria_municipio` | `ano`, `mes`, `sigla_uf`, `id_municipio`, `ipca`, `descricao_categoria` (alimentação, habitação, transportes, saúde) | — |
| `br_ibge_inpc.mes_categoria_municipio` | `ano`, `mes`, `sigla_uf`, `id_municipio`, `inpc`, `descricao_categoria` | — |
| `br_ibge_pof.dicionario` | dicionário da Pesquisa de Orçamentos Familiares | — |
| `br_ibge_pnadc.microdados` | `renda`, `posicao_ocupacional`, `sexo`, `cor_raca` (para estratificar famílias) | — |

### Perguntas Respondíveis

- **Q45:** Cruzando `preco_venda` × `produto` × `sigla_uf` × `data_coleta` na ANP com `br_ibge_ipca.mes_categoria_municipio` (categoria = "Transportes") permite medir transmissão de preços de combustível para inflação.
- **Q46:** Unindo `br_ibge_ipca` (IPCA geral) × `br_ibge_inpc` (para trabalhadores earning ≤ 5 SM) × `descricao_categoria` permite analisar impacto diferenciado da inflação por classe.

---

## 15 — Poder, Elite e Reprodução Social

### Tabelas e Colunas

| Tabela | Colunas Chave | Tamanho |
|--------|---------------|---------|
| `br_camara_dados_abertos.deputado` | `id_deputado`, `nome`, `data_nascimento`, `sexo`, `id_municipio_nascimento`, `sigla_uf_nascimento` | 278 KB |
| `br_camara_dados_abertos.deputado_profissao` | `id_deputado`, `entidade`, `titulo`, `ano_inicio`, `ano_fim` (trajetória profissional) | — |
| `br_camara_dados_abertos.despesa` | `id_deputado`, `sigla_partido`, `categoria_despesa`, `valor_documento`, `fornecedor`, `cnpj_cpf_fornecedor`, `url_documento` | 125 MB |
| `br_tse_eleicoes.candidatos` | `ocupacao`, `instrucao`, `genero`, `raca`, `idade`, `sigla_partido`, `cargo`, `sigla_uf` | 149 MB |
| `br_tse_eleicoes.resultados_candidato` | `id_candidato`, `votos`, `situacao` (eleito/não eleito) | — |
| `br_me_cnpj.socios` | `cnpj`, `nome_socio`, `qualificacao_socio` (para detectar links empresarial-político) | — |
| `br_tse_eleicoes.receitas_candidato` | `tipo_receita`, `origem_receita` (pessoa física, jurídica, partido) | — |

### Perguntas Respondíveis

- **Q47:** Cruzando `id_municipio_nascimento` × `sigla_uf_nascimento` dos deputados com `br_ibge_pib.municipio` permite analisar origem regional das élites políticas.
- **Q48:** Unindo `br_camara_dados_abertos.deputado_profissao` × `deputado` × `despesa` por `id_deputado` permite mapear trajetória profissional, origens e conexões econômicas (via `cnpj_cpf_fornecedor`).
- **Q49:** Cruzando `br_tse_filiacao_partidaria.microdados` × `br_tse_eleicoes.candidatos` × `br_cgu_emendas_parlamentares.microdados` permite analisar perpetuação de élites partidárias.

---

## 16 — Economia Política e Desenvolvimento

### Tabelas e Colunas

| Tabela | Colunas Chave | Tamanho |
|--------|---------------|---------|
| `br_rf_arrecadacao.uf` | `ano`, `mes`, `sigla_uf`, 44 variáveis de arrecadação: `irpf`, `irpj_entidades_financeiras`, `irpj_demais_empresas`, `cofins`, `pis_pasep`, `csll`, `iof`, `ipi_fumo`, `ipi_bebidas`, `ipi_automoveis`, `ipi_importacoes`, `itr`, `imposto_importacao`, `imposto_exportacao`, `cide_combustiveis`, `receita_previdenciaria_propria` | 1,7 MB |
| `br_me_siconfi.municipio_despesas_funcao` | `id_municipio`, `sigla_uf`, `funcao` (Saúde, Educação, Assistência Social, Segurança, Transporte, Desenvolvimento), `valor_empenhado`, `valor_liquidado`, `valor_pago` | — |
| `br_me_siconfi.municipio_receitas_orcamentarias` | `id_municipio`, `origem_receita` (impostos, transferências, patrimonial), `valor_arrecadado` | — |
| `br_ibge_pib.municipio` | `pib`, `pib_per_capita`, `va_agro`, `va_industria`, `va_servicos` | — |
| `br_ibge_pib.gini` | `gini_pib`, `gini_va_agro`, `gini_va_industria`, `gini_va_servicos`, `sigla_uf`, `ano` | 25 KB |

### Perguntas Respondíveis

- **Q50:** Cruzando `irpf` × `irpj` × `cofins` × `pis_pasep` × `itr` × `sigla_uf` na Receita Federal com `br_ibge_pib.gini` (gini setorial) permite analisar estrutura Tributária e desigualdade.

---

## Síntese: Perguntas Respondidas por Tema

| Tema | Tabelas Usadas | Perguntas |
|------|---------------|-----------|
| **Desigualdade Racial** | Census 2022, SIM, RAIS, CID-10, PIB/Gini | Q1–Q4 |
| **Educação** | ENEM, IDEB, INSE, CAGED, SICOFIN, PIB | Q5–Q8 |
| **Saúde** | CNES, SINASC, SIM, PNS, ANS, CID-10 | Q9–Q12 |
| **Trabalho** | RAIS, CAGED, PNADC, CBO, CNAE | Q13–Q16 |
| **Política** | TSE, Câmara, Despesas, Filiação | Q17–Q20 |
| **Violência** | ISP/RJ, SIM, Gini, Census | Q21–Q23 |
| **Economia/Crédito** | SICOR, ESTBAN, ANATEL, PIB | Q24–Q27 |
| **Políticas Sociais** | CGU/Bolsa Família, SICONFI, PROUNI, SISU | Q28–Q30 |
| **Gênero/Família** | SINASC, CAGED, PNADC, CNES | Q31–Q33 |
| **Meio Ambiente** | PRODES, SEEG, TRASE, geobr, CAR | Q34–Q36 |
| **Infraestrutura** | SNIS, ANATEL, CNES, Census Escolar | Q37–Q39 |
| **Interseccionalidade** | RAIS, CAGED, SINASC, ISP/RJ | Q40–Q42 |
| **Migração** | CAGED, População, Census, geobr | Q43–Q44 |
| **Consumo/Preços** | ANP, IPCA, INPC, POF, PNADC | Q45–Q46 |
| **Poder/Elites** | Câmara, TSE, CNPJ, TSE Receitas | Q47–Q49 |
| **Economia Política** | Receita Federal, SICONFI, PIB/Gini | Q50 |

---

## Notas Metodológicas

### Estratégia de Cruzamento

A maioria das perguntas requer joins entre múltiplas tabelas usando:
- **`id_municipio`** (7 dígitos IBGE) — chave primária para cruzamentos municipais
- **`sigla_uf`** + **`ano`** / **`mes`** — para análises temporais e estaduais
- **`cbo_2002`** / **`cnae_2_subclasse`** — para análises ocupacionais e setoriais
- **`raca_cor`** / **`sexo`** / **`faixa_etaria`** — para desagregações sociodemográficas

### Unidades de Análise

- **Indivíduo:** microdados de censos (Census 2022), PNADC, RAIS, SINASC, SIM
- **Domicílio:** Census 2022, setor censitário
- **Setor censitário:** agregados de 2010, 2022
- **Município:** a maioria das tabelas adminstrativas (PNAD, RAIS, CAGED, SNIS, PIB, etc.)
- **UF / Região:** tabelas agregadas da RF, IBGE, BACEN
- **País:** tabelas nacionais (ENEM, SEEG, ANP)

### Principais Bases por Tamanho

| Base | Tamanho | Conteúdo |
|------|---------|----------|
| RAIS vínculos | 51,1 GB | Todo emprego formal do Brasil |
| ANS beneficiários | 8,3 GB | Planos de saúde privados |
| Bolsa Família | 25,8 GB | Transferências sociais |
| ENEM microdados | 6,3 GB | Exames nacionais |
| SINASC | 1,4 GB | Nascimentos |
| SIM | 1,4 GB | Óbitos |
| CAGED | 1,5 GB | Movimentações de emprego |

---

## Conclusão

A Base dos Dados Brasil oferece um ecossistema completo para pesquisa em ciências sociais, com 533 tabelas cobrindo desde censos demográficos (1970-2022) até dados administrativos de saúde, educação, trabalho, política e meio ambiente. A articulação entre bases — possível através de identificadores padronizados (`id_municipio`, `sigla_uf`, `cbo_2002`, `cnae_2`) — permite responder perguntas de pesquisa complexas que exigem cruzamentos multidimensionais entre variáveis demográficas, econômicas e sociais.
