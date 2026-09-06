# Achados fortes — rodadas de 2026-09-05 e 2026-09-06

Relações medidas no beelink cruzando os datasets espelhados entre **2026-09-01 e
2026-09-04** (Pix por município, ANM/CFEM, IBAMA autos+embargos+CTF, INPE DETER,
PRODES acumulado, ANEEL GD, PNCP, CGU Sanções, Gás do Povo, Novo Bolsa Família,
BCB SCR.data/Desenrola/IF.data, Transferegov SICONV, IBGE CNEFE, Tesouro CAUC,
RF DIRPF, SINAN arboviroses, SEDEC, CGU terceirizados, Querido Diário texto,
Senado dados abertos) contra as covariáveis já conhecidas do espelho.

Perguntas em [`perguntas.md`](perguntas.md) temas 57–76; respostas completas,
com os pendentes e os avisos de dado, em [`respostas.md`](respostas.md) na seção
"Rodada 2026-09-05".

Correlações são **Spearman** sobre 5.570 municípios ou 27 UFs. Onde aparece
`r_parcial`, o efeito foi medido **depois de residualizar log-população,
log-PIB per capita e efeito fixo de UF** — é o que separa achado real de
"município grande/rico tem mais de tudo".

## As relações fortes

| # | Relação | Nível | n | Valor | Por que importa |
|---|---|---|---|---|---|
| **B1** | Proposta de convênio **com emenda parlamentar** vira convênio assinado | proposta | 524.919 | **86,5% × 15,6%** | A emenda não empurra: ela *é* o mecanismo de aprovação. Sem padrinho, o SICONV é uma fila que quase ninguém atravessa |
| **B2** | Densidade agropecuária (CNEFE) × cobertura 4G/5G (Anatel) | município | 5.570 | **r_parcial −0,55** | Maior parcial de todo o painel novo. O apagão digital é **rural**, não "de município pequeno" |
| **B3** | Auto do IBAMA pela **mesma tipificação**: Amazônia × Cerrado | auto | 69.381 | **R$ 115 mil × R$ 24 mil**; infração documental **45×** | A régua da multa muda com o bioma, não só a escala do dano |
| **B15** | Desmatamento acumulado 2002–2025 (PRODES) | bioma | 7 | **Cerrado 326.731 km² × Amazônia 139.868 km²** | O Cerrado desmatou 2,3× a Amazônia; Cerrado + Caatinga somam 3,3×. A geografia da atenção não é a da perda |
| **B9** | Desenrola por mil famílias do Bolsa Família | UF | 27 | **DF 945 × MA 100 (9,4×)**; r com PIB pc **+0,89** | Programa de renegociação de dívida de pessoa endividada chegou 9× mais aos estados ricos |
| **T73-2** | Margem do intermediário na terceirização federal | posto | 161.274 | **1,87× (superior) → 3,31× (alfabetizado)** | A margem é **regressiva**: no topo o trabalhador leva 53% do que o governo paga; na base, 30% |
| **B13** | Empresas de terceirização federal sancionadas pela própria CGU | empresa | 7.905 | **1.261 (16%)** | Uma em cada seis empresas que fornecem gente ao Executivo está no CEIS/CNEP |
| **B4** | Geração solar por domicílio × cobertura do Bolsa Família | município | 5.551 | **r_parcial −0,34** | A placa solar é marcador de classe que **sobrevive** ao controle de renda |
| **B11** | Templos por domicílio (CNEFE) × Bolsa Família | município | 5.555 | **r_parcial +0,22** (quintis 0,081 → 0,261) | **Corrige o A16** da rodada anterior: medindo o prédio (CNEFE) e não o CNPJ, a associação dobra e resiste ao controle |
| **T70-3** | Obras em construção por domicílio × PIB per capita | município | 5.570 | quintis **R$ 40,6 mil → 14,6 mil** | Inverso da intuição: o canteiro de obras do Brasil é **autoconstrução pobre**, não incorporação |
| **B10** | Inadimplência PF (SCR.data) × conectividade (IBC) | UF | 27 | **r −0,62** contra −0,31 com PIB pc | Quem não paga é previsto melhor por internet do que por renda |
| **T66-2** | "Adiantamentos a depositantes" | modalidade | — | **59,2% de inadimplência**, 0,06% da carteira | Pior crédito do país e irrelevante sistemicamente. Imobiliário: R$ 24,6 tri a 1,28% |
| **B5 / T59-1** | Alerta DETER × autuação IBAMA | município | 1.251 | **r_parcial +0,36**; **27 municípios** com >10 km² alertados e **zero** autos desde 2015 | Ourilândia do Norte/PA: 30% do desmate de São Félix do Xingu, 3% dos autos |
| **T58-1** | Substância minerada × perfil social | município | 3.217 | Basalto: PIB pc R$ 46 mil, BF 6% · Quartzito: R$ 13,4 mil, BF 32% | A **substância** prediz a sociedade; o valor da CFEM não (r = +0,23) |
| **B18** | BNDES: cobertura indireta automática × direta | município | 5.570 | **4.772 × 379 (12,6×)** | Sem banco credenciado, o fomento federal atinge 6,8% do país |
| **B7 / B16** | Pix como termômetro territorial | município | 5.570 | **70% dos municípios são devedores líquidos**; penetração **r_parcial +0,38** com 4G/5G | Adoção do Pix é infraestrutura, não bolso |
| **T69-2** | Pendências do CAUC por item | município | 5.570 | **Matriz de Saldos Contábeis 1.509** × transparência eletrônica **8** | O Brasil municipal publica; o que ele não consegue é fechar a contabilidade no padrão exigido |
| **T68-3** | CAUC × sucesso em convênio | município | 5.568 | **r_parcial −0,001** | O filtro fiscal não morde — quem seleciona é a emenda (B1) |

## Rodada de fechamento das pendentes (2026-09-05)

Segunda passada respondendo perguntas antes marcadas `⏳`. Mesma metodologia
(Spearman; `r_parcial` residualiza log-população, log-PIB per capita e UF).

