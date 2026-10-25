# rodado — guia para agentes (db.rodado.xyz)

> Espelho de dados públicos brasileiros consultável por SQL (DuckDB, só leitura):
> {resumo}.
> Este guia é público; os dados exigem credencial. Atualizado a partir do catálogo em {gerado}.

Você é um agente (LLM, script, notebook) e quer responder perguntas com estes dados por conta
própria. Tudo passa por HTTP: descobrir tabelas, ler o schema, consultar, exportar. Nada a instalar.

**O caminho, do mais largo ao mais estreito — cada passo custa poucos KB:**

0. caso parecido já resolvido → `/exemplos?busca=<palavras da pergunta>` (fontes, recorte, ordem de grandeza)
1. tema (lista no fim desta página) → `/tabelas?tema=<tema>` ou `/tabelas?busca=<palavras>`
2. dataset → `/tabelas?dataset=<dataset>` (as tabelas e quantas linhas cada uma tem)
3. tabela → `/colunas?t=<dataset>.<tabela>` (colunas, tipos, partição)
4. **contexto → `/contexto?dataset=<dataset>&tabela=<tabela>`** (armadilhas medidas, códigos, joins)
5. **ensaio → `POST /confere`** com a SQL: diz, sem executar, se a tabela existe, se a partição
   está filtrada e que armadilha medida a consulta toca
6. consulta → `POST /query`, agregando no servidor; leia os `avisos` que vêm junto das `linhas`. Se a SQL
   cita coluna de uma armadilha `[erro]`, o `/query` recusa com 400 e a armadilha no corpo — leia,
   corrija ou, se a consulta já trata disso, repita com `?ciente=1`
7. conferência → a lista da seção 2b, antes de responder
8. **link → `POST /q` com cada SQL que sustenta a resposta** e cite `https://db.rodado.xyz/q/<id>`
   junto do número (seção 4b) — vale para qualquer pergunta, mesmo que ninguém tenha pedido link

**Prefere MCP?** O mesmo espelho, com as mesmas armadilhas e recusas, como ferramentas MCP
(`describe_table`, `resolve_join`, `get_metric`, `run_sql`…), aberto e sem nada local além do
repositório público: `git clone https://github.com/rafapolo/rodado` e
`claude mcp add rodado -- python3 mcp/mcp_server.py` (`pip install -r mcp/requirements.txt`
antes). Detalhes em `mcp/MCP.md`.

**Orçamento de contexto.** Nunca baixe `/tabelas` sem filtro (~60 KB) nem `/catalogo.json`
(~460 KB, é da página): filtre por `tema`, `busca` ou `dataset`. Não leia os YAML de
`docs/context/` no GitHub (centenas de KB): `/contexto` entrega a fatia do dataset que interessa.
`/exemplos` e `/contexto` custam 2–8 KB cada; `/confere` ainda menos.

## 1. Credencial

**Até 26/10/2026 o acesso está aberto**: nenhuma rota pede credencial e os exemplos abaixo
funcionam sem o `$AUTH`. Depois disso, toda rota além desta página pede **uma** destas, que
quem te pediu a tarefa precisa te dar:

- usuário e senha (HTTP Basic): `curl -u rodado:$RODADO_SENHA ...`
- token: `?token=$RODADO_TOKEN` em qualquer URL

Guarde em variável de ambiente; nunca escreva a senha ou o token em arquivo, log, commit ou
resposta. Sem credencial a resposta é `401`. Nos exemplos abaixo, `$AUTH` é `-u rodado:$RODADO_SENHA`.

## 2. O fluxo que funciona

1. **Descobrir** — texto, um dataset por linha, com a descrição e as tabelas com o número de
   linhas: `curl $AUTH 'https://db.rodado.xyz/tabelas?tema=saude'`,
   `?busca=vacina` (palavras no nome ou na descrição, sem acento) ou `?dataset=br_me_cnpj`.
   A procedência de cada tabela está em `FROM _rodado_metadata`.
