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

> ⚠️ `bun harness/casos.ts` marca T02-1…T02-4 como suspeitos: cada gabarito casa
> por palavra-chave com mais de uma pergunta de `perguntas.md` (IDEB, ENEM, PIB e
> INSE aparecem nas 4). O emparelhamento numeração↔conteúdo aqui não está
> confirmado — revisão humana pendente (ver T05 em 2026-09-01 para um caso onde a
> numeração de fato estava errada). Não usar este bloco para avaliação automática
> até resolver.

- **T02-1 ✅** IDEB × ENEM: **r = +0,45 (n=1.657)**; PIB pc × ENEM só +0,185 e rendimento × ENEM +0,168 — aprendizado explica mais que renda. *(A7)*
- **T02-2 ✅** INSE × ENEM/IDEB (município, n=2.254): **INSE × redação +0,27; INSE × IDEB AF +0,14**; controlando INSE, IDEB × ENEM cai de +0,20 para **+0,17** — o nível socioeconômico explica o desempenho tanto quanto (ou mais que) o fluxo medido pelo IDEB.
- **T02-3 ✅** Rural × urbano no ENEM 2022: nos 491 municípios com os dois pares comparáveis, escolas rurais ficam **~32 pontos atrás na redação**; a defasagem é maior no tercil mais pobre (**37,2**) que no mais rico (**32,3**).
- **T02-4 ✅** Participação no ENEM (presentes/pop 15–24, n=2.254): média 1,1%; **× IDEB AF +0,315**, × nota do próprio município +0,13, × PIB pc −0,005 — participação acompanha aprendizado, não renda.
- **T02-5 ✅** ΔIDEB 2017→2021 × Δln PIB pc: **r = −0,07 (n=4.739)** — evolução do IDEB não segue ciclos econômicos municipais.

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
- **T05-2 ⏳ (bloqueio parcial removido, pergunta ainda não respondida)** O Senado passou a ter `processo`/`votacao_parlamentar`/`relatoria` (ver "Desbloqueio registrado" em `achados_fortes.md`) — mas `processo` não tem coluna de tema/área estruturada, só `ementa` (texto livre) e `autoria` (texto livre, não FK limpa para senador). A pergunta ("proposições alinhadas ao perfil econômico do estado que elegeu o senador") precisaria de classificação da `ementa` por palavra-chave ou de usar `relatoria`/comissão como proxy de área — nenhum dos dois foi tentado. Continua sem resposta, mas por falta de classificação, não de tabela.
- **T05-3 ✅** Ocupação declarada × eleição 2022 (dep. federal/senador): deputados na reeleição **58,8%**, engenheiros 7,8%, médicos 6,5% vs **empresários 3,9%** (n=1.229 candidatos) — abaixo da média (~5%), empresário não é profissão que elege.
- **T05-4 ◐** Fragmentação partidária municipal 2022: nº efetivo de partidos médio **5,6** (n=3.035); × PIB pc **+0,21**; AP mais fragmentado, PI menos. Comparação com votações nominais da Câmara pendente.
- **T05-5 ✅** Gasto por voto × transferências voluntárias (UF, n=27): **r = +0,92** — mas é estrutural: UFs pequenas (RR R$144/voto, 749 transf pc) têm campanha cara por eleitor E recebem mais transferência per capita; ambas as séries escalam com o tamanho do eleitorado.

## 06 · Crime

- **T06-1 ✅ (2026-09-05) — SISDEPEN destravado, e a resposta é não.** O bloqueio anterior ("corrompido") era de leitura, não de dado: `br_mjsp_sisdepen.populacao_carceraria` traz a UF por **extenso com a sigla entre parênteses** (`"Minas Gerais (MG)"`), então agrupar por `uf` cru gera 59 categorias e some com tudo. Com `regexp_extract(uf,'\(([A-Z]{2})\)',1)` e a soma das 24 colunas `q_4_1_*_populacao_prisional_*`, saem **575.622 presos em 27 UFs**. Encarceramento por 100 mil habitantes: mediana **241**; **SP 484, RO 481, MS 476, DF 471, AC 420** no topo. **A relação com a queda de homicídios entre 2015 e 2021 é nula: r = −0,02.** Encarcerar mais não previu queda maior. O que a taxa de encarceramento acompanha é riqueza (**r = +0,52 com PIB per capita**, −0,47 com cobertura do Bolsa Família): estado rico prende mais, e prende mais porque tem estrutura para prender. A queda nacional de homicídios no período foi de **−21,6%**, e os campeões de queda (DF −49,5%, GO −45,1%, MG −43,4%, SP −42,1%) têm taxas de encarceramento de 188 a 484 — toda a faixa. **Ressalva de cobertura**: o preenchimento do SISDEPEN é desigual (BA aparece com 84 presos/100k, implausível — a Bahia real está acima de 200), então a leitura vale para o padrão geral, não para o número de cada UF.
- **T06-2 ✅** ISP-RJ × SIM (homicídios dolosos × agressões, 2019–23, n=92 municípios ≥30 mil hab): **r = +0,81 em log-taxa** — as duas fontes contam a mesma violência; divergências ficam nos municípios pequenos.
- **T06-3 ✅** Especialização CNAE (HHI) × homicídio: bruto **+0,16**; controlando PIB pc **−0,04 (n=1.604)** — dependência de um único setor não prevê homicídio.
- **T06-4 ✅ (2026-09-05) — nem prisão, nem pobreza: é política de polícia.** Mortes por intervenção legal (SIM, CID Y35, 2019–21): mediana **abaixo de 0,5/100 mil hab/ano**, mas com dispersão extrema — **AP 7,18, BA 4,44, RJ 3,20, PR 2,02, GO 2,25** contra AC 0,00, PE 0,03 e MG 0,09. Contra o tamanho do sistema prisional: **r = −0,09 — nada**. Contra a renda: **+0,41** (perverso, mas é composição). Contra a própria taxa de homicídio: **−0,07 — nada**. Medindo pela **fatia da letalidade total que é policial**, o retrato fica mais nítido ainda: **AP 13,0% e RJ 12,7% de todos os homicídios do estado são mortes por intervenção policial**, contra 0,6% em Sergipe e 0,7% em Minas — uma diferença de **20 vezes** entre UFs. Letalidade policial não é resposta a violência nem a encarceramento; é doutrina de corporação.
- **T06-5 ◐** Fronteiras/portos/capitais dos 12 municípios de fronteira internacional + portos principais: taxa de homicídio **82,7/100k vs 61,9** nos demais (n=3.293) — concentração ~34% acima da média; correlação com % transporte (RAIS) saiu indeterminada (NaN).

## 07 · Economia e Crédito

- **T07-2 ✅** Agências/100k × PIB pc: **r = +0,12 (n=2.466, ≥20 mil hab) — presença bancária quase não discrimina renda municipal**. *(A15)*
- **T07-1 ✅** Captação de crédito rural (SICOR 2022, via `recurso_publico_complemento_operacao`) × PIB agropecuário e rebanho (município): **r = +0,74 com VA agropecuário; +0,30 com rebanho (PPM)** (n=5.503) — crédito rural segue a renda agro do município mais de perto do que o tamanho do rebanho.
- **T07-3 ✅ (2026-09-05) — bloqueio destravado.** Não é preciso ligar tomador ao imóvel: o `id_car` do SICOR já traz o código IBGE embutido nas posições 3–9 (ver T17-2). Crédito rural 2020–24 mapeado em **5.564 municípios, R$ 934,9 bi**. O crédito se concentra onde há mais área cadastrada (**r = +0,45**, parcial **+0,54**) e sobretudo onde há mais valor agropecuário (**+0,77**), mas alcança só **2,2% dos imóveis do CAR** no município mediano — concentração alta e uniforme, não um fenômeno dos municípios de maior PIB agro.
- **T07-5 ◐ (2026-09-05)** A parte fundiária está respondida acima (concentração de 2,2% dos imóveis, sem relação com o tamanho médio do imóvel). O cruzamento com uso do solo do MapBiomas segue não montado — a tabela municipal do MapBiomas espelhada é de transição de-para, não de estoque de cobertura por município.
- **T07-4 ✅ (2026-08-27)** Municípios que tinham ≥1 agência ESTBAN em dez/2014 (n=3.646): comparando os que **perderam** agências até dez/2022 (n=1.970) vs os que mantiveram/ganharam (n=1.676) — crescimento nominal do PIB municipal 2014→2021 quase igual entre os grupos (77,1% vs 83,2%). Correlação bruta entre "perdeu agência" (binário) e crescimento do PIB: **r = −0,035**; controlando por ln(população) via correlação parcial: **r ≈ −0,024 (n=3.646)** — praticamente nulo. Perder agência bancária não prediz crescimento de PIB municipal inferior, mesma UF/porte controlado.

## 08 · Políticas Públicas

- **T08-1 ✅** Benefícios (BF jun/23) × gasto assistencial (SICONFI 2022 pago): **r = −0,08 (n=3.053)** — quem tem mais beneficiários não gasta mais em assistência social per capita (média R$ 159/hab); gasto saúde até negativo com benefícios (−0,22).
- **T08-2 ◐** Cobertura × pobreza: benefícios seguem vulnerabilidade medida por escolaridade materna (+0,57, T03-5), mas o Censo 2022 do espelho não tem renda/domicílio para medir pobreza diretamente.
- **T08-3 ✅** Arrecadação própria × dependência de benefícios: **r = −0,44 bruto (n=3.055); controlando PIB pc −0,07** — municípios que arrecadam menos dependem mais de BF, mas o efeito é todo capturado pela renda.
- **T08-4 ✅** Gasto em saúde × mortalidade infantil: **r = −0,12 (n=1.411)** — gasto municipal per capita quase não discrimina TMI; resultado depende de fatores fora do orçamento local.
- **T08-5 ✅ (2026-09-05, sem o SIOP) — o município não compensa nem duplica: ele ignora.** O SIOP é orçamento da União (bloqueio já mapeado em T40-4), então o teste usa o SICONFI municipal 2023 (5.356 municípios com despesa por função). **A assistência social é 3,51% da despesa paga do município mediano** — e essa fatia **não tem relação nenhuma com a demanda social local**: × cobertura do Novo Bolsa Família **r = +0,02**, × cobertura do Gás do Povo **−0,05**, × PIB per capita **+0,05**, × pendências no CAUC **+0,05**. Todas abaixo de |0,06|. **Onde o repasse federal direto ao cidadão é maior, o município não gasta mais nem menos em assistência social — gasta o mesmo.** A despesa municipal per capita, essa sim, é fortemente explicada por porte (**−0,67 com população**) e renda (+0,42): é escala, não política social. O único sinal positivo relevante é com convênio recebido per capita (+0,17), o que sugere que a assistência social municipal é, na margem, financiada por transferência voluntária e não por decisão orçamentária própria.

## 09 · Gênero

- **T09-2 ✅ (parcial)** Cesárea × renda municipal: **+0,24**; × rendimento médio +0,19 (n=3.853) — parto cirúrgico cresce com renda local. *(A12)*
- **T09-1 ✅** Feminização do emprego formal (RAIS 2022) × notificações de violência (SINAN violência 2019+2021): **r = −0,06 (n=1.668 municípios)** — nenhuma relação; notificações medem estrutura de atendimento, não violência bruta.
- **T09-3 ◐** Mulheres nas admissões (CAGED 2021): **35,7% do total vs 37,0% nos 4 setores de maior salário** — entrada feminina nos setores ricos já é proporcional; o gargalo não está na porta de entrada.
- **T09-4 ◐** Coberto por T03-4: RMM média 91,9/100 mil NV (21 UFs), r = +0,31 com salas de parto (alocação reativa), −0,50 com PIB pc.
- **T09-5 ✅ (reformulado, 2026-09-05) — a lacuna salarial de gênero é fenômeno de município RICO.** Chefia de domicílio por sexo segue ausente do Censo 2022 espelhado, mas a segunda metade da pergunta — rendimento formal feminino vs masculino por município — é respondível e produz o achado forte. RAIS 2022, 5.404 municípios com ≥100 vínculos de cada sexo: a lacuna mediana (1 − fem/masc) é de apenas **5,8%**, e **em 2.114 municípios (39,1%) a mulher formal ganha MAIS que o homem**. Mas a lacuna cresce com a riqueza: **r = +0,61 com PIB per capita, +0,59 com formalização, −0,55 com cobertura do Bolsa Família**. Por UF: **SC 22,6%, RS 18,3%, PR 17,4%, MS 17,3%** contra **SE −14,7%, PB −12,0%, PE −9,4%, RN −8,9%** (mulher ganha mais). A explicação é composição: no município pobre o emprego formal feminino é professora, enfermeira e servidora — qualificado —, enquanto o masculino é braçal; no município rico há indústria e gerência masculinas para abrir a distância. **Ler a lacuna salarial como "onde a mulher está pior" inverte o mapa da desigualdade de renda.**
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
- **T12-3 ✅ / T12-5 ✅** Dupla desvantagem × rotatividade setorial (CAGED 2021): **r = +0,04 com lacuna mulher-negra; +0,19 com lacuna de gênero; −0,33 com lacuna racial** — setores de alta rotatividade não concentram as maiores desigualdades; para raça o sinal até inverte.
- **T12-2 ✅** % mães pretas/pardas (SINASC 2022, por município de residência, n≥30 nascimentos) × leitos obstétricos SUS por 1.000 nascidos (CNES 2022) × PIB pc: **r = +0,02 com leitos (praticamente nulo, n=3.052); r = −0,26 com PIB pc** — a composição racial das mães não se associa à oferta de leito obstétrico, mas municípios com mais mães pretas/pardas são sistematicamente mais pobres.
- **T12-4 ◐ (2026-09-05)** Chefia feminina segue indisponível no Censo 2022 do espelho. O par restante foi medido: mortalidade feminina precoce (SIM, 20–59 anos, 2020–22) × rendimento formal feminino dá **r = −0,05 — nada**; × lacuna salarial de gênero **+0,12**; × PIB per capita **+0,20** (positivo, artefato de registro, mesmo padrão de T22-2/T42-5). **A dupla desvantagem que a pergunta procura não aparece**: os municípios de menor rendimento feminino não são os de maior mortalidade feminina precoce.

## 13 · Migração

- **T13-2 ✅** Saldo de movimentação CAGED 2022 (proxy de atração de trabalhadores) × PIB pc 2021, e % de admissões em construção civil (CNAE seção F) × PIB pc, mesmo recorte (n=5.042 municípios com ≥30 admissões): **r = +0,05 com saldo; r = −0,03 com % construção** — nem atração líquida de vínculos nem boom da construção acompanham a renda municipal.
- **T13-1 ✅ (proxy, 2026-09-05)** O CAGED segue sem par origem→destino, mas o saldo líquido de vínculos responde a pergunta na substância. Saldo CAGED 2019–22 relativo à população de 2010 × crescimento populacional 2010→2022 (n=5.564): **r = +0,37**. Emprego formal e população crescem juntos, com folga grande. O pano de fundo é mais duro que a correlação: **2.393 dos 5.565 municípios (43%) PERDERAM população entre os censos**. E o saldo de vínculos acompanha muito mais a renda (**+0,57 com PIB per capita**) que o crescimento populacional acompanha (**+0,18**) — o emprego se concentra onde já há dinheiro; a população, nem tanto.
- **T13-3 ◐ — e um aviso de dado (2026-09-05).** O par origem→destino existe, mas **na RAIS, não no CAGED**: `microdados_vinculos` tem `id_municipio` (do estabelecimento, consistente com a partição de UF) e `id_municipio_trabalho` (nacional). Em 2022, **13,67 milhões de vínculos ativos têm os dois diferentes**, em 86.119 pares. Da matriz: **58,6% dos deslocamentos ficam dentro da mesma região imediata do IBGE** e **84,8% dentro da mesma UF** — a hierarquia urbana de fato contém quase todo o movimento, que é a resposta à pergunta. **Mas o saldo líquido não é migração e não deve ser lido como tal**: São Paulo aparece com **−1.072.060** de saldo, Rio com −383.321 e Belo Horizonte com −342.765, enquanto São Gonçalo/RJ (+96.625) e Carapicuíba/SP (+91.665) lideram os receptores. Ninguém acredita que um milhão de pessoas a mais saiam de São Paulo para trabalhar fora do que entram. **O par mede sede-do-estabelecimento × local-de-trabalho — é matriz→filial, não residência→emprego.** Usar `id_municipio_trabalho` como origem-destino de pessoa é erro; a estrutura de proximidade (os 58,6%) sobrevive porque filial fica perto da matriz, o saldo não sobrevive.
- **T13-4 ◐ (2026-09-05)** Sem par origem→destino de pessoa (ver acima), "exportador vs receptor" fica sem definição limpa. O que se mede: dos 2.393 municípios que perderam população, o saldo de vínculos é sistematicamente pior, e a associação renda↔emprego (+0,57) é 3× a associação renda↔população (+0,18) — consistente com esvaziamento demográfico de município pobre sem que o emprego formal o acompanhe na mesma proporção.
- **T13-5 ❌ **SEM RESPOSTA** — bloqueio estrutural confirmado (2026-09-05).** Nem o CAGED nem a RAIS têm par origem→destino **de pessoa**: o CAGED registra só o município do estabelecimento, e o par da RAIS é sede-do-estabelecimento × local-de-trabalho, não residência → emprego (ver o aviso em T13-3). Sem que um dos lados seja domicílio, a antecipação temporal que a pergunta pede não é construível com o espelho atual.

## 14 · Consumo

- **T14-1 ✅** Dispersão de preço da gasolina por município (ANP 2023, CV = desvio/média) × número de postos concorrentes × PIB pc: **r = +0,29 com concorrência (n=461, municípios com ≥5 coletas); r = +0,07 com PIB pc** — mais postos concorrentes correlaciona com MAIS dispersão de preço, não menos (provável efeito de tamanho de cidade: mais postos = mais bairros/perfis de preço, não mercado mais competitivo/uniforme); renda não discrimina.
- **T14-2 ✅ (UF, n pequeno)** IPCA alimentação 12 meses (por região metropolitana, 2023) × preço médio da gasolina (ANP) × renda média (POF 2017), por UF: **r = +0,18 com ANP; r = −0,11 com renda POF** (n=10 UFs com RM no IPCA) — correlações fracas e n pequeno, porque o IPCA regional só cobre as principais regiões metropolitanas, não as 27 UFs.
- **T14-3 ❌ **SEM RESPOSTA**** Segue pendente: exige casar categorias de despesa da POF com categorias do IPCA — trabalho de classificação (crosswalk COICOP), não join.
- **T14-4 ◐ (2026-09-05, reformulado)** Sem coordenadas de distribuidora, o teste possível é preço × estrutura local. Com dados 2025–26 (**422 municípios cobertos pela coleta da ANP**, 416 com ≥5 postos, gasolina comum mediana **R$ 6,35**): **preço × PIB per capita = −0,21** e **× cobertura do Bolsa Família = +0,23** — **a gasolina é mais cara no município pobre**, não mais barata. E não é concorrência: preço × postos por 100 mil habitantes dá **+0,02**, exatamente nada. O que a lista de extremos mostra é logística pura: **Parintins/AM R$ 8,39, Cruzeiro do Sul/AC R$ 8,09, Rio Branco/AC R$ 7,45** contra **Goiatuba/GO R$ 5,76 e São Luís/MA R$ 5,79** — R$ 2,63 de diferença, 45%, entre uma cidade sem estrada e um porto. O preço da gasolina no Brasil é função de distância da refinaria/porto, e o pobre paga a conta do frete.
- **T14-5 ◐ (2026-09-05, com aviso de cobertura)** **A coleta de preços da ANP cobre apenas 422 dos 5.570 municípios (7,6%)** — é uma pesquisa de capitais e cidades médias, não um censo. Qualquer afirmação de "consumo por município" a partir dela herda esse recorte. Dentro dele, a dispersão de preços entre postos (CV mediano 4,5%) é **maior nos municípios pobres** (**+0,24 com Bolsa Família, −0,22 com PIB per capita, −0,24 com ticket médio do Pix**) e **não cai com mais concorrentes por habitante** (−0,12). Isso **corrige a leitura de T14-1** feita com dados de 2023: o sinal com concorrência era com o número absoluto de postos (+0,15, que é tamanho de cidade); normalizado por população, o efeito da concorrência desaparece e o que sobra é pobreza.

## 15 · Poder e Elites

- **T15-1 ◐** Patrimônio dos eleitos medido (R$ 3,12 mi médio); autoria Câmara pendente.
- **T15-3 ✅** Recorrência de sobrenome entre vereadores eleitos (TSE 2016+2020, mesmo município) × PIB pc: **r = −0,18 (n=5.568 municípios com ≥5 eleitos nas duas eleições)** — sobrenome repetido entre eleitos é levemente MAIS comum em municípios mais pobres, não mais ricos; em média **56,4% dos vereadores eleitos** dividem sobrenome com outro eleito do mesmo município nas duas eleições.
- **T15-5 ✅** Razão patrimônio médio do deputado federal eleito (TSE 2022, por UF) / PIB pc da UF (proxy de renda do eleitorado — Censo 2022 não tem renda) × emendas parlamentares pagas por UF (CGU, 2023+): **r = +0,02 (n=27 UFs)** — a razão patrimônio/renda do eleito não prevê quanto a UF recebe em emendas.
- **T15-2 ✅ (2026-09-05, com a data como resposta)** A pergunta pressupõe doação empresarial, que o STF proibiu em 2015. O teste correto é sobre o **último ciclo em que ela existiu**: **18.230 CNPJ doaram R$ 3,52 bilhões em 2014**. Desses, **1.946 (10,7%) aparecem como fornecedor no PNCP** e **1.101 (6,0%) venceram licitação federal desde 2020** — dez anos depois. E há gradiente por tamanho da doação, mas fraco e monotônico: do quintil que menos doou ao que mais doou, a presença no PNCP vai de **9,7% para 12,1%** e na licitação de **5,2% para 7,6%**. Quem doou mais em 2014 aparece mais como fornecedor uma década depois, mas o efeito é de ~2,5 pontos percentuais, não de ordem de grandeza. *(A parte sobre "candidatos empresários eleitos mais vezes" já foi respondida em T05-3: empresário é 3,9% dos candidatos e está abaixo da média de sucesso.)*
- **T15-4 ✅ (2026-09-05)** Doadores recorrentes (CNPJ que doou em 2+ dos ciclos 2018/2020/2022/2024): **1.812 de 40.909 doadores PJ**, R$ 19,26 bi no total. A recorrência **triplica** a chance de receber cartão corporativo (**0,22% contra 0,07%**) e mais que dobra a de vencer licitação (**0,55% contra 0,24%**). Mas as taxas absolutas são ínfimas — e o motivo é estrutural: **depois de 2015 o "doador CNPJ" é quase inteiramente partido, comitê e candidato (CNPJ de campanha), não empresa**. Em 2022, R$ 6,63 bi de receita declarada tem "outros recursos" e fundos públicos como fonte dominante. A pergunta, na forma em que foi feita, só tem resposta empírica no regime pré-2015 — ver T15-2.

## 16 · Economia Política

- **T16-1 ✅** % da arrecadação federal nacional (soma de tributos, RF 2021) × % do PIB nacional, por UF: **SP arrecada 38,1% do total contra 30,2% do PIB (gap +7,9pp); RJ +7,0pp; DF +4,1pp** — só essas 3 UFs arrecadam acima do seu peso no PIB; as outras 24 arrecadam abaixo, MG é o maior gap negativo (−2,8pp) — consistente com sede fiscal de empresas concentrada em SP/RJ/DF independente de onde a atividade ocorre.
- **T16-3 ✅** % de II+IE (imposto de importação+exportação) na arrecadação total (RF 2021, UF) × % do PIB em valor agropecuário: **r = −0,32 (n=27 UFs)** — UFs mais dependentes de II/IE têm proporcionalmente MENOS peso agro no PIB, não mais; II/IE segue porto/indústria, não produção primária.
- **T16-4 ✅ (dado escasso, ressalva forte)** Arrecadação total (RF 2020, UF) × transferências voluntárias empenhadas (Transferegov, UF recebedora): **r = +0,88 (n=27 UFs)** — mas `br_transferegov.transferencias` só tem 2019-2020 no espelho (4.248 linhas no total do Brasil), claramente incompleto frente ao volume real de transferências voluntárias; tratar como indício de que ambas escalam com o tamanho da UF, não como medida confiável de direcionamento político.
- **T16-2, T16-5 ⏳** Pendentes — bloqueio de dado: `br_rf_arrecadacao` não tem arrecadação em nível de município (só UF, CNAE nacional, natureza jurídica nacional, e ITR que é só imposto rural); sem arrecadação municipal não dá pra medir volatilidade (T16-2) nem arrecadação per capita por município (T16-5).

## 17 · Agropecuária

- **T17-1 ✅ (parcial)** Rebanho × crédito SICOR 2022: **r = +0,57 (n=5.423; R$ 127,5 bi creditados)** — pecuária puxa crédito; % de área em imóveis gigantes × crédito por bovino **−0,16**. *(A2)*
- **T17-2 ✅ (2026-09-05) — e o join foi destravado.** `br_bcb_sicor.recurso_publico_propriedade.id_car` tem **41 caracteres no formato `UF(2) + código IBGE(7) + hash(32)`** — o município está embutido no próprio identificador, e `substr(id_car,3,7)` o extrai sem precisar de join com o SICAR. Isso **resolve o bloqueio de T17-2, T07-3 e T07-5 de uma vez**: 12.542.973 de 12.542.997 registros (99,9998%) têm código IBGE válido. Com ele, o crédito rural 2020–24 é mapeável em **5.564 municípios, R$ 934,9 bilhões**. Sobre a concentração: a mediana municipal é de **apenas 2,2% dos imóveis do CAR com alguma operação de crédito** — e a fatia financiada **não é maior nos municípios de imóvel grande** (× área total do CAR **−0,07**, × rebanho **−0,07**). O crédito rural formal alcança uma minoria estreita dos imóveis em todo lugar; onde há mais imóvel gigante ele não alcança proporcionalmente mais.
- **T17-3 ✅ (2026-09-05, sem o TRASE) — o achado clássico, qualificado.** Com o crédito agora municipalizado (ver T17-2), crédito rural 2020–24 × desmatamento acumulado (PRODES): **r = +0,58 bruto e +0,64 parcial** (controlando população, PIB per capita e UF) — a relação "onde há mais crédito rural há mais desmatamento" **se confirma e fica mais forte depois dos controles**. Ela sobrevive até ao controle pela escala do agro: incluindo a área cadastrada do CAR entre os controles, o coeficiente cai mas permanece em **+0,39**. **Mas o crédito está no desmate consolidado, não na frente ativa**: contra o alerta DETER recente, o mesmo controle derruba a correlação de +0,37 para **+0,07**. Leitura: o crédito rural financia terra já aberta, não a abertura corrente — o que muda a política pública indicada (condicionalidade sobre o passivo, não interdição da fronteira). Os maiores tomadores são o MATOPIBA e o Cerrado, não a Amazônia: **São Desidério/BA R$ 8,50 bi (9.001 km² desmatados), Formosa do Rio Preto/BA R$ 7,94 bi, Jaborandi/BA R$ 5,42 bi, Correntina/BA R$ 3,54 bi, Baixa Grande do Ribeiro/PI R$ 3,40 bi e Rio Verde/GO R$ 3,01 bi**. O TRASE segue sem chave municipal — a cadeia de exportação por commodity não entrou.
- **T17-4 ✅** CAR pendente × crédito: bruto +0,00; controlando rebanho **−0,12 (n=5.417)** — pendência custa pouco crédito formal, mas custa.
- **T17-5 ✅ (2026-09-05) — produtividade, não escala.** Com o crédito por município (T17-2) e a área do CAR: **VA agropecuário por hectare cadastrado × crédito por hectare = r = +0,73** — a associação mais forte deste tema. E o sinal contra o tamanho é **negativo**: VA agro por hectare × área total do CAR = **−0,45**. Ou seja, **o hectare que recebe mais crédito produz mais valor, e os municípios de maior área cadastrada produzem MENOS por hectare**. Crédito rural está correlacionado com intensificação, não com extensão — o que é o oposto da leitura habitual da relação crédito↔desmate (T17-3), e as duas coisas convivem porque quem tem terra aberta antiga a intensifica com crédito.

## 18 · Comércio Exterior

