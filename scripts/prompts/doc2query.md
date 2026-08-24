# Gerar perguntas que cada tabela responde (doc2query)

Você recebe um lote de tabelas do acervo **rodado** — dados públicos brasileiros
espelhados em DuckDB. Para cada tabela, escreva as perguntas em português do
Brasil que **aquela tabela responde**.

## Por que isso existe

A busca semântica do acervo indexa hoje o que a tabela *é* — uma lista de nomes
de coluna com tipo. Medido, isso fica quase ortogonal a uma pergunta em prosa
(similaridade 0,08). Uma frase em português sobre o mesmo assunto marca 0,39.

Então o índice passa a guardar **as perguntas que a tabela responde**, não a
descrição dela. Assim consulta e índice vivem no mesmo espaço.

Isso quer dizer que **as perguntas são o produto**, não um enfeite. Uma pergunta
que ninguém faria é uma entrada morta no índice; uma que a tabela não responde é
pior, porque desvia a busca para o lugar errado.

## Entrada

Um JSON por linha:

```json
{"id":"br_ms_sim.microdados","dataset":"br_ms_sim","tabela":"microdados","linhas":12345678,"colunas":["ano","sigla_uf","causa_basica","idade","sexo","raca_cor"]}
```

## Saída

Um JSON por linha, **na mesma ordem**, sem markdown, sem cercas, sem comentário:

```json
{"id":"br_ms_sim.microdados","perguntas":["quantas pessoas morreram em Pernambuco no ano passado","quais as principais causas de morte no Brasil","como a mortalidade varia por raça","qual estado tem mais mortes violentas","quantos óbitos de crianças foram registrados","a mortalidade caiu ou subiu nos últimos anos","quantas mulheres morreram de câncer","em que idade as pessoas mais morrem"]}
```

**8 perguntas por tabela.**

## Regras

1. **Escreva como uma pessoa pergunta, não como a coluna se chama.** Este é o
   ponto inteiro do exercício. Se a coluna é `vl_remun_media_nom`, a pergunta diz
   "salário médio". Se é `qt_vinculos_ativos`, diz "quantos empregos formais".
   Repetir o nome da coluna não acrescenta nada ao índice — ele já tem os nomes.

2. **Só o que a tabela responde sozinha** (ou juntando com o diretório de
   municípios/UF para virar nome). Se a tabela não tem valor monetário, não
   pergunte preço. Se não tem `ano`, não pergunte evolução. Inventar capacidade
   envenena a busca.

3. **Varie o formato.** Entre as 8, cubra pelo menos cinco destes:
   contagem · ranking ou extremo ("qual o maior") · evolução no tempo ·
   recorte geográfico (município, estado, região) · cruzamento por atributo
   (sexo, raça, idade, porte, setor) · busca pontual ("existe X") ·
   proporção ou média · comparação entre dois grupos.

4. **Varie o vocabulário.** Se uma pergunta diz "óbitos", outra diz "mortes",
   outra "faleceram". Sinônimo é o que faz a busca funcionar para quem não
   conhece o jargão do órgão.

5. **Curtas e diretas** — 5 a 15 palavras. Sem "por favor", sem "gostaria de
   saber", sem ponto de interrogação (o índice não precisa).

6. **Minúsculas**, exceto nomes próprios (Pernambuco, SUS, Bolsa Família).

7. **Sem ano fixo** salvo quando a tabela cobrir um só ano. Prefira "no ano
   passado", "nos últimos anos", "por ano".

8. **Tabela `dicionario`**: são tabelas de decodificação de código. Pergunte
   sobre o significado dos códigos ("o que significa o código de raça no
   SINASC"), não sobre o fenômeno.

9. Se a tabela for **opaca** — nome críptico, colunas sem sentido claro — escreva
   menos perguntas, porém honestas, e acrescente `"incerta": true` na saída. Uma
   entrada marcada é recuperável; oito chutes plausíveis não são.

## Contexto do acervo

Datasets seguem `br_<órgão>_<assunto>` — `br_ms_` é Ministério da Saúde,
`br_inep_` é INEP (educação), `br_me_` é Ministério da Economia, `br_tse_` é
Justiça Eleitoral, `br_ibge_` é IBGE, `br_cgu_` é Controladoria-Geral da União,
`br_bd_diretorios_` são tabelas de referência (municípios, UF, CNAE, CBO, CID).
`world_` e `us_` são fontes internacionais — pergunte em português do mesmo
jeito.

`microdados` costuma ser registro individual (uma linha por óbito, nascimento,
vínculo, candidato). Tabelas com nome de recorte (`municipio`, `uf`, `brasil`)
costumam ser agregados naquele nível.
