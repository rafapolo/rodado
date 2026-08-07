# Bens dos candidatos

Toda pessoa que se candidata no Brasil assina uma declaração de bens. Ela é pública, item a
item. Este painel junta as declarações de **1.025 pessoas que já foram eleitas deputado
federal** — 4.000 declarações ao todo, de 2010 a 2026 — e as coloca contra uma régua só: o
subsídio que o próprio cargo depositou na conta delas no mesmo período.

**[→ Abrir o painel](https://claude.ai/code/artifact/af80ed4f-4dd3-4a52-9e2a-6330acccb277)**

![Dispersão de 900 parlamentares: patrimônio declarado no eixo horizontal, em escala logarítmica de R$ 1 mil a mais de R$ 10 milhões, contra o crescimento patrimonial em múltiplos do subsídio do período no eixo vertical. A massa se concentra em torno de zero e uma pluma sobe à direita; 156 pontos ficam acima da linha tracejada de 1×](/analises/img/panorama-bens-candidatos.png)

Dá para procurar qualquer parlamentar pelo nome, ver a trajetória declarada dele eleição por
eleição, filtrar por partido, estado e espectro, e ampliar qualquer região do gráfico.

---

## O que aparece

**A regra é o patrimônio parado.** Dos 900 parlamentares com régua comparável, **744 — 83%**
ficam abaixo da linha: o patrimônio deles cresceu menos do que o salário bruto do período. A
mediana do crescimento declarado é **0,24 vez** o subsídio
do período: o parlamentar típico termina o intervalo entre duas declarações com um quarto do que
o cargo lhe pagou convertido em bens. Um quarto deles declara crescimento praticamente nulo, e
metade fica abaixo de 0,7.

Entre os eleitos em 2018 que voltaram a se registrar em 2022, **306 dos 471 — 65%** declararam,
ao fim do mandato, possuir menos do que o mandato lhes pagou de salário bruto. E 17 deputados
federais declararam não possuir bem nenhum.

Isso não é acusação, e também não é retrato fiel de riqueza: o subsídio é bruto, e depois de
imposto e de viver sobra pouco para virar patrimônio — mas a declaração também subestima o que
se tem, por regra e por omissão, como a seção seguinte detalha. É justamente essa forma que torna visível a outra ponta.

**A outra ponta são 156 pessoas.** Elas declararam crescimento patrimonial maior do que todo o
subsídio recebido no intervalo entre a primeira e a última declaração. No recorte de 2018 a 2022
isoladamente, são 47.

Mas essa conta cobra do salário uma explicação que às vezes está em outro lugar. Quem é sócio de
empresa tem origem de renda fora do mandato, e ignorar isso seria injusto. Aplicando a mesma
régua generosa da análise anterior — somar ao subsídio o **capital social integral** de toda
empresa em que a pessoa consta como sócia, sem descontar a parte dos demais sócios e sem exigir
que esse capital tenha virado renda:

| | pessoas |
|---|---:|
| Acima da linha considerando só o subsídio | 156 |
| …cujo capital social já cobre o crescimento inteiro | **40** (26%) |
| …que seguem acima mesmo somando o capital social | **92** |
| …destes, sem nenhuma empresa registrada | 24 |

Ou seja: **um quarto dos casos deixa de ser anomalia de salário assim que a empresa entra na
conta** — e vira outra pergunta, de contabilidade empresarial, com outros documentos. Restam 92
pessoas cujo crescimento declarado supera tudo o que o mandato pagou *e* tudo o que as empresas
delas poderiam explicar, somando R$ 442 milhões sem contrapartida no dado público. Vinte e quatro
delas não constam como sócias de empresa nenhuma.

Atenção a uma limitação do gráfico e do painel: **eles ainda mostram o múltiplo só contra o
subsídio.** A régua ampliada acima foi calculada à parte. Quem usar a figura ou a ferramenta para
apontar um caso precisa checar o capital social da pessoa antes de concluir qualquer coisa —
é o que a tabela desta seção diz que muda em um quarto das vezes.

**A diferença entre partidos é de grau, não de natureza.**

![Mapa de calor com 11 partidos nas linhas e faixas de crescimento patrimonial nas colunas, cada linha somando 100%. A massa de todas as bancadas se concentra em torno de zero, à esquerda da divisa de 1×, e um traço branco marca a mediana de cada partido — do PT, o menor, ao PODE, o maior](/analises/img/partidos-desvio-regua.png)

Nenhuma bancada foge do padrão: em todas elas a massa fica à esquerda da divisa de 1×. O que
muda é a mediana, que escorrega de 0,10 vez o subsídio no PT a 0,44 no PODE, e a espessura da
cauda à direita. A distância entre a legenda mais contida e a mais expandida é de um terço de
salário — real, mas modesta perto da variação dentro de cada bancada.

| partido | n | mediana | acima de 1× |
|---|---:|---:|---:|
| PT | 103 | 0,10× | 5 (5%) |
| REPUBLICANOS | 78 | 0,12× | 9 (12%) |
| PSB | 35 | 0,20× | 6 (17%) |
| PSDB | 43 | 0,26× | 9 (21%) |
| PL | 130 | 0,28× | 24 (18%) |
| PSD | 75 | 0,30× | 15 (20%) |
| MDB | 84 | 0,31× | 15 (18%) |
| PDT | 31 | 0,33× | 6 (19%) |
| PP | 87 | 0,34× | 25 (29%) |
| UNIÃO | 73 | 0,36× | 16 (22%) |
| PODE | 27 | 0,44× | 6 (22%) |

O PT tem a menor mediana e também a menor proporção acima da linha — 5%, contra 29% do PP. Mas
o mapa cobra cautela: só entram partidos com pelo menos 20 parlamentares de régua comparável, o
partido considerado é o do último registro e não o da eleição em que a pessoa foi eleita, e
diferenças de poucos pontos entre bancadas de 30 pessoas não sobrevivem ao acaso.

**E direita contra esquerda?** As três últimas linhas do mapa agregam os partidos por bloco
ideológico, na mesma escala:

| bloco | n | mediana | acima de 1× |
|---|---:|---:|---:|
| esquerda | 201 | 0,15× | 20 (10%) |
| direita | 411 | 0,26× | 82 (20%) |
| centro | 273 | 0,31× | 52 (19%) |

A esquerda tem metade da proporção das outras duas acima da linha. Mas **centro e direita são
indistinguíveis entre si** — 19% e 20% —, o que já derruba a leitura de que o eixo esquerda-direita
organize o fenômeno: se organizasse, o centro ficaria no meio, e ele não fica.

O que enfraquece de vez a explicação por bloco é a variação **dentro** de cada um. Na direita, a
mediana vai de 0,12× no REPUBLICANOS a 0,36× no UNIÃO; no centro, de 0,26× no PSDB a 0,44× no
PODE; na esquerda, de 0,10× no PT a 0,33× no PDT. Cada bloco cobre quase toda a amplitude dos
outros. Saber o partido de alguém informa mais sobre o patrimônio declarado dele do que saber
o lado do espectro — e saber qualquer um dos dois informa pouco, porque o que domina é a
variação entre pessoas da mesma legenda.

Vale lembrar também que os blocos têm tamanhos muito diferentes — 411 à direita contra 201 à
esquerda —, o que faz a direita concentrar mais casos absolutos acima da linha (82 contra 20)
simplesmente por ser maior. É por isso que a comparação aqui é sempre proporcional.

**E abaixo da linha, a anomalia é de sinal contrário.** Somar o capital social à régua não muda
nada para quem já está abaixo — só empurra para mais longe. Mas cruzar os dois dados nesse grupo
revela outra coisa: gente que **declara possuir menos do que as próprias empresas valem**.

Dos 744 abaixo da linha, 456 (61%) são sócios de alguma empresa. E entre eles:

| | pessoas | |
|---|---:|---:|
| Capital social somado maior do que **tudo** o que declaram possuir | 105 | 14% dos 744 |
| Sócios que não declaram nenhuma participação societária | 211 | 46% dos sócios |
| As duas coisas ao mesmo tempo | **40** | |

Esses 40 são donos de empresas com R$ 184 milhões de capital social somado e declaram, juntos,
R$ 21 milhões de patrimônio — sem uma linha de participação societária em nenhuma das
declarações. A comparação é grosseira de propósito: capital social é o que foi subscrito na
empresa, não o que cabe à pessoa, e uma cota de 5% numa empresa de R$ 90 milhões não obriga
ninguém a declarar R$ 90 milhões.

Mas obriga a declarar alguma coisa. E é aí que o grupo abaixo da linha deixa de ser só a
paisagem normal da Câmara: quem cresce pouco pode estar vivendo do salário, como a maioria, ou
pode simplesmente não estar contando o que tem. Os dois casos ficam no mesmo lugar do gráfico, e
o gráfico sozinho não os separa.

**Por bloco, a leitura se inverte no meio do caminho.**

| bloco | abaixo da linha | são sócios | capital > declarado | sócios que **não** declaram |
|---|---:|---:|---:|---:|
| esquerda | 181 | 70 (39%) | 12 (7%) | **42 (60%)** |
| centro | 221 | 155 (70%) | 36 (16%) | 64 (41%) |
| direita | 329 | 226 (69%) | 57 (17%) | 102 (45%) |

Nas duas primeiras colunas o resultado é o esperado e pouco interessante: a esquerda tem muito
menos empresários — 39% contra cerca de 70% dos outros dois blocos —, e por isso também menos
casos de capital social maior que o patrimônio declarado. É composição, não comportamento.

A última coluna é que surpreende. **Entre os parlamentares de esquerda que são sócios de empresa,
60% não declaram a participação** — a maior taxa dos três blocos, acima dos 45% da direita e dos
41% do centro. A esquerda tem menos empresários, mas os que tem omitem a cota com mais
frequência. Com 70 sócios de esquerda contra 226 de direita, a diferença fica no limite do que a
amostra sustenta, e merece confirmação caso a caso antes de virar afirmação.

**Acima da linha, o bloco não explica nada.** Aplicando a régua ampliada com o capital social, a
proporção que sobrevive é praticamente idêntica nos três: 60% na esquerda, 58% no centro, 60% na
direita. O desconto das empresas retira a mesma fatia de cada lado do espectro.

**O salário ficou parado oito anos.** O subsídio de deputado federal foi fixado em R$ 33.763 com
efeitos a partir de fevereiro de 2015 e só mudou em janeiro de 2023, quando passou a R$ 39.293.
As legislaturas 2015-2018 e 2019-2022 inteiras correram com o mesmo valor nominal. Por isso a
régua aqui é calculada mês a mês, e não por média — e por isso ela difere entre quem foi
reeleito e quem entrou novo, já que o reeleito passou mais meses recebendo dentro da mesma
janela.

**Dois terços têm empresa.** 683 das 1.025 pessoas constam como sócias ou titulares de ao menos
uma empresa nos registros da Receita Federal. Ter empresa é renda fora do salário, e o painel
mostra isso ao lado do patrimônio justamente para que a comparação com o subsídio não seja lida
como acusação onde há explicação.

**Mas quatro em cada dez não põem a empresa na declaração de bens.** A cota de uma sociedade é
um bem como outro qualquer, e o formulário do TSE tem rubrica própria para ela — "quotas ou
quinhões de capital", "ações", "outras participações societárias", os mesmos códigos do imposto
de renda. Cruzando quem consta como sócio na Receita com o que declarou à Justiça Eleitoral no
registro mais recente:

| | pessoas | % dos sócios |
|---|---:|---:|
| Sócios que **declaram** participação societária | 412 | 60,3% |
| Sócios que **não declaram** nenhuma | **271** | **39,7%** |
| …destes, com capital social somado ≥ R$ 100 mil | 125 | 18,3% |
| …destes, com capital social somado ≥ R$ 1 milhão | 40 | 5,9% |

Vinte e um dos 271 declararam patrimônio zero — nada, nenhum bem. E há o movimento contrário:
48 pessoas declaram participação societária sem constar como sócias em nenhuma empresa ativa no
retrato da Receita, o que é esperado para quem tem cota em empresa já encerrada ou fora do
recorte.

O número não prova omissão. As regras do imposto de renda dispensam declarar cotas de uma mesma
empresa cujo valor de aquisição some menos de R$ 1.000, e quem é sócio sem capital ou tem cota
ainda não integralizada não tem custo a lançar. Há também descompasso de data: o retrato do
quadro societário é de setembro de 2024, e a declaração pode ser de 2022 ou de 2026. É por isso
que o corte de R$ 1 milhão importa — ali as três explicações deixam de ser plausíveis, e sobram
40 casos.

**2026 ainda está em aberto.** O prazo de registro se encerra em 15 de agosto de 2026. Quando
estes dados foram extraídos, o arquivo público cobria cerca de 28% das candidaturas esperadas.
Os pontos de 2026 aparecem marcados como parciais: ausência ali não significa ausência de bem,
significa candidatura ainda não registrada.

---

## O que a declaração de bens não é

Nada aqui mede patrimônio. Mede **declaração de patrimônio** — e a distância entre as duas coisas
é grande, conhecida e tem direção previsível.

A declaração é preenchida pelo próprio candidato, não é auditada no ato do registro, e segue a
regra do imposto de renda: bens entram pelo **custo de aquisição**. Um apartamento comprado em
1995 continua declarado a preço de 1995. Isso sozinho já põe o valor declarado muito abaixo do
valor real, sem nenhuma má-fé envolvida — é o que a norma manda.

Some-se a isso a omissão, que este próprio levantamento consegue enxergar:

- **271 dos 683 sócios de empresa** não declaram nenhuma participação societária, embora o
  formulário tenha rubrica própria para isso
- **40 pessoas** são sócias de empresas com R$ 184 milhões de capital social somado e declaram
  R$ 21 milhões de patrimônio, sem uma linha de cota
- **215 de 988 pessoas — 22%** declaram hoje menos do que já declararam em algum registro
  anterior, e 37 declararam algo no passado e zero depois

Esse último número é o mais eloquente. Patrimônio pode encolher de verdade — venda de bem,
divórcio, dívida, um mau negócio. Mas um quinto de um grupo perdendo patrimônio ao longo de anos
não descreve uma economia; descreve inconsistência entre declarações da mesma pessoa.

**A consequência para tudo o que está acima é assimétrica.** Não há incentivo para declarar mais
do que se tem, e há vários para declarar menos. Então:

O número de pessoas acima da régua é um **piso**, não um teto. Quem omite bens no registro final
aparece com crescimento menor do que teve, e alguns dos que estão logo abaixo da linha só estão
ali por isso.

E o grupo abaixo da linha **não é uma certidão de modéstia**. Ele mistura quem de fato vive do
salário — a maioria, e é o comportamento esperado — com quem simplesmente não contou o que tem.
O gráfico põe os dois no mesmo lugar e não sabe separá-los.

Por isso o múltiplo serve para **ordenar e priorizar**, não para concluir. Ele diz por onde
começar a checar. Qualquer afirmação sobre uma pessoa específica exige sair daqui e ir aos
documentos: quadro societário atualizado, registro de imóveis, declaração de imposto de renda.

---

## Como ler

O múltiplo do subsídio mede **quanto da variação patrimonial o salário deixa de explicar**. Não
mede ilicitude. Parlamentar pode ter empresa, aluguel, herança, venda de bem, ganho de capital
ou renda do cônjuge — e a maioria dos casos acima da linha tem alguma dessas explicações
disponível. O número é onde a checagem começa, não onde ela termina.

Os valores são nominais e estão a custo de aquisição, porque é assim que a declaração de bens é
preenchida: um imóvel comprado em 1990 continua declarado a preço de 1990. Nada aqui é corrigido
pela inflação — corrigir introduziria um valor que a declaração não afirma.

A régua conta apenas os meses de mandato federal. Quando alguém passou parte do intervalo num
mandato municipal ou estadual, cujo valor não entra nesta conta, o período aparece marcado como
parcial em vez de ser tratado como se não tivesse havido remuneração alguma. E quando a régua
acumulada não chega a cerca de um ano de subsídio, o painel diz que não há comparação possível
em vez de inventar um número — são 125 das 1.025 pessoas.

**A série começa em 2010, e não antes, por um defeito na fonte.** Nos arquivos de 2006 e 2008 o
identificador que liga cada candidato aos bens que declarou não é único: há 19.204 registros de
candidatura para 3.162 identificadores distintos em 2006. Cruzar por ele nesses dois anos
espalha os bens de uma pessoa por dezenas de outras — o sintoma foi um patrimônio de R$ 132
milhões aparecendo idêntico em duas pessoas diferentes. De 2010 em diante o identificador é
único e o cruzamento fecha.

---

**Fontes:** Tribunal Superior Eleitoral, declarações de bens dos registros de candidatura de 2010
a 2026; Câmara dos Deputados, decretos legislativos que fixaram o subsídio parlamentar (nº
112/2007, nº 805/2010, nº 276/2014 e nº 172/2022); Receita Federal, Cadastro Nacional da Pessoa
Jurídica, quadro societário.

Análise relacionada: [O salário não explica](/analises/o-salario-nao-explica/), que examina caso
a caso os deputados no topo dessa distribuição.