- **T18-2 ✅ (fato)** Exportações 2023: **69,8% primários (NCM caps. 01–27), US$ 339,7 bi totais** — confirma concentração em commodities.
- **T18-1 ✅** Exportação de manufaturados (COMEX 2023, NCM capítulos 28+, mesma regra de corte usada em T18-2) × vínculos formais na indústria (RAIS 2022, CNAE divisões 10-33): **r = +0,55 (n=1.857 municípios exportadores)** — municípios que exportam mais manufaturados de fato empregam mais na indústria formal, não é só composição de pauta.
- **T18-5 ✅** Valor exportado per capita (COMEX 2023 ÷ população) × PIB per capita (2021): **r = +0,61 (n=2.458 municípios exportadores)** — quanto mais exportação por habitante, maior a renda per capita local; explica uma fração real, não total, da diferença de PIB pc dentro do país.
- **T18-3 ◐ (2026-09-05, corte transversal)** A defasagem temporal ("nos anos seguintes") não foi montada, mas o corte 2021–23 responde a associação. **2.770 municípios registram importação.** Importação per capita × peso da indústria no PIB: **r = +0,51**; × formalização **+0,53**; × PIB per capita **+0,48**. A importação de insumo é o marcador mais nítido de indústria formal no espelho — mais forte que o próprio PIB industrial contra formalidade. A comparação com "vizinhos não importadores" exige a matriz de adjacência (`br_bd_vizinhanca.municipio`, disponível) e não foi montada.
- **T18-4 ✅ (2026-09-05, resposta negativa)** **A concentração exportadora é altíssima e não tem nada a ver com estrutura fundiária.** Nos 1.844 municípios que exportaram mais de US$ 1 milhão em 2021–23, o HHI por SH4 tem **mediana de 0,614** — o município exportador típico depende de um ou dois produtos. Mas contra o tamanho médio do imóvel rural (CAFIR): **r = +0,14**; contra a área total do CAR: **+0,15**; contra o número de imóveis: **+0,02**. O que explica a concentração é o **peso do agro no PIB (+0,37)** — monocultura de commodity, não latifúndio. Município de agro concentrado exporta uma coisa só, tenha ele imóveis grandes ou pequenos.

## 19 · Mercado Financeiro

- **T19-4 ✅ (proxy)** Bancos × crédito: agências × PIB pc fraco (+0,12, A15); SICOR pendente.
- **T19-1 ✅** IBC (Anatel) × agências bancárias/100k hab (ESTBAN 2022) × bolsistas CNPq/100k hab (2022, junção por nome do município de destino): **r = +0,19 com agências; r = +0,13 com bolsistas** (n=342, municípios com bolsista CNPq) — conectividade acompanha um pouco mais a presença bancária do que a presença de bolsistas.
- **T19-3 ✅** Bolsistas CNPq/100k hab × agências ESTBAN/100k hab × PIB pc, mesmo recorte de 342 municípios: **r = +0,04 com densidade bancária; r = −0,05 com PIB pc** — praticamente nenhuma relação; onde há bolsista não é nem mais bancarizado nem mais rico, dentro do universo de municípios que já têm algum bolsista.
- **T19-2 ✅ (2026-09-05) — o crédito rural cresceu 65% mais rápido que a produção, e é fenômeno de município pobre.** Com o crédito municipalizado (T17-2), em 5.222 municípios: o crédito nominal cresceu **2,75× entre 2019 e 2024** enquanto o valor agropecuário do PIB cresceu **1,66× entre 2016 e 2021**. **3.865 municípios (74%) tiveram crédito crescendo acima da produção.** O descolamento — proxy de endividamento relativo — é **maior nos municípios mais pobres** (**r = −0,27 com PIB per capita, +0,12 com cobertura do Bolsa Família**) e **menor onde há mais desmatamento** (−0,10). Contra a perda de agências (ESTBAN 2014→2022): **r = 0,00, exatamente nada** — o endividamento rural relativo não tem relação com a retirada bancária do município. *Aviso de dado obrigatório: `id_car` no SICOR só é preenchido a partir de 2019 (0% até 2017, 3% em 2018, 94,7% em 2019, ~98% depois). Qualquer série municipal de crédito rural anterior a 2019 é impossível por essa via.*
- **T19-5 ✅ (2026-09-05) — a retirada bancária é generalizada, não seletiva.** Dos **3.674 municípios que tinham ao menos um banco no ESTBAN em dez/2014, 1.813 (49,3%) perderam presença até dez/2022 e apenas 103 (2,8%) ganharam.** Metade do Brasil municipal perdeu banco em oito anos. E a saída **não escolhe pelo bolso**: variação do número de instituições × PIB per capita dá **r = −0,08**, × formalização **−0,13**, × Pix per capita **−0,08** — todas desprezíveis e, se algo, ligeiramente *negativas* (saiu-se um pouco mais dos ricos, onde havia mais a fechar). A presença bancária não antecede nem segue o crescimento do PIB municipal: ela recua em bloco, por decisão de rede, e o Pix ocupou o lugar (ver T67-1).

## 20 · Ciência

- **T20-1, T20-2, T20-4 ✅ (UF, não município)** Bolsistas CNPq por UF de origem (2022) × nota média de redação ENEM da UF × PIB pc da UF × população da UF: **r = +0,57 com ENEM; r = +0,69 com PIB pc; r = +0,80 com população** (n=27 UFs) — bolsas seguem fortemente o tamanho populacional e a renda da UF, mais do que corrigem a desigualdade regional (reforço, não correção, respondendo T20-4). Só em nível de UF: a tabela de bolsas só tem UF de origem, não município, então T20-1/T20-2 não puderam ser feitas no recorte municipal que a pergunta original pede.
- **T20-3 ◐ (2026-09-05, direção invertida)** A pergunta supõe escola boa → bolsista depois; o que o dado permite é o corte contemporâneo, e ele mostra co-localização, não fluxo. **Apenas 443 dos 5.571 municípios (8%) recebem bolsa do CNPq** (por município da instituição de destino, 2018+). Neles a média do ENEM redação 2022 é de **636,3 contra 560,0** nos demais — 76 pontos. Mas isso é quase todo porte e renda: população mediana 95.032 contra 10.304, PIB per capita R$ 41.055 contra R$ 23.323. **Dentro do mesmo decil de população a vantagem encolhe e some** — no decil 3 os municípios com bolsa vão *pior* (434,8 × 539,0). A direção causal que a pergunta pede exige coorte de aluno, que o espelho não tem.
- **T20-5 ✅ (2026-09-05)** Municípios sem bolsa e sem instituição de destino têm ENEM redação mediano de **560,0 contra 636,3** dos que têm — mas, controlando o porte, a diferença é de **poucos pontos e muda de sinal entre decis**. **Nos decis mais altos de população a vantagem persiste** (decil 9: 648,1 × 607,5; decil 8: 615,4 × 588,7), nos baixos não. A leitura honesta: **campus universitário acompanha cidade grande e rica, e é isso que a nota do ENEM está captando** — não um efeito local do campus sobre a escola de ensino médio.

## 21 · Corrupção

- **T21-4 ✅** Emendas parlamentares pagas por município (CGU, 2022+) × despesa orçamentária paga total (SICONFI 2023): **r = +0,31 (n=1.423 municípios com emenda>0)**; emendas representam em média só **0,37% da despesa municipal paga** — correlação moderada, sem sinal forte de retenção estadual visível nesse corte, mas o teste é indireto (não segue a emenda específica até a execução, só compara totais agregados).
- **T21-1 ✅ (2026-09-05, sem a parte tributária)** Cartão de pagamento do governo federal 2020+: **54.743 fornecedores PJ, 223.218 transações, R$ 97,0 milhões**. Recorrência é rara e concentrada: só **0,18% dos fornecedores têm 100+ transações, e eles respondem por 14,7% do valor**. A sobreposição com licitação é o achado: **12,0% dos fornecedores de cartão também venceram licitação federal** desde 2020 — mas **entre os recorrentes esse número sobe para 39,8%, mais de três vezes**. Quem vende muito no cartão é quem já é fornecedor licitado; o cartão funciona como canal paralelo do mesmo grupo, não como porta de entrada de novos. A parte tributária (arrecadação proporcional pela RF) segue bloqueada: `br_rf_arrecadacao` não tem grão de empresa nem de CNAE municipal.
- **T21-2 ✅ (2026-09-05) — não, os fornecedores não são "sempre os mesmos".** Cadeia montada pelo SICONV: emenda → proposta → convênio → pagamento a fornecedor. Convênios com emenda parlamentar pagaram **R$ 50,67 bilhões a 90.577 fornecedores distintos em 5.509 municípios**. O HHI de concentração de fornecedor por município é de **0,178 na mediana** — baixo — e o município mediano tem **11 fornecedores distintos** recebendo. **413 municípios (7,5%)** têm um fornecedor com mais de metade do valor. Ou seja: a captura por fornecedor único existe, mas é exceção localizada, não o padrão. Contraste com a concentração da própria mineração (HHI 0,822, T58-4) — o dinheiro de emenda é pulverizado; o da CFEM não.
- **T21-3 ✅ (2026-09-05, sem a parte tributária) — o padrão anormal é a norma.** Das **23.046 licitações federais 2020+ com participantes identificados, 12.686 (55,0%) tiveram um único participante**. Por CNAE do vencedor, a taxa de participante único é: **atividades financeiras (64) 97,1%**, **organizações associativas (94) 91,3%**, **saúde humana (86) 76,3%**, **educação (85) 70,6%**, manutenção/reparação (33) 60,5%, obras (45) 56,9%, TI (62) 56,6% — contra comércio varejista (47) 50,3% e atacadista (46) 40,5%. **Onde o objeto é serviço especializado ou institucional, a licitação é praticamente sempre de um só concorrente; onde é compra de mercadoria, há disputa.** A parte da pergunta sobre arrecadação proporcional na RF segue bloqueada: `br_rf_arrecadacao` não tem grão de empresa nem CNAE municipal (mesmo bloqueio de T16-2, T16-5 e T21-1).
- **T21-5 ❌ **SEM RESPOSTA** — bloqueio de método confirmado (2026-09-05).** O cartão de pagamento descreve a compra em `transacao` (texto livre, sem catálogo) e a licitação em `descricao_item_compra` (texto livre com padrão CATMAT parcial). Não há chave de item comum entre as duas bases, e casar "itens idênticos" por similaridade de texto produziria pares não verificáveis — o tipo de resultado que este arquivo evita. Precisaria de um mapeamento transação→CATMAT que não existe no espelho.

## 22 · Clima

- **T22-1 ✅** Focos de calor 2019–22 × desmatamento: **r = +0,66 (n=5.240 municípios)**; × emissões agro +0,51; × VA agro per capita só +0,10 — o fogo segue o desmate e as emissões, não a renda formal do agro.
- **T22-2 ✅** Óbitos por causa respiratória (SIM 2022, CID J*) per capita × focos de queimada (INPE 2022) per capita, por município: **r = −0,14 (n=5.471)** — fraco e no sentido oposto ao esperado; provável confundimento (municípios de fronteira agrícola com mais queimada tendem a ter população mais jovem/rural, não necessariamente mais mortalidade respiratória registrada) — não confirma a hipótese, mas o teste é agregado anual, não capta o pico mensal que a pergunta original pede.
- **T22-3 ◐** Coberto por T22-1: fogo associado à conversão produtiva (emissões agro +0,51) muito mais que à renda (+0,10) — padrão de uso da terra, não evento natural.

## 23 · Epidemiologia

- **T23-2 ✅ (só dengue, não "doenças infecciosas" em geral)** Letalidade de dengue (SINAN 2022, óbitos/casos por município de residência, `evolucao_caso='2'`) × estabelecimentos CNES per capita (dez/2022): **r = −0,01 (n=2.569 municípios com ≥30 casos)** — praticamente nulo; letalidade de dengue não acompanha densidade de estabelecimentos de saúde. `br_ms_sinan` só tem dengue e influenza/SRAG, não cobre "doenças infecciosas" de modo geral.
- **T23-1 ✅ (2026-09-05) — não há subnotificação de grave; há sobrenotificação de leve.** Dengue: **2.045 municípios com ≥50 notificações em 2022**. A taxa de internação (AIH com CID A90/A91 ÷ casos notificados) é de **2,25% na mediana**, e **não** acompanha a oferta hospitalar (**r = +0,01 com estabelecimentos CNES por 10 mil hab**) nem a renda (+0,03). O único sinal é **−0,20 contra a própria incidência**: quanto mais casos notificados por habitante, **menor** a fração que interna. Isso é o oposto de subnotificação de casos graves — é ampliação da base de notificação leve nos municípios de surto. Onde há epidemia, notifica-se muito caso leve; a internação é aproximadamente constante.
- **T23-3 ✅ (2026-09-05) — o gradiente é de vigilância, não de doença.** Notificação de dengue por 100 mil habitantes: **+0,22 com PIB per capita, −0,21 com cobertura do Bolsa Família, +0,19 com estabelecimentos CNES por habitante**. Notifica-se mais dengue onde há mais dinheiro e mais posto de saúde. A condição socioeconômica explica o gradiente **das notificações** com sinal positivo — o inverso do que a pergunta supõe para a doença. Combinado com T28-1 (violência) e T42-5 (mortalidade respiratória), fecha-se um padrão: **neste espelho, quase toda série de notificação mede capacidade de registro antes de medir fenômeno.**
- **T23-4 ✅ (2026-09-05, via IEPS) — a cobertura vacinal caiu, e não é ela que prevê o óbito.** O SIPNI segue ilegível (view sobre S3 com esquema misto: qualquer leitura aborta com `INTERNAL Error: Unsupported type for NumericValueUnionToValue`, e não há parquet local). Mas o **IEPS (`br_ieps_saude.municipio`) traz cobertura vacinal municipal pronta** — `cob_vac_polio`, `cob_vac_penta`, `cob_vac_tvd1` — e resolve a pergunta. Cobertura de poliomielite: mediana municipal de **80,9%**, com **1.693 municípios (30%) abaixo de 70%**, muito longe da meta de 95%. Contra óbitos por causa infecciosa (SIM 2020–22, CID A00–B99): **r = −0,005 — exatamente zero**. Contra a renda: +0,10. **Baixa cobertura vacinal não prevê excesso de óbito infeccioso no recorte municipal** — o efeito de rebanho e a raridade do desfecho tornam o teste ecológico cego, o que é resultado metodológico, não ausência de risco.
- **T23-5 ✅ (2026-09-05, resposta negativa)** Pré-natal inadequado (SINASC 2022, `pre_natal_agr` em 1–3 consultas): mediana de **4,66% dos nascidos vivos**. Contra a densidade de notificação de dengue (proxy de vigilância): **r = −0,14**; contra estabelecimentos CNES: **−0,25**; contra atenção básica: **−0,08**. Os sinais são fracos e todos na direção esperada, mas **a variável que mais prevê pré-natal inadequado é a pobreza (+0,20 com cobertura do Bolsa Família)**, não a oferta de serviço. A concentração que a pergunta procura — "pior vigilância junto com pior pré-natal" — existe, mas é um efeito de segunda ordem sobre um efeito de renda.

## 24 · Assistência SUS

- **T24-1 ✅** % de AIHs "exportadas" (SIH 2022, `id_municipio_paciente != id_municipio_estabelecimento`) × leitos SUS/hab (CNES dez/2022) × PIB pc: **r = −0,50 com leitos (n=5.570 — quase todo o país); r = −0,07 com PIB pc** — falta de leito local prediz exportação de paciente muito mais que a renda municipal.
- **Achado técnico (vale para qualquer query futura com SIH)**: `br_ms_sih.aihs_reduzidas` usa o código de município do SUS de 6 dígitos (`id_municipio_paciente`/`id_municipio_estabelecimento`, sem dígito verificador), não o `id_municipio` de 7 dígitos do IBGE usado no resto do espelho — juntar direto (como em qualquer outra tabela) dá 0 linhas silenciosamente, sem erro. Precisa passar por `br_bd_diretorios_brasil.municipio.id_municipio_6` primeiro. Ano de 2022 sozinho já tem 12,5M linhas (não bilhões) — uma partição por ano é perfeitamente consultável.
- **T24-4 ✅ (2026-08-27)** Valor pago por AIH de parto normal (SIH 2022, procedimento SIGTAP `310010039`, o mais frequente do ano com 791 mil AIHs) × porte hospitalar (soma de leitos totais no CNES dez/2022), por região: **o valor sobe com o porte em TODAS as 5 regiões** — Nordeste R$493→R$573 (+16%), Norte R$512→R$624 (+22%, a maior diferença), Sudeste R$532→R$581 (+9%), Sul R$549→R$595 (+8%), Centro-Oeste R$553→R$584 (+6%), comparando hospitais pequenos (<50 leitos) a grandes (150+ leitos), mesmo procedimento. n=790.609 AIHs casadas a porte+região (99,9% das 791.058 do procedimento). Achado consistente: hospital maior recebe mais pelo mesmo parto, em todo o país.
- **T24-2 ✅ (2026-09-05) — o IEPS confirma, e o indicador que confirma é a saúde privada.** A tabela do IEPS existe e tem grão municipal (`br_ieps_saude.municipio`). A desigualdade de acesso aparece de forma inequívoca na **cobertura de plano privado**: **r = +0,65 com PIB per capita e −0,73 com cobertura do Bolsa Família** — a segunda correlação mais forte de todo este arquivo depois de INSE×pobreza. O sistema é literalmente dois: onde há renda, há plano; onde não há, há ESF (T49-4, +0,29 com pobreza). A concentração de procedimento ambulatorial por equipamento especializado não foi montada (a SIA tem 6,16 bilhões de linhas, fora do orçamento desta passada).
- **T24-3 ✅ (2026-09-05, resposta negativa)** Internações por condição sensível à atenção básica (SIH 2022, lista reduzida de CIDs): **0,71% das AIHs na mediana municipal**. Contra a cobertura de atenção básica do IEPS: **r = +0,02 (cob_ab), +0,07 (ESF), +0,16 (agentes comunitários)** — todas **positivas**, o oposto da hipótese. Contra a pobreza: **+0,27**. Mais atenção básica não reduz internação evitável no corte transversal; o que a prevê é pobreza. Como em T03-2 (ESF × mortalidade infantil, +0,17), o sinal positivo é **alocação reativa** — a ESF é posta onde o problema está —, e não iatrogenia. Separar as duas coisas exige desenho longitudinal, não corte.
- **T24-5 ✅ (2026-09-05) — a dependência de atendimento fora é quase universal.** **81,7% das AIHs do município mediano são de paciente tratado fora do próprio município.** A variável que explica isso é tamanho (**r = −0,68 com população**), não carência: contra estabelecimentos CNES por habitante dá **−0,11**, contra PIB per capita **−0,10**, e contra mortalidade geral **+0,06**. Curiosamente é **maior onde a cobertura de atenção básica é maior (+0,34)** — porque a ESF cobre 100% justamente nos municípios pequenos que não têm hospital. **Municípios com alta mortalidade evitável não são os que mais dependem de fora**: a hipótese da pergunta não se sustenta.
- **T24-nota ✅** Mortalidade infantil × cesárea: **−0,40 (n=2.283)** — municípios com mais cesáreas têm menor TMI, mas é provável seleção (cesárea marca acesso, não causa). *(A10)*

## 25 · Orçamento

- **T25-4 ✅** Emendas parlamentares per capita (2023+) × % votos Lula 2022: **r = −0,006 (n=1.406 municípios) — dinheiro de emenda não segue alinhamento eleitoral municipal**.
- **T25-1 ✅** Emendas CGU × transferências Transferegov por município: **r = +0,10 (n=1.096)** — são circuitos distintos; quem recebe emenda não é quem capta planos de ação.
- **T25-2 ❌ **SEM RESPOSTA** — bloqueio estrutural confirmado (2026-09-05).** `br_siop_orcamento.dados` (5.610 linhas, **só o exercício de 2025**) é o **catálogo de ações orçamentárias** — órgão, função, subfunção, programa, ação, produto, base legal — e **não tem nenhuma coluna de valor** (nem dotação, nem empenho, nem pago). Sem valor não há como comparar o custo do crédito rural subsidiado com o dos programas sociais no orçamento federal. Esse bloqueio é o mesmo de T40-4 e vale para toda pergunta que peça montante do SIOP.
- **T25-3 ◐** Execução por tipo (CGU 2023+): individual finalidade definida **74,4%** pago/empenhado; transferências especiais **99,7%**; bancada **52,5%**; comissão **43,2%** — individuais executam melhor que coletivas. Velocidade/bloqueio no SIOP/Transferegov pendente.
- **T25-5 ❌ **SEM RESPOSTA**** Mesmo bloqueio de T25-2: o SIOP espelhado não tem valores, só o catálogo de ações de 2025 — não há série de juros nem de emendas no orçamento para comparar com a arrecadação. A parte "quanto virou emenda" é respondível pelo `br_cgu_emendas_parlamentares.microdados` (88.991 linhas com `valor_empenhado`/`valor_pago` por ano e município), mas a comparação com juros do orçamento federal exige o SIOP com valores.

## 26 · Servidores

Reaberto em 2026-09-05: o recorte municipal segue bloqueado (a tabela só tem
`sigla_uf` de lotação), mas o recorte **estadual** responde 4 das 5 perguntas, e
o item 4 é respondível por **tempo de serviço** em vez de idade.

- **T26-1 ✅ (UF, 2026-09-05)** Servidores federais por 100 mil habitantes (jun/2025, 555.893 com UF de lotação): **DF 3.557 — 3,2× o segundo colocado (RR 1.120)** e **46× o último (SP 77,2)**. Depois de DF e das UFs pequenas do Norte (RR, AP), o Executivo federal é surpreendentemente pouco presente nos estados grandes: SP tem 34.289 servidores para 44 milhões de habitantes, menos que o RS (49.961 para 10,9 milhões). Não é a renda local que distribui o servidor federal — é a sede administrativa e a rede de universidades e institutos federais.
- **T26-2 ✅ (UF, 2026-09-05)** Comparação feita **por UF, não por cargo↔CBO** (o crosswalk continua não existindo), o que responde a pergunta na sua parte verificável: mediana da remuneração bruta federal ÷ mediana do vínculo formal da RAIS 2022 na mesma UF. **A razão é de 2,7× a 7,7× e é fortemente regressiva geograficamente**: PB 7,74×, RN 7,54×, CE 7,40× e AL 7,18× no topo; DF 5,38×, MT 4,84×, RO 3,64×, RR 3,12× e AP 2,73× na base. O salário federal é quase idêntico entre estados (R$ 10,3 mil a R$ 14,1 mil de mediana), enquanto o mercado local varia de R$ 1,60 mil a R$ 2,61 mil — **o servidor federal é uma elite de renda muito maior no Nordeste que no Centro-Oeste**, não porque ganhe mais, mas porque o entorno ganha menos.
- **T26-3 ❌ **SEM RESPOSTA** — bloqueio de granularidade confirmado (2026-08, reconfirmado 2026-09-05).** `cadastro_servidores` só tem `sigla_uf` de lotação (e ela vem preenchida em apenas 555.893 das 778.516 linhas de jun/2025 — ver o aviso em T26-1). Sem `id_municipio` não há como identificar município-sede de órgão federal nem compará-lo com vizinhos. Os itens 1, 2, 4 e 5 deste tema foram respondidos em nível estadual em 2026-09-05; este é o único que a UF não substitui.
- **T26-4 ◐ (2026-09-05)** Sem data de nascimento, mas **com `data_diploma_ingresso_servico_publico`**: dos 778.516 registros de jun/2025, o tempo médio de serviço é **16,0 anos**; **136.446 (17,5%) têm 25 anos ou mais** e **117.069 (15,0%) têm 30 anos ou mais** — a fatia elegível a aposentadoria integral por tempo no médio prazo. A concentração é muito desigual entre órgãos: **Ministério da Gestão e Inovação 60,7% com 30+ anos, Defesa 55,6%, Agricultura 37,2%**, contra **Educação 9,4%** (o maior empregador, com 409.558 registros) e Saúde 12,8%. O passivo previdenciário de curto prazo está nos ministérios-meio e no setor rural, não na máquina de ensino. A projeção orçamentária contra o SIOP até 2035 exige a idade, que a tabela não traz.
- **T26-5 ✅ (UF, 2026-09-05)** Onde o servidor federal é denso, a dependência do setor público aparece na própria composição do quadro: o **DF tem 26,3% dos seus servidores em função comissionada**, quase o dobro da média, contra 7,6% em RR e 10,9% no RS. Depois do DF vêm MT e TO (19,9%), AM e PA (19,5%) — estados onde a presença federal é pequena em número mas concentrada em cargos de direção, isto é, presença **de comando**, não de serviço.

## 27 · Opinião

- **T27-eleitoral ✅ (UF)** Geografia do voto 2022: **PIB pc × Lula = −0,62; rendimento médio × Lula = −0,33; homicídios/100k × Lula = +0,46** — Lula venceu nos estados mais pobres e mais violentos; Bolsonaro nos ricos. *(A8, A9)*
- **T27-1…T27-5 ◐** Pesquisas Poder360/PNS/PNADC pendentes; base eleitoral calculada.

## 28 · Violência Escolar

- **T28-5 ✅** Autolesão notificada entre 10-19 anos (`br_ms_sinan_violencia`, 2022, `LES_AUTOP='1'`) per capita × nota média SAEB 9º ano (2021, rede total, localização total): **r = +0,03 (n=1.163 municípios com ≥3 notificações)** — praticamente nulo; nota SAEB não prevê taxa de autolesão notificada.
- **2 achados técnicos (valem para queries futuras)**: (1) `br_ms_sinan_violencia.microdados_violencia` usa o código de município do SUS de 6 dígitos (`ID_MN_RESI`), igual ao problema achado em `br_ms_sih` — precisa do bridge `br_bd_diretorios_brasil.municipio.id_municipio_6`; `br_ms_sinan.microdados_dengue` (tabela normalizada, minúsculas) já usa o `id_municipio` de 7 dígitos direto, não tem esse problema. (2) `br_inep_saeb.municipio` tem várias linhas por município/ano (rede × localização × disciplina × série) — juntar sem filtrar essas dimensões infla o join silenciosamente (achei um caso com 90 mil "municípios" em vez de ~1.200); filtrar rede/localização/série antes de agregar.
- **T28-1 ✅ (2026-09-05) — a notificação mede vigilância, não violência.** Violência contra adolescentes (SINAN, 10–19 anos, 2021–23; 5.166 municípios com ao menos uma notificação, mediana 28,7/100 mil) contra o INSE das escolas: **r = +0,17**. Contra o PIB per capita **+0,22**, contra conectividade **+0,23**, contra formalidade **+0,21** — e contra a cobertura do Bolsa Família **−0,18**. **Todos os sinais são o oposto do que a pergunta supõe**: notifica-se mais violência contra adolescente onde a escola é melhor, a renda é maior e a internet funciona. O golpe final é a correlação com o desfecho letal: **viol. notificada × homicídio juvenil = +0,003, exatamente zero**. A notificação do SINAN mede a existência de um serviço que notifica, não a existência de violência — mesma classe de artefato já achada em T22-2 (mortalidade respiratória) e T42-5.
- **T28-2 ✅ (2026-09-05)** **Sim, e fortemente.** INSE médio das escolas × homicídio juvenil (SIM 15–24 anos, 2020–22) por município: **r = −0,37**; **entre UFs, r = −0,75**. AM (INSE 4,05) tem 14,3 homicídios juvenis/100 mil, PA (4,23) tem 11,2 e MA (4,18) tem 9,2; SC (5,46) tem 2,0, SP (5,27) tem 1,4. Aviso de uso que vale mais que o resultado: **INSE × cobertura do Bolsa Família dá r = −0,90** — o indicador socioeconômico do INEP é, na prática, um índice de pobreza municipal com outro nome, e usá-lo como "controle socioeconômico" ao lado de renda é colinearidade, não controle.
- **T28-3 ◐ (2026-09-06, resposta fraca e no sentido oposto)** Coorte montada: SAEB 9º ano de 2019 → inscrição no ENEM 2022 (mesmos alunos, 3 anos depois), 2.907 municípios. Participação no ENEM por mil habitantes × letalidade juvenil: **r = +0,06 — nada**. Isolando o **resíduo** da participação depois de descontar o desempenho no SAEB — isto é, "quem participa mais ou menos do que sua nota faria esperar" —, os sinais aparecem mas invertidos em relação à hipótese: **+0,12 com homicídio juvenil, +0,17 com cobertura do Bolsa Família, −0,20 com INSE**. **Municípios mais pobres e mais violentos têm participação no ENEM ACIMA do esperado pela nota, não abaixo.** Explicação plausível: onde não há alternativa de trabalho ou de curso técnico, o ENEM é a única porta e todo mundo presta. A "queda de participação" que a pergunta procura não existe nesse recorte. *Ressalva: a taxa usa população como denominador, não matrícula do 3º ano — a matrícula por coorte exigiria o Censo Escolar alinhado, não montado.*
- **T28-4 ❌ **SEM RESPOSTA**** Segue pendente por escopo da fonte: o ISP-RJ cobre apenas o Rio de Janeiro; qualquer resposta seria sobre um estado, não sobre o Brasil que a pergunta pede.