| # | Relação | Nível | n | Valor | Por que importa |
|---|---|---|---|---|---|
| **C1** | Crédito rural (SICOR) × desmatamento acumulado | município | 5.456 | **r_parcial +0,64**; **+0,39** controlando também a área do CAR | Confirma e endurece o achado clássico — mas contra o alerta DETER recente cai a **+0,07**: o crédito está no desmate **consolidado**, não na frente ativa. **Reconfirmado em 2026-09-06 (H17)** sob controle de área (+0,46) e em forma puramente intensiva, crédito por hectare × share da área desmatada (**+0,45 parcial**, quintis 0,37→0,83, igual dentro e fora da Amazônia) — é o único dos dois achados de desmatamento que sobrevive |
| **C2** | Valor agropecuário por hectare × crédito por hectare | município | 5.456 | **r = +0,73**; × área do CAR **−0,45** | Crédito rural é **intensificação, não extensão** — e os municípios de maior área cadastrada produzem *menos* por hectare |
| **C3** | Violência notificada contra adolescente (SINAN) × homicídio juvenil (SIM) | município | 5.524 | **r = +0,003** — e **+0,22 com PIB per capita** | A notificação mede a existência de um serviço que notifica, não a de violência. Notifica-se mais onde a escola é melhor e a internet funciona |
| **C4** | INSE (INEP) × cobertura do Bolsa Família | município | 5.543 | **r = −0,90** | O "indicador socioeconômico" do INEP é um índice de pobreza com outro nome — usá-lo como controle ao lado de renda é colinearidade |
| **C5** | Obesidade adulta (SISVAN) × PIB per capita | município | 5.287 | **r = +0,54**; déficit infantil × Bolsa Família **+0,46** | As duas faces da transição nutricional coexistem no mesmo país e ano, com geografias **opostas** |
| **C6** | Remuneração federal ÷ mediana RAIS da UF | UF | 27 | **PB 7,74× · AP 2,73×** | O servidor federal é elite de renda muito maior no Nordeste — não porque ganhe mais (salário quase igual), mas porque o entorno ganha menos |
| **C7** | Margem sobre o terceirizado federal | posto | 161.274 | 1,87× (superior) → **3,31×** (alfabetizado) | Já em B12; a regressividade da margem se confirma escalão a escalão |
| **C8** | Medalhas olímpicas do Brasil por edição | edição | 20 | 1980 **9** → 1984 **37**; 1992 **14** → 1996 **68** | Degraus de política esportiva, não curva de PIB — estável em 55–86 mesmo na recessão de 2015–16 |
| **C9** | Preço da gasolina (ANP) × PIB per capita | município | 416 | **r = −0,21**; × postos por 100 mil hab **+0,02** | Gasolina é **mais cara no município pobre**, e concorrência não explica nada: Parintins/AM R$ 8,39 × Goiatuba/GO R$ 5,76 (45%) |
| **C10** | Vazão recente ÷ histórica (ANA) | município | 292 | mediana **0,901**; **38% perderam >20%** | 10% menos água que a média histórica — mas a rede de estações **não cobre a fronteira agrícola**, então o cruzamento com fogo é enviesado |
| **C11** | Desmatamento acumulado por UF (PRODES) | UF | 27 | PA 113.139 km²; depois **BA 58.435, MT 58.246, TO 53.993, MA 52.977, GO 49.651** | Cinco estados de Cerrado/Caatinga/MATOPIBA entre os seis primeiros |
| **C12** | "Frente ativa" = DETER ÷ passivo acumulado | município | 756 | mediana **0,043**; Normandia/RR **3,97**, Japurá/AM 2,79, Pacaraima/RR 2,35 | A fronteira que se abre agora é **Roraima e Amapá**, não o Pará dos anos 2000 |
| **C13** | UFs como países: faixa de renda do Banco Mundial | UF | 27 | **22 de 27 são "renda média-alta"**, nenhuma de baixa renda | Combinado com AP 64,7 homicídios/100 mil: **renda média-alta com letalidade de zona de guerra** |
| **C14** | Deslocamento intermunicipal (RAIS) dentro da região imediata | vínculo | 13,67 mi | **58,6%** (84,8% na mesma UF) | A hierarquia urbana do IBGE contém quase todo o movimento — **mas o saldo líquido não é migração** (ver avisos) |
| **C15** | HHI de titulares da CFEM | município | 3.218 | mediana **0,822**; **44% acima de 0,9** | Em metade dos municípios mineradores um único CNPJ responde por mais de 82% da arrecadação |
| **C16** | Municípios fora da Área Mínima Comparável 2000→2010 | município | 5.571 | **6** (o Censo 2022 captou 5) | A malha municipal está congelada desde 2010 — contra 3.800 AMCs necessárias para comparar 1970 com 2010 |
| **C17** | Pendências do CAUC por item | município | 5.570 | Matriz de Saldos Contábeis **1.509** × transparência eletrônica **8** | Já em T69-2; o gargalo do município brasileiro é contábil, não de publicidade |

## Outros números da rodada

| # | Fato | Valor |
|---|---|---|
| B17 | Convênio **com** emenda: execução do repasse | **52,2% × 31,8%** sem emenda (e mediana de pedido menor: R$ 289 mil × R$ 478 mil) |
| B6 | Ticket médio do Pix PF × cobertura do Bolsa Família | **r_parcial −0,37** — bom proxy de pobreza, ruim de riqueza |
| B8 | Cobertura do CAR (SICAR) × desmatamento acumulado | **r_parcial +0,35** — o cadastro persegue a fronteira, não a antecipa |
| B12 | Custo pago pelo governo ÷ salário do terceirizado | **2,5× no posto mediano** (R$ 4.352 × R$ 1.731) |
| B14 | Top 100 fornecedores do PNCP no valor global | **95,3%** — indício de valor sujo, não de concentração real (ver avisos) |
| T62-3 | Cobertura do PNCP | **4.687 de 5.570 municípios (84%)**, mediana de 228 contratos |
| T64-1 | Gás do Povo sobre o Novo Bolsa Família | **26,2%** (3,49M × 13,34M), variando 4× entre municípios (p10 8,6% · p90 32,4%) |
| T61-5 | Geração distribuída por titular | **4,26M empreendimentos PF (35,4 GW) × 363 mil PJ (18,1 GW)** |
| T67-1 | Municípios com instituição financeira sediada (IF.data) | **467 de 5.570 (8,4%)** |
| T76-3 | CEAPS por senador: extremos | **AM R$ 614 mil × GO R$ 164 mil (3,7×)** — e o DF, dos que menos gastam, lidera em discursos (425,5) |

## Desbloqueio registrado

O Senado passou a ter `processo` (162.678 proposições), `votacao_parlamentar`
(288.855 votos nominais), `discurso` (99.620), `relatoria` e `senador_comissao`.
Isso **fecha o bloqueio T05-2**, que estava catalogado como "o espelho não tem
tabela de proposições do Senado — pipeline necessário". A comparação
Câmara × Senado é agora possível sem scraping novo.

## Rodada de fechamento das pendentes (2026-09-06)

Terceira passada, respondendo o que restava marcado `⏳`. Cobertura final:
**263 ✅ · 82 ◐ · 28 ⏳** de 373 perguntas (partiu de 132 pendentes).

