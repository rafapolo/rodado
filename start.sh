#!/bin/bash
set -euo pipefail

echo "[start] Building DuckDB views from S3..."
python3 prepara_db.py

echo "[start] Starting Caddy..."
caddy start --config /app/Caddyfile --adapter caddyfile

echo "[start] Starting DuckDB UI on :4213..."
exec duckdb --ui basedosdados3.duckdb