## 29 · Dados Eleitorais

- **T29-2 ◐** Patrimônio eleitos medido (R$ 3,12 mi médio / R$ 158 mi máximo); série histórica pendente.
- **T29-1 ✅ (2026-08-27)** Deputados federais reeleitos (mesmo `titulo_eleitoral_candidato` eleito em 2018 E 2022, n=282 de 513 — taxa de reeleição 55%): o mapa municipal de votos se repete fortemente — correlação intra-candidato entre o vetor de votos por município em 2018 e em 2022, **r médio = 0,87 (mediano 0,92, n=275 com ≥20 municípios votados)**. O perfil de renda da base eleitoral (PIB per capita médio ponderado por voto) também é estável entre as duas eleições: **r = 0,93 (n=282)** — quem elegeu um deputado por um perfil de renda em 2018 continua elegendo pelo mesmo perfil em 2022. **Achado de bug de query**: filtrar `resultado ILIKE '%eleito%'` captura also "não eleito" (substring "eleito" dentro de "não eleito"), inflando reeleitos de 282 para 472 — usar `resultado IN ('eleito por media','eleito por qp')`.
- **T29-3 ✅ (2026-08-27)** Margem de vitória no 1º turno da eleição presidencial 2022 (diferença de % de votos válidos entre 1º e 2º colocado, por município, margem média 31,7%) × emendas parlamentares pagas per capita (2023+, mesma fonte de T15-5/T25-4/T40-3): **r = +0,018 (n=5.570, quase todo o país)** — praticamente nulo. Município com eleição presidencial mais disputada não recebe nem mais nem menos emenda depois.
- **T29-5 ✅ (2026-08-27)** Queda de comparecimento presidencial 1º turno 2018→2022 (nacional: 79,2%→78,7%, −0,47pp, n=5.570) × % população jovem 15-29 (Censo 2022): **r = +0,05**; × PIB per capita 2021: **r = +0,01** — ambos praticamente nulos, não confirma a hipótese. Capitais tiveram queda maior (−1,21pp) que municípios do interior (−0,46pp) — o oposto do que a pergunta original sugeria (interior/pobre/jovem caindo mais).
- **T29-4 ✅ (reformulado, 2026-09-05)** A operacionalização que faltava é o **índice de Rice** (|sim−não| ÷ total, por votação e partido), calculado nas duas casas para 2023+. **Câmara**: NOVO 1,00, PCdoB 0,98, PSOL 0,97, PT 0,97, PV 0,93 no topo; **UNIÃO 0,64, PSDB 0,71, MDB 0,72, PP 0,74, PSD 0,76** na base. **Senado**: PT 0,94, PL 0,89, MDB 0,87, PDT 0,86; UNIÃO e PODEMOS 0,78 na base. O padrão vale nas duas casas: **partido ideológico vota unido, partido de centro fisiológico vota dividido** — 36 pontos de diferença entre topo e base na Câmara. Ver T76-4 para a comparação Câmara×Senado.
- **T29-extra ✅** Correlações geográficas do voto em A8/A9 acima.

## 30 · Estrutura Produtiva

- **T30-1 ✅ (parcial)** Empresas/100k × rendimento médio: **+0,24 (n=5.570)** — mercados com mais empresas pagam melhor. Concentração de capital social pendente. *(A13)*
- **T30-2 ✅ (2026-08-27)** Microempresas ativas per capita (`br_me_cnpj.porte='1'`, snapshot 2025-09, matriz, média nacional 7.167/100 mil hab) × crescimento de vínculos RAIS 2012→2022 por município: **r = −0,10 (n=5.557 municípios com ≥20 vínculos em 2012)** — fraco e no sentido oposto ao esperado: mais microempresa per capita não acompanha maior crescimento formal, se algo é levemente pior.
- **T30-3 ✅ (2026-08-27)** Taxa líquida de abertura de empresas (aberturas−baixas, via datas em `br_me_cnpj.estabelecimentos` snapshot único 2025-09, painel município×ano 2011-2020) × crescimento do PIB municipal nominal: correlação contemporânea **r = 0,043**; um ano depois **r = 0,076** (n≈50-56 mil pares município-ano) — ambas fracas, mas a defasada é a maior das duas, um sinal (fraco) de antecipação, não de coincidência pura.
- **T30-4 ✅ (2026-08-27)** Empresas com sócio formalmente estrangeiro (`br_me_cnpj.socios.tipo='3'`, dez/2021, 8.877 CNPJs distintos) × emprego formal (`br_me_rais_identificada.estabelecimentos` 2021): só **192 (2,2%) aparecem como estabelecimento empregador na RAIS**, contra uma taxa-base de 15,5% entre todos os 20,4 milhões de CNPJ ativos do país (3,16M/20,4M) — empresa com sócio estrangeiro tem ~7x menos chance de ser empregadora direta, consistente com boa parte sendo veículo de investimento/holding sem operação própria (mesmo padrão achado em T48-2 para offshores do ICIJ). Entre as 192 que empregam, a comparação por CNAE (n pequeno, máx. 18 por divisão) não mostra padrão consistente de empregar mais nem menos que a média nacional do setor.
- **T30-5 ◐ (2026-08-27)** HHI de concentração de emprego por seção CNAE (`br_me_rais_identificada` 2021, 21 seções) × arrecadação federal por trabalhador formal na seção (`br_rf_arrecadacao.cnae` 2021, só disponível em nível de seção nacional, não município): **r = −0,25 (log-log: −0,31, n=15 seções com arrecadação não-nula)** — setores mais concentrados arrecadam proporcionalmente MENOS por trabalhador, não mais; mas n=15 no nível de seção é amostra pequena para uma conclusão forte. `br_rf_arrecadacao` não tem grão municipal nem por porte de empresa (mesmo bloqueio de T16-2/T16-5), então o teste fica limitado ao nível macro de setor.

## 31 · Desenvolvimento Humano

- **T31-3 ◐** IVS-IPEA × mortalidade infantil (SIM×SINASC 2020–22): **r = +0,31 (n=1.423 municípios ≥20 mil hab)** — vulnerabilidade social prevê TMI melhor que PIB pc (−0,13, T03-3).
- **T31-1 ◐ (2026-09-05)** Cobertura de benefícios × IVS-IPEA: o AVS só tem uma onda no espelho, então a comparação é cross-seccional. Cobertura do Novo Bolsa Família (jul/2026) × IVS: a direção é a esperada, mas o IVS não adiciona poder preditivo sobre a própria taxa de cobertura — a focalização já é quase tautológica com o CadÚnico. Ver T65-1: a cobertura do NBF sozinha separa municípios melhor (−0,74 com formalidade) que o índice composto.
- **T31-2 ◐ (2026-09-05)** Beneficiários muitos × vulnerabilidade baixa: os municípios nesse quadrante existem, mas o teste correto (erro cadastral vs sobreposição de programas) exige o CadÚnico por família, que não está no espelho — só a folha de pagamento. Com o que há, o Gás do Povo (T64-1) mostra o inverso: a cobertura *sub*-atende o cadastro em 74% dos casos.
- **T31-4 ✅ (2026-09-06) — o bloqueio anterior estava errado: o AVS tem DUAS ondas.** `br_ipea_avs.municipio` traz **2000 e 2010** (158.983 e 160.698 linhas), com os recortes `raca_cor`/`sexo`/`localizacao` — filtrando `='total'` nos três sai a série municipal limpa, 5.565 municípios nas duas ondas. **O IVS médio caiu de 0,481 para 0,352, e 5.478 municípios (98,4%) melhoraram** — melhora quase universal na década. E o ganho **não** acompanhou o crescimento econômico: **Δ IVS × crescimento do PIB per capita 2010→2021 dá r = −0,07 (nada)**. O que prevê a melhora é o ponto de partida: **r = −0,48 com o IVS de 2000** — quem estava pior melhorou mais, convergência clássica. Contra a cobertura atual do Bolsa Família: **−0,22** (quem mais melhorou tem hoje mais beneficiários — o mesmo território, com política de renda no lugar do vazio). **A década de queda da vulnerabilidade brasileira foi de convergência e transferência, não de crescimento local.**

## 32 · Conectividade

- **T32-1 ✅** Anatel IBC × ENEM: **r = +0,57 (n=1.736)** — mais forte que qualquer medida de renda. *(A4)*
- **T32-5 ✅ (proxy)** IBC × formalidade +0,56 e × empresas +0,57 (A5, A6) — conectividade anda com dinamismo econômico; direção causal pendente.
- **T32-3 ✅** Densidade banda larga fixa (Anatel) × IBC: **r = +0,73 (n=3.070)**; × PIB pc **+0,31** — as duas métricas Anatel se confirmam mutuamente; a renda explica bem menos.
- **T32-2 ✅ (2026-09-05) — confirmam a direção, divergem na magnitude.** A "normalização dedicada" que faltava é simples: o SIMET tem faixa de velocidade categórica, e a fração de escolas do município na faixa "mais de 50 Mbit/s" é um índice utilizável. Contra o IBC da Anatel: **r = +0,40**; contra a cobertura 4G/5G: **+0,33**; contra fibra: **+0,18**. As duas fontes concordam sobre a ordem dos municípios, mas o IBC é sistematicamente mais otimista — ele mede a **oferta comercial** na malha urbana, enquanto o SIMET mede a **entrega dentro da escola**. Onde a divergência é maior é onde há oferta e não há entrega. Aviso de cobertura: **43% das escolas rurais e 31,7% das urbanas estão como "Sem Medidor Instalado"** — o SIMET não mede um terço da rede, e ignorar essa categoria (em vez de tratá-la como nula) enviesa qualquer índice para cima.
- **T32-4 ✅ (2026-09-05) — sim, e a diferença é brutal.** Nacionalmente: **30,5% das escolas rurais estão "Sem Internet" contra 2,0% das urbanas** (15× mais), e apenas **15,2% das rurais têm mais de 50 Mbit/s contra 51,8% das urbanas**. **Dentro do mesmo município** — 1.752 municípios com pelo menos 3 escolas de cada tipo medidas —, o índice urbano supera o rural em **0,31 ponto na média**, e a urbana é melhor em **907 dos 1.752 (52%)**, empate ou vantagem rural nos demais. Ou seja: a defasagem nacional de 15× é quase toda **entre municípios** (rural pobre × urbano rico), não dentro deles. Consistente com T70-4: o apagão digital brasileiro é geográfico-rural, não uma discriminação intramunicipal contra a escola do campo.

## 33 · Internacionais

- **T33-1 ◐** Ranking FBSP×Censo (CVLI/100k, último ano): AP 64,7; BA 47,7; AM 42,5; CE 39,0; PE 37,3 — 5 UFs acima de 37/100k, faixa de países em conflito armado. Comparação com benchmarks internacionais (fora do espelho) pendente.
- **T33-2 ◐ (2026-09-05)** Sem série de países vizinhos no espelho (a base OCDE cobre 36 países e para em 2019, com Gini e pobreza até **2016**), a comparação direta não é possível. O que se mede é a amplitude intra-brasileira: **PIB per capita do DF R$ 101.848 contra MA R$ 18.443 — 5,5×**. Para referência, a razão entre o mais rico e o mais pobre dos 36 países da base OCDE no mesmo indicador é da mesma ordem de grandeza — ou seja, **a dispersão de renda entre estados brasileiros é comparável à dispersão entre países da OCDE**, mas com todas as unidades sob a mesma moeda, a mesma política monetária e o mesmo orçamento federal.
- **T33-3 / T33-5 ✅ (2026-09-05)** **Se cada UF fosse um país, 22 das 27 seriam "renda média-alta" pelo corte do Banco Mundial e nenhuma seria de baixa renda.** Convertendo o PIB per capita de 2021 a R$ 5,40/US$: **DF US$ 18.861 (alta renda, único)**; 21 UFs entre US$ 3.609 e 11.813 na faixa média-alta (MT 11.813, SP 11.341, RJ 10.950, SC 10.429 no topo); e **5 na faixa média-baixa — SE 4.346, CE 4.103, PI 3.625, PB 3.609, MA 3.415**. Combinado com T33-1 (AP 64,7 homicídios/100 mil, BA 47,7, AM 42,5 — patamar de país em conflito armado), o retrato é de **estados de renda média-alta com letalidade de zona de guerra**: a violência brasileira não é função de pobreza absoluta no padrão internacional. Ressalva: conversão a câmbio nominal, não PPP; em PPP as posições sobem, a ordem não muda.
- **T33-4 ◐ (2026-09-05)** O par bom-em-segurança × ruim-em-social existe e é nítido: **SC (INSE 5,46, 2,0 homicídios juvenis/100 mil) e SP (5,27, 1,4)** contra **AM (4,05, 14,3) e PA (4,23, 11,2)** — mas isso é a diagonal esperada, não o quadrante contraintuitivo que a pergunta procura. A correlação INSE × homicídio juvenil entre UFs é **−0,75** (ver T28-2): segurança e indicador social andam juntos no Brasil, com pouquíssima exceção. O quadrante "seguro e socialmente ruim" praticamente não existe; o inverso (rico e violento) aparece em MT e MS.

## 34 · Bases Territoriais

- **T34-1 ✅ (2026-09-05)** **Apenas 6 dos 5.571 municípios do diretório do IBGE não existem na Área Mínima Comparável 2000→2010** — Mojuí dos Campos/PA (23.501 hab), Balneário Rincão/SC (15.981), Pescaria Brava/SC (10.190), Paraíso das Águas/MS (5.510), Pinto Bandeira/RS (2.723) e Boa Esperança do Norte/MT. **O Censo 2022 captou 5 dos 6**: Boa Esperança do Norte/MT é o único sem população publicada — emancipação posterior/pendente, não lacuna do Censo. A malha municipal brasileira, em termos de código, está praticamente congelada desde 2010 (5.565 → 5.571 em 22 anos), contra 3.800 AMCs necessárias para comparar 1970 com 2010.
- **T34-2 ◐ (2026-09-05)** Os 5 emancipados com dado têm população mediana **10.190 contra 11.066** dos demais (praticamente igual) e PIB per capita mediano **R$ 18.435 contra R$ 24.623** — 25% mais pobres. Amostra de 5 não sustenta conclusão; o sinal é sugestivo de emancipação de distrito periférico, não de polo econômico.

## 35 · Transporte

- **T35-4 ◐** Tempo de deslocamento (Mobilidados) × rendimento RAIS: **r = −0,40 entre municípios ≥100 mil hab (n=101)**; × PIB pc −0,15 — cidades mais ricas têm deslocamentos menores; a "renda efetiva" (salário÷tempo) penaliza as metrópoles médias do Norte/Nordeste. Demais itens exigem cruzamento com CAGED origem-destino.
- **T35-1 ◐ (2026-09-05)** Municípios-dormitório: o tempo médio de deslocamento (Mobilidados, **única onda 2010, 229 municípios**) correlaciona com log-população (**r = +0,50**) e negativamente com PIB per capita (**−0,12**) — quem mais viaja não é quem mais ganha, é quem mora na periferia de metrópole. Os extremos são inequívocos: **Japeri/RJ 67 min (53% acima de 1 h) e Francisco Morato/SP 66 min (54%)**, ambos com PIB pc abaixo de R$ 16 mil; contra a mediana nacional da amostra. O elo com o fluxo origem-destino do CAGED segue não montado.
- **T35-2 ✅ (2026-09-05)** **Não são as de maior PIB.** Entre os 227 municípios com tempo medido, PIB per capita × tempo de deslocamento dá **r = −0,12**: mobilidade ruim é atributo de periferia metropolitana pobre, não de metrópole rica. O que prevê o tempo é o tamanho da aglomeração (+0,50 com log-pop), não a renda.
- **T35-3 ◐ (2026-09-05)** Mortes no trânsito (SIM 2020–22, CID V01–V99): mediana de **11,8/100 mil hab** nos municípios com dado de mobilidade. Contra taxa de motorização: **r = +0,16** (fraco). Contra tempo de deslocamento: **r = −0,46** — quanto mais longo o deslocamento, MENOS morte no trânsito per capita, porque deslocamento longo é transporte coletivo de periferia metropolitana e morte no trânsito é fenômeno de rodovia e de moto no interior. A infraestrutura de transporte coletivo, medida indiretamente, protege.

## 36 · Religiosidade

- **T36-1 ✅** Templos/100k × PIB pc: **r = −0,11 (n=5.570) — praticamente nenhuma relação**; Piauí (mais pobre) lidera densidade de templos, SC (rica) é 2ª. *(A16)*
- **T36-2 ✅** Fiéis por religião (Censo 2022) × templos no CNPJ (CNAE 9491-0/00): **r = +0,47 com % evangélicos e −0,58 com % católicos (n=1.687 municípios)** — o registro empresarial de templos captura o evangelicalismo; católico tem paróquia, não empresa.
- **T36-3 ✅ (2026-09-05) — o templo do município pobre não tem carteira assinada.** Vínculos formais em organizações religiosas (RAIS 2022, CNAE 9491): **112.366 vínculos em 4.449 municípios**. Contra a densidade física de templos do CNEFE (T65-2): **r = −0,09 — nenhuma relação**. Contra a renda: **+0,30 com PIB per capita, +0,31 com formalização, −0,41 com cobertura do Bolsa Família**. Ou seja: o **prédio** religioso é mais denso onde há pobreza (T65-2, r_parcial +0,22) e o **emprego** religioso formal é mais denso onde há riqueza. A rede de fé do município pobre existe fisicamente e é invisível na RAIS — é trabalho voluntário, informal ou pastor sem vínculo. A série 2010→2022 de composição religiosa segue indisponível (Censo 2010 por religião não está no espelho).
- **T36-4 ◐** Coberto por T36-2: onde há muitos evangélicos há mais templos-CNPJ (+0,47); perfil socioeconômico fino fica para cruzamento com instrução do próprio censo religioso.
- **T36-5 ✅ (proxy)** Templos × rendimento médio RAIS: +0,06 — idem, nada.

## 37 · Sanções

- **T37-1 ✅** Dos **93 sancionados do TCU, 38 (41%) seguem com CNPJ ativo** em 2023.
- **T37-5 ✅ (parcial)** PGFN: **R$ 7,06 trilhões consolidados, 7,67M devedores; SP sozinho R$ 3,04 tri** (RJ 873 bi, MG 601 bi). Sobreposição com TCU pendente.
- **T37-2 ✅ (2026-09-05) — sim, e em escala bilionária.** A dívida ativa da PGFN tem **6.675.326 devedores pessoa jurídica somando R$ 4,91 trilhões**. Desses, **25.643 venceram alguma licitação federal desde 2020**, carregando **R$ 241,7 bilhões de dívida ativa**, e **12.130 receberam pagamento por cartão corporativo** no mesmo período. Ter débito inscrito em dívida ativa não impede — nem na licitação, nem no cartão.
- **T37-3 ✅ (2026-09-05) — a recriação de personalidade jurídica é maciça.** Das empresas sancionadas no CEIS/CNEP, **10.064 sócios pessoa física** estão identificados no quadro societário do CNPJ (set/2025). Desses, **5.941 (59%) constam também como sócios de outras empresas não sancionadas** — ao todo **17.581 empresas distintas**, uma média de 3 empresas por sócio reincidente. A sanção recai sobre o CNPJ; o sócio segue livre e já está em outras três empresas. *Ressalva de método: o CPF do sócio vem mascarado no cadastro público, então o casamento usa CPF mascarado + nome exato — colisão de homônimo é possível, e o número deve ser lido como teto, não como piso.*
- **T37-4 ✅ (2026-09-05)** Empresas sancionadas no CEIS/CNEP que aparecem como estabelecimento empregador na RAIS identificada 2021: **2.783 empresas com 335.205 vínculos ativos**. A sanção fecha o balcão público, não a empresa nem o emprego — mesmo padrão de T63-5 e coerente com o achado de 2026-08 sobre os 93 inidôneos do TCU (38 ainda com CNPJ ativo). Por município, a distribuição segue a de T63-1: absoluto nas capitais, taxa per capita dominada por município pequeno com uma única empresa.

## 38 · Educação Básica

- **T38-4 ✅ (fato)** PISA 2022 matemática: **Brasil 380,3 vs OCDE 474,8** (n≈10.800 alunos BRA) — gap de ~95 pontos ≈ 2,5 anos escolares.
- **T38-3 ❌ **SEM RESPOSTA** — bloqueio de granularidade confirmado (2026-08, reconfirmado 2026-09-05).** `br_inep_formacao_docente` tem apenas as tabelas `brasil` (5.040 linhas), `regiao` (25.200) e `uf` (133.840) — **não existe grão municipal**. A alfabetização do INEP tem taxa por UF (`uf_taxa_alfabetizacao`), então o par formação docente × alfabetização é possível **só em nível estadual** (n=27), sem o controle de renda municipal que a pergunta pede. Não executado nesse recorte reduzido por baixo poder estatístico.
- **T38-5 ✅ (2026-08-27)** Queda de matrícula na educação básica (Sinopse INEP, `br_inep_sinopse_estatistica_educacao_basica.localizacao`, soma de todas as etapas/redes/localizações, 2010→2022, média nacional −9,7%) × queda de população jovem 0-19 (`br_ibge_censo_2022.populacao_grupo_idade_sexo_raca`, mesmo intervalo, média −17,2%, total nacional 62,9M→54,5M): **r = +0,71 (n=5.565 municípios)** — forte e no sentido esperado: onde a população jovem caiu mais, a matrícula caiu mais também, embora em proporção menor (a queda de matrícula é sistematicamente menor que a queda demográfica — indício de melhora de cobertura/permanência absorvendo parte da retração de coorte). **Achado de bug de query, não de dado**: `br_ibge_censo_2022.populacao_grupo_idade_sexo_raca` e `.indice_envelhecimento_raca` guardam os censos **2010 E 2022 na mesma tabela** sob a coluna `ano` (apesar do nome do dataset ser só "censo_2022") — um `SUM(populacao)` sem `WHERE ano=2022` soma as duas safras e dobra o total (confirmado: 393,8M vs os 203,1M reais). As demais tabelas do dataset (`populacao_grupo_idade_uf`, `populacao_idade_sexo`, `alfabetizacao_grupo_idade_sexo_raca`, as `caracteristica_domicilio_*`) não têm esse problema — só essas duas.
- **T38-2 ◐ (2026-08-27)** `br_inep_educacao_especial.matricula_aee` só tem grão UF×rede (Pública/Privada), sem município nem escola — não dá pra responder "dentro do mesmo município" como a pergunta pede. Com o que existe: cobertura do AEE (atendimento educacional especializado) entre os alunos público-alvo da educação especial (2021, média nacional 49,1%, UF×rede) × proficiência SAEB 9º ano matemática (mesma UF×rede): **r = +0,12 (n=54)** — fraco, sem relação clara. Ressalva importante: `quantidade_matricula` nessa tabela é o total de alunos **público-alvo da educação especial**, não a matrícula geral da rede — a métrica calculável é "% deles que recebe atendimento especializado", não "% da rede que é educação especial" (que exigiria uma tabela de matrícula total por UF×rede, disponível em outra tabela do Sinopse, não cruzada aqui por orçamento de tempo).
- **T38-1 ❌ **SEM RESPOSTA** — bloqueio de comparabilidade confirmado (2026-09-05).** O PISA espelhado (`world_oecd_pisa.student`, 1,7M linhas) mede proficiência em escala própria por aluno de 15 anos, e a "proporção de alfabetizados" do INEP (`br_inep_saeb.brasil_taxa_alfabetizacao` / `uf_taxa_alfabetizacao`) é uma taxa de 2º ano do fundamental em escala nacional. **Não há régua comum**: converter uma na outra exige equating psicométrico, não join. E o recorte por faixa socioeconômica não é comparável — o PISA usa ESCS, o INEP usa INSE, construídos com itens diferentes. Qualquer número produzido aqui seria inventado.

## 39 · Justiça

- **T39-1 ✅ (fato)** Judiciário estadual (CNJ 2021, 28 tribunais): **despesa de pessoal = 90,1% em média** da despesa total; mínimo 76,4%, máximo 98,7%. Confirma o gancho do tema.
- **T39-2 ◐ (2026-09-05, pelo lado do CNJ)** O lado dos TCEs segue bloqueado (nenhum dos 4 espelhos tem multa por município — ver o bloqueio de 2026-08-25 preservado abaixo), mas **o lado da improbidade existe e é utilizável**: `br_cnj_improbidade_administrativa.condenacao` tem **53.342 condenações, 1992–2024, com UF**. E o primeiro achado é um aviso de dado: **o Acre aparece com 28.600 condenações — 5,5× São Paulo (5.184) e mais da metade do país inteiro**, num estado de 900 mil habitantes. Não é litigiosidade real; é assimetria de alimentação do cadastro pelo TJAC (ou atribuição de UF residual). Excluindo o AC, a distribuição é plausível e acompanha porte: SP 5.184, MG 1.675, MA 1.606, PR 1.541, RJ 985. **Qualquer ranking estadual de improbidade a partir desta tabela precisa excluir o AC explicitamente.** O cruzamento com penalidade de TCE segue impossível.
- **T39-3, T39-4 ❌ **SEM RESPOSTA** — bloqueio estrutural mantido (2026-08-25, reconfirmado 2026-09-05)**: nenhum dos 4 espelhos de TCE tem multa/penalidade por município. `br_tce_sp` é só uma tabela de 2 colunas (nome do município), sem nenhum dado de fiscalização. `br_tce_pi` tem `despesas_total`/`receitas_total`/`licitacoes_estado`/`prefeituras` mas nenhuma tabela de penalidade/deliberação. `br_tce_rj.penalidades_ressarcimento_estado` existe mas as 948 linhas são **100% `TipoEnte = 'ESTADUAL'`** — zero linhas municipais. `br_tce_es` tem `resultados_fiscalizacoes` (só `ValorExecutivo`/`ValorLegislativo` por ano/esfera, sem município) e `lista_responsaveis`/`julgamento_contas` (por responsável, sem valor de multa nem porte do município). Cruzar CNJ-improbidade × "TCEs que mais multaram" por município não é possível com o que está espelhado — precisaria de um scrape novo (SP e PI não têm fonte de penalidade nenhuma hoje).
- **T39-5 ◐ (2026-09-05, com o denominador trocado)** Volume processual segue ausente (`recursos_financeiros` não tem coluna de processo — bloqueio de 2026-08-25 mantido), mas a tabela traz **`despesa_total_justica_pc`**, despesa per capita, que responde a segunda metade da pergunta. Na Justiça Estadual 2020+ (28 tribunais): **mediana R$ 285,90 por habitante/ano, mínimo R$ 139,10, máximo R$ 988,70 — 6,8× entre o mais caro e o mais barato**. TJDFT R$ 985, TJRO R$ 595, TJMT R$ 468, TJRR R$ 427 contra **TJCE R$ 145, TJPA R$ 149, TJAM R$ 186**. Por ramo, a Justiça Estadual (R$ 286) custa 3× a do Trabalho (R$ 91) e 8× a Eleitoral (R$ 35) por habitante. **"Custo por processo" continua incalculável; "custo por brasileiro" varia 7× conforme o estado.**

## 40 · Federalismo Fiscal

- **T40-1 ◐** CAPAG 2025 × transferências voluntárias per capita (Transferegov): **r = +0,03 (n=2.000+ municípios ≥20 mil hab)** — capacidade fiscal não explica quem recebe transferência; porte e política sim.
- **T40-2 ✅** CAPAG × FIRjan IFGF: **r = +0,37 (n=1.322)** — os dois índices concordam parcialmente; divergências concentram-se nos intermediários (C/B).
- **T40-3 ✅ (2026-08-25)** CAPAG 2025 × emendas parlamentares per capita (`br_cgu_emendas_parlamentares`, valor pago 2014–2025, R$168,6 bi / 5.419 municípios): **r = −0,08 (n=1.509 municípios ≥20 mil hab)** — join direto por código IBGE de 7 dígitos (`id_municipio_gasto` = `Código Município Completo`, sem padding, sem bridge documentada — nenhuma existia entre essas duas tabelas). Mesmo padrão do T40-1: capacidade fiscal não explica quem recebe mais emenda por habitante; se algo, o sinal é levemente inverso (piores CAPAG recebem um pouco mais), não "política forte = melhor nota".
- **T40-4 ❌ **SEM RESPOSTA** — falso pressuposto confirmado (2026-08-25, reconfirmado 2026-09-05 com o motivo adicional)**: `br_siop_orcamento` é orçamento da **União**, não dos municípios — e, além disso, a tabela espelhada **não tem coluna de valor nenhuma** (só o catálogo de ações de 2025, ver T25-2). Despesa obrigatória por orçamento municipal vive no SICONFI (`br_me_siconfi.municipio_despesas_funcao`, usado em T08-5), e o cruzamento com o IFGF da Firjan é viável por ali — não pelo SIOP.
- **T40-5 ❌ **SEM RESPOSTA** — bloqueio de fonte confirmado (2026-09-05).** `br_tesouro_capag.municipios` (5.568 linhas) **não tem coluna de ano** — é um retrato único, não uma série. Sem duas ondas não há "municípios que melhoraram a CAPAG", e a pergunta fica sem sujeito. Alternativa possível numa próxima passada: usar o IFGF da Firjan (`br_firjan_ifgf.ranking`, que **tem** `ano` e cobre 5.570 municípios) como medida de evolução de gestão fiscal no lugar da CAPAG.

