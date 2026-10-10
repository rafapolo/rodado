#!/usr/bin/env bash
# Baixa os locais de votação do TSE (2022 e 2026) no beelink e reconstrói
# br_rodado_eleicoes.{secao_setor,setor_local}. Idempotente: sobrescreve os dois parquet.
# Depois de rodar, se as views ainda não existirem:
#   printf 'br_rodado_eleicoes/secao_setor\nbr_rodado_eleicoes/setor_local\n' > /tmp/l.txt
#   python3 scripts/sync/cria_views_novas.py /tmp/l.txt
set -euo pipefail
BEELINK="${BEELINK_HOST:-beelink}"
AQUI="$(cd "$(dirname "$0")" && pwd)"
URL="https://cdn.tse.jus.br/estatistica/sead/odsele/eleitorado_locais_votacao/eleitorado_local_votacao"

ssh "$BEELINK" bash -s <<REMOTO
set -euo pipefail
mkdir -p ~/rodado/br_rodado_eleicoes/secao_setor ~/rodado/br_rodado_eleicoes/setor_local
for ano in 2022 2026; do
  d=~/duckdb_tmp/tse_locais/\$ano
  mkdir -p "\$d"
  curl -sf -o "\$d/locais.zip" "${URL}_\$ano.zip"
  unzip -o -q "\$d/locais.zip" -d "\$d" -x '*.pdf'
done
REMOTO
ssh "$BEELINK" '~/bin/duckdb -readonly ~/rodado/basedosdados.duckdb' < "$AQUI/constroi_ponte.sql"
