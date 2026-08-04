# Religião × Polarização política nos municípios (2024 × Censo 2022)

Cruzamento do mapa de **inclinação/polarização das prefeituras 2024** (1º turno, TSE, voto
ponderado pela nota ideológica do partido de cada candidato) com o **perfil religioso do
Censo 2022** (IBGE). Junção por `UF + nome normalizado`: **5.546 de 5.557** municípios
casaram (11 perdidos por grafia).

![Lado a lado: inclinação ideológica do voto para prefeito em 2024 (esquerda) e perfil religioso dos municípios no Censo 2022 (direita)](/analises/img/religiao-x-polarizacao-mapas.jpg)

Os dois mapas lado a lado: à esquerda, cada município colorido pela inclinação ideológica do
voto para prefeito (vermelho = esquerda, azul = direita); à direita, o mesmo território
colorido pelo perfil religioso declarado no Censo (amarelo = mais católico, roxo = mais
evangélico). O Nordeste amarelo-e-avermelhado e o Sul azul são o que sustenta — e o que
limita — toda a análise abaixo.

**Mapas interativos:**
[Prefeitos 2024 — Esquerda × Direita](https://xn--2dk.xyz/dataviz/eleicoes) ·
[Perfil Religioso dos Municípios](https://xn--2dk.xyz/dataviz/religioes) ·
[Igrejas Geolocalizadas](https://xn--2dk.xyz/dataviz/religioes/igrejas)

> **Nota de versão.** As notas ideológicas usam o survey de especialistas de Bolognesi,
> Ribeiro & Codato, com **um override**: o **PL → 8,5** (mais à direita que o NOVO, 8,2),
> porque o survey é de 2018, antes de o PL virar a legenda do bolsonarismo. Como o PL é o
> maior partido em votos (15,6M), esse ajuste desloca perceptivelmente a cauda direita.
> Detalhes em `../metodologia.md`.

---

## 1. Religião prediz o *lado*, não a *intensidade*

A composição religiosa se correlaciona com **para onde** o município pende — mas **não** com
o quão dividido/polarizado ele é.

| correlação (n=5.546) | com **inclinação** (dir+) | com **polarização** |
|---|---:|---:|
| **% evangélica** | **+0,214** | −0,01 |
| **% católica** | **−0,180** | −0,01 |
| % espírita | +0,074 | — |
| % sem religião | +0,033 | +0,06 |
| % umbanda/candomblé | −0,005 | — |

Mais evangélicos → mais à direita; mais católicos → mais à esquerda. Mas **nenhuma**
religião prevê polarização (todos os `r` ≈ 0). **A religião move o eixo esquerda↔direita,
não o grau de racha ideológico** — o achado "negativo" mais limpo do conjunto (ver §6 para
o que *de fato* move a polarização).

## 2. O gradiente: a esquerda some antes de a direita crescer

Municípios ordenados por % evangélica, em quintis:

| faixa evangélica | evang. média | inclinação | % voto **direita** | % voto **esquerda** |
|---|---:|---:|---:|---:|
| 1–13% | 10,0% | 5,64 | 34,2% | **23,8%** |
| 13–19% | 16,3% | 5,82 | 36,5% | 19,0% |
| 19–25% | 21,7% | 6,02 | 40,2% | 14,6% |
| 25–31% | 27,9% | 6,23 | 46,7% | 10,9% |
| **31–89%** | 38,4% | 6,28 | **49,8%** | **11,0%** |

Do quintil menos ao mais evangélico, o voto de direita sobe +16pp (34→50%) e o de esquerda
**cai pela metade** (24→11%). O efeito é mais um **recuo da esquerda** em território
evangélico do que uma explosão da direita (que já era maioria em quase todo lugar).

![Heatmap do cruzamento entre % evangélica e inclinação ideológica, com painéis por região](/analises/img/religiao-x-polarizacao-heatmap.png)

O mesmo gradiente visto como distribuição conjunta. **A cor não é contagem de municípios** —
é o resíduo padronizado, o quanto cada célula foge do esperado se religião e voto fossem
independentes; um heatmap de densidade crua só mostraria que quase todo município fica entre
5,5 e 6,5. O número dentro da célula é o dado literal (% da faixa evangélica, cada linha
soma 100). Células com |z| < 1,3 ficam cinza: é ruído amostral, não associação.

Duas coisas que a tabela acima não mostra. Primeiro, a **assimetria** do §2 aparece na
intensidade: o canto inferior-esquerdo (pouco evangélico, esquerda dura) é a célula mais
saturada do painel — z = +9,0, de longe o maior desvio da grade —, enquanto o canto
direito cresce de forma bem mais modesta. O que a religião prevê com força é a **presença da
esquerda**, não a da direita. Segundo, os painéis regionais são o §3 renderizado: a diagonal
sobrevive no **Nordeste** e no **Sudeste** e **some por completo no Sul e no Centro-Oeste**,
que saem cinza. Os cinco painéis dividem uma escala de cor fixa — um painel sem cor é
ausência de associação, não falta de dados.

## 3. Metade disso é geografia (mas não toda)

Confundidor: o **Nordeste** é ao mesmo tempo mais católico e mais à esquerda (redutos do
PT); **Norte/Centro-Oeste** são mais evangélicos e mais à direita. Testando a correlação
evangélico→direita **dentro** de cada região:

| região | r(evang, lean) |
|---|---:|
| **Nordeste** | **+0,159** |
| Sudeste | +0,112 |
| Norte | +0,088 |
| Centro-Oeste | +0,032 |
| Sul | +0,032 |

O `r` nacional (+0,214) não só encolhe dentro das regiões — ele **desaparece no Sul e no
Centro-Oeste**, e o sinal do católico chega a **inverter** (r=+0,03): lá o município é ao
mesmo tempo muito católico (72,6% no Sul) *e* de direita (lean 6,17). A clivagem
religião↔política é, na prática, um **fenômeno do Nordeste** (e em parte do Sudeste), onde a
base católica popular sustenta o PT; **não é uma lei nacional**. No Sul, católico
colonial-conservador (herança ítalo-alemã) e evangélico votam igualmente à direita.

### 3b. Não é o *tipo* de evangélico (teste da hipótese luterana)

Hipótese natural para o Sul: seus evangélicos seriam mais **históricos/de missão**
(luteranos IECLB) e menos pentecostais, logo menos bolsonaristas. Os dados de templos
geolocalizados (mapa de igrejas, ~574k templos classificados por vertente) **não sustentam**:

| | r(**fração pentecostal** dos templos, lean) | r(% evang, lean) |
|---|---:|---:|
| Brasil | **−0,02** | +0,24 |
| Nordeste | −0,11 | +0,17 |
| Sul | −0,09 | +0,03 |
| Sudeste | +0,00 | +0,13 |

- **O Sul não é distintamente "de missão":** 16,7% dos templos evangélicos são de missão vs
  71,3% pentecostais — praticamente igual ao resto do país (o Nordeste é o *mais* de missão,
  20,3%).
- **A fração pentecostal não prevê voto de direita em lugar nenhum** (r≈−0,02, até levemente
  negativo). O que correlaciona (fracamente) é a *quantidade* de evangélicos, não o *tipo*.

*Ressalva:* isso conta **templos, não fiéis**. Igreja luterana é grande e escassa; pentecostal
é pequena e numerosa — então a contagem de templos subestima o peso luterano no Sul. Não é
uma rejeição definitiva, mas a explicação mais econômica não é o tipo de evangélico, e sim
que **o Sul vota à direita em bloco, independentemente de religião** — provavelmente um
contraste de *tipo de católico* (nordestino popular vs sulista colonial-conservador).

## 4. Perfil por região

| região | n | pop % | evang. | catól. | sem rel. | inclin. | polariz. | % dir | % esq |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| Norte | 449 | 8% | 34,1% | 55,8% | 7,0% | 6,30 | 0,79 | 55% | 8% |
| Nordeste | 1.779 | 27% | 17,5% | 73,9% | 6,2% | **5,51** | 0,99 | 32% | **27%** |
| Centro-Oeste | 464 | 7% | 29,5% | 59,2% | 7,1% | **6,48** | 0,80 | 58% | 8% |
| Sudeste | 1.664 | 43% | 24,9% | 65,1% | 5,6% | 6,18 | 0,92 | 42% | 10% |
| Sul | 1.190 | 15% | 21,3% | 72,6% | **3,2%** | 6,17 | **1,01** | 44% | 14% |

O Nordeste é a única região à esquerda do centro (5,51) e a única onde o voto de esquerda
(27%) rivaliza com o de direita. Centro-Oeste é o mais à direita (6,48). O Sul combina
alta religiosidade católica, baixíssima secularização (3,2%) e a maior polarização média.

## 5. Nos redutos evangélicos, a esquerda quase não existe

Nos **345 municípios com >40% de evangélicos**: inclinação média 6,35, voto de direita
52,6%, **voto de esquerda só 10,1%**. Prefeitos eleitos:

> MDB 70 · PP 56 · União 52 · PL 48 · PSD 31 · Republicanos 27 — quase tudo centrão/direita.

Espelho: onde a **esquerda venceu a prefeitura** (752 municípios), a população é mais
**católica** (72,8% vs 67,6%) e menos **evangélica** (19,4% vs 23,4%) que a média.

## 6. O que *realmente* move a polarização: cidade, não igreja

A polarização ideológica não tem a ver com religião — é **estrutural e urbana**:

| correlação com **polarização** | r |
|---|---:|
| nº de candidatos | **+0,319** |
| margem 1º–2º | **−0,267** |
| população (log) | **+0,237** |
| % evangélica | −0,012 |
| % sem religião | +0,059 |

Mecânica clara pelo nº de candidatos: **1 candidato → 0,00 · 2 → 0,86 · 3 → 1,04 · 4 → 1,16
· 5 → 1,32 · 6+ → 1,46.** Mais candidatos (e mais eleitores) abrem espaço para nomes em
pontos distintos do espectro. Onde há dois nomes do mesmo campo, a disputa pode ser
acirrada (margem baixa) sem ser ideologicamente polarizada.

**Capitais polarizam quase o dobro do interior (1,79 vs 0,94)** — e pendem levemente mais à
esquerda (5,90 vs 6,00). A metrópole racha; o interior consolida.

![Heatmap do cruzamento entre % evangélica e polarização, sem padrão visível](/analises/img/religiao-x-polarizacao-heatmap-nulo.png)

O painel de controle, para o §1: exatamente o mesmo cruzamento e a mesma escala de cor,
trocando o eixo horizontal de *para onde o município pende* para *o quanto ele está
dividido*. A diagonal desaparece — sobram células isoladas, sem gradiente e sem canto
saturado. Vale como leitura negativa da figura do §2: aquela diagonal é sinal, não um
artefato do método de binagem ou da escala de cor, porque o mesmo método aplicado a uma
variável sem associação produz cinza.

| capital | inclin. | polariz. | evang. | venceu |
|---|--:|--:|--:|---|
| Recife/PE | 4,38 | 1,82 | 28% | PSB |
| Porto Alegre/RS | 4,46 | 1,63 | 13% | MDB |
| Florianópolis/SC | 4,76 | 2,04 | 14% | PSD |
| São Paulo/SP | 4,90 | **2,65** | 23% | MDB |
| Fortaleza/CE | 5,57 | **2,78** | 26% | PL |
| Rio de Janeiro/RJ | 6,54 | 1,65 | 25% | PSD |
| Belo Horizonte/MG | 6,61 | 1,79 | 27% | PL |
| Rio Branco/AC | 7,35 | 1,47 | 47% | PL |
| Maceió/AL | **7,91** | 1,48 | 30% | PL |

*(26 capitais casadas; recorte acima ilustra os extremos.)* Fortaleza e São Paulo são as
mais rachadas do país entre grandes cidades; Maceió e Rio Branco, as mais à direita.

## 7. O que pesa é o *nível*, não a *velocidade* de conversão

O crescimento evangélico 2010→2022 mal se correlaciona com inclinação (≈+0,05) e é até
levemente negativo com polarização (≈−0,06): municípios que **mais** se converteram na
década não são mais à direita nem mais divididos. O que alinha com a direita é já **ser**
evangélico, não estar virando.

## 8. Extremos nomeados

- **Mais à direita (lean 8,5):** dezenas de municípios com candidatura única do **PL** e
  100% dos votos (ex.: Bom Jesus de Goiás/GO, Chácara/MG, Bela Vista do Paraíso/PR).
- **Mais à esquerda (lean 2,5):** municípios com PT único (ex.: Rio Doce/MG, Bela Vista do
  Piauí/PI, vários no interior gaúcho católico).
- **Mais polarizados:** Pedro do Rosário/MA (3,20), Santo Antônio dos Lopes/MA (3,12),
  Gentil/RS (3,00) — disputas com muitos candidatos de campos opostos.

---

## 9. O terreno religioso de cada partido

Tudo acima trata a eleição como escalar contínuo (`lean`). Mas o dado tem uma dimensão
categórica que as figuras anteriores ignoram: **qual partido efetivamente ganhou a
prefeitura**. Trocando o eixo, a pergunta vira *em que terreno religioso cada sigla vence*.

![Faixa de % evangélica dos municípios onde cada partido elegeu prefeito em 2024, ordenada pela mediana](/analises/img/religiao-x-partido-amplitude.png)

O gradiente é limpo e cobre **dez pontos percentuais**: o PT elege prefeito onde os
evangélicos são **15,8%** da população; o UNIÃO, onde são **25,9%**. No meio, a ordem
acompanha de perto a escala esquerda-direita — a correlação entre a nota ideológica do
partido e a mediana evangélica do seu território é de **+0,70**.

| partido | prefeituras | mediana evangélica | p10–p90 | nota ideológica |
|---|---:|---:|---:|---:|
| PT | 252 | 15,8% | 8,6–28,0% | 2,5 |
| PSB | 312 | 17,0% | 9,4–34,7% | 3,7 |
| PDT | 151 | 21,0% | 11,9–36,2% | 3,3 |
| MDB | 860 | 21,1% | 9,4–38,6% | 5,7 |
| PSD | 884 | 21,2% | 10,7–33,4% | 5,9 |
| PP | 751 | 21,8% | 9,6–37,3% | 7,0 |
| PSDB | 275 | 22,5% | 11,2–35,8% | 6,0 |
| REPUBLICANOS | 437 | 23,6% | 10,8–36,4% | 7,2 |
| PODE | 126 | 24,4% | 12,6–38,4% | 5,7 |
| **PL** | 519 | **25,1%** | 11,6–38,9% | 8,5 |
| **UNIÃO** | 587 | **25,9%** | 12,4–39,4% | 6,9 |

*(as 11 siglas com mais de 100 prefeituras; a figura traz as 18 com 15 ou mais)*

Mas repare na coluna `p10–p90`: as faixas se sobrepõem quase inteiramente. **Nenhum partido
tem território religioso exclusivo** — todos vencem em municípios de quase todo tipo de
perfil. A diferença está em onde cada um se concentra.

![Mapa de calor: fatia das prefeituras de cada partido por faixa de % evangélica, cada linha somando 100%](/analises/img/religiao-x-partido-perfil.png)

Normalizando cada linha em 100%, aparece o que a mediana esconde: o que separa as pontas
não é só a posição da mancha, é a **cauda**. **9,2%** das prefeituras do PL e **8,9%** das
do UNIÃO estão em municípios com 40% ou mais de evangélicos, contra **2,0%** das do PT.

## 10. E, de novo, é quase tudo geografia

O §3 mostrou que metade da associação municipal entre religião e voto é efeito regional. Com
o partido no eixo, o diagnóstico é ainda mais duro. Basta trocar a % evangélica bruta pelo
**excedente regional** — quanto o município tem de evangélicos acima ou abaixo da mediana da
sua própria região — para o gradiente desabar.

![Excedente regional de evangélicos por partido: % do município menos a mediana da sua região](/analises/img/religiao-x-partido-excedente.png)

O PT ganha onde há poucos evangélicos porque **ganha no Nordeste** (67% das suas
prefeituras), a região menos evangélica do país — mediana de 15,9%. O UNIÃO ganha onde há
muitos porque ganha no Norte e no Centro-Oeste (34,2% e 29,7%). Medidos contra os vizinhos,
os dez pontos de gradiente viram **dois**, e a correlação com a escala ideológica cai de
**+0,70 para +0,15**.

Não é zero, porém, e não troca de sinal: **dentro de cada uma das cinco regiões** a
correlação segue positiva — Norte +0,35 · Nordeste +0,48 · Centro-Oeste +0,63 ·
Sudeste +0,22 · Sul +0,39. E sobra um resíduo nomeável: o **PL é o único partido claramente
acima da própria região** (+1,9 p.p.) e, entre os grandes, o **PT é o mais abaixo dela**
(−2,5 p.p.). Os dois partidos que a eleição nacional opõe são também os dois que sobram
depois do controle geográfico.

O §7 se confirma por este novo corte: a **velocidade** de conversão não separa os partidos.
A mediana do crescimento evangélico 2010→2022 fica entre 4,7 e 6,4 p.p. em *todos* os 18 —
o PT (5,4) e o PL (4,9) inclusive. O que distingue é o nível, e mesmo esse é quase todo
geografia.

## 11. Não é quem vence, é quem estava no páreo

Até aqui o vencedor foi tratado sozinho. Mas cada município produz um *par* — quem ficou em
1º e quem ficou em 2º. Tomando o par como unidade (não ordenado: interessa quem estava em
campo, não quem levou), o sinal fica **mais forte** do que com o vencedor isolado.

![Matriz partido × partido: mediana de % evangélica dos municípios onde cada par disputou o 1º e o 2º lugar](/analises/img/religiao-x-partido-confrontos.png)

A correlação entre a **nota ideológica média do par** e o terreno do confronto é de
**+0,73**, contra +0,70 do vencedor sozinho. E a matriz tem estrutura de canto: **PSB × PT**
é disputa de município católico (14,0% de evangélicos), **PL × UNIÃO** é disputa de
município evangélico (30,7%) — 17 pontos entre os dois cantos, contra os 10 pontos que
separavam os partidos individualmente.

O ponto forte é o seguinte: **fixado o vencedor, o adversário ainda move o terreno em 8 a 12
pontos**. Lendo a linha do MDB, o adversário ordena o terreno quase perfeitamente pela
própria nota ideológica:

| MDB vence contra | prefeituras | % evangélica típica |
|---|---:|---:|
| PSB | 42 | 16,6% |
| PT | 81 | 17,0% |
| PDT | 36 | 17,6% |
| PSDB | 56 | 18,6% |
| PSD | 107 | 19,5% |
| PP | 120 | 19,8% |
| REPUBLICANOS | 59 | 20,6% |
| UNIÃO | 92 | 24,9% |
| PL | 107 | 25,1% |

O mesmo MDB, o mesmo cargo, o mesmo ano — e oito pontos e meio de diferença no perfil
religioso do município conforme quem ele derrotou. Vale para PSD (+8,9 p.p.), PP (+9,9),
UNIÃO (+9,4) e PL (+10,4). **Saber quem ganhou diz menos sobre o município do que saber
contra quem.** É um lembrete de que o partido do prefeito é um resumo pobre: o que localiza
o município no mapa religioso é a composição da disputa inteira.

## 12. A mesma lógica não sobe para governador — e é aí que ela fica nítida

Vale perguntar por que toda esta análise para no nível municipal. A resposta é que **para
governador ela é estruturalmente impossível**: a unidade eleitoral é o estado, então
geografia e unidade de análise coincidem. Não há "excedente regional" a calcular — cada
governador *é* a sua região — e 27 observações não sustentam nada parecido com o corte por
partido dos §9 a §11. O que os §9–§11 fazem só é possível porque a eleição de prefeito
oferece 5.546 unidades.

Mas a eleição de governador oferece em troca algo que a de prefeito não pode dar. A
`metodologia.md` lista como ressalva que "município ≠ candidato": na disputa municipal cada
município tem uma oferta de candidatos diferente, e a correlação entre religião e voto
mistura o **eleitorado** com a **oferta**. Na disputa estadual, todos os municípios de um
estado escolhem entre os **mesmos** nomes. Comparar municípios dentro de um estado isola o
eleitorado com os candidatos mantidos constantes.

O resultado corrige a leitura do §1. Nacionalmente, os dois pleitos se parecem — r de
+0,214 com a inclinação da eleição de prefeito, +0,234 com a de governador. Mas *dentro de
cada estado*, a mediana do r salta de **+0,086 na disputa de prefeito para +0,215 na de
governador**: mantendo os candidatos constantes, o sinal religioso mais que dobra. Boa parte
da fraqueza do número nacional era o ruído de 5.546 disputas locais distintas, não ausência
de relação. O que muda é a **intensidade**, não a abrangência: o número de estados com r
positivo é praticamente o mesmo (18 de 24, contra 19 na disputa de prefeito). Onde o efeito
existe ele fica mais forte; onde não existia, fica mais claramente negativo.

O que ele **não** corrige é o §3. Medida com candidatos constantes, a associação continua
sendo um fenômeno regional, e do mesmo jeito:

| região | mediana do r intraestadual (governador) | UFs |
|---|---:|---:|
| Nordeste | **+0,478** | 9 |
| Norte | +0,269 | 5 |
| Sudeste | +0,131 | 4 |
| Sul | +0,079 | 3 |
| Centro-Oeste | −0,036 | 3 |

Na Bahia (+0,536), no Ceará (+0,621), na Paraíba (+0,520) e em Pernambuco (+0,524) o perfil
religioso do município prevê bem a inclinação do voto para governador. Em São Paulo
(−0,104), no Rio Grande do Sul (−0,121) e em Goiás (−0,202) ele prevê o contrário, ou nada.
Ou seja: o desenho mais limpo torna o efeito **mais forte onde ele já existia** e não o faz
aparecer onde não existia. "Católico = esquerda" segue sendo um fenômeno nordestino — agora
com um teste que não pode ser atribuído a quem apareceu na cédula.

*Ressalvas próprias desta seção:* são pleitos de anos e naturezas diferentes — governador em
2022, ano presidencial e eleição nacionalizada; prefeito em 2024, disputa local. AP, RR e DF
ficam de fora por terem menos de 20 municípios. E a falácia ecológica continua valendo:
municípios mais evangélicos votarem mais à direita não é o mesmo que evangélicos votarem
mais à direita.

---

## Síntese

1. **Existe** clivagem religião↔política real e na direção esperada (evangélico↔direita,
   católico↔esquerda), de **magnitude modesta** — longe de determinística.
2. O efeito é **regional, não nacional**: existe no Nordeste (e em parte no Sudeste) e
   **some no Sul e Centro-Oeste**, onde católicos e evangélicos votam igualmente à direita.
   Não é o *tipo* de evangélico (a fração pentecostal não prevê o voto — §3b); é que o Sul é
   politicamente homogêneo à direita. "Católico = esquerda" é fenômeno nordestino.
3. **Religião não gera polarização.** Ela desloca o município no espectro; o racha
   ideológico é dirigido por **número de candidatos, população e competitividade** — é um
   fenômeno de **cidade grande**, não de igreja.
4. **Os partidos vencem em terrenos religiosos distintos** (PT 15,8% de evangélicos, UNIÃO
   25,9%), mas descontada a região o gradiente encolhe de dez pontos para dois (§10). O
   partido é sobretudo um marcador de **onde** se ganha. A exceção que resiste ao controle
   é o **PL**, o único claramente mais evangélico que a própria vizinhança.
5. **O confronto informa mais que o vencedor** (§11). Fixado quem ganhou, o terreno ainda
   muda 8 a 12 pontos conforme quem foi o segundo colocado — e o par tem correlação maior
   com a religião (+0,73) do que o vencedor sozinho (+0,70). O partido do prefeito é um
   resumo pobre da disputa.
6. **Com os candidatos constantes, o sinal dobra — mas só onde já havia** (§12). Na eleição
   de governador, onde todo o estado escolhe entre os mesmos nomes, o r intraestadual mediano
   sobe de +0,086 para +0,215. O número nacional fraco era em parte ruído das 5.546 disputas
   locais. Ainda assim, o efeito segue concentrado no Nordeste (+0,478) e ausente no
   Centro-Oeste (−0,036): o desenho mais limpo reforça o §3 em vez de derrubá-lo.

## Ressalvas

- **Falácia ecológica:** correlação entre agregados municipais ≠ comportamento individual.
  Não se conclui daqui "o evangélico vota à direita" — só que *municípios* mais evangélicos
  *tendem* a votar mais à direita.
- **Notas de especialistas**, não verdade objetiva; herdadas do partido, não do candidato.
  Prefeitura é eleição personalista → sinal ruidoso por construção. O override do PL (§nota)
  é uma escolha editorial explícita e auditável.
- **Janelas temporais** próximas mas distintas: Censo 2022, eleição 2024.
- Correlações são de força **fraca a moderada** (|r| ≤ 0,3); descrevem tendência, não
  poder preditivo forte.
- **O +0,70 do §9 não é comparável ao +0,214 do §1.** Aquele é a correlação entre **18
  medianas partidárias**; este, entre 5.546 municípios. Agregar remove ruído e **infla `r`
  por construção** — tomar o número maior como "efeito mais forte" seria falácia ecológica
  de segunda ordem. O §10 existe justamente para impedir essa leitura: é o mesmo efeito
  fraco, só que suavizado pela média, e a maior parte dele é geografia.
- **Partidos pequenos são anedota.** Siglas com poucas prefeituras (NOVO 18, PC do B 19,
  MOBILIZA 21) têm percentis instáveis, e no mapa de calor suas linhas parecem mais
  concentradas só porque cada município vale uma fatia maior. O corte mínimo é de 15
  prefeituras; leia as siglas grandes.

---

*Fontes: TSE `br_tse_eleicoes.resultados_candidato_municipio` (2024, prefeito, 1º turno);
IBGE Censo 2022 (perfil religioso); centroides `br_bd_diretorios_brasil.municipio`.
[Query](https://github.com/rafapolo/xyz/blob/main/dataviz/eleicoes/dados/query.sql) e
[notas partidárias](https://github.com/rafapolo/xyz/blob/main/dataviz/eleicoes/metodologia.md)
reprodutíveis. A junção, as correlações deste relatório e os dois heatmaps saem de
[`heatmap_religiao_x_lean.py`](https://github.com/rafapolo/xyz/blob/main/dataviz/eleicoes/heatmap_religiao_x_lean.py),
que imprime os `r` de §1, §3 e §6 para conferência. As três figuras de §9 e §10 saem de
[`perfil_religioso_partidos.py`](https://github.com/rafapolo/xyz/blob/main/dataviz/eleicoes/perfil_religioso_partidos.py),
que reaproveita aquela junção e imprime a tabela por partido, os dois `r`, as correlações
intrarregionais e a matriz de confrontos de §11. Os números de §12 saem do mesmo script,
sobre `dados/governador_2022_raw.json`, gerado por
[`query_governador.sql`](https://github.com/rafapolo/xyz/blob/main/dataviz/eleicoes/dados/query_governador.sql).*
