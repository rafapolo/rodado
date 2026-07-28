# Judeus no Censo Brasileiro (1980 · 1991 · 2010)

O que **6.304 registros amostrais** do Censo 2010 mostram sobre renda, escolaridade, cor
declarada e geografia da população judaica no Brasil — e o que o dado simplesmente não
alcança. Microdados do IBGE (`br_ibge_censo_demografico`), consultados em DuckDB.

> **Nota de escopo.** A análise nasceu de uma afirmação em circulação: a de que judeus no
> Brasil têm renda e escolaridade maiores que as de brancos cristãos, e que isso
> demonstraria a inexistência de discriminação estrutural contra eles. A afirmação tem
> duas partes separáveis. Uma é **empírica**: judeus têm renda e escolaridade maiores?
> A outra é **inferencial**: vantagem socioeconômica agregada prova ausência de
> discriminação estrutural? Este documento responde só a primeira.

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

Terceiro, os códigos análogos em censos anteriores reproduzem os totais publicados daqueles
anos com precisão ainda maior — **1980 bate exato**.

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

## 4. Raça governa mais que religião

**11,7% dos judeus declarados não se declaram brancos.** E a estratificação interna é severa.

| Cor/raça | Participação | População | Renda pessoal |
|---|---:|---:|---:|
| Branca | 88,3% | 93.958 | R$ 5.037 |
| **Parda** | 9,6% | 10.183 | **R$ 1.568** |
| Preta | 1,6% | 1.681 | R$ 4.154 |
| Amarela | 0,5% | 492 | R$ 3.991 |
| Indígena | 0,1% | 111 | R$ 269 |

Judeus pardos ganham **3,2x menos** que judeus brancos — abismo maior que o que separa
brancos católicos de pretos e pardos na população geral (2,1x). E as duas populações vivem
em lugares diferentes:

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

São **duas populações distintas dentro da mesma categoria censitária**. O eixo
Norte-Nordeste corresponde às comunidades históricas amazônicas — judeus marroquinos
chegados a Belém e Manaus a partir de 1810, miscigenados localmente — e a linhagens
nordestinas. O núcleo São Paulo–Rio–Rio Grande do Sul é a imigração asquenazita do século
XX, branca em 94 a 98%.

A hierarquia racial brasileira opera com força total *dentro* da judiaria. Isso sugere que
a posição socioeconômica aqui é governada por raça, não por religião — o que enfraquece o
uso da renda judaica agregada como medida de qualquer coisa relativa a antissemitismo.

---

## 5. Série histórica

| Ano | Judeus | População do país | Por milhão | Variável / peso | Aferição |
|---|---:|---:|---:|---|---|
| 1980 | 91.795 | 119.011.062 | **771** | `v508=7` / `v604` | exato |
| 1991 | 86.422 | 146.815.775 | **589** | `v0310=71` / `v7301` | validado |
| 2010 | 106.425 | 190.755.799 | **558** | `v6121=710` / `peso_amostral` | validado |

Em números absolutos a população cai e depois recupera. Como fração do país, **cai 28% em
trinta anos** — a judiaria brasileira não acompanhou o crescimento demográfico nacional.

Razão de renda pessoal, mesma definição em cada ano:

| Ano | Judeus | Católicos | Total Brasil | Razão |
|---|---:|---:|---:|---:|
| 1991 | Cr$ 3.591.858 | Cr$ 988.746 | Cr$ 1.005.167 | **3,63x** |
| 2010 | R$ 4.699 | R$ 911 | R$ 901 | **5,16x** |

Moedas diferentes e 1991 em plena hiperinflação, mas a razão dentro de cada ano é imune ao
nível de preços. A vantagem relativa não é estática: **cresceu de 3,6x para 5,2x entre 1991
e 2010**.

> **A série de renda não alcança a chegada.** A pergunta que motivava o recorte histórico —
> a vantagem já veio com os imigrantes ou foi construída no Brasil? — não é respondível com
> este material. O primeiro ponto disponível, 1991, já está cerca de sessenta anos depois
> da onda imigratória principal das décadas de 1920 e 1930. A série mostra que a vantagem
> *se ampliou* no período recente, não qual era a posição de partida.

---

## 6. Limites: o que este dado não pode fazer

Cobertura por censo:

| Censo | População | Renda | Observação |
|---|---|---|---|
| 1970 | ausente | ausente | Nenhuma coluna de religião no schema |
| 1980 | exato | ausente | Renda não recuperável na tabela |
| 1991 | validado | inferido | Variável de renda identificada por perfil |
| 2000 | ausente | ausente | Tabela não traz variável de religião |
| 2010 | validado | validado | Base principal deste documento |
| 2022 | agregado | agregado | Judaísmo diluído em "Outras religiosidades" |

**Religião declarada não é etnia.** Judeu secular ou cultural que respondeu "sem religião"
é invisível no Censo. Estimativas comunitárias de judeus étnicos no Brasil, na faixa de 120
a 150 mil, são maiores que os 107 mil por religião. Há subcontagem de composição
desconhecida, e não há como saber se os ausentes se parecem com os presentes.

**A amostra é pequena onde importa.** São 6.304 registros amostrais, caindo para 1.382 na
célula-chave — superior completo, regiões metropolitanas de São Paulo e Rio, 25 a 64 anos.
Suficiente para as diferenças grandes vistas aqui; apertado para qualquer corte mais fino.

**Duas identificações de variável são inferidas, não documentadas.** O código 710 para
judaísmo em 2010 e a variável `v3561` como renda pessoal em 1991 foram estabelecidos por
perfil estatístico e batimento com totais publicados, não por documentação oficial do IBGE.
A validação de população é forte; a variável de renda de 1991 é a peça mais frágil da cadeia.

**Renda de 1980 é irrecuperável aqui.** As colunas de alta cardinalidade da tabela de 1980 —
candidatas naturais a renda contínua — revelaram-se códigos de município: `3550308` é São
Paulo, `3304557` é Rio de Janeiro. Estender a série de renda até 1980 exigiria o layout
oficial do Censo de 1980, que não está neste acervo.

**O dado não decide a questão que o motivou.** Renda e escolaridade agregadas medem posição
socioeconômica. Se posição socioeconômica é ou não um teste válido de discriminação
estrutural é uma questão conceitual, não estatística — e a literatura sobre minorias
economicamente dominantes existe justamente porque essa equivalência falha com frequência.
Este documento estabelece os fatos de renda. Não estabelece o que eles provam.

---

**Projeto relacionado:**
[Shutafut — Empresas Israelenses no Brasil](/analises/shutafut/) ·
visualização em rede de empresas israelenses operando no Brasil, seus sócios brasileiros,
estruturas de propriedade e atividades econômicas.