2. **Ler o schema** de uma tabela — colunas, tipos e quais são partição:
   `curl $AUTH 'https://db.rodado.xyz/colunas?t=br_me_cnpj.empresas'`
   → `[{"coluna": "...", "tipo": "VARCHAR", "particao": false}, ...]`.
   Para várias tabelas de uma vez: `SELECT schema_name, table_name, column_name, data_type FROM duckdb_columns() WHERE schema_name = 'br_me_rais'`.
3. **Ler o contexto** do dataset — o que já se mediu sobre ele e não está no schema:
   `curl $AUTH 'https://db.rodado.xyz/contexto?dataset=br_ms_sim'` (e `&tabela=microdados`
   para estreitar). Markdown com:
   - **armadilhas medidas**: a coluna plausível que é a errada, a partição que é retrato e não
     fluxo, a unidade trocada, a sentinela — cada uma com o número que a confirmou;
   - **significado dos códigos** (valor → rótulo) de colunas que nenhum dicionário decodifica;
   - **pontes**: a expressão de join pronta para ligar a coluna à tabela de referência
     (município, UF, CNPJ, país…), que substitui a igualdade ingênua;
   - as **métricas nomeadas** que saem do dataset (população, PIB per capita, saldo do CAGED…).

   `curl $AUTH https://db.rodado.xyz/contexto` (sem `dataset`) traz as regras que valem para o
   espelho todo: falsos amigos, colunas cujo código muda entre fontes, as métricas e as
   hierarquias (município → UF → região, CNAE, CID-10). Um dataset sem contexto não está
   livre de armadilha: só ninguém mediu ainda.
4. **Olhar uma amostra** antes de agregar: `FROM dataset.tabela LIMIT 5`. Códigos (sexo,
   raça/cor, tipo de movimentação) costumam vir como número ou sigla; descubra os valores com
   `SELECT col, count(*) FROM ... GROUP BY 1 ORDER BY 2 DESC LIMIT 20`. Muitos datasets têm
   uma tabela `dicionario` com o significado de cada código.
5. **Agregar no servidor** e trazer só o resultado. A consulta roda lá; trazer milhões de
   linhas para agregar na sua máquina é lento e bate no limite.
6. **Ensaiar e consultar.** `curl $AUTH --data-binary @q.sql https://db.rodado.xyz/confere`
   devolve `{"tabelas": [{"tabela", "linhas", "particoes", "filtra_particao"}], "problemas": [...],
   "avisos": [...], "colunas_nao_achadas": [...]}` em milissegundos: resolva os `problemas`
   antes de mandar ao `/query`. A resposta do `/query` traz no corpo `{"linhas": [...], "avisos":
   [...], "contexto": [...], "truncado": ...}`: os `avisos` são as armadilhas medidas das tabelas
   e colunas que a SQL cita — leia antes de usar o número. Um erro traz `dica` e `avisos` no corpo.
7. **Conferir** antes de afirmar — seção 2b.

## 2b. Conferência antes de responder

Pergunta que cruza fontes erra em silêncio: o join casa pela metade, o filtro pega o código de
outro dataset, a soma conta a mesma pessoa duas vezes, e o número sai plausível. Antes de dar a
resposta:

1. **Escreva a ordem de grandeza esperada antes de rodar** (população de SP ~45 mi; óbitos no
   Brasil ~1,5 mi/ano; nascidos vivos ~2,6 mi/ano). Um resultado 1.000× fora é unidade ou join.
2. **Use o caso parecido** de `/exemplos` como régua: se o seu número diverge de um medido
   para o mesmo recorte, descubra por quê antes de responder.
3. **Conte o join.** Rode `count(*)` das duas pontas e do resultado: quantas linhas casaram e
   quantas sobraram. Join por chave com formato diferente (código com `.0`, CNPJ sem zeros,
   município de 6 × 7 dígitos) casa 0% sem dar erro — a ponte em `/contexto` traz a expressão.
4. **Decodifique o código na própria tabela** (`<dataset>.dicionario` ou `/contexto`), nunca
   reaproveitando o de outra fonte: `sexo` e `raca_cor` mudam de código entre datasets e anos.
5. **Dois caminhos para o mesmo total**: soma por UF = total nacional; contagem pela coluna A =
   contagem pela coluna B equivalente. Diferença é sinal de filtro errado.