| # | Relação | Nível | n | Valor | Por que importa |
|---|---|---|---|---|---|
| **D1** ⚠️ | Área rural declarada ao fisco (CAFIR) × desmatamento acumulado | município | 5.547 | **r = +0,82 bruto → +0,31 controlando a área do município → +0,04 em intensidade** | **Rebaixado pela bateria H16 (2026-09-06).** O bruto era escala: os dois lados são áreas, e log-população não controla área. Na forma intensiva (share da área municipal cadastrada × share desmatada) sobra +0,04, e o pouco que sobra é **só Amazônia Legal** (+0,32 dentro, −0,00 fora, n=4.779). Ver `respostas.md`, bateria H01–H19 |
| **D2** | Encarceramento (SISDEPEN) × queda de homicídios 2015→2021 | UF | 27 | **r = −0,02** | Prender mais não previu queda maior. O que a taxa de encarceramento acompanha é riqueza (**+0,52 com PIB pc**) |
| **D3** | Letalidade policial como fatia da letalidade total | UF | 27 | **AP 13,0% e RJ 12,7% × SE 0,6%** | 20× entre UFs. Não responde a violência (r = −0,07) nem a encarceramento (−0,09): é doutrina de corporação |
| **D4** ⚠️ | Lacuna salarial de gênero (RAIS) × PIB per capita | município | 5.404 | **r = +0,61 bruto → +0,11 parcial**; em **39% dos municípios a mulher ganha mais** | A lacuna é fenômeno de município rico **no bruto**. H13 (2026-09-06) rodou o parcial e testou a alternativa racial do Censo 2022: composição racial por instrução prevê **pior** (+0,06) que renda (+0,11). Sob controle, nada previu a lacuna |
| **D5** | Cobertura de plano de saúde privado (IEPS) × pobreza | município | 5.550 | **r = −0,73** | O sistema é literalmente dois: onde há renda, há plano; onde não há, há ESF (**+0,29 com pobreza**) |
| **D6** | Convênios do CEPIM: execução financeira | convênio | 962 | **85,1% × 39,3%** da média SICONV | Não travaram: o dinheiro saiu inteiro e a prestação de contas não voltou. 283 "Inadimplente" + 254 "PC Rejeitada" |
| **D7** | Devedores da PGFN que vencem licitação federal | empresa | 6,68 mi PJ | **25.643 com R$ 241,7 bi de dívida ativa** | Débito inscrito não impede — nem na licitação, nem no cartão corporativo (12.130) |
| **D8** | Sócios de empresas sancionadas em outras empresas | sócio | 10.064 | **5.941 (59%) em 17.581 outras empresas** | A sanção recai sobre o CNPJ; o sócio já está em outras três empresas |
| **D9** | Licitações federais com **um único participante** | licitação | 23.046 | **55,0%** — financeiro 97%, associações 91%, saúde 76% | Onde o objeto é serviço especializado, a disputa praticamente não existe |
| **D10** | Presença bancária (ESTBAN) 2014→2022 | município | 3.674 | **1.813 (49%) perderam, 103 ganharam**; r com PIB pc **−0,08** | Metade do Brasil municipal perdeu banco em 8 anos, e a saída não escolhe pelo bolso |
| **D11** | Instituições financeiras sediadas (IF.data) | município | — | **690 em 2009 → 464 em 2025**, com instituições subindo de 2.114 para 2.295 | O sistema ganhou instituições e perdeu territórios ao mesmo tempo |
| **D12** | Crédito rural × produção agropecuária, 2019→2024 | município | 5.222 | crédito **2,75×** × PIB agro **1,66×**; 74% descolados | O descolamento é maior no município pobre (**−0,27 com PIB pc**) |
| **D13** | CNPJ sancionados citados em diários oficiais | município | 524 | **2.755 empresas em 482 municípios (92%)** | 449.693 CNPJ extraídos do texto integral em uma passada — caminho de auditoria que o PNCP não permite |
| **D14** | Declaração local de emergência × reconhecimento federal | município | 524 / 1.147 | **401 declaram · só 83 nos dois** | A instância mais frequente do desastre brasileiro é a menos visível |
| **D15** | Escolas rurais "Sem Internet" × urbanas (SIMET) | escola | 127.950 | **30,5% × 2,0% — 15×**; dentro do município, quase empate | A defasagem é entre municípios, não intramunicipal — confirma B2 |
| **D16** | Disciplina partidária: Senado × Câmara (índice de Rice) | partido | — | UNIÃO **0,78 × 0,64**, PSDB **0,86 × 0,71**, MDB **0,87 × 0,72**; PT 0,94 × 0,97 | O Senado é ~15 pontos mais disciplinado — e a diferença inteira é do centrão |
| **D17** | Hora extra no Senado × votações no mês | mês | 36 | pico em **julho (3,6× a mediana, recesso)**; agosto lidera votações e fica abaixo | Segue o calendário administrativo, não o plenário |
| **D18** | Cooperativas de crédito sediadas × bancos grandes | município | — | **433 × 20**; 416 só com cooperativa, pop. mediana **51,5 mil** | Cooperativa ocupa cidade média próspera, não município pequeno abandonado |
| **D19** | Notificação de dengue × PIB per capita | município | 4.604 | **+0,22** (e −0,21 com pobreza) | Terceiro caso do mesmo artefato: a série mede capacidade de registro antes de medir fenômeno (com T28-1 e T42-5) |
| **D20** | Doadores empresariais de 2014 que hoje são fornecedores | empresa | 18.230 | **10,7% no PNCP**; do quintil que menos doou ao que mais doou, 9,7% → 12,1% | Existe gradiente, mas de ~2,5 pontos — não de ordem de grandeza |
| **D21** | Despesa do Judiciário estadual per capita | tribunal | 28 | **TJDFT R$ 985 × TJCE R$ 145 — 6,8×** | "Custo por processo" segue incalculável; "custo por brasileiro" varia 7× |
| **D22** | Assistência social na despesa municipal × demanda local | município | 5.356 | **3,51% da despesa**; r com Bolsa Família **+0,02** | Onde o repasse federal é maior, o município gasta o mesmo — não compensa nem duplica |

## Hipóteses inéditas testadas fora de `perguntas.md` (2026-09-06)

Geradas a partir dos **17 datasets com chave territorial que nunca entraram em
`perguntas.md`** (ver a seção de cobertura abaixo). São hipóteses sem pergunta
prévia — testadas do zero, com o resultado reportado inclusive quando nega a
hipótese.

| # | Hipótese | n | Resultado |
|---|---|---|---|
| **E1** | *Concentração onomástica como índice de desenvolvimento*: municípios onde o nome próprio mais comum concentra mais nascimentos são mais pobres | 5.565 | **Bruto forte, parcial fraco.** Share do nome mais comum × pobreza **+0,48**, × IVS 2010 **+0,41**, × PIB pc **−0,46**. Mas controlando log-população e log-nascimentos (o município pequeno tem poucos nomes por construção), sobra **+0,11 com pobreza e −0,15 com renda**. **Encerrado em 2026-09-06**: com o painel completo da bateria (H18) o parcial cai a **+0,03**, e a diversidade de nomes × PIB pc a −0,02. Não sobra nada — reportado aqui justamente porque a versão bruta é sedutora e enganosa |
| **E2** | *Pé-de-Meia acerta o alvo?* Focalização do programa de permanência escolar (2,2 milhões de alunos, 5.547 municípios) | 5.547 | **A melhor focalização medida neste espelho: r = +0,89 com a cobertura do Bolsa Família**, −0,67 com PIB per capita, −0,67 com formalização. Supera o Gás do Povo em alcance relativo (T64-1, que cobre só 26% do cadastro) e é o oposto da geografia do Desenrola (B9) |
| **E3** | *A nota de transparência (EBT/CGU) prevê integridade?* | 665 | **Não — e o sinal é o contrário.** EBT × empresas sancionadas por 100 mil hab: **+0,18**; × pendências no CAUC: **−0,14**; × contratos por fornecedor no PNCP: **+0,17**. Município mais bem avaliado em transparência tem *mais* fornecedor sancionado e *mais* concentração de fornecedor. A nota mede **publicação**, não conduta — o mesmo padrão de T69-2 (o Brasil municipal publica; o que ele não faz é fechar a contabilidade) |

## Bateria de hipóteses H01–H19 (2026-09-06)

Rodada completa de `scripts/hipoteses_overnight.sh` — 5 blocos SQL + análise em
**88 segundos**, painel de **5.571 municípios × 164 colunas**, 1.941 pares
intensivos varridos. Cada hipótese tinha a **condição de falseamento escrita
antes de rodar**; a maioria falseou. Respostas completas em
[`respostas.md`](respostas.md), fila e método em
[`tasks/hipoteses.md`](../../tasks/hipoteses.md).

Aqui só o que **sobreviveu ao parcial** e merece ficar como achado.

| # | Relação | Nível | n | Valor | Por que importa |
|---|---|---|---|---|---|
| **F1** | Devedores da PGFN entre os credores de pagamento municipal (MIDES 2018–2024) | município | 3.061 | **12,2% dos credores levam 22,7% do valor** — R$ 467,6 bi de R$ 2.063,7 bi | Devedor da União não é exceção do fornecedor municipal: é o fornecedor **grande**. A desproporção entre contagem e valor é o achado, não a presença |
| **F2** | Reclamação no Consumidor.gov como medida de **acesso digital** | município | 5.563 | **r_parcial +0,29** com penetração do Pix, **+0,28** com conectividade, **−0,16** com pobreza | 9,92 milhões de reclamações. Quintis de reclamação → Pix 0,516→0,637 e pobreza 0,345→0,096, ambos monotônicos. Reclamar é privilégio de infraestrutura — usar a base como proxy de lesão ao consumidor inverte o sinal |
| **F3** | Crédito rural por hectare × **share da área municipal desmatada** | município | 5.456 | **r_parcial +0,45** (bruto +0,54), quintis **0,37 → 0,83** | A forma intensiva do C1: sobrevive ao controle de área e vale igual **dentro (+0,50) e fora (+0,53) da Amazônia Legal**. É o contraste com o D1 que dá o achado — o **fluxo** (crédito) resiste, o **estoque** (cadastro fundiário) não |
| **F4** | Concentração do pagamento municipal num único credor | município | 3.060 | **HHI mediano 0,167**; o maior credor leva **38,5%** do valor no município mediano e **>50% em 234 municípios** | Primeira medida de concentração de fornecedor **municipal** do espelho. Descritivo forte; o que a explica não é: pobreza (+0,14) e densidade empresarial (−0,13) pesam igual |
| **F5** | Pagamento municipal a empresa sancionada (CEIS/CNEP) | município | 3.339 | **R$ 18,4 bilhões** — 0,80% do valor entre os 3.339 municípios com pagamento (0,71% sobre todos os município-ano), mediana municipal 0,49%, p90 2,12% | Complementa o D13 (sancionado **citado** em diário) com o sancionado **pago**. As duas medidas são independentes (r = −0,004): citação é presença, pagamento é dinheiro |
| **F6** | Constatação **grave** da CGU não acompanha pobreza | município | 1.350 | bruto **+0,37 → parcial +0,08** | 82.664 ordens de fiscalização sorteadas, share grave mediano 11,4%. Depois do controle a irregularidade grave é quase uniforme: o que varia entre municípios é a **chance de ser pego**, não a conduta |
| **F7** | Fornecedor sediado no próprio município que paga | município | 3.063 | **49,4% dos pagamentos** no agregado; quintis de população **35,2% → 50,5%** | A compra pública vaza para o polo regional, e o vazamento é quase todo **porte** (parcial +0,11) |

