#!/usr/bin/env bash
# Roda cada qN_*.sql no beelink (somente leitura) e grava o CSV ao lado.
set -euo pipefail  # erro de SQL sai no stderr: rode a query à mão para ver
cd "$(dirname "$0")"
for f in q*.sql; do
  [ -n "${1:-}" ] && [[ "$f" != "$1"* ]] && continue
  echo "-> $f"
  { echo "SET enable_progress_bar=false;"; cat "$f"; } |
    ssh "${BEELINK_HOST:-beelink}" '~/bin/duckdb -readonly -csv ~/rodado/basedosdados.duckdb' 2>/dev/null > "${f%.sql}.csv"
done
