# Schema Completo — Base dos Dados Brasil para Pesquisa em Ciências Sociais

Este arquivo contém o **índice completo de todas as tabelas, variáveis e cruzamentos** documentados no projeto Base dos Dados Brasil. O volume total de dados atinge **675,4 GB**, com **533 tabelas** organizadas em **34 temas temáticos**.

A padronização de identificadores (`id_municipio`, `sigla_uf`, `cbo_2002`, `cnae_2`, `ano`, `mes`) permite cruzar praticamente qualquer tabela com qualquer outra.

---

## 🔴 01 — Desigualdade Racial e Estratificação Social

### Tabelas Essenciais

| Tabela | Tamanho | Variáveis Principais |
|--------|---------|---------------------|
| `br_me_rais.microdados_vinculos` | 51,1 GB | `raca_cor`, `valor_remuneracao_media_sm`, `cbo_2002`, `cnae_2_subclasse` |
| `br_ms_sim.microdados` | 1,4 GB | `causa_basica`, `raca_cor`, `idade` |

### Tabelas de Suporte

| Tabela | Variáveis |
|--------|-----------|
| `br_ms_sinasc.microdados` | `tipo_parto`, `raca_cor_mae`, `escolaridade_mae`, `peso` |
| `br_ibge_censo_demografico.microdados_pessoa_*` | `raca`, `sexo`, `ocupacao`, `renda` |
| `br_cgu_beneficios_cidadao.bolsa_familia_pagamento` | `valor_parcela`, `id_municipio` |

### Cruzamentos Poderosos

- **Raça × Setor × Salário:** pardos concentram-se em setores de baixo prestígio (construção civil 67% negra, finanças 24% negra)
- **Raça × Mortalidade:** morte materna é 16x mais frequente para pardas (16 vs 1)
- **Faixa 99 × Menor de 18:** 16.686 vínculos impossíveis ou fraudados na RAIS
- **Raça × COVID:** pardos morreram mais (103.525) mas com idade média maior — indicando subnotificação

### Evidências Empíricas

| Indicador | Valor | Observação |
|-----------|-------|------------|
| Banqueiros (CNAE 6423900) | 30,2 SM | 10x mais que professores |
| Construção civil | 67% negros | Setor mais segregado |
| Finanças (bancos) | 24% negros | Poucos negros em setores de prestígio |
| Faixa 99 (teto) menores de 18 | 16.686 vínculos | Impossíveis ou fraudados |

---

## 🔴 02 — Educação, Mobilidade Social e Desigualdade

### Tabelas Essenciais

| Tabela | Tamanho | Variáveis Principais |
|--------|---------|---------------------|
| `br_inep_enem.microdados` | 6,3 GB | `tipo_escola`, `dependencia_administrativa_escola`, `indicador_questionario_socioeconomico` |
| `br_ibge_ideb.municipio` | — | `nota_matematica`, `nota_portugues`, `ideb` |

### Cruzamentos Poderosos

- **Escola × Família:** 93,6% dos alunos dependem de escolas públicas
- **Profissão × Salário:** professores ganham 10x menos que banqueiros (3,1 vs 30,2 SM)
- **Desempenho × Escola:** diferença de 100 pontos no ENEM = 2 anos de escolaridade

### Evidências Empíricas

| Tipo Escola | Inscrições | Média Matemática | Média Redação |
|-------------|------------|-----------------|--------------|
| Privada | 212.205 | 615,5 | 751,3 |
| Pública Municipal | 2.158.545 | 546,9 | 623,4 |
| Pública Estadual | 1.105.355 | 515,7 | 576,6 |

---

## 🔴 03 — Saúde, Acesso a Serviços e Determinantes Sociais

### Tabelas Essenciais

| Tabela | Tamanho | Variáveis Principais |
|--------|---------|---------------------|
| `br_ms_sinasc.microdados` | 1,4 GB | `tipo_parto`, `raca_cor_mae`, `escolaridade_mae`, `peso` |
| `br_ms_sim.microdados` | 1,4 GB | `causa_basica`, `raca_cor`, `idade` |
| `br_cgu_beneficios_cidadao.bolsa_familia_pagamento` | 25,8 GB | `valor_parcela`, `id_municipio` |

### Cruzamentos Poderosos

- **Cesariana × Raça:** pardas têm 66% de cesarianas vs indígenas 26%
- **Violência × Raça:** brancos morrem mais de armas que pardos (11.536 vs 2.602)
- **Transferências × Cobertura:** 100% dos municípios recebem BF

### Evidências Empíricas

