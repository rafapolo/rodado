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
- **T05-2 ✅** Ocupação declarada × eleição 2022 (dep. federal/senador): deputados na reeleição **58,8%**, engenheiros 7,8%, médicos 6,5% vs **empresários 3,9%** (n=1.229 candidatos) — abaixo da média (~5%), empresário não é profissão que elege.
- **T05-3 ⏳** Senado: o espelho não tem tabela de proposições do Senado (só `senadores` + CEAPS) — pipeline necessário.
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
- **T07-1, T07-3, T07-4, T07-5 ⏳** Pendentes — SICOR/MapBiomas fora do painel atual.

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
- **T11-5 ⏳** Pendente — cruzamento IBC × formalidade por interior exige recorte urbano/rural fino; base parcialmente coberta por A5/A6 (+0,56/+0,57 no agregado).

## 12 · Interseccionalidade

- **T12-1 ✅** Mulher negra × homem branco no mesmo setor (RAIS 2022, 21 setores): **mediana de 40,3% de lacuna salarial** — a dupla desvantagem é generalizada e grande.
- **T12-3 ✅ / T12-5 ✅** Dupla desvantagem × rotatividade setorial (CAGED 2021): **r = +0,04 com lacuna mulher-negra; +0,19 com lacuna de gênero; −0,33 com lacuna racial** — setores de alta rotatividade não concentram as maiores desigualdades; para raça o sinal até inverte.
- **T12-2 ⏳** Pendente — exige mães por raça (SINASC) × leitos obstétricos per capita (CNES) × renda: query dedicada ainda não executada.
- **T12-4 ⏳** Pendente — chefia feminina não existe no Censo 2022 do espelho (ver T09-5).

## 13 · Migração

- **T13-1…T13-5 ⏳** Pendentes — fluxos origem/destino do CAGED exigem query dedicada (232 mi linhas).

## 14 · Consumo

- **T14-1…T14-5 ⏳** Pendentes — ANP e IPCA fora do painel atual.

## 15 · Poder e Elites

- **T15-1 ◐** Patrimônio dos eleitos medido (R$ 3,12 mi médio); autoria Câmara pendente.
- **T15-2…T15-5 ⏳** Pendentes — cruzamentos TSE×CNPJ×CGU dedicados.

## 16 · Economia Política

- **T16-1…T16-5 ⏳** Pendentes — rf_arrecadacao exige agregação própria por UF/setor.

## 17 · Agropecuária

- **T17-1 ✅ (parcial)** Rebanho × crédito SICOR 2022: **r = +0,57 (n=5.423; R$ 127,5 bi creditados)** — pecuária puxa crédito; % de área em imóveis gigantes × crédito por bovino **−0,16**. *(A2)*
- **T17-2 ⏳** Pendente — exige join SICAR imóvel→tomador via id_car/cpf (`recurso_publico_propriedade`), pipeline dedicado.
- **T17-3 ⏳** Pendente — TRASE não tem chave municipal direta com PRODES/PPM no espelho.
- **T17-4 ✅** CAR pendente × crédito: bruto +0,00; controlando rebanho **−0,12 (n=5.417)** — pendência custa pouco crédito formal, mas custa.
- **T17-5 ◐** Coberto por T17-1/T10-5: crédito segue rebanho (+0,57) e emissões seguem renda agro (+0,39); produtividade por hectare fica para o cruzamento fino com SICAR.

## 18 · Comércio Exterior

- **T18-2 ✅ (fato)** Exportações 2023: **69,8% primários (NCM caps. 01–27), US$ 339,7 bi totais** — confirma concentração em commodities.
- **T18-1, T18-3, T18-4, T18-5 ⏳** Pendentes — join COMEX×RAIS por município.

## 19 · Mercado Financeiro

- **T19-4 ✅ (proxy)** Bancos × crédito: agências × PIB pc fraco (+0,12, A15); SICOR pendente.
- **T19-1, T19-2, T19-3, T19-5 ⏳** Pendentes.

## 20 · Ciência

- **T20-1…T20-5 ⏳** Pendentes — cnpq_bolsas fora do painel atual.

## 21 · Corrupção

- **T21-1…T21-5 ⏳** Pendentes — cadeia cartão→licitação→RF é análise dedicada (100 mi+ linhas).

## 22 · Clima

