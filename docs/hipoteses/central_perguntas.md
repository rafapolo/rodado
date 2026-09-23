# Perguntas geradas a partir de `central_emendas.md`

A 21ª edição do Radar da Central das Emendas ([`central_emendas.md`](central_emendas.md))
descreve, em prosa jornalística, um conjunto de **esquemas** — padrões estruturais de
como emendas parlamentares podem ser usadas fora do interesse público — e cita achados
pontuais (nomes de parlamentares, municípios, valores). Este arquivo generaliza cada
esquema em pergunta testável contra o mirror, para descobrir se o padrão se repete em
escala nacional, não só nos casos que a reportagem já nomeou.

Diferente de [`perguntas.md`](perguntas.md) (43 temas × 5 perguntas, regra fixa de
n≥3 datasets simultâneos), aqui a cobertura é **oportunista**: um esquema vira pergunta
só até onde os dados do mirror permitem testá-lo, e várias perguntas abaixo são
descritivas/série temporal (n=1 ou n=2) em vez de cruzamento amplo — o objetivo é achar
casos semelhantes aos da reportagem, não cobrir um espaço fixo de perguntas.

Código de referência: `E<esquema>-<nº>`, resolvido em [`central_respostas.md`](central_respostas.md).
Datasets-chave usados: `br_cgu_emendas_parlamentares.microdados` (autor, função/subfunção,
município, valor empenhado/pago por emenda, 2014–2025), `br_transferegov.planos_acao`
(repasse via convênio/plano de ação), `br_tse_eleicoes.*` (candidatos, resultados,
votos por município), `br_me_cnpj.socios`/`empresas` (quadro societário), `br_cgu_licitacao_contrato.*`
(licitação, participantes, contratos), `br_me_siconfi.municipio_despesas_funcao` (despesa
municipal por função/subfunção).

---

## E1 · Conflito de interesse por vínculo societário

> "recursos indicados por parlamentares financiaram projetos executados por empresas
> em que os parlamentares constaram como sócios, de que seus familiares são sócios,
> de propriedade de ex-assessores ou de doadores de campanha" — e "os mecanismos
> públicos disponíveis também não conseguem identificar esses vínculos de forma
> automática" (UOL, citado em `central_emendas.md`).

1. Quantos parlamentares federais eleitos aparecem como sócio pessoa física de alguma
   empresa (nome normalizado + 6 dígitos centrais do CPF, únicos dígitos não mascarados
   em `br_me_cnpj.socios.documento`), e isso é um universo grande o bastante para o
   pareamento automático ingênuo (nome + fragmento de CPF) ser confiável, ou a segunda
   reportagem está certa de que "não existe forma automática"? *(n=2: br_tse_eleicoes.candidatos,
   br_me_cnpj.socios)*
2. Das empresas casadas dessa forma a um parlamentar, quantas aparecem como vencedoras
   de licitação (`vencedor=true`) num órgão do mesmo município para o qual esse mesmo
   parlamentar destinou emenda? *(n=3: br_tse_eleicoes.candidatos, br_me_cnpj.socios,
   br_cgu_licitacao_contrato.licitacao_participante, cruzado com
   br_cgu_emendas_parlamentares.microdados)*
3. Nos seis casos nomeados pela reportagem (irmão de senador, ex-chefe de gabinete,
   ex-mulher sócia, artista empresariado, postos de gasolina ligados a deputado), o
   *nome da empresa* aparece em `br_cgu_licitacao_contrato` ou em `br_transferegov.planos_acao`
   como recebedora, e o valor bate com o citado pela reportagem? *(n=2: br_cgu_licitacao_contrato,
   br_transferegov.planos_acao)*

## E2 · Padrões atípicos de contratação (baixa concorrência)

> "número reduzido de concorrentes, inabilitações e propostas com valores muito
> próximos" nas contratações financiadas por emenda.

1. Qual fração das licitações no mirror teve apenas 1 participante, e essa taxa é
   mais alta nos municípios que mais recebem emenda parlamentar do que nos que menos
   recebem? *(n=2: br_cgu_licitacao_contrato.licitacao_participante,
   br_cgu_emendas_parlamentares.microdados)*
2. Entre licitações com 2+ participantes, qual fração tem propostas cujo valor difere
   em menos de 1% entre 1º e 2º colocado (indício de combinação prévia), e esse padrão
   é mais comum em municípios pequenos? *(n=1: br_cgu_licitacao_contrato.licitacao_item)*