## 41 · Nutrição

- **T41-excesso ✅ (fato)** SISVAN 2023: excesso de peso adulto — **RS 73,6%, RN 72,4%, SP 71,9%, MS 71,7%, CE 70,4%** (top 5 UFs). CMED/BPS/Farmácia Popular pendentes.
- **T41-1 ◐ (2026-09-05, com ressalva de unidade)** O Farmácia Popular segue sem preço praticado (só cadastro de estabelecimentos), então a comparação foi feita contra o **BPS — Banco de Preços em Saúde**, que é o preço efetivamente pago pela compra pública. Casaram **119 princípios ativos** entre CMED e BPS 2023–25. O preço público mediano fica em **1,4% do teto CMED**, e **nenhuma das 119 substâncias** é comprada acima do teto. **Esse 1,4% não deve ser lido como desconto de 98%**: o teto da CMED é por *apresentação* (caixa) e o `preco_unitario` do BPS é por *unidade* (comprimido/ampola) — a razão embute o número de unidades por caixa. A comparação só vira número honesto depois de normalizar apresentação→unidade, que a CMED não traz em coluna própria. **O que é comparável e vale**: dentro do próprio BPS, mesmo item CATMAT (mesma dosagem e apresentação), o preço pago varia entre UFs por um fator mediano de **2,9×**, com casos de **201× (risperidona solução oral 1 mg/ml, R$ 0,50 a R$ 100,73), 12,2× (dipirona 500 mg/ml solução oral) e 10,0× (tramadol 50 mg/ml)**. A diferença regional que a pergunta procura existe — e é do lado da compra pública, não do teto regulatório.
- **T41-4 ❌ **SEM RESPOSTA**** Segue bloqueado: o Farmácia Popular espelhado não tem série temporal de preço, só o cadastro de estabelecimentos credenciados — não há "antes e depois" para medir.
- **T41-2 ✅ / T41-5 ✅ (reformulado, 2026-09-05)** A pergunta como escrita depende do BPS, que não mede consumo local (ver a nota de 2026-08-27 logo abaixo). Mas o **SISVAN 2023 sozinho responde a parte substantiva, e com inversão forte**: em 5.287 municípios com ≥200 adultos acompanhados, a **obesidade adulta é de município RICO** (**r = +0,54 com PIB per capita, +0,54 com formalidade, +0,50 com conectividade, −0,52 com cobertura do Bolsa Família**), enquanto o **déficit nutricional infantil é de município POBRE** (**+0,46 com Bolsa Família, −0,38 com PIB pc**). Obesidade mediana municipal: **33,3% dos adultos acompanhados**. Por UF: RS 40,3%, SP 39,0%, MS 38,9%, RJ 38,5%. Extremos municipais: São Francisco do Conde/BA 80,3% e Madre de Deus/BA 79,1% contra Terra Roxa/SP 7,5% e Dom Pedro/MA 10,4%. **A transição nutricional brasileira tem duas faces territoriais opostas no mesmo país e no mesmo ano** — e a oferta de saúde local (estabelecimentos de saúde por domicílio no CNEFE) não explica nenhuma das duas (r = 0,00).
- *(nota de método mantida)* **⏳ — descoberta de incompatibilidade de fonte (2026-08-27)**: `br_saude_bps.dados` é **compra pública de medicamento por instituição** (hospital/secretaria, `nome_do_municipio_da_instituicao`), não consumo per capita da população — testado mesmo assim (déficit nutricional infantil SISVAN 2023, taxa média 4,3%, n=5.536 municípios, × gasto BPS per capita por município da instituição compradora, join por nome+UF): **r = −0,01, mas só 153 dos 5.536 municípios (2,8%) têm alguma instituição compradora no BPS** — a maioria dos municípios nunca aparece porque a compra costuma ser centralizada em secretarias estaduais/grandes hospitais, não no município de residência do paciente. O indicador não responde "acesso a medicamento contínuo da população local", só "volume de compra pública onde a instituição está sediada" — resultado descartado por não medir o que a pergunta pede.
- **T41-3 ❌ **SEM RESPOSTA**** Pendente — POF só tem grão UF (`sigla_uf`, sem município); "gasto com alimentação" não é uma coluna direta em `br_ibge_pof.despesa_coletiva_2017` — as despesas vêm codificadas por produto (`V1904`/`id_codigo_5_bd`/`id_codigo_7_bd`) e exigem cruzar com `cadastro_de_produtos_2017` para isolar a categoria "alimentação" (equivalente a um crosswalk COICOP), não tentado nesta rodada por risco de classificação errada sem tempo para validar.

## 42 · Água

- **T42-1 ✅ (2026-09-05)** Índice de estiagem construído da telemetria da ANA: vazão média 2019–2023 ÷ vazão média 2000–2015, por estação, agregada ao município da estação (34.605 estações mapeadas por nome+UF, 1.241 municípios com par completo). Nos **292 municípios com ≥2 estações**, a razão mediana é **0,901 — 10% menos água que na média histórica**; **112 (38%) perderam mais de 20% da vazão** e 63 ganharam mais de 20%. **Mas a coincidência com fogo é o oposto do esperado**: razão de vazão × focos de calor per capita **r = +0,30** e × alerta DETER **+0,38** — os municípios que *perderam* vazão são os que têm *menos* fogo. A explicação é geográfica, não causal: a perda de vazão está concentrada no Sul/Sudeste e no São Francisco (bacias monitoradas há décadas), enquanto o fogo está no arco amazônico, onde a rede telemétrica é rala. **A pergunta como formulada não é respondível com viés zero — a rede de estações da ANA não cobre a fronteira agrícola.**
- **T42-2 ✅ (2026-09-05, resposta negativa)** Com o SISAM (158,7 milhões de linhas, cobertura **2014–2019**, 5.570 municípios) em vez do INMET estação a estação: **PM2,5 municipal médio 2017–19 × focos de calor per capita dá r = +0,15 — quase nada.** O que prevê PM2,5 no Brasil é ser São Paulo: os 6 municípios de maior concentração são **São Paulo (51,3 µg/m³), Diadema, Osasco, Taboão da Serra, Guarulhos e São Bernardo**, todos com focos de calor per capita próximos de zero. **O material particulado modelado do SISAM mede tráfego e indústria metropolitana, não queimada** — usar essa tabela como proxy de fumaça de fogo é erro de leitura.
- **T42-3 ❌ **SEM RESPOSTA** — bloqueio estrutural confirmado (2026-09-05).** `br_mma_extincao.fauna_ameacada` (1.258 espécies) e `flora_ameacada` (6.418) têm **apenas categoria, espécie, família, ordem, grupo e lista_2014 — nenhuma coluna geográfica**: não há bioma, UF nem município. Qualquer pergunta "espécies ameaçadas por bioma/município" está estruturalmente bloqueada com o que está espelhado; precisaria da camada de distribuição geográfica das espécies, que não veio no scrape.
- **T42-4 ❌ **SEM RESPOSTA**** O HydroSHEDS espelhado (`basins_atlas`, 3,79M polígonos) é uma base de bacias identificada por `hybas_id`, sem código IBGE nem nome de bacia da ANA — casar as duas fontes é operação espacial (ponto da estação dentro do polígono da bacia), fora do escopo não-geométrico.
- **T42-5 ✅ (2026-09-05, resposta negativa e com aviso)** Mortalidade respiratória (SIM 2017–19, CID J00–J99) × focos de calor per capita: **r = −0,23**; × PM2,5 do SISAM: **−0,01**; × ozônio: **+0,15**. Mais fogo, *menos* morte respiratória registrada por habitante — o mesmo resultado invertido já achado em T22-2, agora com fonte independente de qualidade do ar. A causa é confundimento de registro e estrutura etária, não proteção: mortalidade respiratória × PIB per capita dá **+0,20** e × cobertura do Bolsa Família **−0,39**, ou seja, **a série de óbito respiratório mede onde há idoso e onde há médico que codifica J, não onde há fumaça**. Qualquer estudo de fogo × saúde neste espelho precisa de desenho intra-município ao longo do tempo, não de corte transversal.

## 43 · Cultura

- **T43-3 ✅ (com ressalva)** Medalhas olímpicas do Brasil por esporte (contagem por atleta, esportes coletivos inflados): futebol 181, vôlei 132, basquete 60, vela 36, atletismo 35, vôlei de praia 26, judô 24, natação 21.
- **T43-4 ✅ (2026-09-05)** **Ciclos de política esportiva, não PIB.** Medalhas do Brasil por edição de Verão: 1920 **7**, 1948 12, 1952 3, 1956 1, 1960 13, 1964 12, 1968 4, 1972 2, 1976 3, 1980 9, **1984 37**, 1988 27, **1992 14** (queda), **1996 68**, 2000 48, 2004 42, **2008 86**, 2012 63, 2016 56, 2020 55. Duas rupturas de patamar, ambas de política e não de economia: **1984** (fim da era de medalha esparsa) e **1996** (salto para dezenas, sustentado até hoje). O crescimento do PIB brasileiro foi contínuo e suave nesse período; a curva de medalhas é degrau. **A queda de 1992** — em plena abertura econômica — e a **estabilidade 2008–2020 em torno de 55–86** apesar de recessão profunda em 2015–16 fecham o caso: o desempenho olímpico brasileiro anda com o financiamento e a estrutura do esporte, não com o ciclo econômico. Ressalva de método: a contagem por atleta infla esportes coletivos; medida por **eventos com medalha** o platô recente fica em 17–21 por edição (2008: 17, 2016: 18, 2020: 21).
- **T43-1, T43-2, T43-5 ❌ **SEM RESPOSTA** — bloqueio estrutural confirmado (2026-08-27, reconfirmado 2026-09-05)**: `world_olympedia_olympics.athlete_bio` (a única tabela com dados de atleta) tem `birth_date`/`birth_year`/`country`/`country_noc`, mas **nenhuma coluna de cidade ou município de nascimento** — nem texto livre, nem código. Sem essa chave geográfica não dá pra ligar medalha a município (T43-1, T43-2, T43-5) (T43-4 foi respondido acima em nível nacional, que é o recorte possível). Precisaria de uma fonte adicional (ex.: COB, Wikipedia estruturada) com naturalidade do atleta.

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
- **T44-3 ✅ (2026-09-05) — o cadastro tributário rural mede desmatamento melhor que o crédito.** CAFIR (Receita Federal), última referência: **10.119.257 imóveis rurais em 5.547 municípios**. **Área cadastrada no CAFIR × desmatamento acumulado: r = +0,82** — a correlação mais forte já medida contra o PRODES neste espelho, acima do crédito rural (+0,58, T17-3) e da própria área do CAR. Por contagem de imóveis a associação cai para +0,55, ou seja: **é a área declarada, não o número de propriedades, que acompanha a floresta derrubada**. O CAFIR e o SICAR contam quase a mesma coisa (r = +0,89 entre as contagens de imóveis), mas o CAFIR tem a vantagem de ser área tributável declarada ao fisco, sem a sobreposição de polígonos que inutiliza a área do SICAR (ver o aviso em T60-4).
  tem 169,9M linhas mas só 3,89M `id_imovel_receita_federal` distintos — e
  **61-64% de TODAS as linhas, em TODO snapshot mensal, têm
  `id_imovel_receita_federal = NULL`** (confirmado no snapshot mais recente,
  2025-09-02: 6,27M de 10,16M linhas). `id_municipio`/`area` seguem preenchidos
  nessas linhas órfãs, mas sem id não dá pra saber se são propriedades
  distintas ou fragmentos/duplicatas das linhas com id — qualquer soma por
  município seria um número inventado. Não é bug desta sessão, é dado como
  chegou; precisa de re-scraping ou de entender a causa na fonte antes de usar
  esta tabela pra qualquer coisa.
- **T44-4 ✅ (2026-09-05) — praticamente todos.** Dos **4.014 municípios com ao menos um termo de embargo do IBAMA**, **3.951 (98,4%) declaram produção de lavoura temporária na PAM do mesmo ano**. O embargo não interrompe a atividade agrícola do município — nem deveria, já que embarga a área e não o município, mas o número mostra que a medida convive com produção declarada em praticamente 100% dos casos. O número de embargos acompanha o desmatamento (**r = +0,44**) muito mais que a produção agrícola (**+0,20 com valor da lavoura, +0,17 com área plantada**): embarga-se onde se derruba, não onde se planta. *Aviso de dado: `qtd_area_embargada` em `br_ibama_embargos_novo.termo_embargo` é **100% nula** nos 4.014 municípios — só a contagem de termos é utilizável.*
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
- **T45-5 ✅ (2026-09-05)** Sim, e com taxa de casamento quase perfeita — mas pelo motivo trivial explicado em T48-1. Das **9.591 empresas brasileiras com CNPJ estruturado no OpenSanctions, 9.577 (99,9%) casam no cadastro CNPJ** de set/2025, espalhadas por **1.716 municípios**, e **7.451 (78%) seguem com situação cadastral ativa**. A taxa de casamento é alta porque a fonte é o próprio CEIS brasileiro, já com CNPJ válido — não é validação cruzada independente. O número útil é outro: **78% das empresas em lista de sanção seguem ativas**, na mesma faixa do achado de T63-5 e dos inidôneos do TCU.
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

- **T48-1 ✅ (2026-09-05) — a resposta é "quase nada de próprio, e o que há é reimportação".** As três listas realmente internacionais são ínfimas para o Brasil: **OFAC tem 20 entradas com menção ao Brasil, todas pessoas físicas** (programas SDNTK e SDGT, sem CPF estruturado — a identificação vem em texto livre de "remarks", tipo "Cedula No. RG-01…"); **UN Sanctions: 0**; **EU Sanctions: 0**. O OpenSanctions, por sua vez, tem **131.626 entidades com país Brasil, das quais 131.432 (99,9%) trazem identificador estruturado** — mas o exame da procedência desmonta a impressão de cobertura internacional: das **9.591 empresas brasileiras com CNPJ**, **9.270 (97%) vêm do próprio CEIS da CGU**, 186 da lista suja do trabalho escravo do MTE e 19 da lista de licitantes debarred. **O que o espelho chama de "sanções internacionais sobre o Brasil" é, em 97% dos casos, a lista brasileira reimportada.** Identificador estruturado próprio de origem internacional: praticamente inexistente.
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
- **T48-3 ✅ (2026-09-05) — não produz identificação confiável, e o número mostra por quê.** O ICIJ tem **4.022 nomes distintos de officers ligados ao Brasil** (com mais de 8 caracteres). Casando por nome exato normalizado contra o quadro societário do CNPJ de set/2025: **2.283 (57%) encontram ao menos um sócio homônimo**, ligados a **19.864 empresas brasileiras**. Mas a média de ocorrências do nome no cadastro é de **8,7 sócios distintos por nome** — e só **360 dos 2.283 nomes (16%) são únicos no país**. Os campeões de colisão são exatamente o que se espera: "MARCOS ANTONIO DOS SANTOS" aparece 605 vezes, "JULIO CESAR DOS SANTOS" 465, "ANTONIO CARLOS RODRIGUES" 359. **Nome exato não serve como chave de beneficiário final no Brasil**: sem data de nascimento ou CPF do lado do ICIJ, 84% dos casamentos são ambíguos por construção. Os 360 nomes únicos são a única fração investigável, e ainda assim exigem confirmação documental caso a caso.
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
- **T49-4 ✅ (2026-09-05, reformulado via IEPS)** A tabela de vacinação Covid do espelho só tem o cadastro de estabelecimentos (805.803 linhas, sem doses), então a pergunta foi respondida com a **cobertura vacinal infantil de rotina do IEPS**, que mede a mesma capacidade instalada. Cobertura da ESF × cobertura vacinal: **r = +0,12 (polio), +0,13 (pentavalente), +0,11 (tríplice viral)** — positivo mas fraco. O achado que importa é outro e é forte: **a ESF está onde a pobreza está** (**+0,29 com cobertura do Bolsa Família, −0,29 com PIB per capita**) e **onde há ESF morre-se menos de causa infecciosa** (**r = −0,26** com óbitos infecciosos por 100 mil). A Atenção Básica é a política pública de saúde deste espelho com direcionamento pró-pobre mais nítido — o oposto da geografia do Desenrola (T66-3) e dos fundos do DIRPF (T69-3).
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
- **T53-5 ❌ **SEM RESPOSTA** — bloqueio de cobertura temporal confirmado (2026-09-05).** `world_oecd_public_finance.country` cobre **36 países e vai até 2019**, com as variáveis distributivas (Gini, taxa de pobreza) parando em **2016**. Posicionar o gasto obrigatório dos estados brasileiros no comparativo internacional exigiria anos sobrepostos com a CAPAG — que, por sua vez, **não tem coluna de ano** (ver T40-5). As duas fontes não têm janela temporal em comum, e o cruzamento fica sem base.
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
- **T55-4 ❌ **SEM RESPOSTA** — bloqueio estrutural reconfirmado (2026-09-05, com o motivo exato).** `br_fipe_veiculos.precos` (11.289 linhas) tem **apenas `vehicle_type | brand_code | brand_name | model_code | model_name`** — é um **catálogo de modelos, não uma tabela de preços**, apesar do nome. Não há coluna de valor, de ano-modelo nem de referência temporal, e nenhuma chave geográfica. Sem preço não há proxy de renda; a pergunta não tem como ser respondida com o que está espelhado, e a tabela deveria ser renomeada ou re-raspada com a coluna de valor.
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

---

# Rodada 2026-09-05 — temas 57–76 (datasets espelhados entre 2026-09-01 e 2026-09-04)

Painel municipal montado no beelink cruzando os datasets novos (Pix por município,
ANM/CFEM, IBAMA autos+embargos+CTF, INPE DETER, PRODES acumulado, ANEEL GD, PNCP,
CGU Sanções, Gás do Povo, Novo Bolsa Família, BCB SCR.data/Desenrola/IF.data,
Transferegov SICONV, IBGE CNEFE, Tesouro CAUC, RF DIRPF, SINAN arboviroses, SEDEC,
CGU terceirizados, Querido Diário texto, Senado dados abertos) contra as
covariáveis já conhecidas (PIB, RAIS, SIM, Anatel, PRODES, população).

Correlações são **Spearman** (rank) sobre 5.570 municípios ou 27 UFs. Onde
aparece `r_parcial`, o efeito foi medido **depois de residualizar log-população,
log-PIB per capita e efeito fixo de UF** — é a única forma de separar achado
real de "município grande/rico tem mais de tudo".

## Resultados transversais desta rodada

| # | Correlação / fato | Nível | n | valor |
|---|---|---|---|---|
| B1 | Proposta de convênio COM emenda parlamentar vira convênio | proposta | 524.919 | **86,5% × 15,6%** sem emenda |
| B2 | Densidade agropecuária no CNEFE × cobertura 4G/5G (Anatel) | município | 5.570 | **r_parcial = −0,55** |
| B3 | Auto de infração IBAMA (mediana, Infração da Flora) Amazônia × Cerrado | auto | 61.947 | **R$ 115.000 × R$ 24.000** |
| B4 | Unidades de geração solar por domicílio × cobertura do Bolsa Família | município | 5.551 | **r_parcial = −0,34** |
| B5 | Alerta DETER (km²) × autos de infração IBAMA | município | 1.251 | **r_parcial = +0,36** |
| B6 | Ticket médio do Pix PF × cobertura do Bolsa Família | município | 5.555 | **r_parcial = −0,37** |
| B7 | Penetração do Pix × densidade agropecuária (CNEFE) | município | 5.570 | **r_parcial = −0,45** |
| B8 | Cobertura do CAR (SICAR) × desmatamento acumulado | município | 5.563 | **r_parcial = +0,35** |
| B9 | Desenrola por mil famílias do Bolsa Família — DF × MA | UF | 27 | **944 × 100 (9,4×)** |
| B10 | Inadimplência PF (SCR.data) × conectividade (IBC Anatel) | UF | 27 | **r = −0,62** |
| B11 | Templos por domicílio (CNEFE) × cobertura do Bolsa Família | município | 5.555 | **r_parcial = +0,22** |
| B12 | Custo pago pelo governo ÷ salário do terceirizado | posto | 161.274 | **2,5× (médio) a 3,3× (alfabetizado)** |
| B13 | Empresas de terceirização federal com sanção CGU (CEIS/CNEP) | empresa | 7.905 | **1.261 (16%)** |
| B14 | Top 100 fornecedores do PNCP concentram do valor global | fornecedor | 502.211 | **95,3% — indício de valor sujo** |
| B15 | Cerrado × Amazônia no desmatamento acumulado 2002–2025 (PRODES) | bioma | 7 | **326.731 km² × 139.868 km²** |
| B16 | Municípios em saldo Pix negativo (pagam mais do que recebem) | município | 5.570 | **3.906 (70%)** |
| B17 | Convênio COM emenda: execução do repasse | convênio | 152.816 | **52,2% × 31,8%** sem emenda |
| B18 | BNDES: cobertura territorial indireta automática × não-automática | município | 5.570 | **4.772 × 379** |

## 57 · Pix como Termômetro Territorial

- **T57-1 ✅** **3.906 dos 5.570 municípios (70%) são devedores líquidos no Pix em 2025** — pagam mais do que recebem. A razão recebido/pago acompanha renda (**r = +0,23 com PIB pc**) e formalização (**+0,26 com vínculos/hab**), mas fracamente: o Pix drena para fora de quase todo o interior, e a exceção não é riqueza — é sede de operação. Extremos por habitante: Rochedo/MS perde R$ 848 mil per capita/ano; Coroados/SP e São Francisco do Conde/BA captam R$ 320–336 mil. Municípios pequenos com uma única grande empresa ou agroindústria distorcem a métrica nas duas pontas.
- **T57-2 ✅** **Infraestrutura, não bolso.** Penetração do Pix (pagadores PF distintos ÷ população) × cobertura 4G/5G: **r_parcial = +0,38** depois de descontar renda, tamanho e UF — o maior coeficiente do bloco. Contra o PIB per capita bruto a correlação existe (+0,52) mas some quando se controla conectividade. *(B7 é o espelho negativo: −0,45 contra densidade rural.)*
- **T57-3 ◐** **Não substitui, complementa.** Ticket médio do Pix PF × rendimento médio da RAIS: r = +0,27 — abaixo do PIB pc (+0,53). Mas contra a cobertura do Bolsa Família o ticket do Pix é forte e sobrevive aos controles (**r_parcial = −0,37**, B6), enquanto o PIB pc é o controle. Leitura: o ticket do Pix mede **consumo disponível**, não produto — é bom proxy de pobreza, ruim de riqueza.
- **T57-4 ✅** A fatia do valor recebido que vai a PJ acompanha formalização (**+0,73 bruto, +0,38 parcial**) e é a variável Pix mais colada ao PIB industrial (**+0,27 parcial com share industrial**). Existem, sim, municípios com CNPJ registrado e Pix quase todo PF — o padrão é interior agropecuário, onde a empresa está cadastrada mas o dinheiro corre entre pessoas.
- **T57-5 ✅** **Sim, o campo é o último bolsão não-digital.** Quintis de densidade agropecuária no CNEFE contra penetração do Pix: **0,65 → 0,60 → 0,57 → 0,54 → 0,50**, monotônico, e **r_parcial = −0,45** já descontadas renda, população e UF.

## 58 · Mineração, CFEM e Destino Social da Geologia

- **T58-1 ✅** **A substância importa mais que o valor.** Entre municípios com CFEM (n=3.217), o valor arrecadado per capita explica pouco (r = +0,23 com PIB pc, +0,21 com formalidade). Já a substância dominante separa mundos: **basalto** — PIB pc R$ 46 mil, formalidade 0,241, Bolsa Família 6,0%, homicídios 11,1/100k; **quartzito** — PIB pc R$ 13,4 mil, formalidade 0,092, Bolsa Família 32,2%, homicídios 13,7. Ouro lidera homicídios (**23,8/100k**), calcário dolomítico vem logo atrás (22,6). Geologia é destino social — não pela renda que gera, mas pelo tipo de operação que sustenta.
- **T58-2 ◐** **Não há efeito da mineração em si.** Municípios com CFEM: 14,96 homicídios/100k contra 14,76 dos sem — diferença desprezível. E dentro dos mineradores, mais CFEM per capita significa **menos** homicídio (r = −0,08). O que existe é efeito de substância + região: os 37 municípios de ouro da Amazônia Legal têm 29,0/100k, mas os outros mineradores da mesma região têm 29,1 — é a Amazônia, não o ouro. **Fora da Amazônia**, porém, ouro tem 7,1 contra 13,1 dos demais mineradores. O ouro amazônico não é mais violento que seu entorno; seu entorno é que é violento.
- **T58-3 ✅ (2026-09-05)** **A renda mineral não compra nem dispensa capacidade administrativa.** Entre os 3.217 municípios com CFEM, o valor per capita arrecadado é ortogonal a tudo que mede gestão: × pendências no CAUC **−0,01**, × taxa de sucesso em convênios **+0,01**, × desembolso de convênio per capita **−0,02**, × fundos habilitados no DIRPF **+0,04**, × valor de contrato PNCP per capita **+0,03**. Cinco indicadores independentes, todos abaixo de |0,04|. A CFEM entra no caixa e não deixa marca em nenhum comportamento administrativo observável.
- **T58-4 ✅ (2026-09-05)** **A renda mineral chega concentrada em quase todo lugar.** HHI de titulares da CFEM (2022–25) por município: mediana **0,822** — em metade dos municípios mineradores um único CNPJ responde por mais de 82% da arrecadação. Em **1.418 dos 3.218 (44%)** o HHI passa de 0,9, isto é, monopólio praticamente total. A concentração não é exceção de município pobre: é o padrão nacional da mineração brasileira no nível municipal.
- **T58-5 ◐ (2026-09-05)** As tabelas `scm_*` seguem sem código IBGE (`municipio_s` em texto livre, várias cidades por célula). O que o `sigmine_processos_minerarios` responde sem geografia: dos 8,3 milhões de registros, **665.225 estão com `FASE` nula** e as fases preenchidas são dominadas por **autorização de pesquisa (115.802)** contra **concessão de lavra (15.953)** — 7 títulos de pesquisa para cada 1 de lavra. A resposta parcial é que o estoque de títulos é majoritariamente **pesquisa, não extração** — o que explica boa parte dos municípios com título e sem CFEM sem precisar invocar sonegação.

## 59 · Fiscalização Ambiental: Alerta, Auto e Embargo

- **T59-1 ✅** **A fiscalização segue o alerta, mas com folga enorme.** DETER (km² alertado 2023+) × autos IBAMA: **r = +0,51 bruto, +0,36 parcial** (n=1.251). Dos 606 municípios com mais de 10 km² alertados, **27 não têm um único auto de infração desde 2015**. A mediana é 0,44 auto por km² alertado, mas a dispersão é de duas ordens de grandeza: São Félix do Xingu/PA (7.009 km² alertados, 1.676 autos) contra Ourilândia do Norte/PA (2.068 km², **50 autos**) e Peixoto de Azevedo/MT (2.158 km², **72 autos**).
- **T59-2 ✅** Ver acima: os 27 municípios com alerta alto e zero autuação existem e são identificáveis. O par mais gritante da lista dos maiores desmatadores é Ourilândia do Norte/PA — 30% do desmate alertado de São Félix do Xingu com 3% dos autos.
- **T59-3 ✅** **O CTF mede indústria formal, não risco ambiental.** Densidade de empresas no Cadastro Técnico Federal por 100 mil hab: **r = +0,65 com PIB pc, +0,63 com formalidade, −0,66 com Bolsa Família**, mas apenas **+0,09 com desmatamento**. É um censo de economia formal com etiqueta ambiental.
- **T59-4 ◐** Mais CTF, ligeiramente mais autos: **r_parcial = +0,16** (n=4.321). O registro não funciona como escudo, mas o efeito é fraco — quem se cadastra é quem tem estrutura para ser encontrado.
- **T59-5 ✅ — o achado mais forte do bloco.** **A Amazônia é multada 7× mais caro que o Cerrado pela mesma tipificação.** "Infração da Flora (não classificada)", mediana do auto: **Amazônia R$ 115.000 | Cerrado R$ 24.000 | Mata Atlântica R$ 16.500** (n=69.381). "Infração de Administração Ambiental": **R$ 110.000 | R$ 3.500 | R$ 2.000** (55×). "Apresentar informação parcialmente falsa": **R$ 111.500 na Amazônia × R$ 2.500 na Mata Atlântica** (45×). Ressalva importante: o valor do auto é proporcional a área/volume, então parte da diferença é escala da operação, não severidade da régua — mas a razão de 45× em infração documental (onde não há área) mostra que a régua também difere.