### Os nulos desta bateria

Medidos com n suficiente — achado negativo, não falta de dado:

| Par | n | r_parcial |
|---|---|---|
| Fatia paga a sancionado × nota de transparência EBT | 345 | **+0,05** |
| Fatia paga a sancionado × ordens de fiscalização da CGU (FEF) | 620 | **+0,02** |
| Fatia paga a sancionado × densidade de empresa sancionada no município | 906 | **−0,004** |
| Nota do consumidor × densidade empresarial | 5.541 | **+0,05** |
| Capital social mediano do estabelecimento × formalização | 5.570 | **−0,02** |

Lidos juntos, os três primeiros dizem uma coisa só: **nada do que se publica
sobre integridade municipal prevê para onde o dinheiro municipal efetivamente
vai** — nem a nota de transparência, nem a auditoria federal, nem a presença de
empresa sancionada no território. É o E3 generalizado do indicador para o caixa.

### O que a bateria derrubou

**D1** (CAFIR × desmatamento, +0,82) e **E1** (concentração onomástica) caíram; a
ressalva de **D4** (lacuna de gênero) foi registrada na tabela acima. As três
correções têm a mesma causa e estão marcadas com ⚠️ nas linhas originais.

## Achados da varredura de inéditos (2026-09-06)

Saíram do método de §5 de [`tasks/hipoteses.md`](../../tasks/hipoteses.md):
subtrair de todas as combinações de família as que `perguntas.md`, `hipoteses.md`
e este arquivo já ocupam, e aplicar os **8 moldes** de
[`docs/context/moldes.yaml`](context/moldes.yaml) às fontes que nunca os
receberam. Rodada completa em 2026-09-06: **G1–G7** abaixo são o que sobreviveu de H20–H36 (5 confirmadas, 4 falseadas, 3 nulas, 1 sem dado). Respostas completas em [`respostas.md`](respostas.md).

| # | Relação | Nível | n | Valor | Por que importa |
|---|---|---|---|---|---|
| **G1** | Dispersão do preço de medicamento entre compradores públicos (Banco de Preços em Saúde) | item × unidade × ano | 1.199 células, R$ 7,1 bi | **razão p90/p10 mediana 2,40×**; decil mais disperso **3,75×** | Mesmo medicamento, mesma unidade de fornecimento, **mesmo ano** — e o comprador do décimo mais caro paga 2,4× o do décimo mais barato. Midazolam 5 mg/ml injetável (2021) varia **5,8×**; risperidona 1 mg/ml, 4,4×; enoxaparina 100 mg/ml, 3,3× sobre R$ 109 milhões. `br_saude_bps` tem CNPJ do comprador **e** do fornecedor: a cadeia é rastreável |
| **G2** | **Tamanho médio** da propriedade rural (CAFIR, ha/imóvel) × uso da terra | município | 5.436–5.542 | crédito por hectare **r_parcial −0,301**; valor agropecuário por hectare **−0,204** (com log-área) | O que sobra do D1. A *quantidade* de terra cadastrada era escala e morreu; o *tamanho* dela sobrevive. Do 1º ao 5º quintil (130 ha → 3.630 ha), o valor agropecuário por hectare cai de R$ 294 para R$ 40 e o crédito de R$ 365 para R$ 59 — **7× e 6×**. A perna de desmatamento **não** sobrevive (+0,09; −0,015 dentro da Amazônia): tamanho de propriedade é intensidade de uso, não fronteira |
| **G3** | O SNIS de saneamento é auto-declarado — e o que prevê o quanto se declara é **conectividade**, não rede | município | 5.302 | razão declarado/base-IBGE **mediana 0,616**; **98,1% declaram menos** que o IBGE; × cobertura 4G/5G **r_parcial +0,634** | **Segundo maior parcial já medido neste espelho**, atrás só do B2. O município mediano informa atender 62% do que a base do IBGE lhe atribui, e a lacuna é predita por celular (+0,63) muito acima de renda (+0,12). Quintis de formalização → razão 0,404 → 0,824. O "déficit de saneamento" do SNIS é, em boa parte, déficit de quem preenche o formulário |
| **G4** | Obra formalmente registrada (CNO) ÷ domicílio em construção (CNEFE) | município | 5.568 | mediana **0,46**; × pobreza **r_parcial −0,346**, × densidade de obras **−0,458** | Fecha o T70-3 pelo lado da formalidade: onde **mais** se constrói, **menos** se registra. Menos da metade do canteiro brasileiro tem obra registrada, e a fração cai justamente onde a construção é mais intensa |
| **G5** | Coleta de lixo em Belo Horizonte × padrão de acabamento do imóvel | imóvel | 5,25 mi | coleta diária: **P1 1,5% → P5 81,4%**; positiva em **9 de 9** zonas | Primeiro achado **intraurbano** do espelho. Controlando zoneamento, o serviço público mais básico é distribuído por padrão construtivo em cinco degraus monotônicos. Nas duas zonas centrais é 100% para todos — onde o serviço é universal a hierarquia some; onde é escasso, ela aparece |
| **G6** | Infraestrutura urbana precificada em Fortaleza | face de quadra | 68.932 | face **com** esgoto vale **2,01×** a sem; sem pavimento R$ 26 → asfalto R$ 59 → concreto R$ 90; índice 0–6 × log valor **r +0,42** | Preenchimento >99,7% nos 6 indicadores, com centróide. **Mas dentro do mesmo logradouro sobra +0,034**: a infraestrutura é precificada por rua, não por face — a desigualdade urbana de Fortaleza tem grão de quarteirão, não de lote |
| **G7** | A nota CAPAG não prevê endividamento municipal | município | 4.747 | contratou operação de crédito: **A+ 40,4% × D 5,3%**, mas **r_parcial −0,004** | Sexto caso de "a regra formal não morde", com T68-3, D7, D9, F1 e F5. O gradiente aparente é inteiramente renda: o PIB pc mediano vai de R$ 43.305 (A+) a R$ 12.142 (D) |

## Fechamento do Bloco I e diagnósticos do Bloco H (2026-09-06)

As duas hipóteses do Bloco I (`tasks/hipoteses.md`, H41–H45) que sobreviveram
ao parcial, promovidas depois da checagem de magnitude que `CLAUDE.md` exige
(ordem de grandeza esperada, flag de anomalia, verificação por duas vias —
método completo em `scripts/hipoteses/96_blocof_fechamento.py`). As outras três
(H41 choque de exportação, H42 terceirização da saúde, H43 troca de partido)
fecharam como nulo ou confirmação parcial pequena demais para entrar aqui — ver
`respostas.md` tema 77 e `tasks/hipoteses.md`.

