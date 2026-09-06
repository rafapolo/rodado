# UX de `pages/analises/` — índice escaneável e artigo navegável

> Aberto 2026-09-06, a pedido. Levantamento feito lendo `index.html`,
> `viewer.js`, `analises.css`, `scripts/gera_analises.py`, o `manifest.json` e
> os 11 markdowns de `results/`. Os números abaixo foram medidos no checkout;
> o resto é plano. **Nada deste arquivo foi implementado.**

## O que foi medido

**Índice (`/analises/`)** — 13 itens no `manifest.json`. Os deks têm de 269 a
779 caracteres (40 a 120 palavras), mediana 429:

```
269 300 315 372 403 411 429 519 572 597 646 742 779
```

São ~6.500 caracteres de parágrafo corrido empilhados numa coluna de 700px.
Não dá para varrer, só para ler de cima a baixo. As tags de fonte existem em
todo cartão e não fazem nada — 15 órgãos distintos, com Receita Federal em 10
dos 13 itens, IBGE em 6, ANA e TSE em 5.

A lista inteira é montada por JS a partir do `manifest.json`
(`renderIndex()` em `viewer.js:208`). Sem JS — ou para um crawler —
`/analises/` é literalmente `<p class="doc-msg">Carregando…</p>`. Esse é
exatamente o problema que `gera_analises.py` foi escrito para resolver nas
páginas individuais e que ficou sem resolver no índice.

**Página da análise** — os textos vão de 1.522 a 4.328 palavras, com 3 a 14
seções de `h2`:

| Arquivo | Palavras | `h2` | Figuras |
|---|---|---|---|
| `tres-cidades-tres-comunicacoes.md` | 4.328 | 7 | 4 |
| `censo-judeus-brasil.md` | 4.172 | 6 | 1 |
| `religiao-x-polarizacao.md` | 3.984 | 14 | 7 |
| `o-salario-nao-explica.md` | 3.857 | 11 | 3 |
| `o-brasil-que-os-dados-revelam.md` | 3.703 | 9 | 0 |
| `cancer-mata-interna.md` | 3.517 | 10 | 6 |
| `bens-dos-candidatos.md` | 2.726 | 3 | 2 |
| `o-unico-doador-do-negao.md` | 2.301 | 5 | 0 |
| `nao-era-um-doador-era-um-escritorio.md` | 1.963 | 5 | 0 |
| `duas-outorgas-mais-agua-que-a-copasa.md` | 1.622 | 8 | 0 |
| `mapa-da-saude-mental.md` | 1.522 | 6 | 0 |

Não há sumário, não há noção de onde se está no texto, e não há saída no fim
além do rodapé global do site. Ao mesmo tempo `main` tem `max-width: 1180px` e
o texto trava em `--measure: 700px` (`site.css:120`, `analises.css:5`) —
sobram ~450px de gutter vazio à direita em qualquer tela de desktop.

**Órfã** — `mapa-da-saude-mental` tem `.md` (desde 02-09), pasta, shell
gerado e `img/og-mapa-da-saude-mental.png`, mas **não está no
`manifest.json`**. Não aparece no índice e o próprio `gera_analises.py` já
cospe o aviso (`gera_analises.py:118-125`). É a única decisão de conteúdo
deste plano: entra no manifest ou sai do ar.

## O plano

Seis itens. Nenhum introduz dependência nova, nenhum reescreve conteúdo.

### 1. Cartão do índice escaneável — sem reescrever dek nenhum

`line-clamp: 3` no `.idx-list .dek`. A primeira frase de quase todo dek já é o
gancho ("93% da reeleição de Hélio Negão saiu do caixa do PL"), então cortar
em três linhas não perde o essencial e o texto completo continua no DOM para
SEO. Data em mono alinhada à direita do título, na mesma linha, em vez de
correr atrás dele.

Custo: ~10 linhas em `analises.css`. Zero mudança de conteúdo.

### 2. Tag vira filtro

As tags já estão desenhadas em todo cartão e hoje são decoração. Clicar numa
delas estreita a lista; o estado vai para `?fonte=`, e a eyebrow vira
`Análises / Receita Federal ✕`. Nenhum chrome novo — o controle é o que já
está na tela.