## 60 · Desmatamento Acumulado por Bioma

- **T60-1 ✅ — contraria a atenção pública.** PRODES acumulado 2002–2025: **Cerrado 326.731 km²**, Amazônia Legal 139.868 km², Caatinga 128.279 km², Mata Atlântica 64.298 km², Pampa 35.859 km², Pantanal 16.897 km². O Cerrado desmatou **2,3× a Amazônia** no período, e Cerrado + Caatinga somam **3,3×**. A geografia da atenção não é a geografia da perda.
- **T60-2 ✅ (2026-09-05)** Frente ativa = alerta DETER 2023+ ÷ desmatamento acumulado do município. Nos 756 municípios com ≥5 km² alertados, a mediana é **0,043** — o alerta recente representa 4% do passivo. Os fora da curva têm frente **maior que o passivo inteiro**: **Normandia/RR 3,97, Japurá/AM 2,79, Pacaraima/RR 2,35, Mazagão/AP 1,96, Amajari/RR 1,61**. Roraima aparece 3 vezes nos 5 primeiros. **A fronteira que se abre agora não é o Pará dos anos 2000 — é Roraima e o Amapá**, territórios com passivo histórico pequeno e movimento recente desproporcional.
- **T60-3 ◐ (2026-09-05)** A primeira metade está respondida (T60-1: Cerrado + Caatinga = 3,3× a Amazônia). Por UF, o desmatamento acumulado do PRODES põe **PA 113.139 km²** à frente, mas seguido de **BA 58.435, MT 58.246, TO 53.993, MA 52.977 e GO 49.651** — cinco estados de Cerrado/Caatinga/MATOPIBA entre os seis primeiros. A segunda metade (o crédito seguiu essa geografia?) tem resposta parcial em T75-4: o BNDES agro **não** seguiu — ficou no agro consolidado (r = +0,13 com desmatamento). O elo com o SICOR por município não foi montado.
- **T60-4 ✅** **O CAR persegue a fronteira, não a antecipa.** Cobertura do CAR (área cadastrada ÷ área do município) × desmatamento: **r_parcial = +0,35**. Alerta metodológico gerado aqui: a soma das áreas do SICAR excede a área do município em **5.563 dos 5.571 casos** (mediana 923× a área municipal) — há sobreposição massiva de polígonos e/ou unidade de área divergente. **`sicar_cobertura` só é utilizável como ranking, nunca como percentual.**
- **T60-5 ✅ (2026-09-05) — a cicatriz não antecipa, acompanha.** Cicatriz de queimada (DETER) do ano *t* × desmatamento alertado do ano *t+1*, por município, 2017–2024: **r médio = +0,30**. Mas contra o desmatamento do **mesmo ano** a correlação é maior: **r médio = +0,37**. Fogo e desmate são o mesmo evento na mesma janela — o fogo é o método, não o aviso prévio. E o poder preditivo **cai ao longo da série**: de +0,32 (2017→18) para **+0,14 (2024→25)**, com queda também no par contemporâneo. Interpretação: a fração do desmatamento que passa pelo fogo vem diminuindo — a derrubada mecanizada não deixa cicatriz térmica. **Usar foco de calor como alerta precoce de desmate está ficando pior a cada ano.**

## 61 · Geração Distribuída Solar

- **T61-1 ✅** **Agronegócio, não riqueza.** kW instalados per capita por UF: MT 0,87 | MS 0,69 | PR 0,60 | RO 0,50 | TO 0,49 — contra SP 0,17 e DF 0,21. Correlação com PIB per capita entre UFs: apenas **+0,30**. Municipalmente a GD por domicílio sobe monotonicamente com o peso agropecuário no PIB: **0,137 → 0,148 → 0,163 → 0,208 → 0,289** por quintil de adoção.
- **T61-2 ✅** **A placa solar é marcador de classe, e o efeito sobrevive ao controle de renda.** GD por domicílio × cobertura do Bolsa Família: quintis **0,35 → 0,29 → 0,17 → 0,12 → 0,078**, e **r_parcial = −0,34** já descontados PIB pc, população e UF (B4). É a variável nova que mais separa municípios pobres de não-pobres depois de tirar a renda da equação.
- **T61-3 ◐** GD rural × crédito BNDES per capita: **r = +0,52 bruto, +0,20 parcial** — o financiamento acompanha a adoção, mas não a explica sozinha.
- **T61-4 ◐ (2026-09-05)** Sem dados de interrupção da ANEEL no espelho, o teste possível é contra a qualidade da infraestrutura em geral: GD por habitante × IBC da Anatel **r = +0,33**, × fibra **+0,22**, × cobertura 4G/5G **+0,15**. **Todos positivos** — a placa solar aparece onde a infraestrutura é boa, não onde é ruim. Isso descarta a hipótese de fuga da rede ruim e reforça T61-2 (adoção é marcador de classe e de agro capitalizado). A parte sobre irradiação continua aberta: o INMET tem radiação global horária, mas o agregado municipal exige mapear estação→município.
- **T61-5 ✅** **4,26 milhões de empreendimentos PF (35,4 GW) contra 363 mil PJ (18,1 GW)** — PF domina em número, PJ em potência média (50 kW × 8 kW). Por classe: Residencial 3,77M (28,5 GW), Comercial 422 mil (14,4 GW), Rural 389 mil (6,7 GW). Adoção "de telhado" em unidades, "de investidor" em megawatts.

## 62 · PNCP — o Novo Portal de Contratações

- **T62-1 ✅ — não, e o dado precisa de aviso.** A soma de `valorGlobal` do PNCP dá **R$ 47,7 trilhões**, mais de 4× o PIB brasileiro — é lixo. Mediana R$ 3.236, p99 R$ 4,0 milhões, mas **406 contratos acima de R$ 1 bilhão**. Exemplo verificado: "ANDREIA DA SILVA OLIVEIRA", credenciamento de profissional de saúde em Palmeiras de Goiás, `valorGlobal` = **R$ 2.371.097.155.200** (2,37 trilhões) repetido em 2 linhas; o mesmo fornecedor tem outro contrato de R$ 31.500, plausível. **Regra: usar mediana/quantis no PNCP, nunca soma; qualquer total precisa de winsorização explícita.**
- **T62-2 ◐** Contratos por fornecedor: mediana 1,76 por município. Correlaciona com tamanho (+0,25) e conectividade (+0,18), fracamente com CAUC (**−0,11**) e com Bolsa Família (−0,14). Não sustenta a tese de captura ligada a má gestão fiscal.
- **T62-3 ✅** **4.687 dos 5.570 municípios (84%) publicaram ao menos um contrato no PNCP** — cobertura muito melhor que o Querido Diário (524 municípios, 9%). Mediana de 228 contratos por município.
- **T62-4 ✅** **2.891 dos 399.147 fornecedores PJ do PNCP (0,7%) constam do CEIS/CNEP da CGU.** Número pequeno em proporção, grande em absoluto — e o PNCP cobre só 2021–2026, então não é possível dizer pelo espelho se contrataram antes ou depois da sanção sem cruzar as datas de sanção uma a uma.
- **T62-5 ✅ — campo inútil hoje.** `emendaParlamentar` está **nulo em 5.011.914 dos 5.043.371 contratos (99,4%)**. Dos preenchidos, apenas **223 marcam `true`**. Não mede nada.

## 63 · Sanções, Leniência e Impedimento

- **T63-1 ◐** **7.885 empresas sancionadas (CEIS/CNEP) com CNPJ ativo em set/2025, espalhadas por 1.483 municípios.** Em absoluto a lista é a das capitais (SP 539, Salvador 368, Brasília 335, Rio 265). Per capita, a taxa cai fortemente com o tamanho (**r = −0,72 com população**) — sanção é fenômeno de município pequeno quando normalizada, o que provavelmente reflete uma única empresa sancionada num município de 3 mil habitantes, não geografia real da irregularidade.
- **T63-2 ✅ — não moram juntas.** Sanção administrativa per capita × desmatamento: **r = −0,15**; × fibra ótica: −0,15; × formalidade: +0,13. A irregularidade administrativa e a ambiental têm geografias independentes no espelho.
- **T63-3 ◐ (2026-09-05)** Escala medida: **2.891 dos 399.147 fornecedores PJ do PNCP (0,7%) constam do CEIS/CNEP**, e **1.261 das 7.905 empresas de terceirização federal (16%)** — a mesma pergunta respondida para dois mercados públicos distintos dá 0,7% num e 16% no outro. O recorte por CNAE dos acordos de leniência especificamente (tabela de 12 acordos com efeitos) não foi executado — n pequeno demais para correlação, vale como estudo de caso.
- **T63-4 ✅ (2026-09-05) — sim, e o achado é pior que a pergunta supõe.** Dos 3.530 registros do CEPIM, **962 casam com um convênio do SICONV** pelo número. A situação desses convênios: **283 "Inadimplente" e 254 "Prestação de Contas Rejeitada"** — 56% em situação irregular declarada, mais 212 em análise e 72 aguardando. E o dado que inverte a leitura: **a execução financeira desses convênios é de 85,1% do repasse, contra 39,3% da média geral do SICONV**. Não são convênios que travaram: **são os que o dinheiro saiu inteiro e a prestação de contas não voltou**. Os motivos de impedimento confirmam — 751 por instauração de tomada de contas especial, 485 por não apresentação de documentação, 380 por não apresentação da prestação de contas.
- **T63-5 ◐** Das empresas sancionadas com documento de 14 dígitos, **7.885 ainda têm estabelecimento ativo no CNPJ**. A contagem de vínculos RAIS dessas empresas não foi feita nesta rodada.

## 64 · Gás do Povo — Focalização de um Programa Novo

- **T64-1 ✅** **O Gás do Povo cobre 26,2% das famílias do Novo Bolsa Família** (3,49M contra 13,34M, competência jul/2026). A correlação municipal entre os dois é altíssima (**r = +0,97**) — a focalização segue o cadastro, como esperado —, mas a **cobertura varia 4× entre municípios**: mediana 21,6%, p10 8,6%, p90 32,4%. Casos quase descobertos: Benjamin Constant do Sul/RS (2 famílias para 397 do Bolsa Família, 0,5%), Jacareacanga/PA (32 para 2.840, 1,1%).
- **T64-2 ◐** A rede de revenda credenciada acompanha população (**r = +0,77**) e cobertura (+0,64), como esperado. A pergunta certa — se os municípios de pior cobertura são os de menos revenda por família — pede a razão revendas/famílias, não computada.
- **T64-3 ◐** Domicílios por CEP (dispersão do endereçamento no CNEFE) × cobertura do Gás do Povo: **r_parcial = +0,14** — sinal na direção esperada mas fraco. O gargalo logístico existe, não é a explicação principal.
- **T64-4 ✅ (2026-09-05)** A família média do Gás do Povo tem **3,21 pessoas** (média sobre 5.517 municípios), contra **2,79 pessoas por domicílio do Censo 2022** no Brasil. O programa capta famílias **15% maiores** que a média nacional — coerente com focalização em famílias com criança, não com viés de cadastro.
- **T64-5 ✅ — não.** Cobertura do Gás do Povo × pendências no CAUC: correlação desprezível. Programa federal pago direto ao cidadão não depende da capacidade administrativa do município — que é exatamente o desenho.

## 65 · Novo Bolsa Família em Microdado

- **T65-1 ✅** A fração de domicílios do CNEFE com Novo Bolsa Família é o melhor índice de pobreza municipal do painel: **r = −0,74 com formalidade, −0,72 com PIB pc, −0,59 com conectividade (IBC)**. Supera qualquer variável isolada do Censo em poder de separação.
- **T65-2 ✅** **Sim — e o efeito sobrevive aos controles.** Templos por domicílio (CNEFE) × cobertura do Bolsa Família: quintis **0,081 → 0,142 → 0,196 → 0,222 → 0,261**, e **r_parcial = +0,22** descontados renda, população e UF; **+0,19** descontando também conectividade. Isso **corrige o sinal do achado A16 da rodada anterior** (templos por CNPJ × PIB pc = −0,11, fraco): medindo o prédio no CNEFE em vez do registro no CNPJ, a associação entre rede religiosa e pobreza é 2× mais forte e resiste ao controle. Top: Melgaço/PA 38,1 templos por mil domicílios, Maraã/AM 32,2, Careiro da Várzea/AM 30,4 — contra mediana nacional de 7,9.
- **T65-3 ✅ (2026-09-05)** Parcela média do Novo Bolsa Família por município (jul/2026): mediana **R$ 839**, p10 R$ 764, p90 R$ 970 — variação de apenas **27% entre o decil de baixo e o de cima**, muito menor que qualquer desigualdade territorial brasileira. Mas a assimetria existe e tem sinal contraintuitivo: a parcela é **maior nos municípios mais ricos** (**r = +0,39 com PIB per capita, −0,38 com a própria taxa de cobertura**). Não é privilégio regional — é composição familiar: onde há menos beneficiários, quem recebe tem família maior e acumula mais adicionais.
- **T65-4 ◐** Cobertura do NBF × razão recebido/pago no Pix: **r = −0,30 bruto**, mas **−0,10 parcial**. A tese da "transferência que vaza" não se sustenta depois de descontar renda e UF.
- **T65-5 ◐** Cobertura do NBF × chikungunya por 100 mil: **r = +0,33 bruto**, **−0,04 parcial**. Pobreza e arbovirose parecem morar juntas, mas é confusão com região e renda — não sobra efeito próprio.

## 66 · Crédito às Famílias, Inadimplência e Desenrola

- **T66-1 ✅ — conectividade, não renda.** Inadimplência do crédito PF por UF (SCR.data, 2025+): × IBC da Anatel **r = −0,62**; × PIB per capita apenas **−0,31**. Também forte: × densidade de obras no CNEFE +0,53, × templos por domicílio +0,51, × formalidade −0,53. Extremos: **TO 7,78% e MA 7,42%** contra **SC 3,84% e DF 4,05%** — o dobro. Ativo problemático segue o mesmo mapa (TO 12,7% × SC 6,5%).
- **T66-2 ✅** **"Adiantamentos a depositantes" tem 59,2% de inadimplência** — o cheque especial não-contratado é, disparado, o pior crédito do país. Mas sua carteira é de **R$ 16,9 bilhões contra R$ 27,9 trilhões em empréstimos**: 0,06% do total. A atenção regulatória que recebe é desproporcional ao volume, e proporcional ao dano por tomador. Empréstimos (9,72%) e financiamento rural (5,22%) é onde mora o risco sistêmico; financiamento imobiliário, com R$ 24,6 trilhões, tem **1,28%**.
- **T66-3 ✅ — chegou aos ricos.** Operações do Desenrola por mil famílias do Bolsa Família: **DF 945, SC 871, SP 905** contra **MA 100, PA 137, PI 136** — razão **9,4×** entre DF e MA. Correlação com PIB per capita entre UFs: **+0,89**; com cobertura do Bolsa Família: **−0,94**. Um programa de renegociação de dívida de pessoa endividada alcançou proporcionalmente 9× mais gente nos estados onde há menos pobreza. Total: 4,25 milhões de operações.
- **T66-4 ◐** Nº de conglomerados participantes por UF acompanha o alcance, mas ambos acompanham o tamanho do sistema financeiro local — não separa oferta de demanda sem controlar carteira.
- **T66-5 ❌ **SEM RESPOSTA**** Mesmo bloqueio: o SEDEC espelhado só tem reconhecimentos vigentes de 2026, e a inadimplência do crédito rural pede a safra ruim do ano correspondente. O dado do SCR existe e está medido (financiamento rural PF com **5,22% de inadimplência**, R$ 12,78 trilhões de carteira — T66-2); o que falta é a série de desastres.

## 67 · Presença Bancária e Sistema Financeiro Territorial

- **T67-1 ✅** **Apenas 467 dos 5.570 municípios (8,4%) têm instituição financeira sediada** segundo o IF.data (2024). A presença acompanha população (+0,63) e conectividade (+0,57), e é negativamente associada à densidade agropecuária (−0,57). Ela não explica o volume de Pix melhor que a renda: o Pix per capita é bem previsto pelo PIB pc (+0,69) e pela conectividade, e a sede bancária adiciona pouco — Pix não precisa de agência.
- **T67-2 ✅ (2026-09-05) — cooperativa é de cidade média, não de município abandonado.** Pelo `segmento` do IF.data (2024): as cooperativas de crédito estão sediadas em **433 municípios com 799 instituições**, contra **20 municípios** no segmento dos bancos comerciais grandes. **416 municípios têm cooperativa e nenhum banco sediado** — a hipótese se confirma em número. Mas o perfil desmente a imagem de "cooperativa no vazio": onde há cooperativa a população mediana é de **51,5 mil habitantes** e o PIB per capita **R$ 43,8 mil**, ambos muito acima da mediana nacional (11 mil hab, R$ 24,6 mil). A cooperativa ocupa a **cidade média do interior próspero**, não o município pequeno e pobre — esse segue sem instituição sediada de tipo nenhum.
- **T67-3 ◐** Municípios com IF sediada têm maior taxa de sucesso em convênios (**r = +0,49**) e maior fatia de propostas com emenda (+0,48) — mas ambos são fortemente confundidos com porte do município.
- **T67-4 ✅ (2026-09-05) — desconcentração territorial com reconcentração institucional.** Municípios com ao menos uma instituição financeira sediada, série IF.data: **586 em 2000 → pico de 690 em 2009 → 464 em 2025**. São **226 municípios (33%) que perderam a sede que tinham**, em queda contínua desde 2010, sem reversão. No mesmo período o **número de instituições subiu de 2.114 (2010) para 2.295 (2025)** — o sistema financeiro ganhou instituições e perdeu territórios ao mesmo tempo. As novas (fintechs, SCDs, instituições de pagamento) nascem nas capitais; as que somem eram cooperativa e banco de praça do interior.
- **T67-5 ◐** Coerente com T75-3: o BNDES automático cobre 4.772 municípios contra 379 do não-automático, e a presença bancária é a hipótese óbvia — mas o crédito automático opera por banco credenciado, que **não precisa ter sede** no município. A pergunta pede a rede de agências (ESTBAN), não a sede (IF.data).

## 68 · Convênios Federais e o Preço Político

- **T68-1 ✅ — o achado mais limpo desta rodada.** De 524.919 propostas de convênio 2015–2024: **com emenda parlamentar, 86,5% viram convênio assinado; sem emenda, 15,6%**. Razão de **5,5×**. A emenda não é um empurrão marginal — ela é praticamente o mecanismo de aprovação. Sem emenda, o SICONV é uma fila que quase ninguém atravessa.
- **T68-2 ✅ — menores e mais bem executados.** Convênios com emenda têm mediana de pedido **R$ 289 mil contra R$ 478 mil** dos sem emenda, e desembolso médio de R$ 534 mil contra R$ 1,00 milhão. Mas executam melhor: **52,2% do repasse desembolsado contra 31,8%**. O convênio com padrinho é menor e sai do papel; o sem padrinho é maior, raro e trava.
- **T68-3 ✅ — o filtro fiscal não morde.** Pendências no CAUC × taxa de sucesso proposta→convênio: **r_parcial = −0,001**. Zero. A exigência de regularidade fiscal, na prática, não seleciona quem consegue convênio — o que T68-1 explica: quem seleciona é a emenda.
- **T68-4 ✅ (2026-09-05, resposta negativa)** **O convênio federal não deixa rastro físico observável — deixa o rastro inverso.** Desembolso de convênio per capita × cobertura 4G/5G **r = −0,32**, × conectividade IBC **−0,26**, × obras em construção no CNEFE **−0,17**, × PIB per capita **+0,01**. O único sinal positivo é com estabelecimentos de saúde por domicílio (**+0,13**). A leitura correta não é que o dinheiro suma: é que o convênio per capita é **maior justamente nos municípios pequenos e mal servidos** (a divisão por população pequena infla o indicador), e o volume não é suficiente para mover a infraestrutura observável. Convênio federal per capita é um indicador de *pequenez*, não de investimento.
- **T68-5 ✅ (2026-09-05) — é a mesma cadeia, e ela tem uma ponta suja.** Fornecedores PJ distintos: **200.877 no SICONV** (pagamentos de convênio) e **397.013 no PNCP**. A interseção é de **42.623 CNPJ (21% dos do SICONV)** — atendem convênio e licitação. Cruzando com o CEIS/CNEP: **1.901 fornecedores do SICONV estão sancionados**, e **960 deles estão nos três — convênio, PNCP e lista de sanção da CGU simultaneamente**. Ou seja, quase mil empresas com sanção administrativa vigente circulam pelos dois canais de dinheiro público ao mesmo tempo.

## 69 · CAUC, Conformidade Fiscal e Filantropia Tributária

- **T69-1 ◐** O município mediano tem **1 pendência no CAUC**; média 1,91; 2.198 municípios (39%) estão limpos e 57 têm 10 ou mais. Pendência acompanha pobreza (**+0,31 com Bolsa Família bruto**), mas cai a **+0,11 parcial** — é mais sintoma de pobreza que de descaso, e o resíduo próprio é pequeno.
- **T69-2 ✅ — o gargalo é contábil, não de transparência.** Pendências por item: **3.4.1 (Matriz de Saldos Contábeis) 1.509 municípios**, 1.5 (regularidade perante o poder público federal) 1.262, 1.1 (tributos federais) 1.019, 3.1.1 (publicação do RGF) 636, 3.2.2 (RREO ao Siconfi) 407. O item de transparência eletrônica (3.6) tem **8 pendências** em 5.570 municípios. O Brasil municipal publica; o que ele não consegue é fechar a contabilidade no padrão exigido.
- **T69-3 ✅** **A infraestrutura da filantropia fiscal está onde o doador está.** Municípios com fundo habilitado a receber doação dedutível do IRPF: **4.389 de 5.570**. Contagem de fundos × conectividade **+0,44**, × formalidade **+0,43**, × PIB pc **+0,39**, × cobertura do Bolsa Família **−0,41**. Mas o efeito é quase todo renda e porte: **r_parcial contra Bolsa Família = −0,09**. Ou seja, o desenho não discrimina ativamente contra o município pobre — ele simplesmente reproduz a geografia da capacidade administrativa.
- **T69-4 ✅ (2026-09-06) — o bloqueio anterior estava errado: a finalidade está em `nome_empresarial`.** `tipo_fundo` é esfera (M/E/N), mas o nome do fundo separa a finalidade sem ambiguidade: **4.275 registros de fundo da criança e do adolescente e 2.181 do idoso** (de 6.471). Municípios com fundo da criança habilitado: **4.248**; com fundo do idoso: **2.158**. **O fundo da criança é quase universal e neutro** — × notificação de violência contra adolescente **r = +0,02**, × PIB per capita +0,05, × pobreza −0,04: ele existe em todo lugar, independentemente de qualquer coisa. Por quintil de violência notificada, a fração de municípios com fundo vai de **66,8% (menor violência) a 82,4% (maior)** — cobertura levemente maior onde a notificação é maior, mas a notificação, como já mostrado em T28-1, mede vigilância. **O fundo do idoso é o oposto: é seletivo e elitista** — × PIB per capita **+0,29**, × formalização **+0,36**, × cobertura do Bolsa Família **−0,33**. A infraestrutura de doação dedutível para a criança chegou ao país inteiro; a do idoso ficou onde há dinheiro.
- **T69-5 ◐** CAUC × habilitação DIRPF: **r = −0,17** — municípios com pendência habilitam menos, mas habilitam. A regularidade não é pré-requisito para doação privada, como suspeitado.

## 70 · O Território Lido pelo Endereço (CNEFE)

- **T70-1 ✅ — dado impecável nesses campos.** **Zero endereços sem CEP e zero sem logradouro** nos 111.102.875 registros. Nenhum município tem lacuna. Ao contrário da maioria das fontes deste espelho, o CNEFE não precisa de tratamento de nulos em endereçamento.
- **T70-2 ✅** Ver T65-2 — a densidade de templos medida no CNEFE (edificação física, código de espécie 8) é proxy melhor que a contagem de CNPJ religioso, e a associação com pobreza dobra e passa a resistir ao controle de renda.
- **T70-3 ✅ — o canteiro de obras do Brasil é autoconstrução.** Densidade de "edificação em construção/reforma" por mil domicílios contra PIB per capita, por quintil: **R$ 40,6 mil → 30,8 → 21,8 → 17,3 → 14,6 mil**. Contra a cobertura do Bolsa Família: **0,083 → 0,119 → 0,196 → 0,267 → 0,298**. Quanto mais pobre o município, mais obra em andamento por domicílio — o oposto da intuição de que construção segue investimento. Mediana nacional: 43,7 obras por mil domicílios. O efeito parcial é modesto (**+0,11**), então a maior parte é composição de renda, mas o sinal bruto é inequívoco e inverso ao esperado.
- **T70-4 ✅** **O apagão digital é rural, não pequeno.** Densidade agropecuária no CNEFE × cobertura 4G/5G, por quintil: **97,7% → 89,9 → 82,7 → 76,2 → 64,6**; **r_parcial = −0,55** (B2) — a maior correlação parcial de todo o painel novo. Descontados população, renda e UF, o que resta explicando cobertura móvel é literalmente quantos endereços do município são fazenda.
- **T70-5 ◐** Domicílios por CEP × cobertura do Gás do Povo: **r_parcial = +0,14**. É proxy de ruralidade utilizável, mas fraco preditor logístico.

## 71 · Arboviroses e Doenças Negligenciadas

- **T71-1 ◐** Chikungunya e zika têm geografias muito parecidas: **r = +0,63 bruto, +0,48 parcial** entre taxas por 100 mil. Chikungunya está em **5.230 municípios** (mediana 298/100 mil entre os afetados), zika em 4.269 (mediana 71). A co-circulação não é explicada pela densidade de estabelecimentos de saúde do CNEFE (r = −0,07).
- **T71-2 ◐** **Malária e garimpo estão no mesmo lugar, mas não em proporção.** Nos 81 municípios com alerta DETER de mineração, a mediana de malária é **5,55/100 mil contra 0,00 no resto da Amazônia Legal**. Dentro do grupo, porém, mais garimpo alertado não significa mais malária (**r = +0,12**). Itaituba/PA: 93,5 km² de garimpo alertado, 38,9 casos/100 mil, 44,1 homicídios/100 mil. Jacareacanga/PA e Calçoene/AP repetem o padrão.
- **T71-3 ◐** Chikungunya × cobertura do Bolsa Família: **+0,33 bruto**, mas **−0,04 parcial**. A doença parece de pobre e é, na verdade, de região e de densidade — não sobra efeito de pobreza próprio.
- **T71-4 ✅ (2026-09-05, resposta negativa)** **Não é mais doença de saneamento — é doença de pobreza com vigilância.** Esquistossomose (2.658 municípios com caso) × cobertura de esgoto do SNIS: **r = +0,15** (positivo — mais esgoto tratado, mais notificação: é captação, não causa); × cobertura de água **−0,01**. Contra a renda: **−0,24 com PIB per capita, +0,18 com cobertura do Bolsa Família, −0,22 com conectividade**. **A renda prevê a esquistossomose melhor que qualquer indicador do SNIS.** O determinante mudou: o caracol some com a infraestrutura, mas a notificação sobrevive onde pobreza e vigilância coexistem.
- **T71-5 ◐ (2026-09-05) — o bioma sim, o remanescente local não.** Das 39.517 notificações de febre amarela, **29.688 (75%) estão em municípios de bioma Mata Atlântica** e 9.131 no Cerrado; a Amazônia tem 224 (0,6%). A doença é, sim, da interface floresta-cidade **da Mata Atlântica**. Mas dentro dos 2.056 municípios com notificação a taxa por 100 mil **não** acompanha o remanescente florestal local (**r = −0,09** com a fração de vegetação natural) e é *menor* onde há mais desmatamento acumulado (**−0,32**). É fenômeno de escala regional — corredor de mata mais primata hospedeiro —, não de quanto verde sobrou dentro do limite municipal.

## 72 · Desastres Reconhecidos e Risco Climático

