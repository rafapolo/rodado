#!/bin/bash
cd "$(dirname "$0")"
INIT=$(mktemp /tmp/duckdb_init_XXXX)
printf "LOAD httpfs;\nATTACH 'basedosdados.duckdb' AS bd (READ_ONLY);\n" > "$INIT"
duckdb --ui ui.duckdb -init "$INIT"
rm -f "$INIT"