- **T22-1 ✅** Focos de calor 2019–22 × desmatamento: **r = +0,66 (n=5.240 municípios)**; × emissões agro +0,51; × VA agro per capita só +0,10 — o fogo segue o desmate e as emissões, não a renda formal do agro.
- **T22-2…T22-4 ⏳** Pendentes — INMET (bdmep) e SICAR×queimadas exigem séries temporais por estação/malha; pipeline dedicado.
- **T22-5 ◐** Coberto por T22-1: fogo associado à conversão produtiva (emissões agro +0,51) muito mais que à renda (+0,10) — padrão de uso da terra, não evento natural.

## 23 · Epidemiologia

- **T23-1…T23-5 ⏳** Pendentes — SINAN dengue, SIH, SIPNI exigem agregações dedicadas.

## 24 · Assistência SUS

- **T24-1…T24-5 ⏳** Pendentes — SIH/SIA (bilhões de linhas) precisam pipeline próprio.
- **T24-nota ✅** Mortalidade infantil × cesárea: **−0,40 (n=2.283)** — municípios com mais cesáreas têm menor TMI, mas é provável seleção (cesárea marca acesso, não causa). *(A10)*

## 25 · Orçamento

- **T25-4 ✅** Emendas parlamentares per capita (2023+) × % votos Lula 2022: **r = −0,006 (n=1.406 municípios) — dinheiro de emenda não segue alinhamento eleitoral municipal**.
- **T25-1 ✅** Emendas CGU × transferências Transferegov por município: **r = +0,10 (n=1.096)** — são circuitos distintos; quem recebe emenda não é quem capta planos de ação.
- **T25-2 ⏳** Pendente — SICOR não tem chave municipal direta com SIOP (só via `recurso_publico_complemento_operacao`); cruzamento de orçamento exige pipeline.
- **T25-3 ◐** Execução por tipo (CGU 2023+): individual finalidade definida **74,4%** pago/empenhado; transferências especiais **99,7%**; bancada **52,5%**; comissão **43,2%** — individuais executam melhor que coletivas. Velocidade/bloqueio no SIOP/Transferegov pendente.
- **T25-5 ⏳** Pendente — série temporal RF × emendas × juros no SIOP exige tabela `dados` do SIOP re-scrapeada (cabeçalhos corrompidos).

## 26 · Servidores

- **T26-1…T26-5 ⏳** Pendentes — cadastro CGU (852 mi linhas) exige amostragem dedicada.

## 27 · Opinião

- **T27-eleitoral ✅ (UF)** Geografia do voto 2022: **PIB pc × Lula = −0,62; rendimento médio × Lula = −0,33; homicídios/100k × Lula = +0,46** — Lula venceu nos estados mais pobres e mais violentos; Bolsonaro nos ricos. *(A8, A9)*
- **T27-1…T27-5 ◐** Pesquisas Poder360/PNS/PNADC pendentes; base eleitoral calculada.

## 28 · Violência Escolar

- **T28-1…T28-5 ⏳** Pendentes — SINAN por faixa etária e INSE fora do painel.

## 29 · Dados Eleitorais

- **T29-2 ◐** Patrimônio eleitos medido (R$ 3,12 mi médio / R$ 158 mi máximo); série histórica pendente.
- **T29-1, T29-3, T29-4, T29-5 ⏳** Pendentes.
- **T29-extra ✅** Correlações geográficas do voto em A8/A9 acima.

## 30 · Estrutura Produtiva

- **T30-1 ✅ (parcial)** Empresas/100k × rendimento médio: **+0,24 (n=5.570)** — mercados com mais empresas pagam melhor. Concentração de capital social pendente. *(A13)*
- **T30-2…T30-5 ⏳** Pendentes.

## 31 · Desenvolvimento Humano

- **T31-4 ◐** IVS-IPEA × mortalidade infantil (SIM×SINASC 2020–22): **r = +0,31 (n=1.423 municípios ≥20 mil hab)** — vulnerabilidade social prevê TMI melhor que PIB pc (−0,13, T03-3).
- **T31-1…T31-3, T31-5 ⏳** Pendentes — CGU×AVS e setores censitários exigem cruzamentos dedicados; AVS só tem um ano no espelho (sem série "entre ondas").

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
- **T35-1…T35-4 ⏳** Pendentes — dormitório×fluxo CAGED e geobr exigem pipeline dedicado.

