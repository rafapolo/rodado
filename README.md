# baseldosdados

Mirror completo das tabelas públicas do projeto [Base dos Dados](https://basedosdados.org/) — 533 tabelas, ~675 GB em Parquet+zstd — hospedado no Hetzner Object Storage e acessível via DuckDB no browser.

## Scripts

| Script | Função |
|---|---|
| `roda.sh` | Exporta BigQuery → GCS → Hetzner S3 (pipeline principal) |
| `prepara_db.py` | Cria `basedosdados.duckdb` com views sobre os parquets do S3 |

## Fluxo de exportação

```
BigQuery (basedosdados) → GCS (Parquet + zstd) → Hetzner Object Storage (rclone)
```

1. Descobre automaticamente todos os datasets e tabelas via API do BigQuery
2. Exporta em paralelo no formato Parquet com compressão zstd
3. Transfere GCS → Hetzner Object Storage via rclone (streaming direto, sem disco local)
4. Verifica a contagem de arquivos entre GCS e S3

Resume automático: se interrompido, basta rodar novamente — tabelas e transfers já concluídos são pulados.

## Estrutura dos dados no S3

```
s3://<HETZNER_S3_BUCKET>/
└── <dataset>/
    └── <tabela>/
        └── *.parquet
```

## Configuração

Crie um arquivo `.env`:

| Variável | Descrição |
|---|---|
| `YOUR_PROJECT` | ID do seu projeto GCP (para faturamento) |
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
| `BASIC_AUTH_PASSWORD` | Senha de acesso ao shell web e endpoint `/query` |

## Uso — exportação

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

### `--gcloud-run`

Cria uma VM `e2-standard-4` Debian 12 em `us-central1-a`, copia o script e o `.env`, instala dependências e executa via SSH.

| Variável | Padrão | Descrição |
|---|---|---|
| `GCP_VM_NAME` | `bd-export-vm` | Nome da instância |
| `GCP_VM_ZONE` | `us-central1-a` | Zona do Compute Engine |

## Uso — exploração local

```bash
python prepara_db.py  # cria basedosdados.duckdb com views para todas as tabelas
duckdb basedosdados.duckdb
```

## Acesso remoto — https://db.xn--2dk.xyz

Container Docker (Caddy + ttyd) com shell DuckDB acessível via browser ou curl, protegido por senha.

### Shell no browser

Acesse https://db.xn--2dk.xyz → autentique com a senha → shell DuckDB interativo direto no browser.

### SQL via curl

Endpoint `POST /query` — aceita SQL no body, retorna output como texto plano.
Autenticação via header `X-Password`.

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

# Salvar resultado
curl -s -X POST https://db.xn--2dk.xyz/query \
  -H "X-Password: <senha>" \
  --data-binary @query.sql > resultado.csv
```

O DuckDB suporta saída em CSV e JSON nativamente:

```sql
-- CSV com header
COPY (SELECT * FROM br_ibge_censo2022.municipios LIMIT 100)
TO '/dev/stdout' (FORMAT csv, HEADER true);

-- JSON
SELECT * FROM br_ibge_censo2022.municipios LIMIT 10
FORMAT JSON;
```

### Deploy

```bash
haloy deploy
```
