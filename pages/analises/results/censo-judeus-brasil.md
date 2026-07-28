# Judeus no Censo Brasileiro

O que **6.304 registros amostrais** do Censo 2010 mostram sobre renda, escolaridade, cor
declarada e geografia da população judaica no Brasil — e o que o dado simplesmente não
alcança. Microdados do IBGE (`br_ibge_censo_demografico`), consultados em DuckDB.

---

## 1. Como identificar judeus no microdado

O Censo pergunta religião, não etnia. No Censo 2010 a variável é `v6121` e o código do
judaísmo é `710`. O dicionário do dataset **não documenta** essa variável, então a
identificação foi validada por três vias independentes.

Primeiro, o esquema geral de códigos bate com totais publicados pelo IBGE:

| Código | Religião | Calculado | Publicado IBGE | Erro |
|---|---:|---:|---:|---:|
| 110 | Católica | 122.682.929 | 123.280.172 | 0,5% |
| 610 | Espírita | 3.844.732 | 3.848.876 | 0,1% |
| 620 | Umbanda | 407.354 | 407.331 | 0,0% |
| 630 | Candomblé | 167.119 | 167.363 | 0,1% |
| 001 | Agnóstico | 124.300 | 124.436 | 0,1% |
| 002 | Ateu | 615.242 | 615.096 | 0,0% |
| **710** | **Judaísmo** | **106.425** | **107.329** | **0,8%** |

Segundo, a geografia do código 710 reproduz a distribuição histórica conhecida da judiaria
brasileira: São Paulo 48%, Rio 23%, com Rio Grande do Sul, Pernambuco e Pará
desproporcionalmente representados — as colônias agrícolas gaúchas, Recife, e a comunidade
marroquina de Belém.

Cada um desses núcleos vem de uma migração distinta, e é essa sobreposição de ondas que
produz o mapa. **Recife** é o mais antigo e o mais descontínuo: a Kahal Zur Israel, fundada
por volta de 1636 sob domínio holandês, foi a primeira sinagoga das Américas, e se dispersou
com a retomada portuguesa de Pernambuco em 1654 — parte daquela comunidade seguiu para Nova
Amsterdã e originou a primeira congregação judaica da América do Norte. A comunidade
recifense de hoje não é continuação daquela: é majoritariamente do século XX, sobre um
substrato colonial de cristãos-novos. O **Rio Grande do Sul** nasce de um projeto dirigido —
a Jewish Colonization Association, do barão Maurice de Hirsch, assentou judeus do Leste
Europeu em colônias agrícolas como Philippson (1904) e Quatro Irmãos (1912), cujas famílias
depois migraram em massa para Porto Alegre. **Belém e Manaus** vêm dos sefarditas marroquinos
chegados a partir de 1810, tratados na seção 4. E o eixo **São Paulo–Rio**, que hoje
concentra 71% do total, é sobretudo a grande onda asquenazita do início do século XX, com
pico nos anos 1920 e 1930, somada a sefarditas do Oriente Médio e a refugiados do pós-guerra.
Foi também a onda que esbarrou na política imigratória do Estado Novo, incluindo a Circular
Secreta 1.127, de 1937, que instruía o corpo diplomático brasileiro a negar visto a judeus.

Terceiro, os códigos análogos em censos anteriores reproduzem os totais publicados daqueles
anos com precisão ainda maior: em 1980 (`v508=7`, peso `v604`) o cálculo dá **91.795**
contra 91.795 publicados — exato.

---

## 2. Renda e escolaridade

Valores nominais de 2010, salário mínimo = R$ 510.

| Grupo | n amostral | Renda pessoal | Renda domiciliar | Per capita (SM) |
|---|---:|---:|---:|---:|
| **Judeus** | 6.304 | **R$ 4.699** | **R$ 11.774** | **8,04** |
| Brancos católicos | 6.777.876 | R$ 1.251 | R$ 3.544 | 2,14 |
| Brancos evangélicos | 1.977.630 | R$ 902 | R$ 2.751 | 1,56 |
| Pretos e pardos | 10.603.690 | R$ 586 | R$ 1.818 | 0,97 |
| Indígenas | 111.816 | R$ 412 | R$ 1.181 | 0,57 |

Escolaridade, pessoas de 25 anos ou mais:

| Grupo | Superior completo | Até fundamental incompleto |
|---|---:|---:|
| **Judeus** | **62,1%** | 8,7% |
| Brancos católicos | 16,6% | 43,2% |
| Brancos evangélicos | 11,0% | 43,7% |
| Pretos e pardos | 5,6% | 57,1% |

**A premissa factual se confirma.** Judeus declarados têm renda e escolaridade
substancialmente maiores que as de brancos cristãos no Censo 2010.

---

## 3. A vantagem sobrevive aos controles — reduzida

A comparação bruta confunde religião com três outras coisas: idade média mais alta (40,8
anos contra 34,2 dos brancos católicos), concentração metropolitana e escolaridade.
Restringindo a São Paulo e Rio, faixa de 25 a 64 anos, e comparando dentro da mesma faixa
de instrução:

| Grupo | Médio completo | Superior completo |
|---|---:|---:|
| **Judeus** | **R$ 3.719** | **R$ 8.107** |
| Brancos católicos | R$ 1.674 | R$ 5.382 |
| Brancos evangélicos | R$ 1.271 | R$ 3.719 |
| Pretos e pardos | R$ 1.075 | R$ 3.029 |

A razão judeus/brancos católicos cai de **3,76x** na comparação bruta para **1,51x** entre
pessoas com superior completo, mesma região e mesma faixa etária. A maior parte do
diferencial bruto é composição — escolaridade, idade, geografia. Mas sobra um diferencial
real depois dos controles.

---

## 4. Os judeus não brancos

**11,7% dos judeus declarados não se declaram brancos** — cerca de 12,5 mil pessoas. E a
estratificação interna é severa.

| Cor/raça | Participação | População | Renda pessoal |
|---|---:|---:|---:|
| Branca | 88,3% | 93.958 | R$ 5.037 |
| **Parda** | 9,6% | 10.183 | **R$ 1.568** |
| Preta | 1,6% | 1.681 | R$ 4.154 |
| Amarela | 0,5% | 492 | R$ 3.991 |
| Indígena | 0,1% | 111 | R$ 269 |

Judeus pardos ganham **3,2x menos** que judeus brancos — abismo maior que o que separa
brancos católicos de pretos e pardos na população geral (2,1x).

### Onde eles estão

As duas populações não convivem: elas ocupam regiões diferentes do país.

| UF | Brancos | Pretos e pardos | % não branca |
|---|---:|---:|---:|
| Bahia | 1.006 | 1.244 | **54,8%** |
| Pará | 932 | 1.036 | **52,7%** |
| Amazonas | 802 | 864 | **50,9%** |
| Minas Gerais | 2.187 | 1.167 | 34,8% |
| Pernambuco | 1.753 | 655 | 27,2% |
| Paraná | 3.747 | 341 | 8,3% |
| Rio de Janeiro | 22.943 | 1.334 | 5,5% |
| São Paulo | 48.749 | 1.947 | 3,8% |
| Rio Grande do Sul | 7.373 | 131 | 1,7% |

No eixo Norte-Nordeste a maioria dos judeus **não é branca**. No núcleo São Paulo–Rio–Rio
Grande do Sul, a população é branca em 94 a 98%. Descendo ao nível municipal, o padrão fica
mais nítido — e aponta para o rio:

| Município | n amostral | Judeus | % não branca |
|---|---:|---:|---:|
| Belém (PA) | 61 | 1.346 | 39,6% |
| Manaus (AM) | 60 | 1.183 | 42,7% |
| Macapá (AP) | 18 | 217 | 40,1% |
| Benjamin Constant (AM) | 17 | 203 | 72,2% |
| Santarém (PA) | 9 | 93 | 100% |
| Tabatinga (AM) | 9 | 92 | 88,9% |

Belém e Manaus são as duas maiores populações judaicas do Norte. Quanto mais interior
adentro, maior a fração não branca — embora as cidades ribeirinhas apareçam com amostras
minúsculas, de 9 a 17 registros, e os percentuais delas devam ser lidos como indício de
direção, não como medida.

### Os marroquinos do Amazonas

O contexto histórico não vem do Censo, mas explica o que ele mede.

**Por que saíram.** No norte do Marrocos, judeus viviam confinados aos *mellahs*, os bairros
judaicos, sob o estatuto de *dhimmi* — condição legal subordinada, com imposto específico e
restrições impostas a não muçulmanos. Somem-se pobreza, fome e episódios de violência: a
guerra hispano-marroquina de 1859-60 atingiu Tetuán diretamente e produziu uma das ondas de
saída. As comunidades de origem eram Tânger, Tetuán e Casablanca, e também Rabat, Fez e
Marrakesh.

**Por que o Brasil.** A abertura dos portos em 1808 e a garantia constitucional de culto
privado a não católicos, em 1824, abriram a porta. Mas o ímã foi econômico: a explosão da
borracha como matéria-prima industrial, que entre 1879 e 1912 atraiu gente do mundo inteiro
para a Amazônia. Não foi só refúgio — foi uma economia em expansão oferecendo a mobilidade
que o Marrocos negava por lei.

**Quantos e quando.** Cerca de **mil famílias entre 1810 e 1910** — um século de fluxo
contínuo, não uma leva única. A primeira sinagoga da Amazônia, a Essel Avraham, foi
inaugurada em **Belém em 1824**; o primeiro cemitério judaico da cidade, em **1842**. É a
primeira imigração judaica organizada e duradoura do Brasil independente, um século antes da
onda asquenazita que formaria as comunidades de São Paulo e do Rio.

De Belém subiram o rio. Muitos trabalharam como **regatões**, comerciantes itinerantes que
percorriam o Amazonas e seus afluentes vendendo mercadoria e comprando produto da floresta.
O comércio fixou famílias em Cametá, Baião, Gurupá, Breves, Macapá, Altamira, Santarém,
Óbidos, Alenquer, Faro, Oriximiná, Itaituba, Boim e Aveiros — e adiante, até Iquitos, na
Amazônia peruana.