## 36 · Religiosidade

- **T36-1 ✅** Templos/100k × PIB pc: **r = −0,11 (n=5.570) — praticamente nenhuma relação**; Piauí (mais pobre) lidera densidade de templos, SC (rica) é 2ª. *(A16)*
- **T36-2 ✅** Fiéis por religião (Censo 2022) × templos no CNPJ (CNAE 9491-0/00): **r = +0,47 com % evangélicos e −0,58 com % católicos (n=1.687 municípios)** — o registro empresarial de templos captura o evangelicalismo; católico tem paróquia, não empresa.
- **T36-3 ⏳** Pendente — exige RAIS série longa por CNAE religioso vs mudança de composição religiosa 2010→2022; censo 2010 por religião não está no espelho.
- **T36-4 ◐** Coberto por T36-2: onde há muitos evangélicos há mais templos-CNPJ (+0,47); perfil socioeconômico fino fica para cruzamento com instrução do próprio censo religioso.
- **T36-5 ✅ (proxy)** Templos × rendimento médio RAIS: +0,06 — idem, nada.

## 37 · Sanções

- **T37-1 ✅** Dos **93 sancionados do TCU, 38 (41%) seguem com CNPJ ativo** em 2023.
- **T37-5 ✅ (parcial)** PGFN: **R$ 7,06 trilhões consolidados, 7,67M devedores; SP sozinho R$ 3,04 tri** (RJ 873 bi, MG 601 bi). Sobreposição com TCU pendente.
- **T37-2, T37-3, T37-4 ⏳** Pendentes — join PGFN×licitações×sócios.

## 38 · Educação Básica

- **T38-4 ✅ (fato)** PISA 2022 matemática: **Brasil 380,3 vs OCDE 474,8** (n≈10.800 alunos BRA) — gap de ~95 pontos ≈ 2,5 anos escolares.
- **T38-1, T38-2, T38-3, T38-5 ⏳** Pendentes.

## 39 · Justiça

- **T39-1 ✅ (fato)** Judiciário estadual (CNJ 2021, 28 tribunais): **despesa de pessoal = 90,1% em média** da despesa total; mínimo 76,4%, máximo 98,7%. Confirma o gancho do tema.
- **T39-2…T39-5 ⏳** Pendentes — improbidade e TCEs estaduais.

## 40 · Federalismo Fiscal

- **T40-1 ◐** CAPAG 2025 × transferências voluntárias per capita (Transferegov): **r = +0,03 (n=2.000+ municípios ≥20 mil hab)** — capacidade fiscal não explica quem recebe transferência; porte e política sim.
- **T40-2 ✅** CAPAG × FIRjan IFGF: **r = +0,37 (n=1.322)** — os dois índices concordam parcialmente; divergências concentram-se nos intermediários (C/B).
- **T40-3…T40-5 ⏳** Pendentes — exigem série temporal da CAPAG (só há um ano no espelho) e SICONFI alinhado ao Transferegov.

## 41 · Nutrição

- **T41-excesso ✅ (fato)** SISVAN 2023: excesso de peso adulto — **RS 73,6%, RN 72,4%, SP 71,9%, MS 71,7%, CE 70,4%** (top 5 UFs). CMED/BPS/Farmácia Popular pendentes.
- **T41-1…T41-4 ⏳** Pendentes.

## 42 · Água

- **T42-1…T42-5 ⏳** Pendentes — séries hidro/clima exigem alinhamento temporal dedicado.

## 43 · Cultura

- **T43-3 ✅ (com ressalva)** Medalhas olímpicas do Brasil por esporte (contagem por atleta, esportes coletivos inflados): futebol 181, vôlei 132, basquete 60, vela 36, atletismo 35, vôlei de praia 26, judô 24, natação 21.
- **T43-1, T43-2, T43-4, T43-5 ⏳** Pendentes — nascimento de atletas × municípios.

## Multi-referência (seção final)

- **M1 ⏳ / M2 ⏳ / M3 ⏳ / M4 ⏳ / M5 ⏳** — as cadeias completas exigem pipelines dedicados; componentes já medidos aparecem nas entradas parciais acima (ex.: M4 usa A1/A2; M3 usa T37-1/T37-5).
