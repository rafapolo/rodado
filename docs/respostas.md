# Respostas — referência cruzada com perguntas.md

Cada entrada usa o código `T<tema>-<nº>` que identifica a pergunta exata em
[`perguntas.md`](perguntas.md). Status:
**✅ respondida** (query executada no beelink em 2026-08-23, com n e resultado),
**◐ parcial** (parte do cruzamento respondida),
**⏳ pendente** (exige análise dedicada ainda não executada).
Todas as queries usam filtros de partição e valores checados contra ordens de
grandeza esperadas; correlações são Pearson sobre agregados municipais (painel
de 5.570 municípios) ou estaduais (27 UFs), conforme indicado.

## Resultados transversais (base das respostas abaixo)

| # | Correlação | Nível | n | r |
|---|---|---|---|---|
| A1 | Emissões agropecuárias (SEEG) × desmatamento (PRODES) | município | 5.570 | **+0,85** |
| A2 | Rebanho bovino (PPM) × desmatamento | município | 5.538 | **+0,80** |
| A3 | Vínculos formais/100k hab (RAIS) × PIB per capita | UF | 27 | **+0,93** |
| A4 | Conectividade (Anatel IBC) × ENEM redação | município | 1.736 | **+0,57** |
| A5 | Empresas ativas/100k hab (CNPJ) × Anatel IBC | município | 5.570 | **+0,57** |
| A6 | Formalidade (RAIS/100k) × Anatel IBC | município | 5.570 | **+0,56** |
| A7 | IDEB anos finais × ENEM redação | município | 1.657 | **+0,45** |
| A8 | Homicídios/100k (SIM) × % votos Lula 2022 | UF | 27 | **+0,46** |
| A9 | PIB per capita × % votos Lula 2022 | UF | 27 | **−0,62** |
| A10 | Mortalidade infantil × % cesárea (SINASC/SIM) | município | 2.283 | **−0,40** |
| A11 | Peso agro no PIB × desmatamento | município | 5.570 | +0,25 |
| A12 | Cesárea × PIB per capita | município | 3.853 | +0,24 |
| A13 | Empresas/100k × rendimento médio RAIS | município | 5.570 | +0,24 |
| A14 | Lacuna racial salarial × homicídios/100k | UF | 27 | +0,12 |
| A15 | Agências bancárias/100k × PIB per capita | município | 2.466 | +0,12 |
| A16 | Templos religiosos/100k × PIB per capita | município | 5.570 | −0,11 |
| A17 | Vulnerabilidade social (IVS-IPEA 2010) × cobertura Bolsa Família per capita (2025) | município | 5.565 | **+0,82** |

Fatos medidos (não-correlações): PISA 2022 matemática Brasil 380 vs OCDE 475;
exportações 2023 com 69,8% de primários (US$ 339,7 bi); dívida ativa PGFN
R$ 7,06 tri / 7,67M devedores (SP R$ 3,04 tri); 38 dos 93 sancionados do TCU
ainda com CNPJ ativo; deputados federais eleitos 2022 com patrimônio médio de
R$ 3,12 mi (mediana R$ 1,03 mi, máximo R$ 158 mi); despesa de pessoal do
Judiciário estadual em média 90,1% da despesa total (mín 76%, máx 99%,
2021); excesso de peso adulto (SISVAN 2023) liderado por RS 73,6%,
RN 72,4%, SP 71,9%.

## 01 · Desigualdade Racial

- **T01-1 ✅** Lacuna racial salarial (RAIS 2022) × homicídios/100k (SIM): **r = +0,12 entre UFs — fraca**. DF tem a maior lacuna (51%) e baixa letalidade (7/100k); AM combina lacuna 37% com 36/100k. *(A14)*
- **T01-2 ✅** Maioria negra × salário formal controlando renda: bruta **r = −0,27** entre municípios; controlando PIB pc **+0,04 (n=4.251)** — o aparente castigo salarial de municípios maioria negra é inteiramente explicado pela renda local; dentro de cada tercil de PIB o sinal some.
- **T01-3 ◐** Composição racial por CNAE (RAIS 2022, declarados): população preta+parda 53%; **finanças 28%, informação 40%, educação/saúde ~40–46% vs construção 62%** — setores de maior qualificação têm menos pretos+pardos. Ressalva: adm. pública tem 91% sem raça declarada.
- **T01-4 ✅** Mesmo achado de T01-1: a lacuna racial não prevê homicídio entre UFs.
- **T01-5 ✅** Lacuna racial RAIS 2012→2022: média municipal subiu de **9,4% para 10,6%** (n=5.459); 2.237 reduziram. Quem reduziu não cresceu mais em PIB pc (**r = +0,02**) nem difere em alfabetização/envelhecimento — redução de lacuna foi fenômeno próprio, não fruto de riqueza.

## 02 · Educação

> Refeito do zero em 2026-09-02: as 5 respostas anteriores deste tema tinham
> correspondência numeração↔conteúdo incerta (`bun harness/casos.ts` marcava
> T02-1…T02-4 como suspeitos — vocabulário sobreposto entre as 5 perguntas
> impedia reatribuir com segurança). Em vez de reordenar os gabaritos antigos,
> cada pergunta abaixo foi respondida com uma query nova e dedicada, garantindo
> 1:1 com `perguntas.md`.

- **T02-1 ✅** Em 3.591 municípios com IDEB (anos finais, rede pública), INSE e ENEM em 2021: correlação bruta IDEB × ENEM = **+0,36**; dividida em terços de INSE cai para **+0,09 (terço mais pobre) / +0,15 / +0,16 (mais rico)** — a relação sobrevive ao controle por nível socioeconômico, mas fica bem mais fraca: boa parte da correlação bruta é explicada pelo INSE.
- **T02-2 ✅** Dentro do terço mais pobre de PIB per capita (2021), escolas rurais têm IDEB **0,42 ponto** abaixo das urbanas (4,25 vs 4,67, n=6.369 escolas) e nota ENEM **9,4 pontos** abaixo (n=75.248 candidatos); no terço mais rico o gap cai para **0,28 ponto** de IDEB e **4,8 pontos** de ENEM (n=8.853 escolas / 184.311 candidatos) — pior fluxo e desempenho rural confirmados, com gap maior justamente nos municípios pobres.
- **T02-3 ✅** Entre 5.536 municípios com IDEB, ENEM e PIB per capita 2021, **392 (7,1%)** combinam IDEB abaixo da mediana, participação ENEM acima da mediana e PIB per capita acima da mediana — acesso sem aprendizado mesmo com renda. Exemplos: Canaã dos Carajás-PA (PIB per capita R$ 894.806, IDEB 4,6), Conceição do Mato Dentro-MG, Tasso Fragoso-MA, Porto dos Gaúchos-MT, Nova Lima-MG — municípios de economia mineradora/agro com renda concentrada, não distribuída.
- **T02-4 ✅** Em 24 UFs com ao menos 15 municípios (n=3.574), a correlação média INSE × ENEM (**+0,382**) é levemente maior que INSE × IDEB (**+0,360**), e o ENEM vence em 13 das 24 UFs contra 11 do IDEB — o nível socioeconômico explica um pouco mais a variação do ENEM que a do IDEB, mas a margem é pequena e não sistemática.
- **T02-5 ◐** Entre 4.744 municípios, só **469 (9,9%)** ganharam população jovem (0-19 anos) de 2010 a 2022 (+13,6% em média, contra a tendência nacional de queda); desses, **88,3%** também ampliaram matrícula (+18,5%, Sinopse INEP) e o IDEB subiu em média **0,93 ponto** entre 2009 e 2021 — próximo, mas levemente abaixo, do ganho médio de **1,05 ponto** nos municípios que perderam população jovem. Δpopulação × Δmatrícula r=**+0,71** (forte); Δpopulação × ΔIDEB r=**−0,08** (nula) — quem ganhou população jovem ampliou matrícula quase sempre, mas isso não se traduziu em ganho extra de IDEB. `◐` porque descreve um subconjunto pequeno (9,9%) do país, não o padrão geral.

## 03 · Saúde

- **T03-1 ✅** Benefícios (Bolsa Família jun/2023) × cesárea (SINASC 2022): **r = −0,60 (n=1.910 municípios)**; controlando oferta obstétrica local, **−0,57** — mais beneficiários, menos cesárea, e a oferta não explica a relação.
- **T03-2 ✅** TMI (SIM 2020–22 / SINASC) × CNES: **r = −0,26 com leitos/1.000 hab; +0,17 com equipes ESF/10 mil hab** (n=1.946; TMI ponderada 9,7/1000). ESF se concentra justamente onde a mortalidade é alta — direcionamento da política, não iatrogenia.
- **T03-3 ◐** Mortalidade infantil × PIB pc: **r = −0,13 (n=2.283)** — fraca; pobreza municipal não é o único determinante.
- **T03-4 ✅** Mortalidade materna (SIM 2019–21, causa O) × oferta obstétrica: RMM média **91,9/100 mil NV** (21 UFs); **r = +0,31** com salas de parto/100 mil hab (alocação reativa: mais oferta onde morre mais) e **r = −0,50** com PIB pc.
- **T03-5 ✅** Benefícios chegam à vulnerabilidade: tx de beneficiários × pré-natal inadequado **+0,39**, × mãe sem ensino médio **+0,57** (n=1.910) — o perfil SINASC confirma focalização.

## 04 · Mercado de Trabalho

- **T04-1 ◐** Rotatividade (CAGED) × homicídios: **r = +0,07 — desprezível** municipalmente.
- **T04-2 ✅** Queda 2020 → recuperação 2022 (n=5.554 municípios): **r = +0,10 entre queda relativa e recuperação; +0,02 com PIB pc** — nem o tamanho da queda nem a renda local explicam quem recuperou emprego formal.
- **T04-3 ◐** CBOs de admissão barata × rendimento RAIS (2021, n=217 grupos ≥5 mil admissões): **r = +0,33** entre salário médio de admissão (CAGED) e rendimento RAIS — admissões precárias se concentram nas ocupações de baixo rendimento, mas com folga considerável. *CAGED do espelho está sem admissões 2022+ (gap de sync: 124 mil adm vs 20 mi deslig em 2022) — refazer quando sincado.*
- **T04-4 ✅** Especialização produtiva (HHI CNAE, n=3.029 municípios): HHI médio 0,221; controlando população, **× PIB pc −0,24 e × alfabetização −0,61** — municípios dependentes de um único setor são sistematicamente mais pobres e menos escolarizados.
- **T04-5 ✅ (UF)** Formalização × renda: **vínculos/100k × PIB pc = +0,93 entre UFs (n=27)** — o emprego formal acompanha quase perfeitamente a riqueza regional. *(A3)*

## 05 · Política

- **T05-1 ✅** Patrimônio × autoria (legislatura 2023+, match por nome_urna 81%, n=404): **r = −0,18** entre log do patrimônio e nº de proposições — deputados mais ricos não autorizam mais; mediana de 451 proposições.
- **T05-2 ⏳** Senado: o espelho não tem tabela de proposições do Senado (só `senadores` + CEAPS) — pipeline necessário.
- **T05-3 ✅** Ocupação declarada × eleição 2022 (dep. federal/senador): deputados na reeleição **58,8%**, engenheiros 7,8%, médicos 6,5% vs **empresários 3,9%** (n=1.229 candidatos) — abaixo da média (~5%), empresário não é profissão que elege.
- **T05-4 ◐** Fragmentação partidária municipal 2022: nº efetivo de partidos médio **5,6** (n=3.035); × PIB pc **+0,21**; AP mais fragmentado, PI menos. Comparação com votações nominais da Câmara pendente.
- **T05-5 ✅** Gasto por voto × transferências voluntárias (UF, n=27): **r = +0,92** — mas é estrutural: UFs pequenas (RR R$144/voto, 749 transf pc) têm campanha cara por eleitor E recebem mais transferência per capita; ambas as séries escalam com o tamanho do eleitorado.

## 06 · Crime

- **T06-1 ⏳** Pendente — INFOPEN/SISDEPEN no espelho está corrompido (colunas com unicode inválido, 1.514 linhas) — precisa re-scrapagem.
- **T06-2 ✅** ISP-RJ × SIM (homicídios dolosos × agressões, 2019–23, n=92 municípios ≥30 mil hab): **r = +0,81 em log-taxa** — as duas fontes contam a mesma violência; divergências ficam nos municípios pequenos.
- **T06-3 ✅** Especialização CNAE (HHI) × homicídio: bruto **+0,16**; controlando PIB pc **−0,04 (n=1.604)** — dependência de um único setor não prevê homicídio.
- **T06-4 ⏳** Pendente — mortes por intervenção policial (SIM) exigem SISDEPEN, que está corrompido no espelho (ver T06-1).
- **T06-5 ◐** Fronteiras/portos/capitais dos 12 municípios de fronteira internacional + portos principais: taxa de homicídio **82,7/100k vs 61,9** nos demais (n=3.293) — concentração ~34% acima da média; correlação com % transporte (RAIS) saiu indeterminada (NaN).

## 07 · Economia e Crédito

- **T07-2 ✅** Agências/100k × PIB pc: **r = +0,12 (n=2.466, ≥20 mil hab) — presença bancária quase não discrimina renda municipal**. *(A15)*
- **T07-1 ✅** Captação de crédito rural (SICOR 2022, via `recurso_publico_complemento_operacao`) × PIB agropecuário e rebanho (município): **r = +0,74 com VA agropecuário; +0,30 com rebanho (PPM)** (n=5.503) — crédito rural segue a renda agro do município mais de perto do que o tamanho do rebanho.
- **T07-3, T07-5 ⏳** Pendentes — mesmo bloqueio de T17-2 (T07-3: exige ligar tomador SICOR ao imóvel SICAR via CPF/CNPJ/id_car, join dedicado) e concentração de crédito × uso do solo MapBiomas × estrutura fundiária (T07-5) é multi-dimensional demais para uma query só.
- **T07-4 ✅ (2026-08-27)** Municípios que tinham ≥1 agência ESTBAN em dez/2014 (n=3.646): comparando os que **perderam** agências até dez/2022 (n=1.970) vs os que mantiveram/ganharam (n=1.676) — crescimento nominal do PIB municipal 2014→2021 quase igual entre os grupos (77,1% vs 83,2%). Correlação bruta entre "perdeu agência" (binário) e crescimento do PIB: **r = −0,035**; controlando por ln(população) via correlação parcial: **r ≈ −0,024 (n=3.646)** — praticamente nulo. Perder agência bancária não prediz crescimento de PIB municipal inferior, mesma UF/porte controlado.

## 08 · Políticas Públicas

- **T08-1 ✅** Benefícios (BF jun/23) × gasto assistencial (SICONFI 2022 pago): **r = −0,08 (n=3.053)** — quem tem mais beneficiários não gasta mais em assistência social per capita (média R$ 159/hab); gasto saúde até negativo com benefícios (−0,22).
- **T08-2 ◐** Cobertura × pobreza: benefícios seguem vulnerabilidade medida por escolaridade materna (+0,57, T03-5), mas o Censo 2022 do espelho não tem renda/domicílio para medir pobreza diretamente.
- **T08-3 ✅** Arrecadação própria × dependência de benefícios: **r = −0,44 bruto (n=3.055); controlando PIB pc −0,07** — municípios que arrecadam menos dependem mais de BF, mas o efeito é todo capturado pela renda.
- **T08-4 ✅** Gasto em saúde × mortalidade infantil: **r = −0,12 (n=1.411)** — gasto municipal per capita quase não discrimina TMI; resultado depende de fatores fora do orçamento local.
- **T08-5 ⏳** Pendente — SIOP no espelho tem cabeçalhos corrompidos (BOM) na tabela `dados`; exige re-scrapagem antes do cruzamento.

## 09 · Gênero

- **T09-2 ✅ (parcial)** Cesárea × renda municipal: **+0,24**; × rendimento médio +0,19 (n=3.853) — parto cirúrgico cresce com renda local. *(A12)*
- **T09-1 ✅** Feminização do emprego formal (RAIS 2022) × notificações de violência (SINAN violência 2019+2021): **r = −0,06 (n=1.668 municípios)** — nenhuma relação; notificações medem estrutura de atendimento, não violência bruta.
- **T09-3 ◐** Mulheres nas admissões (CAGED 2021): **35,7% do total vs 37,0% nos 4 setores de maior salário** — entrada feminina nos setores ricos já é proporcional; o gargalo não está na porta de entrada.
- **T09-4 ◐** Coberto por T03-4: RMM média 91,9/100 mil NV (21 UFs), r = +0,31 com salas de parto (alocação reativa), −0,50 com PIB pc.
- **T09-5 ⏳** Pendente — o Censo 2022 no espelho não tem tabela de responsabilidade/chefia de domicílio.
- **T09-extra ✅** Mulheres nos vínculos formais medidas (pct_mulher no painel); correlação com rendimento: **−0,19 municipalmente** — onde mais mulheres trabalham formalmente, salário médio menor.

## 10 · Meio Ambiente

- **T10-1 ✅** Desmatamento × emissões agropecuárias: **r = +0,85 (n=5.570)**; × peso do agro no PIB: +0,25. Quem desmata emite junto; o PIB formal agro nem tanto. *(A1, A11)*
- **T10-2 ✅** SICAR × PRODES (n=1.871 municípios ≥50 imóveis): **% de imóveis pendentes × desmatamento r = +0,21**; área total cadastrada × desmatamento **+0,61**; pendência × rebanho +0,17.
- **T10-3 ✅** Rebanho × desmate: **r = +0,80** — pecuária é o vetor. *(A2)*
- **T10-4 ✅** CAR validado vs pendente (n=1.871): % validado × desmate **−0,36 bruto, −0,25 controlando rebanho**; % pendente × desmate +0,17 no mesmo controle — regularização anda com menos desmate mesmo com produção igual.
- **T10-5 ✅** ΔVA agro 2016→2021 × Δemissões agro: **+0,39 (n=1.872 Amazônia+Cerrado)**; mudança no desmate × Δemissões +0,20 — renda e emissões andam juntas, mas não um para um.

