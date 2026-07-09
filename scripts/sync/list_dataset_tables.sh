#!/usr/bin/env bash
dataset="$1"
bq ls --project_id=basedosdados --dataset_id="basedosdados:$dataset" --max_results=10000 --format=json 2>/dev/null \
| python3 -c "
import json, sys
data = sys.stdin.read()
if not data.strip():
    sys.exit(0)
for t in json.loads(data):
    ref = t.get('tableReference', {})
    print(ref['datasetId'] + '/' + ref['tableId'] + '\t' + t.get('type','TABLE'))
" > "/tmp/bq_tables_dir/$dataset.txt"
