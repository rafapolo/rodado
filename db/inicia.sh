#!/usr/bin/env bash
# Sobe as peças do db.rodado.xyz dentro do container; cada uma se reinicia se cair.
# O Caddy fica em primeiro plano: se ele cair, o container cai e o haloy o refaz.
set -u
cd "$(dirname "$0")"

laco() {  # nome, comando...
  local nome=$1; shift
  while true; do
    echo "$(date '+%F %T') [$nome] sobe"
    "$@" 2>&1 | sed -u "s/^/[$nome] /"
    echo "$(date '+%F %T') [$nome] caiu"
    sleep 10
  done
}

laco catalogo python3 catalogo.py &
# sem catálogo ainda (primeiro deploy, volume vazio), terminal e endpoint esperam por ele
espera() { until [ -s "$RODADO_DB" ]; do sleep 15; done; "$@"; }

laco consulta espera python3 consulta.py &
# MCP por HTTP em /mcp: atrás da mesma senha/token do Caddy (sem bearer próprio) e
# consultando o consulta.py daqui de dentro, sem voltar pela internet
laco mcp env MCP_TRANSPORT=http MCP_BACKEND=http MCP_HTTP_BEHIND_AUTH=1 \
  MCP_HTTP_HOST=127.0.0.1 MCP_HTTP_PORT=18082 MCP_HTTP_ALLOWED_HOSTS=db.rodado.xyz \
  RODADO_URL=http://127.0.0.1:18081 python3 mcp/mcp_server.py &
# Catppuccin Mocha (https://catppuccin.com/palette); a JetBrains Mono quem carrega é a
# página (index.html injeta a fonte no iframe e troca a família depois que ela chega).
# Fundo transparente (allowTransparency): o degradê radial vem do CSS que index.html injeta.
TEMA='{"background":"#00000000","foreground":"#cdd6f4","cursor":"#f5e0dc","cursorAccent":"#1e1e2e","selectionBackground":"#585b70","black":"#45475a","red":"#f38ba8","green":"#a6e3a1","yellow":"#f9e2af","blue":"#89b4fa","magenta":"#f5c2e7","cyan":"#94e2d5","white":"#bac2de","brightBlack":"#585b70","brightRed":"#f38ba8","brightGreen":"#a6e3a1","brightYellow":"#f9e2af","brightBlue":"#89b4fa","brightMagenta":"#f5c2e7","brightCyan":"#94e2d5","brightWhite":"#a6adc8"}'
# cada aba é um processo com sua instância do DuckDB (1,5 GB no máximo): 4 abas, não 12
laco terminal espera ttyd -i 127.0.0.1 -p 18080 -b /tty -W -m 4 \
  -t titleFixed=rodado -t allowTransparency=true -t fontSize=12 -t lineHeight=1.15 \
  -t 'fontFamily="JetBrains Mono", Menlo, monospace' -t "theme=$TEMA" \
  python3 terminal.py &

exec caddy run --config /etc/caddy/Caddyfile --adapter caddyfile