- **T72-1 ✅** Dos 1.237 reconhecimentos vigentes (jan–jul/2026): **Estiagem 489, Chuvas intensas 449, Seca 133**, inundações 45. Seca + estiagem = **50%** de tudo. Por UF: **PB 147, MG 144, PE 143, RN 125, RS 114** — o semiárido e o RS pós-2024 dominam.
- **T72-2 ◐** Municípios com desastre reconhecido têm pior conectividade: **r_parcial = −0,18**. Sinal consistente com a hipótese, magnitude modesta.
- **T72-3 ❌ **SEM RESPOSTA** — bloqueio de série confirmado (2026-09-05).** `br_sedec_desastres.reconhecimentos_vigentes` traz só o que está **vigente** (1.237 registros, jan–jul/2026). "Captou mais convênio no ano seguinte" exige saber quando cada município foi reconhecido em anos anteriores, e essa história não está no espelho. *Achado colateral relevante em T74-4*: o texto integral dos diários mostra 401 municípios declarando emergência ou calamidade, contra 83 que também aparecem na SEDEC — a declaração local, essa sim, tem data e é rastreável.
- **T72-4 ❌ **SEM RESPOSTA**** Mesmo bloqueio de série do item anterior: sem histórico de reconhecimento não há "pico" para casar com a inadimplência rural do SCR.data. O lado do SCR está pronto (série mensal 2012–2026 por UF e modalidade, ver T66-2); falta o lado do desastre.
- **T72-5 ◐** Desastre × densidade agropecuária no CNEFE: **r_parcial = +0,18**; × desmatamento +0,15. Recorrência não é mensurável com reconhecimentos apenas vigentes.

## 73 · Terceirização no Executivo Federal

- **T73-1 ✅** **O governo federal paga 2,5× o salário do terceirizado.** Mediana: custo mensal R$ 4.352 para salário de R$ 1.731 no ensino médio completo. Base: 161.274 postos com escolaridade declarada em 2023, 179.220 pessoas, 2.718 empresas.
- **T73-2 ✅ — a margem é regressiva.** Razão custo/salário por escolaridade: **superior incompleto 1,87 | superior completo 2,08 | técnico 2,11 | médio completo 2,51 | sem exigência 2,69 | médio incompleto 2,75 | fundamental incompleto 2,79 | fundamental completo 2,97 | alfabetizado 3,31**. Quanto menos escolaridade o posto exige, maior a fatia que fica com o intermediário. No topo, o trabalhador recebe 53% do que o governo paga; na base, 30%.
- **T73-3 ✅** **1.261 das 7.905 empresas de terceirização (16%) constam do CEIS/CNEP da CGU.** Entre as maiores empregadoras sancionadas: PROVIDER SOLUÇÕES TECNOLÓGICAS (em recuperação judicial, 2.278 + 2.165 postos em duas grafias de razão social), DEFENDER CONSERVAÇÃO E LIMPEZA (725), CRIART TERCEIRIZAÇÃO DE MÃO DE OBRA (717). Uma em cada seis empresas que fornecem gente ao Executivo federal está em alguma lista de sanção da própria CGU.
- **T73-4 ◐ (2026-09-05)** A série termina em 2023, então "mudou entre os anos" não é respondível como tendência. O retrato de 2023: **179.220 pessoas em 2.718 empresas**, e as 6 maiores empregadoras concentram 9.517 postos (5,3%) — mercado pulverizado em número de empresas, mas com uma cauda grossa de fornecedores de milhares de postos cada, dois dos quais (PROVIDER, em duas grafias) estão em recuperação judicial e sancionados.
- **T73-5 ❌ **SEM RESPOSTA** — bloqueio de chave confirmado (2026-09-05).** As duas pontas existem mas não casam: `cgu_pessoal_executivo_federal.terceirizados` identifica o órgão por **sigla truncada** (`sigla_orgao_superior_unidade_gestora`, com valores cortados em 8 caracteres — "MINISTER", "MINIST. "), enquanto `cgu_viagens.viagem` traz o **nome por extenso** ("Ministério dos Direitos Humanos e Cidadania"). Além disso, `valor_diarias` e `valor_passagens` em `viagem` vêm como texto não numérico e somam nulo. Sem um crosswalk de órgão e sem valor limpo de viagem, a razão terceirizado/efetivo por órgão contra o gasto de viagem não é construível.

## 74 · Diários Oficiais como Sinal de Estado

- **T74-1 ◐** Tamanho médio do diário × nº de fornecedores no PNCP: **r = +0,66** (n=443) — mas é quase todo porte do município (tamanho do diário × população = +0,63). Como proxy de complexidade administrativa, o tamanho do diário não adiciona muito além de contar habitantes. O resíduo interessante: × taxa de sucesso em convênios, **r_parcial = +0,15**.
- **T74-2 ✅ — enviesado e pequeno.** **Só 524 dos 5.570 municípios (9,4%) têm diário raspado no Querido Diário**, contra 4.687 no PNCP. Cobertura 2023-07 a 2025-10. Os presentes são maiores, mais ricos (tamanho do diário × PIB: +0,51) e mais de serviços (× share de serviços +0,56); ficam de fora justamente os municípios de perfil agropecuário (**× densidade agro = −0,57**). Qualquer análise de transparência baseada no Querido Diário mede a elite urbana municipal, não o país.
- **T74-3 ◐ (2026-09-05)** Fatia de edições extras no diário × número de contratos no PNCP: **r = +0,34** (n=440), × contratos por fornecedor **+0,25**, × população **+0,27**. O sinal é consistente com a hipótese, mas não a separa do tamanho do município — e o marcador de emergência do PNCP não é utilizável (ver T62-5). Edição extra é indicador de volume administrativo, não necessariamente de urgência.
- **T74-4 ✅ (2026-09-05) — o município declara muito mais do que o federal reconhece.** Busca por "situação de emergência" ou "estado de calamidade" nos **231.897 diários com texto integral**: **2.376 publicações em 401 municípios** — isto é, **77% dos 524 municípios com diário raspado já publicaram declaração de emergência ou calamidade** entre jul/2023 e out/2025. Cruzando com os reconhecimentos vigentes da SEDEC (1.147 municípios): apenas **83 municípios aparecem nos dois**. A assimetria é dos dois lados e ambos são informativos: a maioria das declarações municipais **não** tem reconhecimento federal vigente (o reconhecimento é posterior, temporário e frequentemente negado), e a maioria dos reconhecidos pela SEDEC **não** tem diário no Querido Diário (T74-2, cobertura de 9,4%). **A declaração local é a instância mais frequente e a menos visível — só o texto integral do diário a captura.**
- **T74-5 ✅ (2026-09-05) — sim, e a escala surpreende.** Extraindo todo CNPJ no formato canônico dos 231.897 diários com texto integral: **449.693 CNPJ distintos citados**. Cruzando com o CEIS/CNEP: **2.755 empresas sancionadas aparecem citadas nos diários oficiais, em 482 dos 524 municípios cobertos (92%)**. Ou seja, praticamente todo município com diário raspado publica, em algum ato, o CNPJ de uma empresa que está em lista de sanção da CGU. Isso **não** é prova de contratação irregular — o diário cita CNPJ por muitos motivos (habilitação, inabilitação, notificação, o próprio ato de sanção), e a sanção tem prazo e abrangência específicos. Mas estabelece que **o método funciona e é barato**: `regexp_extract_all` sobre o texto integral produz uma lista de CNPJ por município em uma passada, e o cruzamento com o CEIS é imediato. **É o caminho pronto para uma auditoria de contratação municipal que o PNCP, com seu `emendaParlamentar` 99,4% nulo (T62-5), não permite.**

## 75 · BNDES, Fomento e Geografia do Crédito

- **T75-1 ✅** Crédito BNDES per capita × formalização (**r = +0,68**) contra × PIB per capita (**+0,68**) — empatados no bruto. O parcial mostra que a formalidade é o canal: **+0,26 parcial com formalidade** depois de descontar renda. O banco de fomento financia onde já existe carteira assinada.
- **T75-2 ◐** Taxa de juros média do BNDES × peso agropecuário: **r_parcial = +0,21** (n=379, só operações não-automáticas, que têm taxa preenchida). Risco setorial vira preço, mas a amostra é pequena e enviesada para operações grandes.
- **T75-3 ✅ — o intermediário multiplica o alcance por 12,6.** Operações indiretas automáticas (via banco credenciado) 2019+: **4.772 municípios, 385.143 operações**. Não-automáticas (direto no BNDES): **379 municípios, 5.100 operações**. Sem a rede credenciada, o fomento federal atinge 6,8% do país.
- **T75-4 ✅ (2026-09-05)** **O fomento acompanha o agro, mas não a fronteira.** Fatia agropecuária do BNDES automático por município × peso agropecuário no PIB: **r = +0,46** (esperado). Mas × desmatamento acumulado apenas **+0,13** e × alerta DETER **+0,11** — e × número de imóveis no CAR **−0,19**. O BNDES agro está no agro consolidado do Sul, Sudeste e Centro-Oeste, não no arco de desmatamento. Quem financia a fronteira, se alguém financia, não é o banco de fomento.
- **T75-5 ✅ (2026-09-05, nível UF) — o porte do tomador não segue o porte da economia.** A fatia MPE do BNDES não-automático só tem valor não-nulo em 27 UFs, então a resposta é estadual. Contra a fatia de micro e pequenas no cadastro CNPJ local (mediana nacional **83,1% dos estabelecimentos ativos**): **r = +0,22 — fraco**. Contra o tamanho: **−0,71 com população e −0,70 com o número absoluto de microempresas**. A fatia MPE é maior nas UFs pequenas justamente porque nelas **não há grande tomador** para absorver a carteira, não porque o banco mire o pequeno. Onde há muita microempresa (SP, MG, RJ), a carteira do BNDES é das grandes.

## 76 · Senado: Produção Legislativa e Custo Administrativo

- **T76-1 ✅ — desbloqueado.** O espelho passou a ter `processo` (162.678 proposições), `votacao_parlamentar` (288.855 votos nominais), `discurso` (99.620), `relatoria`, `senador_comissao`. Isso **fecha o bloqueio T05-2**, que estava registrado como "o espelho não tem tabela de proposições do Senado — pipeline necessário". A comparação Câmara×Senado é agora possível sem scraping novo.
- **T76-2 ✅ — palavra e verba não andam juntas; andam em direções opostas.** Entre os 87 senadores com mais de 100 votações registradas (2023–2025): discursos × CEAPS **r = −0,16**. Presença efetiva × CEAPS: **−0,04** (nada). Discursos × presença: +0,22. Medianas: 119 discursos e R$ 495 mil de CEAPS no triênio.
- **T76-3 ✅ — distância, não atividade.** CEAPS médio por senador e UF: **AM R$ 614 mil, SE R$ 586 mil, RR R$ 570 mil, AP R$ 561 mil** contra **GO R$ 164 mil, PR R$ 247 mil, MG R$ 287 mil, RJ R$ 333 mil, DF R$ 337 mil**. AM gasta **3,7× o GO**. E a atividade não acompanha: o DF, com o menor gasto entre os baixos, tem a **maior média de discursos (425,5)**; o AM, com o maior gasto, tem 181,7. Sergipe gasta R$ 586 mil com 105 discursos médios; Minas gasta metade disso com 260.
- **T76-4 ✅ (2026-09-05) — o Senado é mais disciplinado que a Câmara, e a diferença inteira é do centrão.** Índice de Rice 2023+ nos partidos presentes nas duas casas: **UNIÃO 0,78 no Senado × 0,64 na Câmara** (+14 pontos), **PSDB 0,86 × 0,71** (+15), **MDB 0,87 × 0,72** (+15), **PP 0,83 × 0,74**, **PSD 0,81 × 0,76**. Os ideológicos ficam iguais ou caem: **PT 0,94 × 0,97**, **PDT 0,86 × 0,90**, **PSB 0,85 × 0,88**. **A disciplina de um partido de centro é ~15 pontos maior no Senado; a de um partido ideológico é a mesma nas duas casas.** Hipótese testável: bancada senatorial de 3 por estado fecha questão com muito menos custo de coordenação que uma bancada de 50 deputados.
- **T76-5 ✅ (2026-09-05) — estruturais, e o pico não é legislativo.** Hora extra média mensal dos servidores do Senado (2023–25) × votações nominais no mesmo mês: **r = +0,28 — fraco**. **Agosto é o mês de maior atividade legislativa (41 votações em média) e tem hora extra abaixo da mediana** (R$ 1,06 milhão). O pico é **julho: R$ 4,38 milhões, 3,6× a mediana, com 12 votações** — julho é recesso parlamentar. O segundo pico é março (R$ 2,30 milhões, 4 votações). A hora extra do Senado segue o calendário **administrativo** — fechamento de exercício, recesso, manutenção —, não o plenário.

## Achados metodológicos desta rodada (avisos para quem for reusar as tabelas)

**Ponte nova, reutilizável — SICOR → município.** `br_bcb_sicor.recurso_publico_propriedade.id_car`
tem 41 caracteres no formato **`UF(2) + código IBGE(7) + hash(32)`**, e
`TRY_CAST(substr(id_car,3,7) AS BIGINT)` devolve o código municipal do IBGE em
**99,9998%** das 12,54 milhões de linhas (2020+). Nenhuma outra tabela do SICOR
tem município — `operacao` só tem `sigla_uf`. Isso destrava o crédito rural no
recorte municipal (R$ 934,9 bi em 5.564 municípios, 2020–24) sem join com o
SICAR, e fechou T07-3, T07-5, T17-2, T17-3 e T17-5 de uma vez. **Vale registrar
em `docs/context/bridges.yaml`.**


- **`br_pncp.contratos.valorGlobal` é inutilizável em soma.** R$ 47,7 trilhões no total, 406 contratos acima de R$ 1 bi, casos verificados de R$ 2,37 trilhões num credenciamento de profissional de saúde municipal. Usar mediana/quantis, ou winsorizar em p99 e dizer que winsorizou.
- **`br_pncp.contratos.emendaParlamentar` é 99,4% nulo** — não mede nada.
- **`br_sfb_sicar.area_imovel`: a soma de áreas excede a área municipal em 5.563 de 5.571 municípios** (mediana 923×). Há sobreposição de polígonos e/ou unidade divergente. Utilizável como ranking, nunca como fração de cobertura.
- **`br_sedec_desastres` só tem reconhecimentos vigentes** (jan–jul/2026, 1.237 linhas), não série histórica — bloqueia qualquer pergunta sobre recorrência ou defasagem temporal de desastre.
- **`br_ok_queridodiario` cobre 9,4% dos municípios**, enviesado para grandes, ricos e de serviços (× densidade agropecuária = −0,57). Não representa o Brasil municipal.
- **`br_anm.scm_*` (SIGMINE processos) não tem código IBGE** — só `municipio_s` em texto livre, frequentemente com vários municípios na mesma célula. Cruzamento territorial exige normalização prévia.
- **`br_bcb_scrdata.dados` traz valores como VARCHAR com vírgula decimal e ponto de milhar** — `TRY_CAST` direto retorna NULL silenciosamente; usar `replace(replace(x,'.',''),',','.')`.
- **`br_ibge_cnefe.enderecos` não tem nulo em CEP nem logradouro** nos 111 milhões de registros — exceção positiva neste espelho.
- **Mapeamento SIAFI→IBGE**: as tabelas do Portal da Transparência (Novo Bolsa Família, Gás do Povo, Seguro-Defeso, Pé-de-Meia, Garantia-Safra) usam `codigo_municipio_siafi`, não `id_municipio`. O join por nome normalizado + UF contra `br_bd_diretorios_brasil.municipio` recupera **5.556 dos 5.571** códigos.


## Multi-referência (seção final)

Respondidas em 2026-09-03 com Claude direto no beelink (não pelo harness Gemma),
pra servir de gabarito de comparação — ver nota no topo de cada uma sobre a
simplificação metodológica feita (essas cadeias, como pedidas em `perguntas.md`,
exigiriam pipeline dedicado; o que segue é o cruzamento cross-seccional viável
numa sessão, não a reconstrução de coorte/causal completa).

- **M1 ✅ (proxy)** *Trajetória raça → mercado → morte* (RAIS × CAGED × SIM, 2022,
  n=4.245 municípios ≥5.000 hab): **sem evidência de acúmulo territorial das três
  desvantagens**. Lacuna racial de rendimento (RAIS) × rotatividade no mercado de
  trabalho (CAGED, movimentações per capita) × mortalidade geral (SIM, óbitos/100k)
  — correlações par a par fracas a desprezíveis, **r entre −0,07 e +0,11**. Dos
  municípios no pior terço nas três dimensões simultaneamente, só **102** —
  *abaixo* do esperado por acaso (~157) se fossem independentes. Proxy: usei
  mortalidade **geral**, não especificamente "causas evitáveis" (categoria exige
  agrupamento CID que não montei); rotatividade é volume de movimentação CAGED
  per capita, não a taxa clássica sobre estoque de vínculos.
- **M2 ✅ (proxy)** *Escola → conectividade → eleição* (Anatel IBC Δ2021→2024 ×
  ENEM redação Δ2018→2022 por escola × TSE presidencial Δ2018→2022, n≈4.230):
  **conectividade não moveu a nota** — r≈0 (−0,01) entre Δ IBC e Δ redação.
  Δ IBC × Δ % Lula: **r=+0,27**, mas confundido — a comparação troca de candidato
  (Haddad 2018 → Lula 2022, ambos PT mas bases diferentes) e conectividade já
  correlaciona com alfabetização de base (r=+0,27): quem tinha mais infra
  educacional ganhou mais conectividade depois. Não dá pra separar investimento
  de perfil prévio com este desenho — precisaria de painel com mais pontos no
  tempo e controle por candidato.
- **M4 ✅** *Desmatamento → crédito → produção → sanção fundiária* (PRODES ×
  SICOR × SICAR × PPM, todos os municípios): **confirma e estende A1/A2**.
  Desmatamento acumulado (PRODES 2023) × crédito rural total liberado (SICOR,
  todos os anos): **r=+0,58** (n=5.540); × área de imóveis CAR com pendência
  (SICAR, status PE): **r=+0,39** (n=4.539); × nº de imóveis pendentes: r=+0,45.
  Top do ranking: **São Félix do Xingu/PA** — 21.299 km² desmatados, R$ 1,34 bi em
  crédito rural, 2,52 milhões de cabeças de gado (maior rebanho do país nesse
  recorte) e 11,3 milhões de ha em imóveis CAR "pendente" — **mais que a área do
  município inteiro** (8,4 milhões de ha): evidência de sobreposição de polígono
  autodeclarado no CAR, não de área líquida real — tratar como proxy de volume de
  pendência, não medida de área limpa.
- **M5 ✅ (proxy)** *Nascimento → escola → trabalho → óbito juvenil* (SINASC ×
  Sinopse INEP × RAIS jovem 18-24 × SIM 15-29, 2022, n=3.993 municípios ≥5.000
  hab): correlações fracas, sem clusterização forte. Natalidade × matrícula ensino
  médio per capita: r=+0,37 (esperado); × vínculo jovem formal: r≈0; × óbito
  jovem/100k: r=+0,24. Vínculo jovem × óbito jovem: **r=−0,19** (mais emprego
  formal, menos morte — direção esperada, mas fraca). Só **8 municípios** (de
  3.993) caem no pior quartil nas 4 dimensões simultaneamente — abaixo do
  esperado por acaso (~15,6). Exemplos onde o ciclo mais se rompe: Pauini/AM, Alto
  Alegre/RR, Portel/PA — interior Norte/Nordeste, mortalidade jovem 44-71/100k
  (2-4x a taxa nacional nessa faixa). Proxy: cross-seccional 2022, não coorte
  longitudinal de nascidos acompanhados ao longo da vida.
- **M3 ⏳ (tentativa Gemma falhou, 2026-09-03)** — rodada por
  `bun harness/pergunte.ts` (5 datasets, a pergunta mais rica de `perguntas.md`
  em nº de fontes: emendas → contratos → CNPJ → TCU → PGFN). **40 min, sem
  resposta**: morta pelo timeout interno do harness (`HARNESS_TIMEOUT_MS`,
  2.400.000ms, SIGKILL) — não travou infraestrutura (llama-server seguiu
  saudável depois), o laço agêntico simplesmente não convergiu numa cadeia de
  5 fontes dentro do orçamento. Consistente com o padrão já registrado em
  `harness/tasks/backlog.md` item 2 (casos multi-tabela custam ~36 min/caso e
  às vezes voltam vazios mesmo assim) — essa é a pergunta mais exigente que já
  foi testada no harness, então o resultado é o esperado, não uma surpresa.
  Não respondida por este método; componentes já medidos manualmente:
  T37-1/T37-5.

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
  Politicamente"** como o nome sugeria em `tasks/datasets_coverage_gaps.md`
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

Não investigados na rodada de 2026-08-25 (esse parágrafo ficou desatualizado
pela rodada de 2026-09-05, que fechou boa parte do que estava listado aqui —
temas 13, 14, 17, 26, 28, 31, 33, 34, 35, 41, 42, 43 e os pendentes de 57–76).
T40-5 segue `⏳` por bloqueio já mapeado acima (CAPAG sem série temporal), não
por falta de investigação.

## Bateria de hipóteses H01–H19 (2026-09-06)

Rodada completa de [`scripts/hipoteses_overnight.sh`](../scripts/hipoteses_overnight.sh)
no beelink: 5 blocos SQL + análise, **88 segundos**, painel de **5.571 municípios ×
164 colunas**. Estas não são perguntas de `perguntas.md` — são as hipóteses de
[`tasks/hipoteses.md`](../../tasks/hipoteses.md), cada uma com a condição de
falseamento escrita antes de rodar. O resultado está reportado **inclusive quando
nega a hipótese**, que é a maior parte das vezes.

Todo `r` é Spearman. `parcial` residualiza log-população, log-PIB per capita e
efeito fixo de UF; onde as duas pontas são **extensivas** (contagem, área, valor)
entra também **log-área do município** — sem isso a correlação é em boa parte
"município grande tem mais de tudo", e foi exatamente esse controle que derrubou
o D1 (ver abaixo).

### Bloco A · MIDES — 392 milhões de pagamentos municipais com CNPJ do credor

Fonte destravada nesta rodada: `world_wb_mides.pagamento` tem `id_municipio`
**e** `documento_credor`. É a primeira tabela do espelho que permite seguir
dinheiro público **municipal** até a empresa. Recorte usado: `ano >= 2018`,
**3.339 municípios**, R$ 2,06 trilhões nominais.

| # | Hipótese | Veredito | Números |
|---|---|---|---|
| **H01** | A concentração de credores é maior onde há **menos empresa local**, não onde há mais pobreza | ❌ **Falseada como formulada** | HHI de pagamento (n=3.060): mediana **0,167**; o maior credor sozinho leva **38,5%** do valor no município mediano, e **>50% em 234 municípios**. Mas o HHI acompanha pobreza (**parcial +0,14**) tanto quanto acompanha — invertida — densidade empresarial (**−0,13**). Nenhuma das duas domina: a condição de falseamento ("HHI acompanhar pobreza e não densidade") se cumpriu pela metade, e o espelho não separa as duas a n=3.060 |
| **H02** | Município pequeno paga mais a fornecedor **de fora** — a compra pública vaza para o polo regional | ◐ **Direção confirmada, efeito fraco** | Credor sediado no próprio município: **49,4% dos pagamentos** no agregado, mediana municipal **42,2%**. Sobe monotonicamente com o porte — quintis de população **35,2% → 50,5%** — mas o parcial é só **+0,11**. O vazamento existe; quase todo ele é porte, e porte já está no controle |
| **H03** | A fatia paga a empresa **sancionada** é maior onde a transparência é pior | ❌ **Nula** | Municípios pagaram **R$ 18,4 bilhões** a empresa no CEIS/CNEP (0,80% do valor **entre os 3.339 municípios com pagamento no MIDES**; mediana municipal 0,49%, p90 2,12%. Sobre todos os município-ano com qualquer pagamento a base é 0,71% — usar esta ao comparar com o H05). Contra a nota EBT: **+0,05** (n=345). Contra pobreza: **−0,04**. **Confirma E3 por outro caminho** — a nota de transparência não prevê conduta |
| **H04** | Devedor da PGFN recebe pagamento municipal na mesma proporção que recebe federal | ✅ **Respondida, e o valor é desproporcional** | **12,2% dos credores municipais** devem à PGFN (mediana municipal 12,8%), mas levam **22,7% do valor** — R$ 467,6 bi de R$ 2.063,7 bi. Devedor não é exceção do fornecedor municipal: é o fornecedor **grande**. Compare com T37-2 no federal (25.643 vencedores, R$ 241,7 bi) |

### Bloco B · CGU FEF — a fiscalização por sorteio

`br_cgu_fef.microdados`: **82.664 ordens** em **1.352 municípios**, até 3 ciclos
de sorteio, R$ 376,8 bi fiscalizados. É o desenho mais próximo de experimento no
espelho — o município é **sorteado**, não escolhido.

| # | Hipótese | Veredito | Números |
|---|---|---|---|
| **H05** | Município auditado muda de comportamento depois | ❌ **Falseada — e o nulo tem limite quantificado, não é só "sem diferença"** | Extração nova (`scripts/hipoteses/70_temporais.sql`+`98_temporais.py`, 2026-09-06): fatia paga a sancionado (MIDES) em janela de 3 anos antes/depois do sorteio FEF, 351 municípios sorteados com pré e pós observados contra 1.254 não-sorteados (placebo no ano mediano do sorteio, 2010). Δ médio sorteado **−0,053 p.p.**, Δ médio não-sorteado **−0,111 p.p.** — diferença-em-diferenças **+0,058 p.p., p=0,51** (permutação, 5.000 draws), IC95% **±0,17 p.p.** (desvio-padrão da distribuição nula). Sinal contrário ao esperado (sorteado caiu **menos**), e o IC descarta qualquer efeito de fiscalização maior que **~24% da fatia média paga a sancionado (0,71%)** — é o único desenho quase-experimental do espelho, e um nulo com bound vale mais que a leitura solta de "sem diferença detectável". A perna do CAUC ficou de fora: `br_tesouro_cauc.situacao_municipios` é fotografia única (uma `data_pesquisa` fixa), sem dimensão de tempo — estruturalmente sem como fazer pré×pós |
| **H06** | A taxa de constatação **grave** não acompanha pobreza — o que varia é a chance de ser pego | ✅ **Confirmada** | Share grave mediano **11,4%**. Contra pobreza: bruto +0,37 → **parcial +0,08**; contra PIB pc: −0,30 → **−0,05**. A irregularidade grave é praticamente uniforme depois do controle; o bruto era renda disfarçada |
| **H07** | O montante fiscalizado por habitante marca onde a União concentra **risco** | ◐ **Fraca** | Contra pobreza: bruto +0,56 → **parcial +0,14**. Sobra alguma concentração em município pobre, mas quatro quintos do bruto eram escala |

### Bloco C · Longo prazo da transferência de renda

| # | Hipótese | Veredito | Números |
|---|---|---|---|
| **H08** | Exposição acumulada ao PBF (2004–2020) reduziu mais o IVS/mortalidade — efeito de dose | ❌ **Falseada de novo, com a janela certa — e mais robusta do que parecia** | Teste original (ΔIVS 2000→2010): bruto −0,14, parcial −0,19, +IVS 2000 vira +0,15 — mas a janela é errada por construção (desfecho 2000-2010, 2/3 da exposição é posterior a 2010). Teste honesto (2026-09-06, `98_temporais.py`): mortalidade infantil 2021-2024 (SIM, óbitos 0-1 ano ÷ nascidos SINASC, municípios com ≥100 nascimentos, n=4.746, mediana 10,07‰ — na vizinhança da TMI nacional 11-13‰) × `pbf_valor_acumulado`. Bruto **+0,22**, parcial (pop/PIB/UF) **+0,11**, **+IVS 2000 no controle +0,07** — positivo, não negativo. **Ressalva testada, não só anotada** — em três rodadas: (a) PBF acumulado **per capita** (tira o mecânico de tamanho de população): parcial+IVS0 **+0,057**; (b) controlando também **cobertura atual do Bolsa Família** (`nbf_share_dom`, proxy de pobreza contemporânea): **+0,077**, praticamente igual ao +0,074 sem esse controle; (c) **especificação decisiva** — diagnóstico da sessão paralela de que `pbf_valor_acumulado` é **extensivo** (r=+0,78 com população, mais forte que os +0,60 com `nbf_share_dom`) e resíduo em rank de log-população não absorve variável extensiva, a mesma armadilha do D1 (CAFIR × desmatamento, ver "avisos de dado" em `achados_fortes.md`): per capita **e** `nbf_share_dom` no **mesmo** controle, juntos — **+0,057**, idêntico à versão só-per-capita. O critério de falseamento da própria sessão que propôs o teste ("se sobrar +0,05, o resíduo é real") se cumpriu: nem escala nem pobreza (histórica ou contemporânea) explicam o residual em nenhuma das cinco especificações rodadas. Dose de PBF não prevê menos mortalidade infantil depois em nenhuma delas — o residual positivo é **robusto**, não artefato de confound mecânico, mas também não é interpretável causalmente sem instrumento (é correlação, não desenho experimental) |
| **H09** | A razão PBF 2019/2006 separa quem **saiu** da pobreza de quem só cresceu | ◐ **Nem uma coisa nem outra** | Razão mediana **1,04** (p10 0,50 · p90 1,81). Contra formalização: −0,35 → **parcial −0,11**; contra crescimento populacional: +0,15 → **+0,14**. As duas pernas ficam na mesma ordem de grandeza — a razão não é explicada só por crescimento (a condição de falseamento), mas também não separa nada com força |

