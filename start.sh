#!/bin/bash
set -euo pipefail

# DuckDB init: load S3 credentials from env at session start
INIT=$(mktemp /tmp/duckdb_init_XXXX.sql)
S3_ENDPOINT="${HETZNER_S3_ENDPOINT#https://}"
S3_ENDPOINT="${S3_ENDPOINT#http://}"
cat > "$INIT" <<SQL
INSTALL httpfs; LOAD httpfs;
SET s3_endpoint='${S3_ENDPOINT}';
SET s3_access_key_id='${AWS_ACCESS_KEY_ID}';
SET s3_secret_access_key='${AWS_SECRET_ACCESS_KEY}';
SET s3_url_style='path';
SQL

echo "[start] Starting Caddy..."
caddy start --config /app/Caddyfile --adapter caddyfile

echo "[start] Starting DuckDB UI..."
exec duckdb --ui -init "$INIT" basedosdados.duckdb
