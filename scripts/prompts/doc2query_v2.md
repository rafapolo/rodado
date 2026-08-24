# Gerar perguntas que cada tabela responde — v2, registro analítico

Você recebe um lote de tabelas do acervo **rodado** — dados públicos brasileiros
espelhados em DuckDB. Para cada tabela, escreva as perguntas em português do
Brasil que **aquela tabela responde**.

## Por que uma segunda rodada existe

A primeira rodada gerou perguntas descritivas — "quantos X em Y", "qual o maior
Z". Medido na bancada de perguntas multi-tabela (`tasks/multi_tabela.plan`),
elas não bastam: quem pesquisa pergunta no registro ANALÍTICO — "existe relação
entre A e B", "como a composição de X varia com Y", "onde concentram os casos
de Z" — e a tabela certa fica invisível porque nenhuma pergunta do índice usa
esse vocabulário. Exemplo real: `populacao_grupo_idade_sexo_raca` ficou no
posto 71 para "sub-representação de mulheres e pessoas negras entre candidatos".

Então esta versão gera as DUAS camadas:

- **Descritivas**: o que a tabela tem (como a v1 já fazia bem).
- **Analíticas**: o ASPECTO que a tabela leva numa pesquisa maior — a composição
  que serve de denominador, o indicador que se correlaciona com outro, a
  desigualdade que se mede dentro dela. Sempre restritas ao que a tabela
  responde SOZINHA; a outra ponta da pesquisa não entra na frase.

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
{"id":"br_ms_sim.microdados","perguntas":["quantas pessoas morreram em Pernambuco no ano passado","quais as principais causas de morte no Brasil","como a mortalidade varia por raça","qual estado tem mais mortes violentas","quantos óbitos de crianças foram registrados","a mortalidade caiu ou subiu nos últimos anos","quantas mulheres morreram de câncer","em que idade as pessoas mais morrem","existe diferença na mortalidade entre homens e mulheres","onde se concentra a morte violenta no país","qual a desigualdade racial na mortalidade","como se distribuem as mortes por faixa etária"]}
```

**12 perguntas por tabela.**

## Regras

1. **Escreva como uma pessoa pergunta, não como a coluna se chama.** Este é o
   ponto inteiro do exercício. Se a coluna é `vl_remun_media_nom`, a pergunta diz
   "salário médio". Se é `qt_vinculos_ativos`, diz "empregos formais".
   Repetir o nome da coluna não acrescenta nada ao índice — ele já tem os nomes.

2. **Só o que a tabela responde sozinha** (ou juntando com o diretório de
    municípios/UF para virar nome). Se a tabela não tem valor monetário, não
   pergunte preço. Se não tem `ano`, não pergunte evolução. Inventar capacidade
   envenena a busca.

3. **Das 12, ao menos 4 analíticas**, nestes moldes:
   - comparação entre grupos: "há diferença de X entre A e B"
   - desigualdade/concentração: "onde se concentra X", "qual a desigualdade de X"
   - relação/composição: "como se compõe X por Y", "X acompanha Y?"
   - recorte como aspecto de pesquisa: não "população por cor_raca", mas
     "quantos negros e brancos há em cada município", "qual o perfil de sexo e
     raça da população local"

4. **Varie o vocabulário com o sinônimo COTIDIANO, não só o jargão.** `sexo`
   também é "mulheres e homens"; `cor_raca` também é "negros, pardos, brancos";
   `vinculo` também é "emprego formal". É esse segundo vocabulário que a v1 não
   cobriu e a busca precisa ter.

5. **Varie o formato.** Entre as 12, cubra pelo menos seis destes:
   contagem · ranking ou extremo · evolução no tempo · recorte geográfico ·
   cruzamento por atributo · busca pontual · proporção ou média · comparação
   entre dois grupos · concentração/desigualdade.

6. **Curtas e diretas** — 5 a 16 palavras. Sem "por favor", sem ponto de
   interrogação.

7. **Minúsculas**, exceto nomes próprios (Pernambuco, SUS, Bolsa Família).

8. **Sem ano fixo** salvo quando a tabela cobrir um só ano.

9. **Tabela `dicionario`**: são tabelas de decodificação de código. Pergunte
   sobre o significado dos códigos, não sobre o fenômeno.

10. Se a tabela for **opaca** — nome críptico, colunas sem sentido claro —
    escreva menos perguntas, porém honestas, e acrescente `"incerta": true`.

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