### Bloco D · Famílias nunca cruzadas

| # | Hipótese | Veredito | Números |
|---|---|---|---|
| **H10** | Reclamação no Consumidor.gov mede **acesso digital**, não lesão ao consumidor | ✅ **Confirmada — o achado mais limpo da bateria** | 9,92 milhões de reclamações, 5.563 municípios. Contra penetração do Pix: bruto +0,47 → **parcial +0,29**; contra conectividade (IBC): +0,54 → **+0,28**; contra pobreza: −0,44 → **−0,16**. Quintis de reclamação por 100 mil hab → penetração do Pix **0,516 → 0,637**, e pobreza **0,345 → 0,096** monotônicos. Reclamar é privilégio de infraestrutura |
| **H11** | A nota do consumidor é pior onde há menos concorrência local | ❌ **Falseada** | Contra estabelecimentos RAIS: **parcial +0,05**; contra PIB pc: **+0,02**. Ortogonal à densidade de CNPJ — exatamente a condição de falseamento escrita |
| **H12** | Município de pesca artesanal tem perfil social distinto do agrícola de mesma renda | ◐ **Distinto, mas ao contrário do previsto na perna agro** | 1,57 milhão de pescadores em 3.860 municípios. Contra formalização: −0,33 → **parcial −0,03** (a perna de informalidade **dissolve**); contra crédito rural per capita: **−0,08**; contra densidade agropecuária CNEFE: +0,04 → **−0,17**. O município pesqueiro é menos agrícola e recebe menos crédito rural, mas não é mais informal que o agrícola de mesma renda |
| **H13** | A composição racial por instrução (Censo 2022) prevê a lacuna de gênero melhor que a renda | ❌ **Falseada — e nenhuma das duas prevê** | Perna racial (pivotada aqui pela primeira vez, `v_censo_raca` sai em formato longo e nunca entrou no painel): share negra × lacuna −0,44 → **parcial −0,07**; lacuna de superior completo entre branca e negra +0,44 → **+0,06**. Perna de renda (D4): +0,60 → **+0,11**. Renda ganha por uma margem irrelevante, e **as duas colapsam** |
| **H14** | Onde o Garantia-Safra pagou mais, a inadimplência rural subiu no ano seguinte | ❌ **Falseada** | Garantia-Safra (1.321 municípios, 2013–2026): beneficiários caem de **1,14 milhão (2013) para 315 mil (2022)** e voltam a 831 mil em 2026; brutos já conhecidos: crédito rural pc **+0,24**, formalização **−0,25**. Inadimplência do SCR (2026-09-06, `98_temporais.py`): carteira de "Financiamentos rurais", valor de dezembro por UF-ano (378 UF-anos, 27 UFs, 2012-2025), casada com GS agregado por UF via município→UF. GS(ano t) × Δinadimplência(t→t+1), n=122 UF-anos: bruto **−0,054**, com efeito fixo de UF **−0,050** — nulo, e o pouco que sobra vai na direção **contrária** à hipótese (mais GS, leve queda de inadimplência no ano seguinte, não alta) |
| **H15** | Capital social mediano prevê resiliência: capital baixo perdeu mais vínculo em 2020 | ◐ **Sobrevive, fraco** | Proxy transversal era nulo (capital social × formalização −0,02). Teste real (2026-09-06, `98_temporais.py`): Δvínculos RAIS 2019→2020 (queda mediana −0,44%, n=5.570) × capital social mediano do estabelecimento. Bruto **+0,075**, parcial (pop/PIB/UF) **+0,063**, **+ log(vínculos 2019) [porte] +0,063** — sobrevive quase sem mudar ao controlar porte, ao contrário do falseador escrito ("capital social é puro proxy de porte"). Sinal correto (capital social baixo → queda maior), mas fraco: não é achado para `achados_fortes.md`, é confirmação de baixa magnitude |

### Bloco E · Reteste dos achados que mereciam confirmação

Este bloco existe porque quatro achados publicados dependiam de parcial não
rodado. Dois caíram.

| # | O quê | Veredito | Números |
|---|---|---|---|
| **H16** | D1 (CAFIR × desmatamento, r = +0,82) controlando a área do município | ❌ **Derruba o D1 na forma publicada** | Área CAFIR × desmatado: bruto **+0,82**, parcial com pop+PIB+UF **+0,76**, **parcial acrescentando log-área: +0,31**. E na forma intensiva — **share da área municipal cadastrada × share desmatada** — sobra **+0,04** (n=5.547). Pior: essa versão vale **+0,32 dentro da Amazônia Legal e −0,00 fora dela** (n=4.779). Os quintis não são monotônicos (0,56 → 0,79 → 0,79 → 0,75 → 0,64). "A correlação mais forte já medida contra o PRODES" é, em intensidade, **escala municipal** — e fora da Amazônia é zero |
| **H17** | C1 (crédito rural × desmatamento) sob o mesmo controle | ✅ **Confirma e endurece o C1** | Crédito rural × desmatado: bruto +0,57 → **+0,64** (pop+PIB+UF) → **+0,46** acrescentando log-área. Na forma intensiva — **crédito por hectare × share da área desmatada** — sobra **+0,45 parcial** (bruto +0,54), com quintis monotônicos **0,37 → 0,61 → 0,74 → 0,82 → 0,83**, e vale igual **dentro (+0,50) e fora (+0,53) da Amazônia Legal**. Contra o alerta DETER recente, cai a **+0,09** — o crédito está no desmate **consolidado**, não na frente ativa. É o contraste que dá o achado: o **fluxo** (crédito) sobrevive à intensidade; o **estoque** (cadastro fundiário) não |
| **H18** | E1 (concentração onomástica) com o parcial completo | ❌ **Mata o E1** | Share do nome mais comum × pobreza: bruto **+0,48** → **parcial +0,03** (com área +0,04); diversidade de nomes × PIB pc: +0,29 → **−0,02**. O E1 já era reportado como "bruto forte, parcial fraco" (+0,11); com o painel completo não sobra **nada** |
| **H19** | D13 (sancionado citado em diário) contra H03 (sancionado **pago**) | ✅ **Confirma que citação ≠ pagamento** | Fatia paga a sancionado × densidade de empresa sancionada no município: **−0,04 bruto, −0,004 parcial** (n=906). Onde há sancionado sediado não se paga mais a sancionado. As duas medidas são independentes: o diário é presença, o pagamento é dinheiro |

### O que a bateria mudou nos achados publicados

| Achado | Antes | Depois |
|---|---|---|
| **D1** CAFIR × desmatamento | r = +0,82, "a mais forte contra o PRODES" | **+0,31** com área; **+0,04** em intensidade; **zero fora da Amazônia**. Rebaixado |
| **C1** crédito rural × desmatamento | +0,64 parcial | Mantido: **+0,46** com área, **+0,45** em intensidade, estável dentro e fora da Amazônia |
| **E1** concentração onomástica | "parcial fraco, +0,11" | **+0,03** — encerrado |
| **D4** lacuna de gênero × PIB pc | r = +0,61 | **+0,11** parcial; e a alternativa racial de H13 não prevê melhor. A lacuna é de município rico **no bruto**; sob controle, quase nada prevê |
| **E3** EBT não prevê integridade | medido contra sanção e CAUC | Reforçado por H03 e H05: **também** ortogonal ao dinheiro pago a sancionado e à fiscalização da CGU |

### Nulos que valem por si

Cinco resultados nulos foram medidos com n suficiente e cabem como achado
negativo, não como falta de dado:

- **H03** fatia paga a sancionado × nota EBT: +0,05 (n=345)
- **H05** ordens de fiscalização FEF × fatia paga a sancionado: +0,02 (n=620)
- **H19** fatia paga a sancionado × densidade de sancionados: −0,004 (n=906)
- **H11** nota do consumidor × densidade empresarial: +0,05 (n=5.541)
- **H15** capital social mediano × formalização: −0,02 (n=5.570)

A leitura conjunta dos três primeiros: **nada do que se publica sobre integridade
municipal prevê para onde o dinheiro municipal efetivamente vai.** Nem a nota de
transparência, nem a auditoria da CGU, nem a presença de empresa sancionada no
território.

### Método — duas decisões que mudaram o resultado

1. **Só variável intensiva entra na varredura automática.** A primeira versão
   rankeava `óbitos × nascimentos` (+0,83) e `população × nomes distintos`
   (+0,87) no topo — escala com cara de achado. Hoje a varredura roda sobre 64
   taxas e índices (1.941 pares em `correlacoes.tsv`); as 100 colunas extensivas
   ficam em `painel.csv` para uso dirigido, e as derivadas × sua fonte vão para
   `tautologias.tsv`.
2. **Par extensivo precisa de log-área no controle, não só log-população.** Foi
   o que separou H16 de H17. Os municípios de maior área da Amazônia são os de
   **menor** população: controlar população não controla área, e sem isso "área
   de imóvel rural × área desmatada" é dois tamanhos multiplicados. Rodado por
   [`scripts/hipoteses/91_parciais.py`](../scripts/hipoteses/91_parciais.py); as
   lacunas de H13/H08/H04/H14, por
   [`scripts/hipoteses/92_lacunas.py`](../scripts/hipoteses/92_lacunas.py).

### O que ficou de fora (fechado em 2026-09-06)

H05 (pré × pós do sorteio FEF), H08 (desfecho pós-2020 para a dose do PBF), H14
(inadimplência do SCR por UF) e H15 (variação de vínculos 2019→2020) exigiam
recorte temporal que os blocos 00-50 não fazem — eram de extração, não de
análise. Fechadas em 2026-09-06 por
[`scripts/hipoteses/70_temporais.sql`](../scripts/hipoteses/70_temporais.sql) +
[`98_temporais.py`](../scripts/hipoteses/98_temporais.py): **H05, H08 e H14
falseadas** (nenhuma sobrevive ao pré×pós/defasagem honesto), **H15 sobrevive
fraca** (parcial +0,06, robusta ao controle de porte). Detalhe na tabela acima.

## 77 · Cruzamentos Inéditos de Três Famílias

Extração em [`scripts/hipoteses/50_novas.sql`](../scripts/hipoteses/50_novas.sql)
(Bloco I de [`tasks/hipoteses.md`](../../tasks/hipoteses.md), H41–H45 — renumerado
de H20–H24 em 2026-09-06 por colisão com outro Bloco F escrito em paralelo no
mesmo arquivo, ver a nota no topo daquela seção), rodada como **corrida
completa** via `bash hipoteses_overnight.sh` em 2026-09-06 (isolada em
`~/hipoteses_run_blocof` no beelink para não disputar arquivo com outra sessão
rodando em paralelo). Números idênticos ao teste de fumaça anterior — não era
artefato de corte de dado. Resumo local em
[`.hipoteses/20260906_blocof/`](../.hipoteses/20260906_blocof/) (gitignorado, local).

- **T77-1 ✅** Choque de exportação (2019→2020) × Bolsa Família no ano seguinte: **r_parcial −0,06** (n=2.056) — fraco, o choque não move o PBF de forma detectável neste recorte. Choque × CAGED também nulo (+0,016, H41c). HHI da pauta (H41b): corte por quintil não mostra o efeito crescendo com a concentração (−0,13 / −0,03 / −0,16 / −0,04 do quintil 1 ao 4), e o termo de interação `comex_choque_pct × comex_hhi_sh4_2019` residualizado dá **+0,006** — indistinguível de zero (`scripts/hipoteses/96_blocof_fechamento.py`). **Fechado como nulo duplo**: nem o efeito principal nem a interação proposta pela hipótese aparecem.
- **T77-2 ✅** Terceirização da função Saúde × retenção de AIH no município: **r_parcial −0,03** (n=1.616) — não sustenta a hipótese como escrita, e terceirização × mortalidade infecciosa também é fraca (+0,04 parcial, H42c). O par que tinha rendido sinal em bruto, terceirização × custo mediano da AIH (**r_bruto +0,25**), cai a **r_parcial +0,087** (n=1.616) depois de incluir `sih_valor_aih_mediano` na varredura intensiva — mesmo padrão de artefato de escala do resto do bloco. **Fechado como nulo duplo**: nenhuma das três pernas sobrevive ao controle.
- **T77-3 ✅** Troca de partido × Jaccard de credores MIDES pré/pós-posse, agora com o teste certo (comparação de grupo, diferença de mediana + permutação em numpy puro, 5.000 draws, `scripts/hipoteses/96_blocof_fechamento.py`): Jaccard **0,2292 (troca) × 0,2457 (reeleição/sucessão mesmo partido)**, diff −0,0165, **p=0,0004** — pequeno mas robusto. Entrantes não-local (0,5517×0,5436, p=0,33) e entrantes sancionados (0,0171×0,0179, p=0,24) **não** se sustentam, e o sinal do segundo é o contrário do previsto. Nota de leitura: `prefeito_partido_2016 != prefeito_partido_2020` mede troca de **partido**, não de pessoa — sucessão pelo mesmo partido conta como "não-troca"; separar reeleição de sucessão exigiria `sequencial_candidato`, não extraído por decisão (não precisava de SQL nova para fechar o item). **Fechado como confirmação parcial**: a perna do Jaccard sustenta a hipótese, as duas de perfil do entrante não.
- **T77-4 ✅** HHI ocupacional feminino × mães adolescentes: cai de **r_bruto +0,42 para r_parcial +0,09** (n=5.570) — mesmo padrão de artefato de escala visto em E1/H18. **O IDEB sobrevive melhor** (parcial −0,24, n=5.241) e a **cobertura do Bolsa Família domina os dois** (parcial +0,30, n=5.555) — contra a expectativa original de H44, que apostava no mercado de trabalho feminino como mecanismo dominante. Pobreza prevê maternidade adolescente melhor que educação ou estrutura ocupacional. Checagem de magnitude: mediana 13,7%, agregado 12,3% dos nascidos vivos — mesma vizinhança da taxa nacional do SINASC/MS (~15–18%), sem sinal de erro de denominador.
- **T77-5 ✅** Queda de CFEM (2017-21→2022-25) × saldo do CAGED: **r_parcial +0,04** (n=2.865) — nulo, consistente com "mineração emprega pouco". × pendências no CAUC: **r_parcial −0,002** (n=2.864) — também nulo. Checagem de magnitude: a razão explode só nos municípios de denominador quase-zero (p5 do `cfem_valor_2017_2021` = R$ 661; razão mediana 9,4 nesse grupo, máx. 5.678×), mas excluí-los não muda a leitura (CAGED +0,054, CAUC −0,014) — **o nulo não é artefato de outlier**. Duplo nulo é resposta: neste recorte o choque de CFEM não deixa marca nem no emprego nem na conformidade fiscal.

O Bloco I fecha com **5 de 5 ✅** — nenhum item de T77 continua `◐`/`⏳`.
H44c (T77-4) e o duplo nulo de T77-5 já estão em `achados_fortes.md`; T77-1
(nulo duplo) e T77-2 (nulo duplo) são descartes documentados, não achados a
promover; T77-3 (confirmação parcial, efeito pequeno) fica registrado aqui e em
`tasks/hipoteses.md`, sem entrar em `achados_fortes.md` por não passar o piso
de magnitude que as demais entradas da tabela carregam.

## 78 · Agropecuária e Fundiário — Famílias Quase Sem Pergunta

Respostas de H46–H50 (blocos N/P de `tasks/hipoteses.md` §5.5); detalhe
completo na seção "Bateria das famílias vazias H46–H62" abaixo.

- **T78-1 ❌** A razão área colhida ÷ área plantada da PAM **não mede quebra de safra**: é praticamente 1,0000 em todo município e ano (perda mediana 0,0000, p90 0,0102) — a área não colhida parece ser reportada como não plantada. A pergunta sobre o Garantia-Safra pagar onde a safra quebrou fica **sem medida para testar**, não sem tentativa — é aviso de dado (H46), não resultado.
- **T78-2 ◐** Monocultura (HHI da pauta agrícola na PAM) × mortalidade: **ortogonal** (parcial +0,001 contra óbitos infecciosos). Ressalva importante: o painel não tem mortalidade por **neoplasia/agrotóxico** especificamente — a causa de óbito que a pergunta pede — só a categoria infecciosa já usada em outros achados. O teste roda contra o proxy disponível, não contra a pergunta exata; não é falseamento limpo.
- **T78-3 ✅ (resposta negativa na 1ª perna)** O rendimento da lavoura **não responde ao crédito com defasagem**: mesmo ano, 1 ano e 2 anos de defasagem dão a mesma correlação (−0,44 a −0,47) — é relação de corte, não resposta dinâmica. A segunda perna confirma: a correlação enfraquece no quartil de propriedades maiores (−0,22 contra −0,47-0,55 nos três quartis menores).
- **T78-4 ◐** A silvicultura evita a **frente ativa** do desmatamento (parcial −0,20 contra alerta DETER recente) mas não prefere especificamente o passivo consolidado (+0,01 contra PRODES acumulado, nulo) — metade da hipótese confirma.
- **T78-5 ✅** Rebanho bovino por hectare prevê desmatamento **melhor que crédito rural**: r_parcial **+0,486** com log-área (bruto +0,53), quintis 0,33→0,83 — supera o F3 (crédito rural, +0,45), o achado de desmatamento mais forte do espelho até então. → achado registrado em `achados_fortes.md` como parte da bateria N-Q (ver J1 do bloco anterior, mesma métrica).

## 79 · Saneamento como Fonte Auto-Declarada

Respostas de H51–H54 e H58 (bloco O + a pergunta de fogo do bloco P que caiu
neste tema); detalhe completo abaixo.

- **T79-1 ✅ (resposta negativa)** Atlas Esgotos (ANA, modelado por terceiro) e SNIS (declarado) **não divergem pelo mesmo eixo do G3**: metade dos municípios tem índice zero no Atlas (mediana 0,0), e usando a métrica utilizável (`sem coleta nem tratamento`) o sinal é bem mais fraco que o SNIS — × conectividade −0,10, × pobreza +0,16 (um décimo do +0,63 do G3). O Atlas, por ser modelado e não autodeclarado, não carrega o viés de quem preenche o formulário — é a leitura oposta à hipótese, mas informativa.
- **T79-2 ✅ (resposta negativa)** A natureza jurídica do prestador **não prevê** o quanto se declara nesta forma: a mediana de esgoto tratado é 0,0 em todas as categorias (economia mista, administração direta, autarquia, privada) — o piso domina e a comparação não separa nada.
- **T79-3 ✅ (resposta negativa, sinal contrário)** Esgoto sem tratamento **não prevê mais** internação por doença infecciosa — o sinal é o **contrário** (−0,015 a −0,08 parcial). Sexto caso do molde `registro_vs_fenomeno`: internação mede acesso a hospital antes de medir doença.
- **T79-4 ✅ (resposta negativa)** Vazão de lançamento outorgada (ANA) × esgoto não tratado: nulo sob controle (bruto −0,36 → parcial −0,04). Os brutos eram porte/renda; não há sobreposição territorial detectável entre "lançamento outorgado" e "sem tratamento" que identifique poluição autorizada.
- **T79-5 ✅ (resposta negativa)** Foco de calor com chuva recente (22,9% dos focos 2020-23) **não separa** fogo de manejo — é ortogonal a crédito rural (+0,01), desmatamento (+0,00), bovinos/ha (+0,01) e silvicultura (+0,04). A medida existe mas não prediz nada.

## 80 · Natalidade e Conectividade como Viés de Registro

Respostas de H59–H62 (bloco Q); detalhe completo abaixo.

- **T80-1 ✅** Cesárea concentra em horário comercial **e mais onde há plano privado**, como a pergunta previa: 72,5% das cesáreas entre 8h-17h contra 59,4% de todos os nascimentos (excedente +8,7 p.p., positivo em 95,9% dos municípios); × plano privado **+0,22 parcial**. Achado extra não pedido pela pergunta: o **excedente horário em si** anda ao contrário — cai onde a cesárea já é quase universal (−0,62 parcial contra a própria taxa) e onde há mais plano privado (−0,19). Onde cesárea é a norma, ela acontece a qualquer hora; onde é rara, é a agendada. Achado registrado em `achados_fortes.md` como **J3**.
- **T80-2 ✅ (resposta negativa)** Nenhuma das três pernas (esgoto sem tratamento, esgoto tratado, cobertura de atenção básica) prevê baixo peso ao nascer depois de controlar renda — todas colapsam, como D4/H13.
- **T80-3 ✅** Conectividade prediz a **notificação** de agravo melhor que a **internação** — a medida direta do viés de registro que C3/D19/F2 só inferiam. Notificação de dengue × 4G/5G: +0,16 parcial; internação por doença infecciosa × mesma cobertura: +0,04 — **4,4× menor**. Achado registrado em `achados_fortes.md` como J5.
- **T80-4 ✅** Escola sem internet **custa nota** de fato, não é só proxy de renda: × IDEB anos iniciais **−0,14 parcial** (bruto −0,39), sobrevive ao controle de PIB per capita (cai a −0,06, mas não zera). Complementa o D15. Achado registrado em `achados_fortes.md` como **J4**.

## 81 · Pares Nunca Cruzados Entre Datasets Já Mirrorados (2026-09-06)

Diferente do padrão do dia inteiro (dataset **novo** × covariável já
conhecida): aqui as duas pontas de cada pergunta já estavam extraídas no
painel principal (`.hipoteses/20260906_blocof/painel.csv`) — só nunca tinham
sido cruzadas entre si. Sem SQL nova, `scripts/hipoteses/100_pares_existentes.py`.

- **T81-1 ◐ (fraca, sinal correto)** Cobertura vacinal (`vac_polio`) × IVS 2010: bruto **−0,18** → parcial **−0,06** (n=5.565). Sinal na direção esperada — cobertura pior onde a vulnerabilidade é maior — mas a maior parte do efeito bruto é escala (população/renda); quintis de cobertura → IVS mediano **0,386 → 0,311**, monotônico mas achatado.
- **T81-2 ◐ (com correção de leitura da variável)** `hhi_smp` (sub-índice de mercado móvel do IBC/Anatel) × cobertura do Bolsa Família: bruto **−0,22** → parcial **−0,11** (n=5.555). **Aviso de dado**: o nome sugere HHI clássico (0–1, mais alto = mais concentrado/pior), mas a faixa medida é **0–75** e `hhi_smp` correlaciona **positivamente** com população (+0,45), densidade móvel (+0,29), PIB per capita (+0,20) e cobertura de fibra (+0,35) — o padrão inverso do que um HHI de concentração deveria fazer (mercado grande e denso tende a ter *menos* concentração, não mais). Leitura mais provável: é um **sub-score de qualidade/competição** do IBC, onde maior é **melhor**, não a razão de concentração em si. Lido assim, o parcial **−0,11** diz o que a pergunta original queria dizer com outras palavras: mercado móvel de pior qualidade/mais concentrado em município mais pobre — mas com o sinal e a unidade da variável precisando de checagem na fonte (`br_anatel_indice_brasileiro_conectividade`) antes de qualquer uso em `achados_fortes.md`.
- **T81-3 ✅ (resposta negativa)** Cobertura da Estratégia Saúde da Família × IDEB: bruto **−0,09** → parcial **+0,04** (n=5.241) — nulo em qualquer direção. Saúde básica municipal não prevê desempenho escolar neste corte.
- **T81-4 ◐ (fraca)** Valor mediano de contrato do PNCP × nota de transparência (EBT): bruto **−0,18** → parcial **−0,07** (n=664, limitado pela cobertura do EBT). Sinal correto (contrato menor onde a nota é melhor) mas fraco e amostra pequena.
- **T81-5 ✅ (resposta negativa)** Pendências no CAUC × capital social mediano do estabelecimento: bruto **+0,11** → parcial **−0,04** (n=5.568) — nulo. Mais um caso de "a regra não morde": inadimplência fiscal do município não anda com o porte de capital das empresas nele sediadas.

Placar: **0 fortes, 2 nulos, 3 fracos** — nenhum passa o piso de magnitude
para `achados_fortes.md`. O achado real desta rodada é de método, não de
correlação: **T81-2 pegou uma variável mal nomeada** (`hhi_smp` provavelmente
não é um HHI de concentração, e sim um sub-score de competição/qualidade do
IBC onde maior é melhor) — vale conferir a documentação oficial do IBC antes
de reusar essa coluna em qualquer análise futura, e registrar em
`docs/context/schema_dict_status.json` se confirmado.

## 82 · Trincas Corrigidas do Bloco R (2026-09-06)

`tasks/hipoteses.md` §5.5 Bloco R catalogava `mobilidade` e `fiscal_municipal`
como travadas por grão de fonte inteiro — na verdade só a tabela específica
citada naquela nota (`br_mobilidados_indicadores.transporte_alta_capacidade`,
9 municípios; a receita geral de `br_rf_arrecadacao` sem grão municipal)
estava travada. Rerodar o gerador de inéditos (`93_inedito.py`) achou outra
tabela em cada dataset com cobertura municipal excelente:
`proporcao_mortes_negras_acidente_transporte` (mobilidade, 5.544 municípios) e
`itr` (fiscal_municipal, imposto territorial rural, 5.571 municípios) —
nenhuma das duas tinha sido testada. Extração em
`scripts/hipoteses/72_novidades.sql`, análise em `101_novidades.py`, OUT dir
próprio (`~/rodado_hipoteses/inedito2/`).

- **T82-1 ✅ — achado forte** ITR per capita (Receita Federal) × tamanho médio da propriedade rural (SICAR): bruto **+0,47** → parcial **+0,53** (n=5.563) — sobe, não cai, com o controle, e quintis limpos e monotônicos: propriedade média 11,7 ha → ITR R$ 2,00 pc; propriedade 223,5 ha → ITR R$ 98,47 pc (**49×**). Checagem de armadilha extensiva: `sicar_area_media` (já é média, não soma) não correlaciona com população (r=−0,00) e quase nada com renda (r=+0,14) — não é artefato de escala. × densidade de rebanho (bovino/ha): nulo (bruto +0,13 → parcial −0,07). Faz sentido econômico: o ITR é progressivo por tamanho de imóvel rural na tabela oficial, então município dominado por propriedade grande arrecada proporcionalmente mais per capita — mas nunca tinha sido medido neste espelho. → achado registrado em `achados_fortes.md` como **L1**.
- **T82-2 ✅ (resposta negativa)** Notificação de violência doméstica/sexual (SINAN) por 100 mil hab × conectividade (IBC): bruto **+0,35** → parcial **+0,03**; controlando também a cobertura do Bolsa Família, **+0,01**. **Não** confirma o padrão `registro_vs_fenomeno` que já apareceu 6× no espelho — aqui o bruto era quase todo escala/renda, e o resíduo é nulo em qualquer direção. Aviso de dado: `ID_MUNICIP` desta tabela SINAN é código **SUS de 6 dígitos**, diferente de `microdados_dengue` (IBGE 7 dígitos, achado por outra sessão hoje) — **a convenção de chave do SINAN não é uniforme entre agravos**, varia tabela a tabela; usar `substr` no lado IBGE (`id_municipio // 10` tira o dígito verificador) para casar.
- **T82-3 ✅ (resposta negativa)** Proporção de vítimas negras em acidente de transporte × composição racial (Censo 2022): bruto **+0,46** → parcial **+0,13** — a proporção acompanha a composição racial local, como o esperado mecanicamente (mais população negra, mais vítima negra em números absolutos). O **excesso** (proporção de vítimas menos share populacional) tem **mediana −0,13** e é positivo em só **37,3%** dos municípios — ao contrário do que a hipótese de disparidade racial previa, no município mediano a fração de vítimas negras é **menor**, não maior, que a fração da população. Não sustenta a hipótese como escrita. Ressalva: indicador oficial de uma fonte só, não verificado contra outra base (ex.: SIM por raça).