| # | Relação | Nível | n | Valor | Por que importa |
|---|---|---|---|---|---|
| **I1** | Cobertura do Bolsa Família (`nbf_share_dom`) prevê maternidade adolescente (SINASC) melhor que estrutura ocupacional feminina ou IDEB | município | 5.555 | **r_parcial +0,30** (bruto +0,61) — maior que o HHI ocupacional (+0,09, hipótese original) e que o IDEB (−0,23) | Pobreza, não mercado de trabalho feminino nem escola, é o que prevê mãe adolescente. Checado contra a taxa nacional do SINASC/MS (~15–18% dos nascidos vivos): mediana do painel 13,7%, agregado 12,3% — mesma vizinhança, sem sinal de erro de denominador |
| **I2** | Choque de CFEM (2017-21→2022-25) não move nem o saldo do CAGED nem as pendências do CAUC — "mineração emprega pouco" e não é choque fiscal detectável | município | 2.865 | **r_parcial +0,04** (CAGED) e **−0,002** (CAUC), ambos nulos | Duplo nulo verificado contra o risco óbvio de artefato: a razão explode nos municípios de denominador quase-zero (p5 do CFEM 2017-21 = R$ 661; razão mediana 9,4× nesse grupo), mas excluí-los não muda a leitura (CAGED +0,05, CAUC −0,01) — o nulo é do grosso da distribuição, não driven por outlier |
| **I3** | Intensidade de construção por domicílio (CNEFE) acompanha crescimento populacional 2000→2010 independentemente do PIB — nível **e** crescimento | município | 5.565 | **r_parcial +0,31** (era +0,33; quase não muda ao acrescentar crescimento do PIB, `pib/pib_2010-1`, ao controle padrão de nível de PIB) | H39 de `tasks/hipoteses.md` §5.2 Bloco H — hipótese sinalizada pela outra sessão, fechada aqui por acordo de divisão de trabalho (`scripts/hipoteses/97_h38_h40.py`). Complementa o T70-3 (obras × PIB per capita, inverso: autoconstrução pobre) com uma perna demográfica que T70-3 não testou — o canteiro cresce onde a população cresce, não só onde falta renda |

**Nota de nomenclatura (2026-09-06):** os três primeiros achados desta seção
eram rotulados H1/H2/H3, que colidem com os nomes das hipóteses H01–H03 de
`tasks/hipoteses.md` §2 Bloco A (HHI de credores, credor local, pago a
sancionado) — flagrado pela sessão `analise-hipoteses-municipais`. Renomeados
para **I1/I2/I3** (casa com o Bloco I de onde vêm I1/I2).

I1 e I2 vêm do Bloco I (H41–H45, `respostas.md` tema 77); I3 vem do
Bloco H de §5.2 (`div_nomes`/`obras_1000dom`/MIDES, sinalizados pela sessão
`analise-hipoteses-municipais` e cedidos por acordo — ver `tasks/hipoteses.md`).
H38 e a metade de H40 (`div_nomes × mides_valor_pc`) que testei junto **não**
sobreviveram: H38 é definicional (mesma tabela, dois resumos da mesma
distribuição), e a inversão de sinal de H40 é artefato de recorte de
cobertura do MIDES — nenhum dos dois entra aqui, detalhe em
`tasks/hipoteses.md`.

## Lei Rouanet — H30/H31 (2026-09-06)

`br_minc_salic` (projetos, entidades, incentivos, recibos) nunca tinha sido
cruzado com nada neste espelho — sem view no `.duckdb`, lido via
`read_parquet` direto (`scripts/hipoteses/71_rouanet.sql` + `99_rouanet.py`).
Detalhe em `tasks/hipoteses.md` §5.2 Bloco G.

| # | Relação | Nível | n | Valor | Por que importa |
|---|---|---|---|---|---|
| **K1** | Funil Rouanet (aprovado→captado) por região — **invertido** do previsto | projeto | 196.539 (81.447/3.073 Sudeste/Norte com aprovado>0) | Captação mediana **Sudeste 0,47 × Norte 1,00**, diff=−0,53, **p=0,0002** | A hipótese original apostava em Sudeste convertendo melhor (rede de patrocinador maior) — é o oposto: Sudeste aprova 26× mais projetos que o Norte e uma fatia bem maior deles nunca capta nada. Aprovação pouco seletiva onde o volume é grande, não rede de patrocínio, é o que explica a diferença |
| **K2** | Proponente e patrocinador da Rouanet × CEIS/CNEP e PGFN, contra taxa-base de CNPJ ativo | CNPJ | 27.274 proponentes, 22.399 patrocinadores | Sancionado **17-24×** a taxa-base (0,0117%); devedor PGFN **1,7-3,2×** (9,87%) | Sétimo caso de "a regra não morde" (com T68-3, D7, D9, F1, F5, G7) — o incentivo fiscal cultural tem o mesmo filtro de integridade que a compra pública: nenhum. Patrocinador (quem tem o benefício fiscal) é mais devedor que proponente (31% × 17%). **Sem controle de porte/setor** — parte do excesso pode ser que CNPJ ativo o bastante para patrocinar cultura não é o CNPJ médio dos 67,6 milhões ativos no país, que inclui muito microempresa/inativo |

**Correção de método que valeu a pena registrar**: a taxa-base "certa" para
comparar contra CEIS/CNEP e PGFN é `count(DISTINCT cnpj)` de
`br_me_cnpj.estabelecimentos` (CNPJ **ativo**), não uma razão entre dois
números de universos diferentes — o 6,68 milhões citado em D7 é o próprio
universo de devedores da PGFN (confirmado aqui: 6.673.698 de 67.640.763 CNPJ
ativos são devedores PGFN, bate exatamente com o D7), não o total de empresas
do país. Dividir 7.893 (sancionados) por 6,68 milhões (devedores) mistura o
numerador de um cadastro com o denominador de outro — sempre vai inflar
qualquer interseção testada contra essa base.

## Trincas corrigidas do Bloco R — ITR × propriedade rural (2026-09-06)

`mobilidade` e `fiscal_municipal` estavam catalogadas em `tasks/hipoteses.md`
§5.5 Bloco R como travadas por grão de fonte — na verdade só a tabela
específica citada estava travada (`br_mobilidados_indicadores` tem 9
municípios **na tabela de transporte de alta capacidade**; `br_rf_arrecadacao`
não tem município **na receita geral**). Rerodar o gerador de inéditos achou
outra tabela em cada, nunca testada: `itr` (imposto territorial rural, 5.571
municípios) e `proporcao_mortes_negras_acidente_transporte` (5.544). Tema 82
de `perguntas.md`, extração `scripts/hipoteses/72_novidades.sql`,
análise `101_novidades.py`.

| # | Relação | Nível | n | Valor | Por que importa |
|---|---|---|---|---|---|
| **L1** | ITR per capita (Receita Federal) × tamanho médio da propriedade rural (SICAR) | município | 5.563 | **r_parcial +0,53** (bruto +0,47) — sobe, não cai, com o controle; quintis **R$ 2,00 → 98,47 pc (49×)** conforme o tamanho médio vai de 11,7 a 223,5 ha | Nunca medido neste espelho. Faz sentido econômico — o ITR é progressivo por tamanho de imóvel na tabela oficial — mas é o tipo de relação que só aparece cruzando duas famílias (fiscal × fundiário) que nunca tinham sido testadas juntas. Checagem de armadilha extensiva: `sicar_area_media` já é média (não soma), não correlaciona com população (r=−0,00) |

Os outros dois testes do mesmo tema saem nulos (documentados em
`respostas.md` tema 82, não repetidos aqui): notificação de violência
doméstica × conectividade **não** confirma o `registro_vs_fenomeno` (parcial
+0,03, quase todo escala); proporção de vítimas negras em acidente de
transporte × composição racial **não** mostra excesso sistemático (mediana do
excesso −0,13, positivo em só 37% dos municípios — o oposto da hipótese de
disparidade).

**Vale reconferir as outras famílias do Bloco R** (`comercio_exterior`,
`precos_indices`, `seguranca`, `justica`) com o mesmo cuidado — a nota
original pode ter testado a tabela errada dentro do dataset em mais de um
caso.

## Achados das famílias vazias (2026-09-06)

