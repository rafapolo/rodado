# baseldosdados

Mirror completo das tabelas públicas do projeto [Base dos Dados](https://basedosdados.org/) — 533 tabelas, ~675 GB em Parquet+zstd.

Os dados foram exportados do BigQuery para o Hetzner Object Storage (Helsinki) no formato Parquet com compressão zstd, organizados por dataset e tabela. O acesso é feito diretamente sobre os arquivos via DuckDB, sem necessidade de importar nada localmente — as queries leem os parquets do S3 sob demanda.

---

## Consultando os dados

Acesso via browser ou curl, protegido por senha - peça!

### Shell no browser

Acesse **https://db.ミ.xyz** → autentique → shell DuckDB interativo direto no browser.

Use `.tables` para listar os datasets.

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

---

## Exploração local

Para rodar as queries na sua própria máquina com DuckDB instalado:

```bash
duckdb data/basedosdados.duckdb
```

As queries são executadas diretamente sobre os arquivos Parquet no S3 — não há download de dados. O DuckDB lê os arquivos remotos sob demanda via `httpfs`.
Precisa da credencial da .env - peça!

---

## Ask: linguagem natural → SQL

Interface TUI que permite fazer perguntas em português e obter SQL automaticamente.

### Arquitetura

```
Pergunta → [schema filtrado] → LLM local (sqlcoder) ou API externa
         → SQL
```

1. **Schema filtrado**: As tabelas relevantes são filtradas e enviadas ao LLM
2. **Geração SQL**: Modelo local (sqlcoder via Ollama) ou API externa (Gemini/OpenRouter)

### No browser

Acesse **https://ask.ミ.xyz** → autentique → digite sua pergunta em português.

### Local

```bash
# Compilar
cd ask
cargo build --release

# Modo interativo (TUI)
./target/release/ask

# Modo CLI
./target/release/ask "Quantos municípios tem SP?"
```

### Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `SQL_GENERATOR` | `gemini` | Generator: `sqlcoder`, `gemini`, ou `openrouter` |
| `GEMINI_API_KEY` | — | Chave API Gemini (obrigatória se usar gemini) |
| `OPENROUTER_API_KEY` | — | Chave API OpenRouter (obrigatória se usar openrouter) |
| `GEMINI_MODEL` | `gemini-flash-lash` | Modelo Gemini |
| `OPENROUTER_MODEL` | `openai/gpt-4o-mini` | Modelo OpenRouter |
| `OLLAMA_MODEL` | `sqlcoder` | Modelo Ollama (sqlcoder ou sqlcoder:14b) |
| `OLLAMA_HOST` | `http://localhost:11434` | Host Ollama |
| `TOP_K_TABLES` | `5` | Número de tabelas a selecionar |
| `SCHEMA_FILE` | `context/schema_compact_inline.txt` | Schema texto para fallback |
| `SCHEMA_JSON` | `context/basedosdados-schema.json` | Schema JSON completo |
| `DB_FILE` | `data/basedosdados.duckdb` | Arquivo DuckDB |

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
| `scripts/roda.sh` | Pipeline principal de exportação |
| `scripts/prepara_db.py` | Gera `data/basedosdados.duckdb` com views para todas as tabelas |

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
chmod +x scripts/roda.sh
./scripts/roda.sh --dry-run    # estima tamanho e custo
./scripts/roda.sh              # execução local
./scripts/roda.sh --gcloud-run # cria VM no GCP, roda lá e deleta ao final
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

### Deploy do servidor para serviços de db e ask

```bash
haloy deploy -f shell/haloy.yml
```
