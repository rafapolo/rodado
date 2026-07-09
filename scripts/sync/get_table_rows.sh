#!/usr/bin/env bash
dt="$1"  # dataset/table
dataset="${dt%%/*}"
table="${dt#*/}"
n=$(bq show --project_id=basedosdados --format=json "${dataset}.${table}" 2>/dev/null \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('numRows','0'), d.get('type','TABLE'))" 2>/dev/null)
echo -e "${dt}\t${n}"
