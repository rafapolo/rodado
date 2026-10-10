#!/usr/bin/env bash
# Roda os testes de UI/UX contra o db.rodado.xyz no ar, buscando a senha no finland.
set -euo pipefail
cd "$(dirname "$0")"
[ -d node_modules ] || bun install --silent
RODADO_SENHA="${RODADO_SENHA:-$(ssh finland 'cat /root/rodado-db/.senha')}" exec bun test --timeout 60000 "$@"
