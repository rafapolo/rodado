#!/usr/bin/env bash
#
# bench_gemma.sh — benchmarka gemma-4-26B-A4B (q4_0 QAT) no beelink com uma
# task real, uma execucao por tamanho de batch de prefill.
#
# Roda daqui (mac) e dirige a beelink por ssh. Salva tudo em benchmarks/.
#
#   ./scripts/bench_gemma.sh                              # task padrao
#   ./scripts/bench_gemma.sh tasks/outra_coisa.md         # outra task
#   PPS="512 256 128" ./scripts/bench_gemma.sh            # outros batches
#
set -euo pipefail

# ---------------------------------------------------------------------------
# THREADS=8 e CONSTANTE, nao parametro.
#
# Medido em 2026-09-01 (ver gemma_stats.md): os 8 nucleos fisicos do Ryzen
# 5800H ja saturam a banda de memoria. Os 8 threads logicos do SMT nao
# acrescentam banda, so disputa — com 16 threads o prefill cai 32%, a geracao
# cai 31% e o desvio-padrao cresce ~10x (+-0,23 -> +-6,27 t/s).
# Nao troque por $(nproc).
# ---------------------------------------------------------------------------
readonly THREADS=8

BEELINK="${BEELINK_HOST:-beelink}"
TASK="${1:-tasks/relatorio_saude_mental.md}"
PPS="${PPS:-512 128}"          # tamanhos de batch de prefill a comparar
NGEN="${NGEN:-512}"            # tokens a gerar na execucao real
CTX="${CTX:-8192}"
REPS="${REPS:-3}"              # repeticoes do llama-bench sintetico

REMOTE_MODEL="\$HOME/llm/gemma-4-26B_q4_0-it.gguf"
REMOTE_BIN="\$HOME/llama.cpp/build/bin"
REMOTE_WORK="\$HOME/llm/bench"
REMOTE_WORK_REL="llm/bench"      # scp nao expande $HOME no destino

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
OUTDIR="$REPO/benchmarks"
mkdir -p "$OUTDIR"

[[ -f "$REPO/$TASK" ]] || { echo "task nao encontrada: $REPO/$TASK" >&2; exit 1; }

TASKNAME="$(basename "$TASK" .md)"
RAW="$OUTDIR/${TASKNAME}_${STAMP}.log"
SUMMARY="$OUTDIR/${TASKNAME}_${STAMP}.md"

echo "task:    $TASK"
echo "batches: $PPS"
echo "threads: $THREADS (fixo)"
echo "saida:   ${SUMMARY#"$REPO"/}"
echo

# --- envia a task ----------------------------------------------------------
ssh "$BEELINK" "mkdir -p $REMOTE_WORK"
scp -q "$REPO/$TASK" "$BEELINK:$REMOTE_WORK_REL/task.md"

# --- contexto da maquina ---------------------------------------------------
{
  echo "### ambiente"
  ssh "$BEELINK" '
    echo "host:      $(hostname)"
    echo "governor:  $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor) / epp=$(cat /sys/devices/system/cpu/cpu0/cpufreq/energy_performance_preference)"
    echo "load:      $(uptime | sed "s/.*average: //")"
    echo "mem livre: $(free -g | awk "/^Mem:/{print \$7\" GiB\"}")"
    echo "build:     $($HOME/llama.cpp/build/bin/llama-cli --version 2>&1 | head -1)"
  '
  echo
} | tee "$RAW"

# --- avisa se o governor nao estiver em performance -------------------------
GOV="$(ssh "$BEELINK" 'cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor')"
if [[ "$GOV" != "performance" ]]; then
  echo "AVISO: governor='$GOV', nao 'performance'. Numeros virao baixos." >&2
  echo "  corrigir: ssh -t $BEELINK 'sudo cpupower frequency-set -g performance'" >&2
  echo >&2
fi

