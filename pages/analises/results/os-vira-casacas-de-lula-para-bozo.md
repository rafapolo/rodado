# Os vira-casacas: de Lula em 2022 a Flávio Bolsonaro em 2026

No 1º turno de 2022 Lula venceu em 3.371 municípios. No 1º turno de 2026, em 4 de outubro,
**703 deles deram a vitória a Flávio Bolsonaro**. Nenhum município fez o caminho
inverso: onde Bolsonaro venceu em 2022, Flávio também venceu em 2026.

Comparamos esses 703 com os 2.661 municípios em que Lula venceu nas duas eleições. São os
vizinhos naturais, porque os dois grupos votaram em Lula em 2022. Em cada município
olhamos cerca de 150 indicadores: renda, programas sociais, educação, saúde, raça e idade
no Censo, crédito rural, Pix e emprego formal por setor de atividade.

A resposta curta é menos interessante do que a pergunta. **Quase tudo que distingue os
vira-casacas se explica por onde eles estavam em 2022 (perto do empate) e por onde ficam
no mapa (Sul, Centro-Oeste, interior de SP e MG).** O que sobra depois disso é um perfil
modesto, mas consistente: menos Bolsa Família, mais população branca, agro com mais
crédito por hectare e municípios menores.

> **Flávio não é Jair.** Em 2026 o candidato do PL é outra pessoa, contra uma direita mais
> dividida (Caiado, Zema, Augusto Cury e outros). "Virar" aqui quer dizer o município ter
> passado do 1º lugar de Lula para o 1º lugar de Flávio. Não quer dizer que os mesmos
> eleitores mudaram de lado, e muito menos de ideologia.

---

## 1. Quem virou já estava perto do empate em 2022

![Margem de Lula em 2022 contra margem de Lula em 2026, nos municípios que Lula venceu em 2022](/analises/img/vira-casacas-margens.png)

| | vira-casacas (703) | Lula manteve (2.661) |
|---|---:|---:|
| vantagem de Lula em 2022, mediana | **7,0 p.p.** | 48,2 p.p. |
| vantagem de Lula em 2022, 10% mais altos | acima de 15,2 p.p. | acima de 70,2 p.p. |
| vantagem de Lula em 2026, mediana | **−8,3 p.p.** | +38,8 p.p. |
| variação do voto em Lula, 2022 → 2026, média | **−8,9 p.p.** | −5,0 p.p. |

- **67%** dos vira-casacas deram a Lula menos de 10 p.p. de vantagem em 2022, e **97%**
  menos de 20 p.p.
- Lula perdeu votos em todos os 703. No Brasil inteiro também perdeu, com queda mediana
  de 5,5 p.p., mas ali perdeu mais.
- **Em 2026 a virada não foi apertada.** Só 11,5% dos vira-casacas ficaram a menos de
  2 p.p. de empate. Na mediana, Flávio venceu por 8 p.p. e somou 7,9 p.p. a mais do que
  Bolsonaro teve em 2022 nesses mesmos municípios.

A margem de 2022, sozinha, acerta quem virou e quem não virou com AUC de **0,98**. AUC é a
chance de o modelo dar nota maior a um vira-casaca sorteado do que a um município sorteado
que Lula manteve; 0,5 é sorte e 1 é acerto perfeito. Todo indicador que acompanha "Lula
ganhou apertado em 2022" vai parecer, numa comparação crua, um indicador de virada. É por
isso que as comparações abaixo são feitas de três jeitos, cada um mais exigente que o
anterior.

## 2. Geografia: Sul e Centro-Oeste viraram, o Nordeste não

![Vira-casacas como fração dos municípios que Lula venceu em 2022, por UF](/analises/img/vira-casacas-uf.png)

| região | Lula venceu em 2022 | viraram | taxa |
|---|---:|---:|---:|
| Sul | 345 | 250 | **72%** |
| Centro-Oeste | 140 | 97 | **69%** |
| Sudeste | 797 | 283 | 36% |
| Norte | 303 | 58 | 19% |
| Nordeste | 1.779 | 15 | **0,8%** |

Minas Gerais tem o maior número absoluto (175), seguida de Rio Grande do Sul (132),
Paraná (91), São Paulo (88) e Goiás (68). Piauí, Pernambuco, Paraíba e Sergipe não tiveram
nenhum. Saber só a UF já separa os dois grupos com AUC de 0,89.

## 3. O perfil, e quanto dele resiste aos controles

![Diferença entre vira-casacas e municípios que Lula manteve, antes e depois de restringir aos de margem comparável](/analises/img/vira-casacas-perfil.png)