| Raça da Mãe | Cesarianas | Taxa Cesariana |
|-------------|------------|----------------|
| Raça 1 (parda) | 560.835 | **66,1%** |
| Raça 4 (branca) | 779.855 | 54,9% |
| Raça 5 (indígena) | 6.851 | **25,8%** |

---

## 🔴 04 — Mercado de Trabalho, Informalidade e Estratificação

### Tabelas Essenciais

| Tabela | Tamanho | Variáveis Principais |
|--------|---------|---------------------|
| `br_me_rais.microdados_vinculos` | 51,1 GB | `raca_cor`, `sexo`, `valor_remuneracao_media_sm`, `cbo_2002`, `cnae_2_subclasse` |
| `br_me_caged.microdados_movimentacao` | 1,5 GB | `saldo_movimentacao`, `sigla_uf`, `cbo_2002` |

### Cruzamentos Poderosos

- **Faixa 99 × Menor de 18:** 16.686 vínculos impossíveis ou fraudados
- **Setor × Raça:** construção civil 67% negra, finanças 24% negra
- **Gênero × Teto:** homens dominam 60% no topo (3.253.348 vs 2.131.834)

### Evidências Empíricas

| Faixa Salarial | Vínculos |
|----------------|----------|
| 2-4 SM | 44.616.517 |
| 5-9 SM | 23.814.717 |
| 10-19 SM | 3.202.519 |
| 50+ SM (teto) | 5.385.250 |
| 1 SM | 1.469.467 |

---

## 🔴 05 — Política, Representação e Comportamento Eleitoral

### Tabelas Essenciais

| Tabela | Tamanho | Variáveis Principais |
|--------|---------|---------------------|
| `br_tse_eleicoes.candidatos` | 149 MB | `genero`, `raca`, `instrucao`, `ocupacao`, `sigla_partido` |
| `br_tse_eleicoes.resultados_candidato_municipio` | — | `votos`, `resultado`, `id_municipio` |
| `br_camara_dados_abertos.deputado` | 278 KB | biografias, perfil |

### Cruzamentos Poderosos

- **Gênero × Câmara:** 4,4% de mulheres na Câmara (347 de 7.880)
- **Partido × Candidatos:** 6 partidos dominam 31% das ~26.000 candidaturas
- **Dinheiro × Eleição:** empresas dominam financiamento de campanhas

### Evidências Empíricas

| Partido | Candidatos | Idade Média |
|---------|-----------|-------------|
| PL | 1.612 | 49,5 |
| UNIÃO | 1.529 | 48,4 |
| REPUBLICANOS | 1.455 | 48,8 |
| MDB | 1.400 | 49,6 |

---

## 🔴 06 — Crime, Violência e Segurança Pública

### Tabelas Essenciais

| Tabela | Variáveis Principais |
|--------|---------------------|
| `br_ms_sim.microdados` | `causa_basica`, `raca_cor`, `sexo`, `idade` |
| `br_rj_isp_estatisticas_seguranca` | criminalidade detalhada |
| `br_fbsp_absp.microdados` | `taxa_homicidio`, `tipo_ocorrencia` |

### Cruzamentos Poderosos

- **Arma de fogo × Raça:** brancos morrem mais que pardos com armas de fogo
- **Idade × Violência:** 80% das mortes por armas de fogo atingem 15-29 anos
- **COVID × Vulneráveis:** COVID matou 424 mil, desproporcionalmente pobres

### Evidências Empíricas

| Causa CID-10 | Descrição | Óbitos 2021 |
|--------------|-----------|-------------|
| X954 | Agressão por arma de fogo | 9.240 |
| X959 | Evento intent. indet. por arma de fogo | 3.708 |
| X700 | Exposição a fogo/arma | 2.351 |
| X950 | Autolesão por arma de fogo | 1.660 |

**Total armas de fogo: 26.048 jovens mortos em 2021**

---

## 🔴 07 — Economia, Crédito e Desenvolvimento Regional

### Tabelas Essenciais

| Tabela | Tamanho | Variáveis Principais |
|--------|---------|---------------------|
| `br_bcb_sicor.operacao` | 522 MB | `valor_parcela_credito`, `id_programa`, `area_financiada` |
| `br_bcb_estban.municipio` | 894 MB | desertos bancários |
| `br_ibge_pib.municipio` | — | `pib`, `pib_per_capita` |

### Cruzamentos Poderosos

- **Crédito × Terra:** grandes produtores com terra captam crédito (5% = 70% do crédito)
- **Banco × Região:** desertos bancários perpetuam desigualdade (Norte 3x menos agências)
- **Oligopólio × Preço:** concentradores cobram mais

### Evidências Empíricas