6. **Cobertura**: diga quais anos, UFs e municípios entraram (`count(DISTINCT id_municipio)`),
   e se a série muda de método no meio (estimativa × Censo, CAGED antigo × Novo CAGED).
7. **Se o dado não existe no espelho, diga isso.** Não troque silenciosamente por outra fonte
   ou outro ano; diga qual seria a fonte certa e o que foi usado no lugar.
8. **Na resposta**: o número, a fonte original (`_rodado_metadata.source_name`), o recorte
   (período, território, filtros), as ressalvas do `/contexto` que se aplicaram e o **link
   `/q/<id>` da consulta que gerou o número** (seção 4b), para quem lê conferir e refazer.

## 3. Consultar: `POST /query`

```bash
curl $AUTH --data-binary 'SELECT sigla_uf, count(*) n FROM br_bd_diretorios_brasil.municipio GROUP BY 1 ORDER BY 2 DESC' \
  https://db.rodado.xyz/query
curl $AUTH 'https://db.rodado.xyz/query?formato=csv' --data-binary @consulta.sql
curl $AUTH -G https://db.rodado.xyz/query --data-urlencode 'q=DESCRIBE br_inep_ideb.municipio'
```

| parâmetro | valores |
|---|---|
| corpo do POST (ou `q=` no GET) | o SQL, **um comando por requisição**, até 512 KB |
| `formato` | sem ele: `{"linhas", "avisos", "contexto", "truncado"}`; `json` (só a lista de linhas), `csv`, `tsv`, `parquet` |
| `limite` | linhas devolvidas: padrão {limite_padrao}, máximo {limite_maximo} |

Cabeçalhos da resposta: `X-Linhas` (quantas vieram), `X-Truncado` (`1` se o limite cortou —
então agregue ou aumente o `limite`), `X-Segundos`, e os avisos também em `X-Avisos` (sem acento,
separados por `||`) — o único lugar onde eles aparecem em `csv`, `tsv`, `parquet` e `json`. Erro vem como `{"erro": "..."}` com
status 400 (SQL inválido ou recusado — inclusive a consulta que cita coluna de armadilha `[erro]`:
o corpo traz a armadilha e a `dica`; repita com `?ciente=1` depois de tratar dela), 429 (servidor cheio: espere e repita), 504 (estourou
{tempo} s).

**Regras do SQL** (dialeto DuckDB, não BigQuery nem Postgres):

- Só leitura: `SELECT`, `FROM`, `WITH`, `DESCRIBE`, `SHOW`, `SUMMARIZE`. Escrita é recusada.
- Tabelas como `dataset.tabela`. Funções que abrem arquivo (`read_parquet`, `read_csv`,
  `glob`…) e `FROM 'caminho'` são recusadas: use as views.
- {tempo} s por consulta e {simultaneas} consultas ao mesmo tempo no servidor inteiro. Seja sequencial.
- Tabela grande (dezenas de milhões de linhas ou mais) exige filtro na partição — as colunas
  com `"particao": true` em `/colunas`, em geral `ano`, `mes`, `sigla_uf`. Sem isso a consulta
  lê o dataset inteiro e estoura o tempo.
- Tabela grande **sem** partição (o `/confere` avisa) é lida inteira a cada consulta, com
  qualquer filtro: `count(DISTINCT causa_basica)` do SIM só para SP levou 73 s. Agregue tudo
  numa consulta só em vez de uma por recorte.
- `SUMMARIZE` e `count(DISTINCT ...)` numa tabela enorme são caros: faça numa partição.

## 4. Exportar

Cada requisição devolve no máximo {limite_maximo} linhas. Para mais que isso, agregue no servidor
ou fatie (uma requisição por `ano`, `sigla_uf`… ou com `ORDER BY` + `OFFSET`), sempre uma por vez.

- **CSV/TSV/Parquet direto**: `?formato=csv` (ou `tsv`, `parquet`) e `-o arquivo`:
  `curl $AUTH 'https://db.rodado.xyz/query?formato=parquet&limite=10000' --data-binary @q.sql -o r.parquet`