## 11 · Infraestrutura

- **T11-1 ✅** Conectividade (IBC) × cobertura de água/esgoto (SNIS 2021): **r = +0,14 água e +0,11 esgoto (n=5.302)** — defasagem digital e déficit sanitário andam juntos, mas fracamente; saneamento segue sua própria lógica.
- **T11-2 ✅** Gasto municipal em saneamento (SICONFI 2021 pago) × cobertura de esgoto: **r = +0,24 (n=1.737)** — investimento converte-se em cobertura apenas parcialmente.
- **T11-3 ✅ (proxy)** Conectividade × educação: **IBC × ENEM = +0,57** — infraestrutura digital acompanha desempenho escolar melhor que a própria renda. *(A4)*
- **T11-4 ✅** Água universalizada sem esgoto × ambos universalizados: PIB pc médio **R$ 35,4 mil vs R$ 45,2 mil** (n=665+354; "outros" R$ 30,4 mil) — o esgoto é a linha que separa municípios ricos dos medianos.
- **T11-5 ✅ (proxy capital/não-capital)** IBC × formalidade RAIS/100k hab, sem recorte urbano/rural fino (o espelho não tem essa variável), mas separado por capital de UF: **r = +0,55 nos não-capitais (n=5.543); r = +0,76 nas 27 capitais** — a relação já medida no agregado (A6, +0,56) é ligeiramente mais forte nas capitais, não mais fraca.

## 12 · Interseccionalidade

- **T12-1 ✅** Mulher negra × homem branco no mesmo setor (RAIS 2022, 21 setores): **mediana de 40,3% de lacuna salarial** — a dupla desvantagem é generalizada e grande.
- **T12-3 ✅** Dupla desvantagem × rotatividade setorial (CAGED 2021): **r = +0,04 com lacuna mulher-negra** — setores de alta rotatividade não concentram a desvantagem combinada.
- **T12-5 ✅** Mesmo cruzamento (CAGED 2021 × RAIS), decompondo por eixo: **r = +0,19 com lacuna de gênero; −0,33 com lacuna racial** — rotatividade setorial não explica a interseção; para o recorte racial o sinal até inverte.
- **T12-2 ✅** % mães pretas/pardas (SINASC 2022, por município de residência, n≥30 nascimentos) × leitos obstétricos SUS por 1.000 nascidos (CNES 2022) × PIB pc: **r = +0,02 com leitos (praticamente nulo, n=3.052); r = −0,26 com PIB pc** — a composição racial das mães não se associa à oferta de leito obstétrico, mas municípios com mais mães pretas/pardas são sistematicamente mais pobres.
- **T12-4 ⏳** Pendente — chefia feminina não existe no Censo 2022 do espelho (ver T09-5).

## 13 · Migração

- **T13-2 ✅** Saldo de movimentação CAGED 2022 (proxy de atração de trabalhadores) × PIB pc 2021, e % de admissões em construção civil (CNAE seção F) × PIB pc, mesmo recorte (n=5.042 municípios com ≥30 admissões): **r = +0,05 com saldo; r = −0,03 com % construção** — nem atração líquida de vínculos nem boom da construção acompanham a renda municipal.
- **T13-1, T13-3, T13-4, T13-5 ⏳** Pendentes — bloqueio de dado, não de query: `br_me_caged.microdados_movimentacao` registra só o município do estabelecimento (uma ponta), não um par origem→destino do trabalhador; sem isso não dá pra medir fluxo entre municípios (T13-1, T13-3, T13-5) nem separar "exportador" de "receptor" de trabalhadores (T13-4) do jeito que a pergunta original pede.

## 14 · Consumo

- **T14-1 ✅** Dispersão de preço da gasolina por município (ANP 2023, CV = desvio/média) × número de postos concorrentes × PIB pc: **r = +0,29 com concorrência (n=461, municípios com ≥5 coletas); r = +0,07 com PIB pc** — mais postos concorrentes correlaciona com MAIS dispersão de preço, não menos (provável efeito de tamanho de cidade: mais postos = mais bairros/perfis de preço, não mercado mais competitivo/uniforme); renda não discrimina.
- **T14-2 ✅ (UF, n pequeno)** IPCA alimentação 12 meses (por região metropolitana, 2023) × preço médio da gasolina (ANP) × renda média (POF 2017), por UF: **r = +0,18 com ANP; r = −0,11 com renda POF** (n=10 UFs com RM no IPCA) — correlações fracas e n pequeno, porque o IPCA regional só cobre as principais regiões metropolitanas, não as 27 UFs.
- **T14-3, T14-4, T14-5 ⏳** Pendentes — T14-3 exige casar categorias de despesa da POF com categorias do IPCA (classificação, não só join); T14-4 exige proximidade/distância a distribuidoras (sem coordenadas prontas no recorte usado); T14-5 pede "frota implícita", que não é uma coluna existente — precisaria de uma metodologia própria para estimar.

## 15 · Poder e Elites

- **T15-1 ◐** Patrimônio dos eleitos medido (R$ 3,12 mi médio); autoria Câmara pendente.
- **T15-3 ✅** Recorrência de sobrenome entre vereadores eleitos (TSE 2016+2020, mesmo município) × PIB pc: **r = −0,18 (n=5.568 municípios com ≥5 eleitos nas duas eleições)** — sobrenome repetido entre eleitos é levemente MAIS comum em municípios mais pobres, não mais ricos; em média **56,4% dos vereadores eleitos** dividem sobrenome com outro eleito do mesmo município nas duas eleições.
- **T15-5 ✅** Razão patrimônio médio do deputado federal eleito (TSE 2022, por UF) / PIB pc da UF (proxy de renda do eleitorado — Censo 2022 não tem renda) × emendas parlamentares pagas por UF (CGU, 2023+): **r = +0,02 (n=27 UFs)** — a razão patrimônio/renda do eleito não prevê quanto a UF recebe em emendas.
- **T15-2, T15-4 ⏳** Pendentes — exigem ligar candidato (CPF, TSE) a sócio de empresa (CNPJ) e depois a contrato/pagamento (CGU), um encadeamento de 3 entidades por CPF/CNPJ que não é uma correlação de corte só; fica para uma passada de resolução de entidade dedicada.

## 16 · Economia Política

- **T16-1 ✅** % da arrecadação federal nacional (soma de tributos, RF 2021) × % do PIB nacional, por UF: **SP arrecada 38,1% do total contra 30,2% do PIB (gap +7,9pp); RJ +7,0pp; DF +4,1pp** — só essas 3 UFs arrecadam acima do seu peso no PIB; as outras 24 arrecadam abaixo, MG é o maior gap negativo (−2,8pp) — consistente com sede fiscal de empresas concentrada em SP/RJ/DF independente de onde a atividade ocorre.
- **T16-3 ✅** % de II+IE (imposto de importação+exportação) na arrecadação total (RF 2021, UF) × % do PIB em valor agropecuário: **r = −0,32 (n=27 UFs)** — UFs mais dependentes de II/IE têm proporcionalmente MENOS peso agro no PIB, não mais; II/IE segue porto/indústria, não produção primária.
- **T16-4 ✅ (dado escasso, ressalva forte)** Arrecadação total (RF 2020, UF) × transferências voluntárias empenhadas (Transferegov, UF recebedora): **r = +0,88 (n=27 UFs)** — mas `br_transferegov.transferencias` só tem 2019-2020 no espelho (4.248 linhas no total do Brasil), claramente incompleto frente ao volume real de transferências voluntárias; tratar como indício de que ambas escalam com o tamanho da UF, não como medida confiável de direcionamento político.
- **T16-2, T16-5 ⏳** Pendentes — bloqueio de dado: `br_rf_arrecadacao` não tem arrecadação em nível de município (só UF, CNAE nacional, natureza jurídica nacional, e ITR que é só imposto rural); sem arrecadação municipal não dá pra medir volatilidade (T16-2) nem arrecadação per capita por município (T16-5).

## 17 · Agropecuária

- **T17-1 ✅ (parcial)** Rebanho × crédito SICOR 2022: **r = +0,57 (n=5.423; R$ 127,5 bi creditados)** — pecuária puxa crédito; % de área em imóveis gigantes × crédito por bovino **−0,16**. *(A2)*
- **T17-2 ⏳** Pendente — exige join SICAR imóvel→tomador via id_car/cpf (`recurso_publico_propriedade`), pipeline dedicado.
- **T17-3 ⏳** Pendente — TRASE não tem chave municipal direta com PRODES/PPM no espelho.
- **T17-4 ✅** CAR pendente × crédito: bruto +0,00; controlando rebanho **−0,12 (n=5.417)** — pendência custa pouco crédito formal, mas custa.
- **T17-5 ◐** Coberto por T17-1/T10-5: crédito segue rebanho (+0,57) e emissões seguem renda agro (+0,39); produtividade por hectare fica para o cruzamento fino com SICAR.

## 18 · Comércio Exterior

- **T18-2 ✅ (fato)** Exportações 2023: **69,8% primários (NCM caps. 01–27), US$ 339,7 bi totais** — confirma concentração em commodities.
- **T18-1 ✅** Exportação de manufaturados (COMEX 2023, NCM capítulos 28+, mesma regra de corte usada em T18-2) × vínculos formais na indústria (RAIS 2022, CNAE divisões 10-33): **r = +0,55 (n=1.857 municípios exportadores)** — municípios que exportam mais manufaturados de fato empregam mais na indústria formal, não é só composição de pauta.
- **T18-5 ✅** Valor exportado per capita (COMEX 2023 ÷ população) × PIB per capita (2021): **r = +0,61 (n=2.458 municípios exportadores)** — quanto mais exportação por habitante, maior a renda per capita local; explica uma fração real, não total, da diferença de PIB pc dentro do país.
- **T18-3, T18-4 ⏳** Pendentes — T18-3 exige comparação temporal (RAIS antes/depois de começar a importar), T18-4 exige índice de concentração (Herfindahl por NCM) cruzado com estrutura fundiária SICAR — ambos precisam de mais que uma query de correlação simples.

## 19 · Mercado Financeiro

- **T19-4 ✅ (proxy)** Bancos × crédito: agências × PIB pc fraco (+0,12, A15); SICOR pendente.
- **T19-1 ✅** IBC (Anatel) × agências bancárias/100k hab (ESTBAN 2022) × bolsistas CNPq/100k hab (2022, junção por nome do município de destino): **r = +0,19 com agências; r = +0,13 com bolsistas** (n=342, municípios com bolsista CNPq) — conectividade acompanha um pouco mais a presença bancária do que a presença de bolsistas.
- **T19-3 ✅** Bolsistas CNPq/100k hab × agências ESTBAN/100k hab × PIB pc, mesmo recorte de 342 municípios: **r = +0,04 com densidade bancária; r = −0,05 com PIB pc** — praticamente nenhuma relação; onde há bolsista não é nem mais bancarizado nem mais rico, dentro do universo de municípios que já têm algum bolsista.
- **T19-2, T19-5 ⏳** Pendentes — não executadas nesta rodada por orçamento de tempo (T19-2 cruza crescimento de crédito SICOR com queda de agências ESTBAN, T19-5 pede correlação defasada agências→PIB, ambas exigem duas leituras temporais por município em vez de uma correlação simples).

## 20 · Ciência

- **T20-1 ◐** Bolsistas CNPq por UF de origem (2022) × nota média de redação ENEM da UF (n=27 UFs): **r = +0,57**. Proxy em nível de UF — a tabela de bolsas só tem UF de origem, não município, então não é a correlação municipal que a pergunta pede.
- **T20-2 ◐** Bolsistas CNPq por UF × população da UF (Censo, n=27 UFs): **r = +0,80** — bolsas seguem fortemente o tamanho populacional, reforçando a concentração regional em vez de distribuir proporcionalmente. Mesma ressalva de T20-1: proxy em nível de UF, não a distribuição por região das IES em recorte fino.
- **T20-4 ✅** Bolsistas CNPq por UF × PIB pc da UF (n=27 UFs): **r = +0,69** — bolsas seguem a renda da UF mais do que corrigem a desigualdade regional (reforço, não correção).
- **T20-3, T20-5 ⏳** Pendentes — exigem comparação antes/depois (T20-3: escolas de alta nota alimentando bolsistas anos depois) ou comparação de vizinhança (T20-5: municípios com/sem campus, mesma renda) — nenhuma das duas é uma correlação de um corte só.

## 21 · Corrupção

- **T21-4 ✅** Emendas parlamentares pagas por município (CGU, 2022+) × despesa orçamentária paga total (SICONFI 2023): **r = +0,31 (n=1.423 municípios com emenda>0)**; emendas representam em média só **0,37% da despesa municipal paga** — correlação moderada, sem sinal forte de retenção estadual visível nesse corte, mas o teste é indireto (não segue a emenda específica até a execução, só compara totais agregados).
- **T21-1, T21-2, T21-3, T21-5 ⏳** Pendentes — exigem identificar fornecedor por CNPJ recorrente entre `cgu_cartao_pagamento`/`cgu_licitacao_contrato` (100 mi+ linhas ao todo) e comparar perfil por entidade, não uma correlação agregada de um corte só; fica para uma passada de resolução de entidade dedicada.

## 22 · Clima

- **T22-1 ✅** Focos de calor 2019–22 × desmatamento: **r = +0,66 (n=5.240 municípios)**; × emissões agro +0,51; × VA agro per capita só +0,10 — o fogo segue o desmate e as emissões, não a renda formal do agro.
- **T22-4 ✅** Óbitos por causa respiratória (SIM 2022, CID J*) per capita × focos de queimada (INPE 2022) per capita, por município: **r = −0,14 (n=5.471)** — fraco e no sentido oposto ao esperado; provável confundimento (municípios de fronteira agrícola com mais queimada tendem a ter população mais jovem/rural, não necessariamente mais mortalidade respiratória registrada) — não confirma a hipótese, mas o teste é agregado anual, não capta o pico mensal que a pergunta original pede.
- **T22-2, T22-3 ⏳** Adiados — geoespacial: T22-2 pede comparar estação INMET mais próxima de cada município com seus vizinhos (requer distância geográfica); T22-3 pede sobreposição irregular entre polígonos de imóveis do SICAR (a `condicao` do imóvel não tem flag de sobreposição, só status de análise — precisaria calcular a partir de `geometria`). Nenhum dos dois é join+agregação simples.
- **T22-5 ◐** Coberto por T22-1: fogo associado à conversão produtiva (emissões agro +0,51) muito mais que à renda (+0,10) — padrão de uso da terra, não evento natural.

## 23 · Epidemiologia

- **T23-2 ✅ (só dengue, não "doenças infecciosas" em geral)** Letalidade de dengue (SINAN 2022, óbitos/casos por município de residência, `evolucao_caso='2'`) × estabelecimentos CNES per capita (dez/2022): **r = −0,01 (n=2.569 municípios com ≥30 casos)** — praticamente nulo; letalidade de dengue não acompanha densidade de estabelecimentos de saúde. `br_ms_sinan` só tem dengue e influenza/SRAG, não cobre "doenças infecciosas" de modo geral.
- **T23-1, T23-3, T23-4, T23-5 ⏳** Pendentes — T23-1 exige SIH (bilhões de linhas, fora do orçamento desta passada); T23-3/T23-5 esbarram na mesma limitação de outras entradas (Censo 2022 não tem renda, exigiria PIB pc como proxy — não tentado nesta rodada); T23-4 exige comparação antes/depois (cobertura vacinal SIPNI seguida de óbito), não uma correlação de corte só.

## 24 · Assistência SUS

- **T24-1 ✅** % de AIHs "exportadas" (SIH 2022, `id_municipio_paciente != id_municipio_estabelecimento`) × leitos SUS/hab (CNES dez/2022) × PIB pc: **r = −0,50 com leitos (n=5.570 — quase todo o país); r = −0,07 com PIB pc** — falta de leito local prediz exportação de paciente muito mais que a renda municipal.
- **Achado técnico (vale para qualquer query futura com SIH)**: `br_ms_sih.aihs_reduzidas` usa o código de município do SUS de 6 dígitos (`id_municipio_paciente`/`id_municipio_estabelecimento`, sem dígito verificador), não o `id_municipio` de 7 dígitos do IBGE usado no resto do espelho — juntar direto (como em qualquer outra tabela) dá 0 linhas silenciosamente, sem erro. Precisa passar por `br_bd_diretorios_brasil.municipio.id_municipio_6` primeiro. Ano de 2022 sozinho já tem 12,5M linhas (não bilhões) — uma partição por ano é perfeitamente consultável.
- **T24-4 ✅ (2026-08-27)** Valor pago por AIH de parto normal (SIH 2022, procedimento SIGTAP `310010039`, o mais frequente do ano com 791 mil AIHs) × porte hospitalar (soma de leitos totais no CNES dez/2022), por região: **o valor sobe com o porte em TODAS as 5 regiões** — Nordeste R$493→R$573 (+16%), Norte R$512→R$624 (+22%, a maior diferença), Sudeste R$532→R$581 (+9%), Sul R$549→R$595 (+8%), Centro-Oeste R$553→R$584 (+6%), comparando hospitais pequenos (<50 leitos) a grandes (150+ leitos), mesmo procedimento. n=790.609 AIHs casadas a porte+região (99,9% das 791.058 do procedimento). Achado consistente: hospital maior recebe mais pelo mesmo parto, em todo o país.
- **T24-2, T24-3, T24-5 ⏳** Pendentes — T24-2 exige tabela IEPS de acesso (não confirmada no espelho); T24-3/T24-5 exigem classificar CID em "causa evitável", que não é um filtro direto de coluna.
- **T24-nota ✅** Mortalidade infantil × cesárea: **−0,40 (n=2.283)** — municípios com mais cesáreas têm menor TMI, mas é provável seleção (cesárea marca acesso, não causa). *(A10)*

