#!/bin/bash
set -euo pipefail

S3_ENDPOINT="${HETZNER_S3_ENDPOINT#https://}"
S3_ENDPOINT="${S3_ENDPOINT#http://}"

# Init SQL para o terminal web (credenciais não ficam expostas como env vars)
cat > /app/ssh_init.sql <<SQL
INSTALL httpfs;
LOAD httpfs;
SET s3_endpoint='${S3_ENDPOINT}';
SET s3_access_key_id='${AWS_ACCESS_KEY_ID}';
SET s3_secret_access_key='${AWS_SECRET_ACCESS_KEY}';
SET s3_region='${BUCKET_REGION}';
SET s3_url_style='path';
SET enable_object_cache=true;
SET threads=4;
SET memory_limit='4GB';
SQL
chmod 600 /app/ssh_init.sql

echo "[start] Starting ttyd terminal (db)..."
ttyd --port 7681 --writable duckdb -readonly --init /app/ssh_init.sql /app/data/basedosdados.duckdb &

echo "[start] Starting ttyd terminal (ask)..."
PROMPT_FILE=/app/system_prompt.md ttyd --port 7682 --writable /app/ask &

echo "[start] Starting auth service..."
python3 /app/auth.py &

echo "[start] Starting Caddy..."
exec caddy run --config /app/Caddyfile --adapter caddyfile
