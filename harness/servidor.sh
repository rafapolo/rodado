#!/usr/bin/env bash
# Sobe (ou reinicia) o llama-server no beelink com a config medida, e abre o
# túnel daqui. Sem argumentos reinicia; `status` só informa.
#
#     ./harness/servidor.sh          # reinicia com a config padrão
#     ./harness/servidor.sh status   # o que está no ar
#     ./harness/servidor.sh aquece   # só o aquecimento + detector de raciocínio
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
# Teto do turno de aquecimento, em ms de servidor (prompt_ms + predicted_ms).
# Medido 2026-09-02 com a flag certa: 2.140 ms frio, 530 ms quente, 6 tokens
# gerados. Com raciocínio ligado o mesmo turno gera centenas de tokens de
# pensamento a ~13 t/s e estoura — o histórico do harness é 20,9 s contra 4,7 s.
# 10.000 ms deixa 19x de folga para o caso bom e ainda pega o caso ruim.
LIMIAR_MS="${LIMIAR_MS:-10000}"

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

# Aquecimento com detector de raciocínio ligado.
#
# Por que existe: das quatro maneiras de desligar o raciocínio, três só PARECEM
# funcionar — `reasoningEfforts: false` no dsh declara o modelo como
# não-raciocinante para o harness e não manda nada ao llama.cpp; `--reasoning
# off` no llama-server não resolve; `reasoningEfforts: off:` nem carrega. O que
# resolve é `--chat-template-kwargs '{"enable_thinking":false}'`, e
# `--dump-config` não pega nenhuma das outras: ele valida a composição do patch,
# não o carregamento do plugin. Este script PASSAVA a flag certa e ninguém
# conferia que ela FEZ EFEITO — a distinção é exatamente o modo de falha.
#
# O corpo da requisição NÃO manda `chat_template_kwargs` de propósito.
# `modelo.ts` manda em toda chamada, e mandar aqui testaria a requisição em vez
# do servidor: passaria mesmo com o llama-server subido sem a flag, que é o caso
# que se quer pegar.
#
# Dois turnos, e o julgado é o segundo: o primeiro paga o prefill frio (é o
# aquecimento, que vale por si) e o segundo mede regime. De brinde, `cache_n`
# do segundo turno diz se o cache de prefixo está vivo — 44x sem sinal nenhum
# no resultado quando quebra.
aquece() {
  local url="http://127.0.0.1:$PORTA/v1/chat/completions"
  # Pergunta curta cuja resposta certa tem 6 tokens, mas que um modelo
  # raciocinando responde com centenas. Nada de data nem de nada variável: este
  # corpo é byte-idêntico entre execuções, então o 2º turno mede cache quente.
  local corpo='{"messages":[{"role":"user","content":"Três tabelas do espelho têm 12.480, 9.312 e 4.208 linhas. Qual é o total? Responda só o número."}],"temperature":0,"max_tokens":160}'
  local resp

  curl -s -m 120 "$url" -H 'Content-Type: application/json' -d "$corpo" >/dev/null 2>&1 || true
  resp=$(curl -s -m 120 "$url" -H 'Content-Type: application/json' -d "$corpo" 2>/dev/null || true)

  if [[ -z "$resp" ]]; then
    echo "AVISO: aquecimento não obteve resposta em $url — o túnel está aberto? (ssh -f -N -L $PORTA:127.0.0.1:$PORTA $HOST)" >&2
    return 1
  fi

  # 1. Campo de raciocínio na resposta. O llama.cpp separa o pensamento em
  #    `reasoning_content` quando `--reasoning-format` é deepseek/auto, e o
  #    deixa inline como `<think>` quando é `none` — por isso as três formas.
  if grep -qE '"reasoning(_content)?"[[:space:]]*:' <<<"$resp" || grep -qF '<think' <<<"$resp"; then
    echo "REPROVADO: o servidor devolveu campo de raciocínio — thinking está LIGADO." >&2
    echo "Conserto: suba o llama-server com --chat-template-kwargs '{\"enable_thinking\":false}'." >&2
    echo "Não adianta --reasoning off nem reasoningEfforts no dsh: os dois passam por aplicados e não são." >&2
    return 1
  fi

  # 2. Tempo do turno. Sem campo de raciocínio a saída pode ainda vir cheia de
  #    pensamento em prosa; o tempo pega esse caso.
  local pms dms tot cache
  pms=$(grep -oE '"prompt_ms":[0-9.]+' <<<"$resp" | head -1 | cut -d: -f2)
  dms=$(grep -oE '"predicted_ms":[0-9.]+' <<<"$resp" | head -1 | cut -d: -f2)
  cache=$(grep -oE '"cache_n":[0-9]+' <<<"$resp" | head -1 | cut -d: -f2)
  tot=$(awk -v a="${pms:-0}" -v b="${dms:-0}" 'BEGIN{printf "%d", a+b}')

  if [[ -z "$pms$dms" ]]; then
    echo "AVISO: resposta sem bloco timings — não dá para medir o turno. Confira à mão." >&2
    return 1
  fi
  printf '  aquecimento: %s ms (limiar %s), cache_n=%s\n' "$tot" "$LIMIAR_MS" "${cache:-?}"
  if (( tot > LIMIAR_MS )); then
    echo "REPROVADO: turno de aquecimento em ${tot} ms, acima do limiar de ${LIMIAR_MS} ms." >&2
    echo "É a assinatura de raciocínio ligado (20,9 s contra 4,7 s medidos). Suba com" >&2
    echo "--chat-template-kwargs '{\"enable_thinking\":false}' e rode de novo." >&2
    return 1
  fi
  # cache_n=0 no 2º turno com corpo idêntico significa prefixo instável: a
  # rodada segue correta e fica ~7x mais lenta, sem nada no log.
  if [[ "${cache:-0}" == "0" ]]; then
    echo "AVISO: cache de prefixo não pegou no 2º turno idêntico — algo variável entrou no prefixo." >&2
  fi
  return 0
}