Blocos N–Q de [`tasks/hipoteses.md`](../../tasks/hipoteses.md) §5.5, escolhidos
pelo gerador de inéditos: as sete famílias com **menos combinações ocupadas**.
Extração `scripts/hipoteses/60_familias_vazias.sql`, análise
`scripts/hipoteses/97_familias.py`. Placar: 4 ✅ · 6 ❌ · 3 ◐ · 4 não rodadas;
respostas completas em [`respostas.md`](respostas.md).

| # | Relação | Nível | n | Valor | Por que importa |
|---|---|---|---|---|---|
| **J1** | **Rebanho bovino por hectare** × share da área municipal desmatada | município | 5.538 | **r_parcial +0,486** com log-área no controle (bruto +0,526); quintis **0,332 → 0,831** | **Supera o F3** (crédito rural × desmatamento, +0,45), que era o achado de desmatamento mais forte que sobrevivia à intensidade. Contra crédito por hectare dá +0,291 — as duas medidas contam a mesma história por lados diferentes. E como o crédito, o gado está no desmate **consolidado**: contra o DETER recente cai a −0,097 |
| **J2** | Concentração de tomador do crédito rural (HHI por município, SICOR 2019+ via `id_car`) | município | 5.391 | HHI mediano **0,007**, maior tomador leva **2,7%**; × tamanho da propriedade **+0,174**, × crédito por hectare **−0,352** | O crédito rural é **muito pulverizado** — o oposto da concentração de fornecedor municipal (F4, HHI 0,167). E as duas pernas apontam junto com C2 e G2: onde o crédito é **intenso** ele é disperso; onde a propriedade é **grande** ele concentra. Intensidade pulveriza, extensão concentra |
| **J3** | Cesárea e hora do parto (SINASC 2021, municípios com ≥100 nascimentos) | município | 1.733 | cesárea mediana **59,7%**; **72,5%** delas entre 8h e 17h contra **59,4%** de todos os nascimentos — excedente **+8,7 pontos**, positivo em **95,9%** dos municípios | O excedente horário existe e é quase universal. Mas ele **cai** onde a cesárea é mais comum (**r_parcial −0,622** contra a própria taxa) e onde há mais plano privado (−0,193): onde a cesárea é quase universal ela acontece a qualquer hora — virou o modo padrão de nascer; onde é mais rara, é a agendada |
| **J4** | Escola sem internet (SIMET) × IDEB anos iniciais | município | 5.430 | **r_parcial −0,144** (bruto −0,385); contra PIB pc o parcial cai a −0,063 | A defasagem digital **custa nota** e não é só proxy de renda — o efeito sobre o IDEB sobrevive ao controle, ainda que modesto. Complementa o D15 (30,5% das escolas rurais sem internet contra 2,0% das urbanas) com a perna de desfecho que faltava |

| **J5** | Conectividade prediz **notificação** 4,4× mais do que prediz **internação** | município | 4.950 / 5.570 | notificação de dengue (SINAN 2023) × cobertura 4G/5G **r_parcial +0,159**; internação infecciosa (SIH, CID A/B) contra a mesma cobertura **+0,036** | **A medida direta do viés que C3, D19 e F2 só inferiam.** As duas séries são do mesmo ano e do mesmo sistema de saúde; a única diferença é que uma exige alguém preencher uma ficha e a outra exige um leito. Por quintil de IBC a notificação vai de 117 a 293 por 100 mil (2,5×) e a internação de 183 a 239 (1,3×). Quem usa série de notificação como medida de incidência está medindo, em boa parte, quem consegue notificar |

### Nulos e falseadas com n suficiente

| Par | n | r_parcial |
|---|---|---|
| Esgoto sem tratamento (Atlas ANA) × share de internação infecciosa (SIH) | 5.570 | **−0,015** |
| Esgoto sem tratamento × taxa de óbito infeccioso | 5.570 | **−0,084** |
| Baixo peso ao nascer × esgoto, atenção básica e pobreza | 1.733 | **+0,005 · −0,009 · +0,037** |
| Fogo com chuva recente ("de manejo") × crédito, desmatamento, gado | 5.393–5.500 | **+0,011 · +0,001 · +0,010** |
| HHI da pauta agrícola × mortalidade infecciosa | 5.509 | **+0,001** |
| Termos de embargo do IBAMA por 100 mil hab × tamanho da propriedade | 3.997 | **+0,091** (bruto +0,327 — era escala) |

O nulo de esgoto × internação é o mais instrutivo, e o **sinal é negativo**:
onde há menos saneamento há **menos** internação registrada. É
`registro_vs_fenomeno` pela sexta vez — com C3, D19, F2, H36 e, por outro
caminho, G3. Junto com "a regra não morde" (seis casos: T68-3, D7, D9, F1, F5,
G7), são os dois padrões mais replicados do espelho.

## Quanto do espaço de hipóteses é de fato válido

Medido em cascata sobre `docs/context/basedosdados-schema.json` (228 datasets),
com a **cobertura municipal aferida no beelink** (`approx_count_distinct` sobre a
maior tabela municipal de cada dataset, com amostragem nas acima de 20M linhas).

| Filtro | Datasets | Trincas |
|---|---|---|
| **F0** tem chave territorial | 150 | 551.300 |
| **F1** tem chave **municipal** (só UF dá n=27, poder baixo) | 128 | 341.376 |
| **F2** exclui referência, dicionário e diretório (sem desfecho) | 124 | 310.124 |
| **F3** cobre ≥500 municípios | 114 | 240.464 |
| **F4** cobre ≥2.000 municípios | 103 | **176.851** |
| **F5** três **famílias temáticas** distintas (24 famílias) | — | 146.316 |
| **F6** no máximo uma perna de covariável-controle | — | 145.236 |
| **F7** **trincas de família distintas** — a hipótese, não a instância | — | **2.002** |

**A resposta é 2.002, não 573.800.** As 145 mil trincas de F6 são
*instâncias* da mesma hipótese: RAIS×SIM×PIB e CAGED×SIM×Censo testam a mesma
proposição (mercado de trabalho × mortalidade × demografia) com tabelas
diferentes. O que constitui uma hipótese distinta é a trinca de **famílias**.

Dessas 2.002, `perguntas.md` já cobre **93 (4,6%)** — restam **1.909 hipóteses
substantivas por elaborar**.

### O que os filtros descartaram, e por quê

- **F1 (−22 datasets)**: têm só UF. Uma trinca inteiramente estadual roda com
  n=27 — serve para descrever (o CEAPS por senador, a inadimplência do SCR), não
  para testar associação com controle.
- **F3 (−10)**: cobertura municipal baixa demais, e é aqui que mora a armadilha.
  Vários datasets *parecem* municipais e não são: **`br_ibge_ipca` cobre 9
  municípios** (é pesquisa de região metropolitana), `br_ipea_acesso_oportunidades`
  **18**, `br_fbsp_absp` **29**, `br_mobilidados_indicadores` **9** na tabela de
  transporte de alta capacidade, `br_rj_isp_estatisticas_seguranca` **86** (é só
  o Rio). Cruzá-los "por município" produz n de duas casas.
- **F4 (−11)**: entre 500 e 2.000 municípios — utilizáveis, mas com viés de
  seleção conhecido (é sempre o município grande que aparece).
- **F5/F7 (−143 mil)**: redundância. Somar SINAN dengue + SINAN zika +
  SINAN chikungunya não é uma trinca de três fontes; é uma fonte três vezes.

### Distribuição das 24 famílias

`educacao` 14 · `demografia_censo` 12 · `vigilancia_sinan` 10 ·
`fiscalizacao_ambiental` 7 · `transferencia_renda` 7 · `saude_producao` 6 ·
`credito_financeiro` 5 · `compras_publicas` 5 · `desmatamento_clima` 5 ·
`trabalho_empresa` 5 · `fiscal_municipal` 4 · `conectividade` 3 ·
`agropecuaria` 3 · `politica` 3 · `justica` 3 · `mineracao_energia` 2 ·
`fundiario` 2 · e sete famílias com um único dataset municipal utilizável:
`precos_indices`, `comercio_exterior`, `seguranca`, `mobilidade`,
`mortalidade`, `natalidade`, `sancao_integridade`.