O tamanho da diferença é o *rank-biserial*, que vai de −1 a 1 (0 = nenhuma diferença; +0,5
quer dizer que, num par sorteado, o vira-casaca tem o valor maior em 75% das vezes). Cada
indicador passou por três filtros:

1. **Bruto:** a diferença tem que valer depois da correção por múltiplos testes
   (Benjamini-Hochberg, 5%). Foram 155 indicadores testados, e 139 passaram.
2. **Mesma UF e mesmo porte:** a diferença tem que aparecer comparando municípios da mesma
   UF, com população, PIB per capita e área controlados. Passaram 48.
3. **Mesma UF, mesmo porte e mesma margem de 2022:** só os municípios que Lula ganhou por
   até 31 p.p. (os 703 contra 649 que Lula manteve), comparados dentro de faixas de 2,5 p.p.
   de margem de 2022. **Passaram 10.**

| indicador | vira-casacas × Lula manteve (medianas) | diferença bruta | mesma UF e porte | + mesma margem 2022 |
|---|---|---:|:---:|:---:|
| famílias no Bolsa Família / domicílios | 12% × 34% | −0,80 | sim | **sim** |
| alunos no Pé-de-Meia / população¹ | 0,8% × 1,9% | −0,78 | sim | **sim** |
| analfabetismo, 15 anos ou mais (2022) | 7,8% × 18,2% | −0,76 | sim | não |
| IDH municipal (2010)² | 0,69 × 0,60 | +0,75 | sim | não |
| PIB per capita | R$ 32 mil × R$ 13,5 mil | +0,71 | não | não |
| população branca (2022) | 50% × 25% | +0,65 | sim | **sim** |
| valor médio do Pix de pessoa física | R$ 195 × R$ 143 | +0,64 | sim | **sim** |
| empregos formais por habitante | 0,17 × 0,09 | +0,62 | sim | não |
| crédito rural por habitante | R$ 17,6 mil × R$ 2,2 mil | +0,58 | sim | por pouco, não |
| crédito rural por hectare de imóvel no CAR | R$ 200 × R$ 67 | +0,49 | sim | **sim** |
| emprego formal no setor público | 31% × 56% | −0,49 | sim | não |
| Ideb | 6,1 × 5,3 | +0,45 | sim | não |
| população preta (2022) | 7,0% × 9,3% | −0,33 | sim | **sim** |
| população (log) | 7 mil × 11 mil hab. | −0,25 | — | **sim** (menores) |

¹ O Pé-de-Meia exige inscrição no CadÚnico, então é a mesma medida que o Bolsa Família
vista por outro lado, e não um segundo achado.
² IDH, índice de vulnerabilidade social, analfabetismo e Bolsa Família andam juntos
(correlações entre 0,71 e 0,87). Na prática são um único eixo de vulnerabilidade, não
quatro descobertas.

**Como ler a tabela.** No bruto, os vira-casacas parecem municípios mais ricos, mais
escolarizados e mais formalizados. A maior parte disso, porém, é a diferença entre o
Nordeste e o resto do país, e entre quem dava 70% a Lula e quem dava 52%. Comparados com
municípios da mesma UF que Lula também ganhou por pouco, os vira-casacas continuam
diferentes em menos coisas:

- têm **menos dependência de Bolsa Família**;
- são **mais brancos e menos pretos**;
- têm **agro mais capitalizado**, com mais crédito rural por hectare;
- têm **Pix de valor médio mais alto**;
- são **municípios menores**.

Mesmo esses efeitos são moderados: cada desvio-padrão do indicador muda de 3 a 8 pontos
percentuais a chance de o município ter virado.

## 4. Economia: o que a estrutura setorial diz

Para a composição setorial usamos o emprego formal de 2024 por seção e divisão da CNAE em
cada município, mais a fatia da agropecuária no PIB municipal e o crédito rural.

- **No bruto, os vira-casacas têm mais emprego privado em quase tudo e menos setor
  público.**
  - Agropecuária: 12% do emprego formal, contra 3% nos municípios que Lula manteve.
  - Indústria de transformação: 8,1% contra 2,5%.
  - Atacado, transporte e serviços financeiros: duas a quatro vezes mais.
  - Administração pública: 29% contra 53% do emprego formal.
- **Parte disso é aritmética.** As seções somam 100% do emprego formal: se a administração
  pública pesa 24 pontos a menos, os setores privados pesam, juntos, 24 pontos a mais. No
  bruto, 19 das 20 seções são maiores nos vira-casacas (a exceção é informação e
  comunicação). Comparando municípios da mesma UF e do mesmo porte, continuam maiores só
  comércio, indústria de transformação, transporte e atividades profissionais. Nessa
  comparação o emprego formal no agro já não difere.
