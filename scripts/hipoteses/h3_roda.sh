#!/usr/bin/env bash
# hipoteses3 — extracao OFFLINE no beelink. Nao usa rede.
#
#   ssh beelink 'bash -s' < scripts/hipoteses/h3_roda.sh      # ou copie e rode la
#   bash scripts/hipoteses/h3_roda.sh                          # se ja estiver no beelink
#
# Cada bloco grava CSV em $OUT e deixa um sentinela: rodar de novo pula o que ja
# terminou, entao a corrida e retomavel se a maquina cair no meio da noite.
# Os blocos 90-94 sao as tabelas gigantes (SIA tem 6,16 bilhoes de linhas) e
# ficam por ultimo de proposito: se algum estourar o tempo, os 11 primeiros ja
# terminaram e o resultado e aproveitavel.
#
# Variaveis:
#   DB      caminho do .duckdb   (default ~/rodado/basedosdados.duckdb)
#   DUCKDB  binario duckdb       (default ~/bin/duckdb)
#   OUT     saida                (default ~/rodado_hipoteses/h3_<data>)
#   ONLY    roda so o que casar  (ex: ONLY=60 para so a matriz de CNPJ)
#   SKIP    pula o que casar     (ex: SKIP=9 para deixar os gigantes de fora)
# DOIS DETALHES DO RENAME (h3_* passou a viver solto em scripts/hipoteses/):
#
# 1. STAGE ANTES DO SCP. Os .sql agora dividem pasta com os scripts da rodada
#    antiga, entao nao da para copiar o diretorio inteiro. Leve so o que e h3:
#      mkdir -p /tmp/h3 && cp scripts/hipoteses/h3_*.sql scripts/hipoteses/h3_roda.sh /tmp/h3/
#      scp -r /tmp/h3 beelink:~/ && ssh beelink 'cd ~/h3 && bash h3_roda.sh'
#
# 2. OS SENTINELAS MUDARAM DE NOME junto com os arquivos: o basename virou
#    `h3_00_pontes` em vez de `00_pontes`. Uma corrida contra um $OUT antigo NAO
#    reconhece o que ja terminou e refaz os 41 blocos do zero -- inclusive o SIA,
#    que le 480 milhoes de linhas. Ou use um $OUT novo, ou renomeie os sentinelas:
#      ssh beelink 'cd ~/rodado_hipoteses/h3_<data> && for f in .done_[0-9]*; do
#                     mv "$f" ".done_h3_${f#.done_}"; done'

set -uo pipefail

DB="${DB:-$HOME/rodado/basedosdados.duckdb}"
DUCKDB="${DUCKDB:-$HOME/bin/duckdb}"
[ -x "$DUCKDB" ] || DUCKDB="$(command -v duckdb || true)"
OUT="${OUT:-$HOME/rodado_hipoteses/h3_$(date +%Y%m%d)}"
ONLY="${ONLY:-}"; SKIP="${SKIP:-}"
SQLDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

[ -f "$DB" ]      || { echo "erro: banco nao encontrado em $DB" >&2; exit 1; }
[ -n "$DUCKDB" ]  || { echo "erro: duckdb nao encontrado" >&2; exit 1; }
mkdir -p "$OUT"
LOG="$OUT/run.log"
say() { printf '%s  %s\n' "$(date +'%F %T')" "$*" | tee -a "$LOG"; }

say "banco   $DB"
say "duckdb  $($DUCKDB --version 2>/dev/null | head -1)"
say "saida   $OUT"
say "---"

for f in "$SQLDIR"/h3_*.sql; do
  name="$(basename "$f" .sql)"
  [ -n "$ONLY" ] && [[ "$name" != *"$ONLY"* ]] && continue
  [ -n "$SKIP" ] && [[ "$name" == *"$SKIP"* ]] && { say "PULA  $name (SKIP)"; continue; }
  if [ -f "$OUT/.done_$name" ]; then say "PULA  $name (ja concluido)"; continue; fi

  tmp="$OUT/.sql_$name.sql"
  sed "s#__OUT__#$OUT#g" "$f" > "$tmp"
  say "INICIA $name"
  t0=$SECONDS
  # -readonly SEMPRE: o banco e lido por outras sessoes e uma conexao de escrita
  # trava todas as demais, inclusive as read-only, ate desconectar.
  if "$DUCKDB" -readonly "$DB" < "$tmp" >> "$LOG" 2>&1; then
    touch "$OUT/.done_$name"
    say "OK    $name  ($((SECONDS-t0))s)"
  else
    say "FALHA $name  ($((SECONDS-t0))s) — segue para o proximo; ver $LOG"
  fi
  rm -f "$tmp"
done

say "---"
say "arquivos gerados:"
ls -1sh "$OUT"/*.csv 2>/dev/null | tee -a "$LOG"
say "fim. Traga com:  scp -r beelink:$OUT ./tasks/hipoteses_resultado/"
