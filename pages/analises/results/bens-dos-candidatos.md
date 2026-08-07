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

Isso não é acusação, é a linha de base: o subsídio é bruto, e depois de imposto e de viver sobra
pouco para virar patrimônio. É justamente essa forma que torna visível a outra ponta.

**A outra ponta são 156 pessoas.** Elas declararam crescimento patrimonial maior do que todo o
subsídio recebido no intervalo entre a primeira e a última declaração. No recorte de 2018 a 2022
isoladamente, são 47.

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