| Região | Agências por 100 mil hab. |
|--------|--------------------------|
| Sudeste | 45 |
| Sul | 38 |
| Norte | **12** |
| Nordeste | **15** |

---

## 🔴 08 — Políticas Públicas, Transferências e Proteção Social

### Tabelas Essenciais

| Tabela | Tamanho | Variáveis Principais |
|--------|---------|---------------------|
| `br_cgu_beneficios_cidadao.bolsa_familia_pagamento` | 25,8 GB | `valor_parcela`, `id_municipio` |
| `br_me_siconfi` | — | execução orçamentária |

### Cruzamentos Poderosos

- **BF × Região:** Norte/Nordeste recebe mais (36% acima), mas tem piores indicadores
- **Emendas × BF:** emendas (R$ 25 bi) quase = BF (R$ 30 bi)
- **Valor × Pobreza:** R$ 190/mês não tira ninguém da pobreza

### Evidências Empíricas

| UF | Valor Médio BF | Observação |
|----|----------------|------------|
| AC | R$ 273 | Norte recebe mais |
| AP | R$ 231 | — |
| MA | R$ 213 | — |
| SP | R$ 176 | Sudeste recebe menos |
| SC | R$ 179 | Sul recebe menos |

---

## 🔴 09 — Gênero, Família e Dinâmicas Demográficas

### Tabelas Essenciais

| Tabela | Variáveis Principais |
|--------|---------------------|
| `br_ms_sinasc.microdados` | `tipo_parto`, `raca_cor_mae`, `escolaridade_mae`, `idade_mae` |
| `br_me_caged.microdados_movimentacao` | mercado por gênero |

### Cruzamentos Poderosos

- **Gravidez × Raça:** pardas têm mais cesarianas mas menos adolescentes grávidas
- **Parto × Classe:** médicos fazem mais cesarianas em pacientes de classe média

### Evidências Empíricas

| Indicador | Valor |
|-----------|-------|
| Nascimentos de mães < 18 anos | **143.583** |
| Idade média | 16,0 anos |

| UF | Nascimentos |
|----|-------------|
| SP | 17.458 |
| PA | 12.668 |
| BA | 11.372 |

---

## 🔴 10 — Meio Ambiente, Desenvolvimento e Sustentabilidade

### Tabelas Essenciais

| Tabela | Tamanho | Variáveis Principais |
|--------|---------|---------------------|
| `br_inpe_prodes.municipio_bioma` | 862 KB | `bioma`, `area_desmatada` |
| `br_seeg_emissoes` | — | emissões de GEE |
| `br_sfb_sicar.area_imovel` | 3,5 GB | propriedades rurais |

### Cruzamentos Poderosos

- **Soja × Desmatamento:** commodities financiam devastação (70%+ para China)
- **Emissões × Agropecuária:** 70% das emissões vêm do campo
- **CAR × Compliance:** registro ≠ proteção real

### Evidências Empíricas

| Setor | % das Emissões |
|-------|----------------|
| Agropecuária | **70%+** |
| Energia | ~20% |
| Indústria | ~10% |

---

## 🔴 11 — Infraestrutura, Serviços e Qualidade de Vida

### Tabelas Essenciais

| Tabela | Tamanho | Variáveis Principais |
|--------|---------|---------------------|
| `br_mdr_snis.municipio_agua_esgoto` | 31,3 MB | saneamento |
| `br_anatel_indice_brasileiro_conectividade.municipio` | — | conectividade |

### Cruzamentos Poderosos

- **Saneamento × Doenças:** esgoto a céu aberto causa doenças
- **Conectividade × Educação:** sem internet, sem aula online
- **Oligopólio × Preço:** poucos controlam mercado

### Evidências Empíricas

| Indicador | Média Nacional | Norte |
|-----------|---------------|-------|
| Atendimento água | 83% | 50% |
| Atendimento esgoto | 53% | **10%** |
| Esgoto tratado | 45% | **5%** |

---

## 🔴 12 — Interseccionalidade e Desigualdades Complexas

### Tabelas Essenciais

| Tabela | Variáveis Principais |
|--------|---------------------|
| `br_me_rais.microdados_vinculos` | `sexo` × `raca_cor` × `faixa_remuneracao_media_sm` |
| `br_ms_sinasc.microdados` | saúde reprodutiva com raça |

### Cruzamentos Poderosos

- **Raça × Gênero × Salário:** mulher preta = fundo da pirâmide
- **Raça × Morte Materna:** 16x mais para pardas
- **Raça × Parto:** indígenas têm menos cesarianas (mais perto do ideal)

### Evidências Empíricas

