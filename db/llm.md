# rodado — guia para agentes (db.rodado.xyz)

> Espelho de dados públicos brasileiros consultável por SQL (DuckDB, só leitura):
> {resumo}.
> Este guia é público; os dados exigem credencial. Atualizado a partir do catálogo em {gerado}.

Você é um agente (LLM, script, notebook) e quer responder perguntas com estes dados por conta
própria. Tudo passa por HTTP: descobrir tabelas, ler o schema, consultar, exportar. Nada a instalar.

## 1. Credencial

**Até 26/10/2026 o acesso está aberto**: nenhuma rota pede credencial e os exemplos abaixo
funcionam sem o `$AUTH`. Depois disso, toda rota além desta página pede **uma** destas, que
quem te pediu a tarefa precisa te dar:

- usuário e senha (HTTP Basic): `curl -u rodado:$RODADO_SENHA ...`
- token: `?token=$RODADO_TOKEN` em qualquer URL

Guarde em variável de ambiente; nunca escreva a senha ou o token em arquivo, log, commit ou
resposta. Sem credencial a resposta é `401`. Nos exemplos abaixo, `$AUTH` é `-u rodado:$RODADO_SENHA`.

## 2. O fluxo que funciona

1. **Descobrir** que tabelas existem — texto, um dataset por linha, com a descrição e as
   tabelas com o número de linhas (~60 KB inteiro; filtre para gastar pouco contexto):
   `curl $AUTH 'https://db.rodado.xyz/tabelas?busca=vacina'` (palavras no nome ou na descrição)
   ou `?dataset=br_me_cnpj`. A procedência de cada tabela está em `FROM _rodado_metadata`.
   A lista de datasets está no fim desta página.
2. **Ler o schema** de uma tabela — colunas, tipos e quais são partição:
   `curl $AUTH 'https://db.rodado.xyz/colunas?t=br_me_cnpj.empresas'`
   → `[{"coluna": "...", "tipo": "VARCHAR", "particao": false}, ...]`.
   Para várias tabelas de uma vez: `SELECT schema_name, table_name, column_name, data_type FROM duckdb_columns() WHERE schema_name = 'br_me_rais'`.
3. **Olhar uma amostra** antes de agregar: `FROM dataset.tabela LIMIT 5`. Códigos (sexo,
   raça/cor, tipo de movimentação) costumam vir como número ou sigla; descubra os valores com
   `SELECT col, count(*) FROM ... GROUP BY 1 ORDER BY 2 DESC LIMIT 20`. Muitos datasets têm
   uma tabela `dicionario` com o significado de cada código.
4. **Agregar no servidor** e trazer só o resultado. A consulta roda lá; trazer milhões de
   linhas para agregar na sua máquina é lento e bate no limite.
5. **Conferir** antes de afirmar: ordem de grandeza plausível, total batendo por dois
   caminhos (soma das partes = total), unidades (R$ inteiro, não milhares).

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
| `formato` | `json` (padrão, lista de objetos), `csv`, `tsv`, `parquet` |
| `limite` | linhas devolvidas: padrão {limite_padrao}, máximo {limite_maximo} |

Cabeçalhos da resposta: `X-Linhas` (quantas vieram), `X-Truncado` (`1` se o limite cortou —
então agregue ou aumente o `limite`), `X-Segundos`. Erro vem como `{"erro": "..."}` com
status 400 (SQL inválido ou recusado), 429 (servidor cheio: espere e repita), 504 (estourou
{tempo} s).

**Regras do SQL** (dialeto DuckDB, não BigQuery nem Postgres):

- Só leitura: `SELECT`, `FROM`, `WITH`, `DESCRIBE`, `SHOW`, `SUMMARIZE`. Escrita é recusada.
- Tabelas como `dataset.tabela`. Funções que abrem arquivo (`read_parquet`, `read_csv`,
  `glob`…) e `FROM 'caminho'` são recusadas: use as views.
- {tempo} s por consulta e {simultaneas} consultas ao mesmo tempo no servidor inteiro. Seja sequencial.
- Tabela grande (dezenas de milhões de linhas ou mais) exige filtro na partição — as colunas
  com `"particao": true` em `/colunas`, em geral `ano`, `mes`, `sigla_uf`. Sem isso a consulta
  lê o dataset inteiro e estoura o tempo.
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
- **Link para humanos**: `curl $AUTH --data-binary 'SELECT ...' https://db.rodado.xyz/q` devolve
  `{"url": "/q/<id>"}`; `https://db.rodado.xyz/q/<id>` abre o terminal já com a consulta rodando.

## 5. Armadilhas que já custaram caro

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

## 6. Datasets

`dataset` · tabelas · linhas · fonte. As tabelas de cada um em `/tabelas?dataset=<dataset>`.

{datasets}