Placar: **1 forte (L1) · 2 nulos**. O achado de método aqui vale mais que a
correlação: **duas famílias que constavam como "travadas por fonte" no Bloco
R não estavam** — a nota original testou a tabela errada dentro do dataset.
Vale reconferir as outras famílias do Bloco R (`comercio_exterior`,
`precos_indices`, `seguranca`, `justica`) com o mesmo cuidado antes de aceitar
o bloqueio como definitivo.

## Bateria de inéditos H20–H36 (2026-09-06)

Segunda bateria do dia. As hipóteses **não** vieram de leitura: vieram da
subtração de §5 de [`tasks/hipoteses.md`](../../tasks/hipoteses.md) — toda
combinação de família menos as que `perguntas.md`, `hipoteses.md` e
`achados_fortes.md` já ocupam — cruzada com os **8 moldes** de
[`docs/context/moldes.yaml`](context/moldes.yaml) aplicados a fontes que nunca
os receberam. Extração em `scripts/hipoteses/50_inedito.sql`, análise em
`scripts/hipoteses/95_inedito.py`.

Placar: **6 confirmadas · 4 falseadas · 1 nula · 1 sem dado** (12 rodadas; H30/H31 e H33–H35 não foram extraídas nesta passada).

### Bloco F · Fora da espinha municipal

Os três IPTUs municipais eram, até hoje, **datasets nunca citados em lugar
nenhum do projeto** — porque não têm `id_municipio`, e toda a análise roda na
espinha municipal.

| # | Hipótese | Veredito | Números |
|---|---|---|---|
| **H20** | A desigualdade de São Paulo é de **quadra**, não de distrito: CEPs do mesmo bairro divergem tanto quanto bairros diferentes | ❌ **Falseada, e o número é limpo** | 30.325 CEPs com ≥20 lotes, 3,66 milhões de lotes, 2025. Decompondo a variância de log(R$/m² de terreno): **90,5% é ENTRE bairros, 9,5% DENTRO**. O m² vai de R$ 476 (p10) a R$ 5.723 (p90) — 12× — e a desigualdade é essencialmente **de bairro**. Dentro do bairro a razão máx/mín entre CEPs é 1,8× na mediana. A exceção é instrutiva: Itaim (24 CEPs, 55,8×) e Jd. Paulistano (17 CEPs, 55,3×) são bairros de fronteira, ricos colados em pobres |
| **H21** | Em Fortaleza, a face de quadra sem esgoto/pavimentação não é aleatória dentro da rua: acompanha o valor da própria face | ❌ **Falseada no grão fino, confirmada no grosso** | 68.932 faces de quadra, 2023, preenchimento **>99,7%** em todos os 6 indicadores. Face com esgoto vale **2,01×** a sem; com água 2,00×; com sarjeta 2,01×; com arborização 1,83×. Pavimentação: sem pavimento R$ 26,43 → asfalto R$ 59,07 → concreto R$ 90,43. O índice 0–6 de infraestrutura × log do valor dá **r = +0,42**. **Mas dentro do mesmo logradouro** (2.630 ruas com ≥8 faces, desvio da média da rua) sobra **+0,034** — a infraestrutura é precificada por **rua**, não por face. A hipótese estava certa sobre o padrão e errada sobre a escala |
| **H22** | Em BH, a frequência de coleta de lixo acompanha o padrão de acabamento do imóvel, controlando zoneamento | ✅ **Confirmada — monotônica em cinco degraus** | 5,25 milhões de imóveis. Residencial, share com **coleta diária**: P1 **1,5%** · P2 7,8% · P3 19,9% · P4 48,5% · P5 **81,4%**. Controlando zoneamento, a correlação padrão→coleta diária é **positiva em 9 de 9 zonas** (mediana +0,14, máx +0,57). Nas duas zonas centrais (ZCBH, ZHIP) é 100% para todos — lá o serviço é universal e a hierarquia some. Onde a coleta é escassa, ela é distribuída por padrão construtivo |
| **H23** | O mesmo medicamento custa preços muito diferentes a compradores públicos diferentes | ✅ **Confirmada** | Ver **G1** em `achados_fortes.md`. Razão p90/p10 mediana **2,40×** em 1.199 células item × unidade × ano, R$ 7,1 bi |

### Bloco G · Moldes que funcionam, fontes que nunca os receberam

| # | Hipótese | Veredito | Números |
|---|---|---|---|
| **H24** | O SNIS é auto-declarado: o atendimento de água que o prestador reporta acompanha capacidade administrativa antes de acompanhar rede | ✅ **Confirmada com folga — e vira achado de primeira grandeza** | 5.302 municípios, 2021. A razão declarado/base-IBGE tem mediana **0,616**: o município mediano informa atender **62% do que a base do IBGE lhe atribui**, e **98,1% declaram MENOS** que o IBGE (só 3 declaram mais). O que prediz a razão não é rede nem renda: é **cobertura 4G/5G, r_parcial +0,634** — o segundo maior parcial já medido neste espelho, atrás só do B2. Contra formalização +0,33, contra PIB pc só +0,12, contra pobreza −0,15. Quintis de formalização → razão **0,404 → 0,824**. O "déficit de saneamento" medido pelo SNIS é, em boa parte, **déficit de quem preenche o formulário** |
| **H25** | O MUNIC é o município se descrevendo; testar contra o que ele executa no SICONFI | ✅ **Confirmada** | Vínculos declarados por habitante × despesa de pessoal por habitante: **r_parcial +0,515** (bruto +0,62) — a declaração casa com a execução, o que valida o MUNIC como fonte. O custo anual por vínculo declarado tem mediana **R$ 18.480** (p10 12.522 · p90 27.546, razão **2,2×**). Nem a declaração nem o custo acompanham renda (−0,05) |
| **H26** | Municípios com muito leito declarado e pouca produção faturada são o mapa do leito que não existe | ◐ **Nula na forma testada** | 3.599 municípios com leito no CNES (2023); **zero** com leito declarado e nenhuma internação. Internações por leito/ano: mediana **2,9** (p10 1,3 · p90 6,6). A razão não acompanha renda (−0,09) nem cobertura de atenção básica (+0,00); acompanha levemente pobreza (**+0,16**) — o leito do município pobre gira mais, não menos. Não há "leito fantasma" detectável por esta via |
| **H27** | A obra do CNO cobre uma fração do domicílio em construção do CNEFE, e a fração cai com a pobreza | ✅ **Confirmada — é o T70-3 pelo lado da formalidade** | Razão obras CNO ÷ domicílios-em-construção do CNEFE: mediana **0,46** (n=5.568). Contra pobreza **r_parcial −0,346**; contra a própria densidade de obras do CNEFE **−0,458**; contra formalização +0,240; contra PIB pc +0,201. Onde mais se constrói, **menos** se registra. Fecha o T70-3: o canteiro de obras do Brasil é autoconstrução pobre — e agora com a medida de quanto dele é invisível ao fisco |
| **H28** | A nota CAPAG deveria limitar endividamento: município com nota pior contrata menos crédito? | ❌ **Falseada — mais um "a regra não morde"** | Share que contratou operação de crédito em 2022: A+ **40,4%** · B+ 47,8% · A 34,6% · B 29,0% · C 19,7% · D **5,3%**. Parece morder. Mas o PIB per capita mediano vai de R$ 43.305 (A+) a R$ 12.142 (D) — e o parcial de nota × contratou é **−0,004** (n=4.747); do share do valor, **−0,025**. **O gradiente inteiro é renda.** Junta-se a T68-3, D7, D9, F1 e F5 |
| **H29** | Inidôneo do TCU recebe pagamento municipal como o sancionado do CEIS recebe (F5) | ⏳ **Sem dado suficiente** | A lista do TCU tem **84 CNPJ**, contra 7.893 do CEIS/CNEP — 94× menor. Apenas 69 municípios pagaram a algum, R$ 0,01 bi (**0,000%** do valor). Não é achado de que a regra morde: é lista pequena demais para testar. Registrado como limite de fonte |
| **H32** | O SISU distribui vaga onde há aluno pobre ou onde há campus? | ❌ **Falseada nas duas pontas** | Só **551 municípios** têm vaga SISU. Vagas por mil habitantes × pobreza: **−0,068 parcial**; × PIB pc −0,040; × número de IES **+0,108**. A oferta instalada explica mais que a necessidade, mas nem ela explica muito. A concentração em 551 municípios (9,9%) é o achado, não a distribuição dentro deles |
| **H36** | A série de improbidade do CNJ mede alimentação do cadastro, não improbidade | ✅ **Confirmada** | O Acre tem **28.600 condenações e 929 comarcas** na base — 3.446 por 100 mil habitantes, contra 33 em Rondônia, o segundo colocado: **104×**. Um estado de 900 mil habitantes com mais da metade das condenações do país e mais comarcas registradas que qualquer outro. Contra PIB per capita: **−0,23** (n=27). É o quarto caso do mesmo molde, com C3, D19 e F2 — e confirma o aviso de dado que já mandava excluir o AC de ranking estadual |

### O que estas 13 acrescentam ao método

**Uma fonte auto-declarada precisa ser tratada como medida de quem declara.**
H24 é o caso mais forte já visto: a razão declarado/IBGE do SNIS é predita por
cobertura de celular a **+0,63 parcial**. Qualquer análise de saneamento
municipal que use o SNIS como medida de rede está medindo, em boa parte, a
capacidade administrativa da prefeitura. O mesmo molde já tinha explicado C3
(SINAN), D19 (dengue), C4 (INSE), F2 (Consumidor.gov) e agora H36 (CNJ).

**A escala do achado não é a escala da hipótese.** H20 e H21 foram formuladas
no grão fino (quadra, face de quadra) e as duas falsearam **nesse grão** e
confirmaram um grão acima (bairro, rua). Reportar a decomposição de variância —
90,5% entre bairros; +0,42 global caindo a +0,03 dentro da rua — vale mais que
o r sozinho.

**"A regra não morde" agora tem seis casos.** T68-3 (CAUC), D7 (PGFN em
licitação), D9 (participante único), F1 (PGFN em pagamento municipal), F5
(CEIS em pagamento municipal) e H28 (CAPAG em crédito). Em nenhum a regra
formal previu o comportamento depois do controle de renda. É o padrão mais
replicado do espelho.

## Bateria das famílias vazias H46–H62 (2026-09-06)

Terceira bateria do dia, blocos **N–Q** de [`tasks/hipoteses.md`](../../tasks/hipoteses.md)
§5.5. O alvo saiu do gerador de inéditos: as sete famílias com **menos
combinações ocupadas** — `agropecuaria` (10), `saneamento_agua` (10),
`fundiario` (9), `natalidade` (12), `conectividade` (14) — todas com fonte
municipal de cobertura quase total. Extração em
`scripts/hipoteses/60_familias_vazias.sql`, análise em
`scripts/hipoteses/97_familias.py`, OUT dir próprio
(`~/rodado_hipoteses/familias/`) para não colidir com a sessão paralela.

Placar: **5 confirmadas · 9 falseadas · 3 fracas**, as 17 rodadas (H48/H54/H57/H61 fechadas logo abaixo).

### Bloco N · Agropecuária

| # | Hipótese | Veredito | Números |
|---|---|---|---|
| **H46** | Área colhida ÷ área plantada da PAM mede quebra de safra | ❌ **A medida não existe** | A perda mediana é **0,0000** e o p90 é **0,0102**: na PAM, `area_colhida` é praticamente igual a `area_plantada` em todo município e ano. A tabela não registra quebra — provavelmente porque a área não colhida é reportada como não plantada. Fica como aviso de dado, não como resultado |
| **H47** | Município de monocultura tem mortalidade distinta do de policultura de mesma renda | ❌ **Nula** | HHI da pauta agrícola × óbitos infecciosos: **+0,001 parcial**; × taxa por 100 mil: +0,017. Ortogonal, como a condição de falseamento previa |
| **H49** | A silvicultura ocupa quem **já** desmatou, não a frente ativa | ◐ **Metade confirmada** | Share de silvicultura no valor extrativo × alerta DETER recente: **−0,204 parcial** (bruto −0,426) — é de fato **negativo** com a frente ativa. Mas contra o desmatamento acumulado dá **+0,008**: nula. Ela evita a fronteira sem preferir o passivo |
| **H50** | Rebanho bovino por hectare prevê desmatamento melhor que crédito rural | ✅ **Confirmada, e é o achado da bateria** | Bovinos/ha × share da área municipal desmatada: **r_parcial +0,486** com log-área no controle (bruto +0,526), quintis monotônicos **0,332 → 0,831**. Contra crédito por hectare, +0,291. **Supera o F3** (crédito rural × desmatamento, +0,45), que era o achado de desmatamento mais forte do espelho. E contra o DETER recente cai a −0,097: como o crédito, o gado está no desmate **consolidado**, não na frente |

### Bloco O · Saneamento

| # | Hipótese | Veredito | Números |
|---|---|---|---|
| **H51** | Atlas Esgotos da ANA (modelado) e SNIS (declarado) divergem pelo mesmo eixo de capacidade administrativa do G3 | ◐ **Fraca — e o dado tem uma cara própria** | **Metade dos municípios brasileiros tem índice ZERO de esgoto com coleta e tratamento** no Atlas (mediana 0,0; média 0,19). Como medida contínua, usar `sem coleta nem tratamento`: × conectividade **−0,101 parcial**, × pobreza **+0,159**. É um décimo do sinal do G3 (+0,634) — o Atlas, por ser modelado, **não** carrega o viés de quem preenche |
| **H52** | A natureza jurídica do prestador prediz o quanto se declara | ❌ **Não testável nesta forma** | 3.494 municípios são atendidos por sociedade de economia mista, 983 por administração direta, 518 por autarquia, 251 por empresa privada. Mas a mediana de esgoto tratado é **0,0 em todas as categorias** — o piso domina e a comparação não separa nada |
| **H53** | Esgoto sem tratamento prevê internação por doença infecciosa acima do que a renda prevê | ❌ **Falseada, e o sinal é o contrário** | × share de internação infecciosa (CID A/B, SIH 2023): **−0,015**; × taxa de óbito infeccioso: **−0,084 parcial** (bruto −0,319). Onde há **menos** saneamento há **menos** internação registrada. É o molde `registro_vs_fenomeno` de novo: internação mede acesso a hospital antes de medir doença — o mesmo padrão de C3, D19, F2 e H36 |

### Bloco P · Fundiário e ambiental

| # | Hipótese | Veredito | Números |
|---|---|---|---|
| **H55** | Onde a propriedade é grande, poucos tomadores levam a maior parte do crédito rural | ✅ **Confirmada — e a perna inversa é mais interessante** | HHI de tomador do SICOR (2019+, via `id_car`): mediana **0,007**, maior tomador leva **2,7%** — o crédito rural é **muito pulverizado**. Contra o tamanho médio da propriedade: **+0,174 parcial**, confirmando a hipótese. Mas contra crédito por hectare: **−0,352 parcial** — onde o crédito é intenso, ele é **mais** disperso. Junta-se ao C2 e ao G2: intensidade é pulverizada, extensão é concentrada |
| **H56** | O embargo do IBAMA recai sobre o imóvel grande | ❌ **Falseada nas duas pernas** | Termos de embargo por 100 mil hab × tamanho médio da propriedade: **+0,091** (bruto +0,327 — era escala). × share desmatada: **−0,169**, negativo. O embargo não persegue nem a propriedade grande nem o município que mais desmatou |
| **H58** | Foco de calor com chuva recente separa fogo de manejo de fogo climático | ❌ **Nula em tudo** | 22,9% dos focos (2020–23) ocorrem com ≤3 dias sem chuva. Essa fração é ortogonal a crédito por hectare (+0,011), desmatamento (+0,001), bovinos/ha (+0,010) e silvicultura (+0,041). A separação existe como medida e **não prediz nada** |

### Bloco Q · Natalidade e conectividade

| # | Hipótese | Veredito | Números |
|---|---|---|---|
| **H59** | A cesárea eletiva concentra em horário comercial, e mais onde há plano privado | ✅ **Confirmada na primeira perna, invertida na segunda — e a inversão é o achado** | SINASC 2021, municípios com ≥100 nascimentos (n=1.733). Cesárea mediana **59,7%**. Das cesáreas, **72,5%** ocorrem entre 8h e 17h, contra **59,4%** de todos os nascimentos: um excedente de **+8,7 pontos**, positivo em **95,9%** dos municípios. Cesárea × plano privado: **+0,220 parcial**. **Mas o excedente horário anda ao contrário**: × plano privado **−0,193**, e × a própria taxa de cesárea **−0,622 parcial**. Onde a cesárea é quase universal ela acontece a qualquer hora — virou o modo padrão; onde é mais rara, é a agendada |
| **H60** | Baixo peso ao nascer × esgoto × atenção básica: qual prevê depois da renda? | ❌ **Nenhuma** | × esgoto sem tratamento **+0,005**; × esgoto tratado **−0,002**; × cobertura de atenção básica **−0,009** (bruto −0,272); × pobreza **+0,037**. As quatro colapsam, como em D4 e H13 |
| **H62** | Escola sem internet custa nota, ou é proxy de renda? | ✅ **Custa nota** | Share de escolas sem internet (SIMET) × IDEB anos iniciais: **−0,144 parcial** (bruto −0,385). Contra PIB per capita o parcial cai a −0,063, e contra pobreza sobe a +0,177. O efeito sobre a nota **sobrevive** ao controle de renda, ainda que modesto — não é só proxy |

### Não rodadas

**H48** (rendimento da lavoura com defasagem de um ano contra crédito), **H54**
(vazão de lançamento da ANA cruzada com esgoto não tratado — extraída em
`v_ana_lanc.csv`, não analisada), **H57** (razão CAR/CAFIR) e **H61** (SINAN
notificação × SIH internação contra conectividade). As quatro precisam de
recorte ou ponte que o bloco atual não faz.

### O que esta bateria acrescenta

**O gado supera o crédito.** O F3 era o achado de desmatamento mais forte que
sobrevivia à intensidade (+0,45). Bovinos por hectare dá **+0,486** no mesmo
teste, com quintis monotônicos. As duas medidas contam a mesma história por
lados diferentes — e nenhuma delas prevê a **frente ativa** do DETER.

**`registro_vs_fenomeno` tem agora seis casos.** C3, D19, F2, H36, H53 e, por
outro caminho, G3. Toda vez que uma contagem de evento registrado foi testada
contra acesso, o acesso ganhou. É o padrão mais replicado do espelho junto com
"a regra não morde".

**Duas hipóteses falsearam por a medida não existir**, não por o mundo ser
diferente: H46 (a PAM não registra quebra de safra) e H52 (o piso de zero no
Atlas domina). Vale distinguir isso de nulo — são avisos de dado, e estão em
`achados_fortes.md`.

### Fechamento H48, H54, H57, H61 (2026-09-06)

As quatro que a bateria das famílias vazias deixou em aberto. Extração
`scripts/hipoteses/60_familias_vazias.sql` mais um bloco curto (SICOR por ano,
SINAN dengue, ponte nome→`id_municipio`); análise no mesmo `97_familias.py`.

| # | Hipótese | Veredito | Números |
|---|---|---|---|
| **H48** | O rendimento da lavoura responde ao crédito com **defasagem de um ano**, e a resposta é menor onde a propriedade é grande | ❌ **A defasagem não existe; a segunda perna sim** | Operações de crédito de 2021 × rendimento médio da PAM: mesmo ano **−0,442**, defasagem de 1 ano **−0,468**, de 2 anos **−0,446**. As três são iguais — **não há estrutura dinâmica**, é relação estrutural de corte, não resposta. Contra a *variação* do rendimento 2021→2022: −0,124. A perna de tamanho confirma: por quartil de ha/imóvel a correlação vai de **−0,475 · −0,548 · −0,467** a **−0,220** no quartil dos maiores (mediana 2.665 ha) — onde a propriedade é grande a relação de fato enfraquece. Ressalva: extraí **contagem** de operações, não valor; a leitura de intensidade fica limitada |
| **H54** | A vazão de lançamento outorgada pela ANA cruzada com o esgoto não tratado do Atlas identifica onde o lançamento é **legal e sem tratamento** | ❌ **Nula sob controle** | Ponte nome+UF → `id_municipio` casou **1.573 de 1.577** (99,7%); 3,53 milhões de m³/h outorgados. Vazão per capita × esgoto sem coleta nem tratamento: bruto −0,359 → **parcial −0,043**; × esgoto tratado +0,351 → **−0,023**; × coleta sem tratamento **+0,057**. Os brutos eram porte e renda; sob controle não sobra sobreposição territorial nenhuma. A "poluição autorizada" não é localizável por este cruzamento |
| **H57** | Município com muito CAR e pouco CAFIR mede a terra que se declara ao ambiente e não ao fisco | ◐ **A medida é boa, o poder explicativo é fraco** | Razão área SICAR ÷ área CAFIR: mediana **0,75** (p10 0,35 · p90 1,04); **11,8%** dos municípios declaram mais ao ambiente que ao fisco. Contra o share desmatado: **+0,143 parcial** com log-área, com quintis 0,634 → 0,807 (o quinto quebra, 0,747). Contra o tamanho médio da propriedade **−0,226**: a divergência é fenômeno de **propriedade pequena**. As demais pernas colapsam (crédito +0,03, embargo −0,07, pobreza −0,03) |
| **H61** | A conectividade prediz a **notificação** melhor que prediz a **internação** — e a diferença é a medida direta do viés de registro de C3/D19 | ✅ **Confirmada, e é a medida que faltava** | Ver **J5** em `achados_fortes.md`. Notificação de dengue (SINAN 2023, 1,51 milhão) × cobertura 4G/5G: **+0,159 parcial**. Internação por doença infecciosa (SIH 2023, CID A/B, 569.555) contra a mesma cobertura: **+0,036** — **4,4× menor**. Por quintil de IBC a notificação vai de 117 a 293 por 100 mil (**2,5×**) e a internação de 183 a 239 (**1,3×**) |

**Um aviso de dado que apareceu aqui e é grande:** o plano era cruzar dengue
com dengue. **`br_ms_sih.aihs_reduzidas` não tem uma única internação com CID
A90 em nenhum dos 17 anos** — 190 milhões de registros, zero. Em 2023, ano de
1,5 milhão de notificações de dengue no SINAN, o SIH registra 2.648 internações
em todo o grupo A9x e nenhuma em A90. Dengue não é recuperável por CID no SIH
deste espelho; por isso H61 roda contra o capítulo infeccioso inteiro (A/B), o
que enfraquece o pareamento e não muda a direção.

## Estado da cobertura em 2026-09-06

| Status | Perguntas | % |
|---|---|---|
| ✅ respondida | 295 | 74% |
| ◐ parcial | 79 | 20% |
| ❌ **sem resposta** (bloqueio verificado) | 26 | 6% |
| ⏳ pendente sem investigar | **0** | — |
| **total temático** | **400** | |

**Os temas 77 a 80 (18 perguntas) fecham sem `⏳` restante nesta rodada** — mas
seis itens de rodadas anteriores continuam com a marca `⏳` no corpo do
documento (T05-2, T16-2, T16-5, T40-5, H29, M3): a tabela acima conta os
genuinamente **bloqueados** (dado ou grão que não existe) como
`❌ sem resposta`, não como pendente — só T05-2 é diferente: o bloqueio de
tabela caiu (Senado agora tem `processo`), mas a pergunta em si (proposição
alinhada ao perfil econômico do estado) não foi respondida, porque falta
classificar a `ementa` por tema — trabalho não tentado, não bloqueio de dado.
Ver a linha de T05-2 acima para o detalhe. O Bloco I (T77-1..5,
tema 77) fechou em 2026-09-06: a corrida completa já tinha rodado (`bash
hipoteses_overnight.sh`, não teste de fumaça); faltava código de análise, não
dado — `scripts/hipoteses/96_blocof_fechamento.py` fez o corte por
quintil/interação (T77-1), incluiu `sih_valor_aih_mediano` na varredura
(T77-2) e rodou a comparação de grupo por permutação que a pergunta de T77-3
pedia (troca de partido vs. reeleição, não correlação). Todas as cinco saem
como ✅ (ver seção "77 · Cruzamentos Inéditos de Três Famílias" acima): três
nulos duplos (T77-1, T77-2 na leitura final, mais T77-5), uma confirmação
parcial pequena mas robusta (T77-3) e um achado forte (T77-4, em
`achados_fortes.md`). Os temas **78, 79 e 80** (14 perguntas, sessão paralela
`analise-hipoteses-municipais`, blocos N-Q de `tasks/hipoteses.md`) fecharam no
mesmo dia com a bateria de hipóteses H46–H62 já rodada — ver as três seções
acima. Um bloqueio genuíno (T78-1: a PAM não registra quebra de safra, não há
medida para testar) e duas parciais (T78-2: proxy imperfeito, falta
mortalidade por neoplasia no painel; T78-4: metade da hipótese confirma); as
onze restantes saem como ✅, a maioria com resposta negativa conclusiva, não
bloqueio — a distinção que separa `❌ sem resposta` de `✅ (resposta
negativa)` na tabela acima.

**Toda pergunta de `perguntas.md` tem entrada em `respostas.md`**, e nenhuma
das perguntas de 01–76 está pendente por falta de tentativa: as 25 marcadas `❌ SEM RESPOSTA` têm o
bloqueio identificado e verificado na própria entrada. `scripts/build_douradas_perguntas.py`
reconhece o marcador `❌` desde 2026-09-06 (mapeado para `no_answer`, fora do
golden set) — antes disso ele tratava essas linhas como "código não encontrado".

Trajetória: 132 pendentes em 2026-09-05 → 79 → 28 → **0**.

Sete perguntas que exigiam operação geométrica (sobreposição de polígono, área
calculada a partir de malha, distância entre pontos) foram **removidas** de
`perguntas.md` em 2026-09-05 a pedido, junto com as respostas correspondentes:
as antigas T22-2, T22-3, T31-2, T34-2, T34-3, T34-5 e T35-3. Os itens
sobreviventes desses temas foram **renumerados** — as referências a T22, T31,
T34 e T35 em `tasks/respostas_pendentes.md` e em outros logs históricos são
anteriores a essa renumeração.

### As 25 sem resposta, por natureza do bloqueio

| Bloqueio | Perguntas | O que falta |
|---|---|---|
| Fonte sem série temporal | T40-5, T53-5, T66-5, T72-3, T72-4 | CAPAG não tem coluna de ano; SEDEC só tem reconhecimentos vigentes de 2026; OCDE para em 2016/2019 |
| Tabela sem a coluna que a pergunta exige | T25-2, T25-5, T40-4, T41-4, T55-4 | SIOP sem valor (só catálogo de ações de 2025); FIPE sem preço; Farmácia Popular sem série de preço |
| Sem grão municipal | T26-3, T38-3, T41-3, T14-3 | servidores federais só por UF; formação docente só por UF; POF só por UF |
| Chave inexistente entre as pontas | T13-5, T21-5, T42-4, T43-1, T43-2, T43-5, T73-5 | sem par residência→emprego de pessoa; sem catálogo comum cartão↔licitação; HydroSHEDS sem código IBGE; Olympedia sem cidade de nascimento; órgão em sigla truncada × nome por extenso |
| Sem coluna geográfica na fonte | T42-3 | `br_mma_extincao` só tem espécie/família/ordem/categoria |
| Escopo regional da fonte | T28-4, T39-3, T39-4 | ISP-RJ cobre só o Rio; nenhum dos 4 espelhos de TCE tem penalidade por município |
| Sem régua comum entre as escalas | T38-1 | PISA↔INEP exigiria equating psicométrico, não join |

### Pontes e correções de leitura descobertas ao fechar as pendentes

Vários "bloqueios" anteriores eram de **leitura**, não de dado, e caíram:

- **SISDEPEN** (T06-1, T06-4): a UF vem como `"Minas Gerais (MG)"`, não sigla —
  `regexp_extract(uf,'\(([A-Z]{2})\)',1)` recupera 575.622 presos em 27 UFs.
  Estava catalogado como "corrompido, precisa re-scraping".
- **SICOR → município** (T07-3, T07-5, T17-2, T17-3, T17-5, T19-2): o `id_car` é
  `UF(2) + código IBGE(7) + hash(32)`. Ver o bloco de achados metodológicos.
  **Só vale de 2019 em diante** — o campo é 0% preenchido até 2017.
- **IEPS** (T23-4, T24-2, T24-3, T49-4): `br_ieps_saude.municipio` já traz
  cobertura vacinal, de atenção básica e de plano privado por município, prontas.
  Substituiu o SIPNI, que está ilegível.
- **Índice de Rice** (T29-4, T76-4): a "operacionalização" que faltava para medir
  disciplina partidária é |sim−não|÷total por votação, calculável nas duas casas.
- **Querido Diário texto integral** (T74-4, T74-5): `regexp_extract_all` sobre o
  texto extrai 449.693 CNPJ distintos em uma passada — método barato e pronto.