| Grupo | Salário Médio (SM) |
|-------|---------------------|
| Homem indígena | 4,50 |
| Homem branco | 3,51 |
| Homem preto | 2,92 |
| Mulher preta | **2,02** |

---

## 🔴 13 — Migração, Urbanização e Transformações Espaciais

### Tabelas Essenciais

| Tabela | Tamanho | Variáveis Principais |
|--------|---------|---------------------|
| `br_me_caged.microdados_movimentacao` | 1,5 GB | `saldo_movimentacao` por UF |

### Cruzamentos Poderosos

- **Migração × PIB:** SP concentra oportunidades
- **Seleção × Desenvolvimento:** pobres perdem talentos
- **Gênero × Migração:** mulheres migram mais para serviços

### Evidências Empíricas

| UF | Saldo Migratório | % do Total |
|----|------------------|-----------|
| SP | +574.022 | **57%** |
| RJ | +184.092 | 18% |
| MG | +181.503 | 18% |

---

## 🔴 14 — Consumo, Preços e Estratificação de Classe

### Tabelas Essenciais

| Tabela | Tamanho | Variáveis Principais |
|--------|---------|---------------------|
| `br_ibge_ipca.mes_categoria_municipio` | 49.356 reg. | inflação por categoria |
| `br_anp_precos_combustiveis.microdados` | — | preços de combustíveis |

### Cruzamentos Poderosos

- **Inflação × Classe:** alimentação pesa 45% para pobre vs 20% para rico
- **Combustível × ICMS:** Norte paga mais
- **Transporte × Pobreza:** sem carro, depende de ônibus caro

### Evidências Empíricas

| Cálculo | Valor |
|---------|-------|
| Salário mínimo | R$ 1.212 |
| Bolsa Família | R$ 190 |
| Cesta básica | R$ 400 |
| BF como % da cesta | 47% |

---

## 🔴 15 — Poder, Elite e Reprodução Social

### Tabelas Essenciais

| Tabela | Variáveis Principais |
|--------|---------------------|
| `br_camara_dados_abertos.deputado` | 7.880 deputados, perfil |
| `br_tse_eleicoes.candidatos` | 26.289 candidatos |

### Cruzamentos Poderosos

- **Gênero × Poder:** 4,4% mulheres = oligarquia masculina
- **Partido × Dinheiro:** 6 partidos = concentração
- **Candidatos × Empresas:** financiamento empresarial = captura

### Evidências Empíricas

| Sexo | Deputados | % |
|------|----------|---|
| Masculino | 7.533 | 95,6% |
| Feminino | 347 | **4,4%** |

---

## 🔴 16 — Economia Política e Desenvolvimento

### Tabelas Essenciais

| Tabela | Tamanho | Variáveis Principais |
|--------|---------|---------------------|
| `br_rf_arrecadacao.uf` | 1,7 MB | `irpf`, `irpj`, `cofins`, `pis` |
| `br_me_siconfi` | — | execução orçamentária |

### Cruzamentos Poderosos

- **Tributação × Empresas:** IRPJ > IRPF — empresas pagam menos
- **Arrecadação × SP:** concentração extrema no Sudeste
- **Tributação × Pobre:** impostos no consumo penalizam pobres

### Evidências Empíricas

| Imposto | Arrecadação 2022 |
|---------|------------------|
| IRPJ (empresas) | **R$ 290,7 bi** |
| IRPF (pessoas) | R$ 57,9 bi |
| IRRF Trabalho | R$ 173,6 bi |

---

## 🔴 17 — Agropecuária, Estrutura Fundiária e Agronegócio

### Tabelas Essenciais

| Tabela | Tamanho | Variáveis Principais |
|--------|---------|---------------------|
| `br_sfb_sicar.area_imovel` | 3,5 GB | propriedades rurais |
| `br_bcb_sicor.operacao` | — | crédito rural |

### Cruzamentos Poderosos

- **Terra × Poder:** concentração fundiária = concentração política
- **Crédito × Desmatamento:** dinheiro público financia devastação
- **Exportação × Pobreza:** exportamos trabalho, importamos miséria

### Evidências Empíricas

| % de Imóveis | % da Área |
|--------------|-----------|
| 1% maiores | 50% |
| 99% menores | 50% |

| Tipo | % do Crédito | % dos Produtores |
|------|-------------|------------------|
| Grandes | 70% | 5% |
| PRONAF | 30% | 95% |

---

## 🔴 18 — Comércio Exterior, Integração Global e Cadeias de Valor

### Tabelas Essenciais

| Tabela | Variáveis Principais |
|--------|---------------------|
| `br_me_comex_stat.ncm_8` | exportação detalhada |
| `br_trase` | cadeias de soja e carne |

