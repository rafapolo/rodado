# baseldosdados

Mirror completo das tabelas públicas do projeto [Base dos Dados](https://basedosdados.org/) — 533 tabelas, ~675 GB em Parquet+zstd — hospedado no Hetzner Object Storage e acessível via DuckDB.

## O que tem aqui

| Script | Função |
|---|---|
| `roda.sh` | Exporta BigQuery → GCS → Hetzner S3 (pipeline principal) |
| `prepara_gui.py` | Cria views DuckDB sobre os parquets do S3 para exploração local |
| `gera_schemas.py` | Gera `schemas.json` e `file_tree.md` com metadados de todos os parquets |

**Arquivos gerados:**

| Arquivo | Descrição |
|---|---|
| `schemas.json` | Schema completo de todas as 533 tabelas (colunas, tipos, tamanhos) |
| `file_tree.md` | Árvore do bucket S3 com tamanhos e contagem de arquivos |
| `basedosdados.duckdb` | Banco DuckDB com views para todas as tabelas (gerado por `prepara_gui.py`) |
| `all_tables.txt` | Lista completa de tabelas descobertas |
| `done_tables.txt` | Tabelas exportadas com sucesso para o GCS |
| `done_transfers.txt` | Datasets transferidos com sucesso para o S3 |
| `failed_tables.txt` | Tabelas que falharam após 3 tentativas |

## Fluxo de exportação

```
BigQuery (basedosdados) → GCS (Parquet + zstd) → Hetzner Object Storage (rclone)
```

1. Descobre automaticamente todos os datasets e tabelas via API do BigQuery
2. Exporta todas as tabelas em paralelo no formato Parquet com compressão zstd
3. Transfere GCS → Hetzner Object Storage via rclone (streaming direto, sem disco local)
4. Verifica a contagem de arquivos entre GCS e S3
5. Oferece opção de deletar o bucket GCS ao final

O script suporta **resume automático**: se interrompido, basta rodar novamente — tabelas e transfers já concluídos são pulados.

## Estrutura dos dados no S3

```
s3://<HETZNER_S3_BUCKET>/
└── <dataset>/
    └── <tabela>/
        └── *.parquet
```

## Pré-requisitos

**Exportação (`roda.sh`) — execução local:**
- `google-cloud-sdk` (`bq`, `gcloud`, `gsutil`)
- `parallel` (GNU parallel)
- `rclone`
- `flock`

**Execução via VM (`--gcloud-run`):** apenas `gcloud` localmente — dependências instaladas automaticamente na VM.

**Scripts Python** (`prepara_gui.py`, `gera_schemas.py`):
- `duckdb`, `pyarrow`, `boto3`, `s3fs`, `python-dotenv`

Autenticação GCP (uma vez antes da exportação):

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project SEU_PROJECT_ID
```

## Configuração

Crie um arquivo `.env` na raiz:

| Variável | Descrição |
|---|---|
| `YOUR_PROJECT` | ID do seu projeto GCP (para faturamento) |
| `BUCKET_NAME` | Nome do bucket GCS intermediário |
| `BUCKET_REGION` | Região do bucket — deve ser `US` |
| `SOURCE_PROJECT` | Projeto fonte (`basedosdados`) |
| `PARALLEL_EXPORTS` | Jobs paralelos de exportação BigQuery (padrão: 8) |
| `HETZNER_S3_BUCKET` | Nome do bucket no Hetzner Object Storage |
| `HETZNER_S3_ENDPOINT` | Endpoint do Hetzner (ex: `https://hel1.your-objectstorage.com`) |
| `S3_CONCURRENCY` | Transfers paralelos do rclone (padrão: 64) |
| `PARALLEL_UPLOADS` | Datasets enviados em paralelo (padrão: 4) |
| `AWS_ACCESS_KEY_ID` | Access key do Hetzner Object Storage |
| `AWS_SECRET_ACCESS_KEY` | Secret key do Hetzner Object Storage |

## Uso

```bash
# Exportação
chmod +x roda.sh
./roda.sh --dry-run    # estima tamanho e custo antes de rodar
./roda.sh              # execução local
./roda.sh --gcloud-run # cria VM no GCP, roda lá e deleta a VM ao final

# Exploração via DuckDB
python prepara_gui.py  # cria basedosdados.duckdb com views para todas as tabelas
duckdb --ui basedosdados.duckdb

# Dump de schemas
python gera_schemas.py  # gera schemas.json e file_tree.md (~21 MB de egress)
```

## Servidor com UI protegida por senha

Para expor o DuckDB UI num servidor com HTTPS e autenticação básica, use o [Caddy](https://caddyserver.com/) como reverse proxy.

**Pré-requisitos no servidor:** `caddy`, `htpasswd` (pacote `apache2-utils`), `duckdb`

**1. Instalar o serviço DuckDB UI**

Edite `duckdb-ui.service` com o usuário e caminho corretos e copie para o systemd:

```bash
# edite User= e WorkingDirectory= e EnvironmentFile= no arquivo
cp duckdb-ui.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now duckdb-ui
```

**2. Configurar o Caddy**

Edite `Caddyfile` substituindo `your.domain.com` pelo domínio real, depois:

```bash
cp Caddyfile /etc/caddy/Caddyfile
systemctl reload caddy
```

O Caddy obtém o certificado TLS via Let's Encrypt automaticamente (portas 80 e 443 abertas no firewall).

**Trocar a senha:**

```bash
htpasswd -nbB -C 10 admin NOVA_SENHA | cut -d: -f2 | base64
# cole o resultado no Caddyfile no lugar do hash atual, depois:
systemctl reload caddy
```

**Arquivos relevantes:**

| Arquivo | Função |
|---|---|
| `Caddyfile` | Config do Caddy: HTTPS + basicauth → proxy para localhost:4213 |
| `duckdb-ui.service` | Serviço systemd que sobe o DuckDB UI em background |

---

### `--gcloud-run`

Cria uma VM `e2-standard-4` Debian 12 em `us-central1-a`, copia o script e o `.env`, instala as dependências e executa via SSH. Variáveis opcionais:

| Variável | Padrão | Descrição |
|---|---|---|
| `GCP_VM_NAME` | `bd-export-vm` | Nome da instância |
| `GCP_VM_ZONE` | `us-central1-a` | Zona do Compute Engine |