O filtro útil é **por órgão** (o que vem antes do ` · `), não pela tag
inteira: "Receita Federal · CNPJ" e "Receita Federal · CNPJ" já são a mesma
coisa em 10 dos 13 itens, mas "MTE · RAIS 2025" e "MTE · RAIS 2025 e RAIS
identificada" são strings diferentes para a mesma fonte.

Custo: ~30 linhas em `viewer.js`.

### 3. Índice também renderizado estático

`gera_analises.py` passa a escrever a `<ul class="idx-list">` dentro de
`pages/analises/index.html`, e `renderIndex()` só monta se o container estiver
vazio. Mesma justificativa que fez os shells existirem: crawler não roda JS.
De quebra, o índice deixa de piscar "Carregando…".

Custo: ~20 linhas em `gera_analises.py`, mais o guard no viewer.

### 4. Sumário no gutter direito — o item de maior retorno

Envolver `#doc` num `<div class="artigo">` com
`grid-template-columns: minmax(0, var(--measure)) 1fr`, e um `<aside>` sticky
na coluna 2 listando os `h2`. **A infraestrutura já existe**: `ancoraTitulos()`
(`viewer.js:125`) já enumera `h2, h3, h4` e já dá a cada um um `id`
slugificado — o sumário lê o que ela produziu. Seção corrente destacada por
`IntersectionObserver`.

Abaixo de ~1000px o aside vira um `<details>` fechado acima do texto.

Usa espaço que já está vazio, para documentos de até 14 seções que hoje só se
navegam rolando.

Custo: ~25 linhas de CSS, ~30 de JS, um `<div>` no `MODELO` do gerador.

### 5. Tempo de leitura e prev/next

Tempo de leitura calculado depois do render, contando palavras de `#doc` — o
`.md` já está carregado, então o custo é zero — na mesma linha do `rodado em`:
`rodado em 09-08-2026 · 8 min de leitura`.

No fim do artigo, `.pager` — a classe **já existe** em `site.css:325` e já é
usada nas páginas de tema — com a análise anterior e a próxima na ordem do
manifest (que já é cronológica reversa), mais "ver todas". Reuso puro, nenhum
CSS novo.

Custo: ~25 linhas em `viewer.js`.

### 6. Resolver a órfã

`mapa-da-saude-mental`: entra no `manifest.json` (com `rodado_em`, `dek` e
`tags`) ou a pasta e a og-image saem. Decisão de conteúdo, não de código.

## O que este plano deliberadamente não faz

| O quê | Por quê |
|---|---|
| **Miniaturas no índice** | As `og-*.png` são cartões de texto sobre o mesmo fundo bege, geradas por `gera_og_image.py`. Como miniatura viram 13 retângulos visualmente idênticos. O índice fica melhor tipográfico |
| **Barra de progresso de leitura** | Redundante com o sumário do item 4, que já diz em que seção o leitor está |
| **Agrupar o índice por mês** | As 13 análises cabem em julho–setembro de 2026. Agrupar hoje só adiciona cabeçalhos a uma lista de 13 |
| **Tempo de leitura no índice** | Exigiria 13 `fetch` no load ou gravar contagem de palavras de volta no `manifest.json`. É a única peça que mexeria em dado — fica de fora por padrão. Se for desejado, o write-back idempotente no `gera_analises.py` é uma linha |
| **Figura sangrando para 1180px** | Tentador com 450px de gutter livre, mas briga com o sumário do item 4 pelo mesmo espaço. Decidir depois que o 4 estiver de pé |
| **Encurtar as tabelas longas** | `censo-judeus-brasil.md` tem 118 linhas de tabela e `tres-cidades` tem 106, dentro de 700px com `overflow-x`. É trabalho de conteúdo, não de UX de navegação |

## Ordem de execução

1, 3 e 5 são baratos e independentes entre si. 4 é o de maior retorno e o
único que mexe em layout. 2 é o único com estado de URL.

Sugestão: **1 → 5 → 4 → 3 → 2**, rodando `python3 scripts/gera_analises.py`
depois de 3, 4 e 5 — os três tocam o `MODELO` e exigem os 12 shells
regenerados.

## Nota de estado (2026-09-06)

Na abertura deste plano havia trabalho não commitado na árvore: o campo
`rodado_em` adicionado ao `manifest.json`, ao `viewer.js`, ao `analises.css` e
ao `gera_analises.py`, mais os 12 shells regenerados. Vale commitar isso antes
de começar, para o diff de UX não vir misturado com o de metadado.
