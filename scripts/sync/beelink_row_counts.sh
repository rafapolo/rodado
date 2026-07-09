#!/usr/bin/env bash
set -euo pipefail
cd ~/baseldosdados-data
for dir in */*/; do
  dt="${dir%/}"
  n=$(~/bin/duckdb -json -c "SELECT sum(num_rows) as r FROM parquet_file_metadata('${dt}/*.parquet');" 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(d[0]['r'] if d and d[0]['r'] is not None else 0)" 2>/dev/null || echo 0)
  echo -e "${dt}\t${n}"
done