**As famílias de uma perna são o gargalo real do espelho.** Segurança pública
municipal depende inteiramente do SISDEPEN; preços, do IPCA de 9 municípios;
integridade empresarial, do CEIS. Não há como triangular nenhuma delas com
fonte independente — e é por isso que achados como o de letalidade policial
(D3) ou o de sanção (B13, D7, D8) não têm confirmação cruzada dentro do espelho.

### Os 17 datasets territoriais sem nenhuma pergunta

`br_ipea_acesso_oportunidades` (grid H3 com renda, raça e acesso — permite
segregação **intramunicipal**, que nenhuma pergunta atual alcança, embora só
cubra 18 municípios) · `br_mc_indicadores` (Bolsa Família 2004–2020 — efeito de
**longo prazo**, hoje só medido em corte) · `br_ibge_censo2022_raca` ·
`br_mj_consumidorgovbr` (10,2 mi de reclamações) · `br_cgu_seguro_defeso` ·
`br_cgu_pe_de_meia` · `br_ibge_inpc` · `br_ibge_ipca15` · `br_minc_salic` ·
`br_cgu_fef` · `br_cgu_dados_abertos` · `br_mjsp_procurados` ·
`br_ibge_nomes_brasil` · `br_me_rais_identificada` · `world_wb_mides` (303 mi
de empenhos) · `br_cgu_ebt` · `br_geobr_mapas`.

Três deles já foram testados nesta rodada (E1, E2, E3 acima).

## Avisos de dado (quem for reusar estas tabelas)

- **`br_pncp.contratos.valorGlobal` é inutilizável em soma** — R$ 47,7 trilhões
  no total, 406 contratos acima de R$ 1 bi, caso verificado de R$ 2,37 trilhões
  num credenciamento de profissional de saúde municipal. Usar mediana/quantis,
  ou winsorizar em p99 e dizer que winsorizou.
- **`br_pncp.contratos.emendaParlamentar` é 99,4% nulo** — não mede nada.
- **`br_sfb_sicar.area_imovel`: a soma de áreas excede a área municipal em 5.563
  de 5.571 municípios** (mediana 923×). Sobreposição de polígonos e/ou unidade
  divergente. Utilizável como ranking, nunca como fração de cobertura.
- **`br_sedec_desastres` só tem reconhecimentos vigentes** (jan–jul/2026, 1.237
  linhas) — bloqueia qualquer pergunta sobre recorrência ou defasagem temporal.
- **`br_ok_queridodiario` cobre 9,4% dos municípios**, enviesado para grandes,
  ricos e de serviços (× densidade agropecuária = −0,57). Não representa o
  Brasil municipal.
- **`br_anm.scm_*` (SIGMINE) não tem código IBGE** — só `municipio_s` em texto
  livre, frequentemente com vários municípios na mesma célula.
- **`br_bcb_scrdata.dados` traz valores como VARCHAR com vírgula decimal e ponto
  de milhar** — `TRY_CAST` direto retorna NULL em silêncio; usar
  `replace(replace(x,'.',''),',','.')`.
- **`br_ibge_cnefe.enderecos` não tem nulo em CEP nem em logradouro** nos 111
  milhões de registros — exceção positiva neste espelho.
- **Ponte nova — SICOR → município**: `br_bcb_sicor.recurso_publico_propriedade.id_car` é `UF(2) + código IBGE(7) + hash(32)`; `substr(id_car,3,7)` devolve o município em **99,9998%** das 12,54 milhões de linhas. Nenhuma outra tabela do SICOR tem município (`operacao` só tem `sigla_uf`). Destrava o crédito rural municipal (R$ 934,9 bi, 5.564 municípios, 2020–24) sem join com o SICAR. **Registrar em `bridges.yaml`.**
- **`id_municipio_trabalho` da RAIS não é destino de commuting**: é o local de trabalho contra a sede do estabelecimento. São Paulo aparece com saldo de **−1.072.060** — é matriz→filial, não residência→emprego. A estrutura de proximidade (58,6% na mesma região imediata) sobrevive; o saldo líquido, não.
- **A coleta de preços da ANP cobre 422 dos 5.570 municípios (7,6%)** — é pesquisa de capitais e cidades médias, não censo.
- **`br_mma_extincao` não tem coluna geográfica nenhuma** (só espécie/família/ordem/categoria) — qualquer pergunta de espécie ameaçada por bioma ou município está estruturalmente bloqueada.
- **`world_olympedia_olympics.athlete_bio` não tem cidade de nascimento** — só data, ano e país; medalha por município é impossível sem fonte adicional.
- **`br_inpe_sisam` (PM2,5 modelado) mede tráfego metropolitano, não fumaça de queimada** — os 6 municípios de maior PM2,5 são São Paulo e vizinhos, com focos de calor próximos de zero; correlação com fogo apenas +0,15.
- **`br_cgu_servidores_executivo_federal.cadastro_servidores` só preenche `sigla_uf` para parte dos registros** (555.893 de 778.516 em jun/2025) — filtrar por UF descarta 29% do quadro.
- **SISDEPEN não estava corrompido**: `br_mjsp_sisdepen.populacao_carceraria` traz a UF como `"Minas Gerais (MG)"`; `regexp_extract(uf,'\(([A-Z]{2})\)',1)` recupera 575.622 presos em 27 UFs. O preenchimento é desigual (BA sai com 84 presos/100k, implausível) — use para padrão, não para o número de cada UF.
- **`id_car` do SICOR só existe a partir de 2019**: 0% preenchido até 2017, 3% em 2018, 94,7% em 2019, ~98% depois. Série municipal de crédito rural anterior a 2019 é impossível por essa via.
- **`br_ms_sipni_doses_historicas` é ilegível**: view sobre `s3://healthbr-data/` com `union_by_name`; qualquer leitura aborta com `INTERNAL Error: Unsupported type for NumericValueUnionToValue`, e não há parquet local. **Use `br_ieps_saude.municipio`**, que já traz cobertura vacinal municipal pronta.
- **`br_cnj_improbidade_administrativa` tem o Acre com 28.600 condenações** — 5,5× São Paulo, mais da metade do país, num estado de 900 mil habitantes. Artefato de alimentação do cadastro: **excluir o AC de qualquer ranking estadual**.
- **SIM 2022 está incompleto para o RJ**: 1.867 homicídios contra 4.054 em 2021 (razão 0,46). DF (0,60), AP (0,69) e RR (0,70) também. Para séries que terminem em 2022, conferir a razão 2022/2021 por UF antes de concluir queda.
- **`br_siop_orcamento.dados` não tem nenhuma coluna de valor** — é o catálogo de ações de 2025 (5.610 linhas), não orçamento executado.
- **`br_fipe_veiculos.precos` não tem preço** — só `vehicle_type | brand | model`. É catálogo de modelos apesar do nome.
- **`br_rf_dirpf.fundos_habilitados.tipo_fundo` é esfera (M/E/N)**, não finalidade — não separa fundo da criança de fundo do idoso.
- **`br_ibama_embargos_novo.termo_embargo.qtd_area_embargada` é 100% nula** nos 4.014 municípios com embargo; só a contagem de termos é utilizável.
- **`br_tesouro_capag.municipios` não tem coluna de ano** — retrato único, não série.
- **SIH e SINAN usam código de município de 6 dígitos** (SUS), não o IBGE de 7 — precisa do bridge por `substr(id_municipio,1,6)`.
- **43% das escolas rurais no SIMET estão "Sem Medidor Instalado"** (31,7% das urbanas): tratar essa categoria como nula, não como zero, ou o índice enviesa para cima.
- **Mapeamento SIAFI→IBGE**: as tabelas do Portal da Transparência (Novo Bolsa
  Família, Gás do Povo, Seguro-Defeso, Pé-de-Meia, Garantia-Safra) usam
  `codigo_municipio_siafi`, não `id_municipio`. O join por nome normalizado + UF
  contra `br_bd_diretorios_brasil.municipio` recupera **5.556 dos 5.571** códigos.