## E3 · Emenda como moeda de barganha eleitoral

> No Amazonas, "municípios que mais receberam recursos estão, em sua maioria, entre
> os que declararam apoio à candidatura do senador"; municípios sem apoio receberam
> menos.

1. Isolando cada senador que destinou emenda 2023–2025 ao seu próprio estado, o valor
   por município se correlaciona com a votação do próprio senador ali em 2022 (proxy de
   base eleitoral, não de apoio de terceiros)? *(n=3: br_cgu_emendas_parlamentares.microdados,
   br_tse_eleicoes.candidatos, br_tse_eleicoes.resultados_candidato_municipio)*
2. Em anos eleitorais (2018, 2022) o valor médio pago por emenda sobe em relação aos
   anos não eleitorais, no Brasil como um todo? *(n=1: br_cgu_emendas_parlamentares.microdados)*

## E4 · Pulverização em eventos desproporcionais ao orçamento local

> "atrações que custariam cerca de R$ 2 milhões, mais que o dobro do orçamento
> municipal de 2026, de R$ 930 mil" — recursos federais financiando espetáculos em
> municípios de orçamento minúsculo.

1. Existe algum município-ano em que o valor pago em emenda de subfunção
   Desporto/Cultura/Turismo excede um percentual alto (ex.: >5%) da despesa total paga
   do município naquele ano? *(n=2: br_cgu_emendas_parlamentares.microdados,
   br_me_siconfi.municipio_despesas_funcao)*
2. Nos municípios pequenos (despesa total < R$20 milhões/ano), qual a distribuição da
   razão emenda-de-evento/despesa-total, e ela é sistematicamente mais alta que nos
   municípios grandes? *(n=2: mesmas duas acima)*

## E5 · Emenda não transforma a estrutura do orçamento municipal

> Caio Sousa: analisando ~4.800 municípios (2015–2023), "pouca alteração na composição
> dos orçamentos municipais após o recebimento das emendas" — entregas pontuais, não
> política pública.

1. Nos municípios que tiveram um salto de emenda recebida de um ano para o outro, a
   participação de saúde/educação na despesa total muda de forma duradoura nos 2 anos
   seguintes, comparado aos municípios sem salto? *(n=2: br_cgu_emendas_parlamentares.microdados,
   br_me_siconfi.municipio_despesas_funcao)*

## E6 · Vantagem de incumbência via emenda

> "esse conjunto de recursos e estruturas cria uma vantagem significativa para quem
> já ocupa um mandato" — emenda como capital político para a reeleição.

1. Entre deputados federais eleitos em 2018, o valor total de emenda destinada no
   mandato (2019–2022) é maior, em média, para os que se reelegeram em 2022 do que
   para os que concorreram e perderam? *(n=2: br_cgu_emendas_parlamentares.microdados,
   br_tse_eleicoes.candidatos cruzado com resultados_candidato)*
2. Deputados que não destinaram nenhuma emenda rastreável no mandato têm taxa de
   reeleição menor que os que destinaram? *(n=2: mesmas duas acima)*

## E7 · Concentração vs. pulverização do valor das emendas

> Bondarovsky: "o volume de recursos e pagamentos torna a fiscalização um desafio";
> Marchesini/Bocayuva/Brito (Insper): a maioria dos parlamentares não usa mecanismo
> participativo algum na escolha de destino das emendas.

1. Que fração do valor total pago em emendas (2014–2025) está concentrada no decil de
   maior valor por emenda individual, vs. quanto do total representa a metade das
   emendas de menor valor? *(n=1: br_cgu_emendas_parlamentares.microdados)*

## E8 · Avanço do Legislativo sobre o orçamento

> "elas somaram R$ 50,4 bilhões [2025], quase 30% das despesas primárias
> discricionárias do Executivo federal"; crescimento de "R$ 2 bilhões, em 2013, para
> aproximadamente R$ 60 bilhões em 2025" segundo a Central das Emendas.

1. Como evolui o total anual pago/empenhado em emendas parlamentares de 2014 a 2025 no
   mirror, e essa curva confirma o salto que a reportagem descreve? *(n=1:
   br_cgu_emendas_parlamentares.microdados)*