## 25 · Orçamento

- **T25-4 ✅** Emendas parlamentares per capita (2023+) × % votos Lula 2022: **r = −0,006 (n=1.406 municípios) — dinheiro de emenda não segue alinhamento eleitoral municipal**.
- **T25-1 ✅** Emendas CGU × transferências Transferegov por município: **r = +0,10 (n=1.096)** — são circuitos distintos; quem recebe emenda não é quem capta planos de ação.
- **T25-2 ⏳** Pendente — SICOR não tem chave municipal direta com SIOP (só via `recurso_publico_complemento_operacao`); cruzamento de orçamento exige pipeline.
- **T25-3 ◐** Execução por tipo (CGU 2023+): individual finalidade definida **74,4%** pago/empenhado; transferências especiais **99,7%**; bancada **52,5%**; comissão **43,2%** — individuais executam melhor que coletivas. Velocidade/bloqueio no SIOP/Transferegov pendente.
- **T25-5 ⏳** Pendente — série temporal RF × emendas × juros no SIOP exige tabela `dados` do SIOP re-scrapeada (cabeçalhos corrompidos).

## 26 · Servidores

- **T26-1, T26-3, T26-5 ⏳** Bloqueio de dado: `br_cgu_servidores_executivo_federal.cadastro_servidores` só tem `sigla_uf` (lotação), não `id_municipio` — não dá pra medir onde os servidores residem/se concentram no recorte municipal que as perguntas pedem.
- **T26-4 ⏳** Bloqueio de dado: a tabela não tem idade nem data de nascimento do servidor, só datas de ingresso no cargo/órgão — não dá pra projetar aposentadoria por idade.
- **T26-2 ⏳** Pendente — `remuneracao` (1,27M linhas/mês, tratável) tem valor por servidor, mas o cargo público (`descricao_cargo`, texto livre) não tem uma chave de conversão direta para CBO (usado na RAIS); comparar as duas exigiria um crosswalk cargo→CBO que não existe pronto no espelho.

## 27 · Opinião

- **T27-eleitoral ✅ (UF)** Geografia do voto 2022: **PIB pc × Lula = −0,62; rendimento médio × Lula = −0,33; homicídios/100k × Lula = +0,46** — Lula venceu nos estados mais pobres e mais violentos; Bolsonaro nos ricos. *(A8, A9)*
- **T27-1…T27-5 ◐** Pesquisas Poder360/PNS/PNADC pendentes; base eleitoral calculada.

## 28 · Violência Escolar

- **T28-5 ✅** Autolesão notificada entre 10-19 anos (`br_ms_sinan_violencia`, 2022, `LES_AUTOP='1'`) per capita × nota média SAEB 9º ano (2021, rede total, localização total): **r = +0,03 (n=1.163 municípios com ≥3 notificações)** — praticamente nulo; nota SAEB não prevê taxa de autolesão notificada.
- **2 achados técnicos (valem para queries futuras)**: (1) `br_ms_sinan_violencia.microdados_violencia` usa o código de município do SUS de 6 dígitos (`ID_MN_RESI`), igual ao problema achado em `br_ms_sih` — precisa do bridge `br_bd_diretorios_brasil.municipio.id_municipio_6`; `br_ms_sinan.microdados_dengue` (tabela normalizada, minúsculas) já usa o `id_municipio` de 7 dígitos direto, não tem esse problema. (2) `br_inep_saeb.municipio` tem várias linhas por município/ano (rede × localização × disciplina × série) — juntar sem filtrar essas dimensões infla o join silenciosamente (achei um caso com 90 mil "municípios" em vez de ~1.200); filtrar rede/localização/série antes de agregar.
- **T28-1, T28-2, T28-3, T28-4 ⏳** Pendentes — não executadas nesta rodada por orçamento de tempo; T28-2/T28-3/T28-4 citam ISP-RJ, que só cobre o Rio de Janeiro (regional, não nacional), então qualquer resposta seria só sobre um estado, não o Brasil que a pergunta parece pedir.

## 29 · Dados Eleitorais

- **T29-2 ◐** Patrimônio eleitos medido (R$ 3,12 mi médio / R$ 158 mi máximo); série histórica pendente.
- **T29-1 ✅ (2026-08-27)** Deputados federais reeleitos (mesmo `titulo_eleitoral_candidato` eleito em 2018 E 2022, n=282 de 513 — taxa de reeleição 55%): o mapa municipal de votos se repete fortemente — correlação intra-candidato entre o vetor de votos por município em 2018 e em 2022, **r médio = 0,87 (mediano 0,92, n=275 com ≥20 municípios votados)**. O perfil de renda da base eleitoral (PIB per capita médio ponderado por voto) também é estável entre as duas eleições: **r = 0,93 (n=282)** — quem elegeu um deputado por um perfil de renda em 2018 continua elegendo pelo mesmo perfil em 2022. **Achado de bug de query**: filtrar `resultado ILIKE '%eleito%'` captura also "não eleito" (substring "eleito" dentro de "não eleito"), inflando reeleitos de 282 para 472 — usar `resultado IN ('eleito por media','eleito por qp')`.
- **T29-3 ✅ (2026-08-27)** Margem de vitória no 1º turno da eleição presidencial 2022 (diferença de % de votos válidos entre 1º e 2º colocado, por município, margem média 31,7%) × emendas parlamentares pagas per capita (2023+, mesma fonte de T15-5/T25-4/T40-3): **r = +0,018 (n=5.570, quase todo o país)** — praticamente nulo. Município com eleição presidencial mais disputada não recebe nem mais nem menos emenda depois.
- **T29-5 ✅ (2026-08-27)** Queda de comparecimento presidencial 1º turno 2018→2022 (nacional: 79,2%→78,7%, −0,47pp, n=5.570) × % população jovem 15-29 (Censo 2022): **r = +0,05**; × PIB per capita 2021: **r = +0,01** — ambos praticamente nulos, não confirma a hipótese. Capitais tiveram queda maior (−1,21pp) que municípios do interior (−0,46pp) — o oposto do que a pergunta original sugeria (interior/pobre/jovem caindo mais).
- **T29-4 ⏳** Pendente — "fragmentação partidária... medida nas votações da Câmara" não tem operacionalização direta no espelho: `br_camara_dados_abertos.votacao_parlamentar` registra votos individuais sim/não por proposição, não um índice de fragmentação de bancada comparável ao número efetivo de partidos (NEP) municipal do TSE já calculado em T05-4; construir esse índice a partir de votação nominal exigiria metodologia própria (ex.: dispersão de posição por partido por proposição), não uma correlação de corte só.
- **T29-extra ✅** Correlações geográficas do voto em A8/A9 acima.

## 30 · Estrutura Produtiva