- **Variável extensiva não é absorvida por resíduo em rank de log-escala** —
  vale para os dois lados da armadilha. Par **extensivo × extensivo** precisa
  de log-área no controle além de log-população (foi o que derrubou o D1). E
  par **extensivo × intensivo** engana igual: `pbf_valor_acumulado` (valor
  total pago em 16 anos) correlaciona **+0,777 com população** e só +0,597 com
  pobreza atual — controlar pobreza contemporânea não o move, porque o que ele
  carrega além de pobreza é **tamanho**. Na forma per capita ele vira quase
  sinônimo de pobreza atual (+0,922). Antes de interpretar qualquer soma
  acumulada, dividir pela base.
- **Par extensivo × extensivo precisa de log-área no controle, não só
  log-população.** Foi o que derrubou o D1: área CAFIR e área desmatada são dois
  tamanhos, e os municípios de maior área da Amazônia são os de **menor**
  população — controlar população não controla área. `+0,76` vira `+0,31` só de
  acrescentar `log(area_total)`, e `+0,04` se as duas pontas virarem share da
  área municipal. Vale para qualquer par onde os dois lados sejam contagem,
  área ou valor absoluto.
- **`world_wb_mides.pagamento`: a coluna de valor é `valor_final`, não
  `valor_pago`** — e a tabela cobre **1994–2024** (392,7 milhões de pagamentos,
  R$ 13,2 tri **nominais**). Somar a série inteira mistura real de 1994 com real
  de 2024; usar recorte de anos (a bateria usa `ano >= 2018`) ou deflacionar.
  Cobre 3.339 municípios, não os 5.570.
- **`br_cgu_fef.microdados` é o desenho quase-experimental do espelho** —
  `sorteio_ciclo_fef` é sorteio, não escolha. 82.664 ordens em 1.352 municípios,
  até 3 ciclos. O corte transversal (acumulado por município) desperdiça o
  desenho: o valor está em comparar sorteado × não sorteado no **pós**.
- **`br_ibge_censo2022_raca.instrucao` e `br_cgu_garantia_safra` saem em formato
  longo** (uma linha por município × categoria). Não entram em merge
  municipal sem pivô — foi por isso que a perna racial de H13 ficou de fora do
  painel na primeira passada.
- **`br_mdr_snis`: 2022 só tem as colunas `_ibge`**; o par declarado × base-IBGE
  (que é o que torna o SNIS testável como fonte auto-declarada, ver G3) existe
  até **2021**. `populacao_urbana` e `populacao_urbana_atendida_agua` são 100%
  nulas em 2022.
- **`br_sp_saopaulo_geosampa_iptu.valor_terreno` já é R$/m²**, não valor total —
  dividir pela área infla a leitura por três ordens de grandeza. Confirmado no
  Jd. Paulista: R$ 13.665/m². `valor_construcao` idem. 3,8 milhões de lotes em
  2025, um por `numero_contribuinte`.
- **`br_ce_fortaleza_sefin_iptu.centroide` é `GEOMETRY`**, não texto: precisa de
  `CAST(... AS VARCHAR)` para exportar, e `ST_X`/`ST_Y` exigem a extensão
  spatial (indisponível em conexão `-readonly`). Preenchimento **>99,7%** nos 6
  indicadores de infraestrutura — exceção positiva.
- **`br_tcu_inidoneos.empresas` tem só 84 CNPJ**, contra 7.893 do CEIS/CNEP.
  Não serve para testar "a regra não morde" — a lista é 94× menor e o resultado
  é indistinguível de zero por tamanho de amostra, não por comportamento.
- **`br_mec_prouni` só tem a tabela `dicionario`** — nenhum dado. E
  `br_saude_farmaciapopular` só tem o cadastro de estabelecimento credenciado,
  sem volume dispensado: dá para medir a rede, não o programa.
- **`br_ms_sih` não tem `morbidade_hospitalar`** — a tabela é `aihs_reduzidas`,
  com `id_municipio_paciente`, `id_municipio_estabelecimento` e
  `id_municipio_gestor` (três municípios diferentes por AIH; escolher qual
  responde a pergunta).
- **`br_me_siconfi`: o estágio de receita é `'Receitas Brutas Realizadas'`** e a
  conta de crédito é exatamente `'Operações de Crédito'`. `ILIKE '%realizada%'`
  não casa nada, e as variantes ("Mercado Interno", "Contratuais") são
  subcontas que dupla-contam se somadas junto com a conta-mãe.
- **`approx_count_distinct` é determinístico e enviesa +23% nos códigos IBGE** —
  devolveu **6.859 idêntico para 50 datasets diferentes**, todos cobrindo os
  mesmos 5.570 municípios. Para cobertura territorial use `count(DISTINCT)`,
  mesmo custando 40 minutos (é o que gerou `docs/context/cobertura_municipal.json`).
- **`/dev/shm` no beelink tem cota**: agregação grande aborta com
  `Disk quota exceeded` no `duckdb_tmp`. Passar
  `SET temp_directory='/home/polo/tmp_duck'` (disco) resolve; `SET memory_limit`
  sozinho não.
- **`br_ibge_pam` não registra quebra de safra**: `area_colhida` é praticamente
  igual a `area_plantada` em todo município e ano (perda mediana **0,0000**,
  p90 0,0102). A área não colhida aparentemente é reportada como não plantada.
  A razão colhida/plantada **não** serve como medida de perda.
- **`br_ana_atlas_esgotos`: metade dos municípios tem índice ZERO** de esgoto
  com coleta e tratamento (mediana 0,0; média 0,19). Como variável contínua o
  piso domina — use `indice_sem_atendimento_sem_coleta_sem_tratamento`, que é
  bem distribuído, e não o índice positivo.
- **`br_ms_sinasc.id_municipio_nascimento` é o município do HOSPITAL**, não da
  mãe (existe `id_municipio_residencia` separado). Município sem maternidade
  registra só parto domiciliar, todos vaginais: a taxa de cesárea mediana cai a
  **3,5%** sem filtro e sobe a **59,7%** entre os 1.733 municípios com ≥100
  nascimentos (agregado nacional 57,0%). Filtrar por volume antes de usar.
- **`br_ms_sinasc.hora_nascimento` é 100% nula em 2022**, e 2023 é ano parcial
  (986 mil registros contra ~2,6 milhões). Para qualquer análise de horário,
  usar **2021**.
- **`br_ms_sih.aihs_reduzidas` não tem `diagnostico_principal`** — a coluna é
  `cid_principal_subcategoria`.
- **`br_simet_educacao_conectada.indicador_internet` é BOOLEAN**, não `'Sim'`.
- **`br_inep_ideb.municipio` tem `rede = 'publica'` como agregado** ao lado de
  `municipal`, `estadual` e `federal` — somar todas dupla-conta.
- **`br_ms_sih.aihs_reduzidas` não tem uma única internação com CID `A90`
  (dengue) em nenhum dos 17 anos** — 190 milhões de registros, zero. Em 2023,
  ano de 1,5 milhão de notificações de dengue no SINAN, o SIH registra 2.648
  internações em todo o grupo A9x. **Dengue não é recuperável por CID no SIH
  deste espelho**; para pareamento notificação × internação, usar o capítulo
  infeccioso inteiro (A/B) e dizer que usou.
- **`br_ms_sinan.microdados_dengue.id_municipio_residencia` é o código IBGE de
  7 dígitos**, ao contrário do SIH e do SIA, que usam o código do SUS de 6.
  Juntar os dois com a mesma chave devolve zero linhas em silêncio.
- **`br_bcb_sicor.recurso_publico_propriedade` só dá contagem de operações por
  município** — o valor está em `br_bcb_sicor.saldo`/`liberacao`, sem município.
  Cruzamentos de "crédito por hectare" a partir daí medem **densidade de
  contrato**, não volume financeiro.
