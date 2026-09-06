#!/usr/bin/env bash
# Bateria de hipoteses do rodado — roda OFFLINE, na maquina que tem o .duckdb.
#
#   bash scripts/hipoteses_overnight.sh
#
# Nao usa rede. Cada bloco SQL grava CSV em $OUT e deixa um sentinela; rodar de
# novo pula o que ja terminou (retomavel se a maquina cair no meio da noite).
#
# Variaveis de ambiente:
#   DB      caminho do .duckdb        (default ~/rodado/basedosdados.duckdb)
#   DUCKDB  binario duckdb            (default ~/bin/duckdb, senao o do PATH)
#   OUT     diretorio de saida        (default ~/rodado_hipoteses/<data>)
#   ONLY    roda so os blocos que casarem com o padrao (ex: ONLY=40)
#
# Depois: copiar $OUT para o repo e pedir a analise.
#   scp -r beelink:~/rodado_hipoteses/<data> ./tasks/hipoteses_resultado/

set -uo pipefail

DB="${DB:-$HOME/rodado/basedosdados.duckdb}"
DUCKDB="${DUCKDB:-$HOME/bin/duckdb}"
[ -x "$DUCKDB" ] || DUCKDB="$(command -v duckdb || true)"
OUT="${OUT:-$HOME/rodado_hipoteses/$(date +%Y%m%d)}"
ONLY="${ONLY:-}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SQLDIR="$HERE/hipoteses"

if [ ! -f "$DB" ]; then echo "erro: banco nao encontrado em $DB" >&2; exit 1; fi
if [ -z "${DUCKDB:-}" ]; then echo "erro: duckdb nao encontrado" >&2; exit 1; fi

mkdir -p "$OUT"
LOG="$OUT/run.log"
say() { printf '%s  %s\n' "$(date +'%F %T')" "$*" | tee -a "$LOG"; }

say "banco   $DB"
say "duckdb  $($DUCKDB --version 2>/dev/null | head -1)"
say "saida   $OUT"
say "---"

run_block() {
  local f="$1" name; name="$(basename "$f" .sql)"
  if [ -n "$ONLY" ] && [[ "$name" != *"$ONLY"* ]]; then return 0; fi
  if [ -f "$OUT/.done_$name" ]; then say "PULA  $name (ja concluido)"; return 0; fi

  local tmp="$OUT/.sql_$name.sql"
  sed "s#__OUT__#$OUT#g" "$f" > "$tmp"

  say "INICIA $name"
  local t0=$SECONDS
  # -readonly: o banco e lido por outras sessoes; nunca abrir para escrita
  if "$DUCKDB" -readonly "$DB" < "$tmp" >> "$LOG" 2>&1; then
    touch "$OUT/.done_$name"
    say "OK    $name  ($((SECONDS-t0))s)"
  else
    say "FALHA $name  ($((SECONDS-t0))s) — segue para o proximo; ver $LOG"
  fi
  rm -f "$tmp"
}

for f in "$SQLDIR"/[0-9]*.sql; do run_block "$f"; done

# analise (numpy + pandas; sem scipy, sem rede)
if [ -n "$ONLY" ] && [[ "90" != *"$ONLY"* ]]; then
  say "pula analise (ONLY=$ONLY)"
else
  say "INICIA analise"
  t0=$SECONDS
  if python3 "$SQLDIR/90_analise.py" "$OUT" >> "$LOG" 2>&1; then
    say "OK    analise ($((SECONDS-t0))s)"
  else
    say "FALHA analise — ver $LOG"
  fi
fi

say "---"
say "arquivos gerados:"
ls -1sh "$OUT"/*.csv "$OUT"/*.tsv "$OUT"/*.txt 2>/dev/null | tee -a "$LOG"
say "fim"