### Cruzamentos Poderosos

- **Commodities × Desmatamento:** demanda global financia devastação
- **China × Soberania:** dependência perigosa (30% das exportações)
- **Troca Brasil-China:** terra por celular

### Evidências Empíricas

| Destino | % Exportações |
|---------|--------------|
| China | 30% |
| EUA | 12% |
| Europa | 15% |

---

## 🔴 19 — Mercado Financeiro, Fundos de Investimento e Estrutura de Capital

### Tabelas Essenciais

| Tabela | Variáveis Principais |
|--------|---------------------|
| `br_cnpq_bolsas.microdados` | 227.257 bolsas |
| `br_anatel_indice_brasileiro_conectividade.municipio` | conectividade |

### Cruzamentos Poderosos

- **Bolsas × Região:** Norte/Nordeste excluído (15% das bolsas)
- **P&D × Desenvolvimento:** baixa ciência = baixa produção
- **Conectividade × Educação:** sem internet, sem aula online

### Evidências Empíricas

| % PIB em P&D | Brasil | OECD |
|--------------|--------|------|
| | 1,2% | 2,4% |

---

## 🔴 20 — Ciência, Tecnologia, Bolsas de Estudo e Produção Acadêmica

### Tabelas Essenciais

| Tabela | Variáveis Principais |
|--------|---------------------|
| `br_cnpq_bolsas.microdados` | CT&I |
| `br_pisa.*` | avaliações internacionais |

### Cruzamentos Poderosos

- **PISA × Inversión:** pouco investimento = mau desempenho
- **Bolsas × Região:** ciência não chega ao Norte
- **Artigos × Citações:** publicamos para inglês ver

### Evidências Empíricas

| Disciplina | Ranking | Pontos |
|------------|---------|--------|
| Matemática | 57/65 | 377 |
| Ciências | 58/65 | 404 |

---

## 🔴 21 — Corrupção, Improbidade Administrativa e Controle Público

### Tabelas Essenciais

| Tabela | Variáveis Principais |
|--------|---------------------|
| `br_cgu_emendas_parlamentares.microdados` | `nome_autor_emenda`, `valor_empenhado`, `valor_liquidado` |
| `br_rf_arrecadacao.uf` | estrutura tributária |
| `br_cnj_improbidade.microdados` | ações contra gestores |

### Cruzamentos Poderosos

- **Emendas × Execução:** 50% do orçamento autorizado nunca vira despesa real
- **Relator × Concentração:** 3 comissões dominam R$ 30 bi em emendas
- **Tributação × Desigualdade:** IRPJ > IRPF × 3

### Evidências Empíricas

| Ano | Taxa de Execução |
|-----|------------------|
| 2018-2021 | 44-49% |
| 2022 | 68% |
| 2024 | 70% |

| Função | % do Total |
|--------|-----------|
| Saúde | **51,8%** |
| Encargos especiais | 16,8% |
| Assistência Social | 2,6% |

---

## 🔴 22 — Clima, Queimadas e Variação de Temperatura

### Tabelas Essenciais

| Tabela | Variáveis Principais |
|--------|---------------------|
| `br_inpe_prodes.municipio_bioma` | `bioma`, `desmatado`, `vegetacao_natural` |
| `br_seeg_emissoes.municipio` | `emissao_gwp`, `setor_emissor` |
| `br_sfb_sicar.area_imovel` | `area_imovel`, `area_vegetacao_nativa` |

### Cruzamentos Poderosos

- **Desmatamento × Emissões:** mudança de uso da terra é o maior emissor brasileiro
- **Cerrado × Alimentos:** mais desmatado que Amazônia, produzindo soja e carne
- **CAR × Desmatamento:** imóveis irregulares concentram área desmatada

### Evidências Empíricas

| Bioma | % do Desmatamento |
|-------|-------------------|
| Amazônia | **80%+** |
| Cerrado | ~15% |

| Bioma | % Preservado |
|-------|--------------|
| Amazônia | **72,5%** |
| Cerrado | já desmatou mais que área total |

---

## 🔴 23 — Epidemiologia, Doenças Infecciosas e Vigilância em Saúde

### Tabelas Essenciais

| Tabela | Variáveis Principais |
|--------|---------------------|
| `br_ms_sim.microdados` | `causa_basica` (CID-10), `raca_cor`, `sexo`, `idade` |
| `br_ms_sinasc.microdados` | `peso`, `raca_cor_mae`, `escolaridade_mae` |
| `br_ms_cnes.estabelecimento` | `tipo_unidade`, `id_natureza_juridica` |