Daí as duas consequências que o Censo de 2010 registra. A primeira é a **dispersão
ribeirinha**: comunidades de poucas famílias espalhadas por dezenas de povoados que nenhuma
lista de "judiaria brasileira" costuma mencionar. A segunda é a **miscigenação**, que decorre
da primeira — núcleos desse tamanho não sustentam endogamia por gerações, e a descendência
manteve identificação judaica declarada sem corresponder à branquitude que o país associa a
judeus.

Há uma lacuna importante entre a história e o dado. Estimativas de divulgação falam em
dezenas de milhares de descendentes já no fim do século XIX, enquanto o Censo 2010 encontra
cerca de **3.600 judeus no Pará e Amazonas somados**. Os dois números não se contradizem:
medem coisas diferentes. O Censo capta quem **declara judaísmo como religião** — a
descendência que não pratica, ou que se identifica de outro modo, é invisível para ele. É o
limite da seção 5 em forma concreta, e provavelmente o maior deles neste recorte.

Ainda assim, Belém tem hoje população judaica declarada equivalente à de Belo Horizonte
(1.346 contra 1.300, diferença dentro do erro amostral), e Manaus vem logo atrás. São
comunidades com duzentos anos de presença contínua, quatro em cada dez de seus membros
declarando-se pretos ou pardos — mais antigas que a imigração que define a imagem pública do
judeu no Brasil.

> Fontes do bloco histórico: [CONIB](https://conib.org.br/noticias/todas-as-noticias/a-historia-dos-mais-de-200-anos-da-imigracao-judaica-na-amazonia.html),
> [Portal Amazônia](https://portalamazonia.com/historias-da-amazonia/judeus-amazonia-terceira-geracao/),
> [Morashá](https://www.morasha.com.br/hoje-no-brasil/los-nuestros-os-marroquinos-na-amazonia.html) e
> [Museu da Inquisição](https://museudainquisicao.org.br/artigos/duzentos-anos-de-miscigenacao-judaica-na-amazonia/).
> A obra de referência é *Eretz Amazônia: os judeus na Amazônia*, de Samuel Benchimol (1998).

### O que isso significa para a leitura da renda

A hierarquia racial brasileira opera com força total *dentro* da judiaria: mesma religião
declarada, renda 3,2x menor. Isso sugere que a posição socioeconômica aqui é governada por
raça, não por religião — o que enfraquece o uso da renda judaica agregada como medida de
qualquer coisa relativa a antissemitismo. A média de R$ 4.699 descreve principalmente uma
população branca, metropolitana e de imigração recente, e apaga uma minoria interna cuja
renda se parece com a do resto do Norte do país.

---

## 5. Limites: o que este dado não pode fazer

**Religião declarada não é etnia.** Judeu secular ou cultural que respondeu "sem religião"
é invisível no Censo. Estimativas comunitárias de judeus étnicos no Brasil, na faixa de 120
a 150 mil, são maiores que os 107 mil por religião. Há subcontagem de composição
desconhecida, e não há como saber se os ausentes se parecem com os presentes.

**A amostra é pequena onde importa.** São 6.304 registros amostrais, caindo para 1.382 na
célula-chave — superior completo, regiões metropolitanas de São Paulo e Rio, 25 a 64 anos.
Os municípios amazônicos do interior aparecem com 9 a 17 registros: suficiente para
sinalizar um padrão consistente com a história conhecida, insuficiente para quantificá-lo.

**O código 710 é inferido, não documentado.** A identificação do judaísmo em 2010 foi
estabelecida por perfil estatístico, batimento com totais publicados e coerência
geográfica — não por documentação oficial do IBGE.

**2010 é o dado mais recente possível.** O Censo 2022 dilui o judaísmo dentro de "Outras
religiosidades", sem desagregação. A tabela de 2000 do acervo não traz variável de religião,
e a de 1970 não tem coluna de religião identificável. Só 1980, 1991 e 2010 permitem
identificar judeus, e apenas 2010 traz o conjunto completo de renda, instrução e cor.

**O dado não decide a questão que o motivou.** Renda e escolaridade agregadas medem posição
socioeconômica. Se posição socioeconômica é ou não um teste válido de discriminação
estrutural é uma questão conceitual, não estatística — e a literatura sobre minorias
economicamente dominantes existe justamente porque essa equivalência falha com frequência.
Este documento estabelece os fatos de renda. Não estabelece o que eles provam.

---

**Projeto relacionado:**

[![Shutafut — rede de empresas israelenses no Brasil](/analises/shutafut/demo.jpg)](/analises/shutafut/)

[**Shutafut — Empresas Israelenses no Brasil**](/analises/shutafut/) · visualização em rede
de 394 empresas israelenses e 391 brasileiras operando no país, com seus sócios, estruturas
de propriedade e atividades econômicas, navegável por CNAE e por linha do tempo.