- **Nenhuma seção ou divisão da CNAE sobrevive à comparação com a mesma margem de 2022.**
  A que chegou mais perto foi a administração pública (menor nos vira-casacas). A
  estrutura setorial acompanha "Lula ganhou apertado em 2022", e não a virada em si.
- **O único indicador econômico que resiste é o crédito rural por hectare.** O que pesa é
  o agro capitalizado, não o tamanho do agro: a fatia da agropecuária no PIB e o emprego
  formal no agro caem para perto de zero quando se compara municípios de mesma margem.

A economia pesa mais quando a pergunta é **o quanto** Lula caiu, e não **se** o município
virou. Nos 5.570 municípios, comparando dentro da mesma UF e controlando o porte e o voto
de Lula em 2022:

| a cada 1 desvio-padrão a mais de… | variação do voto em Lula, 2022 → 2026 |
|---|---:|
| domicílios no Bolsa Família | **+1,2 p.p.** (caiu menos) |
| emprego formal no setor público | **+0,9 p.p.** |
| população preta | +0,4 p.p. |
| agropecuária no PIB | **−0,7 p.p.** (caiu mais) |
| crédito rural por habitante | −0,6 p.p. |
| emprego formal na agropecuária | −0,5 p.p. |
| população branca | −0,9 p.p. |
| PIB per capita | −0,3 p.p. |
| emprego no comércio | −0,3 p.p. |
| emprego no setor financeiro | −0,2 p.p. |
| arrecadação de royalties de mineração por habitante | −0,2 p.p. |

Todos esses coeficientes passam na correção por múltiplos testes. Juntos, os indicadores
elevam a parte explicada da queda de Lula de 45% (só UF, porte e voto de 2022) para 60%.

## 5. Quanto disso é explicável

| o que o modelo sabe | AUC (vira-casaca × Lula manteve) |
|---|---:|
| só a UF | 0,89 |
| UF e porte | 0,91 |
| UF, porte e ~130 indicadores | 0,94 |
| só a margem de 2022 | **0,98** |
| margem de 2022, UF, porte e indicadores | 0,99 |

O AUC foi medido em validação cruzada que separa regiões imediatas inteiras entre treino e
teste, para que municípios vizinhos, quase idênticos, não se ajudem a acertar. **Os
indicadores acrescentam 0,03 a UF e porte, e praticamente nada a quem já sabe a margem de
2022.**

## Limites

- **Associação, não causa.** Nada aqui diz por que algum eleitor mudou de voto. Os dados
  são agregados por município e não seguem eleitores.
- **O corte binário é frágil.** Quem estava a 2 p.p. de empate em 2022 vira com uma
  oscilação pequena, e quem estava a 50 p.p. nunca vira. A medida contínua (seção 4) é a
  mais robusta.
- **2022 e 2026 não são a mesma disputa.** Em 2022 a comparação é Lula contra Jair
  Bolsonaro. Em 2026 é Lula contra Flávio, com mais candidatos de direita dividindo voto.
- **Cobertura desigual.** Alguns indicadores existem só para parte dos municípios (por
  exemplo, as fiscalizações federais por sorteio e os royalties de mineração), e essa
  falta de dados também segue a geografia.
- **O emprego formal subestima o agro**, que é muito informal e de conta própria. Por
  isso a fatia no PIB e o crédito rural são as medidas principais do setor.
- **Empates excluídos:** 9 municípios empatados em 2022 e 7 em 2026 (com uma casa
  decimal) ficaram fora dos dois grupos. Boa Esperança do Norte (MT), criado depois de
  2022, ficou fora de tudo. Os 5.570 municípios restantes foram casados com os
  indicadores, sem perdas.

---

**Fontes.** TSE: resultados do 1º turno presidencial de 2022 e de 2026, por município.
IBGE: Censo 2022 (raça, idade, alfabetização), PIB dos municípios e diretório de
municípios. MTE: RAIS 2024 (emprego formal por CNAE e natureza jurídica). MDS: Bolsa
Família e Pé-de-Meia. Banco Central: Pix por município e crédito rural (SICOR). Serviço Florestal Brasileiro:
Cadastro Ambiental Rural (área dos imóveis). PNUD: IDH municipal. IPEA: índice de vulnerabilidade social.
INEP: Ideb. ANM: royalties de mineração (CFEM).