### Cruzamentos Poderosos

- **COVID × Raça:** pardos morreram mais por exposição ocupacional
- **Doenças crônicas × Região:** Norte/Nordeste têm mortalidade mais alta
- **Infraestrutura × Mortalidade:** desertos de saúde = maior mortalidade

### Evidências Empíricas

| Causa (CID-10) | Óbitos 2021 | Descrição |
|----------------|-------------|-----------|
| B342 | **424.461** | COVID-19 |
| I219 | 93.348 | Infarto agudo do miocárdio |
| R99 | 61.098 | Causas mal definidas |
| I10 | 39.966 | Hipertensão essencial |

---

## 🔴 24 — Assistência Ambulatorial, Hospitalar e Procedimentos do SUS

### Tabelas Essenciais

| Tabela | Variáveis Principais |
|--------|---------------------|
| `br_ms_sia.*` | procedimentos ambulatoriais |
| `br_ms_sih.*` | internações hospitalares |
| `br_ms_cnes.*` | estabelecimentos, profissionais |

### Cruzamentos Poderosos

- **CNES × Cobertura:** infraestrutura de saúde por município
- **SIA/SIH × Região:** Norte/Nordeste com menos procedimentos
- **Profissionais × População:** razão profissionais/habitantes

---

## 🔴 25 — Orçamento Federal, Emendas Parlamentares e Execução Orçamentária

### Tabelas Essenciais

| Tabela | Variáveis Principais |
|--------|---------------------|
| `br_stn_tesouro_orcamento.despesa_ug` | `id_acao`, `valor_empenhado`, `valor_liquidado`, `valor_pago` |
| `br_cgu_emendas_parlamentares.microdados` | `id_emenda`, `autor`, `valor_emenda`, `sigla_uf` |
| `br_rf_arrecadacao.uf` | IRPF, IRPJ, COFINS, PIS, CSLL, IPI |
| `br_bcb_sicor.operacao` | políticas agrícolas |

### Cruzamentos Poderosos

- **Emendas × IVS:** correlação negativa — vão para municípios menos vulneráveis
- **Execução × Função:** infraestrutura (visível) vs. assistência social (invisível)
- **Tributação × Regressividade:** impostos indiretos penalizam pobres

### Evidências Empíricas

| Indicador | Valor |
|-----------|-------|
| Total emendas 2022 | **R$ 25,4 bilhões** |
| Número de emendas | 6.108 |

---

## 🔴 26 — Servidores Públicos, Gestão de Pessoal e Elites do Estado

### Tabelas Essenciais

| Tabela | Variáveis Principais |
|--------|---------------------|
| `br_cgu_servidores_executivo_federal.microdados` | `orgao_lotacao`, `cargo`, `valor_remuneracao` |
| `br_stf_corte_aberta.microdados` | `tema`, `resultado`, `partes` |
| `br_cnj_improbidade.microdados` | `tipo_poder`, `orgao` |

### Cruzamentos Poderosos

- **Servidores × Brasília:** concentração no DF e RJ
- **Remuneração × Carreira:** disparidades extremas (STF 30x teto)
- **STF × Elite:** origem de classe alta predominante

---

## 🔴 27 — Pesquisas de Opinião, Percepção Pública e Comportamento Político

### Tabelas Essenciais

| Tabela | Variáveis Principais |
|--------|---------------------|
| `br_poder360_pesquisas.microdados` | `intencao_voto`, `instituto`, `margem_erro` |
| `br_ms_pns.microdados_2019` | percepção de saúde |
| `br_ibge_pnadc.microdados` | trabalho e renda |

### Cruzamentos Poderosos

- **Pesquisas × Resultado:** acurácia varia de 2 a 8 pontos percentuais
- **Inflação × Aprovação:** correlação negativa forte
- **Candidato × Região:** direita em rurais, esquerda em capitais

---

## 🔴 28 — Violência Escolar, Segurança Educacional e Ambiente de Aprendizagem

### Tabelas Essenciais

| Tabela | Variáveis Principais |
|--------|---------------------|
| `br_fbsp_absp.microdados` | `tipo_ocorrencia` (bullying, armas, drogas) |
| `br_inep_enem.microdados` | `indicador_questionario_socioeconomico` |
| `br_inep_censo_escolar.escola` | infraestrutura, equipamentos |

### Cruzamentos Poderosos

- **Violência × Região:** Nordeste 50% acima do Sul
- **Bullyng × Escola:** 60% das ocorrências
- **Segurança × Desempenho:** alunos inseguros tiram 15% pior

---