- **Python (Polars)**:
  ```python
  import io, os, polars as pl, requests
  r = requests.post("https://db.rodado.xyz/query", params={"formato": "parquet", "limite": 10_000},
                    data=sql.encode(), auth=("rodado", os.environ["RODADO_SENHA"]), timeout=330)
  r.raise_for_status(); df = pl.read_parquet(io.BytesIO(r.content))
  ```
- **DuckDB local** (junta o resultado com dado seu):
  ```sql
  CREATE SECRET rodado (TYPE http, SCOPE 'https://db.rodado.xyz',
    EXTRA_HTTP_HEADERS MAP {'Authorization': 'Basic ' || to_base64(('rodado:' || getenv('RODADO_SENHA'))::BLOB)});
  SET force_download = true;
  CREATE MACRO rodado(q) AS TABLE
    FROM read_parquet('https://db.rodado.xyz/query?formato=parquet&limite=10000&q=' || url_encode(q));
  FROM rodado('SELECT ano, count(*) FROM br_ms_sim.microdados WHERE ano >= 2020 GROUP BY 1');
  ```
- **Link para humanos**: ver a seção 4b.

## 4b. Toda resposta leva o link `/q/` da consulta

Quem te fez a pergunta quer o número **e** o caminho até ele. Por isso, ao responder qualquer
pergunta com estes dados — mesmo que ninguém tenha pedido link —, salve cada SQL que sustenta a
resposta e cite o link curto ao lado do número que ela produziu:

```bash
curl $AUTH --data-binary @q.sql https://db.rodado.xyz/q      # → {"id": "14QDGArQ", "url": "/q/14QDGArQ"}
```

`https://db.rodado.xyz/q/<id>` abre o terminal do navegador com a consulta já rodando: quem lê
confere o número, muda o filtro e refaz, sem copiar SQL. Na resposta, prefixe o domínio
(`https://db.rodado.xyz/q/14QDGArQ`), um link por número ou tabela de resultado — não um por
consulta exploratória que ficou pelo caminho.

- **Salve a SQL final, a que deu o número citado**, depois do `/query` bem-sucedido: o link
  executa de novo, então a consulta tem que rodar dentro de {tempo} s (filtro de partição).
- Um comando por link, até 64 KB. A mesma SQL dá sempre o mesmo id: repetir o `POST` não duplica.
- Quem abre um link que existe entra sem senha e roda aquela consulta; não ponha no SQL nada
  que não deva ir para quem recebe a resposta (dado pessoal fora do que a pergunta pedia,
  credencial, comentário interno).
- Sem acesso a HTTP de escrita? Mostre a SQL em bloco de código e diga que o link não foi gerado.

## 5. Armadilhas que já custaram caro

As gerais; as de cada dataset estão em `/contexto?dataset=`.

- **CNPJ**: `br_me_cnpj.empresas`, `estabelecimentos`, `socios` e `simples` são só o **retrato
  mais recente** (sem filtro de ano/mês). O passado está em `*_historico`: estado na data X
  = `inicio <= X AND fim >= X` (aaaamm). Classificar estabelecimento por nome não precisa de
  join com `empresas` (`nome_fantasia` já está em `estabelecimentos`).
- **Chaves de join**: município é `id_municipio` (IBGE, 7 dígitos) na maioria; a Receita usa
  `id_municipio_rf` — converta por `br_bd_diretorios_brasil.municipio`. CNPJ pode vir sem
  zeros à esquerda em algumas fontes: compare com `lpad(cnpj, 14, '0')`.
- **Mesmo nome, coisas diferentes**: `valor` aparece em dezenas de tabelas com sentidos
  diferentes; nunca junte por ele. `sexo` e `raca_cor` têm códigos que mudam entre datasets.
- **Valores monetários** em reais inteiros, salvo indicação; desconfie de total na casa do trilhão.
- **Procedência**: `_rodado_metadata` diz de onde veio cada tabela (`source_name`, `source_url`,
  `scrape_date`). Cite a fonte original, não "o rodado".

## 6. Temas

`tema` · nome · datasets — os maiores por número de linhas. Os datasets de um tema em
`/tabelas?tema=<tema>`; contexto semântico gerado em {gerado_contexto}.

{temas}
