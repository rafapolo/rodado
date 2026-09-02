#!/usr/bin/env bash
# Sobe (ou reinicia) o llama-server no beelink com a config medida, e abre o
# túnel daqui. Sem argumentos reinicia; `status` só informa.
#
#     ./harness/servidor.sh          # reinicia com a config padrão
#     ./harness/servidor.sh status   # o que está no ar
#     CTX=65536 SLOTS=5 ./harness/servidor.sh   # avaliação paralela
#
# Existe porque reiniciar isso à mão falhou três vezes seguidas do mesmo jeito:
# o processo antigo ainda segura a porta quando o novo tenta subir, e o novo
# morre com "couldn't bind" sem que nada apareça — o antigo continua servindo
# com a config velha, e a medição seguinte sai errada sem aviso.
set -euo pipefail

HOST="${BEELINK_HOST:-beelink}"
PORTA="${PORTA:-8099}"
CTX="${CTX:-32768}"
SLOTS="${SLOTS:-1}"
MODELO="${MODELO:-~/llm/gemma-4-26B_q4_0-it.gguf}"
BIN="${BIN:-~/llama.cpp/build/bin/llama-server}"

estado() {
  local cfg
  cfg=$(ssh "$HOST" "ps -eo args | grep '[l]lama-server -m' | head -1" 2>/dev/null || true)
  if [[ -z "$cfg" ]]; then echo "  servidor: parado"; else
    echo "  servidor: $(echo "$cfg" | grep -oE '\-c [0-9]+ -np [0-9]+' || echo '?')"
    echo "  saúde:    $(ssh "$HOST" "curl -s -m 3 http://127.0.0.1:$PORTA/health" 2>/dev/null || echo inalcançável)"
  fi
  if curl -s -m 3 "http://127.0.0.1:$PORTA/health" >/dev/null 2>&1; then
    echo "  túnel:    aberto"
  else
    echo "  túnel:    fechado"
  fi
}

if [[ "${1:-}" == "status" ]]; then estado; exit 0; fi

echo "parando o que estiver no ar…"
# -np com pgrep numa linha só mataria o próprio ssh: o padrão casa a si mesmo.
ssh "$HOST" 'for p in $(pgrep -f "llama-server -m"); do kill -9 "$p" 2>/dev/null || true; done' || true

# Esperar a PORTA liberar, não o processo sumir: é o bind que falha, e ele falha
# em silêncio.
for _ in $(seq 1 20); do
  sleep 1
  ssh "$HOST" "ss -ltn 2>/dev/null | grep -q ':$PORTA '" || break
done

echo "subindo: -c $CTX -np $SLOTS  (thinking off, KV em f16)"
# Cada flag é medida, não gosto — ver harness/README.md.
ssh "$HOST" "setsid $BIN -m $MODELO \
  -t 8 -c $CTX -np $SLOTS \
  --chat-template-kwargs '{\"enable_thinking\":false}' \
  --host 127.0.0.1 --port $PORTA < /dev/null > /tmp/srv.log 2>&1 & disown" || true

for _ in $(seq 1 60); do
  sleep 5
  ssh "$HOST" "curl -s -m 2 http://127.0.0.1:$PORTA/health" 2>/dev/null | grep -q ok && break
done

# O túnel, se ainda não estiver de pé: o servidor escuta só em loopback.
curl -s -m 3 "http://127.0.0.1:$PORTA/health" >/dev/null 2>&1 || \
  ssh -f -N -L "$PORTA:127.0.0.1:$PORTA" "$HOST" 2>/dev/null || true
sleep 2

# Confere que subiu com a config PEDIDA, não com a que sobrou.
real=$(ssh "$HOST" "grep -a -oE 'n_slots = [0-9]+, n_ctx_slot = [0-9]+' /tmp/srv.log | head -1" 2>/dev/null || true)
echo "$real"
if [[ "$real" != *"n_slots = $SLOTS"* || "$real" != *"n_ctx_slot = $CTX"* ]]; then
  echo "AVISO: o que subiu não é o que foi pedido (-c $CTX -np $SLOTS). Rode de novo." >&2
  exit 1
fi
estado
