# Capas das análises

Toda análise do `pages/analises/results/manifest.json` tem uma capa abstrata,
`pages/analises/img/capa-<slug>.webp`, gerada por `scripts/gera_capas.ts`. Ela
aparece com 120px de altura em três lugares:

- no topo do cartão `.noticia` da home (`gera_home.py`, PT e EN);
- no cartão da lista `/analises/` (`viewer.js`, `renderIndex`);
- acima do `.meta` ("rodado em …") na página da análise (`gera_analises.py`).

Sem o arquivo, os três lugares simplesmente saem sem capa.

## Análise nova: o que fazer

1. Ler o título e o dek da análise e decidir **um motivo** (o desenho do
   centro) e **uma paleta** — critérios abaixo.
2. Acrescentar a linha em `TEMAS`, em `scripts/gera_capas.ts`:
   `"<slug>": ["<paleta>", "<motivo>"]`.
   Se nenhum motivo existente serve, escrever um novo em `MOTIVOS` (regras em
   "Motivo novo").
3. Rodar `python3 scripts/gera_analises.py` — ele chama o `gera_capas.ts`
   antes das páginas e da home. Para só refazer uma capa:
   `bun scripts/gera_capas.ts <slug>`.
4. Conferir a capa no cartão (só o miolo aparece) e na página da análise
   (a faixa inteira).

Sem entrada em `TEMAS`, a capa ainda sai: paleta e motivo sorteados pelo slug,
e o script imprime `! <slug>: sem tema em TEMAS`. É um quebra-galho; a capa
certa é a que puxa o assunto.

## A estética

Referência: as ilustrações de podcast do Exposing the Invisible
(exposingtheinvisible.org/en/listen/) — mandalas radiais pintadas à mão,
cores saturadas, anéis finos soltos e uma linha pontilhada horizontal tipo
onda sonora cortando tudo.

Cada capa empilha, de baixo para cima:

1. **fundo** — gradiente diagonal entre as duas primeiras cores da paleta, com
   7 manchas desfocadas (aquarela);
2. **três mandalas** — uma grande no centro (raio 330, maior que a tela, então
   aparece cortada em cima e embaixo) e duas laterais menores, com posição,
   tamanho e número de raios sorteados; cada uma tem anel cheio, cacos
   triangulares alternando duas cores, disco interno escuro e um colar de
   pontinhos;
3. **anéis finos** — 14 círculos só de contorno, espalhados;
4. **faixa pontilhada** — a espinha comum a todas: pontos creme (às vezes da
   cor de destaque) com brilho, na altura do meio, de ponta a ponta;
5. **motivo central** — o único elemento que muda de assunto para assunto;
6. **grão de papel** — ruído fino por cima de tudo.

As camadas 2, 3 e 5 passam por um filtro de turbulência + deslocamento
(`#pincel`): é isso que tira o ar de vetor e deixa a borda tremida de tinta.

Tudo é determinístico pelo slug (semente FNV): rodar de novo dá a mesma capa.

### Formato e enquadramento

A tela é **1680×240** (7:1), o dobro da altura exibida. A mesma imagem é
cortada em duas proporções, com `object-fit: cover`:

- **cartão**, ~2,8:1 — sobra só o terço central (~680px da tela);
- **página da análise**, ~6:1 ou mais — aparece quase tudo.

Por isso o motivo precisa caber em **~±200px do centro** (x 640–1040), e as
laterais só completam. A faixa pontilhada é o que garante continuidade nos dois
cortes.

Sai em WebP (q 78, ~50 KB) e não em SVG porque o filtro de turbulência é caro de
repintar — a home tem 8 cartões num carrossel arrastável.

### Paletas

Cada uma é `[fundo, fundo2, anel, raio A, raio B, miolo/traço claro, traço escuro]`.

| paleta | clima | usada em |
|---|---|---|
| `turquesa` | céu, dinheiro público, neutro-vivo | gastos da União, doador único |
| `solar` | eleição, calor, tensão política | vira-casacas, salário, religião × polarização |
| `violeta` | rede, mídia, poder | corresponsáveis, três cidades |
| `floresta` | país, território, retrato geral | o Brasil que os dados revelam (PT e EN) |
| `rubro` | alerta, conflito de interesse | emenda que pagou a própria empresa, escritório |
| `aurora` | saúde, cruzamento de cadastros | câncer, cinco cadastros |
| `oceano` | água, saúde em massa, censo | outorgas, dados de saúde, judeus no censo |
| `terra` | indústria, dívida, moradia | poluentes, devedora/fornecedora, ibge13 |

Critério: primeiro o assunto (água → `oceano`, eleição → `solar`), depois
variar em relação às capas vizinhas na home — duas análises seguidas com a
mesma paleta ficam com cara de repetição no carrossel.

As cores precisam funcionar sobre o fundo claro (`#f6f2ea`) e o escuro
(`#1b1811`) do site, já que a imagem não lê as variáveis de tema. As paletas
saturadas de hoje passam nos dois.

### Motivos

O motivo é **uma ideia visual da tese da análise**, não ilustração literal:
a forma do achado (um → muitos, laço, divisão, crescimento), não o objeto.

| motivo | desenho | ideia |
|---|---|---|
| `sankey` | fitas que se abrem da esquerda para a direita | fluxo de dinheiro, origem → destino |
| `rede` | nós ligados em torno de um central | grupo societário, rede de pessoas |
| `virada` | disco vermelho/azul com seta girando | mudança de lado |
| `laco` | seta que volta para si, moeda no meio | dinheiro que volta para quem mandou |
| `divida` | moedas empilhadas → contrato | devedor que vira fornecedor |
| `venn` | cinco círculos sobrepostos | os mesmos em vários cadastros |
| `grade` | grade 9×7 de pontos | muitos retratos de um país |
| `fumaca` | três chaminés com plumas | poluição, indústria |
| `ondas` | três emissores de ondas | comunicação, mídia, cidades |
| `agua` | gota sobre ondas | água, outorgas, rios |
| `barras` | barras crescendo acima de uma linha tracejada | patrimônio que passa de um teto |
| `leque` | um nó ligado a dezenas | um doador, muitas campanhas |
| `escritorio` | bloco de 12 sócios, cada um abrindo seu leque | grupo agindo junto |
| `saude` | células + linha de pulso | doença, hospital |
| `matriz` | matriz de quadradinhos + pulso | dado de saúde em massa |
| `hexagonos` | treliça hexagonal | censo, composição de população |
| `dividido` | campo partido, pontos vermelhos e azuis | polarização |
| `casas` | casinhas em fila | moradia, série histórica |

Vermelho `#d8322a` e azul `#2f5fc0` fixos (fora da paleta) marcam
esquerda/direita em `virada` e `dividido`.

### Motivo novo

Uma função `(rng, p) => string` em `MOTIVOS` que devolve SVG centrado em
`CX, CY` (840, 120):

- caber em ±200px na horizontal e ±100px na vertical;
- traço grosso (4–7px) em `p[5]` (claro), com `p[6]` (escuro) para contorno —
  a 120px de altura, traço fino some;
- poucos elementos grandes; o filtro de pincel borra detalhe pequeno;
- usar `rng()` para variação, nunca `Math.random()` — a capa tem de ser
  reprodutível;
- sem texto (exceção: o `$` da moeda em `laco`).

Depois de criar, registrar a linha na tabela de motivos acima.
