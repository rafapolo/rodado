#!/usr/bin/env bash
# db.rodado.xyz no beelink: terminal (ttyd), endpoint de SQL e túnel até o finland.
# Sem sudo nem systemd --user aqui: o cron sobe isto numa sessão tmux e cada
# peça se reinicia sozinha se cair.
#   */5 * * * * tmux has-session -t rodado_db 2>/dev/null || tmux new -d -s rodado_db ~/rodado_db/servico.sh
set -u
cd "$(dirname "$0")"
LOG=~/logs/rodado_db
mkdir -p "$LOG"

laco() {  # nome, comando...
  local nome=$1; shift
  while true; do
    echo "$(date '+%F %T') sobe" >>"$LOG/$nome.log"
    "$@" >>"$LOG/$nome.log" 2>&1
    echo "$(date '+%F %T') caiu ($?)" >>"$LOG/$nome.log"
    sleep 10
  done
}

laco consulta python3 consulta.py &
# Catppuccin Mocha (https://catppuccin.com/palette); a JetBrains Mono quem carrega é a
# página (index.html injeta a fonte no iframe e troca a família depois que ela chega).
TEMA='{"background":"#1e1e2e","foreground":"#cdd6f4","cursor":"#f5e0dc","cursorAccent":"#1e1e2e","selectionBackground":"#585b70","black":"#45475a","red":"#f38ba8","green":"#a6e3a1","yellow":"#f9e2af","blue":"#89b4fa","magenta":"#f5c2e7","cyan":"#94e2d5","white":"#bac2de","brightBlack":"#585b70","brightRed":"#f38ba8","brightGreen":"#a6e3a1","brightYellow":"#f9e2af","brightBlue":"#89b4fa","brightMagenta":"#f5c2e7","brightCyan":"#94e2d5","brightWhite":"#a6adc8"}'
laco terminal ~/bin/ttyd -i 127.0.0.1 -p 18080 -b /tty -W -m 12 \
  -t titleFixed=rodado -t fontSize=12 -t lineHeight=1.15 \
  -t 'fontFamily="JetBrains Mono", Menlo, monospace' -t "theme=$TEMA" \
  python3 terminal.py &
# O finland só deixa este usuário/chave abrir as duas portas, na interface da
# rede do haloy (172.18.0.1), nunca em 0.0.0.0: lá o INPUT é ACCEPT.
laco tunel ssh -N -i ~/.ssh/rodado_tunel \
  -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
  -R 172.18.0.1:18080:127.0.0.1:18080 -R 172.18.0.1:18081:127.0.0.1:18081 \
  tunel@89.167.95.136 &
wait
