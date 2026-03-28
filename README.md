# baseldosdados

Mirror completo das tabelas públicas do projeto [Base dos Dados](https://basedosdados.org/) — 533 tabelas, ~675 GB em Parquet+zstd.

Os dados foram exportados do BigQuery para o Hetzner Object Storage (Helsinki) no formato Parquet com compressão zstd, organizados por dataset e tabela. O acesso é feito diretamente sobre os arquivos via DuckDB, sem necessidade de importar nada localmente — as queries leem os parquets do S3 sob demanda.

---

## Consultando os dados

Acesso via browser ou curl, protegido por senha. Peça a senha para o administrador.

### Shell no browser

Acesse **https://db.xn--2dk.xyz** → autentique → shell DuckDB interativo direto no browser.

### SQL via curl

Endpoint `POST /query` — SQL no body, resultado como texto plano:

```bash
# Query inline
curl -s -X POST https://db.xn--2dk.xyz/query \
  -H "X-Password: <senha>" \
  --data-binary "SELECT count(*) FROM br_anatel_banda_larga_fixa.densidade_brasil"

# A partir de um arquivo .sql
curl -s -X POST https://db.xn--2dk.xyz/query \
  -H "X-Password: <senha>" \
  --data-binary @minha_query.sql

# Heredoc (útil em scripts)
curl -s -X POST https://db.xn--2dk.xyz/query \
  -H "X-Password: <senha>" \
  --data-binary @- << 'SQL'
SELECT sigla_uf, sum(densidade) AS total
FROM br_anatel_banda_larga_fixa.densidade_uf
WHERE ano = 2023
GROUP BY 1
ORDER BY 2 DESC
SQL

# Salvar resultado em arquivo
curl -s -X POST https://db.xn--2dk.xyz/query \
  -H "X-Password: <senha>" \
  --data-binary @query.sql > resultado.csv
```

### Descobrindo tabelas

```sql
-- listar todos os datasets (schemas)
SHOW SCHEMAS;

-- listar tabelas de um dataset
SHOW TABLES IN br_anatel_banda_larga_fixa;

-- ver colunas de uma tabela
DESCRIBE br_anatel_banda_larga_fixa.densidade_brasil;
```

No shell do browser, `.tables` lista tudo de uma vez.

### Exportar em CSV ou JSON

O DuckDB permite formatar a saída diretamente na query:

```sql
-- CSV com header (pipe para arquivo via curl)
COPY (SELECT * FROM br_ibge_censo2022.municipios LIMIT 1000)
TO '/dev/stdout' (FORMAT csv, HEADER true);

-- JSON
SELECT * FROM br_ibge_censo2022.municipios LIMIT 10
FORMAT JSON;
```

---

## Exploração local

Para rodar as queries na sua própria máquina com DuckDB instalado:

```bash
python prepara_db.py   # gera basedosdados.duckdb com views apontando para o S3
duckdb basedosdados.duckdb
```

As queries são executadas diretamente sobre os arquivos Parquet no S3 — não há download de dados. O DuckDB lê os arquivos remotos sob demanda via `httpfs`.

---

## Ask: linguagem natural → SQL

Interface TUI que permite fazer perguntas em português e obter SQL automaticamente.

### No browser

Acesse **https://ask.xn--2dk.xyz** → autentique → digite sua pergunta em português.

### Local

```bash
cd ask
cargo build --release
./target/release/ask                    # modo interativo
./target/release/ask "Quantos municípios tem SP?"  # modo CLI
```

### Variáveis de ambiente

| Variável | Descrição |
|---|---|
| `GEMINI_API_KEY` | Chave da API Gemini (obrigatória para usar modelos Gemini) |
| `OPENROUTER_API_KEY` | Chave para usar modelos via OpenRouter |
| `GEMINI_MODEL` | Modelo a usar (padrão: `gemini-flash-latest`) |
| `SCHEMA_FILE` | Arquivo de schema (padrão: `context/schema_compact_inline.txt`) |
| `DB_FILE` | Arquivo DuckDB (padrão: `basedosdados.duckdb`) |

---

## Arquivos de schema

O diretório `context/` contém artefatos gerados automaticamente para contexto do LLM e descoberta de tabelas:

| Arquivo | Descrição |
|---|---|
| `schema_compact_inline.txt` | Schema condensado para contexto do LLM |
| `schema_compact.txt` | Schema mais verboso |
| `schema_ddl.sql` | DDL das views DuckDB |
| `join_graph.json` | Relacionamentos entre tabelas |
| `file_tree.md` | Estrutura de arquivos no S3 com tamanhos |
| `schemas.json` | Schema raw do BigQuery |

---

## Descobrindo tabelas

```sql
-- listar todos os datasets (schemas)
SHOW SCHEMAS;

-- listar tabelas de um dataset
SHOW TABLES IN br_anatel_banda_larga_fixa;

-- ver colunas de uma tabela
DESCRIBE br_anatel_banda_larga_fixa.densidade_brasil;
```

No shell do browser, `.tables` lista tudo de uma vez. Para descoberta programática, use os arquivos em `context/`.

---

## Pipeline de exportação

> Seção para mantenedores — não necessário para consulta dos dados.

### Fluxo

```
BigQuery (basedosdados) → GCS (Parquet + zstd) → Hetzner Object Storage (rclone)
```

1. Descobre automaticamente todos os datasets e tabelas via API do BigQuery
2. Exporta em paralelo no formato Parquet com compressão zstd
3. Transfere GCS → Hetzner Object Storage via rclone (streaming direto, sem disco local)
4. Verifica contagem de arquivos entre GCS e S3

Resume automático: se interrompido, basta rodar novamente.

### Scripts

| Script | Função |
|---|---|
| `roda.sh` | Pipeline principal de exportação |
| `prepara_db.py` | Gera `basedosdados.duckdb` com views para todas as tabelas |

### Configuração (`.env`)

| Variável | Descrição |
|---|---|
| `YOUR_PROJECT` | ID do projeto GCP (para faturamento) |
| `BUCKET_NAME` | Nome do bucket GCS intermediário |
| `BUCKET_REGION` | Região do bucket S3 (ex: `eu-central`) |
| `SOURCE_PROJECT` | Projeto fonte (`basedosdados`) |
| `PARALLEL_EXPORTS` | Jobs paralelos de exportação BigQuery (padrão: 8) |
| `HETZNER_S3_BUCKET` | Nome do bucket no Hetzner Object Storage |
| `HETZNER_S3_ENDPOINT` | Endpoint do Hetzner (ex: `https://hel1.your-objectstorage.com`) |
| `S3_CONCURRENCY` | Transfers paralelos do rclone (padrão: 64) |
| `PARALLEL_UPLOADS` | Datasets enviados em paralelo (padrão: 4) |
| `AWS_ACCESS_KEY_ID` | Access key do Hetzner Object Storage |
| `AWS_SECRET_ACCESS_KEY` | Secret key do Hetzner Object Storage |
| `BASIC_AUTH_PASSWORD` | Senha do shell web e endpoint `/query` |
| `GEMINI_API_KEY` | Chave da API Gemini para o ask |

### Executando

```bash
chmod +x roda.sh
./roda.sh --dry-run    # estima tamanho e custo
./roda.sh              # execução local
./roda.sh --gcloud-run # cria VM no GCP, roda lá e deleta ao final
```

Autenticação GCP necessária antes da primeira exportação:

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project SEU_PROJECT_ID
```

#### `--gcloud-run`

Cria uma VM `e2-standard-4` Debian 12 em `us-central1-a`, copia o script e o `.env`, instala dependências e executa via SSH.

| Variável | Padrão | Descrição |
|---|---|---|
| `GCP_VM_NAME` | `bd-export-vm` | Nome da instância |
| `GCP_VM_ZONE` | `us-central1-a` | Zona do Compute Engine |

### Deploy do servidor

```bash
haloy deploy
```