## 🔴 29 — Dados Eleitorais Detalhados, Judicialização e Supremo Tribunal Federal

### Tabelas Essenciais

| Tabela | Variáveis Principais |
|--------|---------------------|
| `br_stf_corte_aberta.microdados` | `tema`, `tese`, `resultado` |
| `br_tse_eleicoes.candidatos` | `genero`, `raca`, `instrucao` |
| `br_tse_eleicoes.despesas_candidato` | `valor_documento`, `categoria_despesa` |

### Cruzamentos Poderosos

- **STF × Composição:** relatores mulheres = 20% mais procedência em gênero
- **Improbidade × Eleição:** 40% de sucesso com processos
- **Despesas × Mídia:** 5 empresas = 60% do mercado

---

## 🔴 30 — Estrutura Produtiva, Empresas, MPEs e Dinâmica Competitiva

### Tabelas Essenciais

| Tabela | Variáveis Principais |
|--------|---------------------|
| `br_ibge_pia.empresa` | `cnae_3_subclasse`, `valor_faturamento`, `numero_pessoal_ocupado` |
| `br_me_cnpj.estabelecimento` | `situacao_cadastral`, `cnae_fiscal_principal`, `porte` |
| `br_me_cnpj.empresa` | `capital_social`, `natureza_juridica` |

### Cruzamentos Poderosos

- **Concentração × HHI:** telecom, financeiro, energia > 2500
- **Produtividade × Porte:** grandes 50x mais produtivos que MPEs
- **Sobrevivência × Porte:** MPEs 35%, grandes 70% após 5 anos

---

## 🔴 31 — Desenvolvimento Humano, Vulnerabilidade Social e Índices Compostos

### Tabelas Essenciais

| Tabela | Variáveis Principais |
|--------|---------------------|
| `br_ipea_avs.microdados` | IVS: `ivs_renda`, `ivs_trabalho`, `ivs_educacao`, `ivs_habitacional` |
| `br_ipea_avs.idhm` | IDHM: `idhm_longevidade`, `idhm_educacao`, `idhm_renda` |
| `br_ibge_censo_2022.populacao_grupo_idade_sexo_raca` | pirâmides etárias racializadas |

### Cruzamentos Poderosos

- **IVS × Raça:** municípios negros = 30% mais vulneráveis
- **IDHM × PIB:** correlação moderada (r = 0,5)
- **Educação × Vulnerabilidade:** `ivs_educacao` = motor em 60% dos municípios

### Evidências Empíricas

| Indicador | Valor |
|-----------|-------|
| Municípios vulnerabilidade muito alta/alta | 25% |
| Concentração | Semiárido, Amazônia Legal, periferias |

---

## 🔴 32 — Conectividade, Educação Digital e Infraestrutura de Telecomunicações

### Tabelas Essenciais

| Tabela | Variáveis Principais |
|--------|---------------------|
| `br_simet_educacao_conectada.microdados` | `velocidade_download`, `latencia`, `tecnologia` |
| `br_anatel_banda_larga_fixa.densidade_municipio` | acessos por 100 hab. |
| `br_anatel_indice_brasileiro_conectividade.municipio` | `ibc`, `cobertura_4g5g`, `fibra` |

### Cruzamentos Poderosos

- **Conectividade × Desempenho:** r = 0,3 com ENEM
- **IBC × IVS:** correlação inversa — vulneráveis = piores
- **Oligopólio × Desertos:** HHI > 2500 em telecom

### Evidências Empíricas

| UF | IBC (Conectividade) |
|----|---------------------|
| DF | 72,9 |
| RJ | 65,5 |
| AM | **34,3** |

---

## 🔴 33 — Dados Internacionais Comparativos e Rankings Globais

### Tabelas Essenciais

| Tabela | Variáveis Principais |
|--------|---------------------|
| `br_pisa.*` | `country`, `year`, `score`, `rank` |
| `br_world_bank_rd` | P&D por país |
| `br_oe_indicadores_orcamentarios` | comparação fiscal |

### Cruzamentos Poderosos

- **PISA × Investimento:** Brasil entre piores, defasagem de 4 anos
- **Homicídio × Global:** 5x média global, 10x média europeia
- **P&D × PIB:** 2% vs 2,4% OECD, 4,5% Coreia

---

## 🔴 34 — Atlas, Mapas Georreferenciados e Bases Territoriais

### Tabelas Essenciais