# --- roda ------------------------------------------------------------------
for PP in $PPS; do
  echo "=== pp$PP ===" | tee -a "$RAW"

  echo "  [1/2] llama-bench sintetico (-p $PP)..."
  T0=$(date +%s)
  ssh "$BEELINK" "
    $REMOTE_BIN/llama-bench -m $REMOTE_MODEL \
      -p $PP -n 128 -t $THREADS -r $REPS 2>&1 | grep -E '^\|'
  " | tee -a "$RAW"
  echo "WALL_BENCH_pp$PP=$(( $(date +%s) - T0 ))" | tee -a "$RAW"

  echo "  [2/2] execucao real da task (-b $PP -ub $PP)..."
  T1=$(date +%s)
  ssh "$BEELINK" "
    cd $REMOTE_WORK
    $REMOTE_BIN/llama-cli -m $REMOTE_MODEL \
      -f task.md -st --jinja \
      -t $THREADS -b $PP -ub $PP -n $NGEN -c $CTX \
      --temp 0.7 --top-p 0.95 --top-k 20 --seed 42 \
      < /dev/null > bruto_pp$PP.txt 2>&1
    grep -oE '\[ Prompt: [0-9.]+ t/s \| Generation: [0-9.]+ t/s \]' bruto_pp$PP.txt | tail -1
    # limpa a saida do llama-cli. O cabecalho (banner ASCII + lista de /comandos)
    # muda de tamanho entre builds, entao usa maquina de estados em vez de contar
    # linhas: descarta tudo ate o fim do bloco "available commands:", e corta no
    # rodape de perf.
    awk '
      estado==0 && /^available commands:/ {estado=1; next}
      estado==0 {next}
      estado==1 && (/^  \// || /^[[:space:]]*$/) {next}
      estado==1 {estado=2}
      estado==2 && /^\[ Prompt:/ {exit}
      estado==2 {print}
    ' bruto_pp$PP.txt > resposta_pp$PP.txt
    # rede de seguranca: se o cabecalho mudar e o awk zerar a saida, cai pro corte simples
    if [ ! -s resposta_pp$PP.txt ]; then
      sed -e '1,/^modalities /d' -e '/^\[ Prompt:/,\$d' bruto_pp$PP.txt > resposta_pp$PP.txt
    fi
    echo \"PALAVRAS=\$(wc -w < resposta_pp$PP.txt)\"
  " | tee -a "$RAW"
  echo "WALL_TASK_pp$PP=$(( $(date +%s) - T1 ))" | tee -a "$RAW"
  echo | tee -a "$RAW"
done

# --- traz as respostas de volta --------------------------------------------
for PP in $PPS; do
  scp -q "$BEELINK:$REMOTE_WORK_REL/resposta_pp$PP.txt" \
        "$OUTDIR/${TASKNAME}_${STAMP}_resposta_pp$PP.txt" 2>/dev/null || true
done

# --- resumo em markdown ----------------------------------------------------
{
  echo "# Benchmark — $TASKNAME"
  echo
  echo "- Modelo: \`gemma-4-26B-A4B-it-qat\` (q4_0), 13,43 GiB, MoE 128 experts / ~4B ativos"
  echo "- Threads: **$THREADS** (fixo — ver gemma_stats.md)"
  echo "- Task: \`$TASK\` ($(wc -w < "$REPO/$TASK" | tr -d ' ') palavras)"
  echo "- Data: $(date '+%Y-%m-%d %H:%M')"
  echo
  echo "## Sintetico (llama-bench)"
  echo
  echo "| teste | t/s |"
  echo "|---|---|"
  grep -E '^\| gemma4' "$RAW" \
    | awk -F'|' '{gsub(/^ +| +$/,"",$7); gsub(/^ +| +$/,"",$8); print "| "$7" | "$8" |"}' \
    | sort -u
  echo
  echo "## Execucao real da task"
  echo
  echo "| batch | tempo total | prefill (t/s) | geracao (t/s) | palavras |"
  echo "|---|---|---|---|---|"
  for PP in $PPS; do
    BLK=$(awk "/^=== pp$PP ===/{f=1} f{print} /^WALL_TASK_pp$PP=/{if(f)exit}" "$RAW")
    WT=$(echo "$BLK" | grep -oE "WALL_TASK_pp$PP=[0-9]+" | tail -1 | cut -d= -f2)
    PE=$(echo "$BLK" | grep -oE 'Prompt: [0-9.]+' | tail -1 | cut -d' ' -f2)
    GE=$(echo "$BLK" | grep -oE 'Generation: [0-9.]+' | tail -1 | cut -d' ' -f2)
    TK=$(echo "$BLK" | grep -oE 'PALAVRAS=[0-9]+' | tail -1 | cut -d= -f2)
    echo "| $PP | ${WT:-?} s | ${PE:-?} | ${GE:-?} | ${TK:-?} |"
  done
  echo
  echo "## Tempo de parede por etapa"
  echo
  echo "| batch | llama-bench | task real |"
  echo "|---|---|---|"
  for PP in $PPS; do
    WB=$(grep -oE "WALL_BENCH_pp$PP=[0-9]+" "$RAW" | tail -1 | cut -d= -f2)
    WT=$(grep -oE "WALL_TASK_pp$PP=[0-9]+" "$RAW" | tail -1 | cut -d= -f2)
    echo "| $PP | ${WB:-?} s | ${WT:-?} s |"
  done
  echo
  echo "Log completo: \`${RAW#"$REPO"/}\`"
  echo "Respostas geradas: \`benchmarks/${TASKNAME}_${STAMP}_resposta_pp*.txt\`"
} > "$SUMMARY"

echo
echo "--- resumo ---"
cat "$SUMMARY"