- **T30-1 ✅ (2026-09-02, completo)** Empresas/100k × rendimento médio: **+0,24 (n=5.570)** — mercados com mais empresas pagam melhor. *(A13)* Concentração de capital social: HHI por divisão CNAE (2 dígitos, prefixo de `cnae_fiscal_principal`) do capital social entre matrizes ativas (`br_me_cnpj.estabelecimentos` + `.empresas`, snapshot 2025-09, 86 divisões com ≥30 empresas) × salário médio (`br_me_rais.microdados_vinculos` 2021, `valor_remuneracao_media_sm`, vínculo ativo em 31/12) e × volume de vínculos por divisão: **r(HHI, salário) = +0,07; r(HHI, emprego) = −0,02 (n=86 divisões)** — nenhuma das duas correlações se sustenta; setor dominado por poucas gigantes não paga sistematicamente mais nem emprega proporcionalmente menos. **Achado de qualidade de dado**: 124 empresas em `br_me_cnpj.empresas` têm `capital_social` = exatamente `999.999.999.999` (R$ 1 trilhão, quase o PIB nacional inteiro) — valor-sentinela/placeholder, não capital real; refazer o HHI excluindo essas 124 linhas não muda o resultado (mesmos r's), mas o valor deveria ser tratado como nulo em qualquer outro uso de `capital_social`.
- **T30-2 ✅ (2026-08-27)** Microempresas ativas per capita (`br_me_cnpj.porte='1'`, snapshot 2025-09, matriz, média nacional 7.167/100 mil hab) × crescimento de vínculos RAIS 2012→2022 por município: **r = −0,10 (n=5.557 municípios com ≥20 vínculos em 2012)** — fraco e no sentido oposto ao esperado: mais microempresa per capita não acompanha maior crescimento formal, se algo é levemente pior.
- **T30-3 ✅ (2026-08-27)** Taxa líquida de abertura de empresas (aberturas−baixas, via datas em `br_me_cnpj.estabelecimentos` snapshot único 2025-09, painel município×ano 2011-2020) × crescimento do PIB municipal nominal: correlação contemporânea **r = 0,043**; um ano depois **r = 0,076** (n≈50-56 mil pares município-ano) — ambas fracas, mas a defasada é a maior das duas, um sinal (fraco) de antecipação, não de coincidência pura.
- **T30-4 ✅ (2026-08-27)** Empresas com sócio formalmente estrangeiro (`br_me_cnpj.socios.tipo='3'`, dez/2021, 8.877 CNPJs distintos) × emprego formal (`br_me_rais_identificada.estabelecimentos` 2021): só **192 (2,2%) aparecem como estabelecimento empregador na RAIS**, contra uma taxa-base de 15,5% entre todos os 20,4 milhões de CNPJ ativos do país (3,16M/20,4M) — empresa com sócio estrangeiro tem ~7x menos chance de ser empregadora direta, consistente com boa parte sendo veículo de investimento/holding sem operação própria (mesmo padrão achado em T48-2 para offshores do ICIJ). Entre as 192 que empregam, a comparação por CNAE (n pequeno, máx. 18 por divisão) não mostra padrão consistente de empregar mais nem menos que a média nacional do setor.
- **T30-5 ◐ (2026-08-27)** HHI de concentração de emprego por seção CNAE (`br_me_rais_identificada` 2021, 21 seções) × arrecadação federal por trabalhador formal na seção (`br_rf_arrecadacao.cnae` 2021, só disponível em nível de seção nacional, não município): **r = −0,25 (log-log: −0,31, n=15 seções com arrecadação não-nula)** — setores mais concentrados arrecadam proporcionalmente MENOS por trabalhador, não mais; mas n=15 no nível de seção é amostra pequena para uma conclusão forte. `br_rf_arrecadacao` não tem grão municipal nem por porte de empresa (mesmo bloqueio de T16-2/T16-5), então o teste fica limitado ao nível macro de setor.

## 31 · Desenvolvimento Humano

- **T31-4 ◐** IVS-IPEA × mortalidade infantil (SIM×SINASC 2020–22): **r = +0,31 (n=1.423 municípios ≥20 mil hab)** — vulnerabilidade social prevê TMI melhor que PIB pc (−0,13, T03-3).
- **Achado de bug de query (2026-09-02)**: `br_ipea_avs.municipio` **não** está no grão de município apesar do nome —
  é UDH (Unidade de Desenvolvimento Humano, subdivisão intramunicipal do Atlas IPEA), com até 1.594 linhas para um
  único `id_municipio` (São Paulo) na combinação `raca_cor='total'`/`sexo='total'`/`localizacao='total'` que parece
  a "linha resumo". Um `JOIN` direto por `id_municipio` sem `GROUP BY`/`AVG()` prévio infla `n` (5.565 municípios
  viraram 16.687 linhas nesta sessão) — a correlação em si não muda muito porque os pares se repetem idênticos, mas
  o `n` reportado ficaria errado. **A nota anterior de que "AVS só tem um ano no espelho" também estava errada**: a
  tabela tem **dois anos, 2000 e 2010** (não uma série contínua, mas dá pra medir Δ entre as duas ondas do Censo
  correspondentes — T31-5 abaixo).
- **T31-1 ✅ (2026-09-02)** IVS 2010 (`br_ipea_avs.municipio`, agregado por município com `AVG(ivs)` sobre as UDH) ×
  taxa de beneficiários do Bolsa Família por habitante (`br_cgu_beneficios_cidadao.novo_bolsa_familia`,
  snapshot mais recente 2025-07, CPFs distintos ÷ população 2022): **r = +0,82 (n=5.565)** — forte e no sentido
  esperado, vulnerabilidade social medida em 2010 prevê bem a cobertura de benefício quinze anos depois; taxa média
  de cobertura 9,8% da população. *(A17, correlação forte ≥0,4 — ver "Resultados transversais")*
- **T31-3 ✅ (2026-09-02)** Dado o r=+0,82 de T31-1, o descolamento que a pergunta imagina (muitos beneficiários,
  baixa vulnerabilidade) é raro: separando os municípios em quartis de IVS e de cobertura, **0 dos 5.565** caem no
  quadrante "1º quartil de vulnerabilidade (menos vulnerável) + 4º quartil de cobertura (mais benefício)", e só
  **2** caem no oposto (muito vulnerável, pouca cobertura) — não há evidência de sobreposição de programas nem de
  erro cadastral em massa; a focalização do CGU segue de perto o indicador de vulnerabilidade nos extremos.
- **T31-5 ◐ (2026-09-02)** ΔIVS 2000→2010 por município: **melhorou (caiu) em 5.510 dos 5.565 (99%)**, média
  −0,129 (de 0,480 para 0,352) — melhora quase universal, não seletiva. Cruzando essa melhora com crescimento do
  PIB per capita no período mais próximo disponível (2002→2010, `br_ibge_pib.municipio`): **r = +0,08 em nível
  absoluto de Δ; r = −0,07 em crescimento relativo** — praticamente nulo, a melhora do IVS não acompanhou quem
  cresceu mais em renda. Contra a cobertura atual de benefícios (2025, proxy imperfeito por não haver CGU antes de
  2004): **r = −0,16** — fraco, mas no sentido de que quem mais melhorou tem hoje cobertura um pouco maior (efeito
  provavelmente capturado pelo nível de vulnerabilidade de partida, já medido em T31-1). `◐` porque a pergunta
  original pede "acompanhou... repasses sociais" numa janela 2000-2010 em que o Bolsa Família do espelho mal
  existia (a tabela `bolsa_familia_pagamento` mais antiga só cobre 2021+); a comparação usa a cobertura de 2025
  como proxy estrutural, não a série histórica que a pergunta sugere.
- **T31-2 ⏳** Bloqueio estrutural: a pergunta pede sobrepor áreas de risco do IPEA-AVS a "setores censitários mais
  vulneráveis do Censo" — o espelho só tem dado demográfico em grão de setor censitário para o **Censo 2010**
  (`br_ibge_censo_demografico.setor_censitario_*_2010`); o Censo 2022 (`br_ibge_censo_2022`) só existe em grão de
  **município** no espelho, sem tabela de setor censitário. E o próprio AVS para em 2010 (ver acima) — não há como
  cruzar "setor censitário mais vulnerável" de 2022 com nada no espelho.

## 32 · Conectividade

- **T32-1 ✅** Anatel IBC × ENEM: **r = +0,57 (n=1.736)** — mais forte que qualquer medida de renda. *(A4)*
- **T32-5 ✅ (proxy)** IBC × formalidade +0,56 e × empresas +0,57 (A5, A6) — conectividade anda com dinamismo econômico; direção causal pendente.
- **T32-3 ✅** Densidade banda larga fixa (Anatel) × IBC: **r = +0,73 (n=3.070)**; × PIB pc **+0,31** — as duas métricas Anatel se confirmam mutuamente; a renda explica bem menos.
- **T32-2, T32-4 ⏳** Pendentes — SIMET tem formato por escola (faixa_velocidade) sem nota/velocidade contínua municipal; cruzamento exige normalização dedicada.

## 33 · Internacionais

- **T33-1 ◐** Ranking FBSP×Censo (CVLI/100k, último ano): AP 64,7; BA 47,7; AM 42,5; CE 39,0; PE 37,3 — 5 UFs acima de 37/100k, faixa de países em conflito armado. Comparação com benchmarks internacionais (fora do espelho) pendente.
- **T33-2…T33-5 ⏳** Pendentes — os comparativos internacionais (OCDE/países vizinhos) não estão no espelho além do PISA.

## 34 · Atlas

- **T34-1…T34-5 ⏳** Pendentes — malhas geobr exigem funções espaciais.

## 35 · Transporte

- **T35-5 ◐** Tempo de deslocamento (Mobilidados) × rendimento RAIS: **r = −0,40 entre municípios ≥100 mil hab (n=101)**; × PIB pc −0,15 — cidades mais ricas têm deslocamentos menores; a "renda efetiva" (salário÷tempo) penaliza as metrópoles médias do Norte/Nordeste. Demais itens exigem cruzamento com CAGED origem-destino.
- **T35-2 ✅ (2026-09-02)** `br_mobilidados_indicadores.tempo_deslocamento_casa_trabalho` (única safra, 2010, 229
  municípios metropolitanos) × PIB per capita 2021 e crescimento de PIB pc 2010→2021 (`br_ibge_pib.municipio`):
  **r = −0,10 com o nível de PIB pc 2021 (n=227); r = −0,08 com o crescimento relativo 2010-2021** — ambos fracos e
  negativos, contrariando a hipótese: as regiões de pior mobilidade **não** são sistematicamente nem as mais ricas
  nem as de crescimento mais recente; tempo de deslocamento parece descolado do ciclo econômico municipal medido
  por PIB.
- **T35-4 ✅ (2026-09-02)** `br_mobilidados_indicadores.transporte_media_alta_capacidade` (2019, indicador
  "Estações de TMA em operação na capital" — metrô/BRT/VLT) × mortes por acidente de transporte no SIM 2019
  (`causa_basica` CID-10 `V*`, local de ocorrência, ÷ população): das **27 capitais, 9 têm alguma estação de
  transporte de média/alta capacidade e 18 não têm nenhuma**. Taxa média de mortes no trânsito: **10,6/100 mil
  habitantes nas capitais com TMA vs 19,9/100 mil nas sem TMA** — quase o dobro. Confirma a hipótese: capitais com
  infraestrutura de transporte de massa registram bem menos mortes no trânsito per capita que as sem nenhuma —
  ainda que o desenho seja observacional (correlação, não causal; capitais com metrô tendem a ser as maiores/mais
  antigas, um confundidor óbvio não controlado aqui).
- **T35-1, T35-3 ⏳** Pendentes — bloqueios de dado confirmados (2026-09-02): T35-1 exige o par origem→destino do
  trabalhador no CAGED, que o espelho não tem (só o município do estabelecimento — mesmo bloqueio de T13-1/3/5).
  T35-3 pede "onde o tempo de deslocamento cresceu mais **entre medições**", mas
  `tempo_deslocamento_casa_trabalho` tem uma safra só (2010) — sem segunda medição não há Δ para calcular.

## 36 · Religiosidade

- **T36-1 ✅** Templos/100k × PIB pc: **r = −0,11 (n=5.570) — praticamente nenhuma relação**; Piauí (mais pobre) lidera densidade de templos, SC (rica) é 2ª. *(A16)*
- **T36-2 ✅** Fiéis por religião (Censo 2022) × templos no CNPJ (CNAE 9491-0/00): **r = +0,47 com % evangélicos e −0,58 com % católicos (n=1.687 municípios)** — o registro empresarial de templos captura o evangelicalismo; católico tem paróquia, não empresa.
- **T36-3 ⏳** Pendente — exige RAIS série longa por CNAE religioso vs mudança de composição religiosa 2010→2022; censo 2010 por religião não está no espelho.
- **T36-4 ◐** Coberto por T36-2: onde há muitos evangélicos há mais templos-CNPJ (+0,47); perfil socioeconômico fino fica para cruzamento com instrução do próprio censo religioso.
- **T36-5 ✅ (proxy)** Templos × rendimento médio RAIS: +0,06 — idem, nada.

## 37 · Sanções

- **T37-1 ✅** Dos **93 sancionados do TCU, 38 (41%) seguem com CNPJ ativo** em 2023.
- **T37-5 ✅ (parcial)** PGFN: **R$ 7,06 trilhões consolidados, 7,67M devedores; SP sozinho R$ 3,04 tri** (RJ 873 bi, MG 601 bi). Sobreposição com TCU pendente.
- **T37-2 ✅ (2026-09-02)** CNPJ com dívida ativa federal (`br_pgfn_dividaativa.divida`,
  pessoa jurídica, CPF/CNPJ normalizado com `regexp_replace`, **6.675.326 CNPJs
  distintos**) cruzados contra `br_cgu_licitacao_contrato.contrato_compra` e
  `br_cgu_cartao_pagamento.microdados_governo_federal` (toda a série de cada
  tabela, ambas pequenas — 472.638 e 1.666.696 linhas, sem necessidade de
  filtro de partição): **24.942 desses CNPJs (0,37%) firmaram 166.692
  contratos federais (R$517,4 bi)**; **24.926 (0,37%) receberam 142.256
  transações de cartão corporativo (R$43,2 milhões)**. Os 20 maiores CNPJs por
  valor contratado concentram R$234,1 bi dos R$517,4 bi — e são, quase todos,
  estatais/empresas de economia mista com disputa tributária federal em curso
  (CAIXA, SERPRO, BNDES, Correios, Telebras, Banco do Brasil, Embraer,
  FIOTEC), não fornecedores irregulares. **Ressalva importante**: a dívida
  ativa da PGFN inclui qualquer inscrição em status `ATIVA*` — cobrança,
  parcelamento negociado no SISPAR, ajuizada — não distingue débito
  contestado/parcelado de inadimplência definitiva; ter uma linha na PGFN é
  comum até para os maiores fornecedores legítimos do governo. Excluindo os
  20 maiores, ainda restam **24.922 CNPJs / R$283,3 bi / 161.900 contratos** —
  a cauda longa de empresas menores com débito federal que seguem contratando
  seria o recorte mais informativo para uma investigação de integridade, não
  o agregado bruto.
- **T37-3 ◐ (2026-09-02)** Sócios pessoa física (`br_me_cnpj.socios`,
  `tipo='2'`, snapshot 2025-09) dos 84 CNPJs distintos de
  `br_tcu_inidoneos.empresas`: **79 das 84 empresas têm ao menos 1 sócio PF
  no snapshot atual, totalizando 131 pares pessoa-empresa / 125 pessoas
  distintas**. Buscando essas mesmas pessoas (par `documento`+`nome`) como
  sócias de QUALQUER outro `cnpj_basico` na mesma tabela: **72 das 125
  (57,6%) reaparecem em 166 CNPJs novos distintos**; dessas 166 empresas, **58
  (35%) estão `Ativa`, 55 `Baixada`, 53 `Inapta`** (matriz, 2025-09) —
  indício real de recriação de personalidade jurídica por sócios de empresas
  inidôneas. **Ressalva que rebaixa para `◐`**: `br_me_cnpj.socios.documento`
  vem mascarado para pessoa física (só os 6 dígitos do meio, ex.
  `***855401**`) — `bridges.yaml` já registra que essa máscara sozinha NÃO
  identifica uma pessoa (999.751 máscaras distintas para 17,17M pares,
  0,18% únicas). Mitiguei exigindo `documento` **e** `nome` idênticos, o que
  reduz muito a chance de colisão mas não a elimina — é correspondência
  heurística de identidade, não uma chave garantida.
- **T37-4 ✅ (2026-09-02)** CNPJ (matriz) do TCU e da PGFN cruzados contra
  `br_me_rais_identificada.estabelecimentos` (ano mais recente do espelho,
  2021): das **84 empresas do TCU, 18 (21%) têm estabelecimento na RAIS 2021,
  somando 228 vínculos ativos** — exemplos: Construtora CHC Ltda (Fortaleza-CE,
  55 vínculos), C R Almeida S/A Engenharia (São José dos Pinhais-PR, 2
  estabelecimentos, 45+41), Metro 2 Construções (Saquarema-RJ, 13), Quartzo
  Engenharia de Defesa (Rio de Janeiro-RJ, 11), CMSD Tecnologia (Pinhais-PR,
  11), Sistematech (Barueri-SP, 11), D G de Oliveira Construções (Bom Jesus
  do Tocantins-PA, 6), GD Distribuidora de Livros (Belo Horizonte-MG, 5) — a
  maioria construtoras/engenharia, condizente com o perfil de sanção do TCU
  (obras públicas). Para a PGFN, a escala muda de ordem: dos **2.778.942
  estabelecimentos totais da RAIS 2021, 825.417 (29,7%) pertencem a um
  `cnpj_basico` com alguma dívida ativa federal registrada**, respondendo por
  **23.666.974 dos 47.500.354 vínculos formais do país (49,8%)** — quase
  metade do emprego formal brasileiro está em empresa com débito federal
  inscrito em algum momento. Mesma ressalva de T37-2: a base PGFN é ampla
  demais (qualquer inscrição ativa) para servir de proxy de irregularidade
  sozinha; o achado central é que a proporção de estabelecimentos "devedores"
  cresce quando ponderada por vínculo — empresas maiores/mais antigas
  acumulam mais dívida ativa registrada ao longo do tempo, não que o débito
  se concentre nas pequenas.

## 38 · Educação Básica

- **T38-4 ✅ (fato)** PISA 2022 matemática: **Brasil 380,3 vs OCDE 474,8** (n≈10.800 alunos BRA) — gap de ~95 pontos ≈ 2,5 anos escolares.
- **T38-3 ⏳** Bloqueio parcial: `br_inep_formacao_docente` só tem granularidade UF/região/nacional (colunas `grupo`/`modalidade`/`rede`/`tipo_localizacao`, sem município) — não dá pra responder no recorte municipal que a pergunta pede; um recorte por UF seria possível mas exigiria decodificar os códigos de `grupo` (não documentados no dicionário consultado nesta rodada).
- **T38-5 ✅ (2026-08-27)** Queda de matrícula na educação básica (Sinopse INEP, `br_inep_sinopse_estatistica_educacao_basica.localizacao`, soma de todas as etapas/redes/localizações, 2010→2022, média nacional −9,7%) × queda de população jovem 0-19 (`br_ibge_censo_2022.populacao_grupo_idade_sexo_raca`, mesmo intervalo, média −17,2%, total nacional 62,9M→54,5M): **r = +0,71 (n=5.565 municípios)** — forte e no sentido esperado: onde a população jovem caiu mais, a matrícula caiu mais também, embora em proporção menor (a queda de matrícula é sistematicamente menor que a queda demográfica — indício de melhora de cobertura/permanência absorvendo parte da retração de coorte). **Achado de bug de query, não de dado**: `br_ibge_censo_2022.populacao_grupo_idade_sexo_raca` e `.indice_envelhecimento_raca` guardam os censos **2010 E 2022 na mesma tabela** sob a coluna `ano` (apesar do nome do dataset ser só "censo_2022") — um `SUM(populacao)` sem `WHERE ano=2022` soma as duas safras e dobra o total (confirmado: 393,8M vs os 203,1M reais). As demais tabelas do dataset (`populacao_grupo_idade_uf`, `populacao_idade_sexo`, `alfabetizacao_grupo_idade_sexo_raca`, as `caracteristica_domicilio_*`) não têm esse problema — só essas duas.
- **T38-2 ◐ (2026-08-27)** `br_inep_educacao_especial.matricula_aee` só tem grão UF×rede (Pública/Privada), sem município nem escola — não dá pra responder "dentro do mesmo município" como a pergunta pede. Com o que existe: cobertura do AEE (atendimento educacional especializado) entre os alunos público-alvo da educação especial (2021, média nacional 49,1%, UF×rede) × proficiência SAEB 9º ano matemática (mesma UF×rede): **r = +0,12 (n=54)** — fraco, sem relação clara. Ressalva importante: `quantidade_matricula` nessa tabela é o total de alunos **público-alvo da educação especial**, não a matrícula geral da rede — a métrica calculável é "% deles que recebe atendimento especializado", não "% da rede que é educação especial" (que exigiria uma tabela de matrícula total por UF×rede, disponível em outra tabela do Sinopse, não cruzada aqui por orçamento de tempo).
- **T38-1 ⏳** Pendente — cruzar alfabetização INEP × PISA por faixa socioeconômica exige casar as faixas de INSE (`inep_indicador_nivel_socioeconomico`, escala própria) com os quartis de status socioeconômico do PISA (índice ESCS, escala OCDE), que não têm correspondência direta documentada — não é join por chave, é reclassificação metodológica.

## 39 · Justiça

- **T39-1 ✅ (fato)** Judiciário estadual (CNJ 2021, 28 tribunais): **despesa de pessoal = 90,1% em média** da despesa total; mínimo 76,4%, máximo 98,7%. Confirma o gancho do tema.
- **T39-2, T39-3, T39-4 ⏳ — bloqueio estrutural confirmado (2026-08-25)**: nenhum dos 4 espelhos de TCE tem multa/penalidade por município. `br_tce_sp` é só uma tabela de 2 colunas (nome do município), sem nenhum dado de fiscalização. `br_tce_pi` tem `despesas_total`/`receitas_total`/`licitacoes_estado`/`prefeituras` mas nenhuma tabela de penalidade/deliberação. `br_tce_rj.penalidades_ressarcimento_estado` existe mas as 948 linhas são **100% `TipoEnte = 'ESTADUAL'`** — zero linhas municipais. `br_tce_es` tem `resultados_fiscalizacoes` (só `ValorExecutivo`/`ValorLegislativo` por ano/esfera, sem município) e `lista_responsaveis`/`julgamento_contas` (por responsável, sem valor de multa nem porte do município). Cruzar CNJ-improbidade × "TCEs que mais multaram" por município não é possível com o que está espelhado — precisaria de um scrape novo (SP e PI não têm fonte de penalidade nenhuma hoje).
- **T39-5 ⏳ — bloqueio estrutural confirmado (2026-08-25)**: `br_cnj_estatisticas_poder_judiciario` só tem a tabela `recursos_financeiros` (despesa por tribunal/ano — a mesma usada em T39-1), sem nenhuma coluna de volume processual (não existe `numero_processos`/`processos_julgados`). "Custo médio por processo" não dá pra calcular sem uma tabela de movimentação processual do CNJ, que não está no espelho.

## 40 · Federalismo Fiscal

- **T40-1 ◐** CAPAG 2025 × transferências voluntárias per capita (Transferegov): **r = +0,03 (n=2.000+ municípios ≥20 mil hab)** — capacidade fiscal não explica quem recebe transferência; porte e política sim.
- **T40-2 ✅** CAPAG × FIRjan IFGF: **r = +0,37 (n=1.322)** — os dois índices concordam parcialmente; divergências concentram-se nos intermediários (C/B).
- **T40-3 ✅ (2026-08-25)** CAPAG 2025 × emendas parlamentares per capita (`br_cgu_emendas_parlamentares`, valor pago 2014–2025, R$168,6 bi / 5.419 municípios): **r = −0,08 (n=1.509 municípios ≥20 mil hab)** — join direto por código IBGE de 7 dígitos (`id_municipio_gasto` = `Código Município Completo`, sem padding, sem bridge documentada — nenhuma existia entre essas duas tabelas). Mesmo padrão do T40-1: capacidade fiscal não explica quem recebe mais emenda por habitante; se algo, o sinal é levemente inverso (piores CAPAG recebem um pouco mais), não "política forte = melhor nota".
- **T40-4 ⏳ — falso pressuposto confirmado (2026-08-25)**: `br_siop_orcamento` é orçamento da **União** (por órgão/UO/função/ação — ver tabelas `dados`/`alteracoes_orcamentarias`/`localizadores`), não tem despesa obrigatória por orçamento **municipal**. A métrica que a pergunta pede ("quanto pesam as despesas obrigatórias do orçamento dos municípios") vive no SICONFI (`br_me_siconfi`), não no SIOP — a pergunta cruza a fonte errada com o índice municipal (IFGF).
- **T40-5 ⏳** Pendente — exige série temporal da CAPAG (só há um ano no espelho) e SICONFI alinhado ao Transferegov por município e ano.

## 41 · Nutrição

- **T41-excesso ✅ (fato)** SISVAN 2023: excesso de peso adulto — **RS 73,6%, RN 72,4%, SP 71,9%, MS 71,7%, CE 70,4%** (top 5 UFs). CMED/BPS/Farmácia Popular pendentes.
- **T41-1, T41-4 ⏳** Bloqueio já documentado (ver "Bloqueios mapeados" ao fim): `br_saude_farmaciapopular.estabelecimentos` não tem preço praticado nem série temporal.
- **T41-2, T41-5 ⏳ — descoberta de incompatibilidade de fonte (2026-08-27)**: `br_saude_bps.dados` é **compra pública de medicamento por instituição** (hospital/secretaria, `nome_do_municipio_da_instituicao`), não consumo per capita da população — testado mesmo assim (déficit nutricional infantil SISVAN 2023, taxa média 4,3%, n=5.536 municípios, × gasto BPS per capita por município da instituição compradora, join por nome+UF): **r = −0,01, mas só 153 dos 5.536 municípios (2,8%) têm alguma instituição compradora no BPS** — a maioria dos municípios nunca aparece porque a compra costuma ser centralizada em secretarias estaduais/grandes hospitais, não no município de residência do paciente. O indicador não responde "acesso a medicamento contínuo da população local", só "volume de compra pública onde a instituição está sediada" — resultado descartado por não medir o que a pergunta pede.
- **T41-3 ⏳** Pendente — POF só tem grão UF (`sigla_uf`, sem município); "gasto com alimentação" não é uma coluna direta em `br_ibge_pof.despesa_coletiva_2017` — as despesas vêm codificadas por produto (`V1904`/`id_codigo_5_bd`/`id_codigo_7_bd`) e exigem cruzar com `cadastro_de_produtos_2017` para isolar a categoria "alimentação" (equivalente a um crosswalk COICOP), não tentado nesta rodada por risco de classificação errada sem tempo para validar.

## 42 · Água

- **T42-3 ⏳ — bloqueio estrutural confirmado (2026-09-02)**: `br_mma_extincao.fauna_ameacada` e `.flora_ameacada`
  (as únicas duas tabelas do dataset) têm só `especie_ou_subespecie`/`familia`/`grupo`/`ordem`/`categoria` de
  risco — **nenhuma coluna geográfica**, nem bioma, nem município, nem UF. Não há chave nenhuma pra ligar espécie
  ameaçada a MapBiomas ou a foco de queimadas do INPE; a pergunta pede um cruzamento espacial que a fonte não
  suporta de jeito nenhum, não é falta de join documentado.
- **T42-1, T42-2, T42-4, T42-5 ⏳** Pendentes — `br_ana_telemetria` é a fonte comum às quatro, e o
  `codigo`/`municipiocodigo` do seu `inventario` (37.782 estações) **não bate com o id_municipio do IBGE em nenhum
  caso testado** (0 de 4.770, achado documentado em `bridges.yaml`/nota de T42 no prompt) — sem essa chave não dá
  pra colocar bacia/estação no mesmo grão de município que `inpe_queimadas`/`mapbiomas_estatisticas`/`inmet_bdmep`
  exigem; a série hidro/clima em si existe, mas o vínculo geográfico dela ao resto do espelho não.

## 43 · Cultura

- **T43-3 ✅ (com ressalva)** Medalhas olímpicas do Brasil por esporte (contagem por atleta, esportes coletivos inflados): futebol 181, vôlei 132, basquete 60, vela 36, atletismo 35, vôlei de praia 26, judô 24, natação 21.
- **T43-1, T43-2, T43-4, T43-5 ⏳ — bloqueio estrutural confirmado (2026-08-27)**: `world_olympedia_olympics.athlete_bio` (a única tabela com dados de atleta) tem `birth_date`/`birth_year`/`country`/`country_noc`, mas **nenhuma coluna de cidade ou município de nascimento** — nem texto livre, nem código. Sem essa chave geográfica não dá pra ligar medalha a município (T43-1, T43-2, T43-5) nem checar se o crescimento de medalhas seguiu município/região (T43-4 pede série temporal nacional, que é possível, mas o cruzamento com PIB nacional/ciclos de política esportiva não foi tentado nesta rodada). Precisaria de uma fonte adicional (ex.: COB, Wikipedia estruturada) com naturalidade do atleta.

## 44 · Saneamento, Produção Rural e Desmatamento

- **T44-1 ✅ (2026-08-25)** Esgotamento sanitário (ANA Atlas Esgotos) × mortalidade
  infantil (SIM×SINASC 2020-22): **r = +0,30 (n=1.709 municípios ≥20 mil hab)**
  entre o índice "sem coleta/sem tratamento" e a TMI — mais forte que renda
  (PIB per capita × TMI: r=−0,19 no mesmo recorte). Saneamento prevê mortalidade
  infantil melhor que renda pura.
- **T44-2 ✅ (2026-08-25)** Desmatamento acumulado (PRODES 2022) × produção
  agropecuária municipal (PAM/PEVS, mesmo ano): **r=+0,52 com valor de lavoura**
  (temporária+permanente), r=+0,29 com silvicultura plantada, r=+0,21 com
  extração vegetal nativa — n=5.563 municípios. Terra desmatada vira
  predominantemente lavoura, não silvicultura nem extração nativa. **Achado
  lateral**: `br_ibge_pam.valor_producao` está em **mil reais**, não reais —
  confirmado batendo a safra de soja 2022 (121,29 Mt, valor batendo só como
  R$347 bi, não R$347 mi) — sem aviso no schema; virou métrica
  `valor_producao_agropecuaria` em `metrics.yaml` pra não repetir o erro.
- **T44-3 ⏳ — bloqueio estrutural grave confirmado (2026-08-25)**: `br_rf_cafir.imoveis_rurais`
  tem 169,9M linhas mas só 3,89M `id_imovel_receita_federal` distintos — e
  **61-64% de TODAS as linhas, em TODO snapshot mensal, têm
  `id_imovel_receita_federal = NULL`** (confirmado no snapshot mais recente,
  2025-09-02: 6,27M de 10,16M linhas). `id_municipio`/`area` seguem preenchidos
  nessas linhas órfãs, mas sem id não dá pra saber se são propriedades
  distintas ou fragmentos/duplicatas das linhas com id — qualquer soma por
  município seria um número inventado. Não é bug desta sessão, é dado como
  chegou; precisa de re-scraping ou de entender a causa na fonte antes de usar
  esta tabela pra qualquer coisa.
- **T44-4 ⏳ — dataset inteiro vazio, confirmado (2026-08-25)**: as 8 tabelas de
  `br_ibama_embargos` têm linhas (113.878 em `termo_embargo`, 48.776 em `itens`,
  439 em `decisao`) mas **100% das colunas são string vazia** — o header do CSV
  original virou o próprio nome da coluna (uma mega-string com `;` dentro) e
  nenhuma linha de dado real foi carregada. Diferente do bloqueio já conhecido
  ("infra-blocked, SSL proxy" em `todo.md`) — aquele é sobre não conseguir
  *atualizar*; este é sobre o que já está no beelink não servir pra nada.
  Precisa reprocessar o CSV fonte do zero (delimitador `;`, provavelmente lido
  como texto único por engano).
- **T44-5 ✅ (2026-08-25)** Outorgas de captação de água (ANA, join por nome+UF —
  99,4% de 6.283 pares casaram, `br_ana_outorgas` não tem `id_municipio` algum,
  achado novo em `bridges.yaml`) por habitante × produção agrícola per capita
  (PAM): **r=+0,13**; × densidade de empresas ativas per capita (CNPJ):
  **r=+0,02 (n=1.583)** — outorgas per capita não é bem explicado por nenhum
  dos dois; provavelmente reflete disponibilidade hídrica/setor industrial
  específico, não densidade econômica geral.

## 45 · Integridade do Sistema Financeiro e Fornecedores Públicos

- **T45-1 ✅ (2026-08-25)** Dos 93 CNPJs inidôneos do TCU, **57 (61%) estão
  registrados no SICAF** (Comprasgov) e **12 desses (21%) seguem com
  `habilitadoLicitar=true`** — formalmente inidôneos e ainda habilitados a
  licitar com a União.
- **T45-2 ✅ (2026-08-25)** Dos 41.106 CNPJs de fundos de investimento (CVM),
  **8 têm dívida ativa federal (PGFN)**, somando **R$121,6 milhões**. Baixa
  incidência é esperada — fundos são veículos passivos, não costumam ter
  passivo tributário próprio.
- **T45-3 ✅ (2026-08-25)** Dos 2.529 CNPJs penalizados pelo Banco Central,
  **82 (3,2%) também são administradores de carteira registrados na CVM** —
  **29 seguem "EM FUNCIONAMENTO NORMAL"**, 68 registros (de CNPJs que podem
  se repetir) estão "CANCELADA".
- **T45-4 ✅ (2026-08-25)** Só 1 dos 84 CNPJs inidôneos do TCU aparece como
  sócia pessoa jurídica no grafo de holdings (Brasil.IO): **C R Almeida S/A —
  Engenharia de Obras**, sócia consorciada em **13 consórcios de obras
  públicas** (Consórcio Imigrantes, Consórcio Queiroz Galvão-CR Almeida,
  entre outros).
- **T45-5 ⏳ — bloqueio estrutural confirmado (2026-08-25)**: dos 131.626
  registros do OpenSanctions tagueados Brasil, o campo `identifiers` de
  `LegalEntity` está praticamente vazio — só 11 fragmentos de identificador no
  total, 2 parecendo CNPJ (e esses 2 são reexportações de sanções domésticas
  Lei 8666/14133, não sanção internacional de verdade). Cruzar por CNPJ direto
  não é viável; sobraria só nome-a-nome contra dezenas de milhões de linhas do
  CNPJ, exatamente o tipo de join caro que o CLAUDE.md já pede pra evitar.

## 46 · Educação Superior e Acesso

- **T46-1 ✅ (2026-08-25)** PROUNI (ingressantes com financiamento não
  reembolsável integral+parcial, Censo da Educação Superior 2021) por
  município × PIB per capita 2021: **r = −0,017 (n=1.909 municípios com ≥50
  ingressantes)** — nenhuma correlação. Nacionalmente o PROUNI cobriu 73.299
  bolsas integrais + 14.760 parciais em 2021 (~2,2% dos 3,95M ingressantes),
  em queda desde 2019 (138.115 integrais). O programa não se concentra nem
  nos municípios mais pobres nem nos mais ricos — a distribuição segue onde
  há IES privada com sede aberta, não a renda do município.
- **T46-2 ✅ (2026-08-25)** % de docentes com doutorado nas IES por município
  (Censo da Educação Superior 2021) × taxa de abandono no ensino médio
  (Indicadores Educacionais 2021): **r = +0,12 (n=603 municípios com ≥20
  docentes em exercício)** — correlação fraca e no sentido contrário ao
  esperado, provavelmente confundida por porte/urbanização (cidades maiores
  têm IES mais qualificada E mais abandono por outros motivos). Médias:
  28,7% de docentes com doutorado, 3,5% de abandono no EM — ambas plausíveis.
- **T46-3 ✅ (2026-08-25)** Bolsistas de mobilidade internacional CAPES
  (2005-2019, por UF da instituição de origem no Brasil) × PIB per capita
  2019 e docentes com doutorado 2019: **r = +0,41 com PIB per capita,
  r = +0,98 com docentes doutores (n=27 UFs)** — a correlação quase perfeita
  com o corpo docente doutor mostra que mobilidade internacional segue
  capacidade de pesquisa instalada, não renda. **5 estados (SP, MG, RJ, RS,
  PR) concentram 67% dos 138.987 bolsistas** identificados por UF brasileira
  (dos 146.036 totais — o resto tem `uf_instituicao_origem` preenchido com
  nome de estado/região **estrangeira**, ex.: "CALIFORNIA", "KANSAS",
  "HLAVNI MESTO PRAHA" — a coluna mistura origem BR e origem estrangeira sob
  o mesmo nome, não documentado antes; decodificação exigiu casar nome de UF
  por extenso, sem sigla, contra `br_bd_diretorios_brasil.uf.nome`).
- **T46-4 ✅ (2026-08-25)** Concorrência no SISU (candidatos aprovados por
  vaga, 2021) × taxa de conclusão (concluintes/matrículas, Censo da Educação
  Superior 2021), por município: **r = +0,10 (n=495 municípios)** — sem
  relação. Médias: 2,9 candidatos aprovados por vaga, 13% de concluintes
  sobre matrículas no ano (plausível para cursos de ~4-5 anos com matrícula
  em expansão). Concorrência de entrada não prediz throughput de formação.
- **T46-5 ✅ (2026-08-25)** Nível socioeconômico médio das escolas na ANA
  2016 (escala ordinal 1-7, Muito Baixo…Muito Alto) comparando municípios
  com e sem IES local (Censo da Educação Superior 2016): **4,52 nos 698
  municípios com IES vs. 3,77 nos 4.856 sem IES** — quase 1 ponto de
  diferença numa escala de 7. Ter ensino superior local acompanha (não prova
  causar) melhor nível socioeconômico nas escolas de ensino fundamental da
  mesma cidade. **Achado lateral, novo bug de código**: `nivel_socio_economico`
  em `br_inep_ana.escola` usa faixas de código DIFERENTES nos dois únicos
  anos da tabela — 2014 usa 8-14, 2016 usa 15-21 pro mesmo rótulo ("Alto" =
  13 em 2014, = 20 em 2016) — comparar o código bruto entre anos dá ordenação
  errada silenciosa; documentado em `bridges.yaml` `coded_differently`.

## 47 · Servidor Público e Integridade

- **T47-1 ✅ — com ressalva importante (2026-08-25)** Cargos comissionados
  federais per capita por UF (Painel Estatístico de Pessoal, `br_mp_pep`,
  ano/mês mais recente 2025-05, `cce_e_fce + das_e_correlatas`) × PIB per
  capita 2021: **r = +0,61 (n=27 UFs) com o DF incluído, mas r = −0,07 sem
  o DF** — a correlação inteira era um artefato de um único ponto de
  alavancagem: o DF concentra 19.419 cargos comissionados (4x mais que o
  RJ, segundo colocado, com 4.758) só por sediar a maioria dos órgãos
  federais, e por acaso também é a UF de maior PIB per capita do Brasil.
  Removido o DF, não sobra relação nenhuma entre riqueza da UF e
  concentração de cargo comissionado federal.
- **T47-2 ✅ (2026-08-25)** Composição racial dos cargos comissionados
  federais em 2024 (`br_mp_pep`) × população brasileira no Censo 2022:
  **Branca 53,1% (PEP) vs 45,5% (Censo) — sobrerrepresentada em +7,6pp**;
  **Parda 35,2% vs 44,3% — sub-representada em −9,1pp**; **Preta 8,1% vs
  8,9% — quase proporcional**; Amarela e Indígena levemente
  sobrerrepresentadas em termos relativos (bases pequenas). O desenho do
  desequilíbrio racial no topo do funcionalismo federal é mais específico
  do que "não-branco sub-representado": quem perde participação é
  principalmente pardo, não preto.
- **T47-3 ✅ — achado contraintuitivo (2026-08-25)** Composição racial do
  funcionalismo federal como um todo (`br_me_siape`, 358.869 vínculos,
  snapshot mais recente): Branca 54,5%, Parda 30,0%, Preta 7,1%, Não
  informado 5,3%. Comparado ao cargo comissionado (PEP 2024: Branca 53,1%,
  Parda 35,2%, Preta 8,1%) — **o topo (comissionados) não é mais branco que
  a base, é ligeiramente MENOS branco e mais pardo/preto** do que o
  funcionalismo geral capturado pelo SIAPE. Ressalva: as duas fontes cobrem
  universos parecidos mas não idênticos (SIAPE aqui é pesado em
  universidades federais nos exemplos observados; PEP é comissionados do
  Executivo como um todo, incluindo autarquias fora do escopo típico do
  SIAPE) — tratar como sinal, não como prova definitiva de igualdade.
- **T47-4 ✅ (2026-08-25)** Dos 84 CNPJs inidôneos do TCU (`br_tcu_inidoneos.empresas`,
  formato de 14 dígitos), **8 (9,5%) aparecem como responsável por obra no
  CNO** (`br_rf_cno.microdados`, `id_responsavel` = CNPJ), somando **8.535
  registros de obra, 7.633 ainda com `situacao = 'Ativa'`**. Destaque:
  **C R Almeida S/A — Engenharia de Obras**, a mesma empresa achada em
  T45-4 como sócia em 13 consórcios de obras públicas via grafo de holding
  do Brasil.IO, aparece aqui também com 193 obras ativas no CNO — as duas
  fontes independentes (TCU + Brasil.IO em T45-4, TCU + CNO aqui)
  convergem na mesma empresa.
- **T47-5 ✅ (2026-08-25)** Obras ativas no CNO per capita por município
  (174,4M registros nacionais com `situacao = 'Ativa'`) × participação
  industrial no PIB local (`va_industria/pib`, 2021): **r = +0,15**; ×
  PIB per capita: **r = +0,23 (n=5.558 municípios, cobertura quase total)**
  — correlações fracas. Município ter mais obra ativa registrada per
  capita acompanha muito fracamente maior renda, e quase não se relaciona
  com o peso do setor industrial — esperado, já que `va_industria` agrega
  extrativa+transformação+construção+utilidades, não isola construção
  civil (o espelho não tem essa quebra).

## 48 · Sanções Internacionais e Verificação de Identificador

- **T48-1 ⏳ — bloqueio estrutural confirmado (2026-08-25)**: nenhuma das
  três listas tem identificador estruturado utilizável para CNPJ/CPF.
  `eu_sanctions.sanctions` (42.347 linhas, 5.994 entidades) tem **zero**
  linhas ligadas ao Brasil em qualquer campo de país/nacionalidade/texto
  livre; `un_sanctions.sanctions` (1.002 linhas) idem. `global_ofac_sanctions.sanctions`
  (19.129 linhas) não tem coluna de país estruturada — só **20 linhas**
  mencionam "Brazil" em `remarks` (texto livre, majoritariamente
  Hezbollah/narcotráfico); busca por "CNPJ" no texto: 0 ocorrências; por
  "CPF": 1, falso positivo. O Brasil simplesmente não é alvo principal de
  nenhuma das três listas, e mesmo as poucas linhas que citam o país não
  têm identificador parseável em coluna.
- **T48-2 ✅ (2026-08-25)** Das 1.532 entidades do ICIJ Offshore Leaks
  marcadas Brasil, **292 CNPJs distintos** casam por nome exato normalizado
  contra `br_me_cnpj.empresas.razao_social` — sem colisão relevante (máx.
  2 CNPJ por nome ICIJ). Dos 292: **191 (65%) `Ativa`**, 83 (28%)
  Suspensa, 16 (6%) Baixada. **290 dos 292 (99%) têm `natureza_juridica='2216'`
  — "Empresa Domiciliada no Exterior"** (o código legal específico para
  empresa estrangeira que possui imóvel/aeronave registrável no Brasil);
  `capital_social=0` em 100% dos casos confirma que são veículos
  administrativos, não empresas operacionais — o mecanismo é: sociedades
  do Panama/Pandora/Paradise Papers que compraram imóvel/aeronave no
  Brasil precisaram de CNPJ próprio para isso.
- **T48-3 ⏳ — join por nome não confiável para pessoa física (2026-08-25)**:
  dos 4.025 nomes distintos de "officers" (pessoa física) do ICIJ marcados
  Brasil, **2.293 (57%) casam por nome exato** contra
  `br_me_cnpj.socios.nome`, mas o mais frequente casado, "ROBERTO RESTUM",
  aparece em **944 linhas de sócio diferentes** — implausível como
  beneficiário único. Sem CPF (que o ICIJ não expõe), o join por nome aqui
  produz volume grande e plausível, mas não confiável — mesma armadilha
  de nome comum já documentada em T45-5, ao contrário de T48-2 (nomes de
  empresa offshore são distintivos o bastante para não colidir).
- **T48-4 ✅ (2026-08-25)** Das 292 entidades ICIJ casadas ao CNPJ (T48-2),
  **82 (28%) aparecem como sócia pessoa jurídica** no grafo de holdings do
  Brasil.IO — ex.: FLINDERS INVESTMENTS CORP. (Panama Papers) é sócia de
  GREENVALE HOLDING LTDA. Contra os CNPJ inidôneos do TCU: **zero
  sobreposição** — populações estruturalmente diferentes (TCU pune
  fornecedor público; ICIJ vaza posse offshore), confirma que não é o
  mesmo fenômeno de T45-4/T47-4 (C R Almeida S/A).
- **T48-5 ✅ (2026-08-25)** Das 292 entidades casadas ao CNPJ, **277 (95%)
  vêm do Panama Papers**, 6 do Pandora Papers, 4+1 do Paradise Papers —
  consistente com o Panama Papers ter tido a maior cobertura do Brasil
  (era Lava Jato, 2016). Jurisdição de incorporação: Panamá (104), Ilhas
  Virgens Britânicas (71), Nevada-EUA (69). Taxa de ativa por origem não
  difere o bastante entre vazamentos para um padrão claro de sobrevivência
  por jurisdição — o volume fora do Panama Papers é pequeno demais (11
  linhas) para comparação confiável.

## 49 · Saúde Suplementar e Atenção Básica

- **T49-1 ✅ (2026-08-25)** Cobertura de plano privado médico-hospitalar (ANS
  2021, deduplicado — ver bug de `data_carga` abaixo) × TMI (SIM×SINASC
  2021), n=3.987 municípios com ≥20 nascidos vivos: **r = −0,21**;
  controlando PIB per capita, parcial ≈ **−0,20** — praticamente inalterado.
  Cobertura média municipal (não ponderada) 9,2%, TMI média 16,2/1000. Plano
  privado prevê menos mortalidade infantil independente da renda — mas
  cobertura×PIB pc já é r=+0,40, então os dois efeitos coexistem sem se
  anular.
- **T49-2 ✅ (2026-08-25)** Cobertura de plano privado (ANS dez/2020,
  deduplicado) × cobertura ESF (Atenção Básica 2020), n=5.568 municípios
  (quase universal): **r = −0,47**; controlando PIB per capita, parcial ≈
  **−0,44** — forte mesmo sem a renda como confundidor. Cobertura ESF média
  87,2%, cobertura privada média 8,4%. Leitura mais plausível: ESF se
  concentra onde o privado não chega (mesmo padrão de "direcionamento da
  política" de T03-2), não que o privado desloque o público.
- **T49-3 ✅ — achado contra-intuitivo (2026-08-25)** Cobertura vacina
  pentavalente (Imunizações 2020) × TMI (SIM×SINASC 2020), n=3.886
  municípios: **r = +0,13** — positiva. Cobertura ESF × TMI no mesmo
  recorte: **r = +0,19**, maior que a da vacina. Ambas positivas pelo mesmo
  motivo de T03-2/T49-2: cobertura de vacina e de ESF sobem justamente nos
  municípios de pior indicador de saúde (focalização/mutirão), não o
  contrário — nenhuma das duas "causa" mais óbito. Cobertura penta média
  85,0%.
- **T49-4 ⏳ — bloqueio estrutural confirmado (2026-08-25)**: a pergunta
  pedia cobertura vacinal Covid-19 (doses/pessoa por município), mas
  `br_ms_vacinacao_covid19` só tem `microdados_estabelecimento` (805.803
  linhas, um diretório de postos — id/nome/município, sem data, sem dose,
  sem paciente) e `dicionario`. O próprio `dicionario` referencia duas
  tabelas que **não existem no disco nem na view**: `microdados_paciente`
  (sexo/raça/nacionalidade do vacinado) e `microdados_vacinacao` (tipo de
  vacina, categoria prioritária, data da dose) — mesmo padrão de
  `br_mec_prouni` (T46-1): o `dicionario` promete uma granularidade que o
  mirror não trouxe. **Nota lateral usável**: com o que existe dá pra medir
  densidade de pontos de vacinação (não cobertura) — 27,3
  estabelecimentos/100 mil hab em média (n=5.570, cobertura quase total),
  fracamente correlacionada com ESF (**r = +0,28**).
- **T49-5 ✅ — achado contra-intuitivo (2026-08-25)** Beneficiários ANS 60+
  (médico-hospitalar, dez/2022, deduplicado) ÷ total de beneficiários, por
  município, vs. população 60+ ÷ população total (Censo 2022), n=2.581
  municípios com ≥500 beneficiários: nacionalmente **14,4% dos
  beneficiários ANS têm 60+ contra 15,9% da população geral** — o plano
  privado é ligeiramente MAIS jovem que a população, não mais velho
  (esperava-se seleção adversa pró-idoso; consistente com a maioria dos
  planos serem coletivos empresariais, vinculados a emprego formal de
  adultos em idade ativa). **r = +0,62** entre % 60+ no plano e % 60+ na
  população do mesmo município; **r = −0,11** com PIB per capita (municípios
  mais ricos têm base de beneficiários levemente mais jovem).

## 50 · Justiça Complementar e Filiação Partidária

- **T50-1 ✅ (2026-08-25)** Filiação partidária TSE (16.479.345 filiados
  regulares, snapshot 2024-10-21): mulheres variam de 25,8% (NOVO) a
  53,6% (PMB) da base por partido. Eleitos 2022: mulheres eleitas variam
  de 11,2% (PSD) a 27,7% (PT) entre os grandes partidos — **PSOL é o único
  onde a conversão é quase 1:1** (52,3% filiadas → 52,9% eleitas); NOVO
  tem a menor base feminina filiada (25,8%) e também baixa conversão
  (11,1%). A lacuna filiação→eleição (~25-37pp por UF) **não varia com a
  riqueza do estado**: r=+0,11 (n=27 UFs) entre o tamanho da lacuna e o
  PIB per capita 2021 — é fenômeno estrutural do sistema partidário, não
  regional.
- **T50-2 ✅ (2026-08-25)** Filiados por partido×UF × votos para deputado
  federal 2022: **r=+0,64 (n=579 pares partido×UF)** — mais filiados
  acompanha mais votos, correlação moderada. Outlier: PTB/RS com só 12
  filiados mas 89.766 votos (7.480 votos/filiado, ~100x a mediana) —
  indício de "puxador de legenda" carregando sozinho um partido de base
  filiada residual. A eficiência de conversão (votos/filiado) **não varia
  com a riqueza da UF**: r=−0,13 (n=27) contra PIB per capita.
- **T50-3 ✅ (2026-08-25)** Taxa de homicídio doloso 2022 por UF (SINESP)
  × população Censo 2022 × % votos Bolsonaro/PL no 1º turno: **r=−0,43
  (n=27 UFs)** — estados mais violentos votaram proporcionalmente menos
  em PL. Faixa: PE no topo (34,7/100mil, 29,9% PL) a SP no fundo
  (6,6/100mil, 47,7% PL); exceção clara: RR (25,9/100mil, mas 69,6% PL).
  Corrobora de forma independente o achado prévio de T27 (homicídios×Lula
  = +0,46, PIB pc×Lula = −0,62) — como PL e PT concentram a maior parte
  do 1º turno, os dois resultados são espelhados e se validam mutuamente.
  **Achado de bridge quebrada**: a entrada existente em `bridges.yaml`
  para `br_mjsp_sinesp.ocorrencias_uf.uf` descrevia "código de 2 letras",
  mas os dados reais são nome de estado por extenso acentuado — um join
  ingênuo `uf = sigla_uf` devolvia zero linhas; corrigido.
- **T50-4 ◐ (2026-08-25)** STF: 2.708.849 decisões (2000-2025), 7.644
  classificadas "Direito Eleitoral". Candidaturas TSE: anos de eleição
  municipal registram 15-20x mais candidaturas que anos de eleição geral
  (380-560 mil vs 18-29 mil), mas **o volume de decisões eleitorais do
  STF não acompanha esse salto** — média de 298 casos/ano em anos
  municipais vs 346/ano em anos gerais, praticamente igual. Confirma que
  disputas municipais ficam nas TREs/TSE e raramente sobem ao STF. **A
  perna do gasto do Judiciário eleitoral (CNJ) está bloqueada** — ver bug
  novo de escala documentado abaixo.
- **T50-5 ✅ — com ressalva de cobertura (2026-08-25)** PROCON (2024):
  13.803 reclamações, 3.083 CNPJs distintos, mas **cobre só 7 de 27 UFs**
  (CE, GO, SP, PE, SC, PB, MT). Reclamações por 100 mil hab: CE 80,4
  (51% de todo o dataset) a MT 0,30 — disparidade de 268x quase certamente
  é cobertura desigual da fonte, não litigiosidade real. Setor mais
  reclamado: bancos com carteira comercial (2.679), distribuição de
  energia (536), água/saneamento (486). Das CNPJs reclamadas, **86,4%
  seguem ativas** no cadastro CNPJ.

## 54 · Censo Histórico e Consistência Populacional

- **T54-1 ✅ (2026-08-25)** IBGE (`br_ibge_populacao.municipio`) e MS
  (`br_ms_populacao.municipio`, somado por sexo/faixa etária) concordam
  **byte-a-byte em 2018-2021 e 2024-2025 (diff=0 nos 5.570 municípios)** —
  o MS simplesmente copia a estimativa do IBGE vigente nesses anos.
  Divergem em dois regimes diferentes: **2000-2012**, ruído de revisão de
  -0,16% a -4,49% (vintages diferentes da mesma estimativa); e
  **2022-2023**, queda estrutural de -3,69%/-4,07% — o IBGE resetou para
  o Censo 2022 (203.080.756, já verificado em `metrics.yaml`) enquanto o
  MS manteve a extrapolação de tendência antiga (210.862.983). Em 2022:
  MS é maior em **5.487 dos 5.570 municípios (98,5%)**, divergência média
  absoluta 2,66%, 7 municípios com mais de 10% de diferença, correlação
  0,9998 (mesma forma, nível sistematicamente diferente). Achado tipo T31
  "duas fontes discordam", mas com mecanismo identificado — o MS não
  aplicou o reset do Censo 2022; virou caveat na métrica `populacao`.
- **T54-2 ✅ — achado grave de estabilidade (2026-08-25)** Nenhum dos 3.876
  códigos de `id_municipio` distintos no Censo 1970 (mirror) ficou "fora"
  da lista atual de 5.570 municípios (2022) — o IBGE nunca reaproveita um
  código para um lugar diferente. Mas o inverso é grave: **1.694 dos 5.570
  municípios atuais (30,4%) não existem como código próprio no Censo 1970**,
  e **1.632 (29,3%) não existem no Censo 1980** — criados depois, majoritariamente
  por emancipação pós-Constituição de 1988. Em 2010 o problema já é pequeno
  (5 municípios, 0,09%). Um join direto `id_municipio` 1970→2022 perde
  silenciosamente 30% dos municípios de hoje, e mesmo os pares que casam
  não são diretamente comparáveis (o "pai" em 1970 ainda inclui o
  território dos filhos emancipados depois). Achado lateral de
  metodologia: a primeira tentativa desse cálculo usando `NOT IN` deu 0
  divergências nos dois sentidos — armadilha clássica de `NOT IN` com
  `NULL` na subquery; corrigido com `NOT EXISTS`/anti-join.
- **T54-3 ◐ (2026-08-25)** Para 2010: a soma de `peso_amostral` por
  `id_municipio` nos microdados pessoa bate **exatamente** com
  `br_ibge_populacao.municipio` (190.755.799 = 190.755.799, correlação 1,0
  em 5.565 municípios) — reconciliação de fontes bem-sucedida. Mas a
  reconstrução **não é possível para 1970/1980/1991/2000** — nenhuma
  dessas quatro tabelas tem coluna de peso amostral no mirror (só existe
  em `microdados_pessoa_2010`); 1970 tem 24,78M linhas para uma população
  real de ~93M, confirmando amostra sem peso publicado, não censo completo.
- **T54-4 ✅ (2026-08-25, com ressalva)** Usando os únicos dois anos com
  coluna "sabe ler e escrever" decodificada no mirror (`v0323` em 1991,
  `v0428` em 2000), taxa de alfabetização não-ponderada 5+ anos: **73,97%
  em 1991 (11.148.907/15.071.878) → 74,66% em 2000 (15.133.376/20.274.411)**
  — alta de só 0,69pp. **Ressalva**: denominador "5+" difere do "15+"
  oficial do IBGE (que saltou de ~81,9% para ~86,4% na mesma década) — os
  números não são comparáveis ao oficial, só entre si. Confirma T54-2 numa
  nova janela: dos 4.491 municípios de 1991, todos têm par em 2000, mas
  **1.016 municípios de 2000 (18,4%) não existiam como código em 1991**.
- **T54-5 ✅ (2026-08-25)** `br_ibge_estadic.recursos_humanos` (2020, único
  ano coincidente com `br_ibge_pib.uf`) × PIB per capita por UF: **r =
  −0,25 (n=27 UFs)** — sinal fraco na direção esperada. Extremos: RR
  (15,91%), MA (9,44%), RO (7,06%) têm as maiores fatias de comissionados
  na administração direta; TO (0,13%), SC (0,67%), SP (0,84%) as menores —
  os estados mais ricos do Sul/Sudeste concentram o extremo baixo, mas
  n=27 é pequeno demais para além de um sinal direcional.

## 51 · Energia, Comércio Exterior e Infraestrutura

- **T51-1 ✅ (2026-08-25)** Consumo de energia elétrica por UF (MME,
  "Total", 2021) × PIB por UF (soma dos municípios, 2021): **r = +0,98
  (n=27) em nível bruto** — quase só efeito de tamanho de estado.
  Normalizando ambos por população (Censo 2022), **r cai para +0,67** —
  ainda forte, mas bem menor que a bruta sugeria. **Achado de correção de
  escopo**: `br_mme_consumo_energia_eletrica` só tem a tabela `uf` no
  espelho (38.880 linhas, 2004-2023) — **não existe grão municipal**, ao
  contrário do que a descrição do dataset sugeria. Sanity check: soma
  nacional 2023 = 531,0 TWh, batendo com o consumo elétrico nacional real
  (~500-550 TWh/ano, EPE).
- **T51-2 ✅ (2026-08-25)** Tráfego aéreo por UF de destino (ANAC
  `pontualidade`, maio/2026, UF extraída do texto livre via regex) × PIB
  por UF: **r = +0,98**; × consumo de energia por UF: **r = +0,94** —
  tráfego aéreo replica quase perfeitamente o tamanho econômico do estado
  (SP: 66.492 etapas previstas no mês, RR: 140). Mas cancelamento e
  atraso **não** acompanham riqueza: cancelamento ponderado × PIB **r =
  +0,24**, atraso>30min × PIB **r = −0,11** — ambos fracos, um com sinal
  "errado". Pontualidade parece explicada por outra coisa (companhia
  aérea, hub congestionado), não por riqueza do estado de destino.
- **T51-3 ✅ — achado nuançado (2026-08-25)** Preço do cimento CP II-32
  (SINAPI, jun/2026) por UF × PIB per capita: **r = −0,41** — RR
  (R$1,59/kg) e AC (R$1,34/kg) pagam mais que o dobro de RJ (R$0,68/kg) e
  SP (R$0,71/kg), consistente com sobrecusto logístico no Norte remoto.
  Mas o **índice geral de materiais** (1.794 insumos, cada um relativizado
  à média nacional do próprio insumo) inverte o sinal: **r = +0,29** com
  PIB per capita. A "sobretaxa da distância" é real para uma commodity
  pesada e transportada (cimento), mas não generaliza para a cesta inteira
  de materiais, que mistura itens cujo preço reflete mais mão de
  obra/terreno local do que frete.
- **T51-4 ✅ (2026-08-25)** Custo de mão de obra de referência do SINAPI
  (classificação MAO DE OBRA, unidade "H") × salário médio real na
  construção civil formal (RAIS 2022, CNAE 41/42/43): **r = +0,36
  (n=27)**. Salário RAIS construção × PIB per capita: **r = +0,39**. Os
  três se movem na mesma direção mas com correlação só moderada — o piso
  SINAPI (SP R$3.177/mês-equiv.) não é um substituto fiel do salário real
  (SP R$3.451, PA R$3.529 — PA supera SP na RAIS apesar de não liderar no
  SINAPI). **Achado colateral de unidade**: a classificação MAO DE OBRA do
  SINAPI mistura `unidade='H'` (horista) e `unidade='MES'` (mensalista)
  sem separação — média direta mistura R$/hora com R$/mês silenciosamente.
- **T51-5 ✅ — validação forte (2026-08-25)** Consumo de energia
  "Comercial" por UF (MME 2021) × vínculos formais no comércio (RAIS 2022,
  CNAE 45/46/47): **r = +0,99 em nível bruto**, **r = +0,89 per capita** —
  a correlação sobrevive quase intacta mesmo neutralizando o tamanho do
  estado. É a validação mais limpa do grupo: consumo comercial de energia
  é um proxy fiel da densidade do setor de comércio formal, não só do
  tamanho do estado.

## 52 · Séries Financeiras, Dívida Pública e Crédito

- **T52-1 ✅ (2026-08-25)** Crédito BNDES per capita acumulado (2002-2026,
  `operacoes_nao_automaticas`, só linhas com `id_municipio`) × PIB per
  capita 2021: **r = +0,19 (n=1.132 municípios)** — correlação fraca e
  positiva; crédito de fomento concentra-se um pouco mais em municípios
  ricos, mas não é o fator dominante. Distribuição assimétrica: **média
  R$10.519/hab vs. mediana R$1.498/hab**. Total contratado nos municípios
  identificados: **R$602,8 bilhões**, de um total geral de **R$1,229
  trilhão contratado / R$952 bilhões desembolsados** em 23.483 operações
  desde 2002.
- **T52-2 ✅ (2026-08-25)** **Zero** dos 4.356 CNPJs distintos que tomaram
  crédito direto do BNDES aparecem entre os 84 CNPJs (14 dígitos)
  inidôneos do TCU — nem por CNPJ completo nem por raiz (8 primeiros
  dígitos). Resultado negativo genuíno, não bloqueio: o join funciona
  (99,9% dos CNPJs do BNDES batem contra `br_me_cnpj.estabelecimentos`),
  só não há sobreposição nesta tabela (que cobre só operações diretas
  grandes, não o crédito indireto via bancos repassadores).
- **T52-3 ✅ (2026-08-25)** Estoque da dívida pública federal em dezembro
  de cada ano ÷ PIB nacional: **2017: 79,2% → 2018: 81,0% → 2019: 83,1% →
  2020: 91,1% (pico da pandemia) → 2021: 84,8%**. Não é monotônico: salto
  concentrado em 2020, reversão parcial em 2021. Nível ~5-10pp acima da
  série oficial de Dívida Bruta do Governo Geral do BCB — mesma forma,
  escopo mais amplo (inclui carteira do Banco Central). **Achado de
  escala**: somar `valor_estoque` por `ano` sem filtrar `mes` infla o
  total em ~12x (cada linha é um snapshot mensal, não um fluxo) — virou
  caveat de métrica.
- **T52-4 ✅ (2026-08-25)** IGP-M acumulado (tabela anual, limpa) **2019:
  7,30% vs. IPCA 4,31% (+3,0pp)**; **2020: 23,14% vs. IPCA 4,52%
  (+18,6pp — descolamento enorme)**; **2021: 17,78% vs. IPCA 10,06%
  (+7,7pp)** — os três valores de IGP-M batem exatamente com os números
  oficiais da FGV. 2020 confirma a história clássica: índice "de atacado"
  disparou na pandemia enquanto o índice ao consumidor ficou represado.
  **Achado de bug de schema**: as 4 tabelas MENSAIS de `br_fgv_igp`
  (`igp_m_mes`, `igp_di_mes`, `igp_10_mes`, `igp_og_mes`) têm as colunas
  `ano` e `mes` **trocadas** — `ano` contém o número do mês (1-12) e `mes`
  contém o ano. Confirmado: `WHERE mes=2021 AND ano=12` devolve
  `variacao_acumulada_ano = 17,78%`, batendo com o IGP-M oficial de 2021.
  As tabelas ANUAIS não têm o bug. Um `GROUP BY ano` numa tabela `*_mes`
  agrupa por mês do calendário, não por ano civil — sem erro, silencioso.
- **T52-5 ✅ (2026-08-25)** Selic anualizada (composta a partir da série
  mensal do BCB SGS) × valor total contratado anual pelo BNDES: **r =
  −0,38 (n=23 anos, 2003-2025)** — correlação negativa moderada, longe de
  mecânica (2022 teve Selic alta *e* contratação em alta; 2024 teve Selic
  caindo *e* o maior volume contratado da série, R$93,9 bi). Consistente
  com o crédito do BNDES rodar majoritariamente em TJLP/TLP, parcialmente
  isolado do ciclo Selic. **Achado de unidade**: as séries `meta_selic`/
  `selic_anualizada` (series_code 4390/4391) em `br_bcb_sgs.series`
  **não são taxas anuais apesar do nome** — são a Selic mensal (%a.m.,
  valores típicos 0,2-1,3); ler o valor bruto como %a.a. é um erro de 10x.

## 53 · Índices de Competitividade e Comparativos Internacionais

- **T53-1 ✅ (2026-08-25)** Os três índices de saúde fiscal estadual **não**
  medem a mesma coisa. CLP "Solidez Fiscal" 2022 × CAPAG estados 2022:
  **r=+0,71 (n=26)** — concordam bem. Mas CLP-fiscal × IFGF (agregado por
  UF, média municipal 2022): **r=+0,16**; CAPAG × IFGF: **r=+0,05
  (n=27)**. O IFGF é bottom-up a partir de municípios — sua média por UF
  não captura o mesmo que um índice do próprio governo estadual, mesmo
  compartilhando o rótulo "fiscal".
- **T53-2 ✅ (2026-08-25)** CLP ranking geral (2022) × PIB per capita 2020:
  **r=+0,78 (n=27)** — forte. DF R$87.016, SP R$51.365 per capita vs. SP
  #1 no ranking geral (83,2), AP último (#27, 27,0). Competitividade
  estadual é, em boa parte, riqueza — mas ~39% da variância fica fora da
  renda (r²≈0,61).
- **T53-3 ◐ — comparação de bases diferentes (2026-08-25)** Razão impostos
  líquidos/PIB nos 27 estados (IBGE 2020): faixa 6,8%-17,3%, média 11,7%.
  Razão IRPF/PIB na OCDE (2015, 34 países): faixa 3,3%-27,3%, média 9,1%.
  `impostos_liquidos` do IBGE é agregado de impostos indiretos (tipo VAT),
  não IRPF — os numeradores medem tributos de natureza distinta; mostra
  que o Brasil não está fora da amplitude OCDE, mas não permite concluir
  "mais ou menos tributado" sem normalizar as bases.
- **T53-4 ✅ (2026-08-25)** CLP "Segurança Pública" × "Sustentabilidade
  Social" (2022): **r=+0,71 (n=27)**; Segurança × PIB per capita 2020:
  **r=+0,58**. SC #1 em segurança (100,0), DF #2 (83,5); RR último (0,0),
  AP (3,0) — consistente com rankings de violência conhecidos. Segurança
  correlaciona mais com coesão social do que com renda pura.
- **T53-5 ⏳ — corrupção de dado confirmada (2026-08-25)**:
  `expenditure_health`/`expenditure_education`/`total_expenditure`/
  `total_receipt` em `world_oecd_public_finance.country` estão
  preenchidos com o sentinel de overflow `INT32_MIN` (-2147483648) em
  82%-98,5% das linhas "não-nulas" (`total_expenditure`: só 20 de 1.319
  linhas têm valor real) — qualquer benchmark de gasto público seria
  calculado sobre lixo. Colunas limpas e usáveis: PIB nominal, desemprego,
  expectativa de vida, Gini, WGI de governança (2010-2016 só).

## 55 · Vulnerabilidade Social, Medicamentos e Consumo

- **T55-1 ✅ (2026-08-25)** Série nacional anual 2000-2019: homicídios
  LGBTQI+ (GGB) × óbitos por agressão no SIM (causa_basica X85-Y09): **r =
  +0,82 (n=20 anos)** — as duas séries sobem e caem juntas, inclusive a
  queda 2018→2019 aparece nas duas ao mesmo tempo. **Achado estrutural**:
  nenhuma das 5 tabelas de `br_ggb_relatorio_lgbtqi` tem UF ou município —
  é 100% agregado nacional por ano; a correlação geográfica originalmente
  cogitada não é respondível.
- **T55-2 ✅ (2026-08-25)** Top 15 princípios ativos por quantidade
  vendida no SNGPC (2014-2021) casados por nome contra `br_anvisa_cmed.precos`
  (13/15 casaram): **r(ln quantidade, ln preço mediano) = +0,14 —
  praticamente nulo**. Fenobarbital (R$11,36/caixa, 882 mil unidades) e
  periciazina (R$12,85, 903 mil) vendem tanto quanto escitalopram
  (R$227,04, 1,71 milhão) — preço regulado não filtra o volume entre os
  mais vendidos. Ressalva: a tabela de vendas está truncada em exatamente
  10.000.000 de linhas e cobre só 406 dos 5.570 municípios (ver bloqueio).
- **T55-3 ✅ (2026-08-25)** Cruzando os mesmos top-15 do SNGPC com
  `br_anvisa_consultas.registros`: **fenobarbital tem só 3 registros
  `Ativo` contra 21 `Inativo`** (11º mais vendido, 882 mil unidades) e
  **periciazina só 1 `Ativo` contra 2 `Inativo`** (903 mil unidades) —
  concentração extrema de fabricante para dois medicamentos de alto
  volume. Escitalopram, por contraste, tem 46 ativos/47 inativos. Risco
  de desabastecimento é real e específico, não genérico.
- **T55-4 ⏳ — bloqueio estrutural confirmado (2026-08-25)**:
  `br_fipe_veiculos.precos` (11.289 linhas, único arquivo no disco) tem
  **apenas 5 colunas**: `vehicle_type`, `brand_code`, `brand_name`,
  `model_code`, `model_name` — nenhuma coluna de preço, ano ou geografia,
  apesar do nome da tabela. É um catálogo estático de marca/modelo, não
  uma série de preços FIPE. Não há chave municipal ou temporal alguma
  para cruzar com nada.
- **T55-5 ✅ — padrão invertido (2026-08-25)** Composição racial 2019:
  **GGB (vítimas LGBTQI+): Branca 36,8%, Parda 27,4%, Preta 9,7%** (n=329)
  vs. **SIM (agressão, todas as vítimas): Parda 68,4%, Branca 21,7%,
  Preta 7,6%** (n=42.702) — padrão invertido: entre vítimas LGBTQI+
  identificadas pela imprensa (fonte do GGB), branca é a maior fatia;
  entre vítimas de homicídio em geral, parda domina esmagadoramente.
  Plausivelmente reflete viés de cobertura jornalística do GGB (sub-registra
  vítimas menos visíveis), não uma diferença demográfica real.

## 56 · Violência Notificada, Vulnerabilidade Infantil e Autolesão

- **T56-1 ✅ (2026-08-27)** Volume anual de notificações de autolesão/tentativa
  de suicídio no SINAN (`LES_AUTOP='1'`, partição `ano_sinan`) × taxa nacional
  de suicídio do Atlas da Violência IPEA (série 323, `valores_nacional`):
  **r = 0,75 (n=12 anos, 2011-2022)** — ambos sobem no período, mas em ritmos
  muito diferentes: autolesão notificada saltou de 14.940 (2011) pra 116.269
  (2021, +678%), enquanto a taxa de suicídio subiu de 5,02 pra 7,38 por 100
  mil (+47%). A correlação alta reflete duas séries crescentes no mesmo
  período mais do que uma relação direta — o crescimento da notificação é
  muito mais rápido que o crescimento real de suicídios, consistente com
  expansão da cobertura/cultura de notificação do SINAN ao longo da década,
  não com uma epidemia de autolesão 7x maior que o aumento real de mortes.
  2022 tem queda no SINAN (61.676) que é artefato de subnotificação daquele
  ano (mesmo padrão do dip visto na contagem geral da tabela), não real.
- **T56-2 ✅ (2026-08-27)** Taxa de notificação de violência sexual contra
  crianças/adolescentes (SINAN, `VIOL_SEXU='1'` e idade < 18 extraída de
  `NU_IDADE_N`, 197.256 notificações com município de residência preenchido,
  2010-2019) por 100 mil habitantes × cobertura líquida de pré-escola
  (`br_abrinq_oca.municipio_primeira_infancia`, 5.570 municípios): **r =
  0,025 (n=22.270 pares município-ano)** — correlação nula. Cobertura
  pré-escolar municipal não explica taxa de notificação de violência sexual
  infantil; mais provável é que a notificação capture capacidade/vontade de
  notificar (rede de saúde, Conselho Tutelar) tanto quanto incidência real,
  ruído que domina qualquer sinal de vulnerabilidade educacional.
- **T56-3 ✅ (2026-08-27)** Composição racial das vítimas notificadas no SINAN
  (preto+pardo, `CS_RACA IN ('2','4')` sobre raça conhecida) × proporção de
  vítimas negras entre homicídios do Atlas da Violência IPEA (série 41 ÷
  série 328, mesmo conceito "negro" = preto+pardo no IPEA): **SINAN sobe de
  46,5% (2011) pra 57,7% (2022); Atlas IPEA sobe de 67,4% pra 76,6%** no
  mesmo intervalo — pessoas negras são sempre 15-21 pontos percentuais mais
  representadas entre os homicídios (desfecho letal) do que entre as
  notificações de violência em geral (todos os tipos, incluindo
  não-letais). **Achado de gotcha de codificação**: `CS_RACA='2'` sozinho
  (só "preta") captura apenas ~9% das notificações — usar só o código
  "preta" em vez de "preta+parda" subestima em 5x a proporção real de
  vítimas negras; ver `coded_differently` em `bridges.yaml`.
- **T56-4 ✅ (2026-08-27)** Participação de parceiro/ex-parceiro/namorado/
  ex-namorado (`REL_CONJ`/`REL_EXCON`/`REL_NAMO`/`REL_EXNAM`='1') entre
  agressores de vítimas mulheres no SINAN: oscila entre 22,9% e 33,3% do
  total de notificações femininas, **sem tendência de alta** — cai de 31,9%
  (2011) pra 26,3% (2024) em termos relativos, mas em número absoluto cresce
  de 23.925 pra 115.362 (quase 5x), porque o total de notificações femininas
  do SINAN também explodiu (75.033 → 437.828, ~5,8x). No mesmo período, os
  homicídios de mulheres do Atlas da Violência IPEA **caíram** de 4.522
  (2011) pra 3.806 (2022, -16%). As duas séries divergem: violência não-letal
  contra a mulher notificada cresce fortemente em volume absoluto (mais
  expansão de cobertura do sistema de notificação do que necessariamente
  mais violência) enquanto o desfecho letal (homicídio) recua no mesmo
  intervalo.
- **T56-5 ✅ (2026-08-27) — bug de partição confirmado** `NU_ANO` vem como
  string vazia (`''`) para **326.563 de ~4,94M linhas** de
  `br_ms_sinan_violencia.microdados_violencia`, concentradas quase
  inteiramente (326.503 de 326.563) no lote com `ano_sinan=2020` — um
  `GROUP BY NU_ANO` pula 2020 inteiro em silêncio (a série salta de 2019
  direto pra 2021, sem erro nem linha vazia visível). A coluna `ano_sinan`
  (inteira, sem valores em branco, cobre 2009-2025 continuamente) é a
  partição confiável — **usar `ano_sinan`, nunca `NU_ANO`, pra qualquer
  série temporal desta tabela.**

## 57 · Ofertas Públicas CVM e Mercado de Capitais

- **T57-1 ✅ (2026-09-02)** Valor total ofertado por ano (`data_inicio_oferta`),
  `br_cvm_oferta_publica_distribuicao.dia`: cresce de R$0,4 bilhão (2008, 2
  ofertas) para R$667,5 bilhões (2021, 6.117 ofertas), caindo para R$614,1
  bilhões em 2022 (5.833 ofertas). **A série para em 2022 — não há uma linha
  sequer de 2023 em diante**, apesar de o dataset se chamar "oferta pública"
  no presente; qualquer leitura de tendência recente com esta tabela
  subestima silenciosamente sem esse corte explícito. **Achado adicional**:
  100% das 27.486 linhas têm `modalidade_oferta = 'Dispensada de Registro'`
  (ICVM 476/476-A) — a tabela cobre só colocação privada/restrita a
  investidor qualificado, não a oferta pública registrada/IPO que o nome
  sugere; nenhuma linha tem `modalidade_registro` preenchida.
- **T57-2 ✅ (2026-09-02)** Por `tipo_ativo`, valor total (R$2.985,6 bilhões
  somados, 2008-2022): **cotas de fundo de investimento fechado lideram**
  (R$1.228,8 bi, 18.166 ofertas), seguidas de **debêntures simples**
  (R$1.103,2 bi, 3.283) — as duas somam **78,1%** do total. O resto se
  distribui entre ações ordinárias (R$180,1 bi), notas promissórias
  (R$155,8 bi), CRI (R$136,5 bi), CRA (R$66,9 bi), notas comerciais (R$48,7
  bi) e certificados de depósito de valores mobiliários (R$23,2 bi).
- **T57-3 ✅ (2026-09-02)** Por `nome_lider` (coordenador), top 6: Itaú BBA
  R$535,5 bi (1.995 ofertas), Bradesco BBI R$376,6 bi (830), BTG Pactual
  R$331,0 bi (2.335), Santander R$159,7 bi (1.044), BRL Trust R$126,7 bi
  (966), XP Investimentos R$86,2 bi (852). **Os três maiores concentram
  41,6% do valor total ofertado** ((535,5+376,6+331,0)/2.985,6) — mercado de
  coordenação bem mais concentrado que o de emissores (13.052 CNPJs
  emissores distintos).
- **T57-4 ✅ (2026-09-02)** Cruzando `cnpj_emissor` (normalizado,
  `lpad(regexp_replace(...,14,'0'))`) contra `br_cvm_fundos.fundos.CNPJ_FUNDO`
  (bridge documentada em `bridges.yaml`): **4.164 dos 46.809 fundos
  registrados (8,9%) já emitiram ao menos uma oferta pública** nesta tabela.
  Patrimônio líquido médio desses fundos: R$48,1 milhões, contra R$50,6
  milhões da média geral dos 46.809 — **sem diferença de porte relevante**;
  ter feito oferta pública de cotas não distingue fundo grande de pequeno.
- **T57-5 ✅ (2026-09-02) — achado limpo, zero coincidências** Dos 13.052
  CNPJs emissores distintos de `br_cvm_oferta_publica_distribuicao.dia`,
  **nenhum** casa com os 84 CNPJs distintos de `br_tcu_inidoneos.empresas`
  (join via `bridges.yaml`, `lpad(regexp_replace(...))` nos dois lados).
  Diferente do achado positivo do CNO em T47-4 (mesma lista de inidôneos, via
  obras públicas), o mercado de capitais registrado na CVM não deu acesso a
  nenhuma das empresas formalmente declaradas inaptas a contratar com a
  União — ao menos não sob o mesmo CNPJ.

## Multi-referência (seção final)

- **M1 ⏳ / M2 ⏳ / M3 ◐ / M4 ⏳ / M5 ⏳** — as cadeias completas exigem pipelines dedicados; componentes já medidos aparecem nas entradas parciais acima (ex.: M4 usa A1/A2; M3 usa T37-1/T37-2/T37-4/T37-5 — falta só o elo emenda→contrato→fornecedor, que exige juntar `cgu_emendas_parlamentares` a `contrato_compra` por órgão/UG, ainda não tentado).

## Bloqueios mapeados (dado ausente, corrompido ou sem chave — não é falta de query)

Catálogo dos itens `⏳` cujo bloqueio já está identificado como estrutural, não como
análise pendente. Cada um precisaria de trabalho de dado (re-scraping, campo novo,
chave nova) antes de qualquer query fazer sentido — tentar responder sem isso
produziria um número que parece verificado mas não é.

- **T05-2** — Senado: o espelho só tem `senadores` + CEAPS; não existe tabela de
  proposições/votações do Senado. Precisaria raspar o dataset de proposições do
  Senado (análogo ao que existe para a Câmara em `br_camara_dados_abertos`).
- **T06-1, T06-4** — INFOPEN/SISDEPEN: colunas com unicode inválido (1.514 linhas).
  Precisa re-scraping da fonte original antes de ser consultável.
- **T08-5, T25-5** — SIOP: a tabela `dados` tem cabeçalhos corrompidos por um BOM
  (byte order mark) não tratado no scraping original. Precisa reprocessar o CSV/XLSX
  fonte tratando o encoding correto.
- **T09-5, T12-4** — Censo 2022 no espelho não tem tabela de responsabilidade/chefia
  de domicílio. Precisaria adicionar essa tabela do Censo 2022 (existe no IBGE, não
  foi trazida para o espelho).
- **T17-3** — TRASE (`br_trase_supply_chain`, citado em `perguntas.md` como
  `trase_supply_chain`) não compartilha uma chave municipal direta com PRODES/PPM no
  formato atual; precisaria de uma tabela ponte (TRASE usa nomes de município em
  formato próprio, não `id_municipio` do IBGE).
- **T25-2** — SICOR não tem chave municipal direta com SIOP; a única ponte é
  `br_bcb_sicor.recurso_publico_complemento_operacao.id_municipio` (usada nas
  respostas de T07-1/T17-1 acima) contra o lado do SIOP, que está bloqueado de todo
  modo por T08-5/T25-5 (cabeçalhos corrompidos) — bloqueio composto.
- **T33-2…T33-5** — comparativos internacionais (rankings OCDE, países vizinhos) só
  existem no espelho via `world_oecd_pisa`; não há CVLI, PIB ou outro indicador
  internacional comparável além do PISA. Precisaria trazer uma fonte nova (ex.:
  World Bank, UNODC) para os comparativos pedidos.
- **T36-3** — precisaria de Censo 2010 por religião, que não está no espelho (só
  Censo 2022 tem os microdados de religião, `br_ibge_censo2022_religiao`); sem o
  ponto de 2010 não dá pra medir mudança de composição religiosa 2010→2022.
- **T44-3** — `br_rf_cafir.imoveis_rurais`: 61-64% de todas as linhas, em todo
  snapshot mensal, têm `id_imovel_receita_federal = NULL` (169,9M linhas, só
  3,89M ids distintos). Precisa re-scraping ou entender a causa na fonte.
- **T44-4** — `br_ibama_embargos` (8 tabelas, 113k-48k-439 linhas): 100% das
  colunas vazias, o header do CSV virou o próprio nome da coluna. Dataset
  inteiro precisa ser reprocessado do zero.
- **T45-5** — OpenSanctions `identifiers` de `LegalEntity` tagueado Brasil
  praticamente vazio (11 fragmentos em 131.626 registros); cruzamento por CNPJ
  direto inviável, só sobraria nome-a-nome caro.
- **T46-1** — `br_mec_prouni` (dataset inteiro) só tem a tabela `dicionario`
  no beelink — sem microdados de beneficiário PROUNI algum (confirmado tanto
  na view DuckDB quanto no disco: `~/rodado/br_mec_prouni/` só tem a pasta
  `dicionario/`). Não bloqueou T46-1 porque o Censo da Educação Superior tem
  as mesmas contagens de bolsista PROUNI agregadas por curso/município
  (`quantidade_ingressantes_financiamento_nao_reembolsavel_prouni_integral`/
  `_parcial`), mas qualquer pergunta que precise do microdado individual
  (CPF, nome, nota) do PROUNI está bloqueada — precisa re-scraping.
- **T47** — `br_mp_pep.cargos_funcoes` **não é "Pessoas Expostas
  Politicamente"** como o nome sugeria em `tasks/espelho_subutilizado.md` (Parte I)
  (hipótese razoável, mas errada) — é o **Painel Estatístico de Pessoal**
  do então Ministério do Planejamento: um painel agregado de cargos e
  funções comissionadas do Executivo federal por UF/órgão/raça/sexo/faixa
  etária, sem CPF nem nome de pessoa alguma. Não serve para o ângulo AML de
  identificar PEPs individuais — serve para análise demográfica/estrutural
  do alto escalão federal (usado em T47-1/T47-2/T47-3).
- **T47** — `id_responsavel` em `br_rf_cno.microdados` é a string literal
  `"nan"` (não NULL, não vazio) para **todo** registro cujo responsável é
  pessoa física (qualificação 110 "Construção em nome coletivo" e
  similares) — 350,1M de 534,1M linhas (65,5%). É artefato de pipeline
  (provavelmente um `NaN` do pandas serializado como texto na exportação
  original), não dado ausente na fonte — o nome (`nome_responsavel`)
  continua presente. Bloqueia qualquer cruzamento por CPF de pessoa física
  nesta tabela; só os 183,9M de linhas com `id_responsavel` de 14 dígitos
  (CNPJ, pessoa jurídica) são utilizáveis para join (usado em T47-4).
- **T47** — `br_me_siorg.remuneracao` (tabela de remuneração por
  cargo/função, esquema CA/CAS/CCD/CCE pós-reforma de 2019) não casa por
  nome com `br_mp_pep.cargos_funcoes.nivel_funcao`/`subnivel_funcao`
  (esquema DAS/CCX/FEX/FPE) — são dois sistemas de nomenclatura de cargo
  comissionado diferentes, sem tabela de correspondência no espelho.
  Estimar custo total de comissionados (contagem do PEP × remuneração do
  SIORG) exigiria uma tabela-ponte cargo-a-cargo que não existe aqui.
- **T49-4** — `br_ms_vacinacao_covid19`: só `microdados_estabelecimento`
  (diretório de postos, sem dose/data/paciente) e `dicionario` existem no
  mirror; as duas tabelas que o próprio `dicionario` referencia —
  `microdados_paciente` e `microdados_vacinacao` (tipo de vacina, categoria
  prioritária, data da dose) — não existem no disco. Sem elas não dá pra
  medir cobertura vacinal Covid-19 por município, só densidade de postos.
  Mesmo padrão de `br_mec_prouni` (T46-1): `dicionario` promete
  granularidade que o mirror não trouxe.
- **T49-1/T49-5** — `br_ans_beneficiario.informacao_consolidada`: múltiplas
  cargas `data_carga` coexistem no mesmo `(ano, mes)` em todo o período
  2014-2025 (2 a 12 `data_carga` distintas por ano); somar
  `quantidade_beneficiario_ativo` agrupando só por `ano/mes` duplica a
  contagem (25,3M vs 50,1M em dez/2022 sozinho, contra ~50,9M oficial da
  ANS). Não é bloqueio de uso — é armadilha silenciosa que exige filtrar
  por `WHERE data_carga = MAX(data_carga)` antes de agregar; virou métrica
  verificada em `metrics.yaml`.
- **T48-1** — `eu_sanctions.sanctions` e `un_sanctions.sanctions` não têm
  nenhuma linha ligada ao Brasil (0 de 42.347 e 0 de 1.002, checado em
  todo campo de país/nacionalidade/texto livre); `global_ofac_sanctions.sanctions`
  não tem coluna de país/CNPJ/CPF estruturada nenhuma — só 20 de 19.129
  linhas mencionam "Brazil", todas em `remarks` de texto livre, sem CNPJ
  (0 ocorrências) nem CPF real (1 falso positivo). Estrutural: as três
  listas simplesmente não cobrem o Brasil como alvo.
- **T48-3** — `global_icij_offshoreleaks.officers` (pessoa física) não tem
  CPF — cruzamento por nome contra `br_me_cnpj.socios.nome` produz alto
  volume (2.293 de 4.025 nomes casam) mas com colisão massiva em nomes
  comuns (ex. "ROBERTO RESTUM" casa 944 sócios), não confiável para
  identificar beneficiário final sem uma segunda chave (CPF, data de
  nascimento) que o ICIJ não expõe.
- **T51** — `br_me_exportadoras_importadoras` (dataset inteiro) só tem a
  tabela `dicionario` no beelink (3 linhas) — **sem a tabela de
  microdados `empresas_exportadoras_importadoras`** que o próprio
  dicionário referencia (confirmado na view DuckDB e no disco: só a pasta
  `dicionario/` existe). Mesmo padrão exato de `br_mec_prouni` (T46-1).
  Precisa de re-scraping.
- **T53-5, correlato de T33-2…T33-5** — `world_oecd_public_finance.country`:
  as colunas de despesa/receita agregada (`total_expenditure`,
  `total_receipt`, `expenditure_health`, `expenditure_education`) trazem
  o sentinel de overflow `INT32_MIN` (-2147483648) em 82%-98,5% das
  linhas aparentemente preenchidas (só 20 de 1.319 valores de
  `total_expenditure` são reais). Bloqueia qualquer benchmark
  internacional de gasto público em saúde/educação até reprocessamento
  na fonte. Resposta direta sobre desbloquear T33-2…T33-5: `world_wb_mides`
  **não desbloqueia nada** — é dado municipal brasileiro mal rotulado
  (ver achado abaixo), zero linha internacional; `world_oecd_public_finance`
  desbloqueia parcialmente só o ângulo "benchmark contra a OCDE" (nunca
  "países vizinhos" — o Brasil não está na lista de 36 países, e os
  únicos latino-americanos são México e Chile), e só nas colunas não
  corrompidas pelo sentinel (PIB, desemprego, expectativa de vida, Gini,
  WGI de governança 2010-2016).
- **`world_wb_mides` não é o dataset que o nome diz** — confirmado ao ler
  os dados: as 9 tabelas (`empenho`, `licitacao`, `licitacao_item`,
  `licitacao_participante`, `liquidacao`, `pagamento`,
  `orgao_unidade_gestora`, `relacionamentos`, `dicionario`) são
  empenho/licitação/pagamento de governos municipais **brasileiros**
  (colunas `id_municipio`, `sigla_uf`, `orgao`) — cobre 10 estados
  brasileiros, 303.323.046 linhas, 1989-2024, zero relação com o World
  Bank Multidimensional Inequality Dataset que o nome sugere. Mesma
  classe de erro de `br_mp_pep` (tema 47) — precisa de
  renomeação/reclassificação no catálogo.
- **T54-3, T54-4** — `br_ibge_censo_demografico.microdados_pessoa_*`: só a
  tabela de **2010** tem `peso_amostral`; 1970/1980/1991/2000 não têm
  coluna de peso alguma — totais populacionais não são reconstituíveis
  para esses 4 anos a partir do microdado, só proporções não-ponderadas
  (viés desconhecido). A variável "sabe ler e escrever" só existe
  decodificada no `dicionario` para 1991 (`v0323`) e 2000 (`v0428`) — uma
  série completa de alfabetização 1970-2010 não é possível com o que está
  espelhado hoje.
- **T54-2 / geral** — qualquer série histórica municipal 1970/1980→hoje
  via join direto em `id_municipio` perde silenciosamente ~30% dos
  municípios atuais (criados depois), e mesmo os pares que casam misturam
  território que se emancipou depois — precisaria de tabela de
  correspondência município-pai→filho (não existe no espelho).
- **T55 / `br_fipe_veiculos`** — a única tabela do dataset (`precos`,
  11.289 linhas) não tem preço, ano nem geografia: só
  `vehicle_type`/`brand_code`/`brand_name`/`model_code`/`model_name`. É
  um catálogo de marca/modelo, não uma série de preços FIPE apesar do
  nome. Precisaria de re-scraping trazendo a série de valores mensais.
- **T55 / `br_anvisa_medicamentos_industrializados.microdados`** — a
  tabela tem exatamente 10.000.000 de linhas, e os 406 municípios
  presentes estão todos concentrados no começo do alfabeto (de "Águas
  Frias" a "Áurea") — SP, RJ, BH, Salvador, Curitiba e Fortaleza têm zero
  linhas. Consistente com scrape processado em ordem alfabética, cortado
  ao bater o teto de 10M — não é amostra aleatória. Comparações entre
  substâncias sofrem menos que comparações entre municípios, que ficam
  inteiramente inválidas sem re-scraping completo.
- **T55 / `br_ggb_relatorio_lgbtqi`** — dataset inteiro (5 tabelas) é
  100% agregado nacional por ano; nenhuma tabela tem UF, região ou
  município. Qualquer pergunta de correlação geográfica está
  estruturalmente bloqueada.
- **Tema 41 (CMED/Farmácia Popular)** — parcialmente desbloqueado com
  ressalva: `br_anvisa_cmed.precos` existe e tem preço regulado real
  (51.140 linhas, 2.246 substâncias) mas é snapshot único atual, sem
  série histórica — T41-4 ("ficaram mais baratos depois do Farmácia
  Popular") continua bloqueada por falta de série temporal.
  `br_saude_farmaciapopular.estabelecimentos` só tem localização de
  farmácia credenciada, nenhuma coluna de preço praticado ou medicamento
  vendido — T41-1/T41-4 seguem bloqueadas mesmo com o CMED disponível.
- **T50-4 (CNJ recursos_financeiros — bug novo)** —
  `br_cnj_estatisticas_poder_judiciario.recursos_financeiros.gastos_totais`
  (e outras colunas de despesa absoluta) contém valores implausíveis e,
  no ramo Eleitoral, **duplicados**: em 2014 as 28 linhas de tribunal
  (TRE-AC…TRE-SP + a linha agregada "TRE") têm o MESMO `gastos_totais` =
  R$2.268.768.427.050 (2,27 trilhões) — um `SUM()` por tribunal infla
  28x, e o valor unitário já é absurdo por si só. No ramo Estadual não há
  duplicação, mas os valores também não fecham: TJSP registra
  `despesa_rh` = R$739 bilhões em 2014, MAIOR que seu próprio
  `gastos_totais` (R$209,8 bilhões) no mesmo ano. T39-1 não foi afetado
  porque usou proporção (`despesa_pessoal`/`despesa_total`), que cancela
  o fator de escala comum — qualquer uso futuro de valor absoluto de
  despesa nessa tabela precisa reprocessar a fonte do CNJ antes de
  confiar no número.
- **br_mjsp_ckan.procon** — cobre só 7 de 27 UFs (CE, GO, SP, PE, SC, PB,
  MT), com Ceará sozinho respondendo por 51% das reclamações — provável
  scrape incompleto, não litigiosidade real.
- **br_mjsp_ckan.infopen** — mesma classe de bug já catalogada para
  SISDEPEN em T06-1/T06-4: nomes de coluna com unicode inválido, impede
  até um `SELECT *`. Precisa re-scraping.
- **br_mjsp_procurados.procurados** — só 195 linhas, sem CPF nem ID
  numérico (nome+estado em texto livre) — não sustenta cruzamento de 3+
  datasets além de contagem trivial por UF. Não é dado quebrado, é
  escopo pequeno por natureza.
- **br_stf_corte_aberta.decisoes** — sem nenhuma chave geográfica (nem
  UF, nem município) — grão processo/decisão, só `ano` é utilizável para
  série temporal. Qualquer pergunta "por estado/município" sobre o STF
  está estruturalmente bloqueada com o que está espelhado hoje.

Confirmado durante esta rodada (não estava listado como bloqueio antes):

- **T20-1, T20-2** (bolsas CNPq por *município de origem*) — `br_cnpq_bolsas.microdados`
  só tem `sigla_uf_origem` (estado), não município de origem; o único município
  disponível é `municipio_destino` (onde fica a instituição que recebe o bolsista).
  Respondido em nível de UF em vez de município (ver seção 20 acima) — para
  responder no recorte municipal original seria preciso outra fonte com a
  naturalidade/origem municipal do bolsista.

Confirmado em 2026-08-25 (rodada `respostas_pendentes.md`, temas 39-40):

- **T39-2, T39-3, T39-4** — nenhum dos 4 espelhos de TCE (ES/PI/RJ/SP) tem
  penalidade/multa por município: SP é só nome de município (2 colunas), PI não
  tem tabela de penalidade nenhuma, RJ tem uma (`penalidades_ressarcimento_estado`)
  mas 100% `TipoEnte='ESTADUAL'` (zero linhas municipais), ES tem fiscalização só
  agregada por ano/esfera sem município. Precisaria de scrape novo em pelo menos
  SP e PI antes de qualquer cruzamento com CNJ-improbidade fazer sentido.
- **T39-5** — `br_cnj_estatisticas_poder_judiciario` só tem a tabela `recursos_financeiros`
  (despesa por tribunal/ano); não existe coluna de volume processual, então "custo
  médio por processo" não é calculável com o que está espelhado.
- **T40-4** — falso pressuposto: `br_siop_orcamento` é orçamento da União (por
  órgão/função/ação), não tem despesa obrigatória por orçamento municipal — essa
  métrica vive no SICONFI (`br_me_siconfi`), não no SIOP.

Não investigados nesta rodada (fora do orçamento desta passada, permanecem `⏳`
sem reclassificação): temas 13, 15, 16, 21, 22 (itens 2-4), 23, 24, 26, 28, 29
(exceto os já ◐), 30 (itens 2-5), 31 (itens 1-3 e 5), 32 (itens 2 e 4), 34, 35
(itens 1-4), 37 (itens 2-4), 38, 41 (itens 1-4), 42, 43 (itens 1,2,4,5), M1-M5.
T40-5 segue `⏳` mas por bloqueio já mapeado acima (CAPAG sem série temporal),
não por falta de investigação. A maioria dos temas restantes já vem
autodescrita no arquivo como "pipeline dedicado" (tabelas de centenas de
milhões/bilhões de linhas, funções espaciais do geobr, encadeamento CPF/CNPJ
multi-tabela) — plausível que uma fração precise de re-scraping ou chave nova
como os itens acima, mas isso não foi verificado tabela por tabela.