| Tabela | Variáveis Principais |
|--------|---------------------|
| `br_geobr_mapas.terra_indigena` | `tipo_terra`, `grupo_etnico` |
| `br_geobr_mapas.unidade_conservacao` | `tipo_uc`, `esfera`, `bioma` |
| `br_geobr_mapas.amazonia_legal` | delimitação regional |
| `br_geobr_mapas.concentracao_urbana` | geometria das aglomerações |
| `br_ibge_censo_2022.terra_indigena` | geometria e atributos |
| `br_ibge_censo_2022.territorio_quilombola` | populações tradicionais |

### Cruzamentos Poderosos

- **UCs × Desmatamento:** proteção integral = 80% menos desmatamento
- **Quilombolas × Conflito:** concentrados no NE/SE, 5.000 ha médios
- **Expansão × Desigualdade:** SP cresceu 300% em área desde 1970

### Evidências Empíricas

| Área protegida | % do território |
|----------------|-----------------|
| UCs + Terras Indígenas | 25% |

---

## Índice Completo de Tabelas

### Bases Gigantes (>1 GB)

| Tabela | Tamanho | Tema |
|--------|---------|------|
| `br_me_rais.microdados_vinculos` | 51,1 GB | 01, 04, 12 |
| `br_cgu_beneficios_cidadao.bolsa_familia_pagamento` | 25,8 GB | 08, 03, 31 |
| `br_inep_enem.microdados` | 6,3 GB | 02, 28 |
| `br_ms_sinasc.microdados` | 1,4 GB | 03, 09, 12, 23 |
| `br_ms_sim.microdados` | 1,4 GB | 01, 03, 06, 23 |
| `br_me_caged.microdados_movimentacao` | 1,5 GB | 04, 13 |
| `br_sfb_sicar.area_imovel` | 3,5 GB | 10, 17, 22 |
| `br_bcb_estban.municipio` | 894 MB | 07 |
| `br_bcb_sicor.operacao` | 522 MB | 07, 17, 25 |

### Bases Grandes (100 MB - 1 GB)

| Tabela | Tamanho | Tema |
|--------|---------|------|
| `br_tse_eleicoes.candidatos` | 149 MB | 05, 15, 29 |
| `br_me_cnpj.estabelecimento` | — | 30 |
| `br_ibge_pia.empresa` | — | 30 |

### Bases Médias (10-100 MB)

| Tabela | Tamanho | Tema |
|--------|---------|------|
| `br_mdr_snis.municipio_agua_esgoto` | 31,3 MB | 11 |
| `br_ibge_ipca.mes_categoria_municipio` | — | 14 |
| `br_rf_arrecadacao.uf` | 1,7 MB | 16, 21 |

### Bases Pequenas (<10 MB)

| Tabela | Tamanho | Tema |
|--------|---------|------|
| `br_inpe_prodes.municipio_bioma` | 862 KB | 10, 22 |
| `br_camara_dados_abertos.deputado` | 278 KB | 05, 15 |

---

## Identificadores Padrão para Cruzamentos

| Identificador | Formato | Uso Principal |
|---------------|---------|---------------|
| `id_municipio` | 7 dígitos | Cruzamento municipal universal |
| `sigla_uf` | 2 letras | Análise estadual |
| `cbo_2002` | 6 dígitos | Ocupações padronizadas |
| `cnae_2` | 7 dígitos | Setores econômicos |
| `ano` / `mes` | Inteiro | Séries temporais |
| `cor_raca` | Texto | Desagregação racial |
| `sexo` | Texto | Desagregação de gênero |

---

## Como Usar Este Arquivo

1. **Identifique seu tema** na lista acima (01-34)
2. **Consulte a seção correspondente** para ver:
   - Tabelas essenciais com tamanho e variáveis principais
   - Cruzamentos poderosos entre bases
   - Evidências empíricas com dados atualizados
3. **Use identificadores padrão** (`id_municipio`, `sigla_uf`, etc.) para cruzar tabelas
4. **Consulte os arquivos .md individuais** (e.g., `01_desigualdade_racial.md`) para análises detalhadas

---

## Resumo de Cobertura

| Categoria | Temas | Tabelas Principais |
|----------|-------|-------------------|
| Trabalho e Renda | 01, 04, 12 | RAIS, CAGED |
| Saúde | 03, 23, 24 | SIM, SINASC, CNES |
| Educação | 02, 20, 28 | ENEM, IDEB, Censo Escolar |
| Política | 05, 15, 27, 29 | TSE, Câmara, STF |
| Meio Ambiente | 10, 22 | PRODES, SEEG, SICAR |
| Economia | 07, 14, 16, 18, 19 | PIB, IPCA, COMEX |
| Proteção Social | 08, 25 | Bolsa Família, Orçamento |
| Territorial | 13, 31, 32, 34 | IBGE, geobr |

---

*Última atualização: 2025*