if [[ "${1:-}" == "status" ]]; then estado; exit 0; fi
if [[ "${1:-}" == "aquece" ]]; then aquece; exit $?; fi

echo "parando o que estiver no ar…"
# -np com pgrep numa linha só mataria o próprio ssh: o padrão casa a si mesmo.
ssh "$HOST" 'for p in $(pgrep -f "llama-server -m"); do kill -9 "$p" 2>/dev/null || true; done' || true

# Esperar a PORTA liberar, não o processo sumir: é o bind que falha, e ele falha
# em silêncio.
for _ in $(seq 1 20); do
  sleep 1
  ssh "$HOST" "ss -ltn 2>/dev/null | grep -q ':$PORTA '" || break
done

# NOJINJA=1: TESTADO E DESCARTADO em 2026-09-03 — não usar. A hipótese era
# que, com --jinja (padrão), o parser de tool-call do llama-server às vezes não
# reconhece as tags nativas do Gemma (`<|tool_call>...<tool_call|>`, diferente
# do `<tool_call>...</tool_call>` que o parser genérico espera) — 4 de 6
# sessões reais da rodada do item 2 do backlog terminaram com a chamada de
# ferramenta caindo como texto solto em vez de ser executada. --no-jinja
# QUEBRA O SERVIDOR INTEIRO para este modelo: toda chamada volta
# `{"error":{"code":500,"message":"this custom template is not supported, try
# using --jinja"}}` — o template do Gemma exige o motor jinja, não é só o
# tool-calling que depende dele. Mantido como flag só para não repetir o
# experimento; ver regras.md, "Desfazer também é refino".
FLAG_JINJA=""
[[ "${NOJINJA:-0}" == "1" ]] && FLAG_JINJA="--no-jinja"

echo "subindo: -c $CTX -np $SLOTS  (thinking off, KV em f16)${FLAG_JINJA:+, $FLAG_JINJA}"
# Cada flag é medida, não gosto — ver harness/README.md.
ssh "$HOST" "setsid $BIN -m $MODELO \
  -t 8 -c $CTX -np $SLOTS $FLAG_JINJA \
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

# Só depois do /health: a flag de thinking não aparece em lugar nenhum da
# config — só no comportamento.
aquece || { echo "AVISO: o servidor subiu, mas o aquecimento reprovou. NÃO rode medição." >&2; exit 1; }
estado
